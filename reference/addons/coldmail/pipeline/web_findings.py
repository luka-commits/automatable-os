#!/usr/bin/env python3
"""web_findings.py — the website half of the `markt` cold email.

Companion to findings.py, same contract: **Python decides what is true and what it
means, the model only writes it together.** Not one line here is a judgement call the
model gets to make, because a wrong website claim goes to a stranger who can check it
in five seconds.

Why this exists: findings.py reads the Apify place object, so every finding it can
produce is a Google-profile finding. Three findings that all come from the profile read
as one theme; the mail is meant to sound like we looked at the business, not at one
listing. The website is the second theme, and it costs one HTTP request because the
scrape already hands us the URL.

TWO TIERS, on purpose:
  evaluate(html, ctx)              one homepage fetch -> conversion / copy / trust
  evaluate(html, ctx, pages=[...]) + the full crawl -> structure (report leads only)

STRENGTH is not "how broken is it" but "how much does naming it earn a reply", the same
rule findings.py uses. Rates below are MEASURED across the 22 leads that have a stored
homepage, not guessed, because a gap that fires on everyone is true and still says
nothing about THIS business:

    no embedded map      95%   dropped, universal and nobody cares
    no FAQ schema        77%   dropped, same
    no AggregateRating   86%   kept but capped, the consequence is concrete
    no LocalBusiness     55%
    no tap-to-call       41%
    H1 without city      36%
    title without service 32%
    thin main text       32%
    copy flags           27%
    title without city   23%
    no viewport           0%   dropped, fires on nobody

The copy findings QUOTE the lead's own words back. That is deliberate: a sentence they
wrote themselves cannot read as a template, and it makes the claim self-evidencing.

Usage:
  python3 web_findings.py --url https://example.com      # fetch + print findings
  python3 web_findings.py --self-check                   # assertions, no network
"""
from __future__ import annotations
import argparse, html as _html, json, re, sys, urllib.request

# Platitude openers: an H1 that could sit on any competitor's site. Kept deliberately
# short and literal -- a fuzzy "is this generic" score would be a judgement call, and a
# wrong one insults someone about text they wrote themselves.
PLATITUDE = re.compile(
    r"\b(welcome to|your trusted|quality you can trust|professional service|"
    r"we provide|committed to excellence|your local experts?|second to none|"
    r"you can trust|excellence in)\b", re.I)


def _t(s):
    """Trim and un-escape. Quoting a raw title into an email printed "Health &amp; Fitness"
    at a stranger, which looks exactly as automated as it is."""
    return _html.unescape((s or "")).strip()


# Words that say nothing about the trade, so their absence from a title proves nothing.
# The keyword is a SEARCH phrase ("luxury gym chelsea"), not a description of the business.
_QUALIFIER = {"luxury", "best", "top", "cheap", "affordable", "local", "professional",
              "emergency", "24", "hour", "hours", "near", "me", "the", "and", "for", "in"}


# Ortsnamen-Bestandteile, die nichts unterscheiden. "Saint" faellt raus, weil Google
# "Bury Saint Edmunds" fuehrt und die Firma selbst "Bury St Edmunds" schreibt.
_TOWN_NOISE = {"saint", "st", "upon", "on", "the", "under", "over", "great", "little",
               "north", "south", "east", "west", "am", "an", "der", "im", "bei"}


def names_town(text: str, town: str) -> bool:
    """Nennt der Text den Ort? Toleriert die uebliche Schreibweisen-Drift.

    Ein exakter Vergleich warf "1 Allocks - Emergency Locksmith in Bury St Edmunds"
    vor, den Ort nicht zu nennen, weil er in unseren Daten "Bury Saint Edmunds" heisst.
    Das waere eine Falschaussage ueber den eigenen Titel des Betriebs gewesen. Es genuegt
    daher ein unterscheidender Bestandteil ("edmunds"), nicht die ganze Phrase.
    """
    t = (text or "").lower()
    if not town:
        return True                      # kein Ort bekannt -> nie behaupten, er fehle
    if town.lower() in t:
        return True
    parts = [w for w in re.sub(r"[^a-z0-9äöüß ]", " ", town.lower()).split()
             if len(w) > 2 and w not in _TOWN_NOISE]
    return any(p in t for p in parts) if parts else True


