#!/usr/bin/env python3
"""Renders context/today.html from context/STATUS.md and context/.upwork_jobs.json.

The dashboard is a VIEW only. It never writes anything back — every button on
it just copies a ready sentence to the clipboard for you to paste into your
Claude Code chat, which then runs the actual command (upwork_status.py, or
editing STATUS.md). Re-run this script any time; it's fully derived, never
hand-edited.

Usage:
    python3 reference/scripts/render_dashboard.py [--date YYYY-MM-DD]
"""
import re, html, json, pathlib, datetime, argparse, subprocess

W = pathlib.Path(__file__).resolve().parents[2]
TPL = W / 'context/today_template.html'
OUT = W / 'context/today.html'

# A fresh clone has none of the state files yet, and five empty tabs look broken
# rather than new. So each one falls back to demo/, and the page says so in a
# banner: a populated dashboard nobody can mistake for their own. The setup
# deletes demo/ as its last step, and from then on there is no fallback left.
DEMO = W / 'demo'
DEMO_USED = set()


def state(name):
    """context/<name> if it exists, otherwise demo/<name>."""
    real = W / 'context' / name
    if real.exists():
        return real
    fallback = DEMO / name
    if fallback.exists():
        DEMO_USED.add(name)
        return fallback
    return real                       # let the caller handle the missing file


CONFIG = state('config.yaml')
UPWORK_JOBS = state('.upwork_jobs.json')

ap = argparse.ArgumentParser()
ap.add_argument('--date', help='YYYY-MM-DD, otherwise today')
args = ap.parse_args()
TODAY = datetime.date.fromisoformat(args.date) if args.date else datetime.date.today()


def _cfg():
    """Tiny hand-rolled reader for the handful of keys we need — avoids a YAML
    dependency for a config file that is never more than names, ids and a goal.

    Two things it has to survive, both found by running it against a real config:

    1. **Trailing comments.** `name: "Alex"   # e.g. "Alex Miller"` used to fail
       outright, because the old pattern anchored to end-of-line and choked on the
       quotes inside the comment. The dashboard then rendered with no name and no
       explanation. Comments are stripped first now, quote-aware so a `#` inside a
       value survives.
    2. **One level of nesting.** Keys indented under a parent (`user:` → `name:`)
       are read as if they were flat. That is deliberate: this file is shared with
       a workspace whose config nests, and a key name is unique across both. First
       occurrence wins, so a top-level key beats a nested one of the same name.
    """
    out = {}
    if not CONFIG.is_file():
        return out
    for ln in CONFIG.read_text(encoding='utf-8').splitlines():
        # Strip a trailing comment, but not a '#' inside a quoted value.
        stripped, quoted = [], False
        for ch in ln:
            if ch == '"':
                quoted = not quoted
            if ch == '#' and not quoted:
                break
            stripped.append(ch)
        m = re.match(r'^([a-z_]+):\s*"?(.*?)"?\s*$', ''.join(stripped).strip())
        if m and m.group(2) and m.group(1) not in out:
            out[m.group(1)] = m.group(2)
    return out


CFG = _cfg()
# The raw text as well, for the few settings read by pattern rather than by key.
try:
    CFG_TEXT = CONFIG.read_text(encoding='utf-8')
except OSError:
    CFG_TEXT = ''
# The system is English throughout. This constant stays because the tab renderers
# and the template read it, but there is one language and nothing to choose.
LANG = 'en'
USER_NAME = CFG.get('name', '')

