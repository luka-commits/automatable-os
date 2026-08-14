#!/usr/bin/env python3
"""Fetches real brand SVGs once into assets/logos/, so the pitch page can ship
them embedded -- a pitch page must not make external requests at runtime, so
it can't reach out to a CDN when someone opens it.

Why real logos instead of generated shapes: a client recognizes the
GoHighLevel or n8n mark before they read the label. A redrawn stand-in symbol,
they never recognize.

Not every brand is available. Slack and OpenAI had their logos pulled from the
collection (404) -- for those, the node falls back to its shape symbol instead
of showing a wrong logo.

    python3 fetch_logos.py            # fetches the default list
    python3 fetch_logos.py --check    # only reports what's missing
"""
import pathlib
import sys
import urllib.request
import urllib.error

ASSETS = pathlib.Path(__file__).resolve().parent.parent / 'assets'
OUT = ASSETS / 'logos'

# slug -> how Claude references it in the graph
WANTED = [
    'n8n', 'zapier', 'make', 'hubspot', 'googleads', 'googlesheets', 'notion',
    'airtable', 'stripe', 'twilio', 'whatsapp', 'gmail', 'calendly', 'shopify',
    'wordpress', 'webflow', 'salesforce', 'pipedrive', 'trello', 'asana',
    'googlecalendar', 'typeform', 'mailchimp', 'openai',
]


def fetch(slug):
    """With a User-Agent header. Without one the CDN answers Python's default
    identifier with a 403, while the same URL returns 200 via curl -- without
    the header this looks like "logo doesn't exist" instead of "rejected"."""
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
    except Exception as e:                      # network down: fail loud, don't guess
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

    print(f'have: {len(have)}')
    if missing:
        print(f'unavailable ({len(missing)}): {", ".join(missing)}')
        print('  -> these nodes show their shape symbol instead of a wrong logo.')


if __name__ == '__main__':
    main()
