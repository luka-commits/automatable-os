#!/usr/bin/env python3
"""
Import leads from CSV to Instantly campaign.

Reads enriched contact data and bulk imports to an Instantly campaign
with proper field mapping for personalization variables.
"""

import argparse
import csv
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

INSTANTLY_API_KEY = os.getenv('INSTANTLY_API_KEY')
INSTANTLY_API_BASE = 'https://api.instantly.ai/api/v2'
BATCH_SIZE = 1000  # Instantly API limit


def get_headers():
    """Return API headers with authentication."""
    return {
        'Authorization': f'Bearer {INSTANTLY_API_KEY}',
        'Content-Type': 'application/json'
    }


# CSV columns mapped to Instantly's built-in lead fields. Anything not in here
# is passed through as a custom variable (so {{Icebreaker}}, {{header}}, etc.
# work in Instantly templates without code changes).
BUILTIN_FIELD_MAP = {
    'email': 'email',
    'first_name': 'first_name',
    'last_name': 'last_name',
    'business_name': 'company_name',
    'company_name': 'company_name',
    'website': 'website',
    'company_website': 'website',
    'phone': 'phone',
}


def read_csv(file_path):
    """
    Read CSV file and return list of lead dictionaries.

    Maps known columns to Instantly built-in lead fields and passes every
    other non-empty column through as a custom variable. Backward compatible
    with the legacy 8-column lead-cleaner output (header, business_name, city,
    state, website, email, first_name, greeting) and forward compatible with
    any new personalization columns (Icebreaker, custom_intro, etc.) added
    upstream.

    Args:
        file_path: Path to CSV file

    Returns:
        List of dictionaries, one per lead
    """
    leads = []

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            lead = {'custom_variables': {}}

            for col, raw in row.items():
                if col is None:
                    continue
                value = (raw or '').strip()
                if not value:
                    continue
                key = col.strip()
                builtin = BUILTIN_FIELD_MAP.get(key.lower())
                if builtin:
                    # Don't overwrite a builtin already filled (e.g.
                    # business_name vs company_name → first wins)
                    lead.setdefault(builtin, value)
                else:
                    lead['custom_variables'][key] = value

            if lead.get('email'):
                leads.append(lead)

    return leads


def import_leads_batch(campaign_id, leads, skip_duplicates=True):
    """
    Import a batch of leads to a campaign — single-POST per lead.

    Instantly v2 /api/v2/leads expects a single lead per POST (NOT a leads array
    in the payload). Empirically tested 2026-05-16: array-payload returns 400
    "Email is required when creating a lead". This function loops single-POSTs
    and aggregates the result so the upstream import_leads() flow doesn't need
    to change.

    Args:
        campaign_id: Instantly campaign UUID
        leads: List of lead dictionaries (any size — loop is per-lead)
        skip_duplicates: Skip if lead already in campaign

    Returns:
        {"uploaded": N, "skipped": M, "errors": [...]} aggregate response

    Raises:
        Exception if ALL leads in batch fail (transient API outage). Per-lead
        failures are collected, not raised — preserves partial success.
    """
    url = f'{INSTANTLY_API_BASE}/leads'
    uploaded = 0
    skipped = 0
    errors = []

    for lead in leads:
        if not lead.get('email'):
            errors.append({'lead': lead.get('company_name', '?'), 'error': 'missing email'})
            continue

        payload = {
            'campaign_id': campaign_id,
            'skip_if_in_campaign': skip_duplicates,
            **lead,  # flatten lead fields (email, first_name, company_name, custom_variables, ...)
        }

        try:
            response = requests.post(url, headers=get_headers(), json=payload, timeout=30)
            if response.status_code in (200, 201):
                uploaded += 1
            elif response.status_code == 409 or 'already' in response.text.lower():
                skipped += 1
            else:
                errors.append({
                    'lead': lead.get('email', '?'),
                    'error': f'API {response.status_code}: {response.text[:150]}'
                })
        except Exception as e:
            errors.append({'lead': lead.get('email', '?'), 'error': str(e)[:150]})

    if uploaded == 0 and errors and len(errors) == len(leads):
        # All-fail = likely auth/network outage. Raise to upstream caller.
        raise Exception(f'All {len(leads)} leads failed: {errors[0]["error"]}')

    return {'uploaded': uploaded, 'skipped': skipped, 'errors': errors}


