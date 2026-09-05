---
name: backgrounder
description: Research a person from the user's Gmail, Google Calendar, and the public web, compile a multi-tab Google Sheet backgrounder in Drive, and render a one-screen HTML pre-meeting brief from it. Use this whenever the user asks for a backgrounder, dossier, or research on a person they know or correspond with — "who is X", "brief me on X", "prep me for my meeting with X", "what's my history with X", "pull together what we know about X" — even when they don't say "backgrounder". Also use it to refresh or update an existing backgrounder sheet or brief before a meeting.
---

# Backgrounder

Produce two linked deliverables about one person:

1. **The backgrounder sheet** — a multi-tab Google Sheet in Drive: the complete research record.
2. **The brief** — a one-screen HTML page the user reads the day before meeting the person: a curated subset of the sheet.

**The contract that makes this a system, not a one-off:** every fact lands in the sheet *before* it may appear on the brief or anywhere else. The sheet is the complete record; the brief renders only from the sheet. When you discover something new while building the brief (a photo, a bio fact), write it to the sheet first. This keeps the record auditable and lets the user trust that "look at the spreadsheet if I need detail" is always true.

All Google access goes through the `gws` CLI — load the `google-workspace` skill (or its equivalent) for identity resolution and command patterns. Every `gws` call runs as exactly one identity via `GOOGLE_WORKSPACE_CLI_CONFIG_DIR`; resolve which identity owns the user's mail before the first call.

## Phase 0 — Inputs

You need: (a) who the person is (a name, possibly partial, plus whatever context the user gave — "Ed, who I met through Michael"), and (b) a destination Drive folder. If no folder is given, create one named "<Person> Backgrounder" and tell the user where it is. Don't ask questions you can answer by searching.

## Phase 1 — Identify the person

