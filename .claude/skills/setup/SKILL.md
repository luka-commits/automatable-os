---
name: setup
description: "One-time first-run personalization of a freshly copied workspace: asks language, name, email, role, projects, daily tools and Claude plan, fills context/, creates project folders, then archives itself. Runs automatically on first start or via /setup, 'ersteinrichtung'. NOT for daily use. An existing folder uses /adopt."
---

# Setup Skill — One-Time Workspace Personalization

## Core Principle

**Detect state, pick the language, ask once, write ONE config file, fill templates, archive itself.**

**And: the user must never wait into the void.** After their answers you work for several minutes straight. Before every longer block, one short line in the chat — `⚙️ Creating your project folders …`, `📄 Filing your documents …`, `✉️ Looking through your sent mail …`. One line, not a status report.

### Every step happens. Skipping is a decision the user makes, never one you make for them.

This skill contains a lot of "skip", "without comment", "don't offer by yourself". **Every single one of those refers to what you SAY, never to whether you ASK.** They exist so the setup does not turn into a sales pitch — not so that steps quietly disappear.

Measured on a real run (2026-07-23): Supabase and Vercel never came up, the plugins were never installed, and the person only noticed afterwards that a third of the equipment was missing. Nobody had decided that. The steps were simply gone, and a step that is gone never asks to come back.

So, in order:

1. **Run every step from 0 to 8, in order.** None gets left out because it "probably isn't relevant". You do not know that. The person in front of you does.
2. **Question or offer skipped because of a rule?** Then it is a rule about the WORDING, and the step still happens.
3. **Something genuinely does not apply** (no npm, no Git repo, no mail connection)? Then it is skipped **and named in the closing summary**, one line, with what it would have done. Never silently.
4. **The closing summary in Step 8 lists all of it** — done, declined, not possible. That list is the proof that this ran completely. Without it, neither of you can tell a deliberate no from a forgotten step.

**The test:** if the user asks afterwards "was X part of this?", they must be able to find the answer in the summary. Every "sorry, that never came up" is a bug in this skill, not user error.

## Say what is happening, and why it matters

The person in front of you has never seen this system and cannot tell a necessary step from a decorative one. So **before every step that asks something of them — a question, a sign-in, a decision — one sentence saying what happens now and what it buys them.** Not what you are technically doing. What it changes for them.

> Not: *"Now I'm going through the six connector slots."*
> But: *"Next we hook up your mailbox and calendar. That is what turns the morning briefing from a to-do list into something that actually knows your day."*

Three things make the difference between explaining and lecturing:

- **The benefit, not the mechanism.** "So that drafts sound like you and not like a template" beats "deriving your writing style from your Sent folder".
- **One sentence, then act.** A second sentence of justification turns into a lecture, and a lecture is what makes people click away.
- **Only where something is being asked of them.** Steps that run by themselves need the one-line progress note above, nothing more. Explaining something the user does not have to decide costs their attention for the moment when they really do.

### This is a conversation, not a form being filled in

Someone sitting through this has handed over half an hour and has no idea how long it lasts or what is still coming. Without that, every question feels like an interruption instead of a step. So:

**Say where you are, at every step.** One short line, before the content: _"Step 4 of 8 — your projects."_ That single habit is the difference between "this is going somewhere" and "how much longer is this".

**Open every step with what and why, close it with what it just bought them.** Two sentences, not a paragraph:

> *"Now the mailbox and the calendar. That's what turns tomorrow's briefing from a list into something that actually knows your day."*
> … *"Done — from tomorrow morning I can see your appointments."*

**Answers get picked up, not just recorded.** Someone who said in Step 1 that they work with Notion hears in Step 7.2 _"you mentioned Notion — let's connect that"_, not a generic question about six categories. That is the difference between being listened to and being surveyed.

**When something takes longer, say what is happening.** Installations and mail analysis run for minutes. Silence in those minutes reads as a crash.

**And at the end of each larger block, a real handover:** _"That's the equipment done. What's left is the summary, then you're ready."_ People need to know that the end is in sight — otherwise they quit two steps before it.

**Never techspeak without a translation.** "MCP connector", "runtime", "marketplace" mean nothing to the person in front of you. Say the thing, then the word once if it matters later: _"a connection to your mailbox — that's what's called a connector here"_.

**Why this is a rule and not a matter of style:** someone who does not understand why a step matters skips it — and the steps that get skipped are the equipment ones at the end, the ones that decide whether this stays a folder of notes or becomes a system that reaches into the tools they actually work in.

Personal values live only in `context/config.yaml` — skills read them from there at runtime. This skill never edits skill files.

## Step 0: Detect Package State

Read `context/config.yaml`.

- **Contains `[YOUR NAME]`** → fresh, unpersonalized package. Proceed straight to Step 0.5 — nothing to lose here.
- **A real name is already filled in** → **an earlier run was interrupted.** No "already set up": Step 8 archives this skill away when it finishes, so the fact that you are running at all means the last run broke off somewhere between Step 3 (writes the name) and Step 8. Say that honestly and continue where things are missing instead of overwriting everything: check what still carries placeholders (`context/PROJECTS.md` → `[First project`, `context/STATUS.md` → `[YYYY-MM-DD]`, project folders in `projects/`, is `context/EMAIL_STYLE.md` there?) and only make up the gap. Pattern: *"Your setup didn't run all the way through last time — name and location are in, but your projects are still missing. I'll catch that up, takes 5 minutes."* Only overwrite everything if the user explicitly wants to start over.
- **File missing entirely** → the copy is incomplete and cannot be reconstructed: `config.yaml` is the only place that knows the expected schema, and `/morning` reads exact keys from it. Don't invent anything, say it: the folder has to be cloned fresh (see `VERSION.md`).

## Step 0.5: Ask the Working Language (FIRST — before anything else)

Before the greeting and the intake questions, ask exactly one bilingual line — because everything the skill says from here on has to already be in the chosen language:

> **Which language should I work in? / In welcher Sprache soll ich arbeiten?**
> **English** or **Deutsch** — just hit enter for English. / **Englisch** oder **Deutsch** — mit Enter nimmst du Englisch.

Nothing else in this message: no greeting, no explanation, no questions. The real greeting comes in Step 1, in their language.

**From the answer onwards, the ENTIRE rest of the setup runs in that language.** That means every word the user sees: the fresh-start question (Step 0.6), the greeting and the six intake questions (Step 1), the model question (Step 3.5), the project and task proposals (Step 4), the document question (Step 6), the mail-style question and the derived profile (Step 7), every question in the equipment steps (7.1–7.4), and the whole closing summary including the mini-briefing (Step 8). No mixing, no "just this one line in English".

**The step contents in this SKILL.md stay English regardless** — they are instructions for you, not user output. The example wordings quoted in the steps below are English because this file is English; if the user picked German, you translate them as you speak them. Never paste an English example verbatim into a German conversation.

Store the answer as `"en"` or `"de"` and write it to `config.yaml → language` in Step 3. Anything other than a clear German choice (empty answer, enter, unclear) means `"en"`.

