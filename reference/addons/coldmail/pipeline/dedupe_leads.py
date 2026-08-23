#!/usr/bin/env python3
"""dedupe_leads.py — von Google-Maps-Zeilen zu anschreibbaren Betrieben.

Google Maps liefert einen Eintrag pro STANDORT, nicht pro FIRMA. In der
Locksmith-Liste steht Timpson 1.877 Mal, jede Filiale eine eigene Zeile, alle mit
derselben Website. Ohne diesen Schritt schreibt die Kampagne 1.877 Mal denselben
Satz ("ich habe mir eure Website angeschaut") an dieselbe Firma. Das ist kein
Personalisierungsfehler, das ist Spam, und es verbrennt die Sende-Domain.

Gemessen an 7.291 Locksmith-Places (2026-07-25):

    7.291 Zeilen  ->  3.984 verschiedene Domains
                  ->  3.948 nach Abzug der Social-Profile
                  ->  3.930 nach Abzug der Ketten

Die grosse Zahl ist Schritt 1 und kostet KEINEN Betrieb: es sind Dubletten
derselben Firma. Der Kettenfilter kostet 18 von 3.984 Domains, also 0,5%.

WARUM SCHWELLE 10: 91% der Domains haben genau einen Standort, und drei Domains
tragen ein Drittel aller Zeilen. Jede Schwelle zwischen 10 und 25 trifft dieselben
Marken; 10 ist davon die sichere, weil sie keinen Handwerker mit drei Transportern
erfasst. Die Asymmetrie entscheidet: eine Kette anzuschreiben kostet einen Send,
einen wachsenden Lokalbetrieb wegzuwerfen kostet einen Kunden.

NIE LOESCHEN, IMMER BUCKETN — dieselbe Regel wie ingest_to_supabase.py. Alles
Aussortierte geht mit Grund in eine beschriftete Nachbardatei.

WO ES HINGEHOERT: vor Stufe 4 (Kontakt). Sonst laesst MillionVerifier Adressen
fuer 3.361 Zeilen pruefen, die anschliessend ohnehin wegfallen.

UEBER ALLE REGIONEN AUF EINMAL, nie pro Datei. Gemessen: bei regionaler Zaehlung
rutschen 220 Ketten-Standorte durch, weil eine Kette in einer einzelnen Region
unter der Schwelle bleibt -- Keytek in 38 von 62 Regionen, Timpson in 15. Und die
Entdoppelung braucht denselben Blick, sonst ergibt eine Domain in drei Regionen
drei Leads. Deshalb nimmt die CLI mehrere Dateien und poolt sie.

Usage:
  python3 dedupe_leads.py output/*-locksmith/raw.json [--chain-threshold 10] [--dry-run]
  python3 dedupe_leads.py --self-check
"""
from __future__ import annotations
import argparse, datetime, json, re, sys, urllib.parse
from collections import defaultdict

DATE_TAG = datetime.date.today().isoformat()

CHAIN_THRESHOLD = 10


# Plattformen, auf denen sich VIELE Firmen einen Host teilen. Hier identifiziert erst der
# Pfad den Betrieb: facebook.com/bobslocks und facebook.com/janeslocks sind zwei Firmen.
SHARED_HOST = ("facebook.com", "instagram.com", "linktr.ee", "wa.me", "t.me",
               "yelp.", "nextdoor.", "checkatrade.com", "yell.com", "trustpilot.",
               "linkedin.com", "twitter.com", "x.com", "sites.google.com")

# Baukasten-Subdomains: der Betrieb hat eine eigene Subdomain, aber keine eigene Domain.
# Der Host identifiziert ihn eindeutig, es ist nur keine echte Website.
BUILDER_HOST = ("wixsite.com", "business.site", "godaddysites.com", "weebly.com",
                "squarespace.com", "jimdosite.com", "webnode.")


def domain_of(place: dict) -> str:
    w = (place.get("website") or "").strip()
    if not w.startswith("http"):
        return ""
    try:
        return re.sub(r"^(www|m)\.", "", w.split("/")[2].lower())
    except IndexError:
        return ""


def is_shared_host(host: str) -> bool:
    return any(s in host for s in SHARED_HOST)


def is_builder(host: str) -> bool:
    return any(s in host for s in BUILDER_HOST)


