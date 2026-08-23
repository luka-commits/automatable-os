#!/usr/bin/env python3
"""build_lead_findings.py — Rohscrape rein, fertige Mail-Bausteine raus.

Das Stueck, das die Pipeline zusammenhaengt. Vorher lagen alle Teile einzeln da:
dedupe_leads entdoppelt, findings.py liest das GBP, web_findings die Website -- aber
niemand rief sie nacheinander auf. Der Social-Riegel in web_findings war deshalb toter
Code: er braucht ctx['url'], und es gab keinen Aufrufer, der ihn setzt.

Ablauf je Lead:
  1. Entdoppeln + Ketten raus (dedupe_leads, ueber ALLE Regionen gemeinsam)
  2. GBP-Findings aus dem Apify-Place-Objekt (findings.py)
  3. Website holen: nackter HTTP-Abruf, bei Sperre/Leere Firecrawl
     gemessen 60% direkt, Firecrawl rettete 12 von 12 blockierten
  4. Website-Findings (web_findings) -- MIT url, damit ein Facebook-Profil genau einen
     wahren Befund erzeugt statt fuenf falscher
  5. Drei Findings waehlen, in der psychologischen Reihenfolge aus PIPELINE.md:
     erst ein Positives, dann eine sofort pruefbare Luecke, dann eine mit Geldfolge

Ausgabe: eine JSON-Zeile je Lead mit genau den Bausteinen, die der Generator
formulieren darf. Er bekommt fertige fact/means-Paare und fuegt nichts hinzu.

Usage:
  python3 build_lead_findings.py output/*-locksmith/raw.json --out runs/locksmith.jsonl
  python3 build_lead_findings.py ... --limit 20 --no-firecrawl
  python3 build_lead_findings.py --self-check
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, socket, ssl, subprocess, sys, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(__file__.rsplit("/", 1)[0]))
import findings as gbp_findings          # noqa: E402
import web_findings as web               # noqa: E402
from dedupe_leads import dedupe          # noqa: E402
import trades                            # noqa: E402
import benchmark                         # noqa: E402
from verdict import verdict              # noqa: E402
import score as scoring                  # noqa: E402

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


class _Redirect308(urllib.request.HTTPRedirectHandler):
    """Python 3.9 folgt 308 nicht -- die Seite gilt dann als unerreichbar und wandert an
    Firecrawl, obwohl ein simples Folgen genuegt haette. Gemessen: 2 von 80 Sites.

    Es reicht NICHT, http_error_308 zu setzen: `redirect_request` prueft den Code noch
    einmal gegen eine feste Liste ohne 308 und wirft dort. Deshalb wird der Code fuer die
    Pruefung auf 307 gedreht -- semantisch dasselbe (Methode und Body bleiben erhalten),
    nur permanent.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(req, fp, 307 if code == 308 else code,
                                        msg, headers, newurl)

    http_error_308 = urllib.request.HTTPRedirectHandler.http_error_301


OPENER = urllib.request.build_opener(_Redirect308,
                                     urllib.request.HTTPSHandler(context=CTX))


CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_sitecache")


def _cache_pfad(url: str) -> str:
    return os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest() + ".html")


