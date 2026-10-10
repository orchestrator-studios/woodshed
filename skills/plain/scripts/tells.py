#!/usr/bin/env python3
"""Find candidate AI-voice tells in a document.

A finder, not a fixer. Over-reports by design: every hit needs a human decision.
Works on markdown, HTML and plain text.

    python tells.py <file> [--category headings|quotes|aphorism|meta|dashes|all]
    python tells.py <file> --counts        # just the tally
"""
import argparse
import html
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- heading text

HEADING_PATTERNS = [
    (re.compile(r"^\s*#{1,6}\s+(.*?)\s*$"), 1),              # markdown
    (re.compile(r"<h[1-6][^>]*>(.*?)</h[1-6]>", re.I | re.S), 1),  # html
    (re.compile(r"<div class=\"grp\">(.*?)</div>", re.I | re.S), 1),  # nav groups
]

# headings that argue, announce or editorialise rather than label
ARGUING_HEAD = re.compile(
    r"\b(why this|why it|what this (really )?means|the point is|worth noting|"
    r"worth noticing|read this|said plainly|in short|the thing to|the one thing|"
    r"what to (know|notice)|here'?s (why|how|what)|note that|remember that|"
    r"keep in mind|the (real|whole|entire) (point|reason|question)|"
    r"this matters|why that matters|what follows|the takeaway|the upshot|"
    r"so what|tl;?dr|the bottom line|in practice|at a glance|"
    r"why (this|that|it) (is|exists|works|happens)|"
    r"(the )?(good|bad) news)\b",
    re.I,
)

# "Name — an explainer clause" / "Name: an explainer clause"
HEAD_EXPLAINER = re.compile(r"^(.{3,60}?)\s*(?:—|--|&mdash;|:)\s+(.{12,})$")

# a heading that is a full sentence (has a finite verb and is long)
HEAD_SENTENCE = re.compile(
    r"\b(is|are|was|were|has|have|does|do|will|would|can|cannot|can't|should|"
    r"must|gets?|goes|comes|means|looks|reads|belongs|lives|stays|wins)\b",
    re.I,
)

HEAD_NUM_PREFIX = re.compile(r"^\s*\d+\s*(?:·|\.|\)|-|—|&middot;)\s+")

# ---------------------------------------------------------------- sentence tells

APHORISM = re.compile(
    r"\b(enforced by hope|motion without movement|comfort is not|"
    r"is not a .{2,30}, it(?:'s| is) a|not .{2,25} but rather|"
    r"and that(?:'s| is) (?:the|exactly) (?:point|whole point|it)|"
    r"that(?:'s| is) (?:the|precisely the) (?:point|whole point)|"
    r"is (?:precisely|exactly) what|"
    r"two .{2,25} under one|"
    r"the .{2,25} that (?:nobody|no one) |"
    r"not .{2,30}; it is |not .{2,30} &mdash; it is |"
    r"a feature,? not a bug|rather than a (?:bug|failure|problem), (?:it|that) is)",
    re.I,
)

META = re.compile(
    r"\b(said plainly|in other words|to put it another way|the one-line version|"
    r"this (?:panel|section|page|document) exists|worth stating|"
    r"before (?:the|we get to the) detail|"
    r"(?:that|this) is (?:encouraging|reassuring) rather than|"
    r"is a feature rather than|rather than a failure|"
    r"the (?:short|long) (?:version|answer) is|"
    r"put simply|simply put|to be clear|let(?:'s| us) be clear|"
    r"taken to its limit|in the limit|at the extreme)\b",
    re.I,
)

# short quoted phrase = a coinage being promoted. Matched only after tags are
# stripped, or every class="..." attribute scores a hit.
SCARE_QUOTES = re.compile(r"[\"“]([^\"”\n]{2,40}?)[\"”]")

