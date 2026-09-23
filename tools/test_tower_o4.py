"""O4 -- does inherited maturity actually reach the prompt path, and change it?

G-7 (05_PHASE4_PLAN_AUDIT.md) demanded these two claims be separated, because
conflating them is how a wire that delivers nothing gets reported as a product
working:

  (a) THE CAUSAL EDGE EXISTS -- a persisted capsule reaches MissionContext and
      changes a deterministic verdict. Provable here, by mutation, with a
      deterministic oracle.
  (b) THE MISSION STARTS HIGHER -- needs O0 plus production contracts that
      actually require the token. NOT claimed by this file. See §5.

The oracle for (a) is applicability.py gate 3: a contract whose
`required_evidence` is unmet returns BLOCKED_BY_MISSING_EVIDENCE, and one whose
evidence is present does not. That is deterministic, and it is the same gate the
real capsule will feed.

The contract used is SYNTHETIC and built in this file. That is deliberate: no
production contract requires `tower_baseline` yet, and shipping one just to make
a test pass would be the test inventing its own subject.

Run: python tools/test_tower_o4.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

from modules.capability_runtime.applicability import Verdict, evaluate  # noqa: E402
from modules.capability_runtime.contract import CapabilityContract  # noqa: E402
from modules.capability_runtime.applicability import MissionContext  # noqa: E402
from modules.gsd_x import tier  # noqa: E402
from modules.tower import capsule as tc  # noqa: E402

_PASS = 0
_FAIL = 0


def _check(gate: str, cond: bool, evidence: str, diagnostic: str) -> None:
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("  PASS %-36s %s" % (gate, evidence))
    else:
        _FAIL += 1
        print("  FAIL %-36s %s" % (gate, diagnostic))


def _contract() -> CapabilityContract:
    """Synthetic, and says so. Requires the capsule's token and nothing else."""
    return CapabilityContract(
        id="synthetic_tower_consumer",
        name="Synthetic Tower consumer (test only)",
        owner="test",
        triggers=["persist", "migration", "schema"],
        required_evidence=["tower_baseline"],
        # HR-APA-006 rejected the first version of this fixture: "no consumer --
        # activation would be invisible". The estate applied the Liveness
        # Standard to a synthetic contract, which is the validator being right,
        # so the fixture declares its consumer rather than being loosened.
        consumers=["test_tower_o4"],
        outputs=["verdict"],
        scope=["synthetic-test-only"],
    )


def _write_capsule(state: str, tokens: list, produced_at: float | None = None) -> None:
    p = tc.capsule_path("/synthetic")
    payload = {"state": state, "reason": "test fixture", "family": tc.FAMILY,
               "repo_key": "SYNTHETIC-REPO", "repo": "/synthetic",
               "produced_at": produced_at if produced_at is not None else time.time(),
               "schema": 1, "evidence_tokens": tokens}
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="tower_o4_")
    real_state_dir, real_repo_key = tc._state_dir, tc._repo_key
    contract = _contract()
    try:
        tc._state_dir = lambda: tmp
        tc._repo_key = lambda path=None: "SYNTHETIC-REPO"

        print("V-O4 gates -- the causal edge")

        # --- NEGATIVE CONTROL: no capsule at all ---------------------------
        cap_file = tc.capsule_path("/synthetic")
        if os.path.exists(cap_file):
            os.remove(cap_file)
        ev_before = tier.observable_evidence(__import__("pathlib").Path(_PP_ROOT))
        v_before = evaluate(contract, MissionContext(
            description="add a schema migration", available_evidence=ev_before))
        _check("V-O4-BLOCKED-WITHOUT-CAPSULE",
               v_before.verdict == Verdict.BLOCKED_BY_MISSING_EVIDENCE,
               "verdict=%s (%s)" % (v_before.verdict.name, v_before.reason),
               "without a capsule the contract must be BLOCKED, got %s"
               % v_before.verdict.name)
        _check("V-O4-NO-TOKEN-WITHOUT-CAPSULE", "tower_baseline" not in ev_before,
               "evidence=%s" % ev_before,
               "no capsule must contribute no token")

        # --- THE EDGE: an AVAILABLE capsule changes the verdict -------------
        _write_capsule(tc.AVAILABLE, ["tower_baseline"])
        ev_after = tier.observable_evidence(__import__("pathlib").Path(_PP_ROOT))
        v_after = evaluate(contract, MissionContext(
            description="add a schema migration", available_evidence=ev_after))
        _check("V-O4-TOKEN-REACHES-EVIDENCE", "tower_baseline" in ev_after,
               "evidence=%s" % ev_after,
               "the capsule token did not reach observable_evidence")
        _check("V-O4-VERDICT-CHANGED",
               v_before.verdict == Verdict.BLOCKED_BY_MISSING_EVIDENCE
               and v_after.verdict != Verdict.BLOCKED_BY_MISSING_EVIDENCE,
               "%s -> %s : a persisted delta changed a deterministic verdict"
               % (v_before.verdict.name, v_after.verdict.name),
               "verdict did not change: %s -> %s"
               % (v_before.verdict.name, v_after.verdict.name))

        # --- POSITIVE CONTROL (spec §8): not-applicable contributes nothing --
        _write_capsule(tc.NOT_APPLICABLE, [])
        ev_na = tier.observable_evidence(__import__("pathlib").Path(_PP_ROOT))
        _check("V-O4-POSITIVE-CONTROL", "tower_baseline" not in ev_na,
               "NOT_APPLICABLE capsule -> evidence=%s" % ev_na,
               "a mission outside the family must receive nothing")

        # --- STALE contributes nothing --------------------------------------
        _write_capsule(tc.AVAILABLE, ["tower_baseline"],
                       produced_at=time.time() - (tc.FRESH_SECONDS + 60))
        ev_stale = tier.observable_evidence(__import__("pathlib").Path(_PP_ROOT))
        _check("V-O4-STALE-CONTRIBUTES-NOTHING", "tower_baseline" not in ev_stale,
               "stale capsule -> evidence=%s" % ev_stale,
               "stale maturity must not be inherited")

        # --- FAIL-OPEN: a broken capsule costs the prompt nothing ------------
        with open(cap_file, "w", encoding="utf-8") as fh:
            fh.write("{ not json at all")
        ev_broken = tier.observable_evidence(__import__("pathlib").Path(_PP_ROOT))
        _check("V-O4-FAIL-OPEN",
               "source" in ev_broken and "tower_baseline" not in ev_broken,
               "corrupt capsule -> evidence=%s, base tokens intact" % ev_broken,
               "a corrupt capsule must not cost the prompt its other evidence")

        print()
        print("TOWER_O4_PASS=%d/%d  threshold=%d/%d"
              % (_PASS, _PASS + _FAIL, _PASS + _FAIL, _PASS + _FAIL))
        print()
        print("  CLAIM PROVEN     (a) the causal edge exists: a persisted")
        print("                       capsule changes a deterministic verdict.")
        print("  CLAIM NOT PROVEN (b) a real mission starts higher. No")
        print("                       production contract requires this token,")
        print("                       so nothing in the estate consumes it yet.")
        return 0 if _FAIL == 0 else 1
    finally:
        tc._state_dir, tc._repo_key = real_state_dir, real_repo_key
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
