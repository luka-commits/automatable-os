# Connecting connectors (MCP)

Mail and calendar are not hard-wired into this package. There is no fixed link to one particular mail program. Instead, everything runs through **connectors** that you connect yourself in **Claude Cowork**. Claude Code uses the same connection, so you only set it up once.

That is the real advantage: you decide what gets connected. Connect Microsoft 365 and it runs through that. Connect Google Workspace, same thing. Both in parallel works too.

**Two routes, one recommendation.** The simple route is the connector in Claude Cowork — sign in once, no configuration, and that is the right choice for almost everyone. On Google Workspace there is additionally an **advanced route**: the `gws` CLI, which talks to the full Google API (Sheets, Drive uploads, scripted routines) but wants a one-time setup in the Google Cloud Console. If that is you: [`reference/gws-cli.md`](gws-cli.md) is the guide. Everyone else can ignore that file.

## The promise up front

> ### Nothing is ever sent and nothing is ever written into the calendar
> The system creates **drafts**. Sending happens by hand, with one click in your mail program. Appointments are read, never created, changed or cancelled. Not even when a connector could technically do it. If you want that anyway, Claude will tell you that this decision deliberately stays with you.

Also unchanged: mail and calendar are only touched with your permission, and that permission applies per session. Sensitive topics (HR, salary, performance) stay out.

## What a connector is

A connector is a link between Claude and a service you already use. It runs on an open standard (MCP, Model Context Protocol). In practice that means: you sign in to the service once and allow Claude access. After that Claude can read there, without you copying or exporting anything.

Worth knowing:

- The connection belongs to your account, not to this folder. It is available in every Claude window.
- You can see at any time in the settings what is connected, and you can disconnect it there too.
- On the first tool call, Claude Code asks for permission once. Click "always allow" once and the question does not come back.

## Connecting

**You do not have to figure this out yourself the first time.** The setup asks early what you work with every day, and then connects those systems by name. What you did not mention gets one short question, so that nothing (chat, CRM) stays open forever purely because it never came up. Mailbox and calendar are not optional here, without them the daily briefing is an empty shell. Everything else is an offer.

Adding or changing something later: one sentence in the chat ("connect my CRM"), or `/checkup`, which shows you what is still open and sets it up on request.

By hand it goes like this:

1. Open **Claude Cowork**
2. **Settings → Connectors**
3. Pick the connector you want and sign in with your work account
4. Restart Claude Code so the connection takes effect

If Claude Code still reports that a tool is not available: restart once, then ask again in the session.

### If your system is not in the catalogue

Cowork covers the systems most people use, and the catalogue keeps growing — HubSpot, to name one, went from "no way in" to an official connector within weeks. So the first move is always to look, not to assume.

If a system genuinely has no connector, that is **not the end of it**. Almost every serious tool publishes an MCP server of its own, and Claude Code can use it directly, without Cowork. The difference for you is small, because **Claude sets it up, not you**: it runs the command, and the only thing left on your side is generating a token in your tool's settings — and it will open that exact page for you rather than describing where to click.

The order, and it matters:

1. **Connector in Cowork** — sign in once, nothing to configure. Always check this first.
2. **The system's own MCP server, added in Claude Code** — you fetch a token, Claude does the rest.
3. **Genuinely no way in** — then it gets said plainly, and that system stays manual for now.

**One rule holds throughout:** a route is only offered once it has been checked that it exists. Not "there is bound to be an MCP server for that". Looked it up, or not offered.

**And checking means actually looking, not remembering.** For anything beyond the household names — an industry system, a practice or property management tool, a CRM nobody outside the trade has heard of — the model's memory is the wrong source: these tools ship connectors quietly and the knowledge is stale within months. So search for it (`firecrawl search "<product> MCP server"`, plus the vendor's own docs and integrations page) and read what you find before you say a word to the user. Three outcomes, and each one gets said plainly: there is an MCP server (then set it up, they only fetch the token), there is an API but no MCP server (then say what that would mean — a piece of work, not a five-minute step), or there is genuinely nothing (then that system stays manual, and that is an honest answer, not a failure).

