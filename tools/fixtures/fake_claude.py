"""Stand-in for `claude -p` to drive asc_design_gate_run.py end to end with no model.
First call: writes a SLOP index.html. A --resume call: loads the three skills and writes a clean page.
A judge prompt: answers JSON preferring page B."""
import json
import os
import sys

a = sys.argv[1:]
prompt = a[a.index("-p") + 1]
resume = a[a.index("--resume") + 1] if "--resume" in a else None
if "=== PAGE A ===" in prompt:
    print(json.dumps({"result": json.dumps({"winner": "B", "slop_markers": {"A": 3, "B": 1}, "reasons": ["stub"]})}))
    sys.exit(0)
sid = resume or "fake-%d" % os.getpid()
page = os.path.join(os.getcwd(), "index.html")
ev = [{"type": "system", "subtype": "init", "session_id": sid}]
if resume:
    for s in ("design-md", "design-taste-frontend", "frontend-design"):
        ev.append({"type": "assistant", "session_id": sid, "message": {"content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": s}}]}})
    html = "<!doctype html><html lang='en'><head><title>T</title></head><body><h1>Action items from meetings</h1></body></html>\n"
else:
    html = "<!doctype html><html><head><title>T</title></head><body><h1>Action items — fast</h1></body></html>\n"
open(page, "w", encoding="utf-8").write(html)
ev.append({"type": "assistant", "session_id": sid, "message": {"content": [
    {"type": "tool_use", "name": "Write", "input": {"file_path": page, "content": "x"}}]}})
ev.append({"type": "result", "session_id": sid, "usage": {"output_tokens": 1}, "result": "index.html"})
print("\n".join(json.dumps(e) for e in ev))