def business_key(place: dict) -> str:
    """Was DIESEN Betrieb identifiziert — die Grundlage jeder Dubletten-Erkennung.

    Eigene Domain  -> der Host. Alle Filialen einer Firma teilen ihn, genau das wollen wir.
    Geteilter Host -> Host PLUS Pfad. Sonst wuerden 68 verschiedene Facebook-Seiten zu einer
                      Firma verschmelzen; gemessen sind es 127 Places mit 125 verschiedenen
                      Profilen, also praktisch durchweg eigenstaendige Betriebe. Sie als
                      Dubletten zu verwerfen haette 125 echte Leads gekostet, ausgerechnet
                      die besten fuer ein Website-Angebot.
    """
    host = domain_of(place)
    if not host:
        return ""
    if is_shared_host(host):
        w = (place.get("website") or "").strip().lower()
        path = w.split(host, 1)[-1] if host in w else ""
        # Reihenfolge zaehlt: erst Query und Fragment weg, DANN der Schraegstrich. Andersherum
        # bleibt "/janeskeys/?ref=x" als "/janeskeys/" stehen und trennt sich von "/janeskeys".
        path = re.sub(r"[?#].*$", "", path).rstrip("/")
        return f"{host}{path}"
    return host


def _reviews(p: dict) -> int:
    n = p.get("reviewsCount")
    return int(n) if isinstance(n, (int, float)) else 0


def dedupe(places: list, chain_threshold: int = CHAIN_THRESHOLD):
    """-> (leads, dropped). `dropped` carries a reason per row, nothing is discarded."""
    by_key: dict[str, list] = defaultdict(list)
    leads, dropped = [], []

    for p in places:
        if not isinstance(p, dict):
            continue
        key = business_key(p)
        if not key:
            dropped.append((p, "keine Website im Profil"))
            continue
        by_key[key].append(p)

    for key, group in by_key.items():
        host = key.split("/")[0]
        # Eine Kette teilt sich EINE eigene Domain. Auf einem geteilten Host ist jede
        # Seite eine andere Firma, dort waere die Schwelle sinnlos; und ein
        # Baukasten-Betrieb hat per Definition genau einen Standort.
        if not is_shared_host(host) and not is_builder(host) and len(group) >= chain_threshold:
            for p in group:
                dropped.append((p, f"Kette: {len(group)} Standorte auf {host}"))
            continue
        # Ein Lead je Domain. Der mit den meisten Bewertungen ist der etablierteste
        # Standort und damit der plausibelste Ansprechpartner; bei Gleichstand entscheidet
        # der Name, damit derselbe Input immer denselben Lead ergibt.
        group.sort(key=lambda p: (-_reviews(p), (p.get("title") or "")))
        leads.append(group[0])
        for p in group[1:]:
            dropped.append((p, f"weiterer Eintrag desselben Betriebs ({key})"))

    leads.sort(key=lambda p: (p.get("title") or ""))
    return leads, dropped


