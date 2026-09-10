# target-contact — backgrounder & requirements survey

Project folder: `docs/target-contact/` gathers everything for this effort —
this requirements doc and the card mock (`card-mock.html`).

Working doc for a future skill. **We are not building the skill yet** — this doc
exists to gather insight first, so the skill is shaped by real requirements
rather than assumptions. Status: survey questions answered (first pass, from
public research — confirm with Adam/Carrie); input/output shape drafted;
results-card UI first pass built.

## Origin

WhatsApp exchange between Adam and Cliff, Sept 9 2026. Carrie (Adam's wife —
same end user as the backgrounder skill) described a recurring problem in her
job search: at large organizations, figuring out **who** the right person to
focus on is takes real work.

## The problem, as Adam framed it

Carrie has two cases where she needs to find the right person to focus her
attention on:

**1. Recruiting firms**
- Firms like [Daversa Partners](https://daversa.com/) are big enough to have
  many practice areas and many seniority levels.
- Carrie wants to quickly find the most senior person/people who work in *her*
  practice areas — and the best way to contact them.

**2. Target companies (internal recruiting)**
- Some companies Carrie is targeting are big enough that many internal
  hiring-oriented people run recruiting for the org she'd be working in.
- Carrie wants to quickly find the most senior person/people who deal with
  recruiting internally for her practice areas — and the best way to contact
  them.

**Related: senior leadership**
- Carrie will also want to find senior leadership in her area(s) at a
  particular company — the people she'd be working for/with, not just the
  recruiters who guard the door.

## Tools already on Carrie's radar

- [hunter.io](https://hunter.io/) — Carrie was considering it. Adam's read:
  it's not really oriented around finding *individuals* the way Carrie needs;
  it's more for finding email patterns / teams at a company. Likely role in the
  skill: a contact-info lookup *after* the right person is identified (email
  pattern inference / verification), not the discovery engine.

## Who Carrie is (public research, 2026-09-09)

Profile: [linkedin.com/in/carrieseifer](https://linkedin.com/in/carrieseifer)
(also surfaces as linkedin.com/in/carrie-seifer-aa04ab1).

Carrie Seifer is a revenue-leadership executive, ~25 years at the intersection
of marketing, media, and technology, based in New York:

- **Current/recent:** EVP, Global Revenue at Integral Ad Science (IAS) —
  global sales + customer success across Americas/EMEA/APAC. Joined ~2025
  after "5 awesome years at GWI."
- **Prior:** Chief Customer Officer & GM at GWI (market research/consumer
  insights); CRO at IBM Watson Advertising & The Weather Company; President of
  Investment at MediaVest / President, Publicis Spark Foundry; earlier
  leadership at Millennial Media, Meetup, Condé Nast, Vindigo, SixDegrees,
  Wired.
- **Recognition:** Adweek Media All-Stars, Business Insider 30 Most Powerful
  Women in Mobile, Cynopsis Top Women in Digital.

Sources: [LinkedIn](https://www.linkedin.com/in/carrie-seifer-aa04ab1),
[Crunchbase](https://www.crunchbase.com/person/carrie-seifer),
[GWI hire announcement](https://www.businesswire.com/news/home/20200211005383/en/),
[Brand Innovators](https://brand-innovators.com/speakers/carrie-seifer/),
[ZoomInfo](https://www.zoominfo.com/p/Carrie-Seifer/1611224813).

**What this implies:** her "practice area" is **go-to-market / revenue
leadership** (CRO, EVP Sales, Chief Customer Officer, President-level) in
**adtech / martech / media / data & insights**. That is precisely the lane of
firms like Daversa, which places CEO/CRO/CFO/CPO for venture-backed and
growth-stage tech and has a named
[B2B go-to-market practice](https://huntscanlon.com/daversa-partners-continues-expansion-of-its-european-practice/).

## Survey answers (first pass — inferred, to confirm with Adam/Carrie)

- **Practice areas.** GTM/revenue leadership (CRO, EVP Sales, CCO, President)
  × adtech/martech/media/data-insights. Stable enough to store as a default
  **seeker profile**; each search can override or narrow it.
- **Seniority.** At her level the right recruiter is a Partner/MD who *runs*
  CRO/GTM searches, not a senior associate; internally it's the Head/VP of
  Executive Talent Acquisition (or CPO at smaller companies). "Most senior
  *relevant*" beats "most senior absolutely" — a GTM-practice partner beats
  the firm's founder if the founder doesn't touch her lane.
- **Ranked list, not single answer.** (Cliff's directive.) Return ~3–6 ranked
  candidates; decorate the top 1–2 with full detail. Practice areas genuinely
  map to multiple people, so the list is the honest answer.
- **Contact.** Layered, in order of value: (1) warm-intro path through her
  network — 25 years in NYC media means shared employers/boards are likely;
  (2) LinkedIn profile; (3) email — verified if possible, else pattern-inferred
  via Hunter with an explicit confidence status. Never present an inferred
  email as verified.
- **Volume & cadence.** Job-search rhythm: a handful of orgs per week,
  one-at-a-time lookups. Design single-shot first; batch-over-a-target-list is
  a later configurability item.
- **Output form.** A **results card** (see below): ranked list, decorated top
  entries, caveats, sources. Backed by a well-defined JSON schema; the card is
  a template over the schema.
- **Sources.** LinkedIn (people + company pages), firm/company team pages,
  press (Hunt Scanlon covers exec-search moves), Crunchbase, Hunter for email
  patterns. Aggregators like ZoomInfo as corroboration only. Every claim on
  the card carries a source.
- **Success.** The top-ranked person, contacted the recommended way, engages —
  or at minimum is confirmed as the right owner of her lane. Failure signal:
  a redirect ("you want my colleague X") — worth capturing as feedback.

## Core formulation and workflow

The question the skill answers is: **"Who at X owns Y, given person Z?"**

- **X** — the organization (search firm or company)
- **Y** — the practice area / function being sought
- **Z** — the seeker, as a working bio

Z is not just a convenience that fills in a default Y. **Z conditions the
answer itself**: different Z's may get different people for the *same* X and
Y, because "owns" is relative to the seeker — their industry lane, seniority
tier, geography, and network all change who the right owner is. Two
executives both asking "who at Daversa owns CRO searches" should get
different ranked lists if one is growth-stage adtech and the other is
enterprise infrastructure.

Therefore the workflow is:

1. **Build the seeker bio (Z).** Before any org research, construct a working
   version of the user's bio — career history, function, level, industries,
   geography, and network surface (past employers, likely warm-path
   territory). Built from their LinkedIn + whatever they provide; cached as a
   stored profile and reused across queries, refreshed when stale.
2. **Resolve the query.** Combine Z with the org (X) and practice area (Y);
   Y may default from Z but can be overridden or narrowed per query.
3. **Research X.** Enumerate candidate people at the org for the target kind
   (recruiters / internal recruiting / leadership).
4. **Rank against Z.** Score relevance *relative to the seeker's bio*, not
   just against Y in the abstract.
5. **Decorate the top 1–2** (contact, warm paths from Z's network, outreach
   angle) and render the results card.

## Generalized input shape

The three cases collapse into one input: **organization + target kind +
practice area**, with the practice area defaulting from a stored seeker
profile.

```json
{
  "organization": { "name": "Daversa Partners", "domain": "daversa.com",
                    "kind": "search_firm | company" },
  "target": {
    "who": "recruiters | internal_recruiting | leadership",
    "function": "go-to-market / revenue leadership",
    "level": "C-level / EVP",
    "industries": ["adtech", "martech", "media", "data & insights"]
  },
  "seeker": { "profile": "carrie", "linkedin": "linkedin.com/in/carrieseifer" },
  "options": { "max_results": 6, "decorate_top": 2 }
}
```

Notes:
- `target.who` disambiguates the three cases; `organization.kind` usually
  implies it (search firm → recruiters) but companies need the
  internal-recruiting vs. leadership distinction.
- `seeker` (Z) is a first-class input, not metadata: it powers relevance
  ranking (her lane), warm-path detection (her employment history / network),
  and can shift *which* person ranks first even for an identical practice
  area. The `profile` value references a stored bio built in workflow step 1.
- A practice area may legitimately match several people — hence ranked list.

## Output schema (v0)

```json
{
  "query": { "…echo of input…": null, "run_at": "2026-09-09T14:30:00Z" },
  "results": [
    {
      "rank": 1,
      "name": "…", "current_title": "…", "org_unit": "B2B Go-to-Market practice",
      "location": "New York, NY",
      "relevance": { "score": 92, "rationale": "one sentence: why this person owns her lane" },
      "confidence": { "level": "high | medium | low", "basis": "what the evidence is" },
      "contact": {
        "linkedin": "https://…",
        "email": { "address": "…", "status": "verified | pattern_inferred | unknown", "source": "hunter.io" },
        "other": []
      },
      "sources": [ { "title": "…", "url": "…" } ],
      "detail": {
        "bio": "2–3 sentences",
        "tenure": "Partner since 2019",
        "recent_signal": "recent placement / post / press item",
        "warm_paths": [ { "via": "shared employer: Publicis", "note": "…" } ],
        "outreach_angle": "suggested opening hook"
      }
    }
  ],
  "also_considered": [ { "name": "…", "title": "…", "why_not": "…" } ],
  "caveats": [ "…" ]
}
```

`detail` is present only on decorated entries (top `decorate_top`). The card
UI is a pure template over this object — configurability later means theming
and field selection, not schema changes.

## Results card (UI first pass)

Mock lives at `card-mock.html` in this folder — a static render of the schema
with **illustrative sample people** (real firm, fictional partners, clearly
bannered) so we're not fabricating contact details for real people in a mock.
Published as an artifact for Adam/Carrie to react to.

Design intent: dossier-grade, scannable. Query echo up top; top 1–2 as
expanded entries (rationale, confidence, contact block with explicit email
status, warm paths, outreach angle, sources); rest as compact ranked rows;
caveats; collapsible raw JSON to make the schema contract visible.

## Remaining open questions

- Confirm the survey answers above with Adam/Carrie — especially practice-area
  defaults and what contact channels she'll actually use.
- LinkedIn access model: her logged-in browsing vs. public pages only — this
  gates data quality and needs a deliberate choice.
- Relationship to backgrounder: natural pipeline is target-contact → pick one →
  backgrounder them. Share source conventions? Sheet-as-record?
- Feedback loop: capture "redirected to colleague X" outcomes to improve
  ranking?

## Log

- 2026-09-09 — Doc created from Adam's notes. Name chosen: **target-contact**.
- 2026-09-09 — Researched Carrie (public web); answered survey first-pass;
  drafted input/output schema; built results-card mock (Cliff's direction:
  ranked list + decorated top entries, schema-backed, templatized UI).
- 2026-09-09 — Moved everything into `docs/target-contact/`. Added core
  formulation ("who at X owns Y, given Z") and the workflow requirement that
  step 1 is building the seeker's bio, since Z conditions the answer — the
  same X and Y can resolve to different people for different Z's.
