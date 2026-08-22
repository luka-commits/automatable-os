#!/usr/bin/env python3
"""PreToolUse hook: catches in-place file edits made through a python3 heredoc.

Why this hook exists: the most common source of errors in this workspace was a
`python3 - <<EOF` with `read_text()` + `re.sub()` + `write_text()`. If the re.sub
matches nothing, it is a SILENT no-op: the script reports success, the file is
unchanged, and nobody notices. The Edit tool fails loudly in exactly that case.
Measured on 23 July: this move showed up 134 times (the three most frequent
patterns in the audit).

What gets blocked: a python call that reads a file AND writes it back
(read-modify-write), which is the edit-in-place signature.
What passes:
  - `assert` in the body, the deliberate mass replacement with a guaranteed hit count
  - reading only, or writing a NEW file only (no in-place edit)
  - anything that is not python

Deliberately a narrow heuristic on the command string rather than a python parser.
Cases that slip through are still caught by the rule in CLAUDE.md; cases that block
wrongly are solved by `assert` or by going through a script in reference/scripts/.
"""
import json
import re
import sys


def is_inplace_python_edit(cmd: str) -> bool:
    if not re.search(r'\bpython3?\b', cmd):
        return False
    # Heredoc or -c only; a `python3 script.py` is a script, not an inline edit.
    if '<<' not in cmd and ' -c' not in cmd:
        return False
    # The deliberate, guarded mass replacement is allowed (the CLAUDE.md exception).
    if 'assert' in cmd:
        return False
    reads = bool(re.search(r'read_text\(|\.read\(|open\([^)]*[\'"]r', cmd))
    writes = bool(re.search(r'write_text\(|re\.sub\(|\.sub\(|open\([^)]*[\'"]w', cmd))
    return reads and writes


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # nothing usable on stdin: do not get in the way
    if data.get('tool_name') != 'Bash':
        return 0
    cmd = (data.get('tool_input') or {}).get('command', '')
    if is_inplace_python_edit(cmd):
        sys.stderr.write(
            "Blocked: editing a file through a python3 heredoc (read + write in one call).\n"
            "A re.sub that matches nothing is a silent no-op. Use the Edit tool instead,\n"
            "which fails loudly in exactly that case. For a genuine mass replacement:\n"
            "a script in reference/scripts/ with `assert n == expected`.\n")
        return 2  # 2 = block; stderr goes to Claude
    return 0


def demo() -> None:
    """Self-check:  python3 .claude/hooks/no-heredoc-edit.py --demo"""
    block = "cd ~/dev && python3 - <<PY\np=Path('x'); t=p.read_text(); p.write_text(t.replace('a','b'))\nPY"
    ok_assert = "python3 - <<PY\nt=p.read_text(); t=re.sub('a','b',t); assert n==3; p.write_text(t)\nPY"
    ok_read = "python3 -c \"print(open('x').read())\""
    ok_script = "python3 reference/scripts/render_dashboard.py --fast"
    ok_newfile = "python3 - <<PY\nopen('new.txt','w').write('hello')\nPY"
    assert is_inplace_python_edit(block), "read+write has to block"
    assert not is_inplace_python_edit(ok_assert), "assert is the exception"
    assert not is_inplace_python_edit(ok_read), "reading only is fine"
    assert not is_inplace_python_edit(ok_script), "calling a script is fine"
    assert not is_inplace_python_edit(ok_newfile), "writing a new file only is fine"
    print("demo ok: 5 cases correct")


if __name__ == '__main__':
    if '--demo' in sys.argv:
        demo()
    else:
        sys.exit(main())
