#!/usr/bin/env python3
"""score.py — zwei Zahlen, die der Inhaber in einer Sekunde versteht.

Der Anlass (Luka, 27.07.2026): "vielleicht koennten wir auch einen Score verteilen fuer
Google Business Profil und fuer die Webseite, und sagen dass wir noch weitere Scores haben
fuer SEO und AI Visibility, mit genauer Zusammensetzung und was zu tun ist, um sie auf 100
zu bringen."

Warum das in einer Kaltmail funktioniert: fuenf Stichpunkte muss man lesen, "62 von 100"
versteht man sofort. Und eine Zahl erzeugt eine Frage, die eine Liste nie erzeugt -- warum
62, und was fehlt zu 100. Genau diese Frage ist der Grund zu antworten.

DIE REGEL, DIE HIER ALLES TRAEGT: der Score darf dem spaeteren Report NIE widersprechen.
Der Report rechnet mit DataForSEO, Lighthouse und Geo-Grid, die es beim Kaltlead nicht gibt.
Also wird hier NICHT dieselbe Zahl geschaetzt, sondern eine ehrlich kleinere gerechnet: nur
das von aussen Sichtbare, und die Mail sagt genau das. Aus der Begrenzung wird der Haken --
zwei von vier Scores stehen, die anderen beiden brauchen den tieferen Zug.

NICHT GEMESSEN IST NIE EIN ABZUG. Ein Check, dessen Datenfeld fehlt (Oeffnungszeiten ohne
Detailseite), faellt aus ZAEHLER UND NENNER. Sonst bestraft der Score den Lead fuer eine
Luecke in unserem Scrape, und wir schicken ihm eine Zahl, die wir nicht verteidigen koennen.

Die Check-IDs sind dieselben wie in findings.py und lead-magnet/audit.py. Das ist der
einzige Grund, warum Mail und Report nicht auseinanderlaufen koennen.

Usage:
  python3 score.py --self-check
"""
from __future__ import annotations
import sys

# Gewicht = wie viel dieser Punkt fuer einen NOTDIENST wiegt, nicht wie fein er technisch ist.
# Rund-um-die-Uhr schlaegt Schema-Markup um Laengen, weil das eine den Auftrag um zwei Uhr
# entscheidet und das andere eine Zeile im Quelltext ist.
GBP_WEIGHTS = {
    "gbp-claimed": 20,
    "gbp-hours": 18,
    "gbp-secondary-categories": 16,
    "gbp-services": 14,
    "gbp-reviews-volume": 12,
    "gbp-photos": 6,
    "gbp-posts": 4,
}
MIN_FACTORS = 5     # darunter ist es keine Bewertung, sondern eine Beobachtung

SITE_WEIGHTS = {
    "web-own-site": 22,
    "web-tap-to-call": 20,
    "web-viewport": 18,          # ohne Viewport ist die Seite auf dem Handy unbenutzbar
    "web-nap-consistency": 16,   # Nummer auf der Seite gegen die im Profil
    "web-title": 16,
    "web-lead-capture": 14,
    "web-location-content": 12,
    # Die erste sichtbare Zeile der Seite. Feuerte bei 11 von 56 abgerufenen Sites, zaehlte
    # aber nie -- ein Befund ohne Gewicht ist ein Befund, den der Score verschweigt.
    # Bewusst leichter als web-title (16): beide messen "nennt es Job und Ort", nur auf
    # zwei Flaechen. Gleiches Gewicht wuerde denselben Mangel doppelt bestrafen.
    "web-h1": 12,
    "web-schema": 8,
    "web-word-readability": 8,
    "web-meta-og": 6,
    "web-map-embed": 5,
    "web-lang": 3,
}


def score(findings: list, measured: set, weights: dict) -> tuple:
    """-> (0-100, [was am meisten kostet]). None, wenn nichts gemessen wurde.

    `measured` sind die Check-IDs, zu denen wir ueberhaupt Daten hatten. Alles andere
    faellt aus der Rechnung, statt als Mangel zu zaehlen.
    """
    applicable = {c: w for c, w in weights.items() if c in measured}
    # Unter drei Faktoren ist es kein Score, sondern eine einzelne Beobachtung mit einer
    # Zahl davor. Der Lauf zeigte "your site 100 across 1" -- ein Betrieb, dessen Seite wir
    # nicht abrufen konnten, bekam die Bestnote fuer den einen Punkt, den wir pruefen
    # konnten. Lieber gar keine Zahl als eine, die bei der ersten Rueckfrage zerfaellt.
    if len(applicable) < MIN_FACTORS:
        return None, []
    failed = {f["check"] for f in findings if f["kind"] == "gap"}
    lost = {c: w for c, w in applicable.items() if c in failed}
    total = sum(applicable.values())
    pts = round((total - sum(lost.values())) * 100 / total)
    costly = sorted(lost.items(), key=lambda x: -x[1])
    return pts, [c for c, _ in costly]


