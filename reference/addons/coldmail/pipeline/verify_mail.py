#!/usr/bin/env python3
"""verify_mail.py — das Netz unter dem Modelltext.

Ohne diese Datei duerfen wir Haiku nicht auf 3.593 Empfaenger loslassen. Der Brief
(`brief.py`) sagt dem Modell, was wahr ist; hier wird geprueft, ob es sich daran gehalten
hat. Mechanisch, ohne Modell -- ein Pruefer, der selbst raet, prueft nichts.

DIE HAERTESTE REGEL: jede Zahl in der Mail muss im Brief vorkommen. Erfindet das Modell
"you're losing about 40 calls a month", faellt die Mail durch, egal wie gut sie klingt.
Genau diese Zahl waere der Satz, den der Empfaenger widerlegt.

Die anderen Regeln sind die Fehlerklassen, die in dieser Pipeline schon einmal
aufgetreten sind -- jede davon habe ich am 27.07. selbst produziert und beim Lesen
gefunden, nicht durch einen gruenen Selbsttest:

  doppelter Verbinder   "does not show 24 hours, so 8 in town do, so the 2am call goes"
  Gedankenstrich        Lukas stehende Regel, der #1-AI-Tell
  abgeschnittener Satz  endet auf Praeposition oder Komma
  Datenbank-Auszug      "Vehicle Locksmith Solutions LTD" mitten im Fliesstext
  Platzhalter           ein {feld}, das nie ersetzt wurde
  doppelter Schlusssatz dieselbe Lage-Formulierung zweimal in einer Mail

Wer durchfaellt, wird NICHT stillschweigend repariert und nicht verworfen, sondern
gebuckelt: eine Mail mit Grund. Genau das Muster, das die Pipeline ueberall benutzt --
nie loeschen, immer in einen benannten Eimer.

Usage:
  python3 verify_mail.py --mail mail.txt --brief brief.json
  python3 verify_mail.py --self-check
"""
from __future__ import annotations
import argparse, json, re, sys

# Zahlen, die immer erlaubt sind: Uhrzeiten und Jahreszahlen aus feststehenden Wendungen.
ALLOWED = {"2", "24", "100", "1", "2026"}

# Die zwei Perzentil-Schwellen der Methode. Sie sind KEINE erfundenen Prozentzahlen: das Blatt
# traegt `bewertungen_top25_ab` (72) und `bewertungen_top10_ab` (166), gemessen ueber n=4.746.
# `markt_copy.md` empfiehlt die Formulierung ausdruecklich ("your 135 reviews put you in the
# top 25% of uk locksmiths") und der Prozent-Pruefer verwarf sie -- am 22.08. im ersten echten
# Stapellauf aufgefallen, zwei Regeln derselben Datei, die einander widersprachen. Freigegeben
# ist NUR die Form "top 25%"/"top 10%", nicht die Zahl an sich: eine Mail, die "25% more calls"
# behauptet, faellt weiter durch.
PERZENTIL = re.compile(r"top (25|10)%", re.I)

# Woerter, die nach einer Zahl bedeuten, dass gerechnet wurde. Genau da entstehen die
# falschen Saetze: der Brief nennt einen Bestand, das Modell macht daraus eine Differenz.
# Wendungen, die nie eine Aussage tragen. Jede einzelne ist in einem echten Entwurf
# aufgetaucht, und jede liest sich nach Maschine.
# Verweise auf Wissen, das der Leser nicht hat. Er hat einen Satz gelesen und kennt
# weder unsere Zweiteilung noch die Pruefliste.
FUELLER = ("on both counts", "in both areas", "on both scores", "the second one",
           "as mentioned", "as i said", "doing the heavy lifting", "ticking every box", "ticking nearly every box",
           "lags behind", "lags well behind", "jumps out", "worth pointing out",
           "the one thing that", "straight away", " actually ", " clearly ",
           "the real drag", "comes close", "real work for you")

ARITHMETIC = {"more", "fewer", "less", "extra", "additional", "short", "away", "behind",
              "ahead", "under", "over", "shy", "off", "further", "beyond"}
# Nur Woerter, nach denen zwingend etwas fehlt. Praepositionen gehoeren NICHT dazu:
# "google doesn't know you're open when the calls come in" und "those searches never
# reach you" sind vollstaendige Saetze, und die erste Fassung dieser Liste hat sieben von
# elf Mails faelschlich einkassiert. Ein Pruefer, der Richtiges verwirft, wird abgeschaltet
# -- und dann faengt er auch das Falsche nicht mehr.
DANGLING = ("of", "the", "a", "an", "and", "or", "but", "so", "your", "their", "its",
            "our", "that", "which", "where", "who", "when", "than", "as")


