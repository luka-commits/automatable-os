#!/usr/bin/env python3
"""Holt echte Marken-SVGs einmal nach assets/logos/, damit die Seite sie
eingebettet ausliefern kann -- eine Pitch-Page darf keine externen Requests
machen, also kann sie nicht zur Laufzeit an ein CDN.

Warum echte Logos statt generierter Symbole: ein Kunde erkennt das
GoHighLevel- oder n8n-Zeichen, bevor er die Beschriftung liest. Ein
nachgezeichnetes Symbol erkennt er nie.

Nicht alle Marken sind zu haben. Slack und OpenAI haben ihre Logos aus der
Sammlung nehmen lassen (404) -- fuer die faellt der Knoten auf sein
Formen-Symbol zurueck, statt ein falsches Logo zu zeigen.

    python3 fetch_logos.py            # holt die Standardliste
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
    """Mit User-Agent. Ohne einen antwortet das CDN mit 403 auf Pythons
    Default-Kennung, waehrend dieselbe URL per curl 200 liefert -- ohne den
    Header sieht das wie "Logo gibt es nicht" aus statt wie "abgewiesen"."""
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
    except Exception as e:                      # Netz weg: laut sein, nicht raten
        print(f'  {slug}: Netzwerkfehler {e}', file=sys.stderr)
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
        print(f'nicht verfuegbar ({len(missing)}): {", ".join(missing)}')
        print('  -> diese Knoten zeigen ihr Formen-Symbol statt eines falschen Logos.')


if __name__ == '__main__':
    main()
