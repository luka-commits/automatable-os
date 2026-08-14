# Claude Code Plugins

> **Up front:** plugins apply to the whole machine, not just to this folder. Whoever installs one has it in every Claude Code project. And: **the package needs none of them.** All the tools (`/morning`, `/eod`, `/email`, `/ingest`, `/setup`) run without any plugin. What follows are experience notes, not prerequisites.

If commands are not recognised after an installation: `/reload-plugins`.

For the two recommended command-line tools (firecrawl, playwright) see [`tools.md`](tools.md). Those are not plugins.

## Recommended

### Anthropic Official Marketplace — and what in it actually counts

**Enabled during setup** (SETUP.md step 3): `/plugin marketplace add anthropics/claude-plugins-official` — that only makes the catalogue known, installing happens one by one and only on your yes. In everyday use: if Claude notices during a task that a plugin from the catalogue would concretely help, it recommends it in one sentence with the install command — never install unasked, never nag repeatedly.

A curated, reviewed directory from Anthropic itself — the first place to look before installing a plugin from a foreign source. But: most of it is developer tooling (code review, commits, debugging) and irrelevant for this workspace. **Two things count for you here — one of which you already have:**

- **`skill-creator` is already in the package as a skill, not as a plugin** — it builds new skills and improves existing ones, the tool behind the promise from `VISION.md`: you describe what you do every week and get your own command for it (procedure: `reference/extending-the-system.md`). Deliberately bundled rather than installed: building your own commands is a core promise, and a core promise must not depend on a marketplace being reachable. Do not install the plugin of the same name on top — that gives you the same skill twice under one name.
- **`claude-md-management`** — audits the CLAUDE.md once the workspace has grown over months and the rules start sprawling. Install only when needed.

Everything else from the marketplace only on a concrete occasion: every plugin applies to the whole machine, brings its own commands and reads along in every session — three installed plugins that nobody uses make `/help` cluttered and every answer a little more expensive.

### `ponytail`: anti-over-engineering

**Install:**
```
/plugin marketplace add DietrichGebert/ponytail
/plugin install ponytail@ponytail
```

Forces the simplest, shortest solution (YAGNI). Useful before extending skills or the dashboard: `/ponytail-review` after larger rebuilds, `/ponytail-audit` for a whole project. Whoever adapts this package saves themselves the classic round in which a small change turns into a framework.

## By use case — what for what

The short overview Claude recommends from in everyday use (installing happens only on your yes):

| You want to … | Tool | When |
|---|---|---|
| Turn recurring procedures into your own commands | `skill-creator` (already bundled, nothing to install) | As soon as the first procedure ran the same way twice |
| Find out what is worth automating for YOU | `claude-code-setup` (official catalogue) — analyses your usage so far and suggests automations | After 2–4 weeks of use; before that there are no patterns to read |
| Have your own code reviewed | Install nothing: `/code-review` and `/security-review` are **built into** Claude Code | Right away, if you have code in the workspace |
| Create and improve designs / interfaces | `impeccable` (below) | Only for serious frontend work |
| See and reduce token costs | `codeburn` (below, runs without installation via `npx`) | When the bill raises questions |
| Keep rebuilds simple instead of inflating them | `ponytail` (above) | Before every larger build of your own |
| Tidy up the CLAUDE.md after months | `claude-md-management` (official catalogue) | When the rules start sprawling |
| Sales/marketing work with Claude | `anthropics/knowledge-work-plugins` (official, below) | When sales/marketing in the team use Claude |
| Find a skill that may already exist | `find-skills` (below) | Before building something yourself |
| Develop software seriously (TDD, debugging, planning) | `superpowers` (below) | Only on developer machines |

## Optional (if needed)

### `claude-code-setup`: find automation candidates

**Install:** `/plugin install claude-code-setup@claude-plugins-official`

Reads your own Claude Code usage (locally) and recommends which of your recurring procedures would be worth building as a skill, hook or routine. The perfect pairing with `extending-the-system.md` and `routines.md`: first it shows you WHAT, then we build it. Pointless before week 2 — it needs a usage history.

### `impeccable`: design guidance for frontends

**Install:**
```
/plugin marketplace add pbakaus/impeccable
/plugin install impeccable@impeccable
```
Docs: https://impeccable.style

**When:** only once you seriously develop the dashboard visually, for example with `/impeccable critique context/today.html`. Before that, superfluous.

### `knowledge-work-plugins`: sales, marketing & co (official, from Anthropic)

**Install:** `/plugin marketplace add anthropics/knowledge-work-plugins`, then e.g. `/plugin install sales@knowledge-work-plugins`

Open-source plugins from Anthropic for knowledge work beyond code — sales, marketing and more. For a startup often the most relevant catalogue after the official one: whoever in the team does proposals, campaigns or customer research with Claude finds ready-made procedures here instead of building their own.

### `find-skills`: search first, then build

**Install:** `npx skills add vercel-labs/skills --skill find-skills`

Searches the open skill registry (skills.sh) before something is built from scratch — the "does this already exist?" question as a tool. The fence around it: the registry is community-made, quality varies. Look at found skills first (source, what they read/write), then install — never blindly, and Claude installs nothing unasked as a matter of principle.

### `superpowers`: development methodology for the engineers in the team

**Install:** `/plugin marketplace add obra/superpowers-marketplace`, then `/plugin install superpowers@superpowers-marketplace`

A proven skill framework for serious software development: brainstorming → plan → implementation, test-driven, systematic debugging. **But:** it hooks into every session and pushes its methodology through — on the machine of someone who only steers briefings and projects here, that is noise and collides with the lean everyday use of this package. So: only on developer machines, not as a team standard.

### `codeburn`: make consumption visible

**Test without installing:** `npx codeburn`

Read-only, it only reads local session files, nothing leaves the machine. Shows consumption by model and project; `codeburn optimize` finds token waste with concrete fixes.

**When:** when you want to know what your usage is actually driven by. For the everyday case the model tiers in `CLAUDE.md` ("Token Economy") are enough — mechanics on Haiku, judgement on the session model, deep analysis on Opus only when it earns it.

## Power users — with your eyes open

Two tools for people who already drive the system confidently and want more. Both deliberately NOT for the first while and not for every machine.

### `claude-mem`: cross-session additional memory

**Install:** `/plugin marketplace add thedotmack/claude-mem`, then `/plugin install claude-mem@thedotmack`

Remembers what happened in earlier sessions and makes it searchable — useful when a lot of work happens outside the core commands and context gets lost between sessions. **Know three things before switching it on:**

1. **It logs tool calls** — including project content that was read — into its own local database. Whoever works with confidential client data clarifies that beforehand (the same question as with every tool that has full access).
2. **It brings a daemon and a vector database with it** — runs in the background, wants maintenance. When something jams, that is one more source of error.
3. **The file memory stays the truth.** `PROJECTS.md`, `STATUS.md` and `JOURNAL.md` remain the place where the state lives — readable, correctable, versioned in Git. claude-mem is additional recall, never a replacement. Do not rebuild anything in the system around it.

### `task-observer`: log skill gaps automatically (experiment)

**Install:** `npx skills add rebelytics/one-skill-to-rule-them-all --skill task-observer`

Watches the work, logs gaps and improvement candidates, feeds weekly reviews. Honest assessment: **this package already has its own mechanics for that** — the "from now on" learning loop, the end of day, and `claude-code-setup` for the automation analysis. task-observer puts a second observation log next to it (two places for the same kind of knowledge) and costs a little in every session. Whoever tries it: as an experiment with an expiry date — decide after two weeks whether it really beats the built-in loop, otherwise out again.
