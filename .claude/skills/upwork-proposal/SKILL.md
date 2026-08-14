---
name: upwork-proposal
description: Writes the cover letter and screening answers for one specific Upwork job, on a proven formula: proof up front, 5-7 quantified deliverables, a video line, risk reversal, clear CTA. Works with or without a Loom recording. Use on "write a proposal for this job", "apply to this Upwork job", "draft my cover letter", or once upwork-screener surfaces a match worth applying to. Finding and scoring jobs is upwork-screener, the visual pitch page is upwork-pitch-page, answering an existing client thread is upwork-reply. Drafts only, never sends.
---

# Upwork Proposal

Built on Jono Catliff's proposal formula, the one behind his "5-star, Top Plus badge" write-up.
Its own logic: a client skims, so proof goes first, promises carry numbers, risk sits with the
freelancer rather than the buyer, and the letter ends with one obvious next action.

## Guardrails, every run

**Draft only. A proposal goes out when you say so, never before.** Full reasoning in
[`reference/upwork-regeln.md`](../../../reference/upwork-regeln.md); the short version is that
unattended sending costs the account, and the account is the income.

**What the Upwork MCP can and cannot do lives in
[`reference/upwork-mcp.md`](../../../reference/upwork-mcp.md).** Read it there rather than
guessing here. Relevant to this skill: submitting a proposal runs two-stage (draft, then
confirm), which is what makes "draft now, send on approval" natural rather than bolted on.

**Say the call count at the end.** One sentence. Then "well under the limit" is measured.

## Step 1: Gather

Three inputs, and only the first two are required:

1. **The full job listing.** Not a summary. The requirement mirrors in Part A section 5 quote it,
   and the screening answers in Part B need the exact question wording.
2. **Your proof**, from `context/experience.md`. That file is the single source for anything
   about your track record. Nothing about it gets invented here.
3. **The client's name**, if the listing shows one.

**A Loom transcript is welcome but never required.** See Step 3.

## Step 2: Pick the proof that is actually yours

The formula says to stack the strongest proof in the opening. Catliff ranks proof S to C, and the
full ranking with the three top-earner profiles it was checked against sits in
[`upwork-profile/references/winning-formula.md`](../upwork-profile/references/winning-formula.md).

**Place yourself in it honestly before writing a word, because applying the ranking naively
invents credentials you do not have.** Fill the right-hand column from `context/experience.md`
and your Upwork profile, then lead with your strongest real tier and never borrow from a
higher one.

| Tier | Catliff's markers | You |
|---|---|---|
| S | video testimonials, Top Rated, 100% JSS, $100K+ earned | |
| A | 100+ reviews, 100+ projects, major press | |
| B | hours saved, client revenue, named brand work | |
| C | certifications, years in the field, following | |

Most people who need this skill sit in B, and B is not a consolation prize: "cut their
follow-up time from two days to twenty minutes" beats a badge, because it is the outcome the
client is actually buying. An empty S row is not a gap to paper over, it is information about
which proof to lead with.

**So the opening leads with your strongest real tier and claims no badge you have not earned.**
If you have genuine reviews in `context/testimonials.json`, a short quote from one is fair proof
when it fits the job. Writing "Top Rated" or "100% Job Success" into a proposal when you are not
is a lie the client can check in one click, on the same page as the proposal.

## Step 3: The video line, which stays in either way

**The letter always carries a video line. The letter never waits for the video.**

This is the correction that matters most in this skill. The earlier version required a recorded
Loom before it would write anything, and on 14.08.2026 that blocked a real application: good job,
no recording, no proposal. Catliff's formula keeps the line as a visible placeholder precisely so
the freelancer sees what is still missing.

- **No transcript:** write the whole proposal, keep `[INSERT LOOM LINK HERE]` in place, and tell
  the user plainly that this has to be replaced before sending.
- **Transcript supplied:** weave what the recording demonstrated into the requirement mirrors, and drop the
  real link in.

## Step 4: Write Part A, the cover letter

300 to 400 words. Screening answers are separate and do not count toward it.

**For the shape of a finished one, read `references/worked-example.md`** (a real GHL job, run
through the checker). Faster than reconstructing the structure from the seven parts below, and it
shows how the quantified lines actually read when they are not filler.

**1. Greeting, job title, immediate proof.** Two or three sentences. Name the role from the
listing in the first sentence, so the client knows instantly this was written for their post,
then two or three proof points straight away.

