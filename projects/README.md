# projects/ — where the work lives

One folder per project. A project is normally one client engagement, and it is created the
moment you win one, not when you get around to it.

**This folder is yours.** It is in `.gitignore`, so `git pull` never touches it. What ships is
this file and `_template/`.

## The shape

```
projects/
  _template/              copied when a project is created — do not work in it
  acme-seo-audit/
    README.md             what this is, who the client is, what was agreed
    inputs/               what came in. Never edited: it is the record of what you were given
    work/                 your own work in progress
    outputs/              what went out, dated
    code/                 the repo, when there is one
    _archive/             superseded work. Never deleted
```

Subfolders appear when they have something in them, not in advance. A project with three
files does not need five empty directories.

## The one rule that keeps it honest

**State lives in `context/`, material lives in the project.**

`context/PROJECTS.md` says how a project stands. `context/STATUS.md` holds its open tasks.
Neither of those ever moves into the project folder, because the question you actually ask in
the morning is "how does everything stand", not "how does one project stand in isolation".

The project folder answers the other question: *what do I have.* What the client sent, what
you made, what you delivered. That question is always asked from inside one project.

Getting this backwards is the classic mistake, and it fails quietly: a status file per project
means no single place is ever right, and you find out weeks later.

## Naming, so the folder stays readable in a year

- **A slug, lowercase, hyphens:** `acme-seo-audit`, not `Acme SEO Audit (Final)`.
- **Client first when there is a client:** `acme-seo-audit` sorts next to `acme-ads-rebuild`,
  which is what you want when the same client comes back.
- **Deliverables are dated, never versioned:** `outputs/2026-08-14_audit.pdf`. The newest date
  is the one that counts. No `final`, no `v2`, no `final-final`.

## Creating one

```bash
python3 reference/scripts/new_project.py "Acme SEO audit" --client "Acme GmbH"
```

It copies `_template/`, writes the `README.md`, adds a block to `context/PROJECTS.md` and a
first task to `context/STATUS.md`. Run it with `--dry-run` to see what it would do.

A won Upwork job takes the same route with the job's own data filled in:

```bash
python3 reference/scripts/new_project.py --from-job <job_id>
```

That is what `upwork-won` runs. See below.

## From a won job to a project

When a job reaches `hired`, the pipeline is done and delivery starts. That handover is a real
step, not a formality — three weeks later, "what did I actually promise" is answered by the
proposal and the pitch page, and only if they were moved somewhere you will look.

Say **"I won the Acme job"** (or run `upwork-won`) and this happens:

1. The project folder is created from the job record: client, scope from the posting, agreed
   terms.
2. Its first tasks land in `context/STATUS.md` under the project name, drawn from what the
   posting actually asked for.
3. The proposal, the pitch page and the message history move into `inputs/` as project
   material.
4. The job record keeps `project: <slug>`, so the funnel still counts it and the project can
   still say where it came from.

After that it is an ordinary project. `ingest` files client material into it, its tasks show
up in `morning`, `eod` closes them out.

## Archiving one

When a project is over, move it to `_archive/` **inside `projects/`**, and do the two things
that are easy to skip:

1. **Deal with its open tasks first.** Each one is finished, void, or has to move somewhere
   else. A project archived with live tasks still in `STATUS.md` leaves you with entries whose
   context has vanished.
2. **Move its `PROJECTS.md` block to the History section** at the bottom of that file, with
   the date and one line on how it ended.

Nothing is ever deleted. The approach you rejected is what answers "why didn't we do it that
way" a year later.
