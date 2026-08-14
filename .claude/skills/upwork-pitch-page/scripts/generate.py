#!/usr/bin/env python3
"""Fuellt das universelle Pitch-Seiten-Template mit Job-Daten, einem bereits
exportierten Diagramm-Bild und den echten Upwork-Testimonials. Reiner
Zusammenbau -- das Diagramm selbst (Figma MCP) und alle Texte (Claude, aus dem
Job-Posting) entstehen davor im Chat, nicht hier.

Page order:
Headline -> Video (voll breit) -> 3 Eignungspunkte darunter (custom Icon statt
1/2/3) -> Social Proof (echte Testimonial-Texte) -> ausklappbarer CV -> Was ich
bauen wuerde (Diagramm) -> Wie es ablaufen wuerde (Tools/Timeline/Budget/
Kickoff-Bedarf, 4 Spalten mit Icons) -> "See what we can do" (Lead-Magnet mit
Cover-Screenshot eines echten Beispiel-Reports) -> Footer-Links. Kein Foto mehr
(deliberately removed). Testimonials, report cover and lead magnet are
echte Assets -- nie erfinden. Fehlt der Lead-Magnet, bleibt die Sektion ehrlich
platzhaltert statt mit erfundenem Inhalt aufgefuellt zu werden.

Usage:
    python3 generate.py <job_id> \
        --hook "..." --subhead "..." \
        --fit-point "Grund 1" --fit-point "Grund 2" --fit-point "Grund 3" \
        --diagram-png /pfad/zum/export.png \
        --loom-url "https://loom.com/share/..." \
        --tool "GoHighLevel" --tool "n8n" \
        --timeline "..." \
        --budget "..." \
        --kickoff "..." --kickoff "..." \
        [--lead-magnet-url "https://..." --lead-magnet-teaser "..." --lead-magnet-cta "..."] \
        [--video-length "3 minute"] \
        [--max-testimonials 8] \
        [--out /pfad/zur/ausgabe.html]

Ohne --out wird der Dateiname aus dem Job-Titel abgeleitet und nach
jobs/<YYYY-MM-DD>_<slug>.html geschrieben.

Exit 1 bei fehlendem Job, ungueltigem PNG-Pfad oder leeren Pflichtfeldern -- ein
stilles Halb-Ergebnis waere schlimmer als ein Abbruch mit Grund.
"""
import argparse, base64, datetime, json, pathlib, re, sys

W = pathlib.Path(__file__).resolve().parents[4]
JOBS = W / 'context/.upwork_jobs.json'
ASSETS = pathlib.Path(__file__).resolve().parent.parent / 'assets'
CONTEXT = W / 'context'
TEMPLATE = ASSETS / 'template.html'
TESTIMONIALS_FILE = CONTEXT / 'testimonials.json'
REPORT_COVER_FILE = ASSETS / 'report-cover-example.jpg'
VIDEOS_FILE = ASSETS / 'videos.json'
DIAGRAM_JS_FILE = ASSETS / 'diagram.js'
LOGO_DIR = ASSETS / 'logos'
# Jeder erzeugte Graph landet hier. Eine Bibliothek, die von Hand gepflegt
# werden muss, bleibt leer -- also fuellt sie sich als Nebenprodukt jedes Laufs.
LIBRARY = pathlib.Path(__file__).resolve().parent.parent / 'library'
# Source image for the hero dither. Do not swap it for another picture without
# retuning the constants in the template -- they are set against this drawing.
DITHER_FILE = ASSETS / 'ink-plume.png'
OUT_DIR = W / 'jobs'

YT_PLAY = (
    '<svg viewBox="0 0 28 20" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    '<path fill="#FF0000" d="M27.4 3.1A3.51 3.51 0 0 0 24.9.6C22.7 0 14 0 14 0S5.3 0 3.1.6'
    'A3.51 3.51 0 0 0 .6 3.1C0 5.3 0 10 0 10s0 4.7.6 6.9a3.51 3.51 0 0 0 2.5 2.5C5.3 20 14 20 14 20'
    's8.7 0 10.9-.6a3.51 3.51 0 0 0 2.5-2.5C28 14.7 28 10 28 10s0-4.7-.6-6.9z"/>'
    '<path fill="#ffffff" d="M11.2 14.29 18.5 10l-7.3-4.29z"/></svg>'
)

