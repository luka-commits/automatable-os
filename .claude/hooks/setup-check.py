#!/usr/bin/env python3
"""At the start of every session: is this workspace actually finished?

Why a hook and not a rule: a rule needs someone to follow it. Measured in a real
workspace, the morning routine that contains the same self-test ran six times in
ninety days. What should happen at the start has to happen at the start.

This hook speaks up ONLY when something is missing, and then one line per item,
in plain language with the next step. When everything is there it stays silent —
otherwise it gets skimmed past after three days.

It checks only what fails silently and costs something:

    setup never ran            the folder is an unused copy
    setup ran, Upwork did not  the acquisition half is inert
    no backup                  the disk dies and everything is gone
    no mail, no calendar       the briefing stays a task list
    a key is missing           a tool is installed and can do nothing

All of those fail without a sound. A missing feature announces itself; one that
was never set up does not.
"""
import json
import os
import pathlib
import subprocess
import sys

W = pathlib.Path(os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd())


def config_text():
    try:
        return (W / 'context/config.yaml').read_text(encoding='utf-8')
    except OSError:
        return ''


def has_remote():
    try:
        r = subprocess.run(['git', '-C', str(W), 'remote'],
                           capture_output=True, text=True, timeout=5)
        return bool(r.stdout.strip())
    except Exception:
        return False


def check():
    """A list of (what is missing, what it costs, the next step).

    Whether setup ran at all is already answered by check-setup.sh on the same
    event, with the more reliable marker: the setup skill archives itself away
    at the end, so as long as its folder is there, it has not run. While that
    holds, this hook stays quiet — two voices on one topic and the user stops
    hearing the second.
    """
    if (W / '.claude/skills/setup').is_dir():
        return []

    cfg = config_text()
    if not cfg or '[YOUR NAME]' in cfg:
        return []                     # check-setup.sh has the floor

    open_items = []

    # The handover that used to be missing. `setup` archives itself and nothing
    # pointed at the Upwork half afterwards, so the acquisition side sat there
    # fully built and never started. Skipped entirely when the user said they do
    # not work on Upwork: optional means optional.
    if 'upwork_enabled: false' not in cfg and not (W / 'context/expertise.md').is_file():
        open_items.append((
            'Upwork is not set up yet',
            'the screener, the proposals and the pitch pages all read '
            'context/expertise.md and none of them can run without it',
            'say "set up automatable os"'))

    if not has_remote():
        open_items.append(('No backup repo',
                           'if the disk dies, your work is gone',
                           'say "set up my backup"'))

    # A mail slot counts as filled as soon as any route exists — connector OR
    # CLI. That is why this looks for the text, not for a structure.
    if 'slot: mail' not in cfg and 'gws' not in cfg:
        open_items.append(('No route to your mailbox',
                           'the briefing stays a task list instead of your day',
                           'say "connect my mailbox"'))
    if 'slot: calendar' not in cfg:
        open_items.append(('No calendar connected',
                           'your appointments never show up in the briefing',
                           'say "connect my calendar"'))

    # A key the tooling claims but that does not exist: the tool is there and
    # can do nothing, and nobody notices.
    keys = pathlib.Path.home() / '.config/credentials.env'
    txt = keys.read_text(encoding='utf-8', errors='ignore') if keys.is_file() else ''
    for name, purpose in (('FIRECRAWL_API_KEY', 'reading web pages'),
                          ('OPENROUTER_API_KEY', 'images and specialist models')):
        if name in cfg and name not in txt:
            open_items.append((f'The key for {purpose} is missing',
                               'the tool is set up and can do nothing',
                               f'say "add my {name.split("_")[0].title()} key"'))
    return open_items


def main():
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    try:
        open_items = check()
    except Exception:
        return 0                      # a hint never blocks a session

    if not open_items:
        return 0                      # fully set up: stay quiet

    lines = '\n'.join(f'- **{what}** — {cost}. {step}' for what, cost, step in open_items)
    text = (
        f'Checked at startup: {len(open_items)} thing(s) are still missing in this '
        f'workspace.\n{lines}\n'
        'Tell the user ONCE, in your own words, at most two sentences, after your actual '
        'answer and never before it. Not a second time in this session, and no pushing: '
        'they decide whether and when.'
    )
    print(json.dumps({'hookSpecificOutput': {
        'hookEventName': 'SessionStart',
        'additionalContext': text,
    }}))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
