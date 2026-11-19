"""diagnosis.py -- CPP-DBG-001: causal-proof verifier for a bug-diagnosis record.

Owner: craif (declared causal authority in vault/audits/usirc/BOUNDARY_CONTRACT.md).
Reality Scan (bcap-2 phase 1) found that CRAIF's code only owns the liveness repair
transaction and says "diagnosis is explicitly not CRAIF's role" (candidate.py), while the
boundary contract names CRAIF the owner of causal candidates, evidence and closure. This
module is the executable half of that contract: it does NOT run the investigation and it is
not a second incident ledger. It judges a *record* of one investigation (DBG-C01..C08) and
refuses a causal/closure claim the evidence does not support. Absent evidence is UNMEASURED,
never a pass.

CLI: python3 -m modules.craif.diagnosis <record.json>   (exit 0 iff VERIFIED or an honest
NOT_REPRODUCED/UNRESOLVED; exit 1 on any rejection)
"""
from __future__ import annotations

import json
import math
import re
import sys
from dataclasses import dataclass, field

TIERS = ("LIGHT", "STANDARD", "FORENSIC")
HONEST_STATES = ("NOT_REPRODUCED", "UNRESOLVED")
CLAIMS = ("FIXED", "ROOT_CAUSE_CONFIRMED") + HONEST_STATES
_SECRET_RE = re.compile(
    r"(authorization\s*[:=]\s*\S+|bearer\s+[A-Za-z0-9._\-]{8,}|set-cookie\s*:|cookie\s*:\s*\S+|"
    r"sk-[A-Za-z0-9_\-]{16,}|ghp_[A-Za-z0-9]{20,}|password\s*[\"']?\s*[:=]\s*[\"']?\S+)",
    re.I,
)
_CONFIDENCE = 0.95  # a flaky bug is "fixed" only when a clean streak this long is >=95% unlikely by chance


@dataclass
class Verdict:
    status: str                      # VERIFIED | HONEST_UNRESOLVED | REJECTED
    rejections: list[str] = field(default_factory=list)
    unmeasured: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status != "REJECTED"


def classify_tier(symptom_scope: str, intermittent: bool = False, external: bool = False) -> str:
    """DBG-C07: a localised defect is LIGHT; unknown-component spread STANDARD; the
    concurrency/intermittent/production/perf/security/data class is FORENSIC."""
    if intermittent or external or symptom_scope in ("concurrency", "performance", "security", "data"):
        return "FORENSIC"
    if symptom_scope in ("single_line", "localised"):
        return "LIGHT"
    return "STANDARD"


def required_clean_runs(failures: int, attempts: int) -> int | None:
    """Clean runs needed after a fix before 'fixed' beats chance at 95%. None when the
    original failure rate is unmeasurable (no attempts or no failures observed)."""
    if attempts <= 0 or failures <= 0:
        return None
    p = failures / attempts
    if p >= 1.0:
        return 1
    return math.ceil(math.log(1.0 - _CONFIDENCE) / math.log(1.0 - p))


