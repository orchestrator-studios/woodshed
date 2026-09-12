---
name: ledger
description: Global cross-session work memory and session board — a live database of sessions (what's running) and events (what happened), plus the streams of work they belong to, held by the BotBeam ledger service (/ledger API). Use when significant work completes (deliverable shipped, decision made, external communication sent), when asked to log work, recall what happened, review open loops, check what's going on, or manage sessions/streams on the board. Verbs — log, recall, review, stream, sessions.
---

# Work ledger

A **live database of sessions and events**, held by the BotBeam ledger service
and shared across every machine and workspace. Sessions answer *what is running
right now*; events answer *what happened*. It works from any workspace.

The service is the only system of record. Everything reaches it through the
`/ledger` API — no local files, ever.

Canonical reference: **The Ledger Book**
(`C:\code\woodshed\docs\ledger\ledger-reference.html`) — its "How it runs"
panel is the operational picture behind this skill.

## Your place in the system

Three independent feeds keep the database current. They never talk to each
other; each talks only to the service, which is the only writer.

| Feed | Runs | Maintains | If it stops |
|---|---|---|---|
| **Hooks** | automatically, on 5 CC lifecycle moments | session rows | the board goes stale |
| **Sweep** | every 5 min, per machine | transcript presence → expiry | dead cards linger |
| **You (this skill)** | when your work produces an outcome | **events and streams** | history is lost, unrecoverably |

**Hooks are not part of this skill.** They are wired in
`~/.claude/settings.json`, run `scripts/session_event.py` in a separate OS
process, and fire whether or not this skill was ever loaded. They share a
folder with this skill and nothing else. Consequence: **session telemetry is
not your job and never needs your help** — sessions appear, change state, and
close on the board with no action from you.

**Events are entirely your job.** No sensor can see that a diff was a
deliverable or that a conversation settled a decision. You are the only feed
that can forget, which is why logging is a standing duty rather than a feature
someone invokes.

## Objects

| Object | Origin | What it is |
|---|---|---|
| Workspace | Claude Code | directory Claude launches in; has many sessions |
| Session | Claude Code | persistent conversation; the service annotates it (status, stream, activity) |
| Stream | ledger | thread of work under management — state, next action, open loops |
| Event | ledger | something that happened; append-only, immutable |

**Two planes, two nouns, never interchanged.** Hooks post **signals**
(telemetry — mechanical, high-volume, not stored as records; they update
columns on the session row). You post **events** (the record — judged, rare,
stored forever, immutable).

Session lifecycle: **active** (waiting ⇄ processing ⊇ run) → **dormant** ⇄
**archived** → **expired**. Statuses are **stored, declared** by the signal or
call that causes each transition — nothing is inferred from timestamps. A
crashed session keeps its last status until a sweep repair lands (deferred,
known gap).

Boundary with Claude Code's auto-memory: facts that stay true → auto-memory;
things that happened → ledger.

## Credentials

Base URL and bearer token from `~/.config/orchestra/botbeam.json`. Every call
carries `Authorization: Bearer <token>`. The service stamps all timestamps —
never send one.

## Verbs (`/ledger <verb>`; bare `/ledger` shows orientation and offers them)

### log

**A standing duty, not a request.** Log the moment your work produces an
outcome — never waiting to be asked, never asking permission first.

One call: `POST {base}/ledger/events`

```json
{
  "stream_id": "orchestra",
  "headline": "v0.2.5 cut and deployed",
  "body": ["commit 1ee891f pushed", "marketplace refreshed, plugin updated"],
  "session_id": "<this session's full uuid>",
  "stream_update": { "state": "...", "next_action": "...", "open_loops": ["..."] },
  "create_stream": { "title": "...", "working_paths": ["C:\\code\\..."] }
}
```

- `stream_update` **rides in the same call** whenever the outcome changed the
  thread's state or next action — never a second call.
- `create_stream` only when the slug is genuinely new.
- `meta` is the built-in stream for ledger-system work.
- The response returns the event, the emitting session, and the stream.
- **Logging also writes your session** (`last_event_at`, `status="active"`) in
  the same transaction. That is the only place the two planes touch.

Your session id: the full uuid, visible in your scratchpad directory path.

**Emission rules — the judgment half (the service cannot see any of this):**

1. **What qualifies:** a deliverable shipped · a decision made · an external
   communication sent · a stream changing state · an open loop opened or
   closed. **Not:** routine lookups, intermediate steps, or anything
   reconstructible from git or the tool it lives in.
2. **One event per outcome, at completion** — not per step, not per tool call.
   A long session that ships one thing emits one event.
3. **Self-triggered** — because the work happened, not because the user
   narrated it.
4. **Stream discipline** — every event names its stream; genuinely new thread
   → `create_stream` in the same call; ledger-system work → `meta`.
5. **Corrections are new events** — never edited, never deleted; a later event
   supersedes an earlier one.

**Shape is the service's business** (one-line headline, 1–4 bullets,
`session_id` required, stream exists or comes with `create_stream`, atomic,
immutable). If a call is rejected, fix the call — never route around it, and
never hand-edit a data file. A change that would require reaching around the
API means the API is missing an endpoint; the service gets extended.

