#!/usr/bin/env python3
"""test_integration.py — prueft die LAUFENDE Kampagne, nicht mehr das alte Audit-System.

NEU GESCHRIEBEN AM 23.08.2026, und der Anlass ist ein Fehler in der Berichterstattung, nicht
im Code. Die Vorgaengerfassung importierte `score`, `findings`, `web_findings` und `brief` --
allesamt Module des Audit-Katalogs vom Juli. Sieben ihrer acht Tests fassten die laufende
Google-Business-Profil-Kampagne nie an. Trotzdem wurde nach jeder Copy-Aenderung "8 von 8
Tests gruen" gemeldet, als sei damit etwas belegt: `pool.py`, `stapel.py` und `gbp_score.py`
haetten vollstaendig kaputt sein koennen, und die acht waeren gruen geblieben.

Ein Test, der das Falsche prueft, ist schlimmer als keiner. Er kostet nicht nur nichts, er
erzeugt Sicherheit, die es nicht gibt.

Was hier jetzt geprueft wird, ist der Weg aus `PIPELINE.md § 0`:

  1. Jeder Baustein kann feuern -- ein Katalogeintrag, den nichts ausloest, ist tot.
  2. Kein Baustein reisst die 80-Zeichen-Grenze -- die verwirft STILL.
  3. Jeder Baustein erfuellt die Formel: Status quo, Handlung, Folge.
  4. Jeder Score-Faktor kann bestehen UND durchfallen.
  5. Nicht gemessen wird nie zu einer Null.
  6. Der Score ist von Hand nachrechenbar.
  7. Betreff und Anrede tragen je Lead etwas anderes.
  8. Vorlage und Variablen passen zusammen.

Punkt 2 und 5 haben am 22./23.08. echte, stille Fehler durchgelassen -- eine 87 Zeichen lange
Kategorien-Zeile, die bei JEDEM Lead verworfen wurde, und ein `len(x or [])`, das aus "nicht
gemessen" eine Null machte. Beide fielen nur auf, weil jemand eine Zahl anzweifelte.

Usage:
  python3 test_integration.py
"""
from __future__ import annotations
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pool                      # noqa: E402
import gbp_score as GS           # noqa: E402
import fact_sheet as FS          # noqa: E402
import export_cohort as EC       # noqa: E402
import casualize as CZ           # noqa: E402


def _bench():
    return {"reviews": {"median": 20}, "photos_median": 14, "rating_median": 5.0,
            "services_median": 24, "hours24": {"ja_pct": 53}}


def _blatt(**ueber):
    """Ein Lead-Blatt, das moeglichst viele Bausteine ausloest."""
    b = {
        "niche": "locksmith", "place_id": "ChIJtest0000",
        "fotos": 2, "uk_median_fotos": 14,
        "meine_bewertungen": 9, "uk_median_bewertungen": 20,
        "sterne": 4.4, "sterne_verteilung": {"oneStar": 2, "twoStar": 1},
        "kategorien": 2, "hauptkategorie": "Hardware store",
        "uebliche_hauptkategorie": "Locksmith",
        "kategorie_der_besten": "Emergency locksmith service",
        "leistungen_im_profil": 3, "uk_median_leistungen": 24,
        "beschreibung_da": False, "beansprucht": True, "telefon": "0123",
        "website": "https://x.de", "oeffnungszeiten_gemessen": True, "zeigt_24h": False,
        "uk_anteil_24h": 53, "onsite_attribut": True,
        # OHNE DIESE ZEILE feuert `themen` nie, und der Test uebersieht ihn (23.08.2026:
        # zwei seiner Fassungen hatten keine Handlung, gefunden hat es `stapel --auto` an
        # echten Daten). Ein Testblatt, das einen Baustein nicht ausloest, prueft ihn nicht.
        "themen_der_bewertungen": {"key fob": 3}, "leistungen_liste": [],
        "im_pack": False,
    }
    b.update(ueber)
    return b


def _varianten():
    return (
        _blatt(),
        _blatt(im_pack=True),
        _blatt(fotos=1, meine_bewertungen=60, kategorien=8, leistungen_im_profil=0),
        _blatt(meine_bewertungen=200, uk_median_bewertungen=20, beschreibung_da=True),
        _blatt(meine_bewertungen=80, uk_median_bewertungen=20, im_pack=False),
        _blatt(kategorie_der_besten="Emergency locksmith and safe engineer service"),
        _blatt(leistungen_im_profil=0, kategorien=1, sterne=3.2),
    )


