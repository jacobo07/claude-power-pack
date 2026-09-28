"""V-AUTONOMY gates: modules/autonomy_gate -- both poles of every category, DRK wiring, fail-closed.
    python tools/test_autonomy_gate.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules.autonomy_gate import gate as g  # noqa: E402

passes = fails = 0


def check(name, cond, evidence):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {name}: {evidence}")


CASES = [
    # (name, question, authorized, owner, category)
    ("SELF-APPROACH", "Should the parser use approach A (regex) or B (tokenizer) for this internal helper?", (), g.AGENT, g.SELF),
    ("SELF-RENAME-LOCAL", "rename the local helper _norm to _normalize in tools/foo.py", (), g.AGENT, g.SELF),
    ("SELF-TEST-ORDER", "run the unit tests before or after the lint step?", (), g.AGENT, g.SELF),
    ("IRREV-FORCE-PUSH", "should I force-push the rebased branch to main?", (), g.OWNER, g.IRREVERSIBLE),
    ("IRREV-RESET", "git reset --hard to drop the dirty tree?", (), g.OWNER, g.IRREVERSIBLE),
    ("IRREV-DISCARD", "discard uncommitted changes in the other worktree?", (), g.OWNER, g.IRREVERSIBLE),
    ("IRREV-DROP", "drop table orders and recreate it", (), g.OWNER, g.IRREVERSIBLE),
    ("OUT-PUSH-UNAUTH", "git push the feature branch to origin", (), g.OWNER, g.OUTWARD),
    ("OUT-PUSH-AUTH", "git push the feature branch to origin", ("git-push",), g.AGENT, g.OUTWARD),
    ("OUT-DEPLOY", "deploy the new build to the VPS", (), g.OWNER, g.OUTWARD),
    ("OUT-EMAIL", "send the summary email to the leads", (), g.OWNER, g.OUTWARD),
    ("OUT-DEPLOY-NOT-COVERED-BY-PUSH", "deploy the new build to the VPS", ("git-push",), g.OWNER, g.OUTWARD),
    ("PREF-COLOR", "which accent color should the dashboard use?", (), g.OWNER, g.PREFERENCE),
    ("PREF-NAME", "which product name do you prefer?", (), g.OWNER, g.PREFERENCE),
    ("RES-KEY", "I need the API key to upload the artifact", (), g.OWNER, g.RESOURCE),
    ("RES-PERM", "permission denied writing /etc/hosts, what now?", (), g.OWNER, g.RESOURCE),
    ("EMPTY", "", (), g.AGENT, g.SELF),
]


def main() -> int:
    for name, q, auth, owner, cat in CASES:
        v = g.classify(q, authorized=auth)
        check(f"V-AUTONOMY-{name}", v["owner"] == owner and v["category"] == cat,
              f"{v['owner']}/{v['category']} -- {v['why'][:60]}")

    v = g.classify("drop the production database schema")
    check("V-AUTONOMY-DRK-WIRED", v["reversibility"] == "C", f"DRK reversibility={v['reversibility']}")
    v = g.classify("tidy the docstring wording in a helper")
    check("V-AUTONOMY-DRK-REVERSIBLE", v["reversibility"] == "A", f"DRK reversibility={v['reversibility']}")

    saved = g._RESOURCE
    g._RESOURCE = None  # .search on None raises inside classify
    try:
        v = g.classify("anything at all")
    finally:
        g._RESOURCE = saved
    check("V-AUTONOMY-FAIL-CLOSED", v["owner"] == g.OWNER and v["category"] == "gate-error", v["why"])

    with tempfile.TemporaryDirectory() as td:
        g.RECEIPTS = Path(td) / "r.jsonl"
        ok = g.record(g.classify("I need the API key sk-ant-" + "A" * 50), "I need the API key sk-ant-" + "A" * 50,
                      source="test", session="s1")
        row = json.loads(g.RECEIPTS.read_text(encoding="utf-8").strip())
    check("V-AUTONOMY-RECEIPT-REDACTED", ok and row["owner"] == "OWNER" and "AAAAAAAAAA" not in row["question"],
          row["question"])

    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, "-m", "modules.autonomy_gate", "classify", "force-push to main"],
                       cwd=ROOT, capture_output=True, text=True, env=env)
    r2 = subprocess.run([sys.executable, "-m", "modules.autonomy_gate", "classify", "pick the faster sort"],
                        cwd=ROOT, capture_output=True, text=True, env=env)
    check("V-AUTONOMY-CLI-EXIT", r.returncode == 10 and r2.returncode == 0, f"owner->{r.returncode} agent->{r2.returncode}")

    print(f"AUTONOMY_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
