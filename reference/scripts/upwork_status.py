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


def cmd_migrate(args):
    """Seeds history for jobs that don't have one yet. Idempotent.

    Only what is provable gets reconstructed: 'new' at found_at, plus today's
    status at status_updated_at. Steps that were never recorded are NOT invented
    — a fabricated history curve is worse than a short one.
    """
    jobs = load()
    seeded = applied = 0
    for j in jobs:
        if j.get('history'):
            continue
        found = j.get('found_at') or j.get('status_updated_at')
        if found:
            add_history(j, 'new', found)
        st = j.get('status', 'new')
        if st != 'new':
            add_history(j, st, j.get('status_updated_at') or found)
        seeded += 1
        if st in ('proposal_sent', 'interviewing', 'offer_sent', 'hired') and not j.get('applied_at'):
            j['applied_at'] = j.get('status_updated_at') or found
            applied += 1
    if args.dry_run:
        print(f'DRY RUN: {seeded} of {len(jobs)} jobs would get a history, {applied} an applied_at.')
        return
    save(jobs)
    print(f'{seeded} of {len(jobs)} jobs given a history, {applied} an applied_at.')


# Upwork's terms cap caching of API responses at 24 hours. That covers the
# verbatim Upwork content, not your own work — score, rationale, status, notes
# and history are yours and stay.
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

p_mig = sub.add_parser('migrate', help='Seed history for existing records (idempotent).')
p_mig.add_argument('--dry-run', action='store_true')
p_mig.set_defaults(func=cmd_migrate)

p_pru = sub.add_parser('prune', help="Drop Upwork content older than 24h (Upwork's caching rule).")
p_pru.add_argument('--hours', type=int, default=24)
p_pru.add_argument('--dry-run', action='store_true')
p_pru.set_defaults(func=cmd_prune)

args = ap.parse_args()
args.func(args)