### recall <topic>

`GET {base}/ledger/search?q=<topic>` (also `/events?stream_id=&since=`).
Answer inline, in prose — dates, links, current state. If the ledger has
nothing, say so.

### review [week|month]

The management overlay (default: last 7 days).
`GET {base}/ledger/streams` + `GET {base}/ledger/events?since=` — digest what
moved, what's stalled, open loops, suggested next actions. Offer to close
streams idle for a month. Staleness comes from the service: fresh ≤3d,
aging 4–14d, stale >14d.

### stream <name> [close]

- Show: `GET {base}/ledger/streams`.
- Update: `PUT {base}/ledger/streams/{id}` — field-level replace of `title`,
  `state`, `next_action`, `open_loops`, `working_paths`. Usually unnecessary:
  prefer `stream_update` inside `log`.
- Close: `POST {base}/ledger/streams/{id}/close` with `{"reason": "..."}` —
  logs its own closure event.

### sessions [list | archive <prefix>… | archive --all --keep <prefix>… | unarchive <prefix>]

The **only** session write you ever make — and only when the user asks.
*Seeing* the board needs no Claude at all.

- `list` — `GET {base}/ledger/sessions` → `{items: [...]}`, each with stored
  `status` plus computed `activity`, `relevant`. Filters: `?status=`
  `?machine=` `?relevant=true`.
- `archive <prefix>…` — resolve prefixes against `list`, then
  `POST {base}/ledger/sessions/{id}/archive` per session (409 = it's active;
  tell the user, don't force). Batch:
  `POST {base}/ledger/sessions/archive` with `{"prefixes": [...]}` or
  `{"all": true, "keep": [...]}`.
- `unarchive <prefix>` — `POST {base}/ledger/sessions/{id}/unarchive`
  (usually unnecessary: any activity writes the session back to active).

There is no `seed` — the store initializes from live activity; a session
appears on its first prompt.

## The board and the orientation — both automatic

**The board.** Hooks post every SessionStart / UserPromptSubmit / Stop /
SessionEnd / PostToolUse signal to
`POST {base}/ledger/sessions/{id}/signals`. The service writes the
declared statuses and serves `GET {base}/ledger/board`; the user watches the
**Sessions view in the BotBeam app** — Active sessions as cards in a stable
grid (solid green = processing, ⚡ = run, hollow ring = waiting; ordered by
first_seen so cards never jump), Inactive sessions below by recency, and the
**events feed** beneath both. Only ever-prompted, non-archived, non-expired
sessions appear.

**The orientation.** The one-screen "what's going on" injected into every new
session by the SessionStart hook — active streams with their state and next
action, plus recent activity. It comes from `GET {base}/ledger/index`, served
by the service. It is why a brand-new session already knows what is in flight.
You never maintain it and never write it.

Never post session state by hand, and never render or beam a board yourself.

## Setup (once per machine — offer if not wired)

1. **CLAUDE.md pointer** (`~/.claude/CLAUDE.md`): log significant work via this
   skill; consult the ledger for "what's going on."
2. **Hooks** (`~/.claude/settings.json`): SessionStart (fetch
   `GET {base}/ledger/index` for orientation, plus the transmitter),
   UserPromptSubmit, Stop, SessionEnd, PostToolUse (no matcher — all tools; the
   service classifies) →
   `python "C:/code/woodshed/skills/ledger/scripts/session_event.py"`, all
   `"shell": "bash"`, `"async": true`.
3. **Sweep task**: `schtasks /Create /TN LedgerSweepReport /SC MINUTE /MO 5
   /TR "pythonw C:\code\woodshed\skills\ledger\scripts\sweep_report.py"`.
4. **Credentials**: `~/.config/orchestra/botbeam.json` — `base_url` + agent
   `token`.
