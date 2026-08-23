#!/usr/bin/env python3
"""gbp_score.py — die eine Zahl, plus was gut laeuft und was nicht.

DER ANLASS (Luka, 22.08.2026): "wir haben businesses in area verglichen, hier ist dein score
basierend auf den folgenden x kategorien. und dann darunter what's working well ... und dann
darunter what can be improved".

WARUM NICHT DER ALTE SCORE. `score.py` rechnet zwei Zahlen: GBP (7 Faktoren) und Site (12).
Die Site-Haelfte kommt aus dem Site-Read, den wir nicht mehr fahren -- sie ist bei locksmith
zu 74% gefuellt und bei JEDER anderen Nische zu 0%. Eine Zahl, die wir fuer die naechste
Nische nicht wiederholen koennen, gehoert nicht in die Vorlage.

Dazu zwei Konstruktionsfehler im GBP-Teil, gemessen am 22.08.:
  `gbp-claimed` traegt das hoechste Gewicht (20), aber nur **1%** der Profile sind
    unbeansprucht -- der Faktor vergibt fast immer volle Punkte und unterscheidet nichts.
  `gbp-posts` (Gewicht 4) rechnet mit `ownerUpdates`, das bei **81%** der Leads `None` ist.
  Und die Beschreibung, mit **99%** der eindeutigste Mangel im ganzen Bestand, kommt in den
    sieben Gewichten GAR NICHT vor.

DIE REGEL, DIE HIER ALLES TRAEGT (PIPELINE.md § 0): ein Faktor, dessen Feld nicht gemessen
ist, faellt aus ZAEHLER UND NENNER. Sonst bestraft der Score den Betrieb fuer eine Luecke in
unserem Scrape -- und wir schicken ihm eine Zahl, die wir nicht verteidigen koennen.

  python3 gbp_score.py --self-check
"""
from __future__ import annotations
import sys

# Die ZWOELF Faktoren, alle aus dem GBP-Scraper, alle in PIPELINE.md § 4b als erlaubt
# gelistet. Erst waren es acht -- Luka, 22.08.: "aber sind wir wirklich so drastisch mit
# nur 8 Faktoren?". Berechtigt: vier weitere hatten 94-100% Datenabdeckung und lagen
# ungenutzt da (Kategorie der Bestbewerteten, Review-Themen, Sterne-Schnitt, schlechte
# Bewertungen).
# Das Gewicht folgt `knowledge/local-seo-method.md`: Kategorien, Leistungsliste und
# Bewertungen bewegen die Sichtbarkeit, Fotos und Oeffnungszeiten entscheiden nach dem Klick.
GEWICHT = {
    "kategorien":      16,  # bis 10 erlaubt, die meisten nutzen 1-2
    "hauptkategorie":  15,  # laut gbp-setup/spec.md der #1-Rankingfaktor
    "leistungen":      14,  # Ziel 20-30, "a top, easy lever"
    "kat_der_besten":  13,  # fuehren die Bestbewerteten eine Kategorie, die er nicht hat?
    "bewertungen":     12,  # "count and recency are among the strongest map-pack signals"
    "beschreibung":    10,  # 99% haben keine -- der eindeutigste Mangel im Bestand
    "themen_gedeckt":   9,  # nennt das Profil, was die Kunden in den Bewertungen schreiben?
    "fotos":            8,  # die Vitrine, nicht der Rang
    "sterne":           7,  # der Schnitt, den jeder Anrufer zuerst sieht
    "keine_schlechten":  6,  # keine unbeantwortete 1- oder 2-Sterne-Bewertung
    "stunden24":         6,  # bei Notdiensten stark, sonst nachrangig
    "stunden":           4,  # ueberhaupt gesetzt
}

# BEWUSST DRAUSSEN, obwohl die Daten zu 100% vorliegen:
#   `claimThisBusiness`  -- nur **1%** der Profile sind unbeansprucht. Ein Faktor, der 99 von
#                           100 Betrieben volle Punkte gibt, verschiebt den Score nach oben
#                           und unterscheidet nichts. Genau der Konstruktionsfehler des alten
#                           `score.py`, wo `gbp-claimed` mit **Gewicht 20** das schwerste
#                           Kriterium war.
#   `phone`              -- dasselbe, 99% haben eine.
# Ein Score-Faktor muss TRENNEN. Was fast jeder erfuellt, gehoert in "what's working well",
# nicht in die Zahl.


