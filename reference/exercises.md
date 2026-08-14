# Exercises — the first week

This is not a manual, it is a training plan. After the setup you learn the system fastest by using it, not by reading about it. Every exercise is a small scenario to copy, with a clear sign that tells you it worked.

**How to work with it:** one exercise per day is enough. Each takes 5 to 15 minutes. The order is a recommendation, not a rule. You do not have to memorize anything, just say the example sentences like this or in your own words. Tip: dictating is faster than typing (Windows: `Win + H`, Mac: press `Ctrl` twice).

**A note on language:** the example sentences below are English. Claude answers in whatever is set in `context/config.yaml → language`, and you can talk to it in that language too — the system does not care which words you use, only what you mean.

---

## Level 1 — The daily rhythm (day 1 to 3)

**Exercise 1 — Your first briefing** (10 min)
Scenario: you are starting the day with the system for the first time. On the first run Claude asks once whether it may look into your mailbox and calendar.
Say: > "Good morning."
Successful when: you are asked once for permission for mail and calendar, after which `context/today.html` opens in the browser with your day.
Behind it: access to mail and calendar stays with you, fresh every session, nothing happens quietly in the background.

**Exercise 2 — Telling the chat three things** (10 min)
Scenario: something changes during the day. You just say it, no command, without touching a file yourself.
Say: > "Chapter three is done. On project X I'm still waiting on IT. And make me a note, I want to follow up on the Meier quote next week."
Successful when: Claude confirms in one or two sentences where each of the three things landed (status, journal or as a task), and the task then shows up in your dashboard under the project.
Behind it: this is the actual operating mode. You say what is going on, the system files it, you maintain no folders.

**Exercise 3 — Your first end of day** (10 min)
Scenario: end of the workday. You want to record what the day produced.
Say: > "I'm done for today."
Successful when: Claude shows you a finished draft of what happened today, and you only correct it. After that a new entry with today's date sits at the top of `context/JOURNAL.md`.
Behind it: the long memory. In two weeks you can read up on what was decided on which day, without having to remember it.

---

## Level 2 — Material and mail (day 3 to 5)

**Exercise 4 — Reading in a document** (15 min)
Scenario: you have a real deck, a set of minutes or a PDF that belongs to one of your projects. Put the file into the `inbox/` folder.
Say: > "Read this in for me."
Successful when: Claude shows you what is in it (to-dos, decisions), and afterwards the file sits in `projects/<your-project>/inputs/`, no longer in `inbox/`. The to-dos are under the project in your task list.
Behind it: project material lands with the project. If someone refers to "that deck from the other day" next week, Claude finds it again there.

**Exercise 5 — Having your mail style derived** (10 min)
Scenario: so that drafts sound like you and not like standard AI, Claude reads your own sent mail once and learns your tone.
Say: > "Derive my mail style from my sent mail."
Successful when: Claude shows you in a few bullet points what it recognized (how you greet, how long you write, how you sign off), and files that in `context/EMAIL_STYLE.md`.
Behind it: structure beats phrasing. Once your style exists as a file, all future drafts sound like you, without you explaining it every time.

**Exercise 6 — A draft and the correction loop** (10 min)
Scenario: you want to reply to someone. Important: Claude only writes the draft, nothing is ever sent automatically, you do that yourself in your mail program.
Say: > "Write a short mail to Nicole saying Friday works for the meeting." When the first draft arrives, deliberately say: > "Too formal, make it shorter and more relaxed."
Successful when: the second draft is noticeably shorter and more relaxed than the first, and it sits as a draft in your mail program, not in your outbox.
Behind it: you correct instead of rebuilding. "That's not right" or "shorter" is enough, Claude adjusts.

**Exercise 7 — Taking over an inbox find** (5 min)
Scenario: after a briefing, mail finds sit in your inbox zone. They are deliberately not tasks yet, until you decide.
Say: > "Take the first inbox entry over as a task in project X."
Successful when: the entry disappears from the inbox and then sits as a task under project X, with a short context line.
Behind it: nothing disappears quietly, but not every find is immediately a task. You decide what becomes of a find.

---

## Level 3 — Shaping the system (week 2)

**Exercise 8 — Correcting a misclassification permanently** (5 min)
Scenario: a calendar appointment shows up in the briefing that does not belong there, for example your sports class or a private block.
Say: > "The sports class on Tuesday never shows up in the briefing from now on."
Successful when: Claude confirms in one line where it recorded that, and the next morning the appointment is gone without you saying it again.
Behind it: "from now on", "always" and "never" are the lever. They turn a one-off correction into a permanent rule, and the system gets better over time.

**Exercise 9 — Phrasing a good instruction** (10 min)
Scenario: you want something built. Instead of prescribing the route, you describe the goal, and then Claude often finds a better solution than the one you had thought up.
Say, instead of "Make a table with three columns": > "In the Friday meeting I want to see within thirty seconds which quotes have gone unanswered for more than two weeks."
Successful when: Claude only asks about what it really needs to know, and delivers something that answers the question, not just the table you described.
Behind it: say the goal, not the route. That is the biggest lever when working with AI (see `reference/extending-the-system.md`, section 1).

**Exercise 10 — Building your first own command** (15 min)
Scenario: there is one thing you regularly do the same way, for example a weekly status report. From the third time on, a command of your own is worth it.
Say: > "Every Friday I write a status report, always the same projects, always the same structure. Build me a command for that."
Successful when: Claude asks a few short questions (which projects, how long, who reads it), after which you can call the new command with a slash and get your result.
Behind it: recurring routines become your own commands. You describe, Claude builds, you program nothing.

**Exercise 11 — Running the self-check** (5 min)
Scenario: you want to know whether the system itself is in order, before you rely on it.
Say: > "/checkup"
Successful when: Claude checks the workspace and tells you in a few lines that everything is fine, or what it quietly repaired.
Behind it: the system never pretends to be up to date. If something is stuck, you find it here, without having to be able to describe what is wrong.

---

After these eleven exercises you know the whole rhythm. From here the system simply keeps learning along: every time something bothers you, say "from now on", and it is settled permanently. The more often you say in the chat what is going on, the better your briefings get.