# Bilingual UI strings for the Heute/Today tab. Kept minimal on purpose — this
# is a two-tab tool, not the full personal cockpit it was extracted from.
TXT = {
    'en': dict(
        wd=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
        mon=['', 'January', 'February', 'March', 'April', 'May', 'June', 'July',
             'August', 'September', 'October', 'November', 'December'],
        tab_projects='Projects', no_projects='No projects in context/PROJECTS.md yet.',
        blocked='Blocked',
        cats={'deep-work': 'Deep Work', 'quick-win': 'Quick Win', 'comms': 'Communication',
              'prep': 'Preparation', 'admin': 'Admin'},
        datum='{wd}, {d} {mon} {y}', offen='open', wartet='waiting on {}',
        todos='Open to-dos', no_tasks='No open tasks yet — add them to context/STATUS.md.',
        quad={'q1': 'urgent + important', 'q2': 'not urgent + important',
              'q3': 'urgent + not important', 'q4': 'not urgent + not important'},
        wd_short=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        tab_today='Today', tab_upwork='Upwork', title='Automatable OS',
        demo_title='This is example data.',
        demo_body='You have none of your own yet, so the dashboard is showing the demo/ folder to give you something to look at. The setup deletes it, or you can, with',
        tab_onboarding='Onboarding',
        onb_hint='What the first run does: the five phases, which tools get connected and why, and where the keys end up.',
        onb_missing='ONBOARDING.html is missing from the folder. The copy is incomplete.',
        tab_system='System',
        f_all='All', f_due='Due',
        tab_tooling='Tooling',
        tool_hint='What this machine actually has: skills, CLIs, connections, plugins, keys. Read from the machine, not from a list somebody maintains.',
        tool_noscript='reference/scripts/inventory.js is missing. The copy is incomplete.',
        tool_nonode='This needs Node.js, which is not installed here. With Node, this tab shows which tools and connections are actually in place.',
        tool_failed='The tooling could not be read.',
        no_briefing='No briefing for today yet. Say “good morning” and it appears here.',
        sys_note='What this system does and why each step is shaped the way it is. '
                 'The same page sits in the folder as SYSTEM.html.',
        sys_missing='SYSTEM.html is missing from the folder. The copy is incomplete, fetch that file from the repo.',
        uw_hint='Pipeline: Applied → In contact → Offer sent → Won. The buttons on a row or card '
                'only copy a chat sentence — pasting it and sending it is what actually moves the '
                'job, or run <code>python3 reference/scripts/upwork_status.py set &lt;id&gt; '
                '&lt;status&gt;</code> yourself.',
    ),
}[LANG]
WD, MON, CATS, QUAD = TXT['wd'], TXT['mon'], TXT['cats'], TXT['quad']
# Short chip labels. The full wording lives in QUAD and is the tooltip.
QUAD_SHORT = {'q1': 'Q1', 'q2': 'Q2', 'q3': 'Q3', 'q4': 'Q4'}


def esc(s):
    return html.escape(s or '', quote=True)


def md(s):
    t = html.escape(s or '', quote=True)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', t)
    return t


def quadrant(cat, due):
    """Eisenhower: urgent from the due date, important from the category."""
    important = cat in ('deep-work', 'admin', 'prep')
    urgent = False
    if due:
        try:
            urgent = datetime.date.fromisoformat(due) <= TODAY + datetime.timedelta(days=7)
        except ValueError:
            pass
    if urgent and important:
        return 'q1'
    if important:
        return 'q2'
    if urgent:
        return 'q3'
    return 'q4'