def measured_gbp(place: dict) -> set:
    """Welche GBP-Checks dieser Scrape ueberhaupt beantworten kann.

    Die Detailseite bringt Oeffnungszeiten, Beitraege und die Themen aus den Bewertungen.
    Fehlt sie, sind diese drei nicht 'schlecht', sondern unbekannt -- und unbekannt darf
    keine Punkte kosten.
    """
    out = {"gbp-claimed", "gbp-secondary-categories", "gbp-reviews-volume",
           "gbp-photos"}
    # Zwei Wege, auf denen die Oeffnungszeiten als gemessen gelten: sie sind da, ODER die
    # Detailseite wurde geholt und sie sind trotzdem leer -- dann ist "keine gesetzt" ein
    # Befund und keine Luecke. Ohne den zweiten Fall behauptete die Mail "no opening hours
    # set" und schrieb zwei Absaetze spaeter, sie habe die Zeiten nicht pruefen koennen.
    # `_detail` setzt detail_backfill.py, wenn der Detail-Lauf nachweislich durch ist. Die
    # OR-Kette dahinter bleibt fuer Scrapes, die vor dem Marker entstanden sind -- sie raet
    # richtig, solange der Betrieb ueberhaupt Bewertungen hat, und genau daran scheitert sie
    # bei einem frisch gelisteten Betrieb ohne eine einzige.
    detail = bool(place.get("_detail")) or any(
        place.get(k) for k in ("ownerUpdates", "imageUrls", "reviewsTags",
                               "peopleAlsoSearch", "additionalInfo"))
    if place.get("openingHours") or detail:
        out.add("gbp-hours")
    if detail:
        out.add("gbp-posts")
    if place.get("reviewsTags"):
        out.add("gbp-services")
    return out


# Checks, die nur ein Crawl ueber MEHRERE Seiten beantworten kann. Der Standardlauf holt
# die Startseite, `pages` bleibt None -- dann sind sie nicht gemessen, sondern unbekannt.
# Ohne diese Trennung konnte web-location-content in keinem echten Lauf durchfallen und
# schenkte jedem Lead seine 12 Punkte. Derselbe Fehler wie damals bei gbp-posts.
NUR_MIT_CRAWL = {"web-location-content"}


def measured_site(html: str, url: str, pages: list | None = None) -> set:
    """Ohne abgerufenes HTML ist NICHTS an der Website gemessen -- ausser der Frage,
    ob es ueberhaupt eine eigene ist. Ein Facebook-Profil beantwortet die, und nur die."""
    if not url:
        return set()
    if not html:
        return {"web-own-site"}
    return set(SITE_WEIGHTS) - (set() if pages else NUR_MIT_CRAWL)


# Was ein Check in der Sprache des Inhabers ist. Nur Punkte, die er sich vorstellen kann --
# "LocalBusiness-Markup" gehoert nicht in eine Zeile, die Neugier wecken soll.
LABELS = {
    "gbp-description": "what your profile says about you",
    "gbp-services": "whether your profile lists what your reviews keep praising",
    "gbp-hours": "whether google shows you as open at night",
    "gbp-posts": "how often you post",
    "gbp-qa": "the questions people left on your profile",
    "web-lighthouse": "how fast the site loads on a phone",
    "web-lead-capture": "how someone reaches you without calling",
    "gbp-map-reach": "how far your listing actually reaches on the map",
    "gbp-review-velocity": "how fast new reviews come in",
    "gbp-response-rate": "how many reviews you answered",
}


def limits(measured: set, weights: dict, cap: int = 3) -> list:
    """Was dieser Scrape NICHT beantworten konnte, in seiner Sprache.

    Der eigentliche Grund fuer diese Funktion (Luka, 27.07.): wir haben behauptet
    "no business description on the profile", ohne das Feld zuverlaessig gezogen zu haben.
    Die ehrliche Fassung ist nicht, den Punkt wegzulassen, sondern ihn zu benennen als
    das, was er ist -- ungeprueft. Damit wird aus einer Schwaeche der beste Grund zu
    antworten: hier ist, was ich von aussen sehen konnte, und hier ist, was ich nicht
    sehen konnte. Der Report schliesst genau diese Luecke.
    """
    missing = [c for c in weights if c not in measured and c in LABELS]
    return [LABELS[c] for c in missing[:cap]]


