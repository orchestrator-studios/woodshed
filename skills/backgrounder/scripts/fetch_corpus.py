#!/usr/bin/env python3
"""Fetch a person's email corpus via the gws CLI, metadata-first.

Lists every message matching the given Gmail queries, fetches lightweight
metadata (headers + snippet) for all of them, then fetches full bodies only
for the subset that needs them: messages the person actually sent/received
(--full-addresses) and/or the N most recent (--full-recent). Retries with
backoff; safe to re-run (resumes from an existing corpus.json).

Usage:
  python3 fetch_corpus.py --config-dir ~/.config/<identity> --out ./corpus \
      --query 'from:x@y.com OR to:x@y.com OR cc:x@y.com' \
      --query '"Full Name" -from:linkedin.com -from:googlealerts-noreply@google.com -from:postmaster.twitter.com -from:mailer-daemon@googlemail.com -from:calendar-invite@lu.ma' \
      --full-addresses x@y.com,old@z.com --full-recent 30

Output: <out>/corpus.json, a list of rows:
  {id, date, from, to, cc, subject, snippet, fresh}
`fresh` is the body text with quoted (">") lines stripped; empty string for
metadata-only rows. Snippets and headers are enough for a mentions inventory;
`fresh` is for the rows you analyze in depth.
"""
import argparse, base64, json, os, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from email.utils import parsedate_to_datetime

GWS_BIN = shutil.which("gws") or "gws"  # Windows: resolve the npm .cmd shim

def gws(config_dir, args):
    env = dict(os.environ, GOOGLE_WORKSPACE_CLI_CONFIG_DIR=config_dir)
    r = subprocess.run([GWS_BIN] + args, capture_output=True, text=True, env=env)
    out = "\n".join(l for l in r.stdout.splitlines() if "keyring" not in l)
    try:
        return json.loads(out)
    except Exception:
        return {}

def list_ids(config_dir, query):
    ids, page = set(), None
    while True:
        p = {"userId": "me", "q": query, "maxResults": 100}
        if page:
            p["pageToken"] = page
        d = gws(config_dir, ["gmail", "users", "messages", "list", "--params", json.dumps(p)])
        ids |= {m["id"] for m in d.get("messages", [])}
        page = d.get("nextPageToken")
        if not page:
            return ids

def get_msg(config_dir, mid, fmt, tries=4):
    for attempt in range(tries):
        m = gws(config_dir, ["gmail", "users", "messages", "get", "--params",
                             json.dumps({"userId": "me", "id": mid, "format": fmt})])
        if "payload" in m:
            return m
        time.sleep(1.5 ** attempt)
    return None

def walk_body(part, acc):
    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
        acc.append(base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", "replace"))
    for sp in part.get("parts", []):
        walk_body(sp, acc)

def row_from(m, with_body):
    h = {x["name"].lower(): x["value"] for x in m["payload"].get("headers", [])}
    fresh = ""
    if with_body:
        acc = []
        walk_body(m["payload"], acc)
        text = "\n".join(acc)
        fresh = "\n".join(l for l in text.splitlines() if not l.startswith(">"))[:3000]
    return {"id": m["id"], "date": h.get("date", ""), "from": h.get("from", ""),
            "to": h.get("to", ""), "cc": h.get("cc", ""), "subject": h.get("subject", ""),
            "snippet": (m.get("snippet") or "")[:200], "fresh": fresh}

def when(row):
    try:
        return parsedate_to_datetime(row["date"]).timestamp()
    except Exception:
        return 0.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--query", action="append", required=True)
    ap.add_argument("--full-addresses", default="", help="comma-separated; messages with any of these in from/to/cc get full bodies")
    ap.add_argument("--full-recent", type=int, default=30, help="also fetch full bodies for the N most recent messages")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    cfg = os.path.expanduser(a.config_dir)
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "corpus.json")
    have = {}
    if os.path.exists(path):
        have = {r["id"]: r for r in json.load(open(path))}

    ids = set()
    for q in a.query:
        found = list_ids(cfg, q)
        print(f"query {q[:60]!r}: {len(found)} ids", file=sys.stderr)
        ids |= found

    def save():
        json.dump(sorted(have.values(), key=when), open(path, "w"), indent=1)

    # pass 1: metadata for everything we don't have yet
    todo = [i for i in sorted(ids) if i not in have]
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for m in ex.map(lambda i: get_msg(cfg, i, "metadata"), todo):
            if m:
                have[m["id"]] = row_from(m, with_body=False)
    save()
    print(f"metadata: {len(have)}/{len(ids)}", file=sys.stderr)

    # pass 2: full bodies for participants and the most recent
    addrs = [s.strip().lower() for s in a.full_addresses.split(",") if s.strip()]
    def needs_body(r):
        blob = (r["from"] + r["to"] + r["cc"]).lower()
        return any(x in blob for x in addrs)
    full_ids = {r["id"] for r in have.values() if needs_body(r)}
    full_ids |= {r["id"] for r in sorted(have.values(), key=when, reverse=True)[:a.full_recent]}
    todo = [i for i in sorted(full_ids) if not have[i].get("fresh")]
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for m in ex.map(lambda i: get_msg(cfg, i, "full"), todo):
            if m:
                have[m["id"]] = row_from(m, with_body=True)
    save()
    missing = len(ids) - len(have)
    print(f"done: {len(have)} rows, {len(full_ids)} with bodies, {missing} unfetchable", file=sys.stderr)

if __name__ == "__main__":
    main()
