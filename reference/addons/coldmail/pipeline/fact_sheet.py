#!/usr/bin/env python3
"""fact_sheet.py — alles Gemessene je Lead auf einem Blatt, fuer den Schreiber.

DER ANLASS (Luka, 30.07.2026): "wenn ich von groesstem hebel rede, ist dabei natuerlich auch
der eindruck ueber das gesamtbild wichtig. die stichpunkte sollen wirken wie jemand, der das
wissen ueber das ganze business hat und dann kontextbasiert die richtigen insights gibt, und
das vielleicht auch cross-references zwischen verschiedenen gbp-zahlen findet."

WARUM DAS `pool.py` NICHT KANN, und zwar prinzipiell: dort ist jeder Baustein an EINE Zahl
gebunden. Ein Baustein ueber Fotos sieht die Bewertungszahl nicht, einer ueber die
Antwortquote sieht die Oeffnungszeiten nicht. Saetze wie

    "1328 reviews and one photo -- the trust is there, the shop window is empty"
    "you answer every review, and the profile still doesn't say you're open at 2am"

entstehen erst, wenn zwei Zahlen zusammen betrachtet werden. Kein Pool aus Einzelzeilen
erzeugt sie, egal wie gut die Gewichtung ist.

DIE ARBEITSTEILUNG BLEIBT TROTZDEM:
  Python  rechnet, vergleicht mit der Kohorte, sagt WIE GROSS jede Luecke ist  (hier)
  Agent   sieht das ganze Blatt, waehlt aus, verbindet, formuliert
  Python  prueft mechanisch nach (verify_mail.py) -- deshalb ist die Auswahl gefahrlos

Kein Urteil in diesem Modul. Es sagt nicht, was wichtig ist -- es legt hin, was gemessen
wurde, samt Vergleichswert. Was daraus die Geschichte ist, entscheidet der Schreiber.

Usage:
  python3 fact_sheet.py --niche locksmith --region Bedford
  python3 fact_sheet.py --niche locksmith --region Bedford --json
  python3 fact_sheet.py --self-check
"""
from __future__ import annotations
import argparse, json, os, re as _re, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def gebiet_lesbar(name: str) -> str:
    """Der Viertelname, wie ihn jemand sagen wuerde.

    Die Namen kommen aus dem amtlichen Verzeichnis und sind Verwaltungsbezeichnungen.
    Gemessen ueber die 540 Grossstadt-Leads: 351 tragen einen sauberen Ortsnamen (Arsenal,
    Oval, Piccadilly), 88 eine angehaengte Himmelsrichtung, 101 einen Doppelnamen mit "&".

    NUR die angehaengte Himmelsrichtung faellt weg: "Plaistow South" -> "Plaistow", weil
    Plaistow der Ort ist und South die Verwaltungshaelfte. Ein VORANGESTELLTES West bleibt
    stehen -- "West Finchley" heisst wirklich so, und daraus "Finchley" zu machen waere eine
    andere Gegend.

    Doppelnamen bleiben ganz. "soho & jewellery quarter" liest sich sperrig, ist aber
    praezise; die erste Haelfte zu nehmen waere geraten, und der Lead koennte in der
    zweiten sitzen.
    """
    import re
    return re.sub(r"\s+(North|South|East|West|Central)$", "", (name or "").strip())