def limits_line(items: list) -> str:
    """Die Zeile fuer die Mail. Ohne offene Punkte gibt es sie nicht."""
    if not items:
        return ""
    if len(items) == 1:
        tail = items[0]
    else:
        tail = ", ".join(items[:-1]) + " or " + items[-1]
    # Der Punkt gehoert hierhin, nicht in die Vorlage: dort stuende er auch dann da, wenn
    # die Zeile leer bleibt, und ein Satzzeichen ohne Satz ist genau der Serienbrief-Tell.
    return f"what i could not see from outside is {tail}."


# Befunde, die zwar stimmen, aber keinen Auftrag benennen. Ein Betrieb, dem nur noch
# diese bleiben, ist nicht schlecht aufgestellt -- wir sehen bloss nicht tief genug.
TECHNICAL = {"web-schema", "web-meta-og", "web-lang", "web-map-embed",
             "web-word-readability", "gbp-photos", "gbp-posts"}


def needs_deeper(findings: list) -> bool:
    """Bleibt nur Technik uebrig, ist die Mail austauschbar -- dann lieber tiefer ziehen.

    Gemessen in Bedford: die zwei bestaufgestellten Betriebe bekamen WORTGLEICH dieselben
    zwei Luecken ("kein Formular", "kein LocalBusiness-Markup"). Beides stimmt, beides
    benennt keinen verlorenen Auftrag, und beide Mails lasen sich identisch -- ausgerechnet
    an die besten Interessenten der Kohorte (Luka, 27.07.: "dann muessten wir auch auf
    DataForSEO und mehr SEO-Findings gehen, damit wir die Gap-Story haben").

    Wer hier True bekommt, gehoert NICHT in den Standardversand, sondern in einen
    Ranking-Zug. Das sind wenige, und es sind die, bei denen sich die Kosten lohnen.
    """
    gaps = [f for f in findings if f["kind"] == "gap"]
    if not gaps:
        return True
    if all(f["check"] in TECHNICAL or f["strength"] < 70 for f in gaps):
        return True

    # ZWEITER Grund, tiefer zu ziehen (Luka, 27.07.): zu wenig, womit er VORNE liegt.
    # Gold Key Locks besteht 13 Faktoren und genau EINER davon traegt einen Vergleich --
    # die anderen zwoelf sind "in Ordnung, nichts zu erzaehlen". Die Abwesenheit eines
    # Problems ist keine Staerke, und eine Mail mit einem Lob gegen drei Maengel liest sich
    # wie eine Abrechnung. Der Maps-Rang aus DataForSEO existiert fuer JEDEN Betrieb und
    # ist immer vergleichend: steht er in den ersten drei, ist das ein starkes Lob, steht
    # er weiter hinten, eine starke Luecke. Beides besser als ein duenner Absatz.
    return len([f for f in findings
                if f["kind"] == "good" and (f.get("fact") or "").strip()]) < 2


def placing(pts, all_pts: list) -> str:
    """Wo dieser Score in der Kohorte steht, als Satzteil. Leer, wenn zu wenige da sind.

    Der Anlass (Luka, 27.07.): "wir erwaehnen immer noch nichts Allgemeines zum GBP -- eine
    allgemeine Einschaetzung basierend auf unseren Daten." Genau das fehlte: die 58 stand da
    und er konnte nichts damit anfangen. 58 ist nicht gut oder schlecht, 58 ist SIEBTER VON
    ELF -- und diese Einordnung bekommt er nirgends sonst, weil niemand ausser uns alle elf
    Profile derselben Stadt nebeneinander bewertet hat.

    Bewusst grob: bei Gleichstand gilt die bessere Platzierung, denn zwei Betriebe mit 58
    sind gleich gut aufgestellt, und einen davon nach hinten zu sortieren waere erfunden.
    """
    vals = sorted([p for p in all_pts if p is not None], reverse=True)
    if pts is None or len(vals) < 4:
        return ""
    rank = vals.index(pts) + 1
    n = len(vals)
    if rank == 1:
        return "the best of the {n} we looked at".format(n=n)
    if rank <= 3:
        return f"{_ORD.get(rank, str(rank))} best of the {n} we looked at"
    if rank > n - 2:
        return f"the lowest of the {n} we looked at" if rank == n else \
               f"second from the bottom of the {n} we looked at"
    return f"{rank}th of the {n} we looked at"


