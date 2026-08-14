---
name: upwork-pitch-page
description: Builds a short, self-contained pitch webpage for ONE specific Upwork job — an interactive solution diagram the client can pan, zoom and edit, a slot for your own walkthrough video, and a tight "why this fits" pitch, as a single static HTML file to send alongside the proposal. Use on "generate the pitch page for job <id>", "make a pitch page for this job", the "Yes, generate it" button in the dashboard's Upwork tab, or any request for a visual to accompany an application. On demand per job only, never automatically for everything the screener finds. Writing the proposal text is upwork-proposal, finding and scoring jobs is upwork-screener.
---

# Upwork Pitch Page

Turns one already-qualified Upwork job into a short webpage you can link from your proposal: a solution diagram drawn from the job's actual requirements, a slot for a walkthrough video you record yourself, and a tight pitch paragraph. **One universal template for every niche** — the page structure does not change, only the content does. Building a separate template per niche before a single real send would be guessing at a difference nobody has confirmed.

**Proven end-to-end once, for real** (job `2088142694814906836`, "AI Lead Processing Workflow Specialist") — the steps below are what actually worked that run, not a plan.

**Before assuming any Upwork capability, check [`reference/upwork-mcp.md`](../../../reference/upwork-mcp.md)** — what the MCP actually returns and what it does not, all of it measured. Two limits already bite here: `find_jobs` search gives only a truncated snippet (the full description needs action=`get`), and there is no working public job link to put on the page. Writing anything back to Upwork is governed by [`reference/upwork-regeln.md`](../../../reference/upwork-regeln.md), though this skill only produces a local file and sends nothing.

## Step 1: Get the job

Read `context/.upwork_jobs.json`, find the record by `id`. If the user names a job by title instead of id, match on `title` and confirm which one before proceeding — don't guess between near-duplicates.

## Step 2: Research the actual mechanism — don't skip it just because the category is familiar

**Corrected 14.08.2026.** The old version of this step said to skip research for "another GHL automation." That was wrong on a real job: "GHL Expert" (two yacht/boat businesses sharing one sales team, multi-channel attribution) got a first diagram that was accurate at the category level but collapsed real, distinct mechanics — UTM/GCLID capture, tag-based lead-source attribution, brand routing, closed-loop conversion reporting back to the ad platforms — into a vague "route by brand" box, because "GHL" felt well-trodden so the step got skipped. The category being familiar tells you nothing about whether *this specific combination of requirements* is.

**So: check `context/tool-knowledge/<tool>.md` first, for every named system in the posting.** That's the accumulated knowledge base (GHL today, more tools as jobs demand them) — read it before drawing anything. Three outcomes:

1. **The file already covers this exact mechanism** — use it, cite nothing further, draw the diagram from it.
2. **The file exists but doesn't cover this angle** (a new combination, a tool feature not yet documented) — research it now (`WebSearch` for current docs/best-practice, or `/last30days` for patterns still settling), then **append the finding to the knowledge-base file with its source** before moving on. The research is wasted if it evaporates after this one job.
3. **No file exists yet for this tool** — same as above, but create the file (see `gohighlevel.md` as the template: what the mechanism actually is, not just that it exists, with sources).

**If the user has built this exact thing before, their own experience outranks any web source** — ask them rather than trust a blog post over a real track record, and mark what they tell you as "firsthand, from their own project" in the knowledge-base file so later runs know it was not scraped.

**"Familiar category" is never itself a reason to skip this step.** The only valid skip is: the knowledge-base file already has the specific mechanism this job needs, so there is nothing left to look up.

## Step 3: Read the posting into a plan

**This is the step that decides whether the page lands.** The engine can draw
anything; what makes a client feel understood is that the boxes carry *their*
situation. The only input is the job posting, so read it deliberately before
drawing anything.

**First, look in the library.** `library/index.json` lists every flow generated
so far. If a past job is close (same shape of system, not necessarily the same
industry), start from its JSON and adapt — faster, and the second version of a
pattern is always better than the first. The library fills itself on every run,
so it is never stale.

Then extract, in this order, and write it down before building the graph:

