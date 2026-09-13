# Ledger — where we are, what we're driving towards

Updated 2026-09-13. Canonical design: `ledger-reference.html` (the Book,
**rev 22**). Live at **BotBeam v2.0.1** — sessions, events, streams, runs and
deliverables, with the board operable from the interface.

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

## PICK UP HERE — browsing what's been taken off the board

Next piece of work, BotBeam session screen. The board can now close a stream and
retire a deliverable (v2.0.1), but there is no way to *find* either afterwards:
the undo slot covers only the last act in the current page load, and once the
page reloads a closed stream is unreachable from the interface. Same hole has
existed quietly for sessions — `unarchiveSession` has sat in the API client with
nothing calling it, because archived sessions have no list either.

Cover all three:

- `GET /ledger/streams?status=closed`, `GET /ledger/deliverables?status=retired`,
  `GET /ledger/sessions?status=archived` — the data is already served, no
  service work needed.
- Render as collapsible sections matching the **Inactive sessions** pattern
  (collapse state persisted in `localStorage`, by the rev-20 ruling).
- Restore controls call `reopen` / `unretire` / `unarchive` with
  `{"actor": "board"}`, the same shape the × buttons use.
- Frontend only. `SessionsView.tsx` + `app.css` + `botbeamApi.ts`.

Invariant 10 is why this matters rather than being a nicety: closing takes the
stream's deliverables and feed entries off the board with it, so a single click
removes a lot from view with no path back through the interface.

## Every write names its actor — invariant 11, 2026-09-13 (designed)

The dashboard needs close/reopen buttons for streams and retire/unretire for
deliverables. Closing logs an event, and an event demanded a `session_id` the
browser does not have. The board is a REST client of the same app — the archive
× already calls `POST /ledger/sessions/{id}/archive` same-origin with the user's
login JWT, and there is no internal route; it works only because archiving logs
no event. The credential cannot carry the answer either: `create_access_token`
builds one payload for browser and agent alike.

**One field, `actor`, a prefixed identifier.** `session:<uuid>` or `board`.
The type is read by parsing the prefix — not a second column, not a nullable
field standing in for a type, not inferred from the credential. A type with one
instance is its own identity, which is why `board` carries no id. New kinds of
actor are new values, not new schema.

- Storage: `actor VARCHAR(64) NOT NULL`, replacing `session_id`. Migration
  rewrites existing rows to `'session:' || session_id`. No nullable column, no
  CHECK, no enum, no backfill gap.
- Liveness (invariant 9) fires when the actor resolves to a session, because
  sessions have liveness. Nothing else about the write differs.
- Uniform across every write that records who acted: events, stream
  close/reopen, runs, and deliverable retire/unretire.
- Query filters keep bare values — `?session_id=<uuid>` — because the parameter
  name has already declared the type.

**No legacy path.** The API takes `actor`; running sessions holding the old
skill copy fail on their next log until restarted. That is a restart, not debt.
`extra="forbid"` rejects `session_id` everywhere, tested.

**The field is uniform; the permissions are not.** `board` may close a stream,
reopen one, retire a deliverable, and close a leaked run — dashboard acts. It
may **not open a run** (422): the board does not do the work, the run row stores
the session, and the ⚡ is a join on sessions.

**Built, not deployed.** BotBeam `b839962` + `e125e38`, 144/144, cut as
**v2.0.0** — the wire contract breaks, so a major bump. Migration 007 rewrites
the 16 event rows to `'session:' || session_id` and drops the column; the FK is
`ledger_events_ibfk_2`, not the `_ibfk_1` default. Migration and deploy must
land back-to-back with a brief record-plane window, and the prod DB write is
**waiting on Cliff's word in BotBeam's session.**

Superseded before it shipped: an earlier cut of this had two mutually exclusive
fields and an `emitter_kind` enum with a CHECK constraint. BotBeam built it
(`4fdfca9` + `e90258c`, never deployed, prod untouched) and it is replaced by
the above.

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

Shipped in BotBeam v1.11.1 and verified in prod. `POST /ledger/streams/{id}/reopen`
followed in v1.12.0 — closing is reversible, and reopening brings the stream's
deliverables and events back with it.

## There is no special stream

`meta` is an ordinary stream. No stream is auto-created, unclosable, or
excluded from attribution, the board, or the index. Work on the ledger itself
is a stream like any other, and if one loud stream crowds the index the answer
is ranking or a user-controlled collapse — never a slug the code knows by name.

Woodshed carries this in `SKILL.md` and the Book; the service dropped the
built-in-stream machinery in v1.11.0 and the board special-cases no slug
(botbeam `437ec8a`).

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