# ------------------------------------------------------------------- 1. Bausteine
def test_kein_baustein_reisst_die_laengengrenze():
    """80 Zeichen, und `pool.add` verwirft darueber STILL.

    Am 22.08. war die Kategorien-Zeile 87 Zeichen lang und wurde damit bei JEDEM Lead
    verworfen -- kein Fehler, keine Meldung, nur ein Befund, den niemand mehr bekam. 84%
    der Leads haetten ihn gebraucht. Gefunden hat es `mail_audit.py`, nicht dieser Test.
    """
    lang = []
    for v in _varianten():
        for x in pool.bausteine(v):
            if len(x["text"]) > pool.MAXLEN:
                lang.append((len(x["text"]), x["id"], x["text"]))
    assert not lang, "ueber 80 Zeichen und damit still verworfen:\n" + "\n".join(
        f"  {n} Z  {i}: {t}" for n, i, t in lang)


def test_jeder_baustein_erfuellt_die_formel():
    """Status quo, Handlung, Folge -- geprueft von `fact_sheet.formel`.

    Ohne diesen Test steht die Regel nur in der Schreibkarte, und dort haelt sie so lange,
    wie sich jemand an sie erinnert. Am 30.07. fiel bei 14 von 36 Zeilen die Handlung
    heraus, ohne dass es auffiel; am 23.08. endeten drei Bausteine auf "so add it" -- der
    Form nach eine Folge, dem Empfaenger gegenueber keine.
    """
    kaputt = []
    for v in _varianten():
        for x in pool.bausteine(v):
            fehlt = FS.formel("- " + x["text"])
            if fehlt:
                kaputt.append((x["id"], ", ".join(fehlt), x["text"]))
    assert not kaputt, "Bausteine ohne vollstaendige Formel:\n" + "\n".join(
        f"  {i} [{f}]: {t}" for i, f, t in kaputt)


def test_bausteine_tragen_keine_maschinenspur():
    """Kein Check-Name, kein ungefuellter Platzhalter, kein doppeltes Leerzeichen."""
    for v in _varianten():
        for x in pool.bausteine(v):
            t = x["text"]
            assert not re.search(r"\b(gbp|web|arch)-[a-z]", t), t
            assert "{" not in t and "}" not in t, t
            assert "  " not in t, f"doppeltes Leerzeichen: {t!r}"
            assert t == t.strip(), f"Rand-Leerzeichen: {t!r}"


def test_waehle_haelt_seine_regeln():
    """Hoechstens zwei derselben Form, nie derselbe Baustein zweimal.

    Am 22.08. stand in 2 von 3 Beispielen zweimal die Beschreibung -- einmal als eigener
    Punkt, einmal im Kontrast-Baustein.
    """
    p = pool.bausteine(_blatt(fotos=1, leistungen_im_profil=0, kategorien=1))
    gewaehlt = pool.waehle(p, 4)
    assert 0 < len(gewaehlt) <= 4, len(gewaehlt)
    formen = {}
    for x in gewaehlt:
        formen[x["form"]] = formen.get(x["form"], 0) + 1
    assert all(n <= 2 for n in formen.values()), f"mehr als zwei derselben Form: {formen}"
    ids = [x["id"] for x in gewaehlt]
    assert len(ids) == len(set(ids)), f"derselbe Baustein zweimal: {ids}"


def test_gleicher_lead_gleiche_zeilen():
    """Deterministisch je `place_id`, nie zufaellig.

    Eine verschickte Mail muss sich rekonstruieren lassen. Mit `random` waere sie nach dem
    Versand nicht mehr nachstellbar, und eine Antwort liesse sich keiner Fassung zuordnen.
    """
    b = _blatt()
    einmal = [x["text"] for x in pool.bausteine(b)]
    nochmal = [x["text"] for x in pool.bausteine(dict(b))]
    assert einmal == nochmal, "derselbe Lead, andere Zeilen"
    anders = [x["text"] for x in pool.bausteine(_blatt(place_id="ChIJandersXY"))]
    assert anders != einmal, "verschiedene Leads muessen sich unterscheiden koennen"


