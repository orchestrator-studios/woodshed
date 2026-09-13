"""Hook transmitter — W1 of Ledger Phase 1 (docs/ledger/phase-1-sessions.html).

Claude Code lifecycle hooks pipe their JSON payload here on stdin; this script
forwards it as one signal to the BotBeam ledger service:

    POST {base_url}/ledger/sessions/{session_id}/signals
    { "signal": <hook name>, "cwd": ..., "machine": ..., "tool": {"name": ...} }

A signal is not a record Event: it is a mechanical observation that updates
columns on the session row and is never stored as a row of its own.

Contract (The Ledger Book, Hooks panel): a sensor, not a judge. It classifies
nothing — the mutating-tool list is service policy — holds no state beyond a
debounce stamp, and NEVER blocks a session: every path exits 0. A dead or slow
service drops the signal; since rev 18 statuses are stored, so a dropped
signal leaves a stale status until the next one lands.

Debounce (PostToolUse only): facts are max-timestamps, so posts inside a burst
carry no new information. A non-mutating tool post is pure heartbeat — skip it
if anything was posted in the last DEBOUNCE_SECS. A mutating tool also feeds
last_run_at, so it debounces only against the last *mutating* post — the first
Edit after a quiet stretch of Reads still lands instantly and lights the bolt.

Credentials: ~/.config/orchestra/botbeam.json → {"base_url": ..., "token": ...}.
"""
import json
import os
import sys
import time
import urllib.request

DEBOUNCE_SECS = 60          # half the service's run window (120s)
TIMEOUT_SECS = 10           # generous — hooks run async, so nothing waits on us
MUTATING = {"Write", "Edit", "NotebookEdit", "Bash", "PowerShell"}  # debounce classes only — the service owns policy


def main() -> None:
    payload = json.load(sys.stdin)
    sid = payload.get("session_id")
    event = payload.get("hook_event_name")
    if not sid or not event:
        return

    tool_name = payload.get("tool_name")
    if event == "PostToolUse" and _debounced(sid, tool_name):
        return

    cfg_path = os.path.expanduser("~/.config/orchestra/botbeam.json")
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)

    body = {
        "signal": event,
        "cwd": payload.get("cwd"),
        "machine": os.environ.get("COMPUTERNAME") or __import__("platform").node(),
    }
    if tool_name:
        body["tool"] = {"name": tool_name}

    req = urllib.request.Request(
        f"{cfg['base_url']}/ledger/sessions/{sid}/signals",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg['token']}",
        },
        method="POST",
    )
    urllib.request.urlopen(req, timeout=TIMEOUT_SECS).read()
    if event == "PostToolUse":
        _stamp(sid, tool_name)


def _stamp_path(sid: str) -> str:
    d = os.path.join(os.environ.get("TEMP") or "/tmp", "ledger-hook")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{sid}.json")


def _read_stamp(sid: str) -> dict:
    try:
        with open(_stamp_path(sid), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _debounced(sid: str, tool_name) -> bool:
    st = _read_stamp(sid)
    now = time.time()
    if tool_name in MUTATING:
        return now - st.get("run", 0) < DEBOUNCE_SECS
    return now - st.get("any", 0) < DEBOUNCE_SECS


def _stamp(sid: str, tool_name) -> None:
    st = _read_stamp(sid)
    st["any"] = time.time()
    if tool_name in MUTATING:
        st["run"] = st["any"]
    with open(_stamp_path(sid), "w", encoding="utf-8") as f:
        json.dump(st, f)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # a hook must never block or noise a session
    sys.exit(0)
