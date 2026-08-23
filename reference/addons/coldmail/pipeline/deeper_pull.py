#!/usr/bin/env python3
"""deeper_pull.py — die Bruecke zu DataForSEO fuer die Leads, denen sonst nichts bleibt.

Der Anlass (Luka, 27.07.2026): "wenn wir nur 100 zu 100 haben, muessten wir auch auf
DataForSEO und mehr SEO-Findings gehen, damit wir die Gap-Story haben. Schau, dass du
das auch automatisch machst."

WER HIER LANDET: `score.needs_deeper()` markiert Betriebe, deren restliche Luecken nur
noch technisch sind -- kein Formular, kein Markup. Beides stimmt, beides benennt keinen
verlorenen Auftrag. Gemessen in Bedford waren das 2 von 12, und ihre Mails lasen sich
WORTGLEICH identisch. Ausgerechnet die bestaufgestellten Betriebe der Kohorte bekamen
also die austauschbarste Mail.

WARUM NUR FUER DIESE: DataForSEO kostet je Abfrage. Ueber 3.593 Leads waere das teuer
und ueberfluessig, weil die grosse Mehrheit echte Luecken im GBP hat. Fuer die wenigen,
bei denen der billige Zug nichts hergibt, lohnt es sich doppelt -- es sind die gut
gefuehrten Betriebe, und die sind als Kunde am meisten wert.

WAS GEZOGEN WIRD: die Maps-Position fuer "<gewerk> <ort>". Das ist die Zahl, die jeder
lokale Betrieb wissen will und selbst nicht sauber messen kann (seine eigene Suche ist
durch Standort und Verlauf verfaelscht). Und es ist die einzige Luecke, die auch ein
tadellos gepflegtes Profil haben kann.

Der `rank` aus dem Apify-Scrape taugt dafuer NICHT: in Bedford kam Platz 3 zweimal vor,
Platz 13 dreimal, gezaehlt wurde ab 2. Daraus eine Position zu behaupten waere eine
erfundene Zahl.

Usage:
  python3 deeper_pull.py runs/locksmith-bedford --niche locksmith [--apply]
  python3 deeper_pull.py --self-check
"""
from __future__ import annotations
import argparse, base64, csv, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _auth() -> str:
    """Basic-Auth-Kopf. credentials.env fuehrt beide Formen, je nach Alter des Eintrags."""
    env = {}
    p = os.path.expanduser("~/.config/credentials.env")
    for line in open(p):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    if env.get("DATAFORSEO_AUTH_BASE64"):
        return env["DATAFORSEO_AUTH_BASE64"]
    if env.get("DATAFORSEO_AUTH_BASE"):
        return env["DATAFORSEO_AUTH_BASE"]
    login, pw = env.get("DATAFORSEO_LOGIN"), env.get("DATAFORSEO_PASSWORD")
    if not (login and pw):
        sys.exit("kein DataForSEO-Login in ~/.config/credentials.env")
    return base64.b64encode(f"{login}:{pw}".encode()).decode()


