---
name: setup-freelancer-os
description: Connects Upwork and teaches the system your niche — verifies the connector, reads what your account already knows (profile, past contracts, the full text of your sent proposals), then asks only what reading cannot answer, and writes context/expertise.md, experience.md and the Upwork keys in config.yaml. Called by the `setup` skill when the user says they work on Upwork, or on "set up upwork", "/setup-freelancer-os". Not the first-run skill — `setup` owns the first run and hands over here. Re-runnable: if the real files already exist, offer to review/update them instead of overwriting blind.
---

# Setup: Freelancer OS

This is the only step a new user needs before anything else in this repo works. Run it as a guided
conversation — ask, don't hand over a blank template and walk away. The screener, the pitch-page
generator and the proposal writer all read the files this skill produces; nothing else in the repo
does real work until they exist.

## Step 0: Check for an existing setup

If `context/config.yaml` already exists, this is a re-run. Read it and the other real files
(`context/expertise.md`, `context/experience.md`, `context/STATUS.md`), summarize what's already
filled in, and ask what the user wants to change rather than starting the interview over. Don't
silently overwrite a real file with a blank template.

## Step 1: Verify the Upwork connection

Call `list_accounts` (Upwork MCP). If it fails or returns nothing usable, stop here and tell the
user plainly: they need to connect the Upwork app for Claude first (Settings → Connectors, or
whatever the current path is in their client), then come back. Don't try to work around a missing
connection — every other skill in this repo depends on it.

From the result, find their **Freelancer** account and its `org_uid`. This is the value that goes
into `context/config.yaml` under `upwork_org_uid` — the user doesn't need to find this themselves,
you already have it.

## Step 2: The interview

Ask these in a natural conversation, not a rigid form — if the user already answered something in
their first message ("I do SEO and Google Ads for local businesses"), don't re-ask it.

1. **Name** — for the dashboard header and proposal sign-offs.
2. **Language** — `de` or `en`. This sets the whole dashboard's language AND the wording of the
   chat sentences its buttons copy (they get pasted into this same chat, so they should match how
   the user actually talks to you).
3. **Slack notifications** — optional. If they want a DM when the screener finds a strong match,
   ask for their Slack user ID (or help them find it — in Slack: profile → "Copy member ID"). If
   they say no or don't have Slack connected, leave it empty; the screener still logs everything to
   the dashboard either way.
4. **Their niche** — walk through `context/expertise.md.example` section by section rather than
   asking one giant open question:
   - Search tracks: 3–7 short, broad Upwork search words, both tool-based (a platform/category they
     specialize in) and needs-based (an outcome a client might describe without naming the
     mechanism). Push back on anything that's really a 2–3 word compound phrase — those return a
     small pool that misses jobs the client worded differently, which is the whole reason
     `expertise.md.example` explains broad-vs-narrow up front.
   - What they build / their niche, in their own words.
   - What a strong match looks like — the overlaps and signals worth a bonus.
   - **At least one real false-positive trap** — a job that looked right but wasn't, that they
     actually turned down or regretted taking. If they can't think of one yet, leave the section
     with the placeholder examples in place and a note to fill it in after the first few runs
     surface a real one — don't invent one for them.
5. **Their background**, for `context/experience.md` (read `context/experience.md.example` for the
   exact section format before asking — this file is shared by the pitch-page and proposal skills,
   so its shape is fixed, follow it exactly): track-record numbers they're comfortable citing,
   notable past projects or companies, any client-sourced praise/trait tags they have (e.g. from
   Upwork's own "Insights from completed jobs"), and relevant background. It's fine if this is thin
   at first — real numbers beat inflated ones, and the pitch-page skill already handles an empty
   section honestly rather than needing it padded.
6. **Testimonials** (optional, can skip and come back later) — if they have real client reviews
   they can paste in (from Upwork or elsewhere), write them into `context/testimonials.json`
   following the format in `context/testimonials.json.example`. Never invent one.

## Step 3: Write the files

Copy every `.example` file that doesn't have a real counterpart yet, then fill in what the
interview produced:

- `context/config.yaml` (name, language, upwork_org_uid, slack_channel_id)
- `context/expertise.md`
- `context/experience.md`
- `context/testimonials.json` (leave as `[]` if skipped)
- `context/STATUS.md` (copy as-is from the example — it already has two sensible starter tasks)
- `context/.upwork_jobs.json` (copy as `[]` from the example — never fabricate job data)

## Step 4: Render and confirm

Run `python3 reference/scripts/render_dashboard.py`. If it errors on an unfilled placeholder, that
means a step above was skipped — go back and fill it in, don't hand-edit the generated
`context/today.html` (it's fully derived and gets overwritten on the next render). Once it renders
clean, tell the user to open `context/today.html` in a browser and offer to run the screener for
the first time ("check upwork") so the Upwork tab has something real to show instead of an empty
state.

## Self-improvement

If a user gets confused by a question here, or the interview missed something the other skills
turned out to need, that's a signal to fix this file directly — the same pattern used by
`upwork-screener`'s own self-improvement step.