# ─────────────────────────────────────────── context/STATUS.md
def parse_status():
    """Tasks live under '## Tasks (open)' / '## Tasks (offen)', grouped by a '### Project'
    heading. One task = '- [ ] **headline** (due DD.MM.) #category', optional indented
    context line below it. Same format documented in context/STATUS.md.example."""
    p = state('STATUS.md')
    if not p.is_file():
        return []
    t = p.read_text(encoding='utf-8')
    tasks, proj, in_open, in_code = [], None, False, False
    lines = t.splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().startswith('```'):
            in_code = not in_code
            continue
        if in_code:
            continue
        if ln.startswith('## '):
            in_open = ln.strip().startswith(('## Tasks (offen)', '## Tasks (open)'))
            continue
        if ln.startswith('### '):
            proj = ln[4:].split('(')[0].strip()
            continue
        if not in_open or not re.match(r'^\s*- \[ \]', ln):
            continue
        raw = re.sub(r'^\s*- \[ \]\s*', '', ln)
        b = re.search(r'\*\*(.+?)\*\*', raw)
        text = (b.group(1) if b else raw)
        text = re.sub(r'\s*\((?:since|seit):?[^)]*\)', '', text).strip()
        waits = re.match(r'^\((?:wartet auf|waiting on) ([^)]+)\)', text)
        status = 'waiting' if waits else 'open'
        stat_lbl = TXT['wartet'].format(waits.group(1)) if waits else TXT['offen']
        # A due date drives the whole urgent/important sort, so a date that does
        # not parse is worse than no date: the task quietly loses its deadline and
        # nobody is told. ISO is the documented form because it is unambiguous in
        # every country and carries its year; DD.MM. still parses so older files
        # keep working, and anything else is reported rather than dropped.
        due, due_unparsed = '', ''
        m = re.search(r'\((?:bis|due) (\d{4})-(\d{2})-(\d{2})\)', raw)
        if m:
            due = f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
        else:
            m = re.search(r'\((?:bis|due) (\d{2})\.(\d{2})\.\)', raw)
            if m:
                d, mo = int(m.group(1)), int(m.group(2))
                y = TODAY.year + (1 if (mo, d) < (TODAY.month, TODAY.day) else 0)
                due = f'{y}-{mo:02d}-{d:02d}'
            else:
                bad = re.search(r'\((?:bis|due) ([^)]+)\)', raw)
                if bad:
                    due_unparsed = bad.group(1).strip()
        cm = re.search(r'#(deep-work|quick-win|komm|comms|prep|admin)', raw)
        cat = ('comms' if cm and cm.group(1) == 'komm' else cm.group(1) if cm else 'deep-work')
        text = re.sub(r'\s*#(deep-work|quick-win|komm|comms|prep|admin)', '', text)
        text = re.sub(r'^\((?:wartet auf|waiting on) [^)]+\)\s*', '', text)
        text = re.sub(r'\s*\((?:bis|due) [^)]+\)', '', text).strip()
        note = ''
        if i + 1 < len(lines) and lines[i + 1].startswith(('  ', '\t')) \
                and not re.match(r'^\s*- \[', lines[i + 1]):
            note = lines[i + 1].strip()
        tasks.append(dict(text=text[:180], proj=proj or 'General', status=status,
                          stat_lbl=stat_lbl, due=due, cat=cat, note=note[:400],
                          due_unparsed=due_unparsed))
    return tasks


def parse_projects():
    """One card per `## ` block in PROJECTS.md.

    Setup asks for the user's projects and writes them here. Without this the
    system would ask and then never show them back, which is worse than not
    asking. Blocks whose heading marks them as history or dormant are skipped —
    the dashboard is for what is running.

    Field labels are matched in both languages, because the workspace this file
    is shared with writes German ones.
    """
    p = state('PROJECTS.md')
    if not p.is_file():
        return []
    out = []
    for blk in re.split(r'\n## ', p.read_text(encoding='utf-8'))[1:]:
        name = blk.splitlines()[0].strip()
        if name.lower().startswith(('history', 'historie', 'dormant', 'ruhend', 'archive')):
            continue
        if name.startswith('['):
            continue                      # untouched template placeholder

        def f(*keys):
            m = re.search(rf'\*\*(?:{"|".join(keys)}):\*\*\s*(.+)', blk)
            v = m.group(1).strip() if m else ''
            return '' if v.startswith('[') else v      # unfilled placeholder

        out.append(dict(name=name, purpose=f('Purpose', 'Zweck'), status=f('Status'),
                        phase=f('Phase') or '', blocker=f('Blocker'),
                        timeline=f('Timeline', 'Zeitachse'),
                        stakeholder=f('Stakeholder'),
                        origin=f('Where it came from', 'Herkunft')))
    return out


