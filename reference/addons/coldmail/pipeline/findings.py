#!/usr/bin/env python3
"""findings.py — the audit library for the `markt` cold email.

The split (Luka, 2026-07-25): **Python decides what is true and what it means. The model only
writes it together.** This file is the "what is true and what it means" half. Every fact, every
number and every comparison is computed here; the generator receives finished statements and may
not add to them.

Each finding carries:
  fact         what we measured, in plain words, numbers already filled in
  means        the consequence in the owner's language, never ours ("google has less to match
               you on", not "weak entity signals")
  strength     0-100, ranks which three make it into the mail
  kind         'good' | 'gap'
  check        the matching `lead-magnet/audit.py` check id, so the mail and the report can never
               contradict each other. IDs are shared on purpose; the data sources still differ
               (this reads the Apify place object, audit.py reads DataForSEO) until the adapter
               exists. Same id = same claim, that is what keeps them aligned.

Usage:
  python3 findings.py --file <apify-dataset.json>       # print findings per place
  python3 findings.py --self-check                      # run the built-in assertions
"""
import json, argparse, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import benchmark  # noqa: E402

# --- strength -------------------------------------------------------------------------------
# Not "how broken is it" but "how much does naming it earn a reply". Two things pull against
# each other: a gap that fires on almost every lead is real but says nothing about THIS business,
# and a mail that always leads with the same line reads like a template by the tenth recipient.
# So universal gaps are capped below differentiating ones even when they matter more technically.
UNIVERSAL_PENALTY = 25   # applied to findings that fire on >90% of the niche


def _n(v):
    try:
        return int(float(v or 0))
    except (TypeError, ValueError):
        return 0