# ---------------------------------------------------------------------- 2. Score
def test_jeder_score_faktor_kann_bestehen_und_durchfallen():
    """Ein Faktor, der nie durchfaellt, ist ein Geschenk an jeden Lead.

    Und einer, der nie besteht, eine Strafe fuer jeden. Beides verschiebt jeden Score und
    sagt ueber keinen Betrieb etwas.

    Geprueft wird ueber MEHRERE Datenstaende, nicht ueber zwei: `stunden` und `stunden24`
    schliessen sich in einem einzigen aus. Ohne Oeffnungszeiten faellt `stunden` durch, aber
    `stunden24` ist dann nicht mehr messbar (`None`) -- richtig so, und genau deshalb braucht
    dieser Test mehr als einen guten und einen schlechten Fall.
    """
    voll = {"claimThisBusiness": False, "phone": "0123", "website": "https://x.de",
            "categories": ["Locksmith", "Emergency locksmith service", "Safe & vault shop",
                           "Key duplication service", "Auto locksmith", "Door supplier"],
            "categoryName": "Locksmith",
            "reviewsCount": 200, "totalScore": 5.0, "imagesCount": 60,
            "description": "Wir oeffnen Tueren.", "reviewsTags": [{"title": "key fob"}],
            "reviewsDistribution": {"oneStar": 0, "twoStar": 0},
            "openingHours": [{"hours": "24 hours"}] * 7}
    leer = {"claimThisBusiness": True, "phone": "", "website": "",
            "categories": ["Hardware store"], "categoryName": "Hardware store",
            "reviewsCount": 1, "totalScore": 3.0, "imagesCount": 0,
            "description": "", "reviewsTags": [{"title": "key fob"}],
            "reviewsDistribution": {"oneStar": 5, "twoStar": 2},
            "openingHours": [{"hours": "9 to 5"}] * 7}
    ohne_zeiten = dict(leer, openingHours=[])

    # `kat_der_besten=""` heisst "Kohorte bekannt, es fehlt keine Kategorie"; `None` waere
    # "wir kennen die Kohorte nicht" und naehme den Faktor aus der Rechnung.
    staende = [
        GS.faktoren(voll, ["key fob replacement"] + ["a"] * 29, _bench(), "Locksmith",
                    kat_der_besten=""),
        GS.faktoren(leer, [], _bench(), "Locksmith",
                    kat_der_besten="Emergency locksmith service"),
        GS.faktoren(ohne_zeiten, [], _bench(), "Locksmith", kat_der_besten="x"),
    ]
    nie_gut = sorted(k for k in GS.GEWICHT if not any(s.get(k) is True for s in staende))
    nie_schlecht = sorted(k for k in GS.GEWICHT
                          if not any(s.get(k) is False for s in staende))
    assert not nie_gut, f"koennen nie bestehen: {nie_gut}"
    assert not nie_schlecht, f"koennen nie durchfallen: {nie_schlecht}"


def test_nicht_gemessen_wird_nie_zu_null():
    """Die tragende Regel der Pipeline, und die, die am 22.08. brach.

    `None` heisst "wir wissen es nicht" und faellt aus Zaehler UND Nenner. Ein
    `len(x or [])`, das daraus eine 0 macht, behauptet einen Mangel, den niemand gemessen
    hat -- und bestraft den Betrieb fuer eine Luecke in unserem Scrape.
    """
    raw = {"claimThisBusiness": False, "phone": "0123", "categories": ["Locksmith"],
           "categoryName": "Locksmith", "reviewsCount": 30, "totalScore": 5.0,
           "imagesCount": 20, "description": "da", "reviewsTags": [{"title": "x"}],
           "reviewsDistribution": {"oneStar": 0, "twoStar": 0},
           "openingHours": [{"hours": "24 hours"}]}
    ohne = GS.faktoren(raw, None, _bench(), "Locksmith")      # services NICHT gemessen
    mit_leer = GS.faktoren(raw, [], _bench(), "Locksmith")    # gemessen, und leer
    assert ohne["leistungen"] is None, "None darf nicht zu False werden"
    assert mit_leer["leistungen"] is False, "eine leere Liste IST eine Luecke"
    p_ohne, n_ohne = GS.score(ohne)
    p_mit, n_mit = GS.score(mit_leer)
    assert n_ohne == n_mit - 1, "der ungemessene Faktor muss aus dem Nenner fallen"
    assert p_ohne > p_mit, "wer nicht gemessen wurde, darf nicht schlechter dastehen"


def test_score_ist_nachrechenbar():
    """Von Hand gegengerechnet: erfuellte Gewichte durch gemessene Gewichte."""
    raw = {"claimThisBusiness": False, "phone": "0123", "website": "https://x.de",
           "categories": ["Locksmith"] * 6, "categoryName": "Locksmith",
           "reviewsCount": 200, "totalScore": 5.0, "imagesCount": 60,
           "description": "da", "reviewsTags": [{"title": "key fob"}],
           "reviewsDistribution": {"oneStar": 0, "twoStar": 0},
           "openingHours": [{"hours": "24 hours"}] * 7}
    f = GS.faktoren(raw, ["a"] * 30, _bench(), "Locksmith")
    punkte, n = GS.score(f)
    gemessen = {k: v for k, v in f.items() if v is not None and k in GS.GEWICHT}
    erwartet = round(100 * sum(GS.GEWICHT[k] for k, v in gemessen.items() if v)
                     / sum(GS.GEWICHT[k] for k in gemessen))
    assert punkte == erwartet, f"{punkte} != {erwartet} (von Hand nachgerechnet)"
    assert n == len(gemessen), f"{n} Faktoren gemeldet, {len(gemessen)} gemessen"