def render_projects():
    projects = parse_projects()
    if not projects:
        return f'<p class="sub">{esc(TXT["no_projects"])}</p>'
    cards = []
    for p in projects:
        meta = ' · '.join(x for x in (p['phase'], p['timeline']) if x)
        parts = ['<div class="pr-card"><div class="pr-head">',
                 f'<span class="pr-name">{esc(p["name"])}</span>']
        if meta:
            parts.append(f'<span class="pr-meta">{esc(meta)}</span>')
        parts.append('</div>')
        # md(), not esc(): these lines are prose the user wrote, and they contain
        # `code` spans naming files. Escaped, the backticks showed up raw.
        if p['purpose']:
            parts.append(f'<p class="pr-purpose">{md(p["purpose"])}</p>')
        if p['status']:
            parts.append(f'<p class="pr-status">{md(p["status"])}</p>')
        # Who it is for and where it came from. Without the origin line, a project
        # that came out of a won job cannot say so, and the link upwork-won makes
        # is invisible from this side.
        foot = ' · '.join(x for x in (p['stakeholder'], p['origin']) if x)
        if foot:
            parts.append(f'<p class="pr-foot">{md(foot)}</p>')
        if p['blocker']:
            parts.append(f'<div class="pr-blocker">{esc(TXT["blocked"])}: {esc(p["blocker"])}</div>')
        parts.append('</div>')
        cards.append(''.join(parts))
    return f'<div class="pr-grid">{"".join(cards)}</div>'


def render_tasks():
    tasks = parse_status()
    if not tasks:
        return f'<p class="sub">{esc(TXT["no_tasks"])}</p>'
    tasks = sorted(tasks, key=lambda t: {'q1': 0, 'q2': 1, 'q3': 2, 'q4': 3}[quadrant(t['cat'], t['due'])])
    rows = []
    for t in tasks:
        quad = quadrant(t['cat'], t['due'])
        # Show the date the user wrote, not a reformatted one. If it did not parse,
        # say so in the column instead of leaving it blank: a blank cell reads as
        # "no deadline", which is exactly the wrong conclusion.
        due_lbl = t['due'] if t['due'] else ''
        if not due_lbl and t.get('due_unparsed'):
            due_lbl = f'<span class="c-due-bad" title="Not understood as a date, so this task '\
                      f'is not counted as urgent. Use (due YYYY-MM-DD).">{esc(t["due_unparsed"])} ?</span>'
        note_div = f'<div class="t-note">{md(t["note"])}</div>' if t['note'] else ''
        rows.append(
            f'<li data-quadrant="{quad}" data-proj="{esc(t["proj"])}"'
            f' data-due="{"1" if t["due"] and t["due"] <= TODAY.isoformat() else ""}"><span class="c-quad {quad}" title="{esc(QUAD[quad])}">{quad.upper()}</span>'
            f'<span class="t-text">{md(t["text"])}</span>'
            f'<span class="c-proj">{esc(t["proj"])}</span>'
            f'<span class="c-cat">{esc(CATS.get(t["cat"], t["cat"]))}</span>'
            f'<span class="c-status">{esc(t["stat_lbl"])}</span>'
            f'<span class="c-due">{due_lbl}</span>{note_div}</li>'
        )
    # Filters, built from what is actually in the list rather than from a fixed
    # set: a chip for a quadrant with no tasks behind it is a dead control, and
    # four of those teach you to stop looking at the row. Same mechanism as the
    # Upwork tab, so there is one filter behaviour in this file and not two.
    present = [q for q in ('q1', 'q2', 'q3', 'q4') if any(
        quadrant(t['cat'], t['due']) == q for t in tasks)]
    projects = sorted({t['proj'] for t in tasks if t['proj'] and t['proj'] != 'General'})
    chips = [('all', TXT['f_all'])]
    if any(t['due'] and t['due'] <= TODAY.isoformat() for t in tasks):
        chips.append(('due', TXT['f_due']))
    # Only when there is something to choose between. One quadrant chip filters to
    # exactly what 'All' already shows, which is the dead control this list was
    # built from `present` to avoid in the first place.
    if len(present) > 1:
        chips += [(q, QUAD_SHORT[q]) for q in present]
    if len(projects) > 1:
        chips += [(f'p:{p}', p) for p in projects]
    bar = '<div class="uw-filterbar t-filterbar">' + ''.join(
        f'<button type="button" class="pill t-filterpill{" active" if k == "all" else ""}"'
        f' data-tfilter="{esc(k)}" title="{esc(lbl)}">{esc(lbl)}</button>'
        for k, lbl in chips) + '</div>'
    return bar + f'<ul class="task-list">{"".join(rows)}</ul>'


