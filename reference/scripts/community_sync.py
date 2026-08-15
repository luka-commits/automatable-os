#!/usr/bin/env python3
"""Pushes your daily counters to the Freelancer OS community dashboard.

Opt-in. Without FOS_COMMUNITY_TOKEN set it does nothing and says so, which is
also what makes it safe to call from /morning and /eod unconditionally.

What leaves your machine is what `upwork_status.py export` prints, and nothing
else: how many jobs reached a stage on a given day. No job id, no title, no
client, no budget, no description. Run with --dry-run to see the exact bytes
before trusting that sentence.

    python3 community_sync.py [--days 90] [--dry-run]

Exits 0 when there is nothing to do, so a missing token never breaks a routine.
"""
import argparse, json, os, pathlib, subprocess, sys, urllib.error, urllib.request

SCRIPTS = pathlib.Path(__file__).resolve().parent

# No default address on purpose. A hardcoded URL means a copy of this package
# can post somewhere its owner never chose, and the first version of this file
# shipped pointing at a host that did not exist. Both the token and the address
# come from the member's own credentials file, or nothing is sent.
URL_VAR = 'FOS_COMMUNITY_URL'


def build_payload(days):
    """Runs the exporter as a subprocess rather than importing it.

    upwork_status.py parses arguments at import time, so importing it here
    would run its CLI instead of exposing a function.
    """
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / 'upwork_status.py'), 'export', '--days', str(days), '--out', '-'],
        capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stderr.strip() or 'export failed', file=sys.stderr)
        sys.exit(1)
    if proc.stderr.strip():
        print(proc.stderr.strip(), file=sys.stderr)
    return json.loads(proc.stdout)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--days', type=int, default=90)
    ap.add_argument('--dry-run', action='store_true', help='Print the exact payload, send nothing.')
    ap.add_argument('--url', default=os.environ.get(URL_VAR, ''))
    args = ap.parse_args()

    token = os.environ.get('FOS_COMMUNITY_TOKEN', '').strip()
    if not args.dry_run:
        if not token:
            print('Community sync is off (no FOS_COMMUNITY_TOKEN). Nothing sent.')
            return
        if not args.url:
            print(f'Community sync is off (no {URL_VAR}). Nothing sent.')
            return

    payload = build_payload(args.days)

    if args.dry_run:
        print(json.dumps(payload, indent=2))
        print(f'\n-- dry run: the above would go to {args.url}, nothing was sent.', file=sys.stderr)
        return

    req = urllib.request.Request(
        args.url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'},
        method='POST')
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', 'replace')[:300]
        print(f'Sync failed ({e.code}): {detail}', file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        # A dashboard being unreachable must never be the reason a morning
        # routine stops, so this reports and exits clean.
        print(f'Community dashboard unreachable ({e.reason}). Nothing sent, nothing lost.', file=sys.stderr)
        return

    print(f'Synced {body.get("days", 0)} day(s) through {body.get("reported_through", "?")}.')


main()
