"""Fake `claude -p` for tools/test_pp_eval.py. Emits the stream-json event shapes observed
from claude 2.1.285 on 2026-09-30 (system/init with `skills`, system/hook_started,
rate_limit_event with unifiedWindows, assistant with usage, result).

FAKE_MODE: fix (repairs calc.py) | nofix | quota (429 result) | leak (tool input names FAKE_LEAK)
FAKE_IGNORE_ARMS=1: behave like arm A whatever flags arrive (drives the positive controls red).
"""
import json
import os
import sys
import time
from pathlib import Path

argv = sys.argv[1:]
settings = argv[argv.index("--settings") + 1] if "--settings" in argv else "{}"
ignore = os.environ.get("FAKE_IGNORE_ARMS") == "1"
no_hooks = "disableAllHooks" in settings and not ignore
no_skills = "--disable-slash-commands" in argv and not ignore
less_context = "claudeMdExcludes" in settings and not ignore
mode = os.environ.get("FAKE_MODE", "fix")


def emit(o):
    print(json.dumps(o), flush=True)


emit({"type": "system", "subtype": "init", "session_id": "fake",
      "skills": [] if no_skills else ["a", "b", "c"]})
for _ in range(0 if no_hooks else 2):
    emit({"type": "system", "subtype": "hook_started"})
resets = int(time.time()) + 3600
emit({"type": "rate_limit_event", "rate_limit_info": {"unifiedWindows": {
    "five_hour": {"utilization": 0.1, "resetsAt": resets},
    "seven_day": {"utilization": float(os.environ.get("FAKE_UTIL", "0.2")), "resetsAt": resets}}}})
tool_input = {"file_path": "calc.py"}
if mode == "leak":
    tool_input = {"command": f"git show {os.environ.get('FAKE_LEAK', '')}"}
emit({"type": "assistant", "message": {
    "usage": {"input_tokens": 10, "cache_read_input_tokens": 1000 if less_context else 5000,
              "cache_creation_input_tokens": 0, "output_tokens": 50},
    "content": [{"type": "tool_use", "name": "Edit", "input": tool_input}]}})
if mode == "fix":
    p = Path("calc.py")
    p.write_text(p.read_text(encoding="utf-8").replace("a - b", "a + b"), encoding="utf-8")
if mode == "quota":
    emit({"type": "result", "subtype": "error_during_execution", "is_error": True,
          "api_error_status": 429, "result": "Claude AI usage limit reached", "num_turns": 1})
    sys.exit(1)
emit({"type": "result", "subtype": "success", "is_error": False, "num_turns": 2, "result": "done"})
