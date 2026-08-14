# Report form

Read in steps 3 and 4 of `/audit`. Governs how findings and proposals are worded.

## The report in chat

Structure, in this order:

1. **One sentence of overall judgement.** Not "the audit is complete", but what is actually the case: "The folder carries the work, but half your documents are invisible to Claude."
2. **At most one line per dimension**, and only for the ones with something to say. Dimensions sitting at `ok` are handled in one collective sentence ("Backup, cold start and decision memory are fine"). Nobody reads a list of passed checks.
3. **The three things with the most leverage**, written out. Why three: more does not get done, fewer feels arbitrary.
4. **What stayed `unknown`**, in half a sentence, with the reason. Missing evidence is not a good grade.

## How a finding is worded

**Consequence rather than measurement.** The measurement is where the statement came from, not the statement.

| Not this | But this |
|---|---|
| "Found 12 orphaned documents" | "Claude never reads these twelve documents, because nothing points at them" |
| "Token load 18,400" | "Every conversation pays about 18,000 tokens before anything happens" |
| "5 repetition patterns detected" | "You have typed this sequence by hand 40 times" |
| "confidence 0.9, severity high" | (values belong in the JSON, not in the sentence) |

Every finding answers three things: **what is the case**, **why that hurts**, **what helps against it**. Without the middle part it is a statistic, not an insight.

**No grades, no overall percentage.** A single score averages a dead journal against clean repo handling and suggests a comparability that does not exist.

## What proposals look like

**Never a single recommendation.** There is no best tool and no best route, there are trade-offs — and naming only one route takes away a decision that belongs to the other person.

Per proposal, two or three routes side by side, in a table:

| Route | Effort | Ongoing | What you get | What you take on |
|---|---|---|---|---|
| … | 20 min once | $0 | … | … |

Below it **one** marked recommendation with a one-sentence reason ("I would take this one, because …"). The other routes stay standing as equals, each with its own advantage — they are not straw men.

**What someone already uses beats the theoretically better tool.** A switch only appears as an option when a stated pain point carries it. Recommending a migration because something is "best practice" is bad advice: the migration costs weeks, and the pain was something else.

## Tone

An experienced person who has looked at the setup and is now saying what stood out. Not "diagnosis complete, 7 of 11 checks passed".

- Everyday language. Technical terms only where they add something.
- No urgency rhetoric. No "critical", no "urgent", no exclamation marks. What really hurts is recognisable from the consequence you described.
- Open points are opportunities, not accusations. A folder without routines is not sloppily run, it has an opportunity it has not taken yet.
- No em-dashes.
