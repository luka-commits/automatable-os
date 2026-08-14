#!/usr/bin/env python3
"""PreToolUse-Hook: faengt das In-Place-Editieren von Dateien per python3-Heredoc ab.

Warum es diesen Hook gibt: die haeufigste Fehlerquelle in diesem Workspace war ein
`python3 - <<EOF` mit `read_text()` + `re.sub()` + `write_text()`. Trifft das re.sub
nichts, ist es ein STILLER No-op: das Skript meldet Erfolg, die Datei ist unveraendert,
niemand merkt es. Das Edit-Tool schlaegt in genau diesem Fall fehl. Gemessen am 23.07.:
dieser Handgriff kam 134-mal vor (die drei haeufigsten Muster im Audit).

Was blockiert wird: ein python-Aufruf, der eine Datei liest UND zurueckschreibt
(read-modify-write) — die Edit-in-place-Signatur.
Was durchgeht:
  - `assert` im Body → die bewusste Massen-Ersetzung mit Treffer-Garantie (CLAUDE.md-Ausnahme)
  - nur lesen, oder nur eine NEUE Datei schreiben (kein In-Place-Edit)
  - alles, was kein python ist

ponytail: bewusst eine schmale Heuristik auf dem Kommando-String, kein Python-Parser.
Faelle, die durchrutschen, faengt weiterhin die Regel im Kopf; Faelle, die zu Unrecht
blocken, loest `assert` oder der Weg ueber ein Skript in reference/scripts/.
"""
import json
import re
import sys


def is_inplace_python_edit(cmd: str) -> bool:
    if not re.search(r'\bpython3?\b', cmd):
        return False
    # Nur Heredoc oder -c; ein `python3 script.py` ist ein Skript, kein Inline-Edit.
    if '<<' not in cmd and ' -c' not in cmd:
        return False
    # Die bewusste, abgesicherte Massen-Ersetzung ist erlaubt (CLAUDE.md-Ausnahme).
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
