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
            j['status_updated_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
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

args = ap.parse_args()
args.func(args)
