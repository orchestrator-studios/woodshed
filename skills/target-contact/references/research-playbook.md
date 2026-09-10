# Research playbook

Tactics per target kind, source hierarchy, and the rules for confidence,
email status, and warm paths. Every search performed here goes into the
record's `audit` block as it happens, not reconstructed afterward.

## Source hierarchy

1. **The org's own site** (team/partners/leadership pages). Best for names,
   titles, and stated practice mandates. Team pages hide people in JS
   sometimes; check raw HTML. Caveat: pages lag reality by a quarter or more.
2. **Trade press.** For executive search, Hunt Scanlon (huntscanlon.com)
   covers partner hires, promotions, and placements — the best public
   evidence of who actually runs which searches. For companies, funding and
   exec-hire announcements name who led what.
3. **LinkedIn.** People search on `company + title keywords`; profiles for
   history and tenure. Public pages only unless the user provides logged-in
   browsing; note which mode the run used in the caveats.
4. **Crunchbase** for people histories; conference speaker bios for
   self-described mandates.
5. **Aggregators (ZoomInfo, RocketReach, etc.):** corroboration only, never
   the sole source for a claim — titles there go stale and are often scraped
   guesses.

## Enumerating: search firms (`recruiters`)

- Fetch the team page; list everyone plausibly in the seeker's lane.
- Search `"<firm>" <function> practice partner` and
  `site:huntscanlon.com <firm>` for practice leads and recent placements.
- Titles decode seniority: Partner / Managing Director run searches and open
  doors; Principal runs searches under a partner (useful fallback contact);
  VP / Associate / Researcher screen and source — too junior to be the
  target, but can appear in `also_considered`.
- The founder/CEO of the firm is usually the wrong answer unless they
  personally run the seeker's practice; if excluded, say so in
  `also_considered` with `why_not`.

## Enumerating: companies (`internal_recruiting`)

- Title vocabulary, roughly senior to junior: Chief People Officer / CHRO;
  VP or Head of Talent Acquisition; Head of Executive Recruiting /
  Executive Talent; Lead Recruiter for a function ("GTM Recruiting Lead").
- The right person depends on the seeker's level: an exec-level seeker wants
  Executive Recruiting or the CPO (at smaller companies the CPO owns exec
  hiring directly); below exec level, the functional recruiting lead.
- Search LinkedIn people for `<company> executive recruiting`, `<company>
  talent acquisition`, and check the company's leadership page for the
  people org.

## Enumerating: companies (`leadership`)

- The seeker's would-be boss and peers: for a GTM seeker that is the CRO,
  President, COO, or CEO depending on company size.
- Leadership page first, then press (exec-hire announcements carry mandate
  descriptions), then LinkedIn.

## Ranking rules

- Score relevance to **this seeker's** function × level × industries, not the
  function in the abstract.
- Most senior *relevant* beats most senior absolutely.
- Geography is a soft signal (same city helps warm outreach) — tiebreaker,
  not a gate.
- Keep 3–6 in `results`; everyone else you seriously looked at goes to
  `also_considered` with an honest `why_not`.

## Confidence rules

- `high`: a stated mandate — named practice lead on the org's site, or
  placements/hires in the seeker's lane covered by press. Two independent
  sources.
- `medium`: title plus inference (e.g. placement history suggests the lane
  but nothing states it).
- `low`: title only, single source. Low-confidence entries stay in the list
  (they are leads), but the caveats say what would firm them up.

## Email rules

- `verified`: confirmed deliverable or published by the person/org.
- `pattern_inferred`: constructed from the org's email pattern (hunter.io or
  observed addresses). Always renders with "verify before sending".
- `unknown`: don't guess. LinkedIn or a warm path is the channel instead.
- Never invent an address; never upgrade a pattern to verified.

## Warm paths

- Intersect the candidate's employment history with the seeker's network
  surface (from the profile): shared employers require overlapping years to
  count — same company, disjoint eras is a talking point, not a warm path.
- Boards, investor networks, and alumni groups count when specific.
- Rank channels in the outreach angle: warm intro > LinkedIn from a shared
  context > inferred email. "No warm path found" is a finding; record it and
  recommend the next-best channel.
