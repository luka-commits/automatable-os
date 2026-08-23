#!/usr/bin/env python3
"""export_cohort.py — THE BRIDGE: Supabase scrape-cohort -> cold-mail working set.

run_campaign scrapes+ingests into `industry_operators` (the authoritative cohort). The cold-mail
pipeline (recover_emails -> lead-cleaner -> icebreaker -> enrich -> assemble) works out of a
`runs/<slug>/` tree of CSVs. This is the step between: it pulls the GENUINE cohort for one
(niche, region) out of Supabase and writes the exact files the downstream expects.

Pulling from Supabase (not the local raw.json) is deliberate — Supabase is the single source of
truth: emails are already @-guarded, duplicates collapsed, nearest-2 computed, and it works for
ANY region already ingested (incl. ones scraped before run_campaign existed).

Writes to runs/<niche>-<region-slug>/ :
  cleaned.csv     5-col [business_name,city,website,email,first_name]  — genuine WITH a valid email
  needs_email.csv 4-col [business_name,city,website,first_name]        — genuine w/ website, NO email
                                                                          (recover_emails fills these)
  cohort_vars.csv     [business_name,website,place_id,competitor_1,competitor_2,market_count]
                                                                          — the Variant-B join data
  no_contact.csv  4-col [business_name,city,website,first_name]        — genuine w/o email AND w/o
                                                                          website (phone-only; bucketed,
                                                                          not dropped — never lose a lead)
first_name is left blank — the scrape carries none; icebreaker/casualize fills it downstream.

Usage:
  export_cohort.py --niche locksmith --region "West Yorkshire"
  export_cohort.py --niche locksmith --region "Greater London" --include-pending
"""
import json, csv, os, re, argparse, urllib.request, urllib.parse, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REF = "qhlklpweondgkswptyfc"


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', (s or '').lower()).strip('-')


def sbkey():
    for line in open(os.path.expanduser('~/.config/credentials.env')):
        if line.startswith('POCKET_DASH_SUPABASE_SERVICE_ROLE='):
            return line.split('=', 1)[1].strip().strip('"')
    sys.exit("no POCKET_DASH_SUPABASE_SERVICE_ROLE")


def valid_email(e):
    """Same guard the scrape/ingest now apply — defend the export too (older rows may predate it)."""
    e = (e or "").strip()
    if "@" not in e or "/" in e or " " in e:
        return ""
    if "mhtml.blink" in e.lower() or e.lower().startswith("frame-"):   # MHTML save-artifact, not real
        return ""
    local, _, host = e.partition("@")
    return e.lower() if local and "." in host else ""


FINDING_COLS = ['position', 'widerspruch', 'tips_intro', 'gut_satz',
                'tip_1', 'tip_2', 'tip_3', 'tip_4', 'tip_5', 'verdict_line',
                'good_1', 'good_2', 'gap_1', 'gap_2', 'gap_3', 'verdict', 'gbp_score',
                'site_score', 'score_line', 'limits_line', 'needs_deeper', 'site_finding',
                'findings_json']


def _lead_blatt(r, mk_basis, bench):
    """Das Eingabe-Dict fuer `pool.gut()` -- dieselben Felder wie `pool.aus_lead`.

    Bewusst NICHT `pool.aus_lead` selbst: das braucht den vollen `market_context` je Lead
    (Nachbarn, Kohorte, Kategorien der Bestbewerteten) und wuerde den Export von Sekunden
    auf Minuten ziehen. "What's working well" liest nur die eigenen Zahlen des Betriebs
    gegen den Landes-Benchmark -- dafuer reicht das kleine Blatt.
    """
    import pool as _pool
    return _pool.aus_lead(r, dict(mk_basis), bench)


def score_zahlen(raw, rd, bench, ueblich, blatt=None):
    """Punkte und Zahl der wirklich gemessenen Faktoren -- die eine Rechenstelle.

    Getrennt von `score_line`, damit ein Aufrufer die Zahlen auch ohne den Satz bekommt.
    """
    import gbp_score as GS
    return GS.score(GS.faktoren(
        raw, (rd or {}).get('services'), bench, ueblich,
        # die Kategorie, die die Bestbewerteten fuehren und er nicht -- steht schon im
        # Blatt, das `pool.aus_lead` gebaut hat
        kat_der_besten=(blatt or {}).get('kategorie_der_besten')))


def score_line(punkte, n_faktoren):
    """Der Satz mit dem Score. EINE Stelle, weil er sonst auseinanderlaeuft.

    Gemessen am 23.08.2026: das Vorschau-Skript baute denselben Satz ein zweites Mal nach
    und zeigte nach einer Kuerzung zwei Runden lang die ALTE Fassung -- also Mails, die so
    nie verschickt worden waeren. Wer den Satz braucht, ruft hier.
    """
    return f"you came out at {punkte}/100 across these {n_faktoren} categories:"


