# Ledger — where we are, what we're driving towards

Updated 2026-09-13 (post-deploy). Canonical design: `ledger-reference.html`
(the Book, rev 20).

## The goal

Sessions and events fully operational end to end — hooks, skill, and the
BotBeam API — with the new four-section dashboard. Then run a test round.

## Live in prod now (BotBeam v1.8.1)

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
`sweep_report.py` and the scheduled task deleted; global CLAUDE.md updated.
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
