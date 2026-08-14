---
name: adopt
description: "Rebuilds an EXISTING folder into the workspace structure without losing anything: proposes in plain language what goes where, asks about everything unclear, moves with a way back, then checks the result against what a fresh setup would have produced. Use it on 'restructure my folder'. An empty workspace is /setup."
---

# /adopt

Brings a folder that grew on its own into the workspace structure. **It is finished when the folder is indistinguishable from one that was set up fresh** — plus the existing contents in their right place.

**The difference to `/setup`:** `/setup` prepares a freshly copied, empty workspace and may create anything. `/adopt` meets someone else's work and may touch almost nothing without asking. That is not a detail, that is the entire difficulty.

## The target is this package's structure, not a compromise with the one you found

**Caution applies to the contents, never to the schema.** What is written in the files belongs to the user; nothing there is guessed and nothing is quietly moved. But **what the folders are called is not up for negotiation** — it is what they came for.

The reason is mechanical, not aesthetic: `/ingest` writes to `inputs/`, `/eod` reads from `work/`, `projects/README.md` describes exactly those three folders, and the audit checks against them. A workspace that keeps `docs/` does not have a second valid schema, it has tools reaching into thin air. Quietly, which is the worse kind.

So, without exception:

- **`inputs/`, `work/`, `outputs/` are the names.** A `docs/`, `notes/`, `material/` you find gets renamed, not treated as equivalent.
- **The question is what goes where, not whether to rename.** "Is `docs/` your own work, or things you received?" is the question. "Shall we keep `docs/`?" is not.
- **If a foreign name does stay**, because the user explicitly insists, that is their decision and it is respected. But it goes into the report in step 5, with the sentence saying what stops working because of it. A deliberate exception is bearable; an unnoticed one is a time bomb.

**The self-test:** if at the end someone says `/ingest` and the file does not land in `inputs/`, the rebuild was not finished, however tidy it looks.

## Why this is the most delicate flow in the whole system

A rebuild is irreversible unless you build it to be reversible. Three routes into damage, all three seen for real:

1. **An existing `CLAUDE.md` gets overwritten.** It often holds months of refinement, and the loss only shows up weeks later, when Claude behaves differently and nobody knows why.
2. **A folder gets moved that something points at.** That is exactly what once killed a morning digest: a launchd job pointed at the old path, started daily, died with exit 127, and **nobody was told**. It could have run like that for months.
3. **Something gets filed that was deliberately somewhere else.** Order imposed by a foreign schema is not order.

The rules below follow from that. They are not caution for its own sake; each one stands for a concrete piece of damage.

## Step 1 — Build the plan (touches nothing)

```
node reference/scripts/adopt-plan.js --root <path>
```

Reads the folder and sorts every entry into four groups: **already fine** · **merge** · **suggested move** · **needs your answer**. Machinery (anything starting with a dot, configuration files) is never suggested for moving — moving it breaks the folder.

Every move suggestion states **who points at this path**: documents, scripts, and especially jobs outside the folder (`~/Library/LaunchAgents`). A suggestion with an external reference is **never carried out without updating it**.

## Step 2 — Show the plan and settle the gaps

Read the plan out in plain language, not the JSON. Structure: what already fits (one line, do not enumerate), what would move and why, and then the questions.

**One question the script never asks, but it always belongs: is there material from more than one client here?** If so, the user decides BEFORE the rebuild whether each client gets their own folder. Asking afterwards is too late; by then everything sits together and has to be touched a second time.

**The questions are the most important part.** The script deliberately does not guess. Typical cases: a folder with mixed contents, a document in the root, an empty directory. One sentence per case, with a suggestion as the default — choosing is faster than explaining.

Only when no question is left does it continue. **An "I don't know" means: the entry stays where it is.** Leaving it is always right, guessing never is.

## Step 2b — Inside the projects

A folder whose root is already correct has not been adopted. That was exactly the finding on the first real run: the plan reported "11 already fine, 0 suggestions" while eleven of sixteen projects used `docs/` instead of `work/`. **Checking only the top level is blind to the normal case** — someone already has an order, it is just a different one.

The plan shows four things for this. Each becomes a question, never a movement:

| What the plan shows | The question it raises |
|---|---|
| **A folder name across many projects** that the schema does not know (`docs/`, `notes/`) | **What is in there — your own work, or things you received?** Then it gets renamed: own work → `work/`, received → `inputs/`, sent out → `outputs/`. Decided once, then applied everywhere. If both are mixed in there, that is the separation described in the section below, not a reason to keep the old name. **The question is where to, never whether.** |
| **A project untouched for more than 90 days** | Is it dormant or is it over? Answer "over" → the flow in `projects/README.md` § "archiving a project", **including** the question about its open tasks. Quietly filing a project away and leaving its tasks standing is the worse kind of mess. |
| **Loose files directly in the project folder** | Is that your own work (`work/`) or something received (`inputs/`)? With more than five files, do not ask file by file, ask once per project. |
| **Version markers in the file name** (`final`, `v2`, `copy`, ` 2.`) | Which one counts? The rebuild is the one occasion to settle that; afterwards nobody ever asks again. Answer → the current one stays in `work/`, the others go to `_archive/` inside the project. **Never guess, never quietly delete.** |

