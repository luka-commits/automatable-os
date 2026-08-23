#!/usr/bin/env python3
"""mail_audit.py — prueft die FERTIGE Mail ueber den ganzen Bestand, nicht nur die Stichpunkte.

DER ANLASS (22.08.2026). An diesem Tag sind acht Fehler hochgekommen, und **kein einziger hat
je eine Ausnahme geworfen**:

  `stapel.offen()` haing an `mail.position`      -> kein Lead galt je als fertig
  `preview_mail.main()` filterte auf `position`  -> haette 0 Mails gerendert
  `batch_briefs.SPALTE = "position"`             -> "4/4 geprueft" + "0 Zeilen geschrieben"
  `kohorte.mit_24h` nie befuellt                 -> Faktor feuerte bei 0% statt 49%
  `spannung_und_liste` reservierte den Besten    -> 68% statt 87% mit drei Stichpunkten
  `len(None or [])` = 0                          -> "nothing under services" ohne Messung
  `export_cohort` laedt `raw` nicht              -> Score bei ALLEN Leads leer
  `min(paare)` ohne key                          -> TypeError bei Gleichstand, 16% der Leads

Alle acht liefen sauber durch und lieferten still weniger oder Falsches. Gefunden wurden sie,
weil Luka nachgefragt hat, ob eine Zahl stimmt -- nicht durch Tests.

DIE REGEL, DIE DARAUS FOLGT: **ein Faktor, dessen Daten bei ueber der Haelfte der Leads
vorliegen und der trotzdem bei 0% feuert, ist ein Fehler und kein Ergebnis.** Dasselbe gilt
fuer eine Spalte, die ueberall leer ist, und fuer einen Einbruch gegen den letzten Lauf.

  python3 mail_audit.py --niche locksmith
  python3 mail_audit.py --niche locksmith --strikt   # Exit 1 bei jedem Befund
"""
from __future__ import annotations
import argparse, collections, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# Ab hier gilt ein Faktor als "haette feuern muessen". Unter der Haelfte ist eine leere Quote
# eine plausible Datenlage, darueber ein Verdacht.
DATEN_SCHWELLE = 50


def laden(niche: str) -> list:
    from dedupe_leads import _supabase
    url, key = _supabase()
    hdr = {"apikey": key, "Authorization": f"Bearer {key}"}
    out, off = [], 0
    while True:
        q = (f"{url}/rest/v1/industry_operators?select=place_id,name,town,region,details,raw,"
             f"raw_dataforseo,web_signals,email&niche=eq.{niche}"
             f"&pipeline_status=neq.disqualified&order=place_id&limit=1000&offset={off}")
        seite = json.load(urllib.request.urlopen(
            urllib.request.Request(q, headers=hdr), timeout=240))
        out += seite
        off += 1000
        if len(seite) < 1000:
            break
    return out


