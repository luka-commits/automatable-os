#!/usr/bin/env python3
"""enrich_cohort_findings.py — die Findings berechnen und in die DATENBANK schreiben.

WARUM NICHT NUR IN DIE CSV: export_cohort erzeugt cohort_vars.csv jedes Mal neu aus
Supabase. Eine Anreicherung, die nur in der CSV steht, ist beim naechsten Export weg.
Deshalb landen die Findings in `industry_operators.web_signals` (JSONB, war leer, keine
Migration noetig) -- dort, wo die Doku ohnehin sagt "Supabase is the single source of
truth". Die CSV wird daraus abgeleitet, nicht andersherum.


Das fehlende Stueck: export_cohort schreibt cohort_vars.csv mit einer Spalte
`site_finding`, und die ist ueber alle 4.277 Zeilen LEER. Damit erreicht keine einzige
Personalisierung Instantly -- weder die GBP- noch die Website-Findings.

Was hier entsteht, je Lead:
  good_1, good_2            Variante B, "what's working well"
  gap_1, gap_2, gap_3       Variante B, "what could be improved"
  site_finding              der staerkste Website-Befund (Rueckwaertskompatibilitaet)
  findings_json             alle Bausteine, fuer den Prosa-Generator von Variante A

KORREKTUR 27.07.2026 — der Absatz unten stimmt so nicht. `markt_copy.md` § Rahmen weist
Block 4 und 5 dem MODELL zu, und die elf von Luka abgenommenen Mails waren modellgeschrieben.
Was hier entsteht, ist die geprueffte Faktenlage (`fact` + `means` je Befund), aus der ein
Sonnet-Subagent die Bloecke 4 und 5 formuliert -- kein fertiger Mailtext. Der Satz unten hat
am 27.07. dazu gefuehrt, dass der `read`-Block deterministisch nachgebaut wurde, obwohl der
Rahmen etwas anderes sagt. Wer den Rahmen aendern will, aendert ihn in markt_copy.md zuerst.

VARIANTE B BRAUCHT KEIN MODELL. Das gerenderte Beispiel in markt_copy.md zeigt
"no booking link, so the ones who do find you have to dial" -- das ist woertlich
`fact`, ", so ", `means`. Die Stichpunkte sind also mechanisch, und damit ist der halbe
A/B-Test ohne Generierung versandfaehig. Nur die Prosa von Variante A braucht das
Modell, und auch die bekommt nur fertige fact/means-Paare und darf nichts hinzufuegen.

Leere Felder sind Absicht: ein Lead ohne Website-Befund bekommt gap_3 = "", nicht
einen aufgefuellten Standardsatz. Lieber zwei echte Stichpunkte als drei, von denen
einer erfunden ist.

Usage:
  python3 enrich_cohort_findings.py runs/locksmith-bedford [--no-firecrawl] [--limit N]
  python3 enrich_cohort_findings.py --self-check
"""
from __future__ import annotations
import argparse, csv, json, os, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_lead_findings import build  # noqa: E402
from markt_umfeld import market_context  # noqa: E402
from dedupe_leads import DATE_TAG  # noqa: E402
from themes import bundle  # noqa: E402

EXTRA_COLS = ["good_1", "good_2", "gap_1", "gap_2", "gap_3", "verdict", "gbp_score",
              "site_score", "score_line", "limits_line", "needs_deeper", "site_finding",
              "findings_json"]


def bullet(f: dict) -> str:
    """Ein Stichpunkt aus fact und means, exakt in der Form aus markt_copy.md.

    "no booking link" + "whoever does find you has to dial"
      -> "no booking link, so whoever does find you has to dial"

    Der Verbinder entfaellt, wenn der Fakt fuer sich steht ("134 reviews at 4.9, second
    in town"), also wenn means nichts Neues hinzufuegt. Kein Modell, keine Deutung.
    """
    fact = (f.get("fact") or "").strip().rstrip(".")
    means = (f.get("means") or "").strip().rstrip(".")
    if not fact:
        return ""
    if not means or means.lower() in fact.lower():
        return fact
    return f"{fact}, so {means}"


