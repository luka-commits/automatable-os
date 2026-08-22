---
name: email
description: "Helps write business emails in the user's personal style, English or German: takes context (recipient, subject, message), produces a short direct draft with signature from config.yaml, then creates it via the configured draft method after an OK — never sent automatically. Trigger: /email, 'write a mail'."
---

# Email Skill — Draft in the User's Personal Style

> **Config:** first name / name / role for signature + closer come from `context/config.yaml` (`user.*`). `{FirstName}` below = `user.first_name`. No city — the workspace does not hold one.
>
> **Draft language — the one exception to the working language.** Everywhere else, output follows `config.yaml → language` (canonical rule: `CLAUDE.md` § Working language). Mail drafts do not: a draft follows **the language of the thread it answers** — reply to a German mail → German draft, reply to an English mail → English draft. Only when there is no thread to follow does it fall back to `config.yaml → language`.
>
> **Style source (in order):** if `context/EMAIL_STYLE.md` exists, THAT is the style reference — the templates below are then only a structural fallback. Without it, the example style below applies (from the package's original author, see the note there).
>
> **"Derive my mail style" — the procedure lives here** (`/setup` archives itself after setup, so don't look it up there): **first check whether it has already happened** — if `context/EMAIL_STYLE.md` exists, don't blindly re-derive, but say in one sentence: _"Your style is already derived (as of: [file date]). Redo it anyway, e.g. because it no longer fits?"_ Only continue on a yes. **Procedure:** get permission → Haiku subagent (the prompt starts by loading the mail search tool of the connected connector; for Microsoft 365 `ToolSearch select:mcp__claude_ai_Microsoft_365__outlook_email_search`, for another connector determine the name via `ToolSearch query:mail`) uses it to fetch the last ~6 months **by naming the sent FOLDER** — Microsoft 365 `folderName="Sent Items"` (German mailbox: "Gesendete Elemente"), Google Workspace `query="in:sent"`; **not** `sender = user.email`, because the search covers the inbox only and a sender filter returns zero of the user's own mail (verified 2026-07-21) — (limit ~50), fetches full texts, returns 15–25 typical excerpts (openers, closers, sign-offs, one-liners), separated by DE/EN, skipping anything sensitive (HR/salary/performance) → from that derive opener/tone/length/closer/signature (judgement work, main model) → write to `context/EMAIL_STYLE.md` (structured like the style reference below) → show the user 5–8 bullets and ask "does this fit?", incorporating corrections directly.

## Purpose

Generate business mail drafts (EN + DE) in the learned personal style. User gives context → draft in chat → after OK, a draft opened in the mail program.

## Trigger

- `/email <context>` — e.g. `/email reply to nicole about the meeting`
- `/email` empty → prompt: "To whom, what about, which language?"
- Chat: "write a mail to X", "draft mail for Y", "how do I reply to X", "write a mail saying Z"

## Style Reference (extracted from Sent Items)

### English

**Opener:**
- `Hi <FirstName>,` standard, all direct colleagues
- `Hello <FirstName>,` slightly more formal
- `Dear <X> Team,` teams, formal requests
- Inline is fine: `Hi FirstName, happy to! I've...`

**Tone:**
- **Formality follows the recipient:** colleagues (an address on a domain from `company_domains`) and recognisably familiar contacts (an existing first-name thread) get the relaxed register. Externals, first contacts and anything unclear get the careful one: full name in the greeting, no contractions, no exclamation marks. When in doubt, careful. Too formal with a close contact is a small thing; too casual with the wrong recipient is embarrassing. (As soon as `EMAIL_STYLE.md` exists, its rule applies.)
- Short, often 1 to 3 sentences, otherwise one paragraph at most
- Direct verbs instead of chains of conditionals
- Warmth through a sparing `!` (`happy to!`, `got it!`, `great, thank you!`)
- When late, honest meta-info: `sorry for the slow reply`, `sorry, I was stuck on other blockers`
- Context sentences for availability: `Friday I'm at a client`
- Emojis rare, the occasional 🙂 at most

**Banned filler phrases (never use):**
- "I hope this email finds you well"
- "I am reaching out regarding..."
- "Thank you in advance for your efforts"
- "Please do not hesitate to contact me"
- Em-dashes (`—`)

**Closer:**
- `Best, {FirstName}` standard, 90% of the time
- `Best\n{FirstName}` (on 2 lines)
- `Thank you\n{FirstName}` when making an explicit request
- `Kind regards\n{FirstName}` rare, only for formal requests

### Signature (always, after the closer)

```
__

{user.name}
{user.role}
```

Nothing after the role. No city, no address — the workspace deliberately does not hold a home location.

## Mail-Type Templates (Common Patterns)

Each type is given in both languages. The German versions are the original examples and stay German on purpose: they show how these mails are actually written in German (`LG`, no filler). Use the version that matches the draft language.

### 1. Short confirmation / thanks

```
Hi <Name>, thanks a lot!
Best regards
{FirstName}
```
One sentence is enough.

### 2. Follow-up with a question

```
Hi <Name>,

quick one, <one sentence of context>. <One-sentence question>?

Best regards
{FirstName}
```

### 3. Meeting proposal

```
Hi <Name>, happy to! I've sent a proposal for <weekday>, unfortunately <alternative day> I'm <reason>.
Best regards
{FirstName}
```

### 4. Status update to stakeholders

```
Hi <Name>,

quick update, and sorry upfront for the long silence, the last few weeks were pretty full with the <project> project.

I have now done <what>, <recommendation / request for feedback>.

Best regards
{FirstName}
```

### 5. IT ticket reply

```
Hello <Name>,

Thank you for your message! <Concrete answer/question>.

Best regards
{FirstName}
```

### 6. Formal request to a team

```
Dear <X> Team,

I am currently working on <context sentence>. <Concrete request / question>.

Best regards
{FirstName}
```

### 7. Sensitive/diplomatic (rescheduling, cancellation)

```
Hi <Name>, all good!
<Short context / proposal>.
Best regards
{FirstName}
```

## Workflow

### Step 1 — Gather context

**The language is detected automatically, never asked for:**
- Reply to an existing mail → take over the language of the original mail (German mail → German reply, English → English), same rule as in `/morning`'s draft creation (Step 5b).
- Fresh mail with no original (new request, not a reply) → derive the language from the user's prompt itself (German prompt → DE, English prompt → EN); if that is ambiguous, fall back to `config.yaml → language`. Only ask when both are genuinely possible (e.g. the recipient is clearly not a German speaker but the prompt is German) — then have it briefly confirmed, not as a standard question.

If the user only types `/email` (without context) → ask in a structured way:
```
Quick basics:
1. To whom? (name / email)
2. What is it about? (1-2 sentences is enough)
3. Is this a reply to a mail? (Yes → which one / URL — the language is taken from it)
4. Mail type? (confirmation / follow-up / meeting proposal / status / request / other)
```

If part of the context is in the trigger (e.g. `/email reply to nicole about the meeting`) → only ask for the missing points.

### Step 2 — Generate the draft

Rules:
1. **Match the appropriate mail-type template** above, don't just copy it over blindly
2. **Recipient's first name** in the opener (never the last name, unless explicitly wanted)
3. **Length:** as short as possible. Rule of thumb: <100 words except for formal requests
4. **Emojis only where they fit** — 🙂 max. once, in relaxed communication with colleagues
5. **Exclamation marks** sparingly, only where warmth clearly belongs
6. **NO em-dashes** (`—`). Use `,`, `.`, `:` instead
7. **Signature always** (see above)
8. **Sensitive topics** (salary, HR, performance, feedback about third parties): issue a WARNING, have the user confirm that they really want to discuss this by mail rather than in person

### Step 3 — Show the draft in chat

Format:
```
📧 Draft proposal

To: <recipient>
Subject: <subject>
Language: <EN|DE>

——————
<Body incl. opener, content, closer, signature>
——————

OK to create the draft? [yes / edit / cancel]
```

User replies:
- `yes` / `ok` / `looks good` → Step 4
- `cancel` / `no` → abort, do nothing
- Free text (e.g. `make it shorter`, `more casual tone`, `sharper subject`, `add X`) → apply, show the draft again

### Step 4 — Create the draft (path via `draft_method` from config.yaml)

There are several ways to create a draft; which one fits depends on what is connected and installed on this machine. Which one works here was determined by `/setup` and recorded as `draft_method:` in `context/config.yaml` (`mcp` · `com` · `mailto` · `applescript` · `manual`). If nothing is there: check the ladder yourself — look for the draft tool of the connected connector via ToolSearch, otherwise the OS default (Windows: `com`, Mac: `mailto`). In all cases: only create/open, NEVER send. Scripts go into `_tmp/` with a **fixed file name** — every run overwrites, so never more than one script is left lying around.

**If the chosen method fails** (policy has changed, mail program mode switched, connector logged out): drop one rung — `mcp` → `com` (Windows) resp. `applescript` (Mac) → `mailto` → `manual` — and tell the user in one sentence what happened instead. If the switch is permanent, update `draft_method` in the config.

#### `mcp`: the connector's draft tool

Only if `/setup` found one. Load the tool via `ToolSearch`, create the draft with it. The very first time, Claude Code asks once for permission for the tool — tell the user upfront: "click 'always allow' once, then it never asks again." **Only the draft tool, never a send tool** — even if the connector offers one. Nothing is sent here, sending deliberately stays with the user (a click in the mail program).

#### `com`: PowerShell COM (Windows default, classic Outlook installed locally)

The draft is created via **Outlook COM in `_tmp/draft.ps1`** (UTF-8 for umlauts) and executed with:
```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File _tmp/draft.ps1
```
`-ExecutionPolicy Bypass` is mandatory: on managed laptops unsigned `.ps1` files are blocked otherwise. If a policy or blocked error still comes back, that is not a COM problem — drop one rung (`mailto`).

Script content:
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Stop'
$outlook = New-Object -ComObject Outlook.Application
$mail = $outlook.CreateItem(0)
$mail.To      = '<recipient address>'
$mail.Subject = '<subject>'
$mail.HTMLBody = '<body as HTML — paragraphs via <br><br>, signature with <br>>'
$mail.Display()   # NEVER .Send()
Write-Host 'Draft created and opened in Outlook.'
```

#### `mailto`: open a link (Mac default, universal fallback)

No script, no permissions needed, independent of the provider — opens the compose window of the default mail program (whatever the user has set there), technically the same as clicking a mail link:
- **Mac:** `open "mailto:<address>?subject=<subject>&body=<body>"`
- **Windows:** `cmd //c start "" "mailto:<address>?subject=<subject>&body=<body>"`

URL-encode subject and body (spaces `%20`, line breaks `%0A`, umlauts as UTF-8 percent encoding). Plaintext only, no attachments; rule of thumb body < ~1,500 characters — try longer mails one rung higher (`com`/`applescript`) or `manual`.

**Limitation for replies:** `mailto` always creates a NEW mail — it cannot reply inside an existing thread. If the draft is a reply, point that out to the user in half a sentence (_"The draft opens as a new mail — best to attach it to the thread via Reply, the text is copyable."_) or offer `manual` right away (text in chat, the user clicks Reply themselves). Do not pretend it is a thread reply.

#### `applescript`: osascript (Mac, opt-in)

Only if `mailto` isn't enough (e.g. HTML wanted) **and** classic Outlook is running. Write the draft as `_tmp/draft.applescript`, execute with `osascript _tmp/draft.applescript`:

```applescript
tell application "Microsoft Outlook"
	set newMail to make new outgoing message with properties {subject:"<subject>", content:"<body as plaintext — line breaks as return>"}
	make new recipient at newMail with properties {email address:{address:"<recipient address>"}}
	open newMail
end tell
```

"New Outlook" mode does not support AppleScript reliably, and central device management can lock down this control via an MDM profile — if the call fails ("not authorized"), drop one rung (`mailto`).

#### `manual`: text in chat

The draft text is already in the chat anyway (Step 3) — then one sentence: "Automating this doesn't work on this machine — copy the text above and paste it into your mail program."

#### After creation (all paths except `manual`)

```
✓ Draft created and opened.
Recipient: <name> · Subject: <subject>
Check in your mail program → Send.
```

## Rules

- **NEVER send automatically.** The skill only creates drafts. Even on "send it" from the user → create the draft, then note "please check in your mail program + send".
- **NEVER multiple drafts in parallel** without a user OK between each one.
- **NEVER draft sensitive content** (salary/HR/performance/conflict about third parties) unasked — warn first and have it confirmed.
- **Recipient's first name** always derived from context. If unclear → ask, don't guess.
- **For replies** — if the user doesn't supply the original mail, ask whether relevant context is missing. Never invent back-references.

## Example Runs

**Run 1: Short trigger with full context**
```
Input: /email thanks to [colleague] for the data
→ Draft:
   To: [name.colleague@company.com]
   Subject: RE: [Topic]
   Body:
     Hi [First name], thanks a lot!
     Best regards
     [YOUR NAME]
     [+ signature]
→ User: "ok"
→ draft_method: com → .ps1 via Outlook COM (.Display())
→ ✓ Draft opened
```

**Run 2: Follow-up with unclear context**
```
Input: /email
→ Prompt: 5 questions
→ User: "to [colleague], German, wanted to push for status, no reply yet"
→ Draft:
   To: [name.colleague@company.com]
   Subject: Project X, quick update?
   Body:
     Hi [FirstName],
     quick one: wanted to check whether you got any further on this? If there is anything I should prepare, say the word.
     Best, [YOUR NAME]
     [+ signature]
→ User: "more casual tone"
→ Draft 2 with adjustments
→ User: "ok"
→ Draft created
```

**Run 3: Formal EN request**
```
Input: /email
→ Context questions
→ User: "RAI Team, English, need approval for a new analysis that does employee-level analytics, formal"
→ Draft:
   To: ResponsibleAI@company.com
   Subject: RAI Approval Request: <analysis name>
   Body:
     Dear Responsible AI Team,
     I am currently working on <context>. The check would <concrete>. Could you please review and confirm this is compliant with RAI guidelines?
     Best regards
     {FirstName}
     [+ signature]
```