def fetch(url: str, allow_firecrawl: bool = True, cache: bool = True):
    """-> (html, quelle). Leeres html heisst: wir wissen nichts, und behaupten nichts.

    Abgerufenes HTML landet auf der Platte. Am 27.07. ist ein Lauf ueber alle 3.593 Leads
    beim SCHREIBEN gestorben, nachdem er ~630 Firecrawl-Credits verbraucht hatte -- und weil
    nichts zwischengespeichert war, war die Arbeit weg und das Guthaben auch. Ein Abruf, den
    wir schon bezahlt haben, wird kein zweites Mal bezahlt.
    """
    # newline="" auf BEIDEN Seiten: ohne das macht Pythons Universal-Newline-Modus beim
    # Lesen aus \r\n ein \n, und der Cache liefert 11 Zeichen weniger als der Frisch-Abruf
    # (gemessen an einer echten Seite). Fuer die Pruefungen harmlos, aber dann haengt das
    # Ergebnis davon ab, ob eine Seite schon mal geholt wurde -- genau die Art Abweichung,
    # die spaeter niemand mehr zuordnen kann.
    if cache:
        p = _cache_pfad(url)
        try:
            with open(p, encoding="utf-8", newline="") as fh:
                gespeichert = fh.read()
            if gespeichert:
                return gespeichert, "cache"
        except OSError:
            pass
    html, quelle = _hole(url, allow_firecrawl)
    if cache and html:
        os.makedirs(CACHE, exist_ok=True)
        try:
            with open(_cache_pfad(url), "w", encoding="utf-8", newline="") as fh:
                fh.write(html)
        except OSError:
            pass                      # ein voller Datentraeger darf den Lauf nicht stoppen
    return html, quelle


def _hole(url: str, allow_firecrawl: bool = True):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                   "Accept": "text/html,application/xhtml+xml"})
        with OPENER.open(req, timeout=20) as r:
            html = r.read(500_000).decode("utf-8", "replace")
        # Eine JS-Seite liefert 200 und eine leere Huelle. Wenig Text heisst hier nicht
        # "duenne Seite", sondern "nicht gerendert" -- der Unterschied entscheidet, ob wir
        # etwas behaupten duerfen.
        if len(re.findall(r"[A-Za-zÄÖÜäöüß]{3,}", re.sub(r"<[^>]+>", " ", html))) >= 80:
            return html, "http"
        reason = "leer"
    except urllib.error.HTTPError as e:
        reason = "blocked" if e.code in (401, 403, 429) else f"http{e.code}"
    except urllib.error.URLError as e:
        # Der Namensdienst kennt die Domain nicht mehr -- gemessen 68% aller URLError.
        # Das ist der einzige Fehler, aus dem wir "die Seite ist tot" ableiten duerfen:
        # ein Timeout oder ein Verbindungsabbruch kann auch an uns liegen.
        reason = "dns-tot" if isinstance(e.reason, socket.gaierror) else type(e).__name__
    except Exception as e:
        reason = type(e).__name__

    # Eine Domain, die der Namensdienst nicht kennt, kann auch Firecrawl nicht abrufen --
    # an sechs toten Domains geprueft, alle sechs kamen leer zurueck. Der Credit waere weg
    # und das Ergebnis dasselbe. Betrifft ~200 der 3593 Leads.
    if not allow_firecrawl or reason == "dns-tot":
        return "", reason
    try:
        r = subprocess.run(["firecrawl", "scrape", url, "--format", "rawHtml"],
                           capture_output=True, text=True, timeout=120)
        blob = r.stdout or ""
        try:
            d = json.loads(blob)
            html = d.get("rawHtml") or (d.get("data") or {}).get("rawHtml") or ""
        except Exception:
            html = blob if "<" in blob else ""
        return (html, "firecrawl") if html.strip() else ("", f"{reason}+fc-leer")
    except Exception:
        return "", f"{reason}+fc-fehler"


