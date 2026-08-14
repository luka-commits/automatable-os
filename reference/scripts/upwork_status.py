#!/usr/bin/env python3
"""Sets the status of an Upwork job in context/.upwork_jobs.json.

The small CRM mechanic behind the upwork-screener skill: a job moves through
new -> notified -> proposal_sent -> interviewing -> offer_sent -> hired
(or rejected / archived / ignored at any point). Dashboard labels:
interviewing = "In contact", offer_sent = "Offer sent".
--follow-up sets next_follow_up; the dashboard flags anything due in the
Upwork tab, grouped by stage.

Usage:
    python3 upwork_status.py set <job_id> <status> [--follow-up +3d|YYYY-MM-DD] [--note "..."]
    python3 upwork_status.py list [--status proposal_sent]

Exits 1 if the job_id doesn't exist — a silent no-op would be worse than an
error that names the cause.
"""
import argparse, datetime, json, pathlib, re, sys

W = pathlib.Path(__file__).resolve().parents[2]
JOBS = W / 'context/.upwork_jobs.json'
STATUSES = ('new', 'notified', 'proposal_sent', 'interviewing', 'offer_sent', 'hired', 'rejected', 'archived', 'ignored')


def load():
    if not JOBS.is_file():
        return []
    try:
        return json.loads(JOBS.read_text(encoding='utf-8'))
    except Exception:
        print(f'ABORT: {JOBS} is not valid JSON.', file=sys.stderr)
        sys.exit(1)


def save(jobs):
    JOBS.write_text(json.dumps(jobs, indent=2, ensure_ascii=False), encoding='utf-8')


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def add_history(j, status, at=None):
    """Appends a stage change to the job's history — append-only.

    Without it, "how many proposals went out today" is unanswerable:
    status_updated_at is overwritten on the next change, so the day is gone.
    The same status twice in a row writes nothing, otherwise a repeated `set`
    inflates the list without telling you anything.
    """
    hist = j.setdefault('history', [])
    if hist and hist[-1].get('status') == status:
        return False
    hist.append({'status': status, 'at': at or now_iso()})
    return True


def parse_follow_up(s):
    if not s:
        return None
    m = re.match(r'^\+(\d+)d$', s)
    if m:
        return (datetime.date.today() + datetime.timedelta(days=int(m.group(1)))).isoformat()
    try:
        return datetime.date.fromisoformat(s).isoformat()
    except ValueError:
        print(f'ABORT: --follow-up expects +Nd or YYYY-MM-DD, got: {s}', file=sys.stderr)
        sys.exit(1)


def cmd_set(args):
    jobs = load()
    for j in jobs:
        if j.get('id') == args.job_id:
            if args.status not in STATUSES:
                print(f'ABORT: unknown status "{args.status}". Allowed: {", ".join(STATUSES)}', file=sys.stderr)
                sys.exit(1)
            j['status'] = args.status
            j['status_updated_at'] = now_iso()
            add_history(j, args.status)
            # applied_at is the day of the FIRST application and is never
            # overwritten — the daily goal counter hangs off it. A job moving on
            # to interviewing later must not shift the day you applied.
            if args.status == 'proposal_sent' and not j.get('applied_at'):
                j['applied_at'] = j['status_updated_at']
            if args.follow_up:
                j['next_follow_up'] = parse_follow_up(args.follow_up)
            elif args.status in ('hired', 'rejected', 'archived', 'ignored'):
                j['next_follow_up'] = None  # closed out, no follow-up due anymore
            if args.note:
                j['notes'] = (j.get('notes', '') + ' ' + args.note).strip()
            save(jobs)
            print(f'{j["id"]} -> {args.status}' + (f' (follow-up {j["next_follow_up"]})' if j.get('next_follow_up') else ''))
            # hired is not the end of the pipeline, it is the handover to delivery.
            # Without this line the job sits here with a final status while the work,
            # the client and the deadlines live nowhere.
            if args.status == 'hired' and not j.get('project'):
                print(f'\n  This job has no project yet. Say "I won this job", or:\n'
                      f'    python3 reference/scripts/new_project.py --from-job {j["id"]} --dry-run')
            return
    print(f'ABORT: job_id "{args.job_id}" not found in {JOBS}.', file=sys.stderr)
    sys.exit(1)


def cmd_list(args):
    jobs = load()
    if args.status:
        jobs = [j for j in jobs if j.get('status') == args.status]
    jobs.sort(key=lambda j: j.get('score', 0), reverse=True)
    for j in jobs:
        fu = f' follow-up:{j["next_follow_up"]}' if j.get('next_follow_up') else ''
        print(f'{j.get("score", "?"):>3}  {j.get("status", "?"):<14} {j.get("id")}  {j.get("title", "")[:70]}{fu}')


