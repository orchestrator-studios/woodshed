# Backgrounder skill — handoff notes for Cliff

From Adam, Sept 2026. The skill researches a person across the operator's Gmail + Calendar + the public web, builds a multi-tab Google Sheet as the auditable record, then renders a one-screen HTML brief strictly from the sheet. It works well; the ask is optimization — mostly wall-clock.

## Contents

```
backgrounder/
  SKILL.md                    the skill (phases, tab specs, honesty rules)
  scripts/fetch_corpus.py     Gmail corpus fetcher (metadata-first, resumable)
  references/brief-rules.md   selection judgment for the one-screen brief
  assets/brief-template.html  tested 3-col light/dark brief layout
  evals/evals.json            eval prompts — see caveat at bottom
```

Drop `backgrounder/` into `~/.claude/skills/`.

## Google access

Everything goes through the `gws` CLI (`@googleworkspace/cli` ≥ 0.22), one config dir per identity, selected per call via `GOOGLE_WORKSPACE_CLI_CONFIG_DIR`. You need a `client_secret.json` (Desktop type) in your config dir — Adam can have you added to the shared GCP project's test-user list, or stand up your own. Then:

```bash
gws auth login --scopes "https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/gmail.modify,https://www.googleapis.com/auth/calendar,https://www.googleapis.com/auth/contacts,https://www.googleapis.com/auth/contacts.other.readonly,openid,https://www.googleapis.com/auth/userinfo.email"
```

Two non-obvious quirks that will bite you otherwise:

- **`project_id` quirk**: `gws auth login` requires `project_id` in `client_secret.json`, but leaving it there makes every API call send `x-goog-user-project`, and non-owners of the project get 403s. Log in with it present, then delete the `project_id` field from the copy in your config dir.
- gws output is prefixed with a `Using keyring backend:` line — strip before parsing JSON.

The skill expects a companion `google-workspace` skill for command patterns; if you don't run Adam's orchestra plugin, the skill still works — the model just leans on `gws --help`/`gws schema` more.

## Performance profile (from a real worst-case-ish run)

Subject with a 20-year history: 447 matched message ids, ~440 metadata fetches, 209 body fetches, ~3–4 min for the corpus (rate-limit dominated), largely masked by running it in the background while calendar/web/sheet work proceeds. Small subjects are a fraction of this.

## Optimization backlog, in expected-value order

1. **Per-message subprocess overhead — the big one.** `fetch_corpus.py` spawns a full `gws` Node process per message (`get_msg` → `subprocess.run`), so every fetch pays ~300–500ms of CLI startup on top of the HTTP call, bounded by `--workers`. Two escape hatches: (a) Gmail API **batch endpoint** (up to 100 `messages.get` per HTTP request), or (b) skip the CLI for the hot loop — pull the bearer token once and hit the REST API directly from Python. Either should cut a rich corpus fetch from minutes to tens of seconds. Keep the retry/backoff and resume behavior; that part earns its keep.

2. **`--full-since` flag.** Currently `--full-addresses` fetches bodies for *every* message the person sent/received across all years; a 20-year record fetched 209 bodies of which ~15 were read. Bodies for the last ~3 years plus on-demand fetches for older threads the model elects to read would halve the body pass. Known tradeoff: without a body, a mention row can't be labeled "quoted mention only", so old rows get slightly vaguer gists. Adam reviewed and deliberately skipped this one; it's viable if #1 doesn't get you enough.

3. **Junk-sender exclusions** (done, Sept 2026): the name query now carries `-from:` exclusions for alert digests, social notifications, bounces. Before that, ~34% of fetched ids were junk dropped post-fetch. Extend the list when a subject's first results page shows another bulk sender.

4. **Scheduling**: launch the corpus fetch the instant the person's addresses are confirmed (before building the sheet skeleton), and push web research to a parallel subagent. Together maybe 30–60s.

Non-goals: the sheet-before-brief contract (auditability), the honesty rules, and metadata-first fetching are load-bearing — optimize around them, not through them.

## Eval caveat

`evals/evals.json` targets "Knut Olson" — seeded test data in Adam's mailbox. Point it at someone with real history in *your* mail (ideally one sparse subject and one rich one; the failure modes differ — padding vs. drowning).
