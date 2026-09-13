"""Ledger board engine.

Maintains the session store (sessions/<id>.json) from Claude Code hook
events and beams the live board to a BotBeam display.

Invoked two ways:
  - As a Claude Code hook (JSON event on stdin): updates the presence store,
    recomputes the board, beams to BotBeam only when semantic state changed.
  - As a CLI:  presence.py list | archive <sid-prefix> | unarchive <sid-prefix>
               | beam (force re-beam) | sweep (TTL decay pass, for a scheduled task)

Terminology (glossary rev 2): a session is ACTIVE while a turn is in flight
(heartbeat within ACTIVE_TTL); a RUN is processing toward a mutation, signaled
by Write/Edit/NotebookEdit tool use (bolt decays after RUN_TTL). Relevant =
not archived; only relevant sessions appear on the board.
"""
import json
import os
import platform
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta

ROOT = os.path.join(os.path.expanduser("~"), "claude-memory")
SESS_DIR = os.path.join(ROOT, "sessions")
CONFIG = os.path.join(ROOT, "config", "board.json")
STREAM_PATHS = os.path.join(ROOT, "config", "stream-paths.json")
LASTBEAM = os.path.join(ROOT, "views", ".last-beam.json")
BB_CACHE = os.path.join(ROOT, "config", "botbeam-cache.json")  # lockbox name -> id
MACHINE = platform.node().lower()

DEFAULTS = {
    "botbeam_script": "C:/code/orchestra/plugins/orchestra/skills/botbeam/scripts/botbeam.py",
    "botbeam_device": "",
    "active_ttl_min": 10,
    "run_ttl_min": 10,
    "events_shown": 5,
}
RUN_TOOLS = {"Write", "Edit", "NotebookEdit"}
SHELL_TOOLS = {"Bash", "PowerShell"}
# read-only shell commands: a Bash/PowerShell call is a run UNLESS every
# segment starts with one of these (default-mutating heuristic, glossary Q3)
READONLY_CMDS = {
    "ls", "dir", "cat", "type", "head", "tail", "grep", "rg", "find", "echo",
    "pwd", "cd", "which", "where", "wc", "sort", "uniq", "jq", "sleep", "true",
    "test", "file", "stat", "du", "df", "ps", "whoami", "date", "env",
    "printenv", "history", "diff", "tree", "less", "more",
    "get-childitem", "get-content", "get-item", "select-object", "select-string",
    "measure-object", "get-command", "get-process", "write-output",
}
GIT_READONLY = {"status", "log", "diff", "show", "branch", "shortlog", "blame",
                "ls-files", "remote", "describe", "rev-parse", "config"}


def shell_is_run(command):
    """True if any segment of the shell command looks mutating."""
    if not command:
        return False
    for seg in re.split(r"[;&|]+|&&|\|\|", command):
        words = seg.strip().split()
        if not words:
            continue
        head = words[0].lower().rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        # output redirection mutates even from a read-only command
        # (stderr-discard forms like 2>/dev/null don't count)
        cleaned = re.sub(r"2>&1|2?>+\s*(/dev/null|nul\b)", "", seg, flags=re.I)
        if ">" in cleaned or re.search(r"\btee\b", cleaned):
            return True
        if head in READONLY_CMDS:
            continue
        if head == "git" and len(words) > 1 and words[1].lower() in GIT_READONLY:
            continue
        return True
    return False


def load_json(path, fallback):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return fallback


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def now():
    return datetime.now()


def iso(dt):
    return dt.isoformat(timespec="seconds")


def parse_iso(s):
    try:
        return datetime.fromisoformat(s)
    except (TypeError, ValueError):
        return None


def config():
    cfg = dict(DEFAULTS)
    cfg.update(load_json(CONFIG, {}))
    return cfg


# ---------- BotBeam lockbox store (system of record, phase 1: sessions) ----------