HEDGE = re.compile(
    r"\b(not necessarily|arguably|it could be argued|one might say|"
    r"to some extent|in a sense|more or less|somewhat|fairly|quite possibly|"
    r"it(?:'s| is) worth (?:noting|remembering|saying))\b",
    re.I,
)

RULE_OF_THREE = re.compile(r"(?:^|[.!?]\s)(?:\S+\s+){0,3}\S+\.\s+(?:\S+\s+){0,3}\S+\.\s+(?:\S+\s+){0,3}\S+\.")


def strip_tags(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def em_dash_count(line: str) -> int:
    return len(re.findall(r"&mdash;|—|\s--\s", line))


BLOCK_TAGS = re.compile(r"<(style|script)\b.*?</\1>", re.I | re.S)


def blank_blocks(raw: str) -> str:
    """Blank out <style>/<script> bodies, preserving line numbers — CSS comments and
    selectors otherwise flood the quote and dash categories."""
    def repl(m):
        return "\n" * m.group(0).count("\n")
    return BLOCK_TAGS.sub(repl, raw)


def collect(path: Path):
    raw = blank_blocks(path.read_text(encoding="utf-8", errors="replace"))
    lines = raw.split("\n")
    hits = {k: [] for k in ("headings", "quotes", "aphorism", "meta", "dashes")}

    # --- headings, matched across the whole text so multi-line tags work
    for pat, grp in HEADING_PATTERNS:
        for m in pat.finditer(raw):
            text = strip_tags(m.group(grp))
            if not text or len(text) > 140:
                continue
            lineno = raw.count("\n", 0, m.start()) + 1
            why = []
            if ARGUING_HEAD.search(text):
                why.append("argues/announces")
            em = HEAD_EXPLAINER.match(text)
            if em and not re.match(r"^[A-Z0-9]{1,4}\d*\b", text):
                why.append("appended explainer")
            words = text.split()
            if len(words) >= 5 and HEAD_SENTENCE.search(text) and not text.endswith("?"):
                why.append("full sentence")
            if HEAD_NUM_PREFIX.match(text):
                why.append("numbered prefix")
            if why:
                hits["headings"].append((lineno, text, ", ".join(why)))

    # --- line-level tells
    for i, line in enumerate(lines, 1):
        flat = strip_tags(line)
        if not flat:
            continue
        for phrase in SCARE_QUOTES.findall(flat):
            if len(phrase.split()) <= 6 and not phrase.endswith((".", "!", "?")):
                hits["quotes"].append((i, phrase, "quoted coinage"))
        if APHORISM.search(flat):
            hits["aphorism"].append((i, flat[:110], "aphorism/inversion"))
        if HEDGE.search(flat):
            hits["aphorism"].append((i, flat[:110], "hedge"))
        if META.search(flat):
            hits["meta"].append((i, flat[:110], "meta/restatement"))
        if em_dash_count(flat) >= 2:
            hits["dashes"].append((i, flat[:110], f"{em_dash_count(flat)} dashes"))

    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--category", default="all",
                    choices=["headings", "quotes", "aphorism", "meta", "dashes", "all"])
    ap.add_argument("--counts", action="store_true", help="tally only")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.is_file():
        sys.exit(f"no such file: {path}")

    hits = collect(path)
    cats = list(hits) if args.category == "all" else [args.category]
    total = sum(len(hits[c]) for c in cats)

    if args.counts:
        for c in cats:
            print(f"{len(hits[c]):>4}  {c}")
        print(f"{total:>4}  TOTAL")
        return

    for c in cats:
        rows = hits[c]
        if not rows:
            continue
        print(f"\n=== {c}  ({len(rows)}) ".ljust(72, "="))
        seen = set()
        for lineno, text, why in rows:
            key = (text, why)
            if key in seen:
                continue
            seen.add(key)
            print(f"  {lineno:>5}  [{why}]  {text}")

    print(f"\n{total} candidates. Each needs a decision — this tool does not know "
          f"which are deliberate.")


if __name__ == "__main__":
    main()
