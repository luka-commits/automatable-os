"""The Upwork add-on's dashboard tab.

Everything Upwork-specific that used to sit inside render_dashboard.py. The base
layer renders the day, the projects and the tooling; this file renders the Upwork
pipeline and nothing else. Delete the file and the base still renders, with the
Upwork tab empty.

The names it needs from the base (W, esc, TXT, TODAY and so on) are injected into
this module's namespace by the loader before render() is called, so the code below
reads exactly as it did when it lived in the renderer. That injection is the whole
contract: an add-on gets the base's helpers and hands back one block of HTML.

    render() -> str   the tab's HTML
"""

import datetime
import json
import re

# Label und Hinweis gehoeren dem Add-on, nicht der Basis (23.08.2026). Solange die
# Basis sie in ihrer eigenen Uebersetzungstabelle hielt, hiess ein zweites Add-on:
# die Basis anfassen -- genau das, was der Vertrag in CLAUDE.md ausschliesst.
LABEL = {'en': 'Upwork', 'de': 'Upwork'}
HINT = {
    'en': ('Pipeline: Applied → In contact → Offer sent → Won. The buttons on a row or card '
           'only copy a chat sentence — pasting it and sending it is what actually moves the '
           'job, or run <code>python3 reference/scripts/upwork_status.py set &lt;id&gt; '
           '&lt;status&gt;</code> yourself.'),
}

UW_I18N = {
    'en': {
        'status': {'new': 'New', 'notified': 'Notified', 'proposal_sent': 'Proposal sent',
                   'interviewing': 'In contact', 'offer_sent': 'Offer sent',
                   'hired': 'Won', 'rejected': 'Declined', 'archived': 'Archived', 'ignored': 'Ignored'},
        'stage_label': {'offen': 'Not applied', 'outreach': 'Applied', 'in_kontakt': 'In contact',
                        'angebot': 'Offer sent'},
        'stage_hint': {'offen': 'found and scored, still sitting', 'outreach': 'sent, no reply yet',
                       'in_kontakt': 'client replied', 'angebot': 'offer out, awaiting their call'},
        'stage_empty': {'offen': 'All cleared.', 'outreach': 'Nothing sent yet. The first job is waiting on the left.',
                        'in_kontakt': 'As soon as a client replies, they show up here.',
                        'angebot': 'Appears when a conversation turns into an offer.'},
        'funnel_stages': [('Found', 0), ('Applied', 1), ('In contact', 2), ('Offer sent', 3), ('Won', 4)],
        'funnel_note': 'A real cohort: each job counts at the highest stage it ever reached, taken from its '
                       'history, so declined and archived jobs count where they got to. Jobs found before the first run that wrote history '
                       'only have a reconstructed history.',
        'of_prev': 'of previous',
        'btn_generate': 'Yes, generate it', 'btn_apply': 'Apply', 'btn_reply': 'Got a reply →',
        'btn_offer': 'Offer sent →', 'btn_won': 'Won', 'btn_lost': 'Declined', 'btn_task': '+ Add task',
        'due_badge': 'Follow-up due ({nf})', 'desc_summary': 'Description',
        'th': ('Score', 'Job', 'Client', 'Competition', 'Budget', 'Posted', 'Stage'),
        'comp_none': 'none yet', 'comp_n': '{n} bids', 'comp_inv': '{n} invited',
        'me_title': 'Where you stand', 'me_sub': 'the numbers client minimums test against',
        'me_connects': 'Connects', 'me_applications': 'buys you',
        'me_apps_val': '{lo}–{hi} proposals', 'me_jss': 'Job Success',
        'me_earned': 'earned', 'me_hours': 'billed', 'me_rate': 'hourly rate',
        'excl_lead': '{n} jobs filtered out, so not in the list:',
        'excl_bar': '{n} below the bar', 'excl_gone': '{n} already taken',
        'excl_other': '{n} other',
        'detail_clienthist': 'What this client hires for', 'detail_questions': 'Required screening questions',
        'due_over': '{n}d overdue', 'due_today': 'due today', 'due_in': 'in {n} days',
        'detail_why': 'Why this job', 'detail_history': 'History',
        'detail_lage': 'Where this application stands',
        'detail_nolage': 'Not fetched yet. The screener pulls this for the highest-scoring open jobs.',
        'detail_screening': '⚠ Screening instruction in the text:',
        'lbl_connects': 'Costs', 'val_connects': '{n} connects',
        'lbl_bids': 'Competing bids', 'val_bids': '${avg}/hr average, ${span} range', 'val_bids_fixed': '${avg} average bid, ${span} range',
        'lbl_proposals': 'Proposals so far', 'lbl_live': 'Client status',
        'live_hired': 'someone already hired', 'live_offered': 'an offer is out',
        'live_invites': '{n} invitations sent', 'live_open': 'open, nobody hired yet',
        'lbl_bar': 'Minimum bar', 'bar_hours': '{n} hrs experience',
        'lbl_tz': 'Client is in',
        'flag_gone': 'taken', 'flag_bar': 'below the bar',
        'lbl_fit': 'Fit', 'fit_ok': 'You clear the bar', 'fit_fail': 'You fall short: {why}',
        'fit_jss': 'JSS {need}% required, you have {have}%',
        'fit_earn': '${need} earnings required, you have ${have}',
        'lbl_shape': 'Engagement', 'shape_full': 'full time',
        'shape_part': 'part time', 'shape_asneeded': 'as needed',
        'view': {'list': 'List', 'board': 'Pipeline', 'stats': 'Insights'},
        'today': 'Today', 'proposals': 'proposals', 'streak': '{n}-day streak',
        'week': 'this week {n}', 'next_up': 'Up next:',
        'no_open': 'No open job in the list.', 'as_of': 'as of {d} {t}',
        'weekdays': ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'),
        'kpi_reply': 'Reply rate', 'kpi_speed': 'Time to reply', 'kpi_rate': 'Proposals per week',
        'kpi_reply_hint': '{n} more applications to go', 'kpi_of': '{a} of {b} replied',
        'kpi_speed_hint': 'once a client replies', 'kpi_from': 'median of {n}',
        'kpi_days': '{n} days', 'kpi_rate_hint': 'average of the last four weeks',
        'score_legend': 'Score 0 to 100 from niche fit, client quality, deal size and recency. 70 and up is strong.',
        'btn_batch': "Start today's batch ({n})", 'goal_done': "Daily goal hit. That's it for today.",
        'filter_alle': 'All', 'filter_faellig': 'Due today',
        'filter_todo': 'Has a to-do', 'filter_closed': 'Closed',
        'ago_lt1h': '<1 hr ago', 'ago_h': '{n} hrs ago', 'ago_d': '{n} days ago',
        'stats_empty': 'No stats data yet.',
        'no_run': 'No run yet — say "check upwork" or wait for the next loop pass.',
        'bad_json': 'context/.upwork_jobs.json is not valid JSON — check the file.',
        'no_jobs': 'No jobs found yet.',
    },
}

