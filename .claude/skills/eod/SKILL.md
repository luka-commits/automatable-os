---
name: eod
description: "End of day: reconciles the day plan against reality, records what happened, what's left over and what was decided, then writes JOURNAL.md + PROJECTS.md with a short outlook on tomorrow. Shows one finished proposal, collects corrections only. No hour tracking. Trigger: /eod, 'end of day', 'feierabend'."
---

# /eod — end of day

A short close in the evening. Loads the context itself, shows a finished proposal, only collects corrections — and writes away what the day produced.

**When to use:** in the evening before finishing, when the day left traces the system should know about.

Everything the user sees (proposal, confirmation, entries written into `context/` files) is written in `config.yaml → language` (canonical rule: CLAUDE.md).

---

## Phase 1 — load context (automatic, parallel)

All reads in parallel, before you ask:

1. **Date + weekday** from system context
2. **`context/STATUS.md`** — **Day Plan** (if set today: the basis for the plan-vs-actual reconciliation), Tasks (open), Inbox (unhandled findings), Current Focus
3. **`context/PROJECTS.md`** — how the projects stand: status, blockers, timeline
4. **`context/JOURNAL.md`** — is today's entry already there? (do not duplicate)
5. **Calendar today** via the connected calendar connector (only with permission granted):
   - Deferred tool: load the calendar search tool first. For Microsoft 365 that is `ToolSearch select:mcp__claude_ai_Microsoft_365__outlook_calendar_search`; for another connector determine the tool name via `ToolSearch query:calendar` and use that one
   - Query `*`, afterDateTime = today 00:00, **beforeDateTime = tomorrow 23:59** (today for the review, tomorrow for the outlook in phase 5 — otherwise you would have to invent the number), order = oldest
   - Extract meetings with title + time, split into today/tomorrow
   - **If the retrieval fails** (connector missing, auth expired, permission not granted): do NOT abort, do not retry — close without the calendar and build one calm sentence into the proposal (_"I cannot reach your calendar right now — the review comes from your tasks and the journal."_). No tool name, no error text. A close without the calendar is fully valid, not an error state.
6. **Session history — a bonus only, never the basis:** the reliable sources are the files from 2–4 (today's Rule 1 updates are already in there) plus the calendar. If the chat history additionally holds things from today (what was done, meeting outcomes, decisions), work them in — but the close has to work just as well in a freshly opened window with an empty history. If the history is empty, do NOT dig for it ("what did you do today?") — the proposal comes from the files, and the user closes the gaps in the correction round.

---

## Phase 2 — show the proposal (do not interrogate)

ONE finished proposal that the user only corrects:

```
That was your day — does that work?

📅 [Weekday] [DD.MM.]

🎯 Day Plan: [N] of [M] — [what stayed open, in a half sentence]
   (drop the section if no plan was set)

What happened:
- [Project A]: [activity, derived from calendar/session/tasks]
- [Meeting title, HH:MM] — [outcome, if mentioned in the chat; otherwise: "Outcome?"]

Left over: [open plan items / overdue tasks, briefly]
[If inbox entries are unhandled: "N mail findings are still waiting in the inbox."]

Any blockers, decisions or insights still missing?
```

**Rules:**
- Only propose active projects from PROJECTS.md
- Invent nothing: activities only from calendar, session or files. Where a meeting outcome is missing, ask for it instead of guessing.
- Empty calendar + no session traces → still a proposal from the day plan; if that is empty too: "Quiet day? Then I will only record what stays open."

---

## Phase 3 — collect the delta only

The user corrects (strike, add, supply an outcome). No catalogue of questions — what is right in the proposal stays uncommented.

---

## Phase 4 — write

**A) `context/JOURNAL.md`** — day recap under today's date (append, never overwrite; if the entry already exists, add to it):

```markdown
## [YYYY-MM-DD]
- [Project]: [what happened, 1 sentence]
- [Meeting]: [outcome]
- Decision: [what, why] — only if mentioned
- Insight: [what] — only if mentioned
```

**Tone:** concrete half sentences with names and numbers (`threshold confirmed at 250k (Nicole)`), no nominal prose (`discussion of parameters`). Whoever reads this in three weeks has to understand what was meant without you.

**B) `context/PROJECTS.md`** — only for status-relevant updates. **Back up first** (CLAUDE.md safeguard 3): `mkdir -p context/.backup` + copy the three core files (`PROJECTS.md`, `STATUS.md`, `JOURNAL.md`) there, one generation each is enough. Then: status line (replace), blockers, timeline, "Last updated:".

**C) `context/STATUS.md`** — this is where the work lives: completed tasks to "Recently Done" (max 6, older ones out), tick off day plan items, create new tasks from the conversation. Pull the dashboard along (rule 1).

**D) Git backup (silent, never blocking)** — versioning without git knowledge: the day's state moves into your own private repo, "nothing gets lost" becomes provable, and scheduled runs in the cloud only see what has been pushed.

```bash
git add -A && git commit -m "eod YYYY-MM-DD" && git push
```

- Only if the workspace is a git repo (otherwise skip silently, not a word about it).
- Commit works, push fails (offline, auth expired): no drama — the commit is the backup, the push catches up next time. Say it calmly ONCE per session: _"Everything is backed up — only the copy on GitHub is lagging behind right now, that catches up next time."_ If the push keeps failing (several days): suggest `gh auth login` once (it is in SETUP.md step 0).
- Never `--force`, never resolve conflicts yourself: if the push reports a conflict (a second machine?), say what is going on and recommend the contact person from `VERSION.md`.
- The commit covers the whole workspace — `.gitignore` keeps runtime artifacts (cache, ledger, today.html, backups) out anyway.

---

## Phase 5 — confirmation + outlook

```
✓ Recorded: [1 half sentence on what went into the journal]
✓ PROJECTS.md: [what was updated | "no changes"]

Tomorrow [weekday]: [N meetings, first at HH:MM] · [what carries over from today's plan]
```

No ranking in the outlook (rule 10) — describe what is coming up, do not judge what is important.

---

## Special cases

**Catching up:** user says "for yesterday" → communicate clearly which day is being written for. Change older entries only after confirmation.

**Friday:** after phase 5, offer to summarize the week briefly (from the JOURNAL entries of the week) — only if the user wants it, no ritual.

---

## Output style

- Informal, brief, friendly
- No em-dashes
- Confirmation with a check mark (✓)
- No fluff, no "great job!"
