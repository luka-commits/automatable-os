---
name: upwork-pitch-page
description: Generates a short, self-contained pitch webpage for ONE specific Upwork job you want to apply to — an interactive solution diagram built from the job's actual requirements, a slot for your own Loom walkthrough, and a tight "why this fits" pitch, as a single static HTML file you can send alongside your proposal. Use when you say "generate the pitch page for job <id>", "make a pitch page for this job", click the equivalent dashboard action, or ask for a visual/diagram to accompany an Upwork application. On-demand per job only — never run automatically for every job the screener finds. Not for writing the Upwork proposal text itself (that's `upwork-proposal`) and not for finding/scoring jobs (that's `upwork-screener`).
---

# Upwork Pitch Page

Turns one already-qualified Upwork job into a short webpage you can link from your proposal: a
solution diagram drawn from the job's actual requirements, a slot for the Loom video you record
yourself, and a tight pitch paragraph. One universal template for every niche — the page structure
doesn't change, only the content does.

## Step 1: Get the job

Read `context/.upwork_jobs.json`, find the record by `id`. If you name a job by title instead of
id, match on `title` and confirm which one before proceeding — don't guess between near-duplicates.

## Step 2: Research the technical approach, if the problem isn't already familiar

For a job whose solution shape is genuinely unclear (not "another routine automation" but
something with real technical uncertainty), use `/last30days` to check current best-practice
patterns before building the diagram — combine that with what your own track record already
proves works (`context/experience.md`). Skip this step for jobs that are clearly inside
well-trodden territory; researching every job would be research theater, not diligence.

## Step 3: Build the solution diagram

The diagram is not a static image you draw and export — it's a small JSON graph that
`generate.py` embeds, and the page itself renders it at runtime as an interactive SVG (pan, zoom,
drag nodes, rename, even a "PNG" export button for the viewer). You write the graph directly; no
external diagramming tool is required.

Two ways to pass it, mutually exclusive:

- **`--graph '<json>'`** (or a path to a `.json` file) for anything with branches, parallel
  tracks, or phases — most real implementation plans. Shape:
  ```json
  {"nodes": [{"id": "a", "label": "New lead form", "kind": "source"},
             {"id": "b", "label": "Enrich with AI", "kind": "step", "logo": "openai"},
             {"id": "c", "label": "CRM + Slack alert", "kind": "sink"}],
   "edges": [{"from": "a", "to": "b"}, {"from": "b", "to": "c", "label": "if qualified"}],
   "groups": [{"label": "Milestone 1", "nodes": ["a", "b"]}]}
  ```
  `kind` is one of `source, step, sink, service, decision, note, datastore, milestone, actor`.
  `owner` (optional, one of `you, client, thirdparty`) colors the node by who's responsible for
  it — a sales argument rendered as color: what you'd build is accented, what the client already
  runs stays plain, third-party services stay dashed. `logo` (optional) embeds a real brand mark
  if the slug exists in `assets/logos/` (run `fetch_logos.py` to (re)populate that cache from the
  fixed `WANTED` list in the script; extend that list and re-run if a tool you need isn't there
  yet — never fabricate a logo for one that's missing, the node just falls back to its shape).
- **`--source / --step / --step / --sink [--service "X@2"]`** for a simple linear chain (2–4
  steps, at most 2 supporting services) — the shorthand for jobs that really are just
  trigger → steps → destination.

Keep the diagram to what the client actually asked for in *this* milestone. If the posting scopes
a small first build with room to expand later, diagram only the small build — the roadmap becomes
a line in the pitch text (Step 4), not speculative nodes the posting doesn't support.

## Step 4: Page structure

Order: headline → video (full width) → 3 fit points below it → social proof (real testimonials) →
collapsible background/CV → the diagram ("What I'd build") → the scope block ("How this would
work") → an optional lead-magnet showcase ("See what we can do") → footer. Nav bar segments:
Walkthrough / What I'd build / How this works / Proof / Next step.

1. **Headline** — the page's only headline (`--hook`). No subhead, no pill, no name banner above
   it; the page opens straight on the H1. Pattern: "What your `<concrete system>` would look
   like" — it must clearly reference *this* job, echoing language or the concrete ask from the
   actual posting, not a generic pitch that could sit on any page.
2. **Video, full width** — the Loom slot (Step 5), the first thing after the headline. A
   "progress bar" of 3–4 short chapter labels (`--chapter`, repeatable) sits under the player, so
   what's in the walkthrough is visible before the click.
3. **3 fit points** below the video — a 3-column row (stacks to 1 column under 640px), each
   marked with a filled accent-color checkmark icon instead of a numeral. Pull the 3 points from
   `context/experience.md` — pick entries that genuinely fit this job's domain, never force one
   that doesn't apply, never state a number that isn't in that file. Pass via `--fit-point`
   (exactly 3).
4. **Social proof** — real Upwork review text (never video links, never invented quotes). Your
   own testimonials live in `context/testimonials.json` (copy `context/testimonials.json.example`
   to start; see its schema below); `generate.py` reads all of them by default (`--max-testimonials`
   to cap). If that file is empty or missing, the section renders an honest "Testimonials not
   added yet." line instead of being padded or skipped.
5. **Collapsible background/CV** — collapsed by default (`<summary>More about my background</summary>`).
   Fully data-driven from `context/experience.md`, passed through as flags — nothing is
   hardcoded in the template:
   - `--stat "value|label"` (repeatable) — track-record numbers, e.g. `--stat "$10K+|Earned on Upwork"`.
   - `--trait "..."` (repeatable) — real client-sourced trait tags (e.g. Upwork's own "Insights
     from completed jobs" tags), never self-description.
   - `--client "..."` (repeatable) + `--client-note "..."` — notable past clients/companies, plus
     an optional trailing clause about scale.
   - `--background "role|institution"` (repeatable) — employment and education.
   - `--languages "..."` — one line.
   Every one of these is optional and independently omitted if you don't pass it. If you pass
   *none* of them, the whole block renders one honest "Background details not added yet --
   fill in context/experience.md." line instead of an empty, oddly-shaped panel.
6. **What I'd build** — the diagram from Step 3, full width, interactive.
7. **How this would work** — a 2×2 scope block on a dark surface (the page's one deliberate
   contrast moment — tools/timeline/budget/next-step is what a client actually scans for), each
   quadrant with its own icon: Tools (`--tool`, repeatable), Timeline (`--timeline`), Budget
   (`--budget` — a rough, honest framing, not a precise quote), and what's needed from the client
   to kick off (`--kickoff`, repeatable, labeled "To get started, I'd need"). Never pad any of the
   four with generic filler ("communication," "patience") — every line should be something a
   client could actually check off.
8. **"See what we can do"** (optional) — a lead-magnet showcase: teaser copy + CTA
   (`--lead-magnet-url`, `--lead-magnet-teaser`, `--lead-magnet-cta`), optionally with a tilted
   cover image of a real past deliverable (`--lead-magnet-cover /path/to/image.jpg` — a report,
   a screenshot, anything that shows the quality of your work). Without a cover image the section
   runs copy-only, centered, instead of leaving a blank gap where the image would sit. Without a
   URL at all it renders "Lead magnet not added yet." Same honesty rule as testimonials: a real
   asset or an honest placeholder, never invented copy.
9. **Optional bonus row** — a link to a public workspace (Whimsical, Miro, whatever you use)
   with more diagrams you've mapped for other clients (`--proof-link-url`). Unlike the sections
   above, this one is just omitted entirely when unset — it's a bonus, not a core trust section.
10. **Footer links** — your Upwork profile (`--profile-url`, required — no built-in default, on
    purpose), plus YouTube (`--youtube-url`) and your own site (`--site-url`) only if you set
    them. Source all three from the Portfolio links section of `context/experience.md`.

**Visual language.** The packaged default aesthetic — warm cream ground, serif display headline,
terracotta accent — is a starting point, not a fixed brand. All colors live in one `:root` token
block at the top of `template.html`, and every rule reads from it, so restyling to your own
brand is a ~6-variable override, never a rewrite. If `context/config.yaml` has an `accent_color`
(and optionally a `brand_reference` site you want to match) use those; otherwise the packaged
default works out of the box. Keep the token discipline either way: a new hardcoded color anywhere
below the token block breaks that swap for whoever tries it next.

**Contrast is checked, not eyeballed.** `--text-3` (#6f6656) is 4.5:1 on `--bg`; `--accent-on-ink`
(#e08a5c) exists because plain `--accent` fails small body text on `--ink`. Check any new muted
tone against its actual background before using it for real copy.

**Art direction per section, not one uniform surface.** The page runs light → light → light →
ink full-bleed → warm band → light → light, deliberately breaking the "cream + divider + centered
serif title" repetition that reads as boring at scale. Motion is per-section, never one uniform
fade-on-scroll: the hero plays one orchestrated entrance on load, the video settles rather than
slides, the plan's accent rules draw themselves left-to-right like a spec sheet being ruled up,
the report (if present) swings into place, testimonials get hover only. All easing is
ease-out-expo, no bounce. Reveals are opt-in at runtime (JS adds `.anim` to `<body>` before any
reveal state applies), so a no-JS or headless render ships the fully visible page, not a blank
one — verify this if you ever touch the animation script.

**Anti-pattern discipline.** Section headings are real serif `<h2>`s matching the hero's voice
("What I'd build", "How this would work"), not a tiny uppercase-tracked eyebrow above every
section — that specific pattern is a well-documented AI tell. Don't reintroduce it.

This page's "why me" text is a different, shorter piece of writing than the Upwork proposal
itself — `upwork-proposal` writes the 150–250 word submitted proposal (needs your Loom
transcript); this page's fit points don't require the transcript. Don't duplicate one into the
other.

## Step 5: Ask for the Loom link, or leave the placeholder

The video is yours — you record it after seeing the diagram, narrating over it. If you haven't
sent a link yet, pass `--loom-url` empty (the script defaults to a visible placeholder anchor) and
say plainly that the page is missing the video link, rather than inventing one or silently
shipping without it.

## Step 6: Assemble the page

```
python3 .claude/skills/upwork-pitch-page/scripts/generate.py <job_id> \
  --hook "..." \
  --fit-point "..." --fit-point "..." --fit-point "..." \
  --graph '{"nodes":[...],"edges":[...]}' \
  --loom-url "<url or omit>" --video-length "3 minute" \
  --chapter "..." --chapter "..." --chapter "..." \
  --tool "..." --tool "..." \
  --timeline "..." \
  --budget "..." \
  --kickoff "..." --kickoff "..." \
  --profile-url "https://www.upwork.com/freelancers/~..." \
  --stat "..." --trait "..." --client "..." --background "..." --languages "..." \
  --youtube-url "<optional>" --site-url "<optional>" \
  --lead-magnet-url "<optional>" --lead-magnet-teaser "..." --lead-magnet-cover "<optional path>"
```

Writes `jobs/<YYYY-MM-DD>_<job-title-slug>.html` by default (override with `--out`; see this
repo's `CLAUDE.md` — `jobs/` is the shared, gitignored home for generated per-job artifacts). The
script embeds the diagram data and any images as base64 directly in the HTML — one self-contained
file, nothing external to break or go stale, simple to hand to a deploy step later.

**Look at it before calling it done.** A `file://` URL can't be opened by the browser automation
tools (blocked as "browser-internal or unparseable") — instead, render a real screenshot with
headless Chrome directly and read the image:

```
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --headless --disable-gpu \
  --screenshot=/tmp/pitch_preview.png --window-size=900,1400 "file://<absolute path to the html>"
```

Then use the Read tool on the screenshot. This is the only way this skill has actually verified
its own output — don't skip it and don't just open it in a real Chrome window and assume it's
fine.

**Don't trust a narrow `--window-size` on this same headless flag for a mobile check.** A
`--window-size=390,...` screenshot can show text and the diagram running off the right edge on
every section, looking like a real overflow bug, when the CLI screenshot flag simply doesn't honor
the narrow viewport correctly at that width. If a mobile-width check is ever actually needed, use
a same-origin `<iframe width:390>` inside a real Chrome tab (via the browser tool) and compare
`scrollWidth` to `innerWidth` across elements — ground truth, not another narrow screenshot.

## Step 7: Deploy — ask before the first real one

Vercel is the intended host (token `VERCEL_TOKEN` in your credentials) but confirm with the user
that static HTML + Vercel is what they want before running an actual `vercel deploy` for the first
time in this repo — a static HTML file is fundamentally a rendering problem, not an app, so a
heavier framework is very unlikely to be the right call, but it's still their decision to make
once, not yours to assume. After the first yes, later runs don't need to re-ask — it becomes a
standing decision, not a per-job gate.

## Self-improvement

If the user corrects the tone, the diagram scope, or flags that a page felt generic or overbuilt,
that's a signal to sharpen Step 4's guidance — edit this file directly (the same pattern used in
`upwork-screener`'s self-improvement loop), and if a real send produces a page they particularly
liked, consider saving it under `assets/` as a worked example for future runs to match.

## Reference: `context/testimonials.json` schema

Copy `context/testimonials.json.example` (starts as `[]`) to `context/testimonials.json` and add
real reviews as you collect them:

```json
[
  {"quote": "The exact review text.", "job": "The job title it was left on", "rating": 5.0}
]
```

`price` is accepted too if you want to keep it for your own records, but only `quote`, `job`, and
`rating` are rendered on the page. Never invent an entry — an empty file is honest; a fabricated
review is not.