def ortswahl(x: dict, rank: dict, allein: bool) -> dict:
    """Welchen Ort die Mail nennt und wie sie den Messpunkt beschreibt.

    DER FEHLER, den das behebt (gemessen 30.07. ueber 2.731 offene Leads): bei 393 (14%)
    ist der Ort im Profil NICHT der Ort, in dem gemessen wurde. Ein Londoner Betrieb traegt
    `town: London`, gemessen wurde aber in seinem Viertel (Arsenal, Plaistow, Soho &
    Jewellery Quarter). Die Mail sagte dann "die locksmiths in london" und "wenn jemand
    mitten in der stadt sucht" -- beides falsch: "London" ist fuer ihn bedeutungslos (dort
    sitzen Tausende), und die Stadtmitte ist nicht der Punkt, an dem wir gemessen haben.

    Die Regel: **genannt wird der Ort, ueber den die Aussage geht.** Wo ein Kasten gemessen
    wurde, ist das das Messgebiet -- nie der Ort aus dem Profil. Das ist auch die staerkere
    Fassung: "the locksmiths around plaistow" kann er nachpruefen, "in london" nicht.

    `messpunkt` ist die fertige Wendung fuer Satz 2, damit der Schreiber nicht raet:
      allein im Gebiet   -> "right where you are"  (die Mitte IST seine Tuer)
      Gebiet = sein Ort  -> "in the middle of town" (kuerzer, und "town" stimmt)
      Gebiet ist Viertel -> "in the middle of <viertel>"
    Alle drei sind Wendungen, die `verify_mail.STANDORT` als Perspektive akzeptiert.
    """
    profil_ort = (x.get("town") or x.get("region") or "").strip()
    gebiet = gebiet_lesbar(rank.get("gebiet")) or profil_ort
    if allein:
        return {"nenne_ort": gebiet, "messpunkt": "right where you are"}
    if gebiet.lower() == profil_ort.lower():
        return {"nenne_ort": gebiet, "messpunkt": "in the middle of town"}
    return {"nenne_ort": gebiet, "messpunkt": f"in the middle of {gebiet.lower()}"}


def allein_im_gebiet(leads: list) -> dict:
    """place_id -> sitzt dieser Lead als EINZIGER in seinem Messgebiet?

    Dann faellt der Messpunkt (die Mitte der Leads eines Gebiets) mit seiner eigenen Tuer
    zusammen, und der Satz muss das sagen. Betrifft 379 von 2.386 gemessenen Leads: 198 in
    Vierteln der grossen Staedte (dort ist es Absicht -- wir haben London in 229 Viertel
    zerlegt, WEIL "London" zu grob war) und 181 in kleinen Orten.

    Das heisst NICHT, dass der Markt dort leer ist. LockMinded Islington ist unser einziger
    Lead in seinem Viertel und steht auf Platz 3 neben N1 Locksmiths (597 Bewertungen) und
    RS Lock and Safe (222) -- der Kasten wird von allem gefuellt, was Google kennt, nicht
    von unserer Liste. Ein Gebiet mit einem Lead ist eine duenne Stelle bei UNS.
    """
    import collections
    gebiet = collections.Counter()
    for x in leads:
        g = ((x.get("web_signals") or {}).get("rank") or {}).get("gebiet")
        if g:
            gebiet[g] += 1
    out = {}
    for x in leads:
        g = ((x.get("web_signals") or {}).get("rank") or {}).get("gebiet")
        out[x["place_id"]] = bool(g and gebiet[g] == 1)
    return out



def _nachbar_weite(nearest: list) -> str:
    """Die Entfernung des naechsten Nachbarn als fertige Wendung: "400m" oder "1.2km".

    Gerundet auf 100 Meter. Genauer waere Scheingenauigkeit -- die Koordinaten sind
    Google-Mittelpunkte, keine Tuerschwellen -- und eine Zahl wie "383m" liest sich wie
    eine Behauptung, die jemand nachmessen soll.
    """
    km = next((n.get("km") for n in nearest if n.get("km")), None)
    if not km:
        return ""
    meter = int(round(km * 1000 / 100.0)) * 100
    return f"{meter}m" if meter < 1000 else f"{round(km, 1)}km"


