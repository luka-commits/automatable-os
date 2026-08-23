#!/usr/bin/env python3
"""
Check for new lead responses and categorize them.

Fetches unread emails from Instantly, categorizes based on content,
and optionally sends Slack notifications.

See: directives/opportunity_management.md
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime

import requests
from dotenv import load_dotenv


# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

INSTANTLY_API_KEY = os.getenv('INSTANTLY_API_KEY')
INSTANTLY_API_BASE = 'https://api.instantly.ai/api/v2'
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')


def get_headers():
    """Return API headers with authentication."""
    return {
        'Authorization': f'Bearer {INSTANTLY_API_KEY}',
        'Content-Type': 'application/json'
    }


def load_config():
    """Load Loom videos and category signals config."""
    config_path = Path(__file__).parent / 'loom_videos.json'
    with open(config_path, 'r') as f:
        return json.load(f)


def get_unread_emails(limit=100):
    """
    Fetch unread received emails from Instantly.

    Returns:
        List of email objects
    """
    url = f'{INSTANTLY_API_BASE}/emails'
    params = {
        'is_unread': True,
        'email_type': 'received',
        'limit': limit
    }

    response = requests.get(url, headers=get_headers(), params=params)

    if response.status_code != 200:
        raise Exception(f'API error {response.status_code}: {response.text}')

    data = response.json()
    return data.get('items', [])


def get_email_details(email_id):
    """Fetch full email content by ID."""
    url = f'{INSTANTLY_API_BASE}/emails/{email_id}'
    response = requests.get(url, headers=get_headers())

    if response.status_code != 200:
        raise Exception(f'API error {response.status_code}: {response.text}')

    return response.json()


def get_lead_details(lead_id):
    """Fetch lead details by ID."""
    url = f'{INSTANTLY_API_BASE}/leads/{lead_id}'
    response = requests.get(url, headers=get_headers())

    if response.status_code != 200:
        return None  # Lead may not exist

    return response.json()


def categorize_response(text, config):
    """
    Categorize email response based on content.

    Args:
        text: Email body text
        config: Config with category_signals

    Returns:
        Tuple of (category, suggested_video, confidence)
    """
    text_lower = text.lower()
    signals = config.get('category_signals', {})
    videos = config.get('videos', {})

    # Check each category's signals
    scores = {}

    for category, keywords in signals.items():
        score = 0
        for keyword in keywords:
            if keyword.lower() in text_lower:
                score += 1
        if score > 0:
            scores[category] = score

    # Determine primary category
    if not scores:
        return ('unknown', None, 'low')

    primary = max(scores, key=scores.get)
    confidence = 'high' if scores[primary] >= 2 else 'medium'

    # Map category to suggested Loom video
    video_mapping = {
        'positive': 'demo_full',
        'pricing': 'pricing',
        'question': 'how_it_works',
        'negative': None,
        'ooo': None,
        'referral': None,
        'confused': None
    }

    # Check for specific video triggers
    suggested_video = video_mapping.get(primary)

    # Override with more specific video if triggers match
    for video_id, video_config in videos.items():
        triggers = video_config.get('triggers', [])
        for trigger in triggers:
            if trigger.lower() in text_lower:
                suggested_video = video_id
                break

    return (primary, suggested_video, confidence)


def get_category_emoji(category):
    """Get emoji for category."""
    emojis = {
        'positive': '🟢',
        'pricing': '🟡',
        'question': '🟡',
        'negative': '🔴',
        'ooo': '⚪',
        'referral': '🟠',
        'confused': '🔵',
        'unknown': '❓'
    }
    return emojis.get(category, '❓')


def format_slack_message(response_data):
    """Format response data for Slack notification."""
    category = response_data['category']
    emoji = get_category_emoji(category)

    # Truncate message if too long
    message = response_data['message']
    if len(message) > 300:
        message = message[:300] + '...'

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} NEW LEAD RESPONSE",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Category:* {emoji} {category.upper()}"},
                {"type": "mrkdwn", "text": f"*Confidence:* {response_data['confidence']}"},
                {"type": "mrkdwn", "text": f"*Lead:* {response_data.get('lead_name', 'Unknown')}"},
                {"type": "mrkdwn", "text": f"*Email:* {response_data.get('lead_email', 'Unknown')}"},
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Their message:*\n```{message}```"
            }
        }
    ]

    # Add suggested action
    if response_data.get('suggested_video'):
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Suggested action:* Send `{response_data['suggested_video']}` Loom video"
            }
        })
    elif category == 'negative':
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Suggested action:* No response needed (mark as not interested)"
            }
        })
    elif category == 'ooo':
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Suggested action:* Wait for their return, follow up later"
            }
        })

    # Add divider and metadata
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": f"Campaign: {response_data.get('campaign_name', 'Unknown')} | Thread: {response_data.get('thread_id', 'N/A')}"}
        ]
    })

    return {"blocks": blocks}


def send_slack_notification(response_data):
    """Send notification to Slack webhook."""
    if not SLACK_WEBHOOK_URL:
        print('  [WARN] SLACK_WEBHOOK_URL not configured, skipping notification')
        return False

    payload = format_slack_message(response_data)

    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        return response.status_code == 200
    except Exception as e:
        print(f'  [ERROR] Slack notification failed: {e}')
        return False


def extract_text_from_body(body):
    """Extract plain text from email body (HTML or plain)."""
    if isinstance(body, dict):
        # Prefer plain text, fall back to HTML
        text = body.get('text') or body.get('html', '')
    else:
        text = str(body)

    # Strip HTML tags if present
    text = re.sub(r'<[^>]+>', ' ', text)
    # Normalize whitespace
    text = ' '.join(text.split())

    return text


def process_responses(emails, config, notify_slack=True, verbose=False):
    """
    Process a list of emails and categorize them.

    Args:
        emails: List of email objects from API
        config: Loom videos config
        notify_slack: Whether to send Slack notifications
        verbose: Print detailed output

    Returns:
        List of processed response dictionaries
    """
    results = []

    for email in emails:
        if verbose:
            print(f'\nProcessing email: {email.get("id")}')

        # Get full email content if needed
        email_id = email.get('id')

        # Extract text from body
        body = email.get('body', {})
        text = extract_text_from_body(body)

        if not text:
            if verbose:
                print('  [SKIP] Empty message body')
            continue

        # Categorize
        category, suggested_video, confidence = categorize_response(text, config)

        # Build response data
        response_data = {
            'email_id': email_id,
            'thread_id': email.get('thread_id'),
            'lead_id': email.get('lead_id'),
            'lead_email': email.get('from_address') or email.get('lead'),
            'lead_name': email.get('from_name', 'Unknown'),
            'campaign_id': email.get('campaign_id'),
            'campaign_name': email.get('campaign_name', 'Unknown'),
            'message': text,
            'category': category,
            'suggested_video': suggested_video,
            'confidence': confidence,
            'timestamp': email.get('timestamp') or datetime.now().isoformat()
        }

        if verbose:
            emoji = get_category_emoji(category)
            print(f'  Category: {emoji} {category.upper()} (confidence: {confidence})')
            print(f'  Suggested video: {suggested_video or "None"}')
            print(f'  Message preview: {text[:100]}...' if len(text) > 100 else f'  Message: {text}')

        # Send Slack notification
        if notify_slack:
            success = send_slack_notification(response_data)
            if verbose:
                print(f'  Slack notification: {"sent" if success else "failed"}')

        results.append(response_data)

    return results


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Check for new lead responses and categorize them',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Check for new responses (default)
  python check_responses.py

  # Check without sending Slack notifications
  python check_responses.py --no-slack

  # Verbose output
  python check_responses.py -v

  # Check specific campaign only
  python check_responses.py --campaign-id abc123
        '''
    )

    parser.add_argument(
        '--campaign-id',
        help='Only check responses for this campaign'
    )
    parser.add_argument(
        '--no-slack',
        action='store_true',
        help='Skip Slack notifications'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Max emails to fetch (default: 100)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )

    args = parser.parse_args()

    # Check API key
    if not INSTANTLY_API_KEY:
        print('Error: INSTANTLY_API_KEY not found in .env')
        sys.exit(1)

    # Load config
    try:
        config = load_config()
    except Exception as e:
        print(f'Error loading config: {e}')
        sys.exit(1)

    # Fetch unread emails
    print('Fetching unread responses...')
    try:
        emails = get_unread_emails(limit=args.limit)
    except Exception as e:
        print(f'Error fetching emails: {e}')
        sys.exit(1)

    # Filter by campaign if specified
    if args.campaign_id:
        emails = [e for e in emails if e.get('campaign_id') == args.campaign_id]

    if not emails:
        print('No new responses found.')
        return

    print(f'Found {len(emails)} unread response(s)')

    # Process responses
    results = process_responses(
        emails,
        config,
        notify_slack=not args.no_slack,
        verbose=args.verbose
    )

    # Output results
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print('\n' + '=' * 60)
        print('SUMMARY')
        print('=' * 60)

        # Group by category
        categories = {}
        for r in results:
            cat = r['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r)

        for cat, items in sorted(categories.items()):
            emoji = get_category_emoji(cat)
            print(f'\n{emoji} {cat.upper()}: {len(items)}')
            for item in items:
                video_hint = f" → {item['suggested_video']}" if item['suggested_video'] else ""
                print(f"   • {item['lead_email']}{video_hint}")

        print('\n' + '=' * 60)
        if not args.no_slack and SLACK_WEBHOOK_URL:
            print('Slack notifications sent.')
        elif not SLACK_WEBHOOK_URL:
            print('Note: Add SLACK_WEBHOOK_URL to .env for notifications.')


if __name__ == '__main__':
    main()
