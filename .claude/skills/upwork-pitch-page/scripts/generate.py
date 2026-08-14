#!/usr/bin/env python3
"""Fills the universal pitch-page template with job data, an interactive
solution diagram, and your own testimonials. Pure assembly -- the diagram
structure and all copy (Claude, drawn from the job posting and your own
context/experience.md) are decided before this script runs, not inside it.

Page order: headline -> video (full width) -> 3 fit points below it (custom
checkmark icon, not 1/2/3) -> social proof (your real testimonial text) ->
collapsible background/CV -> what I'd build (the diagram) -> how this would
work (tools/timeline/budget/kickoff needs, 4 columns with icons) -> "see what
we can do" (optional lead magnet with an optional cover image) -> footer
links. Testimonials, the CV facts, and the lead-magnet cover are all real
assets you provide -- never invent them. Where something is missing, the
matching section renders an honest "not added yet" line instead of being
padded with invented content.

Usage:
    python3 generate.py <job_id> \\
        --hook "..." \\
        --fit-point "reason 1" --fit-point "reason 2" --fit-point "reason 3" \\
        --graph '{"nodes":[...],"edges":[...]}' \\
        --loom-url "https://loom.com/share/..." \\
        --chapter "..." --chapter "..." --chapter "..." \\
        --tool "GoHighLevel" --tool "n8n" \\
        --timeline "..." \\
        --budget "..." \\
        --kickoff "..." --kickoff "..." \\
        --profile-url "https://www.upwork.com/freelancers/~..." \\
        [--stat "$10K+|Earned on Upwork" --trait "Collaborative" --client "Acme Inc"] \\
        [--youtube-url "https://youtube.com/@you" --site-url "https://you.com"] \\
        [--lead-magnet-url "https://..." --lead-magnet-teaser "..." --lead-magnet-cover /path.jpg] \\
        [--video-length "3 minute"] \\
        [--max-testimonials 8] \\
        [--out /path/to/output.html]

Without --out, the filename is derived from the job title and written to
jobs/<YYYY-MM-DD>_<slug>.html (relative to the repo root -- see CLAUDE.md's
"jobs/" entry, the shared home for generated per-job artifacts).

Exits 1 on a missing job, an invalid image path, or empty required fields --
a silent half-result would be worse than a loud abort with a reason.
"""
import argparse, base64, datetime, json, pathlib, re, sys

# Same folder depth as the skill's own install location
# (.claude/skills/upwork-pitch-page/scripts/generate.py), four levels up from
# this file to the repo root -- mirrors the pattern in
# reference/scripts/upwork_status.py, just counted from a deeper starting
# point. If you move this script, recount the levels; don't guess.
W = pathlib.Path(__file__).resolve().parents[4]
JOBS = W / 'context/.upwork_jobs.json'
ASSETS = pathlib.Path(__file__).resolve().parent.parent / 'assets'
TEMPLATE = ASSETS / 'template.html'
# Your own data, not shipped with the skill -- see context/testimonials.json.example.
TESTIMONIALS_FILE = W / 'context/testimonials.json'
DIAGRAM_JS_FILE = ASSETS / 'diagram.js'
LOGO_DIR = ASSETS / 'logos'
# Every graph generated lands here. A library that has to be maintained by
# hand stays empty -- so it fills up as a side effect of every real run.
LIBRARY = pathlib.Path(__file__).resolve().parent.parent / 'library'
# The source image for the hero dither: a packaged default decorative asset
# (an abstract ink-plume drawing, no identifying content). The dither
# constants in template.html are tuned to this specific image's luminance
# range -- swap it for your own moody/high-contrast image only if you also
# retune those constants, otherwise the raster reads as flat noise.
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

# A shared style for any section that has nothing real to show yet -- reused
# by testimonials, the CV, and the portfolio block so "not added" always
# reads the same way instead of three different placeholder treatments.
EMPTY_NOTE_CLASS = 'testimonials-empty'


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


