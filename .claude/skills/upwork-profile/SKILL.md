---
name: upwork-profile
description: Audits and fixes your own Upwork profile (title, overview, skills, portfolio, rate, video), each finding with its cost and finished text to paste in. Guides profile setup from scratch when none exists. Use on "check my Upwork profile", "profile audit", "my profile isn't getting invitations", "I want to start on Upwork". Job search is upwork-screener, proposal text is upwork-proposal.
---

# Upwork Profile

The profile decides before any proposal gets read: it determines whether you show up in search
at all, and it is the first thing a client opens after the cover letter. A weak profile makes
every application more expensive, because it has to work against your own presence.

**One process, two starting points.** If a profile exists, it gets audited and improved. If
none exists, that is the same path from zero: the criteria below are identical, there is just
nothing to audit yet. For the empty case: `references/onboarding.md`.

## The guardrails

**`reference/upwork-regeln.md` is the truth.** That file holds the limits with sources and
numbers. Here only what that means for this skill in practice:

1. **Writing needs an explicit yes, per change.** The profile is the public face; a silently
   overwritten title would be expensive and would only surface once the invitations stop.
   Same approval pattern as `upwork-inbox`: draft, show, wait.
2. **On request, not on a schedule.** A profile changes over weeks, not hours. One audit a
   month is plenty; a recurring run would be exactly the polling pattern the rules file names
   as grounds for suspension.
3. **Name the number of Upwork calls at the end.** One sentence is enough: "3 calls." A normal
   run needs three.

## Step 1: Get the current state

`list_accounts` returns the `org_uid` (once per session, then remember it, and **never hardcode
it**, this skill should run on any account). Then two calls:

```
get_profile action=get                # title, overview, skills, languages, education,
                                      # employment, rate, aggregates, location
get_profile action=list_highlights    # portfolio projects and certificates
```

If `action=get` returns nothing or an empty profile, that is the onboarding case:
`references/onboarding.md`, then back here.

**What these two calls do not return** is documented in `reference/upwork-mcp.md`, which is the
one place that tracks what the Upwork MCP actually gives you. The short version for this skill:
Job Success Score, client review texts, billed hours, portfolio contents (titles only) and
whether an intro video exists all live on the public profile page, not in the API. Two ways to
get them, and the first is the better one:

- **Ask.** The numbers sit visibly on the user's own profile page. Someone who reads them out
  saves the fetch entirely.
- **Fetch once.** A single, manually triggered fetch of the user's own public profile page via
  `playwright-cli`. Once, never in a loop and never on a schedule: the rules file judges the
  pattern, not the volume.

If the JSS is still missing afterwards, that is no reason to stop. The audit runs without it,
and the gap gets named rather than estimated.

## Step 2: Assess

**Read `references/winning-formula.md` before judging anything.** It holds the eight patterns
shared by three real top-earning profiles (pulled through the MCP, $295K to $1.09M earned)
plus Jono Catliff's bio formula, including his S/A/B/C ranking for which proof belongs at the
top. Those eight points are the measuring stick the table below applies; without them the
assessment falls back on taste.

Two warnings from that file that matter while assessing: **never hold a beginner against those
three head-on** (what transfers is the form, not their 734 jobs), and **an invented number is
worse than a missing one**, because the first call exposes it.

Every row of the table is a finding. **A finding without a consequence and without finished
replacement text is worthless.** "Title: 6/10" tells nobody what to do. So always: what it is,
what it costs, and the concrete better text.

