# woodshed

The Orchestrator Studios practice room: where skills, tools, and experiments get
worked up before they're ready to perform. When something matures, it graduates —
into [orchestra](https://github.com/orchestrator-studios/orchestra) or its own repo.

Shared workspace for Cliff and Adam.

## Layout

| Directory | What goes there |
| --- | --- |
| `skills/` | Claude skills in development. One folder per skill, with its `SKILL.md`, scripts, assets, evals — and a `HANDOFF.md` if it's mid-collaboration. |
| `tools/` | Standalone scripts and CLIs that aren't skills. |
| `experiments/` | Prototypes and scratch work not yet worth a name. |

## What's here now

- **skills/backgrounder** — researches a person across Gmail, Calendar, and the
  public web; builds a multi-tab Google Sheet as the auditable record, then renders
  a one-screen HTML brief strictly from the sheet. From Adam, Sept 2026; current
  work is wall-clock optimization — see its `HANDOFF.md` for the backlog.

## Conventions

- Skills follow the standard layout (`SKILL.md` + `scripts/`, `references/`,
  `assets/`, `evals/`) so a folder can be dropped into `~/.claude/skills/` as-is.
- Keep handoff/working notes next to the thing they describe, not in a shared docs pile.
- No secrets in the repo — credentials live in env vars or per-identity config dirs
  (e.g. `GOOGLE_WORKSPACE_CLI_CONFIG_DIR` for `gws`).