def enrich_row(row: dict, place: dict, allow_firecrawl: bool,
               places: list | None = None, niche: str = "") -> dict:
    # Ohne die Kohorte beschreibt jeder Befund den Betrieb isoliert -- und alles, was er
    # ueber sich selbst liest, kennt er schon. Der Vergleich ist das Einzige, was er nicht
    # nachsehen kann, also geht er in JEDEN Befund.
    market = market_context(places, place) if places else None
    r = build(place, market=market, allow_firecrawl=allow_firecrawl, niche=niche)
    goods = [f for f in r["_all"]["gbp"] + r["_all"]["site"] if f["kind"] == "good"]
    gaps = [f for f in r["_all"]["gbp"] + r["_all"]["site"] if f["kind"] == "gap"]
    goods.sort(key=lambda f: -f["strength"])
    gaps.sort(key=lambda f: -f["strength"])

    out = dict(row)
    # Zwei Punkte je Seite, jeder eine Lage statt eines Einzelbefunds (Luka, 27.07.).
    # gap_3 bleibt als Spalte bestehen, damit die alte Vorlage nicht bricht, wird aber
    # nicht mehr befuellt -- fuenf Stichpunkte lesen sich wie eine Pruefliste.
    all_f = r["_all"]["gbp"] + r["_all"]["site"]
    gb, gp = bundle(all_f, "good", 2), bundle(all_f, "gap", 2)
    for i in (1, 2):
        out[f"good_{i}"] = gb[i - 1] if len(gb) >= i else ""
        out[f"gap_{i}"] = gp[i - 1] if len(gp) >= i else ""
    out["gap_3"] = ""
    site_gaps = [f for f in r["_all"]["site"] if f["kind"] == "gap"]
    out["site_finding"] = bullet(site_gaps[0]) if site_gaps else ""
    out["verdict"] = r.get("verdict") or ""
    for k in ("gbp_score", "site_score"):
        out[k] = "" if r.get(k) is None else r[k]
    out["score_line"] = r.get("score_line") or ""
    out["limits_line"] = r.get("limits_line") or ""
    out["needs_deeper"] = "1" if r.get("needs_deeper") else ""
    out["findings_json"] = json.dumps(r["findings"], ensure_ascii=False)
    return out


def self_check():
    # exakt die Form aus dem gerenderten Beispiel in markt_copy.md
    got = bullet({"fact": "no booking link", "means": "whoever does find you has to dial"})
    assert got == "no booking link, so whoever does find you has to dial", got
    # ein Fakt, der fuer sich steht, bekommt keinen angehaengten Nebensatz
    assert bullet({"fact": "134 reviews at 4.9, second in town", "means": ""}) == \
        "134 reviews at 4.9, second in town"
    # leere Eingabe erzeugt nichts, niemals einen Fuellsatz
    assert bullet({}) == "" and bullet({"fact": "", "means": "x"}) == ""

    place = {"title": "X", "website": "", "city": "Leeds", "categoryName": "Locksmith",
             "reviewsCount": 4, "totalScore": 4.1, "categories": ["Locksmith"]}
    row = enrich_row({"business_name": "X"}, place, allow_firecrawl=False)
    assert row["site_finding"] == "", "ohne Website kein Website-Befund"
    assert all(c in row for c in EXTRA_COLS), row.keys()
    # nicht belegte Stichpunkte bleiben leer statt aufgefuellt
    assert row["gap_3"] == "" or row["gap_3"], row
    print("self-check ok")


