---
name: coldmail-setup
description: Builds the sending infrastructure before the first cold mail — works out how many mailboxes and domains a daily target needs, shows the monthly cost before anything is bought, then walks through Zapmail domains, DNS, mailboxes and the Instantly export. Starts the warmup clock on day one. Use on "set up cold mail", "/coldmail-setup". Running a campaign is `coldmail-run`.
---

# Cold Mail: the sending infrastructure

**This is the part that takes weeks, and it is the part everyone does last.** Do it first.

New domains have to warm up before they may send. Instantly asks for two weeks minimum and
recommends four; DNS alone takes 24 to 48 hours to propagate. A user who builds their lead list
first and their infrastructure second sits on finished mails for three weeks. **The warmup is the
only step that runs without them, so it starts on day one and the lead work happens while it
runs.**

Say that in the first message. Not as a warning at the end.

## Step 0: what it costs, before anything is bought

**Nothing gets created, connected or charged until they have seen this and said yes.** That is
the promise the base layer makes on this add-on's behalf in `WHAT-THIS-SYSTEM-DOES.md`, and it
is the whole reason an add-on may bring paid services at all.

Ask one question: **how many cold emails a day do you want to send?**

If they don't know, give them the shape rather than a number: 100 a day is roughly 4 mailboxes,
300 a day is 10, and their own capacity is whatever they can actually follow up on. A reply rate
of a few percent means 300 sends a day produce a handful of conversations — more than most
freelancers can handle alongside delivery.

Then compute, and show the arithmetic rather than the result:

```
mailboxes = ceil(target_per_day / 30)      # 30/mailbox/day is Instantly's ceiling
domains   = ceil(mailboxes / 3)            # Zapmail recommends 2-3 mailboxes per domain
```

**Never raise the per-mailbox number to save money.** Instantly is explicit: scale by adding
mailboxes across more domains, not by sending more from each. Thirty is a ceiling, not a target.

| target/day | mailboxes | domains | Zapmail plan |
|---|---|---|---|
| 100 | 4 | 2 | Starter, $39/mo (10 included) |
| 300 | 10 | 4 | Starter, $39/mo |
| 600 | 20 | 7 | Growth, $99/mo (30 included) |
| 900 | 30 | 10 | Growth, $99/mo |

Domains are bought separately (roughly $10–15 a year each, or connected for free if they already
own some). Instantly is its own subscription on top.

**The user decides the domain count, not this skill.** The table is a starting point. Someone who
already owns three suitable domains uses those; someone who wants to spread risk takes more
domains with fewer mailboxes each. Present the number, then ask whether it fits.

State the monthly total in one line before continuing. If they hesitate, that is a legitimate
answer — the base layer works without this add-on, and saying no here changes nothing else.

## Step 1: the domains

Two routes, and the choice matters for the timeline:

**Buy through Zapmail.** DNS is configured automatically, nothing to touch. Fastest.

**Connect existing domains.** They replace the nameservers at their registrar; Zapmail rechecks
and connects automatically once the change lands. **Allow 24 to 48 hours for propagation.**

Either way Zapmail sets up SPF, DKIM, DMARC and MX itself. Do not hand-write those records —
a hand-written SPF that conflicts with the generated one is a deliverability failure that shows
up as silence, not as an error.

**Never use their real business domain.** Cold mail damages sender reputation by design, and a
burnt domain takes the company mail down with it. Separate domains, close to the brand:
`getbrandname.com`, `brandnamehq.com`, `trybrandname.com`. Prefer `.com` — Zapmail names it as the
better TLD for deliverability, and the cheap alternatives are the ones spam filters have learned.

## Step 2: the mailboxes

Google Workspace or Microsoft 365, chosen once for the account. Google activates in up to three
hours, Microsoft in up to twelve.

Names go on real people, not on roles. `luka@`, `luka.knieling@` — not `info@`, `hello@`,
`sales@`. A role address in a cold mail reads as a list, because it is one.

**Mailbox orders cannot be reverted once placed.** Confirm the count and the spelling of every
name before ordering, not after.

## Step 3: start the warmup, then stop waiting

The moment the mailboxes are active, warmup starts in Instantly — and **this is where the skill
hands back and the user goes on with `coldmail-run`.** Say exactly that:

> *"Warmup is running. Nothing to do here for about two weeks. Meanwhile we build the lead list
> and write the mails — say `coldmail-run` when you want to start."*

The ramp itself: start at 10 to 15 a day per mailbox and increase by 10 to 20 percent as long as
bounces stay at or below one percent and complaints stay near zero. Instantly does this on its
own once warmup is on; the numbers matter because they are what to check against in week two.
**Warmup mail does not count against the daily limits** — a mailbox warming up can still send its
full campaign allowance once released.

Write the date into `context/config.yaml` so the dashboard can count the days:

```yaml
coldmail_enabled: true
coldmail_warmup_started: 2026-08-23    # the dashboard counts from here
coldmail_mailboxes: 10
coldmail_target_per_day: 300
```

## Step 4: connect the mailboxes to Instantly

Zapmail exports directly to Instantly — select the mailboxes, export, authenticate once. It does
this automatically as mailboxes go active, so in most cases there is nothing to do but confirm
they arrived.

Verify on the Instantly side rather than trusting the export screen: every mailbox present, every
one warming, none in error. A mailbox that silently failed to connect is a mailbox that never
sends, and nothing will say so later.

## What this skill does not do

**It does not create a campaign and it does not send anything.** That is `coldmail-run`, and it
should not run until warmup has had its two weeks. If the user asks to send earlier, tell them
what it costs: mail from a cold domain lands in spam, and the domain reputation that produces is
not repaired by waiting afterwards.

**It does not touch their existing mail.** The base layer's mail drafts go through their normal
account and have nothing to do with these mailboxes.

## Selbstverbesserung

Zwei Signale zählen: Luka korrigiert eine Zahl oder einen Schritt, oder ein Nutzer läuft an
derselben Stelle zweimal auf. Bei beidem fragen: „Soll das dauerhaft in den Skill?"

**Wohin die Korrektur wandert:**

| Was | Wohin |
|---|---|
| eine Zahl (Postfächer je Domain, Aufwärmdauer, Preis) | in die Tabelle in Schritt 0, mit Datum der Messung |
| ein Schritt, der in der Praxis anders läuft als in der Doku | in den betroffenen Schritt, mit dem Grund |
| ein Fehlerbild, das beim Einrichten auftrat | in „Was schiefgeht" (anlegen, falls es den Abschnitt noch nicht gibt) |
| etwas, das nur eine Variante betrifft (Microsoft statt Google) | `references/`, nach Variante getrennt |

**Die Zahlen hier stammen aus der Zapmail- und Instantly-Dokumentation, nicht aus einem
gefahrenen Setup.** Lukas eigene Installation läuft auf 27 Postfächern mit 810 Mails am Tag —
sobald seine Erfahrungswerte vorliegen (wie viele Domains, welcher Aufwärmplan, was tatsächlich
schiefging), ersetzen sie die Doku-Werte. Gemessenes schlägt Dokumentiertes.

## The check, before handing over

Four things, and all four have to be true:

1. Domains connected, DNS verified by Zapmail
2. Mailboxes active, named after people
3. Warmup running, start date in `config.yaml`
4. Mailboxes visible and warming in Instantly

If one is missing, name which and what it blocks. A setup that is 90 percent done sends nothing,
and the failure mode is silence rather than an error message.
