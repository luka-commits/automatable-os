#!/usr/bin/env python3
"""markt_umfeld.py — die Kohorte um einen Betrieb herum, in Zahlen.

Herausgeloest aus `build_lead_findings.py` am 23.08.2026. Der Grund war kein Aufraeumen um
seiner selbst willen: `mail_audit` und `enrich_cohort_findings` brauchten aus dieser Datei
genau EINE Funktion (`market_context`) und zogen damit `findings`, `web_findings` und `score`
mit -- 1.700 Zeilen des alten Audit-Systems, das seit dem 22.08. nicht mehr laeuft. Solange
dieser Faden hielt, liess sich das Alte nicht archivieren.

Was hier steht, ist der einzige echte Vorsprung dieser Pipeline: der Betrieb kennt seine
eigenen Zahlen, aber nicht, wie er neben seinen zehn naechsten Nachbarn dasteht. Google
zeigt es nicht, und ein Konkurrent baut es nicht am Wochenende nach.
"""
from __future__ import annotations
import math

NACHBARN = 10          # die Kohorte, gegen die verglichen wird
WEIT_KM = 40           # darueber ist es kein gemeinsamer Markt mehr
# Ab hier traegt eine Region den Einleitungssatz. Darunter klingt sie nach Dorf statt nach
# Markt ("the other 5 locksmiths in rutland"), und dann ist das Land die ehrlichere Zahl.
REGION_MIN = 15


def nachbarn_fuer_intro(nearest: list, ketten_pids: set, karte: dict | None = None,
                        wie_viele: int = 2) -> list:
    """Die Nachbarn, die im Einleitungssatz genannt werden duerfen.

    ZWEI FILTER, beide aus echten Mails vom 27.07.:

    KETTEN RAUS. Der Satz stand als "i just looked at round the clock smith and timpson
    locksmiths and safe engineers". Timpson haben wir als Kette aussortiert (1.153 von
    4.746 Leads) und schliessen sie beim Rang-Vergleich aus -- im Einleitungssatz standen
    sie trotzdem als "dein Nachbar". Einem Schluesseldienst zu schreiben "ich habe mir dich
    und Timpson angesehen" ist schwach: das ist eine Filialkette im Schuhgeschaeft, kein
    Wettbewerber auf Augenhoehe.

    NAMEN KUERZEN, aber sanfter als beim Empfaenger. `_competitor_casual_map.json` haelt
    dafuer eine eigene Karte: "1A Ideal Locksmiths Kingston" wird beim EMPFAENGER zu
    "1A Ideal" (er erkennt sich), beim WETTBEWERBER zu "1A Ideal Locksmiths" (ein fremder
    Betrieb muss wiedererkennbar bleiben). casual_brand allein war zu scharf und machte
    aus "B M A Varsity" ein "B M".
    """
    karte = karte or {}
    out = []
    for n in (nearest or []):
        if n.get("place_id") in ketten_pids:
            continue
        name = (n.get("name") or "").strip()
        if not name:
            continue
        out.append(karte.get(name, name))
        if len(out) >= wie_viele:
            break
    return out


def gebiet_und_zahl(region: str, n_region: int, n_land: int, land: str = "the uk") -> tuple:
    """-> (anzahl, gebiet) fuer den Einleitungssatz. markt_copy.md § Rahmen, Block 3.

    Zahl und Etikett MUESSEN zusammenpassen. Der Satz stand als "the other 10 locksmiths in
    birmingham" -- die 10 waren die zehn naechsten Nachbarn, und in Birmingham gibt es
    Hunderte. Der Empfaengner braucht zwei Sekunden, um den ersten Satz der Mail zu
    widerlegen. Die Zahl war richtig, ihr Etikett falsch.
    """
    if n_region >= REGION_MIN and region:
        return max(n_region - 1, 0), region.lower()
    return max(n_land - 1, 0), land


