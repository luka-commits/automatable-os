#!/usr/bin/env python3
"""Does this repo work for someone who just cloned it?

Written after a real clone test found three breaks that reading the files had
missed: two documents existed on disk and in no commit, a skill called a script
subcommand that did not exist, and a step referenced a path from a different
machine. All three would have surfaced on a stranger's first run, which is the
worst possible moment.

Everything here is mechanical. It checks what can be checked without judgement:

    1. Every file path a skill mentions exists
    2. Every `python3 reference/scripts/X.py <cmd>` resolves to a real subcommand
    3. Every `.example` has a gitignored counterpart, and vice versa
    4. No personal data survived: names, ids, keys, machine-specific paths
    5. Every skill has a name and a description in its frontmatter
    6. Every {{PLACEHOLDER}} in a template is filled by its renderer
    7. Nothing shipped here still speaks German, unless it does so on purpose

Exit 1 on any finding, so it can gate a release rather than be read politely.

    python3 reference/scripts/check_repo.py [--quiet]
"""
import pathlib
import re
import subprocess
import sys

W = pathlib.Path(__file__).resolve().parents[2]
SKILLS = W / '.claude/skills'

# Traces of the machine this was extracted from. A hit here means the separation
# missed something, and the repo is public.
LEAKS = [
    (r'\bLuka\b|\bKnieling\b', 'a personal name'),
    (r'flouence\.com', 'a personal domain'),
    (r'\bU0[A-Z0-9]{8,}\b', 'a Slack user id'),
    (r'\b1898663420131815612\b', 'a specific Upwork org id'),
    (r'projects/personal/', 'a path from another workspace'),
    (r'/Users/[a-z]+/', 'an absolute home directory'),
]

# Not a leak: a placeholder is meant to look like one.
LEAK_EXEMPT = re.compile(r'\[YOUR|your\.name@|example\.com|<your')

# Files that legitimately contain what the leak patterns look for: this checker
# defines them, and local tool caches are not shipped.
LEAK_SKIP = ('reference/scripts/check_repo.py', '.impeccable/')

# Paths a skill may reference that do not exist until something creates them.
# A missing runtime file is the normal state of a fresh clone, not a defect —
# flagging it would train the reader to ignore this checker, which is worse
# than not having one.
RUNTIME = (
    'context/BRIEFING.md', 'context/EMAIL_STYLE.md', 'context/today.html',
    'context/.mail_cache.json', 'context/.fragments.json', 'context/.adopt-manifest.json',
    'context/.routinen_log.json', 'context/archive/', 'context/tool-knowledge/',
    'context/audit.json', 'context/profile.md',
    '.claude/skills-deprecated/', 'jobs/',
)


def files(*globs):
    """Everything that would actually be published.

    Filtered through `git check-ignore`, because the question this whole file
    asks is "what does a stranger receive", not "what is on this disk". A
    generated audit.json full of local paths is correct on the machine that made
    it and never leaves — flagging it would be a false alarm.
    """
    out = []
    for g in globs:
        out += [p for p in W.glob(g)
                if '.git/' not in str(p) and 'node_modules' not in str(p)]
    if not out:
        return out
    rels = [str(p.relative_to(W)) for p in out]
    r = subprocess.run(['git', 'check-ignore', '--stdin'], cwd=W,
                       input='\n'.join(rels), capture_output=True, text=True)
    ignored = set(r.stdout.split('\n'))
    return [p for p, rel in zip(out, rels) if rel not in ignored]


def check_leaks():
    findings = []
    for p in files('**/*.md', '**/*.py', '**/*.js', '**/*.html', '**/*.yaml', '**/*.json'):
        rel = str(p.relative_to(W))
        if p.name == 'today.html' or any(rel.startswith(x) for x in LEAK_SKIP):
            continue
        try:
            txt = p.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        for pattern, what in LEAKS:
            for m in re.finditer(pattern, txt):
                line = txt[:m.start()].count('\n') + 1
                ctx = txt.splitlines()[line - 1][:90] if line <= len(txt.splitlines()) else ''
                if LEAK_EXEMPT.search(ctx):
                    continue
                findings.append(f'{p.relative_to(W)}:{line} carries {what}: {m.group(0)}')
    return findings


