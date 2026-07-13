#!/usr/bin/env python3
"""Done-gate for the DAIF Session Continuity Cognitive Compiler (DAIF-08 Part XI).

The corpus specifies. This runner is where the specification either survives contact with a real
session or is refused. Every gate below is measured against real inputs — a real .jsonl from this
machine, the real CLAUDE.md of this repo — because DAIF-08 11.7 forbids asserting a figure in
advance and DAIF-07 12.6 forbids asserting fidelity that has not been DRILLED.

The drill (V-CONTINUITY-GATE-*) is adversarial by construction: the package is compiled, and then a
FRESH OS PROCESS is handed the package file and nothing else — no transcript, no repository, no
import of the compiler — and asked what survived. A verifier that could fall back on the session
would be the near side of the boundary wearing a costume.

Gates:
  V-OBLIGATION-EXTRACTOR-REAL      obligations lifted from a real session, not a fixture
  V-OBLIGATION-EXTRACTOR-FAILOPEN  empty / corrupt / missing session -> [], exit 0
  V-CONSTRAINT-EXTRACTOR-REAL      the PP's own sealed hard rules, with their file:line
  V-COMPILER-PRODUCES-PACKAGE      every slot DAIF-08 11.3 requires is present
  V-CONTINUITY-GATE-CONSTRAINTS    100% of hard constraints survive the reset, or FAIL with detail
  V-CONTINUITY-GATE-OBLIGATIONS    100% of open obligations survive the reset, or FAIL with detail
  V-NO-INVENTED-CLAIMS             the far side reports nothing the near side did not compile
  V-FAIL-VISIBLE-OBSERVED          the seventh clause is observed to REFUSE (never-refusing == inert)
  V-DAIF-PASS-COUNT                the corpus gate still passes at its full count (no regression)

Run:  python tools/test_daif_session_compiler.py
Exit: 0 iff every gate passes.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules.daif.constraint_extractor import extract_constraints   # noqa: E402
from modules.daif.obligation_extractor import extract_obligations   # noqa: E402
from modules.daif.session_continuity_compiler import (              # noqa: E402
    compile_session, write_package,
)

RESUME_READER = ROOT / "modules" / "daif" / "resume_reader.py"
SESSIONS_DIR = Path.home() / ".claude" / "projects" / "C--Users-User--claude-skills-claude-power-pack"
DAIF_CORPUS_GATE_BASELINE = 48   # 8 datasets x 6 gates, sealed at SCS C95

_passes: list[str] = []
_fails: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    print(f"  [OK  ] {gate}: {evidence}")
    _passes.append(gate)


def _fail(gate: str, diagnostic: str) -> None:
    print(f"  [FAIL] {gate}: {diagnostic}")
    _fails.append(gate)


def _real_session() -> Path | None:
    """The largest real transcript on this machine. Real input, never a fixture."""
    if not SESSIONS_DIR.is_dir():
        return None
    sessions = sorted(SESSIONS_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_size, reverse=True)
    return sessions[0] if sessions else None


def _resume_far_side(package_path: Path, workdir: Path) -> dict:
    """Cross the boundary. A separate process, a different working directory, the package alone."""
    proc = subprocess.run(
        [sys.executable, str(RESUME_READER), str(package_path)],
        capture_output=True, text=True, cwd=str(workdir), timeout=120,
    )
    if proc.returncode != 0:
        return {"readable": False, "error": proc.stderr[:400]}
    try:
        return json.loads(proc.stdout)
    except (json.JSONDecodeError, ValueError) as exc:
        return {"readable": False, "error": f"far side emitted unparseable output: {exc}"}


# ---------------------------------------------------------------------------

def gate_obligation_extractor_real(session: Path) -> None:
    obligations, report = extract_obligations(session)
    if not obligations:
        _fail("V-OBLIGATION-EXTRACTOR-REAL",
              f"0 obligations from {session.name} ({report['turns_scanned']} turns scanned)")
        return
    unsourced = [o.identifier for o in obligations if not o.source]
    if unsourced:
        _fail("V-OBLIGATION-EXTRACTOR-REAL", f"{len(unsourced)} obligation(s) carry no source pointer")
        return
    kinds = ", ".join(f"{k}={v}" for k, v in report["by_kind"].items())
    _ok("V-OBLIGATION-EXTRACTOR-REAL",
        f"{len(obligations)} open obligations from a real session ({report['turns_scanned']} turns; {kinds})")


def gate_obligation_extractor_failopen() -> None:
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        empty = d / "empty.jsonl"
        empty.write_text("", encoding="utf-8")
        corrupt = d / "corrupt.jsonl"
        corrupt.write_text('{not json\n\x00garbage\n{"type":"user"}\n'
                           '{"type":"user","message":{"content":42}}\n', encoding="utf-8")
        missing = d / "no_such_session.jsonl"
        try:
            a, _ = extract_obligations(empty)
            b, _ = extract_obligations(corrupt)
            c, _ = extract_obligations(missing)
        except Exception as exc:                                  # noqa: BLE001 — the gate IS the catch
            _fail("V-OBLIGATION-EXTRACTOR-FAILOPEN", f"raised {type(exc).__name__}: {exc}")
            return
    if a or b or c:
        _fail("V-OBLIGATION-EXTRACTOR-FAILOPEN",
              f"expected [] on all three, got empty={len(a)} corrupt={len(b)} missing={len(c)}")
        return
    _ok("V-OBLIGATION-EXTRACTOR-FAILOPEN", "empty / corrupt / missing session each return [], no raise")


def gate_constraint_extractor_real() -> None:
    constraints, report = extract_constraints(ROOT)
    hard = [c for c in constraints if c.strength == "hard"]
    sealed = [c for c in hard if re.match(r"^HR-", c.identifier)]
    if not sealed:
        _fail("V-CONSTRAINT-EXTRACTOR-REAL", "0 sealed HR-* rules extracted from this repo")
        return
    unprovenanced = [c.identifier for c in hard if not c.provenance or c.provenance == "unknown"]
    if unprovenanced:
        _fail("V-CONSTRAINT-EXTRACTOR-REAL",
              f"{len(unprovenanced)} constraint(s) with no provenance — a rumor, per DAIF-01 2.4")
        return
    sample = sealed[0]
    _ok("V-CONSTRAINT-EXTRACTOR-REAL",
        f"{len(hard)} hard ({len(sealed)} sealed HR-*), every one provenanced; "
        f"e.g. {sample.identifier} @ {sample.provenance}")


def gate_compiler_produces_package(package: dict) -> None:
    required = ["mission_contract", "hard_constraints", "decisions_with_justifications",
                "current_reality", "open_obligations", "evidence_pointers", "expansion_handles",
                "done_gate", "compiled_at", "session_id", "status", "size"]
    missing = [k for k in required if k not in package]
    if missing:
        _fail("V-COMPILER-PRODUCES-PACKAGE", f"missing slots: {', '.join(missing)}")
        return
    if package.get("savings_claim") is not None:
        _fail("V-COMPILER-PRODUCES-PACKAGE",
              "package asserts a savings figure — forbidden in advance by DAIF-08 11.7")
        return
    size = package["size"]
    if not size["fits_budget"]:
        _fail("V-COMPILER-PRODUCES-PACKAGE",
              f"{size['estimated_tokens']} est. tokens over the {size['budget_tokens']} budget")
        return
    _ok("V-COMPILER-PRODUCES-PACKAGE",
        f"all 8 contents of 11.3 present; {size['estimated_tokens']} est. tokens "
        f"(budget {size['budget_tokens']}); no savings figure asserted")


def gate_continuity_constraints(package: dict, far: dict) -> float:
    before = [c["identifier"] for c in package["hard_constraints"]]
    after = far.get("constraint_ids", [])
    survived = [i for i in before if i in set(after)]
    pct = 100.0 * len(survived) / len(before) if before else 0.0
    lost = [i for i in before if i not in set(after)]
    unauditable = far.get("constraints_without_evidence", [])
    if not before:
        _fail("V-CONTINUITY-GATE-CONSTRAINTS", "0 constraints compiled — nothing to survive")
        return 0.0
    if lost:
        _fail("V-CONTINUITY-GATE-CONSTRAINTS",
              f"{pct:.1f}% survived — {len(lost)} LOST across the boundary: {', '.join(lost[:5])}")
        return pct
    if unauditable:
        _fail("V-CONTINUITY-GATE-CONSTRAINTS",
              f"{len(unauditable)} constraint(s) survived without an evidence pointer (clause 5)")
        return pct
    _ok("V-CONTINUITY-GATE-CONSTRAINTS",
        f"{pct:.0f}% ({len(survived)}/{len(before)}) hard constraints survived a fresh-process reset")
    return pct


def gate_continuity_obligations(package: dict, far: dict) -> float:
    before = [o["identifier"] for o in package["open_obligations"]]
    after = set(far.get("obligation_ids", []))
    closeable = set(far.get("closeable_obligation_ids", []))
    hauntings = far.get("hauntings", [])
    if not before:
        _fail("V-CONTINUITY-GATE-OBLIGATIONS", "0 obligations compiled — nothing to survive")
        return 0.0
    # DAIF-07 12.5 — survival is CLOSEABILITY. A name that survived without its closure condition
    # is a haunting and is counted LOST by this gate, loudly.
    survived = [i for i in before if i in after and i in closeable]
    pct = 100.0 * len(survived) / len(before)
    lost = [i for i in before if i not in after]
    if lost or hauntings:
        detail = []
        if lost:
            detail.append(f"{len(lost)} absent: {', '.join(lost[:5])}")
        if hauntings:
            detail.append(f"{len(hauntings)} haunting(s) (survived as a name, cannot be closed): "
                          + ", ".join(str(h.get("identifier")) for h in hauntings[:5]))
        _fail("V-CONTINUITY-GATE-OBLIGATIONS", f"{pct:.1f}% survived closeable — " + "; ".join(detail))
        return pct
    _ok("V-CONTINUITY-GATE-OBLIGATIONS",
        f"{pct:.0f}% ({len(survived)}/{len(before)}) open obligations survived the reset CLOSEABLE "
        f"(all five resumption elements intact)")
    return pct


def gate_no_invented_claims(package: dict, far: dict) -> None:
    before_c = {c["identifier"] for c in package["hard_constraints"]}
    before_o = {o["identifier"] for o in package["open_obligations"]}
    invented_c = [i for i in far.get("constraint_ids", []) if i not in before_c]
    invented_o = [i for i in far.get("obligation_ids", []) if i not in before_o]
    if invented_c or invented_o:
        _fail("V-NO-INVENTED-CLAIMS",
              f"far side reported {len(invented_c)} constraint(s) and {len(invented_o)} "
              f"obligation(s) the compiler never produced")
        return
    _ok("V-NO-INVENTED-CLAIMS",
        f"far side reported 0 constraints and 0 obligations absent from the compiled package")


def gate_fail_visible_observed(workdir: Path) -> None:
    """A gate never observed to refuse is indistinguishable from an inert one (11.6).

    Two refusals are forced here, on inputs that genuinely cannot be guaranteed."""
    empty_session = workdir / "unreadable.jsonl"
    empty_session.write_text("", encoding="utf-8")
    pkg = compile_session(ROOT, empty_session)
    if pkg["status"] != "FAIL_VISIBLE" or not pkg.get("cannot_guarantee"):
        _fail("V-FAIL-VISIBLE-OBSERVED",
              f"a 0-turn session compiled to status={pkg['status']} instead of refusing")
        return

    # And the far side must refuse a package it cannot read, rather than reporting an empty success.
    broken = workdir / "broken_package.json"
    broken.write_text("{ this is not json", encoding="utf-8")
    far = _resume_far_side(broken, workdir)
    if far.get("readable") is not False:
        _fail("V-FAIL-VISIBLE-OBSERVED", "far side did not refuse an unreadable package")
        return

    # Clause 6 — a source that MOVED while the session was down must be detected. A detector never
    # observed to fire is inert, so it is fired here: a constraint source is edited behind the
    # package's back, and the far side must notice on its own hash rather than trust the record.
    moved_src = workdir / "moving_claude.md"
    moved_src.write_text("# rules\n- MUST hold the line\n", encoding="utf-8")
    stale_pkg = workdir / "stale_package.json"
    stale_pkg.write_text(json.dumps({
        "schema": "daif-08-part-xi/resume-pack/v1",
        "hard_constraints": [], "open_obligations": [],
        "integrity": {"constraint_sources": [
            {"source": "moving_claude.md", "path": str(moved_src),
             "sha256": "0" * 64},          # the world as the pack recorded it
        ]},
    }), encoding="utf-8")
    moved_src.write_text("# rules\n- MUST hold the line\n- and one more, added after the boundary\n",
                         encoding="utf-8")
    stale_far = _resume_far_side(stale_pkg, workdir)
    if not stale_far.get("moved_sources"):
        _fail("V-FAIL-VISIBLE-OBSERVED",
              "clause 6 detector did not fire on a source that changed while the session was down")
        return

    _ok("V-FAIL-VISIBLE-OBSERVED",
        f"three refusals observed: a 0-turn session ({len(pkg['cannot_guarantee'])} named gap(s)); "
        f"an unreadable package; a constraint source that moved behind the pack's back")


def gate_daif_pass_count() -> None:
    """The corpus gate must not regress. The compiler is new work, not a licence to break DAIF."""
    runner = ROOT / "tools" / "test_daif.py"
    if not runner.is_file():
        _fail("V-DAIF-PASS-COUNT", "tools/test_daif.py is missing")
        return
    proc = subprocess.run([sys.executable, str(runner)], capture_output=True, text=True,
                          cwd=str(ROOT), timeout=300)
    m = re.search(r"DAIF_PASS=(\d+)/(\d+)", proc.stdout)
    if not m:
        _fail("V-DAIF-PASS-COUNT", "corpus gate emitted no DAIF_PASS line")
        return
    got, total = int(m.group(1)), int(m.group(2))
    if proc.returncode != 0 or got != total or got < DAIF_CORPUS_GATE_BASELINE:
        _fail("V-DAIF-PASS-COUNT",
              f"corpus gate regressed: DAIF_PASS={got}/{total} (baseline {DAIF_CORPUS_GATE_BASELINE}), "
              f"exit={proc.returncode}")
        return
    _ok("V-DAIF-PASS-COUNT", f"corpus gate holds at DAIF_PASS={got}/{total} (baseline {DAIF_CORPUS_GATE_BASELINE})")


def main() -> int:
    print("== DAIF Session Continuity Compiler — done-gate ==")
    session = _real_session()
    if session is None:
        print("  [FAIL] no real session transcript found — this gate refuses to run on a fixture")
        return 1
    print(f"  session: {session.name} ({session.stat().st_size:,} bytes)\n")

    gate_obligation_extractor_real(session)
    gate_obligation_extractor_failopen()
    gate_constraint_extractor_real()

    package = compile_session(ROOT, session)
    gate_compiler_produces_package(package)

    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        # The boundary: the package is written to durable ground, and everything else is gone.
        pkg_path = write_package(package, ROOT, workdir / "continuity.json")
        far = _resume_far_side(pkg_path, workdir)
        if not far.get("readable"):
            print(f"  [FAIL] the far side could not read the package: {far.get('error')}")
            return 1

        c_pct = gate_continuity_constraints(package, far)
        o_pct = gate_continuity_obligations(package, far)
        gate_no_invented_claims(package, far)
        gate_fail_visible_observed(workdir)

    gate_daif_pass_count()

    total = len(_passes) + len(_fails)
    print(f"\n  measured survival: hard constraints {c_pct:.0f}%  |  open obligations {o_pct:.0f}%")
    print(f"  clauses 3 and 4 of the 11.5 gate remain UNVERIFIED (behavioral; require the "
          f"two-arm trial of 11.7)")
    print(f"\nDAIF_COMPILER_PASS={len(_passes)}/{total}  threshold={total}/{total}")
    if _fails:
        print("  refused: " + ", ".join(_fails))
    return 0 if not _fails else 1


if __name__ == "__main__":
    sys.exit(main())
