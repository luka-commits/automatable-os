# Onboarding: from a fresh clone to a working day

The path through the system, end to end. It was written before the last third of it existed,
with every missing piece marked as a gap so the shape could be judged before it was built.
**All of them are built now**, which is why this reads as a description rather than a plan.

Where something still cannot be done, it says so in place — the Upwork message thread that
cannot be exported, the profile fields the API refuses to write. Those are limits, not gaps.

**Two layers, and this file covers both.** The base runs your day: the briefing, your
projects, the dashboard, mail drafts. The Upwork add-on sits on top of it and turns Upwork from
a place you check into a pipeline that runs, but you can switch it off during setup and lose
nothing else. Phase 4 below is the add-on; the rest is the base.

Either way the pipeline only counts as finished when a won job has become a project you are
actually delivering.

**Getting in the door is [`SETUP.md`](SETUP.md)**, which covers the terminal, VS Code and the
desktop app. If you would rather see it than read it, each layer has its own page:
[`WHAT-WORKS-BASE.html`](WHAT-WORKS-BASE.html) and
[`WHAT-WORKS-UPWORK.html`](WHAT-WORKS-UPWORK.html).

---

## Part 1 — First run, once

**The principle: read first, then ask what reading cannot answer.** Most of what this system
needs to know about you is already on Upwork, in an account we are connected to by step 2. An
interview that asks for it anyway is slower, and it gets worse answers — people describe their
own niche in generalities, while their last twelve contracts describe it exactly.

Four steps, in this order, because each one needs what the previous produced. The order is
enforced by the session-start hooks rather than by you remembering it.

### What gets read, and what it produces

Measured against a real account, all of it available once the connector answers:

| Call | What it gives | What it fills |
|---|---|---|
| `get_profile action=get` | title, full overview, skills, rate, employment, education, `profileAggregates` (lifetime earnings, job count, feedback count) | your track-record numbers, no guessing and no inflation |
| `list_contracts action=search` | every past contract: title, type, status, feedback score both ways | what you actually get hired for, and what went well |
| `list_freelancer_proposals` → `action=get` | **the complete cover-letter text of every proposal you have sent** | your voice, in exactly the genre this system writes in |
| `find_jobs action=get` on won jobs | the postings behind your wins | the wording clients use for what you do |

**Your own past proposals are the single most valuable input, and nobody has to type them.**
They are your writing, in the right register, on the right platform, already approved by you
once. From twenty of them the system can read how you open, whether you link a video, how you
handle price, how you close — and then write in that shape instead of a generic one.

**What reading cannot answer, and must be asked:**

- **What you want more of.** The past says what you have done, not what you want next. A
  freelancer moving from web work into automation has a history that points backwards.
- **What to turn down.** The regrets — the job that looked right and wasn't. Partly derivable
  (a contract with a low feedback score, a proposal you withdrew) but the reason behind it is
  yours alone, and the reason is what makes the rule reusable.
- **Name, language, Slack.** Small, and no API knows them.

**One thing genuinely cannot be fetched:** client review *texts*. The profile response carries
feedback scores but not the words. If you want testimonials on a pitch page, they get pasted
in by hand — measured, not assumed.

### How the interview should feel

Not an interrogation. The system reads first, then puts what it found in front of you:

> "I read your profile, twelve contracts and twenty proposals. You look like a GoHighLevel and
> automation specialist for local service businesses — lead routing, CRM setup, follow-up
> workflows. Average accepted rate around $X. You almost always open with a Loom link and a
> flowchart. Two questions: is that still what you want more of, and what have you taken that
> you'd turn down today?"

Two questions instead of twelve, and both are ones only the person can answer. Everything else
is confirmed or corrected, which takes seconds and produces better files than a blank form.

This is what `setup-automatable-os` does in its Step 2, before a single question. When the
connector never answers, it falls back to asking — and says so, rather than running the
interview silently as though it were the plan.

### 1. The workspace is yours

`setup` — language, your name, how you want to be addressed, which folders you need. It
writes `context/`, creates the project folders, then archives itself so it never runs twice.

### 2. Upwork is connected

`setup-automatable-os` — verifies the Upwork connector answers, fetches your `org_uid`, and
writes it to `context/config.yaml`. **If the connector is missing, this is where it stops**,
because nothing downstream works without it and a half-connected setup is worse than an
honest failure.

**This is where most first runs stall, so the short version up front.** Connect Upwork in the
Claude app — <https://claude.ai/directory/connectors/upwork>, or Customize → Connectors → Add
→ Browse connectors → Upwork → Connect. That connection belongs to your account rather than to
one program, so it is there in the app and in Claude Code, terminal and VS Code alike. **Then
restart the session**, because a connection made mid-session is invisible to that session, and
that one step is behind most of the "it says it isn't connected" reports.

The second route (`claude mcp add`), the two cases where the connector button is blocked, and
the VS Code trap that looks exactly like success are in
[`reference/mcp.md`](reference/mcp.md) § Upwork.