# ─────────────────────────────────────────── add-ons
CLOSED_STATUSES = ('hired', 'rejected', 'archived', 'ignored')
UPWORK_JOBS = state('.upwork_jobs.json')

# An add-on is one file in reference/addons/ that exposes render() -> HTML.
# The base hands it the helpers it needs and takes back one block of markup; it
# never imports an add-on by name and never breaks when one is missing. That is
# what keeps Upwork optional and what the next add-on will dock into.
ADDONS = W / 'reference/addons'
_ADDON_EXPORTS = ('W', 'OUT', 'CONFIG', 'TODAY', 'TXT', 'LANG', 'DEMO_USED',
                  'CLOSED_STATUSES', 'UPWORK_JOBS', 'esc', 'md', 'state')


def addon_tab(name, label, body):
    """One add-on's tab button and pane, or two empty strings when it is absent.

    This is what "optional" has to mean in an interface: no button, no pane, no
    trace. A tab that is present but empty is worse than none, because the reader
    has to click it to find out that it was never for them.
    """
    if not body:
        return '', ''
    btn = f'    <button class="tab" data-tab="{esc(name)}">{esc(label)}</button>'
    pane = (f'  <div class="tabpane" id="pane-{esc(name)}" hidden>\n'
            f'{body}\n'
            f'  </div><!-- /pane-{esc(name)} -->')
    return btn, pane


def addon_names():
    """Every add-on present, in a stable order. Files and packages both count.

    A one-file add-on was enough while Upwork was the only one: it renders a tab
    out of a JSON file the skills maintain. An add-on that carries a real machine
    (cold mail brings a scraper, a benchmark and a mail builder) does not fit in
    one file, and forcing it to would put its pipeline somewhere else than itself.
    So an add-on is `<name>.py` OR `<name>/__init__.py`, and the rest of the
    contract is unchanged.

    Sorted, because tab order should not depend on filesystem order -- that
    differs between machines and would reshuffle the interface for no reason.
    """
    if not ADDONS.is_dir():
        return []
    namen = {p.stem for p in ADDONS.glob('*.py') if p.stem != '__init__'}
    namen |= {p.name for p in ADDONS.iterdir()
              if p.is_dir() and not p.name.startswith('_') and (p / '__init__.py').is_file()}
    return sorted(namen)


def load_addon(name):
    """The add-on's module, or None when it is off or absent.

    Separated from rendering (23.08.2026) because the base needs more from an
    add-on than its HTML: the tab's label and the line above it belong to the
    add-on, not to the base's own translation table. As long as the base held
    those, adding a second add-on meant editing the base -- which is exactly what
    the contract says must not happen.
    """
    # One switch, not two. `<name>_enabled: false` in config.yaml is what morning,
    # setup and the session hook already read; the dashboard has to agree with them
    # or the tab outlives the answer the user gave during setup.
    if f'{name}_enabled: false' in CFG_TEXT:
        return None
    datei = ADDONS / f'{name}.py'
    paket = ADDONS / name / '__init__.py'
    pfad = datei if datei.is_file() else (paket if paket.is_file() else None)
    if pfad is None:
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location(f'addon_{name}', pfad)
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__.update({k: globals()[k] for k in _ADDON_EXPORTS})
    spec.loader.exec_module(mod)
    return mod


def addon_html(name, fallback=''):
    """Render one add-on's tab, or return the fallback if it is not installed.

    A missing add-on is the normal case, not an error: the base ships without
    any. A broken one is different and says so in the tab rather than taking the
    whole render down with it, because a dashboard that refuses to build tells
    you nothing about the day.
    """
    try:
        mod = load_addon(name)
        return mod.render() if mod else fallback
    except Exception as e:
        return f'<p class="sub">Add-on "{esc(name)}" failed to render: {esc(str(e))}</p>'


def addon_text(mod, feld, rueckfall=''):
    """A label or hint the add-on ships for itself, in the dashboard's language."""
    wert = getattr(mod, feld, None)
    if isinstance(wert, dict):
        return wert.get(LANG) or wert.get('en') or rueckfall
    return wert or rueckfall

