# Upwork: what is allowed, with the numbers

The single source for every Upwork skill in this repo. Measured 14 August 2026 from Upwork's
own pages, not from blogs. Whoever changes a number here names the source next to it.

## The hard line

**Unattended automation is prohibited.** Upwork names these verbatim as grounds for
enforcement:

> "Using OAuth2 tokens or session cookies from a browser or **an official client** in a script or bot"
> "Exceeding rate limits or **running background polling that resembles scraping**"

— [Use bots and other automation properly](https://support.upwork.com/hc/en-us/articles/43342677368467-Use-bots-and-other-automation-properly)

Two approaches that would technically work are therefore out: copying your Claude Code OAuth
token into another runner (a cron job, a hosted agent, a credential vault), and polling on a
tight schedule.

**What stays fully allowed, and it is nearly everything:** the official connector inside Claude
Code, with a human in front of it. Search, score, draft, submit proposals, read and answer
messages, contracts, milestones, finances. Exactly one capability is missing from that list,
and it is "sends on its own".

## The numbers

| Limit | Value | Source |
|---|---|---|
| Requests per IP | **10/second**, then HTTP 429 | [Support](https://support.upwork.com/hc/en-us/articles/115015933428-What-are-the-API-requests-limits) |
| Requests per IP | **300/minute** | [Developer docs](https://www.upwork.com/developer/documentation/graphql/api/docs/index.html) |
| Requests per day | **40,000**, confirmed in the API-key application | [API key](https://support.upwork.com/hc/en-us/articles/115015857647-Request-an-API-key) |
| Caching API responses | **24 hours maximum** | both |

The first two contradict each other and both are Upwork's. Assume the stricter one; you will be
orders of magnitude below it either way, because a screener run makes 20 to 40 calls.

**Volume is not the problem. The pattern is.** "Polling that resembles scraping" is a
behavioural judgement with no documented threshold. There is no number below which unattended
polling is safe. What makes it safe is a person triggering it.

## The house rules, stricter than the terms

1. **Writing always needs an explicit yes.** A message, a proposal, an invitation, an offer.
   Draft freely, send never.
2. **Reading runs on demand and once inside `morning`.** No timer. If you ever do schedule it,
   gate it on presence, jitter the interval, and stay off it at night.
3. **Every run reports its call count.** One sentence. Then "well under the limit" is measured
   rather than assumed.
4. **`upwork_status.py prune` after each run.** Upwork content older than 24 hours goes. Your
   own scoring, notes and history are yours and stay.
5. **No token leaves this machine.** Not into a vault, a cron job or a hosted agent.

## The route to automation runs through revenue

An approved API key would permit automation. The criteria:

| Requirement | |
|---|---|
| $25,000 lifetime earnings | |
| Job Success Score ≥ 90% | |
| Identity verified, payment method, profile photo, account in good standing | |

Plus: *"Upwork API is available for personal and internal use only. Commercial use isn't
supported."* Worth clarifying with Upwork before selling anything built on this.

**So the ordering is not arbitrary.** The daily proposal tracker is not a detour on the way to
an autonomous agent, it is the entry ticket. The number that unlocks it is revenue.

## The open contradiction, stated rather than resolved

Upwork's own MCP server ships a `set_tool_permission` switch with an `always_allow` value,
described in its own documentation as "useful for automated flows". So Upwork builds
automation into its own tool while the help pages tie unattended automation to an approved key.

Two Upwork sources, two directions. This file does not resolve that, because it cannot. If you
intend to run anything unattended, ask Upwork support directly and write their answer here.
