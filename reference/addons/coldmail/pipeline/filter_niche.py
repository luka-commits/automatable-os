#!/usr/bin/env python3
"""filter_niche.py — keyword-generic niche filter (any industry, no per-niche config).

The generic version of industrie-screening's filter_targets.py: instead of hardcoded
locksmith terms, you pass the niche-match terms (the keyword + synonyms the orchestrating
skill generates per niche — e.g. locksmith→schlüssel/aufsperr, dentist→zahnarzt/dental,
cleaner→cleaning/reinigung). Classifies each scraped place into 3 tiers:

  keep    — primary category OR name contains a niche term      (confident in-niche)
  verify  — empty / vague primary category, benefit of doubt    → the site-read confirms it
  drop    — positive non-target (chain/government/...) OR a clear OTHER category

Matching is on the PRIMARY category (categoryName) + the name, NOT the whole category blob —
a hardware store with "locksmith" as a SECONDARY category is a hardware store, not a locksmith
(the lesson filter_targets learned). keep+verify are written to --out (each tagged with `tier`);
the downstream site-read resolves the verify tier. This makes the scrape layer plug-any-industry.

Usage:
  filter_niche.py raw.json --keyword locksmith --terms "locksmith,schlüssel,aufsperr" --out targets.json
  filter_niche.py raw.json --keyword dentist            # --terms defaults to keyword + stem
"""
import json, argparse

NON_TARGET = ["government", "behörde", "rathaus", "stadtverwaltung", "schule", "school",
              "museum", "polizei", "police", "hospital", "krankenhaus", "university",
              "universität", "embassy", "botschaft", "town hall", "courthouse"]

# Other-trade category markers: a business whose REAL trade is one of these is NOT the niche,
# even if it self-tags the niche as a (secondary) Google category. The tell-tale we hit live:
# "OneStop Van Solutions" tagged itself "Locksmith" but is really [Truck accessories, Van fit-out,
# Auto electrical] = a van-security shop. Note: "auto electrical"/"car security" alone are NOT here
# — genuine AUTO-locksmiths carry those; the disqualifiers are clearly-different physical trades.
OTHER_TRADE = ["window", "garage door", "glazing", "conservatory", "truck accessor", "van fit",
               "tyre", "fencing", "roofing", "kitchen", "bathroom", "blinds", "hardware store",
               "diy store", "supermarket", "plumb", "scaffold", "wrapping", "car wash",
               "car dealer", "dealership", "furniture", "removal", "builders merchant",
               "estate agent", "letting agent", "cleaning service", "carpet",
               # added 2026-06-13 from real WY false-genuines (lean, locksmith-flavoured — move to
               # per-niche config when a 2nd niche arrives):
               "composite door", "ironmonger", "car tuning", "vehicle tuning"]

# Name words that betray a NON-locksmith business even when it self-tags the "Locksmith" Google
# category (live false-positives: "Lock Investments", "Key Logistics", "Key Realty", "Tech Repair
# Guys"). Metadata alone can't separate these from a real generic-named locksmith → send to verify,
# the site-read decides.
NAME_DISQUALIFY = ["invest", "logistic", "realty", "realtor", "estate", "property", "recruit",
                   "solicitor", "accountant", "mortgage", "insurance", "tech repair", "phone repair",
                   "computer repair", "it support", "travel", "consult", "capital", "holdings",
                   "marketing", "media", "design studio",
                   # clearly-consumer businesses no locksmith is ever named after:
                   "laundry", "launderette", "restaurant", "barber", "salon", "butcher", "bakery",
                   "florist", "pharmacy", "dentist", "optician", "tattoo", "takeaway", "kebab", "pizza", "cafe",
                   # added 2026-06-13: name-betrays-other-trade even with a 'Locksmith' category
                   "composite door", "ironmonger", "training", "tuning"]


def cat_of(p):
    return (p.get("categoryName") or (p.get("categories") or [""])[0] or "").strip()


def clean_email(e):
    """Accept only a real email. The scrape's `emails`/`email` field sometimes carries a
    Maps URL or junk (live case: '//www.google.com/maps/place/...') — that must NEVER reach
    a cold-mail tool. Reject anything with a slash/space or no real local@host.dot shape."""
    e = (e or "").strip()
    if "@" not in e or "/" in e or " " in e:
        return ""
    local, _, host = e.partition("@")
    return e.lower() if local and "." in host else ""


def pick_email(p):
    """First VALID email from the scrape (emails[] list, then the singular email field)."""
    for cand in (p.get("emails") or []):
        c = clean_email(cand)
        if c:
            return c
    return clean_email(p.get("email"))


def resolve_terms(keyword, terms_str=""):
    """Niche-match terms: explicit --terms, else keyword + its singular stem."""
    kw = (keyword or "").strip().lower()
    terms = [t.strip().lower() for t in (terms_str or "").split(",") if t.strip()] or [kw, kw.rstrip("s")]
    return list(dict.fromkeys(t for t in terms if t))


