#!/usr/bin/env python3
"""verify_spp.py — S++ end-to-end umbrella verifier.

Composes every sub-verifier in the Power Pack into one row-table +
single exit code. Sibling of (NOT replacement for) the Owner-authored
``tools/verify_full_install.py`` which audits the Programmatic Budget
Layer specifically; this umbrella invokes that one as one of its rows
and adds the rest of the S++ surface.

Rows:
  1. mirror-parity     — tools/verify_global_mirrors.py
  2. drift-report      — tools/drift_report.py
  3. paths+secrets     — tools/normalize_paths.py --check
  4. rtk-fusion        — tools/verify_rtk_fusion.py
  5. intent-lock       — modules/harness/intent_lock.js --self-test
  6. l3-engine         — tools/test_l3_intent.js
  7. programmatic-budget — tools/verify_full_install.py (Owner-authored)

Each row reports: name | rc | elapsed_s | one-line summary.
Exit 0 iff EVERY row exits 0 OR is marked ``ADVISORY`` in
``ADVISORY_ROWS``. ≤120s wall-clock budget (rows past budget abort).

Doctrine alignment:
* Reality-Contract: each row is a real subprocess call; no synthesised
  composite multiplier. If a sub-verifier does not exist, the row
  surfaces as ``MISSING`` (red) — never silently skipped.
* Mirror-Sync-Direction: tolerates the Owner's expected ``loose-ahead``
  on the documented mirror-parity exceptions (advisory).
* Hooks-dir deny doctrine: this umbrella is read-only by design;
  zero mutations to ``~/.claude/`` or any settings.

Usage:
  python tools/verify_spp.py
  python tools/verify_spp.py --quiet
  python tools/verify_spp.py --row <name>   # run a single row
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Safe-parallel opt-in for `--parallel N` (default OFF, serial).
# Sealed BL-VFIX-VERIFY-SPP-001 (2026-06-01 cont.):
# Empirical floor on this host is the l3-engine row at ~86 s; max
# parallel speed-up is ~max(L3, other_total/workers). max_workers=3
# is the safe cap -- audit pass with max_workers=6 hit
# T-PERF-VERIFY-SPP-PARALLEL-001 (>300 s regression).
PARALLEL_DEFAULT_WORKERS = 3
PARALLEL_MAX_WORKERS = 4

PP = Path(__file__).resolve().parents[1]
NODE = shutil.which("node") or shutil.which("node.exe") or "node"
PY = sys.executable

# Rows that may FAIL without failing the umbrella gate. Use sparingly —
# the default is strict.
ADVISORY_ROWS: set[str] = {
    # programmatic-budget: scope-specific (RTK + JIT + pricing); a
    # missing budget.json or stale pricing is an Owner-side concern,
    # not an S++ gate failure on a fresh install.
    "programmatic-budget",
    # NOTE (2026-05-20, Owner-correction): the prior ``l3-engine``
    # advisory entry was REMOVED. Owner-directive rejected "classified
    # FAIL" framings: verify_spp.py exit 0 means 7/7 strict-OK. The
    # parent/child contention pattern documented earlier is real but
    # is no longer a license to advisory-tag; the row must pass
    # under realistic umbrella conditions or be repaired upstream.
}

ROW_BUDGET_S = 60   # individual row cap; the L3 row needs the bulk of this


def _row(name: str, argv: list[str], cwd: Path = PP,
         budget: int = ROW_BUDGET_S) -> dict:
    """Run one sub-verifier; return {name, rc, elapsed, missing,
    summary}."""
    bin_ok = shutil.which(argv[0]) or Path(argv[0]).is_file()
    if not bin_ok:
        return {"name": name, "rc": 127, "elapsed": 0.0,
                "missing": True,
                "summary": f"binary missing: {argv[0]}"}
    t0 = time.monotonic()
    try:
        cp = subprocess.run(argv, cwd=str(cwd), capture_output=True,
                            text=True, timeout=budget)
        rc = cp.returncode
        elapsed = time.monotonic() - t0
        # Summary = last non-empty line of stdout (or stderr fallback).
        out = (cp.stdout or "").strip().splitlines()
        err = (cp.stderr or "").strip().splitlines()
        summary = (out[-1] if out else err[-1] if err else "(no output)")
        if len(summary) > 80:
            summary = summary[:77] + "..."
        return {"name": name, "rc": rc, "elapsed": elapsed,
                "missing": False, "summary": summary, "budget": budget,
                "stdout": cp.stdout, "stderr": cp.stderr}
    except subprocess.TimeoutExpired:
        # A row that did not FINISH has not told you anything about the
        # thing it measures. Reporting that as a failure conflates "the
        # gate found a defect" with "the gate never ran", and this repo
        # spent a day believing dataset-build was flaky under parallelism
        # when it simply needs 177s and was given 60.
        return {"name": name, "rc": 124,
                "elapsed": time.monotonic() - t0,
                "missing": False, "timed_out": True,
                "summary": f"DID NOT FINISH in {budget}s -- not a verdict"}
    except FileNotFoundError as e:
        return {"name": name, "rc": 127, "elapsed": 0.0,
                "missing": True, "summary": str(e)}


def _present(p: Path) -> bool:
    return p.is_file()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--quiet", action="store_true",
                    help="suppress per-row stdout dumps; only print table")
    ap.add_argument("--row", default=None,
                    help="run a single named row, skip the rest")
    ap.add_argument("--parallel", nargs="?", type=int,
                    const=PARALLEL_DEFAULT_WORKERS, default=0,
                    metavar="N",
                    help=(
                        "opt-in safe parallel mode: run rows across N "
                        f"worker threads (default {PARALLEL_DEFAULT_WORKERS} "
                        f"if no N given; max {PARALLEL_MAX_WORKERS}). "
                        "Wall floor on this host is the l3-engine row "
                        "(~86s). 0 (the default) = serial."
                    ))
    args = ap.parse_args()
    workers = max(0, min(int(args.parallel or 0), PARALLEL_MAX_WORKERS))

    rows_spec = [
        # (name, argv, budget)
        ("mirror-parity",
         [PY, str(PP / "tools" / "verify_global_mirrors.py")],
         15),
        ("drift-report",
         [PY, str(PP / "tools" / "drift_report.py")],
         15),
        ("paths+secrets",
         [PY, str(PP / "tools" / "normalize_paths.py"), "--check"],
         90),  # 13.6s solo yet exceeded 30s under load: 2.2x variance, so
               # its REAL failure was masked by an unmeasured verdict
        ("rtk-fusion",
         [PY, str(PP / "tools" / "verify_rtk_fusion.py")],
         30),
        ("intent-lock",
         [NODE, str(PP / "modules" / "harness" / "intent_lock.js"),
          "--self-test"],
         20),
        ("l3-engine",
         [NODE, str(PP / "tools" / "test_l3_intent.js")],
         360),
        ("programmatic-budget",
         [PY, str(PP / "tools" / "verify_full_install.py"), "--quiet"],
         30),
        ("tis-probe",
         [PY, str(PP / "tools" / "verify_tis.py")],
         30),
        ("monitoring-axis",
         [PY, str(PP / "tools" / "verify_monitoring.py")],
         30),
        ("tco-gate",
         [PY, str(PP / "tools" / "verify_tco.py")],
         20),
        ("uqf-active",
         [PY, str(PP / "tools" / "verify_uqf.py")],
         30),
        ("rules-taxonomy",
         [PY, str(PP / "tools" / "verify_rules.py")],
         10),
        ("osa-active",
         [PY, str(PP / "tools" / "verify_osa.py")],
         20),
        ("globalization",
         [PY, str(PP / "tools" / "verify_globalization.py")],
         15),
        ("proactive-agents",
         [PY, str(PP / "tools" / "verify_proactive_agents.py")],
         15),
        ("hooks-registration",
         [PY, str(PP / "tools" / "verify_hooks_registration.py")],
         15),
        ("hard-rules",
         [PY, str(PP / "tools" / "verify_hard_rules.py")],
         15),
        ("playwright-resilience",
         [PY, str(PP / "tools" / "test_playwright_resilience.py")],
         60),
        ("mcp-health",
         [PY, str(PP / "tools" / "verify_mcp_health.py")],
         30),
        ("compact-resilience",
         [PY, str(PP / "tools" / "test_compact_rescue.py")],
         60),
        ("jit-performance",
         [PY, str(PP / "tools" / "test_jit_performance.py")],
         60),
        ("restart-and-lag",
         [PY, str(PP / "tools" / "test_restart_and_lag.py")],
         90),
        # Budgets below are MEASURED solo runtimes plus headroom, not
        # guesses. dataset-build takes 176.8s and was given 60, so it timed
        # out on every umbrella run and read as a failing gate; auto-reset
        # takes 66.9s against 60. Both were unmeasurable by construction.
        ("dataset-build",
         [PY, str(PP / "tools" / "test_dataset_build.py")],
         360),
        ("integration-wiring",
         [PY, str(PP / "tools" / "verify_integration_wiring.py")],
         60),
        ("sleepy-skills",
         [PY, str(PP / "tools" / "test_sleepy_skills.py")],
         30),
        ("spec-driven",
         [PY, str(PP / "tools" / "test_spec_driven.py")],
         60),
        ("premise-verifier",
         [PY, str(PP / "modules" / "error_prevention" /
                  "premise_verifier.py"), "--self-test"],
         15),
        # frontier-28: three gates that must run in the umbrella, not by memory.
        # Shipping a suite nobody invokes is the exact defect two of them describe.
        ("d2a-provenance",
         [PY, str(PP / "tools" / "test_d2a_provenance.py")],
         30),
        ("dispatch-liveness",
         [PY, str(PP / "tools" / "test_dispatch_liveness.py")],
         45),
        ("cascade-wiring",
         [PY, str(PP / "tools" / "test_cascade_input_wiring.py")],
         30),
        # Semantic admission for the event store. Shape validation cannot
        # tell a failure from a success, and 52 of the first 75 events were
        # not failures at all.
        ("ceps-admission",
         [PY, str(PP / "tools" / "test_ceps_admission.py")],
         60),
        # Every stored event must carry a current admission verdict, so a
        # rule change cannot leave history silently unjudged.
        ("ceps-backfill",
         [PY, str(PP / "tools" / "ceps_backfill_audit.py"), "--check"],
         30),
        # Corroboration must count ancestors, not addresses.
        ("evidence-independence",
         [PY, str(PP / "tools" / "test_evidence_independence.py")],
         45),
        # Fast-path and incrementality cost contracts, asserted against
        # reconstructions of the two bugs that motivated them.
        ("cost-contracts",
         [PY, str(PP / "tools" / "test_cost_contracts.py")],
         90),
        # RED BY DESIGN until the Owner widens one matcher in
        # ~/.claude/settings.json to "Bash|PowerShell". The defect is real
        # -- the whole PreToolUse Bash chain never sees PowerShell -- and a
        # real defect belongs in the umbrella, not in a TODO. Flips green by
        # itself when the matcher changes.
        ("correctness-traps",
         [PY, str(PP / "tools" / "test_correctness_traps.py")],
         45),
        # The drift comparator must be able to GET an inventory. It could
        # not, for months, and the failure read as a config gap.
        ("drift-consumer",
         [PY, str(PP / "tools" / "test_drift_consumer.py")],
         180),
        # The `verified` input HR-CASCADE-001/003 read and nothing wrote.
        ("verification-provenance",
         [PY, str(PP / "tools" / "test_verification_provenance.py")],
         45),
        # A settled decision stops being a decision.
        ("decision-recurrence",
         [PY, str(PP / "tools" / "test_decision_recurrence.py")],
         60),
        # A redundant search is skipped, and reuse expires.
        ("search-reuse",
         [PY, str(PP / "tools" / "test_search_reuse.py")],
         60),
        # Entropy is a direction. Shipped orphaned in 05b4569 -- the exact
        # defect the same session sealed a rule about, caught by an
        # adversarial pass rather than by me.
        ("eed-delta",
         [PY, str(PP / "tools" / "test_eed_delta.py")],
         45),
        ("spec-department",
         [PY, str(PP / "tools" / "test_spec_department.py")],
         60),
        ("governance-propagation",
         [PY, str(PP / "tools" / "test_governance_propagation.py")],
         30),
        ("sdd-os",
         [PY, str(PP / "tools" / "test_sdd_os.py")],
         30),
        ("setup-os",
         [PY, str(PP / "tools" / "test_setup_os.py")],
         30),
        ("benchmarks-ok",
         [PY, str(PP / "tools" / "verify_bench_all.py")],
         60),  # 9s measured incl. the confirm-on-failure second sample
        # The gate above judges performance; this one judges THAT gate.
        # It compared against the raw target while printing "over 1.5x
        # target", so it manufactured 5 false alarms and buried the one
        # real regression among them. Pure -- no subprocess, no clock.
        ("bench-gate",
         [PY, str(PP / "tools" / "test_bench_gate.py")],
         30),
        ("ram-optimization",
         [PY, str(PP / "tools" / "test_ram_optimization.py")],
         30),
        ("auto-reset",
         [PY, str(PP / "tools" / "test_auto_reset.py")],
         180),  # measured 66.9s solo
        ("claude-md-size",
         [PY, str(PP / "tools" / "verify_claude_md_size.py")],
         10),
        ("claude-md-router",
         [PY, str(PP / "tools" / "test_claude_md_router.py")],
         180),  # measured 52.7s solo -- 87% of the old 60s budget, so it
                # flipped with ambient machine load, not with the code it
                # was supposed to be judging
        ("memory-router-freshness",
         [PY, str(PP / "tools" / "test_router_freshness_gate.py")],
         120),
        ("predictive-governance-gates",
         [PY, str(PP / "tools" / "test_predictive_governance_gate.py")],
         120),
        ("predictive-governance-debt",
         [PY, str(PP / "tools" / "predictive_governance_gate.py")],
         120),
        # Six sweeps, each spawning suite subprocesses -- the slowest row here.
        ("mutation-probe",
         [PY, str(PP / "tools" / "test_mutation_probe.py")],
         300),
        # Judgement only; the probe is stubbed, so this costs milliseconds.
        ("mutation-ratchet-gates",
         [PY, str(PP / "tools" / "test_mutation_ratchet.py")],
         120),
        # The push tier itself: measured 38.0s over 3 pairs. The weekly tier
        # (d2a_engine, rule_compiler/parser, ias_c2) is deliberately NOT here --
        # d2a alone costs about 3 minutes, ten times this whole row.
        ("mutation-ratchet",
         [PY, str(PP / "tools" / "mutation_ratchet.py"), "--tier", "push"],
         300),
        # The capture layer records what it observes. Hermetic by restore,
        # so it can run on every push without touching the corpus.
        ("capture-gates",
         [PY, str(PP / "tools" / "test_capture_liveness.py")],
         180),
        # And the live divergence check: fires vs records over 7 days. The
        # 2026-05..08 outage was invisible to every other row here because
        # each component passed while the corpus stayed empty.
        ("capture-liveness",
         [PY, str(PP / "tools" / "capture_liveness.py")],
         60),
        # The V-gates of the intent-fidelity layer itself.
        ("intent-gates",
         [PY, str(PP / "tools" / "test_intent_verified.py")],
         120),
        # And the standing join: every spec's declared criteria resolved
        # against what the repo can actually observe, plus the named ratchet.
        # Static tier only -- the observe tier runs per task, so this row's
        # cost does not grow with the spec corpus.
        ("intent-fidelity",
         [PY, str(PP / "tools" / "intent_verify.py")],
         120),
        # Did adopting a rule actually improve anything, and would it have caught
        # the incident it was written for? `compile_rules` decides only whether a
        # rule is ADMISSIBLE; without this row a rule's value rests on the argument
        # that produced it, and a corpus that can only grow is one that will
        # eventually be ignored.
        #
        # Built 2026-07-29, exported at modules/rule_compiler/__init__.py, and
        # invoked by nothing but its own test until now -- import is not invocation
        # (vault/plans/gap-reverification-2026-08-03.md, candidate B). Three of the
        # twelve Compounding Test questions (a wrong rule can be refuted; learning
        # from outcomes; the Constitution improves) had no producer because of it.
        #
        # Run as -m: the harness uses relative imports and cannot run as a file
        # path. Exit 1 only on REGRESSED -- a rule whose own probe says it made
        # things worse is the one result that should stop a session. Measured 7.7s.
        ("rule-effects",
         [PY, "-m", "modules.rule_compiler.effect_harness"],
         180),
        # UPAC residue R1. Nothing owned transitive surface, pin discipline,
        # replacement cost or an internalization threshold. --gate exits 1 only
        # on DO_NOT_USE (an unpinned constraint with no lockfile: the resolved
        # version is whatever the registry serves at install time). Everything
        # weaker is REVIEW, never USE, because CVE history and upstream health
        # are UNREACHABLE_HERE and absence of evidence is not a pass.
        ("dependency-sovereignty",
         [PY, "-m", "modules.dependency_sovereignty.sovereignty", "--gate"],
         180),
        # And its own V-gates -- the scanner has to be proven to find something,
        # not merely to run.
        ("dependency-sovereignty-gates",
         [PY, str(PP / "tools" / "test_dependency_sovereignty.py")],
         180),
        # UPAC residue R2. The structural half of "what stops being valid first":
        # transitive dependent closure over the real import graph. Reports the
        # mutually-dependent core, because a ranking over a cycle is a false
        # hierarchy. Ships with an UNSEALED baseline, so it reports and never
        # fails until someone deliberately seals the load-bearing set.
        ("architecture-horizon",
         [PY, "-m", "modules.architecture_horizon.horizon", "--gate"],
         120),
        ("architecture-horizon-gates",
         [PY, str(PP / "tools" / "test_architecture_horizon.py")],
         120),
        # UPAC residue R3. The INWARD complement of the row above: what an
        # engineer must assemble to change a unit. Disjoint from modules/uqf by
        # construction (uqf owns file-local defects) and from architecture_horizon
        # by direction; both boundaries are asserted mechanically in its gates.
        ("cognitive-load",
         [PY, "-m", "modules.cognitive_load.load"],
         120),
        ("cognitive-load-gates",
         [PY, str(PP / "tools" / "test_cognitive_load.py")],
         120),
    ]

    if args.row:
        rows_spec = [r for r in rows_spec if r[0] == args.row]
        if not rows_spec:
            print(f"verify_spp: no row named {args.row!r}", file=sys.stderr)
            return 2

    print("=" * 72)
    print("verify_spp — S++ end-to-end umbrella")
    print(f"  PP root : {PP}")
    print(f"  rows    : {len(rows_spec)}")
    print(f"  budget  : {ROW_BUDGET_S}s per row default")
    print("=" * 72)

    t_total = time.monotonic()
    results: list[dict] = []
    results_by_name: dict[str, dict] = {}

    def _emit(r: dict) -> None:
        name = r["name"]
        tag = "OK  " if r["rc"] == 0 else (
            "MISS" if r["missing"]
            else ("ADV " if name in ADVISORY_ROWS else "FAIL"))
        print(f"  [{tag}] {name:<22s} rc={r['rc']:<3d} "
              f"{r['elapsed']:6.2f}s  {r['summary']}", flush=True)
        if not args.quiet and r["rc"] != 0 and not r["missing"]:
            tail = (r.get("stdout") or "").splitlines()[-10:]
            for line in tail:
                print(f"    | {line}")

    if workers > 1 and not args.row and len(rows_spec) > 1:
        # Safe-parallel mode -- ThreadPoolExecutor over the row pool.
        # Wall = max(slowest row, sum(rest)/workers). On this host the
        # l3-engine row is the floor at ~86 s.
        print(f"  [parallel] dispatching {len(rows_spec)} rows "
              f"across {workers} worker threads...", flush=True)
        with ThreadPoolExecutor(max_workers=workers) as ex:
            future_to_name = {
                ex.submit(_row, name, argv, budget=budget): name
                for (name, argv, budget) in rows_spec
            }
            for fut in as_completed(future_to_name):
                name = future_to_name[fut]
                try:
                    r = fut.result()
                except Exception as exc:  # noqa: BLE001
                    r = {"name": name, "rc": 1, "elapsed": 0.0,
                         "missing": False,
                         "summary": f"executor error: "
                                    f"{type(exc).__name__}: {exc}"}
                results_by_name[name] = r
                _emit(r)
        # Render in spec order for stable downstream parsing.
        results = [results_by_name[n] for (n, _, _) in rows_spec
                   if n in results_by_name]
    else:
        # Serial mode (default + --row mode).
        for (name, argv, budget) in rows_spec:
            print(f"  [...] {name} ...", flush=True)
            r = _row(name, argv, budget=budget)
            results.append(r)
            _emit(r)

    total_elapsed = time.monotonic() - t_total
    print("=" * 72)
    print(f"  total elapsed: {total_elapsed:.2f}s")

    # Separated from failures on purpose: a timeout is an unmeasured row.
    timed_out = [r for r in results if r.get("timed_out")]
    if timed_out:
        print(f"  UNMEASURED: {len(timed_out)} row(s) did not finish — "
              f"{[r['name'] for r in timed_out]}")
        print("    (a row that did not finish is not a verdict; raise its "
              "budget or make it faster, do not read it as a defect)")

    # Rows finishing within 25% of their budget are one busy machine away
    # from becoming unmeasured. Surfaced BEFORE they flip, because a gate
    # that changes verdict with ambient load is not measuring the code.
    marginal = [r for r in results
                if not r.get("timed_out") and r.get("budget")
                and r["elapsed"] > 0.75 * r["budget"]]
    if marginal:
        print("  MARGINAL BUDGET: "
              + ", ".join(f"{r['name']} {r['elapsed']:.0f}s/{r['budget']}s"
                          for r in marginal))

    failed_strict = [r for r in results
                     if r["rc"] != 0 and r["name"] not in ADVISORY_ROWS]
    advisory_failing = [r for r in results
                        if r["rc"] != 0 and r["name"] in ADVISORY_ROWS]
    if failed_strict:
        print(f"  STRICT FAIL: {len(failed_strict)} row(s) — "
              f"{[r['name'] for r in failed_strict]}")
        rc = 1
    else:
        print(f"  STRICT PASS — {len(results) - len(advisory_failing)} "
              f"of {len(results)} rows OK"
              + (f", {len(advisory_failing)} advisory rows failing "
                 f"({[r['name'] for r in advisory_failing]})"
                 if advisory_failing else ""))
        rc = 0
    print("=" * 72)

    # Verification provenance. HR-CASCADE-001 and HR-CASCADE-003 read a
    # `verified` input that no code in this estate has ever written, so both
    # sealed rules were inert by starvation. This is the producer: the one
    # thing that already knows whether the tree is green says so, durably,
    # and the cascade gate reads it on the next commit or deploy.
    #
    # ONLY A FULL RUN VOUCHES FOR THE TREE. With --row the suite executes one
    # gate, and recording that as "verify_spp passed" would let a ten-second
    # row write a green that satisfies HR-CASCADE-001's deploy check for an
    # hour. A partial run is not a smaller pass, it is a different claim, and
    # `was_verified()` cannot tell 1/61 from 61/61 by design -- so the
    # distinction has to be made here, at the only place that knows.
    if args.row:
        print(f"  (single row {args.row!r}: verification provenance NOT "
              "recorded -- only a full run vouches for the tree)")
    else:
        try:
            from modules.cascade_prevention.verification_state import (
                record_verification)
            record_verification(
                "verify_spp", rc == 0,
                f"{len(results) - len(failed_strict)}/{len(results)} rows"
                + (f"; strict fail {[r['name'] for r in failed_strict]}"
                   if failed_strict else ""))
        except Exception as exc:  # noqa: BLE001 -- must never fail a run
            print(f"  (verification provenance not recorded: {exc})")
    return rc


if __name__ == "__main__":
    sys.exit(main())
