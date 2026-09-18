---
name: intake
description: Bring external source material into a project the disciplined way — acquire a local copy, preserve provenance and the supersession chain, derive friendly versions (Markdown / dark-mode HTML), assess what arrived, and write a standing intake-notes report ending in questions for the source's owner. Use when asked to intake, ingest, bring in, or process a document, spreadsheet, transcript, or batch of files — whether it arrives from Drive, Gmail, a URL, Zoom, or a local path. NOT the discovery sweep that decides what to bring in — intake starts once the asset and its owning project area are named.
---

# Intake

Turn material someone handed you into a project asset you can trust: a raw copy
that will never change, a record of exactly where it came from, versions that
are pleasant to work with, and an honest report of what it actually contains —
including what's wrong with it.

**Boundary.** Deciding *what* to bring in (sweeping inboxes, chats, Drive
shares) is a separate overlay process — do it before invoking this skill, or as
its own task. Intake begins when you can name (1) the asset(s) and (2) the
project area they belong to. If either is unknown, resolve that first.

The skill is mostly a **procedure**: it composes the capabilities already
present (the `google-workspace` skill for Drive/Gmail, `zoom` for transcripts,
WebFetch for URLs, Python/openpyxl for spreadsheets, the `artifacts` doctrine
for dark-mode HTML). Recurring derivations ship as scripts in `scripts/`
(currently `xlsx_tabs_to_md.py` — prose spreadsheet tabs → faithful Markdown);
prefer extending them over writing one-off converters inside a project.

## The five stages

Run them in order. Each stage's output is the next one's input.

### 1 · Home — before touching anything

Establish where the intake lives:

- Find the **most specific owning area** of the project the material belongs to
  (e.g. `tracks/3-service-discovery-binding/`), and create **`intake/`** inside
  it. Ask only if the area is genuinely ambiguous.
- **Single asset** → files land directly in `intake/`.
- **A batch** (several files arriving together as one delivery) → keep the
  originals in `intake/<batch-name>/raw/`, derived assets and notes beside
  `raw/`, not inside it.
- Filenames are **date-stamped snapshots**: `evaluation-workbook-2026-09-17.xlsx`.
  The date is the acquisition date — it is what makes re-intake of a living
  source coherent.

### 2 · Acquire — get a local copy

Whatever the channel, the goal is identical: a byte-exact local copy.

| Arrives as | How to fetch |
|---|---|
| Drive file / share link | `google-workspace` skill; download natively (`alt=media`) for binary formats, export for native Docs/Sheets. Pick format to **preserve what matters** — e.g. keep .xlsx when cell formatting (highlight colors) carries meaning |
| Gmail attachment | `gws gmail users messages attachments get` |
| URL | WebFetch / curl; note access date |
| Zoom recording/transcript | `zoom` skill |
| Local / pasted file | copy into the intake home |

Rules:

- **Raw is sacred.** The acquired file is never edited — only derived from.
- If the user also wants the project's own **cloud folder** updated (replace a
  stale copy in Drive), do that as part of this stage: trash — never
  permanently delete — the superseded copy, put the canonical one in place,
  and record both ids in the provenance block.
- A **live source** (a file the owner keeps editing) can only ever be
  snapshotted. Say so in the notes, and re-snapshot before any work that
  depends on its current state.

### 3 · Provenance — the block that makes the copy trustworthy

Record, in the intake notes (stage 5), before analysis distracts you:

- Source identifier (Drive file id, message id, URL) and its **owner**.
- Who supplied it, when, through what channel.
- **Their instructions verbatim.** The sender's one throwaway sentence
  ("pink = the ones I vetted myself") is routinely the most important fact in
  the delivery. Quote it; don't paraphrase.
- The **supersession chain**: what this replaces, where every stale copy now
  is (trashed, archived, renamed), and any duplicate shares to disregard.
- Live or fixed: is the source still moving under its owner's hand?

### 4 · Derive — the friendly versions

Create the versions the project will actually read:

- **Prose-shaped sources** (PDFs, Word docs, transcripts, long emails) →
  **Markdown**, faithful to the source's own structure.
- **Reference / visual material** (things the team will return to, compare, or
  present) → **dark-mode HTML** per the `artifacts` skill's doctrine; explain
  the system, not the artifact.
- **Spreadsheets** usually don't get "converted" — they get *measured* (stage
  5); derive extracts only when a slice earns it (e.g. the gold-set rows as a
  table in the notes). The exception: **prose tabs embedded in a workbook**
  (column dictionaries, process workflows, usage guides) earn a Markdown
  rendering — use `scripts/xlsx_tabs_to_md.py`.

Derived files sit beside the raw file (or beside `raw/`), named after it.
Derivations are **regenerable** — if raw and derived ever disagree, raw wins
and the derivation is rebuilt. Every derived file's header records the exact
command that regenerates it (the bundled scripts do this automatically).

### 5 · Assess & report — size it up honestly

**The assessment, typed to what arrived:**

- *Spreadsheet* — every tab and its purpose; the column layout (verify whether
  all tabs share it — don't assume); row counts; value distributions on the
  columns that matter; formulas and what they encode; **cell formatting as
  data** (fills, colors — ask what unexplained ones mean, don't guess).
- *Document* — structure, the claims it makes, what it says is elsewhere or
  "available on request".
- *Transcript* — parties, decisions, commitments made in each direction, dates.
- *Batch* — per-file one-liners plus the relationships between them.

**Always hunt for contradictions and drift** — this is where intake earns its
keep, and a catalog that skips it has missed the point:

- Internal inconsistencies (two scales for one score, guides referencing
  columns that don't exist, thresholds that disagree).
- Drift against what the project already believes — check the repo's existing
  claims (notes, visuals, READMEs) against the new material and **update every
  stale statement you find**, not just the headline numbers.
- Uniformity smells: machine-generated content shows clustering and
  too-perfect regularity. Say so when you see it.
- Measure, never estimate — and label every number with the snapshot date it
  was measured from.

**The report:** one standing intake-notes document per asset or batch
(`intake/<asset>-notes.md`), skeleton:

1. **Provenance** (stage 3's block)
2. **Structure** — what the thing is, tab by tab / section by section
3. **Measurements** — the numbers, dated
4. **Findings & inconsistencies** — what's notable, what's contradictory,
   what smells
5. **Questions for the owner** — intake is not finished until it has produced
   the list of things only the source's owner can answer

The notes are a **current-state document, never a changelog** — a re-intake of
a newer snapshot rewrites them in place (the date-stamped raw files preserve
history; the prose doesn't need to).

## Closing out

The standing duties apply as everywhere else: commit the intake (raw file,
derived assets, notes, and every stale-claim fix it triggered) as one commit,
and log the outcome to the `ledger` — including the supersession facts, which
other sessions need most.

## Where this skill lives

**Source: `C:\code\woodshed\skills\intake`. Always edit there.**
`~/.claude/skills/intake` is a junction to it — one set of files, two paths.
Commit the woodshed repo after editing.
