#!/usr/bin/env python3
"""pool.py — Python entscheidet WAS gesagt wird, Sonnet nur noch WIE.

DER ANLASS (Luka, 27.07.2026): "das email writing dauert immer noch deutlich zu lange,
das muss deutlich deutlich schneller werden. wir müssen die findings oder den pool
bereitstellen der von python vorbereitet wurde und dann schreibt sonnet das nur noch
zusammen basierend auf der situation."

Gemessen: drei Mails brauchten 431 Sekunden. Der Agent verbrachte die Zeit nicht mit
Formulieren, sondern mit Entscheiden -- welcher Befund passt, welcher nicht, wie oft
dieselbe Satzform schon vorkam, ob die Antwortquote ein Lob oder ein Mangel ist. Das
sind REGELN, keine Kunst. Sein Beispiel: bei 100% Antwortquote ist "antworte auf
Bewertungen" kein Vorschlag, sondern Unsinn -- und dass der Agent das selbst merken
muss, kostet mehr Zeit als das Formulieren.

WAS HIER ENTSTEHT: je Lead ein Pool aus fertigen Bausteinen. Jeder traegt
  text     -- der Satz, schon zusammengesetzt, nur noch zu glaetten
  staerke  -- wie gut er traegt
  form     -- aufforderung | beobachtung | vergleich   (fuer die Abwechslungsregel)
  blick    -- kohorte | nutzen | nachbar | automatisierbar   (fuer die Blickwinkel-Regel)
und `waehle()` sucht daraus 3 bis 4 aus, die die Regeln erfuellen. Der Agent bekommt die
Auswahl, nicht den Katalog -- er formuliert und entscheidet nichts mehr.

  python3 pool.py --self-check
"""
from __future__ import annotations

import collections
import sys

# Ab hier ist die Antwortquote ein LOB und kein Mangel. Gemessen ueber 150 Leads ist die
# Verteilung zweigipflig: 23% unter 10%, 32% ueber 90%, Median 55%. Wer fast alles
# beantwortet, braucht dazu keinen Rat.
ANTWORT_GUT = 0.8
ANTWORT_SCHLECHT = 0.35


# Die Copy-Regeln aus markt_copy.md. Herausgeloest aus `write_mail.py` am
# 23.08.2026 -- `stapel` holte sie von dort und zog damit den Sonnet-Weg mit.
# Sie gehoeren hierher: dies ist die Datei, die die Copy baut.
import os as _os
import re as _re

HIER = _os.path.dirname(_os.path.abspath(__file__))


def schreibkarte(marker: str = "HARD RULES") -> str:
    """Die Copy-Regeln aus markt_copy.md, der einen Quelle.

    `marker="SCHREIBKARTE"` holt die kurze Karte statt des vollen Blocks -- dieselbe Datei,
    zwei Adressaten: der Mensch liest die Herleitung, der Agent die Karte.

    Sie standen frueher hier als Text-Konstante, waehrend der RAHMEN (welche Bloecke, wer
    schreibt was) schon in markt_copy.md lag. Zwei Orte fuer dieselbe Sache, und genau daraus
    ist an einem Tag zweimal Drift entstanden. Jetzt gibt es eine Datei: wer die Copy aendern
    will, aendert markt_copy.md, und der naechste Lauf schreibt anders.
    """
    md = open(_os.path.join(HIER, "markt_copy.md"), encoding="utf-8").read()
    m = _re.search(r"```\n(" + _re.escape(marker) + r".*?)\n```", md, _re.S)
    if not m:
        raise RuntimeError(f"Block {marker!r} in markt_copy.md nicht gefunden -- "
                           "das System-Prompt waere ohne Regeln losgelaufen")
    return m.group(1)