| What | Where it usually hides in a posting |
|---|---|
| **Trigger** | "when someone fills in the form", "leads come from Facebook ads" |
| **Named systems** | the tools they already pay for — these become `logo` slugs and `owner: "client"` |
| **Manual work today** | "I currently do this by hand every week", "someone has to check X" |
| **Destination** | where the result must end up: CRM, sheet, inbox |
| **Phase 2 wishes** | "later we want to add…", "start small and expand" |
| **Constraints** | budget, deadline, tools they insist on |

Four rules that separate a bespoke diagram from a template one:

1. **Use their words, verbatim.** "Your Squarespace form", not "web form". "Your
   HubSpot", not "CRM". This single habit does more for the felt personalisation
   than any visual choice on the page.
2. **Never invent a fact the posting does not support.** Where it is silent, say
   so *in the diagram*: a node labelled "Which CRM? — to confirm" is honest, and
   it starts exactly the conversation the pitch is trying to start. A guessed
   tool that turns out wrong costs the job.
3. **Mark the scope.** What is in the first milestone goes in one `group`; the
   later wishes go in a second. The client's own "start small" language becomes
   a visible boundary rather than a promise you did not make.
4. **Manual steps are the argument.** Every step the posting describes as done
   by hand is a step the diagram should show being taken over. That contrast is
   the pitch.
5. **Don't collapse distinct requirements into one node.** Confirmed wrong on a
   real run (14.08.2026, "GHL Expert"): "sales pipeline" and "lead assignment"
   are two separate line items in the posting, and the first draft folded them
   into a single "route by brand" box — a real simplification of what was
   actually being pitched. If the posting names it as its own thing (its own
   sentence, its own clause), it earns its own node, even if that pushes past
   the node count Step 4 mentions. A CRM/process job in particular tends to
   have more distinct real steps than a simple data-pipeline job — attribution
   capture, tagging, routing, assignment, and follow-up are five different
   mechanisms, not one.

## Step 4: Build the graph

Write the plan as JSON and pass it with `--graph` (inline or a file path). The
generator validates it and stops on anything wrong rather than drawing a broken
picture — unknown `kind`, unknown `owner`, an edge or group pointing at a node
that does not exist.

```json
{
  "nodes": [
    {"id": "form", "label": "Your website form", "kind": "source",
     "owner": "client", "logo": "wordpress"},
    {"id": "ai",   "label": "AI reads and categorises", "kind": "step"},
    {"id": "q",    "label": "Qualified?", "kind": "decision"},
    {"id": "crm",  "label": "Your HubSpot", "kind": "datastore",
     "owner": "client", "logo": "hubspot"}
  ],
  "edges": [
    {"from": "form", "to": "ai"},
    {"from": "ai", "to": "q"},
    {"from": "q", "to": "crm", "label": "yes"},
    {"from": "crm", "to": "later", "dashed": true}
  ],
  "groups": [
    {"id": "p1", "label": "Milestone 1: what we build first",
     "nodes": ["form", "ai", "q", "crm"]}
  ]
}
```

**`kind`** picks the shape, so it is read before the label is:
`source` · `step` · `sink` · `decision` (chamfered) · `datastore` (cylinder) ·
`service` (dashed) · `actor` (a person, dotted) · `note` (folded corner) ·
`milestone` (pill).

**`owner`** drives the colour and answers "what am I paying for" without a
sentence: `you` (accented — you build it), `client` (plain — they already run
it), `thirdparty` (dashed — an outside service).

**`logo`** takes a slug from `assets/logos/`. Only the logos a graph actually
names get embedded, so a page costs a few KB rather than all 84. Run
`python3 scripts/fetch_logos.py --check` to see what is available;
**Twilio, Salesforce, Pipedrive and OpenAI are not** (those brands had their
marks removed from the source set), and a node with no logo simply shows its
shape rather than a wrong mark.

**`note`** (optional, 14.08.2026) is the real explanation of what that step
does, in plain client language: two to four sentences, no jargon, written for
someone who does not work in this field. A node carrying one gets a numbered
accent badge, and the same number heads a full-size note card in a grid
directly under the board. That split is the whole point: the box stays short
enough to read as a shape, the explanation stays long enough to actually
explain.

**Two layouts were built and rejected before this one, both for the same
reason — an explanation you have to work for is not an explanation:**

1. *Small grey caption under the box.* Read as a photo caption and got skipped.
2. *Sticky notes on the canvas itself.* Looked genuinely good as a whiteboard,
   but a board with a sketch plus twelve nodes fits the viewport at roughly
   0.37 zoom, which put the note text at ~4px. A note you have to zoom into
   explains nothing. Rejected on the measurement, not on taste.