FIT_ICON = (
    '<svg class="icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<circle cx="12" cy="12" r="12"/>'
    '<path d="M7 12.5L10.5 16L17 8.5" stroke="white" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round"/></svg>'
)


def slugify(title):
    s = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    return s[:60]


def load_job(job_id):
    if not JOBS.is_file():
        print(f'ABBRUCH: {JOBS} fehlt.', file=sys.stderr)
        sys.exit(1)
    jobs = json.loads(JOBS.read_text(encoding='utf-8'))
    for j in jobs:
        if j.get('id') == job_id:
            return j
    print(f'ABBRUCH: job_id "{job_id}" nicht in {JOBS} gefunden.', file=sys.stderr)
    sys.exit(1)


def img_data_uri(path_str, mime='image/png'):
    p = pathlib.Path(path_str)
    if not p.is_file():
        print(f'ABBRUCH: Bild "{p}" existiert nicht.', file=sys.stderr)
        sys.exit(1)
    b64 = base64.b64encode(p.read_bytes()).decode('ascii')
    return f'data:{mime};base64,{b64}', len(b64)


def _cfg_str(key):
    """One quoted value out of context/config.yaml, or ''. Same tiny reader as the
    dashboard renderer: this repo stays dependency-free on purpose."""
    cfg = CONTEXT / 'config.yaml'
    if not cfg.is_file():
        return ''
    m = re.search(rf'^\s*{key}:\s*"([^"]*)"', cfg.read_text(encoding='utf-8'), re.M)
    return m.group(1).strip() if m else ''


def optional_links():
    """The three links that are the freelancer's own, not the system's.

    Every one is optional and every one disappears cleanly when unset. A pitch
    page that ships with a dead "See the whole channel" link is worse than one
    with no link at all, because the client clicks it.
    """
    portfolio, youtube, website = (_cfg_str('portfolio_url'),
                                   _cfg_str('youtube_url'),
                                   _cfg_str('website_url'))
    proof = (f'<a class="proof-link" href="{portfolio}" target="_blank" rel="noopener">'
             f'See more of my work <span class="arrow" aria-hidden="true">→</span></a>'
             if portfolio else '')
    yt_more = (f'<a class="yt-more" href="{youtube}" target="_blank" rel="noopener" data-rise>'
               f'See the whole channel <span class="arrow" aria-hidden="true">→</span></a>'
               if youtube else '')
    foot = []
    if youtube:
        foot.append(f'<a href="{youtube}" target="_blank" rel="noopener">YouTube</a>')
    if website:
        host = re.sub(r'^https?://(www\.)?', '', website).rstrip('/')
        foot.append(f'<a href="{website}" target="_blank" rel="noopener">{host}</a>')
    footer = ''.join('<span class="dot">·</span>' + f for f in foot)
    return proof, yt_more, footer


def cv_stats_html():
    """The track-record row under "More about my background".

    Numbers come from `context/config.yaml` under `upwork.profile`, which the
    screener refreshes from the account on every run. Nothing is invented and
    nothing is hardcoded: a freelancer with no earnings yet gets no stats row
    rather than a row of zeros, because an empty block reads as new while a
    zero reads as failed.
    """
    cfg = CONTEXT / 'config.yaml'
    if not cfg.is_file():
        return ''
    txt = cfg.read_text(encoding='utf-8')

    def num(key):
        m = re.search(rf'^\s*{key}:\s*([\d.]+)', txt, re.M)
        return m.group(1) if m else None

    rows = [
        (f'${round(float(num("lifetime_earnings")) / 1000)}K+', 'Earned on Upwork')
        if num('lifetime_earnings') and float(num('lifetime_earnings')) >= 1000 else None,
        (num('jobs_completed'), 'Projects delivered') if num('jobs_completed') else None,
        (num('hours_worked'), 'Hours logged') if num('hours_worked') else None,
        (f'{num("job_success")}%', 'Job Success Score') if num('job_success') else None,
        (f'${num("hourly_rate")}', 'Per hour, verified') if num('hourly_rate') else None,
    ]
    rows = [r for r in rows if r]
    if not rows:
        return ''
    cells = ''.join(f'<div><strong>{v}</strong><span>{label}</span></div>' for v, label in rows)
    return f'<div class="cv-stats">{cells}</div>'