def _km(a: dict, b: dict):
    """Luftlinie in km zwischen zwei Places. None, wenn einer keine Koordinaten hat."""
    import math
    la, lo = (a.get("location") or {}).get("lat"), (a.get("location") or {}).get("lng")
    lb, lob = (b.get("location") or {}).get("lat"), (b.get("location") or {}).get("lng")
    if None in (la, lo, lb, lob):
        return None
    p1, p2 = math.radians(la), math.radians(lb)
    return 6371 * 2 * math.asin(math.sqrt(
        math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2)
        * math.sin(math.radians(lob - lo) / 2) ** 2))


def nearest_cohort(places: list, place: dict, n: int = NACHBARN) -> tuple:
    """-> (die n naechsten Betriebe inklusive ihm selbst, Entfernung zum n-ten in km).

    Der Anlass (Luka, 27.07.: "koennen wir die Angles ueberhaupt nehmen, weil wir ja den
    country-wide Scrape nutzen"). Berechtigt, und die Messung gibt ihm recht: die Regionen
    sind voellig ungleich. West Midlands 185 Betriebe, Essex 152, Bedford 11, Isle of Wight
    1. Aus "only 3 of the 11 here do" wuerde in den Midlands "only 47 of the 185", und mit
    185 Betrieben einer Grafschaft konkurriert niemand.

    Orte sind das andere Extrem: Median 2 Leads. Ein fester Umkreis auch nicht -- bei 8 km
    haben 26 von 120 weniger als fuenf Nachbarn und einer 83.

    Was traegt, ist eine feste ANZAHL: die zehn naechsten. Immer definiert, Median 6,5 km
    zum zehnten, 90%-Fall 20 km. Nur 1 von 120 liegt ueber 40 km -- und genau dort sagt die
    zurueckgegebene Entfernung, dass "in deiner Naehe" nicht mehr stimmt.
    """
    mit = [(d, q) for q in places
           if q is not place and (d := _km(place, q)) is not None]
    if not mit:
        return places, None
    mit.sort(key=lambda x: x[0])
    gewaehlt = [place] + [q for _, q in mit[:n]]
    return gewaehlt, mit[min(n, len(mit)) - 1][0]


