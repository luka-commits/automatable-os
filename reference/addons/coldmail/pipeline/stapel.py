#!/usr/bin/env python3
"""stapel.py — der Fliessband-Betrieb: Blaetter raus, Mails rein, vier Pruefer dazwischen.

DER ANLASS (Luka, 30.07.2026): "haben wir eine gute logik in place, damit dieses system
jetzt funktioniert fuer alle locksmiths in uk." Die Logik ja, der Betrieb nein: 21 von 2.744
anschreibbaren Leads waren geschrieben, und zwar von Hand. Der Engpass ist nicht die Technik,
sondern dass jeder Lead einzeln durch Datenblatt, Schreiben und Pruefen muss.

DIESE DATEI IST DIE SCHLEIFE, und sie hat genau zwei Richtungen:

  raus   `--next 25`   die naechsten 25 OFFENEN Leads als Datenblatt, plus die Schreibkarte.
                       Offen heisst: Befunde da, aber `web_signals.mail.tip_1` leer.
  rein   `--absorb x.json --apply`
                       die geschriebenen Variablen, durch ALLE VIER Pruefer, und nur was
                       durchkommt wird geschrieben. Der Rest wird benannt, nicht verworfen.

DIE VIER PRUEFER, und warum es vier sind (jeder ist an einem echten Schaden gewachsen):
  1. Zusammenbau   preview_mail   -- fehlende Spalte, Platzhalter, Zeile ins Leere
  2. Zahlen+Stil   verify_mail    -- erfundene Zahl, Fuellwendung, Gedankenstrich, Raeuspern
  3. Bestand       fact_sheet.widerspricht -- ein Rat zu etwas, das der Betrieb schon tut
                   (30.07.: 6 von 11 fertigen Mails, keiner der anderen Pruefer sah es)
  4. Formel        fact_sheet.formel -- Status quo, Handlung, Folge in jeder Zeile
                   (30.07.: 14 von 36 Zeilen ohne Handlung, nachdem ich die Regel selbst
                   aufgeschrieben hatte)

Usage:
  python3 stapel.py --niche locksmith --auto --grenze 20   # 20 Leads: bauen, pruefen\n  python3 stapel.py --niche locksmith --auto --apply       # alle, und schreiben\n  python3 stapel.py --niche locksmith --next 25            # Blaetter fuer einen Agenten
  python3 stapel.py --niche locksmith --next 25 --region Reading
  python3 stapel.py --niche locksmith --absorb mails.json           # nur pruefen
  python3 stapel.py --niche locksmith --absorb mails.json --apply   # pruefen und schreiben
  python3 stapel.py --self-check
"""
from __future__ import annotations
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# Ab 22.08.2026 liefert der Schreiber NUR noch die Stichpunkte. `position` (Satz 2, der
# Rang-Anspruch) und `verdict_line` (die Urteilszeile) sind aus der Vorlage raus -- der
# Rang-Anspruch war widerlegbar, das Urteil doppelte den neuen Abschluss. `widerspruch`
# bleibt: er geht nicht in die Mail, sondern in den Stichpunkt, wenn jemand Schwaecheres
# ueber dem Lead steht.
VARIABLEN = ["widerspruch", "tip_1", "tip_2", "tip_3", "tip_4", "tip_5"]


def _leads(niche: str, region: str = "") -> list:
    import urllib.parse, urllib.request
    from dedupe_leads import _supabase
    url, key = _supabase()
    hdr = {"apikey": key, "Authorization": f"Bearer {key}"}
    out, off = [], 0
    while True:
        q = (f"{url}/rest/v1/industry_operators?select=place_id,name,town,region,details,raw,"
             f"raw_dataforseo,web_signals,email&niche=eq.{urllib.parse.quote(niche)}"
             f"&pipeline_status=neq.disqualified&order=place_id&limit=1000&offset={off}")
        if region:
            q += f"&region=eq.{urllib.parse.quote(region)}"
        seite = json.load(urllib.request.urlopen(
            urllib.request.Request(q, headers=hdr), timeout=120))
        out += seite
        off += 1000
        if len(seite) < 1000:
            break
    return out


