---
name: upwork-screener
description: Searches Upwork on broad terms, scores every result 0-100 against your own niche from context/expertise.md, logs each real candidate to a status-tracked job list, and Slack-DMs only the strong matches. Use on "check upwork", "any new upwork jobs", "run the upwork screener", "/upwork-screener", and once inside /morning. Reads and scores only, never applies. Writing the cover letter is upwork-proposal, the visual pitch page is upwork-pitch-page, and account-side work (messages, invitations, offers) is upwork-inbox.
---

# Upwork Screener

Runs in one pass without asking questions — every step below resolves on its own.

## Cadence: on demand and once inside /morning, never on a loop

Upwork names "running background polling that resembles scraping" as grounds for enforcement,
and permits unattended automation only under an approved API key with real thresholds behind it.
So a `/loop` on a timer is out. **Not because of the volume** — one run makes 20 to 40 calls
against a limit of 40,000 a day, which is nothing. Because of the pattern.

Therefore, on **every** run:

1. **Nothing leaves the account.** This skill reads, and writes to the local job list.
   Applications and messages go out through `upwork-inbox` only, and only on an explicit yes.
2. **Say the call count at the end.** One sentence: "31 Upwork calls." Then "well under the
   limit" is measured rather than assumed.
3. **Then `python3 reference/scripts/upwork_status.py prune`** — Upwork content older than 24
   hours goes (their caching rule), your own scoring stays.

Background and sources: [`reference/upwork-regeln.md`](../../../reference/upwork-regeln.md).

## Why broad search, not narrow

Upwork's search is fuzzy, not exact-match. A three-word compound query does not find the
intersection of those three words; it matches on stray words and returns an unrelated industry.
Measured once: a query naming a client type plus a technology came back full of engineers from a
completely different field.

Narrow queries do not raise precision. They shrink the pool and let good jobs slip past on
wording the query never anticipated — the posting that is exactly your work but is titled after
the tool rather than the outcome, or after the outcome rather than the tool.

So: cast a broad net with plain category words, and make the **scoring** step do the filtering.
That is the whole design. Do not tighten the queries, tighten the score.

## Step 1: Search

**The tracks come from `context/expertise.md` § Search tracks, never from this file.** Setup
writes them from your own answers, and they are the one thing here that is genuinely yours. If
that section is still empty or still carries the example words, stop and say so rather than
searching — a screener running on someone else's niche wastes the run and teaches you nothing.

Call the upwork MCP `find_jobs` (action=`search`, org_uid from `context/config.yaml`),
`verified_payment_only: true`, `sort: "recency"`, `limit: 10` per query, once per track.

Two kinds of track, and a good list has both:

- **Tool-based** — the client already names the platform or category (`SEO`, `automation`,
  `Google Ads`, whatever you actually work in).
- **Needs-based** — the client describes the outcome, not the mechanism (`leads`, `sales`,
  `revenue`). A client posting a plain sales job never says "automation", and a lead-gen system
  is still exactly what you would pitch them. They may be happier with that than with what they
  literally asked for. Credit for the framing: Nick Saraev.

**Casing matters, verified in a real run rather than assumed.** Lowercase `gym` and `seo`
returned zero results while capitalized `Gym` and `SEO` returned normal pools. Whatever casing
sits in `expertise.md`, keep it exactly; do not "clean it up" to lowercase.

One call per track, one raw pool each. **Do not add more specific phrases on top.** If recall
feels low after a few runs, widen the tracks further rather than narrowing back toward compound
niche phrases. The needs-based tracks will surface plenty of jobs with no angle at all, and that
is expected: Step 2's scoring gate is what filters them, not the search. Do not second-guess a
track because most of its pool is noise. The tool-based ones work the same way.

**Rejected tracks are worth writing down too.** When a track turns out to return the wrong
industry entirely — a word that means something else in another field — note it in
`expertise.md` with what it actually returned, so a later run does not re-add it hopefully.

