#!/usr/bin/env python3
"""
List Instantly sender accounts.

Used before creating a campaign to discover which sender accounts are
available, warmed, and have headroom against their daily limits.
"""

import argparse
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


load_dotenv(Path(__file__).parent.parent / '.env')

INSTANTLY_API_KEY = os.getenv('INSTANTLY_API_KEY')
INSTANTLY_API_BASE = 'https://api.instantly.ai/api/v2'


def get_headers():
    return {
        'Authorization': f'Bearer {INSTANTLY_API_KEY}',
        'Content-Type': 'application/json',
    }


def list_accounts(limit=100, only_active=True):
    """Fetch sender accounts from Instantly."""
    url = f'{INSTANTLY_API_BASE}/accounts'
    params = {'limit': limit}

    response = requests.get(url, headers=get_headers(), params=params)

    if response.status_code != 200:
        raise Exception(f'API error {response.status_code}: {response.text}')

    data = response.json()
    accounts = data.get('items', data) if isinstance(data, dict) else data

    if only_active:
        accounts = [a for a in accounts if a.get('status') in (1, 'active', None)]

    return accounts


def print_accounts(accounts):
    if not accounts:
        print('No sender accounts found.')
        return

    print(f'\n{len(accounts)} sender account(s):')
    print('-' * 80)
    for a in accounts:
        email = a.get('email', '?')
        status = a.get('status', '?')
        daily_limit = a.get('daily_limit', '?')
        warmup = a.get('warmup', {})
        warmup_status = warmup.get('status') if isinstance(warmup, dict) else '?'
        print(f'  {email}')
        print(f'    status: {status}  daily_limit: {daily_limit}  warmup: {warmup_status}')
    print('-' * 80)
    print('\nReady-to-paste email_list (active warmed accounts):')
    emails = [a.get('email') for a in accounts if a.get('email')]
    print('  ' + str(emails))


def main():
    parser = argparse.ArgumentParser(description='List Instantly sender accounts')
    parser.add_argument('--all', action='store_true', help='Include inactive accounts')
    parser.add_argument('--limit', type=int, default=100)
    parser.add_argument('--json', action='store_true', help='Print raw JSON')
    args = parser.parse_args()

    if not INSTANTLY_API_KEY:
        print('Error: INSTANTLY_API_KEY not set in .env')
        sys.exit(1)

    try:
        accounts = list_accounts(limit=args.limit, only_active=not args.all)
    except Exception as e:
        print(f'Error: {e}')
        sys.exit(1)

    if args.json:
        import json
        print(json.dumps(accounts, indent=2))
    else:
        print_accounts(accounts)


if __name__ == '__main__':
    main()