def findings_cols(ws, det, raw=None, rd=None, bench=None, ueblich=None, blatt=None,
                  kohorte_schnitt=None, kohorte_n=0):
    """web_signals -> die flachen Spalten, die Instantly als Variablen einsetzt.

    Leer bleibt leer. Ein Lead ohne dritten Befund bekommt gap_3 = "", nie einen
    Fuellsatz -- lieber zwei echte Stichpunkte als drei, von denen einer erfunden ist.
    """
    good, gaps = (ws.get('good') or []), (ws.get('gaps') or [])
    out = {f'good_{i}': (good[i - 1] if len(good) >= i else '') for i in (1, 2)}
    out.update({f'gap_{i}': (gaps[i - 1] if len(gaps) >= i else '') for i in (1, 2, 3)})
    # der alte site_judge-Pfad bleibt Rueckfall, solange nicht ueberall gepusht wurde
    # Die vom Schreiber gelieferten Variablen. Sie stehen in web_signals.mail und kommen
    # damit bei jedem Export automatisch wieder in die CSV, die nach Instantly geht.
    mail = ws.get('mail') or {}
    for k in ('position', 'widerspruch', 'tip_1', 'tip_2', 'tip_3', 'tip_4', 'tip_5',
              'verdict_line'):
        out[k] = mail.get(k) or ''
    # Die Bruecke vor der Liste. Sie bleibt eine VARIABLE und wird kein fester Satz in der
    # Vorlage, weil die Fliesstext-Variante gar keine Liste hat -- dann steht hier nichts,
    # statt eine Liste anzukuendigen, die nie kommt. Keine Zahl darin: die Zahl der
    # Stichpunkte schwankt (gemessen 28.07.: 5 Leads mit drei, 6 mit vier), und wer eine
    # Zahl nennt, liefert sie.
    #
    # EIN SATZ FUER ALLE, seit 22.08.2026 (Luka). Vorher haing die Bruecke am Rang
    # ("keep it that way" / "get you up there" / neutral) -- das setzte das Positions-
    # Statement in Satz 2 voraus, und genau das faellt weg, weil es widerlegbar war. Ohne
    # Positionsanspruch gibt es kein "up there" mehr, auf das sich die Bruecke beziehen
    # koennte. Der Rang-Unterschied lebt weiter, aber dort wo er gemessen ist: `pool.py`
    # waehlt fuer einen Betrieb im Drei-Kasten andere Zeilen als fuer einen ausserhalb.
    hat_tips = any(out[f'tip_{i}'].strip() for i in range(1, 6))
    out['tips_intro'] = '' if not hat_tips else (
        "what's costing you calls:")
    out['verdict'] = ws.get('verdict') or ''
    sc = ws.get('scores') or {}
    out['gbp_score'] = '' if sc.get('gbp') is None else sc['gbp']
    out['site_score'] = '' if sc.get('site') is None else sc['site']
    # DER SCORE, neu gerechnet (22.08.2026). Der alte `sc['line']` nennt zwei Zahlen --
    # "your google profile scores 60 out of 100 ... and your site 67 across 12" -- und die
    # zweite kommt aus dem Site-Read, den wir nicht mehr fahren. Sie ist bei locksmith zu
    # 74% gefuellt und bei JEDER anderen Nische zu 0%; eine Zahl, die wir fuer die naechste
    # Nische nicht wiederholen koennen, gehoert nicht in die Vorlage.
    #
    # `gbp_score` rechnet stattdessen acht Faktoren, alle aus dem GBP-Scraper und alle in
    # PIPELINE.md § 4b gelistet. Nicht gemessen faellt aus Zaehler UND Nenner.
    out['score_line'] = ''
    if raw is not None and bench is not None:
        punkte, n_faktoren = score_zahlen(raw, rd, bench, ueblich, blatt)
        if punkte is not None:
            # DER VERGLEICH, nicht nur die eigene Zahl (Luka, 22.08.: "basically scored your
            # google business profiles against each other, with you achieving xyz percent").
            #
            # Das ist nur erlaubt, WEIL wir es wirklich tun: dieselbe `gbp_score`-Funktion
            # laeuft ueber jeden Wettbewerber der Kohorte, deren Rohdaten ohnehin im Scrape
            # liegen. Waere es nur seine eigene Zahl, waere "gegeneinander" eine Behauptung.
            #
            # "the {n} i looked at" statt "alle hier": wir kennen den Ort nur ausschnittsweise
            # (Bedford 11 von 27). Der Satz sagt damit genau, was er misst -- unsere Auswahl,
            # nicht den Markt (PIPELINE.md § 4b).
            # "google business profiles", nicht nur "profiles" (Luka, 22.08.): sonst weiss
            # der Empfaenger nicht, WELCHES Profil gemeint ist -- Website, Facebook, Google?
            # Der Vergleichswert der Kohorte ist raus: er macht den Satz laenger, ohne dem
            # Empfaenger etwas zu geben, was er tun kann. Gescort wird trotzdem gegeneinander,
            # das ist der Beleg hinter dem Satz.
            # "34/100" statt "34 out of 100" (Luka, 22.08.: "hier reicht auch 34/100 across
            # the following 10 categories, dass wir nochmal ein paar woerter sparen"). Vier
            # Woerter weniger, und der Bruchstrich liest sich wie ein Messwert -- was er ist.
            # "across these" statt "across the following" (23.08.): ein Wort weniger,
            # gleiche Aussage.
            out['score_line'] = score_line(punkte, n_faktoren)

    # WHAT'S WORKING WELL -- bis zu drei Zeilen, die schon passen. 99% der Leads haben
    # mindestens zwei. Leer bleibt leer: kein Lob fuer etwas, das wir nicht gemessen haben.
    import pool as _pool
    out['gut_satz'] = _pool.gut_satz(_pool.gut(blatt)) if blatt else ''

    out['limits_line'] = sc.get('limits') or ''
    out['needs_deeper'] = '1' if sc.get('deeper') else ''
    out['site_finding'] = ws.get('site_finding') or det.get('site_finding') or ''
    out['findings_json'] = json.dumps(ws.get('findings') or [], ensure_ascii=False)
    return out


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from casualize import casual_brand, is_town_fragment  # noqa: E402