**Skip anything posted more than 2 days ago** — check `created_date` against now before scoring. Speed-to-lead is the whole point (early proposals win on Upwork); a 3-day-old posting has likely already collected dozens of proposals. Don't score it, don't log it, don't fetch its description.

## Step 2: Score every result, 0–100

Four components:

- **Niche fit (0–40)** — read `context/expertise.md` § *Your niche* and § *What counts as a
  strong match*, and score against what is written there. **Give a real bonus for an overlap**:
  a posting that sits where two of your areas meet is worth more than one that sits squarely in
  either, because far fewer people can do both.

  **Not every part of a niche is equally central, and the difference is track record.** Inside
  a broad label like "automation" there is usually a core you have actually delivered and a
  periphery you merely could. A posting in the core earns the full bonus. A posting that is
  technically the same label but in an unrelated domain defaults lower — it should not win
  purely on the label. **This is a default weighting, not an exclusion:** let deal quality and
  client trust pull an out-of-domain posting back up when it earns it (novel problem, strong
  budget, client worth having), and never cap it artificially just for sitting outside the core.

  Where the line runs is in `expertise.md`, not here. When the user corrects a score — "that
  one should not have ranked so high" — that correction belongs in the § *Calibration anchors*
  section of that file, in their words, with the job that triggered it. A calibration written
  down once keeps working; one that stays in the chat is gone tomorrow.

