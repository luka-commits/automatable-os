# Changelog

What changed between versions, and what you have to do about it. Anything under
**Action needed** touches a file you own; everything else updates itself on `git pull`.

The format is [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[SemVer](https://semver.org/). Major means your own files need editing, minor means new
capability that leaves your setup alone, patch means a fix.

## [Unreleased]

Work in progress on the author's machine, not yet in this repo. Listed so you know what
is coming and can decide whether to wait:

- A daily proposal tracker in the dashboard: goal, streak, week, and a one-click handover
  of the day's remaining applications
- Job history per record (`history`, `applied_at`), which turns the funnel from a snapshot
  into a real cohort and makes "how many went out today" answerable at all
- A detail overlay per job with the fields that decide an application: connects cost,
  competing bid range, whether the client already hired, and whether you clear their
  minimum bar
- `upwork-inbox` and `upwork-reply`: the account side (messages, invitations, offers) and
  drafted client replies. Drafts only, never sends
- The rules of the road in one place: what Upwork allows, with numbers and sources

## [0.1.0] - 2026-08-14

First public version.

### Added
- `upwork-screener` - searches Upwork on broad terms, scores every result 0-100 against
  your own niche, logs candidates with a status, optionally Slack-DMs strong matches
- `upwork-pitch-page` - a one-page pitch site for a single job, with an editable solution
  diagram and a slot for your own walkthrough video
- `upwork-proposal` - the submitted cover-letter text, built from a video transcript when
  you have one
- `setup-freelancer-os` - run once; writes the config every other skill reads
- A two-tab dashboard (Today / Upwork) rendered to a single static HTML file, with a
  sortable list, a pipeline board, and a funnel
- `upwork_status.py` - the small CRM that moves a job between pipeline stages

### Notes
- The dashboard never writes. Every button copies a ready sentence for you to paste into
  your Claude Code chat; Claude does the actual work with its normal safeguards.
- Nothing is sent to Upwork without you saying so. See the rules section in `CLAUDE.md`.
