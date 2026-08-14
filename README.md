# Freelancer OS

An operating system for freelance work, built for Claude Code. It opens and closes your day,
searches Upwork and scores every result against **your own** niche, turns a qualified job into a
pitch page and a written proposal, and when you win one, turns that into a project with its own
folder and its own first task. Finding the work and doing the work, in one place.

**Nothing in it is mandatory, including Upwork.** Say you don't use it during setup and the whole
acquisition layer stands down: no connector, no nagging, no half-empty tab. The day loop, the
projects and the dashboard work on their own, and referrals and direct clients take the same route
into a project that a won job does.

It's a template, not a hosted product. You clone it, run one setup skill, and it's yours: your own
niche, your own data, your own repo.

**Want the picture before the detail?** Two pages, both offline and both a double click:
[`ONBOARDING.html`](ONBOARDING.html) is the four first-run steps and what each one leaves
behind; [`SYSTEM.html`](SYSTEM.html) is every step of the day and why it is shaped that way.

## What you get

- **`upwork-screener`** — searches Upwork on a broad set of terms (tool-based + needs-based, not
  narrow compound phrases — narrow queries just shrink the pool), scores every result 0–100 against
  your own `context/expertise.md`, logs every real candidate, and optionally sends you a Slack DM
  when a strong match shows up.
- **A dashboard with five tabs**, generated as one static HTML file you open in a browser:
  - **Today** — your briefing, then your open tasks sorted Eisenhower-style (urgent × important),
    filterable by quadrant, by what is due, and by project.
  - **Projects** — how each one stands, and where it came from.
  - **Upwork** — the pipeline, in three views: a sortable **list**, a **Pipeline** board (Outreach →
    In contact → Offer sent, one column each, cards that move as the status changes), and **Stats**
    (a funnel: how many jobs made it from found → applied → in contact → offer → won).
  - **Tooling** — what this machine actually has: skills, CLIs, connections, plugins, keys. Read
    from the machine on every render, not from a list somebody maintains.
  - **System** — the explainer page, so what the thing does is one click away rather than in a
    file you have to know about.
- **`upwork-pitch-page`** (optional) — builds a one-page pitch site for a single job: an
  interactive, editable SVG diagram of the solution (pan, zoom, rename nodes, no design tool
  needed), a slot for a video walkthrough you record yourself, testimonials, and your CV.
- **`upwork-proposal`** (optional) — writes the actual submitted proposal text, using a video
  walkthrough transcript as its source of real technical specifics (record yourself solving the
  problem before you write a word — it reads far less generic).
- **The dashboard never writes anything.** Every button on it just copies a ready sentence to your
  clipboard, for you to paste into your Claude Code chat — Claude does the actual work
  (`upwork_status.py`, editing files) with all its normal safeguards. The dashboard is a pure view,
  always.

## Requirements

- [Claude Code](https://claude.com/claude-code), with the **Upwork** connector enabled (Settings →
  Connectors — this is what lets the screener actually search and read jobs).
- Python 3.9+ (standard library only — nothing to `pip install`).
- Optional: a Slack connection, if you want DM notifications on strong matches.
- Optional, only for `upwork-pitch-page`: a Vercel account, if you want to deploy pitch pages
  instead of just sending the local HTML file (the solution diagram itself is a self-contained
  interactive SVG built from a JSON graph — no external design tool needed).

### Optional: build the thing instead of drawing it

Everything above gets you a proposal and a pitch page. These four turn "here's how I'd build it"
into "here it is, click it", which is a different conversation with a client. All optional, and
worth adding only for the kind of work you actually pitch.

| Add | What it unlocks | How |
|---|---|---|
| **`gh` + `vercel` CLI** | For website jobs: build the page, deploy it, put the live URL in the proposal. The single strongest move available, because the client stops imagining and starts clicking. | `brew install gh` · `npm i -g vercel`, then log in to each |
| **n8n** (self-hosted recommended) | For automation jobs: create the workflow through the API and hand over importable JSON, or a link if your instance is reachable. See the setup below. | Docker, see below |
| **Make** | Same idea, scenarios and blueprints are API-addressable | `MAKE_API_KEY` |
| **`video-analyzer` skill** | Reads an intro video (frames, scene changes, transcript) so `upwork-profile` can judge it. Needed only if you want your profile video assessed. | install the skill, then export your video to a local file |

**GoHighLevel is the exception, and it's worth knowing before you promise anything:** its API
**cannot create workflows.** Measured 14.08.2026 against a live account — `GET /workflows/`
returns 200 but only names and status, `GET /workflows/<id>` is 404, and `POST /workflows/` is
404. A GHL job gets the diagram, not a live link. Add `GHL_API_KEY` if you want to read contacts,
opportunities and appointments; do not plan a build pipeline on it.

#### Setting up self-hosted n8n

Docker is the reliable route. Installing n8n through npm pulls `isolated-vm`, which needs
`node-gyp`, which needs Python's `distutils` — removed in Python 3.12, so the install fails on a
current machine and can even exit 0 while having failed.

```bash
docker volume create n8n_data
docker run -d --name n8n --restart unless-stopped \
  -p 5678:5678 -v n8n_data:/home/node/.n8n \
  -e N8N_SECURE_COOKIE=false \
  docker.n8n.io/n8nio/n8n
```

Open `http://localhost:5678`, create the owner account, then **Settings → n8n API → create an API
key**. Put both in your credentials file:

```
N8N_BASE_URL=http://localhost:5678
N8N_API_KEY=<your key>
```

Verify it actually works before relying on it, by creating a workflow rather than just pinging
the server:

