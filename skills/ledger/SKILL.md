---
name: ledger
description: Global cross-session work memory — a journal of events, a registry of artifacts, and per-workstream state files at C:\Users\cliff\claude-memory\. Use when significant work completes (deliverable shipped, decision made, artifact produced, email sent), when asked to log work, recall what happened, check what's going on across workstreams, or review open loops. Verbs — log, recall, review, stream.
---

# Work ledger

The ledger is Cliff's global, cross-session memory of *what happened* and *what
was produced*. It lives at `C:\Users\cliff\claude-memory\` and works from any
project directory. It complements — never duplicates — the built-in
auto-memory:

- **Auto-memory** holds durable *facts* (who Cliff is, preferences, standing
  project constraints). Declarative; stays true.
- **The ledger** holds *events* (chronological journal), *artifacts* (registry
  with links), and *workstream state* (current status + open loops).

If something is a fact that stays true, it belongs in auto-memory. If it's a
thing that happened or a thing that was made, it belongs here.

## Layout

```
C:\Users\cliff\claude-memory\
  INDEX.md              one-screen orientation; injected at session start
  journal\YYYY-MM-DD.md append-only daily event log
  streams\<slug>.md     one file per workstream: status, state, open loops
  streams\archive\      closed streams
  artifacts\index.md    registry table: date | stream | artifact | home (link)
```

## Verbs

Invoked as `/ledger <verb> [args]`. Bare `/ledger` → show INDEX.md and offer
the verbs.

### log

Record what just happened. Steps:

1. Append an entry to today's `journal\YYYY-MM-DD.md` (create the file with a
   `# YYYY-MM-DD` heading if new):

   ```markdown
   ## <stream-slug>: <one-line headline>

   - what happened / was decided, in 1–4 bullets
   - links to artifacts, PRs, docs
   ```

2. If an artifact was produced, add a row to `artifacts\index.md` (newest
   first) and link its home.
3. Update the affected `streams\<slug>.md`: current state, open loops,
   **Next action**, and the Updated date. Create the stream file (copy an
   existing one as template) if this is a new workstream.
4. Update `INDEX.md`: the stream's one-liner and the Recent activity list
   (keep ~5 entries; INDEX.md stays under ~40 lines).

### recall <topic>

Answer "what happened with X / where is Y":

1. Read `INDEX.md`; if a stream matches, read its file — usually sufficient.
2. If not, Grep `journal\` and `artifacts\index.md` for the topic.
3. Answer with dates, links, and current state. If the ledger has nothing,
   say so plainly — don't guess.

### review [week|month]

The management overlay. Default scope: last 7 days.

1. Read all active `streams\*.md` and the journal files in scope.
2. Produce a digest: **what moved** (per stream), **what's stalled** (streams
   whose Updated date is older than the scope), **open loops** across all
   streams, and **suggested next actions**.
3. Offer to update stream files or close finished streams based on the review.

### stream <name> [close]

Show or update one stream file. `close`: move it to `streams\archive\`,
remove it from INDEX.md, and log the closure in the journal.

## What qualifies for logging

Log: deliverables shipped, decisions made, artifacts produced, external
communications sent (email, Slack post, invoice), a workstream changing state,
open loops created or closed.

Don't log: routine lookups, intermediate work, anything reconstructible from
git history, the repo, or the tool it lives in. When in doubt about a
decision-shaped conversation, log the conclusion in two sentences.

## Artifact policy

**The ledger stores records, never payloads — unless the payload has no home.**

- Artifact landed somewhere real (Drive, Sheets, GitHub, HubSpot, a repo) →
  registry row with the link. Never copy content into the ledger.
- Email sent → journal event with recipient, subject, date. Gmail is the
  system of record; don't copy the body.
- Inline-only artifact (drafted email, analysis, recommendation with no
  natural home) → give it a home: upload it to the Drive folder
  `Claude-Memory-Artifacts` via the gws CLI (use the
  `orchestra:google-workspace` skill; create the folder on first use if
  missing), then register the link. Only if Drive is unavailable, save under
  `artifacts\inline\` as a last resort and note it needs a home.

## Hygiene

- Journal files are append-only; never rewrite past days.
- Stream files describe *current* state — rewrite them freely.
- Convert relative dates to absolute when writing.
- INDEX.md is injected into every session at startup: keep it under ~40
  lines, one line per active stream, ~5 recent-activity entries.
- If a stream has seen no activity in a month, ask Cliff whether to close it
  during the next `review`.
