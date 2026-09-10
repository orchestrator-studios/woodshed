# Veracity: making this trustworthy, not just plausible

Cliff's question (2026-09-09): beyond the audit trail, what should we do so
the output is much better than what Claude Chat or ChatGPT would produce
without a custom skill?

The failure mode to design against is specific: a vanilla chatbot asked "who
at Daversa runs CRO searches" produces a *plausible* answer — a real-sounding
name, a confident title, maybe an email — with no way to tell which parts
were retrieved and which were pattern-completed. For this skill the cost of
that failure is concrete: Carrie sends an outreach that embarrasses her.
Every mechanism below exists to make fabrication structurally hard, not just
discouraged.

## Mechanisms, roughly in order of leverage

**1. Fetch-before-assert.** No person, title, or URL appears in the record
unless it came out of a retrieval performed in this run (or a dated cached
profile). Never cite a page that wasn't actually fetched; never name a person
remembered from training data without confirming them in a live source. This
single rule kills the biggest vanilla-chat failure: confabulated specifics.

**2. Snippet-level evidence.** The audit trail stores not just the URL but
the supporting quote — the sentence from the page that backs the claim
("...co-heads the firm's B2B go-to-market practice..."). Verification becomes
one click plus ctrl-F instead of re-doing the research. Claims that can't
carry a snippet get demoted to inference and labeled as such.

**3. Adversarial verification pass before render.** After the record is
drafted, a separate pass tries to *refute* the decorated entries: is this
person still at the org (check for departure news and newer roles)? Does the
cited page actually say what the rationale claims? Is the title current or
from a stale team page? Ideally run with fresh eyes (a subagent that sees
only the claims and the sources, not the reasoning that produced them), so it
inherits no confirmation bias. Findings downgrade confidence or move a
candidate down; the pass itself is logged in the audit trail as `verify`.

**4. Entity resolution.** Common names collide. Before decorating anyone,
confirm the person via at least two attributes that must co-occur (name +
current org, or name + role history). A LinkedIn profile with the right name
and the wrong history is a different person; this is a classic silent error.

**5. Freshness dating.** Every source in the audit gets an as-of date where
one exists (article date, page-fetched date otherwise). Titles decay; team
pages lag by quarters. A claim resting only on sources older than ~a year
gets a staleness caveat automatically. The card already stamps `run_at`;
refresh mode re-verifies rather than re-trusting.

**6. Structured confidence with stated basis.** The schema requires
`confidence.basis` — a chip can't exist without its evidence sentence, and
the honesty rules tie chip levels to source count and source type (stated
mandate vs. title inference). Vanilla chat has no equivalent forcing
function: its confidence is tone.

**7. Contact-info no-fabrication.** Emails carry `verified |
pattern_inferred | unknown`, inferred addresses always render "verify before
sending", and `unknown` means recommend another channel — never guess. An
invented email is the single most embarrassing possible output.

**8. Negative space is reported.** "No warm path found", "only two people at
this firm plausibly touch your lane", "nothing on this person directly" are
findings that appear on the card. A system that can say "not found" earns
trust for its positive claims. (Inherited from backgrounder's honesty rules.)

**9. The ranked list itself.** Returning one confident answer is the
chatbot's failure shape. The ranked list with scores, an `also_considered`
section with why-nots, and only the top 1–2 decorated keeps the output
honest about how much separation the evidence actually supports.

**10. Feedback loop (later).** When Carrie reports an outcome — "she
redirected me to her colleague", "that email bounced" — record it against
the run and use it on refresh. Redirects are ground truth about who actually
owns the lane; no public source beats them.

## What's baked into the skill draft vs. deferred

Baked in now: 1–9 (SKILL.md contracts, verification phase, playbook rules,
schema `basis`/`status`/`snippet` fields, audit trail).

Deferred: 10 (feedback capture needs a place to live — likely a per-run log
next to the profile), and any scoring of source reliability beyond the
current hierarchy. Both are worth discussing before the skill is committed.