## Step 0.6: Fresh Start, or Is There Already Something? (one question, right after the language)

Before any intake question, ask this one — because the answer decides which of two different jobs this is:

> *"One thing before we start: is this a fresh start, or do you already have a folder where your work lives — notes, project folders, maybe a CLAUDE.md from an earlier attempt? If so, I don't set up a second system next to it, I take that one over."*

- **Fresh start** (the normal case) → carry on with Step 1, everything below applies unchanged.
- **There is an existing folder** → this is an **adoption**, not a setup. Ask for the path, then:
  1. **Measure it silently first:** `node reference/scripts/workspace-audit.js --root <path> --json`. Seconds, local files only, costs nothing. It gives you the lay of the land the takeover plan needs: what is there, what points at what, what is already dead.
  2. **Do not put the findings in front of the user.** Someone who has just arrived does not want a verdict on how they have been working before anything works at all. The measurement feeds your plan, not a report. The full assessment with recommendations is offered later, once the system runs, via `/audit`.
  3. **Hand over to the `adopt` skill** — it owns the takeover (plan, questions, moving with a way back, acceptance). Come back here for the intake questions and the equipment steps 7.1 to 7.4; those are the same in both cases.

**Why this question comes first and not later:** without it, someone with a grown folder runs straight through this setup and ends up with two systems side by side, neither of them complete. That is the most expensive outcome the whole package can produce, and one sentence at the start prevents it.

## Step 1: Ask Onboarding Questions

**First, open the page that shows what is coming.** Before the greeting, open `START-HERE.html` in the browser — OS-dependent (`os` from Step 2.5; unknown → detect with `uname`): **Mac** `open START-HERE.html`, **Windows** `cmd //c start "" START-HERE.html`, fallback `explorer.exe START-HERE.html`. Fails on both → name the file in the chat and carry on, it is never a blocker.

Then one sentence about it, not a lecture: _"I've opened a page for you that shows what happens in the next twenty minutes — you can read it while we go, or ignore it."_

**Why this comes before the questions and not after:** the person is about to answer six questions and hand over access to their mailbox, without any picture of what for. That page carries the eight-minute walkthrough and the whole run step by step. Someone who has seen it says yes to the equipment steps at the end; someone who has not, quits at question four. It is also the only version of this that works before the setup, because the dashboard it normally lives in does not exist yet.

Greet briefly and **say honestly what's coming** — the user just typed "hello" and has no idea what they're in for. Three sentences, no more, along these lines (in their language):

> *"This is going to be your personal work folder: morning briefing, project overview, mail drafts in your style. I'm setting it up for you now — I'll ask you six questions at once, then I'll create the folders. Expect 10 to 20 minutes, depending on how many projects and documents you bring along."*

Never promise "2 minutes". Whoever starts with the wrong expectation quits in minute four. Then ask these together in ONE message — like a short intake form, not one-by-one back-and-forth:

1. **Name + work email address**
2. **Position/role + area** (e.g. "Consultant, PIPE" or "Project Leader, TMT")
3. **Office:** the office abbreviation (e.g. "MUN", "FRA", "BER") and which weekdays they typically go in (rest = remote by default). **Never ask where they live** — a home city or address is private, the workspace has no use for it, and asking for it in an onboarding interview costs trust for nothing.
4. **Running projects/workstreams — ALL of them:** per project the name, a one-sentence purpose, the key stakeholders, the current state/next milestone (as far as known). This is the most important question of the setup — the system is only as good as this initial state. Bullet points are enough, the details come out of the documents in Step 6.
5. **Which tools do you work with every day, and what for each one?** Mailbox, calendar, where files live, where customer contact happens, what you bill with. Bullet points are enough: _"Outlook for mail, HubSpot for customers, WhatsApp for enquiries"_. **The "what for" is the point of the question**, not the list of names.

   **Then one follow-up, always, and it is the valuable one:** _"And is there a system your work actually runs through every day that we haven't named — bookings, patients, projects, orders, stock?"_ People answer "mail and calendar" to the first question and forget the software their whole business sits on, because to them it is not a "tool", it is just the job. That system is usually the most valuable connection there is, and it never comes up on its own. Whatever comes back goes into `tools_in_use` with its purpose — **also when there is no way in.** A named gap can be closed later (the catalogue grows, see `reference/mcp.md`); an unnamed one never comes up again. Step 7.2 decides the route, not this question.
6. **Which Claude plan do you have?** — Pro (€20), Max 5x (€100), Max 20x (€200), or Team/Enterprise through the company. One sentence on why that matters: _"It determines how generously I can work without your quota being empty by lunchtime."_

**Why the tools are asked about this early:** Step 7.2 connects the systems, and it does that fifteen minutes later. Without this answer it has to ask abstractly, slot by slot, _"do you have a CRM?"_ — a question with no context, which people answer with "no" out of uncertainty far more often than it is actually true. With the answer in hand it stops asking and starts working: it knows the systems by name, checks what can be reached and how, and only comes back with the bits that need the user's hands. The list also goes into `config.yaml`, so `/checkup` and `/audit` never ask it again.

**Why the plan is asked about and not the model:** the user knows their plan, it's on their invoice. Which language model fits their work is something they cannot know — and they only notice the wrong answer once the quota is empty or the results stay thin. A question the user cannot answer is not a choice, it's a trap. The model decision is derived from it in Step 3.

Don't over-explain each question.

## Step 2: Compute the Workspace Root

