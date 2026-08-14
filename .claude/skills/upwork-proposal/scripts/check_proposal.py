#!/usr/bin/env python3
"""
Check a proposal draft against the countable rules of Catliff's formula.

Why this exists: the formula ends in a list of failure conditions that are all
mechanical (word count, banned phrases, how many benefits carry a number). A rule
like that, left in prose, gets followed about half the time. Counted, it gets
followed. Everything here is countable on purpose.

What it deliberately does NOT do: judge whether the writing is any good. Risk
reversal and CTA are reported as "check by eye" rather than pass/fail, because a
regex cannot tell a real risk reversal from a sentence that happens to contain
the word "refund". A checker that cries wolf gets ignored within two days, and
then it is worse than no checker at all.

Usage:
    python3 check_proposal.py draft.md
    python3 check_proposal.py draft.md --job-title "GHL Expert"

Exit 0 = every hard check passed. Exit 1 = at least one hard check failed.
"""

import argparse
import pathlib
import re
import sys

# From the formula, verbatim. These are the tells of a generic proposal, which is
# why they cost the job rather than merely reading badly.
BANNED = [
    "i would love to",
    "i'm excited",
    "i am excited",
    "what stood out",
    "passionate",
    "results-driven",
    "i want in",
    "rockstar",
    "ninja",
]

# The cover letter ends where the screening answers begin. Catliff keeps the word
# cap on the letter alone, so the split has to happen before counting.
SCREENING_MARKERS = [
    "screening question",
    "screening answers",
]

VIDEO_SIGNALS = ["loom.com", "[insert loom link", "walkthrough of how i'd", "walkthrough of how i would"]
RISK_SIGNALS = ["you don't pay", "you do not pay", "risk-free", "risk free", "full refund",
                "only pay after", "approve each phase", "before we sign", "milestones, not lump"]
CTA_SIGNALS = ["let's hop on", "lets hop on", "send me a quick message", "reply with your",
               "when works for you", "book a", "15-min", "15 min", "30-min", "30 min"]


def split_letter(text):
    """Return (cover_letter, screening_section_or_None)."""
    low = text.lower()
    for marker in SCREENING_MARKERS:
        idx = low.find(marker)
        if idx == -1:
            continue
        # Walk back to the separator line above the header, if there is one.
        cut = text.rfind("---", 0, idx)
        if cut == -1:
            cut = text.rfind("\n", 0, idx)
        return text[:cut], text[cut:]
    return text, None


def word_count(text):
    return len(re.findall(r"\b[\w'-]+\b", text))


LIST_MARKER = re.compile(r"^(\d+[.)]|[-*•✅])\s+")


def list_lines(text):
    """List items, numbered or bulleted, with the marker stripped.

    The marker has to go before counting digits. Otherwise "1. Great automation
    work" counts as quantified purely because of its own numbering, and a list
    with no metric in it sails through. Caught exactly that way in testing.
    """
    out = []
    for line in text.splitlines():
        s = line.strip()
        if LIST_MARKER.match(s):
            out.append(LIST_MARKER.sub("", s))
    return out


def carries_a_number(line):
    return bool(re.search(r"\d", line))


def first_sentences(text, n=3):
    body = text.strip()
    parts = re.split(r"(?<=[.!?])\s+", body)
    return " ".join(parts[:n])


def main():
    ap = argparse.ArgumentParser(description="Check an Upwork proposal draft against the countable rules.")
    ap.add_argument("draft", help="path to the draft file")
    ap.add_argument("--job-title", default="",
                    help="job title from the listing; enables the opening check")
    args = ap.parse_args()

    path = pathlib.Path(args.draft).expanduser()
    if not path.is_file():
        print(f"ABBRUCH: {path} existiert nicht.", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")

    letter, screening = split_letter(text)
    hard_failures = []
    warnings = []
    notes = []

    # --- hard: word count -------------------------------------------------
    wc = word_count(letter)
    if wc > 400:
        hard_failures.append(f"Cover letter is {wc} words, cap is 400. Cut {wc - 400}.")
    elif wc < 300:
        warnings.append(f"Cover letter is {wc} words, target starts at 300. Thin, but not a fail.")
    else:
        notes.append(f"Word count {wc}, inside 300-400.")

    # --- hard: banned phrases --------------------------------------------
    low_letter = letter.lower()
    hits = [p for p in BANNED if p in low_letter]
    if hits:
        hard_failures.append("Banned phrasing present: " + ", ".join(f'"{h}"' for h in hits))
    else:
        notes.append("No banned phrasing.")

    # --- hard: em dashes (workspace rule, applies to all outgoing copy) ---
    dashes = text.count("—")
    if dashes:
        hard_failures.append(f"{dashes} em dash(es) present. Use a colon, comma or full stop.")
    else:
        notes.append("No em dashes.")

    # --- hard: video line -------------------------------------------------
    if any(sig in low_letter for sig in VIDEO_SIGNALS):
        if "[insert loom link" in low_letter:
            notes.append("Video line present, still a placeholder. You record it before sending.")
        else:
            notes.append("Video line present with a real link.")
    else:
        hard_failures.append("No video walkthrough line. It stays in even when no video exists yet.")

    # --- hard: quantified benefits ---------------------------------------
    items = list_lines(letter)
    quantified = [l for l in items if carries_a_number(l)]
    if len(quantified) < 5:
        hard_failures.append(
            f"Only {len(quantified)} list items carry a number, {len(items)} items total. "
            "The delivery list needs at least 5 quantified, 7 is the target."
        )
    else:
        notes.append(f"{len(quantified)} quantified list items.")

    # --- hard: job title in the opening ----------------------------------
    if args.job_title:
        opening = first_sentences(letter, 3).lower()
        if args.job_title.lower() in opening:
            notes.append("Job title named in the opening.")
        else:
            hard_failures.append(
                f'Job title "{args.job_title}" is not in the first three sentences.'
            )

    # --- eye: the semantic ones ------------------------------------------
    eye = []
    eye.append(("Risk reversal", any(s in low_letter for s in RISK_SIGNALS)))
    eye.append(("Clear CTA", any(s in low_letter for s in CTA_SIGNALS)))
    if screening is not None:
        eye.append(("Screening answers kept separate from the letter", True))

    # --- report -----------------------------------------------------------
    print("=" * 60)
    print(f"Proposal check: {path.name}")
    print("=" * 60)

    for n in notes:
        print(f"  ok    {n}")
    for w in warnings:
        print(f"  warn  {w}")
    for f in hard_failures:
        print(f"  FAIL  {f}")

    print("\nCheck these by eye, a script cannot judge them:")
    for label, found in eye:
        mark = "looks present" if found else "NOT FOUND, verify"
        print(f"  ?     {label}: {mark}")
    if screening is None:
        print("  ?     No screening section found. Correct only if the listing had no questions.")

    print()
    if hard_failures:
        print(f"{len(hard_failures)} hard check(s) failed. Fix before showing it to the user.")
        return 1
    print("Hard checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