- **Client trust (0–30)** — `client.verification_status` (baseline, already filtered), `client.rating`, and critically the **hire ratio** = `client.total_hires / client.total_posted_jobs`. A client with 300 posted jobs and 2 hires is a time-sink even at 5.0★; weight the ratio, not just the star rating. No hire history yet (brand-new client, `total_posted_jobs` low or absent, or `rating` missing) isn't disqualifying, just score it neutrally rather than high.
- **Deal quality (0–20)** — budget/rate signal, engagement (real ongoing commitment scores higher than a one-off gig-shop posting, but don't hard-exclude short jobs), duration. **A rate above your floor is a bonus inside this component, never a gate.** A job below it can
still be worth notifying when the scope and the client are right — measured once on a CRM build
at $8-17/hr that scored 85 and was correctly flagged as worth taking. Score the rate as one more
input; do not let a large number alone rescue a job with no niche fit or a bad client.
**`contractTerms.hourlyContractTerms.engagementType == "FULL_TIME"` pulls this component down**,
because a freelancer takes on projects rather than something that reads as employment. This is
the API's engagement flag, not the hours-per-week number. `PART_TIME` or unset is neutral.
- **Recency (0–10)** — newer postings score higher, and this matters more than the 10-point cap alone suggests: every candidate here already cleared the 2-day-old cutoff, so within that narrow window a same-day posting still deserves the top of the range and a 40-hour-old one the bottom, not a flat middle score. Upwork rewards early proposals; a 2-week-old posting is likely already buried in proposals.

**Calibration lives in `context/expertise.md` § Calibration anchors, and it is the section that
makes this skill good.** A handful of real jobs with the score they deserve, in the user's own
judgement, beats any rubric written in advance. Two or three anchors are enough to start:
something that should score high, something mid, something that looks relevant and is not.

**The false-positive traps are the same file, § False-positive traps.** These are jobs that look
like a match and are not, and they are worth more than the positive examples, because a
screener's real failure mode is confident noise. Four patterns show up in almost every niche:

- **The right label, the wrong half of the field.** Your discipline has sub-specialisms you do
  not do. The posting uses the umbrella word, so it scores well on keywords and badly in reality.
- **The right label, the wrong depth.** Building *on* a technology and engineering the
  technology itself carry the same words and are different jobs. So do "strategy" and
  "execution", "design" and "production".
- **A posting that contradicts the client's own history.** `find_jobs get` returns
  `client_work_history`. When a generic posting comes from a client whose past hires are all one
  narrow thing, trust the history over the text. Clients hire the same kind of work repeatedly.
- **Ongoing operations wearing a project label.** "100% success rate", "24-hour turnaround",
  "handle hundreds of cases daily", "manage the account long-term". The subject matter can be
  exactly right while the shape is a job rather than a build. The giveaway is volume and SLA
  language, not the topic.

**How a trap gets into that file: it gets there by being wrong once.** When the user says a job
should not have scored that high, write it down as a trap in their words, with the posting that
triggered it. That is the whole mechanism, and it is why the third run of this skill is better
than the first.

**A job describing a manual, repetitive process is a niche-fit signal in the other direction** —
"I currently update this by hand every week", "someone has to check X and enter it into Y". If
automation is anywhere in your niche, score it as though the posting had said so, and note what
is manual in the rationale so a proposal can pitch exactly that.

**Hard gate before anything else uses the score:** a job only counts as a genuine candidate if **niche fit ≥ 20** (out of 40) — this is the filter the search-breadth trade-off depends on. A job can't buy its way past irrelevance with a huge budget or a perfect client; if niche fit is under 20, cap the job's effective status at "logged, not a real match" regardless of total score.

## Step 3: Log every candidate

Read `context/.upwork_jobs.json` (a JSON array; treat a missing or empty file as `[]`). For every job scored **≥ 50 total** that passed the niche-fit gate and isn't already present by `id`:

**Fetch the full description** — `find_jobs` search only returns a truncated `description_snippet`, not the real thing. Call `find_jobs` (action=`get`, org_uid from `context/config.yaml`, the job id) for each qualifying candidate to get the complete description text before writing the record — this is a bounded, already-filtered set (only the ones that clear scoring), not every raw search result, so the extra calls are cheap.

**Skip it entirely if it's already filled.** The `find_jobs get` response includes `data.marketplaceJobPosting.activityStat.jobActivity.totalHired` — if that's ≥1, the client has already hired someone (confirmed in a real test: two jobs in one batch showed `totalHired: 1`). Applying to a filled job is pointless; don't log it at all, don't count it toward anything.

Then append a record:

```json
{
  "id": "<upwork job id>",
  "title": "...",
  "url": "https://www.upwork.com/nx/search/jobs/?q=<url-encoded exact title>",
  "found_at": "<ISO 8601 UTC timestamp — when the screener found it>",
  "posted_date": "<the job's own created_date from the API, verbatim>",
  "summary": "<two or three sentences, see below — this is what the list shows>",
  "description_file": "context/upwork-jobs/<id>.md",
  "score": 92,
  "niche_fit": 35, "client_trust": 28, "deal_quality": 19, "recency": 10,
  "rationale": "<one sentence — why this score, not what's already visible in the Client/Budget/Posted columns>",
  "budget": "<budget field from the API — plus any client note about it worth keeping, see below>",
  "job_type": "hourly|fixed",
  "client": {"rating": 4.96, "hires": 422, "posted": 172, "verified": true, "country": "..."},
  "status": "new",
  "status_updated_at": "<same ISO timestamp>",
  "next_follow_up": null,
  "notes": ""
}
```

**Rationale doesn't repeat the columns next to it.** The dashboard shows Client (rating/hire ratio), Budget and Posted as their own columns, and the rationale is read right beside them, so restating "$500 fixed, client 4.9★" there is wasted space the reader has to skip. Use the sentence for what those columns can't show: what the score is actually betting on, or against — the specific scope risk, the overlap that earned the niche-fit bonus, the giveaway that dropped it, whatever a proposal would need to lead with.

**The full description does not go in this file.** Write it to `context/upwork-jobs/<id>.md` and put the path in `description_file`; the record itself carries a **`summary`** of two or three sentences instead. Measured on a real run: full texts were 40 of the file's 83 KB, nearly half, at only 19 jobs — and scanning a list needs the title, the score and a sentence of context, not 5,000 characters of posting. The full text is still needed, but only once a job is actually being applied to, and then only that one. `upwork-proposal` and `upwork-pitch-page` read the file it points at; everything else reads the summary.

**What belongs in a summary:** what the client wants built, the one thing that makes this job distinctive (a hire ratio, a deadline, an unusual constraint, a screening requirement). What does not: anything already visible in its own column, **and anything the rationale is about to say.** The dashboard prints the two under separate headings — "Description" and "Why this job" — so a summary that ends on the same judgement the rationale makes shows the reader the same sentence twice.

**Leave `summary` out and the list falls back to the rationale.** Nothing breaks, but the detail view then has the same line under both headings, so the field is worth writing.

**Budget keeps the client's own framing, not just the number.** When the posting says more than a bare figure — a bonus structure ("$400/mo + up to $130/mo performance bonus"), a milestone framing ("$100 first milestone, more after"), a rate that looks like a placeholder — fold that into the `budget` string itself rather than reducing it to the number alone. The Budget column renders whatever's in the field verbatim, so this is the only place that context survives.

**On the URL — verified the hard way.** `find_jobs` never returns a working public job link; the `id` it returns is an internal numeric ID, not the `~<ciphertext>` a real `upwork.com/jobs/~...` URL needs (confirmed: constructing one from the numeric id and calling `find_jobs get` on it fails with "resource not found"). There's no ciphertext field anywhere in the API response to build a direct link from. The reliable fallback is Upwork's own public search page with the exact job title as the query — it won't always be the single top result, but it gets the user to the job without a broken link. If Upwork's API ever starts returning a real ciphertext, switch back to a direct link; until then, don't reintroduce the `~<id>` pattern.

`found_at` and `posted_date` are different things — don't conflate them. `posted_date` is when the client posted the job (what the dashboard's "posted X ago" is computed from); `found_at` is when this screener happened to see it.