def guess_mime(path_str):
    return 'image/png' if pathlib.Path(path_str).suffix.lower() == '.png' else 'image/jpeg'


def load_testimonials(max_count):
    if not TESTIMONIALS_FILE.is_file():
        return []
    items = json.loads(TESTIMONIALS_FILE.read_text(encoding='utf-8'))
    return items[:max_count] if max_count else items


def stars_html(rating):
    full = round(rating)
    return '★' * full + '☆' * (5 - full)


def parse_pair(raw, flag):
    """Splits "value|label" on the first '|'. Aborts loudly on a missing pipe
    rather than silently swallowing the label -- a malformed --stat/--background
    would otherwise render as a stat with no caption."""
    if '|' not in raw:
        print(f'ABORT: --{flag} needs the form "value|label", got: {raw!r}', file=sys.stderr)
        sys.exit(1)
    value, label = raw.split('|', 1)
    return value.strip(), label.strip()


# Must match shapeFor() in diagram.js -- an unknown kind would silently land
# as a plain box there; here it aborts loudly instead.
GRAPH_KINDS = {'source', 'step', 'sink', 'service', 'decision', 'note',
               'datastore', 'milestone', 'actor'}
GRAPH_OWNERS = {'you', 'client', 'thirdparty'}


def build_graph(spec):
    """Any graph, not just a fixed chain.

    For a real implementation plan, "trigger -> steps -> destination" isn't
    enough -- real plans branch, run parallel tracks, and have phases. Claude
    writes the structure as JSON, not SVG -- same expressive power, but
    checkable, and the layout can't break because the rendering engine does
    it, not free-hand text.

    Shape:
      {"nodes":[{"id":"a","label":"...","kind":"source"}, ...],
       "edges":[{"from":"a","to":"b","label":"if qualified","dashed":true}, ...]}
    Without x/y the engine lays it out automatically.
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
            print(f'ABORT: node without id/label: {n}', file=sys.stderr)
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
                print(f'ABORT: edge points to unknown node "{e.get(side)}".', file=sys.stderr)
                sys.exit(1)

    # Groups (phases): check every member id exists. A typo would otherwise
    # silently draw an empty or half-populated frame.
    groups = g.get('groups') or []
    for grp in groups:
        if not grp.get('label'):
            print(f'ABORT: group without label: {grp}', file=sys.stderr)
            sys.exit(1)
        for nid in grp.get('nodes') or []:
            if nid not in ids:
                print(f'ABORT: group "{grp["label"]}" names unknown node "{nid}".',
                      file=sys.stderr)
                sys.exit(1)

    data = json.dumps({'nodes': nodes, 'edges': g.get('edges') or [], 'groups': groups},
                      ensure_ascii=False)
    fallback = '\n            '.join(f'<li>{n["label"]}</li>' for n in nodes)
    return data, fallback


def build_diagram(source, steps, sink, services):
    """Node list + no-JS fallback. Layout is exclusively the template's job --
    this only builds the list, so there's never a second layout implementation
    that can drift out of sync with the first."""
    if not 1 <= len(steps) <= 4:
        print(f'ABORT: expected 1 to 4 --step, got: {len(steps)}', file=sys.stderr)
        sys.exit(1)
    if len(services) > 2:
        print(f'ABORT: max 2 --service, got: {len(services)}', file=sys.stderr)
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

    # One single node list. The engine tells them apart via `kind`; a second
    # list next to it meant the services never actually showed up.
    data = json.dumps({'nodes': nodes + svc}, ensure_ascii=False)
    fallback = '\n            '.join(
        f'<li>{n["label"]}</li>' for n in nodes)
    if svc:
        fallback += '\n            ' + '\n            '.join(
            f'<li>{s["label"]} (supporting service)</li>' for s in svc)
    return data, fallback


def logos_json(nodes):
    """Only embed the logos this graph actually references.

    Shipping all 20 costs 84 KB on every page, of which two get used. The
    <title> from the Simple Icons file is stripped, otherwise the browser
    shows a brand-name tooltip on hover over the node."""
    want = {n.get('logo') for n in nodes if n.get('logo')}
    out = {}
    for slug in sorted(want):
        f = LOGO_DIR / f'{slug}.svg'
        if not f.is_file():
            print(f'  Note: no logo "{slug}" -- node shows its shape symbol only.', file=sys.stderr)
            continue
        svg = f.read_text(encoding='utf-8')
        inner = re.sub(r'^.*?<svg[^>]*>|</svg>\s*$', '', svg, flags=re.S)
        inner = re.sub(r'<title>.*?</title>', '', inner, flags=re.S)
        out[slug] = inner.strip()
    return json.dumps(out, ensure_ascii=False)


def save_to_library(job, data):
    """Save every generated graph, so the next pitch doesn't start from zero.
    Plus an index next to it, because a folder of 40 JSON files isn't
    searchable and so wouldn't get used."""
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


