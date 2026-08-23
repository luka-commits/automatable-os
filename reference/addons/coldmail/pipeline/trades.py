#!/usr/bin/env python3
"""trades.py — welche Befunde fuer welche Branche zaehlen.

Der Anlass (Luka, 27.07.2026): "kein Booking-Link" war mit 7 von 15 der haeufigste Mangel
der Bedford-Kohorte -- und bei einem Schluesseldienst schlicht falsch. Um zwei Uhr nachts
bucht niemand einen Termin, er ruft an. Wir haben einen Betrieb fuer etwas getadelt, das
bei ihm richtig ist.

Dahinter steht ein groesseres Muster: **ein Notdienst verdient anders als ein Salon.**
Der Kunde steht vor der eigenen Tuer, es regnet, er entscheidet in unter einer Minute und
nimmt den, der rangeht. Daraus folgt, was zaehlt und was nicht:

  ZAEHLT   Rund-um-die-Uhr sichtbar · Nummer mit einem Daumendruck waehlbar ·
           Notfall-Kategorie gesetzt (Google routet Notfall-Absicht darueber) ·
           Profil beansprucht

  ZAEHLT NICHT  Terminbuchung · Textlaenge · doppelte Seitentitel · Tag-Archive ·
                die Ueberschrift der Startseite

Der Grund fuer die zweite Spalte ist derselbe wie fuer die erste: bei einem Notdienst
laeuft der Auftrag ueber den Maps-Eintrag, nicht ueber die Website. Der Kunde tippt
"locksmith near me", drueckt auf Anrufen und liest die Seite nie. Website-Befunde bleiben
deshalb drin, aber gedeckelt -- sie duerfen nie ein Notfall-Signal aus den ersten drei
Plaetzen draengen.

Neue Branche eintragen heisst: eine Zeile in PROFILES. Ohne Eintrag bleibt alles beim
Alten, es gibt keinen stillen Umbau fuer ungetestete Branchen.

Usage:
  python3 trades.py --self-check
"""
from __future__ import annotations
import sys

# Notdienst: der Kunde ist in Not, entscheidet in Sekunden und ruft an.
EMERGENCY = {
    "drop": {
        "gbp-booking-link",        # niemand bucht einen Notfall
        "web-lead-capture",        # und niemand fuellt um zwei Uhr nachts ein Formular aus.
                                   # Derselbe Kategorienfehler wie der Booking-Link, nur eine
                                   # Ebene tiefer -- und er blieb stehen, als der erste fiel.
                                   # Er machte die Mails der zwei bestaufgestellten Betriebe
                                   # in Bedford wortgleich identisch.
        "web-h1",                  # die Startseite wird nicht gelesen, es wird angerufen
        "web-word-readability",    # dito
        "arch-pyramid",            # Seitenarchitektur entscheidet keinen 2-Uhr-Auftrag
        "arch-url-rules",
    },
    "boost": {
        "gbp-hours": 15,           # rund um die Uhr ist DAS Verkaufsargument
        "web-tap-to-call": 25,     # kalte Haende, ein Daumen, eine Chance
        "gbp-secondary-categories": 10,   # Notfall-Kategorie = Notfall-Absicht
        "gbp-claimed": 5,
    },
    # Website-Befunde duerfen ein Notfall-Signal nie verdraengen.
    "site_cap": 70,
}

PROFILES = {
    n: EMERGENCY for n in (
        "locksmith", "auto-locksmith", "emergency-locksmith",
        "plumber", "emergency-plumber", "drainage", "boiler-repair",
        "electrician", "glazier", "garage-door", "locksmiths",
    )
}


def profile(niche: str) -> dict:
    return PROFILES.get((niche or "").strip().lower().replace(" ", "-"), {})


# Wonach ein Kunde SUCHT -- nicht, wie unser Nischen-Slug heisst.
#
# Der Rang-Abruf baute den Suchbegriff bisher als f"{niche} {ort}". Bei `locksmith` geht das
# zufaellig gut, weil der Slug schon ein englisches Substantiv ist. Bei jedem anderen nicht:
# "uk-cleaning bristol", "hk-pilates-studio central", "au-pest-control-service melbourne".
# Der Laendercode wandert mit, der Bindestrich bleibt. Genau derselbe Fehler stand bis heute
# als "407 uk-cleanings mapped in bristol" auf der Portalseite.
#
# Abgeleitet statt hinterlegt waere verlockend, aber der Suchbegriff ist die GRUNDLAGE jeder
# Rang-Aussage. Eine Regel, die bei einer neuen Nische danebenliegt, erzeugt eine falsche
# Zahl in JEDER Mail dieser Nische -- und sie faellt niemandem auf, weil eine Position
# immer plausibel aussieht. Fuer ein Dutzend Nischen ist eine gepflegte Tabelle ehrlicher.
#
# `spezial` gilt fuer Betriebe, deren Name oder Kategorie sie als Spezialisten ausweist.
# Gemessen: 243 der 3.593 Locksmiths (7%) sind Auto-Schluesseldienste. Ihnen "du bist nicht
# unter den drei fuer locksmith bedford" zu schreiben laedt zur Antwort ein, sie machten
# keine Haustueren -- und die waere berechtigt.
SUCHBEGRIFFE = {
    "locksmith":               {"haupt": "locksmith",        "spezial": "auto locksmith"},
    "uk-cleaning":             {"haupt": "cleaning company"},
    "uk-gym":                  {"haupt": "gym"},
    "uk-plumber":              {"haupt": "plumber",          "spezial": "emergency plumber"},
    "hk-pilates-studio":       {"haupt": "pilates studio"},
    "au-pest-control-service": {"haupt": "pest control"},
    "au-gym":                  {"haupt": "gym"},
}