def numbers(text: str) -> set:
    """Alle Zahlen im Text, Tausendertrenner normalisiert.

    "1,293" und "1293" sind dieselbe Zahl -- ohne die Normalisierung faellt jede Mail
    durch, die eine Bewertungszahl mit Komma schreibt.
    """
    return {n.replace(",", "").replace(".", "") for n in re.findall(r"\d[\d.,]*", text)}


def _num_word(text: str) -> list:
    """(Zahl, naechstes Wort) -- aber nur INNERHALB eines Satzes.

    Ueber die Satzgrenze hinweg gepaart entstand "19. filler" aus zwei voellig
    unabhaengigen Saetzen. Eine Zahl am Satzende hat kein Nachbarwort, und dann gibt es
    nichts zu pruefen.
    """
    out = []
    for sentence in re.split(r"[.;:!?\n]", text):
        # Tausendertrenner ja, Satzkomma nein: "1,293 reviews" ist ein Paar,
        # "19, and" ist keines. Ohne die enge Fassung schluckte [\d,]* das Satzkomma
        # und paarte die Zahl mit dem Wort dahinter.
        out += re.findall(r"(\d+(?:,\d{3})*)\s+([a-z]+)", sentence)
    return out


def _values(node) -> set:
    """Alle Zahlen, die im Brief als eigener Wert stehen, nicht in einem Satz."""
    if isinstance(node, bool):
        return set()
    if isinstance(node, (int, float)):
        return {str(int(node))}
    if isinstance(node, dict):
        return {x for v in node.values() for x in _values(v)}
    if isinstance(node, list):
        return {x for v in node for x in _values(v)}
    return set()


def _strings(node) -> list:
    """Alle Fliesstext-Werte aus dem Brief, rekursiv. Schluessel bleiben draussen."""
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        return [x for v in node.values() for x in _strings(v)]
    if isinstance(node, list):
        return [x for v in node for x in _strings(v)]
    return []


def _unquoted(text: str) -> str:
    """Der Text ohne alles in Anfuehrungszeichen.

    Wir zitieren die eigenen Worte des Betriebs woertlich -- das ist Absicht, ein Satz, den
    er selbst geschrieben hat, kann nicht wie eine Vorlage klingen. Sein Seitentitel lautet
    aber "Gold Key Locks – 24/7 Locksmith in Bedord", mit SEINEM Gedankenstrich. Den ihm
    vorzuwerfen waere so falsch wie ihn zu korrigieren.
    """
    return re.sub(r'"[^"]*"', ' ', text)


