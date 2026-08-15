# Version

**v0.2.0**

What changed in it, and whether any of it needs your hand, is in
[`CHANGELOG.md`](CHANGELOG.md). How to move to a newer one is the Updating section of
[`README.md`](README.md) — the short version is `git pull`, and it does not touch your
files.

## When something is broken

Open an issue: <https://github.com/luka-commits/automatable-os/issues>. Include the version
above, what you ran, and what happened instead. There is no support address and no contact
person to chase; the tracker is the whole route, and an issue with the version number in it
is usually enough to tell whether it is already fixed.

**Before you file one, two things are worth a minute:**

```bash
python3 reference/scripts/check_repo.py     # is the copy itself intact
```

and saying `checkup` in the chat, which works through
[`reference/self-test.md`](reference/self-test.md) and reports what is missing rather than
what is wrong with your machine. Between them they catch the common case, which is an
incomplete copy: `.claude/` is a hidden folder and gets dropped by some ways of copying or
zipping a directory. If `.claude/skills/` is missing, no command works and nothing else
matters.

## What "version" means for your copy

Your clone does not update itself, and nothing changes it behind your back. You pull a new
version deliberately, when you want one.

That works because every file that becomes **yours** is in `.gitignore` and ships as
`<name>.example` instead: `config.yaml`, `expertise.md`, `experience.md`,
`testimonials.json`, `STATUS.md`, `.upwork_jobs.json`, the generated dashboard. A pull
replaces the machinery around them and leaves them alone.

The one thing to read before pulling is the **Action needed** section of the changelog. That
is where a version says "this one needs you to edit a file you own" — everything not listed
there takes effect on its own.
