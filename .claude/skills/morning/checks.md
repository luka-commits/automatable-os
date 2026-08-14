# QA checklist for /morning (only read when changing the skill, not on a daily run)

## Test Drive

Try these prompts to validate:

1. `/morning` — default, today
2. `/morning 2026-04-27` — specific future date (light test, mail/journal data may not exist)
3. `Guten Morgen` — should trigger the skill for a German-speaking user
4. `Brief me` — should trigger the skill in English

Output language always follows `config.yaml → language`, not the language of the trigger phrase (canonical rule: CLAUDE.md).

**Sanity checks after a real run:**
- ACTION NEEDED only contains direct asks from real people (compliance/IT mails are in TICKETS)
- ACTION NEEDED · WAITING · FOLLOW-UP NEEDED split: WAITING ≤3d, FOLLOW-UP >3d
- Reminder events (no attendees, user-organized) appear in the 📌 reminder section, not in the calendar
- No same thread appears in two different sections
- Section caps respected
- Every action-needed/follow-up item carries a draft-status tier (🟢/🟡/🔴)
- At least one artificial 🟡 test case asks its question inline instead of guessing or silently skipping
- Declining Step 5b's draft offer costs nothing — briefing, STATUS.md, JOURNAL.md, dashboard all already happened
- Sensitive-flagged mails never appear as draft candidates in Step 5b
- Step 3a's Haiku sub-agent actually fetched full body text before classifying anything as resolved/closed — spot-check one thread against the real mailbox
- If the Haiku sub-agent call fails, Step 3a falls back gracefully (noted in audit footer), briefing still completes
- Re-run on the same day: already-triaged mails are skipped (audit footer shows the count), but a NEW reply in a previously triaged thread still shows up in the briefing
- After the run, triaged mails carry the processed category in the mailbox (if `mail.tag_processed`), and `.triage_ledger.json` has one entry per triaged thread
- A mail finding that was NOT dealt with yesterday is still there today as an inbox row in the task list (persistence via STATUS.md — the ledger skip must not make it disappear)
- "take 1 into project X" turns the inbox entry into a task under project X in STATUS.md; on the next render it sits in the task list and the inbox marker is gone
- Day plan set → green plan markers on the tasks + progress line; "X is done" in the chat → re-render, the bar moves forward
- The dashboard has NO write interaction (no ticking off, no buttons) — only tabs/filters/sorting; everything operational runs in the chat
- Calendar tab: overdue row at the top, due tasks on the right weekday, "due later" at the bottom — all from data-due, without extra fragments
- The briefing block at the top narrates the day conversationally and can be collapsed/expanded (state survives auto-reloads)