def competitor(nearest, i, niche, city, towns=frozenset(), lead_name=''):
    """Konkurrent fuer die Mail: casualisiert, aber nie auf einen Ortsnamen eingedampft.

    "The Bedford Locksmith" wurde zu "bedford", und die Mail behauptete dann
    "your two closest competitors, timpson and bedford" -- eine Stadt als Konkurrent.
    Der erste Anlauf pruefte nur gegen den Ort des LEADS, und der hiess St. Neots, also
    ging "bedford" glatt durch. Geprueft wird deshalb gegen alle Orte der Kohorte: ein
    Konkurrenzname, der auf irgendeinen davon zusammenfaellt, ist keiner mehr.

    DREI WEITERE FEHLER, gemessen am 22.08.2026 ueber 5.488 Konkurrenznamen:

      SELBSTREFERENZ (58) -- "i scored your profile against highfield mot, LOCKWISE and a few
        other locksmiths" bei einem Lead namens LockWise Group. Eine Kettenfiliale, die der
        Filter nicht erkannt hat. Die Mail nennt ihm seinen eigenen Namen als Konkurrenten;
        damit ist sie verbrannt, und zwar in der ersten Zeile.
      DOMAIN STATT NAME (8) -- "keyrecovery.co.uk". Niemand nennt seinen Nachbarn mit
        Top-Level-Domain.
      ABGESCHNITTEN -- "wallasey have" aus einem laengeren Namen: der Rest eines Titels, der
        nach dem Strippen von Gewerk und Ort uebrigblieb, ohne fuer sich zu stehen.

    Abkuerzungen bleiben: "ABH", "RJ", "ASG" sind echte Firmennamen und lesen sich richtig.
    """
    if len(nearest) <= i:
        return ''
    full = nearest[i]['name'] or ''
    # SELBSTREFERENZ zuerst: lieber gar kein Name als der eigene.
    if lead_name and _ist_derselbe(full, lead_name):
        return ''
    short = casual_brand(full, niche, city)
    if not short or is_town_fragment(short, city) or slug(short) in towns:
        short = full
    # Domain-Endung raus: "keyrecovery.co.uk" -> "keyrecovery"
    short = re.sub(r"\.(co\.uk|com|net|org|uk|de|io|shop)\b", "", short, flags=re.I).strip(" .,-")
    # Ein Rest wie "wallasey have" steht nicht fuer sich -- dann lieber der volle Titel.
    if short.lower().split()[-1:] in (["have"], ["and"], ["the"], ["of"], ["for"]):
        short = full
    short = short.strip(" .,-")

    # NOCHMAL gegen den Lead pruefen, jetzt auf dem GEKUERZTEN Namen. Die Kollision entsteht
    # oft erst hier: "Finsbury Park Locksmiths Ltd" und "LockTitan Locksmith Finsbury Park"
    # sind zwei Betriebe, aber casualisiert heisst der eine "Finsbury Park" -- und das steckt
    # im Namen des anderen. Der Empfaenger liest seinen eigenen Ortsteil als Konkurrenten.
    if lead_name and _ist_derselbe(short, lead_name):
        return ''
    # Ein einzelner Buchstabe ist kein Name ("K", "H", "M" -- Reste nach dem Strippen).
    if len(re.sub(r"[^a-z0-9]", "", short.lower())) < 2:
        return full.strip(" .,-")
    # Rein generische Reste sagen nichts ueber einen bestimmten Betrieb.
    if short.lower() in ("locksmith services", "locksmiths", "locksmith", "security",
                         "services", "locks"):
        return full.strip(" .,-")
    return short


def _ist_derselbe(a: str, b: str) -> bool:
    """Sind das derselbe Betrieb? Grosszuegig geprueft, weil ein Treffer teuer ist.

    Der Kettenfilter arbeitet ueber place_ids und erkennt eine zweite Filiale nicht, die
    unter leicht anderem Namen laeuft. Hier zaehlt die Namensform: wenn der kurze Name im
    langen steckt (ohne Rechtsform und Gewerksworte), ist es derselbe.
    """
    def kern(x):
        x = re.sub(r"\b(ltd|limited|group|services?|co|company|the)\b", " ", (x or "").lower())
        return re.sub(r"[^a-z0-9]+", " ", x).strip()
    ka, kb = kern(a), kern(b)
    if not ka or not kb:
        return False
    return ka == kb or (len(ka) >= 5 and ka in kb) or (len(kb) >= 5 and kb in ka)