def cv_html(args):
    """Builds the whole collapsible "More about my background" block from
    context/experience.md facts, passed in as flags. Every sub-block is
    optional and simply omitted if you didn't pass it -- if NONE of them were
    passed, the block renders one honest "not added yet" line instead of an
    empty, oddly-shaped panel."""
    stats = [parse_pair(s, 'stat') for s in args.stat]
    background = [parse_pair(b, 'background') for b in args.background]
    parts = []

    if stats:
        rows = '\n            '.join(f'<div><strong>{v}</strong><span>{l}</span></div>' for v, l in stats)
        parts.append(f'<div class="cv-stats">\n            {rows}\n          </div>')

    if args.trait:
        tags = '\n            '.join(f'<span>{t}</span>' for t in args.trait)
        parts.append('<p class="cv-sub">What clients said after the job was done</p>\n'
                      f'          <div class="cv-traits">\n            {tags}\n          </div>')

    if args.client:
        line = ' · '.join(args.client)
        if args.client_note:
            line += f', {args.client_note}'
        parts.append(f'<p class="cv-sub">Businesses I’ve built for</p>\n'
                      f'          <p class="cv-clients">{line}</p>')

    if background:
        items = '\n            '.join(f'<li><strong>{r}</strong> at {i}</li>' for r, i in background)
        parts.append(f'<p class="cv-sub">Background</p>\n          <ul class="cv-list">\n            {items}\n          </ul>')

    if args.languages:
        parts.append(f'<p class="cv-lang">{args.languages}</p>')

    if parts:
        body = '\n          '.join(parts)
    else:
        body = f'<p class="{EMPTY_NOTE_CLASS}">Background details not added yet -- fill in context/experience.md.</p>'

    return ('<details class="cv">\n'
            '        <summary>More about my background</summary>\n'
            '        <div class="cv-body">\n'
            f'          {body}\n'
            '        </div>\n'
            '      </details>')


def portfolio_html(args):
    """The optional "more of my work" block. A single link, not a shipped
    grid of your own thumbnails -- keep your own images out of a template
    other people run."""
    if args.youtube_url:
        return ('<p class="yt-note">A few recent examples, if you want to see more of the work.</p>\n'
                f'      <a class="yt-more" href="{args.youtube_url}" target="_blank" rel="noopener" data-rise>\n'
                '        See more of my work <span class="arrow" aria-hidden="true">→</span>\n'
                '      </a>')
    return f'<p class="{EMPTY_NOTE_CLASS}">Portfolio link not added yet.</p>'


