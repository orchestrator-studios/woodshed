"""Session-start orientation.

The SessionStart hook runs this and Claude Code injects whatever it prints into
the new session's context. It fetches the one-screen "what's going on" the
ledger service renders from both planes:

    GET {base_url}/ledger/index   ->   text/markdown

A client, not an author: it renders nothing, caches nothing, and holds no
state. If the service is unreachable it prints nothing and exits 0 — a session
must never be blocked or noised by orientation.

Credentials: ~/.config/orchestra/botbeam.json -> {"base_url": ..., "token": ...}
"""
import json
import os
import sys
import urllib.request

TIMEOUT_SECS = 10


def main() -> None:
    cfg_path = os.path.expanduser("~/.config/orchestra/botbeam.json")
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)

    req = urllib.request.Request(
        f"{cfg['base_url']}/ledger/index",
        headers={"Authorization": f"Bearer {cfg['token']}"},
    )
    body = urllib.request.urlopen(req, timeout=TIMEOUT_SECS).read().decode("utf-8")
    if body.strip():
        sys.stdout.write(body)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # orientation is best-effort; never block or noise a session
    sys.exit(0)
