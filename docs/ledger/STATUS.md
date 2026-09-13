# Ledger — where we are, what we're driving towards

Updated 2026-09-13 (rev 21 shipped end to end). Canonical design:
`ledger-reference.html` (the Book, **rev 21**).

## Rev 21 — runs and deliverables (SHIPPED, live in prod at v1.9.0)

The whole previous notion of `run` is deleted: it was a ⚡ computed from a
decaying `last_run_at` inside a 120s window, refreshed by `PostToolUse` for a
hard-coded mutating-tool list. It inferred a state from a clock (against
invariant 2) and was inverted for the case it existed to show — `PostToolUse`
fires on tool *completion*, so a ten-minute build went dark while running and
lit the bolt after it finished.

Replaced by two record-plane objects:

- **Deliverable** — a thing that was made; a name plus exactly one home. It
  **persists and is advanced** (the Book is one deliverable at revs 18→21, not
  four events). Mutable by design; `state` is rewritten by each closing run.
  Renamed from "work product" and un-deferred. Deliberately **not** "artifact"
  — that word is taken three times over (claude.ai Artifacts, the orchestra
  `artifacts` skill, the Artifact Tracker).
- **Run** — a bounded stretch of work against exactly one deliverable,
  **declared at both ends**. Two calls (open with intent, close with outcome)
  because the knowledge is asymmetric: Claude knows in advance it is starting
  bounded work on a known thing, but recognises a decision or a send only as it
  happens. Events therefore stay one call. `abandoned` is a first-class ending.
  **No timeout** — a timer would reintroduce the inference being deleted.

Settled along the way: a run declares **intent, not scope**. Left deliberately
open: the **deliverable ↔ event** linkage.

### Review round (botbeam, 2026-09-13) — all nine points adopted

It caught a real defect: `Deliverable.status` shipped with **no writer** — a
stored status nothing could transition, the exact failure invariant 2 exists to
prevent. Fixed as `POST /ledger/deliverables/{id}/retire · /unretire`, and
retiring is **the user's call, never Claude's**, like archiving a session.

Also settled: the closer of a run **need not be the opener** (that is the manual
cleanup path for crash-leaked runs); one open run per session with a written
recovery recipe; `create_deliverable.stream_id` must already exist (404, no
nested create); `state` is required on close to force *consideration*, not
change; `open_run` carries both `deliverable_id` and `deliverable_name`; and
**`PostToolUse` is kept** as a pure heartbeat — it holds `last_event_at` fresh
through long turns and the deferred crash repair will need an in-turn signal.

**ring + ⚡ is now legal and common.** The old `run` was a sub-state of
`processing`, so the combination was impossible by construction. A run spans
whatever turns it takes, so "waiting on you, still mid-run" is a real state.
The two glyphs are orthogonal channels: the circle says whose move it is, the
bolt says whether a deliverable is being worked.

### BotBeam side of rev 21 — DONE (v1.9.0, commits d7af555 + 588cbe9)

`POST/GET /ledger/runs` + `/close`, `/ledger/deliverables` +
`/retire` · `/unretire`. Migration 006 run on prod (two new tables,
`last_run_at` dropped). 116/116 tests across four suites. The bolt is now a
declared open run (`ended_at IS NULL`); circle and bolt render independently.
Verified live with a real run (`run_5e1caad8f6384f60`).

### Woodshed side of rev 21 — DONE (commit 92d5808, pushed)

- `session_event.py`: tool payload dropped, debounce collapsed to a plain
  heartbeat, docstring rewritten. Smoke-tested live.
- `SKILL.md`: runs/deliverables section is live, `run` added to the verb list,
  frontmatter description updated. Synced to the global skill copy
  (`~/.claude/skills/ledger/SKILL.md`, byte-identical).

### Dead weight removed 2026-09-13

