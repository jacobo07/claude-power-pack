#!/usr/bin/env python3
"""Done-gate for the four enforcement systems (P1-P4) + the UKDL repair.

Every gate here is asserted in BOTH directions. A gate observed only to
PASS is not a gate -- it is a function that returns True. The audit's
whole finding was that the system had rules nobody had ever watched
refuse anything, so each system is made to REFUSE something real:

  P1  the digest is reachable and inside the tool read limit; the
      malformed rules are rejected and CANNOT fire
  P2  an absent artifact FAILS; a real one PASSES; a graceful-failure
      path cannot substitute for the success branch
  P3  a rule with no sweep is REFUSED a seal; a clean sweep is granted
  P4  a broken link is caught; a credential is caught; a missing root
      fails loudly rather than reporting a clean tree

Hermetic: filesystem writes go to a tempdir, never to a global path, so
the suite is re-runnable. Run it three times; it must say the same thing.

    python tools/test_enforcement_systems.py
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.done_gate import ArtifactContract, Kind, Status, gate, verify
from modules.refcheck import RefStatus, lint
from modules.rule_compiler import DIGEST_MAX_BYTES, DIGEST_PATH, compile_rules
from modules.rule_compiler.digest import bucket
from modules.sweep_enforcer import SweepSpec, Verdict, gate_rule_write, seal, sweep

UKDL = Path.home() / ".claude" / "knowledge_vault" / "core" / "ukdl-universal.md"
# The rules the AKOS macro audit named as malformed in the PP archive.
AUDIT_MALFORMED = ["HR-002", "HR-003", "HR-004", "HR-006", "HR-007"]

_passes: list[str] = []
_fails: list[str] = []


def _ok(gate_name: str, evidence: str) -> None:
    _passes.append(gate_name)
    print(f"  [PASS] {gate_name}: {evidence}")


def _fail(gate_name: str, diagnostic: str) -> None:
    _fails.append(gate_name)
    print(f"  [FAIL] {gate_name}: {diagnostic}")


# --------------------------------------------------------------- P1
def t_kill_switch_reachable() -> None:
    if not DIGEST_PATH.exists():
        _fail("V-KILL-SWITCH-REACHABLE",
              f"the digest the router points at does not exist: "
              f"{DIGEST_PATH}. The kill switch is inert again.")
        return
    size = DIGEST_PATH.stat().st_size
    if size > DIGEST_MAX_BYTES:
        _fail("V-KILL-SWITCH-REACHABLE",
              f"digest is {size} B, over the {DIGEST_MAX_BYTES} B budget "
              "-- the agent cannot read it at the trigger point")
        return
    _ok("V-KILL-SWITCH-REACHABLE",
        f"{DIGEST_PATH.name} exists, {size} B (cap {DIGEST_MAX_BYTES})")


def t_digest_covers_valid_rules() -> None:
    res = compile_rules()
    reachable = {r.rule_id for rules in bucket(res.valid).values()
                 for r in rules}
    missing = {r.rule_id for r in res.valid} - reachable
    if missing:
        _fail("V-DIGEST-COVERS-VALID-RULES",
              f"{len(missing)} binding rule(s) unreachable by any trigger "
              f"class: {sorted(missing)[:5]}")
        return
    _ok("V-DIGEST-COVERS-VALID-RULES",
        f"all {len(res.valid)} binding rules reachable by class; "
        "0 omitted")


def t_malformed_rejected() -> None:
    res = compile_rules()
    rejected = {r.rule_id for r in res.rejected}
    still_firing = [r for r in AUDIT_MALFORMED if r not in rejected]
    if still_firing:
        _fail("V-MALFORMED-REJECTED",
              f"these malformed rules are still ACTIVE and can fire: "
              f"{still_firing}")
        return
    # HR-002 is the sharpest case: a ZZZ smoke fixture sealed CRITICAL.
    hr002 = next((r for r in res.rejected if r.rule_id == "HR-002"), None)
    if hr002 is None or not hr002.rejections:
        _fail("V-MALFORMED-REJECTED",
              "HR-002 (the ZZZ smoke fixture) carries no rejection reason")
        return
    reasons = ",".join(x.value for x in hr002.rejections)
    _ok("V-MALFORMED-REJECTED",
        f"{len(AUDIT_MALFORMED)} audit-named rules rejected and INERT; "
        f"HR-002 -> {reasons}")


# --------------------------------------------------------------- P2
def t_done_gate_rejects_proxy(tmp: Path) -> None:
    c = ArtifactContract(name="embeddings",
                         path=str(tmp / "never_written.jsonl"),
                         kind=Kind.JSONL, min_count=1000)
    v = verify(c)
    if v.status is not Status.NEVER_OBSERVED_TO_WORK or v.passed:
        _fail("V-DONE-GATE-REJECTS-PROXY",
              f"an artifact that was never produced returned "
              f"{v.status.value} (passed={v.passed})")
        return
    _ok("V-DONE-GATE-REJECTS-PROXY",
        "absent artifact -> NEVER_OBSERVED_TO_WORK, not a pass")


def t_done_gate_rejects_zero_bytes(tmp: Path) -> None:
    empty = tmp / "zero.jsonl"
    empty.write_text("", encoding="utf-8")
    v = verify(ArtifactContract("embeddings", str(empty), Kind.JSONL))
    if v.status is not Status.EMPTY or v.passed:
        _fail("V-DONE-GATE-REJECTS-EMPTY",
              f"a zero-byte artifact returned {v.status.value}")
        return
    _ok("V-DONE-GATE-REJECTS-EMPTY",
        "zero-byte artifact -> EMPTY (AKOS shipped this as DELIVERED)")


def t_done_gate_rejects_fixture_scale(tmp: Path) -> None:
    small = tmp / "small.jsonl"
    small.write_text('{"id":1}\n{"id":2}\n', encoding="utf-8")
    v = verify(ArtifactContract("index", str(small), Kind.JSONL,
                                min_count=1000))
    if v.status is not Status.TOO_FEW or v.passed:
        _fail("V-DONE-GATE-REJECTS-FIXTURE-SCALE",
              f"2 records against a 1000-record contract returned "
              f"{v.status.value}")
        return
    _ok("V-DONE-GATE-REJECTS-FIXTURE-SCALE",
        "2 records vs a 1000-record contract -> TOO_FEW")


def t_done_gate_accepts_real(tmp: Path) -> None:
    real = tmp / "real.jsonl"
    real.write_text("".join(f'{{"id":{i},"vector":[0.1]}}\n'
                            for i in range(50)), encoding="utf-8")
    v = verify(ArtifactContract("index", str(real), Kind.JSONL,
                                min_count=50,
                                required_keys=("id", "vector")))
    if not v.passed:
        _fail("V-DONE-GATE-ACCEPTS-REAL",
              f"a real artifact was rejected: {v.status.value} {v.detail}")
        return
    _ok("V-DONE-GATE-ACCEPTS-REAL",
        f"PASS with evidence on disk: {v.resolved_path} "
        f"({v.size_bytes} B, {v.count} records)")


def t_done_gate_failure_branch_is_not_success(tmp: Path) -> None:
    handled = tmp / "handled.txt"
    handled.write_text("error handled gracefully\n", encoding="utf-8")
    res = gate([ArtifactContract("handles_bad_input", str(handled),
                                 is_failure_branch=True)])
    only = res.verdicts[0]
    if not only.passed:
        _fail("V-DONE-GATE-FAILURE-BRANCH",
              "the failure-branch check itself did not pass; the test "
              "cannot prove the substitution is refused")
        return
    if res.passed:
        _fail("V-DONE-GATE-FAILURE-BRANCH",
              "a graceful-failure path alone was accepted as DONE")
        return
    _ok("V-DONE-GATE-FAILURE-BRANCH",
        "failure-branch check PASSES yet the gate is NOT DONE -- it "
        "cannot substitute for the success branch")


# --------------------------------------------------------------- P3
def t_sweep_gates_write() -> None:
    allowed, reason = gate_rule_write("U-99", "a rule nobody swept", None)
    if allowed:
        _fail("V-SWEEP-GATES-WRITE",
              "a prevention rule with no sweep was allowed into the ledger")
        return
    v = seal("U-99", "a rule nobody swept", None)
    if v.verdict is not Verdict.REJECTED_NO_SWEEP:
        _fail("V-SWEEP-GATES-WRITE",
              f"expected REJECTED_NO_SWEEP, got {v.verdict.value}")
        return
    _ok("V-SWEEP-GATES-WRITE",
        "unswept rule -> REJECTED_NO_SWEEP; write to UKDL denied")


def t_sweep_finds_gaps(tmp: Path) -> None:
    (tmp / "good.py").write_text(
        "def save(p, t):\n    tmp.write_text(t)\n    os.replace(tmp, p)\n",
        encoding="utf-8")
    (tmp / "legacy.py").write_text(
        "def save(p, t):\n    p.write_text(t)\n", encoding="utf-8")
    spec = SweepSpec(site_pattern=r"def save\(",
                     fix_pattern=r"os\.replace", include="*.py")
    res = sweep(spec, tmp)
    if len(res.sites) != 2:
        _fail("V-SWEEP-FINDS-GAPS",
              f"expected 2 governed sites, found {len(res.sites)}")
        return
    v = seal("U-X", "writes must be atomic", res)
    if v.verdict is not Verdict.REJECTED_GAPS or len(res.gaps) != 1:
        _fail("V-SWEEP-FINDS-GAPS",
              f"the unpatched legacy site was not caught: "
              f"{v.verdict.value}, {len(res.gaps)} gap(s)")
        return
    if not v.collapse_proposal:
        _fail("V-SWEEP-FINDS-GAPS",
              "2 governed sites produced no collapse proposal")
        return
    _ok("V-SWEEP-FINDS-GAPS",
        "the one unswept legacy site -> REJECTED_GAPS + collapse proposal "
        "(this is U-2's exact shape)")


def t_sweep_seals_clean(tmp: Path) -> None:
    (tmp / "a.py").write_text(
        "def save(p, t):\n    os.replace(tmp, p)\n", encoding="utf-8")
    (tmp / "b.py").write_text(
        "def save(p, t):\n    os.replace(tmp, p)\n", encoding="utf-8")
    spec = SweepSpec(site_pattern=r"def save\(",
                     fix_pattern=r"os\.replace", include="*.py")
    v = seal("U-Y", "writes must be atomic", sweep(spec, tmp))
    if v.verdict is not Verdict.ACCEPTED:
        _fail("V-SWEEP-SEALS-CLEAN",
              f"a fully-compliant sweep was refused: {v.verdict.value}")
        return
    _ok("V-SWEEP-SEALS-CLEAN", "all sites comply -> ACCEPTED")


def t_sweep_refuses_empty_site_list(tmp: Path) -> None:
    spec = SweepSpec(site_pattern=r"def nothing_matches_this\(",
                     fix_pattern=r"x", include="*.py")
    v = seal("U-Z", "governs nothing", sweep(spec, tmp))
    if v.sealed:
        _fail("V-SWEEP-REFUSES-VACUOUS",
              "a rule governing ZERO sites was sealed -- all([]) is True, "
              "and that is how a gate becomes vacuous")
        return
    _ok("V-SWEEP-REFUSES-VACUOUS",
        "0 governed sites -> refused (a rule that governs nothing "
        "prevents nothing)")


# --------------------------------------------------------------- P4
def t_refcheck_finds_broken(tmp: Path) -> None:
    doc = tmp / "doc.md"
    doc.write_text(
        "See [the gate](scripts/n8n_validate.py) before delivery.\n"
        "Also [this one](./also_missing.md).\n",
        encoding="utf-8")
    rep = lint([tmp], scan_secrets=False, repo_root=tmp)
    broken = [r for r in rep.refs if r.status is RefStatus.BROKEN]
    if len(broken) != 2:
        _fail("V-REFCHECK-FINDS-BROKEN",
              f"expected 2 broken links, found {len(broken)}: "
              f"{[r.raw for r in broken]}")
        return
    if rep.clean:
        _fail("V-REFCHECK-FINDS-BROKEN",
              "the report claims clean while holding broken links")
        return
    _ok("V-REFCHECK-FINDS-BROKEN",
        f"2 dead links flagged: {', '.join(r.raw for r in broken)}")


def t_refcheck_no_false_positive_on_prose(tmp: Path) -> None:
    doc = tmp / "prose.md"
    doc.write_text(
        "Add `node_modules/` and `.next/` to .gitignore.\n"
        "The convention is `RESUMPTION_FILE.md` at the repo root.\n",
        encoding="utf-8")
    rep = lint([tmp], scan_secrets=False, repo_root=tmp)
    broken = [r for r in rep.refs if r.status is RefStatus.BROKEN]
    if broken:
        _fail("V-REFCHECK-NO-FALSE-BROKEN",
              f"prose paths were gated as BROKEN: {[r.raw for r in broken]} "
              "-- a report full of false positives is a report nobody reads")
        return
    unresolved = [r for r in rep.refs if r.status is RefStatus.UNRESOLVED]
    if not unresolved:
        _fail("V-REFCHECK-NO-FALSE-BROKEN",
              "prose paths vanished entirely; they should be advisory, "
              "not silently dropped")
        return
    _ok("V-REFCHECK-NO-FALSE-BROKEN",
        f"{len(unresolved)} prose path(s) advisory, 0 gated as broken")


def t_refcheck_finds_secret(tmp: Path) -> None:
    # Synthetic and clearly fake (HR-SECRET-005). Real-format-but-fake is
    # the point: it SHOULD trip the detector, proving the detector fires.
    env = tmp / "config.json"
    env.write_text(
        '{"auth_token": "FAKE-NOT-A-REAL-TOKEN-0000",\n'
        ' "DASH_SOME_PWD": "FAKE-NOT-REAL-0000"}\n',
        encoding="utf-8")
    rep = lint([tmp], scan_secrets=True, repo_root=tmp)
    if not rep.credentials:
        _fail("V-REFCHECK-FINDS-SECRET",
              "a file carrying auth_token and a _PWD key was not flagged")
        return
    signals = " | ".join(c.signal for c in rep.credentials)
    for c in rep.credentials:
        if "FAKE-NOT" in c.signal:
            _fail("V-REFCHECK-FINDS-SECRET",
                  "the finding leaked the credential VALUE (HR-SECRET-002)")
            return
    if rep.clean:
        _fail("V-REFCHECK-FINDS-SECRET",
              "the report claims clean while holding credential findings")
        return
    _ok("V-REFCHECK-FINDS-SECRET",
        f"{len(rep.credentials)} credential finding(s), values redacted: "
        f"{signals}")


def t_refcheck_missing_root_is_loud(tmp: Path) -> None:
    try:
        lint([tmp / "does_not_exist"], scan_secrets=False, repo_root=tmp)
    except FileNotFoundError:
        _ok("V-REFCHECK-LOUD-ON-MISSING-ROOT",
            "a root that does not exist raises rather than reporting clean")
        return
    _fail("V-REFCHECK-LOUD-ON-MISSING-ROOT",
          "a nonexistent root was silently accepted -- the linter would "
          "report a clean tree for a tree that is not there")


# ------------------------------------------------------- UKDL repair
def t_ukdl_no_collision() -> None:
    if not UKDL.exists():
        _fail("V-UKDL-NO-COLLISION", f"ledger not found: {UKDL}")
        return
    text = UKDL.read_text(encoding="utf-8-sig")
    ids = re.findall(r"^## (U-\d+[a-z]?)\b", text, re.M)
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        _fail("V-UKDL-NO-COLLISION",
              f"duplicate ids back in the ledger: {dupes}")
        return
    _ok("V-UKDL-NO-COLLISION",
        f"{len(ids)} entries, every id unique (U-16 x1, U-17 x1)")


def t_ukdl_new_lessons_present() -> None:
    text = UKDL.read_text(encoding="utf-8-sig")
    want = ["U-26", "U-27", "U-28", "U-29"]
    missing = [u for u in want if text.count(f"## {u} —") != 1]
    if missing:
        _fail("V-UKDL-U26-U29",
              f"expected exactly 1 heading each; wrong for: {missing}")
        return
    _ok("V-UKDL-U26-U29",
        "U-26 rule-archive-is-a-machine-artifact, U-27 schema-gate, "
        "U-28 queue-depth-alarm, U-29 governance-volume -- 1 heading each")


# -------------------------------------------------------------- base
def t_baseline_imports() -> None:
    try:
        import modules.done_gate  # noqa: F401
        import modules.refcheck  # noqa: F401
        import modules.rule_compiler  # noqa: F401
        import modules.sweep_enforcer  # noqa: F401
    except ImportError as exc:
        _fail("V-BASELINE", f"a new module does not import: {exc}")
        return
    _ok("V-BASELINE", "all four enforcement modules import clean")


def main() -> int:
    print("=== ENFORCEMENT SYSTEMS DONE-GATE (P1-P4 + UKDL) ===\n")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        print("P1 -- Rule Compiler")
        t_kill_switch_reachable()
        t_digest_covers_valid_rules()
        t_malformed_rejected()

        print("\nP2 -- Artifact Done-Gate")
        t_done_gate_rejects_proxy(tmp)
        t_done_gate_rejects_zero_bytes(tmp)
        t_done_gate_rejects_fixture_scale(tmp)
        t_done_gate_accepts_real(tmp)
        t_done_gate_failure_branch_is_not_success(tmp)

        print("\nP3 -- Sweep Enforcer")
        t_sweep_gates_write()
        for name in ("sweep_gaps", "sweep_clean", "sweep_empty"):
            (tmp / name).mkdir(exist_ok=True)
        t_sweep_finds_gaps(tmp / "sweep_gaps")
        t_sweep_seals_clean(tmp / "sweep_clean")
        t_sweep_refuses_empty_site_list(tmp / "sweep_empty")

        print("\nP4 -- Reference Integrity Linter")
        for name in ("rc_broken", "rc_prose", "rc_secret"):
            (tmp / name).mkdir(exist_ok=True)
        t_refcheck_finds_broken(tmp / "rc_broken")
        t_refcheck_no_false_positive_on_prose(tmp / "rc_prose")
        t_refcheck_finds_secret(tmp / "rc_secret")
        t_refcheck_missing_root_is_loud(tmp)

        print("\nUKDL repair")
        t_ukdl_no_collision()
        t_ukdl_new_lessons_present()

        print("\nBaseline")
        t_baseline_imports()

    total = len(_passes) + len(_fails)
    print(f"\nENFORCEMENT_PASS={len(_passes)}/{total}  threshold={total}/{total}")
    if _fails:
        print(f"FAILED GATES: {_fails}")
    return 0 if not _fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