# The stage board: one column per stage, an accent that deepens as the stage
# advances, a follow-up chip on the card. Outreach folds new, notified and
# proposal_sent together, because from where you sit those are one stage —
# "sent, no reply yet".
UW_STAGES = [
    {'key': 'offen', 'statuses': ('new', 'notified'), 'accent_mix': 22},
    {'key': 'outreach', 'statuses': ('proposal_sent',), 'accent_mix': 48},
    {'key': 'in_kontakt', 'statuses': ('interviewing',), 'accent_mix': 74},
    {'key': 'angebot', 'statuses': ('offer_sent',), 'accent_mix': 100},
]

# Funnel rank per status — linear, because a pipeline only ever moves forward.
# Used together with the recorded history, so the funnel counts the highest
# stage a job ever reached rather than where it sits now: a rejected job was
# applied to and interviewed first, and a snapshot of current status would
# History cohort. rejected/archived/ignored are deliberately absent, because we do
# not know how far they got before the no came. Missing beats invented.
UW_FUNNEL_RANK = {'new': 0, 'notified': 0, 'proposal_sent': 1, 'interviewing': 2, 'offer_sent': 3, 'hired': 4}


def _fmt_num(value, decimals=0):
    """English number formatting: $24,150 and $55.00."""
    return f'{value:,.{decimals}f}'


def _uw_goal():
    """The daily goal from config.yaml. No entry means no tracker — better none
    at all than one measuring against a number nobody set."""
    try:
        txt = CONFIG.read_text(encoding='utf-8')
    except Exception:
        return None
    m = re.search(r'^\s*daily_proposal_goal:\s*(\d+)', txt, re.M)
    return int(m.group(1)) if m else None


def _uw_applied_dates(jobs):
    """Every day a proposal went out, as date objects, taken from the history.

    The source is the 'proposal_sent' history entry, not status_updated_at: that
    field is overwritten on the next stage change, and the day would be gone with
    it. applied_at is the fallback for records written before history existed.
    """
    out = []
    for j in jobs:
        stamps = [h.get('at') for h in j.get('history', []) if h.get('status') == 'proposal_sent']
        if not stamps and j.get('applied_at'):
            stamps = [j['applied_at']]
        for s in stamps:
            try:
                out.append(datetime.datetime.fromisoformat(s.replace('Z', '+00:00')).date())
            except (ValueError, AttributeError):
                continue
    return out


def _uw_streak(counts, goal, today, weekdays_only=True):
    """Days in a row the goal was met. The current day never breaks it — at nine
    in the morning, zero proposals is the normal state, not a lapse."""
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


