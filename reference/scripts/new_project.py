#!/usr/bin/env python3
"""Turns a won job into a project you can actually deliver.

This is the handover the pipeline used to be missing. Everything before it finds
clients; without this step the system is a lead generator that hands off into a
void, and the work, the deadlines and the deliverables live nowhere.

    python3 new_project.py "Acme SEO audit" [--client "Acme GmbH"] [--dry-run]
    python3 new_project.py --from-job <job_id> [--dry-run]

Four things happen, and either all of them do or none:

    1. projects/<slug>/ is created from projects/_template/
    2. A block is added to context/PROJECTS.md, above the History section
    3. A first task lands in context/STATUS.md under the project's own heading
    4. With --from-job, the job record keeps `project: <slug>` so the funnel
       still counts it and the project can say where it came from

It refuses rather than overwrites. An existing slug, a missing PROJECTS.md, a
STATUS.md without the heading it needs: each stops the run with the reason, so a
half-created project never exists. Use --dry-run to see the plan first.
"""
import argparse
import datetime
import json
import pathlib
import re
import shutil
import sys

W = pathlib.Path(__file__).resolve().parents[2]
PROJECTS = W / 'projects'
TEMPLATE = PROJECTS / '_template'
PROJECTS_MD = W / 'context/PROJECTS.md'
STATUS_MD = W / 'context/STATUS.md'
JOBS = W / 'context/.upwork_jobs.json'


def die(msg):
    print(f'ABORT: {msg}', file=sys.stderr)
    sys.exit(1)


def slugify(name):
    s = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return re.sub(r'-{2,}', '-', s).strip('-') or 'project'


# Words that carry no meaning in a folder name. An Upwork title is a sentence
# ("Google Ads audit for a dental clinic chain"), and the whole sentence makes a
# folder nobody wants to type.
NOISE = {'a', 'an', 'the', 'for', 'of', 'to', 'and', 'or', 'in', 'on', 'with',
         'we', 'our', 'my', 'need', 'needed', 'looking', 'seeking', 'expert',
         'freelancer', 'specialist', 'help', 'project', 'urgent', 'asap'}


def derive_slug(name, client, limit=44):
    """Client first, then what the job is. Both trimmed to stay readable.

    Client first because the same client comes back: `acme-seo-audit` sorting
    next to `acme-ads-rebuild` is the whole point, and a title-first slug loses
    that. Capped because a folder name is typed, not read.
    """
    what = [w for w in slugify(name).split('-') if w and w not in NOISE][:4]
    parts = []
    if client:
        parts += slugify(client).split('-')[:3]
    parts += what
    seen, out = set(), []
    for w in parts:                    # "Acme" in both client and title reads badly twice
        if w not in seen:
            seen.add(w)
            out.append(w)
    return '-'.join(out)[:limit].strip('-') or slugify(name)[:limit]


def today():
    return datetime.date.today().isoformat()