def push_to_db(rows, apply: bool):
    """Findings nach industry_operators.web_signals. Die CSV ist danach ableitbar.

    Ohne diesen Schritt lebt die Personalisierung nur in einer Datei, die export_cohort
    beim naechsten Lauf ueberschreibt.
    """
    import urllib.parse, urllib.request
    sys.path.insert(0, HERE)
    from dedupe_leads import _supabase
    url, key = _supabase()
    hdr = {"apikey": key, "Authorization": f"Bearer {key}"}

    payload = [(r["place_id"], {
        "good": [r[k] for k in ("good_1", "good_2") if r.get(k)],
        "gaps": [r[k] for k in ("gap_1", "gap_2", "gap_3") if r.get(k)],
        "site_finding": r.get("site_finding") or "",
        "verdict": r.get("verdict") or "",
        "scores": {"gbp": r.get("gbp_score"), "site": r.get("site_score"),
                   "line": r.get("score_line") or "", "limits": r.get("limits_line") or "",
                   "deeper": bool(r.get("needs_deeper"))},
        "findings": json.loads(r.get("findings_json") or "[]"),
        "built": DATE_TAG,
    }) for r in rows if r.get("place_id")]

    if not apply:
        print(f"[dry-run] {len(payload)} Zeilen wuerden web_signals bekommen. Mit --apply schreiben.")
        return

    # Ein PATCH auf ein JSONB-Feld ERSETZT es. Unter web_signals.mail liegen die fertig
    # geschriebenen Mail-Variablen aus batch_briefs -- ohne diesen Schritt waeren die bei
    # jedem Findings-Lauf still weg, und zwar genau bei den Leads, an denen am meisten
    # Arbeit haengt. Deshalb erst lesen, dann zusammenfuehren.
    # Frueher wurden dafuer ALLE betroffenen place_ids per `in.(...)` abgefragt, in Bloecken
    # zu 200. Das ergab eine URL von ~6 kB und PostgREST antwortete 400 -- nach dem teuersten
    # Teil des Laufs, und weil erst am Ende geschrieben wird, war die ganze Arbeit weg.
    # Es braucht die Abfrage gar nicht: gefragt ist nur, WER ueberhaupt Mail-Variablen hat,
    # und das sind eine Handvoll Zeilen. Eine Abfrage, kein Block, keine lange URL.
    # BEWAHRT WIRD ALLES, WAS DIESER LAUF NICHT SELBST SCHREIBT -- nicht namentlich `mail`.
    # Die erste Fassung schuetzte genau ein Feld, und am 28.07. hat sie prompt das naechste
    # verloren: `rank` (die Google-Maps-Position, Grundlage des ersten Satzes der neuen
    # Mail) war nach einem Findings-Lauf still weg, eine Stunde nachdem sie gezogen wurde.
    # Eine Liste zu pflegen, in die jedes neue Feld eingetragen werden muss, ist die
    # falsche Bauform: vergessen wird sie lautlos. Jetzt gewinnt dieser Lauf nur ueber
    # SEINE Schluessel, der Rest der Zeile bleibt stehen.
    alt, off = {}, 0
    while True:
        q = (f"{url}/rest/v1/industry_operators?select=place_id,web_signals"
             f"&web_signals=neq.%7B%7D&order=place_id&limit=1000&offset={off}")
        seite = json.load(urllib.request.urlopen(
            urllib.request.Request(q, headers=hdr), timeout=90))
        for r in seite:
            alt[r["place_id"]] = r.get("web_signals") or {}
        off += 1000
        if len(seite) < 1000:
            break
    bewahrt, fehler = 0, []
    for i, (pid, sig) in enumerate(payload):
        fremd = {k: v for k, v in (alt.get(pid) or {}).items() if k not in sig}
        if fremd:
            sig.update(fremd)
            payload[i] = (pid, sig)
            bewahrt += 1
        # Der Score gehoert AUCH in die Spalte, nicht nur ins JSONB. Nur die Spalte laesst
        # sich sortieren, filtern und vom Portal lesen -- ohne sie bleibt jeder Vergleich
        # zwischen Betrieben ein Python-Lauf statt einer Abfrage.
        felder = {"web_signals": sig}
        # NICHT `is not None` pruefen: enrich_row schreibt "" fuer "nicht messbar" (Erbe der
        # CSV-Spalten), und ein leerer String ist nicht None. Postgres antwortet darauf mit
        # `invalid input syntax for type integer: ""` -- ein 400, das zwei komplette Laeufe
        # gekostet hat, weil niemand den Rumpf der Antwort gelesen hat.
        if isinstance(sig["scores"].get("gbp"), (int, float)):
            felder["setup_score"] = int(sig["scores"]["gbp"])
        req = urllib.request.Request(
            f"{url}/rest/v1/industry_operators?place_id=eq.{urllib.parse.quote(pid, safe='')}",
            data=json.dumps(felder).encode(), method="PATCH",
            headers={**hdr, "Content-Type": "application/json", "Prefer": "return=minimal"})
        try:
            urllib.request.urlopen(req, timeout=30).read()
        except urllib.error.HTTPError as e:
            # Zweimal ist ein Lauf an einem nackten "HTTP Error 400" gestorben, ohne dass
            # erkennbar war WARUM oder BEI WEM. Supabase schickt die Begruendung im Rumpf
            # mit, wir haben sie weggeworfen. Ein einzelner fauler Datensatz darf ausserdem
            # nicht 3.593 andere aufhalten -- er wird benannt und uebersprungen.
            grund = (e.read() or b"").decode("utf-8", "replace")[:300]
            fehler.append((pid, e.code, grund))
            continue
    if fehler:
        print(f"  {len(fehler)} Zeilen abgelehnt, erste drei:")
        for pid, code, grund in fehler[:3]:
            print(f"    {pid}  HTTP {code}  {grund}")
    print(f"web_signals geschrieben: {len(payload) - len(fehler)} Zeilen "
          f"({bewahrt} mit fremden Feldern wie mail/rank, die erhalten blieben)")