A first name plus context is usually enough. Search Gmail for the name; when results are noisy, pivot through the context (the introducer's address, a shared company domain, `subject:` searches). You've identified them when you have:

- Full name, **including spelling variants** (people misspell names in email — record variants; search under all of them).
- Every email address they use (personal and work often both exist; each reveals different threads).
- The anchor facts: who introduced them, what organization connects them to the user.

Watch for false positives: Gmail matches attachments and newsletters, so a name query returns junk (LinkedIn notifications, marketing, unrelated people sharing the name). Verify a message actually concerns *this* person before it enters the record — check the body, not just the match.

## Phase 2 — Skeleton first

Create the sheet in the destination folder, add all tabs with header rows, format (bold frozen headers, wrapped cells, sensible column widths) — then **give the user the link immediately**, before deep research. They asked for something that takes minutes; the link lets them watch it fill in.

## Phase 3 — Populate the tabs

**Fetch the corpus with `scripts/fetch_corpus.py`, not ad-hoc loops.** It lists every matching message, pulls lightweight metadata (headers + snippet) for all of them, and fetches full bodies only where they earn their cost: messages the person sent or received, plus the most recent N. Metadata is enough for the mentions inventory; bodies are for the subset you actually read. The script handles pagination, concurrency, retries, and resume, which otherwise eat several minutes per run in rediscovered rate limits:

```bash
python3 <skill>/scripts/fetch_corpus.py --config-dir ~/.config/<identity> --out <scratch>/corpus \
  --query 'from:X OR to:X OR cc:X' \
  --query '"Full Name" -from:linkedin.com -from:googlealerts-noreply@google.com -from:postmaster.twitter.com -from:mailer-daemon@googlemail.com -from:calendar-invite@lu.ma' \
  --full-addresses X,Y --full-recent 30
```

Keep the junk exclusions on the name query: alert digests, social-network notifications, and bounce messages match names constantly and would otherwise be fetched only to be dropped (they cost a quarter of the fetch on a rich record). Add more `-from:` terms when the first results page shows another bulk sender for this person.

**Write each tab to the sheet as soon as its data is ready** rather than batching writes at the end. The user is watching the sheet fill in; a tab that lands two minutes earlier is two minutes of visible progress. Natural order: Contact & Bio (partial, updated later as web facts arrive), Email Mentions, Meetings, Context, In the News.

Each tab states its source.

**Contact & Bio** (Field/Value rows): name + variants, all email addresses, phone, LinkedIn, location, current role, relationship status, introducer, preferred channels, key colleagues — then a prose bio paragraph, and a **Caveat row** stating the compilation date and known limits of the record. Add a **Photo row** when a photo is found later (source URL + a copy saved to the Drive folder).

**Email Mentions** (Date, From, To/CC, Subject, How they come up, Link): every email where the person genuinely appears — as sender, recipient, or discussed. Chronological. The "how they come up" column is a one-line gist, not a category code. Label honestly: a reply that only carries the name in quoted text is "quoted mention only"; a cc with no discussion is "recipient". Exclude attachment-only matches. Link each row to `https://mail.google.com/mail/u/0/#all/<messageId>` (works for the mailbox owner; note this assumption).

**Context** (Theme, Gist, Supporting emails): the story, organized by theme rather than time — how the person entered the picture, their intended role, sensitivities, open questions. Name the tab after the shared organization or project when one exists ("Lexintel Context"). This is synthesis: 4–7 themes, each a few sentences, citing the emails behind it.

**Meetings** (Date, Meeting, Organizer, Who else was there, Likely topic, Notes): **from Calendar, not email** — users delete old invites, so calendar is the source of truth for what actually got scheduled. Search events by every known address and by name. Cross-reference email around each date to infer the topic. Record the negative space too: a note listing adjacent meetings the person was *not* in prevents the short list from reading as an oversight, and lets you later say "your only call with them was X" with confidence. Flag the standing blind spot: conversations on chat channels (WhatsApp, Slack) appear in neither source.

**In the News** (Date, Item, Source, Relevance): web search, past year. The person first; when they have no press footprint (most people), fall back to their firm and their role's context — and say plainly in the first row that nothing was found on the person directly. Rate each item's relevance honestly (direct / indirect / contextual). Items outside the window that are directly about the person's work may be included, labeled as dated. Web research often yields bio facts (real title, education) — those go into Contact & Bio, per the contract.

## Phase 4 — Render the brief

Read `references/brief-rules.md` for the selection judgment (what earns a place on one screen), then build from `assets/brief-template.html` — a tested three-column layout with light/dark themes. Fill it strictly from sheet content.

Deliver it twice: **publish as an artifact** (the link the user opens before the meeting) and **upload the HTML file to the same Drive folder** as the sheet, so the deliverables live together.

Photos: check the person's firm's team/staff page (often has clean headshots in the raw HTML as `background-image` URLs even when hidden from text extraction); LinkedIn photos are not fetchable. Downscale to <25KB and embed as a base64 data URI — the artifact CSP blocks external images, and embedding makes the brief durable. Record the source in the sheet's Photo row first.

## Refresh mode

When a backgrounder already exists ("update the brief for my meeting tomorrow"), don't rebuild: search Gmail/Calendar since the sheet's caveat date, append new rows, update the Context and the brief's timeline "Now" line and watch-outs, bump the caveat date, republish to the same artifact URL and Drive file.

## Voice

Everything the user reads (sheet cells, brief copy, chat messages) is written in plain professional prose:

- No em dashes. Use commas, periods, colons, or parentheses instead.
- No flowery comparisons, dramatic framing, or metaphors ("the rawest thing in the record", "the story arc"). Say what happened.
- Keep significance proportionate to real life. A person mentioning tennis once in a scheduling email is a scheduling email, not a personality insight. A minor unanswered question is a note, not a red flag. If an item would not matter to the user in the actual meeting, either leave it in the sheet or cut it; do not promote it with urgent labels. It is fine for a brief to have two watch-outs, or none.

## Honesty rules

- Sparse history is a finding, not a failure. Two relevant emails means the sheet says so; don't pad with noise to look thorough.
- The brief warns about what it doesn't know (off-email channels, unanswered questions) — an honest brief includes its own blind spots.
- Distinguish fact from inference throughout: "Michael says Ed is joining" is a fact; "he'll probably start in October" is your inference and must read as one.
