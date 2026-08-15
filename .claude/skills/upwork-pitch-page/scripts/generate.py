#!/usr/bin/env python3
"""Fills the pitch-page template for one job. Assembly only.

The diagram, the copy and the illustrations are decided before this runs; this
turns them into one self-contained HTML file with everything embedded.

Page order: headline, hero illustration, the walkthrough video full width,
three fit points, testimonials, the collapsible background panel, the editable
plan diagram, the four-part scope block, the lead magnet, and the closing ask.

**Nothing on the page is invented, and nothing about a particular person is
written into the template.** Every section that describes *you* is passed in and
disappears when it is not: the background panel, the portrait, the videos, the
report cover, the profile links. That is not politeness, it is correctness — the
template is shared, so a fact hardcoded in it becomes a claim on a stranger's
client-facing page.

Two flags accept a richer format and fall back to a plain sentence:

    --fit-point "30+|Accounts audited|Multi-location, one shared budget"
    --timeline  "Week 1|Findings;;Week 2|Fixes agreed;;Week 3|Handover"

Usage:
    python3 generate.py <job_id> \
        --hook "..." \
        --fit-point "..." --fit-point "..." --fit-point "..." \
        --graph plan.json \
        --tool "..." --timeline "..." --budget "..." --kickoff "..." \
        [--photo face.jpg] [--hero-illustration hero.jpg] [--plan-image x4] \
        [--stat "value|label"] [--trait "..."] [--client "..."] \
        [--background "role|institution"] [--languages "..."] \
        [--lead-magnet-url ... --lead-magnet-title ... --lead-magnet-point ...] \
        [--out path.html]

Without --out the filename comes from the job title:
jobs/<YYYY-MM-DD>_<slug>.html

Exits 1 on a missing job, an image path that does not resolve, or an invalid
graph. A silent half-result would be worse than stopping with a reason.
"""
import argparse, base64, datetime, json, pathlib, re, sys

W = pathlib.Path(__file__).resolve().parents[4]
JOBS = W / 'context/.upwork_jobs.json'
ASSETS = pathlib.Path(__file__).resolve().parent.parent / 'assets'
CONTEXT = W / 'context'
TEMPLATE = ASSETS / 'template.html'
TESTIMONIALS_FILE = CONTEXT / 'testimonials.json'
# Two assets that are deliberately NOT in this repo, because both are personal:
# the report cover is page one of a real client deliverable, and videos.json lists
# somebody's own YouTube videos. Their absence is the correct state for a clone,
# not a defect, and the sections that use them simply do not render.
#
# To use them: drop your own report cover in as a JPEG, and write videos.json as
# [{"id": "<youtube id>", "title": "..."}]. Both are optional either way.
REPORT_COVER_FILE = ASSETS / 'report-cover-example.jpg'
VIDEOS_FILE = ASSETS / 'videos.json'

DIAGRAM_JS_FILE = ASSETS / 'diagram.js'
LOGO_DIR = ASSETS / 'logos'
# Every generated graph lands here. A library that has to be maintained by hand
# stays empty, so this one fills itself as a by-product of every run.
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
# Same mark, once as the play pin on a thumbnail and once as the section's icon.
YT_MARK = YT_PLAY.replace('<svg ', '<svg class="yt-mark" ', 1)

# Stands in for the portrait until someone passes --photo. Drawn rather than
# shipped as a file so it follows the theme tokens and costs no bytes, and left
# deliberately plain: it is a slot that reads as empty, not a stock face
# pretending to be the freelancer. Anyone who sends the page without replacing
# it has sent a page with no photo, which is the honest outcome.
PORTRAIT_PLACEHOLDER = (
    '<span class="next-photo next-photo-empty" role="img" '
    'aria-label="No portrait added yet" data-rise>'
    '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    '<circle cx="24" cy="18" r="7.5"/>'
    '<path d="M9.5 40c1.6-8 7.7-12 14.5-12s12.9 4 14.5 12z"/>'
    '</svg></span>')

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
        print(f'ABORT: {JOBS} is missing.', file=sys.stderr)
        sys.exit(1)
    jobs = json.loads(JOBS.read_text(encoding='utf-8'))
    for j in jobs:
        if j.get('id') == job_id:
            return j
    print(f'ABORT: job_id "{job_id}" not found in {JOBS}.', file=sys.stderr)
    sys.exit(1)


