---
name: audit
description: "Judges a folder as a working system and says what would make it better: coverage, automation, safety, freshness, context ballast and more. Use it on 'audit', 'check my setup', 'what am I missing', and on someone else's setup before a first call. Whether the machinery is intact right now is /checkup."
---

# /audit

Judges a folder as a **working system**: not whether the files are tidy, but whether the whole thing carries the work that actually happens inside it.

**The difference to `/checkup`:** `/checkup` asks "is the machinery intact right now" — fixed list, daily, quiet, this workspace only. `/audit` asks "is this folder any good as a working system" — general criteria, monthly, on any folder. If it sounds like "something is broken on my machine", `/checkup` is the right one.

## Two levels, and only the first always runs

**Level 1, the folder itself.** Measurement and judgement: what is here, is it used, does Claude find it, is it still true, is it backed up. Needs no questions and no preparation, runs in seconds. **This is the default run** and in most cases the whole value — especially in environments where tools are set by IT anyway and nobody picks a CRM.

**Level 2, the business behind it.** Do the tools fit what this person actually does? This needs a short profile and some research, so it is **offered, not assumed** (step 5). If `context/profile.md` already exists, it runs without asking.

That separation is why this skill works the same in a corporate workspace as it does for a freelancer: there it stops at level 1, and that is complete, not halved.

## Step 1 — Measure

```
node reference/scripts/workspace-audit.js [--root <path>]
```

Writes `context/audit.json` and prints a summary to stderr. Reads local files and the session logs under `~/.claude/projects/` only, so it costs nothing.

**Read the JSON, do not interpret the stderr output.** Each dimension has `level` (`ok`/`watch`/`act`/`unknown`), `metric`, and `findings` with `what`/`why`/`fix`/`evidence`.

**`unknown` is not a finding**, it is missing evidence: no git, no session logs, no config. Say it as a limitation, do not score it as a fault. A freshly cloned client folder has no usage data — then the judgement rests on structure and content.

## Step 2 — Judge

What no script sees. Read the entry documents (`CLAUDE.md`, `AGENTS.md`, `README.md`) plus the files named in the findings, **capped at roughly 15 files**:

- **Do two instructions contradict each other?** Two rules governing the same thing differently are worse than no rule — what gets followed is whichever was read last, by accident.
- **Are the rules written so they can be checked?** "Be thorough" is prose. "Check the file exists before writing" is a rule.
- **Does the folder logic match the work that the session logs say really happens?** If 90 percent of the work happens in an area three levels deep, the structure no longer matches reality.
- **Which unused capability is a real gap, and which is simply surplus?** A skill that has existed for six months and that nobody ever invoked is not a reserve, it is ballast — unless it covers a rare, important case.

**Code is not read on the default run.** The code tile measures mechanically only (README present, uncommitted work, dormant repos). If the user then wants a judgement on a single repo ("take a closer look at X"), **read `references/code-review.md`** — it holds the review criteria, the exclusion list against false alarms, and the multi-angle approach with its separate confidence round. If the repo has an open pull request, `/code-review` is the better route and gets recommended instead.

Write the result back into `context/audit.json` as `judgement`.

**Finding discipline:** every finding carries `severity` and `confidence`. Below 0.7 confidence, do not report it at all. Better to miss a theoretical problem than to flood the report with noise — a checker that raises false alarms is ignored within two days and is then worse than none. The test before every finding: would an experienced person actually bring this up in conversation?

## Step 3 — Propose

From the findings, **design the setup this folder ought to have**. Three kinds, all three derivable without a profile:

| Kind | From what | Example |
|---|---|---|
| **Commands** | recurring steps that do not have a name yet | "you do this by hand three times a week" |
| **Routines** | what should happen regularly but gets forgotten | weekly review, inbox pass |
| **Automations** | **evidenced** from the repetition patterns in `audit.json` | "you have typed this sequence 40 times" |

Per proposal: what it solves, what it costs, what you take on with it. **Never a single recommendation** — two or three routes side by side, one marked with a reason. Format: `references/report.md`.

**Do not invent what already exists.** For the question "which Claude automation fits here" there is the `claude-automation-recommender` skill (from the `claude-code-setup` plugin). It knows the full catalogue — hooks, subagents, skills, plugins, MCP servers. Call it and take its result, rather than inventing your own narrower list. If it is not installed (`claude plugin list`), say so in half a sentence and derive it yourself — then only the catalogue is missing, not the judgement.

**Settle the scope first, that is the catch:** the recommender is built for ONE codebase, and a workspace often has many repos. So decide before calling it what it aims at:
- **Workspace-wide automation** (hooks that apply to all work, your own commands, routines) → point it at the workspace root. That is the normal case here, because this is where the recurring steps in the session logs come from.
- **Code automation for one specific project** (test hooks, API docs, migration skills) → point it at `projects/<slug>/code/`, not at the root. A proposal for "this React app" is worthless if it is averaged over twenty mixed repos.
- **Unclear which repo is meant** → one short question, do not guess. "For the whole workspace, or one specific project?" costs a sentence and prevents a report that aims at nothing.

**What it does not have, we do:** it reads only the codebase, not the session logs. The repetition patterns in `audit.json` (`dimensions[automation].findings[].evidence.samples`) are the evidence its proposals cannot supply — "you have typed this sequence 40 times" beats any catalogue recommendation. Bring both together: its catalogue, our evidence.

## Step 4 — Report

In chat: one sentence of overall judgement, then at most one line per dimension, then the three things with the most leverage. Everyday language, **consequence rather than measurement** ("Claude never reads these twelve documents, because nothing points at them" rather than "12 orphans"). No test-protocol look, no listing of every check that passed.

The result sits in `context/audit.json`. **The dashboard does not show it** — there is no placeholder for it, and that is deliberate: an audit is a snapshot with a date, not a running state. Anyone who wants to keep the finding has it written into the journal. The file itself is excluded from delivery, because it describes exactly one machine.

**Repair nothing without saying so.** What is safe and obvious (a dead symlink, a link to a renamed file) gets corrected directly after a short note. Everything else is proposed.

## Step 5 — Offer the business level

After the report, offer **once**, without pushing:

> "If you want, I can also look at whether your tools fit what you actually do — which CRM, which connections are missing, what is being paid for twice. That needs two minutes of questions."

If the user says yes (or `context/profile.md` already exists), continue with **`references/business-layer.md`** — it holds the six questions, the derivation of the target profile, and the tool dossiers.

**When this offer does not come at all:** when the folder is clearly in an environment where tools are not chosen freely (corporate setup, managed connectors, IT requirements in the CLAUDE.md). There, "which CRM would be better" is pointless and reads as naive. When in doubt: do not offer. Level 1 stands on its own.

## Self-improvement

Two signals: a finding gets corrected ("that is not a problem"), or one gets explicitly praised. On either, ask: "Should that go in permanently?"

Where the correction goes depends on what was wrong:

- **False alarm or missed finding in a measured dimension** → into `reference/scripts/workspace-audit.js`, as an exclusion or a new check. A countable rule belongs in the script, not in prose, otherwise it is decoration.
- **Tone or structure of the report** → into `references/report.md`.
- **Wrongly weighted slot or tool judgement** → into `references/business-layer.md`.
- **A question in the intake is missing or grating** → also `references/business-layer.md`.

False alarm means: repair the checker, do not dismiss the finding.