Derive the absolute path from the actual current working directory Claude Code is running in — **do not ask the user to type this**. (This package may have been moved/renamed after being received — compute fresh, never assume from any file's existing content.)

## Step 2.4: Is the Folder Sitting in a Cloud-Synced Directory? (say this immediately, not at the end)

**Do this before anything else is written**, because the answer can move the whole folder — and moving it after the setup means every path, every scheduled job and the Git remote have to be redone.

Check the workspace root path for the usual suspects:

```bash
pwd | grep -Ei 'onedrive|dropbox|google ?drive|pcloud|library/mobile documents|synology ?drive|nextcloud'
```

**No hit → say nothing, move on.** This is the only check in this whole skill that gets reported while it runs, and only when it fires.

**Hit → say it right away, plainly, and let them decide:**

> *"One thing before we start: this folder is inside your <OneDrive/iCloud/Dropbox>. That works, but it causes real trouble later. The sync service copies files while I'm writing them, and then you get duplicates like `STATUS 2.md` — and at some point I read the wrong one. It also tends to break the Git backup.*
>
> *My recommendation: move the folder somewhere local first, for example `~/workspace` or `~/Documents-local`. Your daily backup then runs through GitHub instead of the sync service, which is the safer route anyway. Shall we move it, or do you want to leave it where it is?"*

- **Move it** → move the folder, then **recompute the root from scratch** (Step 2) and carry on. Do not carry the old path forward anywhere.
- **Leave it** → a full answer, respected without a second attempt. But it goes into the closing summary as one line, so it is a documented decision and not a surprise in three weeks: _"Your folder is in <service> — if duplicates like `STATUS 2.md` show up, that's where they come from."_

**Why this is worth its own step:** the ` 2.` duplicates in the check below are the symptom. This is the cause, and it is the one thing that gets massively more expensive the later you fix it.

## Step 2.5: System Check (silently, while the user answers the questions)

Four checks. **Do NOT report the results individually** — they flow into ONE line in the closing summary (Step 8). The user should not be the audience of a self-test. (The sync-location check in Step 2.4 is the deliberate exception: it can change where the folder lives, so it cannot wait for the summary.)

| Check | How | If it's missing |
|---|---|---|
| **Skills there?** | does `.claude/skills/morning/SKILL.md` exist? | **Critical.** The `.claude` folder is hidden and tends to get lost when copying/zipping. Say it plainly: _"A hidden part of the folder got lost during copying — without it the commands don't work. Please get a fresh copy (see VERSION.md) and copy it as a whole, not the individual files inside it."_ Then abort the setup — without skills everything else is pointless. |
| **Which OS?** | `uname -s` → `Darwin` = mac, `MINGW*/MSYS*` = windows | Don't guess. Controls the draft mechanics (PowerShell vs. AppleScript) and how the dashboard is opened — record it in Step 3 as `os:`. |
| **Mail/calendar connector?** | First find out what is connected at all: broad `ToolSearch query:mail` and `ToolSearch query:calendar`. With Microsoft 365 you get back `mcp__claude_ai_Microsoft_365__outlook_email_search` and `mcp__claude_ai_Microsoft_365__outlook_calendar_search`; with another provider take the tool names actually returned, never guess a name. | Not a blocker. **If the search finds nothing, ask ONCE: "Do you work with Microsoft 365 (Outlook) or with Google Workspace?"** (third option: something else). Remember the answer for Step 8, so the offer of help there names the right connector instead of staying generic. Don't keep digging if the user doesn't know: then it stays with the generic path. Remember for Step 8: the mail part is missing, the rest runs. |
| **Script runtime?** | `node --version` (the default), then `uv run python -c "print(1)"`, `python3`, `python` | Record the working variant in Step 3 as `script_command:`. **Nothing found is not a result you accept — Step 7.1 installs Node.** Only if that installation genuinely fails does the dashboard fall away, and then it is named in the summary. |
| **`claude` on the PATH?** | `command -v claude` | Needed for the plugins in Step 7.1. Missing → Step 7.1 installs it. Being inside Claude Code does not prove the command line is there. |
| **Draft path?** | `ToolSearch query:draft` — does the connected connector return a draft tool? (nothing found → try `ToolSearch query:create` as well) | **Yes → `mcp`** (platform- and provider-independent, best path). **No → OS default:** Windows `com` (assumes classic Outlook installed locally), Mac `mailto` (needs no permissions, no MDM risk, works with any mail program). Record it in Step 3 as `draft_method:`. Don't create test drafts — nothing may pop up in the mail program during setup. **Only the DRAFT tool counts:** if the connector also offers a send tool, it is NOT used and NOT mentioned — nothing is ever sent here. Note for Step 8: the first draft via MCP asks for permission once — click "always allow" once and it's quiet after that. |
| **Other MCPs connected?** | Broad `ToolSearch` queries (e.g. `query:people`, `query:transcript`, `query:search`) — what answers besides the mail connector? | Not a blocker, not mandatory. Remember for Step 8: ONE line _"Also connected: [names] — I can use those too, just say what you need."_ Nothing found → don't mention it. |
| **Sync duplicates?** | Files with ` 2.` in the name (`STATUS 2.md`) — OneDrive conflict copies | Remember for Step 8: _"OneDrive created duplicates while syncing ([names]) — I'll leave them alone, but delete them in Explorer, otherwise I'll read the wrong one at some point."_ Never delete them yourself (Safeguard 2). |

## Step 3: Write `context/config.yaml`

Fill every section of `context/config.yaml` from Step 0.5 + Step 1 + Step 2:

**Every section of the template stays in place** — only fill in values, never delete blocks (the skills read all of them):

- `language:` result from Step 0.5 (`en` or `de`) — controls everything the user sees from now on: briefings, dashboard text, mail drafts, entries written into `context/` files, chat.
- `user:` name, first_name (from the name), email, role
- `location:` office_abbreviation, office_room_patterns (the abbreviation plus "Office"), other_office_patterns (only if mentioned), office_days, timezone (default Europe/Berlin)
- `calendar:` `noise_subjects` stays empty (it fills up once the user notices calendar noise — mention it in the Step 8 summary)
- `mail:` leave unchanged (`tag_processed: true`, `processed_categories: ["AI-Triaged"]`) — only touch it if the user rejects the category tag in their mailbox. On Mac feel free to leave `tag_processed` on `true` — `/morning` skips the tag there by itself.
- `company_domains:` **derive it from the email address in Step 1** — enter the domain behind the `@`, e.g. `anna@examplecompany.com` → `["examplecompany.com"]`. NEVER leave the placeholder standing: the internal/external prioritization in the briefing depends on it. Only with private providers (gmail.com, web.de, outlook.com, gmx…) ask ONE short question instead: _"Do you have a company mail domain? Then I'll sort mail from colleagues and from outsiders differently."_ — no answer/no domain → `[]` (empty is honest, a placeholder is a silent error).
- `workspace_root:` Step 2's computed path
- `tools_in_use:` the answer from Step 1, question 5 — one entry per tool with `name` and `purpose` in the user's own words. **Write it down even for systems that never get connected**, because the reason matters later: a tool nobody could reach is a known gap, not a blank. `/checkup` and `/audit` read this instead of asking again.
- `plan:` the answer from Step 1, question 6 (`pro`, `max5`, `max20`, `team` or empty). Needed later when it comes to parallel sub-agents or large runs — whoever is on Pro should know BEFORE a five-agent run that it will eat their quota, not afterwards.
- `os:` result from Step 2.5 (`windows` or `mac`)
- `script_command:` result from Step 2.5 (`node`, `uv run python`, `python3` or `python`) — `/morning` uses exactly that for the dashboard fill. Leave empty if no runtime was found.
- `draft_method:` result from Step 2.5 (`mcp`, `com` or `mailto`) — `/email` and `/morning` use exactly that for mail drafts.
- `inventory:` **record only what Step 2.5 found here, don't guess.** The block is filled later by Steps 7.1 to 7.4, when the equipment is actually set up. Enter now what Step 2.5 really saw:
  - `inventory.connectors:` one entry per connector found, with `name`, `purpose` in plain language, `slot:` and `status: true`. A system the user only mentioned but that doesn't answer gets `status: false`. Step 7.2 adds to and corrects this.
  - `inventory.clis:` `firecrawl` and `playwright` with the result of their version command. Step 7.1 installs what's missing and updates this.
  - `inventory.accounts:` leave empty, Step 7.3 does that.
  - `inventory.repos:` Step 8 enters the workspace's own repo, Step 7.4 the project repos.
  - `inventory.plugins:` leave empty **now** — but not because nothing happens. **Step 7.1 installs the curated set**, and plugins are read live from the machine afterwards, so there is nothing to type in by hand. Do not conclude from this line that plugins are optional.
  - `inventory.routines:` stays empty. That is the one the setup really does not set up. In the closing summary (Step 8) ONE short question: _"Should something run on a schedule?"_ No answer stays empty; the empty state in the dashboard explains by itself how to add one later.
- **Permanently, not just during setup:** if something is added later (a connector, a plugin, a repo, a routine), it belongs in the `inventory` in `context/config.yaml` immediately, without the user having to ask. That's the same order-to-persist as with "from now on / always" (Safeguard 10): said once, anchored permanently, confirmed in one line.

No other file rewrites. If an answer is missing, leave the field empty — never invent a plausible value.

**No script runtime found (Step 2.5):** that is not an outcome, it is a task — **Step 7.1 installs Node.js.** Only if that installation genuinely fails does this become a summary line, under "not possible right now": *"Node.js wouldn't install, so there's no dashboard file — the briefing in the chat works, and we can fix this any time."* Then say what blocked it. Never write the dashboard HTML yourself (see CLAUDE.md).

## Step 3.5: Set the Main Model

The plan answer (Step 1, question 6) determines which model is written as the session default into `.claude/settings.json`. The shipped file deliberately contains **no** `model` — only this step sets it. Without an answer: `sonnet`.

**Pro (€20) → `sonnet`, no choice.** Opus burns through this plan's quota in one to two hours, after which the user is stuck until the reset. That's not a matter of taste, it's a limit, and limits are stated, not put to a vote. One line in plain language, then move on:

> *"On your plan I work briskly and economically, otherwise your quota is empty by lunchtime. For individual heavy tasks you can switch up any time in the chat."*

**Max or Team/Enterprise → offer the choice.** Two options, in their language, not in model names:

> Two ways of working. Which fits better?
>
> **a) Brisk and cheap** (recommended) — for briefings, mail, filing, the normal day.
> **b) Slower, but deeper** — if you analyze a lot, build concepts or think through large documents. Uses considerably more of your quota.
>
> You can switch this any time in the chat, even mid-work.

