#!/usr/bin/env python3
"""USEA constitutional-law ownership audit.

LAW IV requires every important responsibility to have one legitimate
architectural owner, and section 9 requires that a new component earn its
existence against the owners that already exist.

This audit answers, for each of the fifteen constitutional laws: does Claude
Power Pack already own this, and where. It is executable rather than prose
because a hand-written ownership table is a snapshot of somebody's memory --
it cannot notice when an owner is deleted, renamed, or was never there. This
one fails.

Verdicts follow the constitution's own vocabulary (section 3):
    REUSE       an existing owner satisfies the law as-is
    EXTEND      an owner exists and needs additional reach
    CONNECT     owners exist but nothing composes them
    NEW         no legitimate owner can satisfy the responsibility

A NEW verdict requires evidence, and this tool's job is to make that evidence
hard to fake: a law is only claimed as owned if the cited artifact is on disk.

Exit codes mirror the corpus gate's discipline -- a run that broke has not
judged anything:
    0  audit ran, every cited owner resolves
    1  audit ran, one or more cited owners are MISSING (the claim is false)
    4  the audit itself failed
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Law:
    numeral: str
    name: str
    verdict: str
    owners: list[str]
    gap: str = ""
    resolved: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)


# The mapping is a CLAIM. Every path below is checked against the filesystem;
# an unresolvable path is reported as a false claim rather than quietly dropped.
LAWS: list[Law] = [
    Law("I", "REALITY FIRST", "REUSE",
        ["modules/sdd_os", "modules/error_prevention/premise_verifier.py",
         "modules/repo_identity/identity.py"],
        gap="Reality Scan is doctrine in CLAUDE.md, not a callable obligation."),
    Law("II", "ARCHITECTURAL TRUTH", "EXTEND",
        ["modules/arch-decision", "modules/architecture_horizon",
         "modules/contract_fabric"],
        gap="Nothing distinguishes 'target reached' from 'reached through a "
            "valid architectural state'. This is the thinnest coverage found."),
    Law("III", "EMPIRICAL AUTHORITY", "REUSE",
        ["modules/oracle/ovo-protocol.md", "modules/intent_verified"]),
    Law("IV", "OWNERSHIP", "REUSE",
        ["modules/duplicate_to_advantage/d2a_engine.py", "modules/spec_gate/gate.py"]),
    Law("V", "MINIMUM SUFFICIENT CHANGE", "REUSE",
        ["modules/one_shot/compiler.py", "modules/one_shot/lock.py"]),
    Law("VI", "DETERMINISTIC SUPREMACY", "REUSE",
        ["modules/oracle/ovo-protocol.md", "modules/uqf"]),
    Law("VII", "VERSION TRUTH", "REUSE",
        ["modules/dependency_sovereignty/sovereignty.py"]),
    Law("VIII", "FAILURE AS EVIDENCE", "REUSE",
        ["modules/cascade_prevention/engine.py", "modules/drift_registry"]),
    Law("IX", "NO VAPOR DONE", "EXTEND",
        ["modules/done_gate/artifact_done_gate.py", "modules/output_contracts"],
        gap="Completion is binary (done / not done). The constitution's "
            "section 26 defines THIRTEEN graded states and forbids claiming a "
            "stronger one than evidence supports. No owner grades a claim."),
    Law("X", "PRODUCTION REALITY", "REUSE",
        ["modules/sleepless_qa", "modules/deployment"]),
    Law("XI", "NEGATIVE CAPABILITY", "REUSE",
        ["modules/duplicate_to_advantage", "modules/hard_rules/residual.py"]),
    Law("XII", "SCOPE-AWARE LEARNING", "REUSE",
        ["modules/recall_roi", "modules/fable_distillation"]),
    Law("XIII", "NO SILENT REGRESSION", "REUSE",
        ["modules/sqi", "modules/liveness/reachability.py"]),
    Law("XIV", "CAUSAL REPAIR", "REUSE",
        ["modules/cascade_prevention", "modules/error_prevention"]),
    Law("XV", "INFORMATION EFFICIENCY", "REUSE",
        ["modules/token-optimizer", "modules/cognitive_load", "modules/recall_roi"]),
]

# The incumbent for the completeness half of the constitution. Named separately
# because it is a global skill, not a Power Pack module, and an audit scoped to
# modules/ would not see it -- which is how a duplicate gets built.
INCUMBENT = Path.home() / ".claude" / "skills" / "software-best-practices" / "instructions.md"


def audit() -> tuple[list[Law], list[str]]:
    notes: list[str] = []
    for law in LAWS:
        for rel in law.owners:
            (law.resolved if (REPO_ROOT / rel).exists() else law.missing).append(rel)
    if INCUMBENT.exists():
        notes.append(f"INCUMBENT present: {INCUMBENT}")
    else:
        notes.append(f"INCUMBENT ABSENT (expected): {INCUMBENT}")
    return LAWS, notes


def main() -> int:
    try:
        laws, notes = audit()
    except Exception as exc:  # noqa: BLE001 - the audit's own failure branch
        print(f"USEA OWNERSHIP AUDIT: GATE_FAILED  {type(exc).__name__}: {exc}")
        print("  NOTE: the audit failed; ownership was NOT judged.")
        return 4

    by_verdict: dict[str, int] = {}
    total_missing = 0

    print("USEA CONSTITUTIONAL OWNERSHIP AUDIT")
    print("=" * 72)
    for law in laws:
        by_verdict[law.verdict] = by_verdict.get(law.verdict, 0) + 1
        flag = "  " if not law.missing else "!!"
        print(f"{flag} LAW {law.numeral:<5} {law.name:<28} {law.verdict}")
        for r in law.resolved:
            print(f"      ok      {r}")
        for m in law.missing:
            total_missing += 1
            print(f"      MISSING {m}   <-- ownership claim is FALSE")
        if law.gap:
            print(f"      gap:    {law.gap}")
    print("=" * 72)
    for n in notes:
        print(n)

    owned = sum(1 for lw in laws if lw.verdict == "REUSE")
    print(f"\nverdicts: {by_verdict}")
    print(f"laws already owned outright (REUSE): {owned}/{len(laws)}")
    print(f"unresolvable ownership claims: {total_missing}")
    print(f"OWNERSHIP_AUDIT_PASS={len(laws) - total_missing}/{len(laws)}")

    if total_missing:
        print("\nAn unresolvable claim means this audit asserted an owner that is "
              "not on disk. Fix the claim, not the number.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
