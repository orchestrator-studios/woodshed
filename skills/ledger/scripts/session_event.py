"""Hook transmitter — the telemetry plane's sensor (The Ledger Book, Hooks panel).

Claude Code lifecycle hooks pipe their JSON payload here on stdin; this script
forwards it as one signal to the BotBeam ledger service:

    POST {base_url}/ledger/sessions/{session_id}/signals
    { "signal": <hook name>, "cwd": ..., "machine": ... }

A signal is not a record Event: it is a mechanical observation that updates
columns on the session row and is never stored as a row of its own.

Contract: a sensor, not a judge. It classifies nothing, holds no state beyond a
debounce stamp, and NEVER blocks a session: every path exits 0. A dead or slow
service drops the signal; since rev 18 statuses are stored, so a dropped signal
leaves a stale status until the next one lands.

Rev 21: PostToolUse is a PURE HEARTBEAT. The tool payload is gone — it existed
only to feed the mutating-tool classification behind the old run bolt, and that
bolt is deleted (a run is now a declared record-plane object, not a state
inferred from a decaying timestamp). The hook is kept because it holds
last_event_at fresh through a long turn, and the deferred crash repair will
need an in-turn liveness signal to tell "crashed mid-run" from "long build".

Debounce (PostToolUse only): facts are max-timestamps, so posts inside a burst
carry no new information. With nothing left to classify, every PostToolUse
debounces the same way — skip it if anything was posted in the last
DEBOUNCE_SECS.

Credentials: ~/.config/orchestra/botbeam.json → {"base_url": ..., "token": ...}.
"""
import json
import os
import sys
import time
import urllib.request

DEBOUNCE_SECS = 60          # heartbeat cadence; no longer tied to any service window
TIMEOUT_SECS = 10           # generous — hooks run async, so nothing waits on us


def main() -> None:
    payload = json.load(sys.stdin)
    sid = payload.get("session_id")
    event = payload.get("hook_event_name")
    if not sid or not event:
        return

    if event == "PostToolUse" and _debounced(sid):
        return

    cfg_path = os.path.expanduser("~/.config/orchestra/botbeam.json")
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)

    body = {
        "signal": event,
        "cwd": payload.get("cwd"),
        "machine": os.environ.get("COMPUTERNAME") or __import__("platform").node(),
    }

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
        _stamp(sid)


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


def _debounced(sid: str) -> bool:
    return time.time() - _read_stamp(sid).get("any", 0) < DEBOUNCE_SECS


def _stamp(sid: str) -> None:
    with open(_stamp_path(sid), "w", encoding="utf-8") as f:
        json.dump({"any": time.time()}, f)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # a hook must never block or noise a session
    sys.exit(0)
