"""V-APR-JUDGE-* gates for tools/receipt_judge.py: one reading of a receipt for chain, mission, steward and plan
advance (APR-1, EWC K5). Hermetic: temp files only."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import receipt_judge as rj  # noqa: E402
import gsdx_chain as gc  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="receipt-judge-test-"))
passes = fails = 0


def check(gate, ok, detail=""):
    global passes, fails
    passes, fails = passes + bool(ok), fails + (not ok)
    print(f"{'PASS' if ok else 'FAIL'} {gate} {detail}")


def w(name, text):
    p = TMP / name
    p.write_text(text, encoding="utf-8")
    return p


CASES = {   # file text -> expected status; every shape below was seen in a real receipt on 2026-10-11
    "line": ("# U receipt\nStatus: DONE\n- step: PROVEN\n", "DONE"),
    "bold": ("# U receipt\n- **Status:** DONE\n", "DONE"),
    "inline": ("# P2a receipt\n\nMission: m-f5. Status: DONE, local half only (7/7).\n", "DONE"),
    "lower": ("# U\nstatus: done\n", "DONE"),
    "k5": ("# WU-E2 receipt (commit 25f83975)\n\n- M1: PROVEN (56/56).\n- CLI: PROVEN.\n", "UNREADABLE"),
    "partial": ("# U\nStatus: PARTIAL -- step 3 open\n", "PARTIAL"),
    "inprog": ("# U\nStatus: IN PROGRESS\n", "IN_PROGRESS"),
    "stub": ("# U receipt (checkpoint stub)\nStatus: DONE\n", "STUB"),
    "stubline": ("Status: DONE (STUB)\n", "STUB"),
    "human": ("# U\nStatus: BLOCKED_HUMAN -- run `x` with the Owner key\n", "BLOCKED_HUMAN"),
    "prose_after_done": ("# P\n\nStatus: DONE\n- a PARTIAL / IN PROGRESS / stub status now reads as no receipt.\n", "DONE"),
    "title_partial": ("# T receipt -- Status: PARTIAL\n", "PARTIAL"),
    "json_done": (json.dumps({"status": "DONE", "gate_rc": 0}), "DONE"),
    "json_limits": (json.dumps({"status": "DONE_WITH_LIMITS", "limits": ["x"]}), "DONE_WITH_LIMITS"),
    "json_nostatus": (json.dumps({"gate_rc": 0}), "UNREADABLE"),
    "empty": ("", "UNREADABLE"),
}
bad = []
for name, (text, want) in CASES.items():
    got = rj.receipt_status(w(f"{name}.md", text))
    if got != want:
        bad.append(f"{name}: {got} != {want}")
check("V-APR-JUDGE-SHAPES", not bad, "; ".join(bad) or f"{len(CASES)} shapes")
check("V-APR-JUDGE-ABSENT", rj.receipt_status(TMP / "nope.md") is None and not rj.is_closed(TMP / "nope.md"))

# the K5 split: before APR-1 the mission layer called this receipt present and the chain UNREADABLE
k5 = TMP / "k5.md"
check("V-APR-JUDGE-K5-NOT-CLOSED", not rj.is_closed(k5) and not rj.is_done(k5) and gc.receipt_status(k5) == "UNREADABLE")

# agreement across layers, for every shape: the chain's status IS the judge's; DONE implies closed; an unclosed
# receipt is never done. This is the property whose absence halted EWC.
disagree = []
for name in CASES:
    p = TMP / f"{name}.md"
    s = gc.receipt_status(p)
    if s != rj.receipt_status(p) or (rj.is_done(p) and not rj.is_closed(p)) or (s in rj.NOT_CLOSED and rj.is_closed(p)):
        disagree.append(name)
check("V-APR-JUDGE-LAYERS-AGREE", not disagree, ",".join(disagree) or "chain == judge, done => closed")

# a human gate closes the unit for the mission layer but is not DONE for the chain
h = TMP / "human.md"
check("V-APR-JUDGE-HUMAN-GATE-CLOSED-NOT-DONE", rj.is_closed(h) and not rj.is_done(h))

print(f"APR_JUDGE_PASS={passes}/{passes + fails}")
sys.exit(1 if fails else 0)