def assess(rec: dict) -> Verdict:
    rej: list[str] = []
    unm: list[str] = []
    sym = rec.get("symptom") or {}
    loop = rec.get("loop") or {}
    mini = rec.get("minimisation") or {}
    fix = rec.get("fix") or {}
    inst = rec.get("instrumentation") or {}
    claim = rec.get("claim")
    tier = rec.get("tier")
    reproduced = bool(loop.get("red_observed"))

    # claim vocabulary / tier: unknown values are rejected, never defaulted.
    if claim not in CLAIMS:
        rej.append("DBG-CLAIM-UNKNOWN")
    if tier not in TIERS:
        rej.append("DBG-TIER-UNKNOWN")

    # C01 snapshot
    for k in ("verbatim", "expected", "observed", "commit"):
        if not sym.get(k):
            rej.append("DBG-C01-SNAPSHOT-INCOMPLETE")
            break

    # C07 honest non-reproduction (fixture 12): no red => no causal/closure claim.
    if claim in HONEST_STATES:
        if claim == "NOT_REPRODUCED" and not (loop.get("attempts_documented") or rec.get("attempts")):
            rej.append("DBG-C07-NON-REPRODUCTION-UNDOCUMENTED")
        if claim == "UNRESOLVED" and not any(h.get("disposition") == "unresolved" for h in rec.get("hypotheses", [])):
            unm.append("no hypothesis recorded as unresolved")
    elif not reproduced:
        rej.append("DBG-C07-INVENTED-RCA")

    if claim in ("FIXED", "ROOT_CAUSE_CONFIRMED"):
        # C02 loop validity
        if loop.get("red_reason") in ("syntax", "import", "timeout", "harness"):
            rej.append("DBG-C02-FALSE-RED")                       # fixture 1
        if loop.get("oracle_kind") != "exact":
            rej.append("DBG-C02-WEAK-ORACLE")                     # fixture 2
        if loop.get("entrypoint") == "mock" and not loop.get("mock_equivalence_proven"):
            rej.append("DBG-C02-CONTRACT-MISMATCH")               # fixture 3
        if not loop.get("negative_control"):
            rej.append("DBG-C02-NO-NEGATIVE-CONTROL")

        # C03 minimisation faithfulness (fixtures 4, 17)
        dropped = set(mini.get("final_dropped", []))
        for step in mini.get("steps", []):
            if not step.get("bug_persisted", True) and step.get("removed") in dropped:
                rej.append("DBG-C03-UNFAITHFUL-MINIMISATION")
                break
        div = rec.get("divergence") or {}
        if div and div.get("causal_position") is not None and div.get("visible_position") is not None:
            if div["causal_position"] < div["visible_position"] and div.get("cause_claimed_at") == div["visible_position"]:
                rej.append("DBG-C03-VISIBLE-SYMPTOM-IS-NOT-CAUSE")  # fixture 5

        # C04 hypotheses (fixtures 6, 7, 20)
        hyps = rec.get("hypotheses", [])
        if tier != "LIGHT":
            if len(hyps) < 2:
                rej.append("DBG-C04-NO-COMPETING-HYPOTHESES")
            preds = [h.get("predicts_if_true") for h in hyps]
            if len(set(map(str, preds))) < len(preds):
                rej.append("DBG-C04-NON-DISCRIMINATING")
            for h in hyps:
                if h.get("disposition") == "supported":
                    if h.get("own_probe_falsified") or h.get("corroborations", 0) < 2:
                        rej.append("DBG-C04-INSUFFICIENT-CORROBORATION")
                        break
        if tier == "FORENSIC" and sym.get("scope") in ("single_line", "localised") and rec.get("agents_used", 1) > 1:
            rej.append("DBG-C07-OVER-CEREMONY")                    # fixture 20

        # C05 intermittent statistics (fixture 8) and perf confounds (fixture 9)
        trig = loop.get("trigger") or {}
        if trig.get("kind") == "probabilistic":
            need = required_clean_runs(trig.get("failures", 0), trig.get("attempts", 0))
            if need is None:
                unm.append("flake rate unmeasured")
                rej.append("DBG-C05-FLAKE-RATE-UNMEASURED")
            elif fix.get("clean_runs_after_fix", 0) < need:
                rej.append("DBG-C05-FLAKE-UNDERPOWERED")
        perf = rec.get("perf")
        if perf is not None and not (perf.get("baseline_pinned") and perf.get("host_load_stable") and perf.get("same_inputs")):
            rej.append("DBG-C05-MEASUREMENT-CONFOUNDED")

        # C05/C08 instrumentation and redaction (fixtures 14, 15)
        if _SECRET_RE.search(json.dumps(rec.get("evidence_text", ""))) and not inst.get("redaction_applied"):
            rej.append("DBG-C05-SECRET-LEAK")
        for m in inst.get("markers", []):
            if not m.get("removed_proof") and not (m.get("retained") and m.get("owner")):
                rej.append("DBG-C08-LEFTOVER-INSTRUMENTATION")
                break
        h = rec.get("harness") or {}
        if h and (not h.get("bounded") or h.get("orphan_pids", 0) > 0):
            rej.append("DBG-C07-UNBOUNDED-HARNESS")                # fixture 13

        # provenance (fixture 16)
        for a in rec.get("artifacts", []):
            if a.get("worktree") != sym.get("worktree") or a.get("commit") != sym.get("commit"):
                rej.append("DBG-C05-UNBOUND-PROVENANCE")
                break

        # C06 fix and original-path closure (fixtures 10, 11, 17, 18)
        if fix.get("mitigation_only"):
            rej.append("DBG-C06-MITIGATION-NOT-RESOLUTION")
        if fix.get("regression_seam") == "unit" and fix.get("multi_caller_still_failing"):
            rej.append("DBG-C06-SHALLOW-SEAM")
        if fix.get("original_path_rerun") != "green":
            rej.append("DBG-C06-ORIGINAL-PATH-NOT-GREEN")
        mut = fix.get("mutation_detects")
        if mut is False:
            rej.append("DBG-C06-BLIND-REGRESSION-GATE")
        elif mut is None:
            unm.append("regression sensitivity (mutation) unmeasured")

    # C08 promotion (fixture 19): only a verified, contradiction-free record may promote.
    promo = rec.get("promotion") or {}
    if promo.get("requested"):
        contradictory = (
            bool(rec.get("contradictions"))
            or any(h.get("disposition") == "unresolved" for h in rec.get("hypotheses", []))
            or claim in HONEST_STATES
            or bool(rej)
        )
        if contradictory:
            rej.append("DBG-C08-PROMOTION-REFUSED")

    rej = list(dict.fromkeys(rej))
    if rej:
        return Verdict("REJECTED", rej, unm)
    if claim in HONEST_STATES:
        return Verdict("HONEST_UNRESOLVED", [], unm)
    return Verdict("VERIFIED", [], unm)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: python3 -m modules.craif.diagnosis <record.json>", file=sys.stderr)
        return 2
    with open(argv[0], encoding="utf-8") as fh:
        rec = json.load(fh)
    v = assess(rec)
    print(json.dumps({"status": v.status, "rejections": v.rejections, "unmeasured": v.unmeasured}))
    return 0 if v.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