| What | How it is measured | Why it counts |
|---|---|---|
| **Title** | Does the target field come first? Is it concrete rather than generic ("GoHighLevel Expert" beats "Automation Professional")? Does it use the space? | The title is the strongest search field and the only line that always travels with you in result lists. Around 70 characters, though the form is the truth, not that number. |
| **Overview, first two lines** | Do the first ~250 characters say what the client gets? Or is it a greeting and a CV? | Everything after that sits behind "more" and rarely gets opened. Those two lines carry the decision. |
| **Overview, the rest** | Concrete projects with outcomes instead of adjectives. Numbers that can be backed up. | Evidence convinces, self-description does not. |
| **Skills** | Do they cover the niche actually being applied to? Do they contradict the title? | Skills are filter fields in client search. A skill outside the niche pulls in the wrong invitations. |
| **Portfolio** | Count, and whether the project title names an **outcome** rather than just the activity. | Project titles with a measurable outcome clearly beat generic ones. |
| **Certificates** | Present, and relevant to the niche? | An empty field is trust surface given away. |
| **Video** | Present? For the content: `references/video.md` | A profile with a video stands out in a list without them. |
| **Rate** | Relative to earnings, JSS and the kind of projects being targeted. | Too low attracts the wrong clients, too high without evidence puts people off. |
| **Completeness** | Education, employment, languages, availability all set? | Gaps read as half-hearted, and some of these fields are filters. |
| **Consistency** | Do title, overview, skills and portfolio tell **the same** story? | The most expensive mistake and the least visible one: the title promises A, the portfolio shows B, and the client believes neither. |

**Ask the consistency question first, not last.** It often explains why a profile brings no
invitations despite decent individual parts, and it changes what needs doing to those parts.

**Never round up a profile number and never invent one.** What is not in the data is an open
question for the user, not an assumption.

## Step 3: Propose the fixes

**What the API can change is limited, and that determines the shape of the fixes.** The full
picture is in `reference/upwork-mcp.md`; what matters here is that `update_profile` can write
availability, employment, languages, education and other experience, and cannot write title,
overview, skills, hourly rate, portfolio or video. That limit lands on precisely the fields
that decide whether invitations arrive, which is why this skill hands over finished text rather
than promising changes it cannot make. The division of labour that follows:

- **Title, overview, skills, rate, portfolio:** deliver finished text to paste in on
  upwork.com. The text has to be usable, not described: the complete new overview, not "I would
  sharpen the opening".
- **Availability, employment, languages, education:** offer via `update_profile`. The tool
  returns a draft and only executes it after `confirm_draft`. Call that confirmation only after
  an explicit yes, one change at a time.

**Prose is copy, so it follows `context/EMAIL_STYLE.md` when that exists.** Title and overview are copy that goes out. No dashes in
outgoing copy.

**For the title and the first two lines: five to eight variants with different angles**
(niche first, outcome first, tool first, audience first, and so on), not five rewordings of the
same idea. Picking is faster than explaining why a suggestion missed.

## Step 4: Update the reference files

The audit pulls fresh profile data, which leaves two files in the workspace stale, and two
truths about the same thing are worse than one old one:

- `context/experience.md`: track record, key numbers, projects. Source for
  the fit points in `upwork-pitch-page` and for `upwork-proposal`.
- `context/testimonials.json`: the real review texts (list of
  `quote`, `job`, `rating`, `price`). Only touch it if the reviews were actually refetched in
  this run; otherwise leave it alone.

Name changed numbers instead of silently overwriting them: "earnings old to new, JSS old to new"
is the line worth reading.

## Step 5: Output

The verdict first, in two sentences: what is holding the profile back right now. Then the
findings, sorted by impact rather than by the order of the table. Then the finished texts.

The number of Upwork calls at the end.

**No overall score.** A single grade feels precise and is invented; sorting by impact does the
same job honestly.

## Dependencies

Part of the same setup, so worth carrying along when this moves into the template:
`playwright-cli` (the one-off profile page fetch), `video-analyzer`
(video branch), `upwork-screener` / `upwork-proposal` / `upwork-inbox` (same account family).

## Self-improvement

Two signals: a text suggestion gets rejected, or an assessment gets contradicted ("that is
not a problem" / "you should have caught that").

- **Tone** of a suggestion goes to `context/EMAIL_STYLE.md`, not here.
- **Assessment criteria** go in as a row in the Step 2 table.
- **A recurring finding with a good fix** goes to `references/beispiele.md` as an example
  (create it the first time).

For anything else, ask: "Should this go in permanently?" and on yes, work it in with
`skill-creator`.
