# Learnings

What the skill picked up on past jobs and has not yet folded into SKILL.md or
tells.py. Read this before starting a job. Append to it at the end of a job if
something was learned. Entries are short: one line each.

## Candidate tells

Voice patterns seen on a job that no list in SKILL.md or tells.py covers. One per
line, in this shape:

```
- `regex` — YYYY-MM-DD, document — "example sentence"
```

tells.py loads every backticked regex in this section into its `candidate`
category, so a pattern starts firing on the next job without touching the script.

Promotion rule: when a candidate fires again on a second job, move it into the
right list in SKILL.md and the matching regex in tells.py, then delete it here.
If it has sat here through five jobs without recurring, delete it.

<!-- candidates start -->
<!-- candidates end -->

## Corrections

Things the pass did wrong and the user caught: a fact cut, a domain term reworded,
a heading that should have stayed. One per line:

```
- YYYY-MM-DD, document — what went wrong — what to do instead
```

If a correction describes a general rule rather than a one-off, move it into
"What not to touch" or the relevant pass in SKILL.md and delete it here.

<!-- corrections start -->
<!-- corrections end -->
