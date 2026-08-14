#!/usr/bin/env bash
# Reports at session start if the setup is still pending.
#
# Why this hook exists: the instruction in CLAUDE.md alone is not reliable — in
# tests on 2026-07-21 the setup sometimes fired on "hello" and sometimes did not,
# with an identical state. For a new user that is the worst case: they type
# "hello", get a normal chat, and think the system is broken. A hook, by
# contrast, always runs.
#
# The marker is the setup folder itself: the skill archives itself away at the
# end, so its presence reliably means "not done yet".
set -u
DIR="${CLAUDE_PROJECT_DIR:-.}"

if [ -d "$DIR/.claude/skills/setup" ]; then
  MSG="SETUP IS STILL PENDING. This workspace does not belong to anyone yet: the folder .claude/skills/setup/ is still there, and the skill archives itself away at the end. Greet the user on their first message in at most two sentences (what this is) and then IMMEDIATELY start the skill 'setup' via the skill tool. Do not wait for a command, do not ask whether they want to, and do not improvise a setup."
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$MSG"
fi
exit 0