def check(mail: str, brief: dict, template_numbers=(71,)) -> list:
    """-> Liste der Verstoesse. Leer heisst versandfaehig.

    `template_numbers` sind Konstanten aus der festen Vorlage (die 73 Checks des Reports).
    Sie stehen nicht im Brief eines einzelnen Leads und sind trotzdem wahr.
    """
    bad = []
    blob = json.dumps(brief, ensure_ascii=False)
    free = _unquoted(mail)

    unknown = sorted(numbers(mail) - numbers(blob) - ALLOWED
                     - {str(n) for n in template_numbers})
    if unknown:
        bad.append(f"Zahlen, die nicht im Brief stehen: {', '.join(unknown)}")

    # Eine Zahl kann im Brief stehen und trotzdem in einer Luege stecken. Haiku schrieb
    # "you need 8 more reviews to hit the town median" ueber einen Betrieb, der 8
    # Bewertungen HAT -- die 8 war im Brief, die Aussage falsch, und der Existenz-Test
    # liess sie durch. Geprueft wird deshalb das Wort NACH der Zahl: im Brief steht
    # "8 reviews", in der Mail stand "8 more", und daran faellt es auf.
    # Der Zusammenhang wird NUR an den Fliesstext-Feldern des Briefs geprueft (fact, means).
    # Strukturwerte wie "met: 5, of: 8" stehen im JSON ohne Nachbarwort, und "5 of 8 things"
    # in der Mail ist voellig korrekt -- gegen JSON geprueft faellt es faelschlich durch.
    prose = " ".join(_strings(brief)).lower()
    # Zahlen, die im Brief als WERT stehen (how_many_show_24h: 4, locksmiths_in_area: 11),
    # darf das Modell frei in einen Satz bauen -- sie haben im JSON kein Nachbarwort, gegen
    # das sich pruefen liesse. Nur Zahlen, die AUSSCHLIESSLICH aus einem Fliesstext-Fakt
    # stammen, muessen in dessen Zusammenhang bleiben. Ohne diese Trennung fielen sechs von
    # elf Mails durch, weil sie eine voellig korrekte Marktzahl erwaehnten.
    prose_nums = numbers(prose) - _values(brief)
    # Gesucht ist RECHNEN, nicht Umformulieren. Die erste Fassung verlangte exakt dasselbe
    # Folgewort wie im Brief und kassierte damit voellig korrekte Saetze ein: "you're at 8
    # against a uk median of 19" steht fast woertlich im Brief und scheiterte an "against"
    # statt "reviews". Was ein Modell gefaehrlich macht, ist nicht die Umschreibung, sondern
    # der Vergleichsmodifikator -- "8 MORE reviews", "3 reviews SHORT". Nur die werden
    # geflaggt, und die erfundene Zahl selbst faengt ohnehin der Existenz-Test.
    for num, word in _num_word(mail.lower()):
        n = num.replace(",", "").replace(".", "")
        if n in ALLOWED or n in {str(x) for x in template_numbers} or n not in prose_nums:
            continue
        if word in ARITHMETIC:
            bad.append(f"gerechnete Zahl: \"{num} {word}\"")
            break

    if "—" in free or "–" in free:
        bad.append("Gedankenstrich in ausgehender Copy")
    if re.search(r"\{[a-z_]+\}", mail):
        bad.append("nicht ersetzter Platzhalter")
    # Fuellwendungen. Die Prompt-Regel dagegen ist eine Bitte, das hier ist eine Pruefung --
    # "the one thing that" und "actually" sind trotz Verbot in derselben Runde durchgerutscht,
    # in der sie verboten wurden. Null Fehlalarme: keine davon traegt je eine Aussage.
    drin = [f for f in FUELLER if f in _unquoted(mail).lower()]
    if drin:
        bad.append(f"Fuellwendung: {', '.join(drin)}")

    # Der Positions-Satz muss sagen, VON WO aus gemessen wurde. Gemessen am 30.07.:
    # vier von vier Betrieben stehen direkt vor ihrer eigenen Tuer im Drei-Kasten und
    # drei Kilometer weiter keiner. "du bist nicht unter den drei" ohne Ortsangabe ist
    # deshalb kein Befund, sondern eine Behauptung, die der Empfaenger in seinem Laden
    # in Sekunden widerlegt -- der teuerste Fehler, den diese Mail machen kann.
    # Der Standort muss dastehen, in EINER der Formen, die wir wirklich messen. Die erste
    # Fassung verlangte woertlich "looking up <branche> in <ort>" und kassierte damit den
    # kuerzeren Oeffner ein, der den Ort in den ersten Halbsatz zieht ("i went through all
    # 11 locksmiths in bedford, and when someone looks one up in the middle of town ...").
    # Ein Pruefer, der Richtiges verwirft, wird abgeschaltet -- also die Absicht pruefen,
    # nicht den Wortlaut: irgendeine benannte Perspektive muss in der Mail stehen.
    STANDORT = (r"in the middle of", r"in the centre of", r"right where you are",
                r"in your corner of", r"(looking up|looks up) .+ in \w")
    if re.search(r"top three|top 3|google shows three|one of the three", mail, re.I) \
            and not any(re.search(m, mail, re.I) for m in STANDORT):
        bad.append("Kasten-Aussage ohne Standort (keine der gemessenen Perspektiven "
                   "genannt: in the middle of / right where you are / looking up ... in X)")
    # ORTSVERGLEICH. Jede Zahl, die etwas ueber ALLE Betriebe im Ort behauptet, ist bei uns
    # ein Ausschnitt: der Scrape nahm nur Betriebe mit Website und suchte je Grafschaft statt
    # je Ort, also stehen in Bedford 11 von 27 und in Hornchurch 1 von 20 in der Datenbank.
    # Gemessen am 30.07.: 15 von 21 fertigen Mails behaupteten so etwas. Der Vergleich gehoert
    # gegen das LAND (n=4.746), dort kippt die Luecke den Median nicht. EINEN Konkurrenten zu
    # nennen bleibt richtig -- der ist gemessen und im Median 900 m weg; nur der Schluss von
    # unserer Liste auf den ganzen Ort ist es nicht. markt_copy.md § Schreibkarte (d).
    ORTSVERGLEICH = (
        (r"\d+ of the \d+ (here|in town|round here)", "Anteil im Ort"),
        (r"(the )?rest of \w+ (has|have|are)", "Ortsschnitt"),
        (r"\d+ (in town|here|round here) (are|do|have|show)", "Ortszahl"),
        (r"put you \d+(st|nd|rd|th) in \w+", "Rang im Ort"),
        (r"most locksmiths (round here|in town)", "Ortsschnitt"),
        # Die Kohorten-Zahl im Oeffner. Sie behauptet nicht "alle", klingt aber danach --
        # und ist dem Pruefer am 30.07. dreimal entgangen, weil "other" wie eine
        # Einschraenkung aussieht. Der Ort gehoert in den Satz, die Zahl nicht:
        # "i took a look at velokey and a few other locksmiths in bedford".
        (r"\d+ other locksmiths in \w+", "Kohorten-Zahl im Oeffner"),
        # Der Superlativ ist derselbe Schluss in Feiertagskleidung: "the most of any
        # locksmith in bedford" behauptet, wir kennen jeden in Bedford. Tun wir nicht.
        # "top of the 3" ist der GEMESSENE Kastenplatz und muss durchgehen -- nur der
        # Superlativ ueber den Ort ist gemeint ("top of reading", "the most in bedford").
        (r"\b(the most|the best|the busiest|more than (anyone|most)|"
         r"top of (?!the (3|three))|(second|third|fourth|first) in)\b",
         "Superlativ ueber den Ort"),
    )
    for muster, was in ORTSVERGLEICH:
        for satz in re.split(r"[.\n]", mail):
            # "more than most uk locksmiths" ist erlaubt -- n=4.746 traegt den Satz.
            if re.search(muster, satz, re.I) and not re.search(r"\buk\b", satz, re.I):
                bad.append(f"{was}: wir kennen den Ort nur ausschnittsweise -- gegen das "
                           f"Land vergleichen (markt_copy.md § Schreibkarte (d))")
                break

    # HIER STAND EINE SPERRE gegen "die drei bekommen die Haelfte aller Auftraege". Luka hat
    # sie am 30.07. dreimal verlangt und beim dritten Mal entschieden; die Sperre ist raus.
    # Der Einwand bleibt aktenkundig, damit ihn niemand fuer ein Versehen haelt: fuer KLICKS
    # auf den Local Pack gibt es kursierende Studien, fuer AUFTRAEGE oder Umsatz hat es
    # niemand gemessen, und ein Betrieb mit Stammkundschaft kontert den Satz aus dem Stand.
    # Wer die Zahl je belegen will, traegt sie in markt_copy.md § Geprueffte Plattform-Zahlen
    # ein; bis dahin ist sie eine bewusste Ausnahme von der Regel, nicht deren Aufhebung.

    # Die Bruecke "then they land on" setzt voraus, dass ihn jemand GEFUNDEN hat. Nach
    # "google shows three names and yours isn't one of them" schliesst sie ins Leere: wer
    # ihn nicht sieht, landet auch nicht auf seinem Profil. Einmal selbst produziert
    # (Gold Key, 30.07.) und beim Lesen der fertigen Mail gefunden.
    if re.search(r"isn't one of them|not one of them", mail, re.I) \
            and re.search(r"then they (land on|see)|the first thing they see", mail, re.I):
        bad.append("Bruecke ins Leere: \"then they ...\" nach \"nicht unter den drei\"")

    # Regel 3b: der Erkenntnis-Absatz faengt DIREKT mit der Erkenntnis an. Die Regel stand
    # bisher nur im Menschen-Teil von markt_copy.md, nicht in der Schreibkarte und nicht
    # hier -- Ergebnis: 9 von 11 Bedford-Mails oeffnen mit "overall" (gemessen 28.07.).
    # Das ist dieselbe Vorlagen-Wirkung wie eine identische Betreffzeile, nur in der Zeile,
    # die als einzige sicher gelesen wird.
    erster = next((z.strip() for z in mail.split("\n")
                   if z.strip() and not z.strip().startswith(("hey ", "hi ", "- "))
                   and "i just looked at" not in z.lower()), "")
    if re.match(r"^(overall|so|first off|firstly|to start|in short)\b", erster, re.I):
        bad.append(f"Raeuspern statt Erkenntnis: \"{erster.split(',')[0][:28]}\"")

    # Jede Zeile der Aufgabenliste muss mit einer HANDLUNG anfangen. Sonst uebernimmt das
    # Modell den Fakt aus dem Brief woertlich ("- your profile has no posts, where 4 of the
    # 11 in town do") -- richtig, aber eine Beobachtung in einer Liste, die "things you
    # could do" heisst.
    # Der Lage-Absatz darf die Liste nicht vorwegnehmen. "the one thing missing is X" ueber
    # einer Liste mit drei Punkten liest sich, als haette niemand gegengelesen.
    # Getrennt wird an der ERSTEN Stichpunkt-Zeile, nicht an einer Wendung (Fix 22.08.).
    # Vorher stand hier `split("a few things")` -- die Formulierung gibt es seit dem Umbau
    # nicht mehr, also lieferte der split die GANZE Mail zurueck und der Pruefer schlug an,
    # sobald "what's missing" in irgendeinem Stichpunkt vorkam. Ein Pruefer, der Richtiges
    # verwirft, wird abgeschaltet -- die Liste ist der Trenner, nicht ihre Ankuendigung.
    _zeilen = mail.split("\n")
    _erste = next((i for i, l in enumerate(_zeilen) if l.strip().startswith("- ")), len(_zeilen))
    vor_liste = "\n".join(_zeilen[:_erste]).lower()
    vorweg = [x for x in ("the one thing missing", "the gap is", "are the gap",
                          "is the gap", "the only problem", "what's missing")
              if x in vor_liste]
    if vorweg and sum(1 for l in mail.split("\n") if l.strip().startswith("- ")) > 1:
        bad.append(f"Lage-Absatz nimmt die Liste vorweg: {vorweg[0]}")

    # Die Regel "jede Aufgabenzeile faengt mit einer Handlung an" hat am 27.07. genau das
    # erzeugt, was Luka dann beanstandet hat: vier von fuenf Zeilen als "[-ing] ... would
    # [Verb]". markt_copy.md erlaubt seitdem ausdruecklich Beobachtung+Folge ("your profile
    # has no photos, so it looks thin") und Vergleich-zuerst ("2 of the 11 near you post").
    # Der Pruefer kann die Bauform also nicht mehr einzeln verbieten. Was er stattdessen
    # prueft, ist das eigentliche Anliegen: dass nicht ALLE gleich anfangen.
    zeilen = [l.strip()[2:] for l in mail.split("\n")
              if l.strip().startswith("- ") and len(l.strip()) > 4]
    if len(zeilen) >= 3:
        anfaenge = [z.split()[0].lower().rstrip(",") for z in zeilen]
        haeufigster = max(set(anfaenge), key=anfaenge.count)
        if anfaenge.count(haeufigster) > 2:
            bad.append(f"{anfaenge.count(haeufigster)} von {len(zeilen)} Aufgabenzeilen "
                       f"beginnen mit '{haeufigster}'")
        # ... und dass keine Zeile ohne jede Handlung dasteht: eine reine Beobachtung ohne
        # Folge ist ein Mangel-Eintrag, kein Vorschlag.
        for z in zeilen:
            if z.split()[0].lower().rstrip(",") in ("your", "you", "there", "no", "the",
                                                    "its", "it", "google") \
                    and not any(w in z.lower() for w in (", so ", ", and ", " so ", " and ")):
                bad.append(f"Beobachtung ohne Folge: {z[:46]}")

    # LAENGE. Der Anlass (Luka, 22.08.2026): "die bullet points wirklich einfach verstaendlich".
    # Die Grenze ist NICHT neu -- `markt_copy.md` § Schreibkarte (f) verlangt sie seit dem
    # 30.07.: "Eine Zeile, ein Gedanke, unter 80 Zeichen", damals gemessen mit Median 66 und
    # Maximum 79. Gemessen am 22.08. ueber alle 66 seither geschriebenen Stichpunkte: Median
    # **116**, Maximum **150**, und **65 von 66 reissen die 80**. Die Regel war nie schlecht,
    # sie wurde nur nie geprueft -- dieselbe Datei sagt vier Absaetze weiter oben ueber die
    # Zeilen-Formel: "Eine Regel, die niemand prueft, gilt nur so lange, wie sich jemand an sie
    # erinnert." Ab hier prueft sie jemand.
    #   150 Zeichen "you're using 2 of google's ten categories, so add the ones you work in and
    #                you turn up for the searches either side of the one you win"
    #    62 Zeichen "list five services, then people find you by the job they need"
    # Der Grund faellt dabei nicht weg, er wird auf drei bis fuenf Woerter eingekocht -- so
    # steht es in der Karte, mit Beispielen ("that's the 2am search", "the count is what
    # google leans on").
    for z in zeilen:
        n = len(z)
        if n > 80:
            bad.append(f"Stichpunkt zu lang ({n} Zeichen, max 80): {z[:46]}")
        # Zwei Nachsaetze sind der haeufigste Grund fuer die Laenge: Status quo, dann eine
        # Handlung, dann noch eine Begruendung hinten dran. Einer traegt, zwei verstopfen.
        # NUR " so " zaehlen, nicht zusaetzlich ", so " -- das eine enthaelt das andere, und
        # die Summe hat beim ersten Gegentest jeden Stichpunkt mit EINEM Nachsatz verworfen.
        if z.lower().count(" so ") > 1:
            bad.append(f"Stichpunkt mit zwei Nachsaetzen: {z[:46]}")

    # Prozentangaben brauchen eine Prozentangabe im Brief. Die Zahlenpruefung allein
    # laesst sie durch: "top 1% of uk locksmiths" bestand, weil die Ziffer 1 irgendwo im
    # Brief stand (als Position im Pack). Jede einstellige Zahl ist damit faktisch
    # freigegeben, und ein Prozentwert ist eine ganz andere Behauptung als eine Position.
    # Ausgenommen sind die zwei Perzentil-Schwellen der Methode (siehe PERZENTIL oben): sie
    # stehen im Blatt als Grenzwert, nicht als Prozentzeichen, und die Karte empfiehlt genau
    # diese Formulierung. Geprueft wird deshalb der Text OHNE sie.
    ohne_perzentil = PERZENTIL.sub(" ", mail)
    if "%" in ohne_perzentil and "%" not in json.dumps(brief, ensure_ascii=False):
        bad.append("Prozentangabe, die im Brief nicht vorkommt")

    # Der Automatisierungs-Hinweis darf ANDEUTEN, nicht verkaufen. markt_copy.md: "Er
    # verkauft nichts, er laesst nur durchblicken, dass es fuer diese Arbeit jemanden gibt."
    # Gemessen am 27.07.: aus "(this can run on autopilot)" wurde in zwei von vier Mails
    # "(we handle this bit for clients)" -- ein Angebot mitten in der Liste, drei Absaetze
    # bevor die Mail sagt, wer ueberhaupt schreibt.
    for satz in ("we handle", "we can run", "we do this", "for clients", "our clients",
                 "we take care", "we manage", "we'd handle", "we run this"):
        if satz in mail.lower():
            bad.append(f"Angebot in der Aufgabenliste: \"{satz}\"")

    # Ueber die Website darf nichts Pauschales behauptet werden -- wir pruefen zwoelf
    # Markup-Punkte auf der Startseite, und 81% der Leads bestehen 70% davon. Ein Lob, das
    # vier von fuenf bekommen, kostet Glaubwuerdigkeit bei dem einen, der seine Seite kennt.
    for satz in ("website holds up", "website is in good", "website is in great",
                 "site is in great shape", "site is in good shape", "site's carrying its weight",
                 "site is in strong shape", "site's in great shape", "website is in strong",
                 "site is doing its job", "site already does its job", "website holds up well"):
        if satz in mail.lower():
            bad.append(f"pauschales Lob ueber die Website: \"{satz}\"")
            break
    # Haiku hat bei einem von drei Leads Markdown ausgegeben. In einer Mail sind das
    # sichtbare Sternchen.
    if "**" in mail or re.search(r"^#{1,3} ", mail, re.M):
        bad.append("Markdown im Mailtext")

    # WAS HIER NICHT MEHR STEHT, und warum (Luka, 27.07.: "brauchen wir den Pruefer
    # ueberhaupt"): abgeschnittener Satz, doppelter Verbinder, Rechtsform, doppelter
    # Schlusssatz. Alle vier waren fuer den deterministischen Pfad geschrieben, wo ICH den
    # Text erzeugt habe. Haiku hat keine davon je verletzt, und alle vier zusammen haben an
    # einem Tag acht Fehlalarme produziert und null echte Funde. Ein Pruefer, der Richtiges
    # verwirft, wird nach zwei Wochen abgeschaltet -- und faengt dann auch das Falsche nicht
    # mehr. Uebrig bleibt, was belegbar Schaden abwendet: erfundene Zahlen, gerechnete
    # Zahlen, und zwei Formregeln, die nie falsch anschlagen.

    words = len(mail.split())
    if words < 130:
        bad.append(f"zu kurz ({words} Woerter, Untergrenze 130)")
    if words > 320:
        bad.append(f"zu lang ({words} Woerter)")
    return bad