```bash
curl -s -X POST "$N8N_BASE_URL/api/v1/workflows" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" -H "Content-Type: application/json" \
  -d '{"name":"connection test","settings":{"executionOrder":"v1"},"nodes":[],"connections":{}}'
```

**A local instance gives you working workflows and exportable JSON, not a link a client can
open.** `localhost` is yours alone. For a URL that goes in a proposal you need the instance
reachable from outside: a small VPS (~5 EUR/month) or n8n Cloud. A `cloudflared` tunnel from your
laptop works for a quick test and is a poor idea in a proposal, because the link dies the moment
your machine sleeps, and a dead link in an application is worse than no link.

## Quickstart

```bash
git clone https://github.com/luka-commits/freelancer-os.git
cd freelancer-os
claude
```

**You do not have to type anything to start.** A session-start hook notices the setup has
not run and begins it on your first message. If you would rather drive it yourself, say
`set up freelancer os`.

The setup asks for your language and name, then — only if you say you work on Upwork — connects
your account and *reads* it before asking anything: your profile, your past contracts, and the
full text of proposals you have already sent. What it cannot read, it asks, and that is three
questions rather than twelve. Out of it come `context/config.yaml`, `context/expertise.md` and
`context/experience.md`.

The visual version of those steps is [`ONBOARDING.html`](ONBOARDING.html). Once setup is done:

> check upwork

runs the screener for the first time. Open `context/today.html` in a browser to see the result —
re-run `python3 reference/scripts/render_dashboard.py` any time your data changes (the setup and
screener skills do this for you automatically).

## How the pipeline works

```
new → notified → proposal_sent → interviewing → offer_sent → hired
                                                      ↘ rejected (any point)
```

Move a job forward by telling Claude in chat — "the client replied on the SEO job", "I sent them an
offer" — or run `reference/scripts/upwork_status.py` yourself. The dashboard's own buttons are a
shortcut for the same thing: click one, paste what it copied, send it.

## Customizing it

- **Design**: every color in `context/today_template.html` reads from a handful of CSS variables at
  the top of the `<style>` block — change those, not individual rules.
- **Search tracks and scoring**: edit `context/expertise.md` directly, any time — it's the only file
  the screener's scoring step reads for what counts as a good job. If you notice the screener
  under- or over-rating something, that's a signal to sharpen this file, not to argue with it in
  chat every time.
- **Task format**: `context/STATUS.md`'s format (headline, due date, `#category` tag) is documented
  at the bottom of `context/STATUS.md.example`.

## Optional skills that are not in this repo

Three kinds of skill exist, and only the first ships here.

**Shipped:** everything under `.claude/skills/` — the Upwork pipeline, the day loop
(`morning`, `eod`, `ingest`, `checkup`, `audit`), and the CLI handbooks. These update with
`git pull`.

**Not shipped, on purpose — third-party skills with their own release cycle.** Vendoring
them freezes their bugs and drops their fixes; one of them documents exactly that failure in
its own instructions. Install them from the source instead, and they stay current on their
own:

| Skill | What it adds | Install |
|---|---|---|
| `last30days` | What people said about any topic in the last 30 days, across Reddit, X, YouTube, HN | `npx skills add mvanhorn/last30days-skill` |

**Not shipped, and cannot be — Anthropic's own bundled skills** (`docx`, `pdf`,
`powerpoint`). They carry `© Anthropic, PBC. All rights reserved.` and are governed by your
own agreement with Anthropic, so they are not ours to redistribute. If you have Claude Code,
you already have them; nothing to install.

## The tools this expects

Skills degrade honestly when a tool is missing — they say so rather than failing halfway.
Install only what you actually want:

| Tool | Needed for | Without it |
|---|---|---|
| Upwork connector (Claude Code → Settings → Connectors) | everything Upwork | the pipeline cannot run at all |
| `gws` CLI + a Google account | the `gws-*` skills, mail and calendar in `morning` | `morning` skips those tiers and still briefs you |
| `firecrawl` | web scraping and search in research steps | those steps say what they could not fetch |
| `playwright` | browser automation, screenshots | skills that need a browser stop and tell you |
| Slack (MCP) | the screener's DM on a strong match | it logs to the dashboard instead, silently |

**API keys go in one place and never into this repo:** `~/.config/credentials.env`,
`chmod 600`. `.gitignore` already blocks `credentials.env`, `.env` and `*.key` — but the
rule is the habit, not the file. If a skill needs a key it does not have, it says which one
and stops; it does not guess.

## Updating

```bash
git pull
```

That is the whole procedure, and it does not touch your work. Everything you own -
`context/config.yaml`, `expertise.md`, `experience.md`, `testimonials.json`,
`.upwork_jobs.json`, `STATUS.md`, the generated dashboard - is in `.gitignore`, so a pull
updates the machinery and leaves your data where it is. The `.example` files next to them
are the shipped versions; they update, your real files do not.

Read `CHANGELOG.md` before pulling. Anything marked **Action needed** means a file you own
has to change; everything else takes effect on its own. The version you are on is in
[`VERSION.md`](VERSION.md).

If you edited a shipped file directly - a skill, `render_dashboard.py`, the dashboard
template - git will tell you about the conflict. That is the cost of editing in place, and
it is why the customization points above route through `context/` instead.

## Why it's built this way

This started as one person's personal setup and got pulled out into a standalone template so
other freelancers could run their own copy without inheriting anything personal — no one else's
niche, no one else's data, no one else's Slack channel. The **mechanics** (broad-search-then-score,
the pipeline stages, the pure-view dashboard, the "record yourself solving it first" proposal
workflow) are what's worth keeping; your own judgment about your own niche is what makes it work
for you specifically.

## License

MIT — see `LICENSE`. Fork it, change anything, no attribution required.
