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
import re, html, json, pathlib, datetime, argparse

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
LANG = CFG.get('language', 'en') if CFG.get('language') in ('de', 'en') else 'en'
USER_NAME = CFG.get('name', '')

# Bilingual UI strings for the Heute/Today tab. Kept minimal on purpose — this
# is a two-tab tool, not the full personal cockpit it was extracted from.
TXT = {
    'de': dict(
        wd=['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'],
        mon=['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
             'August', 'September', 'Oktober', 'November', 'Dezember'],
        cats={'deep-work': 'Deep Work', 'quick-win': 'Quick Win', 'comms': 'Kommunikation',
              'prep': 'Vorbereitung', 'admin': 'Admin'},
        datum='{wd}, {d}. {mon} {y}', offen='offen', wartet='wartet auf {}',
        todos='Offene To-dos', no_tasks='Noch keine offenen Tasks — trag sie in context/STATUS.md ein.',
        quad={'q1': 'dringend + wichtig', 'q2': 'nicht dringend + wichtig',
              'q3': 'dringend + nicht wichtig', 'q4': 'nicht dringend + nicht wichtig'},
        tab_today='Heute', tab_upwork='Upwork', title='Freelancer OS',
    ),
    'en': dict(
        wd=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
        mon=['', 'January', 'February', 'March', 'April', 'May', 'June', 'July',
             'August', 'September', 'October', 'November', 'December'],
        cats={'deep-work': 'Deep Work', 'quick-win': 'Quick Win', 'comms': 'Communication',
              'prep': 'Preparation', 'admin': 'Admin'},
        datum='{wd}, {d} {mon} {y}', offen='open', wartet='waiting on {}',
        todos='Open to-dos', no_tasks='No open tasks yet — add them to context/STATUS.md.',
        quad={'q1': 'urgent + important', 'q2': 'not urgent + important',
              'q3': 'urgent + not important', 'q4': 'not urgent + not important'},
        tab_today='Today', tab_upwork='Upwork', title='Freelancer OS',
    ),
}[LANG]
WD, MON, CATS, QUAD = TXT['wd'], TXT['mon'], TXT['cats'], TXT['quad']


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
        due = ''
        m = re.search(r'\((?:bis|due) (\d{2})\.(\d{2})\.\)', raw)
        if m:
            d, mo = int(m.group(1)), int(m.group(2))
            y = TODAY.year + (1 if (mo, d) < (TODAY.month, TODAY.day) else 0)
            due = f'{y}-{mo:02d}-{d:02d}'
        cm = re.search(r'#(deep-work|quick-win|komm|comms|prep|admin)', raw)
        cat = ('comms' if cm and cm.group(1) == 'komm' else cm.group(1) if cm else 'deep-work')
        text = re.sub(r'\s*#(deep-work|quick-win|komm|comms|prep|admin)', '', text)
        text = re.sub(r'^\((?:wartet auf|waiting on) [^)]+\)\s*', '', text)
        text = re.sub(r'\s*\((?:bis|due) \d{2}\.\d{2}\.\)', '', text).strip()
        note = ''
        if i + 1 < len(lines) and lines[i + 1].startswith(('  ', '\t')) \
                and not re.match(r'^\s*- \[', lines[i + 1]):
            note = lines[i + 1].strip()
        tasks.append(dict(text=text[:180], proj=proj or 'General', status=status,
                          stat_lbl=stat_lbl, due=due, cat=cat, note=note[:400]))
    return tasks


def render_tasks():
    tasks = parse_status()
    if not tasks:
        return f'<p class="sub">{esc(TXT["no_tasks"])}</p>'
    tasks = sorted(tasks, key=lambda t: {'q1': 0, 'q2': 1, 'q3': 2, 'q4': 3}[quadrant(t['cat'], t['due'])])
    rows = []
    for t in tasks:
        quad = quadrant(t['cat'], t['due'])
        due_lbl = f'{t["due"][8:10]}.{t["due"][5:7]}.' if t['due'] else ''
        note_div = f'<div class="t-note">{md(t["note"])}</div>' if t['note'] else ''
        rows.append(
            f'<li data-quadrant="{quad}"><span class="c-quad {quad}" title="{esc(QUAD[quad])}">{quad.upper()}</span>'
            f'<span class="t-text">{md(t["text"])}</span>'
            f'<span class="c-proj">{esc(t["proj"])}</span>'
            f'<span class="c-cat">{esc(CATS.get(t["cat"], t["cat"]))}</span>'
            f'<span class="c-status">{esc(t["stat_lbl"])}</span>'
            f'<span class="c-due">{due_lbl}</span>{note_div}</li>'
        )
    return f'<ul class="task-list">{"".join(rows)}</ul>'


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
    else:
        actions = ''
    if is_due:
        actions += f'<button type="button" class="say-btn uw-task-btn" data-say="{esc(task_prompt)}">{esc(T["btn_task"])}</button>'
    return actions


def _uw_row(j, today_iso):
    score = j.get('score', 0)
    score_cls = ' strong' if score >= 70 else ''
    status = j.get('status', 'new')
    status_lbl = T['status'].get(status, status)
    client = j.get('client') or {}
    rating = client.get('rating')
    hires, posted = client.get('hires'), client.get('posted')
    client_bits = []
    if rating:
        client_bits.append(f'{rating}★')
    if hires is not None and posted is not None:
        client_bits.append(f'{hires}/{posted} hires')
    client_txt = ' · '.join(client_bits)
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
        f'<td class="rt-td-name"><span class="rt-td-title"><a href="{esc(j.get("url", "#"))}" target="_blank" rel="noopener">{md(j.get("title", ""))}</a></span>'
        f'<span class="rt-td-desc">{esc(j.get("rationale", ""))}</span>{desc_details}</td>'
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
    client = j.get('client') or {}
    rating = client.get('rating')
    hires, posted = client.get('hires'), client.get('posted')
    client_bits = []
    if rating:
        client_bits.append(f'{rating}★')
    if hires is not None and posted is not None:
        client_bits.append(f'{hires}/{posted} hires')
    client_txt = ' · '.join(client_bits)
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
        f'<div class="uw-viewbar">'
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
    'TASKS': render_tasks(),
    'UPWORK_ITEMS': parse_upwork(),
}
for k, v in vals.items():
    h = h.replace('{{' + k + '}}', v)

rest = sorted(set(re.findall(r'\{\{([A-Z_]+)\}\}', h)))
if rest:
    raise SystemExit(f'ABORT: unfilled placeholders: {rest} — today.html was NOT written.')

OUT.write_text(h, encoding='utf-8')
print(f'Rendered {OUT} ({LANG}).')
