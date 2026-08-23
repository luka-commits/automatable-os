#!/usr/bin/env python3
"""themes.py — zwei Punkte je Seite, jeder eine Lage statt eines Einzelbefunds.

Der Anlass (Luka, 27.07.2026): "idealerweise zwei Punkte pro Pro und Contra, aber die
zwei Punkte muessen nicht immer nur ein Finding sein, sondern darin die Gesamtsituation
gut zusammenfassen."

Der Unterschied ist nicht Kosmetik. Fuenf Einzelbefunde lesen sich wie eine Pruefliste,
die ein Werkzeug ausgespuckt hat. Zwei Saetze, die je drei Beobachtungen zu einer Lage
buendeln, lesen sich wie jemand, der hingesehen und verstanden hat -- und genau dieser
Unterschied entscheidet, ob ein Fremder antwortet.

Gebuendelt wird nach THEMA, nicht nach Staerke. Der Inhaber denkt nicht in Check-IDs,
er denkt in "werde ich gefunden", "erreicht mich jemand", "trauen die mir zu". Drei
Befunde aus demselben Thema sind fuer ihn EIN Problem mit drei Symptomen, und so
gehoeren sie auch in den Satz.

Zusammengefasst wird DETERMINISTISCH: der staerkste Befund des Themas traegt den Satz,
die anderen haengen als Fakten dran. Kein Modell formuliert hier, weil eine erfundene
Verbindung zwischen zwei Befunden ("deshalb") eine Behauptung ueber Ursachen waere, die
wir nicht gemessen haben.

Usage:
  python3 themes.py --self-check
"""
from __future__ import annotations
import sys

# Ein Thema ist eine Frage, die der Inhaber sich selbst stellt -- nicht ein Bereich
# unserer Software. "gbp" und "web" sind unsere Einteilung, "findet mich jemand" seine.
THEMES = {
    "found": {
        "checks": ("gbp-secondary-categories", "gbp-services", "gbp-hours",
                   "gbp-description", "web-title", "web-location-content"),
        "gap_lead": "google does not have enough to go on when someone searches",
        "good_lead": "google has plenty to match you on",
    },
    "trust": {
        "checks": ("gbp-reviews-volume", "gbp-reviews-quality", "gbp-photos",
                   "gbp-posts", "gbp-claimed", "web-schema"),
        "gap_lead": "the proof is thinner than the work",
        "good_lead": "the reputation is already doing its job",
    },
    "reach": {
        "checks": ("web-tap-to-call", "web-lead-capture", "web-viewport",
                   "web-nap-consistency", "web-own-site", "gbp-also-searched"),
        "gap_lead": "the people who do find you have a harder time reaching you than they should",
        "good_lead": "once someone lands on you, reaching you is easy",
    },
}
_OF = {c: t for t, d in THEMES.items() for c in d["checks"]}

# KEIN Gedankenstrich in ausgehender Copy -- Lukas stehende Regel, der #1-AI-Tell.
# Ich hatte ihn als Trenner eingebaut und damit in jede Mail geschrieben. Auf der
# Lob-Seite trennt jetzt ein Doppelpunkt (Urteil, dann Beleg), auf der Mangel-Seite
# ein "so" (Fakten, dann Folge) -- was ohnehin praeziser ist als ein Strich.
MAX_WORDS = 26      # ein Stichpunkt, den man am Handy in einem Zug liest
GOOD_PROOF = 14     # der Beleg auf der Lob-Seite: ein Halbsatz, kein Nachweis.
                    # Bei 11 fiel ausgerechnet der Vergleich weg -- aus "shows 24 hours,
                    # which only 4 of the 11 in town do" wurde "shows 24 hours", und damit
                    # aus der Nachricht eine Selbstverstaendlichkeit.


def _clip(fact: str, cap: int = GOOD_PROOF) -> str:
    """Den Beleg auf einen Halbsatz kuerzen, aber nur an einer Kommastelle.

    "135 reviews puts you in the top quarter of uk locksmiths, and second in town" ist als
    Beweis richtig und als Lob zu lang -- er kennt seine Zahl. Gekuerzt wird nur dort, wo
    ohnehin ein Komma steht, damit nie ein halber Satz entsteht. Passt nichts, bleibt der
    ganze Fakt: lieber etwas zu lang als abgeschnitten.
    """
    words = fact.split()
    if len(words) <= cap:
        return fact
    head = " ".join(words[:cap])
    cut = head.rfind(",")
    return head[:cut] if cut > 0 else fact


# Rueckfall, wenn die Themen-Formulierung in dieser Mail schon vergeben ist. Ohne ihn
# stand die zweite Zeile nackt da ("your page title names both the job and the town") --
# ein Fakt ohne Urteil, und genau das soll die Lob-Seite nicht sein.
ASSET_LEAD = {
    ("profile", "good"): "the profile is in decent shape",
    ("site", "good"): "the site does its part",
    ("profile", "gap"): "the profile is leaving work on the table",
    ("site", "gap"): "the site is not pulling its weight",
}


