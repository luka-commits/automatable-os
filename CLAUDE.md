# CLAUDE.md — Freelancer OS

Working instructions for Claude Code **in this repo**. This file is self-contained — nothing it
says lives anywhere else, so it works the moment someone clones this repo, before they've read
anything about how the person who built it works elsewhere.

## What this is

An operating system for freelance work, built around Upwork but not limited to it. Three
layers, and each one works without the ones above it:

1. **The day** — `morning` briefs you, `eod` closes the day, `ingest` files what comes in,
   `checkup` and `audit` keep the workspace honest. Tasks live in `context/STATUS.md`,
   projects in `projects/`, and a static dashboard renders both.
2. **Acquisition** — `upwork-screener` finds and scores jobs against **your own** niche,
   `upwork-pitch-page` and `upwork-proposal` turn a qualified one into something you send,
   `upwork-inbox` and `upwork-reply` handle the account side once a client answers.
3. **Delivery** — a won job becomes a project with its own tasks and materials, and from
   there it is ordinary work the day loop already carries.

`ONBOARDING.md` describes the path end to end. `SYSTEM.html` is the same thing to look at
rather than read: every step, what happens inside it, and why it is shaped that way. Open it
with a double click. `README.md` has the setup walkthrough.

## Optional means optional

**Nothing here is mandatory. Not even Upwork.**

Upwork is one acquisition channel, not the core. Someone whose clients come from referrals or
direct outreach uses the day loop, the projects and the dashboard, and never connects an
Upwork account at all — and the system must not nag them about it, hide half its value behind
it, or leave a dead tab in the interface.

Everything else is the same: a Google account, Slack, a scraping key, a particular terminal, a
particular editor are capabilities you may or may not have. The system's job is to work
without them and say so plainly.

Concretely, for anything you build or change in this repo:

- **A missing tool degrades a step, it never fails a run.** `morning` without a mail
  connection still briefs you on calendar and tasks and names what it skipped. The screener
  without Slack logs to the dashboard instead of sending a DM. Neither stops.
- **Say which one is missing and what it would add.** "No Slack configured, so strong matches
  land in the dashboard only" is useful. A stack trace is not.
- **Never make a preference a requirement.** Terminal, editor, task manager, note app: the
  user has one already. Read from and write to files; let them keep their tools.
- **Ask before installing anything**, and let the answer be no without breaking anything.

The reason is not politeness. A system that demands eight accounts before it does anything
gets abandoned at account three, and the person never finds out whether it was any good.

## First thing to do in a fresh clone

If `context/config.yaml` doesn't exist yet, this repo hasn't been set up. Run the
`setup-freelancer-os` skill (say "set up freelancer os") before anything else — every other
skill here reads files that setup produces.

## Before anything else: what Upwork allows

