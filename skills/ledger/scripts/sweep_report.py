"""Sweep reporter — W3 of Ledger Phase 1 (docs/ledger/phase-1-sessions.html).

Runs on a schedule (every 5 minutes, task LedgerSweepReport). For each session
the ledger service knows on THIS machine, observes whether its Claude Code
transcript still exists on disk, and posts the observations:

    POST {base_url}/ledger/sessions/sweep-report
    { "machine": ..., "observed": [ {"session_id": ..., "transcript_present": bool}, ... ] }

The service owns the expiry rule (N consecutive misses with no events since);
this script observes and reports, nothing more. Transcripts are read-only to it.
A dead service or empty session list is a silent no-op — the next run corrects.
"""
import glob
import json
import os
import sys
import urllib.parse
import urllib.request

TIMEOUT_SECS = 15


def main() -> None:
    cfg_path = os.path.expanduser("~/.config/orchestra/botbeam.json")
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)
    machine = os.environ.get("COMPUTERNAME") or __import__("platform").node()
    headers = {"Authorization": f"Bearer {cfg['token']}", "Content-Type": "application/json"}

    req = urllib.request.Request(
        f"{cfg['base_url']}/ledger/sessions?machine={urllib.parse.quote(machine)}",
        headers=headers)
    sessions = json.load(urllib.request.urlopen(req, timeout=TIMEOUT_SECS))["items"]
    if not sessions:
        return

    projects = os.path.expanduser("~/.claude/projects")
    observed = [{
        "session_id": s["id"],
        "transcript_present": bool(glob.glob(os.path.join(projects, "*", s["id"] + ".jsonl"))),
    } for s in sessions]

    body = json.dumps({"machine": machine, "observed": observed}).encode()
    req = urllib.request.Request(
        f"{cfg['base_url']}/ledger/sessions/sweep-report",
        data=body, headers=headers, method="POST")
    urllib.request.urlopen(req, timeout=TIMEOUT_SECS).read()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # scheduled observer: fail silent, next run corrects
    sys.exit(0)