def load_testimonials(max_count):
    if not TESTIMONIALS_FILE.is_file():
        return []
    items = json.loads(TESTIMONIALS_FILE.read_text(encoding='utf-8'))
    return items[:max_count] if max_count else items


def stars_html(rating):
    full = round(rating)
    return '★' * full + '☆' * (5 - full)


# Muss mit shapeFor() in diagram.js zusammenpassen -- eine unbekannte Art
# wuerde dort still als normaler Kasten landen, hier bricht sie laut ab.
GRAPH_KINDS = {'source', 'step', 'sink', 'service', 'decision', 'note',
               'datastore', 'milestone', 'actor'}
GRAPH_OWNERS = {'you', 'client', 'thirdparty'}


def build_graph(spec):
    """Beliebiger Graph statt fester Kette.

    Fuer echte Implementierungsplaene reicht "Ausloeser -> Schritte -> Ziel"
    nicht: die haben Verzweigungen, parallele Straenge und Phasen. Claude
    schreibt deshalb die Struktur als JSON, nicht als SVG -- gleiche
    Ausdrucksstaerke, aber pruefbar, und das Layout kann nicht kaputtgehen,
    weil es die Engine macht und nicht der Text.

    Form:
      {"nodes":[{"id":"a","label":"...","kind":"source"}, ...],
       "edges":[{"from":"a","to":"b","label":"if qualified","dashed":true}, ...]}
    Ohne x/y ordnet die Engine automatisch an.
    """
    p = pathlib.Path(spec)
    text = p.read_text(encoding='utf-8') if p.is_file() else spec
    try:
        g = json.loads(text)
    except json.JSONDecodeError as e:
        print(f'ABBRUCH: --graph ist kein gueltiges JSON: {e}', file=sys.stderr)
        sys.exit(1)

    nodes = g.get('nodes') or []
    if not nodes:
        print('ABBRUCH: --graph enthaelt keine nodes.', file=sys.stderr)
        sys.exit(1)
    ids = set()
    for n in nodes:
        if not n.get('id') or not n.get('label'):
            print(f'ABBRUCH: Knoten ohne id/label: {n}', file=sys.stderr)
            sys.exit(1)
        if n['id'] in ids:
            print(f'ABBRUCH: doppelte Knoten-id "{n["id"]}".', file=sys.stderr)
            sys.exit(1)
        ids.add(n['id'])
        k = n.setdefault('kind', 'step')
        if k not in GRAPH_KINDS:
            print(f'ABBRUCH: unbekanntes kind "{k}". Erlaubt: {sorted(GRAPH_KINDS)}', file=sys.stderr)
            sys.exit(1)
        o = n.get('owner')
        if o is not None and o not in GRAPH_OWNERS:
            print(f'ABBRUCH: unbekannter owner "{o}". Erlaubt: {sorted(GRAPH_OWNERS)}', file=sys.stderr)
            sys.exit(1)
    for e in g.get('edges') or []:
        for side in ('from', 'to'):
            if e.get(side) not in ids:
                print(f'ABBRUCH: Kante zeigt auf unbekannten Knoten "{e.get(side)}".', file=sys.stderr)
                sys.exit(1)

    # Phasen: pruefen, dass jede Mitglieder-id existiert. Ein Tippfehler wuerde
    # sonst still einen leeren oder halben Rahmen zeichnen.
    groups = g.get('groups') or []
    for grp in groups:
        if not grp.get('label'):
            print(f'ABBRUCH: Phase ohne label: {grp}', file=sys.stderr)
            sys.exit(1)
        for nid in grp.get('nodes') or []:
            if nid not in ids:
                print(f'ABBRUCH: Phase "{grp["label"]}" nennt unbekannten Knoten "{nid}".',
                      file=sys.stderr)
                sys.exit(1)

    data = json.dumps({'nodes': nodes, 'edges': g.get('edges') or [], 'groups': groups},
                      ensure_ascii=False)
    fallback = '\n            '.join(f'<li>{n["label"]}</li>' for n in nodes)
    return data, fallback