def proof_link_html(args):
    """The optional bonus row pointing at a workspace of other diagrams
    you've mapped (Whimsical, Miro, whatever you use). Omitted entirely when
    you haven't set one -- unlike testimonials/CV/portfolio this isn't a core
    trust section, so it can just not be there."""
    if not args.proof_link_url:
        return ''
    return ('<a class="proof-link" href="' + args.proof_link_url + '" target="_blank" rel="noopener">\n'
            '        <svg class="proof-mark" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">\n'
            '          <rect x="3" y="4" width="7" height="7" rx="2" stroke="currentColor" stroke-width="1.7"/>\n'
            '          <rect x="14" y="4" width="7" height="7" rx="2" stroke="currentColor" stroke-width="1.7"/>\n'
            '          <rect x="8.5" y="14" width="7" height="6" rx="2" stroke="currentColor" stroke-width="1.7"/>\n'
            '          <path d="M6.5 11v1.5h11V11M12 12.5V14" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>\n'
            '        </svg>\n'
            '        <span class="proof-copy">\n'
            '          <strong>Systems I’ve mapped for other clients</strong>\n'
            '          <span>The same kind of plan, in my own workspace</span>\n'
            '        </span>\n'
            '        <span class="arrow" aria-hidden="true">→</span>\n'
            '      </a>')


def footer_links_html(args):
    """Upwork profile is always shown (it's required); YouTube and your own
    site are only added when set, instead of a fixed three-link row."""
    links = [f'<a href="{args.profile_url}" target="_blank" rel="noopener">Upwork profile</a>']
    if args.youtube_url:
        links.append(f'<a href="{args.youtube_url}" target="_blank" rel="noopener">YouTube</a>')
    if args.site_url:
        links.append(f'<a href="{args.site_url}" target="_blank" rel="noopener">My site</a>')
    return '\n      <span class="dot">·</span>\n      '.join(links)


