# Dashboard render contract

The binding contract for every render of `context/today.html` — a full `/morning` run and a mid-day update from the chat alike. **For a mid-day update this file plus the changed context files is enough — never load the /morning skill for that.**

## Mechanism

```
python3 reference/scripts/render_dashboard.py --full     # /morning: rebuilds the Setup and Audit tabs too
python3 reference/scripts/render_dashboard.py --fast     # mid-day: markdown parts only, ~0.2 s
```

The script reads `context/STATUS.md`, `PROJECTS.md`, `JOURNAL.md`, `BRIEFING.md` and `config.yaml` and fills every derived placeholder itself. **Your job is three files, nothing else:**

| You write | It carries |
|---|---|
| `context/BRIEFING.md` | the briefing text — `## Lead`, `## Text`, then one `##` per collapsible section |
| `context/.mail_cache.json` | the fragments that need a network call: `agenda`, `inbox_items`, `email_status`, `audit_footer`, `week_days`, `birthdays`, plus `"date": "YYYY-MM-DD"` |
| `context/.fragments.json` | the Start Here blocks that need judgement: `SELBSTTEST`, `TOOLS_EXTRA`, `COMMANDS_USED`, `MEMORY_FILES`, `OWN_TOOLS` |

Everything else — tasks, project cards, notes, counts, dates, the day-status button — is derived. **Never write those fragments by hand and never regenerate the HTML shell.**

**Language follows `config.yaml → language`.** The script carries both wordings and picks at render time; it also READS both, so `## Tasks (open)` and `## Tasks (offen)`, `(due 09.08.)` and `(bis 09.08.)`, `(waiting on X)` and `(wartet auf X)` all work.

**Failure is loud on purpose.** A placeholder without a value aborts the run and leaves `today.html` untouched — a half-filled dashboard looks like a loading error and unsettles more than a state from yesterday does. If the template is missing, say so plainly ("`context/today_template.html` is gone — restore it from the original copy") and carry on with the briefing; the template is source code, not reconstructable.

**The cache is date-stamped.** If `date` is not today, the mail and calendar fields render empty instead of showing yesterday's state. That is why a mid-day re-render never rescans mail or calendar: it reuses the morning's cache and rebuilds only what comes from the files.

## What you write, in detail

### `context/BRIEFING.md`

```markdown
## Lead
ONE sentence, max ~16 words: what shapes the day, what it leads up to.

## Text
2–4 short paragraphs telling the day conversationally, like a chief of staff
briefing you for 30 seconds. Max ~220 words.

## Waiting on
- One line per item: on whom, since when (absolute date + days), and what
  happens if it does not come. That last part is the point.

## Since yesterday
- What actually moved. Past tense, no to-dos.

## Today and overdue
- Tasks dated today or earlier, verbatim from STATUS.md, oldest first.
```

`## Lead` and `## Text` are fixed names. Every other `##` becomes a collapsible section, in file order, with its item count in the summary; the first one renders open. **A section with nothing to say is left out entirely** — never an empty shell, never "nothing here today".

**Three signals belong in `## Text`, woven into the prose rather than listed:** what came in from the mail and needs a decision (with sender and core point), where you are waiting (name and age), and what is due today or overdue (by name, without alarmism). Completeness beats elegance here — better one sentence more than an overdue task that only shows up in the list below. Names and projects in `<strong>`. Prose, no bullets, no icon staccato.

### `context/.mail_cache.json`

`"date"` first, then `"mail_checked": true|false` (false = fast mode without the mailbox; the mail fields stay empty and must not be reported as state). The fragments:

- **`agenda`** — the day as a timeline, one `<li>` per meeting:
  `<li class="ev" data-time="HH:MM" data-end="HH:MM"><b>HH:MM</b> Title <i class="ic ic-video"></i>[<details class="mb"><summary>Briefing</summary><div class="mbc">…</div></details>]<i>context blurb</i></li>`
  **The order is binding: title, format icon, briefing button, THEN the context line** — the context line is a block element, and a briefing button behind it drops into a third line and gets clipped on short meetings. `ic-video` for remote, `ic-bldg` for in person, nothing when unclear. Priority via `p-red`/`p-amber` on the `li`. **`data-end` is mandatory for anything with a time** — the template draws block height, free gaps and overlaps from it; without it everything becomes 30 minutes and the timeline stops matching the calendar. Timed reminders get `class="ev rem"`; all-day items get `<li class="ev rem"><b><i class="ic ic-cal"></i></b> Title</li>` with no `data-time`. Dimming the past, the now line and the "running"/"up next" markers are done client-side — do not compute them.
- **`inbox_items`** — same row markup as tasks, with `data-inbox="1"` and a running number tag. Text = the core point plus the number (plus a mail link); sender and age go into the `t-note`. The inbox is deliberately unfiltered and unsorted: it is a decision zone, not a work list.
- **`email_status`** — one line of non-actionable housekeeping: `Tickets open N · FYI N[ · 🔒 N sensitive]`. Anything actionable already went into `inbox_items`.
- **`audit_footer`** — one line: `X mails checked · M already triaged · Y ticket threads grouped · Z newsletters left out`. Omit any segment whose count is 0.
- **`week_days`**, **`birthdays`** — the week strip and birthday lines, when the calendar was read.

### `context/.fragments.json`

Optional. A missing key renders as an empty string and the block collapses on its own — that is the designed behaviour, not an error.

- **`SELBSTTEST`** — one `<li>` per open item from `reference/self-test.md`: `<li><b>Short label:</b> consequence + what the user can say</li>`. Nothing open → leave it out.
- **`TOOLS_EXTRA`** — only skills the user added themselves, recognised by a `SKILL.md` newer than `VERSION.md`. Per hit `<div class="tool"><code>/name</code><h3>Title</h3><p>one sentence from the frontmatter description</p></div>`.
- **`COMMANDS_USED`**, **`MEMORY_FILES`**, **`OWN_TOOLS`** — the "recently used", "your memory" and "your own tools" rows of the Workspace tab. Cheap, local file dates and `config.yaml` only.

## Opening it

OS from `config.yaml → os`; empty → detect via `uname`. **Windows:** `cmd //c start "" context/today.html`, on failure `explorer.exe context/today.html`. **Mac:** `open context/today.html`. If both fail, name the path. Never blocking.