Upwork suspends accounts for unattended automation. From
[Use bots and other automation properly](https://support.upwork.com/hc/en-us/articles/43342677368467-Use-bots-and-other-automation-properly),
quoted verbatim as grounds for enforcement:

> "Using OAuth2 tokens or session cookies from a browser or **an official client** in a script or bot"
> "Exceeding rate limits or **running background polling that resembles scraping**"

So two things that would technically work are off the table: copying your Claude Code OAuth token
into a cron job, a hosted agent or a credential vault, and polling on a tight schedule.

What stays fully allowed is the official connector inside Claude Code **with you sitting in front
of it**: search, score, draft, submit, read and answer messages, contracts, finances. Exactly one
thing is missing from that list, and it is "sends on its own".

**Therefore, in this repo:**

1. **Nothing leaves the account without an explicit yes** from the human. Draft freely, send never.
2. **The screener runs on demand, not on a timer.** If you ever schedule it, gate it on presence,
   jitter the interval, and stay off it at night.
3. **Each run reports its call count.** One sentence. Then "well under the limit" is measured.
4. **Run `upwork_status.py prune` after each run** — Upwork's terms cap caching of API responses
   at 24 hours. Your own scoring, notes and history are yours and stay.

The numbers, for reference: 300 requests/minute per IP, 40,000/day under an approved API key,
caching capped at 24 hours. Your volume will not come close. **The pattern is what gets flagged,
not the volume** — there is no documented threshold below which unattended polling is safe.

An approved API key would permit automation. It requires $25,000 in lifetime earnings, a Job
Success Score of 90%, and it is "for personal and internal use only. Commercial use isn't
supported."

## The one rule that matters most: the dashboard is a pure view

`context/today.html` is generated by `reference/scripts/render_dashboard.py` and **never
hand-edited** — it's overwritten on every render. Every button on it copies a ready sentence to
the clipboard; it never writes to a file or calls a script itself. All real state changes go
through this chat: you read the pasted sentence, then run the actual command
(`upwork_status.py`, editing `STATUS.md`, etc.). Keep it that way — a dashboard that quietly writes
its own state is a second source of truth waiting to drift from the first.

## Where things live

```
CLAUDE.md                          this file
README.md                          what this is, setup walkthrough, what to install
ONBOARDING.md                      the intended path end to end
SYSTEM.html                        the whole system on one page, for looking at rather than reading
ONBOARDING.html                    the four first-run steps, visually. Open on a double click
CHANGELOG.md                       what changed, and what needs your hand
context/
  config.yaml                      name, language, upwork ids, your daily goal
  expertise.md                     your niche, search tracks, false-positive traps
  experience.md                    your background, read by pitch-page + proposal
  testimonials.json                real client reviews, or []
  STATUS.md                        the only task truth — the Today tab renders exactly this
  PROJECTS.md                      how each project stands. No to-dos, those live in STATUS.md
  JOURNAL.md                       what happened and what was decided, newest first
  PERSONAL.md                      goals, habits, finances — not tied to a project
  .upwork_jobs.json                the job pipeline data
  today_template.html              the dashboard's HTML/CSS/JS shell
  today.html                       generated — never edit by hand
  *.example                        the shipped, empty version of every file above that is yours
.claude/
  skills/                          33 skills, see the table at the bottom of this file
  hooks/                           session-start checks: setup done? update available?
  settings.json                    which hooks run when
reference/
  *.md                             the handbooks, listed in the table below
  scripts/                         the eight scripts, listed in the table below
projects/
  README.md                        the layout, the lifecycle, how a won job becomes one
  _template/                       copied when a project is created
  <slug>/                          one folder per project. Yours, gitignored
jobs/                              generated per-job artifacts (pitch pages, proposal drafts)
```

### The handbooks in `reference/`

Read on demand, not up front. Each one is the single place its topic is settled, so a
skill links here instead of restating it.

| Read this | When |
|---|---|
| [`reference/upwork-mcp.md`](reference/upwork-mcp.md) | Before building anything on Upwork. What the API actually does, measured. Reading gives you a lot, writing almost nothing |
| [`reference/upwork-regeln.md`](reference/upwork-regeln.md) | Before automating anything on Upwork. What is allowed, with the numbers and the sources |
| [`reference/mcp.md`](reference/mcp.md) | Connecting mail, calendar, storage or anything else. What each connection unlocks |
| [`reference/tools.md`](reference/tools.md) | Which CLI does what, and what stops working without it |
| [`reference/plugins.md`](reference/plugins.md) | Which plugins are worth having, and what each one notices for you |
| [`reference/vendor-skills.md`](reference/vendor-skills.md) | Skills in here that other people wrote: where they came from, how they update |
| [`reference/gws-cli.md`](reference/gws-cli.md) | Driving Google Workspace from the command line |
| [`reference/mail-triage-rules.md`](reference/mail-triage-rules.md) | Changing how `morning` decides what a mail is |
| [`reference/routines.md`](reference/routines.md) | Running something on a schedule, and when not to |
| [`reference/dashboard-render.md`](reference/dashboard-render.md) | Touching the dashboard. Why it is a pure view, and what that forbids |
| [`reference/design.md`](reference/design.md) | The visual language the dashboard and the pitch pages share |
| [`reference/links.md`](reference/links.md) | Where a generated page gets hosted |
| [`reference/self-test.md`](reference/self-test.md) | The list `checkup` works through |
| [`reference/ATTRIBUTION.md`](reference/ATTRIBUTION.md) | What in here is not ours, and under which licence |

### The scripts in `reference/scripts/`

| Script | What it does |
|---|---|
| [`reference/scripts/render_dashboard.py`](reference/scripts/render_dashboard.py) | Builds `context/today.html`. Fully derived, safe to re-run any time |
| [`reference/scripts/upwork_status.py`](reference/scripts/upwork_status.py) | The small CRM: stages, history, `applied_at`, `prune` |
| [`reference/scripts/workspace-audit.js`](reference/scripts/workspace-audit.js) | Measures the folder for `audit`; writes `context/audit.json` |
| [`reference/scripts/adopt-plan.js`](reference/scripts/adopt-plan.js) | Plans a rebuild for `adopt`. Reads only, moves nothing |
| [`reference/scripts/inventory.js`](reference/scripts/inventory.js) | What this machine actually has: CLIs, plugins, connections |
| [`reference/scripts/lib-workspace.js`](reference/scripts/lib-workspace.js) | Shared readers for the two above |
| [`reference/scripts/new_project.py`](reference/scripts/new_project.py) | A won job becomes a project: folder, `PROJECTS.md` block, first task, artifacts |
| [`reference/scripts/check_repo.py`](reference/scripts/check_repo.py) | Seven checks that gate a release. Run it before publishing |

**The `.example` rule, and why it is the load-bearing one:** every file above that becomes
*yours* is in `.gitignore` and ships as `<name>.example` instead. That is what makes
`git pull` safe — the machinery updates, your data does not move. If you add a file the user
will fill in, add both halves in the same commit, or the next update publishes their work.

## Working rules

1. **Never commit a real, filled-in file that has a `.example` counterpart.** `.gitignore` already
   excludes them; if you're about to `git add` one anyway, stop and check why it's not being
   caught.
2. **Never fabricate data.** No invented testimonials, no invented job records, no invented
   calibration anchors in `expertise.md` — an empty section that's honest beats a padded one that
   isn't. This mirrors how `render_dashboard.py` already treats missing data (an honest empty
   state, never a guess).