def evaluate(p, market=None, bench=None, niche=""):
    """Apify place object (+ optional market context) -> list of findings, strongest first.

    `market` is the scraped peer set for the same area: {'count': int, 'reviews_rank': int,
    'reviews_leader': str}. Without it, every comparative finding is skipped rather than guessed
    (rule 8 of markt_copy.md: an ungated comparison is automated reputational damage)."""
    out = []
    cats = p.get("categories") or []
    tags = [t.get("title") for t in (p.get("reviewsTags") or []) if t.get("title")]
    reviews, rating = _n(p.get("reviewsCount")), p.get("totalScore")
    # Google zeigt 5.0, nicht 5. "176 reviews at 5" liest sich wie ein Tippfehler
    # in einer Mail, die dem Empfaenger gerade seine eigenen Zahlen vorhaelt.
    if rating is not None:
        rating = f"{float(rating):.1f}"
    photos, posts = _n(p.get("imagesCount")), len(p.get("ownerUpdates") or [])
    # Ob die Detailseite geholt wurde, entscheidet ueber JEDEN Befund, der ein Detailfeld
    # liest. Ohne sie ist das Feld nicht leer, sondern unbekannt.
    # openingHours gehoert NICHT in diese Liste: das Feld kam bei allen 24 Bedford-Places
    # vor, also auch ohne Detailseite. Als Indikator war es damit immer wahr, und der
    # Riegel liess genau die Behauptung durch, die er verhindern sollte.
    _detail_fetched = any(p.get(k) for k in ("ownerUpdates", "imageUrls", "reviewsTags",
                                             "peopleAlsoSearch", "additionalInfo"))

    def add(check, kind, fact, means, strength):
        out.append({"check": check, "kind": kind, "fact": fact, "means": means,
                    "strength": strength})

    # --- what's working -----------------------------------------------------------------------
    # KEIN Befund mehr ueber die Sternezahl. Gemessen an 4.746 britischen Schluesseldiensten
    # liegt der MEDIAN bei 5,0 -- wer 4,9 hat, liegt unter dem Mittelwert. "176 reviews at 4.9"
    # als Lob zu verkaufen heisst, ihm etwas als Staerke zu verkaufen, das jeder hat.
    # Unterschieden wird ueber die MENGE, und die Einordnung dazu bekommt er nirgends sonst.
    _band, _where = benchmark.standing(reviews, bench or {})
    if market and market.get("reviews_rank") and reviews:
        rank = market["reviews_rank"]
        if rank == 1 and _where:
            add("gbp-reviews-volume", "good",
                f"{reviews} reviews puts you in {_where} and first in town", "", 95)
        elif rank == 1:
            add("gbp-reviews-volume", "good", f"{reviews} reviews, the most in town",
                "nobody local out-reviews you", 90)
        elif rank <= 3 and _where:
            add("gbp-reviews-volume", "good",
                f"{reviews} reviews puts you in {_where}, and {_ordinal(rank)} in town", "", 92)
        elif rank <= 3:
            add("gbp-reviews-volume", "good", f"{reviews} reviews, {_ordinal(rank)} in town",
                "the reputation is already there", 85)
    elif _where:
        # Auch ohne Kohorte traegt der Landesvergleich -- er ist die Zahl, die er nirgends
        # nachsehen kann, und der Beleg dafuer, dass hier wirklich jemand gerechnet hat.
        add("gbp-reviews-volume", "good", f"{reviews} reviews puts you in {_where}",
            f"the median sits at {(bench or {}).get('reviews', {}).get('median', 0)}", 88)

    if posts:
        # "six in ten" stand hier bis 27.07. als getippte Zahl in einem Satz, der an den
        # Inhaber geht. Gemessen sind es 66% von 994 -- die Zahl stimmte zufaellig, waere
        # aber bei der naechsten Nische still falsch gewesen.
        # Gemessen am 27.07.: dieser Satz war der haeufigste in der ganzen Kampagne, er
        # stand woertlich gleich in 36% aller Mails. Grund war, dass der Lob-Zweig die
        # LANDESzahl nahm, waehrend der Luecken-Zweig direkt darunter die Stadt-Zahl hat.
        # Ein Lob ohne Vergleich sagt nur, was der Inhaber ohnehin weiss.
        _mkt = (market or {}).get("with_posts", 0)
        _n_t = (market or {}).get("count", 0)
        _nie = (bench or {}).get("posts", {}).get("never_pct")
        if _mkt and _n_t and _mkt < _n_t:
            add("gbp-posts", "good", f"you post, where only {_mkt} of the {_n_t} in town do",
                "the profile looks tended and most here look parked", 75)
        else:
            add("gbp-posts", "good", "you post on your profile",
                f"you are ahead of the {_in_ten(_nie)} who never bother" if _nie
                else "most profiles round here never move", 75)
    elif _detail_fetched:
        # Der fehlende Gegenzweig war ein echter Rechenfehler (Luka, 27.07.: "sind wir
        # sicher, dass die Python-Logik richtig funktioniert"). gbp-posts konnte NUR als
        # Lob feuern. Wer nie postete, erzeugte gar keinen Befund -- und ein Check ohne
        # Befund gilt im Score als bestanden. Gold Key postet null Mal und bekam dafuer
        # vier Punkte geschenkt. Nicht gefeuert ist nicht dasselbe wie in Ordnung.
        _mktposts = (market or {}).get("with_posts", 0)
        _n_town = (market or {}).get("count", 0)
        if _mktposts and _n_town:
            add("gbp-posts", "gap",
                f"your profile has no posts, where {_mktposts} of the {_n_town} in town do",
                "theirs looks tended and yours looks parked", 45)
        else:
            add("gbp-posts", "gap", "you have never posted on your profile",
                "google treats a profile that never moves as one nobody tends", 40)
    # Rund-um-die-Uhr ist bei einem Schluesseldienst das Verkaufsargument. Der Mangel wiegt
    # schwerer als das Lob: wer es NICHT zeigt, verliert den Auftrag um zwei Uhr nachts an
    # den, der es zeigt. Nur bewerten, wenn die Detailseite geholt wurde -- ohne sie ist das
    # Feld bei JEDEM leer und wir wuerfen es jedem vor.
    _hours = p.get("openingHours") or []
    _open24 = any("24" in str(d.get("hours", "")) for d in _hours)
    _mkt24 = (market or {}).get("with_24h", 0)
    # Der Vergleich gehoert in den FAKT, die Folge ins means. Andersherum entstand
    # "does not show 24 hours, so 8 locksmiths in town do, so the 2am call goes to them" --
    # zwei "so" in einem Satz, weil bullet() den Verbinder ohnehin setzt.
    if _hours and not _open24 and _mkt24 >= 2:
        add("gbp-hours", "gap", f"your profile does not show 24 hours, where {_mkt24} in town do",
            "the 2am call goes to one of them", 88)
    elif _open24 and _mkt24 and _mkt24 <= (market or {}).get("count", 99) // 2:
        add("gbp-hours", "good",
            f"your profile shows 24 hours, which only {_mkt24} of the {market['count']} in town do",
            "that is the job nobody shops around for", 80)

    # "34 photos on the profile" allein ist keine Nachricht -- seine eigene Zahl kennt er.
    # Erst der Median der Kohorte macht daraus etwas, das er selbst nicht nachsehen kann.
    _pmed = (market or {}).get("photos_median", 0)
    _prank = (market or {}).get("photos_rank")
    if photos >= 20 and _prank == 1:
        add("gbp-photos", "good", f"{photos} photos, more than any other {p.get('_niche', 'firm')} in town"
            .replace(" _niche ", " firm "),
            "yours is the listing people scroll before they call", 60)
    elif photos >= 20 and _prank and _pmed and photos >= _pmed * 2:
        # Der Rang steht im Fakt, damit niemand aus "ueber dem Median" ein "ueber allen" macht
        add("gbp-photos", "good",
            f"{photos} photos, {_ordinal(_prank)} most in town against a middle of {_pmed}",
            "you look like the established one before anyone reads a word", 55)
    elif photos >= 20 and _pmed and photos >= _pmed * 2:
        add("gbp-photos", "good",
            f"{photos} photos on the profile against a middle of the pack at {_pmed}",
            "you look like the established one before anyone reads a word", 55)
    elif photos >= 20:
        add("gbp-photos", "good", f"{photos} photos on the profile",
            "you look established next to a pack that manages a handful", 45)
    if len(cats) >= 3:
        # Zweithaeufigster Satz der Kampagne (17% woertlich gleich), aus demselben Grund
        # wie oben: eine Zahl ohne Bezug. Wieviele Kategorien der typische Betrieb hier
        # gesetzt hat, kann der Inhaber nirgends nachsehen -- genau deshalb traegt es.
        _cm = (market or {}).get("cats_median", 0)
        add("gbp-secondary-categories", "good",
            f"{len(cats)} categories set, where the typical listing here has {_cm}"
            if _cm and len(cats) > _cm else f"{len(cats)} categories set",
            "google has more than one way to find you", 45)

    # --- what could be improved ---------------------------------------------------------------
    # The single strongest line we have: their own customers' words against their own profile.
    # Only fires when reviewsTags exist AND none of them appear in a category, which is the part
    # that makes it specific to this business instead of true of everyone.
    if tags:
        # Nur EINTRAGBARE Leistungen. Google nimmt in der Leistungs-Sektion Taetigkeiten,
        # keine Eigenschaften -- "response time", "polite staff" und "value for money"
        # kann niemand hinterlegen. Der Befund forderte bis 27.07. genau dazu auf
        # (Luka: "response time comes up 3 times in your reviews but not on the profile
        # finde ich auch schwer verstaendlich"), und gemessen ueber alle Leads sind
        # 35% aller Bewertungs-Themen von dieser Art: 6.529 von 18.438 Vorkommen.
        catblob = " ".join(cats).lower()
        # Positiv UND negativ. "kindness" kam am 27.07. in eine fertige Mail, weil hier
        # nur die schwarze Liste lief -- der Gewerks-Filter steckte allein im Pool. Ein
        # Filter, der an zwei Stellen gebraucht wird und nur an einer steht, ist keiner.
        tags = [t for t in tags
                if not _ist_eigenschaft(t) and _leistung(t, niche)
                # Ein Thema mit Komma zerfasert den Satz: "safe lock install, open and
                # repair" las sich in einer Mail wie zwei abgebrochene Halbsaetze.
                and "," not in t]
        unmatched = [t for t in tags[:6] if t.lower() not in catblob
                     and not any(w in catblob for w in t.lower().split() if len(w) > 4)]
        if len(unmatched) >= 2:
            add("gbp-services", "gap",
                f"your reviews keep saying {unmatched[0]} and {unmatched[1]}, "
                f"but your profile mentions neither",
                "those searches go to someone else", 95)

    # KEIN Befund ueber die Profil-Beschreibung. Wir haben sie NIE gemessen (Luka, 27.07.:
    # "wieso erwaehnen wir die business description, wir scrapen die doch gar nicht").
    # Beleg: von 21 Bedford-Places mit Detailseite tragen genau sieben eine `description`,
    # und alle sieben sind Timpson-Filialen mit demselben Text "Chain of locksmiths, also
    # offering other services". Das ist Googles redaktioneller Markentext, nicht die vom
    # Inhaber geschriebene Beschreibung -- das Apify-Feld heisst nur so.
    #
    # Meine erste Erklaerung ("die fehlt wirklich, das war keine Scrape-Luecke") war falsch:
    # ich habe aus "8 von 25 haben eine" geschlossen, dass die anderen keine schreiben,
    # statt zu pruefen WELCHE acht. Ein Substring-Treffer ist kein Beleg.
    #
    # Der Punkt ist damit nicht verloren, er wandert in die Grenzen-Zeile und wird dort zum
    # Grund fuer den Report. Zurueck kommt er, wenn eine Quelle das echte Feld liefert
    # (DataForSEO my_business_info fuehrt es).

    # KEIN Booking-Link-Befund fuer Schluesseldienste. Er feuerte bei 7 von 15 und war damit
    # der haeufigste Mangel der Kohorte -- aber ein Notdienst WILL, dass das Telefon klingelt.
    # Um zwei Uhr nachts bucht niemand einen Termin. Der Befund stammt aus einer Termin-Branche
    # und tadelte hier etwas, das richtig ist. Fuer Branchen mit echter Terminbuchung
    # (Salon, Praxis, Studio) gehoert er zurueck, dann ueber eine Branchenliste.
    # "one category only, so you show up for one kind of search" war zu abstrakt (Luka, 27.07.):
    # der Inhaber weiss nicht, was eine Kategorie tut, und sieht keinen verlorenen Auftrag.
    # Mit der Kohorte nennen wir die Kategorien, die die Meistbewerteten fuehren und er nicht --
    # aus einer Einstellung wird ein Auftrag, der woanders hingeht.
    missing = [c for c, k in sorted((market or {}).get("leader_cats", {}).items(),
                                    key=lambda x: -x[1])
               if k >= 2 and c not in cats and c.lower() != "service establishment"][:2]
    if len(cats) <= 1 and missing:
        add("gbp-secondary-categories", "gap",
            f"your profile is set to {cats[0].lower()} only, where the most-reviewed firms in "
            f"town are also listed as {' and '.join(m.lower() for m in missing)}",
            "those searches never reach you", 85)
    elif len(cats) <= 1:
        add("gbp-secondary-categories", "gap", "one category only",
            "you show up for one kind of search", 70)
    if photos < 5:
        add("gbp-photos", "gap", f"{photos} photo{'' if photos == 1 else 's'} on the profile",
            "the listing looks thin next to the others", 50)
    # Opening hours live on the place DETAIL page, which the bulk scrape only fetches with
    # `--details on` (scrape.py defaults it OFF for cost). Without that flag the field is
    # empty for EVERY place, and an unguarded check would tell every single recipient their
    # hours are missing -- a false claim in the first line they read from us, at 65 strength
    # so it lands in the top three. Only judge it when the detail page was actually fetched;
    # the other detail-only fields are the tell. Same rule as audit.py's v_posts_cadence:
    # not fetched is not the same as not there.
    if _detail_fetched and not p.get("openingHours"):
        add("gbp-hours", "gap", "no opening hours set",
            "people can't tell if you're reachable now", 65)
    if p.get("claimThisBusiness"):
        add("gbp-claimed", "gap", "the profile isn't claimed",
            "anyone could edit it before you do", 95)
    _med = (bench or {}).get("reviews", {}).get("median", 0)
    if reviews and _med and reviews < _med:
        # Der Vergleich macht aus "wenig Bewertungen" eine Zahl, die er einordnen kann.
        # Und er ist der einzige Weg, ihm zu sagen, dass seine 5,0 Sterne nichts wert sind,
        # ohne ihn anzugreifen: nicht die Note ist das Problem, die Menge ist es.
        add("gbp-reviews-volume", "gap",
            f"{reviews} reviews against a uk median of {_med}",
            "your rating is not what holds you back, the count is", 72)
    elif reviews and reviews < 10:
        add("gbp-reviews-volume", "gap", f"only {reviews} reviews",
            "the ones above you have more to show", 60)

    # --- nur mit --details on -------------------------------------------------------------------
    # Die folgenden Felder liefert die Detailseite. Sie fehlen im Kurz-Scrape, und ohne sie
    # feuert nichts davon -- nicht gemessen ist nie ein Befund. Kuenftige Laeufe holen sie,
    # deshalb sind sie hier ausgebaut und nicht als Idee vertagt.
    dist = p.get("reviewsDistribution") or {}
    ones = _n(dist.get("oneStar"))
    if ones >= 3 and reviews:
        # Bei einem Notdienst entscheidet der Kunde in Panik. Er sortiert nach der
        # schlechtesten Bewertung, weil er wissen will, wie schlimm es werden kann.
        add("gbp-reviews-quality", "gap",
            f"{ones} one-star review{'' if ones == 1 else 's'} sit on the profile",
            "whoever sorts by lowest sees those first, and at 2am nobody reads the good ones", 84)

    pas = [x.get("title") for x in (p.get("peopleAlsoSearch") or []) if x.get("title")][:2]
    if len(pas) == 2:
        # Google sagt uns woertlich, neben wen es ihn stellt. Das kann er nirgends abfragen,
        # und es beantwortet die Frage, die er sich stellt: gegen wen laufe ich eigentlich.
        add("gbp-also-searched", "gap",
            f"google shows {_short(pas[0])} and {_short(pas[1])} right under your profile",
            "that is who people compare you with before they call anyone", 78)

    return sorted(out, key=lambda f: -f["strength"])