def aus_der_db(a):
    """Der ganze Bestand statt eines Run-Ordners.

    Seit dem Detail-Backfill traegt `industry_operators.raw` dasselbe Apify-Objekt, aus dem
    die Run-Ordner bestehen. Der Umweg ueber CSV und raw.json ist damit hinfaellig -- und
    er war der Grund, warum die Findings immer nur fuer die eine gerade bearbeitete Region
    existierten. Verglichen wird weiter INNERHALB der Region: eine Kohorte ueber 61
    Regionen hinweg ist kein gemeinsamer Markt.
    """
    import urllib.parse, urllib.request
    sys.path.insert(0, HERE)
    from dedupe_leads import _supabase
    url, key = _supabase()
    hdr = {"apikey": key, "Authorization": f"Bearer {key}"}

    leads, off = [], 0
    while True:
        q = (f"{url}/rest/v1/industry_operators?select=place_id,website,region,raw"
             f"&niche=eq.{urllib.parse.quote(a.niche)}&pipeline_status=neq.disqualified"
             f"&order=place_id&limit=1000&offset={off}")
        seite = json.load(urllib.request.urlopen(urllib.request.Request(q, headers=hdr),
                                                 timeout=120))
        leads += seite
        off += 1000
        if len(seite) < 1000:
            break
    if a.limit:
        leads = leads[:a.limit]

    nach_region = {}
    for x in leads:
        nach_region.setdefault(x["region"], []).append(x["raw"] or {})
    print(f"{len(leads)} Leads aus der DB, {len(nach_region)} Regionen, hole Websites ...")

    def eine(x):
        return enrich_row({"place_id": x["place_id"], "website": x.get("website") or ""},
                          x["raw"] or {"website": x.get("website") or ""},
                          not a.no_firecrawl, nach_region.get(x["region"]), a.niche)

    # REGIONSWEISE schreiben, nicht am Ende in einem Rutsch. Am 27.07. starb ein Lauf ueber
    # alle 3.593 beim allerletzten Schritt an einem HTTP 400 -- die Findings waren fertig
    # gerechnet, ~630 Firecrawl-Credits verbraucht, und nichts davon in der Datenbank. Ein
    # Absturz darf hoechstens eine Region kosten.
    out = []
    regionen = sorted(nach_region, key=lambda r: -len(nach_region[r]))
    for i, reg in enumerate(regionen, 1):
        teil = [x for x in leads if x["region"] == reg]
        if not teil:
            continue
        fertig = list(ThreadPoolExecutor(max_workers=a.workers).map(eine, teil))
        out += fertig
        if a.push:
            push_to_db(fertig, a.apply)
        print(f"  [{i}/{len(regionen)}] {reg}: {len(fertig)} Leads, "
              f"{sum(1 for r in out if r['gap_1'])} mit Luecke bisher", flush=True)

    mit_site = sum(1 for r in out if r["site_finding"])
    mit_gap = sum(1 for r in out if r["gap_1"])
    mit_good = sum(1 for r in out if r["good_1"])
    leer = sum(1 for r in out if not r["gap_1"] and not r["good_1"])
    print(f"  mit Website-Luecke:      {mit_site}/{len(out)}")
    print(f"  mit mindestens 1 Luecke: {mit_gap}/{len(out)}")
    print(f"  mit mindestens 1 Gutem:  {mit_good}/{len(out)}")
    print(f"  ohne jeden Befund:       {leer}/{len(out)}  <- fuer die gibt es keine Mail")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rundir", nargs="?")
    ap.add_argument("--from-db", action="store_true",
                    help="ueber den ganzen Bestand statt eines Run-Ordners (braucht den Detail-Backfill)")
    ap.add_argument("--push", action="store_true", help="Findings nach Supabase (web_signals)")
    ap.add_argument("--apply", action="store_true", help="mit --push: wirklich schreiben")
    ap.add_argument("--raw", default="", help="raw.json der Region (Standard: aus dem Ordnernamen)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--no-firecrawl", action="store_true")
    ap.add_argument("--niche", default="locksmith", help="steuert das Branchenprofil in trades.py")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        self_check()
        return 0
    if a.from_db:
        return aus_der_db(a)
    if not a.rundir:
        ap.error("rundir, --from-db oder --self-check")

    cv = os.path.join(a.rundir, "cohort_vars.csv")
    all_rows = list(csv.DictReader(open(cv, encoding="utf-8")))
    # --limit begrenzt die ARBEIT, nicht die Datei. Vorher wurde nur der bearbeitete
    # Ausschnitt zurueckgeschrieben und der Rest der Kohorte war weg -- ein Testlauf
    # mit --limit 10 hat 15 Zeilen auf 10 gekuerzt.
    rows = all_rows[:a.limit] if a.limit else all_rows

    # Die Place-Objekte tragen die GBP-Signale; die CSV traegt nur die Kennung.
    raw = a.raw or os.path.join(HERE, "output",
                                os.path.basename(a.rundir).replace("locksmith-", "") + "-region-locksmith",
                                "raw.json")
    by_id = {}
    if os.path.exists(raw):
        for p in json.load(open(raw, encoding="utf-8")):
            if isinstance(p, dict) and p.get("placeId"):
                by_id[p["placeId"]] = p
    else:
        print(f"[warn] {raw} nicht gefunden — ohne Place-Objekte gibt es keine GBP-Findings")

    missing = sum(1 for r in rows if r.get("place_id") not in by_id)
    print(f"{len(rows)} Zeilen, {len(rows)-missing} mit Place-Objekt, {missing} ohne")

    # NUR die Kohorte, nicht die ganze raw.json. Sonst rechnet der Vergleich gegen 24
    # Places, waehrend die Mail von 12 spricht -- zwei Zahlen im selben Text, die sich
    # widersprechen, und der Leser zaehlt nach.
    cohort_pids = {r.get('place_id') for r in all_rows if r.get('place_id')}
    cohort_places = [p for pid, p in by_id.items() if pid in cohort_pids]

    out = list(ThreadPoolExecutor(max_workers=a.workers).map(
        lambda r: enrich_row(r, by_id.get(r.get("place_id"), {"website": r.get("website") or ""}),
                             not a.no_firecrawl, cohort_places, a.niche), rows))

    cols = list(all_rows[0].keys()) + [c for c in EXTRA_COLS if c not in all_rows[0]]
    done = {id(r): o for r, o in zip(rows, out)}
    with open(cv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(done.get(id(r), r) for r in all_rows)

    if a.push:
        push_to_db(out, a.apply)

    filled = sum(1 for r in out if r["gap_1"])
    three = sum(1 for r in out if r["gap_3"])
    goods = sum(1 for r in out if r["good_1"])
    print(f"geschrieben: {cv}")
    print(f"  mit mindestens einer Luecke: {filled}/{len(out)}")
    print(f"  mit drei Luecken (Variante B voll): {three}/{len(out)}")
    print(f"  mit mindestens einem Positiven:     {goods}/{len(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
