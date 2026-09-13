---
name: ledger
description: Global cross-session work memory and session board — a live database of sessions (what's running), runs (what's being made right now), events (what happened), and the deliverables and streams they belong to, held by the BotBeam ledger service (/ledger API). Use when significant work completes (deliverable shipped, decision made, external communication sent), when starting or finishing a bounded piece of work on something, when asked to log work, recall what happened, review open loops, check what's going on, or manage sessions/streams on the board. Verbs — log, run, recall, review, stream, sessions.
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

Two independent feeds keep the database current. They never talk to each
other; each talks only to the service, which is the only writer.

| Feed | Runs | Maintains | If it stops |
|---|---|---|---|
| **Hooks** | automatically, on 5 CC lifecycle moments | session rows | the board goes stale |
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

**Runs and deliverables are your job too** (Book rev 21). Logging records what
happened; opening a run declares what you are *doing* while you do it. Both are
standing duties, neither waits to be asked.

## Objects

| Object | Origin | What it is |
|---|---|---|
| Workspace | Claude Code | directory Claude launches in; has many sessions |
| Session | Claude Code | persistent conversation; the service annotates it (status, stream, activity) |
| Stream | ledger | thread of work under management — state, next action, open loops |
| Event | ledger | something that happened; append-only, immutable |
| Deliverable | ledger | something made — a name plus exactly one home; persists and is advanced |
| Run | ledger | a bounded stretch of work on one deliverable; declared open, declared closed |

**Two planes, two nouns, never interchanged.** Hooks post **signals**
(telemetry — mechanical, high-volume, not stored as records; they update
columns on the session row). You post **events** (the record — judged, rare,
stored forever, immutable).

Session lifecycle: **active** (waiting ⇄ processing) → **dormant** ⇄
**archived**. Three states, no fourth. Statuses are **stored, declared** by the
signal or call that causes each transition — nothing is inferred from
timestamps. Archive is the one manual act: it is how a finished card leaves the
board. A crashed session keeps its last status until a repair mechanism is
added (deferred, known gap).

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
- `create_stream` only when the slug is genuinely new. See **Streams** below.
- `meta` is the built-in stream for ledger-system work — not a home for
  uncategorized work.
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
4. **Stream discipline** — every event names its stream; nothing fits → create
   it in the same call; ledger-system work → `meta`. See **Streams** below.
5. **Corrections are new events** — never edited, never deleted; a later event
   supersedes an earlier one.

**Shape is the service's business** (one-line headline, 1–4 bullets,
`session_id` required, stream exists or comes with `create_stream`, atomic,
immutable). If a call is rejected, fix the call — never route around it, and
never hand-edit a data file. A change that would require reaching around the
API means the API is missing an endpoint; the service gets extended.

### run — open one when you start making something

A **deliverable** is a thing that was made — a name plus exactly one home. It
**persists and is advanced**: the Ledger Book is one deliverable at revs 18 →
19 → 20 → 21, not four unrelated events. A **run** is a bounded stretch of work
against exactly one deliverable, **declared at both ends** — nothing is timed,
sampled, or inferred. The old `run` (a bolt computed from a decaying
`last_run_at`) is deleted.

```
POST {base}/ledger/runs            open   {deliverable_id | create_deliverable, session_id, intent}
POST {base}/ledger/runs/{id}/close end    {session_id, outcome: closed|abandoned, state?}
GET  {base}/ledger/runs?open=true         what the board reads for the ⚡
GET  {base}/ledger/deliverables
POST {base}/ledger/deliverables/{id}/retire · /unretire   — only when the user asks
```

`create_deliverable.stream_id` must name an **existing** stream (404 if not) —
there is no nested `create_stream`. Make the stream first if you need one.

- **Open a run** at the front edge of work that is bounded, aimed at a known
  deliverable, and worth watching — **minutes, not seconds**. Declare the
  **intent** ("cutting rev 21"), never a prediction of scope. Scope changes
  mid-run constantly; that does not make the declaration wrong.
- **A deliverable is born inside the run that needs it** (`create_deliverable`
  rides in the open call), exactly as a stream is born inside its event.