_WORDS = {1: "one", 2: "both", 3: "three", 4: "four", 5: "five", 6: "six",
          7: "seven", 8: "eight", 9: "nine"}


def _word(n):
    """Kleine Zahlen als Wort. "1 of the firms above you" liest sich wie ein Datenbankfeld,
    "one of the firms above you" wie ein Satz. Ab zehn bleibt die Ziffer, weil sie dann
    schneller erfassbar ist als das Wort."""
    return _WORDS.get(n, str(n))


def _short(name):
    """Firmenname fuer den Fliesstext. "Gemini Lock & Safe Bedford Locksmith" mitten in
    einer sonst kleingeschriebenen Mail liest sich wie ein Datenbank-Auszug -- dieselbe
    Regel 7 aus markt_copy.md, die fuer den Empfaenger selbst schon gilt."""
    import casualize
    return (casualize.casual_brand(name, "", "") or name).lower()


def _leistung(thema, niche):
    """Nennt das Thema ein Ding des Gewerks? Ohne trades (oder ohne bekannte Nische)
    wird nicht gefiltert -- lieber ein schwacher Stichpunkt als gar keiner."""
    try:
        from trades import ist_leistung
    except ImportError:
        return True
    return ist_leistung(thema, niche)


def _ordinal(n):
    return {1: "first", 2: "second", 3: "third"}.get(n, f"{n}th")