def competitors_phrase(c1, c2):
    """Die Namen fuer den Einstieg: "auto keys, gold" -- oder einer, oder keiner.

    Frueher stand "your two closest competitors, auto keys and gold," davor. Luka hat den
    Rahmen am 27.07. vereinfacht: "i just looked at name1, name2 and the other x locksmiths
    in bedford". Die Namen stehen jetzt fuer sich; der Leser erkennt sie ohnehin, es sind
    seine Nachbarn.

    Der Kettenfilter entfernt Filialen aus der Kohorte, und damit faellt bei manchen Leads
    der zweite Name weg. Zwei Felder blind in eine feste Formulierung zu setzen erzeugte
    "gold and ,". Der Satzteil wird deshalb hier gebaut, wo bekannt ist, wie viele Namen
    es wirklich gibt.
    """
    c1, c2 = (c1 or '').strip(), (c2 or '').strip()
    if c1 and c2:
        return f"{c1.lower()}, {c2.lower()}"
    if c1:
        return c1.lower()
    return ''


def intro(phrase, others, niche, area, company):
    """Der ganze Grund-Satz. Ohne Namen faellt der Namensteil weg statt leer dazustehen."""
    wer = f"{phrase} and the other {others} {niche}s" if phrase else f"the {others} {niche}s"
    return (f"i just looked at {wer} in {area}, and how they compare to {company}. "
            f"here are some insights you might find interesting.")


def opener(phrase, niche, area):
    """Satz 1 der Mail, KOMPLETT aus Python -- der Agent formuliert ihn nicht mehr.

    Der Anlass (Luka, 22.08.2026): das Positions-Statement ("du stehst nicht in den top 3")
    faellt weg, weil es widerlegbar ist -- gemessen am 30.07. standen vier von vier Betrieben
    an ihrer eigenen Tuer im Drei-Kasten. Damit bleibt von Satz 1 nur noch der Beleg uebrig,
    dass wir bei IHM nachgesehen haben, und der ist reine Datenausgabe.

    Zwei Regeln, beide aus markt_copy.md uebernommen und hier hart verdrahtet:
      KEINE ZAHL   "and the other 7 locksmiths in reading" behauptet mehr, als wir wissen
                   (Reading: 10 von uns erfasst, Google zeigt mehr). "a few other" behauptet
                   nichts und ist trotzdem wahr.
      ORT MUSS REIN Ohne ihn faellt der Beleg weg, dass wir bei ihm und nicht irgendwo
                   nachgesehen haben (Luka, 30.07.: "hier fehlt jetzt der ganze ortsname").
    """
    # Das Nischenwort raus, wenn der Nachbar es im Namen traegt: "abbey gate locksmiths and a
    # few other locksmiths in reading" sagt es zweimal in acht Woertern. Nur am Namensende
    # (auch hinter Bindestrich, "anytime-locksmiths"), damit "locksmith king" heil bleibt.
    if phrase:
        phrase = re.sub(rf"[\s-]{re.escape(niche)}s?\b", "", phrase, flags=re.I).strip(" ,-")
    # KURZ (Luka, 22.08.: "die sektion muessen wir noch etwas kuerzer kriegen"). Vorher
    # standen hier drei Saetze -- "i just checked out X. i scored the profiles against each
    # other and yours came out at N. here's the breakdown across M categories:" -- rund 40
    # Woerter, bevor der erste Befund kommt. Jetzt zwei: was verglichen wurde und mit wem,
    # dann das Ergebnis. Der Bericht-Charakter bleibt ("i scored"), der Anlauf faellt weg.
    # Der Ort als Adjektiv, nicht als Praepositionalphrase (23.08.): "a few other
    # lancashire locksmiths" statt "a few other locksmiths in lancashire" -- ein Wort
    # weniger und es liest sich wie gesprochen.
    wer = (f"{phrase} and a few other {area} {niche}s" if phrase
           else f"the other {niche}s in {area}")
    return f"i scored your google business profile against {wer}."


def opener_gebiet(town: str, region: str) -> str:
    """Welches Gebiet Satz 1 nennt: der ORT, wenn wir einen haben, sonst die Grafschaft.

    Der Anlass (22.08.2026, beim Lesen von zwanzig fertigen Mails): der Opener nahm immer
    `--region`, also die Grafschaft. Legend Locksmiths sitzt in Barnet, die Mail sagte
    "a few other of your competitors in greater london" -- dort sitzen Hunderte, und damit
    ist der Satz keine ueberpruefbare Aussage mehr, sondern eine Floskel. Genau der Fehler,
    den `fact_sheet.ortswahl` fuer den Messpunkt laengst behebt.

    Gemessen ueber die 2.744 anschreibbaren Leads: **68% tragen einen echten Ort**, bei nur
    3% ist er mit der Region identisch. Die restlichen 32% sind Service-Area-Betriebe ohne
    Adresse -- dort ist die Grafschaft der ehrliche Ersatz, denn einen Ort gibt es nicht.
    """
    return ((town or "").strip() or (region or "").strip()).lower()


