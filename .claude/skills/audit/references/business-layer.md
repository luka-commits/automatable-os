# The business level

Read in step 5 of `/audit`, **only when the user has agreed or `context/profile.md` already exists**. It holds the short interview, the derivation of the target profile, the assessment of the tools in use, and the judgement on the toolkit as a whole.

This level is deliberately optional. In an environment where tools are set by IT it is pointless, and the folder part of `/audit` stands on its own.

## The interview: six questions

**Pre-fill rather than ask, wherever the answer is already written down** — `context/config.yaml`, `context/expertise.md`, the project names in `context/PROJECTS.md`. Propose it, have it confirmed. On a folder that is not yours these sources do not exist, and then you ask.

1. **What do you do, and for whom?** One sentence. From it follow the kind of business, the industry, the target customer — and whether the work is local or spread out (derive and quietly confirm, do not ask separately).
2. **How many people are involved, and who touches this folder?** Working alone means shared storage and team chat are *irrelevant*, not *missing*.
3. **List every tool you use daily, and what each is for.** Optional: what have you dropped, and why? The "what for" is the real yield — it names the task the tool is measured against, and it reveals the switching cost. "It was already there" and "our entire billing hangs off it" lead to completely different recommendations. Dropped tools stop you proposing something that has already failed once.
4. **Where does client contact happen?** Mail, phone, WhatsApp, a form, a platform.
5. **What currently costs you the most time or patience?** Up to three things. Without this answer the audit measures completeness instead of usefulness, and a recommendation without real pain never gets acted on.
6. **What should this folder carry, and what explicitly not?**

For a tool with no recognisable "what for", **one** follow-up question, no more. Target: under two minutes. Then write `context/profile.md`; proposals rejected in earlier runs sit there with a date and a reason and are not proposed again.

## Target profile: which capability counts for whom

Twelve capability slots that apply to any business. Each gets a level from the profile: **required · useful · irrelevant**.

```
Mail · Calendar · Storage · Team chat · CRM · Accounting/invoicing
Tasks/projects · Website/shop · Social/publishing · Support inbox
Development · Local visibility
```

**The assignment follows rules derived from the answers, never an industry table.** A fixed mapping of "trades need X" would be exactly the bias this tool exists to avoid.

| From the profile | follows |
|---|---|
| Client contact runs over one channel | that channel becomes required |
| Working alone or as a pair | team chat and shared storage irrelevant |
| Local, walk-in trade or a catchment area | local visibility required |
| Repeat customers, quotes, following up | CRM required |
| Invoices in your own name | accounting required |
| Code, deployments, an own product | development required |
| Reach is part of the business | social/publishing required |
| A pain point names an area explicitly | that area moves up one level |

An **irrelevant slot does not appear in the report at all**. A missing required slot is a finding; a missing useful one is a suggestion.

## The dossier: five questions per named tool

### 1. Functional coverage

Does it cover the tasks that follow from the "what for" **and from the pain points**? The target capabilities are derived from the pain, not from a generic feature list.

> "Enquiries over WhatsApp get lost" → what is needed is a WhatsApp inbox in the CRM → can the named tool do that, and is it switched on?

### 2. Connectability — the ladder

Always check from the top; the first rung that holds wins:

| Rung | Route | Effort for the user |
|---|---|---|
| 1 | Connector in Claude Cowork | sign in once, no configuration |
| 2 | Official MCP server (npm or remote) | create a token, register once |
| 3 | CLI | install, authenticate |
| 4 | REST API with your own script | get a key, build a script |
| 5 | no route | say so honestly, stay manual |

**The rule against invented routes:** a rung is only named once its auth route is evidenced — documentation read, or endpoint checked. No "there is bound to be an MCP server".

That is exactly what went wrong once: for HubSpot the HTTP endpoint looked like a finished integration but had no `registration_endpoint`. The real route was the npm package with a private-app token. Claiming the rung would have sent the user into a dead end.

Two evidenced examples, as a pattern for how differently rung 2 can look:

- **ClickUp** — official MCP server, documented at `developer.clickup.com/docs/connect-an-ai-assistant-to-clickups-mcp-server`
- **GoHighLevel** — LeadConnector MCP at `services.leadconnectorhq.com/mcp/`, bearer PIT token plus `locationId`, 36 tools

These two are **examples, not requirements.** They are here because they show that "has MCP" says nothing about the auth route.

### 3. Reputation in this industry

What users actually say, advantages **and** disadvantages, from review sources (G2, Capterra, Reddit, Trustpilot) — **never from vendor copy**. Vendor copy describes what the tool is meant to do; the review describes what it does.

### 4. Price

What is being paid against what the market charges. Per seat, and what only arrives later (add-on modules, volume limits, onboarding fees).

### 5. Verdict — exactly three outcomes

- **Keep** — covers the task, the connection is in place or reachable
- **Keep and close the one gap** — an add-on, an integration, or a process around it
- **A switch would be worth a look** — only when a stated pain point carries it

## The bundle as a whole

After the individual dossiers, a judgement on the whole toolkit. This is what nobody sees who only looks tool by tool:

| Question | How you spot it | Why it counts |
|---|---|---|
| **Doubled up?** | Two tools with the same "what for" | Double cost, split truth, nobody knows which one counts |
| **Patchwork?** | Where is data copied by hand from A to B? Falls out of the "what for" answers and the pain points | Every manual copy is a recurring source of error and a candidate for automation |
| **Oversized?** | Tool class against business size | Over- and undersizing both cost, just differently |
| **Steerable?** | Share of tools with an evidenced connection route | **The bundle's one metric:** "Claude can reach 6 of your 9 tools." Says in one line how far automation can carry at all |
| **What does it cost together?** | Sum of the subscriptions against business size, plus what is paid for twice | Often the only finding that frees up money immediately |

No solo verdict here either: being doubled up can be deliberate, oversizing can be preparation for growth. The finding names the observation and the question that goes with it, not the verdict.

## Where it goes

Results into `context/tool-dossiers.md`, one block per tool with **a date and a source** per statement. The next run reads from there; only what is older than three months, or what the user has reported a change for, gets researched again.