def img_data_uri(path_str, mime='image/png'):
    p = pathlib.Path(path_str)
    if not p.is_file():
        print(f'ABORT: image "{p}" does not exist.', file=sys.stderr)
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


def profile_links(profile_url):
    """The closing button and the footer link, both pointing at your own profile.

    Built here rather than in the template because an `href=""` is not a quiet
    link: the browser resolves it to the page itself, so the client clicks
    "Message me on Upwork" and the page reloads. With no profile configured the
    whole button is left out and the paragraph above it carries the ask alone.
    """
    if not profile_url:
        return '', ''
    return (f'<a class="btn btn-on-ink" href="{profile_url}" target="_blank" '
            f'rel="noopener" data-rise data-d="2">Message me on Upwork '
            f'<span class="arrow" aria-hidden="true">→</span></a>',
            f'<a href="{profile_url}" target="_blank" rel="noopener">Upwork profile</a>')


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


def cv_block(args):
    """"More about my background", built from the freelancer's own facts.

    This used to sit in the template as literal text, which meant every page
    generated by anyone claimed one particular person's degree, employers and
    client list. A pitch page is a client-facing document; wrong facts in it are
    worse than missing ones. So each part appears only if it was passed, and if
    nothing was, the whole section is dropped rather than opening onto an empty
    panel.

    The values come from `context/experience.md`, which the skill reads and
    passes through as flags. Only the numbers have a second source: without
    --stat they fall back to `context/config.yaml`, which the screener refreshes
    from the account itself.
    """
    parts = []

    if args.stat:
        cells = ''.join(f'<div><strong>{v.strip()}</strong><span>{label.strip()}</span></div>'
                        for v, _, label in (s.partition('|') for s in args.stat) if label)
        if cells:
            parts.append(f'<div class="cv-stats">{cells}</div>')
    else:
        parts.append(cv_stats_html())

    if args.trait:
        tags = ''.join(f'<span>{t}</span>' for t in args.trait)
        parts.append('<p class="cv-sub">What clients said after the job was done</p>'
                     f'<div class="cv-traits">{tags}</div>')

    if args.client:
        names = ' · '.join(args.client)
        note = f', {args.client_note}' if args.client_note else ''
        parts.append('<p class="cv-sub">Businesses I\'ve built for</p>'
                     f'<p class="cv-clients">{names}{note}</p>')

    if args.background:
        items = ''.join(f'<li><strong>{role.strip()}</strong> at {where.strip()}</li>'
                        for role, _, where in (b.partition('|') for b in args.background) if where)
        if items:
            parts.append(f'<p class="cv-sub">Background</p><ul class="cv-list">{items}</ul>')

    if args.languages:
        parts.append(f'<p class="cv-lang">{args.languages}</p>')

    parts = [p for p in parts if p]
    if not parts:
        return ''
    return ('<section class="band band-plain band-tight band-tight-b"><div class="inner">'
            '<details class="cv"><summary>More about my background</summary>'
            f'<div class="cv-body">{"".join(parts)}</div></details></div></section>')


def load_testimonials(max_count):
    if not TESTIMONIALS_FILE.is_file():
        return []
    items = json.loads(TESTIMONIALS_FILE.read_text(encoding='utf-8'))
    return items[:max_count] if max_count else items


def stars_html(rating):
    full = round(rating)
    return '★' * full + '☆' * (5 - full)


# Has to match shapeFor() in diagram.js: an unknown kind would quietly become an
# ordinary box there, whereas here it aborts loudly.
GRAPH_KINDS = {'source', 'step', 'sink', 'service', 'decision', 'note',
               'datastore', 'milestone', 'actor'}
GRAPH_OWNERS = {'you', 'client', 'thirdparty'}


