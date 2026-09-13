# Ledger — where we are, what we're driving towards

Updated 2026-09-13 (rev 21 cut). Canonical design: `ledger-reference.html`
(the Book, **rev 21**).

## Rev 21 — runs and deliverables (specified, NOT built)

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

### Woodshed side of rev 21 — DONE

- `session_event.py`: tool payload dropped, debounce collapsed to a plain
  heartbeat, docstring rewritten. Smoke-tested live.
- `SKILL.md`: runs/deliverables section is live, `run` added to the verb list,
  frontmatter description updated. Synced to the global skill copy.

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

Sessions and events fully operational end to end — hooks, skill, and the
BotBeam API — with the new four-section dashboard. Then run a test round.

## Live in prod now (BotBeam v1.8.2 — verified via /health 2026-09-13)

- **Sessions**: hooks post signals to `/ledger/sessions/{id}/signals`. Stored
  status, three states (active | dormant | archived). Board shows Active as a
  stable card grid, Inactive by recency.
- **Events + streams**: `POST /ledger/events` (atomic: event + emitter liveness
  + stream create/update), `GET /ledger/events`, stream PUT/close/list,
  `/ledger/search`, `/ledger/index`, `/ledger/board`.
- **Events store holds exactly one row** (`ev_b115c835`, orchestra v0.2.6 cut,
  2026-09-13T00:38Z) — the baseline was zero after two junk events were
  surgically deleted; the orchestra session has since logged one real event.
- **Streams: one row**, `orchestra`, born inside that event.
- **Four-section dashboard** (commit edbf8d3, shipped in v1.8.1 2026-09-13):
  Active grid · Inactive (collapsible, persisted) · Streams | Events side by
  side (5:7, stacks below 760px, feed capped 420px). Stream cards: title, state,
  next action, staleness colour, open-loop count. Open tabs auto-reload on the
  version change. Prod is now fully at Book rev 20 + the layout ruling.
- `LEDGER_ADMIN_RESET` is enabled in prod, to be removed after the test round.

## Built, NOT deployed — waiting on Cliff

- Nothing pending.

## Open decisions for Cliff

1. **Create the remaining two streams?** `nuc-perf-slowdown`, `orch-studio-site`,
   with current state carried over by hand. `orchestra` already exists (born
   inside the v0.2.6 event). Without the other two the Streams panel stays
   thin for the test round.
2. Two render details BotBeam flagged: the open-loop count pill carries the
   full list in a hover tooltip; `meta` gets no stream card. Both look right.
3. **Label first-write-wins** (parked): a session's label currently changes
   mid-life when the shell `cd`s to a subdirectory. Workspace should refresh,
   label should not. One-line change, post-round.

## Woodshed side — done, nothing pending

Skill rewritten and synced; `session_event.py` on `/signals` and verified live;
`orientation.py` wired into SessionStart, fetching `/ledger/index`;
`sweep_report.py` deleted; global CLAUDE.md updated. The `LedgerBoardSweep`
scheduled task was recorded as deleted but was still **enabled and running**
`~/claude-memory/scripts/board.py sweep` against the abandoned v1 store —
actually deleted 2026-09-13 and verified gone.
Committed as `c41af15`; Book rev 20 edits since then are uncommitted.

## The hold — LIFTED 2026-09-13

Cliff: "There's no hold now. We are testing." The held backlog is logged as
`ev_00f17d25` on `meta` — Book revs 18–20, the skill rewrite, commit c41af15,
the hooks move. The board build/deploy is BotBeam's to log from its own
session; the emitting session should be the one that did the work.

Ledger contents now: `orchestra` and `meta` streams; events `ev_b115c835`
(orchestra v0.2.6) and `ev_00f17d25` (woodshed record plane), plus BotBeam's
deploy event once it lands.

## How the design settled (so it isn't relitigated)

- Statuses are **stored and declared** by the signal or call that causes each
  transition. Nothing is inferred from timestamps.
- **`expired` and the whole sweep are retired.** Transcript existence is not a
  session state; Claude Code deletes transcripts on its own 30-day clock.
- **Two feeds**: hooks (sessions, automatic) and the skill (events, judgment).
  Hooks are NOT part of the skill.
- **Signals ≠ events**: hooks post signals (telemetry, not stored as rows);
  Claude posts events (record, immutable).
- Emitting an event writes the emitting session's liveness — invariant 9, the
  only place the two planes touch.
- Streams are born inside the event that needs them (`create_stream` rides in
  `POST /ledger/events`) and **close only when Cliff says so**.
- Work products are deferred. `~/claude-memory` is abandoned, not migrated.