**2. "Here's what I'll deliver for your project:"** A numbered list, five to seven items, **every
one carrying a number.**

Here is the trap in that rule, and the resolution:

> **A past-performance number and a delivery promise are different things.** Anything about what
> the user has already achieved comes from `context/experience.md` and gets invented never. Anything about
> what this build will do for this client is a forward promise, where a defensible target is
> legitimate: "answers a new enquiry in under 5 minutes", "0 manual sorting", "inside the 20-30
> hours you scoped". Keep the two kinds distinguishable in your own head while writing, because
> a promise dressed as a track record is the one failure the first call exposes.

Numbers pulled from the client's own posting (their hours, their budget, their tool count) are
the strongest of all, because they prove the listing was read.

**3. The video line.** Step 3.

**4. Risk reversal.** One line, taking the risk off the buyer. Pick by what fits the job size:

- "I work in milestones, not lump sums, so you approve each phase before we move to the next."
- "First sprint is risk-free: we agree a clear milestone and you only pay once it is hit."
- "Free 30-min strategy call before anything is signed. I scope your build live and you decide."
- "If the first deliverable is not what you wanted, you don't pay. Full refund, no questions."

For a new-ish profile the milestone framing is usually the honest one, since it costs nothing to
promise and is how Upwork fixed-price contracts work anyway.

**5. "Here's why I'm the right fit:"** For each major requirement in the listing, a `##` header
paraphrasing that requirement, then two or three lines of proof underneath. Never more than
three. This is the section that makes the proposal feel answered rather than broadcast, so mirror
their words, not your categories.

**6. CTA.** One line, one specific action:

- "Let's hop on a 15-min call to scope this out. When works for you?"
- "Send me a quick message and I'll record a Loom showing exactly how I'd build this for you."
- "Reply with your timeline and I'll send a fixed-price proposal within 24 hours."

**7. Close.** "Thanks for your consideration. Looking forward to hearing from you." then "Best,"
and your first name from `context/config.yaml`.

## Step 5: Part B, the screening answers

Only when the listing actually asks questions. Then, after the close, a visual break and a header:

```
---
**Screening question responses:**
```

Each question in the listing's exact wording in bold, then a one-line answer beneath it, two
sentences at the very most. **These stay out of the cover letter.** Mixing them into the
requirement mirrors is the most common way this formula gets mangled, and it costs the letter its
shape.

## Step 6: Check it, then hand it over

```bash
python3 .claude/skills/upwork-proposal/scripts/check_proposal.py <draft> --job-title "<title>"
```

It counts what is countable: word cap, banned phrasing, em dashes, the video line, how many list
items genuinely carry a number, and whether the opening names the job. It reports risk reversal
and CTA as "check by eye" on purpose, because no regex can tell a real risk reversal from a
sentence containing the word "refund", and a checker that cries wolf gets ignored within days.

**It catches real defects, including in drafts that look finished.** The worked example in
`references/worked-example.md` failed its own quantification rule on the first pass: seven
delivery lines, only four with a number in them. Run it before showing the user anything.

**Phrasing that marks a proposal as generic**, and which the checker fails on: "I would love to",
"I'm excited", "what stood out", "passionate", "results-driven", "I want in", "rockstar",
"ninja". Also out: filler paragraphs, and the grand closing frame ("automation is the future of
business, get on it now"). Say the specific thing instead, and there is no room left for filler.

**Prose that goes to a client is your voice, not the system's.** Read three or four of your own
sent proposals before writing (`list_freelancer_proposals` returns their full text) and match
how you actually open, hedge and close. No em dashes in anything outgoing: they are the most
reliable tell that a machine wrote it, and Upwork does check.

## What to hand back

The proposal ready to paste, the checker's output, and one line naming what still blocks sending:
usually the Loom recording, sometimes a number that needs confirming. Then ask whether to submit,
and wait for the answer.

## Self-improvement

Two signals: the user rewrites part of a proposal, or a proposal wins the job. Either is worth
keeping.

- **A better line or structural fix** goes into this file, at the step it belongs to.
- **A proposal the user liked, or one that won**, goes to `references/` beside the worked example,
  with one line saying what it did well. A second real example beats any amount of instruction.
- **A new verified number about the user's track record** goes to
  `context/experience.md`, never into this skill. One source per fact.