# Words that are German and are not also English, plus German-only orthography.
# A quoted string carrying one of these, in a script with no localization table,
# is text a user will read.
#
# Known limit: this catches German *sentences* reliably, because function words
# give them away, but a single-word label ("Kaltstart", "Frische") only if it is
# listed here. The first version of this check passed a file whose every
# dimension label was still German — the defect surfaced by running the script
# and reading its output, not by scanning it. So run the thing too.
GERMAN = re.compile(
    r'[äöüßÄÖÜ]|'
    r'\b(nicht|keine[rnms]?|kein|eine[rnms]?|und|oder|wird|werden|weil|damit|'
    r'sondern|statt|schon|noch|Datei|Ordner|Zeile|Verweis|Wurzel|erledigt|'
    r'fehlt|liegt|gibt|nichts|etwas|dieser|diesem|diesen|deine[rnms]?|selbst|'
    r'Deckung|Kaltstart|Frische|Sicherung|Sicherheit|Erreichbarkeit|'   # not Ballast: English too
    r'Automatisierung|Lebenszyklus|Wissen|Handwerk|Anbindung|Nutzung|Begruendung|'
    r'geschrieben|geprueft|veraltet|unbekannt|Zustand|Befund|de-DE|'
    r'passt|Einstieg|davon|liest|Lauf|Ordners|passiert|bereits|jeder|jede[nrms]?)\b',
    re.IGNORECASE)   # "Nichts" is as German as "nichts"; the first version missed it

# Lines that legitimately carry German in an English repo. Keep this short and
# specific — every entry is a hole in the check, so each one names its reason.
LANG_EXEMPT = re.compile(
    r'\bSöhne\b'                       # a typeface, not a sentence
    r'|\bZustand, Jotai\b'             # the React state library, not the noun
    r'|\*\*Deutsch\*\*'                # the language question, asked in both
    r'|"[^"]*" / "[^"]*"')             # an EN/DE pair of phrases to match on

# Some files ship both languages on purpose and pick between them — a script with
# an en/de table, a skill with parallel English and German sections. Their German
# is a translation, not a leftover. Detected by shape rather than by filename, so
# a newly localized file is exempt automatically and a de-only one never is.
BILINGUAL = re.compile(
    r"""["']?\bde\b["']?\s*:\s*[{(dict]"""   # a lookup table keyed by language
    r"""|^#+\s*German\s*$"""                 # a "### German" section next to English
    r"""|^DE:\s*$""",                        # an EN:/DE: pair of examples
    re.MULTILINE)


def check_language():
    """A skill that prints German in an English repo is broken for its reader.

    Found the hard way: five scripts were copied over from a German package to
    satisfy missing-file findings, and the mechanical checks all passed while
    `audit` and `adopt` would have printed German at their first user.
    """
    findings = []
    targets = sorted((W / 'reference/scripts').glob('*.[jp][sy]'))
    targets += sorted(SKILLS.glob('*/SKILL.md')) + sorted(SKILLS.glob('*/references/*.md'))
    for p in targets:
        if p.name == 'check_repo.py':
            continue
        txt = p.read_text(encoding='utf-8')
        if BILINGUAL.search(txt):
            continue
        name = p.name if p.parent.name == 'scripts' else f'{p.parent.name}/{p.name}'
        hits = first = 0
        for i, line in enumerate(txt.splitlines(), 1):
            # In a script only quoted text reaches a user; in a skill the prose
            # itself is the instruction, so the whole line counts.
            if p.suffix == '.md':
                spans = [line] if not line.lstrip().startswith('#') else []
            else:
                code = line.split('//')[0].split('#')[0]
                spans = [m.group(2) for m in re.finditer(r'''(['"`])(.*?)\1''', code)]
            for span in spans:
                if GERMAN.search(span) and not LANG_EXEMPT.search(span):
                    hits += 1
                    if hits == 1:
                        first = i
                        findings.append(f'{name}:{i} is German: "{span.strip()[:60]}"')
                    break
        if hits > 1:
            findings[-1] += f'  (+{hits - 1} more lines, from line {first})'
    return findings