# Woran ein Bewertungs-Thema eine EIGENSCHAFT ist statt einer Leistung. Eine Eigenschaft
# beschreibt, WIE er arbeitet; eine Leistung, WAS er macht. Nur Letzteres laesst sich in
# der Leistungs-Sektion des Profils hinterlegen -- ihn zum Ersten aufzufordern ist eine
# Aufgabe, die es nicht gibt.
#
# Die Liste ist bewusst grosszuegig: ein faelschlich verworfenes Thema kostet einen
# Stichpunkt, ein faelschlich empfohlenes kostet Glaubwuerdigkeit.
_EIGENSCHAFT = (
    "time", "price", "pricing", "cost", "charge", "quick", "fast", "prompt", "speed",
    "polite", "friendly", "reliab", "professional", "efficien", "helpful", "courteous",
    "value", "quality", "tidy", "clean", "communication", "response", "attitude",
    "honest", "punctual", "knowledge", "experience", "recommend", "trust", "care",
    # Woerter, die kein Objekt benennen: "quick work", "the job", "great staff"
    "job", "work", "staff", "service quality", "guy", "man ", "team", "lady", "chap",
    # aus dem Pool-Lauf am 27.07.: "great finish", "packaging" landeten als
    # angeblich eintragbare Leistungen in der Auswahl
    "finish", "great", "good", "nice", "packaging", "arrival", "turnaround",
    # 27.07., vierter Nachtrag: "advice", "company", "attention" landeten als
    # angeblich eintragbare Leistungen in einer fertigen Mail. Kein Inhaber kann
    # "advice" unter Leistungen eintragen.
    "advice", "company", "attention", "manner", "approach", "solution", "support",
)