def _service_words(service: str, town: str) -> list[str]:
    """The words in a money keyword that actually name the trade.

    Judging on the FIRST token alone said "your title never says what you do" about
    "Health & Fitness Club Chelsea | KX Gym, London", because the keyword happened to
    start with "luxury". The town is dropped too: it is checked separately, and leaving
    it in produced "carpet cleaning liverpool Liverpool" in the consequence line.
    """
    t = (town or "").lower()
    return [w for w in re.sub(r"[^a-z0-9 ]", " ", (service or "").lower()).split()
            if len(w) > 2 and w not in _QUALIFIER and w != t]


def _toks(s):
    return {w for w in re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).split() if len(w) > 2}


def _has(html, *needles):
    low = html.lower()
    return any(n in low for n in needles)


# Hosts that are somebody else's platform, not the business's own site. 127 of the 7.291
# locksmith places point their Google "website" field at one of these.
NOT_A_SITE = ("facebook.com", "instagram.com", "linktr.ee", "wa.me", "t.me",
              "yelp.", "nextdoor.", "checkatrade.com", "yell.com", "trustpilot.",
              "business.site", "sites.google.com", "linkedin.com", "twitter.com", "x.com")


def is_own_site(url: str) -> bool:
    """False when the 'website' is a social or directory profile.

    This guard exists because pointing the auditor at a Facebook page produced five
    confident findings, every one of them nonsense: it quoted Facebook's own page title
    back as if it were theirs, complained that Facebook carries no LocalBusiness markup,
    and told a cobbler in Sleaford that his title does not mention locksmith Leicester.
    """
    host = (url or "").split("//")[-1].split("/")[0].lower()
    return bool(host) and not any(s in host for s in NOT_A_SITE)


def _digits(v) -> str:
    """Nur die Ziffern. Telefonnummern stehen mal mit Klammern, mal mit Leerzeichen,
    mal mit +44 auf der Seite und mit 0 im Profil -- verglichen wird der nackte Rest."""
    return "".join(c for c in str(v or "") if c.isdigit())


