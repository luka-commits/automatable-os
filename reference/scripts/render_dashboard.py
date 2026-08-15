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
CONFIG = W / 'context/config.yaml'
UPWORK_JOBS = W / 'context/.upwork_jobs.json'

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
    CFG_TEXT = (W / 'context/config.yaml').read_text(encoding='utf-8')
except OSError:
    CFG_TEXT = ''
LANG = CFG.get('language', 'en') if CFG.get('language') in ('de', 'en') else 'en'
USER_NAME = CFG.get('name', '')

# Bilingual UI strings for the Heute/Today tab. Kept minimal on purpose — this
# is a two-tab tool, not the full personal cockpit it was extracted from.
TXT = {
    'de': dict(
        wd=['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'],
        mon=['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
             'August', 'September', 'Oktober', 'November', 'Dezember'],
        tab_projects='Projekte', no_projects='Noch keine Projekte in context/PROJECTS.md.',
        blocked='Blockiert',
        cats={'deep-work': 'Deep Work', 'quick-win': 'Quick Win', 'comms': 'Kommunikation',
              'prep': 'Vorbereitung', 'admin': 'Admin'},
        datum='{wd}, {d}. {mon} {y}', offen='offen', wartet='wartet auf {}',
        todos='Offene To-dos', no_tasks='Noch keine offenen Tasks — trag sie in context/STATUS.md ein.',
        quad={'q1': 'dringend + wichtig', 'q2': 'nicht dringend + wichtig',
              'q3': 'dringend + nicht wichtig', 'q4': 'nicht dringend + nicht wichtig'},
        wd_short=['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'],
        tab_today='Heute', tab_upwork='Upwork', title='Freelancer OS',
        tab_system='System',
        f_all='Alle', f_due='Faellig',
        tab_tooling='Ausstattung',
        tool_hint='Was auf dieser Maschine da ist: Skills, CLIs, Verbindungen, Plugins, Zugaenge. Gelesen wird die Maschine, nicht eine gepflegte Liste.',
        tool_noscript='reference/scripts/inventory.js fehlt. Die Kopie ist unvollstaendig.',
        tool_nonode='Dafuer braucht es Node.js, und das ist hier nicht installiert. Mit Node zeigt dieser Tab, welche Werkzeuge und Verbindungen wirklich stehen.',
        tool_failed='Die Ausstattung liess sich nicht auslesen.',
        no_briefing='Noch kein Briefing fuer heute. Sag „guten Morgen“, dann steht es hier.',
        sys_note='Was dieses System kann und warum jeder Schritt so aussieht. '
                 'Dieselbe Seite liegt als SYSTEM.html im Ordner.',
        sys_missing='SYSTEM.html fehlt im Ordner. Die Kopie ist unvollstaendig, hol dir die Datei aus dem Repo nach.',
    ),
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
        tab_today='Today', tab_upwork='Upwork', title='Freelancer OS',
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
    p = W / 'context/STATUS.md'
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
    p = W / 'context/PROJECTS.md'
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


# ─────────────────────────────────────────── context/.upwork_jobs.json
CLOSED_STATUSES = ('hired', 'rejected', 'archived', 'ignored')

UW_I18N = {
    'de': dict(
        status={'new': 'Neu', 'notified': 'Gemeldet', 'proposal_sent': 'Proposal raus',
                'interviewing': 'In Kontakt', 'offer_sent': 'Angebot versendet',
                'hired': 'Gewonnen', 'rejected': 'Abgelehnt', 'archived': 'Archiviert', 'ignored': 'Ignoriert'},
        stage_label={'outreach': 'Outreach', 'in_kontakt': 'In Kontakt', 'angebot': 'Angebot versendet'},
        stage_hint={'outreach': 'beworben — noch keine Antwort', 'in_kontakt': 'Kunde hat geantwortet',
                    'angebot': 'Angebot raus, wartet auf Zusage'},
        funnel_stages=[('Gefunden', 0), ('Beworben', 1), ('In Kontakt', 2), ('Angebot versendet', 3), ('Gewonnen', 4)],
        funnel_note='Momentaufnahme nach aktuellem Status, keine Verlaufsdaten — abgelehnte/archivierte Jobs '
                    'fehlen, weil wir den Stage-Verlauf nicht mitschreiben.',
        of_prev='von davor',
        btn_generate='Ja, so generieren', btn_apply='Bewerben', btn_reply='Antwort bekommen →',
        btn_offer='Angebot geschickt →', btn_won='Gewonnen', btn_lost='Abgelehnt', btn_task='+ Task anlegen',
        due_badge='Follow-up fällig ({nf})', desc_summary='Beschreibung',
        th=('Score', 'Job', 'Kunde', 'Budget', 'Gepostet', 'Status'),
        view={'list': 'Liste', 'board': 'Pipeline', 'stats': 'Statistik'},
        filter_alle='Alle', filter_faellig='Fällig',
        ago_lt1h='vor <1 Std.', ago_h='vor {n} Std.', ago_d='vor {n} Tagen',
        stats_empty='Noch keine Daten für die Statistik.',
        no_run='Noch kein Lauf — sag „check upwork" oder warte auf den nächsten Loop-Durchlauf.',
        bad_json='context/.upwork_jobs.json ist kein gültiges JSON — Datei prüfen.',
        no_jobs='Noch keine Jobs gefunden.',
        say_gen='Generiere die Pitch-Seite für Upwork-Job {jid} ("{title}")',
        say_reply='Setze Upwork-Job {jid} auf "interviewing" — der Kunde hat geantwortet.',
        say_offer='Setze Upwork-Job {jid} auf "offer_sent".',
        say_won='Setze Upwork-Job {jid} auf "hired".',
        say_lost='Setze Upwork-Job {jid} auf "rejected".',
        say_task='Leg eine Task an: Follow-up für Upwork-Job „{title}" (fällig {nf}).',
        d_connects='Connects', d_bids='Gebote', d_bids_range='(Spanne {span})',
        d_activity='Aktivitaet', d_activity_v='{inv} eingeladen, {hired} eingestellt',
        d_bar='Mindestanforderung', d_bar_none='keine',
        d_terms='Rahmen', d_where='Kunde', d_screening='Screening-Anweisung',
        d_none='Fuer diesen Job wurden noch keine Details geholt. Der Screener holt sie beim naechsten Lauf.',
        d_close='Schliessen',
        today_lbl='Heute', proposals='Bewerbungen',
        streak='{n} Tage in Folge', week='{n} diese Woche',
        next_up='Als naechstes', goal_done='Tagesziel steht.',
        no_open='Keine offenen Jobs mehr in der Liste.',
        btn_batch='Alle {n} abarbeiten',
        say_batch='Arbeite mein Upwork-Tagesziel ab: {n} Bewerbungen, der Reihe nach. {list}. Pro Job erst kurz pruefen, ob er wirklich passt, dann das Proposal, dann zeigen bevor etwas rausgeht.',
        went_to='Wurde zu', btn_convert='In ein Projekt umwandeln',
        say_convert='Ich habe Upwork-Job {jid} gewonnen, leg das Projekt an.',
    ),
    'en': dict(
        status={'new': 'New', 'notified': 'Notified', 'proposal_sent': 'Proposal sent',
                'interviewing': 'In contact', 'offer_sent': 'Offer sent',
                'hired': 'Won', 'rejected': 'Declined', 'archived': 'Archived', 'ignored': 'Ignored'},
        stage_label={'outreach': 'Outreach', 'in_kontakt': 'In contact', 'angebot': 'Offer sent'},
        stage_hint={'outreach': 'applied — no reply yet', 'in_kontakt': 'client replied',
                    'angebot': 'offer out, awaiting their call'},
        funnel_stages=[('Found', 0), ('Applied', 1), ('In contact', 2), ('Offer sent', 3), ('Won', 4)],
        funnel_note="A snapshot by current status, not a history — declined/archived jobs are left out because "
                    "we don't log stage history.",
        of_prev='of previous',
        btn_generate='Yes, generate it', btn_apply='Apply', btn_reply='Got a reply →',
        btn_offer='Offer sent →', btn_won='Won', btn_lost='Declined', btn_task='+ Add task',
        due_badge='Follow-up due ({nf})', desc_summary='Description',
        th=('Score', 'Job', 'Client', 'Budget', 'Posted', 'Status'),
        view={'list': 'List', 'board': 'Pipeline', 'stats': 'Stats'},
        filter_alle='All', filter_faellig='Due',
        ago_lt1h='<1 hr ago', ago_h='{n} hrs ago', ago_d='{n} days ago',
        stats_empty='No stats data yet.',
        no_run='No run yet — say "check upwork" or wait for the next loop pass.',
        bad_json='context/.upwork_jobs.json is not valid JSON — check the file.',
        no_jobs='No jobs found yet.',
        say_gen='Generate the pitch page for Upwork job {jid} ("{title}")',
        say_reply='Set Upwork job {jid} to "interviewing" — the client replied.',
        say_offer='Set Upwork job {jid} to "offer_sent".',
        say_won='Set Upwork job {jid} to "hired".',
        say_lost='Set Upwork job {jid} to "rejected".',
        say_task='Add a task: follow up on Upwork job "{title}" (due {nf}).',
        d_connects='Connects', d_bids='Bids', d_bids_range='(range {span})',
        d_activity='Activity', d_activity_v='{inv} invited, {hired} hired',
        d_bar='Their minimum bar', d_bar_none='none',
        d_terms='Terms', d_where='Client', d_screening='Screening instruction',
        d_none='No details fetched for this job yet. The screener picks them up on its next run.',
        d_close='Close',
        today_lbl='Today', proposals='proposals',
        streak='{n} days running', week='{n} this week',
        next_up='Next up', goal_done="Today's goal is met.",
        no_open='No untouched jobs left in the list.',
        btn_batch='Work through all {n}',
        say_batch='Work through my Upwork goal for today: {n} applications, one after the other. {list}. For each one check first whether it actually fits, then the proposal, then show me before anything goes out.',
        went_to='Became', btn_convert='Turn it into a project',
        say_convert='I won Upwork job {jid}, set up the project.',
    ),
}
T = UW_I18N[LANG]

UW_STAGES = [
    {'key': 'outreach', 'statuses': ('new', 'notified', 'proposal_sent'), 'accent_mix': 40},
    {'key': 'in_kontakt', 'statuses': ('interviewing',), 'accent_mix': 70},
    {'key': 'angebot', 'statuses': ('offer_sent',), 'accent_mix': 100},
]
UW_FUNNEL_RANK = {'new': 0, 'notified': 0, 'proposal_sent': 1, 'interviewing': 2, 'offer_sent': 3, 'hired': 4}


def _uw_funnel(jobs):
    ranked = [j for j in jobs if j.get('status') in UW_FUNNEL_RANK]
    if not ranked:
        return ''
    counts = [(label, sum(1 for j in ranked if UW_FUNNEL_RANK[j['status']] >= min_rank))
              for label, min_rank in T['funnel_stages']]
    top = counts[0][1] or 1
    prev = None
    rows = []
    for label, count in counts:
        width = max(round(count / top * 100), 3 if count else 0)
        cum_pct = round(count / top * 100)
        of_prev = f" · {round(count / prev * 100)}% {T['of_prev']}" if prev else ''
        rows.append(
            f'<div class="uw-funnel-row">'
            f'<span class="uw-funnel-label">{esc(label)}</span>'
            f'<span class="uw-funnel-track"><span class="uw-funnel-bar" style="width:{width}%"></span></span>'
            f'<span class="uw-funnel-count">{count}</span>'
            f'<span class="uw-funnel-pct">{cum_pct}%{of_prev}</span>'
            f'</div>'
        )
        prev = count
    return f'<div class="uw-funnel">{"".join(rows)}</div><p class="uw-funnel-note">{esc(T["funnel_note"])}</p>'


def _posted_ago(posted_date):
    if not posted_date:
        return ''
    try:
        d = datetime.datetime.fromisoformat(posted_date.replace('Z', '+00:00'))
        now = datetime.datetime.now(datetime.timezone.utc)
        hrs = (now - d).total_seconds() / 3600
        if hrs < 1:
            return T['ago_lt1h']
        if hrs < 24:
            return T['ago_h'].format(n=int(hrs))
        return T['ago_d'].format(n=int(hrs // 24))
    except Exception:
        return ''


def _budget_label(budget, job_type):
    b = (budget or '').strip()
    if not b or b in ('0.0', 'Not provided') or b.lower().startswith('not specified'):
        return 'n/a'
    if '$' in b or '/hr' in b or 'fix' in b.lower():
        return b
    if job_type == 'hourly':
        return f'${b}/hr'
    return f'${b} fix'


def _uw_stage_actions(j, is_due=False, nf=None):
    """Say-btn text per stage — copies a ready sentence to the clipboard, the
    dashboard never writes anything itself. These sentences match the examples
    in the upwork-screener skill's status-CRM step, so pasting them is enough."""
    jid, title, status = j.get('id', ''), j.get('title', ''), j.get('status', 'new')
    gen_prompt = T['say_gen'].format(jid=jid, title=title)
    reply_prompt = T['say_reply'].format(jid=jid)
    offer_prompt = T['say_offer'].format(jid=jid)
    won_prompt = T['say_won'].format(jid=jid)
    lost_prompt = T['say_lost'].format(jid=jid)
    task_prompt = T['say_task'].format(title=title, nf=nf)
    if status in ('new', 'notified', 'proposal_sent'):
        actions = (
            f'<button type="button" class="say-btn" data-say="{esc(gen_prompt)}">{esc(T["btn_generate"])}</button>'
            f'<button type="button" class="apply-btn" data-url="{esc(j.get("url", "#"))}">{esc(T["btn_apply"])}</button>'
            f'<button type="button" class="say-btn" data-say="{esc(reply_prompt)}">{esc(T["btn_reply"])}</button>'
        )
    elif status == 'interviewing':
        actions = f'<button type="button" class="say-btn" data-say="{esc(offer_prompt)}">{esc(T["btn_offer"])}</button>'
    elif status == 'offer_sent':
        actions = (
            f'<button type="button" class="say-btn" data-say="{esc(won_prompt)}">{esc(T["btn_won"])}</button>'
            f'<button type="button" class="say-btn" data-say="{esc(lost_prompt)}">{esc(T["btn_lost"])}</button>'
        )
    elif status == 'hired':
        # A won job is the one case where there is nothing left to do here and
        # something important to say: where the work now lives. Without this the
        # link upwork-won creates is invisible from the pipeline side, and the
        # handover looks like the job simply stopped.
        slug = j.get('project')
        actions = (f'<span class="uw-project">{esc(T["went_to"])} '
                   f'<code>projects/{esc(slug)}/</code></span>') if slug else (
                  f'<button type="button" class="say-btn" data-say="{esc(T["say_convert"].format(jid=jid))}">'
                  f'{esc(T["btn_convert"])}</button>')
    else:
        actions = ''
    if is_due:
        actions += f'<button type="button" class="say-btn uw-task-btn" data-say="{esc(task_prompt)}">{esc(T["btn_task"])}</button>'
    return actions


def _uw_goal():
    """The daily goal from config.yaml. No entry means no tracker: better none at
    all than one measuring against a number nobody chose."""
    m = re.search(r'^\s*daily_proposal_goal:\s*(\d+)', CFG_TEXT, re.M)
    return int(m.group(1)) if m else None


def _uw_applied_dates(jobs):
    """Every day an application went out, from the history.

    The source is the `proposal_sent` entry in `history`, not `status_updated_at`:
    that gets overwritten on the next change and the day would be gone. `applied_at`
    is the fallback for records migrated before histories existed.
    """
    out = []
    for j in jobs:
        stamps = [h.get('at') for h in j.get('history', []) if h.get('status') == 'proposal_sent']
        if not stamps and j.get('applied_at'):
            stamps = [j['applied_at']]
        for st in stamps:
            try:
                out.append(datetime.datetime.fromisoformat(st.replace('Z', '+00:00')).date())
            except (ValueError, AttributeError):
                continue
    return out


def _uw_streak(counts, goal, today, weekdays_only=True):
    """Consecutive days the goal was met. The running day never breaks it: at nine in
    the morning, zero applications is the normal state and not a relapse."""
    streak, day = 0, today
    if counts.get(day, 0) < goal:
        day -= datetime.timedelta(days=1)
    while True:
        if weekdays_only and day.weekday() >= 5:
            day -= datetime.timedelta(days=1)
            continue
        if counts.get(day, 0) < goal:
            return streak
        streak += 1
        day -= datetime.timedelta(days=1)


def _uw_tracker(jobs, open_jobs, today):
    """Goal, progress, streak, the week, and what to do next.

    Sits at the top of the tab rather than behind a view pill, because it is the
    daily handle and anything behind a click does not get looked at.
    """
    goal = _uw_goal()
    if not goal:
        return ''
    counts = {}
    for d in _uw_applied_dates(jobs):
        counts[d] = counts.get(d, 0) + 1
    done = counts.get(today, 0)
    week_start = today - datetime.timedelta(days=today.weekday())
    week_done = sum(n for d, n in counts.items() if week_start <= d <= today)
    streak = _uw_streak(counts, goal, today)
    pct = min(round(done / goal * 100), 100)

    # The bars show the SAME week as the counter beside them (Monday to Sunday of the
    # current week), not a rolling seven days. Two definitions of "week" sitting next
    # to each other is how a dashboard starts contradicting itself.
    bars = []
    for i in range(7):
        d = week_start + datetime.timedelta(days=i)
        n = counts.get(d, 0)
        # A bar at 2% of 42px is 0.8px in the palest colour on the page, which is to
        # say invisible. Anything above zero gets a floor, and every day gets a track
        # so an empty day reads as empty rather than as missing.
        h = max(min(round(n / goal * 100), 100), 12) if n else 0
        cls = ' future' if d > today else (' hit' if n >= goal else ('' if n else ' none'))
        fill = '' if d > today or not n else f'<span class="uw-daybar-fill" style="height:{h}%"></span>'
        bars.append(f'<span class="uw-daybar{cls}" title="{d.isoformat()}: {n}">{fill}'
                    f'<span class="uw-daybar-lbl">{esc(TXT["wd_short"][d.weekday()])}</span></span>')

    # The goal is a day's work, not one job. So next to the single next job there is a
    # sentence that hands over everything still missing as one list: one paste instead
    # of five. The dashboard stays a pure view either way — it copies the sentence, the
    # work happens in the chat.
    todo = sorted(open_jobs, key=lambda j: -j.get('score', 0))[:max(goal - done, 0)]
    if todo:
        nxt = todo[0]
        gen = T['say_gen'].format(jid=nxt.get('id', ''), title=nxt.get('title', ''))
        listed = ' · '.join(f'{j.get("id", "")} "{j.get("title", "")}"' for j in todo)
        batch = T['say_batch'].format(n=len(todo), list=listed)
        next_html = (
            f'<div class="uw-next"><span class="uw-next-lbl">{esc(T["next_up"])}</span>'
            f'<span class="uw-next-title">{md(nxt.get("title", ""))}</span>'
            f'<span class="uw-score strong">{nxt.get("score", 0)}</span>'
            f'<button type="button" class="say-btn" data-say="{esc(gen)}">{esc(T["btn_generate"])}</button>'
            f'<button type="button" class="say-btn uw-batch-btn" data-say="{esc(batch)}">'
            f'{esc(T["btn_batch"].format(n=len(todo)))}</button></div>')
    elif done >= goal:
        next_html = f'<div class="uw-next"><span class="uw-next-lbl">{esc(T["goal_done"])}</span></div>'
    else:
        next_html = f'<div class="uw-next"><span class="uw-next-lbl">{esc(T["no_open"])}</span></div>'

    return (
        f'<div class="uw-tracker">'
        f'<div class="uw-tracker-head">'
        f'<span class="uw-tracker-title">{esc(T["today_lbl"])}</span>'
        f'<span class="uw-tracker-count"><b>{done}</b> / {goal} {esc(T["proposals"])}</span>'
        f'<span class="uw-tracker-meta">{esc(T["streak"].format(n=streak))} · '
        f'{esc(T["week"].format(n=week_done))}</span>'
        f'</div>'
        f'<div class="uw-progress"><span class="uw-progress-fill" style="width:{pct}%"></span></div>'
        f'<div class="uw-days">{"".join(bars)}</div>'
        f'{next_html}'
        f'</div>'
    )


def _uw_client(j):
    """The client column, from a record that comes in two shapes.

    The screener writes an object with rating/hires/posted. But this file is
    hand-editable, and anyone noting a client by name writes a plain string —
    which used to end in an AttributeError traceback naming no cause. For a
    dashboard whose whole job is to render what is in the file honestly,
    crashing on a name is the wrong answer, so a string is read as the name.

    This lived twice, once per view, and a fix to one would have left the other.
    """
    client = j.get('client') or {}
    if isinstance(client, str):
        return client
    rating = client.get('rating')
    hires, posted = client.get('hires'), client.get('posted')
    bits = []
    if rating:
        bits.append(f'{rating}★')
    if hires is not None and posted is not None:
        bits.append(f'{hires}/{posted} hires')
    if not bits and client.get('name'):
        bits.append(str(client['name']))
    return ' · '.join(bits)


def _uw_detail(j):
    """The fields that decide an application, in a panel behind the row.

    They come from `find_jobs action=get`, one call per job, which is why the
    screener stores them under `details` rather than the dashboard fetching them:
    pulling them for a whole list is the request pattern Upwork flags as scraping.

    A job screened before this existed simply has no `details`, and then the panel
    says so instead of rendering a grid of dashes.
    """
    d = j.get('details') or {}
    rows = []

    def add(label, value, note=''):
        if value in (None, '', 'Any', 0) and value is not False:
            return
        rows.append(f'<div class="uw-d-row"><dt>{esc(label)}</dt>'
                    f'<dd>{esc(str(value))}'
                    + (f' <span class="uw-d-note">{esc(note)}</span>' if note else '')
                    + '</dd></div>')

    add(T['d_connects'], d.get('connects_cost'))
    if d.get('bid_avg'):
        span = f"{d.get('bid_min', '?')} to {d.get('bid_max', '?')}"
        add(T['d_bids'], d['bid_avg'], T['d_bids_range'].format(span=span))
    if d.get('total_hired') is not None or d.get('invites_sent') is not None:
        add(T['d_activity'],
            T['d_activity_v'].format(inv=d.get('invites_sent', 0),
                                     hired=d.get('total_hired', 0)))
    bar = [x for x in (
        f"JSS {d['min_jss']}%" if d.get('min_jss') else '',
        f"earned {d['min_earnings']}" if d.get('min_earnings') not in (None, '', 'Any') else '',
        f"{d['min_hours']}h" if d.get('min_hours') else '') if x]
    add(T['d_bar'], ' · '.join(bar) if bar else T['d_bar_none'])
    add(T['d_terms'], ' · '.join(x for x in (d.get('experience_level'), d.get('engagement')) if x))
    where = ' · '.join(x for x in (d.get('client_city'), d.get('client_country')) if x)
    add(T['d_where'], where, d.get('client_timezone') or '')
    if d.get('screening_note'):
        rows.append(f'<div class="uw-d-row wide"><dt>{esc(T["d_screening"])}</dt>'
                    f'<dd class="uw-d-screen">{md(d["screening_note"])}</dd></div>')

    body = ''.join(rows) or f'<p class="uw-d-empty">{esc(T["d_none"])}</p>'
    desc = j.get('description') or ''
    if desc:
        body += (f'<details class="uw-d-desc"><summary>{esc(T["desc_summary"])}</summary>'
                 f'<p>{md(desc[:4000])}</p></details>')
    return (f'<div class="uw-detail" hidden><h3>{md(j.get("title", ""))}</h3>'
            f'<dl class="uw-d-grid">{body}</dl></div>')


def _uw_row(j, today_iso):
    score = j.get('score', 0)
    score_cls = ' strong' if score >= 70 else ''
    status = j.get('status', 'new')
    status_lbl = T['status'].get(status, status)
    client_txt = _uw_client(j)
    nf = j.get('next_follow_up')
    is_due = bool(nf and nf <= today_iso and status not in CLOSED_STATUSES)
    due_badge = f'<span class="uw-due-badge">{esc(T["due_badge"].format(nf=nf))}</span>' if is_due else ''
    ago = _posted_ago(j.get('posted_date')) or '–'
    desc = (j.get('description') or '').strip()
    desc_details = (f'<details class="uw-desc"><summary>{esc(T["desc_summary"])}</summary><p>{md(desc)}</p></details>'
                    if desc else '')
    budget_lbl = _budget_label(j.get('budget'), j.get('job_type'))
    return (
        f'<tr class="uw-row{" due" if is_due else ""}" data-uwstatus="{status}" data-uwdue="{"1" if is_due else "0"}">'
        f'<td><span class="uw-score{score_cls}">{score}</span></td>'
        # The title opens the detail panel rather than leaving the page: the fields
        # that decide an application are already here, and Upwork does not return a
        # working public job link anyway (the id is internal, not the ~ciphertext a
        # real URL needs). So the click that feels like "show me this job" shows it.
        f'<td class="rt-td-name"><span class="rt-td-title">'
        f'<button type="button" class="uw-open">{md(j.get("title", ""))}</button></span>'
        f'<span class="rt-td-desc">{esc(j.get("rationale", ""))}</span>'
        f'{_uw_detail(j)}{desc_details}</td>'
        f'<td class="uw-client">{esc(client_txt)}</td>'
        f'<td class="uw-budget">{esc(budget_lbl)}</td>'
        f'<td class="uw-ago">{esc(ago)}</td>'
        f'<td class="uw-status-cell"><span class="uw-status {status}">{esc(status_lbl)}</span>{" " + due_badge if due_badge else ""}'
        f'<div class="uw-actions">{_uw_stage_actions(j, is_due, nf)}</div></td>'
        f'</tr>')


def _uw_card(j, today_iso):
    score = j.get('score', 0)
    score_cls = ' strong' if score >= 70 else ''
    status = j.get('status', 'new')
    status_lbl = T['status'].get(status, status)
    client_txt = _uw_client(j)
    nf = j.get('next_follow_up')
    is_due = bool(nf and nf <= today_iso and status not in CLOSED_STATUSES)
    due_badge = f'<span class="uw-due-badge">{esc(T["due_badge"].format(nf=nf))}</span>' if is_due else ''
    ago = _posted_ago(j.get('posted_date')) or '–'
    desc = (j.get('description') or '').strip()
    desc_details = (f'<details class="uw-desc"><summary>{esc(T["desc_summary"])}</summary><p>{md(desc)}</p></details>'
                    if desc else '')
    budget_lbl = _budget_label(j.get('budget'), j.get('job_type'))
    meta_bits = [b for b in (client_txt, budget_lbl, ago, status_lbl) if b]
    return (
        f'<li class="uw-card{" due" if is_due else ""}" data-uwdue="{"1" if is_due else "0"}">'
        f'<div class="uw-card-top"><span class="uw-score{score_cls}">{score}</span>'
        f'<span class="uw-card-title"><a href="{esc(j.get("url", "#"))}" target="_blank" rel="noopener">{md(j.get("title", ""))}</a></span></div>'
        f'<div class="uw-card-meta">{esc(" · ".join(meta_bits))}</div>'
        f'{due_badge}'
        f'<div class="uw-card-rationale">{esc(j.get("rationale", ""))}</div>{desc_details}'
        f'<div class="uw-actions">{_uw_stage_actions(j, is_due, nf)}</div>'
        f'</li>'
    )


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
    f = W / 'context/BRIEFING.md'
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


def parse_system():
    """The System tab: SYSTEM.html embedded, not restated.

    A second copy of the explanation inside this renderer is exactly the
    duplication the rest of the repo forbids, and it would drift within a month.
    The iframe also keeps that page's CSS out of the dashboard's, which matters
    because both define .card and both style tables.

    If the file is not there, say so plainly rather than showing an empty frame:
    an empty box is indistinguishable from a broken one.
    """
    if not (W / 'SYSTEM.html').is_file():
        return f'<p class="sysnote">{esc(TXT["sys_missing"])}</p>'
    return (f'<p class="sysnote">{esc(TXT["sys_note"])}</p>'
            f'<iframe class="sysframe" src="../SYSTEM.html" '
            f'title="{esc(TXT["tab_system"])}" loading="lazy"></iframe>')


def parse_upwork():
    """context/.upwork_jobs.json (written by the upwork-screener skill), rendered as
    Liste/Pipeline/Statistik (List/Pipeline/Stats) — the same 1:1-borrowed pattern
    from the Automatable tracker's PipelineBoard. Sorting everywhere: open due
    follow-ups first, then score."""
    if not UPWORK_JOBS.is_file():
        return f'<p class="sub">{esc(T["no_run"])}</p>'
    try:
        jobs = json.loads(UPWORK_JOBS.read_text(encoding='utf-8'))
    except Exception:
        return f'<p class="sub">{esc(T["bad_json"])}</p>'
    if not jobs:
        return f'<p class="sub">{esc(T["no_jobs"])}</p>'

    today_iso = TODAY.isoformat()

    def due(j):
        nf = j.get('next_follow_up')
        return bool(nf and nf <= today_iso and j.get('status') not in CLOSED_STATUSES)

    def sort_key(j):
        return (not due(j), -j.get('score', 0))

    active = sorted((j for j in jobs if j.get('status') not in ('archived', 'ignored')), key=sort_key)
    open_jobs = [j for j in active if j.get('status') not in ('hired', 'rejected')]
    present_statuses = [s for s in ('new', 'notified', 'proposal_sent', 'interviewing',
                                     'offer_sent', 'hired', 'rejected')
                         if any(j.get('status') == s for j in active)]

    filters = [('all', T['filter_alle']), ('due', T['filter_faellig'])] + \
        [(s, T['status'][s]) for s in present_statuses]
    filterbar = '<div class="uw-filterbar">' + ''.join(
        f'<button type="button" class="pill uw-filterpill{" active" if key == "all" else ""}" data-uwfilter="{key}">{esc(label)}</button>'
        for key, label in filters
    ) + '</div>'
    th = ''.join(f'<th>{esc(h)}</th>' for h in T['th'])
    list_html = (filterbar +
                 f'<table class="rt-table uw-table"><colgroup>'
                 f'<col style="width:6%"><col style="width:40%"><col style="width:16%">'
                 f'<col style="width:14%"><col style="width:10%"><col style="width:14%">'
                 f'</colgroup><thead><tr>{th}</tr></thead>'
                 f'<tbody>{"".join(_uw_row(j, today_iso) for j in active)}</tbody></table>')

    cols = []
    for stage in UW_STAGES:
        stage_jobs = sorted((j for j in open_jobs if j.get('status') in stage['statuses']), key=sort_key)
        accent = f"color-mix(in srgb, var(--brand) {stage['accent_mix']}%, var(--card))"
        cards = ''.join(_uw_card(j, today_iso) for j in stage_jobs) or '<li class="uw-empty">—</li>'
        cols.append(
            f'<div class="uw-col">'
            f'<div class="uw-col-head" style="border-top-color: {accent}">'
            f'<div><div class="uw-col-title">{esc(T["stage_label"][stage["key"]])}</div>'
            f'<div class="uw-col-hint">{esc(T["stage_hint"][stage["key"]])}</div></div>'
            f'<span class="uw-col-count" style="color: {accent}; background: color-mix(in srgb, {accent} 16%, transparent)">{len(stage_jobs)}</span>'
            f'</div>'
            f'<ul class="uw-col-body">{cards}</ul>'
            f'</div>'
        )
    board_html = f'<div class="uw-board">{"".join(cols)}</div>'
    stats_html = _uw_funnel(active) or f'<p class="sub">{esc(T["stats_empty"])}</p>'

    return (
        _uw_tracker(jobs, [j for j in jobs if j.get('status') in ('new', 'notified')], TODAY)
        + f'<div class="uw-viewbar">'
        f'<button type="button" class="pill uw-viewpill active" data-uwview="list">{esc(T["view"]["list"])}</button>'
        f'<button type="button" class="pill uw-viewpill" data-uwview="board">{esc(T["view"]["board"])}</button>'
        f'<button type="button" class="pill uw-viewpill" data-uwview="stats">{esc(T["view"]["stats"])}</button>'
        f'</div>'
        f'<div class="uw-view uw-view-list">{list_html}</div>'
        f'<div class="uw-view uw-view-board" hidden>{board_html}</div>'
        f'<div class="uw-view uw-view-stats" hidden>{stats_html}</div>'
    )


# ─────────────────────────────────────────── Build
if not TPL.is_file():
    raise SystemExit(f'ABORT: template missing at {TPL}')

date_str = TXT['datum'].format(wd=WD[TODAY.weekday()], d=TODAY.day, mon=MON[TODAY.month], y=TODAY.year)
h = TPL.read_text(encoding='utf-8')
vals = {
    'TITLE': esc(TXT['title']),
    'TAB_TODAY': esc(TXT['tab_today']),
    'TAB_UPWORK': esc(TXT['tab_upwork']),
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
    'UPWORK_ITEMS': parse_upwork(),
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