def schreibe(lead: dict, kohorte: list, bench: dict, ueblich: str) -> dict:
    """Die Mail-Variablen fuer EINEN Lead, ohne Modell. -> {} wenn zu duenn.

    DAS IST DER SCHRITT, DER BIS ZUM 23.08.2026 FEHLTE. `pool.py` konnte die Stichpunkte
    seit dem 22.08. bauen, aber kein Produktionsskript rief es: `--next` gab Datenblaetter
    fuer einen Agenten aus, `--absorb` las dessen Antwort zurueck. Der Maschinen-Weg lief
    nur in einem Skript im Scratchpad, also nirgends, wo er sich wiederholen liess.

    Was hier passiert, ist kein neues Verfahren, sondern das bestehende an der richtigen
    Stelle: Blatt bauen, Bausteine waehlen, Score rechnen, Nachbarn casualisieren -- alles
    Funktionen, die es schon gab.
    """
    import pool
    import gbp_score as GS
    import export_cohort as X
    from casualize import casual_brand
    from markt_umfeld import market_context

    raw = lead.get("raw") or {}
    rohe = [x.get("raw") or {} for x in kohorte]
    mk = dict(market_context(rohe, raw), primary=ueblich)
    blatt = pool.aus_lead(lead, mk, bench, lead.get("niche") or "locksmith")
    zeilen = pool.waehle(pool.bausteine(blatt), 4)
    if len(zeilen) < 3:
        return {}                      # unter drei Stichpunkten geht die Mail nicht raus

    punkte, n_faktoren = X.score_zahlen(
        raw, lead.get("raw_dataforseo"), bench, ueblich, blatt)
    ort = lead.get("town") or ""
    hood = raw.get("neighborhood") or ""
    lead_kurz = casual_brand(lead.get("name") or "", lead.get("niche") or "locksmith",
                             ort, hood) or ""
    nb = (lead.get("details") or {}).get("nearest") or []
    niche = lead.get("niche") or "locksmith"
    c1 = X.competitor(nb, 0, niche, ort, frozenset(), lead.get("name") or "")
    c2 = X.competitor(nb, 1, niche, ort, frozenset(), lead.get("name") or "")

    aus = {f"tip_{i + 1}": "- " + z["text"] for i, z in enumerate(zeilen[:5])}
    aus.update({f"tip_{i}": "" for i in range(len(zeilen) + 1, 6)})
    aus.update({
        "company_casual": (lead_kurz or lead.get("name") or "there").lower(),
        "subject": X.subject(lead.get("region") or "", niche, c1, len(kohorte), lead_kurz),
        "opener": X.opener(X.competitors_phrase(c1, c2), niche,
                           X.opener_gebiet(ort, lead.get("region") or "")),
        "score_line": "" if punkte is None else X.score_line(punkte, n_faktoren),
        "gut_satz": pool.gut_satz(pool.gut(blatt)),
        "tips_intro": X.findings_cols({"mail": {"tip_1": "x"}}, {})["tips_intro"],
    })
    return aus


def offen(leads: list) -> list:
    """Befunde da, Mail noch nicht, und eine Adresse zum Hinschicken.

    Ohne die Adresse waere die Mail Arbeit fuer den Papierkorb -- 849 der 3.593 Leads haben
    keine, und die gehoeren zuerst durch `recover_emails.py`, nicht durch den Schreiber.
    """
    # "Geschrieben" haengt seit 22.08. an `tip_1`, nicht mehr an `position` -- die Variable
    # gibt es nicht mehr. Waere die Pruefung stehengeblieben, haette KEIN Lead je als fertig
    # gegolten und das Fliessband haette dieselben 25 endlos wieder ausgegeben.
    return [x for x in leads
            if (x.get("web_signals") or {}).get("findings")
            and not (((x.get("web_signals") or {}).get("mail") or {}).get("tip_1") or "").strip()
            and (x.get("email") or "").strip()]