**What is never touched here:** a subfolder with its own `.git`. That is client code, a product repo or a cloned third-party checkout — its own history, often a different owner. The plan lists such folders separately as "untouched", and that is where it ends. Not even "just move the README".

### Separating what was received from what you made

A `work/` with everything piled together is the normal case in folders that grew. The separation pays off because `inputs/` answers **what the client sent** — the question that arrives three months later, when nobody can prove it any more.

```
node reference/scripts/adopt-plan.js --root <path> --provenance projects/<group>/<project>/work
```

**Judge on the FIRST level under `work/`, never deeper.** That is the whole trick, and it was learned expensively: per file you get hundreds of follow-up questions, per leaf folder still dozens and plenty of nonsense — every foreign CSS file of a cloned website counted as "written by hand". On the first level it is two questions, and the judgements are right. A person thinks the same way: "the website folder is a copy, nutrition is a project."

**What does NOT work, so nobody builds it again:**

- **Timestamps** ("never edited, so it was received"). A single folder move sets creation and modification time equal, after which every file looks untouched. Tested against real data and discarded.
- **The git history** ("added once, so it was received"). Structural commits touch every file at the same time; the number is then identical for every file. Also tested and discarded.

What works is unspectacular: **format and name**. PDFs, DOCX, voice messages and camera images are things you get; Markdown, HTML and code are things you write. A folder with `wp-content`, `node_modules` or `vendor` anywhere inside it is a downloaded third-party thing, whatever else is in there.

**And the rule above all others: what is mixed gets asked about, not guessed.** On a test run, two of twelve entries stayed open — exactly the two that really were mixed. Both times the follow-up question is the right answer, not a failure of the tool.

**Order:** these questions come together with the ones from step 2, in ONE round. Asking twice is the surest way to lose the user mid-rebuild.

## Step 3 — Execute, with a way back

**Before the first movement**, create a manifest: `context/.adopt-manifest.json` with a timestamp and one line per planned movement (`from`, `to`, `method`). That is the way back; without it the rebuild is a jump without a net.

**The scaffolding belongs in the manifest too.** In a folder that grew there is no `context/` yet, so creating the four folders is itself already a change. Record it first, or the way back does not cover the very beginning.

**If a cloud sync is running (OneDrive, Dropbox, iCloud), have it paused first.** Moving during an active sync creates conflict copies (`STATUS 2.md`), and those only surface days later. One sentence to the user is enough. Conflict copies that already exist are **never resolved by you**: only they know which version counts.

Then, in order:

- **Move with `git mv` when the folder is a repo**, otherwise with `mv`. Never `cp` and then delete: that creates a moment where both exist, and a second where nothing is right.
- **A nested repo moves as a whole.** Never touch its history, never re-initialise it.
- **Merge `CLAUDE.md`, never replace it.** The existing content stays complete; our sections are added, clearly separated. On a contradiction the existing text wins, and the contradiction gets named rather than quietly resolved.
- **Delete nothing.** "Gone" means `inbox/archive/YYYY-MM-<topic>/`.
- **After every movement, update the references** step 1 reported. Only then the next one. Collect them up and you forget half.

**Three rules for archiving, all three learned the hard way on the first real run:**

1. **When archiving, carry the path along, never just the file name.** Moving flat into `inbox/archive/` means two files with the same name overwrite each other, silently. Of 13 files, 10 arrived. The right form is `inbox/archive/YYYY-MM-<topic>/<originalpath>/<file>`.
2. **A pattern in a file name is not proof.** "Contains 2" matched `Seedance 2.0`, a product name. You recognise a sync conflict copy by **the file without the 2 sitting next to it** — otherwise it is simply a name with a number in it. The script checks this now, but the rule holds for every pattern search you write yourself.
3. **Searches stop at the repo boundary.** A `find` over the whole folder runs into `code/` and therefore into someone else's history. On the first run a directory was pulled out of a client repo that way — exactly the boundary called hard two paragraphs above. Every search excludes folders with their own `.git`, not just every movement.

**And one for the manifest:** it is written **per step**, against the paths that hold at that moment. A manifest that records all movements at once points, after the first rename, at paths that no longer exist — and the way back then puts the files into a newly invented folder instead of back.

