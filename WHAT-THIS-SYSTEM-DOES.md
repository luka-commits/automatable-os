# What this system does — and what it doesn't

One page of plain talk so that you (and anyone who asks you) know exactly what happens here. If you are unsure whether you are allowed to use this: read this, and when in doubt ask whoever decides about tools and data at your place (management, IT, data protection). Better to ask beforehand than to explain afterwards.

## What it is

A **personal work folder for Claude Code**: text files with your projects, tasks and notes, plus a few instruction sets (skills) that tell Claude how to build you a briefing in the morning and how to file things.

**It is not a finished product and not a service someone runs for you.** It is a setup you received and that you hold in your own hands. The responsibility for which company data you use with AI stays with you and with your own rules, exactly as with any other Claude use. If there is a policy on this at your place, it applies; this document does not replace it.

## Where your data is processed

**Through your own Claude access — nowhere else.** This package sends nothing to servers of its own, has no database of its own, no cloud sync and no external services. Everything you see here is local files on your machine plus the Claude connection you are using anyway.

**Everything runs locally.** The folder sits on your own machine, your projects, tasks and notes are normal text files inside it. The dashboard too is only a file (`context/today.html`) that your browser opens from the hard drive. There is no server, no login, no hosted address and nobody who could look in from outside. If you take the folder along, you take everything along; if you delete it, everything is gone.

Concretely that means: **if your Claude Code use is fine, this package changes nothing about the data situation** — it only structures what you would show Claude anyway. What is new here nonetheless: Claude routinely accesses your mailbox instead of only what you paste in piece by piece. That is exactly why the next section is here.

## What it reads

| What | When | How |
|---|---|---|
| **Your mails** | only with `/morning` or when you ask for it | Contents are only read. The only thing written back is a tag ("AI-Triaged") on the mails already gone through, so that they are not read again tomorrow. What this tag is called depends on the mail program (in Outlook a category, elsewhere a label). Nothing is moved, deleted, answered or marked as read. Can be switched off via `mail.tag_processed: false` in `context/config.yaml`. Asks for permission again in every new session — you can say no every time. |
| **Your calendar** | as above | Read-only. Appointments only, no changes. |
| **Documents** | only the ones YOU actively put in | e.g. transcripts, minutes, papers in `inbox/` |
| **The files in this folder** | always | Your projects, tasks, notes — that is its memory. |

**Sensitive topics are detected and left out — the typical cases.** If the system recognizes a mail as an HR, salary, bonus or performance topic (by keywords and by known HR senders), it never lands in the briefing, never in the dashboard and is never processed into a draft. It only counts them ("3 sensitive mails — have a look yourself") and keeps its hands off.

**That is not a guarantee.** The detection runs on a keyword and sender list, not on understanding: a subject line like "About your conversation next week" hits none of the keywords and is treated entirely normally. If a topic is sensitive for you, don't rely on the automatic system — you can extend the list in `reference/mail-triage-rules.md` at any time (or tell Claude to do it).

## What it NEVER does

- **Never send mails.** It writes drafts that sit in your mail program. You always press "send" yourself.
- **Never create, change or cancel appointments.** The calendar is read only.
- **Never touch files that have nothing to do with this folder.** Writing happens in four places: into this folder, into your **drafts folder in the mail program** (the draft you check), as a **tag on mails gone through** (see the table above, can be switched off), and for the draft mechanism itself into the subfolder **`_tmp/`** — that is where Claude puts the short script that opens the draft in the mail program. Always the same file name, overwritten with every draft: never more than one such script is left lying around. Anything beyond that Claude asks about first.
- **Nothing of yours is deleted behind your back.** "Gone" means moved to the archive, and you can always go back. If you genuinely want something deleted, you say so and get asked once with the consequence spelled out. Only its own leftovers (temporary scripts, failed attempts) does the system tidy away by itself.
- **Never upload data to outside services.** No database of its own, nothing sent anywhere you did not switch on. There are exactly **two** exceptions, both of which you set up yourself and can switch off:
  - **Your own private GitHub repo.** At the end of the day the system backs up the state of this folder there — created during the setup, under your account, your access, gone the moment you remove the repo connection. Nowhere else.
  - **The community dashboard, only if you join it.** Off unless you paste a token into your credentials file during setup. What it sends is counters and nothing else: how many jobs you found, applied to, heard back from, and won, per day. **No job titles, no client names, no descriptions, no text of any kind** — the exporter refuses to build a payload containing them, and the receiving end rejects one. Check it before you believe it: `python3 reference/scripts/community_sync.py --dry-run` prints the exact bytes and sends nothing.
- **Never look into your mailbox unasked.** Without your yes in this session, nothing happens there.

## What you should keep in mind

- **Who besides you may enter your repo: nobody, unless you invite them.** The setup does not ask, and does not offer. Earlier versions asked whether a contact person should be added as a collaborator, which made sense when the package was handed over by a consultant; here the repo is yours alone. If you later want someone to help, adding a collaborator is your call to make on GitHub, and you can check who has access any time under Settings → Collaborators.
- **Client data:** project notes and mail summaries land in this folder — depending on the project, that is client information. Treat the folder like any other folder with project material: on the machine you use for work, in a place your rules provide for, not on other people's devices or in private clouds.
- **Several clients in one folder:** the briefing presents side by side what belongs to different projects. Everything stays on your machine and in your own Claude session in the process; for the vast majority of work that is unproblematic. If a project has stricter confidentiality requirements, or the client or your project lead demands it: keep a separate folder for that project only (a fresh copy of the package).
- **After a project ends:** what may stay, the system archives (`projects/_archive/`). What has to be deleted under the agreement, you delete yourself in Explorer or Finder — the system deletes nothing on its own, as a matter of principle.
- **Passing it on:** if you pass the folder on to someone, pass on the empty version — not yours. Otherwise you are distributing your project notes with it.
- **The folder is unencrypted.** These are normal text files. Whoever has access to your machine can read them (just like your Word documents).

## The short version, if someone asks you

> "It's a folder with text files that tells my Claude how to summarize my calendar and my mailbox for me in the morning. It only reads, sends nothing and changes no appointments. The folder itself has no server and no database: everything sits on my machine, and what Claude reads takes the same route as with any other Claude use — through my own access, and nowhere else."

## Who to ask

| Question | Contact |
|---|---|
| Are we allowed to use it like this? | whoever decides about tools at your place (management, IT) |
| What about personal data? | your data protection people, internal or external |
| Which connections to mail and calendar exist and what they may do | [`reference/mcp.md`](reference/mcp.md) |
| Claude Code is technically stuck | your IT, plus the official Claude Code documentation |
| Questions about this package itself | see [`VERSION.md`](VERSION.md) |

_Which connectors exist, how you connect them and what they may do is described in [`reference/mcp.md`](reference/mcp.md)._
