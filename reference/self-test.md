# Self-test

The checklist the system uses to check itself. It is read in two places:

- **`/morning`, at the end of the run** — silently. Something is said ONLY when something is wrong, and then at most **one** line. If everything works, the user never notices this check exists.
- **`/checkup`** — on demand, reports the good things too. Made for the support case ("run /checkup and send me the result").

The point: the dangerous failures of this system are the **silent** ones. A placeholder that was never replaced, a missing file, a connection that stopped answering — none of that produces an error message, all of it makes the work worse. This list makes them visible.

## Rules for the output

1. **Only read local files.** The self-test never fetches mail or calendar, so it costs practically nothing. Whether the connection answers is something `/morning` already knows from its own run (Step 0c) — that knowledge is used, not gathered again.
2. **One line, not a report.** In the briefing the **most important** open item is named, none of the others. Two problems does not mean two lines.
3. **Plain language, no system jargon.** Never file names, paths, field names or error texts. Always: what is the consequence for the user, and what do they do about it (one sentence, literally sayable).
4. **Tact by severity.** Level A is mentioned in every briefing for as long as it persists (it is a real defect). Level B only **on Mondays**, so it does not nag.
5. **Never invent values.** If something is missing, ask, do not guess.

## Level A — distorts the work, report daily

| Check | How to spot it | What the user hears |
|---|---|---|
| Setup incomplete | `.claude/skills/setup/` still exists (the skill archives itself away as its last act, so its presence means unfinished). **Not** `[YOUR NAME]` in `config.yaml` — that gets written in step 3, long before the setup is done, so a run that broke off later would look finished. Both missing at once (`.claude/skills/` gone AND the placeholder still there) means something else: the copy is incomplete, see `CLAUDE.md` at the very top. | "Your setup did not finish. Say `/setup` and we'll wrap it up in ten minutes." |
| Company domain missing | `company_domains` is empty or contains `[your-company.com]` | "I don't know your mail domain yet, so I treat mails from colleagues like external ones. Tell me your domain and I'll sort them correctly." |
| Config unreadable | The file exists but cannot be read as YAML | "A line in your settings has slipped, I'm working with half the information right now. I can bring back yesterday's version, just say the word." Plus name the affected line. |
| Work folder moved | `workspace_root` in config.yaml points somewhere other than the folder currently being worked in | Fix it silently (re-derive from the actual working directory, write it back to config.yaml), then ONE sentence: "Your folder has moved — I've adjusted it, everything keeps running." |
| Sync conflict copies | `context/` contains files with ` 2.` in the name (`STATUS 2.md`, `config 2.yaml` — typical OneDrive) | "OneDrive has created duplicate copies of your working files — I'm working with the original, but you should take a quick look at the copies: if there are newer changes in them, say so and I'll merge them." |
| Folders and project list out of sync | A folder in `projects/` (other than `_template`/`_archive`) has no block in `PROJECTS.md` — or a block has no folder | "A project is only half set up — [name] is missing from the overview (or: has no folder). Should I complete it or does it belong in the archive?" |
| Core file missing | One of `PROJECTS.md`, `STATUS.md`, `JOURNAL.md` is gone | Restore it silently from the backup (Safeguard 4), then ONE sentence on what was repaired. Only report it if that does not work. |
| Dashboard template missing | `context/today_template.html` is gone | "The dashboard template is missing, so today there is only the briefing in the chat. The file has to come back from the original copy." |
| No mailbox, no calendar | `inventory.connectors` holds no entry with `slot: mail` or `slot: calendar` and `status: true` (accept the older German spellings `kalender`/`ablage` too — a workspace set up before July 2026 carries them) | "I don't have access to your mailbox and calendar yet, which makes your briefing only half as useful. Say 'connect my mailbox' and we'll set it up in five minutes." This is a real defect, not a comfort topic: without those two the start of the day is an empty shell. |