def bb_creds():
    c = load_json(os.path.join(os.path.expanduser("~"), ".config", "orchestra",
                               "botbeam.json"), {})
    base = os.environ.get("BOTBEAM_BASE_URL", c.get("base_url"))
    tok = os.environ.get("BOTBEAM_TOKEN", c.get("token"))
    return (base.rstrip("/"), tok) if base and tok else None


def bb_api(method, path, body=None):
    creds = bb_creds()
    if not creds:
        return None
    base, tok = creds
    req = urllib.request.Request(
        base + path, method=method,
        headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"},
        data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read()
            return json.loads(data) if data else {}
    except Exception:
        return None


def bb_session_name(sid):
    return "ledger:session:" + sid[:8]


def push_session(s):
    """Write-through: mirror a session record to its BotBeam lockbox."""
    if bb_creds() is None:
        return
    name = bb_session_name(s["session_id"])
    content = {"type": "json", "body": json.dumps(s)}
    cache = load_json(BB_CACHE, {})
    dev_id = cache.get(name)
    if dev_id and bb_api("PUT", f"/api/devices/{dev_id}/content", content) is not None:
        return
    made = bb_api("POST", "/api/devices", {
        "name": name, "kind": "lockbox",
        "description": f"ledger session record ({s['label']})", "content": content})
    if made and made.get("id"):
        cache[name] = made["id"]
        save_json(BB_CACHE, cache)
        return
    # create failed (likely name exists from another day/cache loss): re-list
    lst = bb_api("GET", "/api/devices?kind=lockbox&view=summary") or []
    for d in lst:
        if d.get("name", "").startswith("ledger:session:"):
            cache[d["name"]] = d["id"]
    save_json(BB_CACHE, cache)
    dev_id = cache.get(name)
    if dev_id:
        bb_api("PUT", f"/api/devices/{dev_id}/content", content)


def fetch_remote_sessions():
    """All machines' session records from BotBeam lockboxes, keyed by session_id."""
    if bb_creds() is None:
        return {}
    out = {}
    cache = load_json(BB_CACHE, {})
    dirty = False
    for d in bb_api("GET", "/api/devices?kind=lockbox&view=summary") or []:
        if not d.get("name", "").startswith("ledger:session:"):
            continue
        if cache.get(d["name"]) != d["id"]:
            cache[d["name"]] = d["id"]
            dirty = True
        full = bb_api("GET", f"/api/devices/{d['id']}")
        try:
            rec = json.loads((full or {}).get("content", {}).get("body", ""))
            if rec.get("session_id"):
                out[rec["session_id"]] = rec
        except (ValueError, AttributeError):
            continue
    if dirty:
        save_json(BB_CACHE, cache)
    return out


def merged_sessions():
    """Local records merged with all machines' lockbox records; newest wins."""
    combined = {}
    for s in load_sessions():
        combined[s["session_id"]] = s
    for sid, rec in fetch_remote_sessions().items():
        cur = combined.get(sid)
        if cur is None or (rec.get("last_active") or "") > (cur.get("last_active") or ""):
            combined[sid] = rec
    return list(combined.values())


# ---------- presence store ----------

def session_path(sid):
    return os.path.join(SESS_DIR, sid + ".json")


def load_sessions():
    out = []
    if not os.path.isdir(SESS_DIR):
        return out
    for name in os.listdir(SESS_DIR):
        if name.endswith(".json"):
            s = load_json(os.path.join(SESS_DIR, name), None)
            if s:
                out.append(s)
    return out


def match_stream(paths_to_check):
    """Map any of the given filesystem paths to a declared stream."""
    mapping = load_json(STREAM_PATHS, {})
    for p in paths_to_check:
        if not p:
            continue
        norm = os.path.normcase(os.path.normpath(p))
        for stream, roots in mapping.items():
            for root in roots:
                r = os.path.normcase(os.path.normpath(os.path.expanduser(root)))
                if norm == r or norm.startswith(r + os.sep):
                    return stream
    return None


def handle_event(evt):
    sid = evt.get("session_id")
    if not sid:
        return
    event = evt.get("hook_event_name", "")
    cwd = evt.get("cwd", "")
    s = load_json(session_path(sid), None) or {
        "session_id": sid,
        "label": (os.path.basename(cwd.rstrip("\\/")) or "home") + " · " + sid[:6],
        "cwd": cwd,
        "stream": None,
        "state": "idle",
        "machine": MACHINE,
        "first_seen": iso(now()),
        "last_active": None,
        "last_run": None,
        "archived": False,
    }
    s.setdefault("machine", MACHINE)
    t = iso(now())
    s["open"] = True  # any hook event means Claude is open on this session
    if event == "SessionStart":
        s["state"] = "idle"
        s["last_active"] = t
    elif event == "UserPromptSubmit":
        s["state"] = "active"
        s["last_active"] = t
    elif event == "Stop":
        s["state"] = "idle"
        s["last_active"] = t
    elif event == "SessionEnd":
        s["state"] = "idle"
        s["open"] = False
        s["last_active"] = t
    elif event == "PostToolUse":
        tool = evt.get("tool_name")
        ti = evt.get("tool_input") or {}
        is_run = (tool in RUN_TOOLS
                  or (tool in SHELL_TOOLS and shell_is_run(ti.get("command", ""))))
        if tool in RUN_TOOLS or tool in SHELL_TOOLS:
            s["state"] = "active"
            s["last_active"] = t
            if is_run:
                s["last_run"] = t
            s["stream"] = match_stream([ti.get("file_path", ""), cwd]) or s.get("stream")
    if not s.get("stream"):
        s["stream"] = match_stream([cwd])
    # archived is a kind of closed: any hook event means the session is open,
    # which un-archives it (resume reopens; see data model rev 11)
    s["archived"] = False
    save_json(session_path(sid), s)
    push_session(s)


# ---------- board ----------

def board_state(cfg):
    """Semantic board state: what the display should show, minus timestamps."""
    t = now()
    active_ttl = timedelta(minutes=cfg["active_ttl_min"])
    run_ttl = timedelta(minutes=cfg["run_ttl_min"])
    attach_ttl = timedelta(hours=cfg.get("attach_ttl_hours", 12))
    cards = []
    sessions = merged_sessions()
    labels = {s["session_id"][:6].lower(): s["label"] for s in sessions}
    for s in sorted(sessions, key=lambda x: x.get("last_active") or "", reverse=True):
        if s.get("archived") or s.get("expired"):
            continue
        la, lr = parse_iso(s.get("last_active")), parse_iso(s.get("last_run"))
        # crash backstop: an "open" session silent for attach_ttl renders closed
        is_open = bool(s.get("open")) and la is not None and (t - la) <= attach_ttl
        active = is_open and s.get("state") == "active" and (t - la) <= active_ttl
        run = active and lr is not None and (t - lr) <= run_ttl
        cards.append({
            "label": s["label"],
            "stream": s.get("stream"),
            "machine": s.get("machine", "?"),
            "open": is_open,
            "active": active,
            "run": run,
            "last_active": s.get("last_active"),
        })
    return {"cards": cards, "labels": labels,
            "events": recent_events(cfg["events_shown"]),
            "products": recent_products()}


SID_TAG = re.compile(r"\s*\[sid:([0-9a-fA-F-]{4,})\]\s*")


def recent_events(limit):
    """Last N journal event headlines, newest first. Headlines may carry an
    optional [sid:xxxxxx] tag attributing the event to a session."""
    jdir = os.path.join(ROOT, "journal")
    events = []
    if not os.path.isdir(jdir):
        return events
    for name in sorted(os.listdir(jdir), reverse=True)[:7]:
        if not name.endswith(".md"):
            continue
        date = name[:-3]
        day = []
        try:
            with open(os.path.join(jdir, name), encoding="utf-8") as f:
                for line in f:
                    if line.startswith("## "):
                        headline = line[3:].strip()
                        m = SID_TAG.search(headline)
                        sid = m.group(1).lower() if m else None
                        day.append({"date": date, "sid": sid,
                                    "headline": SID_TAG.sub(" ", headline).strip()})
        except OSError:
            continue
        events.extend(reversed(day))  # newest entry in a day file is last
        if len(events) >= limit:
            break
    return events[:limit]


MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def recent_products(limit=5):
    """Last N rows of the work-product registry (artifacts/index.md)."""
    path = os.path.join(ROOT, "artifacts", "index.md")
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) >= 4 and re.match(r"\d{4}-\d{2}-\d{2}", cells[0]):
                    m = MD_LINK.search(cells[3])
                    rows.append({"date": cells[0], "stream": cells[1],
                                 "product": cells[2],
                                 "home_label": m.group(1) if m else cells[3],
                                 "home_url": m.group(2) if m else None})
    except OSError:
        pass
    return rows[:limit]  # registry is newest-first


