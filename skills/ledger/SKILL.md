---
name: ledger
description: Global cross-session work memory — a journal of events, a registry of artifacts, and per-workstream state files in the user's ledger folder (default ~/claude-memory). Use when significant work completes (deliverable shipped, decision made, artifact produced, email sent), when asked to log work, recall what happened, check what's going on across workstreams, or review open loops. Verbs — log, recall, review, stream, dash.
---

# Work ledger

The ledger is the user's global, cross-session memory of *what happened* and
*what was produced*. It lives in the **ledger root** — `~/claude-memory` unless
the user has designated another location — and works from any project
directory. It complements — never duplicates — Claude Code's built-in
auto-memory:

- **Auto-memory** holds durable *facts* (who the user is, preferences,
  standing project constraints). Declarative; stays true.
- **The ledger** holds *events* (chronological journal), *artifacts* (registry
  with links), and *workstream state* (current status + open loops).

If something is a fact that stays true, it belongs in auto-memory. If it's a
thing that happened or a thing that was made, it belongs here.

## Layout

```
<ledger root>/
  INDEX.md              one-screen orientation (see Setup for startup injection)
  journal/YYYY-MM-DD.md append-only daily event log
  streams/<slug>.md     one file per workstream: status, state, open loops
  streams/archive/      closed streams
  artifacts/index.md    registry table: date | stream | artifact | home (link)
  views/dashboard.html  generated visual dashboard (see Dashboard)
  views/artifact-url.md persistent URL of the published dashboard
```

If the ledger root doesn't exist yet, offer to bootstrap it: create the
layout above with an empty INDEX.md, an empty artifacts registry, and a first
journal entry noting the ledger was created.

## Verbs

Invoked as `/ledger <verb> [args]`. Bare `/ledger` → show INDEX.md and offer
the verbs.

### log

Record what just happened. Steps:

1. Append an entry to today's `journal/YYYY-MM-DD.md` (create the file with a
   `# YYYY-MM-DD` heading if new):

   ```markdown
   ## <stream-slug>: <one-line headline>

   - what happened / was decided, in 1–4 bullets
   - links to artifacts, PRs, docs
   ```

2. If an artifact was produced, add a row to `artifacts/index.md` (newest
   first) and link its home.
3. Update the affected `streams/<slug>.md`: current state, open loops,
   **Next action**, and the Updated date. Create the stream file (copy an
   existing one as template) if this is a new workstream.
4. Update `INDEX.md`: the stream's one-liner and the Recent activity list
   (keep ~5 entries; INDEX.md stays under ~40 lines).

### recall <topic>

Answer "what happened with X / where is Y":

1. Read `INDEX.md`; if a stream matches, read its file — usually sufficient.
2. If not, Grep `journal/` and `artifacts/index.md` for the topic.
3. Answer **inline, in prose** — single-fact recall does not get a dashboard.
   Include dates, links, and current state. If the ledger has nothing, say so
   plainly — don't guess.

### review [week|month]

The management overlay. Default scope: last 7 days.

1. Read all active `streams/*.md` and the journal files in scope.
2. Produce a digest: **what moved** (per stream), **what's stalled** (streams
   whose Updated date is older than the scope), **open loops** across all
   streams, and **suggested next actions**.
3. Regenerate and republish the dashboard (see Dashboard below) and give the
   user its link alongside a short inline summary.
4. Offer to update stream files or close finished streams based on the review.
   If a stream has seen no activity in a month, ask whether to close it.

### stream <name> [close]

Show or update one stream file. `close`: move it to `streams/archive/`,
remove it from INDEX.md, and log the closure in the journal.

### dash

Regenerate and republish the dashboard from current ledger state without a
full review digest.

## Dashboard

Overview-shaped questions ("what have we been up to?", "where does everything
stand?", weekly reviews) get a **visual dashboard**, not a wall of inline
text. Single-fact recall stays inline. The dashboard is canned — the same
layout every time, filled from ledger data — so it stays glanceable.

**Generate:** fill `views/dashboard.html` from the template at
`assets/dashboard-template.html` (in this skill's directory; on first use copy
it to `views/` and replace every `<!-- DATA:... -->` block). Data blocks:
GENERATED (timestamp + source path), TILES (active streams / open loops /
events in window), STREAMS (card per active stream: name, staleness pill,
next action, updated date, loop count), ACTIVITY (14-day dot matrix from
journal events and stream updates), LOOPS (all open loops, chip-tagged by
stream), ARTIFACTS (registry tail, linked).

Template rules — keep them so every regeneration looks like the last:
- Stream colors come from the template's categorical slots in **fixed order
  of stream creation**; a stream keeps its color for life. More streams than
  slots → reuse the pattern in `:root` by adding slots from a validated
  palette, never ad-hoc hues.
- Staleness: fresh ≤ 3 days since update, aging 4–14, stale > 14. Always a
  text label in the pill, never color alone.
- Keep the `<title>`, favicon (📒), and token structure stable.

**Deliver:**
1. **Artifact (primary):** publish `views/dashboard.html` with the Artifact
   tool. The persistent URL lives in `views/artifact-url.md` — pass it as
   `url` when republishing so the address never changes; write that file on
   first publish. Give the user the link.
2. **Display integration (optional):** if the environment has a display/
   push integration (e.g. a BotBeam skill) *and* the user asks to "beam" the
   dashboard or habitually works with a display open, also push the HTML
   there. This is strictly optional — never required, never a substitute for
   the Artifact, and skipped entirely when no such integration exists.

## What qualifies for logging

Log: deliverables shipped, decisions made, artifacts produced, external
communications sent (email, Slack post, invoice), a workstream changing state,
open loops created or closed.

Don't log: routine lookups, intermediate work, anything reconstructible from
git history, the repo, or the tool it lives in. When in doubt about a
decision-shaped conversation, log the conclusion in two sentences.

## Artifact policy

**The ledger stores records, never payloads — unless the payload has no home.**

- Artifact landed somewhere real (Drive, Sheets, GitHub, a wiki, a repo) →
  registry row with the link. Never copy content into the ledger.
- Email sent → journal event with recipient, subject, date. The mail system
  is the system of record; don't copy the body.
- Inline-only artifact (drafted email, analysis, recommendation with no
  natural home) → give it a home: if cloud-storage tooling is available
  (e.g. a Google Drive CLI or skill), upload it to a dedicated folder
  (suggested name: `Claude-Memory-Artifacts`, created on first use), then
  register the link. Otherwise save under `artifacts/inline/` and note it
  still needs a home.

## Hygiene

- Journal files are append-only; never rewrite past days.
- Stream files describe *current* state — rewrite them freely.
- Convert relative dates to absolute when writing.
- INDEX.md is the orientation surface: keep it under ~40 lines, one line per
  active stream, ~5 recent-activity entries.

## Setup (once per machine — offer if not wired up)

Two optional pieces of wiring make the ledger ambient:

1. **Global CLAUDE.md pointer** (`~/.claude/CLAUDE.md`): a short section
   telling every session to log significant work via this skill and consult
   the ledger for "what's going on" questions.
2. **SessionStart hook** (`~/.claude/settings.json`): inject INDEX.md into
   every session so Claude wakes up oriented, e.g.
   `cat "<ledger root>/INDEX.md" 2>/dev/null || true` (bash shell).
