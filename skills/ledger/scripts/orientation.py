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

import hooklog

TIMEOUT_SECS = 10
ALARM_WINDOW_HOURS = 24

# Windows consoles default to cp1252, which cannot encode the em dashes and
# glyphs the service's markdown uses — the write raises and the whole
# orientation is lost, or arrives mojibaked. Claude Code reads this pipe as
# utf-8, so say so.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


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


def alarm() -> None:
    """Surface hook failures into this session — the only moment anyone looks.

    The hook plane is silent by construction, so a broken transmitter is
    indistinguishable from a quiet day. This is the one channel that reaches a
    human and a session unprompted, so the failure log is read back here.
    Prints nothing when there is nothing wrong.
    """
    errs = hooklog.recent(ALARM_WINDOW_HOURS)
    if not errs:
        return
    # Deliberately ASCII: this text must survive any console codepage. The
    # first version used a warning glyph, which raised on cp1252 and was eaten
    # by the very swallow it exists to report.
    sys.stdout.write(
        "\n---\n\n**WARNING - ledger hooks failed %d time(s) in the last %dh.** "
        "The board may be missing signals; nothing else will say so.\n\n"
        "Most recent:\n\n```\n%s\n```\n\n"
        "Full log: `%s`. Check the plumbing with "
        "`python tools/install_ledger.py --verify` (in C:\\code\\woodshed).\n"
        % (len(errs), ALARM_WINDOW_HOURS, "\n".join(errs[-3:]), hooklog.path())
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        hooklog.log("SessionStart/orientation", exc)
    try:
        alarm()
    except Exception:
        pass  # orientation is best-effort; never block or noise a session
    sys.exit(0)