def _n(v, d=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return d


def _themen_gedeckt(raw: dict, services) -> bool | None:
    """Nennt das Profil, was die Kunden in den Bewertungen schreiben?

    `raw.reviewsTags` sind die Themen, die Google aus den echten Bewertungen zieht -- die
    Worte SEINER Kunden. Stehen sie weder in den Kategorien noch in der Leistungsliste,
    sucht jemand nach genau dem Job und findet ihn nicht.
    """
    tags = raw.get("reviewsTags")
    if tags is None:
        return None
    begriffe = [str(t.get("title") if isinstance(t, dict) else t).lower()
                for t in (tags or []) if t]
    if not begriffe:
        return None
    profil = " | ".join(str(x).lower() for x in
                        ((raw.get("categories") or []) + list(services or [])))
    return any(t in profil for t in begriffe)


def faktoren(raw: dict, services, bench: dict, ueblich: str | None,
             kat_der_besten=None) -> dict:
    """-> {faktor: True (erfuellt) | False (Luecke) | None (nicht gemessen)}.

    `None` ist der wichtigste der drei Werte: er heisst "wir wissen es nicht" und haelt den
    Faktor aus der Rechnung. Ein `len(x or [])`, das daraus eine 0 macht, hat am 22.08. die
    halbe Pipeline still verfaelscht.
    """
    raw = raw or {}
    kat = raw.get("categories")
    fotos, bew = raw.get("imagesCount"), raw.get("reviewsCount")
    stunden = raw.get("openingHours")
    f_med = bench.get("photos_median") or 14
    b_med = (bench.get("reviews") or {}).get("median") or 20
    haupt = (kat or [None])[0]

    return {
        "kategorien":     None if kat is None else len(kat) >= 5,
        "hauptkategorie": None if not (haupt and ueblich) else haupt.lower() == ueblich.lower(),
        "leistungen":     None if services is None else len(services) >= 20,
        "bewertungen":    None if bew is None else bew >= b_med,
        # Das Feld ist bei allen gemessen -- fehlt es im Objekt, wurde nicht gescrapt.
        "beschreibung":   None if "description" not in raw else bool((raw.get("description") or "").strip()),
        "fotos":          None if fotos is None else fotos >= f_med,
        "stunden24":      None if not stunden else any("24" in str(d.get("hours", "")) for d in stunden),
        "stunden":        None if stunden is None else bool(stunden),
        # Fuehren die Bestbewerteten eine Kategorie, die er nicht hat? `None` heisst, wir
        # kennen die Kohorte nicht -- dann faellt der Faktor raus statt als Luecke zu zaehlen.
        "kat_der_besten": None if kat_der_besten is None else not kat_der_besten,
        "themen_gedeckt": _themen_gedeckt(raw, services),
        "sterne":         None if raw.get("totalScore") is None else float(raw["totalScore"]) >= 4.5,
        # Eine unbeantwortete Ein- oder Zwei-Sterne-Bewertung ist das Erste, was ein Anrufer
        # liest. Ob sie beantwortet ist, wissen wir nicht -- gezaehlt wird nur, ob es sie gibt.
        "keine_schlechten": (None if not raw.get("reviewsDistribution") else
                             not (_n((raw["reviewsDistribution"] or {}).get("oneStar")) +
                                  _n((raw["reviewsDistribution"] or {}).get("twoStar")))),
    }


# Sieben von zwoelf, angehoben von fuenf am 22.08.2026. Bei genau fuenf gemessenen Faktoren
# ist "0/100 across 5 categories" formal richtig und trotzdem eine duenne Aussage: wir haben
# den Betrieb kaum vermessen und stellen ihm eine Note aus. Gemessen ueber die 2.744
# anschreibbaren Leads kostet die Anhebung fast nichts -- **96% haben sieben oder mehr**,
# 86% sogar zehn oder elf. Die 4% ohne Score bekommen die Mail trotzdem, nur ohne die Zahl:
# `export_cohort` laesst `score_line` dann leer, und die Vorlage rendert die Zeile weg.
MINDESTENS = 7


def score(f: dict) -> tuple:
    """-> (0-100, Zahl der gerechneten Faktoren) oder (None, n) wenn zu wenig gemessen.

    Unter fuenf Faktoren gibt es keine Zahl. Der alte Lauf zeigte "your site 100 across 1" --
    ein Betrieb, dessen Seite nicht abrufbar war, bekam die Bestnote fuer den einen Punkt,
    den wir pruefen konnten. Lieber gar keine Zahl als eine, die bei der ersten Rueckfrage
    zerfaellt.
    """
    gemessen = {k: v for k, v in f.items() if v is not None}
    if len(gemessen) < MINDESTENS:
        return None, len(gemessen)
    voll = sum(GEWICHT[k] for k in gemessen)
    hat = sum(GEWICHT[k] for k, v in gemessen.items() if v)
    return round(hat * 100 / voll), len(gemessen)


def self_check():
    bench = {"photos_median": 14, "reviews": {"median": 20}}
    voll = {"categories": ["Locksmith", "a", "b", "c", "d"], "imagesCount": 40,
            "reviewsCount": 80, "description": "wir oeffnen tueren", "totalScore": 4.9,
            "reviewsTags": [{"title": "key cutting", "count": 5}],
            "reviewsDistribution": {"oneStar": 0, "twoStar": 0, "fiveStar": 80},
            "openingHours": [{"day": "Mon", "hours": "Open 24 hours"}]}
    f = faktoren(voll, ["key cutting"] + [f"s{i}" for i in range(24)], bench, "Locksmith",
                 kat_der_besten=None if False else "")
    assert all(v is True for v in f.values()), f
    assert score(f) == (100, 12), score(f)

    leer = {"categories": ["Hardware store"], "imagesCount": 2, "reviewsCount": 3,
            "description": "", "totalScore": 3.9,
            "reviewsTags": [{"title": "key cutting", "count": 5}],
            "reviewsDistribution": {"oneStar": 3, "twoStar": 1},
            "openingHours": [{"day": "Mon", "hours": "09:00-17:00"}]}
    f2 = faktoren(leer, [], bench, "Locksmith", kat_der_besten="Emergency locksmith service")
    # `stunden` ist erfuellt -- er HAT welche gesetzt, nur keine 24. Genau die Trennung,
    # die der Score braucht: "Zeiten gesetzt" und "24 Stunden" sind zwei Faktoren.
    assert not any(v for k, v in f2.items() if k != "stunden"), f2
    assert f2["stunden"] is True
    assert score(f2) == (round(GEWICHT["stunden"] * 100 / sum(GEWICHT.values())), 12), score(f2)

    # NICHT GEMESSEN faellt aus der Rechnung, statt als Luecke zu zaehlen.
    ohne = faktoren({"categories": ["Locksmith"], "imagesCount": 40, "reviewsCount": 80,
                     "description": "x", "openingHours": [{"hours": "Open 24 hours"}]},
                    None, bench, "Locksmith")
    assert ohne["leistungen"] is None, ohne
    s, n = score(ohne)
    assert n == 7 and s is not None, (s, n)   # 5 Faktoren ohne Daten fallen raus
    # ... und der Score ist HOEHER als mit einer gezaehlten Null -- genau der Unterschied,
    # den `len(None or [])` am 22.08. verwischt hat.
    mit_null = dict(ohne, leistungen=False)
    assert score(ohne)[0] > score(mit_null)[0], (score(ohne), score(mit_null))

    # Unter fuenf gemessenen Faktoren gibt es keine Zahl.
    duenn = {k: None for k in GEWICHT}
    duenn["fotos"] = True
    assert score(duenn)[0] is None, score(duenn)
    print("gbp_score self-check ok")
    return 0


if __name__ == "__main__":
    sys.exit(self_check() if "--self-check" in sys.argv else self_check())