def evaluate(html: str, ctx: dict | None = None, pages: list | None = None) -> list[dict]:
    """ctx: {town, service, gbp_services:[..], rating}. Everything optional; a missing
    input silently drops the findings that need it rather than guessing."""
    ctx = ctx or {}
    out = []

    def add(check, kind, fact, means, strength):
        out.append({"check": check, "kind": kind, "fact": fact, "means": means,
                    "strength": strength})

    # Diese Pruefung steht VOR dem HTML-Riegel, und zwar bewusst: der Befund braucht kein
    # HTML, er steht schon in der URL. Andersherum stieg evaluate bei leerem html aus und
    # der Riegel feuerte nie -- gefunden im Selbstcheck von build_lead_findings.
    url = _t(ctx.get("url"))
    if url and not is_own_site(url):
        host = url.split("//")[-1].split("/")[0].lower().replace("www.", "").replace("m.", "")
        add("web-own-site", "gap",
            f"your Google profile sends people to {host} instead of your own site",
            "you cannot rank a page you do not own, and whoever does rank takes the call",
            98)
        return out

    # Die Domain aus dem Profil loest nicht mehr auf. Setzt build_lead_findings nur bei
    # echtem DNS-Ausfall, nie bei einem gescheiterten Abruf: "blockiert" heisst, die Seite
    # lebt und mag uns nicht, und daraus darf nie "deine Seite ist tot" werden.
    # Betrifft ~5% der Leads, und fuer die ist es der einzige Website-Befund, den es gibt.
    if ctx.get("site_dead") and url:
        host = url.split("//")[-1].split("/")[0].lower().replace("www.", "")
        add("web-site-dead", "gap",
            f"the site on your profile, {host}, does not load at all",
            "every person who taps through from google lands on an error", 99)
        return out

    if not _t(html):
        return out                      # nothing fetched -> nothing claimed, ever

    low = html.lower()
    town = _t(ctx.get("town")).lower()
    service = _t(ctx.get("service")).lower()
    svc_words = _service_words(service, town)
    # The trade phrase without the town, for the consequence line ("floor sanding", not
    # "floor sanding bristol Bristol").
    svc_phrase = " ".join(svc_words)

    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    if m:
        title = _t(re.sub(r"\s+", " ", m.group(1)))
    h1 = ""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    if m:
        h1 = _t(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(1))))

    # ---- copywriting: quote their own words -------------------------------------
    if title:
        tl = title.lower()
        # ANY trade word counts as "says what you do". Requiring all of them, or only the
        # first, both produce false accusations about a title that is perfectly clear.
        miss_town = bool(town) and not names_town(tl, town)
        miss_svc = bool(svc_words) and not any(w in tl for w in svc_words)
        search_phrase = " ".join(x for x in (svc_phrase, ctx.get("town", "")) if x).strip()
        if miss_town and miss_svc:
            add("web-title", "gap", f'your page title reads "{title}"',
                f"someone searching {search_phrase} never sees those words in it", 95)
        elif miss_svc:
            add("web-title", "gap", f'your page title reads "{title}"',
                "it never says what you actually do", 80)
        elif miss_town:
            add("web-title", "gap", f'your page title reads "{title}"',
                f"it never says {ctx.get('town','')}, the one word local searchers add".strip(), 78)
        elif town and svc_words:
            add("web-title", "good", "your page title names both the job and the town",
                "that is the strongest on-page signal there is, and it is already right", 50)

    if h1:
        h1l = h1.lower()
        _h1_blank = (town and svc_words and not names_town(h1l, town)
                     and not any(w in h1l for w in svc_words))
        # Two different faults, two different consequences. Merging them accused
        # "LUXURY HEALTH AND FITNESS CLUB IN LONDON" of being interchangeable, when its
        # actual fault is narrower: it names London, not the district people search.
        if PLATITUDE.search(h1):
            add("web-h1", "gap", f'the first line on your site says "{h1}"',
                "it could sit on any competitor's site, so it gives nobody a reason to call you", 85)
        elif _h1_blank:
            add("web-h1", "gap", f'the first line on your site says "{h1}"',
                f"it never names {ctx.get('town','')}, where the searches you want happen".strip(), 72)
        elif town and town in h1.lower():
            add("web-h1", "good", "your headline names the job and the town",
                "a visitor knows in one second they are in the right place", 45)

    # ---- Handwerk am HTML ---------------------------------------------------------
    # 20 der 23 Website-Checks im Plattform-Katalog sind `source: html` -- beantwortbar
    # aus genau dem HTML, das wir ohnehin holen. Ausgewertet wurden sieben (Luka, 27.07.:
    # "das sind ein bisschen wenig Faktoren"). Die folgenden kosten keinen einzigen
    # zusaetzlichen Abruf, sie lagen nur brach.

    # Fehlt der Viewport, zoomt das Handy auf die Desktop-Breite: Text winzig, Nummer
    # nicht treffbar. Bei einem Notdienst kommt fast jeder Besucher vom Handy, deshalb
    # ist das kein Schoenheitsfehler, sondern die Seite.
    if "name=\"viewport\"" not in low and "name='viewport'" not in low:
        add("web-viewport", "gap", "your site has no mobile viewport set",
            "phones render it at desktop width, so everything is tiny before anyone reads it", 90)

    # Die Nummer auf der Seite gegen die im Google-Profil. Weichen sie ab, ruft ein Teil
    # der Leute eine Nummer an, die woanders klingelt -- und Google wird unsicher, ob
    # Seite und Eintrag derselbe Betrieb sind.
    gbp_phone = _digits(ctx.get("phone"))
    if gbp_phone and len(gbp_phone) >= 9:
        page_digits = _digits(html)
        if gbp_phone[-9:] not in page_digits:
            add("web-nap-consistency", "gap",
                "the number on your site is not the one on your google profile",
                "google cannot tell the two are the same business, and some callers reach "
                "the wrong line", 86)

    if "<meta" in low and 'name="description"' not in low and "name='description'" not in low:
        add("web-meta-og", "gap", "your pages have no meta description",
            "google writes its own preview for you, and it is rarely the one you would pick", 58)

    if "maps.google" not in low and "google.com/maps" not in low:
        add("web-map-embed", "gap", "there is no map on the page",
            "someone deciding whether you cover their street has to go and look it up", 52)

    if not _has(low, "lang=\"", "lang='"):
        add("web-lang", "gap", "your pages declare no language",
            "screen readers and google both have to guess", 30)

    # ---- conversion --------------------------------------------------------------
    # KEIN Lob mehr fuer eine waehlbare Nummer. Es feuerte bei 9 von 11 Leads und stand damit
    # fast wortgleich in jeder Mail -- und er weiss selbst, dass man ihn anrufen kann. Ein Lob
    # muss ihm etwas sagen, das er nicht nachsehen kann, sonst ist es Fuellmaterial mit
    # Vorlagen-Geruch. Als MANGEL bleibt der Check, dort ist er stark.
    if not _has(low, 'href="tel:', "href='tel:"):
        add("web-tap-to-call", "gap", "there is no tap-to-call link",
            "someone on a phone has to copy your number out by hand", 75)

    if not _has(low, "<form", "typeform", "jotform", "hsforms"):
        add("web-lead-capture", "gap", "there is no form on the page",
            "anyone who will not phone has no way to reach you", 70)

    # ---- trust / schema ----------------------------------------------------------
    if not _has(low, "localbusiness"):
        add("web-schema", "gap", "your site carries no LocalBusiness markup",
            "google cannot confidently tie the site to your Google listing", 55)
    else:
        add("web-schema", "good", "your site carries LocalBusiness markup",
            "google can tie the site to your listing, which most local sites skip", 35)

    if not _has(low, "aggregaterating"):
        rating = ctx.get("rating")
        star = f"your {rating}★" if rating else "your reviews"
        # 86% of leads -> capped below the differentiating gaps even though it matters.
        add("web-schema", "gap", "your reviews are not marked up on the site",
            f"{star} cannot show as stars in the search results", 45)

    # ---- depth --------------------------------------------------------------------
    words = len(re.findall(r"[A-Za-zÄÖÜäöüß]{3,}", re.sub(r"<script.*?</script>|<style.*?</style>", " ",
                                                          html, flags=re.S | re.I)))
    if words < 500:
        add("web-word-readability", "gap", f"the page carries about {words} words",
            "google has little to match against the searches you want", 60)

    # ---- structure: only with the full crawl --------------------------------------
    if pages:
        titles = [_t(p.get("title")) for p in pages if _t(p.get("title"))]
        dupes = len(titles) - len(set(titles))
        if dupes:
            add("arch-url-rules", "gap", f"{dupes + 1} of your pages share the same title",
                "google has to pick one of them and drops the rest", 85)
        thin = [p for p in pages if (p.get("words") or 0) < 200]
        if thin:
            add("web-location-content", "gap", f"{len(thin)} of your {len(pages)} pages are near-empty",
                "they compete with your real pages instead of helping them", 70)
        svcs = ctx.get("gbp_services") or []
        if svcs and len(pages) <= 2:
            add("arch-service-city-nesting", "gap",
                f"your profile lists {len(svcs)} services and the site is {len(pages)} page(s)",
                "there is nothing for google to rank for any single one of them", 90)
        arch = [p for p in pages if re.match(r"^(tag|category|author)-", p.get("slug") or "")]
        if len(arch) >= 3:
            add("arch-pyramid", "gap", f"{len(arch)} of your pages are tag archives",
                "near-duplicate pages that pull ranking away from the real ones", 50)

    return sorted(out, key=lambda f: -f["strength"])