def check_paths():
    """A skill that points at a file which is not there fails at the worst moment."""
    findings = []
    pat = re.compile(r'`(context/[\w./<>-]+|reference/[\w./-]+|\.claude/[\w./-]+)`')
    for p in SKILLS.glob('*/SKILL.md'):
        for m in pat.finditer(p.read_text(encoding='utf-8')):
            rel = m.group(1)
            if '<' in rel or '*' in rel:          # a pattern, not a path
                continue
            if any(rel.startswith(x) for x in RUNTIME):
                continue
            target = W / rel
            if target.exists() or (W / f'{rel}.example').exists():
                continue
            findings.append(f'{p.parent.name}: points at {rel}, which does not exist')
    return findings


def check_subcommands():
    """`skill calls script cmd` — does that cmd exist?"""
    findings = []
    pat = re.compile(r'python3 (reference/scripts/[\w_]+\.py) ([a-z][\w-]*)')
    seen = set()
    for p in SKILLS.glob('*/SKILL.md'):
        for m in pat.finditer(p.read_text(encoding='utf-8')):
            script, cmd = m.group(1), m.group(2)
            if (script, cmd) in seen:
                continue
            seen.add((script, cmd))
            if not (W / script).is_file():
                findings.append(f'{p.parent.name}: calls {script}, which does not exist')
                continue
            r = subprocess.run([sys.executable, str(W / script), cmd, '--help'],
                               capture_output=True, text=True, cwd=W)
            if r.returncode != 0 and 'invalid choice' in r.stderr:
                findings.append(f'{p.parent.name}: calls `{script} {cmd}`, not a valid subcommand')
    return findings


def check_examples():
    """The invariant the whole "git pull keeps your work" promise rests on:
    every file that becomes the user's is gitignored and ships as .example."""
    findings = []
    for ex in (W / 'context').glob('*.example'):
        real = str(ex.relative_to(W))[:-len('.example')]
        r = subprocess.run(['git', 'check-ignore', '-q', real], cwd=W)
        if r.returncode != 0:
            findings.append(f'{real} has an .example but is not gitignored — '
                            f'a user filling it in would publish it')
    return findings


def check_frontmatter():
    findings = []
    for p in SKILLS.glob('*/SKILL.md'):
        head = p.read_text(encoding='utf-8')[:1200]
        for field in ('name:', 'description:'):
            if field not in head:
                findings.append(f'{p.parent.name}: SKILL.md has no {field[:-1]} in its frontmatter')
    return findings


def check_placeholders():
    """A {{PLACEHOLDER}} the renderer never fills aborts the render."""
    findings = []
    tpl = W / 'context/today_template.html'
    rnd = W / 'reference/scripts/render_dashboard.py'
    if not (tpl.is_file() and rnd.is_file()):
        return findings
    used = set(re.findall(r'\{\{([A-Z_]+)\}\}', tpl.read_text(encoding='utf-8')))
    filled = set(re.findall(r"'([A-Z_]+)':", rnd.read_text(encoding='utf-8')))
    for name in sorted(used - filled):
        findings.append(f'today_template.html uses {{{{{name}}}}}, which the renderer never fills')
    return findings


CHECKS = [
    ('personal data', check_leaks),
    ('output language', check_language),
    ('file references', check_paths),
    ('script subcommands', check_subcommands),
    ('.example pairs', check_examples),
    ('skill frontmatter', check_frontmatter),
    ('template placeholders', check_placeholders),
]


def main():
    quiet = '--quiet' in sys.argv
    total = 0
    for label, fn in CHECKS:
        found = fn()
        total += len(found)
        if found:
            print(f'\n{label}:')
            for f in found:
                print(f'  {f}')
        elif not quiet:
            print(f'ok  {label}')
    if total:
        print(f'\n{total} finding(s). Fix before publishing.')
        return 1
    if not quiet:
        print('\nClean.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
