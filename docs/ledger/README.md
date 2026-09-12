# Ledger design material

Versioned home for the ledger's design documents. The skill lives in
`skills/ledger/`; this directory holds the reference material behind it.

## The Ledger Book (the one reference)

- `ledger-reference.html` — **rev 19, 2026-09-12** — the unified reference for
  the target architecture: BotBeam as the centralized ledger service and
  system of record. Objects + lifecycles (from the Data Model), flows + APIs
  (from the System Map), plus the `/ledger` API surface, client contracts,
  invariants, and migration plan. Left-rail nav, dark mode, one panel per item.
  - rev 11: one-renderer dashboard (`GET /ledger/views/dashboard`, Claude as
    courier); wire Representations + full response/error specs per endpoint;
    skill rewritten as standing vs answering duties (inference-first); stream
    attribution made a derived rule; `meta` a built-in stream; `workspace_id`
    naming; hooks classify nothing. Lifecycle: active/dormant model — dormant
    covers idle, crashed, and exited alike (no signal witnesses the
    difference); the user clears dormant sessions by archiving.
  - rev 12: clients section restructured — "How it hangs together" narrative
    (two writers by kind of knowledge, coverage/backstop table); displays
    moved out of Clients into their own Projections group. The deep dashboard
    is REMOVED from the design entirely: the only view endpoints are
    `GET /ledger/index` (orientation markdown) and `GET /ledger/board`
    (typed data structure the BotBeam board view renders — the service never
    serves rendered HTML).
  - rev 15: Hooks panel now points to the companion agent-messaging reference
    (see below); no design change.
  - rev 16: added `last_stop_at` as an eighth stored fact (Session panel, cheat
    sheet, representation) — waiting-vs-processing compares last prompt to last
    Stop, so the Stop time must be stored; surfaced by the BotBeam v1.5.0 build.
    Header now reads "sessions plane live (BotBeam v1.5.0)".
  - rev 17 (Cliff's ruling): `turn_state` (waiting|processing) is a STORED
    status — UserPromptSubmit sets processing, Stop/SessionEnd set waiting;
    never inferred from timestamps. Crashed-session cleanup is a separate
    mechanism (sweep repairs stale processing on dormant rows). Invariant 2
    carries the explicit exception. Lifecycle panel now has an exact
    fields-written-per-transition table (universal writes stated once);
    `sweep_miss_count` added to the fact list. Spec sent to the botbeam
    agent (implement + test + commit, deploy held for Cliff).
  - rev 19 also adds the **How it runs** panel (Orientation, second position) —
    the operational picture the Book was missing: the three independent moving
    parts (hooks · sweep · skill) with what runs each and what breaks if it
    stops, a moment-by-moment walkthrough of one session from launch to exit
    showing every write and what appears on the board, and a plain statement
    that **hooks are NOT part of the skill** (separate OS process, wired in
    settings.json, fire without Claude). "Clients — the writers" renamed to
    "the feeds"; two *kinds of knowledge* (witnessed/judged), three feeds.
  - rev 19 (Cliff's rulings — the record plane): **API renamed** —
    `POST /ledger/log` → `POST /ledger/events` (one resource; POST writes, GET
    reads, merged into one panel), and `POST /ledger/sessions/{id}/events` →
    `.../signals` (hook signals are not Events; the collision is over). New
    Conventions row fixes the vocabulary: telemetry says *signal*, record says
    *event*. **Invariant 9 added** — emitting an event writes the emitting
    session in the same transaction (`last_event_at`, `status="active"`,
    un-archive); `turn_state` stays hook-only; the `/events` Effects table
    gains a `sessions` row. **New panel: Event emission rules** — service-
    enforced shape vs skill-enforced judgment (invariant 8's seam). **Work
    products deferred** — specified but not implemented; `product` block
    rejected 422, no products column on the board. **`~/claude-memory`
    abandoned outright** — no import, no reads, no writes; `GET /ledger/index`
    therefore moves into this phase or session-start orientation has no source.
    Board: events feed renders below the session sections. Attribution left
    computed (unchanged) by Cliff's call.
  - rev 18 (Cliff's ruling): session `status` (active|dormant|archived|expired)
    is a STORED status, like `turn_state` — derivation of lifecycle state is
    GONE. Every signal but SessionEnd writes active; SessionEnd and unarchive
    write dormant; archive writes archived; the sweep handler writes expired.
    Crash repair (stale active rows) is explicitly DEFERRED to the sweep — not
    handled now, by decision. Invariant 2 rewritten ("statuses are declared,
    never inferred"); the only computed fields left are run bolt, relevance,
    staleness, attribution. Board layout ruling added: Active / Inactive
    sections; active sessions are cards in a stable grid (first_seen asc,
    never reorder while active), inactive listed by recency. Implementation
    sent to the botbeam agent.
  - rev 13–14: Session cheat sheet panel (Orientation group), written from
    the board backwards: Rule 1 what's listed / Rule 2 glyphs / Rule 3 the two
    windows (silence, run), then a cornering-the-transitions table (every
    visible board change → one cause), facts last as footing.
- The HTML file here is the canonical copy and the deliverable — revisions are
  edits to this file, full stop. A hosted claude.ai copy exists at
  …/8ceb7d22-c3df-4a6b-a5c1-e338f9702d19 (pushed to rev 19 on request
  2026-09-12; frozen at rev 11 before that). **Republish only when Cliff asks
  for a link** — it is a reading convenience for when he's away from the
  machine, never a second source, and it is expected to lag this file. General
  doctrine: the orchestra `artifacts` skill.
- Status: **target architecture — decided, not yet implemented.** The v1
  local-folder system (`~/claude-memory` + `board.py`) remains live until the
  migration steps in the book's "Status & migration" panel land.

Superseded (deleted from this folder at rev 1):
- `data-model.html` (rev 12) — objects/lifecycles, now merged into the book.
  A deployed v1 copy may linger at `~/claude-memory/views/glossary.html`.
- `system-map.html` (rev 4) — flows/APIs, now merged into the book. Its old
  artifact (…/b1f3dfc8-e2ba-491f-b747-0f4bfbee66dc) is superseded by the URL above.

When revising: bump the rev in the header + footer and update here. No
artifact republish.

## Companion references

- `agent-messaging-reference.html` — **rev 3, 2026-09-12** — Claude Code
  inter-agent messaging: inbox socket, SendMessage/ListAgents,
  `crossSessionInbound`, channels, agent teams, hooks-as-transmitters, and a
  queue-bridge build guide. Absorbed from an external cheat sheet (rev 1) and
  fact-checked against the official docs + live tool schemas 2026-09-12; open
  items carry `verify` badges. Platform facts that drift with CLI versions —
  revved independently of the Book. Directly relevant to Phase 1 (W1 hook
  transmitter) and any future agent-to-agent tasking. rev 3 fixed the
  original's tab CSS bug (`.with-rail` panels always visible → "two pages
  in one"); the copy in Downloads still has it.

## Phase plans

- `phase-1-sessions.html` — Phase 1 work plan (2026-09-12): sessions on the
  BotBeam board. Two tabs — BotBeam changes (B1–B6: session store, derivation
  service, /ledger router, board view, admin reset, additive deploy) and
  Woodshed changes (W1–W5: hook transmitter with PostToolUse debounce, hook
  rewiring, sweep reporter, board.py retirement, sessions verb → API) — plus
  the T0–T9 test protocol (cheat-sheet transitions as acceptance checklist).

## Working notes

- `../../skills/ledger/design/session-state.md` — live tracking doc for the
  session-state rework (defect register, decisions, worklist).
