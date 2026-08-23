#!/usr/bin/env python3
"""ingest_to_supabase.py — region-scrape raw.json -> Supabase `industry_operators`.

The cheap competitive-map ingest (no DataForSEO/GBP). Maps the compass scrape into the
market DB so the Portal's existing market-report (CompetitorMap, haversine, nearest) works
on it. Computes, all FREE from the scrape:
  - rank_review + percentile within (niche, region)   (review-prominence, NOT Google rank)
  - nearest 2 competitors + distance (haversine)       -> details.nearest  (the cold-mail hook)
Leaves gbp / setup_score / maps_rank / dataforseo NULL — those fill later on a reply (deep audit).

Preserves existing rows: never overwrites an advanced pipeline_status (interested/lead_magnet/…);
only sets pipeline_status='scraped' on new rows.

Usage:
  ingest_to_supabase.py <raw.json> --niche locksmith --region "West Midlands" --country GB \
      --terms "locksmith,schluessel" [--dry-run]
"""
import json, os, sys, argparse, math, urllib.request, urllib.parse, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from filter_niche import classify, resolve_terms, cat_of, pick_email

REF = "qhlklpweondgkswptyfc"
BASE = f"https://{REF}.supabase.co/rest/v1/industry_operators"
ADVANCED = None  # statuses we must never downgrade; computed below from existing rows


def key():
    for line in open(os.path.expanduser('~/.config/credentials.env')):
        if line.startswith('POCKET_DASH_SUPABASE_SERVICE_ROLE='):
            return line.split('=', 1)[1].strip().strip('"')
    sys.exit("[fatal] POCKET_DASH_SUPABASE_SERVICE_ROLE missing in ~/.config/credentials.env")


def headers(k, extra=None):
    h = {'apikey': k, 'Authorization': f'Bearer {k}', 'Content-Type': 'application/json'}
    if extra:
        h.update(extra)
    return h


def haversine_km(a, b):
    (la1, lo1), (la2, lo2) = a, b
    r = 6371.0
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = math.radians(la2 - la1), math.radians(lo2 - lo1)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(x)), 2)


