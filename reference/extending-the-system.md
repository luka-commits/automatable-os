# Extending the system

This package comes with eight commands: `/setup` and `/adopt` to get started, `/morning`, `/eod`, `/ingest` and `/email` for the daily rhythm, `/checkup` when something feels off, `/audit` when you want the folder judged as a working system. Everything beyond that you build yourself, like this:

**You describe, Claude builds.**

You never write a file here, no command, no program. You say in your own words what you want, and Claude creates it. The skill this guide is about is not technical. It is describing well and asking at the right moment.

---

## 1. Giving good instructions

This is the biggest lever, which is why it comes first. A good instruction is no longer than a bad one, it just contains different things.

**Say the goal, not the route.**

> Bad: "Make a table with three columns and sort it by date."
> Good: "In the Friday meeting I want to see within 30 seconds which quotes have gone unanswered for more than two weeks."

With the second one Claude can decide for itself that a colored marker helps more than a third column. With the first one it builds exactly the table you thought up, even if that table does not solve the problem.

**Say where the information comes from.**

> Bad: "Summarize what happened with the clients this week."
> Good: "Take this week's journal entries and the project states. If something is missing, write that down instead of filling it in."

Without a source Claude guesses when in doubt. With a source it knows what it does not know.

**Say what the result should look like.**

> Bad: "Write me a weekly report."
> Good: "Half a page. Three lines per project: what happened, what is stuck, what I need from someone. Nothing at the end, no summary of the summary."

Length, structure and ending are the three specifications that save the most rework.

**Say what must not happen.**

> "No numbers that are not in the documents."
> "No employee names in that document."
> "Do not touch my mailbox, I only want the project files."

A prohibition is often worth more than three wishes, because it switches off exactly the thing that bothered you last time.

**One example beats any description.**

If you have a report, a mail or an overview lying around somewhere that you like, put it in `inbox/` and say: "It should look like this, just with this month's numbers." That is the fastest route of all. Five minutes of describing does not replace a single file.

---

## 2. When a command of your own is worth it

A command is a routine you call in the chat, like `/morning`. Claude then knows which files to read, in what order to work, and what the result should look like, without you explaining it every time.

**The rule of thumb: on the third time.** If you do the same thing for the third time in a similar form and the routine is the same every time, it is worth it. Not before. Twice by hand costs less than setting it up once.

**How to ask for it:**

> "Every Friday I write a status report for my boss. Always the same projects, always the same structure: progress, risks, what I need. Build me a command for that."

Claude will then ask back what it needs to know: which projects, how long, who reads it, what should never be in there. Answer briefly. After that the command exists and you use it.

**On the first bad result you correct, you do not rebuild.** "The risks section is too long, two sentences are enough" is sufficient. The command gets adjusted and is right next Friday. A new command for the same topic is almost always a mistake, then you have two that differ slightly, and after four weeks you no longer know which is the right one.

**What a command is not worth it for:**

- Anything you do once a quarter. By then you will have forgotten it exists.
- Anything that goes differently every time. Preparing a client conversation is a different task for every client. You are better off saying it fresh every time, then you get a fitting answer every time.
- Anything that is said in two sentences. The command then saves nothing.

---

## 3. When a tool of your own is worth it

The difference in one sentence: **A command is something you say. A tool is something you click.**

A tool is worth it when something gets calculated, displayed, or used by several people. A calculator for your team's workload. An overview your colleague should be able to open without asking you. A form you fill in during every first conversation.

**This is how you describe it:**

> "I need a page where I enter the planned hours per week for each project. At the bottom is the total per person, and if someone goes over 40, I see it immediately. Only I use this, it does not have to save anything."

What Claude wants to know: what goes in, what should come out, who uses it, does it have to remember anything. Nothing more.

**Two things belong to it so it does not get lost:**

1. Say: "Stick to `reference/design.md`." Then the tool looks like the rest of the system and not like a foreign program.
2. The finished tool gets recorded in `context/config.yaml` under `own_tools`, with name, purpose and address. After that it appears in the dashboard in the "Workspace" tab and you will find it again in four weeks. Claude makes this entry itself when you build it. If it does not happen, say "add that to my own tools".

---

## 4. Correcting instead of rebuilding

When a result is not right, say so. **"That's not right" is enough.** You owe no justification and no suggestion how it could be done better. Claude asks back if it is not clear.

But the most important sentence in this whole guide is a different one:

**When you say "always", "never" or "from now on", you get a permanent change instead of a one-off correction.**

That is not a politeness formula, it is the mechanism by which the system gets better. Compare:

| You say | What happens |
|---|---|
| "The report is too long." | This one report gets shorter. |
| "Reports to the board are from now on always a maximum of one page." | Every future report is one page. |
| "The sports class on Tuesday does not need to be in the briefing." | Tomorrow it is in there again. |
| "Private appointments never show up in the briefing." | They never show up again. |
| "Don't write so formally." | This one mail gets more relaxed. |
| "I'm on first-name terms with my clients, from now on always." | All drafts are informal from now on. |

Claude then confirms in one line where it recorded that. If that confirmation does not come, it was probably only remembered for this once, so follow up.

Rule of thumb: if the same mistake bothers you a second time, do not correct it again. Say "from now on".

---

## 5. The brake

More commands are not better.

A system with a handful of commands that all get used is worth considerably more than one with twenty where nobody remembers what they do. Every command you do not use makes the list harder to read and the decision harder about which one you actually need right now.

So: when in doubt, create nothing. Keep saying it by hand in the chat. When it annoys you for the third time that you have to explain it, the moment has come, and by then you also know pretty precisely what the command has to look like.