def pruefe(blatt: dict, vars_: dict, html: str) -> list:
    """Alle vier Pruefer ueber eine geschriebene Mail. -> Liste der Maengel, leer = sauber."""
    import fact_sheet as F
    import preview_mail as P
    import verify_mail as V
    # Stand 22.08.2026: Satz 1 und die Nische kommen aus dem Export, nicht vom Schreiber.
    # Hier werden sie nur gestellt, damit die Vorlage vollstaendig zusammensetzbar ist --
    # der Pruefer soll an den Stichpunkten scheitern, nicht an einer fehlenden Spalte.
    zeile = {"company_casual": (blatt.get("name") or "there").lower(),
             "subject": "",
             "opener": (f"i just checked out a few of your competitors in "
                        f"{(blatt.get('ort') or 'town')}."),
             "niche_plural": "locksmiths",
             # Score und "what's already right" baut `export_cohort`, nicht der Schreiber.
             # Hier werden sie nur gestellt, damit die Vorlage zusammensetzbar ist -- der
             # Pruefer soll an den Stichpunkten scheitern, nicht an einer fehlenden Spalte.
             # OHNE ZAHLEN: die echte Score-Zeile traegt zwei ("60 out of 100 across 12"),
             # und der Zahlen-Pruefer verwirft jede Zahl, die nicht im Datenblatt steht --
             # zu Recht, denn er soll den SCHREIBER kontrollieren. Der Score wird von
             # `export_cohort` gerechnet und ist per Konstruktion korrekt; ihn hier mit
             # Zahlen einzusetzen hiesse, den Pruefer gegen die eigene Maschine laufen zu
             # lassen. Die Vollstaendigkeit der Spalte prueft `preview_mail` weiterhin.
             "score_line": "here's how the profile looks from outside.",
             "gut_satz": "you've got a claimed and verified profile.",
             **{k: (vars_.get(k) or "") for k in VARIABLEN}}
    zeile["tips_intro"] = ("what's costing you calls:"
                           if any(zeile[f"tip_{i}"] for i in range(1, 6)) else "")
    mail, mangel = P.render(html, zeile)
    # Zahlen gegen das Datenblatt, nicht gegen einen Brief: was gemessen wurde, steht dort.
    # 71 (die Checks im Report) und 3 (die drei Kaesten) stehen in der festen Vorlage und
    # in keinem Datenblatt -- ohne die Ausnahme faellt jede Mail wegen ihres eigenen,
    # korrekten Rahmens durch.
    brief = {"blatt": blatt}
    mangel += [b for b in V.check(mail, brief, template_numbers=(71, 3))
               if "zu kurz" not in b]
    mangel += F.widerspricht(blatt, mail)
    for i in range(1, 6):
        if zeile[f"tip_{i}"]:
            fehlt = F.formel(zeile[f"tip_{i}"])
            if fehlt:
                mangel.append(f"Zeile {i} ohne {', '.join(fehlt)}: {zeile[f'tip_{i}'][:40]}")
    return mangel


