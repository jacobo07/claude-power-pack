#!/usr/bin/env python
"""V-GRANT-* gates for authority grants (modules/autonomy_gate/grants.py, oic-v1 S1).

Hermetic: the ledger and the decision log go to a temp dir BEFORE import. Every refusal has a paired
control in which the same grant allows the request, so a module that refuses everything cannot go green.

Mutation drill: set GRANTS_DRILL_DIR to a directory holding a mutated copy of the module
(as modules/autonomy_gate/grants.py); it is imported instead of the real one.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="grants-test-")
os.environ["CPP_AUTHORITY_DIR"] = TMP
os.environ["CPP_AUTONOMY_RECEIPTS"] = str(Path(TMP) / "decisions.jsonl")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.environ.get("GRANTS_DRILL_DIR") or str(ROOT))
from modules.autonomy_gate import grants as cp  # noqa: E402

passes = fails = 0
NOW = 1_800_000_000.0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def raises(fn) -> bool:
    try:
        fn()
    except ValueError:
        return True
    return False


plan = Path(TMP) / "plan.md"
plan.write_text("plan v1\n", encoding="utf-8")
import hashlib  # noqa: E402
PLAN = {"path": str(plan), "sha256": hashlib.sha256(plan.read_bytes()).hexdigest()}
SHA = "161617dfab3c9e8c71ad0d9a6788f9aa2ab3b4d4"
BASE = {"programme": "oic-v1", "level": 3, "provenance": {"reply": "y"}, "plan": PLAN,
        "effects": ["pr.merge", "cd.watch"], "denied": ["pr.force_push"],
        "targets": {"repo": "jacobo07/InfinityOps", "pr": "545", "head_sha": SHA},
        "conditions": ["ci_green"], "delegation_depth": 1, "expires_at": NOW + 48 * 3600}
T = {"repo": "jacobo07/InfinityOps", "pr": "545", "head_sha": SHA}
F = {"ci_green": True}

cid = cp.grant(dict(BASE), now=NOW)
ok = cp.check("pr.merge", target=T, facts=F, now=NOW + 60)
check("V-GRANT-ALLOW-CONTROL", ok["allowed"] and ok["grant"] == cid, str(ok))
check("V-GRANT-GRANT-IDEMPOTENT", cp.grant(dict(BASE), now=NOW) == cid and len(cp.load()) == 1)

v = cp.check("pr.merge", target=dict(T, head_sha="0" * 40), facts=F, now=NOW + 60)
check("V-GRANT-SHA-CHANGE-DENIED", not v["allowed"], str(v["why"]))
v = cp.check("pr.merge", target={k: T[k] for k in ("repo", "pr")}, facts=F, now=NOW + 60)
check("V-GRANT-MISSING-TARGET-DENIED", not v["allowed"], str(v["why"]))
v = cp.check("pr.merge", target=T, facts={}, now=NOW + 60)
check("V-GRANT-MISSING-FACT-DENIED", not v["allowed"], str(v["why"]))
v = cp.check("pr.merge", target=T, facts={"ci_green": "true"}, now=NOW + 60)
check("V-GRANT-FACT-MUST-BE-TRUE-NOT-TRUTHY", not v["allowed"], str(v["why"]))
v = cp.check("pr.close", target=T, facts=F, now=NOW + 60)
check("V-GRANT-UNGRANTED-EFFECT-DENIED", not v["allowed"], str(v["why"]))
v = cp.check("pr.merge", target=T, facts=F, now=NOW + 49 * 3600)
check("V-GRANT-EXPIRED-DENIED", not v["allowed"], str(v["why"]))

plan.write_text("plan v2 (edited after approval)\n", encoding="utf-8")
v = cp.check("pr.merge", target=T, facts=F, now=NOW + 60)
check("V-GRANT-PLAN-EDIT-INVALIDATES", not v["allowed"], str(v["why"]))
plan.write_text("plan v1\n", encoding="utf-8")
check("V-GRANT-PLAN-RESTORED-CONTROL", cp.check("pr.merge", target=T, facts=F, now=NOW + 60)["allowed"])

check("V-GRANT-L4-NOT-GRANTABLE", raises(lambda: cp.grant(dict(BASE, level=4, id="x4"), now=NOW)))
check("V-GRANT-WILDCARD-NOT-GRANTABLE", raises(lambda: cp.grant(dict(BASE, effects=["*"], id="xw"), now=NOW)))
check("V-GRANT-NO-PROVENANCE-NOT-GRANTABLE", raises(lambda: cp.grant(dict(BASE, provenance=None, id="xp"), now=NOW)))

# Delegation: a child narrows, never widens.
child = cp.derive(cid, {"effects": ["cd.watch"]}, now=NOW)
check("V-GRANT-CHILD-SUBSET-ALLOWED", cp.check("cd.watch", target=T, facts=F, now=NOW + 60)["grant"] in (cid, child))
c = cp.load()[child]
check("V-GRANT-CHILD-INHERITS-TARGETS-AND-DENIALS",
      c["targets"] == BASE["targets"] and "pr.force_push" in c["denied"] and c["delegation_depth"] == 0, str(c))
check("V-GRANT-CHILD-CANNOT-WIDEN-EFFECTS", raises(lambda: cp.derive(cid, {"effects": ["pr.close"]}, now=NOW)))
check("V-GRANT-CHILD-CANNOT-WIDEN-TARGET", raises(lambda: cp.derive(cid, {"effects": ["cd.watch"],
                                                                        "targets": {"pr": ["545", "546"]}}, now=NOW)))
check("V-GRANT-CHILD-CANNOT-REDELEGATE", raises(lambda: cp.derive(child, {"effects": ["cd.watch"]}, now=NOW)))

# Revocation: the parent's revoke reaches the child; an unrelated grant survives.
other = cp.grant(dict(BASE, effects=["vps.read"], targets={"host": "kobiiclaw"}, conditions=[], id="grant-other"),
                 now=NOW)
cp.revoke(cid, by="owner", reason="test", now=NOW + 120)
v = cp.check("pr.merge", target=T, facts=F, now=NOW + 180)
check("V-GRANT-REVOKE-DENIES", not v["allowed"], str(v["why"]))
v = cp.check("cd.watch", target=T, facts=F, now=NOW + 180)
check("V-GRANT-REVOKE-REACHES-CHILD", not v["allowed"], str(v["why"]))
check("V-GRANT-REVOKE-SPARES-OTHERS", cp.check("vps.read", target={"host": "kobiiclaw"}, now=NOW + 180)["allowed"])
cp.revoke("all", by="owner", reason="stop everything", now=NOW + 200)
check("V-GRANT-REVOKE-ALL", not cp.check("vps.read", target={"host": "kobiiclaw"}, now=NOW + 240)["allowed"])

# Rotation: a fresh reader (another process, another session) sees the same authority.
before = {k: bool(v["revoked"]) for k, v in cp.load().items()}
import importlib  # noqa: E402
importlib.reload(cp)
after = {k: bool(v["revoked"]) for k, v in cp.load().items()}
check("V-GRANT-SURVIVES-RELOAD", before == after and len(after) == 3, str(after))

dec = Path(os.environ["CPP_AUTONOMY_RECEIPTS"])
rows = dec.read_text(encoding="utf-8").splitlines() if dec.is_file() else []
# exactly one audit row per check() call above (14)
check("V-GRANT-EVERY-CHECK-AUDITED", len(rows) == 14 and all('"category": "grant"' in r for r in rows),
      f"{len(rows)} rows")

print(f"GRANTS_PASS={passes}/{passes + fails}")
sys.exit(0 if fails == 0 else 1)
