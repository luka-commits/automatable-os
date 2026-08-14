# The two recommended CLIs

Two command-line tools belong to the standard kit in this variant: **firecrawl** and **playwright**. They are not plugins and change nothing about Claude Code itself. They simply sit on the machine, and Claude calls them when a task needs them.

The package also runs without either. But then everything that comes from the internet or needs a real browser falls away.

**You do not have to do any of this by hand.** The setup installs both tools and sets up the accounts with you. This page is for looking things up later, when you want to change something or want to know what all this is good for. If something is missing afterwards, one sentence in the chat is enough ("set up my Firecrawl access"), then Claude walks you through it.

**The manuals are already included.** Every tool comes with a skill that tells Claude how to use it properly. They are part of the package, you do not have to load anything:

| Tool | Included skills |
|---|---|
| firecrawl | `firecrawl` — one skill for all of it (search, scrape, map, crawl, agent, browser, download) |
| playwright | `playwright-cli` |
| OpenRouter | no skill of its own needed, the access is enough |
| Supabase (only if you use databases) | `supabase`, `supabase-postgres-best-practices` |
| Your own agents in the cloud | `managed-agents` (needs a paid API access on top of the subscription) |
| Turning your own documents into something you can listen to or study | `notebooklm` (optional, see below) |
| Web pages and interfaces that have to look good | `design-taste-frontend` — bundled, nothing to install. 21st.dev Magic on top is optional (see below) |

Which task runs through which tool is in `CLAUDE.md` as a table under "Tool Routing". That is the part that makes sure the kit actually gets used day to day.

## firecrawl: web content and search

**What it is for day to day:**

- A client sends a link instead of a document. Claude reads the page as clean text and files it into the project, instead of you doing copy-paste.
- Before a meeting: quickly check what the other side's company says publicly, and turn that into a preparation note.
- A question whose answer is more current than the model's knowledge. firecrawl searches and delivers the full texts of the hits, not just a search engine's snippet lines.
- Pulling an entire documentation site into the project folder to work through it offline.

**What does not work without it:** everything that sits behind JavaScript. Many modern pages return an empty shell on a simple request, the content is only loaded later in the browser. firecrawl renders first, which is why text comes back instead of an empty frame. Without firecrawl you are left with the built-in page fetch, which regularly finds nothing on such pages.

**Relation to the built-in capabilities:** Claude Code can search and fetch pages itself. firecrawl is the better route when the complete content matters or the page is built in a modern way. For a quick factual question the built-in search does the job.

**Installation** (verified, globally via npm):

```
npm install -g firecrawl-cli
```

After that firecrawl needs an API key. The key comes from **your company's own Firecrawl account**, not a shared one — billing and usage data then stay with you. Create an account at [firecrawl.dev](https://firecrawl.dev) (the free tier is enough for testing), the key is there under **API Keys**.

Set the key once, permanently:

**Mac** (Terminal):
```
echo 'export FIRECRAWL_API_KEY="fc-YOUR-KEY"' >> ~/.zshrc
```

**Windows** (PowerShell):
```
setx FIRECRAWL_API_KEY "fc-YOUR-KEY"
```

Then close the terminal once and open it again. Whether the key is in place is shown by:

```
firecrawl --status
``` If you do not want to give the data out of the house at all, you can host Firecrawl yourself and point `FIRECRAWL_API_URL` at your own instance.

## playwright: everything that needs a real browser

**What it is for day to day:**

- Looking at the dashboard after a rebuild and checking that it really looks the way it was meant to. Not "the code should be right", but a screenshot.
- A page that requires a login. firecrawl does not get in there, a real browser does.
- Filling in a form that offers no interface for machines.
- Producing a PDF or screenshot of a page to put into a project.

**What does not work without it:** every visual check. Without playwright, Claude can claim the dashboard is fine without ever having seen it. That is the most common way a "done" turns out to be wrong.

**Relation to firecrawl:** the rule is simple. If it is about the **content** of a page, firecrawl is faster and cheaper. If it is about **interaction or appearance** (clicking, typing, signing in, looking), then playwright. You rarely need both at once.

**Installation** (verified, globally via npm):

```
npm install -g playwright
playwright install chromium
```

The second command downloads the browser that playwright drives. Without it the tool is installed but useless, since it has no browser. A quick test:

```
playwright screenshot https://example.com test.png
```

> **On managed company laptops** this browser download can be blocked or forced through an internal proxy. If it fails, it is almost never your fault: get in touch with the contact person from `VERSION.md`. The rest of the system continues to run fully without playwright.

## OpenRouter: images and specialist models (optional)

Claude cannot generate images. If product shots, illustrations or social graphics are needed day to day — or a self-built skill should call a different model (Gemini image models, Kimi, …) — that runs through **one** OpenRouter account instead of five separate provider accounts: one key, all models, billing in one place.