`board.py` (v1 board engine — read transcripts, sniffed tools to guess a run,
rendered its own HTML), `phase-1-sessions.html` (plan, complete),
`design/session-state.md` (argued for derive-at-read, which rev 18 reversed),
`assets/dashboard-template.html` (unreferenced), `emit_test_event.py` (harness
for a deleted script), the duplicate + `sweep_report.py` in the global skill
copy, and the `LedgerBoardSweep` scheduled task. `docs/ledger/README.md`
rewritten — it was a changelog of superseded revs still claiming the
architecture was unimplemented.

## The goal

Sessions, events, runs and deliverables fully operational end to end — hooks,
skill, and the BotBeam API — with the four-section dashboard. **Reached.** What
remains is the test round: exercise the plane for real, then decide it's done.

## Live in prod now (BotBeam v1.9.0 — verified via /health 2026-09-13)

- **Sessions**: hooks post signals to `/ledger/sessions/{id}/signals`. Stored
  status, three states (active | dormant | archived). Board shows Active as a
  stable card grid, Inactive by recency. Labels are **first-write-wins** — a
  card no longer renames itself when the shell `cd`s to a subdirectory
  (botbeam 47fd5d2; this was open decision 3, now closed).
- **Events + streams**: `POST /ledger/events` (atomic: event + emitter liveness
  + stream create/update), `GET /ledger/events`, stream PUT/close/list,
  `/ledger/search`, `/ledger/index`, `/ledger/board`.
- **Runs + deliverables**: `POST/GET /ledger/runs`, `POST /ledger/runs/{id}/close`,
  `GET /ledger/deliverables`, `POST /ledger/deliverables/{id}/retire · /unretire`.
- **Four-section dashboard** (v1.8.1) with the stream visual language on top
  (v1.8.2): Active grid · Inactive (collapsible, persisted) · Streams | Events
  side by side. Each stream owns a stable hashed colour on its card edge, event
  pills and session dots; hover an event to light its stream and session, click
  a stream to filter the feed.
- `LEDGER_ADMIN_RESET` is enabled in prod, to be removed after the test round.

## The board can act — invariant 11, 2026-09-13 (designed, NOT built)

Closing a stream logs an event, and an event demanded a `session_id`. A button
on the dashboard is a web page with no session, so the board could not close a
stream at all. The blocker is invariant 9 meeting its first non-session actor.

**An emitter is a place a user acts from**, and there are two: a Claude session
and the BotBeam interface. Both emit; `emitter_kind` says which, explicitly.

Data level: `ledger_events` gains `emitter_kind` (`'session' | 'board'`, NOT
NULL), `session_id` becomes nullable, and the migration backfills every
existing row to `'session'`. A real constraint, not a convention — `session`
demands a `session_id` that resolves, `board` demands null; both or neither is
a 400. Requests carry `session_id` **or** `emitter: "board"`, never inferred
from the caller's credential, since the browser and every agent authenticate as
the same user. Reads return `emitter_kind` so the board picks its chip from a
field rather than from a null. Board-emitted events skip the liveness write and
only that — the board is a surface, not a running thing.

Rejected: nullable `session_id` alone as the signal. It encodes the newest
concept in the model as a missing value, where a null later means either "the
board did it" or "something broke."

Service side is BotBeam's. Close/reopen buttons are mine, once it deploys — and
the same emitter unblocks deliverable retire/unretire from the board.

## The board is closed under reference — invariant 10, 2026-09-13

Closing a stream must take its deliverables and its feed entries out of the
view with it. `GET /ledger/board` and `GET /ledger/index` filter deliverables
and events by their stream's state; rows are untouched and stay retrievable
through `/ledger/events`, `/ledger/deliverables` and `/ledger/search`.

Found by closing `meta` as a board test: the card vanished and its 3
deliverables and 13 feed events stayed, each with a pill naming a stream the
board no longer showed — and once the title stopped resolving, the pills fell
back to the raw slug. The `meta` carve-out was one instance of this; the rule
makes the whole class impossible, and the frontend needs no change, because
nothing arrives whose stream did not.

