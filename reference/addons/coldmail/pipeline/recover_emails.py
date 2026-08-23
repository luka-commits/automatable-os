#!/usr/bin/env python3
"""recover_emails.py — for leads with a website but no email, find the email via Firecrawl.

Scrapes the homepage (then /contact as fallback) and regex-extracts an email, preferring one on the
business's own domain. Parallel. Merges recovered leads into cleaned.csv.

Usage: python3 recover_emails.py --needs runs/<slug>/needs_email.csv --out runs/<slug>/cleaned.csv [--limit N]
"""
import os, csv, re, argparse, requests
from concurrent.futures import ThreadPoolExecutor

def _firecrawl_key():
    """Env first, then ~/.config/credentials.env — never KeyError-crash on import."""
    if os.environ.get('FIRECRAWL_API_KEY'):
        return os.environ['FIRECRAWL_API_KEY']
    try:
        for line in open(os.path.expanduser('~/.config/credentials.env')):
            if line.startswith('FIRECRAWL_API_KEY='):
                return line.split('=', 1)[1].strip().strip('"')
    except FileNotFoundError:
        pass
    raise SystemExit("[recover] no FIRECRAWL_API_KEY in env or ~/.config/credentials.env")

KEY = _firecrawl_key()
H = {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'}
EMAIL_RE = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
MAILTO_RE = re.compile(r'mailto:([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})', re.I)
JUNK = ('mhtml.blink', 'frame-', 'example.', 'sentry.', 'wix.com', 'godaddy', 'your-email', 'email@', 'domain.com',
        '.png', '.jpg', '.webp', '.gif', 'u003e', 'name@', 'test@')


def dom(u):
    m = re.search(r'https?://([^/]+)', (u or '').lower())
    d = (m.group(1) if m else (u or '').lower()).replace('www.', '')
    return d.split('/')[0] if d else ''


def scrape_emails(url):
    # Same single scrape, but ask for rawHtml too (Firecrawl charges per scrape, not per format -> credit-neutral).
    # mailto: links and footer markup hold emails that never render in the visible markdown text.
    try:
        r = requests.post('https://api.firecrawl.dev/v1/scrape', headers=H,
                          json={'url': url, 'formats': ['markdown', 'rawHtml'], 'onlyMainContent': False,
                                'timeout': 25000}, timeout=45)
        data = (r.json().get('data', {}) or {})
        md = data.get('markdown', '') or ''
        html = data.get('rawHtml', '') or ''
        mailtos = [e.lower() for e in MAILTO_RE.findall(html) if not any(j in e.lower() for j in JUNK)]  # highest-confidence
        text = [e.lower() for e in EMAIL_RE.findall(md + ' ' + html) if not any(j in e.lower() for j in JUNK)]
        return list(dict.fromkeys(mailtos + text))
    except Exception:
        return []


def recover(row):
    d = dom(row['website'])
    emails = scrape_emails(row['website'])
    if not emails:                                              # try /contact
        emails = scrape_emails(row['website'].rstrip('/') + '/contact')
    if not emails:
        return None
    # prefer an email on the business's own domain, else the first non-junk
    pick = next((e for e in emails if d and d.split('.')[0] in e), emails[0])
    row['email'] = pick
    return row


def push_supabase(recovered):
    """Persist recovered emails back to industry_operators (the cohort = source of truth), matched by
    website. Without this the recovery only lives in the CSV and is LOST when export_cohort overwrites
    it from Supabase — the gap that left London under-counted. Match by website (unique per business)."""
    import json, urllib.request, urllib.parse
    REF = "qhlklpweondgkswptyfc"
    key = [l.split('=', 1)[1].strip().strip('"') for l in open(os.path.expanduser('~/.config/credentials.env'))
           if l.startswith('POCKET_DASH_SUPABASE_SERVICE_ROLE=')][0]
    n = 0
    for r in recovered:
        w, e = (r.get('website') or '').strip(), (r.get('email') or '').strip()
        if not w or '@' not in e:
            continue
        q = urllib.parse.urlencode({'website': f'eq.{w}'})
        req = urllib.request.Request(f"https://{REF}.supabase.co/rest/v1/industry_operators?{q}",
                                     data=json.dumps({'email': e}).encode(), method='PATCH',
                                     headers={'apikey': key, 'Authorization': f'Bearer {key}',
                                              'Content-Type': 'application/json', 'Prefer': 'return=minimal'})
        try:
            urllib.request.urlopen(req, timeout=30); n += 1
        except Exception:
            pass
    print(f"  pushed {n} recovered emails to Supabase (by website)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--needs', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--push-supabase', action='store_true',
                    help='persist recovered emails back to industry_operators by website (cohort = source of truth)')
    a = ap.parse_args()
    needs = list(csv.DictReader(open(a.needs)))
    if a.limit:
        needs = needs[:a.limit]
    with ThreadPoolExecutor(max_workers=12) as ex:
        results = list(ex.map(recover, needs))
    recovered = [r for r in results if r]
    print(f"RECOVERY: {len(recovered)}/{len(needs)} emails found via Firecrawl ({100*len(recovered)//max(len(needs),1)}%)")
    for r in recovered[:6]:
        print(f"   {r['business_name'][:26]:28} {r['email']}")
    if a.push_supabase and recovered:
        push_supabase(recovered)
    # append to cleaned (dedup by email)
    if a.limit == 0 and recovered:
        existing = {row['email'].lower() for row in csv.DictReader(open(a.out))}
        add = [r for r in recovered if r['email'].lower() not in existing]
        with open(a.out, 'a', newline='') as f:
            csv.DictWriter(f, fieldnames=['business_name', 'city', 'website', 'email', 'first_name']).writerows(add)
        print(f"  appended {len(add)} new leads to {a.out}")


if __name__ == '__main__':
    main()