def pruefe(niche: str) -> list:
    """-> Liste der Befunde. Leer heisst: die Maschine liefert, was sie liefern kann."""
    import benchmark, pool, gbp_score as GS, export_cohort as X
    from markt_umfeld import market_context

    rows = laden(niche)
    if not rows:
        return [f"keine Leads fuer niche={niche}"]
    bench = benchmark.load(niche)
    nach = {}
    for r in rows:
        nach.setdefault(r["region"], []).append(r)
    prim = collections.Counter((r.get("raw") or {}).get("categories", [None])[0]
                               for r in rows if (r.get("raw") or {}).get("categories"))
    ueblich = prim.most_common(1)[0][0] if prim else None

    offen = [r for r in rows if (r.get("web_signals") or {}).get("findings")
             and (r.get("email") or "").strip()]
    if not offen:
        return [f"keine anschreibbaren Leads fuer niche={niche}"]
    N = len(offen)

    # 1) DATEN DA vs FEUERT -- die Fehlerklasse des 22.08.
    raw_ = lambda r, k: (r.get("raw") or {}).get(k)
    DATEN = {
        "beschreibung": lambda r: "description" in (r.get("raw") or {}),
        "themen": lambda r: raw_(r, "reviewsTags") is not None,
        "24h": lambda r: bool(raw_(r, "openingHours")),
        "fotos": lambda r: raw_(r, "imagesCount") is not None,
        "ein_stern": lambda r: bool(raw_(r, "reviewsDistribution")),
        "bewertungen": lambda r: raw_(r, "reviewsCount") is not None,
        "kategorien": lambda r: raw_(r, "categories") is not None,
        "kategorie_der_besten": lambda r: bool(raw_(r, "categories")),
        "leistungen_leer": lambda r: (r.get("raw_dataforseo") or {}).get("services") is not None,
        "nachbarn": lambda r: bool(((r.get("details") or {}).get("nearest") or [])),
    }
    feuert, stichpunkte, scores, namen_leer = collections.Counter(), collections.Counter(), [], 0
    for r in offen:
        try:
            mk = dict(market_context([x.get("raw") or {} for x in nach[r["region"]]],
                                     r.get("raw") or {}), primary=ueblich)
            bs = pool.bausteine(pool.aus_lead(r, mk, bench, niche))
            _, zs = pool.spannung_und_liste(bs)
        except Exception as e:
            feuert[f"AUSNAHME {type(e).__name__}"] += 1
            continue
        stichpunkte[min(len(zs), 5)] += 1
        for x in bs:
            feuert[x["id"]] += 1
        p, _ = GS.score(GS.faktoren(r.get("raw") or {},
                                    (r.get("raw_dataforseo") or {}).get("services"),
                                    bench, ueblich))
        if p is not None:
            scores.append(p)
        nb = ((r.get("details") or {}).get("nearest") or [])
        if not X.competitors_phrase(
                X.competitor(nb, 0, niche, r.get("town") or "", frozenset(), r["name"]),
                X.competitor(nb, 1, niche, r.get("town") or "", frozenset(), r["name"])):
            namen_leer += 1

    befunde = []
    for fid, hat_daten in DATEN.items():
        da = sum(1 for r in offen if hat_daten(r)) * 100 // N
        quote = feuert[fid] * 100 // N
        if da >= DATEN_SCHWELLE and quote == 0:
            befunde.append(f"STILLER AUSFALL: '{fid}' feuert bei 0%, obwohl die Daten bei "
                           f"{da}% vorliegen")

    for k, v in feuert.items():
        if str(k).startswith("AUSNAHME"):
            befunde.append(f"{k} bei {v} von {N} Leads ({v*100//N}%)")

    # 2) Reichen die Stichpunkte?
    drei = sum(v for k, v in stichpunkte.items() if k >= 3) * 100 // N
    if drei < 80:
        befunde.append(f"nur {drei}% der Leads erreichen drei Stichpunkte (erwartet >= 80%)")

    # 3) Spreizt der Score? Ein Score, der bei jedem dasselbe sagt, ist keiner.
    if scores:
        spanne = max(scores) - min(scores)
        if spanne < 30:
            befunde.append(f"Score spreizt kaum: {min(scores)}-{max(scores)} "
                           f"(Spanne {spanne}, erwartet >= 30)")
    else:
        befunde.append("kein einziger Lead bekommt einen Score")

    # 4) Konkurrenznamen -- eine Mail ohne Namen verliert ihren staerksten Beleg.
    if namen_leer * 100 // N > 10:
        befunde.append(f"{namen_leer*100//N}% der Leads haben keinen Konkurrenznamen "
                       f"(erwartet <= 10%)")

    return befunde, dict(feuert), dict(stichpunkte), scores, N


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--niche", default="locksmith")
    ap.add_argument("--strikt", action="store_true", help="Exit 1 bei jedem Befund")
    a = ap.parse_args()

    ergebnis = pruefe(a.niche)
    if isinstance(ergebnis, list):
        print("\n".join(ergebnis))
        return 1
    befunde, feuert, stich, scores, N = ergebnis

    print(f"{N} anschreibbare Leads · niche={a.niche}\n")
    drei = sum(v for k, v in stich.items() if k >= 3) * 100 // N
    print(f"  Stichpunkte >=3 : {drei}%")
    if scores:
        print(f"  Score           : {min(scores)}-{max(scores)}, "
              f"Median {sorted(scores)[len(scores)//2]}")
    print(f"  Faktoren aktiv  : {sum(1 for v in feuert.values() if v)}\n")

    if befunde:
        print("BEFUNDE:")
        for b in befunde:
            print(f"  ! {b}")
        return 1 if a.strikt else 0
    print("keine Befunde -- die Maschine liefert, was sie liefern kann")
    return 0


if __name__ == "__main__":
    sys.exit(main())