If something breaks midway, the manifest says what has already happened. Rolling back means working the list backwards.

## Step 3b — Catch up the tooling

Structure alone is not adoption. A freshly set-up workspace also has **tools**: installed plugins, available CLIs, connected connectors, stored credentials. A folder with perfect folder logic and no tools is half a rebuild.

The inventory supplies the current state, without guessing:

```
node reference/scripts/inventory.js
```

### Show the comparison first, then offer

**The user sees a two-column list first, not a series of individual questions.** Someone who already has ten things and lacks three wants to see that at a glance, not answer "do you already have…" ten times and still not know at the end what is actually missing.

Compare against: `reference/plugins.md` (the plugins), `reference/tools.md` (`firecrawl`, `playwright`, Node.js, the `claude` command line), `reference/mcp.md` (the connections).

> **Already here:** Node.js, firecrawl, GitHub login, mailbox connected, 3 of 7 plugins
> **Still missing:** playwright (Claude cannot operate web pages) · 4 plugins · calendar · no repo of its own, so no backup

Every line under "still missing" carries in brackets **what does not work today because of it** — not the name of the tool. "playwright is missing" tells nobody anything; "Claude cannot operate web pages for you" does.

Then **offer, do not silently install** — by the same rule as in setup: **one question per group**, with what it does and what it costs, never six questions in a row and never install unasked. A tool whose purpose the user does not know never gets used and is exactly the ballast `/audit` reports later. The only exception is Node.js and the `claude` command line: without them a third of the package does not exist, so those are announced and installed, not asked about.

**And what is already there does not get offered again.** That is what the comparison is for: it is taken ONCE at the start, read from the machine (`claude plugin list` with `Status: ✔ enabled`, `<name> --version`, `ToolSearch` for the connections), not from what some file claims. After that only the right-hand column is worked through, group by group, in a fixed order.

**No step falls away silently** — the same rule as in setup, for the same reason. Every line from "still missing" ends in exactly one of three states: **set up**, **declined** (the user said no; that is a complete answer and is recorded with `status: false`) or **not possible** (with the reason, and what it would have given them). Anything in none of those three states was not decided, it was forgotten: go back and get it, rather than leaving it out of the report. A group that was never asked about is not a no.

**What must not happen here:** that at the end nobody can say what the folder now has and what it does not. The comparison therefore also goes into the report in step 5, with the state after the rebuild, in the same columns, so beginning and end can be compared directly.

**Do not rebuild the actual setting-up here.** Steps 7.1 to 7.4 of the `/setup` skill do exactly that (install tools, work through the connections, create credentials, attach project repos). Point there from here and run them, rather than writing a second, worse version.

## Step 4 — Sign-off against the target state

The rebuild is done when the folder looks like it does after a fresh setup. That is checkable, not a matter of taste:

```
node reference/scripts/workspace-audit.js --root <path>
node reference/scripts/inventory.js
```

**The sign-off, in three parts:**

1. **Structure** — the audit must report no `act` dimension that the rebuild created. `Reachability` especially: dead links are the typical rebuild scar.
2. **Schema** — no project still carries a folder name the system does not know. For that, **run the same planner again** that opened the rebuild:

   ```
   node reference/scripts/adopt-plan.js --root <path>
   ```

   It knows the permitted names (`inputs`, `work`, `outputs`, `code`, `_archive`) and counts the projects against them. The line at the end has to add up: **as many projects "with work/" as "with inputs/"**. If there is still a gap, the rebuild is not finished.

   Whatever remains is either a deliberate exception named in the report, or a forgotten rebuild. There is no third option.
3. **Tooling** — the setup tile on the dashboard shows the required steps at 100%.

Only when all of that holds is the folder indistinguishable from a freshly set-up one. If something stays open, it belongs named rather than smiled away: which point, why it is open, and what would close it.

## Step 5 — Report

Briefly: what was moved (a number, not a list), what stayed put and why, what the user still has to decide. Plus the sentence on how to undo everything, and where the manifest is.

**Do not praise what is a given.** "All 40 files moved successfully" is not news. What is interesting is what did not work and what is different now.

## Self-improvement

Two signals: an assignment gets corrected ("that belongs somewhere else"), or a suggestion gets praised.

- **A wrong or missing assignment rule** → into `reference/scripts/adopt-plan.js`, in `classify()`. A countable rule belongs in the script, otherwise it is decoration.
- **A kind of file or folder that lands in "needs your answer" although it is unambiguous** → also into the script, as a new rule. Every question the script can answer itself saves the next person a minute.
- **Tone or structure of the report** → into this skill, step 5.

And the rule above all others: **if something is guessed and the guess is wrong, do not improve the assignment, abolish the guessing.** The entry then belongs on the questions list.
