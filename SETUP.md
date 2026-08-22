# Setup: from a fresh clone to a working system

Three ways in, depending on how you use Claude. Pick one, they end in the same place. Reckon
with 20 to 30 minutes, once.

**The one thing that decides whether this works:** Claude has to be running **inside this
folder**. It has no icon, it does not announce where it is, and in the wrong folder it answers
perfectly normally while knowing nothing about this system. No error message, no hint. That is
where most setups fail, and it usually only becomes apparent twenty minutes in.

---

## Before you start

| You need | Why | If it's missing |
|---|---|---|
| **Claude Code** | This is a Claude Code workspace, not a hosted app | [claude.com/claude-code](https://claude.com/claude-code) |
| **git** | Fetches the repo, and the evening backup pushes to your own copy | Comes with Xcode tools on macOS, [git-scm.com](https://git-scm.com) on Windows |
| **Python 3.9+** | Renders the dashboard and runs the session checks. Standard library only, nothing to install on top | [python.org](https://python.org). On Windows tick "Add to PATH" during install |
| **The Upwork connector** | Only for the Upwork add-on. The base layer works fully without it | Claude app → Customize → Connectors → Upwork |

Node is optional. Without it the Tooling tab stays empty and everything else runs.

---

## Step 1: Get the folder onto your machine

```bash
git clone https://github.com/luka-commits/automatable-os.git
cd automatable-os
```

**Do not clone into a folder that syncs** (iCloud Drive, OneDrive, Dropbox). Sync services
create conflict copies on fast writes, and you end up with `STATUS 2.md` next to `STATUS.md`
with no way to tell which one is real. Somewhere local: `~/workspace`, `C:\dev`, anything that
is only on this machine.

**Check:** `ls -a` shows `CLAUDE.md`, `context/`, `projects/` and `.claude`. If `.claude` is
missing, you are one folder too high or the clone did not finish.

---

## Step 2: Start Claude in that folder

Three routes. They differ only in how the folder gets opened.

### Route A: Terminal

```bash
cd automatable-os
claude
```

The prompt appears, and you are in the right place.

### Route B: VS Code

1. **File → Open Folder**, choose the cloned `automatable-os` folder. Not its parent, not your
   projects folder: this folder.
2. Open the Claude panel (the Claude icon in the sidebar, or the command palette →
   "Claude Code").
3. Type "hello".

**The trap that looks exactly like success:** if you have a workspace open with several folders
in it, or you opened the parent directory, the Claude panel starts fine and answers normally.
It is simply not in this folder, so none of this system applies. The check below catches it.

### Route C: The Claude desktop app

Open the folder as the working directory for the session, then type "hello". The same rule
decides everything: the session has to point at `automatable-os` itself.

One difference worth knowing: the dashboard is rendered by a Python script. Claude runs it for
you as part of `/morning` and after the screener, so you do not need a terminal for normal use.
If you ever want to render it by hand, that is the one thing you need a terminal for.

### The check, whichever route you took

Type this as your first message:

> where are you running, and is this workspace set up?

A correct answer names this folder and tells you the setup has not run yet. An answer that is
friendly but generic, with no idea what "this workspace" means, is the wrong-folder case from
above. Nothing is broken; the session is just somewhere else.

---

## Step 3: Let the setup run

You do not have to type a command. A session-start hook notices `context/config.yaml` is
missing and begins on your first message. If you would rather drive it yourself:

> set up automatable os

It asks for your name, what you work on, and which tools you already use, then it writes
`context/config.yaml` and fills the workspace. **If you say you work on Upwork**, it connects
your account and reads it before asking anything else: your profile, your past contracts, and
the full text of proposals you have already sent.

**Say no to anything you do not want.** Nothing here is mandatory, Upwork included. The day
loop, the projects and the dashboard work on their own, and the setup names at the end what was
skipped and what that costs you.

---

## Step 4: Look at the dashboard

The setup renders it. Open `context/today.html` by double-clicking it, or from a terminal:

| Your system | Command |
|---|---|
| macOS | `open context/today.html` |
| Windows | `start context/today.html` |
| Linux | `xdg-open context/today.html` |

To re-render it after your data changes:

```bash
python3 reference/scripts/render_dashboard.py
```

**On Windows that is usually `python`, not `python3`** — a plain Windows install ships one and
not the other. If `python3` says "command not found", try `python reference/scripts/render_dashboard.py`.
The session hooks handle this difference on their own; only this manual command does not.

---

## When something does not work

**Claude answers normally but knows nothing about this system.** It is running in a different
folder. This is by far the most common one and it produces no error at all. In VS Code, check
which folder the explorer shows at the top; in a terminal, `pwd`. Then reopen in this folder.

**"It says my Upwork account isn't connected", right after connecting it.** A connection made
mid-session is invisible to that session. Restart the session and it is there.

**The dashboard does not update.** It is a generated file, so it changes only when the renderer
runs. Run it by hand (Step 4) and read what it prints. If it reports unfilled placeholders, a
source file upstream is missing a value — fix that, never the generated HTML, because the next
render overwrites your edit.

**"python3: command not found".** Either Python is not installed or it is called `python` on
this machine. Both are covered in Step 4.

**The session-start checks say nothing at all.** They stay silent when everything is in order.
That is the intended behaviour, not a failure.

---

## Every day after this

Open the folder the way you did in Step 2, and say good morning. Everything else follows from
there: `/morning` opens the day, `/eod` closes it.

**What works once this is done** is laid out on two pages, both a double click:
[`WHAT-WORKS-BASE.html`](WHAT-WORKS-BASE.html) for the base layer, and
[`WHAT-WORKS-UPWORK.html`](WHAT-WORKS-UPWORK.html) for the Upwork add-on.
