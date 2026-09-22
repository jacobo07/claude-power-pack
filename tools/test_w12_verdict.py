"""Gates for the W12 verdict comparator, driven before either arm produced data.

The property under test is an ORDERING, not an arithmetic: movement must be
unreachable until comparability, execution and baseline identity have all passed.
An ordering is the easiest kind of guard to believe and the hardest to notice the
absence of, because a comparator that prints movement unconditionally looks correct
on every valid run -- which is every run anybody will look at closely.

So the refusal cases assert on what is ABSENT from stdout, and they are paired with
licensing cases that assert the same section is PRESENT. A guard that refused
everything would satisfy every refusal assertion on its own and is exactly what the
controls exist to exclude.

The recovery cases drive all four corners of `w12_preregistration.md` §4, including
the one that matters most and is least likely to occur naturally: a treatment whose
`worsened` count falls while its `evicted` count rises. That is an improvement bought
by removing the owner from the agent's view, it reads as repair in every aggregate,
and only a rule that names eviction can refuse it.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "ucr_cif_w12_verdict.py"
OWNER = "modules/governance-overlay"
MOVEMENT_HEADER = "PRE-REGISTERED CAUSAL TEST"

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {gate}  {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}  {diag}")


def fingerprint(**over) -> dict:
    fp = {"oracle_schema": "ucr-cif-oracle/1",
          "corpus_id": "ef2b381beff512ca6919280a",
          "ledger_rows": 2376,
          "owner_universe_n": 40,
          "owner_universe_sha": "ccc401bda49648c8",
          "case_set_sha": "1235476c90059398",
          "cases": 1471,
          "sessions_swept": 573,
          "window_hours": 24,
          "max_owners": 5}
    fp.update(over)
    return fp


def report(owner_pre: dict, owner_post: dict, *, fp: dict | None = None,
           ok: bool = True) -> dict:
    """A derived report carrying only what the comparator reads."""
    return {
        "fingerprint": fp if fp is not None else fingerprint(),
        "arm_divergence": {"routed_cases": 1285, "reordered": 982,
                           "rate": 0.7642, "floor": 0.05, "ok": ok},
        "slot_precision": {"labelled_cases": 116,
                           "control": {"slots": 454, "true": 40, "false": 414},
                           "treatment": {"slots": 454, "true": 38, "false": 416},
                           "precision_delta_points": -0.4405},
        "pre_cap": {"by_owner": {OWNER: owner_pre},
                    "by_modality": {"prose": {"moves": {"improved": 6, "worsened": 13}},
                                    "code": {"moves": {"improved": 10, "worsened": 8}}}},
        "post_cap": {"by_owner": {OWNER: owner_post},
                     "by_modality": {"prose": {"moves": {"improved": 3, "worsened": 12}},
                                     "code": {"moves": {"improved": 8, "worsened": 2}}}},
    }


#: The pre-registered baseline. Both halves, exactly as the committed store holds it.
BASE = {"worsened": 8}


def run(tmp: Path, a: dict, b: dict, movement: bool) -> tuple[int, str]:
    pa, pb = tmp / "a.json", tmp / "b.json"
    pa.write_text(json.dumps(a), encoding="utf-8")
    pb.write_text(json.dumps(b), encoding="utf-8")
    argv = [sys.executable, str(TOOL), "--w9", str(pa), "--w11", str(pb)]
    if movement:
        argv.append("--movement")
    proc = subprocess.run(argv, capture_output=True, text=True, cwd=str(ROOT))
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        # ---- REFUSALS: movement must be unreachable ----------------------
        rc, out = run(tmp, report(BASE, BASE),
                      report({"worsened": 0}, {"worsened": 0},
                             fp=fingerprint(case_set_sha="DRIFTED0000")),
                      movement=True)
        if rc != 0 and MOVEMENT_HEADER not in out and "DRIFTED" in out:
            _ok("V-W12-DRIFT-REFUSES", f"exit {rc}, no movement section")
        else:
            _fail("V-W12-DRIFT-REFUSES",
                  f"exit {rc}; movement_present={MOVEMENT_HEADER in out}")

        rc, out = run(tmp, report(BASE, BASE),
                      {"arm_divergence": {"ok": True}},   # no fingerprint at all
                      movement=True)
        if rc != 0 and MOVEMENT_HEADER not in out and "UNREADABLE" in out:
            _ok("V-W12-UNREADABLE-REFUSES", f"exit {rc}, UNREADABLE is its own class")
        else:
            _fail("V-W12-UNREADABLE-REFUSES",
                  f"exit {rc}; movement_present={MOVEMENT_HEADER in out}")

        rc, out = run(tmp, report(BASE, BASE),
                      report({"worsened": 0}, {"worsened": 0}, ok=False),
                      movement=True)
        if rc != 0 and MOVEMENT_HEADER not in out:
            _ok("V-W12-DEAD-ARM-REFUSES",
                "an arm that did not diverge yields no verdict")
        else:
            _fail("V-W12-DEAD-ARM-REFUSES",
                  f"exit {rc}; movement_present={MOVEMENT_HEADER in out}")

        rc, out = run(tmp, report({"worsened": 5}, {"worsened": 5}),
                      report({"worsened": 0}, {"worsened": 0}),
                      movement=True)
        if rc != 0 and MOVEMENT_HEADER not in out and "MOVED" in out:
            _ok("V-W12-BASELINE-DRIFT-REFUSES",
                "a W9 arm that does not reproduce worsened 8 is not the reference")
        else:
            _fail("V-W12-BASELINE-DRIFT-REFUSES",
                  f"exit {rc}; movement_present={MOVEMENT_HEADER in out}")

        # ---- CONTROL: the guard is not simply refusing everything --------
        rc, out = run(tmp, report(BASE, BASE), report(BASE, BASE), movement=False)
        if rc == 0 and "RUN VALID" in out and MOVEMENT_HEADER not in out:
            _ok("V-W12-VALID-WITHOUT-MOVEMENT",
                "validity can pass while movement stays unrequested")
        else:
            _fail("V-W12-VALID-WITHOUT-MOVEMENT", f"exit {rc}")

        # ---- RECOVERY CORNERS -------------------------------------------
        cases = [
            ("V-W12-FULL-RECOVERY", {"improved": 8}, "FULLY_RECOVERED"),
            ("V-W12-PARTIAL-RECOVERY",
             {"worsened": 3, "improved": 5}, "RECOVERED"),
            ("V-W12-NO-MOVEMENT-IS-NOT-RECOVERY", {"worsened": 8}, "NOT_RECOVERED"),
            ("V-W12-WORSE-IS-NOT-RECOVERY", {"worsened": 9}, "NOT_RECOVERED"),
            ("V-W12-EVICTION-IS-NOT-RECOVERY",
             {"worsened": 2, "improved": 3, "evicted": 3}, "NOT_RECOVERED"),
        ]
        for gate, treat, want in cases:
            rc, out = run(tmp, report(BASE, BASE), report(treat, treat), movement=True)
            line = [ln for ln in out.splitlines() if "post-cap  ->" in ln]
            got = line[0].split("->")[1].strip().split()[0] if line else "<none>"
            if rc == 0 and MOVEMENT_HEADER in out and got == want:
                _ok(gate, f"post-cap {want}")
            else:
                _fail(gate, f"exit {rc}, wanted {want}, got {got}")

        # The eviction case is the one worth stating twice: worsened FELL from 8
        # to 2 and it is still not a recovery.
        rc, out = run(tmp, report(BASE, BASE),
                      report({"worsened": 2, "improved": 3, "evicted": 3},
                             {"worsened": 2, "improved": 3, "evicted": 3}),
                      movement=True)
        if "left the agent's view" in out:
            _ok("V-W12-EVICTION-NAMED",
                "the refusal says WHY, not merely that it refused")
        else:
            _fail("V-W12-EVICTION-NAMED", "eviction disqualifier not explained")

        # ---- HALVES ARE INDEPENDENT --------------------------------------
        rc, out = run(tmp, report(BASE, BASE),
                      report({"improved": 8}, {"worsened": 8}), movement=True)
        pre = [ln for ln in out.splitlines() if "pre-cap   ->" in ln]
        post = [ln for ln in out.splitlines() if "post-cap  ->" in ln]
        pre_v = pre[0].split("->")[1].strip().split()[0] if pre else "<none>"
        post_v = post[0].split("->")[1].strip().split()[0] if post else "<none>"
        # Assert the VALUE the headline carries, not that the string appears
        # somewhere in the output. The first version of this gate tested
        # `"NOT_RECOVERED" in out`, which is satisfied by the post-cap line no
        # matter which half the headline is keyed to -- so a comparator keyed to
        # the flattering half would have passed it. Found by writing the mutation
        # that keys the headline to pre-cap and noticing it had nothing to fail.
        hl = [ln for ln in out.splitlines() if "HEADLINE (post-cap" in ln]
        hl_v = hl[0].rsplit(":", 1)[1].strip() if hl else "<none>"
        headline = hl_v == post_v == "NOT_RECOVERED"
        if pre_v == "FULLY_RECOVERED" and post_v == "NOT_RECOVERED" and headline:
            _ok("V-W12-HALVES-INDEPENDENT",
                "pre-cap repair with post-cap loss is NOT a recovery")
        else:
            _fail("V-W12-HALVES-INDEPENDENT", f"pre {pre_v}, post {post_v}")

    total = _passes + _fails
    print(f"\nW12_VERDICT_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