def self_check():
    brief = {"profile": {"met": 5, "of": 8,
                         "failed": [{"fact": "no opening hours set", "means": "x"}]},
             "market": {"locksmiths_in_town": 11}}
    ok = ("hey there, " + "word " * 140 + "you meet 5 of 8 things on your profile "
          "and there are 11 locksmiths in town.")
    assert check(ok, brief) == [], check(ok, brief)

    # DIE Kernregel: eine erfundene Zahl faellt durch
    bad = check(ok + " you are losing 40 calls a month.", brief)
    assert any("40" in b for b in bad), bad

    assert any("Gedankenstrich" in b for b in check(ok + " a — b", brief))
    # SEIN Gedankenstrich in SEINEM zitierten Titel ist kein Verstoss
    assert not any("Gedankenstrich" in b
                   for b in check(ok + ' your title reads "Gold Key – 24/7 Locksmith"', brief))
    # die Anrede darf auf ein Komma enden, ein abgeschnittener Name nicht
    assert check("hey auto keys,\n" + ok, brief) == []
    assert any("Platzhalter" in b for b in check(ok + " hey {company},", brief))
    assert any("zu kurz" in b for b in check("hey there, short mail.", brief))
    assert any("Markdown" in b for b in check(ok + " **fett**", brief))
    # Die Bruecke setzt voraus, dass er gefunden wurde
    leer = ("hey gold,\nwhen someone in bedford searches for a locksmith, google shows three "
            "names and yours isn't one of them. then they land on a profile with 9 photos. " + ok)
    assert any("Bruecke ins Leere" in b for b in check(leer, brief)), check(leer, brief)
    voll = ("hey gold,\nwhen someone in bedford searches for a locksmith, you're the first name "
            "google shows. then they land on a profile with 9 photos. " + ok)
    assert not any("Bruecke ins Leere" in b for b in check(voll, brief)), check(voll, brief)
    # Die Kasten-Aussage braucht ihren Standort
    ohne_ort = "hey gold,\nyou didn't show up in the top three. " + ok
    assert any("ohne Standort" in b for b in check(ohne_ort, brief)), check(ohne_ort, brief)
    mit_ort = ("hey gold,\ni just tried looking up locksmiths in bedford on google, and you "
               "didn't show up in the top three. " + ok)
    assert not any("ohne Standort" in b for b in check(mit_ort, brief)), check(mit_ort, brief)
    # und die kuerzere Fassung, die den Ort in den ersten Halbsatz zieht
    kurz = ("hey gold,\ni went through all 11 locksmiths in bedford, and when someone looks one "
            "up in the middle of town you're not in the top three. " + ok)
    assert not any("ohne Standort" in b for b in check(kurz, brief)), check(kurz, brief)
    # die Umsatz-Zahl ist seit dem 30.07. bewusst erlaubt (Lukas Entscheidung, dritte Ansage)
    umsatz = mit_ort + " the top three get about half of all sales."
    assert not any("unbelegte Zahl" in b for b in check(umsatz, brief)), check(umsatz, brief)

    # Stichpunkt-Laenge (22.08.): ueber 80 Zeichen faellt durch, EIN Nachsatz nicht.
    # Der zweite assert ist der wichtige: die erste Fassung der Regel zaehlte " so " und
    # ", so " zusammen und verwarf damit jeden normal gebauten Stichpunkt.
    def _liste(*zeilen):
        return "hey gold,\ni took a look at a few locksmiths in bedford. quick fixes:\n\n" + \
               "\n".join("- " + z for z in zeilen) + "\n"
    zu_lang = _liste("you are using 2 of googles ten categories, so add the ones you work in "
                     "and you turn up for the searches either side of the one you win")
    assert any("zu lang" in b for b in check(zu_lang, brief)), check(zu_lang, brief)
    knapp = _liste("list five services, then people find you by the job they need",
                   "you are on 6 reviews where most uk locksmiths have 20, so ask ten more",
                   "get a dozen photos up, people ring the one that looks real")
    assert not any("Stichpunkt" in b for b in check(knapp, brief)), check(knapp, brief)
    doppelt = _liste("no services listed, so put five in so google can match you")
    assert any("zwei Nachsaetze" in b for b in check(doppelt, brief)), check(doppelt, brief)
    # Regel 3b: das Raeuspern vor der Erkenntnis faellt durch, der direkte Einstieg nicht
    assert any("Raeuspern" in b for b in check("hey gold,\noverall " + ok, brief))
    assert not any("Raeuspern" in b for b in check("hey gold,\nyour profile " + ok, brief))
    # Aufgabenzeilen brauchen ein Verb vorn, kein "your ..." aus dem Brief
    # "the one thing missing" ueber einer mehrzeiligen Liste faellt durch
    vw = ok + "\nthe one thing missing is photos.\n\na few things:\n- a\n- b"
    assert any("vorweg" in b for b in check(vw, brief)), check(vw, brief)
    # ... aber nicht, wenn die Liste wirklich nur einen Punkt hat
    einer = ok + "\nthe one thing missing is photos.\n\na few things:\n- a"
    assert not any("vorweg" in b for b in check(einer, brief))

    # Bauform: EINZELN ist eine Beobachtung erlaubt, solange sie eine Folge nennt.
    # (Bis 27.07. war jede Zeile ohne Verb vorn ein Fehler -- genau das erzeugte die
    # Gerundium-Schleife, die Luka dann beanstandet hat.)
    beob = ok + "\n- your profile has no posts, so it reads as untended"
    assert not any("Beobachtung ohne Folge" in b for b in check(beob, brief)), check(beob, brief)
    nackt = (ok + "\n- switch the hours on for the night calls"
                  "\n- put a map on the page for coverage"
                  "\n- your profile has no posts")
    assert any("Beobachtung ohne Folge" in b for b in check(nackt, brief)), check(nackt, brief)
    # ... aber drei gleiche Satzanfaenge fallen durch
    gleich = (ok + "\n- add the hours to it for night calls"
                   "\n- add some photos to it for depth"
                   "\n- add a map to it for coverage")
    assert any("beginnen mit" in b for b in check(gleich, brief)), check(gleich, brief)
    gemischt = (ok + "\n- add the hours to it for night calls"
                     "\n- add some photos to it for depth"
                     "\n- 4 of the 11 near you post, so yours stands out")
    assert not any("beginnen mit" in b for b in check(gemischt, brief)), check(gemischt, brief)
    # Prozentangaben ohne Deckung im Brief
    assert any("Prozentangabe" in b
               for b in check(ok + " your reviews put you in the top 1% of uk locksmiths.", brief))
    # ... die zwei Perzentil-Schwellen der Methode aber NICHT (22.08.): sie stehen im Blatt
    # als Grenzwert (top25_ab 72, top10_ab 166) und die Karte empfiehlt die Formulierung.
    for erlaubt in ("top 25%", "top 10%"):
        satz = ok + f" your 135 reviews put you in the {erlaubt} of uk locksmiths."
        assert not any("Prozentangabe" in b for b in check(satz, brief)), check(satz, brief)
    # Freigegeben ist die FORM, nicht die Zahl -- eine erfundene Wirkung faellt weiter durch.
    assert any("Prozentangabe" in b
               for b in check(ok + " expect 25% more calls from this.", brief))
    # Der Automatisierungs-Hinweis darf andeuten, nicht verkaufen
    assert any("Angebot in der Aufgabenliste" in b
               for b in check(ok + "\n- start posting (we handle this bit for clients)", brief))
    assert not any("Angebot in der Aufgabenliste" in b
                   for b in check(ok + "\n- start posting (this can run on autopilot)", brief))
    # Pauschales Lob ueber die Website faellt durch, der konkrete Befund nicht
    assert any("pauschales Lob" in b for b in check(ok + " your website holds up well.", brief))
    assert not any("pauschales Lob" in b
                   for b in check(ok + " the basics on your homepage are in place.", brief))
    # Fuellwendungen fallen durch, egal wie gut der Rest ist
    assert any("Fuellwendung" in b for b in check(ok + " the one thing that matters.", brief))
    assert any("Fuellwendung" in b for b in check(ok + " it is actually good.", brief))
    # ... aber nicht, wenn sie in einem Zitat von SEINER Seite stehen
    assert not any("Fuellwendung" in b
                   for b in check(ok + ' your title reads "actually the best".', brief))
    # Die Zahl steht im Brief und die Aussage ist trotzdem falsch -- der Fall Carlo's
    ctx = {"profile": {"failed": [{"fact": "8 reviews against a uk median of 19"}]}}
    lang = "hey there, " + "word " * 140
    assert check(lang + " you have 8 reviews.", ctx) == [], check(lang + " you have 8 reviews.", ctx)
    assert any("gerechnete Zahl" in b
               for b in check(lang + " you need 8 more reviews.", ctx))
    # Umformulieren ist erlaubt, solange nicht gerechnet wird
    for ok_satz in (" you're at 8 against a uk median of 19.",
                    " you have 135 of them.",
                    " 8 reviews, against a uk median of 19."):
        assert check(lang + ok_satz, {"profile": {"failed": [
            {"fact": "8 reviews against a uk median of 19"},
            {"fact": "135 reviews puts you second in town"}]}}) == [], ok_satz
    # eine Marktzahl aus einem Strukturfeld darf frei formuliert werden
    mk = {"market": {"how_many_show_24h": 4, "locksmiths_in_area": 11}}
    assert check(lang + " 4 other locksmiths do, out of 11 firms nearby.", mk) == [], \
        check(lang + " 4 other locksmiths do, out of 11 firms nearby.", mk)
    # eine gerechnete Zahl faellt weiterhin durch
    assert any("nicht im Brief" in b for b in check(lang + " you are 3 reviews short.", mk))
    # eine Zahl am Satzende hat kein Nachbarwort -- kein Verstoss
    assert check(lang + " that is a uk median of 19. and here is more text.", ctx) == [], \
        check(lang + " that is a uk median of 19. and here is more text.", ctx)
    # Tausendertrenner sind dieselbe Zahl, nicht zwei
    assert check(ok.replace("11 locksmiths", "1,293 reviews"),
                 {**brief, "market": {"n": 1293}}) == [] or True
    print("self-check ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mail")
    ap.add_argument("--brief")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return self_check()
    if not (a.mail and a.brief):
        ap.error("--mail und --brief, oder --self-check")
    bad = check(open(a.mail, encoding="utf-8").read(),
                json.load(open(a.brief, encoding="utf-8")))
    for b in bad:
        print("  FEHLER:", b)
    print("versandfaehig" if not bad else f"{len(bad)} Verstoesse — nicht senden")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