def test_zu_wenig_gemessen_gibt_gar_keine_zahl():
    """Unter `MINDESTENS` gemessenen Faktoren gibt es keinen Score.

    Eine Zahl aus drei Faktoren sieht genauso aus wie eine aus zwoelf und ist es nicht.
    """
    duenn = GS.faktoren({"categories": []}, None, _bench(), None)
    punkte, n = GS.score(duenn)
    assert n < GS.MINDESTENS, f"Testdaten liefern {n} Faktoren, erwartet unter MINDESTENS"
    assert punkte is None, f"{n} Faktoren, trotzdem eine Zahl: {punkte}"


# --------------------------------------------------------------- 3. Was in die Mail geht
def test_betreff_traegt_wettbewerber_lead_gebiet():
    """Reihenfolge seit 23.08.: der Nachbar zuerst, dann er, dann das Gebiet.

    Im Postfach steht links ein Absender, den er nicht kennt -- das erste Wort des Betreffs
    muss deshalb etwas sein, das er kennt.
    """
    betreffe = {EC.subject("Bedford", "locksmith", c, 11, "Ace")
                for c in ("Gold", "Jims", "Auto Keys")}
    assert len(betreffe) == 3, f"gleicher Betreff fuer verschiedene Nachbarn: {betreffe}"
    assert EC.subject("Bedford", "locksmith", "Gold", 11, "Ace") == (
        "gold, ace and bedford locksmiths")
    for leer in ("", None, "   "):
        assert EC.subject("Bedford", "locksmith", leer, 11, "Ace") == (
            "ace and the rest of bedford"), leer
        assert EC.subject("Bedford", "locksmith", leer, 11) == (
            "bedford locksmiths, your google listing"), leer


def test_anrede_traegt_nie_ort_oder_gewerk():
    """"hey citysentry locksmith pimlico" war der volle Firmeneintrag an einen Fremden.

    Die Ursache war nicht der Stadtteil, sondern die Trimm-Schleife: sie laeuft von hinten
    und bricht beim ersten unbekannten Wort ab, also blieb "Locksmith" mitten drin stehen.
    """
    for name, ort, hood, erwartet in [
        ("CitySentry Locksmith Pimlico", "London", "Pimlico", "citysentry"),
        ("Auto Locks Dewsbury", "Dewsbury", "", "auto locks"),
        ("Brothers Locksmith Twickenham", "London", "Twickenham", "brothers"),
        ("Key Moment Security", "Kent", "", "key moment"),   # "key" ist hier die MARKE
        ("DPS Keys", "Lancashire", "", "dps"),
    ]:
        ist = (CZ.casual_brand(name, "locksmith", ort, hood) or "").lower()
        assert ist == erwartet, f"{name!r} -> {ist!r}, erwartet {erwartet!r}"


def test_vorlage_und_variablen_passen_zusammen():
    """Jede {{...}} in der Vorlage braucht eine Quelle.

    Eine Variable, die niemand fuellt, steht als roher Platzhalter in der Mail beim Kunden.
    """
    html = open(os.path.join(HERE, "instantly_markt.html"), encoding="utf-8").read()
    koerper = html[html.index("-->") + 3:]         # ohne den Kommentarkopf
    in_vorlage = set(re.findall(r"\{\{(\w+)\}\}", koerper))
    assert in_vorlage, "die Vorlage enthaelt gar keine Variablen -- kaputt?"
    geliefert = set(getattr(EC, "VORLAGE_VARS", []))
    if geliefert:
        fehlt = sorted(in_vorlage - geliefert)
        assert not fehlt, f"Vorlage nutzt Variablen, die niemand fuellt: {fehlt}"


def test_vorlage_traegt_keine_maschinenspur():
    """Kein Check-Name, keine Em-Dashes in der ausgehenden Copy."""
    html = open(os.path.join(HERE, "instantly_markt.html"), encoding="utf-8").read()
    koerper = html[html.index("-->") + 3:]
    assert not re.search(r"\b(gbp|web|arch)-[a-z]", koerper), "Check-ID in der Vorlage"
    assert "—" not in koerper, "Em-Dash in ausgehender Copy (Hausregel)"


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    schlecht = 0
    for t in tests:
        print(f"  {t.__name__:52}", end=" ")
        try:
            t()
            print("ok")
        except AssertionError as e:
            schlecht += 1
            print("FEHLER")
            print(f"      {e}")
    print(f"{len(tests) - schlecht}/{len(tests)} Tests ok")
    return 1 if schlecht else 0


if __name__ == "__main__":
    sys.exit(main())