def subject(area, niche, c1, market_count, lead_casual=''):
    """Der Betreff. Bisher trug ihn jede Mail einer Region gleich: `{area} {niche}s, all {n}`.

    Gemessen am 28.07. ueber alle 61 exportierten Regionen (4.273 Leads): das sind **62
    verschiedene Betreffzeilen fuer 4.273 Mails**, und in Greater London allein 844 mal
    dieselbe. Der naechste Konkurrent ist je Lead ein anderer und macht daraus 2.612
    verschiedene, schlimmster Fall 31 statt 844.

    Er bleibt eine Marktaussage, kein Pitch -- derselbe Nachbar, den der Einstiegssatz
    ohnehin namentlich nennt, steht nur schon im Betreff. Ohne Nachbarn (Kettenfilter,
    einziger Betrieb der Region) faellt er auf "your google listing" zurueck.

    Die Notloesung war bis 30.07. `{base}, all {n}` -- also die Kohorten-Zahl als Aussage
    ueber den ganzen Ort, im Betreff, wo sie zuerst gelesen wird. Wir kennen den Ort aber
    nur ausschnittsweise (Bedford 11 von 27, Hornchurch 1 von 20), also faellt sie hier
    genauso weg wie im Text. `market_count` bleibt als Spalte im Export, damit die alte
    Variante B lesbar bleibt -- in den Betreff kommt sie nicht mehr.
    """
    # REIHENFOLGE: Wettbewerber, Lead, Gebiet (23.08.2026, Luka woertlich: "den competitor
    # an den anfang packen, dann den namen des lead business und dann die area dahinter").
    # Der Grund, warum das besser traegt als die alte Fassung: im Postfach steht links der
    # Absender, den er nicht kennt. Das erste Wort des Betreffs muss also etwas sein, das
    # er kennt -- und das ist der Nachbar von nebenan, nicht seine Grafschaft.
    # Der eigene Name daneben sagt in drei Woertern, worum es geht: um die beiden im
    # Vergleich. Das Gebiet haengt hinten als Rahmen.
    #
    # Ohne Wettbewerber (Kettenfilter raeumte die Region leer) faellt er auf Lead plus
    # Gebiet zurueck, nie auf eine Zahl ueber den Ort -- den kennen wir nur ausschnittsweise.
    lead = (lead_casual or '').strip().lower()
    c1 = (c1 or '').strip().lower()
    gebiet = (area or '').lower()
    if c1 and lead:
        return f"{c1}, {lead} and {gebiet} {niche}s"
    if c1:
        return f"{c1}, you and {gebiet} {niche}s"
    if lead:
        return f"{lead} and the rest of {gebiet}"
    return f"{gebiet} {niche}s, your google listing"


VARIABLEN_SPALTEN = ["tips_intro", "gut_satz", "tip_1", "tip_2", "tip_3", "tip_4",
                     "tip_5", "score_line", "opener", "subject", "company_casual"]
FERTIG_SPALTE = "tip_1"   # woran ein Lead als geschrieben erkannt wird


def push_variablen(mails: dict, apply: bool) -> str:
    """Die geschriebenen Variablen nach industry_operators.web_signals.mail.

    Herausgeloest aus `batch_briefs.py` am 23.08.2026: `stapel` brauchte aus jener
    Datei genau diese eine Funktion und zog damit den ganzen Sonnet-Weg mit, der seit
    dem 22.08. nicht mehr laeuft. Hier gehoert sie ohnehin hin -- dies ist die Datei,
    die zwischen Supabase und der Kampagne vermittelt.

    Damit ueberleben sie den naechsten export_cohort, der cohort_vars.csv komplett neu aus
    Supabase baut. Genau daran waeren heute frueh schon die Findings gestorben.
    """
    import urllib.parse, urllib.request
    from dedupe_leads import _supabase
    url, key = _supabase()
    hdr = {"apikey": key, "Authorization": f"Bearer {key}"}
    echte = {k: v for k, v in mails.items()
             if isinstance(v, dict) and (v.get(FERTIG_SPALTE) or "").strip()}
    if not apply:
        return f"[dry-run] {len(echte)} Zeilen wuerden geschrieben"
    for pid, v in echte.items():
        q = (f"{url}/rest/v1/industry_operators?"
             f"place_id=eq.{urllib.parse.quote(pid, safe='')}")
        cur = json.load(urllib.request.urlopen(
            urllib.request.Request(q + "&select=web_signals", headers=hdr), timeout=30))
        if not cur:
            continue
        ws = cur[0].get("web_signals") or {}
        ws["mail"] = {k: (v.get(k) or "").strip() for k in VARIABLEN_SPALTEN}
        req = urllib.request.Request(q, data=json.dumps({"web_signals": ws}).encode(),
                                     method="PATCH",
                                     headers={**hdr, "Content-Type": "application/json",
                                              "Prefer": "return=minimal"})
        urllib.request.urlopen(req, timeout=30).read()
    return f"{len(echte)} Zeilen geschrieben"