def blatt(x: dict, mk: dict, bench: dict, allein: bool = False) -> dict:
    """Eine Supabase-Zeile -> das Datenblatt. Jede Zahl mit ihrem Vergleichswert.

    Leer bleibt leer: was nicht gemessen wurde, steht nicht drin. Ein Feld mit `null` heisst
    "nicht gemessen", nicht "null davon" -- der Unterschied hat am 27.07. vier Faktoren
    unbemerkt Gratispunkte gegeben.
    """
    raw, rd = (x.get("raw") or {}), (x.get("raw_dataforseo") or {})
    ws = x.get("web_signals") or {}
    rank, antw = (ws.get("rank") or {}), (rd.get("antworten") or {})
    kat = raw.get("categories") or []
    dienste = rd.get("services") or []
    themen = rd.get("place_topics") or {}
    b_med = (bench.get("reviews") or {}).get("median")

    def zahl(v):
        return None if v is None else int(v)

    return {
        "name": x.get("name"),
        "ort": x.get("town") or x.get("region"),
        # --- wo er in der Suche steht ---------------------------------------------------
        # `gemessen_wo` sagt dem Schreiber, welchen Satz er nehmen darf. Gemessen wird an
        # der MITTE der Leads eines Gebiets -- sitzt dort nur einer, ist diese Mitte seine
        # eigene Tuer. Das betrifft 379 von 2.386 gemessenen Leads (16%).
        #
        # Dann muss der Satz das auch sagen. Nicht weil "in bedford" gelogen waere, sondern
        # weil "right by you" die staerkere und unangreifbarere Fassung ist: er kann sie
        # selbst nachstellen, und "nicht mal direkt bei dir" trifft haerter als eine
        # Ortsangabe. Gemessen am 30.07.: 8 von 8 Alleinsitzern stehen an der eigenen Tuer
        # im Kasten, zwei Kilometer weiter nur noch 5 -- die Naehe ist also real und der
        # Satz muss sie benennen.
        "kasten": ({"gemessen_in": gebiet_lesbar(rank.get("gebiet")),
                    "gemessen_wo": ("an seiner eigenen tuer -- Satz: 'right by you'"
                                    if allein else "in der Mitte des Gebiets"),
                    "suchwort": rank.get("keyword"),
                    "drin": bool(rank.get("kasten_platz")),
                    "platz": rank.get("kasten_platz"),
                    **ortswahl(x, rank, allein)} if rank.get("kasten_da") else None),
        # Der EINE Konkurrent, der ueber ihm steht und weniger Bewertungen hat -- aus
        # Googles eigener Liste, nicht aus unserer Kohorte. Deshalb ueberlebt er die
        # duenne Datenlage, die jede Aussage ueber den ganzen Ort verbietet: hier geht es
        # um EINEN benannten Betrieb, und den haben wir gemessen. Stand bis 30.07. nicht
        # im Blatt, obwohl die Mails ihn zitierten -- der Zahlen-Pruefer hielt die 73 von
        # Space Locksmiths deshalb fuer erfunden.
        "schwaecher_ueber_dir": rank.get("schwaechster_drueber"),
        # --- Bewertungen: Zahl, Landesmedian, Antwortquote ------------------------------
        "bewertungen": {
            "anzahl": zahl(raw.get("reviewsCount")),
            "sterne": raw.get("totalScore"),
            "uk_median": b_med,
            "beantwortet": zahl(antw.get("beantwortet")),
            "von_geholten": zahl(antw.get("geholt")),
            # Ein- und Zwei-Sterne zusammen, als eigene Zahl (23.08.2026). Der Stichpunkt
            # nennt sie ("you've got 6 bad reviews"), sie ist aus der Verteilung gerechnet
            # und damit belegt -- aber der Zahlen-Pruefer sieht nur, was im Blatt steht, und
            # hielt sie zu Recht fuer erfunden. Derselbe Fall wie `kategorien_offen`.
            "schlechte": (None if not raw.get("reviewsDistribution") else
                          zahl((raw["reviewsDistribution"] or {}).get("oneStar"))
                          + zahl((raw["reviewsDistribution"] or {}).get("twoStar"))),
        },
        # --- WOMIT VERGLICHEN WIRD: das Land, nie der Ort -------------------------------
        # Bis 30.07. standen hier die Ortszahlen (`fotos_median_der_stadt`,
        # `24h_in_der_stadt`, `rang_in_der_stadt`), und der Schreiber hat genau die benutzt:
        # 15 von 21 Mails behaupteten etwas ueber ALLE Betriebe im Ort. Das koennen wir
        # nicht. Der Scrape nahm nur Betriebe mit Website und suchte je Grafschaft statt je
        # Ort, also stehen in Bedford 11 von 27 in der Datenbank und in Hornchurch 1 von 20.
        # Die Ortszahlen sind deshalb nicht nur unbenutzt, sie sind WEG -- was im Blatt
        # steht, landet frueher oder spaeter in einer Mail.
        "land": {
            "n": bench.get("n"),
            "bewertungen_median": b_med,
            "bewertungen_top25_ab": (bench.get("reviews") or {}).get("p75"),
            "bewertungen_top10_ab": (bench.get("reviews") or {}).get("p90"),
            "fotos_median": bench.get("photos_median"),
            "24h_prozent": (bench.get("hours24") or {}).get("ja_pct"),
            "postet_nie_prozent": (bench.get("posts") or {}).get("never_pct"),
        },
        # --- Profil: was drinsteht und was die Nachbarn haben ---------------------------
        "profil": {
            "kategorien": len(kat), "kategorie_liste": kat[:6],
            "kategorien_erlaubt": 10,
            # Die ungenutzten, als eigene Zahl (23.08.2026). Der Stichpunkt nennt sie
            # ("add the rest so 6 more job types find you"), weil eine zaehlbare Folge
            # staerker ist als "mehr Suchen". Sie ist aus 10 minus 4 gerechnet und damit
            # belegt -- aber der Zahlen-Pruefer sieht nur, was im Blatt steht, und hielt
            # sie zu Recht fuer erfunden, solange sie hier fehlte.
            "kategorien_offen": max(0, 10 - len(kat)),
            "leistungen": len(dienste), "leistungen_liste": dienste[:8],
            "fotos": zahl(raw.get("imagesCount")),
            "24h_gezeigt": any("24" in str(d.get("hours", ""))
                               for d in (raw.get("openingHours") or [])),
            "oeffnungszeiten_gesetzt": bool(raw.get("openingHours")),
            "postet": bool(raw.get("ownerUpdates")),
        },
        # --- was Kunden in den Bewertungen sagen ----------------------------------------
        "bewertungs_themen": dict(list(themen.items())[:6]),
        # --- die Nachbarn, gegen die verglichen wurde -----------------------------------
        "nachbarn": [(n.get("name") or "") for n in ((x.get("details") or {}).get("nearest") or [])][:2],
        # Die gemessene Entfernung des naechsten, GERUNDET wie der Baustein sie ausgibt
        # (400m, nicht 0.38km). Sie muss zeichengleich im Blatt stehen, sonst verwirft
        # `verify_mail` sie als erfundene Zahl -- daran sind am 22.08. 14 von 50
        # maschinellen Mails gescheitert, obwohl die Distanz aus dem Scrape stammt.
        "nachbar_entfernung": _nachbar_weite((x.get("details") or {}).get("nearest") or []),
        # Die Bewertungszahl des naechsten Nachbarn. Muss im Blatt stehen, sonst verwirft
        # `verify_mail` sie als erfundene Zahl -- derselbe Fehler wie am 22.08. bei Googles
        # Paarung, und er kostete dort 14 von 50 Mails.
        "nachbar_bewertungen": mk.get("nearest_reviews"),
        # Wen GOOGLE selbst neben ihn stellt (`raw.peopleAlsoSearch`, 52% gefuellt), mit
        # Bewertungszahl. Muss im Blatt stehen, sonst verwirft `verify_mail` die Zahl als
        # "nicht im Brief" -- am 22.08. sind daran 11 von 50 maschinellen Mails gescheitert,
        # obwohl die Zahl direkt aus dem Scrape kam.
        # Die Sternverteilung gehoert INS BLATT, sonst verwirft verify_mail die Ein-Stern-Zahl
        # als "nicht im Brief" -- sie kommt direkt aus dem Scrape und ist damit belegt.
        "sterne_verteilung": raw.get("reviewsDistribution") or {},
        "google_paart": [{"name": p.get("title"), "bewertungen": p.get("reviewsCount"),
                          "sterne": p.get("totalScore")}
                         for p in (raw.get("peopleAlsoSearch") or [])
                         if isinstance(p, dict) and p.get("reviewsCount")][:3],
        # --- was der Audit sonst gefunden hat, nur Profil (die Website ist draussen) ----
        "weitere_luecken": [f.get("fact") for f in (ws.get("findings") or [])
                            if f.get("kind") == "gap" and f.get("area") == "gbp"][:5],
    }


