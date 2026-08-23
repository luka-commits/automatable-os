#!/usr/bin/env python3
"""preview_mail.py — die Vorlage plus eine Zeile aus cohort_vars.csv, als fertige Mail.

Wozu: `instantly_markt.html` ist der Rahmen, `cohort_vars.csv` sind die Variablen, und bis
beide zusammengesetzt sind, hat niemand gesehen, was der Empfaenger bekommt. Genau dort sind
am 27.07. zwei Saetze aufgefallen, die einzeln richtig waren und zusammen unsinnig.

Was hier geprueft wird, und was NICHT:
  HIER   dass jede Variable der Vorlage in der CSV existiert und gefuellt ist, dass kein
         {{platzhalter}} stehen bleibt, dass keine Zeile ins Leere laeuft.
  NICHT  ob die Aussagen stimmen. Das macht `verify_mail.py` gegen den Brief.

Usage:
  python3 preview_mail.py --run runs/locksmith-bedford            # alle geschriebenen Leads
  python3 preview_mail.py --run runs/locksmith-bedford --limit 1
  python3 preview_mail.py --self-check
"""
from __future__ import annotations
import argparse, csv, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "instantly_markt.html")
BETREFF = "{{subject}}"


def render(html: str, row: dict) -> tuple[str, list[str]]:
    """HTML-Vorlage + Zeile -> Klartext, plus die Maengel, die auffallen.

    Instantly setzt eine leere Variable als leeren Text ein; die Zeile bleibt trotzdem
    stehen. Deshalb faellt hier jede Zeile weg, die nach dem Einsetzen leer ist -- sonst
    stuende zwischen den Stichpunkten und dem Fazit ein Loch, dessen Groesse davon abhaengt,
    wie viele Befunde der Lead hatte.
    """
    # Kommentare zuerst raus: die Kopfzeile der Vorlage erklaert {{subject}}, und das ist
    # keine Variable des Rumpfes.
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    fehlt = sorted({m for m in re.findall(r"\{\{(\w+)\}\}", html) if m not in row})
    text = re.sub(r"\{\{(\w+)\}\}", lambda m: (row.get(m.group(1)) or "").strip(), html)
    # Doppelte Leerzeichen entstehen, wo eine leere Variable zwischen zwei Saetzen stand.
    # Im Postfach faellt das nicht auf, HTML faltet Leerraum -- hier schon, und dann sucht
    # jemand einen Fehler, den der Empfaenger nie sieht. Also gleich falten.
    zeilen = [re.sub(r" {2,}", " ", re.sub(r"<[^>]+>", "", z)).strip()
              for z in text.strip().splitlines()]
    out, leer = [], False
    for z in zeilen:
        if z:
            out.append(z)
            leer = False
        elif out and not leer:      # genau eine Leerzeile zwischen zwei Absaetzen
            out.append("")
            leer = True
    mail = "\n".join(out).strip()

    mangel = [f"Variable fehlt in der CSV: {f}" for f in fehlt]
    if "{{" in mail:
        mangel.append("nicht ersetzter Platzhalter")
    if "—" in mail or "–" in mail:
        mangel.append("Gedankenstrich (stehende Regel)")
    if re.search(r"\.\s*\.", mail) or re.search(r",\s*\.", mail):
        mangel.append("Satzzeichen ins Leere (leere Variable mitten im Satz)")
    return mail, mangel


def self_check():
    # Stand 22.08.2026: `position` und `verdict_line` gibt es nicht mehr. Satz 1 kommt fertig
    # aus `export_cohort.opener()`, die Nische aus `niche_plural` -- der Schreiber liefert nur
    # noch die Stichpunkte.
    voll = {"company_casual": "gold",
            "opener": "i just checked out auto keys and a few other of your competitors in bedford.",
            "niche_plural": "locksmiths",
            "score_line": "you came out at 60/100 across the following 12 categories:",
            "gut_satz": "you've got 80 reviews where most uk locksmiths have 20, "
                        "a claimed and verified profile and a website linked from the listing.",
            "tips_intro": "what's costing you calls:",
            "tip_1": "- a", "tip_2": "- b", "tip_3": "", "tip_4": "", "tip_5": ""}
    html = open(TEMPLATE, encoding="utf-8").read()
    mail, mangel = render(html, voll)
    assert not mangel, mangel
    assert mail.startswith("hey gold,"), mail
    # Satz 1 und die Bruecke stehen in EINER Zeile, sonst zerfaellt der Einstieg in zwei Absaetze
    assert "in bedford. you came out at 60/100" in mail, mail
    # kein Loch, wo die leeren Stichpunkte standen: nach der Liste kommt sofort das Angebot
    # zwischen Liste und Abschluss steht seit 22.08. der Empfehlungssatz
    # Empfehlung und Vorstellung sind EIN Absatz (Luka, 22.08.: "das sollte eine sektion
    # sein und nicht zwei") -- zwischen Liste und Abschluss steht genau eine Leerzeile.
    assert "- b\n\nsorting the profile out" in mail, mail
    assert "local leads. i'm a freelancer" in mail, mail
    assert "lowest hanging fruit" in mail, mail
    assert "i'm a freelancer helping locksmiths get found online" in mail, mail
    assert "answer yes and it's yours" in mail, mail
    # "beat" steht seit 22.08. in der Bruecke ueber der Liste ("to beat them"), nicht mehr
    # im Abschluss -- der Gedanke kommt jetzt frueher, statt am Ende wiederholt zu werden.
    for teil in ("full report", "what's already right", "walkthrough included"):
        assert teil in mail, teil
    # und der Schluss ist EIN Absatz, nicht zwei
    assert mail.strip().split("\n\n")[-2].count("reply yes") == 1, mail
    assert "\n\n\n" not in mail, "mehr als eine Leerzeile"
    # keine Liste -> auch keine Ankuendigung einer Liste, und Satz 1 steht dann allein
    prosa = {**voll, "tips_intro": "", "tip_1": "", "tip_2": ""}
    mail3, _ = render(html, prosa)
    assert "costing you calls" not in mail3, mail3
    assert "in bedford." in mail3, mail3
    # fehlende Spalte faellt auf, statt still leer zu bleiben
    _, m4 = render(html, {k: v for k, v in voll.items() if k != "opener"})
    assert m4 and "opener" in m4[0], m4
    print("preview_mail self-check ok")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="runs/<niche>-<region>")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check or not a.run:
        return self_check()

    html = open(TEMPLATE, encoding="utf-8").read()
    rows = [r for r in csv.DictReader(open(os.path.join(a.run, "cohort_vars.csv"),
                                           encoding="utf-8")) if (r.get("tip_1") or "").strip()]
    if a.limit:
        rows = rows[:a.limit]
    schlecht = 0
    for r in rows:
        mail, mangel = render(html, r)
        betreff = re.sub(r"\{\{(\w+)\}\}", lambda m: (r.get(m.group(1)) or ""), BETREFF)
        print("=" * 78)
        print(f"AN   {r.get('business_name', '')[:50]}")
        print(f"BETR {betreff}")
        print("=" * 78)
        print(mail)
        if mangel:
            schlecht += 1
            print(f"\n  >>> {mangel}")
        print()
    print(f"{len(rows) - schlecht}/{len(rows)} sauber zusammengesetzt")
    return 1 if schlecht else 0


if __name__ == "__main__":
    sys.exit(main())