def load_jobs():
    if not JOBS.is_file():
        die(f'{JOBS.relative_to(W)} does not exist — no jobs have been screened yet.')
    try:
        return json.loads(JOBS.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        die(f'{JOBS.relative_to(W)} is not valid JSON ({e}). Fix that file first.')


def find_job(jobs, job_id):
    for j in jobs:
        if str(j.get('id')) == str(job_id):
            return j
    die(f'no job with id "{job_id}" in {JOBS.relative_to(W)}. '
        f'`upwork_status.py list` shows what is there.')


def job_artifacts(job):
    """Pitch pages and proposal drafts already written for this job.

    They live in jobs/ as `YYYY-MM-DD_<slug>.html` and friends. Moving them into
    the project is step three of the handover and the one most easily skipped,
    which is why it happens here rather than in an instruction: in three weeks
    they are the record of what you promised, and only if they are somewhere you
    will actually look.
    """
    src = W / 'jobs'
    if not src.is_dir():
        return []
    keys = {str(job.get('id'))}
    title = slugify(job.get('title') or '')
    if title:
        keys.add(title)
        keys.update(w for w in title.split('-') if len(w) > 4)
    hits = []
    for f in sorted(src.rglob('*')):
        if f.is_file() and any(k in f.name.lower() for k in keys):
            hits.append(f)
    return hits


def project_block(name, client, purpose, origin):
    """The PROJECTS.md entry. Deliberately short: status is a state, not a log."""
    lines = [
        f'## {name}',
        '',
        f'**Purpose:** {purpose}',
        f'**Status:** Just won, nothing delivered yet. First step is in `STATUS.md`.',
        '**Phase:** Planning',
    ]
    if client:
        lines.append(f'**Stakeholder:** {client}')
    lines += [
        f'**Where it came from:** {origin}',
        '',
        "_This project's open to-dos live in `STATUS.md` — here you find how the project "
        'stands, not what needs doing._',
        '',
        '---',
        '',
        '',
    ]
    return '\n'.join(lines)


def insert_project(text, block):
    """Above `## History`, or at the end when that section does not exist."""
    m = re.search(r'^## History[ \t]*$', text, re.MULTILINE)
    if m:
        return text[:m.start()] + block + text[m.start():]
    return text.rstrip('\n') + '\n\n---\n\n' + block.rstrip('\n') + '\n'


def insert_task(text, name, task, context):
    """Under `## Tasks (open)`, in the project's own `### <name>` group.

    A project's tasks belong under the project's name, not scattered: the group
    heading is what makes the morning list readable when four projects run at
    once.
    """
    heading = f'### {name}'
    entry = f'- [ ] **{task}** #prep\n  {context}\n'
    if heading in text:
        i = text.index(heading) + len(heading)
        return text[:i] + '\n\n' + entry + '\n' + text[i:].lstrip('\n')
    m = re.search(r'^## Tasks \(open\)[ \t]*$', text, re.MULTILINE)
    if not m:
        die(f'{STATUS_MD.relative_to(W)} has no "## Tasks (open)" heading — '
            f'that is the one section the dashboard reads. Add it, then re-run.')
    i = m.end()
    return text[:i] + f'\n\n{heading}\n\n' + entry + '\n' + text[i:].lstrip('\n')


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('name', nargs='?', help='Project name, e.g. "Acme SEO audit"')
    ap.add_argument('--client', help='Client name, goes in as the stakeholder')
    ap.add_argument('--from-job', metavar='JOB_ID',
                    help='Build it from a job in context/.upwork_jobs.json')
    ap.add_argument('--slug', help='Override the derived folder name')
    ap.add_argument('--dry-run', action='store_true', help='Print the plan, change nothing')
    args = ap.parse_args()

    if not args.name and not args.from_job:
        ap.error('give a project name, or --from-job <job_id>')

    job = None
    if args.from_job:
        jobs = load_jobs()
        job = find_job(jobs, args.from_job)
        name = args.name or job.get('title') or f'Upwork job {job["id"]}'
        # Written out rather than as a conditional expression: the one-liner this
        # replaces parsed as (A or B) if C else (D or E), so a dict client always
        # produced None and the first task lost the client's name silently.
        #
        # And the name is often genuinely absent: what the screener stores under
        # `client` is Upwork's stats block (rating, hires, posted), because the
        # search response carries no client name at all. So --client is how you
        # supply one, and no name is a normal outcome rather than a failure.
        client = args.client
        if not client:
            raw = job.get('client')
            if isinstance(raw, str):
                client = raw
            elif isinstance(raw, dict):
                client = raw.get('name') or ''
        origin = f'Upwork job `{job["id"]}`'
        purpose = (job.get('description') or '').strip().split('\n')[0][:200] \
            or 'Filled in from the job posting — rewrite this in your own words.'
    else:
        name = args.name
        client = args.client
        origin = 'Added by hand'
        purpose = 'Rewrite this in one sentence: why this project exists, the way you would '\
                  'say it to a colleague.'

    slug = args.slug or derive_slug(name, client)
    folder = PROJECTS / slug

    # Everything that would stop us, checked before anything is written.
    if not TEMPLATE.is_dir():
        die(f'{TEMPLATE.relative_to(W)} is missing — the repo copy is incomplete.')
    if folder.exists():
        die(f'projects/{slug}/ already exists. Pick another name, or pass --slug.')
    if not PROJECTS_MD.is_file():
        die('context/PROJECTS.md does not exist yet. Run the setup skill first — it '
            'creates it from PROJECTS.md.example.')
    if not STATUS_MD.is_file():
        die('context/STATUS.md does not exist yet. Run the setup skill first.')

    first_task = f'Confirm scope and first deliverable with {client}' if client \
        else 'Write down the scope and the first deliverable'
    first_context = (f'Everything you were given is in `projects/{slug}/inputs/`. '
                     f'Read it before replying.')

    if args.dry_run:
        print(f'DRY RUN — nothing written.\n')
        print(f'  create   projects/{slug}/  (from _template/)')
        print(f'  append   context/PROJECTS.md  ->  ## {name}')
        print(f'  append   context/STATUS.md    ->  ### {name}')
        print(f'                                    - [ ] {first_task}')
        if job:
            print(f'  set      job {job["id"]}.project = "{slug}"')
            for f in job_artifacts(job):
                print(f'  move     {f.relative_to(W)}  ->  projects/{slug}/inputs/')
        return

    shutil.copytree(TEMPLATE, folder)
    readme = folder / 'README.md'
    readme.write_text(
        readme.read_text(encoding='utf-8')
        .replace('[Project name]', name)
        .replace('[Name, or "own project"]', client or 'own project')
        .replace('[YYYY-MM-DD]', today())
        .replace('[Upwork job <id>, referral, direct outreach, …]', origin),
        encoding='utf-8')

    PROJECTS_MD.write_text(
        insert_project(PROJECTS_MD.read_text(encoding='utf-8'),
                       project_block(name, client, purpose, origin)),
        encoding='utf-8')
    STATUS_MD.write_text(
        insert_task(STATUS_MD.read_text(encoding='utf-8'), name, first_task, first_context),
        encoding='utf-8')

    moved = []
    if job is not None:
        job['project'] = slug
        JOBS.write_text(json.dumps(jobs, indent=2, ensure_ascii=False), encoding='utf-8')
        for f in job_artifacts(job):
            dest = folder / 'inputs' / f.name
            if dest.exists():          # never clobber; the older one keeps its name
                dest = dest.with_name(f'{dest.stem}_{today()}{dest.suffix}')
            shutil.move(str(f), str(dest))
            moved.append(dest.name)
        keep = folder / 'inputs' / '.gitkeep'
        if moved and keep.exists():     # it says to delete it once there is content
            keep.unlink()

    print(f'projects/{slug}/ created.')
    print(f'  context/PROJECTS.md  += ## {name}')
    print(f'  context/STATUS.md    += ### {name}  ({first_task})')
    if job is not None:
        print(f'  job {job["id"]} now points at it')
        for m in moved:
            print(f'  moved into inputs/: {m}')
    # Say what is actually left. Claiming a step that just ran, or asking for one
    # that cannot be automated without saying so, both cost trust in the output.
    if job is not None:
        rest = ('the message history' if moved else
                'the proposal, the pitch page and the message history')
        print(f'\nStill yours to move: {rest}. Upwork threads cannot be exported, so paste '
              f'the parts that matter into projects/{slug}/inputs/ — in three weeks they are '
              f'the record of what you promised.')
    else:
        print(f'\nNext: put whatever the client already sent into projects/{slug}/inputs/, '
              f'then write the scope into its README.')


if __name__ == '__main__':
    main()