# Rat -> woran man erkennt, dass er schon umgesetzt ist. Der Pruefer, den es am 30.07.
# nicht gab: `verify_mail` kennt nur Mail und Brief, `preview_mail` nur den Zusammenbau.
# Beide liessen sieben von elf Mails durch, die einem Betrieb etwas empfahlen, das er tut.
# Das Muster muss die EMPFEHLUNG treffen, nicht das Thema. Erste Fassung suchte "24 hour"
# und meldete damit auch "you're one of the 5 in bedford showing 24 hours" -- ein Lob. Ein
# Pruefer, der Richtiges verwirft, wird abgeschaltet, und dann faengt er auch das Falsche
# nicht mehr (dieselbe Lehre wie bei der DANGLING-Liste in verify_mail).
RATSCHLAEGE = (
    ("switch on 24 hour", lambda b: b["profil"]["24h_gezeigt"],
     "das Profil zeigt 24 Stunden"),
    ("start posting", lambda b: b["profil"]["postet"], "er postet"),
    ("starting puts you", lambda b: b["profil"]["postet"], "er postet"),
    # drei Formulierungen fuer denselben Rat -- der Pruefer muss alle kennen, sonst
    # rutscht er beim naechsten Umschreiben durch (30.07., "put your services in")
    ("list your services", lambda b: (b["profil"]["leistungen"] or 0) > 0,
     "die Leistungsliste ist gefuellt"),
    ("your services in", lambda b: (b["profil"]["leistungen"] or 0) > 0,
     "die Leistungsliste ist gefuellt"),
    ("write your services", lambda b: (b["profil"]["leistungen"] or 0) > 0,
     "die Leistungsliste ist gefuellt"),
    ("set your opening hours", lambda b: b["profil"]["oeffnungszeiten_gesetzt"],
     "Oeffnungszeiten sind gesetzt"),
    # NICHT GEMESSEN IST NIE EIN WIDERSPRUCH (Fix 22.08.2026). Vorher machte `or 0` aus einem
    # fehlenden Landesmedian eine 0, und damit lag JEDER Betrieb "beim Median oder darueber" --
    # der Pruefer verwarf dann den voellig richtigen Rat "put a few more photos up" bei einem
    # Betrieb mit einem einzigen Foto. Genau dieser Fall stand als roter assert im Selbsttest
    # der Datei. Bei locksmith faellt es nicht auf, weil `benchmarks.json` fotos_median traegt;
    # bei jeder NEUEN Nische feuert es, solange benchmark.py noch nicht gelaufen ist -- also
    # dann, wenn am wenigsten jemand hinsieht.
    ("put a few more photos",
     lambda b: b["land"]["fotos_median"] is not None
     and (b["profil"]["fotos"] or 0) >= b["land"]["fotos_median"],
     "er liegt beim Landesmedian oder darueber"),
)