a → `sonnet`, b → `opus`, no answer → `sonnet`.

**Writing it:** add `"model": "<value>"` as the first field in `.claude/settings.json`. The file is JSON — insert only this field, leave the rest unchanged, then check it for validity once. If it's broken after the edit, permissions and hooks stop working.

**It stays a starting line, not a commitment.** The model check rule (CLAUDE.md, token economy) reports by itself in everyday use when task and model don't match. That's exactly why the question is defensible here at all: a wrong initial choice corrects itself in operation instead of costing money or quality for a year.

## Step 4: Fill In the Blank Context Templates

These ship blank with placeholder tokens (`[YOUR NAME]`, `[YYYY-MM-DD]`):

- **`context/PERSONAL.md`** — name, email, position, **area of expertise**, office + office days from Step 1 (no home location); leave the stakeholder table empty (it fills in as real projects/people show up).
- **`context/PROJECTS.md`** — ONE block per project from Step 1 #4 (Purpose/Status/Phase/Stakeholder/Timeline/Blocker — gaps honestly as `[open]`, never invented). **No to-dos here** — those belong in STATUS.md. Stamp "Last updated". **Writing rules (the template shows the example):** short, concrete sentences in the user's language — purpose = one sentence on why the project exists, the way you'd say it to a colleague ("The client suspects money is sitting in their pricing — we're checking where and how much"), never abstractions without the concrete thing behind them ("potential identification"). Status = what happened last + what's coming next. These blocks later feed the project cards in the dashboard — form-speak here becomes form-speak there.
- **`context/STATUS.md`** — this is where the first tasks land, but **not unasked and not all of them.** Two steps, no direct writing:
  1. **Filter yourself before you show anything.** From the answers, only what passes the Rule 4 intake filter comes along (CLAUDE.md): nothing under 15 minutes, no pure FYI chunks, no milestones/deadlines — **those belong as `Timeline:` in the project block in PROJECTS.md, not as a task** (a date is not work). What should be left: 1–3 real, concretely actionable next steps per project.
  2. **Show the proposal, only write after the OK** (same principle as /ingest — otherwise on day one the user experiences the system writing things into the system behind their back):

     > "From what you've told me, I'd create these tasks:
     > - **[Project]:** [headline] — [one sentence on why it's due]
     > - …
     > Does that fit — anything to drop, anything missing?"

     Work in corrections, then write: headline + indented context line + `#category` (format: STATUS.md header). **The context line is mandatory and must be understandable without you** — in two weeks the user only reads it in the dashboard expander; a task like "finalize segmentation" without the why is worthless by then.
  **Less is more here:** the list fills itself from tomorrow on (mail findings, chat). A setup that starts with 15 tasks teaches the user to ignore the list from day one — exactly what must not happen. **Without this step (with the proposal), the first `/morning` shows zero tasks** — after a setup in which the user named all their projects. Day Plan/Inbox/Recently Done stay empty (correct). Stamp "Last updated" with today's date — that also replaces the `[YYYY-MM-DD]` marker that Step 0 checks as the "not yet filled" signal.
- **`context/JOURNAL.md`** — stamp today's date, one entry "Workspace set up" with the projects created.

## Step 5: Scaffold Their Projects

Create `projects/<slug>/README.md` from `projects/_template/README.md` for EVERY project from Step 1 #4, filled in with what's known so far.

## Step 6: Collect + File Existing Documents

Ask: *"Do you have documents on these projects that I should file — project plans, meeting notes, decks, org charts? Drop them into the `inbox/` folder (or paste them here), I'll sort them in."*

- For each provided document, run the **`/ingest` flow** (that skill's preview + OK loop applies): extract decisions/actions/stakeholders/facts → update the matching project's PROJECTS.md block + `projects/<name>/README.md` → **the filing is done by the `/ingest` flow according to its own rule table** (project material → `projects/<slug>/inputs/`, only homeless things → `inbox/processed/`). **Don't prescribe your own destination here** — what the user brings along during setup is almost always project material, and that's exactly what `/ingest` looks for in `inputs/` later.
- **A whole folder instead of loose documents** — "my old workspace is on the desktop", a case folder, a notes folder with its own logic: that is `/ingest`'s **folder mode**, use it as written there instead of improvising a survey. The rules that matter here: file by content, never mirror the foreign structure, and leave code/data folders where they are. Everything else in this step stays the same.
- Reference material that isn't project state (guides, standards, org charts) → `reference/` instead of ingest, briefly say where it is.
- Delegate bulk extraction of large documents (transcripts, long PDFs) to a **Haiku sub-agent** (structured return), the filing judgment stays here.
- Nothing provided → skip, remind in the summary that `/ingest` files documents any time.

After this step PROJECTS.md should reflect the person's real current workload — that's the bar for "setup done".

## Step 7: Derive the Personal Mail Style (a regular step, needs permission)

**This step is part of the setup, not an extra.** It is the difference between drafts that sound like the user and drafts that sound like the package author. It may be declined (permission for the mailbox is always the user's call), but it is **never quietly passed over**: whatever the outcome, it appears in the Step 8 summary in one line, so nobody discovers three weeks later that their drafts read like a stranger and never learns why.

**Pre-check:** if Step 2.5 found NO mail connector → don't ask (the fetch would fail anyway), and say so plainly in the Step 8 summary: the style is not derived yet, it takes two minutes as soon as the connection is in place, and the sentence for it is "derive my mail style from my sent mail".

Ask ONE question: *"Should I go through your sent mail from the last few months once and derive your writing style? Then all mail drafts (/email, /morning) sound like you from the start. (Read only, nothing gets sent.)"*

- **Yes:**
  1. Delegate the fetch to a **Haiku sub-agent** (self-contained prompt — it must load the mail search tool determined in Step 2.5 via `ToolSearch` FIRST, sub-agents don't inherit tools; with Microsoft 365 that is `ToolSearch select:mcp__claude_ai_Microsoft_365__outlook_email_search`): search with it **by naming the sent FOLDER** — Microsoft 365 `folderName="Sent Items"` (German mailbox: "Gesendete Elemente"), Google Workspace `query="in:sent"` —, last ~6 months, limit ~50; fetch full bodies; return 15–25 representative excerpts (openers, closers, sign-offs, one-liners), grouped DE/EN, skipping sensitive threads (HR/salary/performance).
     > **Not `sender = user.email`** (verified 2026-07-21 against a real Microsoft 365 mailbox): the mail search covers the inbox only, so a sender filter returns zero of the user's own mail and the derivation would silently produce nothing. Same trap as `/morning` Step 3a. **If the fetch comes back empty, say so** and fall back to the package's example style — never write an EMAIL_STYLE.md derived from nothing.
  2. From the excerpts, derive (main model, judgment work): typical openers, formal vs. informal address, tone markers, typical length, closers + signature block, DE vs EN habits, filler phrases the user never uses.
  3. Write the profile to **`context/EMAIL_STYLE.md`** (structure mirrors `/email`'s Style Reference section). `/email` and `/morning` read this file first and fall back to their built-in example templates only if it doesn't exist.
  4. Show the derived profile in 5–8 bullets and ask for a quick sanity-check ("does that fit?") — apply corrections directly to EMAIL_STYLE.md.
- **No / too little history:** accept it without pushing, but **do not pass over it silently** — one line in the Step 8 summary: drafts use the package's example style for now, and the sentence "derive my mail style from my sent mail" starts the same flow any time.

## Steps 7.1–7.4: The Equipment (the part that otherwise never happens)

These four steps run **before** the archiving, because afterwards there is no guided path any more. They are the difference between "set up" and "ready to work".

**One rule applies in all four of them, without exception:** commands that require an input or a login (`gh auth login`, `firecrawl login`, any OAuth flow) **hang in your Bash** — there is no terminal there that could answer them. NEVER run such commands yourself. Instead: give the user the line to paste, say what happens afterwards, and wait for their response. Everything non-interactive (`npm install -g`, `command -v`, `git clone` on public repos) you do yourself.

**Tone in all four:** ONE question per step, plain language, no technical term without an explanation. A "no" is always a complete answer and is never renegotiated. Whatever the user declines is written into the `inventory` with `status: false` — not left out, otherwise it never shows up anywhere later as a possibility.

### Step 7.1: Install the Tools

**Playwright first**, deliberately: once it's there, you can open interfaces yourself in the following steps instead of describing from memory where the user should click.

```bash
npm install -g playwright firecrawl-cli
playwright install chromium
```

Non-interactive, so you do it yourself. If the installation fails on permissions: **never suggest `sudo`**, point at the issue tracker in `VERSION.md` instead.

#### Before that: the two things everything else stands on

Check both first. Neither is optional, and neither gets waved away with "it works without it".

**1. Node.js.** Without it there is no dashboard, no inventory, no audit, no adopt plan — a third of the package. `node --version` says whether it's there. Missing → install it, don't just mention it:

```bash
# Mac
brew install node
# Windows
winget install OpenJS.NodeJS.LTS
```

No Homebrew on the Mac? Then that first (`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`), and say in one sentence what it is: the tool that installs other tools on a Mac. If the installation genuinely fails, that is the one case where the package really runs reduced — then it goes into the closing summary under "not possible right now", with what it would have unlocked. Never silently.

**2. The `claude` command line.** Step 7.1 installs plugins with `claude plugin …`, and that only works if `claude` is on the PATH — being inside Claude Code is not proof of it. Check `command -v claude`. Missing → `npm install -g @anthropic-ai/claude-code`, then check again.

Only once both answer do the two CLIs and the plugins below make sense.

### How things get installed here: announce, ask per group, then do it yourself

**Three rules, and they hold for every install in this step.**

**Nothing is installed silently.** Before anything lands on their machine, they hear what it is and what it does for them — in one sentence, in plain language, without the tool's name doing the explaining. Someone whose laptop quietly grows six new things has learned that this system does things behind their back, and that is the opposite of what it is for.

**One question per group, not per tool.** Six questions in a row is a wall, and a wall gets answered with "yes, yes, yes" — which is not consent, it is surrender. So: the web-and-browser tools are ONE question, the working tool set is ONE question, memory across sessions is ONE question. Each with what it does and what it costs them (usually: nothing, a minute).

**After a yes, you do it — all of it.** No list to work through, no "run this command", no dashboard for them to click through. The choice is theirs, the work is yours. That difference is the whole product: whoever hands the list back has given them exactly the job they were meant to be spared.

A no is a complete answer, gets recorded in `inventory` with `status: false`, and is never renegotiated. It goes into the closing summary as one line under "not set up, available any time" — a no means "not now", never "you never learn this exists".

**Prerequisites are the exception, and only they:** Node.js and the `claude` command line are not a choice, because without them a third of the package does not exist. Those get announced in one sentence and installed, not asked about.

**Group: the working tool set (six plugins).** ONE question, roughly like this — then install all six:

> *"There's a set of tools that make me noticeably better at the work you'll actually give me: building your own commands, reviewing code, keeping things simple instead of over-built, design feedback, and tidying up these rules once they grow. Costs nothing, takes a minute. Shall I set them up?"*

On a yes:

```bash
claude plugin marketplace add DietrichGebert/ponytail
claude plugin marketplace add pbakaus/impeccable

claude plugin install claude-code-setup@claude-plugins-official
claude plugin install code-review@claude-plugins-official
claude plugin install claude-md-management@claude-plugins-official
claude plugin install superpowers@claude-plugins-official
claude plugin install ponytail@ponytail
claude plugin install impeccable@impeccable
```

**Why the setup does this instead of recommending it:** new plugins appear almost daily, and telling this week's real thing from the noise is a job of its own. That selection is the actual product here. Handing the user a list to install themselves gives them back exactly the work they were meant to be spared. What each one is for: `reference/plugins.md`.

**One of them gets a sentence before it is installed, and only one.** `claude-mem` remembers across sessions and makes it searchable — genuinely useful. It also brings a **daemon** (a program that keeps running in the background, with no window) and a database of its own, and it logs the project content it reads into that database. Say that in one sentence and install it only on a yes:

> *"One more: claude-mem remembers things across sessions, so you don't have to repeat yourself in a new chat. Two things about it: it runs quietly in the background all the time, and it writes down what it reads — including client documents — into its own local file. Want it?"*

```bash
claude plugin marketplace add thedotmack/claude-mem
claude plugin install claude-mem@thedotmack
```

A no here is a full answer and costs nothing else; everything in the system works without it. **Not asking would be the mistake** — anyone working with client data has to be able to make that call themselves.

**One skill comes from outside the package, and it gets its own question.** `/last30days` researches what people have actually been saying about a topic in the last thirty days, across Reddit, X and the web, and hands back the findings plus ready-to-use prompts. It is the answer to "what is the state of X right now", where the model's own knowledge stops at its cutoff and a normal web search returns marketing pages. Two things belong in the same breath, because both cost the user something later: it is **not ours** (it lives in its own public repo and is installed from there, so it changes on its own schedule, not with our releases), and it runs on **two API keys of their own**, billed per search. Ask, then install on a yes:

> *"There is one more, and this one is not from us. It looks up what people have actually been saying about a topic in the last month, on Reddit and X, instead of what a search engine wants to show you. Good for 'is this tool any good' and 'what changed recently'. It needs two of your own API keys and costs a few cents per search. Want it?"*

**It ships with the package** — nothing to install, the skill is already here (`reference/vendor-skills.md` says where it came from and how it gets updated). Two things are missing: **Python 3.12 or newer** (the other scripts here run on older versions, this one does not) and the two keys from step 7.3. Without them the skill is installed and simply says so when it is called, so a yes here commits them to nothing. A no is a full answer and goes into the summary under "not set up, available any time".

**Three more exist but install differently**, so they stay a one-liner in the summary rather than a step: `codeburn` needs no installation at all (`npx codeburn` shows what the usage costs), `find-skills` comes through the skill registry (`npx skills add vercel-labs/skills --skill find-skills`), and `herdr` (`brew install herdr`) keeps a long-running job alive when the laptop closes. **Do not install herdr on spec.** Most work here is over in seconds, and anything that should run without a person in front of it belongs in `/schedule`, which is already built in. It is worth a sentence in the summary so they know it exists on the day a job actually runs for hours.

If an install fails (marketplace unreachable, no network): name which one is missing and what it would have done, then carry on. The system runs without every single one of them.

Check the result per tool with `<name> --version` and write it into `inventory.clis`. Plugins are read live from the machine, so nothing has to be written into `inventory.plugins` by hand. The bundled skills (`playwright-cli`, the `firecrawl-*` family) are already in the package, there's nothing to download — ONE sentence in the summary that they're there.

### Step 7.2: Connect the Systems They Named

Connections to mail, calendar and the rest run via **Claude Cowork → Settings → Connectors**. The package brings no connection of its own; Claude Code accesses the same connection. Details and categories: `reference/mcp.md`.

**Start from `tools_in_use` (Step 1, question 5), not from the six slots.** The user already told you what they work with and what for. Map those names onto the slots yourself and say what you found, in their words:

> *"You said Outlook for mail, HubSpot for customers and WhatsApp for enquiries. Mail and calendar I can connect right now. For HubSpot there is a connector too, I'll show you. WhatsApp there is no way into, so that one stays by hand."*

That sentence does two jobs: it proves you listened, and it turns six abstract questions into a short list of concrete steps. Only slots that **nothing** in `tools_in_use` maps to still get asked — in one sentence each, so CRM and chat do not stay empty forever just because they never came up.

Then connect **only what the user says yes to**. Not on spec, that would contradict `reference/mcp.md`.

**Never end at "there is no connector".** The route out is in `reference/mcp.md` under "If your system is not in the catalogue", and it is short: catalogue first, then the system's own MCP server added directly in Claude Code, and only then the honest no. **You run the command, the user only fetches the token** — and you open that settings page for them with Playwright from Step 7.1 instead of describing where to click. A system that stays disconnected because the easy path was missing is the single most expensive outcome of this step: it is exactly the daily tab-switch the whole folder exists to remove.

The one thing that must not happen is guessing a route. Check that it exists before you offer it — the catalogue moves fast in both directions.

| Slot | How you handle it |
|---|---|
| `mail` + `calendar` | **Not optional.** Without them `/morning` is an empty shell. Don't ask whether, ask which system: Microsoft 365 or Google Workspace. From Step 2.5 you often already know what's there. |
| `storage` | Ask. With Microsoft 365, SharePoint/OneDrive usually comes along, then it's one checkbox. |
| `chat` | Ask. Teams with Microsoft 365, otherwise Slack. The benefit in half a sentence: reading along with messages that would otherwise get lost. |
| `crm` | Ask — **with the honest limitation from `reference/mcp.md`** that `/morning` does not pull CRM data into the briefing today. The benefit is targeted look-ups during a conversation, not the briefing. That belongs said before anyone connects. |
| `dev` | Only bring it up if Step 7.3 produced a "yes". Otherwise skip it, without comment. |

Per slot the user says yes to: guide them through Cowork (Settings → Connectors → select the system → sign in with the work account). The sign-in is done by **them**, in the browser. Afterwards **verify via ToolSearch** whether the tools are there now — that's the reliable proof, not their self-report and not a look in the browser either. Only then write it into `inventory.connectors`, with `slot:`.

If it doesn't work after two attempts: don't get stuck on it. Note it with `status: false`, say what still works without this connection, and move on. The rest of the setup must not fail over it.

### Step 7.3: Accounts and Keys

Keys never belong **in the repo** (it gets cloned and versioned; a key checked in once stays in the history). They all live in `~/.config/credentials.env`, permissions `600`.

**You always offer two accounts**, because the tools from 7.1 are half dead without them:

- **Firecrawl** — without a key the tool can't read web pages. Their own account on firecrawl.dev, the free entry tier is enough to try it out. The account belongs to **them**, not to the service provider: that way billing and usage sit with them, and nobody shares a limit.
- **OpenRouter** — needed for images and for models that don't come from Anthropic. Without it, the system says honestly on "make me an image" that it lacks the access.

**Don't offer this by yourself, only on request:** an **Anthropic API key**. That is needed exclusively by the `managed-agents` skill (your own agents that run permanently in the cloud). Important and honest to say when it comes up: **that is a second invoice next to the subscription** and is billed per use. Everyday work never needs it — everything this system does runs through the subscription. Scheduled routines (`/schedule`) incidentally do **not** need it, they run through the subscription access.

**Only if they said yes to `/last30days` in 7.1:** it needs two keys of their own, `OPENAI_API_KEY` (that one searches Reddit) and `XAI_API_KEY` (that one searches X). Both are billed per use and are **a separate invoice from the Claude subscription** — say that before they sign up, not after. **These two do not go into `credentials.env`**, the skill reads its own file:

```bash
mkdir -p ~/.config/last30days && touch ~/.config/last30days/.env && chmod 600 ~/.config/last30days/.env
echo 'OPENAI_API_KEY=<their-key>' >> ~/.config/last30days/.env
```

One key alone already works: with only one of the two, the skill searches only that source and says so. Neither key → it is installed and reports honestly that it lacks access.

**One more question — you ask it, you never answer it for them:** _"Do you also build applications, or do you work with databases?"_

**Never infer the answer from anything they said earlier.** Someone who described themselves as a consultant in Step 1 may still run a website with a database. Guessing "no" here is how Supabase and Vercel silently disappear from a setup without the person ever learning they exist.

- **Yes** → walk them through **Supabase** (database) and **Vercel** (publishing). Both skills are in the package. Afterwards catch up slot `dev` in 7.2.
- **No** → nothing gets installed, and that is a full answer. But it goes into the closing summary as ONE line under "not set up, available any time": _"Supabase and Vercel (databases and publishing your own pages) — say the word if that ever comes up."_ A no means "not now", never "you never learn this exists".

Setting one up always works the same way: open the sign-up page (with Playwright from 7.1 you can open it for them directly), they register and generate the key, then **you** append it:

```bash
mkdir -p ~/.config && touch ~/.config/credentials.env && chmod 600 ~/.config/credentials.env
echo 'FIRECRAWL_API_KEY=<their-key>' >> ~/.config/credentials.env
```

Write every account you set up into `inventory.accounts` (`name`, `purpose`, `key_env`). **Never write the key value into the chat, never into a file in the repo, never repeat it.** Don't type `status`, derive it from the existence of the entry in `credentials.env`.

### Step 7.4: Connect Project Repos

If one of the projects from Step 5 has a Git repo (product code, website, company repo), it is cloned **into the project**, not mixed into the workspace:

```bash
git clone <repo-url> projects/<slug>/code
```

That way Claude sees both in one session: the project context and the real code. The histories stay separate, `.gitignore` excludes `projects/*/code/` — so the end-of-day never commits someone else's code into the private workspace repo. Full reasoning: `projects/README.md`.

If the repo is private, it needs a login you can't perform → give them the line, let them do it. Afterwards enter it in `inventory.repos` (`name`, `url`, `path`).

Ask **at most once** per project, and only where it's plausible. For a project called "quarterly close", don't ask about a repo.

## Step 7.5: The acquisition channel (optional, and genuinely optional)

Everything up to here is the workspace: the day, the projects, the files. This repo also
carries an Upwork pipeline, and it is a **channel, not the core**. Someone whose clients come
from referrals or direct outreach never needs it.

So ask once, plainly, and accept either answer:

> _"One more thing. This workspace has a full Upwork pipeline built in: it searches and scores
> jobs against your own niche, writes the proposals, and tracks what you sent. Do you work on
> Upwork?"_

**If yes** → hand straight over to the `setup-freelancer-os` skill. Do not make them find it
themselves and do not describe it and stop; call it. It verifies the connector, reads what
their account already knows, and writes `expertise.md` and `experience.md`. Say one sentence
about what happens next so the handover does not feel like a cut.

**If no** → say so and be done, in one sentence: _"Then we leave that out. The Upwork tab in
your dashboard stays empty, and nothing else here needs it."_ Then:

- Write `upwork_enabled: false` into `context/config.yaml`
- **Do not ask again.** No hint at the next start, no nudge in the briefing, no note in the
  dashboard. A person who said no has answered.
- `morning` skips its Upwork pass on that flag alone; the day loop is unaffected.

**If unsure ("maybe later")** → treat it as no, and say the one sentence that makes it
reversible: _"Say 'set up upwork' whenever you want it."_ One sentence, once, never repeated.

## Step 8: Archive This Skill + Confirm

1. Move `.claude/skills/setup/` to `.claude/skills-deprecated/setup/` (its job is done — archival pattern, not deletion).
2. **Create their own repo** — only if the workspace is a Git clone (`git rev-parse --is-inside-work-tree`) AND `gh auth status` reports a login. If either is missing: skip silently, not a word about it (`/eod` then skips its backup as well).

   **Why this is not optional:** the cloned folder still points at the repo of whoever sent the package. Without this step, `/eod` pushes the user's work there every evening — or fails every evening. Both only surface after days.

   ONE question, in plain language: _"I'll create your own private repo on GitHub. That's your daily backup, it belongs to you, and none of it is public. Shall I?"_ If yes:

   ```bash
   git remote rename origin upstream
   gh repo create <foldername> --private --source=. --remote=origin --push
   ```

   `gh` creates the repo under the **user's logged-in account** — they own it from the start, there is no transfer. `upstream` stays in place as the source, updates come through it later (`git pull upstream main`).

   **Do not offer anyone else access to it.** The package used to ask here whether a
   contact person should be added as a collaborator, which made sense when it was
   handed over by a consultant. This repo has no such person: it is theirs alone, and
   everything that accumulates in it over time — projects, notes, mail summaries — is
   nobody else's to read. If they later want help from someone, adding a collaborator
   is their call to make, in GitHub, not a question the setup asks.

   Enter the created repo in `context/config.yaml → inventory.repos`. If a command fails: don't dramatize it, ONE sentence in the summary plus an offer of help — the workspace runs fully without a repo, only the backup is missing.
3. Output a summary: what was written to config.yaml, what was filled in (context/ files), which projects were scaffolded, which documents were filed, whether EMAIL_STYLE.md was derived (Step 7), plus these follow-ups.

   **First, the equipment balance — three columns, nothing left out.** This is what makes a complete run distinguishable from a run that quietly lost half its steps. Every item from Steps 7.1 to 7.4 appears in exactly one column:

   > **Set up:** playwright, firecrawl, the 6 plugins, mailbox, calendar …
   > **You said no:** claude-mem (remembers across sessions), test draft …
   > **Not possible right now:** Node.js missing, so no dashboard file — here is what would fix it …

   Read the real state, do not write it from memory: `claude plugin list` for the plugins, `<name> --version` for the CLIs, `inventory.connectors` for the connections. **On plugins, only `Status: ✔ enabled` counts.** `claude plugin list` shows installed AND switched-off ones, and a disabled plugin does nothing while looking present. Measured on a real machine (23.07.): three of seven were silently off for weeks — the balance had shown seven ticks for four working plugins. Anything `✘ disabled` goes into the summary as such, with the line that fixes it: `claude plugin enable <name>@<marketplace>`. **If a line cannot be filled because the step never ran, that is not a gap in the summary — it is a step you skipped, and you go back and do it now.**
   - **`/email` style — this line is mandatory, in every outcome.** Derived → say so with the date. Declined, no history, or no mail connector → say that drafts use the package's example style for now, name the reason in half a sentence, and give the sentence that starts it later ("derive my mail style from my sent mail"). Never leave it out: an undiscovered gap here means weeks of drafts that don't sound like the user.
   - **Calendar noise:** put recurring private calendar blocks (gym, study slots, …) into `config.yaml → calendar.noise_subjects` so briefings ignore them.
   - **Dictate instead of typing (ONE sentence, friendly):** the system lives off being told things — dictating status updates is faster than typing. Windows: `Win + H` starts native dictation in any text field, including the Claude Code window. Mac: enable dictation under System Settings → Keyboard, after that pressing `Ctrl` twice starts the microphone.
4. **System-check line (Step 2.5), ONE line, friendly:**
   - All green → _"Everything's ready."_ Nothing more — no checkmark report about things that work.
   - Something missing → what's missing, what works anyway, and a CONCRETE offer of help — never just a pointer to someone else. Mail pattern, **with the system named in Step 2.5 concretely filled in** (Microsoft 365 or Google Workspace) instead of staying generic: _"I can't find a mail connection yet — tasks, projects and dashboard still work, only the mail part of the briefing is missing. You can set it up in Claude Cowork: Settings → Connectors → connect <the named system> with your work account; I'll then use that same connection. Say 'check the mail connection again' once you've done it — or 'help me with it' and we'll go through it step by step."_ If the user takes the offer: walk them through the setup, then test the connection again via ToolSearch and confirm the result in one sentence. (Which connectors exist and what they're allowed to do: `reference/mcp.md`.)
5. **First dashboard render — this happens, it is not conditional.** Step 7.1 made sure Node is there, so `script_command` exists; if it does not, go back and finish 7.1 instead of skipping this. **Then open it and walk them through it in two sentences, starting with the Start Here tab** — that page is the entire onboarding, and someone who never sees it on day one never finds it. _"That's your dashboard. The first tab, Start Here, is your map — everything else fills up as you work."_ Render the dashboard once from the fresh data — following `reference/dashboard-render.md` (the render contract; do NOT load the `/morning` skill for this, it costs a multiple), with `mail_checked: false` (mail fields honestly empty, calendar starting tomorrow) — and open it. **Write `context/.mail_cache.json` with today's date and `mail_checked: false` while you are at it.** Without that stamp every mid-day update for the rest of the first day silently skips (the render contract refuses to render without a cache from today), and the dashboard the user was just shown freezes at the moment they start working. Two birds: the user immediately sees a visible success ("that's your dashboard, from tomorrow it'll be filled"), and the render path is proven on THIS machine while you're still sitting next to them. If it fails: don't dramatize — one sentence in the summary (the briefing in the chat still works) + offer of help.
6. **Opt-in test draft (only if a `draft_method` is available):** ONE question: _"Should I open a test draft to yourself, so you can see what that looks like later?"_ If yes: a short welcome draft to `user.email` (subject something like "Your workspace is set up ✓", 2–3 sentences), via the `draft_method` from the config — that's the end-to-end proof of the draft path; if it fails, it fails HERE and gets fixed right away, not alone on the first morning. If no: skip without comment. The principle stands: drafts never pop up unasked — this one is explicitly invited, goes only to the user themselves, and nothing is ever sent.
7. **The mini-briefing — how daily life works from now on.** Output it directly in the chat (this is the moment the user is guaranteed to read — they'll never open a documentation file). Exactly these five lines, no more:

   > **How you use this from now on:**
   > - **In the morning:** say "good morning" — I'll pull calendar and mail, brief you and build your dashboard.
   > - **During the day:** just tell me what's up — "chapter 3 is done", "waiting on IT". I'll file it in the right place.
   > - **Documents:** drop them into the `inbox/` folder and say "read this in".
   > - **In the evening:** say "end of day" — two minutes to close out.
   >
   > You don't have to memorize commands — write what you want in your own words.

   Then ONE pointer sentence: "There's more in `ONBOARDING.md` and in the Start Here tab of your dashboard — but the above is all you need." Suggest `/morning` as the first real run (tomorrow morning or right now).
8. **Point at `WHAT-THIS-SYSTEM-DOES.md` once** — one sentence: _"What the system reads and what it never does (send, change appointments, touch HR topics) is in `WHAT-THIS-SYSTEM-DOES.md` — that page is also the answer if anyone asks whether you're allowed to use this."_ Don't walk through it, just show that it exists.

## Quality Guidelines

- **No silent fabrication:** if an answer leaves a gap, say so in the summary — don't invent a plausible default.
- **Re-runs ask first:** never overwrite an already-personalized config silently.
- **One language, from the first answer on:** once Step 0.5 is answered, nothing the user sees switches back. If you catch yourself writing a proposal, a summary or a briefing line in the other language, rewrite it before sending.

## Test Drive

1. First session in a fresh copy → CLAUDE.md's first-run rule triggers this skill automatically, straight to the Step 0.5 language line — one bilingual line, nothing else.
1b. Answer "Deutsch" → everything from the greeting on is German: the six questions, the model question, the task proposal, the closing mini-briefing. Answer with enter/"English" → everything is English. `context/config.yaml` carries `language: "de"` resp. `"en"` at the top.
2. Answer the questions → config.yaml written, context files filled, every named project scaffolded. **Tasks do NOT appear in STATUS.md immediately** — first comes the proposal in the chat (1–3 real actions per project, milestones as `Timeline:` in PROJECTS.md), only after the OK is anything written, every task with a self-explanatory context line.
3. Grep `context/` for `[YOUR NAME]` → zero hits. **Only `context/`**: the documentation and the skills quote the placeholder as text (`CLAUDE.md`, `reference/self-test.md`, `email/SKILL.md`), so a workspace-wide grep fails on a perfectly good run and makes the acceptance test lie.
4. `context/PROJECTS.md` shows exactly the new user's real projects, dated today; ingested documents are reflected there and filed in the owning project's `projects/<slug>/inputs/` (only project-less material lands in `inbox/processed/`).
5. `.claude/skills/setup/` no longer exists; `.claude/skills-deprecated/setup/` does.
5b. `git remote -v` shows **`origin` pointing at the user's repo** and `upstream` at the source — never the other way round. The first push is through, `gh repo view` reports `private`. If the user said no to access, nobody but them is listed under Collaborators.
5c. **Equipment (Steps 7.1–7.4):** `inventory.clis` mirrors what `command -v` really finds. Every system the user named in question 5 is in `inventory.connectors`, with `status: true` or `status: false` and a `slot:`. Slots nobody named and nobody asked about are legitimately absent — the check is "nothing the user mentioned got lost", not "all six appear". No key value is in the chat or in a file in the repo; `~/.config/credentials.env` has permissions `600`. If a project repo was cloned, it sits under `projects/<slug>/code/` and `git status` in the workspace does NOT show it as pending commit.
6. Run `/setup` again → Step 0 detects the real name in config.yaml and asks before doing anything.
7. If a script runtime was found, a rendered `context/today.html` exists at the end (without the mail part); if a `draft_method` is available and the user said yes, a test draft to their own address is waiting — never sent, never to anyone else.