## Level B — a convenience is missing, report on Mondays

| Check | How to spot it | What the user hears |
|---|---|---|
| Mail style never derived | `context/EMAIL_STYLE.md` is missing | "I'm still writing drafts in the default tone. Say 'derive my mail style' and they'll sound like you." |
| Draft path unknown | `draft_method` is empty | "I don't have a way to create mail drafts yet. Say the word and we'll find the right one." |
| Dashboard path unknown | `script_command` is empty | "I can't build the dashboard right now, the briefing in the chat carries on as normal." |
| Equipment never recorded | `inventory` is completely empty | "Your equipment is still empty in the Workspace tab. If you like, I'll note down what you have connected." |
| Routine with no sign of life | A routine is listed in `inventory.routines`, but its most recent result file (e.g. `inbox/briefing-*.md` for the morning routine) is older than 2 working days | "Your [routine] has not delivered anything since [X] — the cloud connection has probably expired. On claude.ai/code/routines you can see the last run; 'Run now' tests it immediately." |
| Tool without access | A CLI is listed in `inventory.clis` with `status: true`, but the matching key is missing from `~/.config/credentials.env` (only the name is checked, the value is never read) | "Firecrawl is installed, but without an access key it can't fetch anything. Say 'set up the Firecrawl access' and we'll do it." |
| A newer version is available | The newest tag on `upstream` is ahead of the version line at the top of `VERSION.md` (`git fetch upstream --tags`, then `git tag -l --sort=-v:refname \| head -1`). No `upstream` remote → that is the same finding, the source just has to be added first. Nobody updates a system they were never told had an update. | "There's a newer version of your workspace — [one line on what is in it]. Say the word and I'll fetch it, takes two minutes and nothing of yours is touched." Then the update route in `VERSION.md`. Do not push: mention it once, and not again for the same version. |
| The same skill twice | A skill in `.claude/skills/` carries the same name as one an enabled plugin brings along (`claude plugin list` plus the plugin's own skills). They do not collide — they appear side by side under two names (`impeccable` and `impeccable:impeccable`) — but one of them is a frozen copy that silently ages while the other updates, and both cost context in every session. | "You have [name] twice, once in the folder and once through a plugin. They do the same thing. I'd move the folder copy to the archive and keep the plugin, then it stays current by itself." Never remove it unasked: in a shared folder the copy may be someone else's deliberate choice. |
| Plugin installed but switched off | `claude plugin list` shows an entry with `Status: ✘ disabled`. A disabled plugin is still listed as present and does nothing — the failure mode is silence, so nobody notices for weeks (measured on a real machine 23.07.: three of seven off). | "Three of your tools are installed but switched off, so they never kick in. I can turn them back on, just say the word." Then: `claude plugin enable <name>@<marketplace>` per plugin. |
| Project repo vanished | An entry in `inventory.repos` has a `path`, but the folder no longer exists | "The code for [project] is no longer where it was. Should I fetch it again?" |
| Dead wood | Tasks that have been open unchanged for more than 30 days | "Three tasks have been sitting unchanged for over a month. Should they go, or are they still current?" |
| Equipment drifting | Today's run contradicts `config.yaml → inventory`: a connector answers that is listed as "not connected" (or the other way round, knowledge from `/morning` Step 0c or ToolSearch — no extra fetch), a listed CLI is missing on the machine | Correct it silently (adjust the inventory, Safeguard 4), then ONE sentence only if something new turned up that needs a decision: "You've connected [X] in the meantime — should I include it in the briefing?" |

## What is NOT checked

- **Whether mailbox and calendar answer.** `/morning` handles that in its own run and says so there already (Step 0c). Reporting it twice is annoying.
- **Whether content is correct.** The self-test checks the mechanics, never factual correctness. A wrong project status is not a technical fault.
- **Anything that costs an extra fetch.** As soon as a check costs money, it does not belong in a silent background run.
