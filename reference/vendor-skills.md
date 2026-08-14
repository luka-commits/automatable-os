> **Related:** three small scripts run automatically at the start of every session (`.claude/hooks/`). `check-setup.sh` says so if the setup has never run, `check-updates.sh` looks once a day for a newer version, and `setup-check.py` names the pieces that are still missing once the setup is done — no backup repo, no mailbox, no calendar, a key that is claimed but absent. Each stays silent when there is nothing to say; together they are the reason a half-finished workspace does not stay half-finished unnoticed.

# Skills from outside — what they are and how they update

Most skills in this package are ours. A few come from other people's open repositories and ship along, licence and all. **The difference matters for updates**, which is why they are listed here rather than mixed in silently.

| | Ours | From outside |
|---|---|---|
| Who owns it | this package | an upstream repository |
| Does a workspace adapt it | sometimes | never |
| How it updates | with a package version, per workspace, your four folders always win | **take the newer version, everywhere at once** — nobody has changed it locally, so nothing can be lost |

An update to an outside skill is therefore cheap and safe. An update to ours needs the careful route in `VERSION.md`, because a workspace may have grown around it.

## What ships from outside

### `last30days` — research on Reddit, X and the web

- **Upstream:** `github.com/mvanhorn/last30days-skill`
- **Licence:** MIT (`LICENSE` ships inside the skill folder)
- **Shipped version:** 3.18.4
- **Shipped without:** the `assets/` folder (14 MB of demo pictures for the README) and the repository history. Only `SKILL.md`, `scripts/`, `references/` and the licence come along.

**It needs two things the package does not provide.** Python **3.12 or newer** — the package's own scripts run on older versions, this one does not, and it says so plainly when started on an older one. And API keys of the user's own: `OPENAI_API_KEY` and `XAI_API_KEY`, billed per search, in `~/.config/last30days/.env`. Without keys the skill is present and reports honestly that it lacks access.

**To update it:**

```
git clone --depth 1 https://github.com/mvanhorn/last30days-skill /tmp/l30d
rm -rf _claude-template/skills/last30days
mkdir -p _claude-template/skills/last30days
cp /tmp/l30d/skills/last30days/SKILL.md /tmp/l30d/LICENSE _claude-template/skills/last30days/
cp -R /tmp/l30d/skills/last30days/scripts /tmp/l30d/skills/last30days/references _claude-template/skills/last30days/
```

Then note the new version in the line above, run `python3 reference/scripts/routing_check.py`, and publish. **Watch for a moved path:** on 08.08.2026 the upstream moved the skill from the repository root into `skills/last30days/`, which silently broke every symlink pointing at the old place.

## What does not ship, and why

Some tools are named in `reference/tools.md` and installed by the setup rather than shipped: `herdr` (a package manager handles it better than we do) and the plugins from the official catalogue (they update themselves). The rule is simple — **ship what a clone must carry, install what a machine can fetch.** A skill only reaches a colleague who clones the repository if it is *in* the repository.