_ORD = {1: "first", 2: "second", 3: "third"}


def summary(gbp_pts, site_pts, n_gbp=0, n_site=0, gbp_place="", site_place="") -> str:
    """Die Zeile fuer die Mail. Was fehlt, wird nicht behauptet.

    Die Faktorenzahl steht bewusst dabei. "62 von 100" allein ist eine Behauptung, die
    jeder aufstellen kann; "62 von 100 ueber 7 Faktoren" ist eine Rechnung, nach der man
    fragen kann -- und genau diese Rueckfrage ist das Ziel der Mail. Sie sagt ausserdem
    ohne Umschweife, dass wir von aussen gemessen haben. Wer spaeter den Report bekommt,
    findet dort mehr Faktoren und eine andere Zahl, und faellt nicht aus allen Wolken.
    """
    def _tail(place):
        return f", {place}" if place else ""

    parts = []
    if gbp_pts is not None:
        # Eine glatte 100 als Zahl zu schicken arbeitet gegen die Mail: sie sagt "hier ist
        # nichts zu tun", und zwar auf Basis von fuenf Punkten, die wir von aussen sehen
        # konnten. Als Satz gesagt ist dieselbe Wahrheit ein Lob, das die schmale Grundlage
        # gleich mitliefert -- und die Grenzen-Zeile zwei Absaetze spaeter greift sauber an.
        parts.append((f"your google profile is clean on all {n_gbp} things i could check "
                      f"from outside" if gbp_pts == 100 else
                      f"your google profile scores {gbp_pts} out of 100 "
                      f"across the {n_gbp} things visible from outside") + _tail(gbp_place))
    if site_pts is not None:
        parts.append(f"your site "
                     f"{'is clean across all' if site_pts == 100 else str(site_pts) + ' across'} "
                     f"{n_site}" + _tail(site_place))
    # Der Punkt gehoert an den Satz, nicht in die Vorlage -- derselbe Grund wie bei
    # limits_line: ein Lead ohne messbaren Score (Jims Auto Keys, 28.07.) bekam sonst
    # "i'm a freelancer doing local marketing. . what i could not see ...".
    return (", and ".join(parts) + ".") if parts else ""


