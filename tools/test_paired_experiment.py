"""V-PEXP-* gates for tools/paired_experiment.py (T8 item 31), in a private experiments dir.

  freeze      re-registering the identical spec is a no-op; a changed spec is refused
  ordering    a run stamped before the registration is refused by the analysis
  grading     an ungraded run leaves the analysis incomplete (quality null, never inferred)
  escape      the host's model id is escaped injectively into the vendor grammar
  committed   the real exp-successor-packet-002 analysis re-derives from its committed files
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import paired_experiment as pe  # noqa: E402

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


H = "a" * 64


def spec(created="2026-01-01T00:00:00.000Z"):
    case = lambda cid, split: {"id": cid, "split": split, "contractSha256": H, "sourceSha256": H,  # noqa: E731
                               "rubricSha256": H, "promptSha256": {"baseline": H, "candidate": "b" * 64}, "maxScore": 2}
    return {"schema": "genesis-paired-experiment-v1", "id": "exp-test", "createdAt": created,
            "worker": {"route": "r", "requestedModel": "m", "config": {}}, "scope": "diagnostic",
            "qualityMetric": "normalized-score", "cases": [case("c1", "training"), case("c2", "holdout")],
            "maxAttemptsPerRun": 1, "targets": {"qualityMultiplier": 1, "tokenReduction": 0.05}}


def run(reg, cid, variant, started):
    return {"caseId": cid, "variant": variant, "registrationSha256": reg["sha256"],
            "promptSha256": H if variant == "baseline" else "b" * 64, "sourceSha256": H,
            "worker": {"route": "r", "requestedModel": "m", "config": {}}, "startedAt": started,
            "attempts": [{"sequence": 1, "status": "passed", "actualModel": "claude-x[1m]",
                          "usage": {"input_tokens": 100, "output_tokens": 10}, "elapsedMs": 5,
                          "outputSha256": "c" * 64}], "historyComplete": True}


def main() -> int:
    base = Path(tempfile.mkdtemp(prefix="pexp-"))
    reg = pe.preregister(spec(), base)
    again = pe.preregister(spec(), base)
    check("V-PEXP-IDEMPOTENT", again["sha256"] == reg["sha256"], reg["sha256"][:12])
    changed = spec()
    changed["targets"]["tokenReduction"] = 0.5
    try:
        pe.preregister(changed, base)
        check("V-PEXP-FROZEN", False, "a changed spec re-registered")
    except pe.ExperimentError as exc:
        check("V-PEXP-FROZEN", "NEW experiment" in str(exc), str(exc)[:90])

    pe.save("exp-test", "runs.json", [run(reg, "c1", "baseline", "2025-12-31T00:00:00.000Z")], base)
    try:
        pe.analyze("exp-test", base)
        check("V-PEXP-ORDERING", False, "a run from before registration was analysed")
    except pe.ExperimentError as exc:
        check("V-PEXP-ORDERING", "after preregistration" in str(exc), str(exc)[:90])

    runs = [run(reg, c, v, "2026-01-02T00:00:00.000Z") for c in ("c1", "c2") for v in ("baseline", "candidate")]
    pe.save("exp-test", "runs.json", runs, base)
    pe.save("exp-test", "grades.json", [], base)
    a = pe.analyze("exp-test", base)
    check("V-PEXP-UNGRADED-INCOMPLETE", a["complete"] is False and a["quality"]["baseline"]["score"] is None,
          "no grade -> no quality claim")
    check("V-PEXP-RAW-KEPT", pe.load("exp-test", "runs.json", base)[0]["attempts"][0]["actualModel"] == "claude-x[1m]",
          "runs.json keeps the raw model id")
    check("V-PEXP-ESCAPE", pe.vendor_id("claude-x[1m]") == "claude-x_5b1m_5d"
          and pe.vendor_id("a_b") != pe.vendor_id("a-b") and pe.vendor_id(None) is None,
          pe.vendor_id("claude-x[1m]"))

    real = "exp-successor-packet-002"
    committed = pe.load(real, "analysis.json")
    if committed is None:
        check("V-PEXP-COMMITTED", False, "no committed analysis")
    else:
        tmp = Path(tempfile.mkdtemp(prefix="pexp-real-"))
        for name in ("registration.json", "runs.json", "grades.json"):
            pe.save(real, name, copy.deepcopy(pe.load(real, name)), tmp)
        again = pe.analyze(real, tmp)
        check("V-PEXP-COMMITTED", json.dumps(again, sort_keys=True) == json.dumps(committed, sort_keys=True),
              f"quality {again['quality']['baseline']['score']}/{again['quality']['candidate']['score']} "
              f"token reduction {again['workerTokenReduction']}")
    print(f"PEXP_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