def _asset(check: str) -> str:
    """Welcher der beiden Anlagen gehoert der Befund: dem Google-Profil oder der Seite.

    Dieselbe Zweiteilung wie im Score, damit die Mail in sich stimmt: zwei Zahlen oben,
    zwei Zeilen darunter, je eine je Anlage.
    """
    return "profile" if check.startswith("gbp-") else "site"


def _fact(f):
    return (f.get("fact") or "").strip().rstrip(".")


def bundle(findings: list, kind: str, n: int = 2) -> list:
    """-> bis zu n Saetze, je einer pro Thema, staerkstes Thema zuerst.

    Ein Thema mit einem einzigen Befund bleibt dieser Befund -- daraus eine "Lage" zu
    machen waere aufgeblasen. Erst ab zwei Beobachtungen entsteht die Zusammenfassung.
    """
    # Gebuendelt wird je ANLAGE, nicht quer durch (Luka, 27.07.: "was mir fehlt ist die
    # Summary des ganzen GBP und der Website, du beschraenkst dich stark auf die
    # Reputation"). Er hat zwei Dinge, die ihm gehoeren: das Google-Profil und die Seite.
    # Genau die zeigen wir im Score, also muessen sie auch die zwei Punkte tragen -- sonst
    # landen beide zufaellig im selben Bereich und die Haelfte der Mail fehlt.
    by_asset = {}
    for f in sorted([x for x in findings if x["kind"] == kind],
                    key=lambda x: -x["strength"]):
        if _OF.get(f["check"]):
            by_asset.setdefault(_asset(f["check"]), []).append(f)

    ranked = [(a, fs) for a, fs in sorted(by_asset.items(),
                                          key=lambda kv: -kv[1][0]["strength"])][:n]
    out, used = [], set()
    for asset, fs in ranked:
        # Die Lage-Formulierung kommt vom staerksten Thema INNERHALB der Anlage -- aber nie
        # zweimal dieselbe. Bei Wolfguard endeten beide Mangel-Zeilen auf "so google does not
        # have enough to go on when someone searches", weil in Profil UND Seite dasselbe Thema
        # vorn lag. Zweimal derselbe Schlusssatz liest sich wie ein Textbaustein, und genau
        # das soll die Buendelung ja verhindern. Ist das Thema vergeben, gilt das naechste
        # der Anlage; gibt es keines, entfaellt die Lage-Zeile und die Fakten stehen allein.
        themes_here = [_OF[x["check"]] for x in fs]
        theme = next((t for t in themes_here if t not in used), None)
        lead = THEMES[theme][f"{kind}_lead"] if theme else ASSET_LEAD.get((asset, kind), "")
        if theme:
            used.add(theme)

        # Die Lob-Seite laeuft ANDERSHERUM (Luka, 27.07.: "kuerzer und allgemeiner, wie eine
        # Executive Summary, die die Essenz verstanden hat"). Beim Mangel muss der Fakt
        # zuerst stehen, weil die Zahl die Behauptung traegt und er sie sonst nicht glaubt.
        # Beim Lob nicht: seine 135 Bewertungen kennt er. Was er nicht hat, ist das Urteil --
        # "dieser Teil ist erledigt". Also Urteil zuerst, ein knapper Beleg dahinter, fertig.
        if kind == "good":
            # IMMER Einschaetzung zuerst, dann EINE konkrete Sache (Luka, 27.07.: "aus Sicht
            # eines Business Owners haette ich gerne die allgemeine Einschaetzung mit einer
            # konkreten Sache"). Vorher trug ein einzelner Befund sich selbst, und dann stand
            # bei einem Lead "1219 photos on the profile against a middle of the pack at 14"
            # ganz ohne Urteil -- eine Zahl, mit der er nichts anfangen kann. Der Grund fuer
            # die alte Ausnahme (die Themen-Zeile schluckte den Vergleich) ist mit dem
            # groesseren GOOD_PROOF weg: der Vergleich passt jetzt in den Beleg.
            proof = _clip(_fact(fs[0]))
            out.append(f"{lead}: {proof}" if (lead and proof) else (proof or lead))
            continue

        facts = [_fact(f) for f in fs[:3] if _fact(f)]
        # Ein gebuendelter Punkt darf nicht laenger sein als ein Satz, den man am Handy
        # in einem Zug liest. Der erste Lauf erzeugte 47 Woerter aus drei Befunden mit
        # Nebensaetzen -- formal richtig und trotzdem uebersprungen. Solange es zu lang
        # ist, faellt der schwaechste Fakt weg, nicht der Vergleich in den anderen.
        while len(facts) > 1 and len(" ".join(facts).split()) > MAX_WORDS:
            facts.pop()
        if len(facts) == 1:
            # ein einzelner Befund traegt sich selbst, samt seiner Folge
            means = (fs[0].get("means") or "").strip().rstrip(".")
            out.append(f"{facts[0]}, so {means}" if means else facts[0])
        else:
            joined = ", ".join(facts[:-1]) + ", and " + facts[-1]
            out.append(f"{joined}, so {lead}" if lead else joined)
    return out