def _ist_eigenschaft(thema: str) -> bool:
    t = (thema or "").lower().strip()
    return any(w in t for w in _EIGENSCHAFT)


_ZEHNTEL = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
            6: "six", 7: "seven", 8: "eight", 9: "nine"}


def _in_ten(pct):
    """Ein gemessener Anteil als gesprochener Satzteil.

    Abgerundet, nie auf. Der Satz behauptet, wie viele es SCHLECHTER machen -- da ist
    Untertreiben die Fassung, die einer Rueckfrage standhaelt.
    """
    z = int(pct) // 10
    if z >= 9:
        return "nearly everyone else"
    if z <= 1:
        return "the few"
    return f"{_ZEHNTEL[z]} in ten"


def select(findings, n_good=2, n_gap=3):
    """The three that go in the mail, plus the good ones. Falls back cleanly: fewer than two
    positives (25% of leads, measured) means the mail drops the 'what's working well' block
    rather than inventing praise."""
    good = [f for f in findings if f["kind"] == "good"][:n_good]
    gaps = [f for f in findings if f["kind"] == "gap"][:n_gap]
    return {"good": good if len(good) >= 2 else [], "gaps": gaps}


def _self_check():
    strong = {"title": "X", "categories": ["Locksmith", "Emergency locksmith service", "Key duplication"],
              "reviewsCount": 134, "totalScore": 4.9, "imagesCount": 43,
              "ownerUpdates": [{}], "description": "", "bookingLinks": [], "openingHours": [{}],
              "reviewsTags": [{"title": "car key replacement"}, {"title": "key coding"}]}
    f = evaluate(strong, market={"reviews_rank": 2})
    facts = " | ".join(x["fact"] for x in f)
    assert any(x["check"] == "gbp-services" for x in f), f"reviewsTags gap missed: {facts}"
    assert f[0]["strength"] >= f[-1]["strength"], "not sorted by strength"
    assert any("second in town" in x["fact"] for x in f), f"rank line missing: {facts}"

    # no market context -> no comparative claim may appear (rule 8)
    f2 = evaluate(strong)
    assert not any("in town" in x["fact"] for x in f2), "comparative claim leaked without market data"

    # thin lead -> fewer than two positives -> the good block is dropped, never padded
    thin = {"categories": ["Locksmith"], "reviewsCount": 3, "totalScore": 4.0, "imagesCount": 1,
            "ownerUpdates": [], "description": "", "bookingLinks": [], "openingHours": []}
    sel = select(evaluate(thin))
    assert sel["good"] == [], f"invented praise for a thin lead: {sel['good']}"
    assert len(sel["gaps"]) == 3, f"expected 3 gaps, got {len(sel['gaps'])}"

    # a filled description must not produce the description gap
    ok = dict(strong, description="We fix locks across Bedford.")
    assert not any(x["check"] == "gbp-description" for x in evaluate(ok)), "false description gap"
    print("self-check ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="Apify dataset JSON (list of place objects)")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        _self_check(); sys.exit(0)
    if not a.file:
        sys.exit("need --file or --self-check")
    for p in json.load(open(a.file)):
        sel = select(evaluate(p))
        print(f"\n=== {p.get('title')}")
        for f in sel["good"]:
            print(f"  [+{f['strength']:3}] {f['fact']} -> {f['means']}")
        for f in sel["gaps"]:
            print(f"  [-{f['strength']:3}] {f['fact']} -> {f['means']}")
