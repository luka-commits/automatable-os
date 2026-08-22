#!/usr/bin/env bash
# Runs a Python hook with whichever interpreter this machine actually has.
#
# Why: the hooks used to call `python3` directly. On macOS and Linux that is
# right, but a Windows install commonly ships `python` and no `python3` at all,
# so every session start produced a failing hook and nobody could tell why from
# the message. A hook that cannot run is worse than no hook: it looks like the
# system is broken when only the interpreter name is.
#
#   bash .claude/hooks/run-python.sh <script.py> [args...]
#
# Exit codes pass through unchanged, which matters because a PreToolUse hook
# uses exit code 2 to block. If no interpreter is found at all, this exits 0
# rather than failing the session: a missing Python means the checks cannot
# run, not that the user did something wrong.
set -u

script="${1:-}"
[ -n "$script" ] || { echo "run-python.sh: no script given" >&2; exit 0; }
shift

for candidate in python3 python py; do
  if command -v "$candidate" >/dev/null 2>&1; then
    # `py` on Windows needs -3 to pick Python 3 rather than a stray Python 2.
    if [ "$candidate" = "py" ]; then
      exec py -3 "$script" "$@"
    fi
    exec "$candidate" "$script" "$@"
  fi
done

echo "run-python.sh: no Python interpreter found (looked for python3, python, py)." >&2
echo "The workspace runs without it; the dashboard render and the setup checks need it." >&2
exit 0
