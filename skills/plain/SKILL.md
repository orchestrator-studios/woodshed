---
name: plain
description: Strip the AI voice out of a document — cutesy or editorializing headings, phrases promoted to proper nouns, inverted and aphoristic sentences, invented jargon, and paragraphs that restate what is directly above them. Use when asked to de-slop, de-Claude, plain up, clean up the writing, cut the fluff, remove the clever phrasing, or do an editorial pass on a doc, page, README, memo or artifact. Not a rewrite for content or structure — the facts, claims and layout survive; only the voice changes.
---

# Plain

An editing pass that removes the voice an LLM writes in, without touching what the
document says. Every fact, claim, number and section survives. What goes is the
packaging.

**The test for every change:** did a reader lose any information? If yes, revert.
If no, the cut was voice.

## When this is the right skill

Someone has a document that is factually fine and reads wrong. The usual symptom is
that it sounds like it is selling itself to you — headings that announce rather than
label, sentences built for effect, phrases capitalised into terms of art that nobody
outside the document uses.

Not this skill: restructuring, fact-checking, shortening by cutting content, or
rewriting for a different audience. Those change what the document says. This one
does not.

## Run it section by section

Do **one section, tab, or page at a time**, then stop and show the user before
continuing. A whole-document pass lands as a wall of diff nobody can review, and the
first section is where you calibrate how far they want this taken — some people want
every callout headline gone, some want short plain ones kept.

Ask once, on the first section, if the answer is not obvious from what they said.
After that, apply the same calibration to the rest without re-asking.

## The passes

Work in this order. Later passes depend on earlier ones having fired.

### 1. Headings

A heading is a **label for what is under it**, not a comment on it and not a pitch for
reading it.

| Cut | Keep |
|---|---|
| The Rule We Break on Purpose | Using the gold memo as an input |
| Why This Is Encouraging Rather Than Discouraging | *(delete — the paragraph says it)* |
| The Thing to Push Back On | *(delete — start the paragraph "Push back on…")* |
| Two Honest Caveats | Caveats |
| The Decision, and It Is a Real Fork | The decision |
| Known defect on move 1 — to be fixed before X starts | Before X starts |
| The one bag that worked | A5 — clean |

Specific tells:

- **A heading that argues.** "Why this matters", "What this really means", "The point
  is", "Worth noticing", "Said plainly", "In short", "Read this first".
- **A heading with an appended explainer** after a dash or colon. Keep the name, drop
  the gloss.
- **A heading that is a complete sentence**, unless the section genuinely answers that
  sentence as a question.
- **Numbered prefixes duplicating a numbered nav.** If the sidebar already says 5,
  the heading does not need "5 · ".

When a callout's heading only restates its first sentence, delete the heading and keep
the text. Many callouts need no heading at all.

### 2. Phrases promoted to proper nouns

The model invents a term, capitalises it or wraps it in quotes, and then uses it as
though the reader already agreed to it. Decide per phrase:

- **It is a real term in this domain** — the project uses it, it appears in the code or
  the source documents. Keep it, unquoted, uncapitalised unless it is genuinely a
  proper noun.
- **You invented it for this document** — replace it with the plain words every time.
  Do not keep it "just for brevity".

Scare quotes are the clearest signal. `the "supplying row"`, `a "material" fact`,
`the "one gate"` — if the quotes are doing work, the phrase is not established, and
if the phrase is established the quotes are noise. Either way they go.

**Invented jargon is the worst case and the easiest to miss**, because by the end of
the document it feels native. If a word appears thirty times and appears nowhere in the
source material, it is yours — replace all thirty. Search the repo or the source to
check before deciding.

### 3. Sentences

- **Inversions for effect.** "Not a test report — it *is* the artifact." → "The output
  you produce is the artifact the system is measured against."
- **Aphorisms and epigrams.** "Enforced by hope", "comfort is not evidence", "motion
  without movement". Each one is a claim wearing a costume. State the claim.
- **Noun-phrase-as-epigram.** "Two things under one name." Say which two things.
- **The rule of three with a rhetorical climax.** "Not clarity. Not priority. Ownership."
- **Em-dash stacking.** More than one dash pair per sentence is almost always a sentence
  that wants to be two sentences.
- **Bolding for emphasis rather than for scanning.** Bold the term a reader scans for,
  not the part you want stressed. If three things in a paragraph are bold, none are.
- **"X is not Y; it is Z"** when nobody proposed Y.
- **Hedge-then-assert.** "Not necessarily wrong, but…" Say which.

State the subject, the claim, and the consequence, in that order. A longer plain
sentence beats a short opaque one.

### 4. Content that is not content

Delete outright:

- A paragraph or callout that **restates the paragraph above it**. The giveaway is an
  opener like "Said plainly", "In other words", "The one-line version", "So:".
- A **summary of a list that is three bullets long**.
- **Forward-looking asides** that are not part of the subject — "taken to its limit,
  this approach could…". Interesting, not load-bearing.
- **Reassurance.** "This is encouraging rather than discouraging", "that is a feature
  rather than a bug". Give the reader the facts and let them judge.
- **Meta-commentary about the document** — "this panel exists because", "worth stating
  plainly because it looks like X".

Expect 20–30% length reduction from this pass alone with zero information lost. If you
are cutting more than that, check you are not removing content.

### 5. Second look

Re-read the section cold. Two things only:

- Did any fact, number, caveat or attribution disappear? Put it back.
- Is anything now *too* terse to parse? Plain is not telegraphic — restore the
  connective words. "Abha first, then Michael T." is fine; "Abha, then Michael" is
  worse if the reader does not know who they are.

## Finding the tells

`scripts/tells.py` scans a file and prints candidate lines by category. It is a finder,
not a fixer — it over-reports by design and every hit needs a human or agent decision.

```
python scripts/tells.py <file> [--category headings|quotes|aphorism|meta|all]
```

Works on markdown, HTML and plain text. Run it before the pass to see the scale, and
after to confirm what is left is deliberate.

## What not to touch

- **Technical terms from the domain.** A step, a fixture, a contract, a commit — if the
  project calls it that, so do you.
- **Numbers, dates, names, file paths, citations.** Never reword a quoted source.
- **Structure.** Same sections, same order, same nav. If the structure is wrong, that
  is a separate conversation.
- **The user's own words.** If they wrote a sentence, it stays unless they ask.
- **Deliberate repetition.** A term repeated because the reader needs it in both places
  is not redundancy.

## Verify before you hand it back

- Diff the before and after. Every deletion should be voice, not information.
- If the document has structural invariants — nav entries matching panels, internal
  links, a table of contents — check them. Renaming a heading breaks anchors pointing
  at it.
- Report what changed as a short list of renames plus a note on what was cut. The user
  is deciding whether your calibration was right, and they cannot do that from a diff
  alone.

## Related

Cliff's standing preference on business documents is the same rule stated for prose:
no aphorisms, no compressed phrasing, no inversions for effect. If a memory or project
note covers house voice, it wins over this file.
