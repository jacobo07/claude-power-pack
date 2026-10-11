"""claim_cost_for: a claim graph populates claim_cost; no/bad graph falls back to None (never 0)."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402

fails = 0


def check(name, ok):
    global fails
    print(("PASS " if ok else "FAIL ") + name)
    fails += 0 if ok else 1


d = Path(tempfile.mkdtemp())
g = d / "g.json"
g.write_text(json.dumps({"claims": [{"id": "a", "class": "novel", "status": "open"},
                                    {"id": "b", "class": "bounded_coding", "status": "open"}]}))
cc = gm.claim_cost_for({"claim_graph": str(g)})
check("graph populates", bool(cc) and cc["candidate"]["with_margin"] > 0)
check("auto_headroom uses it unclamped", "cost_to_completion" in gm.auto_headroom(0, 0, None, {}, cc)[1])
check("explicit claim_cost wins", gm.claim_cost_for({"claim_cost": {"x": 1}, "claim_graph": str(g)}) == {"x": 1})
check("no graph -> None", gm.claim_cost_for({}) is None)
check("missing file -> None", gm.claim_cost_for({"claim_graph": str(d / "nope.json")}) is None)
bad = d / "b.json"
bad.write_text(json.dumps({"phases": 3, "claims": [{"id": "a", "class": "novel"}]}))
check("phase forecast refused -> None", gm.claim_cost_for({"claim_graph": str(bad)}) is None)
sys.exit(1 if fails else 0)