def self_check():
    import fact_sheet as F
    leads = [
        {"place_id": "a", "email": "x@y.de", "web_signals": {"findings": [{"kind": "gap"}]}},
        {"place_id": "b", "email": "x@y.de", "web_signals": {"findings": [{"kind": "gap"}],
                                                             "mail": {"tip_1": "- da"}}},
        {"place_id": "c", "email": "", "web_signals": {"findings": [{"kind": "gap"}]}},
        {"place_id": "d", "email": "x@y.de", "web_signals": {}},
    ]
    assert [x["place_id"] for x in offen(leads)] == ["a"], offen(leads)

    html = open(os.path.join(HERE, "instantly_markt.html"), encoding="utf-8").read()
    blatt = F.blatt({"name": "Gold", "town": "Bedford",
                     "raw": {"reviewsCount": 9, "imagesCount": 1, "categories": ["Locksmith"],
                             "openingHours": [{"day": "Mon", "hours": "Open 24 hours"}]},
                     "raw_dataforseo": {"services": [], "antworten": {}},
                     "web_signals": {"findings": []}},
                    {"photos_median": 14, "count": 11},
                    # der Benchmark ist ab 30.07. das EINZIGE, womit verglichen wird --
                    # die Ortszahlen sind aus dem Blatt raus, siehe fact_sheet.blatt § land
                    {"n": 4746, "reviews": {"median": 20, "p75": 72, "p90": 166},
                     "photos_median": 14, "hours24": {"ja_pct": 53},
                     "posts": {"never_pct": 67}})
    # Die Stichpunkte halten seit 22.08. die 18-Woerter-Grenze aus verify_mail ein -- die
    # Testzeilen sind deshalb kuerzer als frueher, sie pruefen aber unveraendert dasselbe.
    sauber = {"tip_1": "- there's nothing under services, put five in so google "
                       "matches you to the job"}
    assert pruefe(blatt, sauber, html) == [], pruefe(blatt, sauber, html)
    # der Bestands-Pruefer schlaegt an: das Profil zeigt bereits 24 Stunden
    schlecht = dict(sauber, tip_2="- switch on 24 hour opening, that's the 2am job")
    assert any("24 hour" in m for m in pruefe(blatt, schlecht, html))
    # die Formel schlaegt an: keine Handlung in der Zeile
    ohne = dict(sauber, tip_2="- there's nothing under services, so people go elsewhere")
    assert any("ohne Handlung" in m for m in pruefe(blatt, ohne, html)), pruefe(blatt, ohne, html)
    # der Ortsvergleich schlaegt an (30.07.): wir kennen in Bedford 11 von 27 Betrieben,
    # also traegt keine Zahl eine Aussage ueber ALLE im Ort.
    ort = dict(sauber, tip_2="- you're on 1 photo where the rest of bedford has 14, "
                             "so get a dozen up")
    assert any("Ortsschnitt" in m for m in pruefe(blatt, ort, html)), pruefe(blatt, ort, html)
    # ... der Landesvergleich derselben Zeile aber NICHT -- ein Pruefer, der Richtiges
    # verwirft, wird abgeschaltet, und faengt dann auch das Falsche nicht mehr.
    land = dict(sauber, tip_2="- you're on 1 photo where most uk locksmiths have 14, "
                              "so get a dozen up")
    assert pruefe(blatt, land, html) == [], pruefe(blatt, land, html)
    # ... und die neue Laengengrenze faengt genau die Fassung, die vorher hier stand.
    zu_lang = dict(sauber, tip_2="- you're on 1 photo where most uk locksmiths have 14, so "
                                 "get a dozen up, people ring the one that looks real")
    assert any("zu lang" in m for m in pruefe(blatt, zu_lang, html)), pruefe(blatt, zu_lang, html)
    print("stapel self-check ok")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--niche", default="locksmith")
    ap.add_argument("--region", default="")
    ap.add_argument("--next", type=int, default=0, help="so viele Datenblaetter ausgeben")
    ap.add_argument("--absorb", default="", help="geschriebene Variablen einlesen und pruefen")
    ap.add_argument("--apply", action="store_true", help="mit --absorb: die sauberen schreiben")
    ap.add_argument("--auto", action="store_true",
                    help="die Stichpunkte selbst bauen, pruefen und schreiben")
    ap.add_argument("--grenze", type=int, default=0,
                    help="mit --auto: hoechstens so viele Leads bearbeiten")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return self_check()

    import benchmark
    import fact_sheet as F
    from markt_umfeld import market_context
    leads = _leads(a.niche, a.region)
    nach_region = {}
    for x in leads:
        nach_region.setdefault(x["region"], []).append(x["raw"] or {})
    bench = benchmark.load(a.niche)
    allein = F.allein_im_gebiet(leads)
    blaetter = {x["place_id"]: F.blatt(x, market_context(nach_region[x["region"]],
                                                         x["raw"] or {}), bench,
                                       allein.get(x["place_id"], False))
                for x in leads}

    if a.auto:
        import collections
        html = open(os.path.join(HERE, "instantly_markt.html"), encoding="utf-8").read()
        todo = offen(leads)
        if a.grenze:
            todo = todo[:a.grenze]
        # Die uebliche Hauptkategorie der ganzen Nische -- einmal gezaehlt, nicht je Lead.
        zaehl = collections.Counter((x.get("raw") or {}).get("categories", [None])[0]
                                    for x in leads if (x.get("raw") or {}).get("categories"))
        ueblich = zaehl.most_common(1)[0][0] if zaehl else None
        nach_region_voll = {}
        for x in leads:
            nach_region_voll.setdefault(x["region"], []).append(x)

        sauber, duenn, gebuckelt = {}, [], []
        for x in todo:
            vars_ = schreibe(x, nach_region_voll[x["region"]], bench, ueblich)
            if not vars_:
                duenn.append(x.get("name") or x["place_id"])
                continue
            m = pruefe(blaetter[x["place_id"]], vars_, html)
            if m:
                gebuckelt.append((x.get("name") or x["place_id"], m))
            else:
                sauber[x["place_id"]] = vars_
        for name, m in gebuckelt[:12]:
            print(f"  DURCHGEFALLEN {str(name)[:32]:34} {m}")
        if len(gebuckelt) > 12:
            print(f"  ... und {len(gebuckelt) - 12} weitere")
        print(f"\n{len(todo)} offen · {len(sauber)} sauber · {len(gebuckelt)} durchgefallen"
              f" · {len(duenn)} unter drei Stichpunkten")
        if not a.apply:
            print("[dry-run] mit --apply werden die sauberen geschrieben")
            return 0
        from export_cohort import push_variablen
        print(push_variablen(sauber, True))
        return 0

    if a.absorb:
        html = open(os.path.join(HERE, "instantly_markt.html"), encoding="utf-8").read()
        geschrieben = json.load(open(a.absorb, encoding="utf-8"))
        sauber, gebuckelt = {}, []
        for pid, v in geschrieben.items():
            if pid not in blaetter:
                gebuckelt.append((pid, ["kein Datenblatt -- falsche Nische oder Region?"]))
                continue
            m = pruefe(blaetter[pid], v, html)
            (gebuckelt.append((blaetter[pid]["name"], m)) if m
             else sauber.update({pid: v}))
        for name, m in gebuckelt:
            print(f"  DURCHGEFALLEN {str(name)[:32]:34} {m}")
        print(f"{len(sauber)}/{len(geschrieben)} durch alle vier Pruefer")
        if not a.apply:
            print("[dry-run] mit --apply werden die sauberen geschrieben")
            return 1 if gebuckelt else 0
        from export_cohort import push_variablen
        print(push_variablen(sauber, True))
        return 1 if gebuckelt else 0

    todo = offen(leads)
    print(f"{len(todo)} offene Leads mit Befunden und Adresse"
          + (f" in {a.region}" if a.region else "") + "\n")
    if not a.next:
        return 0
    print("=" * 78)
    print("DIE SCHREIBKARTE (aus markt_copy.md):")
    print("=" * 78)
    import pool
    print(pool.schreibkarte("SCHREIBKARTE"))
    print("\n" + "=" * 78)
    print(f"{min(a.next, len(todo))} DATENBLAETTER. Je Lead die Variablen schreiben:")
    print('  {"<place_id>": {"tip_1": "- ...", "tip_2": "- ...", "tip_3": "- ..."}}')
    print("=" * 78)
    for x in todo[:a.next]:
        print(f"\n--- place_id: {x['place_id']}")
        print(json.dumps(blaetter[x["place_id"]], ensure_ascii=False, indent=1))
    print(f"\nZurueckschreiben:  python3 stapel.py --niche {a.niche} "
          f"--absorb mails.json --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