def parse_tooling():
    """The Tooling tab: what this machine actually has, from inventory.js.

    Shelling out to node is the honest option here. The detection logic lives in
    that script (which CLIs are installed, which MCP servers answer, which
    plugins are enabled rather than merely present), and a second Python copy of
    it would drift from the first within a month.

    Node is optional in this repo, so its absence is a sentence rather than a
    stack trace: the tab says what is missing and what it would show.
    """
    script = W / 'reference/scripts/inventory.js'
    if not script.is_file():
        return f'<p class="ivempty">{esc(TXT["tool_noscript"])}</p>'
    try:
        r = subprocess.run(['node', str(script)], cwd=W, capture_output=True,
                           text=True, timeout=25)
    except (FileNotFoundError, subprocess.SubprocessError):
        return f'<p class="ivempty">{esc(TXT["tool_nonode"])}</p>'
    if r.returncode != 0 or not r.stdout.strip():
        # Say what broke. A blank tab is indistinguishable from "you own nothing".
        detail = (r.stderr or '').strip().splitlines()
        tail = detail[-1][:160] if detail else ''
        return (f'<p class="ivempty">{esc(TXT["tool_failed"])}'
                + (f' <code>{esc(tail)}</code>' if tail else '') + '</p>')
    return r.stdout


def parse_briefing():
    """context/BRIEFING.md, to the format reference/dashboard-render.md documents.

    That format was written down and never implemented, so the file could exist
    and the dashboard would not show a word of it. `## Lead` and `## Text` are
    fixed names; every other `##` becomes a collapsible section in file order,
    with its item count in the summary, and the first one renders open.

    A section with nothing in it is left out entirely rather than rendered as an
    empty shell. "Nothing here today" is noise that teaches you to skip the
    whole block.
    """
    f = state('BRIEFING.md')
    if not f.is_file():
        return f'<p class="sub bf-none">{esc(TXT["no_briefing"])}</p>'

    lead, text, sections = '', [], []
    for blk in re.split(r'\n## ', f.read_text(encoding='utf-8')):
        blk = blk.lstrip('# ').rstrip()
        if not blk:
            continue
        head, _, body = blk.partition('\n')
        head, body = head.strip(), body.strip()
        if not body:
            continue                      # nothing to say: leave it out
        if head.lower() == 'lead':
            lead = body
        elif head.lower() == 'text':
            text = [b for b in re.split(r'\n\s*\n', body) if b.strip()]
        else:
            items = [l.strip(' -*\t') for l in body.splitlines() if l.strip(' -*\t')]
            sections.append((head, items))

    if not (lead or text or sections):
        return f'<p class="sub bf-none">{esc(TXT["no_briefing"])}</p>'

    parts = ['<div class="bf">']
    if lead:
        parts.append(f'<p class="bf-lead">{md(lead)}</p>')
    for para in text:
        parts.append(f'<p class="bf-text">{md(para)}</p>')
    for i, (head, items) in enumerate(sections):
        lis = ''.join(f'<li>{md(x)}</li>' for x in items)
        parts.append(
            f'<details class="bf-sec"{" open" if i == 0 else ""}><summary>{esc(head)}'
            f'<span class="bf-count">{len(items)}</span></summary><ul>{lis}</ul></details>')
    parts.append('</div>')
    return ''.join(parts)


def demo_banner():
    """Says the dashboard is showing demo data, when it is.

    Unmissable on purpose. The alternative is someone looking at a pipeline that
    is not theirs and quietly concluding the tool invents jobs, which is a much
    worse first impression than an empty page would have been.
    """
    if not DEMO_USED:
        return ''
    return (f'<div class="demo-banner"><b>{esc(TXT["demo_title"])}</b> '
            f'{esc(TXT["demo_body"])} <code>rm -rf demo/</code></div>')


