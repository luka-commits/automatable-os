#!/usr/bin/env python3
"""Fetches real brand SVGs once into assets/logos/, so the page can embed them.
A pitch page must not make external requests, so it cannot reach a CDN at runtime.

Why real logos instead of generated symbols: a client recognises the GoHighLevel
or n8n mark before reading the label. A redrawn symbol they never recognise.

Not every brand is available. Slack and OpenAI had their logos pulled from the
collection (404), and for those the node falls back to its shape symbol rather
than showing a wrong logo.

    python3 fetch_logos.py            # fetches the default list
    python3 fetch_logos.py --check    # meldet nur, was fehlt
"""
import pathlib
import sys
import urllib.request
import urllib.error

ASSETS = pathlib.Path(__file__).resolve().parent.parent / 'assets'
OUT = ASSETS / 'logos'

# slug -> wie Claude ihn im Graph referenziert
WANTED = [
    'n8n', 'zapier', 'make', 'hubspot', 'googleads', 'googlesheets', 'notion',
    'airtable', 'stripe', 'twilio', 'whatsapp', 'gmail', 'calendly', 'shopify',
    'wordpress', 'webflow', 'salesforce', 'pipedrive', 'trello', 'asana',
    'googlecalendar', 'typeform', 'mailchimp', 'openai',
]


def fetch(slug):
    """With a user agent. Without one the CDN answers 403 to Python's
    Default-Kennung, waehrend dieselbe URL per curl 200 liefert -- ohne den
    header that reads as "no logo for this one" rather than as "refused"."""
    url = f'https://cdn.simpleicons.org/{slug}'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            if r.status != 200:
                return None
            return r.read().decode('utf-8')
    except urllib.error.HTTPError:
        return None
    except Exception as e:                      # network gone: be loud, do not guess
        print(f'  {slug}: network error {e}', file=sys.stderr)
        return None


def main():
    check = '--check' in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    have, missing = [], []
    for slug in WANTED:
        dest = OUT / f'{slug}.svg'
        if dest.is_file():
            have.append(slug)
            continue
        if check:
            missing.append(slug)
            continue
        svg = fetch(slug)
        if svg:
            dest.write_text(svg, encoding='utf-8')
            have.append(slug)
        else:
            missing.append(slug)

    print(f'vorhanden: {len(have)}')
    if missing:
        print(f'not available ({len(missing)}): {", ".join(missing)}')
        print('  -> these nodes show their shape icon rather than the wrong logo.')


if __name__ == '__main__':
    main()