def cmd_summary(args):
    """The cheap read path: the whole pipeline in ~20 lines instead of the raw JSON.

    Reading the job file directly costs tens of thousands of tokens and eats a
    session before any work starts. This is what `morning` and any "how does the
    pipeline stand" question should call.
    """
    jobs = load()
    if not jobs:
        print('No jobs logged yet.')
        return
    today = datetime.date.today()
    counts = {}
    for j in jobs:
        st = j.get('status', 'new')
        counts[st] = counts.get(st, 0) + 1

    print(f'{len(jobs)} jobs logged.\n')
    print('Funnel:')
    for s in STATUSES:
        if counts.get(s):
            print(f'  {counts[s]:3d}  {s}')

    open_jobs = [j for j in jobs if j.get('status') in ('new', 'notified')]
    applied = sum(counts.get(s, 0) for s in ('proposal_sent', 'interviewing', 'offer_sent', 'hired'))
    print(f'\n  {len(open_jobs)} untouched, {applied} applied or further.')
    if open_jobs and not applied:
        print('  NOTE: nothing past "notified" — the funnel stops before the application.')

    today_applied = sum(
        1 for j in jobs
        for h in j.get('history', [])
        if h.get('status') == 'proposal_sent' and str(h.get('at', ''))[:10] == today.isoformat()
    )
    print(f'  {today_applied} proposal(s) sent today.')

    due = [j for j in jobs if j.get('next_follow_up') and j['next_follow_up'] <= today.isoformat()
           and j.get('status') not in ('hired', 'rejected', 'archived', 'ignored')]
    if due:
        print(f'\nFollow-ups due ({len(due)}):')
        for j in sorted(due, key=lambda x: x['next_follow_up'])[:10]:
            print(f'  {j["next_follow_up"]}  {j.get("id")}  {j.get("title", "")[:60]}')

    top = sorted(open_jobs, key=lambda j: j.get('score', 0), reverse=True)[:args.top]
    if top:
        print(f'\nBest untouched ({len(top)} of {len(open_jobs)}):')
        for j in top:
            print(f'  {j.get("score", "?"):>3}  {j.get("status", "?"):<9} {j.get("id")}  {j.get("title", "")[:60]}')

    stamps = [j['found_at'][:10] for j in jobs if j.get('found_at')]
    if stamps:
        print(f'\nFound between {min(stamps)} and {max(stamps)}.')


def derived_history(j):
    """A job's stage history, reconstructed read-only when none was recorded.

    Only what is provable: 'new' at found_at, plus the current status at
    status_updated_at. Steps that were never recorded are NOT invented — a
    fabricated curve is worse than a short one. This is the one place that
    rule lives; `migrate` writes what this returns and `export` reads it.
    """
    if j.get('history'):
        return list(j['history'])
    out = []
    found = j.get('found_at') or j.get('status_updated_at')
    if found:
        out.append({'status': 'new', 'at': found})
    st = j.get('status', 'new')
    if st != 'new':
        at = (j.get('applied_at') if st == 'proposal_sent' else None) or j.get('status_updated_at') or found
        if at:
            out.append({'status': st, 'at': at})
    return out


def cmd_migrate(args):
    """Seeds history for jobs that don't have one yet. Idempotent."""
    jobs = load()
    seeded = applied = 0
    for j in jobs:
        if j.get('history'):
            continue
        derived = derived_history(j)
        if not derived:
            continue
        j['history'] = derived
        seeded += 1
        st = j.get('status', 'new')
        if st in ('proposal_sent', 'interviewing', 'offer_sent', 'hired') and not j.get('applied_at'):
            j['applied_at'] = j.get('status_updated_at') or j.get('found_at')
            applied += 1
    if args.dry_run:
        print(f'DRY RUN: {seeded} of {len(jobs)} jobs would get a history, {applied} an applied_at.')
        return
    save(jobs)
    print(f'{seeded} of {len(jobs)} jobs given a history, {applied} an applied_at.')


# --- export ---------------------------------------------------------------
#
# Counters, and nothing else. This is the whole payload the community app ever
# receives: how many jobs reached a stage on a given day. No job id, no title,
# no client, no budget, no description.
#
# That is not squeamishness, it is the condition under which syncing is allowed
# at all. Upwork's terms cap caching of their content at 24 hours and rule out
# commercial use of their data; a shared server holding many users' job lists
# would be exactly the thing that gets accounts closed. Counters are your own
# activity, not Upwork's content, so they travel.
#
# The whitelist below is enforced before anything is printed. If a later change
# adds a field carrying job content, the export fails loudly here instead of
# quietly publishing it to everyone else's database.
COUNTER_OF = {
    'new': 'found', 'proposal_sent': 'applied', 'interviewing': 'replied',
    'offer_sent': 'offers', 'hired': 'won', 'rejected': 'lost',
}
COUNTERS = ('found', 'applied', 'replied', 'offers', 'won', 'lost')
EXPORT_KEYS = {'schema', 'generated_at', 'reported_through', 'history_recorded', 'days'}


