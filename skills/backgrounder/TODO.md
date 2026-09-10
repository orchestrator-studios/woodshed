# Backgrounder — working notes (Cliff + Claude)

## Fix: deterministic sheet write path (from the 2026-09-04 live run)

The skill has no defined write path to the sheet; each run improvises gws CLI
calls. On Windows this corrupted data in transit (cmd.exe `.cmd` shim ate the
`&` in the "Contact & Bio" range argument), the Sheets API rejected the call,
and the run continued cleanly — the write script never checked for an error
field or exit code. Sheet ended a tab short with no failure reported.

Fix, one script (`scripts/build_sheet.py` or similar):
- Takes rows as a JSON file (no data through shell argv — content must never
  travel as shell syntax).
- Creates skeleton (tabs, headers, formatting) and writes rows; talks to the
  API directly (bearer token or batch endpoint), not through the `.cmd` shim.
- Checks every response; fails loudly.
- Closing audit: read the sheet back, compare mention rows / message ids
  against corpus.json, confirm no tab is empty.

Related (Adam's backlog #1): same direct-API move fixes fetch_corpus.py
per-message subprocess overhead. One shared gws-auth helper serves both.