3. **Edit files directly with Edit/Write, not a Python heredoc that reads-modifies-writes.** A
   `re.sub` with no match is a silent no-op; `Edit` fails loudly on the same case instead.
4. **`render_dashboard.py` aborts rather than half-write.** If you see "unfilled placeholders" on a
   render, a template variable is missing upstream — fix the source, don't patch the generated
   HTML.
5. **Self-improvement is a first-class step in every skill here.** If a user corrects a score, a
   phrasing, or a piece of guidance, edit the relevant `SKILL.md` directly rather than only
   remembering it for next time — that's how these skills got as good as they are before this repo
   even existed.
6. **Check what a tool can actually do before promising it.** Measured 14.08.2026, both against
   live accounts: Upwork's `update_profile` cannot write title, overview, skills, rate, portfolio
   or video, and GoHighLevel's API cannot create workflows at all (`POST /workflows/` → 404). The
   pattern behind both: **reading gives you a lot, writing gives you almost nothing.** So a skill
   that improves something hands over finished text to paste in, rather than promising a change
   the API cannot carry out. When a user asks for an automation, check the writing half exists
   before designing around it.

## Keeping the state files true

`STATUS.md` and `PROJECTS.md` are only worth anything if they match reality, and they only
match reality if **you** write to them as things happen in the chat. Nobody maintains a task
list on purpose; they maintain it as a side effect or not at all.

### What happens in the chat, and where it lands

| What was said | Where it goes |
|---|---|
| A project's situation changed | `PROJECTS.md`, its **Status** line — replaced, not appended |
| A new to-do, and it survives the filter below | `STATUS.md` under that project: headline plus one indented context line |
| Something is blocked | `PROJECTS.md` as **Blocker**; if it is a person, also a task with `(waiting on X)` |
| A decision, or a thing learned the hard way | `JOURNAL.md`, today's entry, one line |
| A task is done | `STATUS.md` → "Recently Done", newest first, capped at about six |
| A job reached `hired` | Not a task. Run `upwork-won`; the project it creates brings its own first task |

**Nothing to run afterwards.** Re-render with `python3 reference/scripts/render_dashboard.py`
and the dashboard follows. It reads the files; it never holds state of its own.

### Not every to-do is a task

The list has to stay readable at a glance, not be complete. Before writing one, in order:

1. **Under fifteen minutes, and you can do it yourself?** Do it. Writing the task down costs
   more than the task.
2. **Just so they know, no action?** `JOURNAL.md`, not `STATUS.md`. "Pushed cleanly, no
   conflict" is not a to-do.
3. **A step in a chain that will run in one sitting anyway?** It belongs in the one task's
   context line, not as its own bullet.