def _uw_tracker(jobs, open_jobs, t, today):
    """The daily tracker: goal, progress, streak, seven days, next job.

    Fixed at the top of the tab rather than behind a view switch: it is the daily
    action, and what sits behind a click does not get looked at.
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

    # The bars show the SAME week as the counter beside them (Monday to Sunday of
    # the current week), not the last seven days. Two definitions of "week" sat
    # side by side before: a rolling seven days under a figure counting from Monday.
    bars = []
    for i in range(7):
        d = week_start + datetime.timedelta(days=i)
        n = counts.get(d, 0)
        h = min(round(n / goal * 100), 100) if goal else 0
        if d > today:
            cls = ' future'
        elif n >= goal:
            cls = ' hit'
        elif n:
            cls = ''
        else:
            cls = ' none'
        fill = '' if d > today else f'<span class="uw-daybar-fill" style="height:{max(h, 4) if n else 0}%"></span>'
        bars.append(f'<span class="uw-daybar{cls}" title="{d.isoformat()}: {n}">{fill}'
                    f'<span class="uw-daybar-lbl">{esc(t["weekdays"][d.weekday()])}</span></span>')

    # The daily goal is a batch, not a single job. So next to the one next job
    # there is a sentence that hands over the whole remaining batch at once — one
    # paste instead of five. The dashboard stays a pure view either way: it copies
    # the sentence, the work happens in the chat.
    todo = sorted(open_jobs, key=lambda j: -j.get('score', 0))[:max(goal - done, 0)]
    if todo:
        nxt = todo[0]
        gen = f'Generate the pitch page for Upwork job {nxt.get("id", "")} ("{nxt.get("title", "")}")'
        liste = ' · '.join(f'{j.get("id", "")} "{j.get("title", "")}"' for j in todo)
        batch = (f'Work through my Upwork goal for today: {len(todo)} applications, one after the other. '
                 f'{liste}. For each job check briefly whether it really fits, then the proposal, '
                 f'then show it to me before anything goes out.')
        batch_btn = (f'<button type="button" class="say-btn uw-batch-btn" data-say="{esc(batch)}">'
                     f'{esc(t["btn_batch"].format(n=len(todo)))}</button>')
        next_html = (f'<div class="uw-next"><span class="uw-next-lbl">{esc(t["next_up"])}</span>'
                     f'<a href="{esc(nxt.get("url", "#"))}" target="_blank" rel="noopener">{md(nxt.get("title", ""))}</a>'
                     f'<span class="uw-score strong">{nxt.get("score", 0)}</span>'
                     f'<button type="button" class="say-btn" data-say="{esc(gen)}">{esc(t["btn_generate"])}</button>'
                     f'{batch_btn}</div>')
    elif done >= goal:
        next_html = f'<div class="uw-next"><span class="uw-next-lbl">{esc(t["goal_done"])}</span></div>'
    else:
        next_html = f'<div class="uw-next"><span class="uw-next-lbl">{esc(t["no_open"])}</span></div>'

    try:
        mtime = datetime.datetime.fromtimestamp(UPWORK_JOBS.stat().st_mtime)
        stand = t['as_of'].format(t=mtime.strftime('%H:%M'), d=mtime.strftime('%d %b'))
    except OSError:
        stand = ''

    return (
        f'<div class="uw-tracker">'
        f'<div class="uw-tracker-head">'
        f'<span class="uw-tracker-title">{esc(t["today"])}</span>'
        f'<span class="uw-tracker-count"><b>{done}</b> / {goal} {esc(t["proposals"])}</span>'
        f'<span class="uw-tracker-meta">{esc(t["streak"].format(n=streak))} · {esc(t["week"].format(n=week_done))}</span>'
        f'<span class="uw-tracker-stand">{esc(stand)}</span>'
        f'</div>'
        f'<div class="uw-progress"><span class="uw-progress-fill" style="width:{pct}%"></span></div>'
        f'<div class="uw-days">{"".join(bars)}</div>'
        f'{next_html}'
        f'</div>'
    )


def _uw_reached(j):
    """The highest stage a job ever reached, taken from its history.

    The current status alone cannot tell you: a declined job was applied to and
    interviewed first, but it reads 'rejected'. Leaving those out — which is what
    counting current status does — flatters every rate in the funnel.
    """
    ranks = [UW_FUNNEL_RANK[h['status']] for h in j.get('history', [])
             if h.get('status') in UW_FUNNEL_RANK]
    if j.get('status') in UW_FUNNEL_RANK:
        ranks.append(UW_FUNNEL_RANK[j['status']])
    if not ranks and j.get('applied_at'):
        ranks.append(1)
    return max(ranks) if ranks else 0


def _uw_funnel(jobs, t):
    if not jobs:
        return ''
    reached = [(j, _uw_reached(j)) for j in jobs]
    counts = [(label, sum(1 for _, r in reached if r >= min_rank))
              for label, min_rank in t['funnel_stages']]
    top = counts[0][1] or 1
    prev = None
    rows = []
    for label, count in counts:
        width = max(round(count / top * 100), 3 if count else 0)
        # At zero, just the zero. "0% · 0% of previous" says the same thing three
        # times and makes the row look fuller than it is.
        cum_pct = f'{round(count / top * 100)}%' if count else ''
        of_prev = f" · {round(count / prev * 100)}% {t['of_prev']}" if prev and count else ''
        rows.append(
            f'<div class="uw-funnel-row">'
            f'<span class="uw-funnel-label">{esc(label)}</span>'
            f'<span class="uw-funnel-track"><span class="uw-funnel-bar" style="width:{width}%"></span></span>'
            f'<span class="uw-funnel-count">{count}</span>'
            f'<span class="uw-funnel-pct">{cum_pct}{of_prev}</span>'
            f'</div>'
        )
        prev = count
    return f'<div class="uw-funnel">{"".join(rows)}</div><p class="uw-funnel-note">{esc(t["funnel_note"])}</p>'


def _uw_insights(jobs, t, today):
    """The funnel plus three numbers. Any number without enough data behind it says
    what would unlock it — an empty tile explains nothing, and a rate computed from
    two data points is worse than no rate at all."""
    applied = [j for j in jobs if _uw_reached(j) >= 1]
    replied = [j for j in jobs if _uw_reached(j) >= 2]

    # Median time to reply: days between proposal_sent and interviewing, per job.
    spans = []
    for j in replied:
        h = {e['status']: e['at'] for e in j.get('history', []) if e.get('status') in ('proposal_sent', 'interviewing')}
        if 'proposal_sent' in h and 'interviewing' in h:
            try:
                a = datetime.datetime.fromisoformat(h['proposal_sent'].replace('Z', '+00:00'))
                b = datetime.datetime.fromisoformat(h['interviewing'].replace('Z', '+00:00'))
                spans.append((b - a).total_seconds() / 86400)
            except ValueError:
                continue
    spans.sort()

    recent = [d for d in _uw_applied_dates(jobs) if (today - d).days < 28]

    def tile(label, value, hint):
        val = f'<span class="uw-tile-val">{esc(value)}</span>' if value else '<span class="uw-tile-val empty">—</span>'
        return (f'<div class="uw-tile"><span class="uw-tile-lbl">{esc(label)}</span>{val}'
                f'<span class="uw-tile-hint">{esc(hint)}</span></div>')

    tiles = [
        tile(t['kpi_reply'],
             f'{round(len(replied) / len(applied) * 100)}%' if len(applied) >= 5 else '',
             t['kpi_reply_hint'].format(n=max(5 - len(applied), 0)) if len(applied) < 5
             else t['kpi_of'].format(a=len(replied), b=len(applied))),
        tile(t['kpi_speed'],
             t['kpi_days'].format(n=round(spans[len(spans) // 2])) if spans else '',
             t['kpi_speed_hint'] if not spans else t['kpi_from'].format(n=len(spans))),
        tile(t['kpi_rate'],
             _fmt_num(len(recent) / 4, 1) if recent else '',
             t['kpi_rate_hint']),
    ]
    return f'<div class="uw-tiles">{"".join(tiles)}</div>' + _uw_funnel(jobs, t)


def _uw_excluded_note(jobs, t):
    """How many jobs were filtered out, and why. They are deliberately not in the
    list — a job already taken, or one whose minimum bar you do not clear, is a
    dead end rather than an option. But the count belongs on screen: otherwise the
    list quietly shrinks and you go looking for the fault in yourself."""
    out = [j for j in jobs if j.get('status') in ('archived', 'ignored')]
    if not out:
        return ''
    me = _uw_profile()
    gone = sum(1 for j in out if (j.get('details') or {}).get('total_hired'))
    bar = sum(1 for j in out
              if (j.get('details') or {}).get('min_jss')
              and me.get('job_success')
              and (j['details']['min_jss'] > me['job_success']))
    bits = []
    if bar:
        bits.append(t['excl_bar'].format(n=bar))
    if gone:
        bits.append(t['excl_gone'].format(n=gone))
    rest = len(out) - gone - bar
    if rest > 0:
        bits.append(t['excl_other'].format(n=rest))
    return (f'<p class="uw-excluded">{esc(t["excl_lead"].format(n=len(out)))} '
            f'{esc(" · ".join(bits))}</p>')


def _uw_me_card(t):
    """Your own numbers — specifically the ones an application fails on.

    Not a trophy case: Job Success, earnings and hours are here because client
    minimums (`preferred_qualifications`) test against exactly these three. Reading
    a requirement should not mean going somewhere else to compare.

    The connects balance sits beside them because it is the real budget ceiling:
    at 7 to 22 connects a proposal, a balance is a finite number of applications,
    and seeing that only at the moment of sending is seeing it too late. The values
    come from config.yaml, never from the code — otherwise in four weeks there is a
    number here whose origin nobody can trace."""
    me = _uw_profile()
    if not me:
        return ''
    stats = []

    def stat(label, value, warn=False):
        cls = ' warn' if warn else ''
        stats.append(f'<div class="uw-me-stat{cls}"><span class="uw-me-val">{esc(value)}</span>'
                     f'<span class="uw-me-lbl">{esc(label)}</span></div>')

    if me.get('connects_balance'):
        c = int(me['connects_balance'])
        # A range rather than an average: a proposal costs anywhere from 7 to 22
        # connects, so a single figure here would be an invention.
        stat(t['me_connects'], f'{c}')
        stat(t['me_applications'], t['me_apps_val'].format(lo=c // 22, hi=c // 7))
    if me.get('job_success'):
        stat(t['me_jss'], f"{round(me['job_success'])}%")
    if me.get('lifetime_earnings'):
        stat(t['me_earned'], f"${_fmt_num(round(me['lifetime_earnings']))}")
    if me.get('hours_worked'):
        stat(t['me_hours'], f"{round(me['hours_worked'])} h")
    if me.get('hourly_rate'):
        stat(t['me_rate'], f"${_fmt_num(me['hourly_rate'], 2)}")

    notes = ''.join(
        f'<li>{esc(me[k])}</li>' for k in ('timezone_warning', 'connects_drain_note') if me.get(k))
    notes_html = f'<ul class="uw-me-notes">{notes}</ul>' if notes else ''
    return (f'<div class="uw-me"><div class="uw-me-head">{esc(t["me_title"])}'
            f'<span class="uw-me-sub">{esc(t["me_sub"])}</span></div>'
            f'<div class="uw-me-stats">{"".join(stats)}</div>{notes_html}</div>')


def _posted_ago(posted_date, t):
    """"3 hrs ago" from the Upwork API's created_date (ISO, e.g.
    2026-08-13T14:34:36+0000). Missing or malformed -> empty string, never a crash."""
    if not posted_date:
        return ''
    try:
        d = datetime.datetime.fromisoformat(posted_date.replace('Z', '+00:00'))
        now = datetime.datetime.now(datetime.timezone.utc)
        hrs = (now - d).total_seconds() / 3600
        if hrs < 1:
            return t['ago_lt1h']
        if hrs < 24:
            return t['ago_h'].format(n=int(hrs))
        return t['ago_d'].format(n=int(hrs // 24))
    except Exception:
        return ''


def _job_description(j):
    """The full text, whether it still sits in the record or beside it in a file.

    Descriptions live in context/upwork-jobs/<id>.md and the record carries only
    `description_file` — otherwise the job file is half description text (measured:
    40 of 83 KB at just 19 jobs). Both forms are read, so older records written
    before the split do not silently render empty.
    """
    inline = (j.get('description') or '').strip()
    if inline:
        return inline
    rel = j.get('description_file')
    if not rel:
        return ''
    try:
        text = (W / rel).read_text(encoding='utf-8')
    except OSError:
        return ''
    # The file's header (title plus meta line, down to the rule) is already on
    # screen here, so only show what comes after it.
    _, sep, rest = text.partition('\n---\n')
    return (rest if sep else text).strip()


def _budget_label(budget, job_type):
    """Normalises the wildly inconsistent budget strings the API returns (bare
    '500.0', '8.0-17.0/hr', 'Not provided', '$800.00 fixed', …) into one short
    column label."""
    b = (budget or '').strip()
    if not b or b in ('0.0', 'Not provided') or b.lower().startswith('not specified'):
        return 'n/a'
    if '$' in b or '/hr' in b or 'fix' in b.lower():
        return b
    if job_type == 'hourly':
        return f'${b}/hr'
    return f'${b} fix'


def _uw_stage_actions(j, t, is_due=False, nf=None):
    """The say-button text per stage — it only copies a chat sentence to the
    clipboard, the dashboard stays a pure view. The sentences match the examples in
    upwork-screener/SKILL.md step 5 so they are recognised when pasted, and they
    follow the configured language, as do the button labels
    mit t. Bei faelligem Follow-up kommt zusaetzlich ein Task-Button dazu -- STATUS.md
    is the only task truth in the workspace; the dashboard never writes there
    itself, it hands over a finished sentence to paste."""
    jid = j.get('id', '')
    title = j.get('title', '')
    status = j.get('status', 'new')
    gen_prompt = f'Generate the pitch page for Upwork job {jid} ("{title}")'
    reply_prompt = f'Set Upwork job {jid} to "In contact", the client replied.'
    offer_prompt = f'Set Upwork job {jid} to "Offer sent".'
    won_prompt = f'Set Upwork job {jid} to "Hired".'
    lost_prompt = f'Set Upwork job {jid} to "Rejected".'
    task_prompt = f'Add a task: follow up on Upwork job "{title}" (due {nf}).'
    if status in ('new', 'notified', 'proposal_sent'):
        actions = (
            f'<button type="button" class="say-btn" data-say="{esc(gen_prompt)}">{esc(t["btn_generate"])}</button>'
            f'<button type="button" class="apply-btn" data-url="{esc(j.get("url", "#"))}">{esc(t["btn_apply"])}</button>'
            f'<button type="button" class="say-btn" data-say="{esc(reply_prompt)}">{esc(t["btn_reply"])}</button>'
        )
    elif status == 'interviewing':
        actions = f'<button type="button" class="say-btn" data-say="{esc(offer_prompt)}">{esc(t["btn_offer"])}</button>'
    elif status == 'offer_sent':
        actions = (
            f'<button type="button" class="say-btn" data-say="{esc(won_prompt)}">{esc(t["btn_won"])}</button>'
            f'<button type="button" class="say-btn" data-say="{esc(lost_prompt)}">{esc(t["btn_lost"])}</button>'
        )
    else:
        actions = ''
    if is_due:
        actions += f'<button type="button" class="say-btn uw-task-btn" data-say="{esc(task_prompt)}">{esc(t["btn_task"])}</button>'
    return actions


# Status -> board stage. The list shows the same stage as the board so both views
# speak one vocabulary, including the colour ramp from pale (early) to strong
# (late).
UW_STATUS_STAGE = {'new': 'offen', 'notified': 'offen', 'proposal_sent': 'outreach',
                   'interviewing': 'in_kontakt', 'offer_sent': 'angebot'}
UW_STAGE_MIX = {'offen': 22, 'outreach': 48, 'in_kontakt': 74, 'angebot': 100}


def _uw_profile():
    """Your own numbers from config.yaml, the ones client minimums are checked
    against. If they are missing, the judgement is simply left out — an invented
    comparison would be worse than none."""
    try:
        txt = CONFIG.read_text(encoding='utf-8')
    except OSError:
        return {}
    out = {}
    for key in ('job_success', 'lifetime_earnings', 'hours_worked', 'hourly_rate',
                'jobs_completed', 'reviews', 'connects_balance'):
        m = re.search(rf'^\s*{key}:\s*([\d.]+)', txt, re.M)
        if m:
            out[key] = float(m.group(1))
    # The two warning notes are free text, so read to end of line. A missing entry
    # means "no note", not "all clear" — so the card shows nothing rather than
    # inventing an all-clear.
    for key in ('connects_drain_note', 'timezone_warning'):
        m = re.search(rf'^\s*{key}:\s*"([^"]*)"', txt, re.M)
        if m:
            out[key] = m.group(1)
    return out


def _uw_bewerbungslage(j, t):
    """The fields from find_jobs get — what the application costs, what the
    competition is bidding, whether the job is genuinely still open.

    The dashboard fetches nothing (it is a pure view, and static HTML cannot reach
    the MCP anyway). upwork-screener writes this, and only for the best open jobs —
    one call per job across the whole list would be exactly the
    Scraping-Muster aus upwork-regeln.md.
    """
    d = j.get('details') or {}
    if not d:
        return f'<h4>{esc(t["detail_lage"])}</h4><p class="uw-nodata">{esc(t["detail_nolage"])}</p>'
    rows = []
    if d.get('connects_cost') is not None:
        rows.append((t['lbl_connects'], t['val_connects'].format(n=d['connects_cost'])))
    if d.get('bid_avg') is not None:
        # On fixed-price jobs the bid is a total, not an hourly rate — an "/hr"
        # on it would simply be wrong.
        span = f"{d.get('bid_min', '?')}–{d.get('bid_max', '?')}"
        key = 'val_bids' if d.get('contract_type') == 'HOURLY' else 'val_bids_fixed'
        rows.append((t['lbl_bids'], t[key].format(avg=round(d['bid_avg'], 2), span=span)))
    if d.get('proposals') is not None:
        rows.append((t['lbl_proposals'], str(d['proposals'])))
    live = []
    if d.get('total_hired'):
        live.append(t['live_hired'])
    if d.get('total_offered'):
        live.append(t['live_offered'])
    if d.get('invites_sent'):
        live.append(t['live_invites'].format(n=d['invites_sent']))
    if live or d.get('fetched_at'):
        rows.append((t['lbl_live'], ' · '.join(live) if live else t['live_open']))
    bar = []
    if d.get('min_jss'):
        bar.append(f"JSS ≥ {d['min_jss']}%")
    if d.get('min_hours'):
        bar.append(t['bar_hours'].format(n=d['min_hours']))
    if d.get('min_earnings') and d['min_earnings'] not in ('Any', 'any'):
        bar.append(f"${d['min_earnings']}+")
    if bar:
        rows.append((t['lbl_bar'], ' · '.join(bar)))
    # The bar as a judgement, not a number: applying to a job whose minimum Job
    # Success you do not clear costs connects and never arrives.
    me = _uw_profile()
    fails = []
    if d.get('min_jss') and me.get('job_success') and d['min_jss'] > me['job_success']:
        fails.append(t['fit_jss'].format(need=d['min_jss'], have=me['job_success']))
    try:
        need_earn = float(str(d.get('min_earnings', '')).replace('$', '').replace(',', ''))
    except (TypeError, ValueError):
        need_earn = 0
    if need_earn and me.get('lifetime_earnings') and need_earn > me['lifetime_earnings']:
        fails.append(t['fit_earn'].format(need=round(need_earn), have=round(me['lifetime_earnings'])))
    if me:
        rows.append((t['lbl_fit'], t['fit_fail'].format(why=' · '.join(fails)) if fails else t['fit_ok']))
    shape = {'FULL_TIME': t['shape_full'], 'PART_TIME': t['shape_part'],
             'AS_NEEDED': t['shape_asneeded']}.get(d.get('engagement'))
    bits = [b for b in (shape, d.get('experience_level', '').title() or None) if b]
    if bits:
        rows.append((t['lbl_shape'], ' · '.join(bits)))
    # City and timezone in one line. The IANA zone keeps its full form on purpose:
    # its last segment is a representative city, not the client's city, so
    # shortening "America/Chicago" to "Chicago" for a client in Austin reads as a
    # second location rather than as a timezone. And when the zone city happens to
    # match the client's own, the short form just says the same word twice.
    ort = ', '.join(x for x in (d.get('client_city'), d.get('client_country')) if x)
    zone = (d.get('client_timezone') or '').replace('_', ' ')
    if ort and zone.split('/')[-1] == (d.get('client_city') or ''):
        zone = ''                       # nothing to add, the city already said it
    if ort or zone:
        rows.append((t['lbl_tz'], ' · '.join(x for x in (ort, zone) if x)))
    body = ''.join(f'<div class="uw-lage-row"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in rows)
    note = (f'<p class="uw-screening">{esc(t["detail_screening"])} {esc(d["screening_note"])}</p>'
            if d.get('screening_note') else '')
    # What else this client hires for says more than their star rating: a history
    # full of work in your field is a different signal from one full of video
    # editing, even at an identical 5.0 stars.
    hist = d.get('client_history') or []
    hist_html = ''
    if hist:
        items = ''.join(
            f'<li>{esc(h.get("title", ""))}'
            + (f'<span class="uw-hist-fb">{h["feedback"]}★</span>' if h.get('feedback') else '')
            + '</li>' for h in hist[:6])
        hist_html = f'<h4>{esc(t["detail_clienthist"])}</h4><ul class="uw-clienthist">{items}</ul>'
    # Screening questions arrive as their own API field and are mandatory to
    # answer — they belong on screen, not buried in the description text.
    q = d.get('screening_questions') or []
    q_html = (f'<h4>{esc(t["detail_questions"])}</h4><ol class="uw-questions">'
              + ''.join(f'<li>{esc(x)}</li>' for x in q) + '</ol>') if q else ''
    return (f'<h4>{esc(t["detail_lage"])}</h4><dl class="uw-lage">{body}</dl>'
            f'{note}{q_html}{hist_html}')


def _uw_flags(j, t):
    """Warning marks in the list: what makes an application hopeless or expensive.
    Only where data exists — no mark means "not fetched", never "all good"."""
    d = j.get('details') or {}
    if not d:
        return ''
    me = _uw_profile()
    out = []
    if d.get('total_hired'):
        out.append(f'<span class="uw-flag gone">{esc(t["flag_gone"])}</span>')
    fails = (d.get('min_jss') and me.get('job_success') and d['min_jss'] > me['job_success'])
    if fails:
        out.append(f'<span class="uw-flag bar">{esc(t["flag_bar"])}</span>')
    if d.get('engagement') == 'FULL_TIME':
        out.append(f'<span class="uw-flag soft">{esc(t["shape_full"])}</span>')
    return ''.join(out)


def _uw_stage_chip(j, t):
    """The stage as a plain label, with no behaviour. Closed jobs keep their own
    word (Won / Declined); collapsing them would throw that information away."""
    status = j.get('status', 'new')
    stage = UW_STATUS_STAGE.get(status)
    if not stage:
        return f'<span class="uw-stagechip closed">{esc(t["status"].get(status, status))}</span>'
    mix = UW_STAGE_MIX[stage]
    bg = f'color-mix(in srgb, var(--brand) {mix}%, var(--card))'
    fg = f'color-mix(in srgb, var(--brand) 55%, var(--text))'
    return (f'<span class="uw-stagechip" style="background:{bg}; color:{fg}">'
            f'{esc(t["stage_label"][stage])}</span>')


def _uw_comp_cell(j, t):
    """Competition in the row, not only in the detail view: 3 bids against 41 turns
    the decision immediately.

    No value means "not fetched", not "no competition" — hence a dash rather than a
    zero. Invited freelancers sit beside it, because a client who has sent 30
    invitations is actively recruiting, and the bid count alone hides that."""
    d = j.get('details') or {}
    n = d.get('proposals')
    if n is None:
        return '<span class="uw-due-none">–</span>'
    cls = ' low' if n <= 5 else (' high' if n >= 30 else '')
    lbl = t['comp_none'] if n == 0 else t['comp_n'].format(n=n)
    inv = (f'<span class="uw-comp-inv">{esc(t["comp_inv"].format(n=d["invites_sent"]))}</span>'
           if d.get('invites_sent') else '')
    return f'<span class="uw-comp-n{cls}">{esc(lbl)}</span>{inv}'


def _uw_due_inline(j, today, t):
    """The follow-up date, in the stage cell rather than a column of its own. Both
    describe the same pipeline position, and as its own column it stood empty
    across every job until the first follow-up was ever set."""
    chip = _uw_due_chip(j, today, t)
    return '' if 'uw-due-none' in chip else f'<span class="uw-due-inline">{chip}</span>'


def _uw_due_chip(j, today, t):
    """ONE chip for timing, so that whether something is due is never in question:
    red for today or overdue, amber for scheduled later, otherwise nothing.
    Separate displays for "due" and "date" made the eye search twice."""
    nf = j.get('next_follow_up')
    if not nf or j.get('status') in CLOSED_STATUSES:
        return '<span class="uw-due-none">–</span>'
    try:
        d = datetime.date.fromisoformat(nf)
    except ValueError:
        return '<span class="uw-due-none">–</span>'
    days = (d - today).days
    if days < 0:
        return f'<span class="uw-duechip over">{esc(t["due_over"].format(n=-days))}</span>'
    if days == 0:
        return f'<span class="uw-duechip over">{esc(t["due_today"])}</span>'
    return f'<span class="uw-duechip soon">{esc(t["due_in"].format(n=days))}</span>'


def _uw_row(j, today_iso, t):
    """One job row in the list view: the table layout, with stage-aware actions
    rather than a fixed pair of buttons."""
    score = j.get('score', 0)
    score_cls = ' strong' if score >= 70 else ''
    status = j.get('status', 'new')
    status_lbl = t['status'].get(status, status)
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
    due_badge = f'<span class="uw-due-badge">{esc(t["due_badge"].format(nf=nf))}</span>' if is_due else ''
    ago = _posted_ago(j.get('posted_date'), t) or '–'
    # Falls back to the rationale so a record written before summaries existed
    # still says something. The detail view prints the rationale under its own
    # heading, so it must not fall back there too — the same sentence twice under
    # two headings reads as a rendering fault, which is what it would be.
    zusammenfassung = (j.get('summary') or j.get('rationale') or '').strip()
    hat_summary = bool((j.get('summary') or '').strip())
    # Only the first paragraph goes in the row — the structured remainder would
    # blow the table apart and belongs in the detail view.
    zusammenfassung_kurz = zusammenfassung.split('\n\n')[0].strip()
    budget_lbl = _budget_label(j.get('budget'), j.get('job_type'))
    # The status column shows the status and nothing else. The actions used to sit
    # under it in the same cell, which made the label itself look clickable; they
    # live in the detail overlay now, which a click on the row opens.
    hist = ''.join(
        f'<li><span class="uw-hist-when">{esc((h.get("at") or "")[:10])}</span>'
        f'<span>{esc(t["status"].get(h.get("status", ""), h.get("status", "")))}</span></li>'
        for h in j.get('history', [])
    )
    hist_html = f'<h4>{esc(t["detail_history"])}</h4><ul class="uw-hist">{hist}</ul>' if hist else ''
    # Absaetze bleiben Absaetze. Ein einzelnes <p> um den ganzen Text laesst HTML
    # swallow every line break, and a 5,000-character posting becomes a wall of
    # text nobody reads. The full text stays OUT on purpose. It is stored so that
    # upwork-proposal and upwork-pitch-page can read it; in the dashboard it would
    # be that wall. What stands here is the summary, plus where the full text is.
    quelle = j.get('description_file')
    desc_html = (f'<h4>{esc(t["desc_summary"])}</h4>'
                 + ''.join(f'<p>{md(par.strip())}</p>'
                           for par in zusammenfassung.split('\n\n') if par.strip())
                 + (f'<p class="uw-desc-src">{esc(quelle)}</p>' if quelle else '')
                 ) if hat_summary else ''
    meta_bits = [b for b in (client_txt, budget_lbl, ago, status_lbl) if b]
    detail = (
        f'<div class="uw-detail" hidden>'
        f'<div class="uw-detail-head"><span class="uw-score{score_cls}">{score}</span>'
        f'<h3><a href="{esc(j.get("url", "#"))}" target="_blank" rel="noopener">{md(j.get("title", ""))}</a></h3></div>'
        f'<p class="uw-detail-meta">{esc(" · ".join(meta_bits))}</p>'
        f'{due_badge}'
        f'<h4>{esc(t["detail_why"])}</h4><p>{esc(j.get("rationale", ""))}</p>'
        f'{desc_html}{_uw_bewerbungslage(j, t)}{hist_html}'
        f'<div class="uw-actions">{_uw_stage_actions(j, t, is_due, nf)}</div>'
        f'</div>'
    )
    return (
        f'<tr class="uw-row{" due" if is_due else ""}" data-uwstatus="{status}" '
        f'data-uwstage="{UW_STATUS_STAGE.get(status, "closed")}" '
        f'data-uwtodo="{"1" if j.get("next_follow_up") and status not in CLOSED_STATUSES else "0"}" '
        f'data-uwdue="{"1" if is_due else "0"}" tabindex="0">'
        f'<td><span class="uw-score{score_cls}">{score}</span></td>'
        f'<td class="rt-td-name"><span class="rt-td-title">{md(j.get("title", ""))}{_uw_flags(j, t)}</span>'
        f'<span class="rt-td-desc">{esc(zusammenfassung_kurz)}</span>'
        f'{("<span class=\'rt-td-why\'>" + esc(j.get("rationale","")) + "</span>") if j.get("summary") and j.get("rationale") else ""}'
        f'{detail}</td>'
        f'<td class="uw-client">{esc(client_txt)}</td>'
        f'<td class="uw-comp">{_uw_comp_cell(j, t)}</td>'
        f'<td class="uw-budget">{esc(budget_lbl)}'
        + (f'<span class="uw-connects">{esc(t["val_connects"].format(n=(j.get("details") or {})["connects_cost"]))}</span>'
           if (j.get('details') or {}).get('connects_cost') is not None else '')
        + f'</td>'
        f'<td class="uw-ago">{esc(ago)}</td>'
        f'<td class="uw-stage-cell">{_uw_stage_chip(j, t)}{_uw_due_inline(j, TODAY, t)}</td>'
        f'</tr>')


def _uw_card(j, today_iso, t):
    """One job card in the stage board. Carries the same fields as the table row,
    nur als Karte statt <tr> -- Score, Kunde, Budget, Alter, Rationale, Follow-up-Badge."""
    score = j.get('score', 0)
    score_cls = ' strong' if score >= 70 else ''
    status = j.get('status', 'new')
    status_lbl = t['status'].get(status, status)
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
    due_badge = f'<span class="uw-due-badge">{esc(t["due_badge"].format(nf=nf))}</span>' if is_due else ''
    ago = _posted_ago(j.get('posted_date'), t) or '–'
    # Falls back to the rationale so a record written before summaries existed
    # still says something. The detail view prints the rationale under its own
    # heading, so it must not fall back there too — the same sentence twice under
    # two headings reads as a rendering fault, which is what it would be.
    zusammenfassung = (j.get('summary') or j.get('rationale') or '').strip()
    hat_summary = bool((j.get('summary') or '').strip())
    # Only the first paragraph goes in the row — the structured remainder would
    # blow the table apart and belongs in the detail view.
    zusammenfassung_kurz = zusammenfassung.split('\n\n')[0].strip()
    budget_lbl = _budget_label(j.get('budget'), j.get('job_type'))
    meta_bits = [b for b in (client_txt, budget_lbl, ago, status_lbl) if b]
    # The card stays short and readable; everything long — description, history —
    # sits in the detail block and is shown only in the overlay. The description
    # used to squeeze into the column as a collapsible <details> and made it noisy.
    hist = ''.join(
        f'<li><span class="uw-hist-when">{esc((h.get("at") or "")[:10])}</span>'
        f'<span>{esc(t["status"].get(h.get("status", ""), h.get("status", "")))}</span></li>'
        for h in j.get('history', [])
    )
    hist_html = f'<h4>{esc(t["detail_history"])}</h4><ul class="uw-hist">{hist}</ul>' if hist else ''
    # Absaetze bleiben Absaetze. Ein einzelnes <p> um den ganzen Text laesst HTML
    # swallow every line break, and a 5,000-character posting becomes a wall of
    # text nobody reads. The full text stays OUT on purpose. It is stored so that
    # upwork-proposal and upwork-pitch-page can read it; in the dashboard it would
    # be that wall. What stands here is the summary, plus where the full text is.
    quelle = j.get('description_file')
    desc_html = (f'<h4>{esc(t["desc_summary"])}</h4>'
                 + ''.join(f'<p>{md(par.strip())}</p>'
                           for par in zusammenfassung.split('\n\n') if par.strip())
                 + (f'<p class="uw-desc-src">{esc(quelle)}</p>' if quelle else '')
                 ) if hat_summary else ''
    detail = (
        f'<div class="uw-detail" hidden>'
        f'<div class="uw-detail-head"><span class="uw-score{score_cls}">{score}</span>'
        f'<h3><a href="{esc(j.get("url", "#"))}" target="_blank" rel="noopener">{md(j.get("title", ""))}</a></h3></div>'
        f'<p class="uw-detail-meta">{esc(" · ".join(meta_bits))}</p>'
        f'{due_badge}'
        f'<h4>{esc(t["detail_why"])}</h4><p>{esc(j.get("rationale", ""))}</p>'
        f'{desc_html}{_uw_bewerbungslage(j, t)}{hist_html}'
        f'<div class="uw-actions">{_uw_stage_actions(j, t, is_due, nf)}</div>'
        f'</div>'
    )
    return (
        f'<li class="uw-card{" due" if is_due else ""}" data-uwdue="{"1" if is_due else "0"}" tabindex="0" role="button">'
        f'<div class="uw-card-top"><span class="uw-score{score_cls}">{score}</span>'
        f'<span class="uw-card-title">{md(j.get("title", ""))}</span></div>'
        f'<div class="uw-card-meta">{esc(" · ".join(meta_bits))}</div>'
        f'{due_badge}'
        f'<div class="uw-card-rationale">{esc(zusammenfassung_kurz)}</div>'
        f'{detail}'
        f'</li>'
    )


def _uw_render(jobs, active, open_jobs, present_statuses, sort_key, today_iso, lang):
    """Builds list, board and stats for one language — the one set in config.yaml.
    Kept as a parameter rather than read from the global so the three views can
    never disagree about which language they are rendering."""
    t = UW_I18N[lang]
    # Filters follow how the list is actually searched: by stage (the same four as
    # the board) and by whether something is waiting on you (open to-do, due
    # today). One pill per raw status sat here before — "New" and "Notified" beside
    # each other are the same stage as far as choosing a job goes.
    stage_keys = [s['key'] for s in UW_STAGES if any(
        UW_STATUS_STAGE.get(j.get('status')) == s['key'] for j in active)]
    UW_FILTERS = ([('all', t['filter_alle'])]
                  + [(f'stage:{k}', t['stage_label'][k]) for k in stage_keys]
                  + [('todo', t['filter_todo']), ('due', t['filter_faellig'])]
                  + ([('stage:closed', t['filter_closed'])]
                     if any(j.get('status') in ('hired', 'rejected') for j in active) else []))
    filterbar = '<div class="uw-filterbar">' + ''.join(
        f'<button type="button" class="pill uw-filterpill{" active" if key == "all" else ""}" data-uwfilter="{key}">{esc(label)}</button>'
        for key, label in UW_FILTERS
    ) + '</div>'
    th = ''.join(f'<th>{esc(h)}</th>' for h in t['th'])
    list_html = (_uw_me_card(t) + filterbar +
                 f'<p class="uw-score-legend">{esc(t["score_legend"])}</p>'
                 # Columns are cut around what decides an application: Competition
                 # is here because 3 bids against 41 turns the choice immediately
                 # and stood nowhere before. Due is not a column of its own — it
                 # was empty across every row until a follow-up was first set; the
                 # date chip sits in the stage cell now, where it
                 # inhaltlich hingehoert (beides beschreibt den Pipeline-Stand).
                 f'<table class="rt-table uw-table"><colgroup>'
                 f'<col style="width:6%"><col style="width:34%"><col style="width:13%">'
                 f'<col style="width:11%"><col style="width:12%"><col style="width:9%">'
                 f'<col style="width:15%">'
                 f'</colgroup><thead><tr>{th}</tr></thead>'
                 f'<tbody>{"".join(_uw_row(j, today_iso, t) for j in active)}</tbody></table>'
                 # Filtered-out jobs are not shown but are counted: otherwise 19
                 # jobs quietly become 15, and that looks like data loss rather
                 # than a decision.
                 + _uw_excluded_note(jobs, t))

    cols = []
    for stage in UW_STAGES:
        stage_jobs = sorted((j for j in open_jobs if j.get('status') in stage['statuses']), key=sort_key)
        accent = f"color-mix(in srgb, var(--brand) {stage['accent_mix']}%, var(--card))"
        cards = (''.join(_uw_card(j, today_iso, t) for j in stage_jobs)
                 or f'<li class="uw-empty">{esc(t["stage_empty"][stage["key"]])}</li>')
        cols.append(
            f'<div class="uw-col">'
            f'<div class="uw-col-head" style="border-top-color: {accent}">'
            f'<div><div class="uw-col-title">{esc(t["stage_label"][stage["key"]])}</div>'
            f'<div class="uw-col-hint">{esc(t["stage_hint"][stage["key"]])}</div></div>'
            f'<span class="uw-col-count" style="color: {accent}; background: color-mix(in srgb, {accent} 16%, transparent)">{len(stage_jobs)}</span>'
            f'</div>'
            f'<ul class="uw-col-body">{cards}</ul>'
            f'</div>'
        )
    board_html = f'<div class="uw-board">{"".join(cols)}</div>'
    stats_html = _uw_insights(jobs, t, TODAY) or f'<p class="sub">{esc(t["stats_empty"])}</p>'

    return (
        _uw_tracker(jobs, open_jobs, t, TODAY) +
        f'<div class="uw-viewbar">'
        f'<button type="button" class="pill uw-viewpill active" data-uwview="list">{esc(t["view"]["list"])}</button>'
        f'<button type="button" class="pill uw-viewpill" data-uwview="board">{esc(t["view"]["board"])}</button>'
        f'<button type="button" class="pill uw-viewpill" data-uwview="stats">{esc(t["view"]["stats"])}</button>'
        f'</div>'
        f'<div class="uw-view uw-view-list">{list_html}</div>'
        f'<div class="uw-view uw-view-board" hidden>{board_html}</div>'
        f'<div class="uw-view uw-view-stats" hidden>{stats_html}</div>'
    )



T = UW_I18N[LANG]



def parse_upwork():
    """Job-Liste aus context/.upwork_jobs.json (geschrieben vom upwork-screener-Skill) --
    in three views (List / Pipeline / Insights). The file is optional — if it is
    missing the tab stays empty rather than breaking, the same as every other
    optional source. Sorting is the same everywhere: open due follow-ups first,
    then score."""
    if not UPWORK_JOBS.is_file():
        return f'<p class="sub">{esc(T["no_run"])}</p>'
    try:
        jobs = json.loads(UPWORK_JOBS.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        # Deliberately narrow. A bare `except Exception` here once reported a
        # NameError inside this file as "your JSON is broken", which sends you
        # looking at a file that was fine all along.
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
    # Filter values are the actual status values, the same ones the status column
    # shows — no separate grouping beside it, or a filter ends up named something
    # ("Outreach") the column itself never says ("Proposal sent").
    present_statuses = [s for s in ('new', 'notified', 'proposal_sent', 'interviewing',
                                     'offer_sent', 'hired', 'rejected')
                         if any(j.get('status') == s for j in active)]

    return _uw_render(jobs, active, open_jobs, present_statuses,
                      sort_key, today_iso, LANG)


# The loader calls render(); inside this file the entry point is parse_upwork().
render = parse_upwork
