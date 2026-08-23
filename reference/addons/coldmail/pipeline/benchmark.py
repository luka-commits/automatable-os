#!/usr/bin/env python3
"""benchmark.py — der Landesvergleich, den sonst niemand hat.

Der Anlass (Luka, 27.07.2026): "wir koennten auch Industry-Benchmarks nehmen und die Leute
dagegen einordnen." Genau das ist unser einziger unnachbaubarer Vorsprung. Der Betrieb kennt
seine 176 Bewertungen. Dass damit nur jeder zehnte Schluesseldienst im Land mithaelt, kann er
nirgends nachsehen -- Google zeigt es nicht, kein Werkzeug rechnet es aus, und ein Konkurrent
baut es am Wochenende nicht nach. Wir haben 4.746 Betriebe in der Datenbank.

DER BEFUND, DER DIE BRANCHE UMDREHT: der Median liegt bei 5,0 Sternen. Die Sternezahl sagt in
dieser Branche also NICHTS -- wer 4,9 hat, liegt unter dem Mittelwert. Unterschieden wird ueber
die ANZAHL: Median 17, oberste 10% ab 156. Ein Betrieb, der stolz auf seine 4,9 ist, hat das
noch nie jemand gesagt. Deshalb faellt der Rating-Befund raus und der Mengen-Befund rein.

Einmal je Nische gerechnet und als JSON abgelegt, nicht je Lead abgefragt. 4.746 Zeilen sind
fuenf Seitenaufrufe, keine 4.746.

Usage:
  python3 benchmark.py --niche locksmith --refresh    # neu rechnen und ablegen
  python3 benchmark.py --niche locksmith              # anzeigen
  python3 benchmark.py --self-check
"""
from __future__ import annotations
import argparse, json, os, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "benchmarks.json")


def _pct(sorted_vals, p):
    if not sorted_vals:
        return 0
    return sorted_vals[min(int(len(sorted_vals) * p / 100), len(sorted_vals) - 1)]


def compute(niche: str) -> dict:
    import speicher
    rows = speicher.lade(niche, ["reviews", "rating", "photos_count", "website"])

    rev = sorted(r.get("reviews") or 0 for r in rows)
    rat = sorted(r["rating"] for r in rows if r.get("rating"))
    pho = sorted(r.get("photos_count") or 0 for r in rows)
    return {
        "niche": niche, "n": len(rows),
        "reviews": {"median": _pct(rev, 50), "p75": _pct(rev, 75),
                    "p90": _pct(rev, 90), "p95": _pct(rev, 95), "p99": _pct(rev, 99)},
        "rating_median": _pct(rat, 50),
        "photos_median": _pct(pho, 50),
        "no_website": sum(1 for r in rows if not r.get("website")),
        "posts": _posting_rate(niche),
        "hours24": _hours24_rate(niche),
        "services_median": _services_median(niche),
    }


def _services_median(niche: str):
    """Wie viele Leistungen ein Profil ueblicherweise listet -- landesweit.

    DER ANLASS (Luka, 23.08.2026): "die sektion hat keinen vergleich oder keine erklaerung
    warum sie das aendern sollten, das ist schwach." Die Leistungs-Bausteine sagten bis
    dahin "add more so you match more searches" -- eine Aufforderung ohne Massstab. Mit dem
    Median wird daraus "you list 8 where most run 23", und das ist eine Aussage, die der
    Empfaenger nirgends sonst bekommt.

    Gezaehlt werden nur Profile, die ueberhaupt eine Leistungsliste haben: ein `None` heisst
    "nicht gemessen", nicht "keine Leistungen", und wuerde den Median nach unten ziehen.
    Gibt keine Zeile Daten her, kommt None zurueck und die Bausteine lassen den Vergleich
    weg, statt eine Null zu behaupten.
    """
    import speicher
    zahlen = [len((r.get("raw_dataforseo") or {}).get("services") or [])
              for r in speicher.lade(niche, ["raw_dataforseo"])
              if isinstance((r.get("raw_dataforseo") or {}).get("services"), list)]
    return _pct(sorted(zahlen), 50) if zahlen else None


def _hours24_rate(niche: str) -> dict:
    """Wie viele haben rund um die Uhr offen -- landesweit, nicht je Ort.

    DER ANLASS (Luka, 30.07.2026): "dann lassen wir die Zahl vielleicht einfach weg oder?"
    Die Mails verglichen mit dem Ort ("you're not showing 24 hours where 5 in town are"),
    und den Ort kennen wir nur ausschnittsweise: in Bedford 11 von 27, in Hornchurch 1 von
    20. Eine Aussage ueber EINEN Betrieb haelt das aus (der Nachbar ist echt und im Median
    900 m weg), eine Aussage ueber ALLE nicht. Also vergleicht die Copy ab jetzt gegen das
    Land, wo n gross genug ist, dass die Luecke den Median nicht kippt.
    """
    import speicher
    oh = [(r.get("raw") or {}).get("openingHours")
          for r in speicher.lade(niche, ["raw"])
          if (r.get("raw") or {}).get("openingHours")]
    if not oh:
        return {}
    rund = sum(1 for tage in oh
               if all("24" in str(t.get("hours", "")).lower() for t in tage))
    return {"n": len(oh), "ja": rund, "ja_pct": round(rund * 100 / len(oh))}