def _n(v, d=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return d


# Was in welcher Lage traegt. NICHT geraten, sondern aus `knowledge/local-seo-method.md`:
#
#   WER NICHT IN DEN DREI STEHT, hat ein Sichtbarkeitsproblem, und dort bewegen laut
#   Wissensbasis genau drei Dinge etwas: Kategorien (bis 10 erlaubt, die meisten nutzen 1),
#   die Leistungsliste (Ziel 20-30, die meisten haben 7-8, "a top, easy lever") und die
#   Bewertungen ("count and recency are among the strongest map-pack signals"). Fotos,
#   Beitraege und Buchungslink stehen dort ausdruecklich DAHINTER.
#
#   WER DRIN STEHT, wird gesehen. Bei ihm entscheidet, was nach dem Klick passiert: Fotos
#   (das Erste, was er sieht), beantwortete Bewertungen, sichtbare Oeffnungszeiten. Und
#   eine Zeile ist bei ihm sogar schaedlich -- "deine Bewertungszahl liegt unter dem
#   Median" widerspricht seiner eigenen Position und laedt zum Widerspruch ein.
#
# WICHTIG, und es war erst falsch (Luka, 30.07.): "wir muessen die balance finden, dass wir
# nicht nur die findings aus dieser gefilterten perspektive geben, sondern objektiv die
# groessten hebel aus den daten die wir haben". Die erste Fassung hat "deine Bewertungszahl
# liegt unter dem Median" bei jemandem in den drei GANZ unterdrueckt -- und damit womoeglich
# seinen groessten Hebel verschwiegen, nur weil er nicht zur Erzaehlung passte. 8 Bewertungen
# gegen Median 20 sind ein Problem, auch wenn er heute rankt.
#
# DIE REGEL LAUTET DESHALB: die Lage bestimmt die FORMULIERUNG und die genannte Folge, die
# DATENLAGE bestimmt die AUSWAHL. Nur was sich selbst widerspricht, wird umformuliert --
# nichts wird weggelassen, weil es unbequem ist.
#
# Der Wert unten ist nur die BASIS (was fuer eine Art Hebel es in dieser Lage ist). Die
# gemessene Luecke verschiebt sie um bis zu 15 Punkte, siehe staerke().
STAERKE = {
    #                     draussen   drin
    "themen":               (90,      78),
    "leistungen_leer":      (88,      70),
    "kategorien":           (86,      60),
    "bewertungen":          (82,      74),   # drin: andere Folge, nicht weniger wichtig
    "24h":                  (84,      86),   # Notdienst: vor und nach dem Klick stark
    "antworten":            (78,      90),   # sichtbares Vertrauen, nach dem Klick top
    "google_paart":         (76,      80),   # Googles EIGENE Zuordnung, s.u.
    "kategorie_der_besten": (94,      82),   # was die Bestbewerteten fuehren, er nicht
    "nachbar_stark":        (88,      80),   # der Nachbar MIT Zahl, wenn er vorn liegt
    "attribut_weg":         (82,      88),   # das EINZIGE "nimm weg" -- beweist Fachwissen
    "hauptkategorie":       (92,      70),   # laut spec.md der #1-Rankingfaktor des Profils
    "leistungen_duenn":     (74,      64),   # unter 20 Leistungen, Ziel laut Methode 20-30
    "ein_stern":            (68,      84),   # nach dem Klick das Erste, was er liest
    "beschreibung":         (38,      34),   # AUFFUELLER: trifft 99,8% -- stand in 92% aller
                                             # Mails, also derselbe Satz fuer fast jeden. Niedrig
                                             # genug, dass jede gemessene Luecke ihn verdraengt.
    "antworten_gut":        (58,      68),
    "nachbarn":             (40,      50),
    "fotos":                (55,      88),   # die Vitrine, nicht der Rang

    "harte_arbeit_da":      (96,    None),   # sagt woertlich "du rankst nicht" -> nur da
}

# ENTFERNT am 22.08.2026:
#   "posten"  -- `raw.ownerUpdates` ist bei 81% der Leads None (nie gemessen) und bei KEINEM
#                einzigen eine nachweislich leere Liste. "Er postet nicht" ist damit nirgends
#                belegbar; 664 Findings behaupteten es trotzdem. PIPELINE.md § 4b.
#
# NEU am 22.08.2026:
#   "beschreibung"  -- 6 von 3.593 Leads haben eine Profilbeschreibung. Das Feld ist bei ALLEN
#                gemessen, die Luecke also belegt (anders als bei den Beitraegen). Der einzige
#                Baustein, der praktisch jeden Lead trifft -- und genau deshalb mit niedriger
#                Staerke: was jeder bekommt, ist nie die Zeile, die die Mail traegt.
#   "google_paart" -- `raw.peopleAlsoSearch`, bei 52% gefuellt, mit Sternen und Bewertungszahl.
#                Das ist GOOGLES eigene Wettbewerber-Zuordnung, nicht unsere Distanzrechnung.
#                Ein Vergleich, den er selbst in seinem Profil nachsehen kann.

SPANNE = 15        # so viel darf die gemessene Luecke die Basis verschieben

# Die Stichpunkt-Grenze aus markt_copy.md § Schreibkarte (f), seit 22.08. auch mechanisch in
# `verify_mail.check`. Sie steht hier NOCHMAL als Konstante, weil ein Baustein, der sie
# reisst, die ganze Mail durchfallen laesst -- besser hier verwerfen als dort.
MAXLEN = 80

# Jeder Vergleich geht gegen das LAND (n=4.746), nie gegen den Ort -- PIPELINE.md § 4b.
# Gemessen am 22.08.: 42% der 10.692 erzeugten Findings tragen so einen Satz.
import re as _re2
_ORTSVERGLEICH = _re2.compile(
    r"in town|of the \d+ (in|near|nearest)|\d+ (here|round here) |the rest of |"
    r"in \w+ out of|\d+(st|nd|rd|th) in ", _re2.I)


def _variante(b: dict, fassungen: list) -> str:
    """Eine von mehreren gleichwertigen Formulierungen, FEST gewaehlt nach place_id.

    Wozu: ein Baustein, der fast jeden Lead trifft, macht aus einer richtigen Zeile eine
    Schablone -- die Beschreibungszeile stand am 22.08. in 92% aller Mails, Wort fuer Wort
    dieselbe. Vier Fassungen senken das auf ein Viertel, ohne die Aussage zu aendern.

    Nicht `random`: derselbe Lead muss bei jedem Lauf dieselbe Zeile bekommen, sonst laesst
    sich eine verschickte Mail spaeter nicht mehr rekonstruieren. Die place_id ist stabil,
    also ist es ihre Quersumme auch.
    """
    pid = str(b.get("place_id") or "")
    return fassungen[sum(map(ord, pid)) % len(fassungen)] if fassungen else ""


def staerke(id_: str, im_pack: bool, vorgabe: int, groesse: float | None = None):
    """-> Staerke in dieser Lage, oder None wenn der Baustein hier nicht angeboten wird.

    `groesse` ist die gemessene Luecke, 0 bis 1: 0 heisst "kaum daneben", 1 heisst "so weit
    daneben wie es geht". Sie verschiebt die Basis um bis zu SPANNE Punkte in beide
    Richtungen. Damit gewinnt bei zwei Bausteinen derselben Art der mit der groesseren
    Luecke -- und ein kleiner Hebel drueckt keinen grossen aus der Liste.
    """
    paar = STAERKE.get(id_)
    basis = vorgabe if not paar else paar[1 if im_pack else 0]
    if basis is None or groesse is None:
        return basis
    return round(basis + SPANNE * (max(0.0, min(1.0, groesse)) - 0.5) * 2)


def bausteine(b: dict) -> list:
    """Alle Bausteine, die fuer DIESEN Lead zutreffen. Reihenfolge egal, waehle() sortiert.

    Ein Baustein entsteht nur, wenn seine Daten da sind. Fehlt eine Zahl, gibt es den
    Baustein nicht -- er wird nie mit einem Platzhalter gebaut.
    """
    out = []
    kohorte = b.get("kohorte") or {}
    # STEHT ER IN DEN DREI, DIE GOOGLE ZEIGT? Dann aendert sich nicht, WAS fehlt, sondern
    # was es ihn kostet (Luka, 27.07.: "dann geht es halt eher um conversion und darum die
    # platzierung auch zu halten"). Bei Platz 14 kostet eine fehlende Kategorie
    # SICHTBARKEIT. Bei Platz 1 nicht -- der wird gesehen. Bei ihm kostet sie den Auftrag
    # NACH dem Klick. Gemessen: 83% der 690 im Pack haben mindestens eine solche Luecke,
    # 65% posten nicht, 51% haben nur eine Kategorie.
    im_pack = bool(b.get("im_pack"))
    n_kohorte = _n(kohorte.get("betriebe"))
    themen = b.get("themen_der_bewertungen") or {}
    antw = b.get("antworten") or {}

    def add(id_, text, vorgabe, form, blick, groesse=None):
        s = staerke(id_, im_pack, vorgabe, groesse)
        if s is None:                  # sagt woertlich etwas, das hier nicht stimmt
            return
        # HARTE LAENGENSICHERUNG (22.08.2026). `verify_mail` verwirft jeden Stichpunkt ueber
        # 80 Zeichen, und mehrere Bausteine setzen Namen ein, deren Laenge wir nicht kennen
        # ("Timpson Locksmiths & Safe Engineers" ist 35 Zeichen allein). Ein zu langer
        # Baustein wuerde die GANZE Mail durchfallen lassen -- lieber ein Baustein weniger.
        # Sie stumm zu verwerfen ist richtig: `waehle()` hat immer mehr Kandidaten als
        # Plaetze, und ein Lead mit zu wenig Zeilen faellt dem Stapel ohnehin auf.
        if len(text) > MAXLEN:
            return
        out.append({"id": id_, "text": text, "staerke": s,
                    "form": form, "blick": blick})

    # --- Antwortquote: Mangel ODER Lob, nie beides -----------------------------------
    geholt, beantwortet = _n(antw.get("geholt")), _n(antw.get("beantwortet"))
    quote = (antw.get("quote_prozent") or 0) / 100 if antw.get("quote_prozent") is not None else None
    if geholt and quote is not None:
        if quote <= ANTWORT_SCHLECHT:
            # Die UNBEANTWORTETEN sind die Zahl, die traegt -- und sie wird hier gerechnet,
            # nicht vom Modell. Das Rechenverbot (markt_copy) ist stumpf: es hat einen
            # richtigen Satz verworfen ("46 of your last 48 sit unanswered", 48-2). Aber es
            # stammt aus einem echten Schaden -- Haiku schrieb "you need 8 more reviews to
            # hit the median" ueber einen Betrieb MIT 8 Bewertungen bei Median 19. Die
            # Loesung ist nicht, das Rechnen zu erlauben, sondern es hier zu tun.
            offen = geholt - beantwortet
            wie = (f"none of your last {geholt} reviews have a reply" if beantwortet == 0
                   else f"{offen} of your last {geholt} reviews have no reply")
            add("antworten", f"{wie}, answer them, people read those",
                96 if beantwortet == 0 else 88, "beobachtung", "nutzen",
                groesse=1 - quote)
        elif quote >= ANTWORT_GUT:
            # Auch ein Lob braucht seine Folge. Ohne sie ist es eine Bilanzzeile, und
            # verify_mail hat sie zu Recht als "Beobachtung ohne Folge" zurueckgewiesen --
            # der Fehler steckte in MEINEM Baustein, nicht in der Formulierung des Agenten.
            # Dieselbe Korrektur wie bei `harte_arbeit_da`: "so it isn't effort" setzt eine
            # Frage voraus, die die Mail nicht mehr stellt. Als Lob ohne Handlung waere die
            # Zeile in einer Fix-Liste ein verschenkter Platz -- also mit einer.
            add("antworten_gut", f"you reply to {beantwortet} of your last {geholt}, "
                                 f"so say that in the description too",
                70, "beobachtung", "nutzen")

    # --- Was Kunden sagen, steht nicht im Profil --------------------------------------
    # Positiv pruefen, nicht negativ ausschliessen: die schwarze Liste hat viermal
    # verloren (siehe trades.GEWERKS_DINGE). Beides zusammen, der Guertel und die
    # Hosentraeger -- das Gewerks-Ding muss vorkommen UND kein Eigenschaftswort.
    niche = b.get("niche") or "locksmith"
    # "dein Profil nennt beides nicht" muss gegen die ECHTE Leistungsliste geprueft werden.
    # The Security Shop fuehrt 23 Leistungen -- ohne diesen Abgleich behaupten wir bei ihm
    # eine Luecke, die es nicht gibt, und er sieht in zwei Klicks, dass wir nicht nachsahen.
    gelistet = " | ".join(b.get("leistungen_liste") or [])
    eintragbar = [t for t in themen
                  if _ist_leistung(t, niche) and not _ist_eigenschaft(t)
                  and str(t).lower() not in gelistet]
    if eintragbar:
        # EIN Thema, nicht zwei (22.08.): zwei Namen plus Folge sprengen die 80 Zeichen bei
        # jedem laengeren Begriff ("car key replacement" ist allein 19). Ein Thema ist auch
        # die schaerfere Zeile -- es ist SEIN Wort, nicht eine Aufzaehlung.
        # NICHT "nothing under services says X": das kollidiert in `waehle` mit dem
        # Services-Baustein ueber dasselbe Thema und hat die Quote am 22.08. von 17% auf 7%
        # gedrueckt. Der Befund ist ein anderer -- hier geht es um SEIN Wort aus den
        # Bewertungen, nicht um die Vollstaendigkeit der Liste.
        # EIGENE SATZFORM mit Review-Bezug (22.08.): vorher benutzte dieser Baustein
        # dieselbe Formel wie `kategorie_der_besten` ("no X on your profile, add it so
        # those searches land") -- in einer Mail standen beide untereinander und lasen sich
        # wie zweimal derselbe Satz. Sein Alleinstellungsmerkmal ist der Bezug auf SEINE
        # Bewertungen: das sind die Worte seiner Kunden, nicht unsere.
        # MIT DER FOLGE, nicht nur mit dem Rat (23.08.): "so add it" sagt nicht, was er
        # davon hat. Der Punkt ist, dass Kunden diese Worte benutzen -- also sucht auch
        # jemand danach, und findet ihn nicht.
        add("themen", _variante(b, [
            f"your reviews say {eintragbar[0]} and your profile doesn't, add it so it lands",
            f"no {eintragbar[0]} on the profile though your reviews do, add it so you match",
            f"customers write {eintragbar[0]}, your profile doesn't, add it so it lands",
        ]),
            95, "beobachtung", "nutzen")

    # --- Leistungsliste gegen die Nachbarschaft ---------------------------------------
    # DUENN ist auch eine Luecke, nicht nur LEER (22.08.2026, Luka: "wir haben ja gar nicht
    # drin, ob er genug services drin hat"). `spec.md § 3` nennt 10-30 als Ziel, die
    # Wissensbasis 20-30. Gemessen ueber 2.137 Leads mit Leistungsdaten: Median 23, aber
    # **46% liegen unter 20** und 32% unter 10. Bisher feuerte der Baustein nur bei ==0,
    # also bei 16% -- zwei Drittel der Luecke blieben ungenutzt.
    #
    # MIT DEM LANDESMEDIAN, seit 23.08.2026 (Luka: "die sektion hat keinen vergleich oder
    # keine erklaerung warum sie das aendern sollten"). "add more" ist eine Aufforderung
    # ohne Massstab -- acht Leistungen koennen viel oder wenig sein, das weiss der
    # Empfaenger nicht. "where most run 24" beantwortet das in vier Woertern, und die Zahl
    # kennt er sonst nirgendwo her. Ohne gemessenen Median faellt der Vergleich weg, statt
    # eine Zahl zu behaupten.
    n_leist = b.get("leistungen_im_profil")
    l_med = _n(b.get("uk_median_leistungen"))
    if n_leist is not None and 0 < n_leist < 20:
        add("leistungen_duenn", _variante(b, [
            (f"you list {n_leist} services where most run {l_med}, add more so the rest show"
             if l_med else
             f"only {n_leist} services listed, add more so you match more searches"),
            (f"{n_leist} services listed where most run {l_med}, add more so those jobs land"
             if l_med else
             f"you list {n_leist} services, add more so you turn up for what people type"),
        ]), 74, "beobachtung", "nutzen", groesse=1 - n_leist / 20)
    if n_leist == 0:
        # "nothing is listed under services" sagt, was FEHLT, nicht was er tun kann
        # (Luka, 27.07.: "das Problem ist, dass sowas nicht action orientiert ist und
        # ihnen sagt, was sie tun koennen"). Die Aufgabe gehoert nach vorn.
        mit = f" where most run {l_med}" if l_med else ""
        add("leistungen_leer", _variante(b, [
            f"nothing under services{mit}, add five so those jobs find you",
            f"your services list is empty{mit}, add five so those searches reach you",
            f"no services listed{mit}, add the jobs you get called for so they land",
            f"you've got no services{mit}, put in five so google can match them",
        ]), 85, "aufforderung", "nutzen")

    # --- Fotos: bei ihm ist es die Vitrine, nicht die Sichtbarkeit --------------------
    # Gegen den LANDESMEDIAN, nicht gegen "die anderen hier" (PIPELINE.md § 4b): wir kennen
    # den Ort nur ausschnittsweise, das Land ueber n=4.746.
    fotos, fmed = _n(b.get("fotos")), _n(b.get("uk_median_fotos")) or 14
    if fotos is not None and fotos < fmed:
        wie = "one photo" if fotos == 1 else f"{fotos} photos"
        text = (f"there's {wie} on your listing, add a dozen so people see the work"
                if fotos <= 3 else
                f"you're on {wie} where most have {fmed}, add a dozen so yours stands out")
        add("fotos", text, 78, "beobachtung", "nutzen" if im_pack else "kohorte",
            groesse=1 - fotos / max(fmed, 1))

    # --- Kategorien -------------------------------------------------------------------
    # Schwelle 4 statt 2 (22.08.2026): Google erlaubt 10, und **84% der Leads nutzen unter 5**
    # -- gegen 58% bei der alten Zwei-Grenze. Das sind 26 Prozentpunkte mehr Leads mit einem
    # belegten Befund, ohne einen Cent Mehrkosten. Ab 5 gesetzten Kategorien ist die Liste
    # ordentlich gefuellt und der Rat waere Erbsenzaehlerei.
    # KURZ GENUG, und das war er nicht (Fix 22.08.2026): "only 4 of google's 10 categories
    # are set, add the ones you work in so more searches hit" sind **87 Zeichen** -- die
    # Laengensicherung in `add` hat den Baustein damit bei JEDEM Lead stumm verworfen,
    # obwohl 84% ihn gebraucht haetten. Kein Fehler, keine Meldung, nur ein Befund, den
    # niemand mehr bekam. Gefunden hat es `mail_audit.py` beim ersten Lauf: "feuert bei 0%,
    # obwohl die Daten bei 100% vorliegen".
    n_kat = _n(b.get("kategorien"))
    if n_kat and n_kat <= 4:
        # DIE FOLGE IST ZAEHLBAR (23.08.): "so more searches hit" gilt fuer jede Zeile
        # der Mail und sagt deshalb nichts. Jede ungenutzte Kategorie ist eine Art Auftrag,
        # fuer die er nicht erscheint -- das sind bei vier gesetzten sechs Stueck, und die
        # Zahl steht im Satz.
        offen_kat = 10 - n_kat
        add("kategorien", _variante(b, [
            f"{n_kat} of 10 categories set, add the rest so {offen_kat} more job types find you",
            f"{n_kat} of google's 10 categories used, add more so {offen_kat} job types find you",
        ]), 80, "beobachtung", "nutzen", groesse=(10 - n_kat) / 9)

    # --- Die HAUPTkategorie, nicht nur ihre Anzahl ------------------------------------
    # `spec.md § 2`: "Primary category is the #1 ranking factor -- get it exactly right",
    # und die Methode sagt "mirror the winning primary". Bisher zaehlten wir nur, WIE VIELE
    # Kategorien gesetzt sind (Luka, 22.08.: "wir haben ja gar nicht drin, ob die
    # Leistungskategorie richtig angegeben ist").
    #
    # Gemessen ueber 2.744 Leads: 73% fuehren "Locksmith" als erste, 13% "Emergency
    # locksmith service" -- und **26% etwas ganz anderes**, von "Hardware store" bis
    # "Property maintenance". Wer als Schluesseldienst unter "Hardware store" laeuft, taucht
    # bei der Schluesseldienst-Suche schlechter auf. Das ist der staerkste Hebel im ganzen
    # Profil und er kostet nichts: die haeufigste Hauptkategorie der Kohorte steht in
    # unseren eigenen Daten.
    #
    # NUR wenn wir die Kohorten-Mehrheit kennen -- sonst waere es eine Behauptung darueber,
    # was "richtig" ist. `waehle` sorgt dafuer, dass sie nicht neben der Anzahl-Zeile steht.
    haupt, ueblich = b.get("hauptkategorie"), b.get("uebliche_hauptkategorie")
    if haupt and ueblich and haupt.lower() != ueblich.lower():
        add("hauptkategorie", _variante(b, [
            f"only 1 main category and it's {haupt.lower()}, switch it so more find you",
            f"only 1 profile category and it says {haupt.lower()}, set it to {ueblich.lower()}",
        ]), 92, "beobachtung", "kohorte")

    # --- Welche Kategorie die BESTBEWERTETEN fuehren und er nicht ----------------------
    # Der staerkste Befund, den diese Pipeline hergibt (22.08.2026). Kein Mangel ("dir
    # fehlt X"), sondern ein Wettbewerbs-Befund: DIE, DIE VOR DIR STEHEN, fuehren X.
    #
    # Und er kostet nichts extra. `gbp-setup/spec.md` schreibt ausdruecklich "competitor
    # categories are NOT pulled" und laesst sie per WebSearch nachholen -- bei uns fallen
    # sie aus dem Regions-Scrape, den wir ohnehin fahren. Das ist der strukturelle Vorteil
    # dieser Pipeline gegenueber einem Einzel-Audit.
    #
    # Gemessen ueber 900 Leads: **71%** fehlt eine Kategorie, die mindestens zwei der fuenf
    # Bestbewerteten fuehren. Haeufigste: "Emergency locksmith service" (321).
    fehlende = b.get("kategorie_der_besten")
    if fehlende:
        # WER "SIE" SIND, STEHT JETZT IM SATZ (23.08.2026, Luka: "keine erklaerung warum
        # sie das aendern sollten"). "add it to match them" liess offen, wer them ist --
        # der staerkste Befund der Pipeline las sich damit wie ein beliebiger Mangel. Die
        # Bestbewerteten zu nennen ist der ganze Punkt: nicht "dir fehlt X", sondern "die,
        # die vor dir stehen, fuehren X".
        # Die Kategorie kann lang sein ("Emergency locksmith service" = 27 Zeichen), und
        # ueber 80 verwirft `add` still. Deshalb steht die kuerzeste Fassung zuerst: faellt
        # die gewaehlte Variante durch, greift bei diesem Lead eben eine andere Zeile.
        # KEIN SUPERLATIV ueber den Ort (markt_copy.md, Schreibkarte d): "the best rated
        # near you" behauptet, wir kennten alle -- wir kennen den Ort nur ausschnittsweise
        # (Bedford 11 von 27). "several near you" sagt genau das, was wir gemessen haben.
        # `verify_mail` hat den ersten Entwurf am 23.08. dafuer durchfallen lassen.
        # JEDE FASSUNG NENNT DEN NUTZEN (23.08.2026, Luka: "'so add it' sollte nie
        # alleinstehen, es sollte immer auch kommuniziert werden was der benefit ist").
        # Vorher endeten alle vier auf der nackten Aufforderung -- formal eine Folge, weil
        # ein "so" davor stand, inhaltlich keine. `fact_sheet.formel` faengt das jetzt.
        kat = fehlende.lower()
        add("kategorie_der_besten", _variante(b, [
            f"several near you list {kat} and you don't, add it so those jobs reach you",
            f"others near you list {kat}, yours doesn't, add it and you show there too",
            f"no {kat} on your profile where others have it, add it so you match",
            f"{kat} is missing on yours, add it so those searches find you",
        ]), 94, "vergleich", "nachbar")

    # --- Ein Attribut, das WEG muss statt dazu ----------------------------------------
    # `spec.md § 7`, woertlich: "Counter-intuitive: REMOVE 'onsite services' and 'online
    # appointment' attributes -- they push reviews out of view on the profile." Gemessen:
    # **22%** der Leads haben es gesetzt.
    #
    # Der wertvollste Satz der ganzen Mail, und zwar wegen seiner Richtung: jeder schreibt
    # "dir fehlt etwas". Wer sagt "nimm etwas WEG, und zwar aus diesem Grund", beweist in
    # einer Zeile, dass er die Oberflaeche kennt -- das kann keine Vorlage.
    if b.get("onsite_attribut"):
        add("attribut_weg", _variante(b, [
            "no onsite services attribute needed, switch it off so your reviews show higher",
            "nothing gained from the onsite services attribute, switch it off so reviews show",
        ]), 82, "aufforderung", "nutzen")

    # --- Die Profilbeschreibung: die Luecke, die fast jeder hat ------------------------
    # 6 von 3.593 Locksmiths haben eine. Das Feld ist bei ALLEN gemessen, die Luecke also
    # belegt -- der Unterschied zu den Beitraegen, wo `None` steht und wir nichts wissen.
    if b.get("beschreibung_da") is False:
        # VIER FASSUNGEN, fest gewaehlt nach place_id (22.08.). Mit nur einer stand derselbe
        # Satz in 92% aller Mails -- richtig, nuetzlich und trotzdem eine Schablone. Die Wahl
        # haengt am place_id und nicht am Zufall, damit derselbe Lead bei einem zweiten Lauf
        # dieselbe Zeile bekommt; sonst laesst sich eine verschickte Mail nie rekonstruieren.
        # ALS VORSPRUNG FORMULIERT, nicht als Mangel (23.08.). 6 von 3.593 Locksmiths
        # haben eine Beschreibung. Eine Luecke, die fast alle teilen, ist kein Vorwurf
        # sondern die billigste Gelegenheit im ganzen Profil -- und genau so liest sie sich
        # auch besser. Zwei der vier Fassungen tragen den Vorsprung, zwei bleiben sachlich,
        # damit nicht jede Mail denselben Dreh hat.
        add("beschreibung", _variante(b, [
            "the description field is empty, fill it and you're ahead of nearly everyone",
            "there's no description on your profile, write one so searches match you",
            "almost nobody fills the description, so writing one puts you in front",
            "your profile has no description, add one so google knows what you do",
        ]), 38, "aufforderung", "nutzen")

    # --- Die Ein-Stern-Bewertungen ----------------------------------------------------
    # `raw.reviewsDistribution` ist bei 94% der Leads da, 35% haben mindestens eine
    # Ein-Stern-Bewertung. Formuliert als GELEGENHEIT, nicht als Vorwurf (Schreibkarte,
    # Ton): eine unbeantwortete schlechte Bewertung ist das, was ein Anrufer zuerst liest,
    # und eine Antwort darauf kostet ihn zwei Minuten.
    # Ein- UND Zwei-Sterne zusammen (22.08.): eine Zwei-Sterne-Bewertung ohne Antwort liest
    # sich fuer den naechsten Anrufer genauso wie eine Ein-Stern-Bewertung. Getrennt gezaehlt
    # greift der Baustein bei 35%, zusammen bei 39% -- vier Punkte ohne Mehrkosten.
    verteilung = b.get("sterne_verteilung") or {}
    eins = _n(verteilung.get("oneStar")) + _n(verteilung.get("twoStar"))
    if eins:
        # Singular und Plural getrennt, sonst steht da "one review sits at one star, reply
        # to them" -- ein Grammatikfehler in 13% aller Mails.
        text = (_variante(b, [
            "one review sits at one or two stars, reply to it, people read those first",
            "you've got one bad review with no reply, answer it, that's what people read",
            "there's one review at the bottom of the scale, reply to it before anyone rings",
        ]) if eins == 1 else _variante(b, [
            f"{eins} reviews sit at one or two stars, reply to them, people read those",
            f"you've got {eins} bad reviews, answer them, that's what people read first",
            f"{eins} of your reviews are one or two stars, reply before anyone rings",
        ]))
        add("ein_stern", text, 74, "beobachtung", "nutzen", groesse=min(1.0, eins / 5))

    # --- Wen Google SELBST neben ihn stellt -------------------------------------------
    # `peopleAlsoSearch`, bei 52% gefuellt. Staerker als unsere Distanzrechnung: diesen
    # Vergleich hat Google gezogen, nicht wir, und er kann ihn im eigenen Profil nachsehen.
    # MIT HANDLUNG, sonst ist es eine Bilanzzeile: die Liste kuendigt Fixes an, also muss
    # auch der Vergleich sagen, was er tun kann. Nur wenn der andere WIRKLICH vorne liegt --
    # "sie haben 12 zu deinen 80" waere kein Argument, sondern ein Eigentor.
    gp = b.get("google_paart") or {}
    meine_b = _n(b.get("meine_bewertungen"))
    if gp.get("name") and gp.get("bewertungen") and meine_b and gp["bewertungen"] > meine_b:
        # Beide Fassungen brauchen ein "so" vor der Handlung: ohne Bindewort sieht
        # `fact_sheet.formel` keine Folge und verwirft die Zeile. Der zweiten fehlte es,
        # und sie hat am 22.08. eine von fuenf Probemails durchfallen lassen.
        add("google_paart", _variante(b, [
            f"google puts you next to {gp['name']} on {gp['bewertungen']} reviews, "
            f"so ask your next ten",
            f"{gp['name']} shows up beside you on {gp['bewertungen']} reviews, "
            f"so ask ten more customers",
        ]), 76, "vergleich", "nachbar")

    # --- 24 Stunden -------------------------------------------------------------------
    # Der Vergleich geht gegen das LAND (53% zeigen 24h), nicht gegen die Kohorte im Ort.
    # Bedingung gegen das LAND, nicht gegen die Ortskohorte (Fix 22.08.2026). Sie hing an
    # `kohorte.mit_24h` -- einem Feld, das seit der Umstellung auf Landesvergleiche niemand
    # mehr befuellt. Der Baustein feuerte damit bei KEINEM einzigen Lead, obwohl 49% keine
    # 24 Stunden zeigen und der Text laengst landesbasiert formuliert ist. Ein stiller
    # Ausfall: kein Fehler, keine Meldung, nur ein Befund, den niemand mehr bekam.
    hat_stunden = bool(b.get("oeffnungszeiten_gemessen"))
    if hat_stunden and not b.get("zeigt_24h"):
        # OHNE DEN ZUSATZ EMPFEHLEN WIR IHM, NICHT ZU SCHLAFEN (Luka, 27.07.: "wenn wir
        # empfehlen 24 hour opening, dann sollten wir danach in Klammern schreiben (have
        # an automated response system / AI agent to take care of all leads)"). "Mach 24
        # Stunden auf" heisst fuer einen Ein-Mann-Betrieb, um zwei Uhr nachts ans Telefon
        # zu gehen. Der Zusatz macht den Rat erst ausfuehrbar -- und laesst nebenbei
        # durchblicken, dass es dafuer jemanden gibt.
        # VIER FASSUNGEN (22.08.): mit nur einer stand dieser Satz in 47% aller Mails --
        # der Baustein greift bei 49% der Leads und war damit die groesste Schablone im
        # ganzen Bestand. Der Automatisierungs-Hinweis steckt in einer davon: "mach 24
        # Stunden auf" heisst fuer einen Ein-Mann-Betrieb sonst, um zwei Uhr nachts ans
        # Telefon zu gehen (Luka, 27.07.).
        # MIT DEM LANDESANTEIL in zwei der vier Fassungen (23.08.): 53% zeigen 24 Stunden,
        # gemessen ueber 4.530 Profile mit Oeffnungszeiten. "mach 24 Stunden auf" ist ein
        # Rat, "die Haelfte der Branche macht das und du nicht" ist ein Grund.
        # OHNE die nackte Prozentzahl: "53%" steht in keinem Datenblatt, das der
        # Empfaenger nachschlagen kann, und `verify_mail` verwirft eine Prozentangabe, die
        # der Brief nicht belegt -- zu Recht. "half the trade" sagt dasselbe und ist bei
        # 53% wahr. Und die HANDLUNG bleibt drin: ohne sie ist es eine Bilanzzeile.
        anteil = _n(b.get("uk_anteil_24h"))
        haelfte = anteil and anteil >= 45
        add("24h", _variante(b, [
            ("half the trade shows 24 hours and you don't, set yours so the 2am jobs land"
             if haelfte else
             "set your hours to 24 hours so you show up for the 2am searches"),
            "your hours are not set to 24, switch them so the night calls find you",
            ("most of the trade shows 24 hours, set yours so the night calls reach you"
             if haelfte else
             "no 24 hour opening on the profile, set it and the 2am jobs reach you"),
            "set your hours to 24 hours so the night calls stop going elsewhere",
        ]),
            90, "aufforderung", "automatisierbar")

    # --- Der harte Teil ist erledigt, der leichte fehlt ------------------------------
    # Die Prospect-Regel des Experten (knowledge/local-seo-method.md): wer VIELE
    # Bewertungen hat und trotzdem nicht rankt, hat den langsamen Teil hinter sich und
    # den schnellen offen. Das ist die staerkste Geschichte, die unsere Daten hergeben,
    # und sie gilt genau in einer Lage -- deshalb None fuer "drin" in STAERKE.
    meine, median = _n(b.get("meine_bewertungen")), _n(b.get("uk_median_bewertungen"))
    if meine and median and meine >= median * 2:
        # ENTFERNT als eigener Satz am 22.08.2026 (Luka): "so it isn't reputation" beantwortet
        # die Frage "warum ranke ich dann nicht" -- und die stellt die Mail nicht mehr, seit
        # das Positions-Statement raus ist. Ohne diese Vorbedingung haengt der Satz in der
        # Luft: es ist nicht die Reputation, WAS ist nicht die Reputation?
        #
        # Die Staerke bleibt trotzdem drin, aber als KONTRAST im selben Satz, mit einer
        # Handlung dahinter. Genau die Cross-Reference-Zeile, die `fact_sheet.py` als das
        # beschreibt, was ein Einzelbaustein sonst nicht kann.
        # Der Kontrast wird IMMER angeboten, auch wenn ein Einzelbaustein dieselbe Luecke
        # nennt. Dass beide nicht zusammen in EINE Mail duerfen, entscheidet `waehle()` --
        # dort, wo ohnehin ausgewaehlt wird. Der erste Anlauf liess ihn hier ausweichen und
        # kostete 9 Prozentpunkte Abdeckung (75% -> 66%): eine Regel an der falschen Stelle
        # verwirft mehr, als sie schuetzt.
        kontrast = None
        if b.get("leistungen_im_profil") == 0:
            kontrast = f"{meine} reviews and no services listed, add five so those searches land"
        elif b.get("beschreibung_da") is False:
            kontrast = f"{meine} reviews and no description, add one so google can read it"
        elif fotos is not None and fotos < fmed:
            kontrast = f"{meine} reviews and only {fotos} photos, add a dozen so yours stands out"
        if kontrast:
            add("harte_arbeit_da", kontrast, 98, "vergleich", "kohorte",
                groesse=min(1.0, meine / (median * 5)))

    # --- Bewertungszahl gegen den Landesmedian ---------------------------------------
    if meine and median and meine < median:
        # DIE LAGE AENDERT DIE FOLGE, NICHT DIE TATSACHE. Wer in den drei steht, hoert
        # nicht "das haelt dich zurueck" -- er steht ja vorn. Bei ihm ist es der Punkt,
        # an dem er den Platz verliert, sobald jemand nachzieht. Weggelassen wird der
        # Befund nie: 8 gegen 20 ist der groesste Hebel, den dieser Lead hat.
        folge = "ask your next ten so you match them"
        add("bewertungen", f"you're on {meine} reviews where most have {median}, {folge}",
            72, "beobachtung", "kohorte", groesse=(median - meine) / median)

    # --- Wer direkt neben ihm sitzt ---------------------------------------------------
    # EIN Name, nicht zwei: "Timpson Locksmiths & Safe Engineers" ist allein 35 Zeichen, und
    # zwei davon reissen die 80 immer. Die Laengensicherung in `add` faengt den Rest.
    # Der Nachbar MIT Entfernung und Handlung (22.08., zweiter Anlauf).
    #
    # Erste Fassung war "x sits right by you, that's who people compare you to" -- eine reine
    # Beobachtung, und die Liste kuendigt Fixes an. Ich habe ihn daraufhin ganz gestrichen,
    # und das war der Fehler: er stand in 51% der Mails und trug den einzigen Satz mit einem
    # ECHTEN NAMEN darin. Ohne ihn fiel die Abdeckung von 90% auf 67% und die Zahl
    # verschiedener Saetze von 2.103 auf 653 -- aus einer personalisierten Mail wurde eine
    # Serienmail. Ein Baustein zu streichen ist billig, seine Varianz nicht.
    #
    # Jetzt traegt er die gemessene Entfernung (Status quo) und eine Handlung. Die Distanz
    # steht in `details.nearest[].km`, ist also gemessen und keine Behauptung.
    nachbarn = [x for x in (b.get("nachbarn") or []) if x]
    n_km = b.get("nachbar_km")

    # ZUERST der Vergleich mit ZAHL, wenn der Nachbar deutlich vorn liegt (22.08.2026).
    #
    # Die Frage war: vergleichen wir gegen den Landesmedian oder gegen den naechsten
    # Wettbewerber? Antwort aus den Daten: BEIDES, nach Lage. Gemessen ueber 2.744 Leads
    # hat der naechste Nachbar bei **35%** mehr Bewertungen, bei **23%** mindestens doppelt
    # so viele (Median-Faktor **7,5x**) -- aber bei **37%** WENIGER. Ihn dort zu nennen
    # waere ein Eigentor, und bei 25% haben wir gar keinen in den Daten.
    #
    # Also: der Nachbar geht vor, WENN er ein Argument ist. Sonst traegt der Landesmedian,
    # der immer da und nie widerlegbar ist. Der Nachbarname macht den Vergleich konkret --
    # eine Zahl kann jeder behaupten, den Namen des Betriebs 700 Meter weiter nicht.
    n_bew, meine_b = _n(b.get("nachbar_bewertungen")), _n(b.get("meine_bewertungen"))
    weite_txt = b.get("nachbar_entfernung") or ""
    if nachbarn and weite_txt and n_bew and meine_b and n_bew >= meine_b * 2:
        add("nachbar_stark", _variante(b, [
            f"{nachbarn[0].lower()} is {weite_txt} away on {n_bew} reviews, "
            f"so ask your next ten for one",
            f"the one {weite_txt} from you is on {n_bew} reviews, "
            f"so ask your next ten customers",
        ]), 88, "vergleich", "nachbar")

    if nachbarn and n_km:
        n0 = nachbarn[0].lower()
        meter = int(round(n_km * 1000 / 100.0)) * 100
        weite = f"{meter}m" if meter < 1000 else f"{round(n_km, 1)}km"
        add("nachbarn", _variante(b, [
            f"{n0} is {weite} away, so get your profile ahead of theirs",
            f"{n0} sits {weite} from you, add what they have and you pull ahead",
        ]), 55, "beobachtung", "nachbar")

    # --- Was findings.py sonst gefunden hat -------------------------------------------
    # Nur, was oben nicht schon steht. Sonst standen "your reviews name tap repair..."
    # und "your reviews keep saying toilet repair..." nebeneinander in derselben Auswahl:
    # zwei Zeilen ueber dieselbe Sache, aus zwei Quellen.
    schon = " ".join(x["text"].lower() for x in out)
    # Leistungsliste und Kategorien sagen beide "dein Profil nennt zu wenig". In einer
    # Mail standen sie nebeneinander und lasen sich wie zweimal derselbe Vorwurf.
    if any(x["id"] == "leistungen_leer" for x in out):
        out = [x for x in out if x["id"] != "kategorien"]
    DOPPELT = {"themen": ("reviews keep saying", "reviews name"),
               "24h": ("24 hour", "24 hours"), "posten": ("post",),
               "bewertungen": ("uk median",)}
    for i, g in enumerate(b.get("luecken") or []):
        satz = f"{g['was']}, so {g['folge']}"
        # Die Marker einer Gruppe sind VARIANTEN derselben Aussage. Geprueft werden muss
        # deshalb "irgendein Marker im neuen Satz UND irgendein Marker im schon Gesagten",
        # nicht derselbe in beiden. Sonst standen "your reviews name lock change..." und
        # "your reviews keep saying back door lock repair..." nebeneinander in derselben Mail.
        if any(any(m in satz.lower() for m in marker) and any(m in schon for m in marker)
               for marker in DOPPELT.values()):
            continue
        # KEIN ORTSVERGLEICH (22.08.2026, PIPELINE.md § 4b). Diese Saetze kommen roh aus
        # `enrich_cohort_findings` und tragen bei 42% einen Vergleich gegen den ORT --
        # "your profile does not show 24 hours, where 6 in town do". Wir kennen den Ort nur
        # ausschnittsweise (Bedford 11 von 27, Hornchurch 1 von 20), also ist der Satz in
        # Sekunden widerlegbar. Bis die Findings selbst auf den Landesvergleich umgestellt
        # sind, faellt er HIER weg statt in der Mail zu landen.
        if _ORTSVERGLEICH.search(satz):
            continue
        add(f"luecke_{i}", satz, 50 - i, "beobachtung", "kohorte")
    return out



def _weite(nearest: list) -> str:
    """Entfernung des naechsten Nachbarn als fertige Wendung: "700m" oder "1.2km".

    Auf 100 Meter gerundet und ZEICHENGLEICH mit `fact_sheet._nachbar_weite` -- beide
    muessen dieselbe Zeichenfolge erzeugen, sonst verwirft `verify_mail` die Zahl als
    erfunden, obwohl sie im Blatt steht.
    """
    km = next((n.get("km") for n in (nearest or []) if n.get("km")), None)
    if not km:
        return ""
    meter = int(round(km * 1000 / 100.0)) * 100
    return f"{meter}m" if meter < 1000 else f"{round(km, 1)}km"


def _staerkster_paar(pas) -> dict:
    """Aus `raw.peopleAlsoSearch` der Vorschlag mit den meisten Bewertungen.

    Google listet dort, wen es neben den Betrieb stellt -- mit Sternen und Anzahl. Genommen
    wird der staerkste: "google shows you next to X, they're on 392 reviews to your 61" ist
    ein Argument, derselbe Satz mit einem Schwaecheren waere keins. Ohne Bewertungszahl kein
    Baustein -- ein Name allein traegt den Vergleich nicht.
    """
    kandidaten = [p for p in (pas or [])
                  if isinstance(p, dict) and (p.get("title") or "").strip()
                  and isinstance(p.get("reviewsCount"), int) and p["reviewsCount"] > 0]
    if not kandidaten:
        return {}
    best = max(kandidaten, key=lambda p: p["reviewsCount"])
    return {"name": best["title"].strip().lower(), "bewertungen": best["reviewsCount"],
            "sterne": best.get("totalScore")}




# Kategorien, die kein Argument sind: Google-Sammelbegriffe ohne Aussage ueber das Gewerk.
# "Service establishment" fuehren 95 der 900 gemessenen Top-Profile -- als Rat waere es
# Unsinn ("trag ein, dass du ein Betrieb bist"). Gefiltert wird auf der Empfehlungsseite,
# nicht beim Messen: sie sagen etwas ueber die Kohorte, nur nichts, was er tun sollte.
GENERISCH = {"service establishment", "establishment", "business", "store", "shop",
             "hardware store", "general contractor", "contractor"}


def kategorie_der_besten(lead_kategorien, leader_cats: dict, mindestens: int = 2):
    """Die staerkste Kategorie, die mehrere Bestbewertete fuehren und der Lead nicht hat.

    `leader_cats` kommt aus `market_context` und zaehlt, wie viele der fuenf meistbewerteten
    Betriebe der Kohorte eine Kategorie fuehren. Genommen wird die haeufigste, die der Lead
    NICHT hat -- ab `mindestens` Nennungen, damit es ein Muster ist und nicht die Eigenart
    eines einzelnen Betriebs.
    """
    hat = {str(c).lower() for c in (lead_kategorien or [])}
    kandidaten = [(n, c) for c, n in (leader_cats or {}).items()
                  if n >= mindestens and str(c).lower() not in hat
                  and str(c).lower() not in GENERISCH]
    return max(kandidaten)[1] if kandidaten else None


def _onsite_attribut(zusatz) -> bool:
    """Ist das Attribut "Onsite services" gesetzt? (`spec.md` sagt: gehoert entfernt.)"""
    if not isinstance(zusatz, dict):
        return False
    for gruppe in zusatz.values():
        for eintrag in (gruppe or []):
            if isinstance(eintrag, dict):
                for k, v in eintrag.items():
                    if v and "onsite service" in str(k).lower():
                        return True
    return False


def _tags_zu_themen(tags) -> dict:
    """`raw.reviewsTags` -> dasselbe Format wie DataForSEOs `place_topics`.

    Apify liefert eine Liste `[{"title": "car key replacement", "count": 5}, ...]`, die
    Themen, die Google aus den echten Bewertungen zieht. Das ist dieselbe Information wie
    `place_topics`, nur aus dem GBP-Scraper statt aus einer zweiten, kostenpflichtigen
    Quelle -- und mit besserer Abdeckung.
    """
    out = {}
    for t in (tags or []):
        if isinstance(t, dict) and (t.get("title") or "").strip():
            out[t["title"].strip().lower()] = t.get("count") or 1
        elif isinstance(t, str) and t.strip():
            out[t.strip().lower()] = 1
    return out


def aus_lead(x: dict, mk: dict, bench: dict, niche: str = "locksmith") -> dict:
    """Eine Supabase-Zeile -> die Eingabe fuer `bausteine`. Die fehlende Verdrahtung.

    `pool.py` stand seit dem 27.07. fertig da und hatte im ganzen Repo keinen einzigen
    Aufrufer -- deshalb sahen die elf Bedford-Mails noch aus wie vor dem Umbau. Diese
    Funktion ist das Stueck dazwischen.

    DIE WEBSITE BLEIBT DRAUSSEN (Luka, 28.07.). `findings` traegt je Befund ein `area`,
    also faellt sie mit einem Filter weg statt mit einer Wortliste. Das ist auch das
    fuenfte Verbot der Schreibkarte: wir messen sie nicht mehr, also reden wir nicht
    darueber.
    """
    raw, rd = (x.get("raw") or {}), (x.get("raw_dataforseo") or {})
    ws = x.get("web_signals") or {}
    antw = rd.get("antworten") or {}
    rang = ws.get("rank") or {}
    return {
        # fuer `_variante`: dieselbe Zeile bei jedem Lauf, siehe dort
        "place_id": x.get("place_id") or "",
        "niche": niche,
        # Dieselbe Quelle wie `rang_block`: der gemessene Kasten-Platz. Stand bis 30.07.
        # auf `pack_rank`, das der umgebaute `rank_pull.py` nicht mehr schreibt -- damit
        # war `im_pack` fuer JEDEN frisch gemessenen Lead False, und Auto Keys (Platz 1)
        # bekam neben "you're the first name google shows" die Tipps fuer einen, der
        # nicht im Kasten steht ("you only show up for one kind of search").
        "im_pack": bool(rang.get("kasten_platz")),
        "antworten": {"geholt": antw.get("geholt"), "beantwortet": antw.get("beantwortet"),
                      "quote_prozent": (None if antw.get("quote") is None
                                        else round(antw["quote"] * 100))},
        # AUS DEM GBP-SCRAPER, nicht aus DataForSEO (22.08.2026, Luka: "wir nutzen nur die
        # Daten aus dem Google-Business-Profil-Scraper mit den Details"). Apifys eigenes
        # `reviewsTags` deckt sogar besser ab als DataForSEOs `place_topics`: 72% gegen 69%
        # ueber die 2.744 anschreibbaren Leads. `place_topics` bleibt als Rueckfall fuer die
        # Altbestaende, die noch keinen Detail-Scrape hatten.
        "themen_der_bewertungen": (_tags_zu_themen(raw.get("reviewsTags"))
                                   or rd.get("place_topics") or {}),
        # None wenn DataForSEO fuer diesen Lead nie lief -- NICHT 0. `len(None or [])` ergibt
        # 0, und daraus wurde "there's nothing under services" bei einem Betrieb, dessen
        # Leistungsliste wir schlicht nie abgefragt haben. Gemessen am 22.08.: der Baustein
        # feuerte dadurch bei praktisch jedem Lead und loeschte ueber die Dopplungsregel den
        # Kategorien-Baustein gleich mit -- 349 von 400 Leads verloren ihn stillschweigend.
        "leistungen_im_profil": (None if rd.get("services") is None
                                 else len(rd["services"])),
        "fotos": raw.get("imagesCount"),
        "kategorien": len(raw.get("categories") or []),
        # Die ERSTE Kategorie ist Googles Hauptkategorie -- laut spec.md der wichtigste
        # Rankingfaktor des Profils. Die "uebliche" kommt aus der Kohorte und wird von
        # `aus_lead`s Aufrufer durchgereicht (mk["primary"]), damit wir nicht behaupten,
        # was richtig ist, sondern zeigen, was die anderen tun.
        "hauptkategorie": (raw.get("categories") or [None])[0],
        "uebliche_hauptkategorie": mk.get("primary"),
        "kategorie_der_besten": kategorie_der_besten(raw.get("categories"),
                                                     mk.get("leader_cats")),
        "onsite_attribut": _onsite_attribut(raw.get("additionalInfo")),
        "meine_bewertungen": raw.get("reviewsCount"),
        "sterne": raw.get("totalScore"),
        # fuer "what's working well": Punkte, die fast jeder hat und die deshalb NICHT in den
        # Score gehoeren (sie trennen nicht), hier aber die Liste fuellen
        "beansprucht": not raw.get("claimThisBusiness"),
        "telefon": bool(raw.get("phone") or raw.get("phoneUnformatted")),
        "website": bool(raw.get("website")),
        "uk_median_bewertungen": ((bench.get("reviews") or {}).get("median")),
        "uk_median_fotos": bench.get("photos_median"),
        "uk_median_leistungen": bench.get("services_median"),
        "uk_anteil_24h": ((bench.get("hours24") or {}).get("ja_pct")),
        # WAS ER SCHON HAT. Ohne diese drei Felder empfiehlt der Pool blind: am 30.07.
        # bekamen 7 von 11 Bedford-Mails einen Rat zu etwas, das der Betrieb bereits tut --
        # fuenfmal "switch on 24 hour opening" an ein Profil, das "Open 24 hours" zeigt.
        # Beide Pruefer liessen es durch, weil keiner den Bestand kennt.
        "zeigt_24h": any("24" in str(d.get("hours", ""))
                         for d in (raw.get("openingHours") or [])),
        # Gemessen ja/nein -- ohne Oeffnungszeiten im Scrape ist "zeigt keine 24 Stunden"
        # keine Luecke, sondern eine Luecke in UNSEREN Daten. PIPELINE.md § 0: nicht
        # gemessen ist nie ein Mangel.
        "oeffnungszeiten_gemessen": bool(raw.get("openingHours")),
        # DREI ZUSTAENDE, nicht zwei (22.08.): True = hat eine, False = nachweislich keine,
        # None = das Feld fehlt, wir wissen es nicht. Nur False erzeugt einen Baustein.
        # Genau diese Unterscheidung fehlte bei den Beitraegen, weshalb sie jetzt draussen
        # sind: dort steht bei 81% der Leads None und nirgends eine leere Liste.
        "beschreibung_da": (None if "description" not in raw
                            else bool((raw.get("description") or "").strip())),
        # Googles eigene Zuordnung. Genommen wird der STAERKSTE der Vorschlaege (meiste
        # Bewertungen) -- er traegt den Vergleich, ein schwaecherer waere kein Argument.
        "google_paart": _staerkster_paar(raw.get("peopleAlsoSearch")),
        "sterne_verteilung": raw.get("reviewsDistribution") or {},
        "leistungen_liste": [str(d).lower() for d in (rd.get("services") or [])],
        "kohorte": {"betriebe": mk.get("count"), "mit_beitraegen": mk.get("with_posts"),
                    "mit_24h": mk.get("with_24h")},
        "nachbarn": [(n.get("name") or "") for n in ((x.get("details") or {}).get("nearest") or [])][:2],
        # gemessene Entfernung des naechsten -- macht aus der Nachbar-Zeile einen Befund
        "nachbar_km": next((n.get("km") for n in ((x.get("details") or {}).get("nearest") or [])
                            if n.get("km")), None),
        # Dieselbe Entfernung als fertige Wendung ("700m"), zeichengleich mit dem Blatt --
        # sonst verwirft `verify_mail` sie als erfundene Zahl.
        "nachbar_entfernung": _weite((x.get("details") or {}).get("nearest") or []),
        # Die Bewertungszahl des NAECHSTEN. `market_context` liefert sie unter
        # `nearest_reviews`; ohne sie bleibt die Nachbar-Zeile eine Ortsangabe ohne Argument.
        "nachbar_bewertungen": mk.get("nearest_reviews"),
        "luecken": [{"was": f.get("fact"), "folge": f.get("means")}
                    for f in (ws.get("findings") or [])
                    if f.get("kind") == "gap" and f.get("area") == "gbp"
                    and f.get("fact") and f.get("means")],
    }


def rang_block(x: dict) -> dict | None:
    """Die Fakten fuer den Positions-Satz, so wie die Schreibkarte sie erwartet.

    Nur der Drei-Kasten, und immer mit dem GEBIET, in dem gemessen wurde. Ohne Gebiet ist
    die Aussage widerlegbar: an der eigenen Tuer steht fast jeder Betrieb im Kasten
    (30.07., vier von vier geprueft), drei Kilometer weiter keiner von ihnen.

    Keine Platzzahl aus der langen Liste mehr -- zwei identische Abfragen im Abstand einer
    Minute ergaben Platz 8 und Platz 10. Drin oder draussen wackelt nicht.

    Kein Kasten gemessen -> KEIN Positions-Satz, die Mail faengt mit dem staerksten Befund
    an. Betrifft die Leads ohne Ort im Profil und die Gebiete, in denen Google fuer diese
    Suche gar keinen Kasten zeigt.
    """
    r = (x.get("web_signals") or {}).get("rank") or {}
    if not r.get("kasten_da"):
        return None                      # kein Kasten gemessen -> kein Positions-Satz
    return {"gebiet": r.get("gebiet"), "keyword": r.get("keyword"),
            "im_kasten": bool(r.get("kasten_platz")), "platz": r.get("kasten_platz")}


ECHTER_BETRIEB = 5     # ab so vielen Bewertungen ist ein Wettbewerber greifbar


def widerspruch_waehlen(drueber: list, meine: int) -> dict | None:
    """Wer ueber ihm steht und schwaecher ist -- aber der GLAUBWUERDIGSTE, nicht der
    extremste.

    Bis 27.07. wurde der mit dem groessten Abstand genommen, und das war fast immer
    einer mit null Bewertungen: "service 1st recruitment has 0 reviews, you've got 1500."
    Technisch wahr, wirkt albern, und bei null Bewertungen ist es oft gar kein echter
    Wettbewerber, sondern ein frischer oder verwaister Eintrag.

    Deshalb zuerst unter denen suchen, die als Betrieb erkennbar sind. Gibt es keinen,
    ist die Aussage eine ANDERE und wird auch anders gesagt: dass ein Eintrag ganz ohne
    Bewertungen ueber ihm steht, ist fuer sich genommen ein Befund.
    """
    schwaecher = [d for d in drueber if d.get("bew", 0) < meine]
    if not schwaecher or meine < 10:
        return None
    echte = [d for d in schwaecher if d.get("bew", 0) >= ECHTER_BETRIEB]
    if echte:
        arg = max(echte, key=lambda d: meine - d["bew"])
        return {"wer": arg.get("name"), "pid": arg.get("pid"), "bew": arg["bew"],
                "art": "schwaecherer_betrieb", "wie_viele": len(schwaecher)}
    arg = schwaecher[0]
    return {"wer": arg.get("name"), "pid": arg.get("pid"), "bew": arg.get("bew", 0),
            "art": "eintrag_ohne_bewertungen", "wie_viele": len(schwaecher)}


def spannung_und_liste(pool: list, wie_viele: int = 4) -> tuple:
    """-> (der Baustein fuer den Spannungssatz, die Zeilen fuer die Liste).

    WARUM GETRENNT: steht ueber der Liste kein Rang-Widerspruch (weil er Erster ist oder
    ueber ihm nur Staerkere stehen), nimmt der Spannungssatz den staerksten Befund. Und der
    stand dann NOCHMAL in der Liste -- "44 of your last 50 reviews have no reply", acht
    Zeilen spaeter "44 of your last 50 reviews are unanswered". Dieselbe Zahl zweimal auf
    einer halben Bildschirmseite liest sich wie ein Fehler, nicht wie Nachdruck.

    Der staerkste Baustein traegt also die Spannung ODER eine Listenzeile, nie beides.
    """
    # Der Spannungssatz ist eine BEOBACHTUNG, keine Aufforderung. Nach "du bist der Erste"
    # kann keine Anweisung stehen ("switch on 24 hour opening") -- das ist ein Themenbruch
    # mitten im Absatz. Es braucht eine Tatsache, die gegen die Position steht: "und dann
    # sind 44 von 50 Bewertungen unbeantwortet".
    # ABGESCHALTET am 22.08.2026, und das war der groesste Engpass der ganzen Maschine.
    #
    # Der Spannungssatz stand frueher als eigener Satz ZWISCHEN dem Positions-Statement und
    # der Liste ("du bist der Erste. und dann sind 44 von 50 Bewertungen unbeantwortet").
    # Beides gibt es nicht mehr: die Vorlage hat seit dem Umbau nur noch Satz 1, die Bruecke
    # und die Stichpunkte. Der staerkste Baustein wurde trotzdem weiter herausgenommen und
    # fuer einen Satz reserviert, den niemand mehr rendert -- also bei JEDEM Lead ersatzlos
    # verschenkt.
    #
    # Gemessen: mit Reservierung erreichten 68% der 2.717 Leads drei Stichpunkte, ohne sie
    # 87%. Neunzehn Prozentpunkte, die an einer Zeile Code hingen, die auf eine geloeschte
    # Mailstruktur zeigte.
    #
    # Die Funktion bleibt mit ihrer Signatur bestehen, weil `batch_briefs` sie so aufruft;
    # sie gibt jetzt nur `None` fuer die Spannung zurueck.
    return None, waehle(pool, wie_viele)


# Was jemand SIEHT, wenn er auf dem Profil landet. Nur solche Befunde taugen als
# Spannungssatz hinter einer Position -- sie schliessen an ("er findet dich, und dann
# sieht er ..."). Ein Verhalten wie "du postest nicht" schliesst nicht an, es steht
# unverbunden daneben: "du bist der Erste. und 44 Bewertungen sind unbeantwortet." ist
# ein Themensprung (Luka, 27.07.: "sowas im Introblock macht doch keinen Sinn").
SICHTBAR_AUF_DEM_PROFIL = {"fotos", "antworten", "leistungen_leer", "kategorien",
                           "themen", "24h"}



# ── WHAT'S WORKING WELL ────────────────────────────────────────────────────────────────
# Der Anlass (Luka, 22.08.2026): "darunter what's working well mit einer zusammenfassung der
# punkte die schon passen und dann darunter what can be improved".
#
# WARUM DAS ZAEHLT, und nicht nur nett ist: eine Mail von einem Fremden, die ausschliesslich
# Maengel auflistet, liest sich wie ein Verkaufsvorwand. Wer zuerst benennt, was gut laeuft,
# beweist, dass er wirklich nachgesehen hat -- und der Empfaenger kann es sofort pruefen.
#
# Gemessen ueber die 2.744 anschreibbaren Leads: **99% haben mindestens zwei** dieser Punkte,
# im Median fuenf bis sechs. Die Sektion ist also praktisch immer fuellbar.
#
# Dieselbe Regel wie ueberall: was nicht gemessen ist, erzeugt keine Zeile -- weder Lob noch
# Tadel. Ein Betrieb bekommt kein "deine Oeffnungszeiten stehen", wenn wir sie nie gesehen
# haben.
def gut(b: dict) -> list:
    """Die Punkte, die schon passen -- kurze Zeilen, keine Handlung, keine Folge.

    Bewusst OHNE die Formel aus `fact_sheet.formel`: das ist kein Vorschlag, sondern eine
    Feststellung. "you're on 80 reviews where most have 20" braucht kein "also mach X".
    """
    raus = []
    raw_f, raw_b = _n(b.get("fotos"), -1), _n(b.get("meine_bewertungen"), -1)
    med_f, med_b = _n(b.get("uk_median_fotos")) or 14, _n(b.get("uk_median_bewertungen")) or 20
    sterne = b.get("sterne")
    n_kat, n_leist = _n(b.get("kategorien"), -1), b.get("leistungen_im_profil")
    v = b.get("sterne_verteilung") or {}

    if raw_b >= 0 and raw_b > med_b:
        raus.append((90, f"{raw_b} reviews where most uk {b.get('niche','locksmith')}s have {med_b}"))
    if sterne and float(sterne) >= 4.8:
        raus.append((84, f"a {sterne} star average"))
    if raw_f >= 0 and raw_f > med_f:
        raus.append((70, f"{raw_f} photos where most have {med_f}"))
    if n_leist is not None and n_leist >= 20:
        raus.append((76, f"{n_leist} services listed"))
    if n_kat >= 5:
        raus.append((66, f"{n_kat} categories set"))
    if b.get("zeigt_24h"):
        raus.append((72, "24 hour opening on the profile"))
    if v and not (_n(v.get("oneStar")) + _n(v.get("twoStar"))):
        raus.append((62, "not one review below three stars"))
    if b.get("beschreibung_da") is True:
        raus.append((58, "a description google can read"))

    # DIE PUNKTE, DIE FAST JEDER HAT (22.08., Luka: "in was laeuft gut wollen wir eher als
    # nur eine kategorie nennen die gut laeuft, die sektion koennen wir gut als liste
    # abhaken"). Genau die Faktoren, die aus dem SCORE fliegen, weil sie nicht trennen --
    # 99% haben ein beanspruchtes Profil, 99% eine Nummer. Fuer eine Zahl ist das wertlos,
    # fuer diese Liste nicht: sie soll zeigen, dass wir das ganze Profil durchgegangen sind,
    # und sie muss sich abhaken lassen. Deshalb stehen sie hier UNTEN -- sie fuellen auf,
    # wenn die starken Punkte fehlen, und werden von ihnen verdraengt, wenn es sie gibt.
    if b.get("beansprucht") is True:
        raus.append((40, "a claimed and verified profile"))
    if b.get("telefon"):
        raus.append((36, "a number people can tap from search"))
    if b.get("website"):
        raus.append((34, "a website linked from the listing"))
    if b.get("oeffnungszeiten_gemessen") and not b.get("zeigt_24h"):
        raus.append((32, "opening hours filled in"))
    if _n(b.get("kategorien"), 0) >= 2:
        raus.append((30, f"{_n(b.get('kategorien'))} categories set, not just the one"))
    if raw_b > 0 and raw_b <= med_b:
        raus.append((28, f"{raw_b} reviews already on the profile"))

    raus.sort(key=lambda x: -x[0])
    # Bis zu DREI (23.08.2026, war vier). Der vierte Punkt kostet ~8 Woerter Lob und
    # verschiebt die Aufmerksamkeit weg von der Liste darunter, wo die Antwort entsteht.
    # Drei reichen fuer den Beweis "wir sind das ganze Profil durchgegangen", und mit den
    # Auffuellern oben erreichen 99% der Leads diese drei.
    return [t for _, t in raus[:3]]


def gut_satz(teile: list) -> str:
    """Die Punkte als EIN Absatz: "you've got a, b, c and d."

    Kein Bullet-Block (Luka, 22.08.: "die sektion nicht als bullet points sondern als absatz,
    eher als aufzaehlung"). Der Grund ist die Wirkung: zwei Listen untereinander lesen sich
    wie ein abgearbeitetes Formular. Ein Absatz oben und eine Liste unten trennt sauber --
    der Absatz sagt "das haben wir alles gesehen", die Liste "das waere zu tun". Und die
    Aufmerksamkeit bleibt auf den Stichpunkten, wo sie hingehoert.

    Deshalb liefert `gut()` Nominalphrasen ohne Verb: "33 services listed" reiht sich,
    "33 services listed, that's a full list" nicht.
    """
    teile = [t for t in (teile or []) if t]
    if not teile:
        return ""
    reihe = teile[0] if len(teile) == 1 else ", ".join(teile[:-1]) + " and " + teile[-1]
    return f"you've got {reihe}."


def waehle(pool: list, wie_viele: int = 4) -> list:
    """Die 3 bis 4, die zusammen die Regeln erfuellen.

    Hoechstens ZWEI derselben Form und mindestens ZWEI Blickwinkel -- beides stand bisher
    als Bitte im Agenten-Prompt und kostete ihn Nachdenken. Es ist eine Auswahlregel.
    """
    # NIE ZWEI ZEILEN UEBER DIESELBE SACHE (22.08.2026). Der Kontrast-Baustein nennt eine
    # Luecke, die es auch als eigenen Punkt gibt -- am 22.08. stand deshalb in 2 von 3
    # Beispielen zweimal die Beschreibung ("80 reviews and no description" plus "your
    # profile has no description"). Geprueft wird das THEMA, nicht die Formulierung: die
    # Bausteine sind absichtlich verschieden formuliert, also faengt kein Textvergleich sie.
    # NUR die Luecken, nicht die Zahlen drumherum. "review" stand hier zuerst mit drin und
    # blockierte damit den Kontrast gegen die Bewertungszeile -- beide nennen Bewertungen,
    # meinen aber Verschiedenes. Das kostete 14 Prozentpunkte Abdeckung (75% -> 61%).
    THEMA = {"description": "beschreibung", "under services": "leistungen",
             "services listed": "leistungen", "photo": "fotos", "categor": "kategorien", "main category": "kategorien",
             "filed as": "kategorien", "services": "leistungen",
             "24 hour": "24h", "one or two star": "ein_stern",
             "bad review": "ein_stern", "bottom of the scale": "ein_stern"}

    def themen_von(text: str) -> set:
        t = text.lower()
        return {v for k, v in THEMA.items() if k in t}

    sortiert = sorted(pool, key=lambda x: -x["staerke"])
    gewaehlt, formen, genannt = [], {}, set()
    for x in sortiert:
        if len(gewaehlt) >= wie_viele:
            break
        if formen.get(x["form"], 0) >= 2:
            continue
        # Der staerkere Baustein gewinnt das Thema -- `sortiert` laeuft von oben nach unten,
        # also steht der Kontrast (98) vor dem Einzelpunkt (38-88) und der Einzelpunkt faellt.
        eigene = themen_von(x["text"])
        if eigene & genannt:
            continue
        if x["blick"] == "automatisierbar" and any(g["blick"] == "automatisierbar"
                                                   for g in gewaehlt):
            # NICHT die Zeile verwerfen, nur die Klammer. Zwei Hinweise auf uns in einer
            # Mail lesen sich wie ein Angebot mitten in der Liste -- aber die Zeile selbst
            # traegt weiter. Vorher fiel sie ganz raus, und die Mail hatte statt vier nur
            # zwei Stichpunkte.
            import re as _re
            x = dict(x, text=_re.sub(r"\s*\([^)]*\)\s*$", "", x["text"]),
                     blick="kohorte")
        gewaehlt.append(x)
        genannt |= eigene
        formen[x["form"]] = formen.get(x["form"], 0) + 1
    # Mindestens zwei Blickwinkel: sonst den schwaechsten gegen einen anderen tauschen.
    #
    # Der Tausch muss ALLE Regeln erneut pruefen, nicht nur den Blickwinkel (Fix 22.08.2026):
    # er setzte den Ersatz blind auf `gewaehlt[-1]` und konnte damit eine dritte Zeile
    # derselben Form oder eine zweite ueber dasselbe Thema hereinholen -- genau die zwei
    # Regeln, die zehn Zeilen weiter oben durchgesetzt werden. Eine Regel, die beim
    # Nachbessern umgangen wird, ist keine.
    if len({g["blick"] for g in gewaehlt}) < 2 and len(gewaehlt) > 1:
        raus = gewaehlt[-1]
        rest_formen = collections.Counter(g["form"] for g in gewaehlt[:-1])
        rest_themen = {t for g in gewaehlt[:-1] for t in themen_von(g["text"])}
        for x in sortiert:
            if x in gewaehlt:
                continue
            if x["blick"] in {g["blick"] for g in gewaehlt[:-1]}:
                continue
            if rest_formen.get(x["form"], 0) >= 2:
                continue
            if themen_von(x["text"]) & rest_themen:
                continue
            gewaehlt[-1] = x
            break
    return gewaehlt


try:
    from findings import _ist_eigenschaft
    from trades import ist_leistung as _ist_leistung
except ImportError:                                   # eigenstaendig lauffaehig halten
    def _ist_eigenschaft(t):
        return False

    def _ist_leistung(t, n):
        return True


def self_check():
    b = {"antworten": {"geholt": 50, "beantwortet": 0, "quote_prozent": 0},
         "themen_der_bewertungen": {"car key replacement": 12, "lock rekeying": 5},
         "leistungen_im_profil": 0, "meine_bewertungen": 8, "uk_median_bewertungen": 20,
         "kohorte": {"betriebe": 11, "mit_beitraegen": 3, "mit_24h": 4},
         "nachbarn": ["A Locks", "B Keys"], "luecken": []}
    p = bausteine(b)
    ids = {x["id"] for x in p}
    assert "antworten" in ids and "antworten_gut" not in ids, ids

    # Bei hoher Quote ist es ein Lob, kein Vorschlag -- Lukas Beispiel
    gut = dict(b, antworten={"geholt": 50, "beantwortet": 50, "quote_prozent": 100})
    ids2 = {x["id"] for x in bausteine(gut)}
    assert "antworten_gut" in ids2 and "antworten" not in ids2, ids2

    # Fehlt eine Zahl, gibt es den Baustein nicht -- nie ein Platzhalter
    ohne = dict(b, antworten={})
    assert not any(x["id"].startswith("antworten") for x in bausteine(ohne))

    # `im_pack` und der Positions-Satz muessen aus DERSELBEN Messung kommen, sonst
    # widerspricht die Mail sich selbst. Genau das ist am 30.07. passiert, weil hier
    # `pack_rank` gelesen wurde und `rank_pull.py` nur noch `kasten_platz` schreibt.
    drin = {"web_signals": {"rank": {"gebiet": "Bedford", "keyword": "locksmith",
                                     "kasten_da": True, "kasten_platz": 1}}}
    assert aus_lead(drin, {}, {})["im_pack"] is True
    assert rang_block(drin)["im_kasten"] is True
    draussen = {"web_signals": {"rank": {"gebiet": "Bedford", "keyword": "locksmith",
                                         "kasten_da": True, "kasten_platz": None}}}
    assert aus_lead(draussen, {}, {})["im_pack"] is False
    assert rang_block(draussen)["im_kasten"] is False

    # Die beiden Lagen sind verschiedene Verkaufsgespraeche, nicht dieselbe Liste in anderer
    # Reihenfolge. Zwei Regeln aus knowledge/local-seo-method.md, mechanisch festgehalten:
    viel = dict(b, meine_bewertungen=60, uk_median_bewertungen=20)
    draussen = {x["id"] for x in bausteine({**viel, "im_pack": False})}
    drin = {x["id"] for x in bausteine({**viel, "im_pack": True})}
    # 1) Wer viele Bewertungen hat und NICHT rankt, bekommt die Prospect-Regel als Satz.
    #    Wer drin steht, nicht -- bei ihm ist es keine Erklaerung, sondern eine Floskel.
    assert "harte_arbeit_da" in draussen and "harte_arbeit_da" not in drin
    # 2) Der Median-Vergleich wird bei jemandem in den drei UMFORMULIERT, nicht
    #    weggelassen (Luka, 30.07.: objektiv groesste Hebel, nicht die bequemen).
    wenig = dict(b, meine_bewertungen=8, uk_median_bewertungen=20)
    d_txt = next(x["text"] for x in bausteine({**wenig, "im_pack": False}) if x["id"] == "bewertungen")
    i_txt = next(x["text"] for x in bausteine({**wenig, "im_pack": True}) if x["id"] == "bewertungen")
    # Bis 22.08. unterschied sich die Bewertungs-Zeile je nach Rang ("...so you keep the
    # spot" gegen "...so google notices"). Beide Fassungen spielten auf die Position an, und
    # die steht seit dem Umbau in keiner Mail mehr -- "damit du den Platz haeltst" ist fuer
    # jemanden, dem wir nie gesagt haben, dass er einen Platz hat, kein Satz. Die Handlung
    # ist in beiden Lagen dieselbe, also ist es die Zeile jetzt auch.
    assert "ask your next ten so you match them" in d_txt and d_txt == i_txt, (d_txt, i_txt)
    # 3) NIE ETWAS EMPFEHLEN, WAS ER SCHON TUT. Am 30.07. stand in 7 von 11 Bedford-Mails
    #    ein Rat zu etwas Vorhandenem, fuenfmal "switch on 24 hour opening" an ein Profil
    #    mit "Open 24 hours". Beide Pruefer liessen es durch -- keiner kennt den Bestand.
    hat_schon = dict(b, zeigt_24h=True, postet=True,
                     themen_der_bewertungen={"car key copying": 5, "lock change": 3},
                     leistungen_liste=["car key copying", "lock change"])
    ids = {x["id"] for x in bausteine({**hat_schon, "im_pack": False})}
    assert "24h" not in ids, "24h empfohlen, obwohl das Profil 24 Stunden zeigt"
    assert "posten" not in ids, "Posten ist seit 22.08. entfernt (nicht belegbar)"
    assert "themen" not in ids, "Luecke behauptet, obwohl die Leistungen gelistet sind"
    # umgekehrt: wer es nicht hat, bekommt es weiter
    fehlt = dict(b, zeigt_24h=False, postet=False, oeffnungszeiten_gemessen=True,
                 themen_der_bewertungen={"car key copying": 5, "lock change": 3},
                 leistungen_liste=[])
    ids2 = {x["id"] for x in bausteine({**fehlt, "im_pack": False})}
    assert {"24h", "themen"} <= ids2, ids2
    assert "posten" not in ids2, "Posten darf nirgends mehr entstehen"

    # 4) Die gemessene Luecke verschiebt die Staerke: 2 von 20 wiegt mehr als 18 von 20
    gross = next(x["staerke"] for x in bausteine({**wenig, "im_pack": False}) if x["id"] == "bewertungen")
    klein = next(x["staerke"] for x in bausteine({**dict(b, meine_bewertungen=18,
                 uk_median_bewertungen=20), "im_pack": False}) if x["id"] == "bewertungen")
    assert gross > klein, (gross, klein)

    w = waehle(p, 4)
    assert len(w) <= 4
    formen = {}
    for x in w:
        formen[x["form"]] = formen.get(x["form"], 0) + 1
    assert max(formen.values()) <= 2, formen
    # Zwei Blickwinkel sind ein ZIEL, keine Bedingung (praezisiert 22.08.2026). Der Tausch
    # am Ende von `waehle` prueft seit heute auch Form und Thema mit -- findet er dann keinen
    # Ersatz, bleibt es bei einem Blickwinkel. Das ist die richtige Reihenfolge: eine zweite
    # Zeile ueber dieselbe Sache waere ein sichtbarer Fehler, ein einheitlicher Blickwinkel
    # nur eine verpasste Nuance.
    assert len({x["blick"] for x in w}) >= 1, w
    assert max(collections.Counter(x["form"] for x in w).values()) <= 2, w
    assert sum(1 for x in w if x["blick"] == "automatisierbar") <= 1
    print(f"self-check ok ({len(p)} Bausteine, {len(w)} gewaehlt)")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        self_check()
    else:
        print(__doc__)
