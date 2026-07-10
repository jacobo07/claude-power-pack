#!/usr/bin/env python3
"""V-gate suite for the Universal Meta-Systems Runtime.

Hermetic: every gate uses synthetic noun-maps / synthetic CLAUDE.md in tmp dirs
and a tmp PM-03 state dir, so the suite passes x3 with no global-state coupling.
The corpus is a read-only precondition (the runtime interprets it); a gate proves
it is never mutated.

Run: python tools/test_meta_systems_runtime.py   (exit 0 iff all gates pass)
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
MODULE = PP_ROOT / "modules" / "universal-meta-systems"
sys.path.insert(0, str(MODULE))

from runtime import LOOP_ORDER, CORPUS_PINNED_SHA          # noqa: E402
from runtime import corpus_parser as cp                    # noqa: E402
from runtime.executor import build_plan, plan_to_dict      # noqa: E402
from runtime.loop import run_loop                          # noqa: E402
from runtime.noun_map import (load_noun_map,               # noqa: E402
                              propose_candidates)

EXPECTED_TOTAL_OPS = 38
_passes = 0
_fails = 0


def _ok(gate: str, ev: str) -> None:
    global _passes
    _passes += 1
    print(f"PASS {gate}: {ev}")


def _fail(gate: str, ev: str) -> None:
    global _fails
    _fails += 1
    print(f"FAIL {gate}: {ev}")


def _mk_repo(noun_map: dict) -> Path:
    d = Path(tempfile.mkdtemp(prefix="ums_repo_"))
    (d / ".pp_meta_systems.json").write_text(
        json.dumps({"noun_map": noun_map}), encoding="utf-8")
    return d


def _hash_datasets(corpus_root: Path) -> str:
    h = hashlib.sha256()
    for f in sorted((corpus_root / "datasets").glob("*.md")):
        h.update(f.name.encode("utf-8"))
        h.update(f.read_bytes())
    return h.hexdigest()


def main() -> int:
    corpus = cp.find_corpus_root(PP_ROOT)
    if corpus is None:
        _fail("V-CORPUS-AVAILABLE", "corpus not found (precondition)")
        print(f"\nMETA_SYSTEMS_RUNTIME_PASS={_passes}/{_passes + _fails}  threshold=7/7")
        return 1

    # snapshot BEFORE any runtime activity (V-CORPUS-UNTOUCHED)
    before = _hash_datasets(corpus)

    # ---- V-NOUN-MAP-DERIVED -------------------------------------------------
    # auto-derive candidate nouns from a synthetic CLAUDE.md (no config file)
    prop_repo = Path(tempfile.mkdtemp(prefix="ums_prop_"))
    (prop_repo / "CLAUDE.md").write_text(
        "Servers server plugin plugin plugin economy economy economy economy",
        encoding="utf-8")
    cands = propose_candidates(prop_repo, 5)
    if cands and cands[0] == "economy" and "plugin" in cands:
        _ok("V-NOUN-MAP-DERIVED",
            f"candidates ranked from CLAUDE.md: {cands}")
    else:
        _fail("V-NOUN-MAP-DERIVED", f"unexpected candidates: {cands}")

    # ---- V-EXECUTOR-DOMAIN-SPECIFIC ----------------------------------------
    repo_a = _mk_repo({"artifact": "WIDGET", "transform": "STAMPING",
                       "witness": "PRESSCELL"})
    repo_b = _mk_repo({"artifact": "DIAGNOSIS", "transform": "PROTOCOL",
                       "witness": "CLINICIAN"})
    plan_a = build_plan("MS-0", load_noun_map(repo_a), corpus)
    plan_b = build_plan("MS-0", load_noun_map(repo_b), corpus)
    txt_a = " ".join(o.signature + o.guarantee for o in plan_a.ops)
    txt_b = " ".join(o.signature + o.guarantee for o in plan_b.ops)
    if (txt_a != txt_b and "WIDGET" in txt_a and "DIAGNOSIS" in txt_b
            and "WIDGET" not in txt_b):
        _ok("V-EXECUTOR-DOMAIN-SPECIFIC",
            "same MS-0, two noun-maps -> two distinct plans "
            f"(A op0: {plan_a.ops[0].signature.split(')')[0]}))")
    else:
        _fail("V-EXECUTOR-DOMAIN-SPECIFIC", "plans not domain-differentiated")

    # ---- V-LOOP-RUNS-ALL-7 --------------------------------------------------
    plans = run_loop(load_noun_map(repo_a), corpus)
    ids = [p.ms_id for p in plans]
    if len(plans) == 7 and ids == LOOP_ORDER and all(p.ops for p in plans):
        _ok("V-LOOP-RUNS-ALL-7", f"loop produced 7 plans in order {ids}")
    else:
        _fail("V-LOOP-RUNS-ALL-7", f"got {len(plans)} plans, order {ids}")

    # ---- V-AUDIT-FINDS-GAPS -------------------------------------------------
    # audit == MS-6 applied to a repo with no history/config -> gap-detection duties
    bare_repo = Path(tempfile.mkdtemp(prefix="ums_bare_"))
    audit = build_plan("MS-6", load_noun_map(bare_repo), corpus)
    op_names = {o.signature.split("(")[0] for o in audit.ops}
    if audit.ms_id == "MS-6" and "DETECT" in op_names and audit.gates:
        _ok("V-AUDIT-FINDS-GAPS",
            f"MS-6 audit exposes {len(audit.ops)} gap-detection actions "
            f"+ {len(audit.gates)} gates on a no-history repo")
    else:
        _fail("V-AUDIT-FINDS-GAPS", f"audit lacked MS-6 detection ops: {op_names}")

    # ---- V-CORPUS-UNTOUCHED -------------------------------------------------
    after = _hash_datasets(corpus)
    git_ok = True
    try:
        head = subprocess.run(
            ["git", "-C", str(corpus), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=15)
        git_ok = (head.returncode != 0) or head.stdout.strip().startswith(CORPUS_PINNED_SHA)
    except Exception:  # noqa: BLE001 -- git optional; hash check is authoritative
        git_ok = True
    if before == after and git_ok:
        _ok("V-CORPUS-UNTOUCHED",
            f"datasets hash stable across full run; HEAD @ {CORPUS_PINNED_SHA}")
    else:
        _fail("V-CORPUS-UNTOUCHED",
              f"corpus changed (hash {before == after}, git {git_ok})")

    # ---- V-PM03-PUBLISHES ---------------------------------------------------
    # hermetic: publish into a tmp bus state dir, never the global bus
    try:
        sys.path.insert(0, str(PP_ROOT / "modules" / "parallel_mesh"))
        import pm_03_bus  # type: ignore
        bus_dir = Path(tempfile.mkdtemp(prefix="ums_bus_"))
        findings = [{"topic": f"meta-system:{plan_a.ms_id}",
                     "claim": f"{plan_a.ms_id} interpreted: {len(plan_a.ops)} actions",
                     "evidence": plan_a.source_path}]
        n = pm_03_bus.publish_session_findings(
            str(repo_a), findings, sid="testsid", state_dir=bus_dir)
        if n == 1:
            _ok("V-PM03-PUBLISHES", "1 finding accepted by PM-03 (tmp state dir)")
        else:
            _fail("V-PM03-PUBLISHES", f"publish returned {n}")
    except Exception as e:  # noqa: BLE001
        _fail("V-PM03-PUBLISHES", f"bus integration error: {e.__class__.__name__}: {e}")

    # ---- V-BASELINE ---------------------------------------------------------
    # no-regression invariant: the parser still yields exactly 38 ops across 7,
    # and every plan serializes cleanly (json round-trip).
    total_ops = sum(len(cp.load_spec(f"MS-{n}", corpus).ops) for n in range(7))
    serializes = True
    try:
        json.dumps([plan_to_dict(p) for p in plans])
    except (TypeError, ValueError):
        serializes = False
    if total_ops == EXPECTED_TOTAL_OPS and serializes:
        _ok("V-BASELINE", f"{total_ops} ops parsed (expected {EXPECTED_TOTAL_OPS}); "
                          "plans JSON-serialize")
    else:
        _fail("V-BASELINE", f"ops={total_ops}, serializes={serializes}")

    total = _passes + _fails
    print(f"\nMETA_SYSTEMS_RUNTIME_PASS={_passes}/{total}  threshold=7/7")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