def pick_three(gbp: list, site: list) -> list:
    """Die psychologische Reihenfolge aus PIPELINE.md, nicht die Stärkeliste.

    Erst ein Positives (senkt die Abwehr, und wir liefern ein Audit statt einer
    Mängelliste), dann die stärkste Lücke, dann die zweitstärkste. Gibt es kein
    Positives, wird KEINES erfunden -- dann sind es drei Lücken.
    Aus jedem Bereich hoechstens zwei, damit die Mail nicht wie ein Profil-Audit klingt.
    """
    all_f = [dict(f, area="gbp") for f in gbp] + [dict(f, area="site") for f in site]
    goods = sorted([f for f in all_f if f["kind"] == "good"], key=lambda f: -f["strength"])
    gaps = sorted([f for f in all_f if f["kind"] == "gap"], key=lambda f: -f["strength"])

    out = []
    if goods:
        out.append(goods[0])
    per_area, gesehen = {}, {f["check"] for f in out}
    for f in gaps:
        if len(out) >= 3:
            break
        # Ein Check liefert manchmal zwei Findings -- web-schema etwa einmal fuer das
        # LocalBusiness-Markup und einmal fuer die Bewertungen. Beide in einer Mail sind
        # zwei Stichpunkte ueber dieselbe Sache, und der Score zaehlt sie ohnehin nur einmal.
        if f["check"] in gesehen or per_area.get(f["area"], 0) >= 2:
            continue
        out.append(f)
        gesehen.add(f["check"])
        per_area[f["area"]] = per_area.get(f["area"], 0) + 1
    return out[:3]



# HERAUSGELOEST am 23.08.2026: `NACHBARN`, `WEIT_KM`, `REGION_MIN`,
# `nachbarn_fuer_intro`, `nearest_cohort` und `market_context` leben jetzt in
# `markt_umfeld.py`. Sie waren der einzige Grund, warum die laufende Kampagne
# diese Datei und damit `findings`/`web_findings`/`score` mitziehen musste.
from markt_umfeld import (NACHBARN, WEIT_KM, REGION_MIN,  # noqa: F401,E402
                          nachbarn_fuer_intro, nearest_cohort, market_context)


def build(place: dict, market: dict | None = None, allow_firecrawl: bool = True,
          niche: str = "") -> dict:
    url = (place.get("website") or "").strip()
    town = (place.get("city") or "").strip()
    cat = (place.get("categoryName") or "").strip()

    bench = benchmark.load(niche)
    # niche MUSS durch: ohne sie faellt der Gewerks-Filter in gbp-services auf "nicht
    # filtern" zurueck, und dann steht "kindness" wieder als eintragbare Leistung im Text.
    gbp = trades.apply(gbp_findings.evaluate(place, market=market or {}, bench=bench,
                                             niche=niche), niche)

    html, source = "", "keine-url"
    if url:
        if web.is_own_site(url):
            html, source = fetch(url, allow_firecrawl)
        else:
            source = "social-profil"      # nicht abrufen, der Befund steht ohne Abruf fest
    site = trades.apply(web.evaluate(html, {"town": town, "service": f"{cat} {town}".strip(),
                                            "rating": place.get("totalScore"), "url": url,
                                            "phone": place.get("phone"),
                                            "site_dead": source == "dns-tot"}),
                        niche, is_site=True)

    # Der Score zaehlt NUR, was dieser Scrape beantworten konnte. Ein fehlendes Datenfeld
    # ist kein Abzug, sonst schicken wir ihm eine Zahl, die unsere Luecke bestraft.
    m_gbp, m_site = scoring.measured_gbp(place), scoring.measured_site(html, url)
    gbp_pts, gbp_costly = scoring.score(gbp, m_gbp, scoring.GBP_WEIGHTS)
    site_pts, site_costly = scoring.score(site, m_site, scoring.SITE_WEIGHTS)

    return {
        "name": place.get("title") or "",
        "town": town, "website": url, "place_id": place.get("placeId") or "",
        "site_source": source,
        "gbp_score": gbp_pts, "site_score": site_pts,
        # OHNE den Site-Score (Luka, 28.07.: "die website dabei so ein bisschen
        # rauslassen"). Die Mail redet ueber das Google-Profil, weil der Auftrag eines
        # Notdienstes ueber den Maps-Eintrag laeuft und nicht ueber die Seite -- eine
        # zweite Zahl ueber die Website macht aus dem einen Thema wieder zwei.
        # `summary` kann den Site-Teil weiterhin, der Report nutzt ihn.
        "score_line": scoring.summary(gbp_pts, None, len(m_gbp), len(m_site)),
        "score_costly": (gbp_costly + site_costly)[:3],
        "needs_deeper": scoring.needs_deeper(gbp + site),
        # Was der Scrape nicht beantworten konnte, wird in der Mail zum Grund fuer den
        # Report -- statt dass wir es stillschweigend als Mangel behaupten.
        "limits_line": scoring.limits_line(
            scoring.limits(m_gbp, scoring.GBP_WEIGHTS, 2)),
        "findings": pick_three(gbp, site),
        # der Verdict sieht ALLE Befunde, nicht nur die drei in der Mail -- die Asymmetrie
        # steckt oft genau in dem, was es nicht in die Stichpunkte geschafft hat.
        "verdict": verdict(gbp + site,
                           bench_band=benchmark.standing(
                               int(place.get("reviewsCount") or 0), bench)[0]),
        "_all": {"gbp": gbp, "site": site},
    }


