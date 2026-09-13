"""Local failure log for the hook plane — the counterweight to silence.

Hooks must never block or noise a session, so every path in this skill swallows
its exceptions and exits 0. That is right for production and hostile to
diagnosis: a dropped signal looks exactly like a quiet day, and "Claude didn't
log it" looks exactly like "the plumbing broke."

So the swallow writes here first. One line per failure, local file, no network:

    %TEMP%\\ledger-hook\\errors.log

Nothing reads this at failure time — the point is that `orientation.py`
surfaces it into the next session's context, and `install_ledger.py --verify`
reports it. A log nobody reads is worse than no log, because it looks like
diligence.

Local-only by design: the most common failure is "the service is unreachable,"
which is precisely when you cannot report a failure to the service.
"""
import os
import time

MAX_LINES = 200          # bounded: this is a tail, not an archive


def _dir():
    d = os.path.join(os.environ.get("TEMP") or "/tmp", "ledger-hook")
    os.makedirs(d, exist_ok=True)
    return d


def path():
    return os.path.join(_dir(), "errors.log")


def log(context, exc):
    """Append one failure. Never raises — this runs inside an except block."""
    try:
        line = "%s\t%s\t%s: %s\n" % (
            time.strftime("%Y-%m-%dT%H:%M:%S"), context,
            type(exc).__name__, str(exc)[:200].replace("\n", " "))
        p = path()
        try:
            with open(p, encoding="utf-8") as f:
                lines = f.readlines()[-(MAX_LINES - 1):]
        except Exception:
            lines = []
        with open(p, "w", encoding="utf-8") as f:
            f.writelines(lines)
            f.write(line)
    except Exception:
        pass  # a failure to record a failure is not worth a second failure


def recent(hours=24):
    """Failures within the window, newest last. Never raises."""
    try:
        cutoff = time.strftime("%Y-%m-%dT%H:%M:%S",
                               time.localtime(time.time() - hours * 3600))
        with open(path(), encoding="utf-8") as f:
            return [ln.rstrip("\n") for ln in f if ln[:19] >= cutoff]
    except Exception:
        return []


def clear():
    try:
        os.remove(path())
    except Exception:
        pass
