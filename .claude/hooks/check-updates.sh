#!/usr/bin/env bash
# On session start: if the source package (upstream) has a newer version than
# this workspace, tell Claude to offer the update. The whole update procedure
# already lives in VERSION.md § "The update route" — this hook is only the
# trigger, so nobody has to remember to ask.
#
# Why a hook and not an instruction: the same reason check-setup.sh is a hook.
# An instruction in CLAUDE.md fires unreliably; a hook always runs. The point of
# this feature is that everyone who installed the system stays current without
# having to think about it.
#
# It stays quiet unless there is genuinely a newer version, fails open on any
# error (offline, no upstream, restricted git), and checks at most once a day so
# a session start never waits on the network twice.
set -u
DIR="${CLAUDE_PROJECT_DIR:-.}"
cd "$DIR" 2>/dev/null || exit 0

# Not set up yet? The workspace is not the user's own until setup archives
# itself away — do not nag about updates before it even belongs to them.
[ -d "$DIR/.claude/skills/setup" ] && exit 0

# Need the source remote. No upstream → nothing to compare against; the daily
# self-test still catches "add the source first", so stay silent here.
git remote get-url upstream >/dev/null 2>&1 || exit 0

# At most one check per day.
STAMP="$DIR/.claude/.last-update-check"
TODAY="$(date +%Y-%m-%d 2>/dev/null)" || exit 0
if [ -f "$STAMP" ] && [ "$(cat "$STAMP" 2>/dev/null)" = "$TODAY" ]; then exit 0; fi

# Fetch tags, but never hang a session on a slow network.
timeout 8 git fetch upstream --tags --quiet 2>/dev/null || exit 0
echo "$TODAY" > "$STAMP" 2>/dev/null || true

LATEST="$(git tag -l --sort=-v:refname 2>/dev/null | head -1)"
[ -z "$LATEST" ] && exit 0

# Current version = the first bold version token in VERSION.md, e.g. **v1.8-open**
CURRENT="$(grep -m1 -oE '\*\*v[0-9]+\.[0-9]+[^*]*\*\*' VERSION.md 2>/dev/null | tr -d '*')"
[ -z "$CURRENT" ] && exit 0
[ "$LATEST" = "$CURRENT" ] && exit 0

# Only speak up if LATEST is actually newer (version sort). If CURRENT sorts
# last, they are already ahead of or equal to the newest tag — stay silent.
NEWER="$(printf '%s\n%s\n' "$CURRENT" "$LATEST" | sort -V 2>/dev/null | tail -1)"
[ "$NEWER" = "$CURRENT" ] && exit 0

MSG="A newer version of this workspace exists: ${LATEST} (this workspace is on ${CURRENT}). On the user's first message, tell them in one short, friendly sentence that an update is available and offer to fetch it. If they say yes, follow the update route in VERSION.md exactly (it commits their work first, their four folders always win on conflict, and it proves the result with a self-test). Give the one-line summary of what is new from VERSION.md § Changes. Mention this once; if they decline, do not bring it up again."
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$MSG"
exit 0