def self_check():
    fb = {"title": "Cobbler", "website": "https://facebook.com/cobbler", "city": "Leeds",
          "categoryName": "Locksmith", "reviewsCount": 12, "totalScore": 4.6,
          "categories": ["Locksmith"], "imagesCount": 3, "openingHours": [{}]}
    r = build(fb, allow_firecrawl=False)
    assert r["site_source"] == "social-profil", r["site_source"]
    sites = r["_all"]["site"]
    assert len(sites) == 1 and sites[0]["check"] == "web-own-site", sites
    assert r["findings"], "ein Social-Lead muss trotzdem Bausteine haben (GBP)"

    nosite = {"title": "X", "website": "", "city": "Leeds", "categoryName": "Locksmith",
              "reviewsCount": 4, "totalScore": 4.1, "categories": ["Locksmith"]}
    r2 = build(nosite, allow_firecrawl=False)
    assert r2["_all"]["site"] == [], "ohne Website wird nichts ueber die Website behauptet"
    assert r2["site_source"] == "keine-url"

    # hoechstens drei, und ein Positives fuehrt wenn es eins gibt
    picked = pick_three([{"check": "a", "kind": "good", "fact": "f", "means": "m", "strength": 30},
                         {"check": "b", "kind": "gap", "fact": "f", "means": "m", "strength": 90},
                         {"check": "c", "kind": "gap", "fact": "f", "means": "m", "strength": 80},
                         {"check": "d", "kind": "gap", "fact": "f", "means": "m", "strength": 70}], [])
    assert len(picked) == 3 and picked[0]["kind"] == "good", picked
    # kein Positives -> keines erfinden
    only_gaps = pick_three([{"check": "b", "kind": "gap", "fact": "f", "means": "m", "strength": 90}], [])
    assert all(f["kind"] == "gap" for f in only_gaps), only_gaps
    print("self-check ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("raw", nargs="*")
    ap.add_argument("--out", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--no-firecrawl", action="store_true")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        self_check()
        return 0
    if not a.raw:
        ap.error("raw.json-Dateien oder --self-check")

    places = []
    for p in a.raw:
        d = json.load(open(p, encoding="utf-8"))
        places += d if isinstance(d, list) else (d.get("items") or [])
    leads, _ = dedupe(places)
    if a.limit:
        leads = leads[:a.limit]
    print(f"{len(places)} Zeilen -> {len(leads)} Leads, hole Websites ...")

    rows = list(ThreadPoolExecutor(max_workers=a.workers).map(
        lambda p: build(p, allow_firecrawl=not a.no_firecrawl), leads))

    from collections import Counter
    src = Counter(r["site_source"] for r in rows)
    with_site = sum(1 for r in rows if r["_all"]["site"])
    three = sum(1 for r in rows if len(r["findings"]) == 3)
    print(f"\nQuelle der Website-Daten: {dict(src)}")
    print(f"Leads mit Website-Befund: {with_site}/{len(rows)} ({round(100*with_site/max(len(rows),1))}%)")
    print(f"Leads mit vollen drei Bausteinen: {three}/{len(rows)}")

    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"geschrieben: {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