**Ask about the industry system, do not wait for it to come up.** The six slots cover what everyone has; what actually runs a business is often the seventh thing — the practice software, the booking system, the ERP, the tool the whole team lives in. It rarely gets mentioned when someone is asked about "mail and calendar", and it is usually the most valuable connection of all. So it gets its own question, once, in their language: *"Is there a system your work runs through every day that we haven't talked about — bookings, patients, projects, orders?"* Whatever comes back goes into `tools_in_use` with its purpose, even when no route exists — a named gap can be closed later, an unnamed one never comes up again.

## Which connectors this package uses

### Mail

**What it enables:** The mailbox triage in `/morning` (what needs an answer, where are you waiting on someone, what is just for information). Deriving your personal writing style from your own sent mail. And, depending on the connector, creating drafts directly in the mailbox.

**Without it:** The briefing still runs, just without the mail part. Drafts are then created through a `mailto:` link, which simply opens the compose window of your default mail program. That works everywhere and needs no permissions.

### Calendar

**What it enables:** The day's appointments in the briefing and the day timeline in the dashboard, including the free blocks in between. Reminders are shown separately from real appointments.

**Without it:** The briefing says honestly that it cannot reach the calendar today, and shows you tasks and projects instead. The calendar tab in the dashboard stays empty rather than guessing.

### File storage (optional)

**What it enables:** Documents that live in your storage can be filed directly, without downloading them first.

**Without it:** You drop the file into the `inbox/` folder and say "read this in". That is the normal case and perfectly sufficient.

### CRM (optional)

If you use a CRM like HubSpot, Salesforce or Pipedrive and there is a connector for it, you can connect it like any other.

**What it enables:** Questions in the chat that would otherwise cost you a tab switch. "Where do we stand with client X", "which deals have been stalled for two weeks", "what did we last talk about, before I write the mail". For mail drafts this is the biggest lever, because the context then comes from the CRM instead of from memory.

**To be honest about it:** The daily briefing pulls **no** CRM data today. `/morning` reads calendar, mailbox and your own project files, nothing more. So a connected CRM helps in conversation, but does not run along automatically. If you want that, say so, then it gets built into the briefing skill.

**Without it:** Nothing is missing. The system simply does not know your CRM.

## The `draft_method` switch

How a draft is created depends on the machine. The setup tries the routes and writes the one that works into `context/config.yaml` as `draft_method`:

| Value | What happens |
|---|---|
| `mcp` | The connector creates the draft directly in the mailbox. Only the draft tool is used, never a send tool. |
| `com` | Windows route via the installed Outlook app. |
| `applescript` | Mac route via the classic Outlook app. |
| `mailto` | Opens the compose window of your default mail program. Universal fallback, always works. |
| `manual` | Claude shows the text in the chat, you copy it. |

If the recorded route ever stops working, Claude automatically falls one step down and tells you in one sentence what happened instead.

**In which language a draft is written:** everything the user sees follows `config.yaml → language`. Mail drafts are the one exception — they follow the language of the thread they answer.

## Which connectors are additionally worth it

Everything connected in Claude Cowork is also available here in Claude Code — connecting is always the same route (Settings → Connectors). **Principle: connect on demand, not in stock.** Every connector is access to your data. That is why the setup *asks* before it connects anything: being asked costs nothing, an unnecessarily open access does.

What tends to pay off most in startup day-to-day, in this order:

