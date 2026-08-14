---
name: upwork-screener
description: Searches Upwork for jobs, scores them against your own configured niche (see `context/expertise.md`), logs every real candidate to a status-tracked job list, and Slack-DMs the strong matches when Slack is configured. Use whenever the user says "check upwork", "any new upwork jobs", "run the upwork screener", "/upwork-screener", or when invoked on a schedule (via /loop or headless) for continuous job screening. Not for writing a proposal/cover letter for a specific job — that's the separate `upwork-proposal` skill.
---

# Upwork Screener

Runs unattended, often headless via `/loop`, with nobody there to answer a question. Every step below must resolve on its own — never stop to ask.

## Why broad search, not narrow

Upwork's search is fuzzy, not exact-match. A narrow compound query — stringing several niche words together at once — returns a grab-bag of unrelated results; Upwork matched on stray words, not the phrase. Narrow queries don't raise precision, they just shrink the pool and let good jobs slip past on wording the query didn't anticipate (a job that's a perfect fit might be titled in pure tool/platform jargon and never use any of your outcome words, or the other way around). So: cast a broad net with plain category words, and make the **scoring** step do the actual filtering. That's the whole design — don't tighten the queries, tighten the score.

## Step 1: Search

Call the upwork MCP `find_jobs` (action=`search`, `org_uid` — read from `context/config.yaml` → `upwork_org_uid`; this is set automatically by the setup skill during onboarding via the Upwork MCP account/profile call, you shouldn't need to find it yourself), `verified_payment_only: true`, `sort: "recency"`, `limit: 10` per query, once for **each search track listed in `context/expertise.md` under "Search tracks."**

Read those tracks fresh from that file each run — don't cache them here or invent your own. They come in two flavors, and a good list has both:

**Tool-based** — the client already knows the platform or category they want.
**Needs-based** — the client describes the outcome they want, not the mechanism. A client posting a plain marketing/sales/ops job rarely names your specific service, but the underlying work might still be exactly what you'd pitch — and they may be happier getting that than what they literally asked for.

**Casing can matter — verified in a real test run, not a guess.** A lowercase single word has returned zero results on Upwork's search while the capitalized version of the exact same word returned a normal pool. If a track in `context/expertise.md` is written with particular casing, use it exactly as written — don't "clean it up" to all-lowercase.

If a track's results skew heavily toward unrelated content (a broad word that mostly matches media/hobby content about a topic rather than businesses that need the service), that's worth dropping or narrowing — but make that call once, by editing the track in `context/expertise.md`, not by re-guessing it every run.

One call per track, one raw pool each. Don't add more specific compound phrases on top of the list in `context/expertise.md` — if recall still feels low after a few runs, widen the existing tracks or add another broad single/short word, rather than narrowing back toward compound niche phrases. The needs-based tracks will surface plenty of jobs with no real fit at all (a generic sales-rep posting, a "grow my revenue" consulting gig) — that's expected and fine, Step 2's scoring gate is what filters them, not the search itself; don't second-guess a needs-based track just because most of its pool is noise, the tool-based tracks work the same way.

**Skip anything posted more than 2 days ago** — check `created_date` against now before scoring. Speed-to-lead is the whole point (early proposals win on Upwork); a 3-day-old posting has likely already collected dozens of proposals. Don't score it, don't log it, don't fetch its description.

## Step 2: Score every result, 0–100

Four components:

- **Niche fit (0–40)** — score the posting against your own criteria in `context/expertise.md`, specifically the **"Your niche / what you build"** and **"What counts as a strong match"** sections. Give a real bonus for hitting an *overlap* — two or more of your own listed strengths showing up in the same posting is worth more than either alone.

  Before scoring high, check the posting against your own **"False-positive traps"** list in `context/expertise.md` — things that use the right keywords but aren't actually what you want. If `find_jobs get` returns `client_work_history`, weigh it over the posting's own text: a generic-sounding posting from a client whose past job titles are dominated by a different kind of work than what's advertised now is probably that different kind of work wearing a broader label — clients tend to hire the same thing repeatedly.

  If `context/expertise.md` has entries under **"Calibration anchors,"** use them as directional anchors for what a given score band should feel like, not a lookup table. It's normal for that section to start empty — it fills in naturally once you've corrected a score or two across a few real runs.

- **Client trust (0–30)** — `client.verification_status` (baseline, already filtered), `client.rating`, and critically the **hire ratio** = `client.total_hires / client.total_posted_jobs`. A client with 300 posted jobs and 2 hires is a time-sink even at 5.0★; weight the ratio, not just the star rating. No hire history yet (brand-new client, `total_posted_jobs` low or absent, or `rating` missing) isn't disqualifying, just score it neutrally rather than high.
- **Deal quality (0–20)** — budget/rate signal, engagement (real ongoing commitment scores higher than a one-off gig-shop posting, but don't hard-exclude short jobs), duration. **A rate above ~$20/hr or a fixed price above ~$50 is a genuine bonus within this component, not a gate** — confirmed in a real run: a job can still be worth notifying below that (a CRM-automation build at $8–17/hr scored 85 and was fine given the scope and client quality). Score it as one more input, the way budget already was — just don't let a big number alone rescue a job with no niche fit or a bad client. **`contractTerms.hourlyContractTerms.engagementType == "FULL_TIME"` pulls this component down.** You're a freelancer taking on projects, not looking for something that reads as full-time employment. This isn't about the hours-per-week number — it's specifically the `FULL_TIME` engagement flag the API returns. `PART_TIME` or unset is neutral.
- **Recency (0–10)** — newer postings score higher, and this matters more than the 10-point cap alone suggests: every candidate here already cleared the 2-day-old cutoff, so within that narrow window a same-day posting still deserves the top of the range and a 40-hour-old one the bottom, not a flat middle score. Upwork rewards early proposals; a 2-week-old posting is likely already buried in proposals.

**Hard gate before anything else uses the score:** a job only counts as a genuine candidate if **niche fit ≥ 20** (out of 40) — this is the filter the search-breadth trade-off depends on. A job can't buy its way past irrelevance with a huge budget or a perfect client; if niche fit is under 20, cap the job's effective status at "logged, not a real match" regardless of total score.

## Step 3: Log every candidate

Read `context/.upwork_jobs.json` (a JSON array; treat a missing or empty file as `[]`). For every job scored **≥ 50 total** that passed the niche-fit gate and isn't already present by `id`:

**Fetch the full description** — `find_jobs` search only returns a truncated `description_snippet`, not the real thing. Call `find_jobs` (action=`get`, `org_uid` — same value as Step 1, from `context/config.yaml` → `upwork_org_uid`, the job id) for each qualifying candidate to get the complete description text before writing the record — this is a bounded, already-filtered set (only the ones that clear scoring), not every raw search result, so the extra calls are cheap.

**Skip it entirely if it's already filled.** The `find_jobs get` response includes `data.marketplaceJobPosting.activityStat.jobActivity.totalHired` — if that's ≥1, the client has already hired someone (confirmed in a real test: two jobs in one batch showed `totalHired: 1`). Applying to a filled job is pointless; don't log it at all, don't count it toward anything.

Then append a record:

```json
{
  "id": "<upwork job id>",
  "title": "...",
  "url": "https://www.upwork.com/nx/search/jobs/?q=<url-encoded exact title>",
  "found_at": "<ISO 8601 UTC timestamp — when the screener found it>",
  "posted_date": "<the job's own created_date from the API, verbatim>",
  "description": "<full job description text from find_jobs action=get>",
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

**Rationale doesn't repeat the columns next to it.** The dashboard shows Client (rating/hire ratio), Budget, and Posted as their own columns — the rationale field is read right beside them, so restating "$500 fixed, client 4.9★" there is wasted space you have to reread. Use the sentence for what those columns can't show: what the score is actually betting on, or against — the specific scope risk, the overlap that earned the niche-fit bonus, the giveaway that dropped it, whatever a proposal would need to lead with.

**Budget keeps the client's own framing, not just the number.** When the posting says more than a bare figure — a bonus structure ("$400/mo + up to $130/mo performance bonus"), a milestone framing ("$100 first milestone, more after"), a rate that looks like a placeholder — fold that into the `budget` string itself rather than reducing it to the number alone. The Budget column renders whatever's in the field verbatim, so this is the only place that context survives.

**On the URL — verified the hard way.** `find_jobs` never returns a working public job link; the `id` it returns is an internal numeric ID, not the `~<ciphertext>` a real `upwork.com/jobs/~...` URL needs (confirmed: constructing one from the numeric id and calling `find_jobs get` on it fails with "resource not found"). There's no ciphertext field anywhere in the API response to build a direct link from. The reliable fallback is Upwork's own public search page with the exact job title as the query — it won't always be the single top result, but it gets you to the job without a broken link. If Upwork's API ever starts returning a real ciphertext, switch back to a direct link; until then, don't reintroduce the `~<id>` pattern.

`found_at` and `posted_date` are different things — don't conflate them. `posted_date` is when the client posted the job (what the dashboard's "posted X ago" is computed from); `found_at` is when this screener happened to see it.

Never touch or re-score a job `id` already in the file — it's owned by whatever status it's since moved to (a human may have marked it `proposal_sent`). Skip it entirely, don't even overwrite its score.

Trim the file to the most recent 500 records by `found_at` after appending, so it doesn't grow forever — but never trim a record whose `status` is anything other than `new` or `notified` (an active pipeline entry — `proposal_sent`, `interviewing`, etc. — never gets silently dropped just because it's old).

Write the file back with `Write`.

## Step 4: Notify — signal only, never noise

Among the jobs newly logged this run (not ones already seen), collect those with **niche fit ≥ 20 AND total score ≥ 70**. If there are none, send nothing — silence is correct, not a failure.

If there are one or more, check `context/config.yaml` for `slack_channel_id`. **If it isn't set, skip this step entirely** — the candidates are already logged from Step 3, that's enough; don't fail, and don't nag the user to go configure Slack. If it is set, send a **single** Slack DM (not one per job) via the Slack MCP, `channel_id` = `slack_channel_id`, listing each: score, title, one-line rationale, budget, client rating + hire ratio, and the link. Then set those jobs' `status` to `"notified"` in the JSON file (rewrite their records).

## Step 5: Status is a small CRM — use `reference/scripts/upwork_status.py`

The job list isn't just a feed, it's a lightweight pipeline: `new → notified → proposal_sent → interviewing → offer_sent → hired` (or `rejected` / `archived` at any point). The dashboard's Upwork tab groups this into three board columns — **Outreach** (`new`/`notified`/`proposal_sent`), **In contact** (`interviewing`) and **Offer sent** (`offer_sent`) — plus `hired`/`rejected` jobs staying visible in the list view. When the user says something like "mark the SEO strategist job as proposal sent", "the client replied on &lt;job&gt;" or "I sent them an offer for &lt;job&gt;", update it with:

```
python3 reference/scripts/upwork_status.py set <job_id> proposal_sent --follow-up +3d
python3 reference/scripts/upwork_status.py set <job_id> interviewing
python3 reference/scripts/upwork_status.py set <job_id> offer_sent --follow-up +3d
```

`--follow-up +3d` sets `next_follow_up` three days out (Upwork's normal response window) — use it on `proposal_sent` and `offer_sent`, omit it for statuses that don't need a follow-up date (`interviewing`, `hired`, `rejected`, `archived`). The dashboard's Upwork tab reads `next_follow_up` and flags anything due, so this is the actual follow-up-control mechanism — it's not automatic, it runs off what gets marked here. The dashboard's own stage-move buttons ("Got a reply", "Offer sent", "Won"/"Declined") just copy a sentence like the ones above to paste into chat — the dashboard itself never writes anything, it's a pure view.

## Step 6: Reconcile — jobs sitting in the list can get filled by someone else

Before searching for new jobs (Step 1), pick up to 5 of the oldest still-open records (`status` is `new` or `notified`) whose `status_updated_at` is more than 1 hour old — checking again within the hour just repeats the same answer, confirmed by rechecking the same 5 jobs twice within 10 minutes and getting identical `totalHired: 0` both times. If nothing qualifies (everything open was already checked recently), skip this step entirely for this run. Otherwise, re-fetch the qualifying records with `find_jobs` (action=`get`). If `activityStat.jobActivity.totalHired` is now ≥1, someone else got hired — set `status` to `archived` and don't count it as active anymore. This is the same check as the "skip if already filled" rule in Step 3, just applied backwards in time to jobs that were open when first logged. Keep it to 5 per run — this is upkeep, not the main job, and doesn't need to sweep the whole list every 15 minutes.

## Self-improvement

If the user corrects a score ("that one shouldn't have scored that high", "you're underrating budget") or flags that good/bad jobs are slipping through the gate, that's a signal to adjust the rubric weights or the hard gate above — edit this file directly, don't just remember it verbally for next time.