def build_graph(spec):
    """An arbitrary graph rather than a fixed chain.

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
        print(f'ABORT: --graph is not valid JSON: {e}', file=sys.stderr)
        sys.exit(1)

    nodes = g.get('nodes') or []
    if not nodes:
        print('ABORT: --graph contains no nodes.', file=sys.stderr)
        sys.exit(1)
    ids = set()
    for n in nodes:
        if not n.get('id') or not n.get('label'):
            print(f'ABORT: node without an id or label: {n}', file=sys.stderr)
            sys.exit(1)
        if n['id'] in ids:
            print(f'ABORT: duplicate node id "{n["id"]}".', file=sys.stderr)
            sys.exit(1)
        ids.add(n['id'])
        k = n.setdefault('kind', 'step')
        if k not in GRAPH_KINDS:
            print(f'ABORT: unknown kind "{k}". Allowed: {sorted(GRAPH_KINDS)}', file=sys.stderr)
            sys.exit(1)
        o = n.get('owner')
        if o is not None and o not in GRAPH_OWNERS:
            print(f'ABORT: unknown owner "{o}". Allowed: {sorted(GRAPH_OWNERS)}', file=sys.stderr)
            sys.exit(1)
    for e in g.get('edges') or []:
        for side in ('from', 'to'):
            if e.get(side) not in ids:
                print(f'ABORT: edge points at unknown node "{e.get(side)}".', file=sys.stderr)
                sys.exit(1)

    # Phases: check every member id exists. A typo would otherwise draw an empty
    # or half-finished frame without saying anything.
    groups = g.get('groups') or []
    for grp in groups:
        if not grp.get('label'):
            print(f'ABORT: phase without a label: {grp}', file=sys.stderr)
            sys.exit(1)
        for nid in grp.get('nodes') or []:
            if nid not in ids:
                print(f'ABORT: phase "{grp["label"]}" names unknown node "{nid}".',
                      file=sys.stderr)
                sys.exit(1)

    data = json.dumps({'nodes': nodes, 'edges': g.get('edges') or [], 'groups': groups},
                      ensure_ascii=False)
    fallback = '\n            '.join(f'<li>{n["label"]}</li>' for n in nodes)
    return data, fallback


def build_diagram(source, steps, sink, services):
    """Node list plus a no-JS fallback. Layout is done entirely by the
    Template -- hier entsteht nur die Liste, damit es nicht zwei Layout-
    implementations that can drift apart."""
    if not 1 <= len(steps) <= 4:
        print(f'ABORT: expected 1 to 4 --step, got {len(steps)}', file=sys.stderr)
        sys.exit(1)
    if len(services) > 2:
        print(f'ABORT: at most 2 --service, got {len(services)}', file=sys.stderr)
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

    # One node list. The engine tells them apart by `kind`; putting a second list
    # beside it meant the services never arrived.
    data = json.dumps({'nodes': nodes + svc}, ensure_ascii=False)
    fallback = '\n            '.join(
        f'<li>{n["label"]}</li>' for n in nodes)
    if svc:
        fallback += '\n            ' + '\n            '.join(
            f'<li>{s["label"]} (supporting service)</li>' for s in svc)
    return data, fallback


def logos_json(nodes):
    """Embed only the logos this graph actually names.

    Alle 20 mitzuliefern kostet 84 KB auf jeder Seite, von denen zwei benutzt
    werden. Das <title> aus der Simple-Icons-Datei fliegt raus, sonst zeigt der
    Browser beim Hovern ueber dem Knoten einen Tooltip mit dem Markennamen.
    """
    want = {n.get('logo') for n in nodes if n.get('logo')}
    out = {}
    for slug in sorted(want):
        f = LOGO_DIR / f'{slug}.svg'
        if not f.is_file():
            print(f'  Note: no logo for "{slug}", the node shows only its shape.', file=sys.stderr)
            continue
        svg = f.read_text(encoding='utf-8')
        inner = re.sub(r'^.*?<svg[^>]*>|</svg>\s*$', '', svg, flags=re.S)
        inner = re.sub(r'<title>.*?</title>', '', inner, flags=re.S)
        out[slug] = inner.strip()
    return json.dumps(out, ensure_ascii=False)


def save_to_library(job, data):
    """Store every generated graph, so the next pitch does not start from
    anfaengt. Ein Index daneben, weil ein Ordner mit 40 JSON-Dateien nicht
    searchable and would therefore never get used."""
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


def videos_section(note, channel_link):
    """"I build these in public": your own YouTube videos, thumbnails embedded.

    Ids and titles are verified through the official oEmbed API rather than
    guessed. If the file, the thumbnails or the videos are missing, the whole
    section goes rather than leaving an empty frame under a heading — and the
    channel link goes with it, because a "see the whole channel" arrow under
    nothing is a link to a section that does not exist.
    """
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
    if not cards:
        return ''
    note_html = f'<p class="yt-note" data-rise data-d="1">{note}</p>' if note else ''
    return ('<section class="band band-plain band-tight"><div class="inner">'
            f'<div class="yt-head" data-rise>{YT_MARK}'
            '<h2 class="serif section-title">I build these in public</h2></div>'
            f'{note_html}<div class="yt-grid">{"".join(cards)}</div>'
            f'{channel_link}</div></section>')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('job_id')
    ap.add_argument('--hook', required=True,
                     help='the ONLY headline on the page. Pattern: "What your <specific system> would '
                          'look like". Must clearly reference THIS job. No subhead any more, '
                          'no pill, no name label above it -- the quote carries itself.')
    ap.add_argument('--fit-point', action='append', required=True,
                     help='one reason you fit, give it three times')
    # The diagram is no longer an image, it is a node list. The template draws an
    # SVG from it at runtime: sharp at any size, following the theme tokens, and
    # the client can zoom in and add steps of their own. The grammar is fixed
    # (trigger -> steps -> sink, services underneath) so nothing can overlap.
    ap.add_argument('--graph',
                     help='the whole graph as JSON, or a path to a .json file. For anything with '
                          'branches, parallel strands or phases. Mutually exclusive with '
                          '--source/--step/--sink aus.')
    ap.add_argument('--source', help='where the process starts, one node (simple chain)')
    ap.add_argument('--step', action='append',
                     help='one processing step, give it 2 to 4 times (simple chain)')
    ap.add_argument('--sink', help='where the result lands, one node (simple chain)')
    ap.add_argument('--service', action='append', default=[],
                     help='a side service, optionally attached to a step with @<index>, '
                          'z.B. "Claude API@2". Max 2.')
    ap.add_argument('--loom-url', default='')
    ap.add_argument('--video-length', default='3 minute')
    ap.add_argument('--video-note', default='A few recent builds from my channel.',
                    help='the line under "I build these in public". Say anything a client '
                         'should know before clicking, e.g. which language they are in')
    ap.add_argument('--tool', action='append', required=True,
                     help='a tool this job would use, repeatable')
    ap.add_argument('--timeline', required=True, help='a short, honest timeline for this job')
    ap.add_argument('--budget', required=True,
                     help='a short, honest budget framing for this job (a range, not a figure to the dollar)')
    ap.add_argument('--kickoff', action='append', required=True,
                     help='what you need from the client to start, repeatable')
    # The "More about my background" panel. All optional, all from
    # context/experience.md — see cv_block() for why none of it is hardcoded.
    ap.add_argument('--stat', action='append', default=[],
                    help='"value|label", e.g. "$10K+|Earned on Upwork". Without any, '
                         'the numbers come from context/config.yaml instead')
    ap.add_argument('--trait', action='append', default=[],
                    help='one client-sourced trait, e.g. "Clear Communicator"')
    ap.add_argument('--client', action='append', default=[],
                    help='one company or project name you may name publicly')
    ap.add_argument('--client-note', default='',
                    help='closing clause after the names, e.g. "plus 15+ smaller builds"')
    ap.add_argument('--background', action='append', default=[],
                    help='"role|institution", employment and education, most relevant first')
    ap.add_argument('--languages', default='', help='one line, e.g. "English (native)"')
    ap.add_argument('--max-testimonials', type=int, default=0,
                     help='0 = alle aus testimonials.json verwenden (Default)')
    ap.add_argument('--hero-illustration', default='',
                     help='path to a generated overview illustration (hand-drawn '
                          'whiteboard-Stil), gezeigt oberhalb des technischen Diagramms. '
                          'Optional. Without the flag the slot simply disappears, no '
                          'Platzhalter noetig.')
    ap.add_argument('--plan-image', action='append', default=[],
                     help='image for the four boxes of the scope section, in this '
                          'in this order: tools, timeline, budget, kickoff. Exactly 0 or 4 '
                          'IMPORTANT: this section sits on a dark ground, so the images '
                          'have to be dark themselves, or a bright box punches a hole in it.')
    ap.add_argument('--live-artifact', action='append', default=[],
                     help='something that has ACTUALLY been built for this job already, as '
                          '"Label|URL": an n8n flow, a Make scenario, a deployed '
                          'Seite. Wiederholbar. Erscheint als eigener Streifen unter dem '
                          'board: the board shows the plan, the link proves it.')
    ap.add_argument('--lead-magnet-url', default='')
    ap.add_argument('--lead-magnet-teaser', default='')
    ap.add_argument('--lead-magnet-cta', default='Get it here')
    ap.add_argument('--lead-magnet-title', default='See a real example of what you would get',
                    help='the heading over the lead magnet. The default is true of any '
                         'lead magnet; name yours instead when you have one')
    ap.add_argument('--photo', default='',
                    help='your own face, shown as a round portrait above the closing '
                         'ask. Any crop works, it is cropped to a circle. Omit and the '
                         'section is exactly as it was')
    ap.add_argument('--report-cover', default='',
                    help='page one of the deliverable, as a JPEG. Defaults to '
                         'assets/report-cover-example.jpg; with no file, the whole '
                         'cover block is left out')
    ap.add_argument('--cover-badge', default='Real example',
                    help='the label on the cover. Change it if the cover is not one: '
                         'a mock-up under a "Real example" badge is a lie on a page '
                         'whose whole argument is that nothing on it is invented')
    ap.add_argument('--lead-magnet-point', action='append', default=[],
                    help='one line of what the reader actually gets. Repeatable; '
                         'with none, the list is left out rather than promising '
                         'something this lead magnet may not contain')
    ap.add_argument('--profile-url', default='',
                    help='your own Upwork profile, the target of the closing button. '
                         'Defaults to upwork_profile_url in context/config.yaml; '
                         'without either, the button and the footer link are left out')
    ap.add_argument('--out')
    args = ap.parse_args()

    if len(args.fit_point) != 3:
        print(f'ABORT: expected exactly 3 --fit-point, got {len(args.fit_point)}', file=sys.stderr)
        sys.exit(1)
    if not args.tool:
        print('ABORT: expected at least 1 --tool.', file=sys.stderr)
        sys.exit(1)
    if not args.kickoff:
        print('ABORT: expected at least 1 --kickoff.', file=sys.stderr)
        sys.exit(1)

    job = load_job(args.job_id)

    if args.graph:
        diagram_data, diagram_fallback = build_graph(args.graph)
    elif args.source and args.step and args.sink:
        diagram_data, diagram_fallback = build_diagram(
            args.source, args.step, args.sink, args.service)
    else:
        print('ABORT: either --graph, or --source + --step + --sink.', file=sys.stderr)
        sys.exit(1)
    photo_file = pathlib.Path(args.photo) if args.photo else None
    if photo_file and photo_file.is_file():
        next_photo = (f'<img class="next-photo" src="{img_data_uri(str(photo_file))[0]}" '
                      f'alt="Portrait" data-rise>')
    else:
        if args.photo:
            print(f'Note: --photo {args.photo} not found.', file=sys.stderr)
        print('Note: no portrait, so the closing section shows a placeholder. Pass '
              '--photo to replace it before you send this.', file=sys.stderr)
        next_photo = PORTRAIT_PLACEHOLDER

    cover_file = pathlib.Path(args.report_cover) if args.report_cover else REPORT_COVER_FILE
    report_cover_src = img_data_uri(str(cover_file), mime='image/jpeg')[0] if cover_file.is_file() else ''
    # Not just the <img>: the whole stage. An <img src=""> is a broken image
    # rather than an empty one, and dropping only the image still left the
    # tilted book frame, its two page edges and a "Real example" badge floating
    # in an empty 290px column — which looks like the page failed to load. With
    # no cover, the copy takes the full width instead.
    report_cover_stage = (
        '<div class="cover-stage" data-cover>'
        f'<span class="cover-flag">{args.cover_badge}</span>'
        '<div class="cover-book">'
        '<span class="cover-sheet s2"></span><span class="cover-sheet s1"></span>'
        f'<img class="cover-face" src="{report_cover_src}" '
        'alt="Cover of a performance report built for another client">'
        '</div></div>'
        if report_cover_src else '')
    # What the reader gets, in their words rather than one product's words. The
    # three lines here used to be fixed text describing one particular report;
    # every page built from this template promised exactly that, whatever the
    # lead magnet actually was.
    lead_magnet_points = (
        '<ul class="report-list" data-rise data-d="2">'
        + ''.join(f'<li>{p}</li>' for p in args.lead_magnet_point)
        + '</ul>') if args.lead_magnet_point else ''

    dither_src = img_data_uri(str(DITHER_FILE))[0] if DITHER_FILE.is_file() else ''

    # The illustration sits ON the board, not above it: diagram.js places it to
    # the left of the flow, so it pans, zooms and exports along with everything
    # else rather than being an attached picture.
    if args.hero_illustration:
        mime = 'image/jpeg' if args.hero_illustration.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
        illustration_src = img_data_uri(args.hero_illustration, mime=mime)[0]
        # The same image twice: large under the headline as the eye-catcher, small
        # on the board as "the short version". Two roles for one motif, poster and
        # thumbnail, which is why it is embedded as JPEG: otherwise the page pays
        # for the detour twice.
        hero_art = f'<div class="hero-art" data-rise data-d="1"><img src="{illustration_src}" alt=""></div>'
    else:
        illustration_src = ''
        hero_art = ''

    if not args.loom_url:
        args.loom_url = '#no-walkthrough-yet'

    # Three proof points, and the number is the argument, not the sentence around
    # it. Written as flowing text the number sat buried mid-paragraph and the
    # three cards came out visibly ragged. "number|label|context" sets the number
    # large so all three cards share one structure; anything without the
    # separator still renders as it always did, so existing calls do not break.
    def fit_item(p):
        parts = [t.strip() for t in p.split('|')]
        if len(parts) >= 3:
            number, label, context = parts[0], parts[1], ' '.join(parts[2:])
            return (f'<li><span class="fit-num">{number}</span>'
                    f'<span class="fit-label">{label}</span>'
                    f'<span class="fit-ctx">{context}</span></li>')
        return f'<li>{FIT_ICON}<span>{p}</span></li>'

    fit_html = '\n        '.join(fit_item(p) for p in args.fit_point)

    # The timeline is the most structured content on the page and had the least
    # structure: four milestones in one paragraph that nobody pulls apart.
    # "period|what;;period|what" becomes numbered rows; a plain sentence stays a
    # plain sentence.
    if '|' in args.timeline:
        steps = [s.strip() for s in args.timeline.split(';;') if s.strip()]
        rows = []
        for i, s in enumerate(steps, 1):
            when, _, what = s.partition('|')
            rows.append(f'<li><span class="ms-num">{i:02d}</span>'
                        f'<span class="ms-when">{when.strip()}</span>'
                        f'<span class="ms-what">{what.strip()}</span></li>')
        timeline_html = f'<ol class="milestones">{"".join(rows)}</ol>'
    else:
        timeline_html = f'<p class="plan-body">{args.timeline}</p>'

    # In the budget the first sentence carries the promise. It sat mid-paragraph
    # and went under; now it stands as a line above.
    head, _, rest = args.budget.partition('. ')
    budget_html = (f'<p class="plan-lead">{head.strip()}.</p>'
                   f'<p class="plan-body">{rest.strip()}</p>') if rest else \
                  f'<p class="plan-body">{args.budget}</p>'

    tools_html = '\n            '.join(f'<li>{t}</li>' for t in args.tool)
    kickoff_html = '\n            '.join(f'<li>{k}</li>' for k in args.kickoff)

    # "Built means linked": a flow that genuinely exists has to be clickable, or
    # to the client it is the same as a drawn one.
    if args.live_artifact:
        items = []
        for raw in args.live_artifact:
            label, sep, url = raw.partition('|')
            if not sep or not url.strip():
                print(f'ABORT: --live-artifact needs "Label|URL", got {raw!r}',
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
        print(f'ABORT: --plan-image exactly 4 times (tools, timeline, budget, kickoff) '
              f'or not at all, got {len(args.plan_image)}', file=sys.stderr)
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
        testimonials_html = '<p class="testimonials-empty">No testimonials added yet.</p>'

    if not args.lead_magnet_url:
        args.lead_magnet_url = '#no-lead-magnet-yet'
        if not args.lead_magnet_teaser:
            args.lead_magnet_teaser = 'No lead magnet configured yet.'
    elif not args.lead_magnet_teaser:
        print('ABORT: --lead-magnet-url is set but --lead-magnet-teaser is missing.', file=sys.stderr)
        sys.exit(1)

    tpl = TEMPLATE.read_text(encoding='utf-8')
    _links = optional_links()

    profile_url = args.profile_url or _cfg_str('upwork_profile_url')
    if not profile_url:
        print('Note: no upwork_profile_url in context/config.yaml, so the closing '
              'button is left out. Add it there or pass --profile-url.', file=sys.stderr)
    cta_link, foot_profile = profile_links(profile_url)
    foot_links = foot_profile + _links[2]
    if not foot_profile:
        # The separator belongs between links, and the profile link was the first.
        foot_links = re.sub(r'^<span class="dot">·</span>', '', foot_links)
    out_html = (tpl
        .replace('{{JOB_TITLE}}', job.get('title', ''))
        .replace('{{HOOK}}', args.hook)
        .replace('{{VIDEOS_SECTION}}', videos_section(args.video_note, _links[1]))
        .replace('{{LOOM_URL}}', args.loom_url)
        .replace('{{VIDEO_LENGTH}}', args.video_length)
        .replace('{{FIT_POINTS}}', fit_html)
        .replace('{{TOOLS}}', tools_html)
        .replace('{{TIMELINE_BLOCK}}', timeline_html)
        .replace('{{BUDGET_BLOCK}}', budget_html)
        .replace('{{KICKOFF_ITEMS}}', kickoff_html)
        .replace('{{DITHER_SRC}}', dither_src)
        .replace('{{HERO_ART}}', hero_art)
        .replace('{{LIVE_ARTIFACTS}}', live_block)
        .replace('{{PLAN_IMG_TOOLS}}', plan_imgs[0])
        .replace('{{PLAN_IMG_TIMELINE}}', plan_imgs[1])
        .replace('{{PLAN_IMG_BUDGET}}', plan_imgs[2])
        .replace('{{PLAN_IMG_KICKOFF}}', plan_imgs[3])
        .replace('{{TESTIMONIALS_BLOCK}}', testimonials_html)
        .replace('{{CV_SECTION}}', cv_block(args))
        .replace('{{PROOF_LINK}}', _links[0])
        .replace('{{FOOTER_LINKS}}', foot_links)
        .replace('{{DIAGRAM_DATA}}', diagram_data)
        .replace('{{DIAGRAM_FALLBACK}}', diagram_fallback)
        .replace('{{DIAGRAM_JS}}', DIAGRAM_JS_FILE.read_text(encoding='utf-8')
                 .replace('{{LOGOS_JSON}}', logos_json(json.loads(diagram_data)['nodes']))
                 .replace('{{ILLUSTRATION_SRC}}', illustration_src))
        .replace('{{REPORT_COVER_STAGE}}', report_cover_stage)
        .replace('{{LEAD_MAGNET_POINTS}}', lead_magnet_points)
        .replace('{{LEAD_MAGNET_TITLE}}', args.lead_magnet_title)
        .replace('{{LEAD_MAGNET_TEASER}}', args.lead_magnet_teaser)
        .replace('{{LEAD_MAGNET_URL}}', args.lead_magnet_url)
        .replace('{{LEAD_MAGNET_CTA}}', args.lead_magnet_cta)
        .replace('{{NEXT_PHOTO}}', next_photo)
        .replace('{{CTA_LINK}}', cta_link))

    if args.out:
        out_path = pathlib.Path(args.out)
    else:
        today = datetime.date.today().isoformat()
        slug = slugify(job.get('title', args.job_id))
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUT_DIR / f'{today}_{slug}.html'

    lib_n = save_to_library(job, diagram_data)
    out_path.write_text(out_html, encoding='utf-8')
    print(f'written: {out_path}  ({len(out_html)} characters, '
          f'{len(json.loads(diagram_data)["nodes"])} diagram nodes, {len(testimonials)} testimonials, library: {lib_n})')


if __name__ == '__main__':
    main()
