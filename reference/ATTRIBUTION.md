# Where the borrowed pieces come from

This package is mostly its own code and its own text. In three places something came from elsewhere, and this is where that is recorded.

## Bundled Anthropic skills

Eight skills under `.claude/skills/` are Anthropic's, not ours. They ship with the package so that documents, decks, PDFs and browser work simply function, without anyone having to hunt them down first:

`docx` · `pdf` · `powerpoint` · `skill-creator` · `writing-clearly-and-concisely` · `managed-agents` · `supabase` · `playwright-cli`

Some of them carry their own `LICENSE.txt` in their folder ("© 2025 Anthropic, PBC"); where that file is missing, the same terms apply — it was lost when the folder was copied, not deliberately removed. They are used as delivered, unmodified.

## Review criteria in the /audit skill

`.claude/skills/audit/references/code-review.md` holds our own German-language set of criteria for judging code. The substance behind it comes from two open Anthropic projects:

- **claude-code-security-review** (MIT, © 2025 Anthropic) — the list of patterns that look dangerous but are not findings
- **code-review** from the official plugin marketplace (Apache 2.0) — the procedure with several viewpoints and a separate confidence pass

What was taken is criteria and procedure, no source code. Neither project ships with this package, and neither one runs.

## Two tools the setup installs but does not ship

Neither of these is in this repository. The setup offers them, the user installs them from the original source, and they update on their own schedule.

- **`herdr`** (Apache 2.0, github.com/herdrdev/herdr) — the agent runtime that keeps long jobs alive. Installed via Homebrew, optional, nothing in the package depends on it.

## A recommended plugin

The `/audit` skill points at the `claude-automation-recommender` skill from the **claude-code-setup** plugin (Apache 2.0, official marketplace). The user installs that themselves; it is not part of this package.

---

_Everything else in this repository is our own work. It is delivered for use inside your own business; passing it on to third parties is not covered by that._