| Connector | What it gives you | Fence |
|---|---|---|
| **Slack** | Mentions and direct messages as briefing context, thread lookup ("what was that again?") | Like mail: read only, only with permission per session |
| **Notion** (or similar company wiki) | "What do we have written on this?" — Claude reads the docs as context instead of you copying them together | Reading for context, not a second place to file things |
| **CRM** (HubSpot, Salesforce, …) | Pipeline status in the briefing, client history when drafting mail | Read only; CRM upkeep stays in the CRM |
| **Linear / Jira / Asana** | Ticket context for projects | **Important:** read for context, never a second task truth — your tasks live in STATUS.md, otherwise you have two lists and neither one is right |
| **Stripe** | Revenue figures on request | On request, not in the daily briefing |

**If you build products yourself**, the developer track is worth adding:

| Connector | What it gives you | Fence |
|---|---|---|
| **GitHub Integration** | Issues, pull requests and repo states directly in the conversation | Independent of the workspace repo from step 1 — that runs through `gh` and does not need this connector |
| **Supabase** | View and change the database by conversation (tables, queries, migrations) | With production databases: let it look first, approve changes deliberately |
| **Vercel** | Deploys, logs and project config | No ready-made catalog entry — add it via "Add" as its own MCP server (`mcp.vercel.com`) |

**For routines there is an extra rule:** a locally connected connector is not enough for a cloud routine — it has to be attached to the routine when it is created (the assistant asks about this, see `SETUP.md` § Running the briefing automatically).

## Wispr Flow — talking instead of typing

Not a connector to your data, but to your voice: **Wispr Flow** turns dictation into text anywhere on the machine, and its MCP server lets Claude reach what you dictated. For anyone who thinks faster than they type — a briefing, a long instruction, notes after a call — this is the single biggest change to how the day feels.

**Setting it up, once:**

1. Install the Wispr Flow app and sign in (wisprflow.ai).
2. Add the server: `claude mcp add --transport http wispr-flow https://api.wisprflow.ai/connect/mcp`
3. Sign in once in the browser when Claude asks.

**What it is not:** it does not read your files and it sends nothing on its own. It carries dictated text, nothing else. **What it costs:** its own subscription, separate from Claude.

**Worth knowing before you start:** dictated text arrives the way it was spoken — half sentences, no punctuation in the right places, names spelled by ear. That is not a fault, it is how speech works, and Claude handles it. What it does mean: for anything that goes out, `/schreiben` (or `/email`) still shapes it. Dictation gets the thought out of your head; it does not write your mail.

## Route B: IMAP directly (when there is no connector)

For mailboxes no connector can reach: no Claude Cowork access, connector blocked by IT, or the mail runs on your own mail server. Then mail and even calendar go through **IMAP directly** — two small, read-only scripts sit in `reference/scripts/` for that:

- **`mail-day.py`** — lists all mail for one day (incoming and outgoing). With that Claude can fetch the raw triage data when the connector is missing.
- **`mail-freebusy.py`** — the trick for the calendar: most appointments arrive as iCal invitations by mail. The script reads the invitations out of the mailbox and builds busy blocks plus free slot suggestions from them. **No OAuth, no calendar access needed.**

**Setting it up:** credentials once in `~/.config/credentials.env` (protect the file with `chmod 600`, it lives outside the repo and never lands in Git):

```
MAIL_IMAP_HOST=imap.your-company.com
MAIL_USER=you@your-company.com
MAIL_PASS=app-password
```

**Honest prerequisite:** the mailbox has to allow IMAP with a password or app password. Own mail servers and most hosters: yes. Microsoft 365 and Google Workspace: only if IT has enabled it — there the connector (route A) is the intended way. Nobody needs both at the same time.

**Limits:** read only (BODY.PEEK — nothing is moved, deleted or marked as read), no file storage, no Teams/chat. Claude calls the scripts itself via the terminal when the connector is missing and the credentials are there.

## Without any connector and without IMAP

The package still runs. Project tracking, dashboard, filing documents, task management and mail drafts need no connector. Exactly two things are missing: the appointments in the briefing and the mailbox triage. The setup checks this itself and tells you in one sentence what is missing and what falls away as a result.