- **Always close.** `closed` carries the deliverable's new `state`;
  `abandoned` leaves it untouched and is a perfectly good ending. An open run
  left behind is the one way this plane can lie on the board. Resubmitting the
  current `state` verbatim is legitimate — a run can finish honestly without
  changing how you'd describe the thing.
- **One open run per session** (409 on a second). If you crashed mid-run, your
  own leaked run is what you'll collide with on resume. Recipe:
  `GET {base}/ledger/runs?open=true&session_id={yours}` → close it as
  `abandoned` → open the new one. Any session may close any run, so you can do
  this for another session too.
- **A run spans turns.** Stopping to ask the user something does not end it —
  the board shows ring+⚡, "parked mid-run." Close it when the *work* ends, not
  when the turn does.
- **Retiring a deliverable is the user's call, never yours** — same rule as
  archiving a session or closing a stream.
- **Why two calls when an event is one:** you know in advance that you are
  starting bounded work on a known thing, so it can be declared up front. You
  do *not* know in advance that a decision is about to be made — those are
  recognised only as they happen. Events stay a single call.
- **Open question:** whether a closing run also writes an event is deliberately
  unsettled. Do not assume one.

### Streams — how they work

**You already know which streams exist.** The orientation injected at session
start lists every active stream with its state and next action. Match your work
against that list; it is the whole basis for choosing a stream.

**Creating one.** When nothing on the list fits, the new stream is born with
the event that needed it — `stream_id` is the slug you are minting and
`create_stream` carries its opening fields, in the same atomic call. There is
no separate create step and never a stream without an event behind it.

- **Re-read first.** Another session may have created a stream since your
  orientation was injected. `GET {base}/ledger/streams` before minting a slug,
  or you will end up with two slugs for one thread of work.
- **Slugs are permanent.** Events reference them; a rename orphans history.
  Short, lowercase, the thing itself.
- `working_paths` is the attribution fallback for sessions that have not logged
  yet — set it when the work has a home directory.

**Closing one is the user's call, never yours.** A stream stays active until
the user explicitly closes it. Do not close a stream on your own judgment, and
do not nag about age or staleness — an old quiet stream is not a problem to
solve. When asked: `POST {base}/ledger/streams/{id}/close`.

**Keeping it current.** `state`, `next_action`, and `open_loops` are yours to
write, and they ride inside `log` as `stream_update` whenever an outcome
changed them. `state` is a few sentences of current reality, rewritten whole
rather than appended to. `next_action` is one concrete step, phrased so it can
be started cold. `open_loops` are things that would otherwise be forgotten.

### recall <topic>

`GET {base}/ledger/search?q=<topic>` (also `/events?stream_id=&since=`).
Answer inline, in prose — dates, links, current state. If the ledger has
nothing, say so.

### review [week|month]

The management overlay (default: last 7 days).
`GET {base}/ledger/streams` + `GET {base}/ledger/events?since=` — digest what
moved, what's stalled, open loops, suggested next actions. Staleness comes from
the service: fresh ≤3d, aging 4–14d, stale >14d. Report it; never propose
closing a stream because of it.

### stream <name> [close]

- Show: `GET {base}/ledger/streams`.
- Update: `PUT {base}/ledger/streams/{id}` — field-level replace of `title`,
  `state`, `next_action`, `open_loops`, `working_paths`. Usually unnecessary:
  prefer `stream_update` inside `log`.
- Close: `POST {base}/ledger/streams/{id}/close` with `{"reason": "...",
  "session_id": "<yours>"}` — logs its own closure event. **Only when the user
  asks.**

### sessions [list | archive <prefix>… | archive --all --keep <prefix>… | unarchive <prefix>]

The **only** session write you ever make — and only when the user asks.
*Seeing* the board needs no Claude at all.

- `list` — `GET {base}/ledger/sessions` → `{items: [...]}`, each with stored
  `status` (active/dormant/archived) plus computed `activity`, `relevant`.
  Filters: `?status=` `?machine=` `?relevant=true`.
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
grid (solid green = processing, ⚡ = an open run, hollow ring = waiting; ordered by
first_seen so cards never jump), Inactive sessions below by recency, and the
**events feed** beneath both. Only ever-prompted, non-archived sessions appear.

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
3. **Credentials**: `~/.config/orchestra/botbeam.json` — `base_url` + agent
   `token`.