def fetch_cohort(niche, region):
    key = sbkey()
    out, off, step = [], 0, 1000
    # `raw` und `raw_dataforseo` MUESSEN mit (22.08.2026): der Score und "what's working
    # well" rechnen aus den Scrape-Feldern, nicht aus `web_signals`. Ohne sie kamen beide
    # Spalten leer aus dem Export -- und zwar lautlos, weil ein fehlendes Feld in Python
    # `None` ist und `faktoren()` daraus korrekt "nicht gemessen" macht. Der Score sagte
    # dann "0 von 8 Faktoren gemessen" und schwieg, statt zu melden, dass die Daten in der
    # Abfrage fehlen.
    sel = ('place_id,name,town,region,website,email,details,web_signals,'
           'raw,raw_dataforseo')
    while True:
        # Was dedupe_leads als Dublette oder Kettenfiliale markiert hat, verlaesst die Datenbank
        # nie wieder Richtung Mail. Ohne diese Zeile war Timpson 3 von 15 Leads in Bedford, und
        # zwei von drei Mails nannten eine Kette als "deinen engsten Konkurrenten".
        q = urllib.parse.urlencode({'select': sel, 'niche': f'eq.{niche}', 'region': f'eq.{region}',
                                    'pipeline_status': 'neq.disqualified'})
        req = urllib.request.Request(f"https://{REF}.supabase.co/rest/v1/industry_operators?{q}",
                                     headers={'apikey': key, 'Authorization': f'Bearer {key}',
                                              'Range-Unit': 'items', 'Range': f'{off}-{off+step-1}'})
        rows = json.load(urllib.request.urlopen(req, timeout=60))
        out += rows
        if len(rows) < step:
            break
        off += step
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--niche', required=True)
    ap.add_argument('--region', required=True)
    ap.add_argument('--include-pending', action='store_true',
                    help="also export tier='pending' (default: genuine only — pending awaits site-read)")
    ap.add_argument('--out-root', default=f"{HERE}/runs")
    a = ap.parse_args()

    rows = fetch_cohort(a.niche, a.region)
    if not rows:
        sys.exit(f"[export] no rows for niche={a.niche!r} region={a.region!r} — ingested yet?")

    tiers = ('genuine', 'pending') if a.include_pending else ('genuine',)
    cohort = [r for r in rows if (r.get('details') or {}).get('tier') in tiers]
    market_count = sum(1 for r in rows if (r.get('details') or {}).get('tier') == 'genuine')
    # competitors are only drawn from CURRENTLY-genuine leads — so a fake demoted by the site-read
    # (tier='not_niche') drops out of the cohort_vars competitor slots, not just the email list.
    genuine_pids = {r['place_id'] for r in rows if (r.get('details') or {}).get('tier') == 'genuine'}

    rundir = os.path.join(a.out_root, f"{slug(a.niche)}-{slug(a.region)}")
    os.makedirs(rundir, exist_ok=True)

    # alle Orte der Kohorte plus die Region -- dagegen wird jeder Konkurrenzname geprueft
    towns = {slug(t) for t in ([a.region] + [r.get('town') for r in rows]) if t}

    # Fuer Score und "what's working well": der Landes-Benchmark, die uebliche
    # Hauptkategorie der Kohorte und je Lead das Datenblatt.
    import benchmark as _bm, fact_sheet as _fs, collections as _c
    bench = _bm.load(a.niche)
    _prim = _c.Counter((r.get('raw') or {}).get('categories', [None])[0]
                       for r in rows if (r.get('raw') or {}).get('categories'))
    ueblich = _prim.most_common(1)[0][0] if _prim else None
    _mk_basis = {'photos_median': bench.get('photos_median') or 14, 'count': len(cohort)}

    # DIE SCORES DER GANZEN KOHORTE, einmal je Region gerechnet. Damit ist "i scored the
    # profiles against each other" keine Floskel: dieselbe Funktion laeuft ueber jeden
    # Wettbewerber, dessen Rohdaten ohnehin im Scrape liegen. Kostet nichts -- es ist
    # Arithmetik auf Daten, die schon da sind.
    import gbp_score as _gs
    _alle_scores = {}
    for _r in cohort:
        _p, _ = _gs.score(_gs.faktoren(_r.get('raw') or {},
                                       (_r.get('raw_dataforseo') or {}).get('services'),
                                       bench, ueblich))
        if _p is not None:
            _alle_scores[_r['place_id']] = _p

    _pos = {r['place_id']: ((r.get('raw') or {}).get('location') or {}) for r in cohort}

    def _kohorte_ohne(pid, wie_viele=10):
        """Schnitt und Anzahl der NAECHSTEN Wettbewerber -- nicht der ganzen Grafschaft.

        Der Opener nennt den ORT ("in belper"), also muss der Score gegen dieselbe
        Nachbarschaft rechnen. Erst stand hier die ganze Region: die Mail sagte "in belper"
        und zwei Saetze weiter "gegen die 50, die ich mir angesehen habe" -- Derbyshire hat
        50 Betriebe, Belper nicht. Zwei Zahlen ueber zwei verschiedene Gebiete im selben
        Absatz, und der Empfaenger merkt es beim ersten Lesen.

        Zehn, weil `nearest_cohort` in `build_lead_findings` dieselbe Zahl nimmt: immer
        definiert, Median 6,5 km zum zehnten. Ohne Koordinaten faellt der Lead auf die
        Region zurueck -- dann steht die groessere Zahl da, aber sie stimmt auch.
        """
        me = _pos.get(pid) or {}
        if me.get('lat') is not None:
            weit = []
            for k, p in _pos.items():
                if k == pid or p.get('lat') is None:
                    continue
                d = ((p['lat'] - me['lat']) ** 2 + (p['lng'] - me['lng']) ** 2) ** 0.5
                if k in _alle_scores:
                    weit.append((d, _alle_scores[k]))
            weit.sort(key=lambda x: x[0])
            andere = [v for _, v in weit[:wie_viele]]
        else:
            andere = [v for k, v in _alle_scores.items() if k != pid]
        return (round(sum(andere) / len(andere)), len(andere)) if andere else (None, 0)

    cleaned, needs, no_contact, cvars = [], [], [], []
    for r in cohort:
        name = r.get('name') or ''
        # 1.798 von 4.277 Schluesseldiensten haben KEINE Adresse -- Service-Area-Betriebe,
        # bei denen Google Strasse und Ort ausblendet (raw.city/street/address alle leer).
        # Der Ort ist also nicht verloren gegangen, es gibt ihn nicht. Die Suchregion ist
        # der ehrliche Ersatz: dort arbeiten sie, und ohne sie bleibt jede Anrede ortlos.
        city = r.get('town') or r.get('region') or ''
        # Der Stadtteil aus dem Scrape (23.08.2026). Er steht in KEINER unserer Spalten --
        # `town` traegt bei einem Betrieb in Pimlico "London" -- und ohne ihn bleibt der
        # Ortsteil in der Anrede stehen ("hey citysentry locksmith pimlico").
        hood = ((r.get('raw') or {}).get('neighborhood') or '')
        site = r.get('website') or ''
        email = valid_email(r.get('email'))
        # owner first name from the site-read (cached in details.first_name) flows to the greeting;
        # empty until a site-read found a real human name on the homepage.
        owner = ((r.get('details') or {}).get('first_name') or '').strip()
        base = {'business_name': name, 'city': city, 'website': site, 'first_name': owner}
        if email:
            cleaned.append({**base, 'email': email})
        elif site:
            needs.append(base)
        else:
            no_contact.append(base)
        det = r.get('details') or {}
        nearest = [n for n in (det.get('nearest') or []) if n.get('place_id') in genuine_pids]
        cvars.append({'business_name': name, 'website': site, 'place_id': r.get('place_id') or '',
                      # auch die Konkurrenten casualisiert -- sie stehen im selben Satz wie der
                      # Lead, und "Velokey - Auto Locksmith" mitten in einer Zeile, die sonst
                      # klingt wie getippt, ist genau der Datenbank-Auszug aus Regel 7.
                      'intro': intro(
                          competitors_phrase(competitor(nearest, 0, a.niche, city, towns, name),
                                             competitor(nearest, 1, a.niche, city, towns, name)),
                          max(market_count - 3, 0), a.niche, a.region.lower(),
                          (casual_brand(name, a.niche, city, hood) or name).lower()),
                      'opener': opener(
                          competitors_phrase(competitor(nearest, 0, a.niche, city, towns, name),
                                             competitor(nearest, 1, a.niche, city, towns, name)),
                          # der ORT, nicht die Grafschaft -- siehe `opener_gebiet`
                          a.niche, opener_gebiet(r.get('town'), a.region)),
                      # Fuer den Abschluss-Absatz ("i do local seo for locksmiths"). Steht als
                      # Variable und nicht fest in der Vorlage, weil sonst bei der naechsten
                      # Nische eine Zielgruppe in der Mail steht, zu der der Empfaenger nicht
                      # gehoert -- derselbe Fehler, den die alte Fassung mit "emergency trades"
                      # eingebaut hatte.
                      'niche_plural': f"{a.niche}s",
                      'subject': subject(a.region, a.niche,
                                         competitor(nearest, 0, a.niche, city, towns, name),
                                         market_count,
                                         casual_brand(name, a.niche, city, hood) or ''),
                      'competitor_1': competitor(nearest, 0, a.niche, city, towns, name),
                      'competitor_2': competitor(nearest, 1, a.niche, city, towns, name),
                      # Fertiger Satzteil statt zweier Felder. Nach dem Kettenfilter fiel
                      # mancher zweitnaechste Betrieb weg, und die Mail las sich
                      # "your two closest competitors, gold and ," -- ein Komma ins Leere.
                      'competitors_phrase': competitors_phrase(
                          competitor(nearest, 0, a.niche, city, towns, name),
                          competitor(nearest, 1, a.niche, city, towns, name)),
                      'competitor_1_km': (round(nearest[0]['km'], 1) if len(nearest) > 0 else ''),
                      'competitor_2_km': (round(nearest[1]['km'], 1) if len(nearest) > 1 else ''),
                      'market_count': market_count,
                      # Regel 6 in markt_copy.md: der Leser kann nachzaehlen. others_count laesst
                      # den Lead selbst und die zwei namentlich genannten weg, market_count_minus_1
                      # zaehlt die zwei wieder mit. Zwei verschiedene Zahlen im selben Text.
                      'others_count': max(market_count - 3, 0),
                      'market_count_minus_1': max(market_count - 1, 0),
                      # site-finding arm (B2): populated once site_judge has run + write patched details
                      'service': det.get('service') or '',
                      # Findings kommen aus web_signals, geschrieben von enrich_cohort_findings --push.
                      # Nur so ueberlebt die Personalisierung diesen Export hier -- vorher stand sie
                      # allein in der CSV und wurde bei jedem Lauf ueberschrieben.
                      **findings_cols(r.get('web_signals') or {}, det,
                                      raw=r.get('raw') or {},
                                      rd=r.get('raw_dataforseo') or {},
                                      bench=bench, ueblich=ueblich,
                                      blatt=_lead_blatt(r, _mk_basis, bench),
                                      **dict(zip(('kohorte_schnitt', 'kohorte_n'),
                                                 _kohorte_ohne(r.get('place_id'))))),
                      # fertig casualisiert, damit die Anrede in Instantly nur noch eingesetzt wird
                      # und niemand dort "Vehicle Locksmith Solutions LTD" liest.
                      # klein, weil die Anrede damit fertig ist: in Instantly steht
                      # `hey {{company_casual}},` und dort laesst sich nichts mehr rechnen.
                      # Block 2 in markt_copy.md ist `hey gold,`, und eine grosse Anrede
                      # ueber einer durchgehend kleingeschriebenen Mail ist genau der Bruch,
                      # der nach Serienbrief aussieht. batch_briefs und intro lowern ohnehin.
                      'company_casual': (casual_brand(name, a.niche, city, hood) or '').lower(),
                      'town_casual': city,
                      # `area` ist der Bereich, den wir WIRKLICH gezaehlt haben, und nur der darf
                      # neben market_count stehen. Vorher stand dort der Ort des Leads: ein
                      # Betrieb in St. Neots las "st. neots locksmiths, all 15", wo die 15 die
                      # Region Bedford sind. Er zaehlt in seiner Stadt nach und findet sie nicht.
                      'area': a.region,
                      'town_mismatch': '1' if city and slug(city) != slug(a.region) else ''})

    def dump(fn, rows, cols):
        with open(os.path.join(rundir, fn), 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)

    dump('cleaned.csv', cleaned, ['business_name', 'city', 'website', 'email', 'first_name'])
    dump('needs_email.csv', needs, ['business_name', 'city', 'website', 'first_name'])
    # ── Der letzte Meter: die Datei, die WIRKLICH nach Instantly geht ──────────────────
    # Bis zum 22.08. gab es sie nicht, und das war die Luecke, an der die Kampagne haengen
    # blieb: `cohort_vars.csv` traegt die Variablen und KEINE Mailadresse, `cleaned.csv` die
    # Adresse und KEINE Variablen. Beide von Hand zu joinen ist genau die Stelle, an der ein
    # Versand die falsche Mail an die falsche Adresse schickt.
    #
    # Drin ist nur, was heute versandfaehig IST -- Adresse UND geschriebene Stichpunkte. Ein
    # Lead ohne `tip_1` wuerde in Instantly eine Mail mit einem Loch erzeugen, wo die Liste
    # steht. Die Spalten sind genau die sechs Variablen der Vorlage plus die Kern-Felder,
    # nichts weiter: jede Spalte mehr ist eine, die jemand versehentlich in die Copy zieht.
    VORLAGE_VARS = ['subject', 'company_casual', 'opener', 'score_line',
                    'gut_satz', 'tips_intro',
                    'tip_1', 'tip_2', 'tip_3', 'tip_4', 'tip_5', 'niche_plural']
    mail_by_pid = {r['place_id']: valid_email(r.get('email')) for r in cohort}
    instantly = [{'email': mail_by_pid.get(v['place_id'], ''),
                  'business_name': v['business_name'], 'website': v['website'],
                  **{k: v.get(k, '') for k in VORLAGE_VARS}}
                 for v in cvars
                 if mail_by_pid.get(v['place_id']) and (v.get('tip_1') or '').strip()]
    dump('instantly.csv', instantly,
         ['email', 'business_name', 'website'] + VORLAGE_VARS)

    dump('cohort_vars.csv', cvars, ['business_name', 'website', 'place_id', 'subject',
                                    'competitor_1', 'competitor_2',
                                    'competitor_1_km', 'competitor_2_km', 'market_count', 'others_count', 'market_count_minus_1', 'service',
                                    'company_casual', 'town_casual', 'area', 'town_mismatch',
                                    'competitors_phrase', 'intro', 'opener',
                                    'niche_plural'] + FINDING_COLS)
    if no_contact:
        dump('no_contact.csv', no_contact, ['business_name', 'city', 'website', 'first_name'])

    print(f"[export] {a.niche} / {a.region}  ->  {rundir}")
    print(f"  cohort: {len(cohort)} ({'+pending' if a.include_pending else 'genuine only'}) · market_count={market_count}")
    print(f"  cleaned.csv     {len(cleaned):4}  (have a valid email)")
    print(f"  needs_email.csv {len(needs):4}  (website, no email -> recover_emails)")
    print(f"  no_contact.csv  {len(no_contact):4}  (phone-only, bucketed)")
    print(f"  cohort_vars.csv {len(cvars):4}  (competitor_1/2 + market_count for Variant B)")
    print(f"  instantly.csv   {len(instantly):4}  <- VERSANDFERTIG (Adresse + geschriebene Mail)")
    ohne_mail = sum(1 for v in cvars if not (v.get('tip_1') or '').strip())
    if ohne_mail:
        print(f"     {ohne_mail} Leads warten noch auf ihre Stichpunkte (stapel.py --next)")
    print(f"\nNEXT: python3 recover_emails.py --needs {rundir}/needs_email.csv --out {rundir}/cleaned.csv")


if __name__ == '__main__':
    main()