def self_check():
    def f(check, kind, fact, strength, means=""):
        return {"check": check, "kind": kind, "fact": fact, "means": means,
                "strength": strength}

    fs = [f("gbp-hours", "gap", "your profile does not show 24 hours", 88, "the 2am call goes elsewhere"),
          f("gbp-secondary-categories", "gap", "your profile is set to locksmith only", 85),
          f("web-tap-to-call", "gap", "there is no tap-to-call link", 70, "people copy it by hand")]
    got = bundle(fs, "gap", 2)
    assert len(got) == 2, got
    # eine Zeile je Anlage: die zwei GBP-Befunde bilden EINE, die Website die andere
    assert "and your profile is set to locksmith only" in got[0], got[0]
    assert "tap-to-call" in got[1], got[1]
    # nur GBP-Befunde ergeben nur eine Zeile, keine erfundene zweite
    assert len(bundle(fs[:2], "gap", 2)) == 1
    # dieselbe Lage-Formulierung kommt in einer Mail nie zweimal vor
    doppelt = [f("gbp-hours", "gap", "no 24 hours", 88),
               f("gbp-description", "gap", "no description", 80),
               f("web-title", "gap", "title says nothing", 75),
               f("web-location-content", "gap", "thin page", 70)]
    two = bundle(doppelt, "gap", 2)
    leads = [THEMES[t]["gap_lead"] for t in THEMES]
    hits = [l for l in leads if sum(1 for x in two if x.endswith(l)) > 1]
    assert not hits, (hits, two)
    # ist das Thema vergeben, traegt die Anlage die Einschaetzung -- nie ein nackter Fakt
    gs2 = [f("gbp-reviews-volume", "good", "135 reviews, second in town", 92),
           f("gbp-photos", "good", "40 photos", 60),
           f("web-schema", "good", "your site carries LocalBusiness markup", 55)]
    both = bundle(gs2, "good", 2)
    assert len(both) == 2 and all(":" in x for x in both), both
    assert got[0].endswith("so google does not have enough to go on when someone searches"), got[0]
    # niemals ein Gedankenstrich in etwas, das an einen Fremden geht
    assert not any("—" in x or "–" in x for x in got), got
    # ein einzelner Befund bleibt er selbst, mit seiner Folge, ohne Lagebeschreibung
    assert got[1] == "there is no tap-to-call link, so people copy it by hand", got[1]
    # kein Stichpunkt wird laenger als ein lesbarer Satz
    lang = [f("gbp-hours", "gap", "your profile does not show 24 hours, where 5 in town do", 88),
            f("gbp-secondary-categories", "gap",
              "your profile is set to locksmith only, where the most-reviewed firms in town "
              "are also listed as emergency locksmith service", 85),
            f("gbp-description", "gap",
              "no business description on the profile, where one of the firms above you wrote one", 68)]
    out = bundle(lang, "gap", 1)[0]
    assert len(out.split()) <= MAX_WORDS + 12, f"{len(out.split())}: {out}"
    # nichts da heisst nichts erfunden
    assert bundle([], "gap") == []
    assert bundle(fs, "good") == []
    # Die Lob-Seite fuehrt mit dem Urteil und belegt knapp, nicht umgekehrt
    gs = [f("gbp-reviews-volume", "good",
            "135 reviews puts you in the top quarter of uk locksmiths, and second in town", 92),
          f("gbp-posts", "good", "you post on your profile", 75)]
    g = bundle(gs, "good", 1)[0]
    assert g.startswith("the reputation is already doing its job:"), g
    assert "—" not in g, g
    # auch ein EINZELNES Lob fuehrt mit der Einschaetzung, und der Vergleich bleibt erhalten
    solo = bundle([f("gbp-hours", "good", "your profile shows 24 hours, which only 4 of the 11 do",
                     80, "that is the job nobody shops around for")], "good", 1)[0]
    assert solo.startswith("google has plenty to match you on:"), solo
    assert "only 4 of the 11" in solo, solo
    assert len(g.split()) < 20, f"{len(g.split())}: {g}"
    # gekuerzt wird nur an einem Komma, nie mitten im Satzteil
    assert not g.rstrip().endswith(("of", "the", "and", "in", "to")), g
    # ein Befund ohne Thema wird nicht heimlich einsortiert
    assert bundle([f("web-lang", "gap", "no lang attribute", 30)], "gap") == []
    print("self-check ok")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        self_check()
    else:
        print(__doc__)