# Woran ein Spezialist erkennbar ist. NUR Name und Kategorie -- die Bewertungs-Themen
# taeuschen: ein normaler Schluesseldienst, der gelegentlich einen Autoschluessel nachmacht,
# traegt "car key" als Thema. Ueber Themen kam ich auf 14%, ueber Name und Kategorie auf 7%,
# und nur die 7% halten einer Nachfrage stand.
SPEZIALIST = {
    "locksmith": ("auto", "car key", "car locksmith", "vehicle"),
    "uk-plumber": ("emergency", "24 hour", "24hr"),
}

# Woran eine LEISTUNG erkennbar ist: sie nennt ein Ding des Gewerks.
#
# Der Umweg ueber eine schwarze Liste ("response time", "polite staff", ...) hat viermal
# verloren: nach jedem Nachtrag kamen "great finish", dann "advice" und "company", dann
# "quote", "property" und "30 minutes" durch. Die Menge moeglicher Eigenschaftswoerter ist
# offen, die Menge der Gewerks-Dinge ist endlich. Also andersherum: was KEIN Ding des
# Gewerks nennt, ist keine eintragbare Leistung.
#
# Der Preis ist ein enger Filter -- "emergency callout" faellt raus, obwohl es eine
# Leistung ist. Das kostet einen Stichpunkt. Ein faelschlich empfohlenes "add 30 minutes
# to your services" kostet Glaubwuerdigkeit.
GEWERKS_DINGE = {
    "locksmith": ("lock", "key", "door", "safe", "alarm", "cylinder", "bolt", "hinge",
                  "upvc", "window", "garage", "entry", "fob", "ignition", "barrel",
                  "handle", "latch", "padlock", "gate", "shutter"),
    "uk-plumber": ("tap", "pipe", "boiler", "leak", "drain", "toilet", "shower", "sink",
                   "radiator", "valve", "cylinder", "bath", "heating"),
    "uk-cleaning": ("clean", "carpet", "window", "oven", "upholster", "floor", "tile",
                    "gutter", "driveway", "sofa", "rug"),
}


def ist_leistung(thema: str, niche: str) -> bool:
    """Nennt dieses Bewertungs-Thema ein Ding des Gewerks? Kennen wir die Nische nicht,
    wird NICHT gefiltert -- lieber ein schwacher Stichpunkt als gar keiner."""
    dinge = GEWERKS_DINGE.get((niche or "").strip().lower().replace(" ", "-"))
    if not dinge:
        return True
    return any(d in (thema or "").lower() for d in dinge)


def suchbegriff(niche: str, ort: str, name: str = "", kategorien=None,
                mit_ort: bool = True) -> str:
    """Der Begriff, unter dem dieser Betrieb gefunden werden will.

    `mit_ort=False` gibt das blosse Wort ohne Ortsnamen zurueck -- fuer die Abfrage ueber
    Koordinaten, wo der Ort schon in der Suchposition steckt. "locksmith" plus Standort
    ist ausserdem naeher an dem, was jemand nachts wirklich tippt, als "locksmith bedford".
    """
    n = (niche or "").strip().lower().replace(" ", "-")
    eintrag = SUCHBEGRIFFE.get(n)
    if not eintrag or (mit_ort and not (ort or "").strip()):
        return ""
    wort = eintrag["haupt"]
    marker = SPEZIALIST.get(n) or ()
    if eintrag.get("spezial") and marker:
        blob = " ".join([name or ""] + list(kategorien or [])).lower()
        if any(m in blob for m in marker):
            wort = eintrag["spezial"]
    return f"{wort} {ort.strip().lower()}" if mit_ort else wort


def apply(findings: list, niche: str, is_site: bool = False) -> list:
    """Befunde nach Branche filtern und gewichten. Ohne Profil unveraendert."""
    pr = profile(niche)
    if not pr:
        return findings
    out = []
    for f in findings:
        if f["check"] in pr.get("drop", set()):
            continue
        g = dict(f)
        g["strength"] = min(f["strength"] + pr.get("boost", {}).get(f["check"], 0), 100)
        if is_site:
            g["strength"] = min(g["strength"], pr.get("site_cap", 100))
        out.append(g)
    return sorted(out, key=lambda f: -f["strength"])


def self_check():
    fs = [{"check": "gbp-booking-link", "strength": 60, "kind": "gap"},
          {"check": "gbp-hours", "strength": 88, "kind": "gap"},
          {"check": "gbp-photos", "strength": 55, "kind": "good"}]
    got = apply(fs, "locksmith")
    assert [f["check"] for f in got] == ["gbp-hours", "gbp-photos"], got
    assert got[0]["strength"] == 100, "88+15 deckelt bei 100"
    # eine Branche ohne Profil wird nicht angefasst
    assert apply(fs, "hair-salon") == fs
    assert apply(fs, "") == fs
    # Website-Befunde werden gedeckelt, damit sie kein Notfall-Signal verdraengen
    site = apply([{"check": "web-title", "strength": 95, "kind": "gap"}], "plumber", is_site=True)
    assert site[0]["strength"] == 70, site
    # der Deckel gilt NUR fuer Website-Befunde
    assert apply([{"check": "gbp-claimed", "strength": 95, "kind": "gap"}],
                 "plumber")[0]["strength"] == 100
    print("self-check ok")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        self_check()
    else:
        for n in ("locksmith", "plumber", "hair-salon"):
            print(f"{n:14} {'Notdienst' if profile(n) else 'kein Profil, Standard'}")