def first(lst):
    return (lst or [None])[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('raw')
    ap.add_argument('--niche', required=True)
    ap.add_argument('--region', required=True)
    ap.add_argument('--country', required=True, help='e.g. GB, DE')
    ap.add_argument('--terms', default='')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    niche = a.niche.strip().lower()
    terms = resolve_terms(a.niche, a.terms)
    raw = json.load(open(a.raw))

    # 1) classify each on metadata (no fetch): keep = confident genuine niche; verify = ambiguous
    #    (primary cat is the niche but a foreign trade is also present, no name signal — the
    #    OneStop-Van-Solutions case, resolved later by the optional site-read); drop the rest.
    tier = {}
    kept = []
    dropped = []
    for p in raw:
        if not p.get('placeId'):
            continue
        c = classify(p, terms)
        if c == 'drop':
            dropped.append(p)            # bucketed below, NOT discarded (Luka's rule: never drop, bucket)
            continue
        tier[p['placeId']] = 'genuine' if c == 'keep' else 'pending'
        kept.append(p)

    # Out-of-target bucket: the non-genuine are written to a labelled sibling of the raw file
    # (name + primary category + reason), never silently discarded — so they're auditable and
    # retrievable (re-classify, a different niche, records). Same shape filter_niche.py emits.
    oot = a.raw.rsplit('.', 1)[0] + '_out_of_target.json'
    json.dump([{"business_name": p.get("title") or p.get("name") or "",
                "category": cat_of(p), "city": p.get("city") or "",
                "website": p.get("website") or "", "place_id": p.get("placeId") or "",
                "reason": "non-genuine-niche (ingest classify drop)"} for p in dropped],
              open(oot, "w"), ensure_ascii=False, indent=1)
    if dropped:
        print(f"  out-of-target bucket: {len(dropped)} non-genuine -> {oot}")

    # 2) dedup: placeId, then collapse duplicate listings (same domain/name @ ~same spot). When
    #    collapsing, PREFER the record whose name confirms the niche ("Eydens Auto Locksmiths" beats
    #    the bare "Eydens" dup so we don't lose the name signal), then higher reviews.
    def domain(url):
        if not url:
            return None
        u = url.lower().split('//')[-1].split('/')[0]
        return u[4:] if u.startswith('www.') else u

    def cell(p):
        loc = p.get('location') or {}
        return (round(loc.get('lat') or 0, 3), round(loc.get('lng') or 0, 3))

    def has_name(p):
        nm = (p.get('title') or '').lower()
        return any(t in nm for t in terms)

    def better(p, cur):
        if cur is None:
            return True
        if has_name(p) != has_name(cur):
            return has_name(p)                              # the niche-named record wins
        return (p.get('reviewsCount') or 0) > (cur.get('reviewsCount') or 0)

    seen_pid, uniq = set(), []
    for p in kept:
        if p['placeId'] in seen_pid:
            continue
        seen_pid.add(p['placeId']); uniq.append(p)

    best = {}
    for p in uniq:
        dom = domain(p.get('website') or p.get('site'))
        k = (dom, *cell(p)) if dom else ((p.get('title') or '').lower().strip(), *cell(p))
        if better(p, best.get(k)):
            best[k] = p
    ops = list(best.values())
    if len(ops) < len(uniq):
        print(f"[dedup] {len(uniq)} → {len(ops)} (collapsed {len(uniq)-len(ops)} duplicate listings)")

    # 3) review-rank; nearest-2 over the GENUINE pool ONLY (pending/verify excluded — never name a
    #    van-shop as someone's nearest rival; the optional site-read can later upgrade pending→genuine).
    ops.sort(key=lambda p: (p.get('reviewsCount') or 0), reverse=True)
    n = len(ops)
    byid = {p['placeId']: p for p in ops}
    coords = {p['placeId']: (p['location']['lat'], p['location']['lng'])
              for p in ops if p.get('location', {}).get('lat') is not None}
    gcoords = {pid: c for pid, c in coords.items() if tier.get(pid) == 'genuine'}
    genuine_n = sum(1 for p in ops if tier.get(p['placeId']) == 'genuine')

    rows = []
    now = datetime.datetime.now(datetime.UTC).isoformat()
    for i, p in enumerate(ops):
        rank = i + 1
        pct = round(100 * (n - rank) / max(n - 1, 1))            # rank1≈100 (top), last≈0
        nearest = []
        if p['placeId'] in coords:
            me = coords[p['placeId']]
            cand = ((haversine_km(me, gcoords[qid]), qid) for qid in gcoords if qid != p['placeId'])
            # ≥50m floor: anything closer is a co-located duplicate listing, not a real rival
            d = sorted((c for c in cand if c[0] >= 0.05), key=lambda x: x[0])[:2]
            nearest = [{'place_id': qid, 'name': byid[qid].get('title'), 'km': km} for km, qid in d]
        rows.append({
            'place_id': p['placeId'], 'niche': niche, 'country': a.country, 'region': a.region,
            'town': p.get('city'), 'name': p.get('title'),
            'website': p.get('website') or p.get('site') or None,
            'phone': p.get('phone') or p.get('phoneUnformatted') or None,
            'email': pick_email(p) or None,
            'instagram': first(p.get('instagrams')), 'facebook': first(p.get('facebooks')),
            'reviews': p.get('reviewsCount') or 0, 'rating': p.get('totalScore'),
            'category_primary': cat_of(p), 'categories': p.get('categories') or [],
            'lat': p.get('location', {}).get('lat'), 'lng': p.get('location', {}).get('lng'),
            'photos_count': p.get('imagesCount'),
            'rank_review': rank, 'percentile': pct,
            'details': {'nearest': nearest, 'tier': tier.get(p['placeId'], 'genuine'),
                        'no_website': not (p.get('website') or p.get('site'))},
            'sources': {'scraper': 'seo_scrape_adaptive', 'src': os.path.basename(os.path.dirname(a.raw))},
            'scraped_at': now, 'updated_at': now, 'raw': p,
        })

    # summary
    with_site = sum(1 for r in rows if r['website'])
    with_email = sum(1 for r in rows if r['email'])
    print(f"[ingest] {niche} / {a.region} ({a.country}): {n} operators "
          f"({genuine_n} genuine, {n-genuine_n} pending site-read · {with_site} site, {with_email} email)")
    print(f"  nearest-2 over genuine pool only ({len(gcoords)} genuine with coords)")
    sample = next((r for r in rows if r['details']['nearest']), rows[0])
    print(f"  sample: {sample['name']} — #{sample['rank_review']} "
          f"· nearest: {[f'{x['name']} {x['km']}km' for x in sample['details']['nearest']]}")
    if a.dry_run:
        print("\n[dry-run] nothing written to Supabase.")
        return

    k = key()
    # fetch existing statuses for this market → don't downgrade advanced ones
    q = urllib.parse.urlencode({'select': 'place_id,pipeline_status',
                                'niche': f'eq.{niche}', 'region': f'eq.{a.region}'})
    existing = {}
    try:
        req = urllib.request.Request(f"{BASE}?{q}", headers=headers(k))
        for r in json.load(urllib.request.urlopen(req, timeout=30)):
            existing[r['place_id']] = r.get('pipeline_status')
    except Exception as e:
        print(f"[warn] could not read existing statuses ({e}); treating all as new")
    # SAFETY: only write brand-new operators + previously-'scraped' ones. Any row whose existing
    # pipeline_status is ADVANCED (interested / lead_magnet / client / …) is left 100% untouched —
    # we never clobber a lead we've already worked or built a lead magnet for.
    def writable(pid):
        if pid not in existing:
            return True                              # brand new
        return existing[pid] in (None, '', 'scraped')  # only ever scraped before → safe to refresh

    to_write = [{**r, 'pipeline_status': 'scraped'} for r in rows if writable(r['place_id'])]
    protected = [r for r in rows if not writable(r['place_id'])]

    def upsert(batch):
        total = 0
        for i in range(0, len(batch), 100):
            chunk = batch[i:i + 100]
            req = urllib.request.Request(
                f"{BASE}?on_conflict=place_id", data=json.dumps(chunk).encode(), method='POST',
                headers=headers(k, {'Prefer': 'resolution=merge-duplicates,return=minimal'}))
            urllib.request.urlopen(req, timeout=60)
            total += len(chunk)
        return total

    n_written = upsert(to_write) if to_write else 0
    print(f"\n✅ upserted {n_written} → industry_operators (new + previously-scraped)")
    if protected:
        print(f"🛡  left {len(protected)} existing advanced leads UNTOUCHED "
              f"(lead_magnet / interested / client — never overwritten)")
    print(f"   query the market: niche=eq.{niche} & region=eq.{urllib.parse.quote(a.region)}")


if __name__ == '__main__':
    main()