def session_label_map():
    """sid prefix -> card label, for resolving event tags."""
    return {s["session_id"][:6].lower(): s["label"] for s in load_sessions()}


def render_html(state):
    # dark board: warm near-black ground, muted greens for life signs
    ink, ink2, muted = "#e8e6df", "#a5a39a", "#6f6d66"
    ground, card_bg = "#141613", "#1e211d"
    hairline = "rgba(255,255,255,0.09)"
    dot_on = "background:#2ecc55;box-shadow:0 0 8px rgba(46,204,85,.7);"
    dot_ring = "background:transparent;border:2px solid #2ecc55;width:6px;height:6px;"
    dot_off = "background:#4a4d47;"
    labels = state.get("labels") or session_label_map()
    cards = []
    for c in state["cards"]:
        bolt = ("<span style='font-size:15px' title='run in progress'>&#9889;</span>"
                if c["run"] else "")
        stream = (f"<div style='font-size:11px;color:#8ecfb3;margin-top:2px'>stream: {c['stream']}</div>"
                  if c["stream"] else
                  f"<div style='font-size:11px;color:{muted};margin-top:2px'>no stream</div>")
        seen = (c.get("last_active") or "never") + " · " + c.get("machine", "?")
        cards.append(
            f"<div style='border:1px solid {hairline};border-radius:8px;padding:10px 14px;"
            f"min-width:210px;background:{card_bg}'>"
            "<div style='display:flex;align-items:center;gap:8px'>"
            f"<span style='width:10px;height:10px;border-radius:50%;{dot_on if c['active'] else (dot_ring if c['open'] else dot_off)}'></span>"
            f"<span style='font-weight:600;font-size:14px;color:{ink}'>{c['label']}</span>{bolt}"
            f"</div>{stream}"
            f"<div style='font-size:10px;color:{muted};margin-top:4px;font-family:monospace'>last active {seen}</div>"
            "</div>")
    if not cards:
        cards.append(f"<div style='color:{ink2}'>No relevant sessions.</div>")
    ev_rows = []
    for e in state["events"]:
        who = labels.get((e.get("sid") or "")[:6])
        chip = (f"<span style='font-family:monospace;font-size:10px;color:#8ecfb3;"
                f"border:1px solid rgba(142,207,179,.35);border-radius:999px;"
                f"padding:1px 7px;margin:0 6px 0 4px'>{who or e.get('sid')[:6]}</span>"
                if e.get("sid") else
                f"<span style='font-family:monospace;font-size:10px;color:{muted};"
                f"margin:0 6px 0 4px'>&mdash;</span>")
        ev_rows.append(
            f"<li style='margin:4px 0;color:{ink2}'>"
            f"<span style='font-family:monospace;font-size:11px;color:{muted}'>{e['date']}</span>"
            f"{chip}<span style='color:{ink}'>{e['headline']}</span></li>")
    events = "".join(ev_rows) or f"<li style='color:{ink2}'>No recent events.</li>"
    prod_rows = []
    for p in state["products"]:
        link = (f"<a href='{p['home_url']}' style='color:#8ecfb3'>{p['home_label']}</a>"
                if p["home_url"] else f"<span style='color:{ink2}'>{p['home_label']}</span>")
        prod_rows.append(
            f"<li style='margin:4px 0'>"
            f"<span style='font-family:monospace;font-size:11px;color:{muted}'>{p['date']}</span> "
            f"<span style='color:{ink}'>{p['product']}</span> &middot; {link}</li>")
    products = "".join(prod_rows) or f"<li style='color:{ink2}'>No work products registered yet.</li>"
    return (
        # fill the whole display tab: darken the host page and stretch the board
        f"<style>html,body{{margin:0;padding:0;background:{ground}}}</style>"
        f"<div style='font-family:system-ui,sans-serif;color:{ink};background:{ground};"
        "padding:20px;min-height:100vh;box-sizing:border-box'>"
        f"<div style='font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:{ink2};"
        "margin-bottom:10px'>Sessions"
        f"<span style='float:right;font-family:monospace;text-transform:none;letter-spacing:0;color:{muted}'>{iso(now())}</span></div>"
        f"<div style='display:flex;flex-wrap:wrap;gap:10px'>{''.join(cards)}</div>"
        # events and work products side by side; columns wrap on narrow displays
        "<div style='display:flex;flex-wrap:wrap;gap:8px 28px;margin-top:16px'>"
        "<div style='flex:1 1 340px;min-width:0'>"
        f"<div style='font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:{ink2};"
        "margin:0 0 4px'>Recent events</div>"
        f"<ul style='margin:0;padding-left:18px;font-size:13px;list-style:none'>{events}</ul>"
        "</div>"
        "<div style='flex:1 1 340px;min-width:0'>"
        f"<div style='font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:{ink2};"
        "margin:0 0 4px'>Recent work products</div>"
        f"<ul style='margin:0;padding-left:18px;font-size:13px;list-style:none'>{products}</ul>"
        "</div>"
        "</div>"
        "</div>")


