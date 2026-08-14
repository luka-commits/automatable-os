---
name: checkup
description: "Checks on request whether the workspace itself is in order: local files only (settings, core files, setup state), reporting in plain language what's running and open. Changes nothing without saying so, never retrieves mail or calendar. Trigger: 'is everything ok', 'checkup', 'ist alles in Ordnung'."
---

# /checkup

The side entrance to the self-test. In everyday use the check runs silently with every `/morning` anyway and only speaks up when there is a finding. This command is for two moments: **"something is acting up on my end"** and **"run /checkup and send me the result"** (support).

## What you do

1. **Read `reference/self-test.md`** — the complete checklist is there. Duplicate nothing of it here, invent nothing on top.
2. **Check every point.** Local files exclusively. **Retrieve neither mail nor calendar** — not even to "quickly" test the connection. Whether it is reachable, the user sees at the next briefing.
3. **Answer like a human**, not like a test protocol:
   - First ONE sentence of overall verdict: everything in order, or what is missing.
   - Then, only if there is anything, the open points as a short list. Per point: what it means for him and what he can say to make it go away.
   - Unlike in the briefing, the good news gets named here too — he did ask, after all. But briefly: one line for everything that runs, no enumeration of every file checked.
4. **Never system jargon.** No filenames, paths, field names, error texts. Exception: the user explicitly says he needs it for a problem report — then the technical version may come along, clearly set apart.
5. **Repair yes, secretly no.** What can safely be fixed by itself (regenerating a missing derived file from the sources, safeguard 4), you do immediately and say in one sentence what you repaired. Anything that needs a decision (missing detail, discarded file, re-setup) is only proposed.

The reply follows `config.yaml → language` (canonical rule: CLAUDE.md).

## Retrofitting — the route that would otherwise be gone

The setup skill archives itself away after the setup. Without this section the user would have **no guided route left** for anything he wants to add later — only a message that something is missing.

So: if the user says "do that" about a reported point (or directly "connect my CRM", "I need a Firecrawl access", "attach the repo"), **you walk him through it** instead of pointing him at a manual. The procedures come from the setup and apply unchanged:

| What is missing | What you do |
|---|---|
| A connection (mail, calendar, storage, chat, CRM, development) | Walk through Claude Cowork: Settings → Connectors → pick the system → sign in with the work account. Afterwards **check via ToolSearch** whether the tools are there now, and write `inventory.connectors` with `slot:`. **No connector in the catalogue? Then it does not stop here** — the system's own MCP server added directly in Claude Code is the second rung, and you run that command, the user only fetches a token. The full route: `reference/mcp.md` § "If your system is not in the catalogue". Never end at "there is no connector"; that sentence was the reason a system stayed unreachable for months. |
| A tool (firecrawl, playwright) | `npm install -g <name>`, for playwright additionally `playwright install chromium`. Then check the version, write `inventory.clis`. Details: `reference/tools.md` |
| An access (Firecrawl, OpenRouter, Supabase, Vercel) | Open the registration page, he creates the account and generates the key, you append it to `~/.config/credentials.env` (permissions `600`). Then `inventory.accounts` with `key_env`. **Never write the key value into the chat and never repeat it.** |
| A project repo | `git clone <url> projects/<slug>/code`, then `inventory.repos` with `path`. Why kept separate: `projects/README.md` |

**The one hard limit:** commands that require a login or an input (`gh auth login`, `firecrawl login`, any OAuth flow) hang in your Bash — there is no terminal there that could answer. **Never run such commands yourself**: give the line to paste, say what happens afterwards, wait for his reply.

And the reverse holds too: an open connection is **not a defect**. If the user does not ask about it, it stays at the one line in the finding. Nothing is offered twice.

**Once, after about a month: the automation question.** From roughly four weeks of use there is something to read that did not exist on day one — the user's own patterns.

**"Once" needs somewhere to live, otherwise it is either every time or never.** Both halves hang on `context/config.yaml → asked.automation` (absolute date, or `declined`): no entry and the oldest line in `JOURNAL.md` more than 28 days old → ask; anything else → say nothing. Write the answer in immediately, `declined` when the user says no. Same mechanism for every other "offer this only once" in this package — a rule with no place to record itself is not a rule.

Then offer it, once, in one sentence: _"You have been working with this for a few weeks now. Want me to look at which of your recurring steps are worth turning into a command?"_ Say yes → install `claude-code-setup` from the official catalogue (`/plugin install claude-code-setup@claude-plugins-official`) and use its `claude-automation-recommender`: it knows the full catalogue of hooks, subagents, skills, plugins and MCP servers, so it beats a list you make up yourself. Say no → never again.

**Why not earlier and not in the setup:** the skill derives its suggestions from what has actually happened. On day one nothing has. Asking then produces generic advice, and generic advice is what teaches people to ignore the next suggestion too.

## Tone

A tradesman who takes a quick look under the hood and then says what's what. Not: "Diagnosis complete, 7 of 9 checks passed."

Example with a clean state:

> Looks good. Your details are complete, all working files are there, the dashboard is from this morning.
>
> One small thing: I still write mail drafts in the default tone, because I never learned your style. Say "derive my mail style", then they will sound like you.

Example with a real finding:

> Two things are not right.
>
> Your setup never quite got finished back then, I am missing your company's mail domain. That is why I treat mails from colleagues like mails from outside and sort your briefing wrongly. Tell me your domain, then it is done in ten seconds.
>
> And your dashboard is from Friday. Say "good morning", then I will rebuild it.

## Not responsible for

Subject-matter questions ("is the project status right?"), content, mail or calendar problems. The self-test checks the **mechanics** of the workspace, nothing else. If the problem is elsewhere, say so clearly and point to the problem report (CLAUDE.md safeguard 1) — that goes to the person the user got the package from.