Service side is BotBeam's, in progress. `meta` is closed in prod meanwhile, so
the board shows the unfixed state until it ships.

## There is no special stream

`meta` is an ordinary stream. No stream is auto-created, unclosable, or
excluded from attribution, the board, or the index. Work on the ledger itself
is a stream like any other, and if one loud stream crowds the index the answer
is ranking or a user-controlled collapse — never a slug the code knows by name.

Woodshed carries this in `SKILL.md` and the Book. The service still has the
built-in-stream machinery to remove (`META_STREAM`, `_ensure_meta`, the
never-closes guard, the attribution and index exclusions) — BotBeam's, in
progress. The board no longer special-cases any slug (botbeam `437ec8a`).

## Built, NOT deployed — waiting on Cliff

- BotBeam v1.10.2 (`0c298b7` + `d46009b`) — superseded by `437ec8a`; do not
  deploy it as-is.

## Open decisions for Cliff

1. **Is the test round done?** If so, `LEDGER_ADMIN_RESET` comes out of prod.

## Known gaps (deferred, by choice)

- **Deliverable ↔ event linkage** is deliberately unsettled. Do not assume one.
- **Whether a closing run also writes an event** is deliberately unsettled.
- **Crashed sessions** keep their last status and will leak an open run until a
  repair mechanism is added. Manual recipe is in the skill: any session may
  close any run, so a leaked run is closed as `abandoned` on resume.

## Woodshed side — done, nothing pending

Skill rewritten and synced; `session_event.py` on `/signals` and verified live;
`orientation.py` wired into SessionStart, fetching `/ledger/index`;
`sweep_report.py` deleted; global CLAUDE.md updated. The `LedgerBoardSweep`
scheduled task was recorded as deleted but was still **enabled and running**
`~/claude-memory/scripts/board.py sweep` against the abandoned v1 store —
actually deleted 2026-09-13 and verified gone. **No exposure to the `/ledger`
tables**: that sweep wrote only v1 targets (local files and the old
`ledger:session:*` lockboxes), never sessions/events/streams/runs, and every
write in those tables is accounted for.

### How the woodshed side reaches other sessions

Two different distribution paths, and only one of them is automatic:

- **Hook scripts run from the repo.** `~/.claude/settings.json` points all five
  hooks at `C:/code/woodshed/skills/ledger/scripts/session_event.py` (and
  `orientation.py` on SessionStart) by absolute path. Editing those files
  changes every session's behaviour on the next hook fire — no copy step.
- **`SKILL.md` is a copy that must be synced.** Claude loads the skill from
  `~/.claude/skills/ledger/SKILL.md`; the repo file is the source. After
  editing the repo copy, copy it to the global path or the two drift.
  Currently byte-identical (sha256 `fe005677…`, 14669 bytes).

The global skill directory holds **only** `SKILL.md` — the duplicate `scripts/`
was deleted in the rev-21 cleanup precisely so there is one live copy of the
code and one of the prose.

## The hold — LIFTED 2026-09-13

Cliff: "There's no hold now. We are testing."

## How the design settled (so it isn't relitigated)

- Statuses are **stored and declared** by the signal or call that causes each
  transition. Nothing is inferred from timestamps.
- **`expired` and the whole sweep are retired.** Transcript existence is not a
  session state; Claude Code deletes transcripts on its own 30-day clock.
- **Two feeds**: hooks (sessions, automatic) and the skill (events, runs,
  deliverables — judgment). Hooks are NOT part of the skill.
- **Signals ≠ events**: hooks post signals (telemetry, not stored as rows);
  Claude posts events (record, immutable).
- Emitting an event writes the emitting session's liveness — invariant 9, the
  only place the two planes touch.
- Streams are born inside the event that needs them (`create_stream` rides in
  `POST /ledger/events`); deliverables are born inside the run that needs them
  (`create_deliverable` rides in `POST /ledger/runs`). Both **close only when
  Cliff says so**.
- `~/claude-memory` is abandoned, not migrated.