def _supabase():
    """(url, key) aus der Portal-Env oder credentials.env. Kein Import-Zeit-Crash."""
    import os
    env = {}
    # `rsplit('/seo/')` ergab ausserhalb des alten seo/-Baums den ganzen Dateinamen
        # als Praefix und damit einen Pfad, der auf eine DATEI zeigte statt in einen
        # Ordner -- NotADirectoryError statt "keine Zugangsdaten". Der Portal-Pfad wird
        # jetzt nur genommen, wenn es diesen Baum ueberhaupt gibt (23.08.2026).
    kandidaten = [os.path.expanduser("~/.config/credentials.env")]
    if "/seo/" in __file__:
        kandidaten.insert(0, f"{__file__.rsplit('/seo/', 1)[0]}/seo/portal/.env.local")
    for p in kandidaten:
        try:
            for line in open(p, encoding="utf-8"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except FileNotFoundError:
            pass
    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or env.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or env.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit("[dedupe] keine Supabase-Zugangsdaten gefunden")
    return url, key


def run_supabase(niche: str, chain_threshold: int, apply: bool):
    """Entdoppelung auf dem BESTAND in industry_operators.

    Der Kettenfilter braucht den Gesamtblick, und der existiert erst, wenn alle Regionen
    eingelesen sind -- pro Regionsdatei rutschen 220 Ketten-Standorte durch. Supabase ist
    genau dieser Gesamtblick, deshalb laeuft der Schritt hier und nicht auf raw.json.

    Nichts wird geloescht: pipeline_status -> 'disqualified', Grund in crm_notes. Nur
    Zeilen, die noch auf 'scraped' stehen, werden angefasst -- wer schon kontaktiert ist,
    bleibt unberuehrt.
    """
    import urllib.request
    url, key = _supabase()
    hdr = {"apikey": key, "Authorization": f"Bearer {key}"}

    rows, offset = [], 0
    while True:
        q = (f"{url}/rest/v1/industry_operators?select=place_id,name,website,town,reviews,"
             f"pipeline_status&niche=eq.{niche}&limit=1000&offset={offset}")
        batch = json.load(urllib.request.urlopen(urllib.request.Request(q, headers=hdr), timeout=60))
        rows += batch
        if len(batch) < 1000:
            break
        offset += 1000
    print(f"{niche}: {len(rows)} Zeilen in Supabase")

    fresh = [r for r in rows if r.get("pipeline_status") == "scraped"]
    print(f"davon unberuehrt ('scraped'): {len(fresh)}")

    places = [{"title": r.get("name") or "", "website": r.get("website") or "",
               "city": r.get("town") or "", "reviewsCount": r.get("reviews") or 0,
               "placeId": r.get("place_id")} for r in fresh]
    leads, dropped = dedupe(places, chain_threshold)
    print(f"-> {len(leads)} Betriebe, {len(dropped)} Zeilen zu markieren")

    from collections import Counter
    for r, n in Counter(re.sub(r"\(.*\)|\d+", "", why).strip() for _, why in dropped).most_common():
        print(f"   {n:>5}  {r}")

    if not apply:
        print("\n[dry-run] nichts geschrieben. Mit --apply ausfuehren.")
        return 0

    done = 0
    for p, why in dropped:
        pid = p.get("placeId")
        if not pid:
            continue
        body = json.dumps({"pipeline_status": "disqualified",
                           "crm_notes": f"dedupe {DATE_TAG}: {why}"}).encode()
        req = urllib.request.Request(
            f"{url}/rest/v1/industry_operators?place_id=eq.{urllib.parse.quote(pid, safe='')}",
            data=body, method="PATCH",
            headers={**hdr, "Content-Type": "application/json", "Prefer": "return=minimal"})
        urllib.request.urlopen(req, timeout=30).read()
        done += 1
    print(f"markiert: {done} Zeilen als disqualified (Grund in crm_notes)")
    return 0


def self_check():
    tim = [{"title": f"Timpson {i}", "website": "https://timpson.co.uk/x",
            "reviewsCount": i} for i in range(12)]
    local = [{"title": "Bob Locks", "website": "https://boblocks.co.uk", "reviewsCount": 40},
             {"title": "Bob Locks North", "website": "https://boblocks.co.uk", "reviewsCount": 90}]
    none = [{"title": "No Site", "website": "", "reviewsCount": 3}]

    # DER FEHLER, DEN LUKA GEFUNDEN HAT: verschiedene Facebook-Seiten sind verschiedene
    # Firmen, keine Dubletten. Nach Host gruppiert waeren aus 68 Betrieben einer geworden;
    # gemessen sind es 127 Places mit 125 verschiedenen Profilen.
    fb = [{"title": "Bobs Locks", "website": "https://facebook.com/bobslocks", "reviewsCount": 5},
          {"title": "Janes Keys", "website": "https://facebook.com/janeskeys", "reviewsCount": 9},
          {"title": "Janes Keys", "website": "https://m.facebook.com/janeskeys/?ref=x", "reviewsCount": 2}]

    leads, dropped = dedupe(tim + local + fb + none)
    names = {p["title"] for p in leads}

    assert names == {"Bob Locks North", "Bobs Locks", "Janes Keys"}, names
    assert len(leads) == 3, leads
    # zwei verschiedene Facebook-Profile ueberleben BEIDE
    assert sum(1 for p in leads if "facebook" in p["website"]) == 2, leads
    # dasselbe Profil ueber m. und mit Tracking-Parameter ist DOCH eine Dublette
    assert sum(1 for _, r in dropped if "derselben" in r or "desselben" in r) == 2, dropped
    # der etabliertere Standort gewinnt, nicht der erste in der Liste
    assert [p for p in leads if p["title"] == "Bob Locks North"][0]["reviewsCount"] == 90
    # nichts geht verloren
    assert len(leads) + len(dropped) == len(tim + local + fb + none)
    reasons = " ".join(r for _, r in dropped)
    assert "Kette: 12 Standorte" in reasons and "keine Website" in reasons, reasons
    # ein geteilter Host ist NIE eine Kette, egal wie viele Profile darauf liegen
    many_fb = [{"title": f"F{i}", "website": f"https://facebook.com/f{i}", "reviewsCount": 1}
               for i in range(15)]
    assert len(dedupe(many_fb)[0]) == 15, "15 Facebook-Seiten sind 15 Firmen, keine Kette"

    # zwei Standorte sind KEINE Kette -> ein Lead, kein Verlust der Firma
    l2, d2 = dedupe(local)
    assert len(l2) == 1 and len(d2) == 1, (l2, d2)

    # deterministisch: gleiche Eingabe, gleiches Ergebnis
    assert [p["title"] for p in dedupe(tim + local)[0]] == [p["title"] for p in dedupe(local + tim)[0]]

    # GLOBAL zaehlen, nicht pro Region. Sechs Standorte in Region A und sechs in B sind
    # zusammen eine Kette; getrennt bliebe sie zweimal unter der Schwelle. Gemessen
    # wuerden so 220 Ketten-Standorte durchrutschen.
    region_a = [{"title": f"Keytek {i}", "website": "https://keytek.co.uk/a",
                 "reviewsCount": i} for i in range(6)]
    region_b = [{"title": f"Keytek {i}", "website": "https://keytek.co.uk/b",
                 "reviewsCount": i} for i in range(6)]
    assert len(dedupe(region_a)[0]) == 1, "regional bleibt die Kette ein Lead"
    assert dedupe(region_a + region_b)[0] == [], "global ist sie eine Kette und faellt weg"
    print("self-check ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("raw", nargs="*", help="eine oder MEHRERE raw.json (Ketten global zaehlen)")
    ap.add_argument("--out", default="", help="Zielpfad-Praefix; Standard: der erste Input")
    ap.add_argument("--chain-threshold", type=int, default=CHAIN_THRESHOLD)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--supabase", metavar="NICHE",
                    help="auf dem Bestand in industry_operators arbeiten statt auf raw.json")
    ap.add_argument("--apply", action="store_true", help="mit --supabase: wirklich schreiben")
    a = ap.parse_args()
    if a.self_check:
        self_check()
        return 0
    if a.supabase:
        return run_supabase(a.supabase, a.chain_threshold, a.apply)
    if not a.raw:
        ap.error("mindestens eine raw.json, --supabase NICHE oder --self-check")

    places = []
    for path in a.raw:
        data = json.load(open(path, encoding="utf-8"))
        places += data if isinstance(data, list) else (data.get("items") or [])
    if len(a.raw) == 1:
        print("HINWEIS: nur eine Datei. Ketten werden regional gezaehlt und rutschen durch "
              "(gemessen: 220 Standorte). Alle Regionen zusammen uebergeben.")
    leads, dropped = dedupe(places, a.chain_threshold)

    from collections import Counter
    why = Counter(re.sub(r"\(.*\)|\d+", "", r).strip() for _, r in dropped)
    print(f"{len(places)} Zeilen -> {len(leads)} anschreibbare Betriebe")
    for r, n in why.most_common():
        print(f"   -{n:>5}  {r}")

    if a.dry_run:
        print("[dry-run] nichts geschrieben")
        return 0

    base = a.out or a.raw[0].rsplit(".", 1)[0]
    out = base + "_leads.json"
    bucket = base + "_deduped_out.json"
    json.dump(leads, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump([{"business_name": p.get("title") or "", "city": p.get("city") or "",
                "website": p.get("website") or "", "place_id": p.get("placeId") or "",
                "reason": r} for p, r in dropped],
              open(bucket, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"geschrieben: {out}\ngebucketet:  {bucket}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
