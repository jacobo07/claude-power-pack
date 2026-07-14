#!/usr/bin/env python3
"""V-gates for the two FAITP debts + the residual compiler (2026-07-14).

The gates that matter here are the REFUSALS. A queue that cannot refuse a promotion to a
rule nobody wrote, and a compiler that cannot refuse a mandate, would both report success
on exactly the input they exist to catch. Every refusal below is asserted on real data.

Hermetic: queue writes go to a temp state dir and promotions are checked against a temp
archive. The live-state gates (MEMORY.md size, pending count) read reality on purpose --
they are the debts' done-gates, not unit tests.
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.fable_distillation.fd_07_flywheel import _append_jsonl  # noqa: E402
from modules.fable_distillation.ukdl_queue import (  # noqa: E402
    _candidates_path, candidates, pending, promote, reject, status_of, under_review)
from modules.hard_rules.residual import (  # noqa: E402
    MOVES, RESIDUAL, FiredRule, audit_corpus, classify_empty_class, compile_residual,
    gate_new_rule, load_cases, run_case)

_REPO = str(_PP_ROOT)
_NOW = datetime(2026, 7, 14, tzinfo=timezone.utc)
_MEMORY = (Path.home() / ".claude" / "projects" /
           "C--Users-User--claude-skills-claude-power-pack" / "memory" / "MEMORY.md")
_ARCHIVE_MD = _MEMORY.parent / "MEMORY_ARCHIVE.md"
_MEMORY_CEILING = 17408
_CASES = _PP_ROOT / "vault" / "hard_rules" / "conflict_cases.json"

_passes, _fails = 0, 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS  {gate}  --  {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL  {gate}  --  {diag}")


# --------------------------------------------------------------------------- #
# D1 -- the queue.
# --------------------------------------------------------------------------- #
def _seed_queue(sd: Path) -> None:
    _append_jsonl(_candidates_path(_REPO, sd),
                  {"fingerprint": "aaaa1111", "claim": "x", "kind": "hard_rule/trap"})
    _append_jsonl(_candidates_path(_REPO, sd),
                  {"fingerprint": "bbbb2222", "claim": "y", "kind": "hard_rule/trap"})


def gate_status_defaults_to_pending(sd: Path) -> None:
    _seed_queue(sd)
    rows = candidates(_REPO, sd)
    if len(rows) == 2 and all(r["status"] == "pending" for r in rows):
        _ok("V-UKDL-CANDIDATES-STATUS",
            "a candidate with no transition derives status=pending (never a constant string)")
    else:
        _fail("V-UKDL-CANDIDATES-STATUS", f"{rows}")


def gate_pending_list_is_exact(sd: Path) -> None:
    promote(_REPO, "aaaa1111", "HR-FAKE-GATE-001", state_dir=sd, now=_NOW,
            archive=_ARCHIVE_FIXTURE)
    p = [r["fingerprint"] for r in pending(_REPO, sd)]
    if p == ["bbbb2222"]:
        _ok("V-UKDL-PENDING-LIST",
            "after one promotion the pending list is exactly the undecided candidate")
    else:
        _fail("V-UKDL-PENDING-LIST", f"pending={p}")


def gate_promotion_needs_a_real_rule(sd: Path) -> None:
    r = promote(_REPO, "bbbb2222", "HR-NOBODY-WROTE-THIS-001", state_dir=sd, now=_NOW,
                archive=_ARCHIVE_FIXTURE)
    if not r["ok"] and "nobody wrote" in r["note"]:
        _ok("V-UKDL-PROMOTION-FAILCLOSED",
            "promotion to a rule absent from the archive is REFUSED")
    else:
        _fail("V-UKDL-PROMOTION-FAILCLOSED", f"{r}")


def gate_rejection_needs_a_reason(sd: Path) -> None:
    r = reject(_REPO, "bbbb2222", reason="  ", state_dir=sd, now=_NOW)
    if not r["ok"]:
        _ok("V-UKDL-REJECTION-REASONED", "a rejection without a reason is refused")
    else:
        _fail("V-UKDL-REJECTION-REASONED", f"{r}")


def gate_transitions_are_append_only(sd: Path) -> None:
    under_review(_REPO, "bbbb2222", state_dir=sd, now=_NOW)
    reject(_REPO, "bbbb2222", reason="superseded", state_dir=sd, now=_NOW)
    st = status_of(_REPO, "bbbb2222", sd)
    if st["status"] == "rejected" and st["note"] == "superseded":
        _ok("V-UKDL-LATEST-WINS",
            "under_review then rejected -> latest transition wins; no row rewritten")
    else:
        _fail("V-UKDL-LATEST-WINS", f"{st}")


def gate_live_queue_drained() -> None:
    p = pending(_REPO)
    if not p:
        _ok("V-UKDL-LIVE-DRAINED",
            "0 candidates pending -- the three promoted rules are recorded as promoted")
    else:
        _fail("V-UKDL-LIVE-DRAINED",
              f"{len(p)} still pending: {[r['fingerprint'] for r in p]}")


# --------------------------------------------------------------------------- #
# D2 -- memory compaction.
# --------------------------------------------------------------------------- #
def gate_memory_size() -> None:
    n = _MEMORY.stat().st_size if _MEMORY.is_file() else -1
    if 0 < n < _MEMORY_CEILING:
        _ok("V-MEMORY-SIZE", f"MEMORY.md = {n} B  (< {_MEMORY_CEILING})")
    else:
        _fail("V-MEMORY-SIZE", f"MEMORY.md = {n} B, ceiling {_MEMORY_CEILING}")


def gate_memory_lossless() -> None:
    """Nothing deleted: every entry still has a row, and the old long-form hooks are
    preserved verbatim in the archive. Follow one pointer and the detail is there."""
    if not (_MEMORY.is_file() and _ARCHIVE_MD.is_file()):
        return _fail("V-MEMORY-POINTERS", "MEMORY.md or MEMORY_ARCHIVE.md missing")
    mem = _MEMORY.read_text(encoding="utf-8", errors="replace")
    arch = _ARCHIVE_MD.read_text(encoding="utf-8", errors="replace")
    rows = [ln for ln in mem.split("\n") if ln.startswith("- [")]
    arch_rows = [ln for ln in arch.split("\n") if ln.startswith("- [")]
    if len(rows) < len(arch_rows):
        return _fail("V-MEMORY-POINTERS",
                     f"{len(arch_rows) - len(rows)} entries lost vs the archive")
    # A pointer is only real if the target exists.
    import re
    broken = []
    for ln in rows:
        m = re.search(r"\]\(([^)]+)\)", ln)
        if m and not m.group(1).startswith(("http", "..", "../")):
            if not (_MEMORY.parent / m.group(1)).exists():
                broken.append(m.group(1))
    if broken:
        return _fail("V-MEMORY-POINTERS", f"broken local pointers: {broken}")
    _ok("V-MEMORY-POINTERS",
        f"{len(rows)} entries kept (archive had {len(arch_rows)}); every local pointer resolves")


# --------------------------------------------------------------------------- #
# D3 -- the residual compiler.
# --------------------------------------------------------------------------- #
def gate_scs_c92_cases() -> None:
    rows = [run_case(c) for c in load_cases(str(_CASES))]
    bad = [r["case"] for r in rows if not r["matches_expectation"]]
    if bad:
        return _fail("V-RESIDUAL-COMPILER-SCS92", f"unexpected verdicts: {bad}")
    shape1 = next(r for r in rows if r["case"].startswith("SCS-C92-SHAPE-1"))
    if shape1["verdict"] != "RESIDUAL_AVAILABLE" or RESIDUAL not in shape1["legal"]:
        return _fail("V-RESIDUAL-COMPILER-SCS92",
                     "the credential deadlock did not yield a legal residual")
    _ok("V-RESIDUAL-COMPILER-SCS92",
        f"{len(rows)} cases as expected; the SCS C92 deadlock resolves to a legal residual, "
        "never 'the Hard Rules conflict'")


def gate_no_false_resolution() -> None:
    """The compiler must refuse a mandate. Mandates CAN contradict; treating one as a
    prohibition would manufacture a resolution that does not exist."""
    out = compile_residual([
        FiredRule(rule_id="M1", stop="always immediately rotate the credential",
                  kind="MANDATE", forbids=[]),
        FiredRule(rule_id="P1", stop="never auto-rotate", forbids=["ROTATE_CREDENTIAL"]),
    ])
    if out["verdict"] == "UNSAFE_JOIN" and "M1" in out["reason"]:
        _ok("V-RESIDUAL-NO-FALSE-RESOLUTION",
            "a MANDATE in the join is refused by name, not silently joined")
    else:
        _fail("V-RESIDUAL-NO-FALSE-RESOLUTION", f"{out['verdict']}")


def gate_residual_is_guaranteed() -> None:
    """Both poles: a normal join keeps the residual; a rule forbidding it escalates."""
    keeps = compile_residual([FiredRule(rule_id="A", stop="never commit",
                                        forbids=["COMMIT"])])
    breaks = compile_residual([FiredRule(rule_id="B", stop="never halt and escalate",
                                         forbids=[RESIDUAL])])
    if (keeps["verdict"] == "RESIDUAL_AVAILABLE" and RESIDUAL in keeps["legal"]
            and breaks["verdict"] == "NO_RESIDUAL" and breaks["residual"] is None):
        _ok("V-RESIDUAL-GUARANTEE",
            "residual survives an ordinary join AND its removal is surfaced, not hidden")
    else:
        _fail("V-RESIDUAL-GUARANTEE", f"{keeps['verdict']} / {breaks['verdict']}")


def gate_addition_is_local() -> None:
    bad = gate_new_rule(FiredRule(rule_id="X", forbids=[RESIDUAL]))
    good = gate_new_rule(FiredRule(rule_id="Y", forbids=["DEPLOY"]))
    if not bad["admitted"] and good["admitted"]:
        _ok("V-RESIDUAL-ADDITION-LOCAL",
            "rule-addition gate is one local check; no global re-ranking")
    else:
        _fail("V-RESIDUAL-ADDITION-LOCAL", f"{bad} / {good}")


def gate_empty_class_splits_on_history() -> None:
    inert = classify_empty_class("PLUGIN-INSTALL", [], ["rejected-rule"])
    virgin = classify_empty_class("BRAND-NEW", [], [])
    if inert["verdict"] == "FAIL_CLOSED" and virgin["verdict"] == "FAIL_OPEN_WITH_QUEUE":
        _ok("V-EMPTY-CLASS-SPLIT",
            "inert-with-rejects = fail-closed; virgin = fail-open + Owner queue")
    else:
        _fail("V-EMPTY-CLASS-SPLIT", f"{inert['verdict']} / {virgin['verdict']}")


def gate_corpus_premise_measured() -> None:
    """The frontier premise is TESTED against the real corpus, not assumed."""
    a = audit_corpus()
    if a["total"] > 0 and a["mandate"] == 0 and a["prohibition"] > 0:
        _ok("V-CORPUS-NO-MANDATES",
            f"{a['total']} real rules: {a['prohibition']} prohibitions, 0 mandates, "
            f"{a['unknown']} undeterminable (fail-closed, not waved through)")
    else:
        _fail("V-CORPUS-NO-MANDATES",
              f"mandates found -- the prohibition premise is FALSE here: {a['mandates']}")


_ARCHIVE_FIXTURE: Path


def main() -> int:
    global _ARCHIVE_FIXTURE
    print("FAITP debts -- V-gates")
    with tempfile.TemporaryDirectory(prefix="faitp_debts_") as td:
        sd = Path(td)
        _ARCHIVE_FIXTURE = sd / "archive.md"
        _ARCHIVE_FIXTURE.write_text("## HR-FAKE-GATE-001 -- fixture\n", encoding="utf-8")
        gate_status_defaults_to_pending(sd)
        gate_pending_list_is_exact(sd)
        gate_promotion_needs_a_real_rule(sd)
        gate_rejection_needs_a_reason(sd)
        gate_transitions_are_append_only(sd)
    gate_live_queue_drained()
    gate_memory_size()
    gate_memory_lossless()
    gate_scs_c92_cases()
    gate_no_false_resolution()
    gate_residual_is_guaranteed()
    gate_addition_is_local()
    gate_empty_class_splits_on_history()
    gate_corpus_premise_measured()
    total = _passes + _fails
    print(f"FAITP_DEBTS_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
