#!/usr/bin/env python3
"""V-SDDEVO-* replay gates for the SDD-OS evolution (W1 of
vault/plans/sdd-os-evolution-2026-10-01.md).

The corpus (fixtures/sdd_os/replay_corpus.json) labels what a CORRECT system
answers: tier range and risk dimensions per prompt, binding strength, spec
readiness and gate decision. The current code is wrong on some of them (D1-D6).
Those cases are named in the corpus's `known_red` set, and this test is a
ratchet over that set:

  * a red case outside `known_red`  -> REGRESSION (gate fails)
  * a `known_red` case now green    -> STALE (gate fails: remove it from the set)

So the set can only shrink, by name, as W2-W5 land. A count or a ratio would be
satisfied by deleting cases.

Isolation (audit gap 14): SDD_OS_STATE_DIR points at a temp dir before any
module is imported, and the live decision ledger's line count is asserted
unchanged. Import root (audit gap 13): SDD_OS_PP_ROOT, when set, is put first
on sys.path so a mutation drill can load a mutated module copy.

Run:  python tools/test_sdd_os_evolution.py            (gates)
      python tools/test_sdd_os_evolution.py --show-red (current red ids, JSON)
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "fixtures" / "sdd_os" / "replay_corpus.json"
LIVE_LEDGER = Path.home() / ".claude" / "state" / "sdd-os" / "decisions.jsonl"
RISK_DIMS = frozenset({"destructive_data", "public_contract", "auth_secrets",
                       "production", "irreversible_external"})
STRENGTHS = frozenset({"STRONG", "WEAK", "AMBIGUOUS", "REFERENCED", "UNBOUND"})
READINESS = frozenset({"READY", "NOT_READY", "LEGACY", "MALFORMED"})

_STATE_DIR = Path(tempfile.mkdtemp(prefix="sddevo-state-"))
os.environ["SDD_OS_STATE_DIR"] = str(_STATE_DIR)

_IMPORT_ROOT = Path(os.environ.get("SDD_OS_PP_ROOT") or ROOT)
sys.path.insert(0, str(_IMPORT_ROOT))

from modules.sdd_os.pre_exec_gate import evaluate  # noqa: E402
from modules.sdd_os.spec_binding import find_bound_spec  # noqa: E402
from modules.spec_gate.gate import classify_tier  # noqa: E402

results: list[tuple[str, bool, str]] = []


def gate(name: str, cond: bool, evidence: str = "") -> None:
    results.append((name, bool(cond), evidence))
    print(f"{'PASS' if cond else 'FAIL'} {name}  {evidence}")


def _ledger_lines() -> int | None:
    """Line count of the live ledger; None when it does not exist."""
    try:
        with LIVE_LEDGER.open("rb") as fh:
            return sum(1 for _ in fh)
    except FileNotFoundError:
        return None


def _make_repo(base: Path, names: list[str], specs: dict[str, str]) -> Path:
    repo = Path(tempfile.mkdtemp(prefix="sddevo-repo-", dir=base))
    spec_dir = repo / "vault" / "specs"
    spec_dir.mkdir(parents=True)
    for name in names:
        (spec_dir / f"{name}.md").write_text(specs[name], encoding="utf-8")
    return repo


# --- case evaluators: each returns (green, reason) -------------------------

def eval_tier(case: dict) -> tuple[bool, str]:
    r = classify_tier(case["prompt"])
    why: list[str] = []
    if not case["tier_min"] <= r.tier <= case["tier_max"]:
        why.append(f"tier={r.tier} not in [{case['tier_min']},{case['tier_max']}]")
    need = set(case["risk"])
    if need:
        dims = getattr(r, "risk_dims", None)
        if dims is None:
            why.append("risk_dims not produced")
        elif not need <= set(dims):
            why.append(f"risk_dims={sorted(dims)} missing {sorted(need - set(dims))}")
    return (not why), ("; ".join(why) or f"tier={r.tier}")


def _strength(binding) -> tuple[str, str]:
    s = getattr(binding, "strength", None)
    if s is not None:
        return str(s), ""
    # The legacy binder has no strength: any match binds as if strong.
    return ("STRONG" if binding.bound else "UNBOUND"), " (legacy: no strength field)"


def eval_binding(case: dict, specs: dict, base: Path) -> tuple[bool, str]:
    repo = _make_repo(base, case["specs"], specs)
    b = find_bound_spec(case["task"], repo)
    got, note = _strength(b)
    why: list[str] = []
    if got != case["expect_strength"]:
        why.append(f"strength={got}{note}, want {case['expect_strength']}")
    want_spec = case.get("expect_spec")
    if want_spec:
        stem = b.spec_path.stem if b.spec_path else None
        if stem != want_spec:
            why.append(f"spec={stem}, want {want_spec}")
    return (not why), ("; ".join(why) or f"strength={got}")


def eval_readiness(case: dict, specs: dict, base: Path) -> tuple[bool, str]:
    try:
        from modules.sdd_os.readiness import assess
    except ImportError:
        return False, "modules.sdd_os.readiness absent (W3)"
    repo = _make_repo(base, [case["spec"]], specs)
    got = assess(repo / "vault" / "specs" / f"{case['spec']}.md", case["task_tier"])
    state = str(getattr(got, "state", got))
    ok = state == case["expect_state"]
    return ok, f"state={state}" + ("" if ok else f", want {case['expect_state']}")


def eval_decision(case: dict, specs: dict, base: Path) -> tuple[bool, str]:
    repo = _make_repo(base, case["specs"], specs)
    d = evaluate(case["task"], repo)
    ok = d.action in case["allowed_actions"]
    return ok, f"action={d.action}" + ("" if ok else f", want one of {case['allowed_actions']}")


# --- ratchet ---------------------------------------------------------------

def compare(red: set[str], known_red: set[str]) -> tuple[set[str], set[str]]:
    """(regressions, stale): red-but-not-known, known-but-now-green."""
    return red - known_red, known_red - red


def _validate_corpus(c: dict) -> list[str]:
    problems: list[str] = []
    specs = c.get("specs") or {}
    ids: list[str] = []
    for case in c.get("tier_cases") or []:
        ids.append(case.get("id", "?"))
        if not {"prompt", "tier_min", "tier_max", "risk", "source"} <= case.keys():
            problems.append(f"{case.get('id')}: missing tier fields")
        elif not 0 <= case["tier_min"] <= case["tier_max"] <= 3:
            problems.append(f"{case['id']}: bad tier range")
        elif not set(case["risk"]) <= RISK_DIMS:
            problems.append(f"{case['id']}: unknown risk {set(case['risk']) - RISK_DIMS}")
    for case in c.get("binding_cases") or []:
        ids.append(case.get("id", "?"))
        if case.get("expect_strength") not in STRENGTHS:
            problems.append(f"{case.get('id')}: bad expect_strength")
    for case in c.get("readiness_cases") or []:
        ids.append(case.get("id", "?"))
        if case.get("expect_state") not in READINESS:
            problems.append(f"{case.get('id')}: bad expect_state")
    for case in c.get("decision_cases") or []:
        ids.append(case.get("id", "?"))
        if not case.get("allowed_actions"):
            problems.append(f"{case.get('id')}: no allowed_actions")
    for case in (c.get("binding_cases") or []) + (c.get("decision_cases") or []):
        problems += [f"{case['id']}: unknown spec {n}" for n in case.get("specs", []) if n not in specs]
    for case in c.get("readiness_cases") or []:
        if case.get("spec") not in specs:
            problems.append(f"{case['id']}: unknown spec {case.get('spec')}")
    if len(ids) != len(set(ids)):
        problems.append("duplicate case ids")
    unknown_red = set(c.get("known_red", [])) - set(ids)
    if unknown_red:
        problems.append(f"known_red names no case: {sorted(unknown_red)}")
    return problems


def run_cases(c: dict, base: Path) -> dict[str, tuple[bool, str]]:
    specs = c["specs"]
    out: dict[str, tuple[bool, str]] = {}
    for case in c["tier_cases"]:
        out[case["id"]] = eval_tier(case)
    for case in c["binding_cases"]:
        out[case["id"]] = eval_binding(case, specs, base)
    for case in c["readiness_cases"]:
        out[case["id"]] = eval_readiness(case, specs, base)
    for case in c["decision_cases"]:
        out[case["id"]] = eval_decision(case, specs, base)
    return out


def tier_report(c: dict) -> None:
    down = esc = 0
    for case in c["tier_cases"]:
        t = classify_tier(case["prompt"]).tier
        down += t < case["tier_min"]
        esc += t > case["tier_max"]
    n = len(c["tier_cases"])
    print(f"  tier: false_downgrade={down}/{n} false_escalation={esc}/{n}")


def invariant_gates(c: dict) -> None:
    """Named W2 invariants, so a mutant is killed by the property it breaks,
    not only by the generic ratchet."""
    known = set(c["known_red"])
    live = [t for t in c["tier_cases"] if t["id"] not in known]
    results_by_id = {t["id"]: classify_tier(t["prompt"]) for t in c["tier_cases"]}
    for dim in sorted(RISK_DIMS):
        labelled = [t for t in live if dim in t["risk"]]
        missed = [t["id"] for t in labelled
                  if dim not in (getattr(results_by_id[t["id"]], "risk_dims", None) or ())]
        gate(f"V-SDDEVO-DIM-{dim.upper()}", bool(labelled) and not missed,
             f"{len(labelled) - len(missed)}/{len(labelled)} labelled cases detected"
             + (f"; missed {missed}" if missed else ""))
    broken, unexplained = [], []
    for cid, r in results_by_id.items():
        base = getattr(r, "base_tier", None)
        floor = getattr(r, "risk_floor", 0)
        if base is None or r.tier != max(base, floor) or r.tier < base:
            broken.append(cid)
        elif r.tier != base and not (getattr(r, "risk_evidence", ()) and "raised" in r.reason):
            unexplained.append(cid)
    # Control the corpus lacks: base above a non-zero risk floor. Without it, "risk floor
    # replaces base" is indistinguishable from "max(base, floor)" on every corpus case.
    ctl = classify_tier("redesign the full architecture and drop the old tables")
    if getattr(ctl, "base_tier", None) != 3 or ctl.tier != 3 or not getattr(ctl, "risk_floor", 0):
        broken.append(f"CONTROL base={getattr(ctl, 'base_tier', None)} floor="
                      f"{getattr(ctl, 'risk_floor', None)} tier={ctl.tier}")
    gate("V-SDDEVO-TIER-MONOTONIC", not broken,
         f"tier == max(base, risk floor) on {len(results_by_id) - len(broken)}/{len(results_by_id)}"
         + (f"; broken {broken}" if broken else ""))
    # Risk facts must not depend on unrelated import side effects (code review W2, F5): with no
    # home directory, importing the autonomy_gate PACKAGE raised and every prompt came back
    # UNASSESSED. Run in a child with no home at all.
    import subprocess
    env = {k: v for k, v in os.environ.items()
           if k not in ("HOME", "USERPROFILE", "HOMEDRIVE", "HOMEPATH")}
    probe = ("import sys; sys.path.insert(0, sys.argv[1]); "
             "from modules.spec_gate.gate import classify_tier; "
             "r = classify_tier('truncate the sessions table and run the migration against production'); "
             "print(r.tier, r.risk_state, '+'.join(r.risk_dims))")
    child = subprocess.run([sys.executable, "-c", probe, str(_IMPORT_ROOT)], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", env=env, timeout=60)
    seen = (child.stdout.strip() or child.stderr.strip()[-120:])
    gate("V-SDDEVO-RISK-WITHOUT-HOME", seen.startswith("3 FOUND"), f"no-home child -> {seen!r}")
    raised = sum(1 for r in results_by_id.values()
                 if getattr(r, "base_tier", None) is not None and r.tier != r.base_tier)
    gate("V-SDDEVO-TIER-EXPLAINED", raised > 0 and not unexplained,
         f"{raised} raised verdicts carry risk evidence"
         + (f"; unexplained {unexplained}" if unexplained else ""))


def main(argv: list[str]) -> int:
    ledger_before = _ledger_lines()
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    base = Path(tempfile.mkdtemp(prefix="sddevo-"))
    try:
        problems = _validate_corpus(corpus)
        tier_cases = corpus.get("tier_cases") or []
        real = sum(1 for t in tier_cases if t.get("source") == "real")
        high_risk = sum(1 for t in tier_cases if t.get("risk"))
        gate("V-SDDEVO-CORPUS-VALID", not problems,
             "; ".join(problems[:4]) or f"{len(tier_cases)} tier cases, all labelled")
        gate("V-SDDEVO-CORPUS-REAL-HALF", tier_cases and 2 * real >= len(tier_cases),
             f"real={real}/{len(tier_cases)}")
        gate("V-SDDEVO-DENOMINATOR", high_risk > 0 and all(
            corpus.get(k) for k in ("binding_cases", "readiness_cases", "decision_cases")),
             f"high-risk tier cases={high_risk}; every section non-empty")
        if problems:
            return _finish(ledger_before)

        outcomes = run_cases(corpus, base)
        red = {cid for cid, (green, _) in outcomes.items() if not green}
        if "--show-red" in argv:
            print(json.dumps(sorted(red)))
        for cid, (green, why) in outcomes.items():
            print(f"  case {cid:<6} {'green' if green else 'RED  '} {why}")
        tier_report(corpus)

        expected = sum(len(corpus[k]) for k in
                       ("tier_cases", "binding_cases", "readiness_cases", "decision_cases"))
        gate("V-SDDEVO-ALL-CASES-JUDGED", len(outcomes) == expected,
             f"{len(outcomes)}/{expected} judged")
        regressions, stale = compare(red, set(corpus["known_red"]))
        gate("V-SDDEVO-RATCHET-NO-REGRESSION", not regressions,
             f"red outside known_red: {sorted(regressions)}" if regressions
             else f"red={len(red)} all known")
        gate("V-SDDEVO-RATCHET-NO-STALE", not stale,
             f"now green, remove from known_red: {sorted(stale)}" if stale
             else f"known_red={len(corpus['known_red'])} all still red")
        invariant_gates(corpus)
        # Positive control: the comparator must see both directions.
        r_ctl, s_ctl = compare({"a", "b"}, {"b", "c"})
        gate("V-SDDEVO-RATCHET-CONTROL", r_ctl == {"a"} and s_ctl == {"c"},
             "comparator reports a synthetic regression and a synthetic stale entry")
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return _finish(ledger_before)


def _finish(ledger_before: int | None) -> int:
    ledger_after = _ledger_lines()
    gate("V-SDDEVO-STATE-ISOLATED",
         ledger_after == ledger_before
         and Path(os.environ["SDD_OS_STATE_DIR"]) == _STATE_DIR
         and not _STATE_DIR.is_relative_to(LIVE_LEDGER.parent),
         f"live ledger lines {ledger_before} -> {ledger_after}; state dir {_STATE_DIR.name}")
    shutil.rmtree(_STATE_DIR, ignore_errors=True)
    passes = sum(1 for _, ok, _ in results if ok)
    print(f"SDDEVO_PASS={passes}/{len(results)}")
    return 0 if passes == len(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