# Die Zeilen-Formel aus markt_copy.md, mechanisch. Sie stand bisher NUR in der Karte, und
# genau deshalb habe ich sie am 30.07. selbst gebrochen: beim Umbau auf ganze Saetze fiel
# bei 14 von 36 Zeilen die Handlung raus (Luka: "ich dachte wir hatten eine klare struktur
# und prinzipien, die wir einhalten wollen"). Eine Regel, die niemand prueft, gilt nur so
# lange, wie sich jemand an sie erinnert.
HANDLUNG = ("add", "list", "put", "switch", "get", "ask", "answer", "reply", "start",
            "write", "swap", "set", "turn on", "fill")
# "that's who people compare you to" und "that's what people read first" sind Folgen -- sie
# sagen, warum die Handlung zaehlt, nur ohne Bindewort. Die Liste kannte am 22.08. nur die
# Bindewort-Form und verwarf damit drei richtig gebaute Bausteine. Geprueft wird die Absicht,
# nicht die Konjunktion.
FOLGE = (" so ", " and ", " because ", ", it's", ", people", ", the count",
         "that's who", "that's what", "that's the", "before anyone", "before they")


def formel(zeile: str) -> list:
    """-> was dieser Stichpunkt-Zeile fehlt: Status quo, Handlung oder Folge.

    STATUS QUO  eine gemessene Zahl oder ein Zustandswort ("nothing", "nobody", "not")
    HANDLUNG    ein Verb, das er anfassen kann
    FOLGE       was es bringt, angehaengt mit so/and/because
    """
    t = " " + zeile.lower().lstrip("- ") + " "
    fehlt = []
    # Status quo: eine Zahl, eine ausgeschriebene Zahl, oder ein Zustandswort
    # "no <etwas>" gehoert dazu (22.08.2026): die Liste kannte "no reply", aber nicht
    # "no description", "no services listed", "no hours set" -- alles gemessene Zustaende
    # in genau derselben Form. Beim ersten maschinellen Lauf fielen dadurch 33 von 50 Mails
    # durch, obwohl ihr Status quo dastand. Geprueft wird jetzt das Muster, nicht die
    # einzelne Wendung.
    # "doesn't/don't/hasn't" (23.08.2026): die Liste kannte "isn't" und "aren't", aber
    # nicht die do-Formen -- "your profile doesn't say it" ist derselbe gemessene Zustand
    # in derselben Rolle und fiel trotzdem durch. Wieder das Muster von oben: geprueft wird
    # die Verneinung, nicht die einzelne Wendung.
    ZUSTAND = ("nothing", "nobody", "not showing", "not posting", "you're not",
               "isn't", "aren't", "doesn't", "don't", "hasn't", "haven't",
               # "missing" (23.08.2026): "key duplication service is missing on yours" ist
               # ein gemessener Zustand in genau derselben Rolle wie "no X on the profile".
               # Ohne dieses Wort fielen 277 von 2.717 Mails durch, alle aus demselben
               # Baustein. Dritte Erweiterung derselben Liste an einem Tag -- das Muster ist
               # jedes Mal dasselbe: die Liste kennt EINE Formulierung der Verneinung und
               # verwirft die anderen. Geprueft gehoert die Verneinung, nicht die Wendung.
               "missing", "not set", "not listed",
               "only", "set to", "one photo", "one review", "empty")
    HAT_NO = _re.search(r"\bno [a-z]", t) or _re.search(r"\bnone of\b", t)
    if not (any(c.isdigit() for c in t) or any(w in t for w in ZUSTAND) or HAT_NO):
        fehlt.append("Status quo")
    # Handlung -- ODER die dokumentierte Ausnahme: eine Zeile, die die URSACHE benennt,
    # impliziert die Handlung ("so it's the words on the profile costing you the calls").
    URSACHE = ("costing you", "keeping you out", "holding you back", "isn't reputation",
               "isn't effort", "not the reputation")
    if not any(f" {v}" in t for v in HANDLUNG) and not any(u in t for u in URSACHE):
        fehlt.append("Handlung")
    if not any(f in t for f in FOLGE):
        fehlt.append("Folge")
    # EINE ZWEITE HANDLUNG IST KEINE FOLGE (23.08.2026, Luka: "'so add it' sollte nie
    # alleinstehen, es sollte immer auch kommuniziert werden, was der benefit ist").
    # "..., so add it" erfuellt die Formel dem Buchstaben nach -- ein Bindewort steht da,
    # ein Verb auch -- und sagt dem Empfaenger trotzdem nichts darueber, was es ihm bringt.
    # Geprueft wird deshalb, was NACH dem Bindewort steht: eine blosse Aufforderung zaehlt
    # nicht als Folge.
    elif _re.search(r"\bso (add|list|put|set|switch|fix|do) (it|them|these|those|that)"
                    r"( too| as well| now)?\b[^a-z]*$", t.strip()):
        fehlt.append("Folge (nur eine zweite Handlung nach 'so')")
    return fehlt