def parse_page(filename, note_key, missing_key, title_key):
    """Embed one of the shipped HTML pages as a tab.

    Embedded rather than restated: those pages are the single source, and the
    iframe keeps their CSS out of the dashboard's, which matters because both
    define .card and both style tables. If the file is not there, say so rather
    than showing an empty frame, since an empty box is indistinguishable from a
    broken one.
    """
    if not (W / filename).is_file():
        return f'<p class="sysnote">{esc(TXT[missing_key])}</p>'
    return (f'<p class="sysnote">{esc(TXT[note_key])}</p>'
            f'<iframe class="sysframe" src="../{filename}" '
            f'title="{esc(TXT[title_key])}" loading="lazy"></iframe>')


def parse_system():
    """The System tab. Same shape as the Onboarding one, so it is the same call."""
    return parse_page('SYSTEM.html', 'sys_note', 'sys_missing', 'tab_system')


# ─────────────────────────────────────────── Build
if not TPL.is_file():
    raise SystemExit(f'ABORT: template missing at {TPL}')

# Add-ons contribute their own tab. This block does not know any of them by name:
# it walks what is installed, asks each for its label and its HTML, and skips the
# ones that hand back nothing. Dropping a new add-on in really is the whole install.
#
# An add-on carries its own LABEL and HINT (a dict per language, or a plain string).
# Upwork predates that and still reads its two from TXT -- the fallbacks below are
# only for it, and can go once its strings move into the add-on.
_addon_tabs, _addon_panes = [], []
for _name in addon_names():
    try:
        _mod = load_addon(_name)
        _body = _mod.render() if _mod else ''
    except Exception as _e:
        _mod, _body = None, (f'<p class="sub">Add-on "{esc(_name)}" failed to render: '
                             f'{esc(str(_e))}</p>')
    if not _body:
        continue
    # Der Hinweis kommt als fertiges HTML aus dem Add-on (er enthaelt <code>), wird
    # also nicht escaped -- ein Add-on ist Code in diesem Repo, keine Nutzereingabe.
    _hint = addon_text(_mod, 'HINT') if _mod else ''
    if _hint:
        _body = f'    <p class="hint">{_hint}</p>\n{_body}'
    _label = addon_text(_mod, 'LABEL', _name.title()) if _mod else _name.title()
    _btn, _pane = addon_tab(_name, _label, _body)
    _addon_tabs.append(_btn)
    _addon_panes.append(_pane)
_addon_tabs, _addon_panes = '\n'.join(_addon_tabs), '\n'.join(_addon_panes)

date_str = TXT['datum'].format(wd=WD[TODAY.weekday()], d=TODAY.day, mon=MON[TODAY.month], y=TODAY.year)
h = TPL.read_text(encoding='utf-8')
vals = {
    'TITLE': esc(TXT['title']),
    'TAB_TODAY': esc(TXT['tab_today']),
    'TODOS_LABEL': esc(TXT['todos']),
    'DATE_LABEL': esc(date_str),
    'DATE_ISO': TODAY.isoformat(),
    'NAME_SUFFIX': esc(f' · {USER_NAME}' if USER_NAME and USER_NAME != 'Your Name' else ''),
    'TAB_PROJECTS': esc(TXT['tab_projects']),
    'TASKS': render_tasks(),
    'PROJECTS': render_projects(),
    'BRIEFING': parse_briefing(),
    'TAB_TOOLING': esc(TXT['tab_tooling']),
    'TOOLING_HINT': esc(TXT['tool_hint']),
    'TOOLING': parse_tooling(),
    'ADDON_TABS': _addon_tabs,
    'ADDON_PANES': _addon_panes,
    'DEMO_BANNER': demo_banner(),
    'TAB_ONBOARDING': esc(TXT['tab_onboarding']),
    'ONBOARDING': parse_page('ONBOARDING.html', 'onb_hint', 'onb_missing', 'tab_onboarding'),
    'TAB_SYSTEM': esc(TXT['tab_system']),
    'SYSTEM': parse_system(),
}
for k, v in vals.items():
    h = h.replace('{{' + k + '}}', v)

rest = sorted(set(re.findall(r'\{\{([A-Z_]+)\}\}', h)))
if rest:
    raise SystemExit(f'ABORT: unfilled placeholders: {rest} — today.html was NOT written.')

OUT.write_text(h, encoding='utf-8')
print(f'Rendered {OUT} ({LANG}).')