def self_check():
    fs = [{"check": "gbp-hours", "kind": "gap"}, {"check": "gbp-photos", "kind": "good"}]
    # gbp-description gehoert NICHT mehr dazu -- nie gemessen, siehe measured_gbp
    m = {"gbp-hours", "gbp-photos", "gbp-claimed", "gbp-posts", "gbp-services"}
    tot = sum(GBP_WEIGHTS[c] for c in m)
    pts, costly = score(fs, m, GBP_WEIGHTS)
    assert pts == round((tot - GBP_WEIGHTS["gbp-hours"]) * 100 / tot), pts
    assert costly == ["gbp-hours"], costly
    # ein Check ohne Daten kostet NICHTS -- weder Zaehler noch Nenner. fs traegt eine
    # gbp-hours-Luecke, aber gbp-hours ist hier NICHT gemessen, also bleibt der Score bei 100.
    assert score(fs, {"gbp-photos", "gbp-claimed", "gbp-services",
                      "gbp-posts", "gbp-secondary-categories"}, GBP_WEIGHTS)[0] == 100
    # gar nichts gemessen heisst kein Score, nicht null
    assert score(fs, set(), GBP_WEIGHTS) == (None, [])
    # und ein einzelner Faktor ergibt keine 100 -- er ergibt keine Zahl
    assert score([], {"web-own-site"}, SITE_WEIGHTS) == (None, [])
    assert score([], {"web-own-site", "web-title", "web-schema"}, SITE_WEIGHTS) == (None, [])
    assert score([], set(SITE_WEIGHTS), SITE_WEIGHTS)[0] == 100
    # eine glatte 100 wird als Satz gesagt, nicht als Zahl geschickt
    assert "clean on all 7" in summary(100, None, 7), summary(100, None, 7)
    assert summary(100, None, 7).endswith("."), "der Satz traegt seinen Punkt selbst"
    assert summary(None, None) == "", "kein Score, kein Satzzeichen"

    # Die Einordnung in der Kohorte -- die Zahl allein sagt ihm nichts
    pool = [90, 75, 58, 58, 40, 30]
    assert placing(90, pool).startswith("the best"), placing(90, pool)
    assert placing(75, pool).startswith("second best"), placing(75, pool)
    assert placing(30, pool).startswith("the lowest"), placing(30, pool)
    # unter vier Betrieben ist eine Platzierung bedeutungslos
    assert placing(58, [58, 40, 30]) == ""
    assert placing(None, pool) == ""
    assert "the best of the 6" in summary(90, None, 7, 0, placing(90, pool))

    # ein Betrieb, dem nur Technik bleibt, gehoert in den tieferen Zug statt in den Versand
    g = lambda c, st: {"check": c, "kind": "gap", "strength": st}
    assert needs_deeper([g("web-schema", 86), g("web-meta-og", 58)])
    # Echte Luecke UND genug Vergleichbares auf der Lob-Seite -> normaler Versand.
    # Die zweite Bedingung ist neu: ohne sie fiel diese Zusicherung, weil hier gar kein
    # Lob stand -- und genau das soll jetzt den tieferen Zug ausloesen.
    _gut = lambda f: {"check": "gbp-photos", "kind": "good", "strength": 55, "fact": f}
    assert not needs_deeper([g("gbp-hours", 88), g("web-schema", 86),
                             _gut("40 fotos gegen 6"), _gut("zweiter in der stadt")])
    assert needs_deeper([]), "gar keine Luecke heisst erst recht tiefer ziehen"
    # Zu wenig Vergleichbares auf der Lob-Seite ist der zweite Grund, tiefer zu ziehen
    gd = lambda fact: {"check": "gbp-photos", "kind": "good", "strength": 55, "fact": fact}
    echte_luecke = [g("gbp-hours", 88)]
    assert needs_deeper(echte_luecke + [gd("40 fotos gegen 6")]), "ein Vergleich reicht nicht"
    assert not needs_deeper(echte_luecke + [gd("40 fotos gegen 6"), gd("zweiter in der stadt")])
    # Ein bestandener Faktor OHNE Beleg zaehlt nicht als Staerke
    assert needs_deeper(echte_luecke + [gd("40 fotos gegen 6"), gd("")])
    # ohne Detailseite sind Oeffnungszeiten und Beitraege unbekannt
    assert "gbp-hours" not in measured_gbp({"title": "x"})
    assert "gbp-hours" in measured_gbp({"openingHours": [{"day": "Mon"}]})
    # Oeffnungszeiten allein sind KEIN Beleg fuer die Detailseite -- sie kommen von der Liste
    # Die Profil-Beschreibung ist NIE gemessen: das Apify-Feld traegt Googles Markentext,
    # nicht den des Inhabers. Sie gehoert deshalb in keinen Nenner, sondern in die Grenzen.
    assert "gbp-description" not in measured_gbp({"reviewsTags": [{"title": "x"}]})
    assert "gbp-description" not in GBP_WEIGHTS
    # Detailseite geholt, Zeiten trotzdem leer -> gemessen, nicht ungeprueft
    assert "gbp-hours" in measured_gbp({"reviewsTags": [{"title": "x"}]})
    # ohne HTML ist an der Website nur die Eigentumsfrage beantwortet
    assert measured_site("", "http://x.de") == {"web-own-site"}
    assert measured_site("", "") == set()
    assert summary(None, None) == ""
    assert summary(62, None, 7) == \
        "your google profile scores 62 out of 100 across the 7 things visible from outside."
    # beide Zahlen tragen ihre Faktorenzahl, sonst ist es eine Behauptung statt einer Rechnung
    assert "across 5" in summary(62, 40, 7, 5)

    # Was nicht gemessen wurde, kommt in die Grenzen-Zeile -- in seiner Sprache, nicht unserer
    lim = limits({"gbp-claimed", "gbp-photos"}, GBP_WEIGHTS)
    # Die Profil-Beschreibung steht nicht mehr im Katalog, also auch nicht in den Grenzen --
    # sie ist gar kein Faktor mehr, sondern etwas, das wir nie erheben konnten.
    assert "whether google shows you as open at night" in lim, lim
    assert all("gbp-" not in x for x in lim), "keine Check-IDs in der Mail"
    assert limits_line([]) == "", "ohne offene Punkte keine Zeile"
    assert limits_line(["a"]) == "what i could not see from outside is a."
    assert limits_line(["a", "b"]).endswith("is a or b.")
    # alles gemessen -> nichts zu sagen
    assert limits(set(GBP_WEIGHTS), GBP_WEIGHTS) == []
    print("self-check ok")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        self_check()
    else:
        print(__doc__)
