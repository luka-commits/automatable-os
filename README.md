# Upwork Cockpit

A self-contained Upwork job-hunting system for Claude Code: it searches Upwork for you, scores
every result against **your own** niche, tracks the whole pipeline from "found" to "won" in a
small two-tab dashboard, and — optionally — turns a qualified job into a pitch page and a written
proposal.

It's a template, not a hosted product. You clone it, run one setup skill, and it's yours: your own
niche, your own data, your own repo.

## What you get

- **`upwork-screener`** — searches Upwork on a broad set of terms (tool-based + needs-based, not
  narrow compound phrases — narrow queries just shrink the pool), scores every result 0–100 against
  your own `context/expertise.md`, logs every real candidate, and optionally sends you a Slack DM
  when a strong match shows up.
- **A dashboard with two tabs**, generated as one static HTML file you open in a browser:
  - **Today** — your open tasks, sorted Eisenhower-style (urgent × important).
  - **Upwork** — the pipeline, in three views: a sortable **list**, a **Pipeline** board (Outreach →
    In contact → Offer sent, one column each, cards that move as the status changes), and **Stats**
    (a funnel: how many jobs made it from found → applied → in contact → offer → won).
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

## Quickstart

```bash
git clone https://github.com/luka-commits/upwork-cockpit.git
cd upwork-cockpit
claude
```

Then, in the chat:

> set up upwork cockpit

The setup skill checks your Upwork connection, interviews you for your niche and background (a
few minutes, not a form to fill out alone), and writes your own `context/config.yaml`,
`context/expertise.md`, and `context/experience.md`. Once it's done:

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

## Why it's built this way

This started as one person's personal setup and got pulled out into a standalone template so
other freelancers could run their own copy without inheriting anything personal — no one else's
niche, no one else's data, no one else's Slack channel. The **mechanics** (broad-search-then-score,
the pipeline stages, the pure-view dashboard, the "record yourself solving it first" proposal
workflow) are what's worth keeping; your own judgment about your own niche is what makes it work
for you specifically.

## License

MIT — see `LICENSE`. Fork it, change anything, no attribution required.
