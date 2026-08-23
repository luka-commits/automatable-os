---
name: coldmail-run
description: Builds the lead list and writes the mails: scrapes a niche region by region, scores every Google profile against the market, and puts the ones that clear four checkers into a file for Instantly. Use on "run cold mail", "build the lead list", "/coldmail-run". Mailboxes and domains come first, via `coldmail-setup`.
---

# Cold Mail: the list and the mails

**Runs while the mailboxes warm up.** If `coldmail-setup` has not run, say so and stop — building
a list with nowhere to send it from is the wrong order, and the warmup is three weeks that only
start when somebody starts them.

All commands run from `reference/addons/coldmail/pipeline/`.

## Step 0: which niche, which country

Two questions, and the first one decides everything downstream.

**The niche has to be a trade, not a market segment.** "Locksmiths" works: it is a Google
category, the businesses have profiles, and their customers find them on a map. "Small
businesses" does not — there is nothing to scrape and nothing to compare against.

**Then its synonyms**, because the filter needs them: locksmith, key cutting, auto locksmith.
Ask for them rather than guessing; the user knows their market's vocabulary.

**Say what the scrape will cost before starting it** — roughly $5 for a country-sized market at
Apify's rates, plus about $1.34 for the service lists. It is their account.

## Step 1: scrape the market

```bash
python3 run_campaign.py --niche <niche> --country UK --terms "<synonyms>"
```

Region by region — the UK ships with 46 counties, Germany with its 16 states. One region at a
time, so a run can stop and resume, and so a market too big to fetch at once still finishes.
**Google Maps caps what one search returns**, which is why a single query for the whole country
would hand back a few hundred businesses and this hands back thousands.

Three things happen inside that command and all three matter:

- **The niche filter** sorts each result into keep, verify or drop. The middle bucket exists
  because a hardware store that mostly cuts keys has the wrong category, and dropping it on that
  basis loses a real lead.
- **Deduplication** collapses locations into companies. Google returns one row per *pin*: in the
  UK locksmith scrape, Timpson appeared 1,877 times, every branch its own row, all with the same
  website. Mailing them all is not weak personalisation, it is spam, and it burns the domain.
- **Chains come out.** A 1,800-branch operation is not a freelancer's customer and would eat the
  entire daily send volume by itself.

## Step 2: fill the gaps

```bash
python3 dfs_listings.py --niche <niche>            # service lists, DataForSEO
python3 recover_emails.py --needs runs/<slug>/needs_email.csv --out runs/<slug>/cleaned.csv
```

Maps carries an email for roughly seven in ten. For the rest, if there is a website, the homepage
and then `/contact` get read and an address on the business's own domain is preferred over a
gmail in the footer. **Only for the ones that are missing** — every fetch costs.

## Step 3: measure the market

```bash
python3 benchmark.py --niche <niche> --refresh
```

This is the step that makes the mails worth reading. It computes the medians the business owner
cannot look up anywhere: reviews, photos, service count, what share of the trade shows 24 hours.
He knows he has 64 reviews. That the median is 20 is the part only we have.

**It must run after the scrape and before the mails.** On a partial scrape the median is built
from a handful of businesses and every comparison in every mail inherits that error, silently.

## Step 4: write and check

```bash
python3 stapel.py --niche <niche> --auto              # build and check, changes nothing
python3 stapel.py --niche <niche> --auto --apply      # keep the clean ones
```

No model writes here. Twenty building blocks, up to five used per mail, each carrying a state, an
action and a consequence. The wording is picked by the business's own ID rather than at random,
so a second run produces the same mail and one sent three weeks ago can still be reconstructed.

**Four checkers, and a lead clears all of them or is not written to:**

| Checker | What it catches |
|---|---|
| `preview_mail` | a missing variable, a broken layout |
| `verify_mail` | a number that is not in that business's data, a claim about a town we know only a slice of, anything over 80 characters |
| `fact_sheet.widerspricht` | advice the business has already taken |
| `fact_sheet.formel` | a line missing its state, its action or its consequence |

Read the dry run before applying. `12 offen · 9 sauber · 3 durchgefallen` means three leads had
something the checkers would not let through — that is the system working, not a failure to fix.

## Step 5: the file for Instantly

```bash
python3 export_cohort.py --niche <niche> --region "<region>"
```

Writes `runs/<slug>/instantly.csv`, and **only the leads that cleared everything**. Nothing to
sort out by hand afterwards.

## Step 6: hand it over — and this needs an explicit yes

```bash
python3 import_to_instantly.py <campaign_id> runs/<slug>/instantly.csv
```

**Ask before running this, every time.** Uploading and activating are separate on purpose, and
nothing leaves without the user's word — that is a promise the base layer makes for every add-on.

Settings that matter when the campaign is created: senders drawn from the warmed mailboxes, the
daily limit set to mailboxes × 30, **tracking off**, stop-on-reply on. Tracking pixels are among
the fastest routes into spam and buy a freelancer nothing.

## When something looks wrong

**A factor fires on 0% of leads although the data is there.** Almost always the 80-character
limit: `pool.add` drops longer lines **silently**. `python3 mail_audit.py --niche <niche>` reports
it over the whole batch.

**Many leads fail with the same message.** Then it is one building block, not the data. The
message names which line.

**The medians look wrong.** `benchmark.py` ran on a partial scrape. Re-run it after the scrape
finishes; nothing else has to be redone.

**Everything is empty and no error appeared.** Check which store is in use:
`python3 speicher.py` prints it. An empty SQLite file where Supabase was expected looks exactly
like "all the leads are gone".

## Selbstverbesserung

Two signals: the user corrects an output, or a run fails at the same place twice. Ask both times
whether it belongs in the skill permanently.

| What | Where it goes |
|---|---|
| a copy rule (wording, what a point may claim) | `pipeline/markt_copy.md`, never here |
| a new building block or a changed one | `pipeline/pool.py`, plus a test in `test_integration.py` |
| a failure mode worth warning about | the section above |
| a step that runs differently in practice | the step itself, with the reason |

**Anything that changes what a mail says goes into the pipeline, not into this file.** A copy
rule written here is one nobody reads at the moment it applies.
