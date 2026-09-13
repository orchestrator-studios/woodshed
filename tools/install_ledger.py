"""Deploy the ledger skill from this clone onto this machine.

The repo is the source; ~/.claude and ~/.config are the runtime. A clone gives
you the skill's *files* and none of the four things that make them run: the
junction that lets Claude Code find the skill, the hook registration, the
credentials, and the CLAUDE.md standing duty. This script installs all four and
can verify them.

    python tools/install_ledger.py            # install / repair (idempotent)
    python tools/install_ledger.py --verify   # report only, change nothing

Written in Python rather than PowerShell because python is already a hard
dependency — every hook shells to it — and because the settings.json merge is
field-level, which PowerShell 5.1's PSCustomObject makes needlessly painful.

Windows only for the junction step (mklink /J); the rest is portable, and on a
POSIX box a symlink would stand in.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_SRC = os.path.join(REPO, "skills", "ledger")
INSTALL_SRC = os.path.join(SKILL_SRC, "install")

HOME = os.path.expanduser("~")
SKILL_DST = os.path.join(HOME, ".claude", "skills", "ledger")
SETTINGS = os.path.join(HOME, ".claude", "settings.json")
CLAUDE_MD = os.path.join(HOME, ".claude", "CLAUDE.md")
CREDS = os.path.join(HOME, ".config", "orchestra", "botbeam.json")
BACKUPS = os.path.join(HOME, ".claude", "backups")

STANZA_MARKER = "## Global work ledger"
HOOK_FINGERPRINT = "skills/ledger/scripts"   # identifies OUR hook entries, old paths included

OK, WARN, BAD = "  ok  ", " warn ", " FAIL "

try:
    sys.stdout.reconfigure(encoding="utf-8")   # cp1252 consoles mangle the report
except Exception:
    pass


class Report:
    def __init__(self):
        self.rows = []
        self.failed = False

    def add(self, level, what, detail=""):
        self.rows.append((level, what, detail))
        if level == BAD:
            self.failed = True

    def render(self):
        print()
        for level, what, detail in self.rows:
            print("[%s] %-22s %s" % (level, what, detail))
        print()


# --------------------------------------------------------------------------
# 1. the junction — ~/.claude/skills/ledger IS this clone


def _is_link(path):
    return os.path.isdir(path) and os.path.islink(path) or _is_junction(path)


def _is_junction(path):
    if not os.path.isdir(path):
        return False
    try:
        return bool(os.readlink(path))
    except OSError:
        return False


def _link_target(path):
    try:
        return os.path.realpath(path)
    except OSError:
        return None


def do_junction(rep, verify):
    if _is_junction(SKILL_DST):
        target = _link_target(SKILL_DST)
        if os.path.normcase(target) == os.path.normcase(SKILL_SRC):
            rep.add(OK, "junction", "-> %s" % target)
            return
        if verify:
            rep.add(BAD, "junction", "points at %s, expected %s" % (target, SKILL_SRC))
            return
        os.rmdir(SKILL_DST)
        rep.add(WARN, "junction", "repointed from %s" % target)
    elif os.path.exists(SKILL_DST):
        if verify:
            rep.add(BAD, "junction", "%s is a real directory, not a link" % SKILL_DST)
            return
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        os.makedirs(BACKUPS, exist_ok=True)
        moved = os.path.join(BACKUPS, "ledger-prejunction-%s" % stamp)
        shutil.move(SKILL_DST, moved)
        rep.add(WARN, "junction", "existing copy moved to %s" % moved)
    elif verify:
        rep.add(BAD, "junction", "missing")
        return

    if verify:
        return
    os.makedirs(os.path.dirname(SKILL_DST), exist_ok=True)
    r = subprocess.run(["cmd", "/c", "mklink", "/J", SKILL_DST, SKILL_SRC],
                       capture_output=True, text=True)
    if r.returncode != 0:
        rep.add(BAD, "junction", r.stderr.strip() or r.stdout.strip())
    else:
        rep.add(OK, "junction", "created -> %s" % SKILL_SRC)


# --------------------------------------------------------------------------
# 2. the hook registration — spliced by key, never overwriting settings.json


def _ours(entry):
    """True if this hook entry belongs to the ledger skill (any path vintage)."""
    for h in entry.get("hooks", []):
        if HOOK_FINGERPRINT in h.get("command", "").replace("\\", "/"):
            return True
    return False


def do_hooks(rep, verify):
    want = json.load(open(os.path.join(INSTALL_SRC, "hooks.json"), encoding="utf-8"))
    want = {k: v for k, v in want.items() if not k.startswith("_")}

    if not os.path.exists(SETTINGS):
        if verify:
            rep.add(BAD, "hooks", "no settings.json")
            return
        settings = {}
    else:
        settings = json.load(open(SETTINGS, encoding="utf-8"))

    live = settings.get("hooks", {})
    stale = []
    for event, blocks in want.items():
        current = [e for e in live.get(event, []) if _ours(e)]
        if current != blocks:
            stale.append(event)

    if not stale:
        rep.add(OK, "hooks", "all %d events registered, paths current" % len(want))
        return
    if verify:
        rep.add(BAD, "hooks", "stale or missing: %s" % ", ".join(stale))
        return

    for event, blocks in want.items():
        others = [e for e in live.get(event, []) if not _ours(e)]
        live[event] = others + blocks
    settings["hooks"] = live

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    os.makedirs(BACKUPS, exist_ok=True)
    if os.path.exists(SETTINGS):
        shutil.copy2(SETTINGS, os.path.join(BACKUPS, "settings-%s.json" % stamp))
    with open(SETTINGS, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    rep.add(OK, "hooks", "wrote %s (backup in ~/.claude/backups)" % ", ".join(stale))


# --------------------------------------------------------------------------
# 3. the standing duty in ~/.claude/CLAUDE.md


def do_claude_md(rep, verify):
    stanza = open(os.path.join(INSTALL_SRC, "claude-md.md"), encoding="utf-8").read()
    body = ""
    if os.path.exists(CLAUDE_MD):
        body = open(CLAUDE_MD, encoding="utf-8").read()

    if STANZA_MARKER in body:
        rep.add(OK, "CLAUDE.md stanza", "present")
        return
    if verify:
        rep.add(BAD, "CLAUDE.md stanza", "missing — sessions will not know to log")
        return

    os.makedirs(os.path.dirname(CLAUDE_MD), exist_ok=True)
    with open(CLAUDE_MD, "a", encoding="utf-8") as f:
        if body and not body.endswith("\n\n"):
            f.write("\n")
        f.write(stanza)
    rep.add(OK, "CLAUDE.md stanza", "appended")


# --------------------------------------------------------------------------
# 4. credentials — never generated, only shaped


def do_creds(rep, verify):
    if os.path.exists(CREDS):
        try:
            cfg = json.load(open(CREDS, encoding="utf-8"))
        except Exception as e:
            rep.add(BAD, "credentials", "unreadable: %s" % e)
            return None
        if not cfg.get("base_url") or not cfg.get("token"):
            rep.add(BAD, "credentials", "missing base_url or token")
            return None
        if "PASTE" in cfg["token"]:
            rep.add(BAD, "credentials", "still the template — paste the agent token")
            return None
        rep.add(OK, "credentials", cfg["base_url"])
        return cfg

    if verify:
        rep.add(BAD, "credentials", "missing %s" % CREDS)
        return None

    os.makedirs(os.path.dirname(CREDS), exist_ok=True)
    shutil.copy2(os.path.join(INSTALL_SRC, "botbeam.example.json"), CREDS)
    rep.add(WARN, "credentials", "template written to %s — paste the token" % CREDS)
    return None


# --------------------------------------------------------------------------
# 5. the service — the other half of the contract


def do_service(rep, cfg):
    if not cfg:
        rep.add(WARN, "service", "skipped (no credentials)")
        return
    try:
        req = urllib.request.Request(
            cfg["base_url"] + "/health",
            headers={"Authorization": "Bearer %s" % cfg["token"]})
        health = json.load(urllib.request.urlopen(req, timeout=10))
        rep.add(OK, "service", "v%s at %s" % (health.get("version", "?"), cfg["base_url"]))
    except Exception as e:
        rep.add(BAD, "service", "unreachable: %s" % e)


# --------------------------------------------------------------------------
# 6. the failure log — the only evidence the silent plane leaves


def do_hooklog(rep):
    sys.path.insert(0, os.path.join(SKILL_SRC, "scripts"))
    try:
        import hooklog
    except Exception as e:
        rep.add(WARN, "hook failures", "hooklog unavailable: %s" % e)
        return
    errs = hooklog.recent(24)
    if not errs:
        rep.add(OK, "hook failures", "none in 24h")
        return
    rep.add(BAD, "hook failures", "%d in 24h — latest: %s" % (len(errs), errs[-1]))
    print("\n  %s" % hooklog.path())
    for line in errs[-5:]:
        print("    %s" % line)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verify", action="store_true",
                    help="report only; change nothing")
    args = ap.parse_args()

    print("repo:    %s" % REPO)
    print("runtime: %s" % os.path.join(HOME, ".claude"))
    print("mode:    %s" % ("verify" if args.verify else "install"))

    rep = Report()
    do_junction(rep, args.verify)
    do_hooks(rep, args.verify)
    do_claude_md(rep, args.verify)
    cfg = do_creds(rep, args.verify)
    do_service(rep, cfg)
    do_hooklog(rep)
    rep.render()

    if rep.failed:
        print("Not fully deployed." if args.verify else "Install incomplete — see FAIL rows.")
        return 1
    print("Ledger skill deployed. New sessions pick it up; open ones keep what they loaded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
