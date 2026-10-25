"""W5a selection: mission-worker sessions on the laptop, last 14 days, grouped by owner kind/profile.
Rule: per class, the 3 newest missions whose owner session has a transcript on disk. Prints JSON."""
import datetime as dt
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
sys.path.insert(0, r"C:\Users\User\.claude\skills\claude-power-pack\tools")
import gsd_mission as g  # noqa: E402

PROJECTS = Path.home() / ".claude" / "projects"


def ts(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        try:
            return dt.datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp()
        except ValueError:
            return 0.0


def transcript(sid):
    hits = list(PROJECTS.glob(f"*/{sid}.jsonl"))
    return str(hits[0]) if hits else None


cut = time.time() - 14 * 86400
classes = {}
for m in sorted(g.all_missions(), key=lambda m: ts(m.get("created_at")), reverse=True):
    o = m.get("owner")
    if ts(m.get("created_at")) < cut or not isinstance(o, dict) or not o.get("session_id"):
        continue
    cls = f"{o.get('kind') or 'full'}:{o.get('profile') or '-'}"
    if len(classes.setdefault(cls, [])) >= 3:
        continue
    t = transcript(o["session_id"])
    if t:
        classes[cls].append({"mission": m["mission_id"], "sid": o["session_id"], "mode": m.get("mode"),
                             "created_at": m.get("created_at"), "transcript": t})
print(json.dumps({"rule": "last 14 days; per owner kind:profile the 3 newest missions with a laptop transcript",
                  "selected_at": dt.datetime.now(dt.timezone.utc).isoformat(), "classes": classes}, indent=1))
