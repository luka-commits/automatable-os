#!/usr/bin/env python3
"""verdict.py — die eine Zeile, die aus einer Liste ein Urteil macht.

`markt_copy.md` verlangt sie ("so basically, {verdict}") und es gab sie nie. Damit endete
jede Mail als Aufzaehlung: fuenf Stichpunkte, kein Gedanke. Der Verdict ist die Stelle, an
der wir zeigen, dass wir nicht nur gemessen, sondern verstanden haben -- und die einzige,
an der aus Information ein Grund zu antworten wird.

Er ist eine ASYMMETRIE, kein Fazit. "Du gewinnst den Teil, der Jahre dauert, und verlierst
den, der einen Nachmittag dauert" wirkt, weil es ein Ungleichgewicht benennt, das der
Inhaber selbst spuert, aber nie in Worte gefasst hat. Ein Fazit ("insgesamt solide, mit
Verbesserungspotenzial") wirkt nie.

WARUM MUSTER STATT MODELL: markt_copy.md, offener Punkt drei -- "ein Dutzend genehmigter
Satzmuster, gekoppelt an Befund-Kombinationen, niemals 3.000 ungeprueffte Absaetze". Ein
Modell, das hier frei formuliert, erzeugt bei 4.700 Empfaengern garantiert Saetze, die
niemand gelesen hat. Jedes Muster hier ist an eine Bedingung gekoppelt, die aus den
Befunden folgt, und faellt keine zu, gibt es keinen Verdict statt eines erfundenen.

Usage:
  python3 verdict.py --self-check
"""
from __future__ import annotations
import sys


def _has(findings, *checks):
    return any(f["check"] in checks for f in findings)


def _kind(findings, kind):
    return [f for f in findings if f["kind"] == kind]


def verdict(findings: list, market: dict | None = None, bench_band: int = 0) -> str:
    """Ein Satzteil fuer "so basically, ...". Leer heisst: die Zeile entfaellt.

    Reihenfolge = Staerke. Das erste passende Muster gewinnt; sie sind so geschnitten, dass
    sich ihre Bedingungen nicht ueberlappen, ausser dass spezifischer vor allgemeiner steht.
    """
    goods, gaps = _kind(findings, "good"), _kind(findings, "gap")
    if not gaps:
        return ""

    strong_rep = bench_band and bench_band <= 10          # oberste 10% des Landes
    invisible = _has(gaps, "gbp-hours", "gbp-secondary-categories", "gbp-services")

    # 1. Der Klassiker, und der staerkste: Ruf steht, Sichtbarkeit nicht.
    if strong_rep and invisible:
        return ("you're winning the part that takes years and losing the part that takes "
                "an afternoon")

    # 2. Ruf steht, aber die Wege zu ihm sind zu. Kein Sichtbarkeits-, ein Kontaktproblem.
    if strong_rep and _has(gaps, "web-tap-to-call", "web-lead-capture"):
        return ("the reputation is doing its job and then the page drops the call at the "
                "last step")

    # 3. Der Notfall-Kern: der Auftrag kommt nachts, das Profil sagt nicht, dass jemand rangeht.
    if _has(gaps, "gbp-hours"):
        return ("the work is there, google just doesn't know you're open when the calls "
                "come in")

    # 4. Seine eigenen Kunden sagen, was er kann, sein Profil sagt es nicht.
    if _has(gaps, "gbp-services"):
        return "your customers already describe what you do better than your profile does"

    # 5. Alles eingerichtet, es fehlt nur der Beleg. Kein Tadel, eine Reihenfolge.
    if not strong_rep and len(goods) >= 2:
        return "the setup is in order, it just doesn't have enough proof behind it yet"

    # 6. Sichtbar unsichtbar: gefunden werden ist das Problem, nicht ueberzeugen.
    if invisible:
        return "you're not losing these jobs on price, you're losing them before anyone calls"

    return ""


def self_check():
    g = lambda c, k="gap": {"check": c, "kind": k, "fact": "", "means": "", "strength": 50}
    # Ruf oben, Sichtbarkeit unten -> die Asymmetrie
    assert "takes an afternoon" in verdict([g("gbp-hours")], bench_band=10)
    # derselbe Befund ohne starken Ruf -> das Notfall-Muster, nicht die Asymmetrie
    assert "when the calls come in" in verdict([g("gbp-hours")], bench_band=0)
    # ohne Luecken gibt es nichts zu urteilen
    assert verdict([g("gbp-photos", "good")]) == ""
    assert verdict([]) == ""
    # ein Befund ausserhalb aller Muster erfindet keinen Verdict
    assert verdict([g("web-schema")]) == ""
    # starker Ruf + nur ein Kontaktproblem -> Muster 2, nicht 1
    out = verdict([g("web-tap-to-call")], bench_band=5)
    assert "last step" in out, out
    print("self-check ok")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        self_check()
    else:
        print(__doc__)