**Setting it up:** account at [openrouter.ai](https://openrouter.ai), key under **Keys**, then set it permanently (same pattern as the Firecrawl key):

```
echo 'export OPENROUTER_API_KEY="sk-or-YOUR-KEY"' >> ~/.zshrc     # Mac
setx OPENROUTER_API_KEY "sk-or-YOUR-KEY"                          # Windows (PowerShell)
```

**Honest classification:** this is not a day-1 thing. The chat itself always runs through Claude (your subscription, no double payment); OpenRouter only comes into play when there is a concrete need — then Claude will say by itself that the key is missing, and this section is the instruction.

## Web design: taste comes bundled, components are optional

Two pieces, and only one of them needs anything from you.

**The taste is already in the package.** The skill `design-taste-frontend` kicks in whenever Claude builds or redesigns a web page, a landing page or an interface. It is the difference between "looks like every AI-generated page" and something that reads as designed: it infers the right design direction from your brief before writing any code, and it checks its own output against a strict list of the usual AI design giveaways. Nothing to install, nothing to sign up for — it is simply there.

**21st.dev Magic (optional): ready-made, polished UI components.** An MCP server from [21st.dev](https://21st.dev): describe a component ("a pricing table with three tiers", "a hero section with a sign-up form") and it returns production-ready code drawn from a large library of professionally designed components. Worth adding the moment web pages become a recurring part of your work; pointless before that.

**Setting it up (only when the occasion is there, not on spec):** the key comes from your own account at [21st.dev](https://21st.dev) — sign in, generate an API key in the console (free to try, heavier use needs a plan). Then one command, which Claude runs for you once you paste the key:

```bash
claude mcp add magic --env API_KEY="YOUR-21ST-KEY" -- npx -y @21st-dev/magic@latest
```

Restart Claude Code once afterwards, and record it in `config.yaml → inventory` like every other piece of equipment.

## Order when setting up

Both belong to the standard kit in this variant and are installed during the setup. The core system (briefing, projects, drafts, filing) also runs without them, it can just do less. If you really only set up one, take firecrawl. Web content comes up more often day to day than browser automation.

## Optional: gws (Google Workspace CLI)

Only relevant on Google Workspace, and only as the **advanced route** — the normal route to mail and calendar is the Cowork connector (`reference/mcp.md`). `gws` adds the full API surface (write to Sheets, upload to Drive, scripted routines without a Cowork session) at the price of a one-time Google Cloud Console setup. Guide: [`reference/gws-cli.md`](gws-cli.md).

**Eight skills come with it, one per job**, so Claude does not have to guess the command line: `gws-shared` (sign-in, global flags, failure modes — read this first when something is stuck), `gws-gmail` and `gws-gmail-send` (mailbox and sending), `gws-calendar` and `gws-calendar-agenda` (change an appointment vs. just see the day), `gws-drive` (files and sharing), `gws-sheets-read` and `gws-sheets-append` (get values out, put a row in). Nothing to install — they are part of the package and kick in when a task needs them.

## Optional: notebooklm (documents you listen to instead of read)

**What it is for:** it turns your own material — a stack of PDFs, transcripts, notes on one subject — into something you can take in differently: an audio version two people talk through, a briefing, a study guide, an FAQ. The point is not summarizing. The point is that a folder of documents you never get around to reading becomes thirty minutes in the car.

**Install (only when there is a concrete occasion, not on spec):**
```bash
pip install notebooklm-py
notebooklm login    # opens the browser for a Google sign-in, the user does that themselves
notebooklm list     # proves it worked
```

On Windows plain `python`/`pip` is often the Store stub — use `uv run python -m pip install notebooklm-py` there.

**Two things belong said before someone starts:** it needs a Google account and a browser sign-in, and it talks to NotebookLM through an interface Google does not officially publish. It works well and it can break when Google changes something. That is a fair trade for what it does, but it is not the kind of tool you build a weekly routine on without a fallback.

## Optional: /last30days (what people are saying right now)

**What it is for:** every question whose answer has a shelf life. Is this tool worth switching to, what changed in the last few weeks, what is the current advice on X. A model answers those from a training cutoff, and a search engine answers them with whoever bought the top result. This one reads Reddit and X from the last thirty days and comes back with the actual threads and posts, with links.

The line against `firecrawl`: firecrawl fetches a page **you already know about**. This one finds out what is being said when you do not know where to look.

**It is not our skill.** It lives in its own public repo and is installed from there, which means it improves and changes on its own schedule rather than with our releases. Install:

```bash
npx skills add mvanhorn/last30days-skill
```

**It costs money per search, and not through the Claude subscription.** Two API keys of your own do the work: OpenAI searches Reddit, xAI searches X. Both are billed per use, both are separate invoices. They go into the skill's **own** file, not into `credentials.env`:

```bash
mkdir -p ~/.config/last30days && touch ~/.config/last30days/.env && chmod 600 ~/.config/last30days/.env
echo 'OPENAI_API_KEY=<your-key>' >> ~/.config/last30days/.env
echo 'XAI_API_KEY=<your-key>'    >> ~/.config/last30days/.env
```

One key alone is enough to start: with only one of the two it searches only that source and says so. **A run that comes back empty is usually a billing problem, not a broken tool** — an exhausted credit balance surfaces as `401`/`403`/`429` and the report then arrives with zero findings. If a search returns nothing, check the balance first.

Use it as `/last30days <topic>`, optionally `/last30days <topic> for <tool>` when you want prompts you can paste straight into something.

## Optional: herdr (work that keeps running when you close the laptop)

**What it is for:** a long job that must not die because the lid went down or the connection dropped. herdr holds the terminal open on the machine and lets you reconnect from another device, so a run started at the desk can be checked from a phone an hour later.

**Be honest about who needs this.** For most work in this system the answer is no. A briefing takes a minute, a draft takes seconds, and anything that should run **without a person in front of it** belongs in `/schedule`, which is built into Claude Code and needs no installation at all. herdr earns its place when a job genuinely runs for hours and you want to look in on it.

```bash
brew install herdr        # macOS/Linux; Windows is in beta
herdr --version
```

Apache 2.0, its own open project. Documentation: [herdr.dev/docs](https://herdr.dev/docs/).

**The manual is in the package:** skill `notebooklm`, nothing to look up.
