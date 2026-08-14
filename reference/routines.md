# Prebuilt routines

Routines are tasks that run on a schedule in Anthropic's cloud, without anyone sitting in front of them — how they work technically and what happens to the data is described in `SETUP.md` § "Running the briefing automatically". This file is the catalog: ready-made routines to switch on, each with one sentence to copy.

**The one prerequisite for all of them:** a routine works with a fresh clone of the repo — it only sees what has been pushed. The end of day (`/eod`) pushes automatically; if you do `/eod` regularly, there is nothing else to do here. A routine's results land in the repo and are there after a `git pull` (or readable on the go in the GitHub app).

**What routines never do:** send mail, create appointments, delete anything. The same rules as locally.

---

## 1. Morning briefing (the classic)

The briefing is finished before you open your laptop. The routine does the same as "good morning" in the chat: calendar, mail triage, tasks, dashboard — and pushes the result.

Switch it on (in the chat, in this folder):

> `/schedule every weekday at 7:30: create the morning briefing (run /morning in full), commit and push`

When creating it, Claude asks about the repo and connectors — mail/calendar have to be attached to the routine, otherwise it runs at the "without mailbox" level. Result: `inbox/briefing-YYYY-MM-DD.md` + a fresh dashboard in the repo.

## 2. Weekly review (Friday afternoon)

What happened this week, what was decided, what was left lying around — from the journal, project states and completed tasks, as one readable page. Good as the basis for your own status report upwards.

> `/schedule every Friday at 16:00: write a weekly review from the last 7 days of JOURNAL.md and PROJECTS.md into inbox/weekly-review-YYYY-MM-DD.md — only what is documented, no evaluation, no ranking — commit and push`

## 3. Monday outlook (Sunday evening)

The look at the coming week before it starts: upcoming due dates, waiting replies, quiet projects. Deliberately without mail access — a pure workspace view, so that nobody touches your mailbox on a Sunday.

> `/schedule every Sunday at 18:00: write an outlook on the coming week from STATUS.md (due dates, waiting-on entries) and PROJECTS.md (timelines) into inbox/week-ahead-YYYY-MM-DD.md, without mail and calendar access — commit and push`

---

**Managing them:** `/schedule list` shows everything, `/schedule run` tests immediately, overview in the browser at [claude.ai/code/routines](https://claude.ai/code/routines). A routine that annoys you gets deleted instead of endured — just say so in the chat.

**Building your own routine:** describe in the chat what should happen regularly and when — Claude formulates the `/schedule` sentence with you. The rules from `extending-the-system.md` § 1 apply here too: say the goal, say the source, name the exception.

## The level above: your own agents

A routine handles **one recurring task at a fixed time**. If instead you need something that is permanently available in the cloud and works on request (an agent of your own for a defined area), that goes through the included skill `managed-agents`. Say in the chat what the agent should be able to do, then Claude walks you through it.

**Two things to know beforehand, because they get expensive or awkward later:**

- **This costs extra.** Your own agents run on a paid Anthropic API access that is billed **alongside** your subscription, per usage. Routines do not need that, they run on your subscription.
- **It only pays off later.** An agent without context is just another chat. What makes it useful is your projects, your current state and your filing, which is exactly what comes into being in the first few weeks. Built before that, it has nothing to work with.