def semantic_key(state):
    """State that matters for diffing — excludes clocks so we don't beam every minute."""
    return json.dumps({
        "cards": [{k: c[k] for k in ("label", "stream", "machine", "open", "active", "run")} for c in state["cards"]],
        "events": state["events"],
        "products": state["products"],
    }, sort_keys=True)


def beam(cfg, force=False):
    state = board_state(cfg)
    key = semantic_key(state)
    if not force and load_json(LASTBEAM, {}).get("key") == key:
        return False
    if not cfg["botbeam_device"]:
        print("presence: no botbeam_device configured", file=sys.stderr)
        return False
    subprocess.run(
        [sys.executable, cfg["botbeam_script"], "existing",
         "--device", cfg["botbeam_device"], "--type", "html", "--body", render_html(state)],
        check=True, capture_output=True, timeout=30)
    save_json(LASTBEAM, {"key": key, "at": iso(now())})
    return True


# ---------- entry ----------

def survey(days=14):
    """Scan Claude Code transcripts for sessions seen in the last N days.

    Returns candidates not yet in the presence store: transcripts live at
    ~/.claude/projects/<sanitized-cwd>/<session-id>.jsonl; the dir name
    encodes the working directory, the file mtime is last activity.
    """
    proj = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    known = {s["session_id"] for s in load_sessions()}
    cutoff = now() - timedelta(days=days)
    out = []
    if not os.path.isdir(proj):
        return out
    for d in os.listdir(proj):
        ddir = os.path.join(proj, d)
        if not os.path.isdir(ddir):
            continue
        cwd_guess = d.replace("--", ":\\", 1).replace("-", "\\") if d[0].isupper() else d
        for f in os.listdir(ddir):
            if not f.endswith(".jsonl"):
                continue
            sid = f[:-6]
            if sid in known:
                continue
            mtime = datetime.fromtimestamp(os.path.getmtime(os.path.join(ddir, f)))
            if mtime >= cutoff:
                out.append({"session_id": sid, "cwd": cwd_guess, "last_seen": iso(mtime)})
    return sorted(out, key=lambda x: x["last_seen"], reverse=True)