def build_diagram(source, steps, sink, services):
    """Knotenliste + No-JS-Fallback. Das Layout macht ausschliesslich das
    Template -- hier entsteht nur die Liste, damit es nicht zwei Layout-
    Implementierungen gibt, die auseinanderlaufen koennen."""
    if not 1 <= len(steps) <= 4:
        print(f'ABBRUCH: 1 bis 4 --step erwartet, bekommen: {len(steps)}', file=sys.stderr)
        sys.exit(1)
    if len(services) > 2:
        print(f'ABBRUCH: max. 2 --service, bekommen: {len(services)}', file=sys.stderr)
        sys.exit(1)

    nodes = [{'id': 'n0', 'label': source, 'kind': 'source'}]
    for i, s in enumerate(steps, 1):
        nodes.append({'id': f'n{i}', 'label': s, 'kind': 'step'})
    nodes.append({'id': f'n{len(steps)+1}', 'label': sink, 'kind': 'sink'})

    svc = []
    for i, raw in enumerate(services):
        label, _, at = raw.partition('@')
        try:
            at_i = int(at) if at else max(1, len(steps) // 2 + 1)
        except ValueError:
            at_i = 1
        svc.append({'id': f's{i}', 'label': label.strip(), 'kind': 'service',
                    'at': max(0, min(at_i, len(nodes) - 1))})

    # Eine einzige Knotenliste. Die Engine unterscheidet ueber `kind`; eine
    # zweite Liste danebenzustellen hiess, dass die Dienste nie ankamen.
    data = json.dumps({'nodes': nodes + svc}, ensure_ascii=False)
    fallback = '\n            '.join(
        f'<li>{n["label"]}</li>' for n in nodes)
    if svc:
        fallback += '\n            ' + '\n            '.join(
            f'<li>{s["label"]} (supporting service)</li>' for s in svc)
    return data, fallback


def logos_json(nodes):
    """Nur die Logos einbetten, die dieser Graph wirklich nennt.

    Alle 20 mitzuliefern kostet 84 KB auf jeder Seite, von denen zwei benutzt
    werden. Das <title> aus der Simple-Icons-Datei fliegt raus, sonst zeigt der
    Browser beim Hovern ueber dem Knoten einen Tooltip mit dem Markennamen.
    """
    want = {n.get('logo') for n in nodes if n.get('logo')}
    out = {}
    for slug in sorted(want):
        f = LOGO_DIR / f'{slug}.svg'
        if not f.is_file():
            print(f'  Hinweis: kein Logo "{slug}" -- Knoten zeigt nur seine Form.', file=sys.stderr)
            continue
        svg = f.read_text(encoding='utf-8')
        inner = re.sub(r'^.*?<svg[^>]*>|</svg>\s*$', '', svg, flags=re.S)
        inner = re.sub(r'<title>.*?</title>', '', inner, flags=re.S)
        out[slug] = inner.strip()
    return json.dumps(out, ensure_ascii=False)


def save_to_library(job, data):
    """Jeden erzeugten Graph ablegen, damit der naechste Pitch nicht bei null
    anfaengt. Ein Index daneben, weil ein Ordner mit 40 JSON-Dateien nicht
    durchsuchbar ist und deshalb nicht benutzt wuerde."""
    LIBRARY.mkdir(parents=True, exist_ok=True)
    slug = slugify(job.get('title', 'untitled'))
    entry = {
        'job_id': job.get('id'), 'title': job.get('title'),
        'saved_at': datetime.date.today().isoformat(),
        'nodes': len(json.loads(data)['nodes']), 'file': f'{slug}.json',
    }
    (LIBRARY / f'{slug}.json').write_text(data, encoding='utf-8')
    idx_file = LIBRARY / 'index.json'
    idx = json.loads(idx_file.read_text(encoding='utf-8')) if idx_file.is_file() else []
    idx = [e for e in idx if e.get('file') != entry['file']] + [entry]
    idx_file.write_text(json.dumps(idx, indent=1, ensure_ascii=False), encoding='utf-8')
    return len(idx)


def videos_html():
    """Echte YouTube-Videos aus assets/videos.json, Thumbnails eingebettet.

    IDs und Titel sind ueber die offizielle oEmbed-API verifiziert, nicht geraten.
    Fehlt die Datei oder ein Thumbnail, faellt der ganze Block weg statt einen
    toten Rahmen zu rendern."""
    if not VIDEOS_FILE.is_file():
        return ''
    cards = []
    for v in json.loads(VIDEOS_FILE.read_text(encoding='utf-8')):
        thumb = ASSETS / v['thumb']
        if not thumb.is_file():
            continue
        src = img_data_uri(str(thumb), mime='image/jpeg')[0]
        cards.append(
            f'<a class="yt-card" href="https://www.youtube.com/watch?v={v["id"]}" '
            f'target="_blank" rel="noopener">'
            f'<span class="yt-thumb"><img src="{src}" alt="{v["title"]}">'
            f'<span class="pin">{YT_PLAY}</span></span>'
            f'<p>{v["title"]}</p></a>')
    return '\n        '.join(cards)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('job_id')
    ap.add_argument('--hook', required=True,
                     help='die EINZIGE Headline der Seite. Muster: "What your <konkretes System> would '
                          'look like" -- muss erkennbar auf DIESEN Job Bezug nehmen. Kein Subhead mehr, '
                          'no pill, no name label above it -- the quote carries itself.')
    ap.add_argument('--fit-point', action='append', required=True,
                     help='ein Eignungsgrund, dreimal angeben')
    # Das Diagramm ist kein Bild mehr, sondern eine Knotenliste. Das Template
    # zeichnet daraus zur Laufzeit ein SVG -- scharf in jeder Groesse, folgt den
    # Theme-Tokens, und der Kunde kann darin zoomen und eigene Schritte
    # ergaenzen. Die Grammatik ist fest (Ausloeser -> Schritte -> Ziel, plus
    # Dienste darunter), damit nichts ueberlappen kann.
    ap.add_argument('--graph',
                     help='kompletter Graph als JSON oder Pfad zu einer .json -- fuer alles mit '
                          'Verzweigungen, parallelen Straengen oder Phasen. Schliesst '
                          '--source/--step/--sink aus.')
    ap.add_argument('--source', help='wo der Prozess startet, ein Knoten (einfache Kette)')
    ap.add_argument('--step', action='append',
                     help='ein Verarbeitungsschritt, 2 bis 4 mal angeben (einfache Kette)')
    ap.add_argument('--sink', help='wo das Ergebnis landet, ein Knoten (einfache Kette)')
    ap.add_argument('--service', action='append', default=[],
                     help='Nebendienst, optional mit @<index> an einen Schritt gehaengt, '
                          'z.B. "Claude API@2". Max 2.')
    ap.add_argument('--loom-url', default='')
    ap.add_argument('--video-length', default='3 minute')
    ap.add_argument('--tool', action='append', required=True,
                     help='ein Tool, das fuer diesen Job zum Einsatz kaeme, mehrfach angeben')
    ap.add_argument('--timeline', required=True, help='eine kurze, ehrliche Zeitschaetzung fuer diesen Job')
    ap.add_argument('--budget', required=True,
                     help='eine kurze, ehrliche Budget-Einordnung fuer diesen Job (Rahmen, nicht auf den Dollar genau)')
    ap.add_argument('--kickoff', action='append', required=True,
                     help='was vom Kunden gebraucht wird um loszulegen, mehrfach angeben')
    ap.add_argument('--max-testimonials', type=int, default=0,
                     help='0 = alle aus testimonials.json verwenden (Default)')
    ap.add_argument('--hero-illustration', default='',
                     help='Pfad zu einer generierten Uebersichts-Illustration (hand-drawn '
                          'whiteboard-Stil), gezeigt oberhalb des technischen Diagramms. '
                          'Optional -- ohne diesen Flag faellt der Slot einfach weg, kein '
                          'Platzhalter noetig.')
    ap.add_argument('--plan-image', action='append', default=[],
                     help='Bild fuer die vier Kaesten der Scope-Sektion, in dieser '
                          'Reihenfolge: Tools, Timeline, Budget, Kickoff. Genau 0 oder 4 '
                          'angeben. WICHTIG: die Sektion hat dunklen Grund -- die Bilder '
                          'muessen selbst dunkel sein, sonst knallt ein heller Kasten rein.')
    ap.add_argument('--live-artifact', action='append', default=[],
                     help='etwas, das fuer diesen Job WIRKLICH schon gebaut wurde, als '
                          '"Label|URL" -- ein n8n-Flow, ein Make-Szenario, eine deployte '
                          'Seite. Wiederholbar. Erscheint als eigener Streifen unter dem '
                          'Board: das Board zeigt den Plan, der Link beweist ihn.')
    ap.add_argument('--lead-magnet-url', default='')
    ap.add_argument('--lead-magnet-teaser', default='')
    ap.add_argument('--lead-magnet-cta', default='Get it here')
    ap.add_argument('--profile-url', default='https://upwork.com/freelancers/~01a748c991a3b91762')
    ap.add_argument('--out')
    args = ap.parse_args()

    if len(args.fit_point) != 3:
        print(f'ABBRUCH: genau 3 --fit-point erwartet, bekommen: {len(args.fit_point)}', file=sys.stderr)
        sys.exit(1)
    if not args.tool:
        print('ABBRUCH: mindestens 1 --tool erwartet.', file=sys.stderr)
        sys.exit(1)
    if not args.kickoff:
        print('ABBRUCH: mindestens 1 --kickoff erwartet.', file=sys.stderr)
        sys.exit(1)

    job = load_job(args.job_id)

    if args.graph:
        diagram_data, diagram_fallback = build_graph(args.graph)
    elif args.source and args.step and args.sink:
        diagram_data, diagram_fallback = build_diagram(
            args.source, args.step, args.sink, args.service)
    else:
        print('ABBRUCH: entweder --graph, oder --source + --step + --sink.', file=sys.stderr)
        sys.exit(1)
    report_cover_src = img_data_uri(str(REPORT_COVER_FILE), mime='image/jpeg')[0] if REPORT_COVER_FILE.is_file() else ''
    dither_src = img_data_uri(str(DITHER_FILE))[0] if DITHER_FILE.is_file() else ''

    # Die Illustration liegt AUF dem Board, nicht darueber: sie wird in
    # diagram.js eingesetzt und dort links neben dem Flow gezeichnet, damit sie
    # mitzoomt, mitpannt und mitexportiert.
    if args.hero_illustration:
        mime = 'image/jpeg' if args.hero_illustration.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
        illustration_src = img_data_uri(args.hero_illustration, mime=mime)[0]
        # Dasselbe Bild zweimal: gross als Eyecatcher unter der Headline, klein
        # als "the short version" auf dem Board. Zwei Rollen desselben Motivs,
        # wie Plakat und Miniatur -- deshalb als JPEG einbetten, sonst zahlt
        # die Seite den Umweg doppelt.
        hero_art = f'<div class="hero-art" data-rise data-d="1"><img src="{illustration_src}" alt=""></div>'
    else:
        illustration_src = ''
        hero_art = ''

    if not args.loom_url:
        args.loom_url = '#loom-link-fehlt-noch'

    fit_html = '\n        '.join(
        f'<li>{FIT_ICON}<span>{p}</span></li>'
        for p in args.fit_point)

    tools_html = '\n            '.join(f'<li>{t}</li>' for t in args.tool)
    kickoff_html = '\n            '.join(f'<li>{k}</li>' for k in args.kickoff)

    # "Gebaut heisst verlinkt": ein Flow, den es wirklich gibt, muss anklickbar
    # sein, sonst ist er fuer den Kunden dasselbe wie ein gezeichneter.
    if args.live_artifact:
        items = []
        for raw in args.live_artifact:
            label, sep, url = raw.partition('|')
            if not sep or not url.strip():
                print(f'ABBRUCH: --live-artifact braucht "Label|URL", bekommen: {raw!r}',
                      file=sys.stderr)
                sys.exit(1)
            items.append(f'<li><a href="{url.strip()}" target="_blank" rel="noopener">'
                         f'{label.strip()}<span class="arrow" aria-hidden="true">&rarr;</span></a></li>')
        live_block = ('<div class="live-artifacts"><p class="live-lede">'
                      'Already built, not just drawn. Open it yourself:</p>'
                      '<ul>' + ''.join(items) + '</ul></div>')
    else:
        live_block = ''

    if args.plan_image and len(args.plan_image) != 4:
        print(f'ABBRUCH: --plan-image genau 4 mal (Tools, Timeline, Budget, Kickoff) '
              f'oder gar nicht, bekommen: {len(args.plan_image)}', file=sys.stderr)
        sys.exit(1)
    plan_imgs = []
    for path in (args.plan_image or []):
        mime = 'image/jpeg' if path.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
        src = img_data_uri(path, mime=mime)[0]
        plan_imgs.append(f'<div class="plan-img"><img src="{src}" alt="" loading="lazy"></div>')
    while len(plan_imgs) < 4:
        plan_imgs.append('')

    testimonials = load_testimonials(args.max_testimonials)
    if testimonials:
        testimonials_html = '<div class="testimonials">\n          ' + '\n          '.join(
            f'<div class="testimonial"><p class="quote">"{t["quote"]}"</p>'
            f'<p class="meta"><span class="stars">{stars_html(t["rating"])}</span>'
            f'<span class="job">{t["job"]}</span></p></div>'
            for t in testimonials) + '\n        </div>'
    else:
        testimonials_html = '<p class="testimonials-empty">Testimonials noch nicht hinterlegt.</p>'

    if not args.lead_magnet_url:
        args.lead_magnet_url = '#lead-magnet-fehlt-noch'
        if not args.lead_magnet_teaser:
            args.lead_magnet_teaser = 'Lead-Magnet noch nicht hinterlegt.'
    elif not args.lead_magnet_teaser:
        print('ABBRUCH: --lead-magnet-url gesetzt, aber --lead-magnet-teaser fehlt.', file=sys.stderr)
        sys.exit(1)

    tpl = TEMPLATE.read_text(encoding='utf-8')
    _links = optional_links()
    out_html = (tpl
        .replace('{{JOB_TITLE}}', job.get('title', ''))
        .replace('{{HOOK}}', args.hook)
        .replace('{{VIDEOS_BLOCK}}', videos_html())
        .replace('{{LOOM_URL}}', args.loom_url)
        .replace('{{VIDEO_LENGTH}}', args.video_length)
        .replace('{{FIT_POINTS}}', fit_html)
        .replace('{{TOOLS}}', tools_html)
        .replace('{{TIMELINE}}', args.timeline)
        .replace('{{BUDGET}}', args.budget)
        .replace('{{KICKOFF_ITEMS}}', kickoff_html)
        .replace('{{DITHER_SRC}}', dither_src)
        .replace('{{HERO_ART}}', hero_art)
        .replace('{{LIVE_ARTIFACTS}}', live_block)
        .replace('{{PLAN_IMG_TOOLS}}', plan_imgs[0])
        .replace('{{PLAN_IMG_TIMELINE}}', plan_imgs[1])
        .replace('{{PLAN_IMG_BUDGET}}', plan_imgs[2])
        .replace('{{PLAN_IMG_KICKOFF}}', plan_imgs[3])
        .replace('{{TESTIMONIALS_BLOCK}}', testimonials_html)
        .replace('{{CV_STATS}}', cv_stats_html())
        .replace('{{PROOF_LINK}}', _links[0])
        .replace('{{YT_MORE}}', _links[1])
        .replace('{{FOOTER_LINKS}}', _links[2])
        .replace('{{DIAGRAM_DATA}}', diagram_data)
        .replace('{{DIAGRAM_FALLBACK}}', diagram_fallback)
        .replace('{{DIAGRAM_JS}}', DIAGRAM_JS_FILE.read_text(encoding='utf-8')
                 .replace('{{LOGOS_JSON}}', logos_json(json.loads(diagram_data)['nodes']))
                 .replace('{{ILLUSTRATION_SRC}}', illustration_src))
        .replace('{{REPORT_COVER_SRC}}', report_cover_src)
        .replace('{{LEAD_MAGNET_TEASER}}', args.lead_magnet_teaser)
        .replace('{{LEAD_MAGNET_URL}}', args.lead_magnet_url)
        .replace('{{LEAD_MAGNET_CTA}}', args.lead_magnet_cta)
        .replace('{{PROFILE_URL}}', args.profile_url))

    if args.out:
        out_path = pathlib.Path(args.out)
    else:
        today = datetime.date.today().isoformat()
        slug = slugify(job.get('title', args.job_id))
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUT_DIR / f'{today}_{slug}.html'

    lib_n = save_to_library(job, diagram_data)
    out_path.write_text(out_html, encoding='utf-8')
    print(f'geschrieben: {out_path}  ({len(out_html)} Zeichen, '
          f'{len(json.loads(diagram_data)["nodes"])} Diagramm-Knoten, {len(testimonials)} Testimonials, Bibliothek: {lib_n})')


if __name__ == '__main__':
    main()