A click-to-reveal tooltip fails the same bar by definition, so don't propose
one. The bar: *"it has to be understandable without us saying
was dazu sagen."*

Not every node needs one. Self-evident boxes ("Your website form", "Sales team
working the deal") stay bare; reach for a note where the label alone is
genuinely opaque to an outsider — a tool-specific mechanism, an abbreviation,
anything where a client would think "and what does that mean for me". Roughly
half to two-thirds of nodes is a healthy ratio.

**Positions are not written.** The engine ranks nodes by longest path and lays
them out left to right; a hand-placed `x`/`y` only creates something to go stale.

**6–10 nodes is a starting rhythm, not a cap.** For a job whose posting genuinely
lists more distinct real steps (Step 3, rule 5), draw all of them — a job that
gets compressed to fit a node count is a job whose pitch undersells its own
scope. **Corrected 14.08.2026:** the earlier version of this guidance said a
graph past ~10 nodes opens anchored at the start instead of fitting the default
view, and framed that as a reason to hold back. The call on the real
run this happened on: that's not a problem — the editor has Fit and fullscreen
for exactly this, and a client clicking through an interactive diagram will use
them. Don't cut real content to make the *first* screenshot look tidy.

Every generated graph is written to `library/` automatically, and stays there —
see the curation step below for what makes one worth reusing.

**Curate, don't just accumulate.** `library/index.json` grows on every run, but
a flow only earns a `pattern` tag and counts as a starting point for a *future*
job once the user has actually seen it and liked it — not automatically the moment
it's generated. When he says a page (or its diagram) is genuinely good, add to
that job's library entry: `"pattern": "<short, reusable name — e.g.
multi-brand-lead-routing, voicebot-crm-integration>"` and `"why_good":
"<one sentence — what made this one worth copying next time>"`. Step 3's "look
in the library" instruction should prefer a `pattern`-tagged entry over a
same-industry one that lacks it — a marked pattern is a proven shape, an
untagged entry is just whatever got drawn last time.

## Step 4a: Should this job get a real build, not just a drawing?

**The judgement that matters is knowing when you actually need the tools.** The board visualises. But for some jobs the far stronger move is to actually build the thing and link it, so the client clicks instead of imagining. The judgement is which — building everything is waste, drawing everything leaves the best card unplayed.

**Build it when all three are true:** the job names a tool that can be built programmatically, the shape of the work is clear enough from the posting that a build wouldn't be guesswork, **and** the job is worth the extra hour (good client, real budget, genuine fit). A cheap gig-shop posting gets a diagram.

| Job names | What is actually possible | Verified |
|---|---|---|
| **A website / landing page** | Build it with Claude Code, deploy with `vercel`, link the live URL. The strongest card on the table: not "here's my plan" but "here it is, click it". | `gh` + `vercel` CLI both set up here |
| **n8n** | Workflows can be created through the n8n API and exported as importable JSON. A self-hosted instance is the usual choice; n8n Cloud works the same way. | needs `N8N_API_KEY` + base URL in `credentials.env` — **not set up yet** |
| **Make** | Scenarios and blueprints are API-addressable, same idea. | `MAKE_API_KEY` present |
| **GoHighLevel** | **Cannot be built via API.** Tested against the live account 14.08.2026: `GET /workflows/` returns 200 but only names and status, `GET /workflows/<id>` is 404, and `POST /workflows/` is 404 ("Cannot POST /workflows/"). GHL's own ideas portal still lists workflow creation as an open request. So a GHL job gets the diagram, plus screenshots from your own existing builds where they fit. Don't promise a live GHL link. | tested with the real key |

**Anything actually built must be linked on the page** — `--live-artifact "Label|URL"` (repeatable) renders a proof strip right under the board. The rule: a flow that exists but isn't clickable is, to the client, the same as a drawn one.

## Step 4b: The diagram is live, not a picture

The page ships a real editor (`assets/diagram.js`), which changes what the
section is for. The reader can drag nodes, pull a connection from any handle,
add a step, rename by double-clicking, delete, undo, tidy the layout, zoom
(wheel or pinch), go fullscreen, download a PNG, and press **Run** to watch a
lead travel the path once.

**The point of the editing is the loop back.** Once they change anything, a
"Copy your version" button appears that encodes the whole graph into the URL
hash. They paste that link into the Upwork chat, and it opens showing *their*
version. Edits that go nowhere would be a gimmick; edits that come back are
requirements gathered before the call. Say so when handing the page over.

## Step 4c: The hero illustration — added 14.08.2026, for jobs where the mechanism itself is hard to picture

**The bar this exists for: the page has to be understandable without anyone saying a word about it** — has to be understandable without us saying anything about it at all. The technical diagram (Step 4) is precise and editable, which is exactly what makes it dense; a first-time reader who isn't technical can look at 10 shape-coded boxes and still not get the one-sentence version of what's happening. The illustration is that one-sentence version, drawn instead of written.

**When to generate one:** a job whose core mechanism has a real "aha" to it that a diagram alone under-sells — multiple distinct sources converging into one shared system (this job: two brands, one CRM, one team), a before/after contrast, a manual process being replaced. Skip it for a job that's already a simple, obvious linear chain; forcing an illustration onto a trivial flow is decoration, not clarity.

**Draw the benefit, not the mechanism.** Corrected 14.08.2026 after a first attempt got called generic and boring: a hand-drawn schematic of boxes and arrows just restates the diagram in a softer font. What earns its place is a picture of *the client's world with the problem solved* — their industry, recognisably, with the outcome visible in it. For this job: two yachts at a marina, enquiries flowing as one stream of light into a single dashboard, and a sales team closing a deal in the background. Someone in that business sees themselves; nobody sees a stock illustration.

Two rules that follow from it: **the industry must be unmistakable** (yachts, not "boats"; a clinic, not "healthcare"), and **the benefit must be the subject**, not a decorative frame around a flowchart.

**How:** invoke `/generate` — the default is now **gpt-image-2 via Kie AI at 2K** (5 ct per image; `models/gpt-image-2-kie.md`). Style that has worked: warm editorial illustration, confident flat shapes with subtle texture, hand-drawn feel but polished, generous negative space. **Pin the palette explicitly in the prompt** (cream `#f3efe6`, terracotta `#c1663e` carrying the light, dark brown `#262019` for line work, sage and ochre as secondaries, and say "no blue, no purple, no neon") — otherwise the model drifts to its own colours and the image stops belonging to the page. Always add "no text, no letters, no numbers, no logos": generated lettering is the fastest way to make a page look machine-made.

**Compress before embedding.** A 2K PNG is ~2.6 MB and the page carries the image twice; as JPEG at quality 86 it is ~350 KB. Convert, then pass the JPEG.

**Wire it in:** `--hero-illustration /path/to/file.png` on the `generate.py` call (Step 7). The section simply loses it when the flag is omitted — no placeholder needed, an illustration is a genuine value-add, not a required part of every page.

**It renders on the board itself, to the left of the flow, not as a block above the widget** (corrected on real user feedback: the image, when used, belongs inside the flow builder right next to the flow, not floating somewhere above it). The layout reserves the space in `autoLayout`, so the sketch pans, zooms, fullscreens and PNG-exports as part of the same board. That placement is the point: anything sitting outside the frame reads as an attached picture, something to skim past. Inside the frame it is part of the plan.

## Step 5: Page structure (redesigned — video-first, social proof moved up, richer scope block, book-launch lead magnet)

1. **Brand row + pill + headline** — your name plus an optional secondary link ("More of my work, on YouTube" — earned that copy after a first version, "Watch my YouTube," got called out as boring and unclickable; the fix was better copy, not removing the link, and it also needs to be genuinely easy to spot, not buried at the bottom). The pill under the brand row is a concrete, stat-based credibility chip (a stat plus a delivery count, e.g. "94% Job Success · 22 builds shipped") — not generic reassurance text ("Built specifically for this project" was cut for exactly this reason: it sounds too generic). The H1 (`--hook`) must clearly reference *this specific job* — echo language or the concrete ask from the actual posting, not a generic automation pitch that could sit on any page. Subhead (`--subhead`) right under it.
2. **Video, full width** — the Loom slot (Step 6), no longer squeezed into a side column; it's the first thing after the headline.
3. **3 fit-points below the video** — a 3-column row (stacks to 1 column under 640px), each bullet marked with a custom inline SVG checkmark icon (`FIT_ICON` in `generate.py`, a filled accent-color circle with a white check) instead of a numeral, replacing the earlier "1, 2, 3" list treatment. Pull the 3 points from `context/experience.md` — pick entries that genuinely fit this job's domain, never force one that doesn't apply, never state a number that isn't in that file. Pass via `--fit-point` (exactly 3).
4. **Social proof, moved up here** — real Upwork review text (never video links, never invented quotes). The real testimonials, taken from the user's own public Upwork profile live in `assets/testimonials.json`; `generate.py` reads all of them by default (`--max-testimonials` to cap). If that file is ever empty, the section renders an honest "not added yet" line. This and the CV below it used to sit near the bottom of the page — both moved up to belong to the video/credibility zone near the top, on the reasoning that trust signals should land early, not after everything else.
5. **Collapsible CV, also moved up here** — collapsed by default (`<details>`/`<summary>`, "More about my background"). Filled by `generate.py` from `context/config.yaml` (`{{CV_STATS}}`) and `context/testimonials.json`, never hardcoded. Deliberately dense rather than minimal: up to five track-record numbers (earned, projects delivered, hours logged, Job Success Score, verified hourly rate), the client-sourced trait tags from Upwork's "Insights from completed jobs" (Collaborative, Committed to Quality, etc. — genuine third-party praise, not self-description), the real company names you have built for, and the employment/education background. When new verified facts land in `experience.md`, pull them in here too rather than leaving this section thin while richer data sits unused in the reference file.
6. **What I'd build** — the widest block on the page (1140px, not the 720px reading measure; the heading and lede stay narrow, the plan gets room). Three parts that work as one: the **board** — the optional hand-drawn sketch sitting left of the live flow, both on the same canvas (Step 4c) — then a **legend** naming what the colours mean, then the **numbered note cards** below it. The legend exists because the colour coding was answering "what am I actually paying for" silently (filled = I build it, plain = you already run it): an encoding nobody explains is decoration, not an argument. The diagram itself is not an image; it renders from the node list at runtime, so it stays sharp at any size, follows the theme tokens, and can be edited by the reader (Step 4b).

   **A board this size will not fit the default view, and that is fine** — an explicit call, made twice: if it does not fit the default view, that is not a problem. Fit, fullscreen and the minimap exist for that. Never cut real content to make the first screenshot look tidy. What must *never* depend on zoom level is the explanation — that is exactly why the notes live below the board at full reading size.
7. **How this would work** — a 4-column scope block, each column with its own small outline SVG icon (wrench / clock / price-tag / checklist) so it reads as a real spec sheet, not four flat text blocks: Tools (`--tool`, repeatable), Timeline (`--timeline`), Budget (`--budget` — a rough, honest framing, not a precise quote), and what's needed from the client to kick off (`--kickoff`, repeatable, still labeled "To get started, I'd need"). Never pad any of the four with generic filler ("communication," "patience") — every line should be something a client could actually check off.
8. **"See what we can do"** — the lead magnet, shown book-launch style: a real report cover screenshot (`assets/report-cover-example.jpg`, page 1 of a real Pocket CEO performance report, rendered via `pdftoppm` and compressed to JPEG) tilted with a drop shadow next to the pitch copy and CTA (`--lead-magnet-url`, `--lead-magnet-teaser`, `--lead-magnet-cta`), plus a one-line note ("Real example, built for another client. Yours would look just as sharp.") so it's clear this specific report belongs to someone else, not fabricated for this page. Same honesty rule as testimonials: a real asset or an honest placeholder, never invented copy. `gopocketceo.com` doesn't currently have a live self-serve "type your business name, get an instant report" flow (checked directly, 14.08.2026) — it's a booking-oriented site, so the CTA points there as "see more," not as a promise of an automated on-page scan.
9. **Footer links** — Upwork profile, YouTube, Pocket CEO, hardcoded since they never change per job.

**Visual language, 14.08.2026:** matched to a single reference site rather than a generic dark-hero SaaS template — warm cream ground, serif display headline, terracotta accent. Don't drift back toward a stock dark-hero-plus-white-cards look; that was the first draft and got replaced for a reason.

**Design pass via `impeccable bolder`.** The verdict on the previous version: layout was right, per-section design was boring, "soll wirklich ein Weltklasse-Design sein." What actually fixed it, in order of impact:

1. **Art direction per section, not one uniform surface.** Every section used to be cream + a 1px divider + a centered serif title, eight times running — that repetition *was* the boringness. Now the page runs light → light → light → **ink full-bleed** → **warm band** → light → light. The palette didn't change; the existing `--ink` and `--bg-band` tokens just went from decoration to real surfaces. Reach for proportion and surface before reaching for new colors.
2. **"How this would work" is the focal moment** and gets the only dark surface, because tools/timeline/budget/next-step is what a client actually scans for. It's also **2×2, not 4×1** — four columns inside a 720px measure left each value ~165px wide, which is the concrete reason it read as filler. The band widens to `--measure-wide` (860px) to deliberately break the page rhythm.
3. **The report is a physical object,** not a thumbnail: real `perspective`, a spine gradient, a page-block edge, sheets stacked behind, settling into its angle on reveal.
4. **Motion is per-section, never one uniform fade-on-scroll** (that's the saturated AI default and reads as the opposite of premium). The hero plays one orchestrated entrance on load; the video *settles* rather than slides; the plan's accent rules *draw themselves* left-to-right like a spec sheet being ruled up; the report swings into place; testimonials get no entrance at all, only hover. All easing is ease-out-expo, no bounce.
5. **Reveals are opt-in at runtime.** JS adds `.anim` to `<body>` before any reveal state applies, so a no-JS or headless render ships the fully visible page instead of a blank one. Verified with `--disable-javascript`. Never gate content visibility on a class-triggered transition.

**Theme layer.** All colors live in one `:root` token block at the top of the template, and every rule reads from it — no hardcoded hex below that block. This exists so the "derive the client's industry from the posting and theme the page to them" idea is a ~6-variable override rather than a rewrite. Keep it that way: a new hardcoded color anywhere below the token block breaks the feature before it's built.

**Contrast is checked, not eyeballed.** `--text-3` (#6f6656) is 4.5:1 on cream; `--accent-on-ink` (#e08a5c) exists because plain `--accent` is only 4.44:1 on `--ink` and fails small body text there. It's a legibility variant of the same hue, not a second brand color. Check any new muted tone against its actual background before using it for real copy.

**Figma is no longer in this pipeline, and that was a deliberate swap (14.08.2026).** The exported PNG could not be read at phone size, carried baked-in whitespace nobody could crop, cost ~270KB a page, and could never follow a theme. The node list plus a runtime renderer fixes all four and adds editing. Don't reintroduce an image export for the diagram; if a static copy is ever needed, the editor's own PNG button produces one from the same data.

**Anti-pattern discipline, from a real `impeccable audit` run (14.08.2026):** section headings are real serif `<h2>`s matching the hero's voice ("What I'd build", "How this would work", "What clients say"), not a tiny uppercase-tracked eyebrow repeated above every section — that specific pattern is impeccable's own named AI tell ("appears on 55-95% of generations regardless of brief"). Don't reintroduce it. Body text against the cream background must clear 4.5:1 contrast — the original `--text-3` token (`#948a7b`) failed at 2.96:1 and was bumped to `#6f6656` (4.93:1); if a future edit adds a new muted-gray token, check its contrast against `--bg` before using it for real content, not just decorative dividers.

This page's "why me" text is a different, shorter piece of writing than the Upwork proposal itself — `upwork-proposal` writes the 150-250 word submitted proposal (needs the walkthrough transcript); this page's fit points don't require the transcript. Don't duplicate one into the other.

## Step 6: Ask for the walkthrough link, or leave the placeholder

The video is the user's own, recorded after seeing the diagram and narrated over it. If there is no link yet, pass `--loom-url` empty (the script defaults to a visible placeholder anchor) and tell him plainly the page is missing the video link, rather than inventing one or silently shipping without it.

## Step 7: Assemble the page

```
python3 .claude/skills/upwork-pitch-page/scripts/generate.py <job_id> \
  --hook "Your <their system>, explained in under 3 minutes" \
  --fit-point "..." --fit-point "..." --fit-point "..." \
  --graph /path/to/plan.json \
  --hero-illustration "<path or omit>" \
  --loom-url "<url or omit>" --video-length "3 minute" \
  --tool "..." --tool "..." \
  --timeline "..." \
  --budget "..." \
  --kickoff "..." --kickoff "..." \
  --lead-magnet-url "<url or omit>" --lead-magnet-teaser "..." --lead-magnet-cta "..."
```

There is no `--subhead` and no `--diagram-png`. The page carries a single
headline (the subhead, brand row and stat pill were cut —
"lieber minimalistisch"), and the diagram comes from `--graph`. A simple chain
can still be expressed with `--source` / `--step` / `--sink` / `--service`
instead of writing JSON, but `--graph` is the one that handles a real plan.

Writes `jobs/<YYYY-MM-DD>_<job-title-slug>.html` by default (override with `--out`). The script embeds the diagram as a base64 data URI directly in the HTML — one self-contained file, nothing external to break or go stale, and simple to hand to a deploy step later.

**Look at it before calling it done.** A `file://` URL can't be opened by the browser automation tools (blocked as "browser-internal or unparseable") — instead, render a real screenshot with headless Chrome directly and read the image:

```
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --headless --disable-gpu \
  --screenshot=/tmp/pitch_preview.png --window-size=900,1400 "file://<absolute path to the html>"
```

Then use the Read tool on `/tmp/pitch_preview.png`. This is the only way this skill has actually verified its own output — don't skip it and don't just open it in a browser window and assume it's fine.

**Don't trust a narrow `--window-size` on this same headless flag for a mobile check — confirmed unreliable.** A `--window-size=390,...` screenshot showed text and the diagram running off the right edge on every section, looking like a real overflow bug. Ground-truth check (a same-origin `<iframe width:390>` inside a real Chrome tab via the browser tool, reading `scrollWidth` vs `innerWidth` across every element) found zero actual overflow — the CLI screenshot flag just doesn't honor the narrow viewport correctly at that width. If a mobile-width check is ever actually needed, use the iframe/DOM-measurement method, not another narrow `--window-size` screenshot.

## Step 8: Deploy — ask before the first real one

Vercel is the intended host (a token in `~/.config/credentials.env`, per the global CLAUDE.md CLI table) but **no deploy has happened yet in this skill's lifetime** — it's a recommendation, not a confirmed decision. Before running an actual `vercel deploy` for the first time, confirm with the user that static HTML + Vercel is still what they wants (the alternative floated was Next.js, rejected as overkill for what's fundamentally a rendering problem, not an app). Once confirmed once, later runs don't need to re-ask — this is a standing decision after the first yes, not a per-job gate.

## Self-improvement

If the user corrects the tone, the diagram scope, or flags that a page felt generic or overbuilt, that's a signal to sharpen Step 5's guidance — edit this file directly (the same pattern already used in `upwork-screener`'s self-improvement loop), and if a real send produces a page the user particularly liked, consider saving it under `assets/` as a worked example for future runs to match.

**Confirmed corrections, 14.08.2026 ("GHL Expert" run) — already folded into the steps above, kept here as the record of what happened:**

- **No em dashes anywhere in generated copy** — hook, fit-points, tool/timeline/budget/kickoff text, all of it. Em dashes are the clearest AI tell in outgoing copy, so the rule applies here without exception; a first pass on this job's fit-points and timeline used two em dashes and a bare `--`, both had to be rewritten. Re-read every generated string for `—` and `--` before calling a page done, the same pass as the em-dash-check any other outgoing copy gets.
- **The diagram-fill bug is fixed** (`assets/diagram.js`, `shapeFor`): ownership-based tinting used to only apply to `source`/`sink`/`milestone` kinds, so `step`/`datastore`/`actor` nodes stayed plain white even with `owner: "you"` — which is most of a typical diagram, so pages read as monotone (only the `decision` node ever had color). Now the tint applies to any node with `owner` other than `client`/`thirdparty`, matching what the code comment already claimed it did. If a future page still looks flat, check this function first before reaching for new color tokens — the existing accent + tint system was never actually broken by *design*, only by this one gating bug.
- **Node captions (Step 4) and the hero illustration (Step 4c) exist because a diagram that's technically correct isn't automatically understood.** The test for both: could this specific box, or this specific page section, be understood by the person it's for without either of us saying one more word about it? A precise diagram passes "is this accurate," not automatically "is this understood" — those are different bars, and only the second one is what actually gets a client to reply.
- **A knowledge base for tool mechanics now exists:** `context/tool-knowledge/<tool>.md` (see Step 2). Keep it growing — it's what turns "research every time" into "research once, reuse forever," and it's the concrete answer to "the system should improve over time."
