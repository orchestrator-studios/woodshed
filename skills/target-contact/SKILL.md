---
name: target-contact
description: Given an organization and a practice area, find the most senior person there who owns that lane for a specific seeker, and the best way to reach them. Use whenever the user asks who to contact, target, or focus on at a firm or company — "who at X should I talk to", "find the right recruiter at X", "who runs recruiting for [function] at X", "who owns [practice] searches at X", "who leads [area] at X" — for recruiting firms (which partner covers the seeker's lane), companies (who runs internal recruiting for the target org), or leadership (the senior people the seeker would work for/with).
---

# Target Contact

Answer the question **"Who at X owns Y, given person Z?"** — X an organization,
Y a practice area or function, Z the seeker.

Produce one deliverable: a **results card** (HTML, published as an artifact) —
a ranked list of ~3–6 candidates, the top 1–2 decorated with full detail
(rationale, confidence, contact, warm paths, outreach angle), plus caveats and
an audit trail of every supporting search.

**The contracts that make this a system, not a one-off:**

1. **Z conditions the answer.** "Owns" is relative to the seeker: their
   industry lane, seniority tier, geography, and network change who the right
   person is. Two seekers asking about the same firm and function may
   correctly get different ranked lists. Never rank against Y in the
   abstract; always rank against Z's bio. That is why the seeker bio is built
   *first*, before any org research.
2. **Ranked list, never a single answer.** A practice area legitimately maps
   to several people. Return the ranked list with honest relevance scores;
   decorate only the top 1–2.
3. **Schema before card.** Build the full JSON record
   (`references/output-schema.json`) first; the card renders strictly from
   it. Nothing appears on the card that is not in the record.
4. **The audit trail is complete.** Every search that informed the card goes
   in the record's `audit` block — query, tool, results, and what each
   contributed or why it was discarded. For load-bearing claims, store the
   supporting quote in the result's `snippet` so verification is one click.
   The confidence chips are only as credible as the evidence behind them.
5. **Fetch before assert.** No person, title, or URL enters the record unless
   it came from a retrieval performed in this run (or a dated cached
   profile). Never cite a page you didn't fetch; never name a person from
   memory without confirming them in a live source.

## Phase 0 — Inputs

You need: (a) the organization X, (b) the target kind — `recruiters` at a
search firm, `internal_recruiting` at a company, or `leadership` at a company
(search firm implies recruiters; for a company, infer from what the user asked
and say which you chose), (c) the practice area Y — defaults from the seeker's
profile, override or narrow when the user specifies, and (d) the seeker Z —
default to the stored profile in `profiles/` when the user doesn't say
otherwise. Don't ask questions you can answer by searching.

## Phase 1 — Seeker bio (Z)

Check `profiles/<name>.md` first. If a profile exists and is under ~90 days
old, use it. If missing or stale, build it: LinkedIn profile plus web search
(press, Crunchbase, conference bios). Capture: career history with dates and
employers, function, level, industries, geography, and the **network
surface** — past employers and orgs where warm paths are likely to live.
Write it to `profiles/<name>.md` with a built-date and sources, then reuse it
across queries.

## Phase 2 — Enumerate candidates at X

Read `references/research-playbook.md` for per-target-kind tactics. In short:
firm/company team pages first, then trade press (Hunt Scanlon for exec
search), LinkedIn people search, Crunchbase. Cast wide here — a candidate cut
in ranking becomes an `also_considered` row with a `why_not`, which is
information the user wants.

## Phase 3 — Rank against Z

Score each candidate's relevance (0–100) *to this seeker*: does this person
own Z's lane (function × level × industries), at a seniority that opens doors
rather than screens resumes? Rationale is one sentence, specific. Assign
confidence per candidate with its basis stated: `high` needs a stated mandate
(named practice lead, or placements in the lane covered by press); `medium`
is title-plus-inference; `low` is title only. Seniority rule: the most senior
*relevant* person beats the most senior person — a practice partner outranks
the firm's founder if the founder doesn't touch Z's lane.

## Phase 4 — Decorate the top 1–2

For the decorated entries only:

- **Contact.** LinkedIn URL. Email carries an explicit status: `verified`,
  `pattern_inferred` (e.g. via hunter.io domain pattern), or `unknown`. Never
  present an inferred email as verified; the card says "verify before
  sending" on inferred addresses.
- **Warm paths.** Intersect the candidate's history with Z's network surface:
  shared employers with overlapping years, shared boards, mutual orbits. A
  warm intro beats a cold email; say so in the outreach angle. "None found"
  is a finding — record it.
- **Recent signal.** A recent placement, post, or press item that makes the
  outreach timely.
- **Outreach angle.** One short paragraph: which parts of Z's story to lead
  with, and which channel to use first, grounded in the evidence above.

## Phase 4.5 — Verify before render

Draft record in hand, try to refute the decorated entries before anything
renders:

- **Identity.** Confirm each decorated person via two co-occurring attributes
  (name + current org, or name + role history). Same-name collisions are a
  silent, classic error.
- **Currency.** Search for departure news or a newer role; team pages lag by
  quarters. A title only as fresh as a stale page gets a staleness caveat.
- **Claims.** Re-check that each cited source actually says what the
  rationale claims (the stored snippets make this fast).

When practical, run this as a fresh-eyes subagent that sees only the claims
and sources, not the reasoning that produced them. Findings downgrade
confidence or reorder ranks; log the pass in the audit trail as step
`verify`.

## Phase 5 — Render the card

Assemble the full record per `references/output-schema.json`, including
`also_considered`, `caveats`, and the complete `audit` block. Then render
from `assets/card-template.html` — a tested single-column layout (light by
default, dark via the card's own toggle) with copy buttons for the page,
each card, contact records, sections, and the raw JSON; the template's
comments mark each region and the schema field it renders. Fill strictly
from the record.

**Every run writes local copies first, then publishes.** Save both the card
HTML and the record JSON to the designated output folder as
`<org-slug>-<run date>.html` / `.json` — never leave a run existing only in
the cloud. The output folder is `runs/` next to this skill's project docs
during development (in woodshed: `docs/target-contact/runs/`); when the
skill is installed standalone, use an `output/` folder the user designates
on first run and remember it. Then publish the card as an artifact and give
the user both the link and the local path. When re-running a query for the
same X, republish to the same artifact URL rather than minting a new one,
and write a new dated file rather than overwriting the old run.

## Voice

Card copy and chat messages are plain professional prose. No em dashes; use
commas, periods, colons, or parentheses. No dramatic framing. Rationales say
what the evidence is, not how impressive the person is.

## Honesty rules

- Confidence chips must trace to the audit trail. If the basis is one
  LinkedIn title, the chip says low and the caveats say so.
- A thin result is a finding, not a failure: if only two people at X plausibly
  touch Y, the card has two rows and says why.
- Distinguish stated fact ("named GTM practice co-lead on the firm's site")
  from inference ("placement history suggests adtech focus") everywhere,
  including rationales.
- Team pages lag reality; when a source may be stale, the caveats say so.