def seed(candidates):
    """Create idle, relevant presence records for the given survey rows."""
    for c in candidates:
        base = os.path.basename(c["cwd"].rstrip("\\/")) or "home"
        rec = {
            "session_id": c["session_id"],
            "label": base + " · " + c["session_id"][:6],
            "cwd": c["cwd"],
            "stream": match_stream([c["cwd"]]),
            "state": "idle",
            "machine": MACHINE,
            "first_seen": c["last_seen"],
            "last_active": c["last_seen"],
            "last_run": None,
            "archived": False,
        }
        save_json(session_path(c["session_id"]), rec)
        push_session(rec)


def main():
    cfg = config()
    args = sys.argv[1:]
    if not args:  # hook mode
        try:
            evt = json.load(sys.stdin)
        except ValueError:
            return
        handle_event(evt)
        try:
            beam(cfg)
        except Exception as e:  # never break a session over a display
            print(f"presence: beam failed: {e}", file=sys.stderr)
        return
    cmd = args[0]
    if cmd == "list":
        for s in load_sessions():
            flag = ("expired" if s.get("expired")
                    else "archived" if s.get("archived")
                    else "open" if s.get("open") else "closed")
            print(f"{s['session_id'][:8]}  {flag:8}  {s.get('state','?'):6}  "
                  f"stream={s.get('stream')}  {s['label']}")
    elif cmd in ("archive", "unarchive"):
        rest = args[1:]
        keep = []
        if "--keep" in rest:
            i = rest.index("--keep")
            keep = [a for a in rest[i + 1:] if not a.startswith("--")]
            rest = rest[:i]
        everything = "--all" in rest
        prefixes = [a for a in rest if not a.startswith("--")]
        for s in load_sessions():
            sid = s["session_id"]
            if any(sid.startswith(k) for k in keep):
                continue
            if everything or any(sid.startswith(p) for p in prefixes):
                s["archived"] = cmd == "archive"
                save_json(session_path(sid), s)
                push_session(s)
                print(f"{cmd}d {s['label']}")
        beam(cfg, force=True)
    elif cmd == "beam":
        print("beamed" if beam(cfg, force=True) else "beam failed")
    elif cmd == "sweep":  # scheduled task: TTL decay repaint + expiry reconcile
        import glob as _glob
        proj = os.path.join(os.path.expanduser("~"), ".claude", "projects")
        for s in load_sessions():
            if s.get("expired") or s["session_id"].startswith("test"):
                continue
            if not _glob.glob(os.path.join(proj, "*", s["session_id"] + ".jsonl")):
                s["expired"] = True  # transcript gone: never resumable again
                save_json(session_path(s["session_id"]), s)
        beam(cfg)
    elif cmd == "seed":
        rest = args[1:]
        days = 14
        if "--days" in rest:
            i = rest.index("--days")
            days = int(rest[i + 1])
            del rest[i:i + 2]
        cands = survey(days)
        if "--apply" in rest:
            ids = [a for a in rest if not a.startswith("--")]
            if ids:  # seed only the listed sid prefixes
                cands = [c for c in cands
                         if any(c["session_id"].startswith(p) for p in ids)]
            seed(cands)
            print(f"seeded {len(cands)} session(s)")
            beam(cfg, force=True)
        else:
            for c in cands:
                print(f"{c['session_id'][:8]}  last seen {c['last_seen']}  {c['cwd']}")
            print(f"-- {len(cands)} candidate(s); apply with: seed --apply [sid-prefix ...]")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