def import_leads(campaign_id, leads, skip_duplicates=True):
    """
    Import all leads to campaign in batches.

    Args:
        campaign_id: Instantly campaign UUID
        leads: List of lead dictionaries
        skip_duplicates: Skip if lead already in campaign

    Returns:
        Dictionary with import statistics
    """
    total = len(leads)
    imported = 0
    skipped = 0
    errors = []

    print(f'\nImporting {total} leads to campaign {campaign_id}')
    print(f'Batch size: {BATCH_SIZE}')
    print(f'Skip duplicates: {skip_duplicates}')
    print('-' * 50)

    # Process in batches
    for i in range(0, total, BATCH_SIZE):
        batch = leads[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

        print(f'\nBatch {batch_num}/{total_batches}: {len(batch)} leads')

        try:
            result = import_leads_batch(campaign_id, batch, skip_duplicates)

            # Parse response
            batch_imported = result.get('uploaded', len(batch))
            batch_skipped = result.get('skipped', 0)

            imported += batch_imported
            skipped += batch_skipped

            print(f'  Imported: {batch_imported}, Skipped: {batch_skipped}')

        except Exception as e:
            error_msg = f'Batch {batch_num} failed: {str(e)}'
            errors.append(error_msg)
            print(f'  ERROR: {error_msg}')

        # Rate limiting - small delay between batches
        if i + BATCH_SIZE < total:
            time.sleep(1)

    print('-' * 50)
    print(f'\nImport complete!')
    print(f'  Total leads: {total}')
    print(f'  Imported: {imported}')
    print(f'  Skipped: {skipped}')
    print(f'  Errors: {len(errors)}')

    return {
        'total': total,
        'imported': imported,
        'skipped': skipped,
        'errors': errors
    }


def list_campaigns():
    """List available campaigns for reference."""
    url = f'{INSTANTLY_API_BASE}/campaigns'
    response = requests.get(url, headers=get_headers())

    if response.status_code != 200:
        raise Exception(f'API error {response.status_code}: {response.text}')

    data = response.json()
    campaigns = data.get('items', [])

    print('\nAvailable campaigns:')
    print('-' * 70)
    for c in campaigns:
        status_map = {0: 'Draft', 1: 'Active', 2: 'Paused', 3: 'Completed'}
        status = status_map.get(c.get('status'), 'Unknown')
        print(f"  {c['id']}")
        print(f"    Name: {c['name']}")
        print(f"    Status: {status}")
        print()

    return campaigns


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Import leads from CSV to Instantly campaign',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # List available campaigns
  python import_to_instantly.py --list-campaigns

  # Import leads to a campaign
  python import_to_instantly.py --campaign-id abc123-def456

  # Import from custom CSV file
  python import_to_instantly.py --campaign-id abc123 --input custom.csv

  # Allow duplicates (import even if already in campaign)
  python import_to_instantly.py --campaign-id abc123 --allow-duplicates
        '''
    )

    parser.add_argument(
        '--campaign-id',
        help='Instantly campaign UUID to import leads into'
    )
    parser.add_argument(
        '--input', '-i',
        default='.tmp/contacts_with_greetings.csv',
        help='Path to CSV file (default: .tmp/contacts_with_greetings.csv)'
    )
    parser.add_argument(
        '--list-campaigns',
        action='store_true',
        help='List available campaigns and exit'
    )
    parser.add_argument(
        '--allow-duplicates',
        action='store_true',
        help='Import leads even if already in campaign'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Read CSV and show what would be imported without actually importing'
    )

    args = parser.parse_args()

    # Check API key
    if not INSTANTLY_API_KEY:
        print('Error: INSTANTLY_API_KEY not found in .env')
        print('Add your API key to .env file')
        sys.exit(1)

    # List campaigns mode
    if args.list_campaigns:
        try:
            list_campaigns()
        except Exception as e:
            print(f'Error listing campaigns: {e}')
            sys.exit(1)
        return

    # Import mode - require campaign ID
    if not args.campaign_id:
        print('Error: --campaign-id required for import')
        print('Use --list-campaigns to see available campaigns')
        sys.exit(1)

    # Resolve input file path
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = Path(__file__).parent.parent / args.input

    if not input_path.exists():
        print(f'Error: Input file not found: {input_path}')
        sys.exit(1)

    # Read CSV
    print(f'Reading CSV: {input_path}')
    leads = read_csv(input_path)
    print(f'Found {len(leads)} leads')

    if len(leads) == 0:
        print('No leads to import')
        return

    # Show sample
    print('\nSample lead (first row):')
    sample = leads[0]
    print(f'  Email: {sample["email"]}')
    print(f'  First name: {sample.get("first_name")}')
    print(f'  Company: {sample.get("company_name")}')
    print(f'  Custom variables: {sample.get("custom_variables")}')

    # Dry run mode
    if args.dry_run:
        print('\n[DRY RUN] Would import above leads. No changes made.')
        return

    # Confirm before import
    print(f'\nReady to import {len(leads)} leads to campaign {args.campaign_id}')
    response = input('Continue? [y/N] ')

    if response.lower() != 'y':
        print('Aborted')
        return

    # Import
    try:
        result = import_leads(
            args.campaign_id,
            leads,
            skip_duplicates=not args.allow_duplicates
        )

        if result['errors']:
            print('\nErrors occurred:')
            for error in result['errors']:
                print(f'  - {error}')
            sys.exit(1)

    except Exception as e:
        print(f'\nImport failed: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
