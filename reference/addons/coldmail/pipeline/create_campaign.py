#!/usr/bin/env python3
"""
Create an Instantly campaign from a JSON config, optionally import leads,
optionally activate.

End-to-end flow:
  1. POST /api/v2/campaigns          → creates draft campaign with sequence
  2. POST /api/v2/leads (batched)    → imports leads from CSV (if --leads)
  3. POST /api/v2/campaigns/{id}/activate → activates (if --activate)

Config schema: see campaign-config.template.json in this folder.

Usage:
  python create_campaign.py --config my-campaign.json
  python create_campaign.py --config my-campaign.json --leads ../outbound/x.csv
  python create_campaign.py --config my-campaign.json --leads x.csv --activate
  python create_campaign.py --config my-campaign.json --dry-run
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

# Reuse lead import logic
sys.path.insert(0, str(Path(__file__).parent))
from import_to_instantly import read_csv, import_leads  # noqa: E402


load_dotenv(Path(__file__).parent.parent / '.env')

INSTANTLY_API_KEY = os.getenv('INSTANTLY_API_KEY')
INSTANTLY_API_BASE = 'https://api.instantly.ai/api/v2'


def get_headers():
    return {
        'Authorization': f'Bearer {INSTANTLY_API_KEY}',
        'Content-Type': 'application/json',
    }


def build_payload(cfg):
    """Translate our friendly config schema into Instantly v2 API payload."""
    schedule = cfg['schedule']
    settings = cfg.get('settings', {})

    sequence_steps = []
    for step in cfg['sequence']:
        sequence_steps.append({
            'type': 'email',
            'delay': step.get('delay_days', 0),
            'variants': [
                {
                    'subject': v.get('subject', ''),
                    'body': v.get('body', ''),
                }
                for v in step['variants']
            ],
        })

    payload = {
        'name': cfg['name'],
        'campaign_schedule': {
            'schedules': [
                {
                    'name': 'Default Schedule',
                    'timing': {
                        'from': schedule.get('from', '09:00'),
                        'to': schedule.get('to', '17:00'),
                    },
                    'days': schedule.get('days', {
                        '1': True, '2': True, '3': True, '4': True, '5': True,
                        '0': False, '6': False,
                    }),
                    'timezone': schedule.get('timezone', 'Australia/Sydney'),
                }
            ]
        },
        'sequences': [{'steps': sequence_steps}],
        'email_list': cfg['email_list'],
        'daily_limit': settings.get('daily_limit', 30),
        'email_gap': settings.get('email_gap', 10),
        'stop_on_reply': settings.get('stop_on_reply', True),
        'stop_on_auto_reply': settings.get('stop_on_auto_reply', True),
        'open_tracking': settings.get('open_tracking', False),
        'link_tracking': settings.get('link_tracking', False),
    }
    return payload


def create_campaign(cfg):
    payload = build_payload(cfg)
    url = f'{INSTANTLY_API_BASE}/campaigns'
    response = requests.post(url, headers=get_headers(), json=payload)

    if response.status_code not in (200, 201):
        raise Exception(f'Create-campaign failed {response.status_code}: {response.text}')

    data = response.json()
    return data.get('id') or data.get('campaign_id') or data.get('uuid')


def activate_campaign(campaign_id):
    url = f'{INSTANTLY_API_BASE}/campaigns/{campaign_id}/activate'
    response = requests.post(url, headers=get_headers())

    if response.status_code not in (200, 201, 204):
        raise Exception(f'Activate failed {response.status_code}: {response.text}')

    return True


def validate_config(cfg):
    required = ['name', 'email_list', 'schedule', 'sequence']
    missing = [k for k in required if k not in cfg]
    if missing:
        raise ValueError(f'Config missing required keys: {missing}')

    if not cfg['email_list']:
        raise ValueError('email_list is empty — need at least one sender account')
    if not cfg['sequence']:
        raise ValueError('sequence is empty — need at least one email step')

    for i, step in enumerate(cfg['sequence']):
        if not step.get('variants'):
            raise ValueError(f'sequence step {i+1} has no variants')


def main():
    parser = argparse.ArgumentParser(
        description='Create an Instantly campaign from JSON config',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--config', required=True, help='Path to campaign JSON config')
    parser.add_argument('--leads', help='Path to cleaned leads CSV to import after creation')
    parser.add_argument('--activate', action='store_true', help='Activate campaign after lead import')
    parser.add_argument('--dry-run', action='store_true', help='Validate + show payload, do not call API')
    args = parser.parse_args()

    if not INSTANTLY_API_KEY:
        print('Error: INSTANTLY_API_KEY not set in .env')
        sys.exit(1)

    config_path = Path(args.config)
    if not config_path.exists():
        print(f'Error: config not found: {config_path}')
        sys.exit(1)

    with open(config_path) as f:
        cfg = json.load(f)

    try:
        validate_config(cfg)
    except ValueError as e:
        print(f'Config validation error: {e}')
        sys.exit(1)

    payload = build_payload(cfg)

    print(f'Campaign: {cfg["name"]}')
    print(f'  Senders:    {len(cfg["email_list"])}  ({", ".join(cfg["email_list"])})')
    print(f'  Sequence:   {len(cfg["sequence"])} steps')
    print(f'  Timezone:   {payload["campaign_schedule"]["schedules"][0]["timezone"]}')
    print(f'  Daily limit: {payload["daily_limit"]}/sender')
    print(f'  Tracking:   open={payload["open_tracking"]} click={payload["link_tracking"]}')

    if args.dry_run:
        print('\n[DRY RUN] Payload:')
        print(json.dumps(payload, indent=2))
        if args.leads:
            print(f'\n[DRY RUN] Would import leads from: {args.leads}')
        if args.activate:
            print('[DRY RUN] Would activate after import')
        return

    print('\nCreating campaign...')
    try:
        campaign_id = create_campaign(cfg)
    except Exception as e:
        print(f'Failed: {e}')
        sys.exit(1)

    if not campaign_id:
        print('Error: campaign created but no ID returned')
        sys.exit(1)

    print(f'Campaign created: {campaign_id}')
    print(f'  https://app.instantly.ai/app/campaign/{campaign_id}')

    if args.leads:
        leads_path = Path(args.leads)
        if not leads_path.exists():
            print(f'Error: leads CSV not found: {leads_path}')
            sys.exit(1)

        print(f'\nReading leads: {leads_path}')
        leads = read_csv(leads_path)
        print(f'Found {len(leads)} leads')

        if leads:
            result = import_leads(campaign_id, leads, skip_duplicates=True)
            if result['errors']:
                print('\nLead import had errors:')
                for err in result['errors']:
                    print(f'  - {err}')

    if args.activate:
        print('\nActivating campaign...')
        try:
            activate_campaign(campaign_id)
            print('Campaign activated.')
        except Exception as e:
            print(f'Activate failed: {e}')
            print('(Campaign + leads are saved as draft. Activate manually in Instantly UI.)')
            sys.exit(1)


if __name__ == '__main__':
    main()