# ---------------------------------------------------------------------------------
def self_check():
    """Every assertion here is a claim we must never make wrongly to a stranger."""
    ctx = {"town": "Bristol", "service": "floor sanding", "rating": 4.8}

    # nothing fetched -> nothing claimed. The single most important guarantee.
    assert evaluate("", ctx) == [], "empty html must produce no findings at all"
    assert evaluate("   ", ctx) == [], "blank html must produce no findings at all"

    # the real girt-services title: no service, no town -> the strongest copy gap
    f = evaluate("<html><head><title>Booking Demo</title></head><body></body></html>", ctx)
    t = [x for x in f if x["check"] == "web-title"][0]
    assert t["kind"] == "gap" and "Booking Demo" in t["fact"], t
    assert t["strength"] == 95, "title with neither job nor town is the top copy gap"

    # a correct title is PRAISED, not ignored -- this is an audit, not a list of faults
    good = evaluate("<title>Floor Sanding Bristol | X</title><h1>Floor sanding in Bristol</h1>"
                    '<a href="tel:+44">call</a><form></form>'
                    '<script type="application/ld+json">{"@type":"LocalBusiness"}</script>', ctx)
    kinds = {x["check"]: x["kind"] for x in good}
    assert kinds["web-title"] == "good", good
    assert kinds["web-h1"] == "good", good
    assert "web-tap-to-call" not in kinds, "eine waehlbare Nummer ist kein Lob mehr"
    assert any(x["kind"] == "good" for x in good), "a clean site must yield positives"

    # the real girt-services H1 -> platitude
    f = evaluate("<h1>Professional Cleaning Services You Can Trust</h1>", ctx)
    h = [x for x in f if x["check"] == "web-h1"][0]
    assert h["kind"] == "gap" and "You Can Trust" in h["fact"], h

    # AggregateRating is universal (86%) -> must never outrank a differentiating gap
    f = evaluate("<title>X</title>", ctx)
    agg = [x for x in f if "stars" in x["means"]][0]
    tap = [x for x in f if x["check"] == "web-tap-to-call"][0]
    assert agg["strength"] < tap["strength"], "universal gaps must not lead the mail"

    # structure findings only exist with the crawl, never inferred from one page
    assert not any(x["check"].startswith("arch-") for x in evaluate("<title>X</title>", ctx))
    f = evaluate("<title>X</title>", {**ctx, "gbp_services": ["a"] * 20},
                 pages=[{"title": "Home", "slug": "home", "words": 300}])
    assert any(x["check"] == "arch-service-city-nesting" for x in f), f

    # duplicate titles
    f = evaluate("<title>X</title>", ctx, pages=[{"title": "Same", "slug": "a", "words": 400},
                                                 {"title": "Same", "slug": "b", "words": 400}])
    assert any("share the same title" in x["fact"] for x in f), f

    # a missing town must not fabricate a town-based claim
    f = evaluate("<title>Some Title</title>", {"service": "plumbing"})
    assert all("None" not in x["fact"] and "None" not in x["means"] for x in f), f

    # a social profile yields ONE true finding, never a website audit. Pointing the
    # auditor at facebook.com/arcadecobbler produced five confident false claims.
    fb = evaluate("<title>The Arcade Cobbler | Sleaford</title><body>x</body>",
                  {**ctx, "url": "http://facebook.com/arcadecobbler"})
    assert len(fb) == 1 and fb[0]["check"] == "web-own-site", fb
    # ... und OHNE html, denn fuer ein Social-Profil holen wir die Seite gar nicht erst.
    # Stand der Riegel hinter dem html-Check, feuerte er in der Praxis nie.
    fb2 = evaluate("", {**ctx, "url": "http://facebook.com/arcadecobbler"})
    assert len(fb2) == 1 and fb2[0]["check"] == "web-own-site", fb2
    assert "facebook.com" in fb[0]["fact"], fb
    assert not any(x["check"] in ("web-title", "web-tap-to-call", "web-schema") for x in fb), fb
    assert is_own_site("https://advantex-cleaning.co.uk/")
    assert not is_own_site("https://m.facebook.com/x") and not is_own_site("https://yell.com/y")
    # no url in ctx -> behave exactly as before, never assume
    assert len(evaluate("<title>T</title>", ctx)) > 1

    # Schreibweisen-Drift: das GBP fuehrt Googles kanonische Form ("Bury Saint Edmunds"),
    # die Firma schreibt "Bury St Edmunds". Ein exakter Vergleich warf ihr vor, den
    # eigenen Ort nicht zu nennen -- gemessen 31 solche Faelle in der Locksmith-Liste.
    bury = evaluate('<title>1 Allocks - Emergency Locksmith in Bury St Edmunds</title>',
                    {"town": "Bury Saint Edmunds", "service": "locksmith"})
    bt = [x for x in bury if x["check"] == "web-title"]
    assert not any(x["kind"] == "gap" and "never says" in x["means"] for x in bt), bt
    assert names_town("locksmith in bury st edmunds", "Bury Saint Edmunds")
    assert names_town("plumber stoke on trent", "Stoke-on-Trent")
    assert not names_town("locksmith in leeds", "Bury Saint Edmunds")
    # ohne bekannten Ort nie behaupten, er fehle
    assert names_town("irgendwas", "")

    # --- the three defects the first real run produced, each now a test -------------
    # 1. kxlife: keyword "luxury gym chelsea" -> judging on the first token alone called
    #    a title that plainly names the trade "never says what you actually do".
    kx = evaluate("<title>Health &amp; Fitness Club Chelsea | KX Gym, London</title>",
                  {"town": "Chelsea", "service": "luxury gym chelsea"})
    kt = [x for x in kx if x["check"] == "web-title"][0]
    assert kt["kind"] == "good", f"title names the trade and the town: {kt}"
    # 2. the quoted text must be human-readable, not raw HTML entities
    assert "&amp;" not in kt["fact"] and "&amp;" not in json.dumps(kx), kx
    # 3. girt-services: the town sits inside the keyword, so it must not be appended twice
    g = evaluate("<title>Booking Demo</title>",
                 {"town": "Liverpool", "service": "carpet cleaning liverpool"})
    gm = [x for x in g if x["check"] == "web-title"][0]["means"]
    assert gm.lower().count("liverpool") == 1, f"town repeated: {gm}"
    assert "carpet cleaning" in gm, gm

    print("self-check ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url")
    ap.add_argument("--town", default="")
    ap.add_argument("--service", default="")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        self_check()
        return 0
    if not a.url:
        ap.error("--url or --self-check")
    req = urllib.request.Request(a.url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    # url MUSS mit, sonst greift der Social-Riegel nicht und ein Facebook-Profil wird
    # als Website auditiert. Genau das ist beim Selbst-Review aufgefallen: der Riegel
    # war gebaut, getestet und von keinem Aufrufer je aktiviert.
    for f in evaluate(html, {"town": a.town, "service": a.service, "url": a.url}):
        mark = "+" if f["kind"] == "good" else "-"
        print(f"  {mark} [{f['strength']:>3}] {f['check']:<26} {f['fact']}")
        print(f"        -> {f['means']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