def cmd_export(args):
    """Daily counters for the community sync. Prints JSON, writes nothing."""
    jobs = load()
    today = datetime.date.today()
    since = args.since or (today - datetime.timedelta(days=args.days)).isoformat()

    days, reconstructed = {}, 0
    for j in jobs:
        if not j.get('history'):
            reconstructed += 1
        for h in derived_history(j):
            counter = COUNTER_OF.get(h.get('status'))
            day = str(h.get('at', ''))[:10]
            if not counter or len(day) != 10 or day < since:
                continue
            days.setdefault(day, dict.fromkeys(COUNTERS, 0))[counter] += 1

    payload = {
        'schema': 1,
        'generated_at': now_iso(),
        # Everything up to this date is known: a day missing from `days` is a
        # real zero, a day after it is "no data yet". Without this the app
        # cannot tell an idle day from a day the OS simply never ran.
        'reported_through': today.isoformat(),
        # False means some rows were reconstructed from found_at/status_updated_at
        # rather than recorded live, so intermediate steps are missing.
        'history_recorded': reconstructed == 0,
        'days': [dict(day=d, **days[d]) for d in sorted(days)],
    }

    assert set(payload) == EXPORT_KEYS, f'export carries unexpected keys: {set(payload) - EXPORT_KEYS}'
    for row in payload['days']:
        extra = set(row) - {'day'} - set(COUNTERS)
        assert not extra, f'export row carries job content: {extra}'

    out = json.dumps(payload, indent=2)
    if args.out and args.out != '-':
        pathlib.Path(args.out).write_text(out, encoding='utf-8')
        print(f'{len(payload["days"])} day(s) written to {args.out}.')
    else:
        print(out)
    if reconstructed:
        print(f'NOTE: {reconstructed} of {len(jobs)} jobs have no recorded history, so their '
              f'intermediate steps are missing. Run `migrate` once to freeze what is provable.',
              file=sys.stderr)


# --- prune ----------------------------------------------------------------
#
# The same 24-hour rule, applied locally: verbatim Upwork content expires,
# your own work — score, rationale, status, notes and history — stays.
CACHED_FIELDS = ('description', 'client', 'budget', 'job_type', 'posted_date')


def cmd_prune(args):
    """Drops cached Upwork content older than 24 hours."""
    jobs = load()
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=args.hours)
    hits, fields = 0, 0
    for j in jobs:
        stamp = j.get('found_at')
        if not stamp:
            continue
        try:
            found = datetime.datetime.fromisoformat(stamp.replace('Z', '+00:00'))
        except ValueError:
            continue
        if found >= cutoff:
            continue
        present = [f for f in CACHED_FIELDS if j.get(f) not in (None, '')]
        if not present:
            continue
        hits += 1
        fields += len(present)
        if not args.dry_run:
            for f in present:
                j.pop(f, None)
            j['cache_pruned_at'] = now_iso()
    size = JOBS.stat().st_size if JOBS.is_file() else 0
    if args.dry_run:
        print(f'DRY RUN: {hits} of {len(jobs)} jobs older than {args.hours}h, '
              f'{fields} cached fields would be removed. File: {size / 1024:.0f} KB.')
        return
    save(jobs)
    print(f'{hits} jobs pruned, {fields} fields removed. '
          f'File: {size / 1024:.0f} KB -> {JOBS.stat().st_size / 1024:.0f} KB.')


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sub = ap.add_subparsers(dest='cmd', required=True)

p_set = sub.add_parser('set')
p_set.add_argument('job_id')
p_set.add_argument('status')
p_set.add_argument('--follow-up')
p_set.add_argument('--note')
p_set.set_defaults(func=cmd_set)

p_list = sub.add_parser('list')
p_list.add_argument('--status')
p_list.set_defaults(func=cmd_list)

p_sum = sub.add_parser('summary', help='The whole pipeline in ~20 lines — never read the raw JSON.')
p_sum.add_argument('--top', type=int, default=8)
p_sum.set_defaults(func=cmd_summary)

p_mig = sub.add_parser('migrate', help='Seed history for existing records (idempotent).')
p_mig.add_argument('--dry-run', action='store_true')
p_mig.set_defaults(func=cmd_migrate)

p_exp = sub.add_parser('export', help='Daily counters for the community sync — counters only, no job content.')
p_exp.add_argument('--since', help='YYYY-MM-DD, overrides --days.')
p_exp.add_argument('--days', type=int, default=90)
p_exp.add_argument('--out', help='File path, or "-" for stdout (default).')
p_exp.set_defaults(func=cmd_export)

p_pru = sub.add_parser('prune', help="Drop Upwork content older than 24h (Upwork's caching rule).")
p_pru.add_argument('--hours', type=int, default=24)
p_pru.add_argument('--dry-run', action='store_true')
p_pru.set_defaults(func=cmd_prune)

args = ap.parse_args()
args.func(args)
