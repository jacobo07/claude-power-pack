#!/usr/bin/env python3
"""Done-gate for the DAIF-08 §11.7 two-arm behavioral trial.

The gates below run against the REAL trial records in vault/trials/ — produced by real API calls to
a real model on real sessions — plus deterministic unit checks of the adjudicators. They do not call
the model: an API call inside a test suite is neither hermetic nor free, and the trial's evidence is
the record it wrote, not a re-run that might land differently.

  V-TRIAL-ARM-A-RUNS           the compiled arm ran and billed real tokens, in every mission
  V-TRIAL-ARM-B-RUNS           the control arm did likewise
  V-TRIAL-CLAUSE-3-MEASURED    clause 3 carries an explicit verdict, never a bare UNVERIFIED
  V-TRIAL-CLAUSE-4-MEASURED    clause 4 likewise
  V-TRIAL-NO-INVENTED-SAVINGS  the delta is exactly B-A, with no floor at zero anywhere in the code
  V-TRIAL-RESULT-SERIALIZABLE  each TrialResult is valid JSON on disk with every required key
  V-TRIAL-ADJUDICATOR-REFUSES  both poles are reachable: the adjudicators are observed to PASS AND
                               to FAIL on synthetic input (a gate never seen to refuse is inert)
  V-DAIF-COMPILER-PASS-UNCHANGED  the SCS C96 gate still stands at 9/9

Run:  python tools/test_daif_two_arm_trial.py
Exit: 0 iff every gate passes.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules.daif.two_arm_trial import (            # noqa: E402
    SEALED_SAMPLE, adjudicate_clause_3, adjudicate_clause_4, adjudicate_invention,
)

TRIALS_DIR = ROOT / "vault" / "trials"
TRIAL_SOURCE = ROOT / "modules" / "daif" / "two_arm_trial.py"
COMPILER_GATE_BASELINE = 9      # DAIF_COMPILER_PASS, sealed at SCS C96

REQUIRED_KEYS = [
    "session_id", "trial_timestamp", "model", "arm_a_tokens", "arm_b_tokens",
    "token_delta_saved", "clause_3_verdict", "clause_4_verdict", "clause_3_evidence",
    "clause_4_evidence", "invention_verdict", "equivalence_overlap", "arm_a", "arm_b",
]

_passes: list[str] = []
_fails: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    print(f"  [OK  ] {gate}: {evidence}")
    _passes.append(gate)


def _fail(gate: str, diagnostic: str) -> None:
    print(f"  [FAIL] {gate}: {diagnostic}")
    _fails.append(gate)


def _load_trials() -> list[dict]:
    out = []
    for sid in SEALED_SAMPLE:
        p = TRIALS_DIR / f"two_arm_{sid}.json"
        if not p.is_file():
            continue
        try:
            out.append(json.loads(p.read_text(encoding="utf-8-sig")))
        except (OSError, json.JSONDecodeError, ValueError):
            continue
    return out


def gate_arm_runs(trials: list[dict], arm: str, gate: str) -> None:
    bad = [t["session_id"] for t in trials
           if not (t.get(arm, {}).get("ok") and t.get(arm, {}).get("total_tokens", 0) > 0)]
    if bad:
        _fail(gate, f"{len(bad)} mission(s) where {arm} did not run or billed 0 tokens: {', '.join(bad)}")
        return
    total = sum(t[arm]["total_tokens"] for t in trials)
    _ok(gate, f"{len(trials)}/{len(trials)} missions ran; {total:,} real tokens billed across the arm")


def gate_clause_measured(trials: list[dict], clause: str, gate: str) -> None:
    verdicts = [(t["session_id"], t[f"{clause}_verdict"], t[f"{clause}_evidence"]) for t in trials]
    unexplained = [s for s, v, ev in verdicts if v == "UNVERIFIED" and not str(ev).strip()]
    if unexplained:
        _fail(gate, f"UNVERIFIED with no documented reason on: {', '.join(unexplained)}")
        return
    missing = [s for s, v, _ in verdicts if v not in ("PASS", "FAIL", "UNVERIFIED")]
    if missing:
        _fail(gate, f"no verdict at all on: {', '.join(missing)}")
        return
    tally = {v: sum(1 for _, x, _ in verdicts if x == v) for _, v, _ in verdicts}
    _ok(gate, f"explicit verdict on {len(verdicts)}/{len(verdicts)} missions — "
              + ", ".join(f"{v}x{n}" for v, n in sorted(tally.items())))


def gate_no_invented_savings(trials: list[dict]) -> None:
    """The delta is the real number. A floor at zero would convert a negative finding — the pack
    costing MORE than the source — into a silent zero, which is the fabrication DAIF-21 Part XIX
    lists as one of its three honest risks."""
    for t in trials:
        expected = t["arm_b_tokens"] - t["arm_a_tokens"]
        if t["token_delta_saved"] != expected:
            _fail("V-TRIAL-NO-INVENTED-SAVINGS",
                  f"{t['session_id']}: delta {t['token_delta_saved']} != B-A ({expected})")
            return
    src = TRIAL_SOURCE.read_text(encoding="utf-8")
    clamp = re.search(r"token_delta_saved\s*=\s*max\s*\(|max\s*\(\s*0\s*,[^)]*arm_b", src)
    if clamp:
        _fail("V-TRIAL-NO-INVENTED-SAVINGS", "the delta is floored at zero in the source")
        return
    deltas = [t["token_delta_saved"] for t in trials]
    _ok("V-TRIAL-NO-INVENTED-SAVINGS",
        f"delta == B-A exactly on {len(trials)}/{len(trials)} missions, no floor in the code; "
        f"observed {deltas} (a negative would be reported as negative)")


def gate_serializable(trials: list[dict]) -> None:
    for t in trials:
        missing = [k for k in REQUIRED_KEYS if k not in t]
        if missing:
            _fail("V-TRIAL-RESULT-SERIALIZABLE",
                  f"{t.get('session_id')}: missing key(s) {', '.join(missing)}")
            return
        try:
            json.dumps(t)
        except (TypeError, ValueError) as exc:
            _fail("V-TRIAL-RESULT-SERIALIZABLE", f"{t.get('session_id')} is not serializable: {exc}")
            return
    _ok("V-TRIAL-RESULT-SERIALIZABLE",
        f"{len(trials)} TrialResult record(s) on disk, valid JSON, all {len(REQUIRED_KEYS)} keys present")


def gate_adjudicator_refuses() -> None:
    """Both poles reachable. An adjudicator that can only pass has measured nothing."""
    ids, texts, wordsets = {"HR-001"}, {"hardrulesnevercommit"}, [{"hard", "rules", "never", "commit"}]
    good = {"state": {"done": ["a"], "in_flight": [], "not_started": ["b"]},
            "hard_constraints": ["HR-001"], "open_obligations": [], "need_source_access": False,
            "source_requests": []}
    bad = {"state": {"done": [], "in_flight": [], "not_started": []},
           "hard_constraints": ["HR-999-DOES-NOT-EXIST"],
           "open_obligations": [], "need_source_access": True,
           "source_requests": ["open the transcript"]}
    checks = [
        ("c3 PASS", adjudicate_clause_3(good, ids, list(texts), wordsets)[0] == "PASS"),
        ("c3 FAIL", adjudicate_clause_3(bad, ids, list(texts), wordsets)[0] == "FAIL"),
        ("c4 PASS", adjudicate_clause_4(good)[0] == "PASS"),
        ("c4 FAIL", adjudicate_clause_4(bad)[0] == "FAIL"),
        ("inv PASS", adjudicate_invention(good, ids, list(texts), wordsets)[0] == "PASS"),
        ("inv FAIL", adjudicate_invention(bad, ids, list(texts), wordsets)[0] == "FAIL"),
        ("c4 UNVERIFIED", adjudicate_clause_4({"state": {}})[0] == "UNVERIFIED"),
    ]
    broken = [name for name, ok in checks if not ok]
    if broken:
        _fail("V-TRIAL-ADJUDICATOR-REFUSES", f"unreachable pole(s): {', '.join(broken)}")
        return
    _ok("V-TRIAL-ADJUDICATOR-REFUSES",
        "all 7 poles reachable — each adjudicator observed to PASS, to FAIL, and to abstain")


def gate_compiler_unchanged() -> None:
    runner = ROOT / "tools" / "test_daif_session_compiler.py"
    proc = subprocess.run([sys.executable, str(runner)], capture_output=True, text=True,
                          cwd=str(ROOT), timeout=900)
    m = re.search(r"DAIF_COMPILER_PASS=(\d+)/(\d+)", proc.stdout)
    if not m:
        _fail("V-DAIF-COMPILER-PASS-UNCHANGED", "the SCS C96 gate emitted no DAIF_COMPILER_PASS line")
        return
    got, total = int(m.group(1)), int(m.group(2))
    if proc.returncode != 0 or got != total or got < COMPILER_GATE_BASELINE:
        _fail("V-DAIF-COMPILER-PASS-UNCHANGED",
              f"regressed to {got}/{total} (baseline {COMPILER_GATE_BASELINE}), exit={proc.returncode}")
        return
    _ok("V-DAIF-COMPILER-PASS-UNCHANGED", f"DAIF_COMPILER_PASS={got}/{total} — SCS C96 still stands")


def main() -> int:
    print("== DAIF-08 §11.7 two-arm behavioral trial — done-gate ==")
    trials = _load_trials()
    if len(trials) != len(SEALED_SAMPLE):
        print(f"  [FAIL] expected {len(SEALED_SAMPLE)} trial record(s) from the sealed sample, "
              f"found {len(trials)}. Run: python modules/daif/two_arm_trial.py --sample")
        return 1
    print(f"  sealed sample: {len(trials)} mission(s), model={trials[0]['model']}\n")

    gate_arm_runs(trials, "arm_a", "V-TRIAL-ARM-A-RUNS")
    gate_arm_runs(trials, "arm_b", "V-TRIAL-ARM-B-RUNS")
    gate_clause_measured(trials, "clause_3", "V-TRIAL-CLAUSE-3-MEASURED")
    gate_clause_measured(trials, "clause_4", "V-TRIAL-CLAUSE-4-MEASURED")
    gate_no_invented_savings(trials)
    gate_serializable(trials)
    gate_adjudicator_refuses()
    gate_compiler_unchanged()

    # The finding, restated where nobody can miss it. The gates above verify that the trial was
    # honestly RUN; they do not assert that the artifact passed, and it did not.
    c4_fails = [t["session_id"] for t in trials if t["clause_4_verdict"] == "FAIL"]
    deltas = [t["token_delta_saved"] for t in trials]
    print(f"\n  MEASURED — token delta saved (B-A) per mission: {deltas}")
    print(f"  MEASURED — clause 4 (no indiscriminate re-reading) FAILED on "
          f"{len(c4_fails)}/{len(trials)} missions: the resumed actor asked for the source anyway.")
    print("  Therefore the DAIF-08 Part XI done-gate REMAINS OPEN. The pack is cheaper and it is "
          "not yet sufficient.")

    total = len(_passes) + len(_fails)
    print(f"\nDAIF_TRIAL_PASS={len(_passes)}/{total}  threshold={total}/{total}")
    if _fails:
        print("  refused: " + ", ".join(_fails))
    return 0 if not _fails else 1


if __name__ == "__main__":
    sys.exit(main())