def classify(p, terms):
    """4-outcome niche genuineness, on Maps metadata only (no fetch):
       'keep'   — the name confirms the niche (e.g. "...Locksmiths"), OR the primary category is
                  the niche AND no other physical trade contradicts it → confident genuine.
       'verify' — primary category is the niche BUT a real other-trade is also present and the name
                  doesn't confirm it (the OneStop-Van-Solutions case), OR category is empty
                  → needs the optional site-read to confirm.
       'drop'   — a positive non-target (government/...) OR not the niche at all.
    """
    cat = cat_of(p).lower()
    name = (p.get("title") or "").lower()
    cats = [c.lower() for c in (p.get("categories") or [])] or [cat]
    blob = " ".join([cat] + cats)
    if any(t in blob for t in NON_TARGET):
        return "drop"
    name_sig = any(t in name for t in terms)              # name confirms the niche (locksmith/schlüssel)
    name_bad = any(d in name for d in NAME_DISQUALIFY)     # name betrays another business
    cat_sig = any(t in cat for t in terms)                # PRIMARY category is the niche
    other_trade = any(d in c for c in cats for d in OTHER_TRADE)
    if name_bad:
        return "verify"                                   # realty/logistics/tech-repair name → site-read decides
    if name_sig:
        return "keep"                                     # name says it → genuine (e.g. Eydens Auto Locksmiths)
    if cat_sig:
        return "verify" if other_trade else "keep"        # niche-cat + a foreign trade, no name → site-read decides
    if not cat:
        return "verify"
    return "drop"


def row_of(p):
    return {
        "placeId": p.get("placeId"),
        "name": p.get("title") or p.get("name"),
        "town": p.get("city") or p.get("town") or "",
        "website": p.get("website") or p.get("site") or "",
        # preserve the scrape's VALID email through the filter, so downstream recovery only
        # has to fill the RESIDUAL (no-email) leads instead of re-scraping every site.
        # clean_email guards against the Maps-URL junk the scrape sometimes emits.
        "email": pick_email(p),
        "phone": p.get("phone") or p.get("phoneUnformatted") or "",
        "reviews": p.get("reviewsCount") or 0,
        "rating": p.get("totalScore") or p.get("rating"),
        "category": cat_of(p),
        "address": p.get("address") or "",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw")
    ap.add_argument("--keyword", required=True)
    ap.add_argument("--terms", default="", help="comma niche-match terms (synonyms); default = keyword + stem")
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    kw = a.keyword.strip().lower()
    terms = [t.strip().lower() for t in a.terms.split(",") if t.strip()] or [kw, kw.rstrip("s")]
    terms = list(dict.fromkeys(t for t in terms if t))
    raw = json.load(open(a.raw))

    keep, verify, drop = [], [], []
    for p in raw:
        if not p.get("placeId"):
            continue
        cat = cat_of(p).lower()
        name = (p.get("title") or "").lower()
        blob = " ".join([cat] + [c.lower() for c in (p.get("categories") or [])])
        if any(t in blob for t in NON_TARGET):
            drop.append(p); continue
        if any(t in cat for t in terms) or any(t in name for t in terms):
            r = row_of(p); r["tier"] = "keep"; keep.append(r); continue
        if not cat:                                  # empty primary category -> benefit of doubt
            r = row_of(p); r["tier"] = "verify"; verify.append(r); continue
        drop.append(p)                               # a clear OTHER category

    survivors = keep + verify
    out = a.out or a.raw.rsplit(".", 1)[0] + "_targets.json"
    json.dump(survivors, open(out, "w"), ensure_ascii=False)
    # Out-of-target bucket: the dropped non-genuine are NOT deleted — they're written
    # to a labelled sibling file (name + primary category + reason) so they're auditable
    # and retrievable (e.g. re-classify, a different niche, or just records). Part of the
    # skill so every run produces it automatically, not an ad-hoc afterthought.
    oot = out.rsplit(".", 1)[0] + "_out_of_target.json"
    json.dump([{"business_name": p.get("title") or p.get("name") or "",
                "category": cat_of(p), "city": p.get("city") or "",
                "website": p.get("website") or "", "place_id": p.get("placeId") or "",
                "reason": "non-genuine-niche (filter_niche drop)"} for p in drop],
              open(oot, "w"), ensure_ascii=False, indent=1)
    n = len(raw)
    print(f"niche '{kw}' (terms: {', '.join(terms)})")
    print(f"  keep (confident):   {len(keep)}")
    print(f"  verify (site-read): {len(verify)}")
    print(f"  dropped:            {len(drop)}  ({100*len(drop)//max(n,1)}% of {n})  -> {oot}")
    print(f"  -> {len(survivors)} survivors written to {out}")


if __name__ == "__main__":
    main()