def showcase_html(args):
    """The lead-magnet showcase. With a cover image it's the tilted-book
    treatment plus the "real example, not fabricated" disclosure note; without
    one, the "showcase-solo" layout centers the copy alone instead of leaving
    a blank 290px gap where the image would sit, and the note is dropped too
    -- it only makes sense once there's an actual image it's disclosing."""
    if args.lead_magnet_cover:
        src = img_data_uri(args.lead_magnet_cover, mime=guess_mime(args.lead_magnet_cover))[0]
        cover = ('<div class="cover-stage" data-cover>\n'
                  '          <div class="cover-book">\n'
                  '            <span class="cover-sheet s2"></span>\n'
                  '            <span class="cover-sheet s1"></span>\n'
                  f'            <img class="cover-face" src="{src}" alt="Cover of a past deliverable">\n'
                  '          </div>\n'
                  '        </div>')
        note = '<p class="note" data-rise data-d="3">Real example, built for another client. Yours would look just as sharp.</p>'
        return 'showcase', cover, note
    return 'showcase showcase-solo', '', ''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('job_id')
    ap.add_argument('--hook', required=True,
                     help='the page\'s only headline. Pattern: "What your <concrete system> would '
                          'look like" -- must clearly reference THIS job. No subhead, no pill, no '
                          'name banner above it -- the page opens straight on the headline.')
    ap.add_argument('--fit-point', action='append', required=True,
                     help='one reason this job fits you, give exactly 3')
    # The diagram is not a static image -- it's a node list. The template
    # draws an SVG from it at runtime: sharp at any size, follows the theme
    # tokens, and the client can pan/zoom it and even add their own steps.
    # The grammar is fixed (trigger -> steps -> destination, plus services
    # underneath) so nothing can overlap.
    ap.add_argument('--graph',
                     help='the full graph as JSON or a path to a .json file -- for anything with '
                          'branches, parallel tracks, or phases. Mutually exclusive with '
                          '--source/--step/--sink.')
    ap.add_argument('--source', help='where the process starts, one node (simple chain)')
    ap.add_argument('--step', action='append',
                     help='one processing step, give 2 to 4 (simple chain)')
    ap.add_argument('--sink', help='where the result lands, one node (simple chain)')
    ap.add_argument('--service', action='append', default=[],
                     help='a supporting service, optionally pinned to a step with @<index>, '
                          'e.g. "Claude API@2". Max 2.')
    ap.add_argument('--loom-url', default='')
    ap.add_argument('--video-length', default='3 minute')
    ap.add_argument('--tool', action='append', required=True,
                     help='a tool you\'d use for this job, repeatable')
    ap.add_argument('--timeline', required=True, help='a short, honest time estimate for this job')
    ap.add_argument('--budget', required=True,
                     help='a short, honest budget framing for this job (a range, not a quote to the dollar)')
    ap.add_argument('--kickoff', action='append', required=True,
                     help='what you need from the client to get started, repeatable')
    ap.add_argument('--chapter', action='append', required=True,
                     help='what the Loom video covers, in order, give 3-4. Shown as a progress '
                          'bar under the player, so what\'s in it is visible before the click.')
    ap.add_argument('--max-testimonials', type=int, default=0,
                     help='0 = use every entry in context/testimonials.json (default)')
    ap.add_argument('--lead-magnet-url', default='')
    ap.add_argument('--lead-magnet-teaser', default='')
    ap.add_argument('--lead-magnet-cta', default='Get it here')
    ap.add_argument('--lead-magnet-cover', default='',
                     help='optional path to a cover image (a past deliverable, a report, '
                          'anything that shows the quality of your work). Left empty, the '
                          'showcase section runs copy-only instead of a blank image slot.')
    ap.add_argument('--profile-url', required=True,
                     help='your Upwork profile URL. Read it from the Portfolio links section of '
                          'context/experience.md and pass it here -- there is no built-in '
                          'default, on purpose.')
    ap.add_argument('--youtube-url', default='',
                     help='optional YouTube or portfolio link (also from context/experience.md\'s '
                          'Portfolio links section). Drives the "more of my work" section and the '
                          'footer YouTube link; left empty, both render an honest placeholder / '
                          'are simply omitted.')
    ap.add_argument('--site-url', default='',
                     help='optional link to your own site or a second product, shown in the '
                          'footer (context/experience.md, Portfolio links).')
    ap.add_argument('--proof-link-url', default='',
                     help='optional link to a workspace (Whimsical, Miro, ...) with more diagrams '
                          'you\'ve mapped for other clients. Omitted entirely when unset.')
    ap.add_argument('--stat', action='append', default=[],
                     help='one track-record number for the CV, as "value|label", e.g. '
                          '"$10K+|Earned on Upwork". Repeatable. Source: context/experience.md.')
    ap.add_argument('--trait', action='append', default=[],
                     help='one client-sourced trait tag for the CV (e.g. "Collaborative"). Repeatable.')
    ap.add_argument('--client', action='append', default=[],
                     help='one notable past client/company name for the CV. Repeatable.')
    ap.add_argument('--client-note', default='',
                     help='optional trailing clause appended after the --client list, '
                          'e.g. "plus 15+ smaller builds across GoHighLevel and n8n."')
    ap.add_argument('--background', action='append', default=[],
                     help='one background/employment/education line for the CV, as '
                          '"role|institution", e.g. "MBA, Marketing & AI|Your University". Repeatable.')
    ap.add_argument('--languages', default='', help='optional languages line for the CV.')
    ap.add_argument('--out')
    args = ap.parse_args()

    if len(args.fit_point) != 3:
        print(f'ABORT: expected exactly 3 --fit-point, got: {len(args.fit_point)}', file=sys.stderr)
        sys.exit(1)
    if not args.tool:
        print('ABORT: at least 1 --tool expected.', file=sys.stderr)
        sys.exit(1)
    if not args.kickoff:
        print('ABORT: at least 1 --kickoff expected.', file=sys.stderr)
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
    dither_src = img_data_uri(str(DITHER_FILE))[0] if DITHER_FILE.is_file() else ''

    if not args.loom_url:
        args.loom_url = '#loom-link-missing'

    fit_html = '\n        '.join(
        f'<li>{FIT_ICON}<span>{p}</span></li>'
        for p in args.fit_point)

    tools_html = '\n            '.join(f'<li>{t}</li>' for t in args.tool)
    kickoff_html = '\n            '.join(f'<li>{k}</li>' for k in args.kickoff)
    chapters_html = '\n        '.join(
        f'<div class="chapter"><span>{c}</span></div>' for c in args.chapter)

    testimonials = load_testimonials(args.max_testimonials)
    if testimonials:
        testimonials_html = '<div class="testimonials">\n          ' + '\n          '.join(
            f'<div class="testimonial"><p class="quote">"{t["quote"]}"</p>'
            f'<p class="meta"><span class="stars">{stars_html(t["rating"])}</span>'
            f'<span class="job">{t["job"]}</span></p></div>'
            for t in testimonials) + '\n        </div>'
    else:
        testimonials_html = f'<p class="{EMPTY_NOTE_CLASS}">Testimonials not added yet.</p>'

    if not args.lead_magnet_url:
        args.lead_magnet_url = '#lead-magnet-missing'
        if not args.lead_magnet_teaser:
            args.lead_magnet_teaser = 'Lead magnet not added yet.'
    elif not args.lead_magnet_teaser:
        print('ABORT: --lead-magnet-url set, but --lead-magnet-teaser is missing.', file=sys.stderr)
        sys.exit(1)

    showcase_class, cover_block, showcase_note = showcase_html(args)

    tpl = TEMPLATE.read_text(encoding='utf-8')
    out_html = (tpl
        .replace('{{JOB_TITLE}}', job.get('title', ''))
        .replace('{{HOOK}}', args.hook)
        .replace('{{LOOM_URL}}', args.loom_url)
        .replace('{{VIDEO_LENGTH}}', args.video_length)
        .replace('{{FIT_POINTS}}', fit_html)
        .replace('{{CV_BLOCK}}', cv_html(args))
        .replace('{{TOOLS}}', tools_html)
        .replace('{{TIMELINE}}', args.timeline)
        .replace('{{BUDGET}}', args.budget)
        .replace('{{KICKOFF_ITEMS}}', kickoff_html)
        .replace('{{CHAPTERS}}', chapters_html)
        .replace('{{DITHER_SRC}}', dither_src)
        .replace('{{TESTIMONIALS_BLOCK}}', testimonials_html)
        .replace('{{DIAGRAM_DATA}}', diagram_data)
        .replace('{{DIAGRAM_FALLBACK}}', diagram_fallback)
        .replace('{{DIAGRAM_JS}}', DIAGRAM_JS_FILE.read_text(encoding='utf-8')
                 .replace('{{LOGOS_JSON}}', logos_json(json.loads(diagram_data)['nodes'])))
        .replace('{{PROOF_LINK_BLOCK}}', proof_link_html(args))
        .replace('{{PORTFOLIO_BLOCK}}', portfolio_html(args))
        .replace('{{SHOWCASE_CLASS}}', showcase_class)
        .replace('{{COVER_BLOCK}}', cover_block)
        .replace('{{SHOWCASE_NOTE}}', showcase_note)
        .replace('{{LEAD_MAGNET_TEASER}}', args.lead_magnet_teaser)
        .replace('{{LEAD_MAGNET_URL}}', args.lead_magnet_url)
        .replace('{{LEAD_MAGNET_CTA}}', args.lead_magnet_cta)
        .replace('{{FOOTER_LINKS}}', footer_links_html(args))
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
    print(f'written: {out_path}  ({len(out_html)} chars, '
          f'{len(json.loads(diagram_data)["nodes"])} diagram nodes, {len(testimonials)} testimonials, library: {lib_n})')


if __name__ == '__main__':
    main()
