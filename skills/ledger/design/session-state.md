# Session state management — working notes

Tracking doc for fixing the board's session lifecycle. Lives with the skill
(`skills/ledger/design/`); update as decisions land and fixes ship.
Companion reference: `docs/ledger/data-model.html` (rev 12).

Status: **diagnosis done, fixes not started** · Updated 2026-09-11

## Essence

Live display states (green dot, bolt, waiting) are derived from timestamps at
render time and work. Stored statuses (`open`, `archived`, `expired`) are
one-way booleans written by whichever trigger fires; nothing reconciles them
with reality, so they drift and latch. Direction of the fix: store facts,
derive every status at read time.

## Pipeline

Trigger → `board.py` updates `sessions/<id>.json` (+ mirror to BotBeam
lockbox) → `beam()` re-renders, pushes to display only on semantic change.
The beam leg is healthy; every defect is on the trigger/store leg.

## BotBeam interface (as of 2026-09-11)

Ledger owns all semantics; BotBeam is passive infra in two roles. No BotBeam
code changes shipped for this — server last committed 7/15; lockboxes since
June. Two mechanisms, unification pending:

- **Display**: board HTML → "Ledger" display (device `pp8wCpVy`) via the
  orchestra skill CLI: `botbeam.py existing --device <id> --type html --body …`
- **Lockboxes** (cross-machine session store, phase 1 — woodshed `3d64a76`):
  direct REST from `board.py` — token/base from `~/.config/orchestra/botbeam.json`;
  `GET /api/devices?kind=lockbox&view=summary` · `POST /api/devices` ·
  `GET/PUT /api/devices/{id}[/content]`; names `ledger:session:<sid[:8]>`,
  body = full session record JSON; name→id cache `config/botbeam-cache.json`.
  Write-through on every event; `merged_sessions()` merges all machines,
  newest `last_active` wins.

## Transitions

| # | Transition | Trigger | Local write | Health |
|---|---|---|---|---|
| 1 | → open | SessionStart hook | create record, `open=true` | ✅ but resume-picker fires it too → ghost record per launch |
| 2 | waiting → processing | UserPromptSubmit hook | `state=active` | ✅ |
| 3 | processing → run | PostToolUse (mutation heuristic) | `last_run` stamp | ✅ |
| 4 | processing → waiting | Stop hook | `state=idle` | ✅ |
| 5 | run/green decay | time only — no event | none (derived) | ❌ depends on sweep; sweep task failing (0x800710E0) |
| 6 | open → closed | SessionEnd hook | `open=false` | ⚠️ crash/kill fires nothing → stuck open |
| 7 | closed → open | SessionStart (resume) | `open=true` | ✅ (side effect: picker ghost, see 1) |
| 8 | closed → archived | CLI `archive` | `archived=true` | ✅ |
| 9 | archived → closed | CLI `unarchive` | `archived=false` | ✅ |
| 10 | archived → open | any hook event | `archived=false` | ⚠️ over-broad: any stray event un-dismisses |
| 11 | closed → expired | sweep: transcript gone | `expired=true` | ❌ sweep unreliable + one transient miss latches forever |
| 12 | expired → open | — | — | ❌ missing entirely; live sessions can be permanently hidden |

## Defect register

- **D1 sticky `expired`, no reverse path** — b1c482f7 (live, hooks firing)
  flagged expired while its transcript exists; board hides it. Likely latched
  during a resume window when the `.jsonl` was briefly absent.
- **D2 sweep task failing** — `LedgerBoardSweep` Last Result 0x800710E0
  ("request refused" — task conditions). Time-driven transitions (5, 11)
  don't run between hook events.
- **D3 launch/picker ghosts** — every `claude` launch/picker leaves a
  one-event record with no transcript (e.g. a90f2470); shows as a closed
  card until hand-archived. No "ever prompted" relevance filter.
- **D4 blanket un-archive** — any event clears `archived`, including
  SessionEnd/noise; design says resume should un-archive, not everything.
- **D5 stream stolen by logging** — every mutating write re-runs
  `match_stream`, file path first; the protocol's own journal write into
  `claude-memory` rebrands sessions `ledger-meta` (17c47e33 invoice session,
  45c76083 perf-monitor session). Ledger-root writes must not attribute.
- **D6 crash-stuck flags** — no SessionEnd on crash → `open=true`,
  `state=active` persist in the record; only the display TTLs paper over it.
- **D7 lossy seed cwd decode** — `C--code-lexintel---plugin` →
  `C:\code\lexintel\\\plugin`; breaks labels and stream matching for seeded
  records. Read cwd from the transcript's first line instead.

## Decisions

- **DECIDED 2026-09-12 — rev 18: ALL session statuses are stored, derivation
  of lifecycle state is gone.** Supersedes "facts-only store" below. `status`
  (active|dormant|archived|expired) is a stored column like `turn_state`,
  written only by the signal/call that causes each transition (any signal but
  SessionEnd → active; SessionEnd/unarchive → dormant; archive → archived;
  sweep handler → expired at the miss threshold). Nothing infers a status from
  timestamps. Crash repair (stale active rows) is DEFERRED — a later sweep
  mechanism, same pattern as the turn_state cleanup; accepted known gap until
  then: a crashed session shows active. Also ruled: board view splits
  Active/Inactive; active sessions are cards in a stable grid (first_seen
  asc, no reordering while active), inactive by recency.
- **DECIDED 2026-09-11 — BotBeam becomes the ledger service.** The entire
  store centralizes behind a `/ledger` API on BotBeam; `~/claude-memory` is
  retired as system of record; Claude/hooks/displays become clients; all
  schemas and state transitions enforced server-side in code. Spec: [The
  Ledger Book](../../../docs/ledger/ledger-reference.html) (rev 1, published
  at the data-model artifact URL). Supersedes the local-folder fixes below —
  D1–D7 get resolved structurally by the service rather than patched in
  board.py.
- **DECIDED — facts-only store**: keep `last_event_at`, `ended_at`,
  `archived_at`, `transcript_missing_since`, `ever_prompted`; derive
  open/closed/archived/expired at read time (now server-side).
- **DECIDED — expiry rule**: N consecutive sweep-report misses AND no recent
  events; self-heals on any new fact.
- **DECIDED — ghost rule**: sessions never prompted aren't board-relevant.
- (pending) Offline behavior when the service is unreachable: hook spool vs
  accepted gaps.
- (pending) Journal migration: import v1 markdown as structured events vs
  archive as-is.

## Worklist (reframed 2026-09-11 around the service architecture)

Migration plan lives in The Ledger Book → Status & migration. Summary:

- [ ] 1. Ledger API in BotBeam: store + `/ledger` endpoints + session state
      machine (facts → derived status)
- [ ] 2. Hooks → `POST /ledger/sessions/{id}/events`; sweep reporter →
      `/sweep-report`; retire board.py's local store (kills D1–D4, D6)
- [ ] 3. `POST /ledger/log` atomic transaction; rewrite SKILL.md verbs as
      API calls (kills drift; D5 via server-side attribution)
- [ ] 4. Service renders board + index; import `~/claude-memory`; retire
      the folder (D7 moot — no more seeding from folder names)

Interim (only if v1 pain blocks daily use before step 2 lands):
- [ ] clear the false `expired` on the live session; drop test/ghost records