def widerspricht(b: dict, mail: str) -> list:
    """-> Raete in dieser Mail, die der Betrieb laut Datenblatt schon umgesetzt hat.

    Der teuerste Fehler dieser Kampagne nach dem falschen Rang: "switch on 24 hour opening"
    an ein Profil, auf dem "Open 24 hours" steht. Er sagt dem Empfaenger woertlich, dass wir
    nicht nachgesehen haben -- und er ist mit einem Blick auf das eigene Profil widerlegt.
    """
    text = mail.lower()
    out = []
    for muster, schon, grund in RATSCHLAEGE:
        try:
            if muster in text and schon(b):
                out.append(f"empfiehlt \"{muster}\", aber {grund}")
        except (TypeError, KeyError):
            continue
    return out


def self_check():
    x = {"name": "Gold Key Locks", "town": "Bedford",
         "raw": {"reviewsCount": 9, "imagesCount": 1, "categories": ["Locksmith"],
                 "openingHours": [{"day": "Monday", "hours": "Open 24 hours"}],
                 "ownerUpdates": []},
         "raw_dataforseo": {"antworten": {"geholt": 8, "beantwortet": 8},
                            "services": [], "place_topics": {"car key": 5}},
         "web_signals": {"rank": {"kasten_da": True, "kasten_platz": 2, "gebiet": "Bedford",
                                  "keyword": "locksmith"},
                         "findings": [{"kind": "gap", "area": "gbp", "fact": "no services listed"},
                                      {"kind": "gap", "area": "site", "fact": "kein Titel"}]}}
    mk = {"reviews_rank": 3, "count": 11, "cats_median": 2, "photos_median": 14,
          "photos_leader": 1219, "with_24h": 5, "with_posts": 3}
    b = blatt(x, mk, {"reviews": {"median": 20}})
    assert b["kasten"]["drin"] is True and b["kasten"]["platz"] == 2
    assert b["bewertungen"]["anzahl"] == 9 and b["bewertungen"]["uk_median"] == 20
    assert b["profil"]["24h_gezeigt"] is True and b["profil"]["postet"] is False
    # die Website bleibt draussen, auch wenn der Audit sie gefunden hat
    assert b["weitere_luecken"] == ["no services listed"], b["weitere_luecken"]
    # ohne Kasten-Messung gibt es kein Kasten-Feld, statt eines geratenen "nicht drin"
    # angehaengte Himmelsrichtung faellt weg, vorangestellte bleibt
    assert gebiet_lesbar("Plaistow South") == "Plaistow"
    assert gebiet_lesbar("West Finchley") == "West Finchley"
    assert gebiet_lesbar("Soho & Jewellery Quarter") == "Soho & Jewellery Quarter"
    assert gebiet_lesbar("Arsenal") == "Arsenal"
    # allein im Gebiet -> der Satz muss die eigene Tuer nennen
    zwei = [{"place_id": "a", "web_signals": {"rank": {"gebiet": "Arsenal"}}},
            {"place_id": "b", "web_signals": {"rank": {"gebiet": "Arsenal"}}},
            {"place_id": "c", "web_signals": {"rank": {"gebiet": "Oval"}}}]
    al = allein_im_gebiet(zwei)
    assert al == {"a": False, "b": False, "c": True}, al
    assert "right by you" in blatt(x, mk, {}, allein=True)["kasten"]["gemessen_wo"]
    assert "Mitte" in blatt(x, mk, {}, allein=False)["kasten"]["gemessen_wo"]
    ohne = blatt({**x, "web_signals": {}}, mk, {})
    assert ohne["kasten"] is None and ohne["bewertungen"]["uk_median"] is None

    # der Pruefer gegen den Bestand: Gold Key zeigt 24 Stunden und postet nicht
    assert widerspricht(b, "- switch on 24 hour opening, and the 2am call stops going") \
        == ['empfiehlt "switch on 24 hour", aber das Profil zeigt 24 Stunden']
    # ein LOB ueber dieselbe Sache ist kein Verstoss
    assert widerspricht(b, "- you're one of the 5 in bedford showing 24 hours, and") == []
    assert widerspricht(b, "- only 3 of the 11 near you post, so starting puts you") == []
    # und er meldet nichts, wo nichts ist
    assert widerspricht(b, "- put a few more photos up") == [], "1 Foto gegen Median 14"
    # Die Formel: was fehlt, wird benannt
    assert formel("- there's nothing under services, so put five in and stop losing that "
                  "search to auto keys") == []
    assert formel("- there's nothing under services, so someone searching finds auto keys "
                  "instead") == ["Handlung"], formel(
        "- there's nothing under services, so someone searching finds auto keys instead")
    assert "Status quo" in formel("- add emergency locksmith and you win those searches")
    # die dokumentierte Ausnahme: wer die Ursache benennt, braucht kein Verb
    assert formel("- your 53 photos are the most in bedford, so it's the words on the "
                  "profile costing you the calls") == []
    # ausgeschriebene Zahl zaehlt als Status quo
    assert formel("- there's one photo on the profile, so get a dozen up and people ring "
                  "the firm that looks real") == []
    assert "Folge" in formel("- you're on 9 photos, add a dozen more")
    print("fact_sheet self-check ok")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--niche", default="locksmith")
    ap.add_argument("--region")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check or not a.region:
        return self_check()

    import benchmark
    from build_lead_findings import market_context
    from dedupe_leads import _supabase
    url, key = _supabase()
    hdr = {"apikey": key, "Authorization": f"Bearer {key}"}
    q = (f"{url}/rest/v1/industry_operators?select=place_id,name,town,region,details,raw,"
         f"raw_dataforseo,web_signals&niche=eq.{urllib.parse.quote(a.niche)}"
         f"&region=eq.{urllib.parse.quote(a.region)}&pipeline_status=neq.disqualified")
    rows = json.load(urllib.request.urlopen(urllib.request.Request(q, headers=hdr), timeout=90))
    kohorte = [r["raw"] or {} for r in rows]
    bench = benchmark.load(a.niche)
    allein = allein_im_gebiet(rows)
    blaetter = {r["place_id"]: blatt(r, market_context(kohorte, r["raw"] or {}), bench,
                                     allein.get(r["place_id"], False))
                for r in rows if (r.get("web_signals") or {}).get("findings")}
    if a.json:
        print(json.dumps(blaetter, ensure_ascii=False, indent=1))
    else:
        for pid, b in blaetter.items():
            print(f"--- {pid} | {b['name']}")
            print(json.dumps(b, ensure_ascii=False, indent=1))
    print(f"\n{len(blaetter)} Datenblaetter", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
