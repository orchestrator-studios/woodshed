"""Emit a synthetic Claude Code hook event as JSON (for testing presence.py).

Usage: emit_test_event.py <session_id> <event> [tool_name] [cwd] [file_path]
"""
import json
import sys

sid, event = sys.argv[1], sys.argv[2]
tool = sys.argv[3] if len(sys.argv) > 3 else None
cwd = sys.argv[4] if len(sys.argv) > 4 else r"C:\Users\cliff\perf-monitor"
fp = sys.argv[5] if len(sys.argv) > 5 else cwd + r"\testfile.txt"

evt = {"session_id": sid, "hook_event_name": event, "cwd": cwd}
if tool:
    evt["tool_name"] = tool
    evt["tool_input"] = {"file_path": fp}
print(json.dumps(evt))