def dfs(path: str, payload: list, timeout: int = 180) -> dict:
    req = urllib.request.Request(
        "https://api.dataforseo.com/v3" + path, data=json.dumps(payload).encode(),
        headers={"Authorization": "Basic " + _auth(), "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def maps_rank(keyword: str, location: str, place_id: str) -> dict | None:
    """-> {'rank': n, 'ahead': [Namen], 'keyword': ...} oder None, wenn nicht gefunden.

    Nicht gefunden heisst NICHT Platz 0. Es heisst, dass wir es nicht wissen -- und dann
    wird nichts behauptet, genau wie ueberall sonst in dieser Pipeline.
    """
    r = dfs("/serp/google/maps/live/advanced",
            [{"keyword": keyword, "location_name": location, "language_code": "en",
              "device": "desktop", "depth": 20}])
    try:
        items = r["tasks"][0]["result"][0]["items"] or []
    except (KeyError, IndexError, TypeError):
        return None
    for i, it in enumerate(items, 1):
        if it.get("place_id") == place_id:
            return {"rank": i, "keyword": keyword,
                    "ahead": [x.get("title") for x in items[:i - 1] if x.get("title")][:3],
                    "of": len(items)}
    # NICHT gefunden ist selbst ein Befund, und ein harter -- aber nur, wenn die Abfrage
    # ueberhaupt Ergebnisse geliefert hat. Kam gar nichts zurueck, wissen wir nichts.
    # Der Suchbegriff wird mitgeschickt und in der Mail zitiert: "for 'locksmith bedford'"
    # macht die Aussage nachpruefbar, und ohne ihn waere sie eine Behauptung ueber alle
    # denkbaren Suchen statt ueber die eine, die wir gemessen haben.
    # ... aber nur, wenn genug zurueckkam, um eine Aussage zu tragen. Die Abfrage
    # "locksmith st. neots" lieferte EIN Ergebnis, und daraus wurde "you do not come up at
    # all in the first 1 google shows" -- formal wahr, inhaltlich Unsinn. Unter zehn
    # Treffern hat der Ort schlicht keinen Kartenblock, den wir beurteilen koennten.
    return ({"rank": None, "keyword": keyword, "ahead": [], "of": len(items)}
            if len(items) >= 10 else None)


def finding(rank_data: dict) -> dict | None:
    """Aus der Position ein Befund, der einen Auftrag benennt.

    Platz 1 bis 3 ist der Kartenblock -- wer da drin steht, bekommt die Anrufe. Alles
    darunter existiert fuer den Suchenden praktisch nicht, und genau so wird es gesagt.
    """
    if not rank_data:
        return None
    n, kw = rank_data["rank"], rank_data["keyword"]
    if n is None:
        return {"check": "gbp-map-reach", "kind": "gap", "strength": 96,
                "fact": f'you do not come up at all in the first {rank_data["of"]} '
                        f'google shows for "{kw}"',
                "means": "the people searching that phrase right now are not seeing you"}
    if n <= 3:
        return {"check": "gbp-map-reach", "kind": "good", "strength": 92,
                "fact": f'you sit at {n} for "{kw}", inside the three google shows first',
                "means": "that is where the calls come from"}
    ahead = rank_data.get("ahead") or []
    tail = f", behind {ahead[0].lower()}" if ahead else ""
    return {"check": "gbp-map-reach", "kind": "gap", "strength": 94,
            "fact": f'you come up {n}th for "{kw}"{tail}',
            "means": "google only shows three before someone has to press for more, "
                     "and almost nobody presses"}


def push_finding(place_id: str, f: dict) -> bool:
    """Den Ranking-Befund in web_signals ergaenzen, ohne den Rest zu ueberschreiben.

    Er wird VORNE eingereiht und ersetzt die schwaechste bestehende Luecke: er ist der
    Grund, warum dieser Lead ueberhaupt den teuren Zug bekommen hat.
    """
    import urllib.parse
    from dedupe_leads import _supabase
    url, key = _supabase()
    hdr = {"apikey": key, "Authorization": f"Bearer {key}"}
    q = f"{url}/rest/v1/industry_operators?place_id=eq.{urllib.parse.quote(place_id, safe='')}"
    cur = json.load(urllib.request.urlopen(
        urllib.request.Request(q + "&select=web_signals", headers=hdr), timeout=30))
    if not cur:
        return False
    ws = cur[0].get("web_signals") or {}
    line = f"{f['fact']}, so {f['means']}"
    if f["kind"] == "gap":
        ws["gaps"] = [line] + [g for g in (ws.get("gaps") or []) if "come up" not in g][:1]
    else:
        ws["good"] = [line] + [g for g in (ws.get("good") or []) if "you sit at" not in g][:1]
    ws["findings"] = [f] + [x for x in (ws.get("findings") or [])
                            if x.get("check") != "gbp-map-reach"]
    ws["deeper_pulled"] = True
    ws.setdefault("scores", {})["deeper"] = False   # hat jetzt eine Story, geht in den Versand
    req = urllib.request.Request(q, data=json.dumps({"web_signals": ws}).encode(),
                                 method="PATCH",
                                 headers={**hdr, "Content-Type": "application/json",
                                          "Prefer": "return=minimal"})
    urllib.request.urlopen(req, timeout=30).read()
    return True


def nach_ort(niche: str, land: str = "England,United Kingdom", limit_orte: int = 0,
             apply: bool = False) -> dict:
    """EINE Abfrage je Ort statt je Lead.

    Die Maps-Antwort auf "locksmith bedford" enthaelt 20 Treffer MIT place_id. Daraus
    laesst sich der Rang JEDES Bedford-Leads ablesen -- eine Abfrage bedient den ganzen
    Ort. Gemessen: 576 Orte fuer 3.593 Leads, also $1.15 statt $7.19, und ein Ort mit 40
    Betrieben kostet so viel wie einer mit einem.

    Wer nicht unter den ersten 20 auftaucht, bekommt KEINE Luecke in unseren Daten,
    sondern den Befund: fuer diese Suche existiert er nicht. Das ist die Aussage, die ein
    lokaler Betrieb am meisten will und selbst nicht sauber messen kann -- seine eigene
    Suche ist durch Standort und Verlauf verfaelscht.
    """
    import collections, urllib.parse
    from dedupe_leads import _supabase
    url, key = _supabase()
    hdr = {"apikey": key, "Authorization": f"Bearer {key}"}

    leads, off = [], 0
    while True:
        q = (f"{url}/rest/v1/industry_operators?select=place_id,name,town"
             f"&niche=eq.{urllib.parse.quote(niche)}&pipeline_status=neq.disqualified"
             f"&town=not.is.null&order=place_id&limit=1000&offset={off}")
        seite = json.load(urllib.request.urlopen(
            urllib.request.Request(q, headers=hdr), timeout=60))
        leads += seite
        off += 1000
        if len(seite) < 1000:
            break

    nach = collections.defaultdict(list)
    for x in leads:
        t = (x.get("town") or "").strip()
        if t:
            nach[t].append(x)
    orte = sorted(nach, key=lambda t: -len(nach[t]))
    if limit_orte:
        orte = orte[:limit_orte]

    zahlen = collections.Counter()
    kosten = 0.0
    for i, ort in enumerate(orte, 1):
        kw = f"{niche} {ort.lower()}"
        try:
            r = dfs("/serp/google/maps/live/advanced",
                    [{"keyword": kw, "location_name": f"{ort},{land}",
                      "language_code": "en", "device": "desktop", "depth": 20}])
        except Exception as e:
            zahlen["abfrage_fehler"] += 1
            print(f"  [{i}/{len(orte)}] {ort}: {type(e).__name__} {str(e)[:70]}", flush=True)
            continue
        kosten += r.get("cost") or 0
        try:
            items = r["tasks"][0]["result"][0]["items"] or []
        except (KeyError, IndexError, TypeError):
            zahlen["ort_ohne_ergebnis"] += 1
            continue
        # Der Ort muss auch der Ort sein, nach dem wir gefragt haben. Fehlt die Aufloesung,
        # liefert DataForSEO ein anderes Gebiet und wir behaupteten einen falschen Rang.
        pos = {it.get("place_id"): n for n, it in enumerate(items, 1) if it.get("place_id")}
        for lead in nach[ort]:
            rd = {"rank": pos.get(lead["place_id"]), "keyword": kw, "of": len(items),
                  "ahead": [x.get("title") for x in items[:max((pos.get(lead["place_id"]) or 1) - 1, 0)]
                            if x.get("title")][:3]}
            f = finding(rd)
            if not f:
                continue
            zahlen["in_top3" if (rd["rank"] or 99) <= 3 else
                   "platziert" if rd["rank"] else "nicht_gefunden"] += 1
            if apply:
                push_finding(lead["place_id"], f)
                _rang_spalte(url, hdr, lead["place_id"], rd["rank"])
        if i % 25 == 0 or i == len(orte):
            print(f"  [{i}/{len(orte)}] {ort}: {dict(zahlen)} ${kosten:.2f}", flush=True)

    zahlen["kosten_usd"] = round(kosten, 3)
    return dict(zahlen)


def _rang_spalte(url, hdr, place_id, rank):
    """maps_rank als Spalte, nicht nur im JSONB -- nur die laesst sich sortieren."""
    import urllib.parse
    q = f"{url}/rest/v1/industry_operators?place_id=eq.{urllib.parse.quote(place_id, safe='')}"
    req = urllib.request.Request(q, data=json.dumps({"maps_rank": rank}).encode(),
                                 method="PATCH",
                                 headers={**hdr, "Content-Type": "application/json",
                                          "Prefer": "return=minimal"})
    try:
        urllib.request.urlopen(req, timeout=30).read()
    except urllib.error.HTTPError as e:
        print(f"    maps_rank fuer {place_id}: {e.code} {(e.read() or b'').decode()[:120]}")


def self_check():
    assert finding(None) is None, "keine Daten, kein Befund"
    g = finding({"rank": 2, "keyword": "locksmith bedford", "ahead": ["Auto Keys"], "of": 20})
    assert g["kind"] == "good" and "inside the three" in g["fact"], g
    b = finding({"rank": 9, "keyword": "locksmith bedford", "ahead": ["Auto Keys"], "of": 20})
    assert b["kind"] == "gap" and "9th" in b["fact"] and "behind auto keys" in b["fact"], b
    # ohne bekannte Vordermaenner wird keiner erfunden
    b2 = finding({"rank": 9, "keyword": "k", "ahead": [], "of": 20})
    assert "behind" not in b2["fact"], b2
    # Gar nicht gefunden ist der haerteste Befund -- aber nur mit genanntem Suchbegriff,
    # sonst ist es eine Aussage ueber alle denkbaren Suchen statt ueber die gemessene
    weg = finding({"rank": None, "keyword": "locksmith bedford", "ahead": [], "of": 20})
    assert weg["kind"] == "gap" and "first 20" in weg["fact"], weg
    assert '"locksmith bedford"' in weg["fact"], weg
    # Aus einer Handvoll Treffer wird kein Urteil: maps_rank liefert dann gar nichts,
    # statt "you do not come up in the first 1" zu behaupten.
    assert finding(None) is None
    print("self-check ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rundir", nargs="?")
    ap.add_argument("--niche", default="locksmith")
    ap.add_argument("--apply", action="store_true", help="wirklich abfragen (kostet je Lead)")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return self_check()
    if not a.rundir:
        ap.error("rundir oder --self-check")

    cv = os.path.join(a.rundir, "cohort_vars.csv")
    rows = [r for r in csv.DictReader(open(cv, encoding="utf-8")) if r.get("needs_deeper")]
    if not rows:
        print("keine Leads brauchen den tieferen Zug — der billige Scrape reicht fuer alle")
        return 0

    print(f"{len(rows)} Leads ohne verwertbare Luecke aus dem billigen Zug:")
    for r in rows:
        kw = f"{a.niche} {r.get('town_casual') or r.get('area')}".strip().lower()
        print(f"   {r['business_name'][:34]:36} -> \"{kw}\"")
    if not a.apply:
        print(f"\n[dry-run] {len(rows)} Maps-Abfragen. Mit --apply ausfuehren.")
        return 0

    got, patched = 0, 0
    for r in rows:
        town = r.get("town_casual") or r.get("area")
        kw = f"{a.niche} {town}".strip().lower()
        rd = maps_rank(kw, f"{town},England,United Kingdom", r["place_id"])
        f = finding(rd)
        if not f:
            print(f"   {r['business_name'][:30]:32} nicht in den ersten 20 gefunden")
            continue
        got += 1
        print(f"   {r['business_name'][:30]:32} {f['kind']:4} {f['fact'][:60]}")
        # Der Befund muss dorthin, wo die Mail ihn liest -- sonst war der Zug umsonst.
        # web_signals ist die eine Quelle, aus der export_cohort die Spalten baut.
        if push_finding(r["place_id"], f):
            patched += 1
    print(f"\n{got}/{len(rows)} mit verwertbarem Ranking-Befund, {patched} in web_signals geschrieben")
    return 0


if __name__ == "__main__":
    sys.exit(main())