4. **Same kind of work, same context, different object?** One task naming them together.

**Rule of thumb: about three tasks per project.** More than that is a project plan, and a
project plan belongs in the project folder or in the context line, not in the list. A real
one grew to 379 lines because tasks quietly turned into deployment logs with commit hashes.

### Lengths, because the list is read every morning

- A `STATUS.md` task: **headline plus at most two lines of context** — what to do, where it
  is, what blocks it. The evidence and the backstory belong in the project or in the chat.
- A `PROJECTS.md` status line: **at most three sentences**, and it is a state, not a
  chronicle. What stood there before is history, so it goes to the journal.
- A `JOURNAL.md` entry: three to five short bullets a day, one line each.

The test: can they read the task in five seconds and know what to do? If you catch yourself
thinking "this needs the context that…", that is the line to cut.

### The categories are not decoration

Every task ends in `#deep-work`, `#quick-win`, `#comms`, `#prep` or `#admin`, and a due date
is written `(due YYYY-MM-DD)`. Together they decide the quadrant the dashboard sorts by:

- **Urgent** = a due date within seven days, or overdue. No date means not urgent.
- **Important** = `#deep-work`, `#admin` or `#prep`. `#quick-win` and `#comms` are not.
- Order: Q1 urgent and important → Q2 important → Q3 urgent → Q4 neither.

Leave the tag off and the task silently lands in the least important quadrant. Write a date
in any other format and the dashboard marks it amber rather than pretending there is no
deadline — but it still does not count as urgent, so use the ISO form.

**The classification is a heuristic, not a truth.** If a placement looks wrong to the user,
fix the category in `STATUS.md` rather than arguing for the rule.

## Building the thing instead of drawing it

The pitch page visualises a plan. For some jobs the stronger move is to actually build it and link
it, so the client clicks instead of imagining. Setup for each is in the README; the judgement of
*when* lives in `upwork-pitch-page`.

**Build it when all three hold:** the job names a tool that can be driven programmatically, the
posting is clear enough that a build isn't guesswork, and the job is worth the extra hour (real
budget, good client, genuine fit). A cheap gig-shop posting gets a diagram.

| Job names | What is possible |
|---|---|
| A website or landing page | Build it, `vercel` deploy, link the live URL. Strongest card available. |
| n8n | Create the workflow through the API, hand over importable JSON. A link needs a publicly reachable instance, not localhost. |
| Make | Scenarios and blueprints are API-addressable, same idea. |
| GoHighLevel | Diagram only. The API cannot create workflows, see rule 6. |

**Anything actually built has to be linked on the pitch page** (`--live-artifact "Label|URL"`). A
flow that exists but isn't clickable is, to the client, the same as a drawn one.

## Skills

33 skills in `.claude/skills/`. The ones you will actually type:

| Skill | What it does | Needs |
|---|---|---|
| `setup-freelancer-os` | First run: connection, reads your account, asks the rest | Upwork connector |
| `morning` / `eod` | Opens and closes the day | nothing; richer with mail + calendar |
| `ingest` | Files a document, transcript or note into the right project | nothing |
| `upwork-profile` | Audits your profile, or walks you through creating one | Upwork connector |
| `upwork-screener` | Finds and scores jobs against `context/expertise.md` | Upwork connector |
| `upwork-proposal` | The cover letter you actually send | Upwork connector |
| `upwork-pitch-page` | A one-page pitch site for a single job | nothing to draft; Vercel to host |
| `upwork-won` | A won job becomes a project: folder, first task, material moved in | nothing |
| `upwork-inbox` / `upwork-reply` | Client messages, invitations, offers — drafts, never sends | Upwork connector |
| `checkup` / `audit` | Is the machinery intact / is this a good system | nothing |

The rest are handbooks for tools you may or may not have installed (`gws-*` for Google,
`firecrawl`, `playwright-cli`, `supabase`, …). They are read, not run, and a missing tool
means the skill says so rather than breaking.

**Not shipped and not ours:** Anthropic's bundled `docx`, `pdf` and `powerpoint` skills carry
`© Anthropic, PBC. All rights reserved.` If you use Claude Code you already have them.
Third-party skills with their own release cycle (`last30days`) are listed in `README.md` with
their install command rather than copied in, so you get their updates instead of our snapshot.