Never touch or re-score a job `id` already in the file — it's owned by whatever status it's since moved to (a human may have marked it `proposal_sent`). Skip it entirely, don't even overwrite its score.

Trim the file to the most recent 500 records by `found_at` after appending, so it doesn't grow forever — but never trim a record whose `status` is anything other than `new` or `notified` (an active pipeline entry — `proposal_sent`, `interviewing`, etc. — never gets silently dropped just because it's old).

Write the file back with `Write` (it sits inside this repo's `context/`, in scope for the edit tools).

## Step 3b: Pull the application picture for the best open jobs

Search gives you title, budget and client rating. What actually **decides** an application comes
only from `find_jobs action=get`, and that is one call per job.

So keep it tight: **the 5 highest-scoring open jobs (`new`/`notified`) that have no `details`
field yet.** Not the whole list, not again every run. Fetching a hundred of them one by one is
exactly the pattern Upwork reads as scraping
([`reference/upwork-regeln.md`](../../../reference/upwork-regeln.md)).

Per job, write into the record:

```json
"details": {
  "fetched_at": "<ISO>",
  "connects_cost": 22,
  "bid_avg": 17.74, "bid_min": 8, "bid_max": 75,
  "invites_sent": 4, "total_hired": 0, "total_offered": 0,
  "min_jss": 0, "min_earnings": "Any", "min_hours": 0,
  "engagement": "PART_TIME", "experience_level": "EXPERT",
  "client_country": "Australia", "client_city": "Brisbane",
  "client_timezone": "Australia/Brisbane",
  "screening_note": "application must begin with the words \"BLUE HERON\""
}
```

Where the fields come from: `connects_cost` · `activityStat.applicationsBidStats` ·
`activityStat.jobActivity` · `preferred_qualifications` · `contractTerms` ·
`clientCompanyPublic`.

**`screening_note` is not an API field.** It sits in the description text ("begin your
application with…", "include the word…") and is recognised while reading. Leave the field out
when the posting has no such instruction. It is worth catching precisely because it is invisible
to every other filter: miss it and a good proposal is discarded unread.

**Two things feed straight back into the scoring:**

1. **A missed minimum bar is an exclusion, not a deduction.** If the job demands a Job Success
   Score above yours or more lifetime earnings than you have — both in `config.yaml` under
   `upwork.profile` — applying is burnt connects. Set the status to `archived` with
   `--note "below the client's minimum bar"`.
2. **`total_hired ≥ 1` means taken.** Same rule as Step 6, just applied earlier.

At the end of the run, refresh your own figures so the comparison does not go stale:
`get_profile action=get` returns `profileAggregates.totalEarnings` and the rest, which belong in
`context/config.yaml` under `upwork.profile`.

## Step 4: Notify — signal only, never noise

Among the jobs newly logged this run (not ones already seen), collect those with **niche fit ≥ 20 AND total score ≥ 70**. If there are none, send nothing — silence is correct, not a failure.

If there are one or more, send a **single** Slack DM (not one per job) via the Slack MCP, to the `slack_channel_id` in `context/config.yaml` — the setup skill asks for it and leaves it empty if you don't use Slack. **Empty means skip the DM entirely**, not fall back to some other channel; the dashboard still logs everything either way. List per job: score, title, one-line rationale, budget, client rating + hire ratio, and the link. Then set those jobs' `status` to `"notified"` in the JSON file (rewrite their records).

## Step 5: Status is a small CRM — use `reference/scripts/upwork_status.py`

The job list isn't just a feed, it's a lightweight pipeline: `new → notified → proposal_sent → interviewing → offer_sent → hired` (or `rejected` / `archived` at any point). The Command Center's Upwork tab groups this into three board columns — **Outreach** (`new`/`notified`/`proposal_sent`), **In Kontakt** (`interviewing`) and **Angebot versendet** (`offer_sent`) — plus a collapsed "Abgeschlossen" section for `hired`/`rejected`. When the user says something like "mark the SEO strategist job as proposal sent", "the client replied on &lt;job&gt;" or "I sent them an offer for &lt;job&gt;", update it with:

```
python3 reference/scripts/upwork_status.py set <job_id> proposal_sent --follow-up +3d
python3 reference/scripts/upwork_status.py set <job_id> interviewing
python3 reference/scripts/upwork_status.py set <job_id> offer_sent --follow-up +3d
```

`--follow-up +3d` sets `next_follow_up` three days out (Upwork's normal response window) — use it on `proposal_sent` and `offer_sent`, omit it for statuses that don't need a follow-up date (`interviewing`, `hired`, `rejected`, `archived`). The Command Center's Upwork tab reads `next_follow_up` and flags anything due, so this is the actual follow-up-control mechanism — it's not automatic, it runs off what gets marked here. The dashboard's own stage-move buttons ("Antwort bekommen", "Angebot geschickt", "Gewonnen"/"Abgelehnt") just copy a sentence like the ones above to paste into chat — the dashboard itself never writes anything (Regel 8, reine Ansicht).

## Step 6: Reconcile — jobs sitting in the list can get filled by someone else

Before searching for new jobs (Step 1), pick up to 5 of the oldest still-open records (`status` is `new` or `notified`) whose `status_updated_at` is more than 1 hour old — checking again within the hour just repeats the same answer, confirmed by rechecking the same 5 jobs twice within 10 minutes and getting identical `totalHired: 0` both times. If nothing qualifies (everything open was already checked recently), skip this step entirely for this run. Otherwise, re-fetch the qualifying records with `find_jobs` (action=`get`). If `activityStat.jobActivity.totalHired` is now ≥1, someone else got hired — set `status` to `archived` and don't count it as active anymore. This is the same check as the "skip if already filled" rule in Step 3, just applied backwards in time to jobs that were open when first logged. Keep it to 5 per run — this is upkeep, not the main job, and doesn't need to sweep the whole list every 15 minutes.

## Self-improvement

Two signals, and they land in different files:

- **A correction about a specific job** ("that one shouldn't have scored that high", "why did
  this get through") → `context/expertise.md`, as a calibration anchor or a false-positive trap,
  in the user's own words with the posting that triggered it. That file is theirs, and this is
  how it gets good.
- **A correction about the method itself** ("you're underrating budget across the board", "the
  hard gate is too tight") → this file, because it applies to everyone running the skill.

The distinction matters: put a personal calibration in here and the next person to pull an
update inherits someone else's niche. Put a method fix in `expertise.md` and it is lost the
moment they rewrite that section.
