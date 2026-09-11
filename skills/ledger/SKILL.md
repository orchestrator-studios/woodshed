---
name: ledger
description: Global cross-session work memory and session board — journal of events, work-product registry, per-stream state files, and hook-driven session tracking in the user's ledger root (default ~/claude-memory). Use when significant work completes (deliverable shipped, decision made, work product produced, email sent), when asked to log work, recall what happened, review open loops, check what's going on, or manage sessions/streams on the board. Verbs — log, recall, review, dash, stream, sessions.
---

# Work ledger

The ledger is the user's global, cross-session memory of *what happened* and
*what was produced*, plus a live board of session activity. It lives in the
**ledger root** — `~/claude-memory` unless the user designates otherwise —
and works from any workspace.

Canonical reference: the **data model** (`views/glossary.html` in the ledger
root, published as an Artifact). Summary of the objects:

| Object | Origin | What it is |
|---|---|---|
| Workspace | Claude Code | directory Claude launches in; has many sessions |
| Session | Claude Code | persistent conversation; ledger annotates it (status, stream, activity) |
| Stream | ledger | thread of work the ledger manages; the file IS the stream |
| Event | ledger | something that happened; append-only journal entry |
| Work product | ledger | something made; record + link, payload lives at its home |

Session lifecycle: **open** (waiting ⇄ processing ⊇ run) → **closed** ⇄
**archived** → **expired**. A *run* is processing toward a mutation. Archived
is a dismissed closed session; any activity un-archives. These states are
maintained automatically by hooks (see Setup) — never edit `sessions/*.json`
by hand except through `scripts/board.py`.

Boundary with Claude Code's auto-memory: facts that stay true → auto-memory;
things that happened or were made → ledger.

## Layout

```
<ledger root>/
  INDEX.md              one-screen orientation; injected at session start
  journal/YYYY-MM-DD.md append-only daily events: "## slug: headline [sid:xxxxxx]"
  streams/<slug>.md     one file per stream; closed → streams/archive/
  artifacts/index.md    work-product registry: | date | stream | product | home |
  sessions/<id>.json    session records (hook-maintained)
  config/board.json     board engine settings (BotBeam device id, TTLs)
  config/stream-paths.json  stream → working directories (attribution map)
  scripts/board.py      board engine (hooks pipe events into it)
  views/                generated views: dashboard.html, glossary.html (data model)
```

If the root doesn't exist, offer to bootstrap: create the layout, empty
registry, first journal entry, then walk Setup below.

## Verbs (`/ledger <verb>`; bare `/ledger` shows INDEX.md and offers them)

### log

Record what just happened.

1. Append to today's `journal/YYYY-MM-DD.md`:
   `## <stream-slug>: <headline> [sid:<your short id>]` plus 1–4 bullets with
   links. Your short id = first 6 chars of your session id (visible in your
   scratchpad directory path). Use slug `meta` for ledger-system work.
2. Work product made? Add a registry row (newest first) linking its home.
3. Update the stream file: current state, open loops, **Next action**,
   Updated date. New stream: create the file, add its working paths to
   `config/stream-paths.json`, add its line to INDEX.md.
4. Update INDEX.md (stream one-liner + Recent activity, ~5 entries, ≤40 lines).

### recall <topic>

Answer inline, in prose — no dashboard for single facts. INDEX → stream file
→ Grep journal/ and artifacts/index.md. Dates, links, current state. If the
ledger has nothing, say so.

### review [week|month]

The management overlay (default: last 7 days). Read active streams + journal
in scope; digest: what moved, what's stalled, open loops, suggested next
actions. Regenerate and republish the deep dashboard (below) and give its
link. Offer to close streams idle for a month.

### dash

Regenerate/republish the deep dashboard without the digest.

### stream <name> [close]

Show or update one stream. `close`: move file to `streams/archive/`, remove
from INDEX.md and `config/stream-paths.json`, log the closure.