def market_context(places: list, place: dict) -> dict:
    """Was der Betrieb selbst NICHT sehen kann: seine Kohorte nebeneinander.

    Das ist unser einziger echter Vorsprung. Er kennt seine 176 Bewertungen; dass ihn damit
    nur ein Betrieb in der Stadt schlaegt, kennt er nicht. Jede Zeile in der Mail, die ohne
    diesen Vergleich auskommt, erzaehlt ihm etwas, das er selbst nachlesen kann -- und liest
    sich damit wie eine Vorlage. Deshalb wird der Vergleich hier einmal je Kohorte gebildet
    und in jeden Befund gereicht, statt dass jeder Befund den Betrieb isoliert beschreibt.
    """
    def n(v):
        try:
            return int(float(v or 0))
        except (TypeError, ValueError):
            return 0

    # NICHT die ganze Region, sondern die zehn naechsten. Sonst bedeutet derselbe Satz in
    # Bedford "deine zehn Nachbarn" und in den West Midlands "185 Betriebe einer Grafschaft".
    alle = [p for p in places if isinstance(p, dict)]
    peers, weite = nearest_cohort(alle, place)
    if weite is None:
        peers = alle
    by_rev = sorted(peers, key=lambda p: -n(p.get("reviewsCount")))
    mine = n(place.get("reviewsCount"))
    rank = next((i + 1 for i, p in enumerate(by_rev)
                 if p.get("placeId") == place.get("placeId")), None)

    cats = {}
    for p in by_rev[:5]:                       # die fuenf meistbewerteten geben den Ton an
        for c in (p.get("categories") or []):
            cats[c] = cats.get(c, 0) + 1
    photos = sorted(n(p.get("imagesCount")) for p in peers)
    # Der RANG, nicht nur der Median. Ohne ihn stand im Brief "43 Fotos gegen einen Median
    # von 14", und das Modell machte daraus "above every other locksmith in bedford" -- bei
    # Platz VIER von elf. Wolfguard hat 1219. Wer den Rang mitliefert, laesst nichts zu
    # schliessen uebrig.
    mine_photos = n(place.get("imagesCount"))
    photos_rank = sorted(photos, reverse=True).index(mine_photos) + 1 if photos else None

    return {
        "count": len(peers),
        # Wie weit der zehnte weg ist. Ueber 40 km ist es kein gemeinsamer Markt mehr, und
        # die Mail darf dann nicht "in deiner Naehe" behaupten.
        "cohort_km": round(weite, 1) if weite is not None else None,
        "cohort_is_local": bool(weite is not None and weite <= WEIT_KM),
        "reviews_rank": rank,
        "reviews_mine": mine,
        "reviews_leader": by_rev[0].get("title") if by_rev else "",
        "leader_cats": cats,
        # Ohne diese Zahl hiess das Lob nur "3 categories set" -- eine Tatsache, die der
        # Inhaber selbst eingetragen hat. Erst der Vergleich macht daraus eine Aussage.
        "cats_median": (lambda c: c[len(c) // 2] if c else 0)(
            sorted(len(p.get("categories") or []) for p in peers)),
        # DIE UEBLICHE HAUPTKATEGORIE der Kohorte (22.08.2026). `spec.md § 2` nennt sie den
        # #1-Rankingfaktor des Profils, und die Methode sagt "mirror the winning primary".
        # Gemessen ueber 2.744 Locksmith-Leads fuehren 73% "Locksmith" als erste Kategorie,
        # 13% "Emergency locksmith service" -- und **26% etwas ganz anderes**, von "Hardware
        # store" bis "Property maintenance". Wer als Schluesseldienst unter "Hardware store"
        # laeuft, taucht bei der Schluesseldienst-Suche schlechter auf.
        #
        # Genommen wird die Mehrheit der KOHORTE, nicht eine Liste von uns: damit sagt die
        # Mail "die meisten hier nutzen X" statt zu behaupten, was richtig ist.
        "primary": (lambda c: c.most_common(1)[0][0] if c else None)(
            __import__("collections").Counter(
                (p.get("categories") or [None])[0] for p in peers
                if (p.get("categories") or [None])[0])),
        # Die Bewertungszahl des NAECHSTEN Nachbarn (22.08.2026). Ohne sie bleibt die
        # Nachbar-Zeile eine Ortsangabe ohne Argument ("x ist 700m weg" -- und?). Mit ihr
        # wird sie der konkreteste Vergleich der Mail: gemessen hat der naechste bei 23% der
        # Leads mindestens DOPPELT so viele Bewertungen, im Median das 7,5-fache.
        #
        # Genommen wird nur der EINE naechste, nie ein Ortsdurchschnitt: eine Aussage ueber
        # einen gemessenen Betrieb haelt, eine ueber "alle im Ort" nicht (§ 4b).
        # `key=` ist Pflicht: ohne ihn vergleicht `min` bei zwei gleich weit entfernten
        # Nachbarn die Dicts selbst und wirft TypeError. Traf 16% der Leads und riss die
        # Abdeckung von 96% auf 81%, weil der Aufrufer die Ausnahme still verschluckt.
        "nearest_reviews": (lambda paare: n(min(paare, key=lambda x: x[0])[1]
                                            .get("reviewsCount")) if paare else None)(
            [(d, q) for q in alle
             if q is not place and (d := _km(place, q)) is not None]),
        "photos_median": photos[len(photos) // 2] if photos else 0,
        "photos_rank": photos_rank,
        "photos_leader": max(photos) if photos else 0,
        "with_description": sum(1 for p in peers if (p.get("description") or "").strip()),
        # Dieselbe Kohorten-Zahl wie bei den Oeffnungszeiten. Ohne sie hiess der Befund
        # "post something now and then, the profile hasn't moved" -- generisch, austauschbar,
        # und ein Rat statt einer Beobachtung. Mit ihr ist es eine Tatsache ueber SEINE Stadt.
        "with_posts": sum(1 for p in peers if p.get("ownerUpdates")),
        "with_24h": sum(1 for p in peers
                        if any("24" in str(d.get("hours", ""))
                               for d in (p.get("openingHours") or []))),
        "ahead_with_description": sum(1 for p in by_rev[:max((rank or 1) - 1, 0)]
                                      if (p.get("description") or "").strip()),
        "ahead_count": max((rank or 1) - 1, 0),
    }