**The two do not race, and the handover between them is what makes it a chain.** While step 1
is still pending, `check-setup.sh` has the floor and the second hook stays silent — two voices
on one topic and the user stops hearing the second. Once `setup` has archived itself,
`setup-check.py` takes over and names step 2 by the thing it is missing: no
`context/expertise.md` means the screener, the proposals and the pitch pages have nothing to
read.

**Three answers, not two.** "I work on Upwork" reads the account; "I do not" switches the
layer off for good; **"I want to start"** is its own path, because there is no account to
read yet and the profile becomes the first thing you build rather than something audited.
A plain yes/no question loses that third person, who answers no truthfully and then never
hears about it again.

**Unless you said you do not work on Upwork.** With `upwork_enabled: false` in your config,
this handover never fires and never nags. Optional means optional, and that includes the
acquisition half of the system.

### 3. Your profile can carry an application

`upwork-profile` — two starting points, one process. **A profile that exists** gets audited:
title, overview, skills, rate, portfolio, video, each finding with what it costs you and
finished text to paste in. **No profile yet** and it walks you through creating one.

This comes before the first search on purpose. The profile decides whether you appear in
results at all and is the first thing a client opens after your cover letter — applying
around a weak profile makes every proposal more expensive than it needs to be.

The audit is honest about what it can and cannot change: `update_profile` writes availability,
employment, languages and education, and **nothing else**. Title, overview, skills, rate,
portfolio and video — the set that actually decides whether invitations arrive — have to be
pasted in by hand. So the skill hands over finished text rather than promising a change the
API cannot make.

### 4. The system knows what you do

Back in `setup-automatable-os`: the niche interview fills `context/expertise.md` (search
tracks, what a strong match looks like, at least one real false-positive trap) and
`context/experience.md` (track record, notable projects, anything a client said about you).

These two files are what makes the screener yours rather than generic. **They are also the
files that stay empty if the interview is rushed** — and an empty `expertise.md` produces a
screener that scores everything alike.

**At the end of first run, these exist:** `config.yaml` · `expertise.md` · `experience.md` ·
`testimonials.json` (or an honest empty one) · `STATUS.md` · a rendered dashboard.

---

## Part 2 — The day

**Morning.** `morning` briefs you: calendar, mail, tasks, then the Upwork pass — new scored
jobs, anything a client wrote, and the day's number against your goal. It is the only
scheduled moment the screener runs; Upwork treats a tight polling loop as scraping.

**During the day.** Open the dashboard's Upwork tab. The tracker at the top says how many
proposals went out against the goal and names the next job worth your time. One button hands
the day's remaining applications over as a single instruction.

Per job, in order: read the detail overlay first (what it costs in connects, what competitors
are bidding, whether the client already hired, whether you clear their minimum bar), then
`upwork-pitch-page` if the job earns a visual, then `upwork-proposal` for the text you send.

**A client wrote back.** `upwork-inbox` finds it, `upwork-reply` drafts three answers in
different directions. **Nothing is sent without you saying so** — not a proposal, not a
message.

**Evening.** `eod` closes the day: what happened, what stayed open, what tomorrow looks like.

---

## Part 3 — A won job becomes work

This is where a job pipeline becomes an operating system.

The moment a job reaches `hired`, the pipeline is finished and delivery starts. Say **"I won
the Acme job"** and `upwork-won` does the handover:

1. **A project folder** is created from the job record — client, scope from the posting, where
   it came from. Named client-first (`bright-smile-group-google-ads-audit`), because the same
   client comes back and you want their projects sorting together.
2. **Its first task** lands in `context/STATUS.md` under the project's own heading. Exactly
   one, and it is the scope conversation: everything else follows from the scope, once that
   exists.
3. **The proposal and the pitch page move in** as project material. In three weeks they are
   the record of what you promised, and only useful if they sit somewhere you will look.
4. **The job record keeps `project: <slug>`**, so the funnel still counts the conversion and
   the project can still say where it came from.

The one thing no script can do is the Upwork message thread. It cannot be exported, and it is
the most valuable document in the project: the posting says what they asked for, the thread
says what you agreed to. So the skill offers to read it and write the decisions into
`inputs/agreed.md` — what was promised, by when, for how much. A summary, not a transcript.

After that it is a normal project: `ingest` files client material into it, tasks show up in
`morning`, `eod` closes them out. The Upwork side is done; delivery is the workspace's job.

**A project that never came from Upwork** takes the same route without the job record:

```bash
python3 reference/scripts/new_project.py "Acme SEO audit" --client "Acme GmbH"
```

Referrals and direct clients are not second-class here. Upwork is one way in, not the only
one.

**Why this matters more than it looks:** without it, everything before it is a lead
generator. With it, the same system that found the client also carries the work — one place
for the whole relationship instead of a pipeline that hands off into a void.

---

## What is deliberately not here

**Sending on its own.** No skill in this system sends a proposal or a message without a human
saying so in that moment. Upwork suspends accounts for unattended automation, and the one
thing worth protecting is the account. Drafting, preparing, scoring, ranking: all automatic.
The last step is yours.

**A schedule.** The screener runs on demand and once inside `morning`. Not on a timer, not in
a loop, not from a hosted runner.

**Tools you did not choose.** Every CLI is optional and every skill says so when one is
missing, rather than failing halfway through.