def _posting_rate(niche: str) -> dict:
    """Wie viele posten nie -- als Anteil, gemessen statt geschaetzt.

    Stand bis 27.07. als "six in ten" in findings.py, also als getippte Zahl in einem
    Satz, der an den Inhaber geht. Beantwortbar ist die Frage nur fuer Leads mit
    Detail-Lauf; `n` sagt deshalb dazu, auf wie vielen sie beruht.
    """
    import speicher
    mit_detail = [(r.get("raw") or {}) for r in speicher.lade(niche, ["raw"])
                  if (r.get("raw") or {}).get("_detail") is True]
    n = len(mit_detail)
    if not n:
        return {}
    # Ein FEHLENDES Feld ist ebenfalls "postet nie" -- nicht "nicht gemessen". Das gilt
    # nur hier, weil der Detail-Lauf das Feld setzt, wenn es Beitraege gibt.
    mit = sum(1 for raw in mit_detail if raw.get("ownerUpdates"))
    return {"n": n, "never": n - mit, "never_pct": round((n - mit) * 100 / n)}


def load(niche: str) -> dict:
    try:
        return json.load(open(CACHE, encoding="utf-8")).get(niche, {})
    except (OSError, ValueError):
        return {}


def save(bm: dict):
    all_bm = {}
    if os.path.exists(CACHE):
        try:
            all_bm = json.load(open(CACHE, encoding="utf-8"))
        except ValueError:
            pass
    all_bm[bm["niche"]] = bm
    json.dump(all_bm, open(CACHE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


def standing(reviews: int, bm: dict) -> tuple:
    """(Prozentband, Satzteil) fuer eine Bewertungszahl. Ohne Benchmark: (0, '').

    Bewusst grob gebandet. "top 4,3%" klingt gerechnet, "top 5%" klingt gewusst -- und die
    Stichprobe traegt die zweite Nachkommastelle ohnehin nicht.
    """
    r = bm.get("reviews") or {}
    if not r:
        return 0, ""
    if reviews >= r.get("p99", 10 ** 9):
        return 1, "the top 1% of uk locksmiths"
    if reviews >= r.get("p95", 10 ** 9):
        return 5, "the top 5% of uk locksmiths"
    if reviews >= r.get("p90", 10 ** 9):
        return 10, "the top 10% of uk locksmiths"
    if reviews >= r.get("p75", 10 ** 9):
        return 25, "the top quarter of uk locksmiths"
    return 0, ""


def self_check():
    bm = {"reviews": {"median": 17, "p75": 59, "p90": 156, "p95": 256, "p99": 900},
          "rating_median": 5.0, "n": 4746}
    assert standing(1293, bm)[0] == 1, standing(1293, bm)
    assert standing(176, bm)[1] == "the top 10% of uk locksmiths"
    assert standing(60, bm)[0] == 25
    # unter dem oberen Viertel gibt es KEINE Einordnung statt einer geschoenten
    assert standing(9, bm) == (0, "")
    assert standing(100, {}) == (0, ""), "ohne Benchmark wird nichts behauptet"
    print("self-check ok")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--niche", default="locksmith")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return self_check()
    bm = compute(a.niche) if a.refresh else load(a.niche)
    if a.refresh:
        save(bm)
    if not bm:
        sys.exit(f"kein Benchmark fuer {a.niche} — einmal mit --refresh rechnen")
    r = bm["reviews"]
    print(f"{bm['n']} {a.niche}s in der Datenbank")
    print(f"  Bewertungen  median {r['median']}  top25% ab {r['p75']}  "
          f"top10% ab {r['p90']}  top5% ab {r['p95']}  top1% ab {r['p99']}")
    print(f"  Rating       median {bm['rating_median']}"
          f"   <- ist der Median 5.0, sagt die Sternezahl in dieser Branche nichts")
    print(f"  Fotos        median {bm['photos_median']}")
    print(f"  ohne Website {bm['no_website']}")
    if bm.get("posts"):
        p = bm["posts"]
        print(f"  posten nie   {p['never']} von {p['n']} mit Detail-Lauf = {p['never_pct']}%"
              f"   <- die Zahl, die in der Mail steht")


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    main()
