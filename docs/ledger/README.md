# Ledger design material

The ledger's reference documents. The skill lives in `skills/ledger/`; the
system of record is the BotBeam ledger service (`/ledger` API).

## The Ledger Book — the one reference

`ledger-reference.html` — the unified reference: what the system does, its
objects and their lifecycles, the full `/ledger` API surface, client contracts,
and the invariants. Every schema and state transition in it is enforced in
service code.

**This HTML file is canonical and is itself the deliverable.** A revision is an
edit to this file, full stop. Bump the rev in the header when you change it.

A hosted claude.ai copy exists at `…/8ceb7d22-c3df-4a6b-a5c1-e338f9702d19`.
**Republish only when Cliff asks for a link** — it is a reading convenience for
when he is away from the machine, never a second source, and it is expected to
lag this file. General doctrine: the orchestra `artifacts` skill.

## Live state

`STATUS.md` — where the work actually stands: what is deployed, what is
specified but unbuilt, and the open decisions. **Read it before doing anything
ledger-related.** The Book is the design; STATUS.md is the situation.

## Companion reference

`agent-messaging-reference.html` — Claude Code inter-agent messaging: inbox
socket, SendMessage/ListAgents, `crossSessionInbound`, channels, agent teams,
hooks-as-transmitters, and a queue-bridge build guide. Platform facts that
drift with CLI versions, so it is revved independently of the Book.

## Scripts (in `skills/ledger/scripts/`)

| Script | Role |
|---|---|
| `session_event.py` | the hook transmitter — posts lifecycle signals to `/ledger/sessions/{id}/signals` |
| `orientation.py` | SessionStart fetch of `GET /ledger/index`, injected as context |

Both are wired in `~/.claude/settings.json` and run as separate OS processes.
**Hooks are not part of the skill** — they fire whether or not it was ever
loaded.

## Superseded and deleted

Everything below was removed once the service became the system of record.
Listed so nobody resurrects it:

- `board.py` — the v1 local board engine. Read transcripts directly, sniffed
  tool names to guess a "run", and rendered its own HTML. The service owns the
  board now and the skill never renders one.
- `phase-1-sessions.html` — the Phase 1 work plan. Complete; the Book and
  STATUS.md carry everything still true.
- `design/session-state.md` — working notes arguing for deriving status at read
  time. Rev 18 ruled the opposite way: statuses are stored and declared.
- `assets/dashboard-template.html`, `scripts/emit_test_event.py`,
  `scripts/sweep_report.py` — an unreferenced canned dashboard, a harness for a
  script that no longer exists, and the retired sweep.
- `data-model.html`, `system-map.html` — merged into the Book.
- `~/claude-memory` — the v1 local-folder store. Abandoned outright, not
  migrated.