### sessions [list | archive <prefix>… | archive --all --keep <prefix>… | unarchive <prefix> | seed [--days N] [--apply [prefix…]]]

Session management via `python <root>/scripts/board.py <args>`:
- `list` — every known session with status (open/closed/archived/expired)
- `archive` / `unarchive` — dismiss/restore board cards (archived is sticky
  only until the session next does something)
- `seed` — survey Claude Code transcripts for sessions the hooks haven't
  seen; dry-run first, then `--apply` the user's chosen prefixes

## The session board (automatic — don't duplicate it)

Hooks pipe every SessionStart / UserPromptSubmit / Stop / SessionEnd /
PostToolUse event into `scripts/board.py`, which maintains `sessions/*.json`
and beams a dark board to the BotBeam "Ledger" display: card per relevant
session (green dot = processing, hollow ring = open·waiting, gray = closed,
⚡ = run), recent events with session chips, recent work products. A
scheduled task (`LedgerBoardSweep`, every 5 min) repaints TTL decay and marks
expired sessions. Your own activity appears on it automatically — never
hand-beam session state.

## Deep dashboard

Overview questions ("what have we been up to?") and `review` get the visual
dashboard — `views/dashboard.html`, template `assets/dashboard-template.html`
(copy on first use; replace every `<!-- DATA:... -->` block: GENERATED,
TILES, STREAMS, ACTIVITY, LOOPS, ARTIFACTS→work products). Publish with the
Artifact tool; the persistent URL is in `views/artifact-url.md` — pass it as
`url` so the address never changes. Keep stream colors in fixed creation
order; staleness fresh ≤3d / aging 4–14d / stale >14d, always labeled.
Optionally also beam to a display integration (e.g. BotBeam) if one exists
and the user asks — optional, never a substitute for the Artifact.

## What qualifies for logging

Log: deliverables shipped, decisions made, work products produced, external
communications sent, a stream changing state, open loops created/closed.
Don't log: routine lookups, intermediate work, anything reconstructible from
git or the tool it lives in. Decision-shaped conversation → log the
conclusion in two sentences.

## Work-product policy

**Records, never payloads — unless the payload has no home.**
- Landed somewhere real (Drive, repo, sheet, published Artifact) → registry
  row with link. Never copy content into the ledger.
- Email sent → journal event (recipient, subject, date); the mail system is
  the record.
- Inline-only product → give it a home: upload via available cloud tooling
  (suggested Drive folder `Claude-Memory-Artifacts`, created on first use)
  and register the link; else `artifacts/inline/` + note it needs a home.

## Hygiene

- Journal is append-only; never rewrite past days. Stream files are current
  state; rewrite freely. Absolute dates always.
- INDEX.md ≤ ~40 lines; it's injected into every session.
- Stream files coordinate sessions by shared disk — last writer wins, so
  keep stream edits short and current.

## Setup (once per machine — offer if not wired)

1. **CLAUDE.md pointer** (`~/.claude/CLAUDE.md`): log significant work via
   this skill; consult the ledger for "what's going on."
2. **Hooks** (`~/.claude/settings.json`): SessionStart (cat INDEX.md, plus
   board.py), UserPromptSubmit, Stop, SessionEnd (board.py), PostToolUse
   matcher `Write|Edit|NotebookEdit|Bash|PowerShell` (board.py) — all
   `"shell": "bash"`, `"async": true`.
3. **Sweep task**: schedule `board.py sweep` every 5 minutes (Windows:
   `schtasks /Create /TN LedgerBoardSweep /SC MINUTE /MO 5 /TR "pythonw
   <root>/scripts/board.py sweep"`).
4. **BotBeam display** (optional): create a "Ledger" display, put its id in
   `config/board.json` as `botbeam_device`. Without it the board silently
   skips beaming; everything else works.
5. **Seed**: `board.py seed` → show the user, `seed --apply <chosen>`.
