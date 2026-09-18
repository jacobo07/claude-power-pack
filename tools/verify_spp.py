#!/usr/bin/env python3
"""verify_spp.py â€” S++ end-to-end umbrella verifier.

Composes every sub-verifier in the Power Pack into one row-table +
single exit code. Sibling of (NOT replacement for) the Owner-authored
``tools/verify_full_install.py`` which audits the Programmatic Budget
Layer specifically; this umbrella invokes that one as one of its rows
and adds the rest of the S++ surface.

Rows:
  1. mirror-parity     â€” tools/verify_global_mirrors.py
  2. drift-report      â€” tools/drift_report.py
  3. paths+secrets     â€” tools/normalize_paths.py --check
  4. rtk-fusion        â€” tools/verify_rtk_fusion.py
  5. intent-lock       â€” modules/harness/intent_lock.js --self-test
  6. l3-engine         â€” tools/test_l3_intent.js
  7. programmatic-budget â€” tools/verify_full_install.py (Owner-authored)

Each row reports: name | rc | elapsed_s | one-line summary.
Exit 0 iff EVERY row exits 0 OR is marked ``ADVISORY`` in
``ADVISORY_ROWS``. â‰¤120s wall-clock budget (rows past budget abort).

Doctrine alignment:
* Reality-Contract: each row is a real subprocess call; no synthesised
  composite multiplier. If a sub-verifier does not exist, the row
  surfaces as ``MISSING`` (red) â€” never silently skipped.
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

def suspect_rows(results: list, advisory: set) -> list:
    """Rows a parallel run reported red, which a solo run could exonerate.

    A parallel run measures the row and the harness together. Measured
    2026-09-02 over 75 rows: five of fourteen strict fails passed cleanly
    alone, and only three of those five were timeouts -- one had exited 1
    outright -- so selecting on "did not finish" alone would have missed
    two of them.

    Advisory rows are excluded because their red already costs nothing;
    re-running them would buy a label nobody reads.
    """
    return [r for r in results
            if (r.get("rc") != 0 or r.get("timed_out"))
            and r.get("name") not in advisory]


def apply_solo(row: dict, solo: dict) -> bool:
    """Fold a solo re-run into a row. True when the row was exonerated.

    Deliberately one-directional, and the asymmetry is a real limit worth
    stating rather than hiding: this can only ever move a red to green. A
    row that PASSES under load and would fail alone is never re-run, so it
    is never caught here. The claim earned is narrow -- "this red did not
    reproduce without the harness's own load" -- and it is not the same
    claim as "this row is healthy".
    """
    if solo.get("rc") != 0:
        return False
    row["rc"] = 0
    row["timed_out"] = False
    row["contended"] = True
    return True


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
    #
    # live-hook-wrappers: the SUBJECT is the Owner's ~/.claude/settings.json,
    # which HR-001 forbids this repo from writing. A row whose only repair is
    # out of reach must not block a sweep -- a gate that is red on arrival and
    # blocks gets disabled within a week, which costs more than it saves. This
    # is the narrow case the Owner-correction above still allows: not a FAIL
    # being reclassified, but a finding about the HOST rather than the tree.
    "live-hook-wrappers",
    # Same shape: subject is ~/.claude/settings.json. The launcher (kclaude.ps1)
    # shows it red on screen at every launch; here it must not block a tree sweep.
    "live-hook-registry",
}

ROW_BUDGET_S = 60   # individual row cap; the L3 row needs the bulk of this

# DECLARED, not observed. The SQI-03 capacity gate compares available memory
# against a requirement the caller states; this is the umbrella's statement of
# what one row costs at peak. It is an ESTIMATE and is labelled as one wherever
# it is printed -- promoting it to "measured" would be the requested/observed
# confusion the monetary-quantity doctrine warns about. Override with --peak-mb
# once a real per-row peak has been sampled.
ROW_PEAK_MB_ESTIMATE = 350

# What the rest of the machine still needs to live on. Exposed as a flag for one
# reason that is not tuning: WITHOUT IT THE PASSING BRANCH CANNOT BE DRIVEN.
# Every refusal branch is reachable on any host by asking for an absurd peak;
# the QUALIFIED branch is reachable only on a host that happens to be healthy,
# so a gate for it would be green on a roomy machine, red on a busy one, and
# evidence on neither. A declarable reserve makes the pass branch a test rather
# than a weather report.
HOST_RESERVE_MB = 1024


def _dirty_paths(root: Path) -> list[str] | None:
    """The SORTED SET of paths git reports dirty. None means 'could not look'.

    A SET, never a count: measured 2026-09-10, a run opened and closed on 254
    dirty paths and the tree had still moved -- one path left the set as another
    entered. A count cannot see that, and a hash of the listing sees it without
    being able to say WHAT moved, which leaves an INCONCLUSIVE nobody can act on.
    """
    git = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
    if not Path(git).is_file() and shutil.which("git") is None:
        return None
    try:
        cp = subprocess.run([git, "status", "--porcelain"], cwd=str(root),
                            capture_output=True, text=True, timeout=30,
                            errors="replace")
    except (OSError, subprocess.SubprocessError):
        return None
    if cp.returncode != 0:
        return None
    return sorted(ln[3:] for ln in (cp.stdout or "").splitlines() if len(ln) > 3)


def _preflight(root: Path, workers: int, peak_mb: int,
               reserve_mb: int = HOST_RESERVE_MB) -> dict:
    """Is this host fit to have its answer about this repository believed?

    Delegates to SQI-03, the estate's incumbent authority on exactly that
    question ("may any result from this host be interpreted at all"). It was
    ORPHANED -- `vault/audits/liveness_report.md` recorded no live surface
    reaching it -- which is why the 82-row sweep that the OS killed at 2181 MB
    free of 32061 MB had nothing standing between it and a verdict.

    Never raises. A preflight that can break the umbrella is worse than no
    preflight, so every failure resolves to UNKNOWN -- which is a ceiling on
    interpretation, never a pass.
    """
    env = {
        "state": "UNKNOWN",
        "verdict_ceiling": "UNVERIFIED",
        "available_mb": None,
        "required_mb": None,
        "capacity": None,          # True / False / None, the gate's own tri-state
        "blocker": None,
        "workers": max(1, workers),
        "peak_mb_per_unit": peak_mb,
        "dirty_before": _dirty_paths(root),
        "error": None,
    }
    try:
        sys.path.insert(0, str(PP))
        from modules.sqi.environment_qualifier import (  # noqa: PLC0415
            Workload, capacity_probe,
        )
        w = Workload("verify_spp sweep", peak_mb_per_unit=peak_mb,
                     units_in_flight=max(1, workers), reserve_mb=reserve_mb)
        gate = capacity_probe(w)
        env["capacity"] = gate.passed
        env["blocker"] = gate.blocker
        env["required_mb"] = w.required_mb
        env["observed"] = gate.observed
        from modules.sqi.environment_qualifier import available_mb  # noqa: PLC0415
        env["available_mb"] = available_mb()
        env["state"] = {True: "QUALIFIED", False: "BLOCKED",
                        None: "PARTIALLY_QUALIFIED"}[gate.passed]
        env["verdict_ceiling"] = {True: "any", False: "BLOCKED",
                                  None: "UNVERIFIED for any failing row"}[gate.passed]
    except Exception as exc:  # noqa: BLE001 -- fail-open to UNKNOWN, never to pass
        env["error"] = f"{type(exc).__name__}: {exc}"
    return env


# NTSTATUS codes that mean the OS took the process away rather than the process
# deciding to leave. 0xC0000017 is STATUS_NO_MEMORY, which is the exact way an
# OOM death presents on Windows -- the death this whole surface exists to stop
# being read as a verdict about the code.
_KILLED_NTSTATUS = {
    0xC0000017,  # STATUS_NO_MEMORY
    0xC00000FD,  # STATUS_STACK_OVERFLOW
    0xC000013A,  # STATUS_CONTROL_C_EXIT
    0xFFFFFFFF,  # TerminateProcess(-1): the harness or a governor stepped in
}


def _terminated_by_os(rc: int) -> bool:
    """Did this process EXIT, or was it TAKEN?

    A process that returns 1 has judged its subject and found it wanting. A
    process the kernel removed has judged nothing at all, and the two are
    indistinguishable by exit code alone unless you look at which codes a
    process can actually choose.

    POSIX: a negative code is `-signal`; nothing returns that voluntarily.
    Windows: subprocess surfaces the raw DWORD, so an OS teardown arrives as a
    negative int or as a 0xCxxxxxxx NTSTATUS. An ordinary failing verifier
    returns 1 or 2 and never lands in either space.
    """
    if rc < 0:
        return True
    return (rc & 0xFFFFFFFF) in _KILLED_NTSTATUS


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
        killed = _terminated_by_os(rc)
        if killed:
            # The founding incident, finally classified. A row the OS took away
            # is UNMEASURED, exactly like a row that ran out of clock -- the
            # cause differs, the epistemic status is identical, and only one of
            # the two had a name in this file before today.
            summary = (f"TERMINATED by the OS (rc={rc}) after {elapsed:.1f}s "
                       f"-- not a verdict")
        return {"name": name, "rc": rc, "elapsed": elapsed,
                "missing": False, "summary": summary, "budget": budget,
                "killed": killed, "stdout": cp.stdout, "stderr": cp.stderr}
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


# Exit codes. 0 and 1 keep their meaning so every existing caller is unaffected;
# the two new ones exist because "nothing was measured" and "something failed"
# are different claims and collapsing them is how a killed sweep came to be read
# as a verdict. Both are non-zero: the gate stays fail-closed in every direction.
EXIT_OK = 0
EXIT_MEASURED_FAILURE = 1      # rows ran, rows failed. A verdict about the code.
EXIT_INCONCLUSIVE = 3          # rows did not finish, or the tree moved under us.
EXIT_PREFLIGHT_REFUSED = 4     # the host cannot carry the sweep. Nothing ran.

# The exit code is what a shell sees; it is not what the estate remembers. The
# provenance store is three-valued and its writer took a bool, so an
# INCONCLUSIVE sweep was recorded as "the tests failed" and a REFUSED one was
# recorded as nothing at all -- leaving a stale green vouching for a tree the
# host could no longer measure. The ladder is carried across this boundary
# intact, in the store's own vocabulary.
_OUTCOME_FOR_EXIT = {
    EXIT_OK: "PASS",
    EXIT_MEASURED_FAILURE: "FAIL",
    EXIT_INCONCLUSIVE: "INCONCLUSIVE",
    EXIT_PREFLIGHT_REFUSED: "BLOCKED",
}


def _record_outcome_started(n_rows: int) -> None:
    """Stamp the store BEFORE dispatch, so a death leaves a trace.

    Fail-open like its sibling. Scoped runs never call it: a --row run does not
    vouch for the tree, so it must not overwrite the record of one that did.
    """
    try:
        from modules.cascade_prevention.verification_state import (
            OUTCOME_STARTED, record_verification)
        record_verification("verify_spp", False,
                            f"dispatching {n_rows} rows",
                            outcome=OUTCOME_STARTED)
    except Exception as exc:  # noqa: BLE001 -- must never fail a run
        print(f"  (verification write-ahead not recorded: {exc})")


def _record_outcome(rc: int, detail: str) -> None:
    """Carry this run's typed outcome into verification provenance.

    Fail-open, always: HR-CASCADE-001 and HR-CASCADE-003 read this store, and a
    verifier that died trying to say what it found would be worse than one that
    stayed quiet. Never let bookkeeping fail a run.
    """
    outcome = _OUTCOME_FOR_EXIT.get(rc, "INCONCLUSIVE")
    try:
        from modules.cascade_prevention.verification_state import (
            record_verification)
        record_verification("verify_spp", rc == EXIT_OK, detail,
                            outcome=outcome)
    except Exception as exc:  # noqa: BLE001 -- must never fail a run
        print(f"  (verification provenance not recorded: {exc})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--quiet", action="store_true",
                    help="suppress per-row stdout dumps; only print table")
    ap.add_argument("--row", default=None,
                    help="run a single named row, skip the rest")
    ap.add_argument("--peak-mb", type=int, default=ROW_PEAK_MB_ESTIMATE,
                    metavar="MB",
                    help=("estimated peak memory of ONE row, for the SQI-03 "
                          f"capacity gate (default {ROW_PEAK_MB_ESTIMATE}, an "
                          "estimate â€” not a measurement)"))
    ap.add_argument("--reserve-mb", type=int, default=HOST_RESERVE_MB,
                    metavar="MB",
                    help=(f"memory the rest of the machine needs (default "
                          f"{HOST_RESERVE_MB}). Exists so the PASSING branch of "
                          "the capacity gate can be driven deterministically"))
    ap.add_argument("--ignore-preflight", action="store_true",
                    help=("run even when the host capacity gate refuses. The "
                          "run is still recorded as BLOCKED: this suppresses "
                          "the refusal, never the finding"))
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
    ap.add_argument("--confirm-fails", action="store_true",
                    help=("re-run every red row alone once before reporting. "
                          "A parallel red measures the row and the harness "
                          "together; this separates them. Costs a second "
                          "pass over the failures, so it is opt-in."))
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
         600),  # Raised 30 -> 90 once already, on the same reasoning and
                # from a 13.6s figure that no longer reproduces. Timed solo
                # three times on 2026-09-02: 151s, 221s, 391s -- identical
                # deterministic output every run (2196 files scanned, 38
                # code leaks), so the WORK is constant and only wall time
                # moves, by 2.6x.
                #
                # Two separable facts. The FLOOR of the work already
                # exceeded the budget, so this row could never finish and
                # never produced a verdict -- its 38 code-path leaks have
                # gated nothing, and a gate that cannot practically fire
                # reads from outside exactly like a gate that passes. That
                # is a budget below the minimum possible runtime, and
                # correcting it is not absorption.
                #
                # The 2.6x spread on top of it is UNEXPLAINED and this
                # number does not certify it. 600 is a hang bound, not a
                # performance target: it exists to catch a wedge, and the
                # question of why a fixed 2196-file scan varies by 2.6x
                # stays open and unowned. Do not quote this as a budget
                # anyone met.
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
        # A knowledge-graph skip must stay recoverable. The Stop hook defers a
        # repo over its size cap; until 2026-08-27 the refresher it named did
        # not exist, so 1335 of 2140 writebacks deferred into nothing and two
        # repos sat at zero nodes -- one for 46 days.
        ("graphify-deferred",
         [PY, str(PP / "tools" / "test_graphify_deferred.py")],
         30),
        # What one project learns must reach the others, and must not carry
        # noise when it does. The bare >=2-projects predicate admits a bare
        # `FAILED`, JavaScript source and a doc template -- injecting those
        # into every project forever is worse than the silence they replace.
        ("cross-project-baseline",
         [PY, str(PP / "tools" / "test_cross_project_baseline.py")],
         60),
        # Two features that act on EVERY project without being asked, so both
        # are only safe if their selection is right. A wrong selector here is
        # not a bug in one repo, it is a wrong action in all of them.
        ("unattended-onboarding",
         [PY, str(PP / "tools" / "test_unattended_onboarding.py")],
         60),
        # Semantic admission for the event store. Shape validation cannot
        # tell a failure from a success, and 52 of the first 75 events were
        # not failures at all.
        ("ceps-admission",
         [PY, str(PP / "tools" / "test_ceps_admission.py")],
         60),
        # The Owner-correction loop, end to end. from_stop_hook() had no
        # caller and its documented reader (/ceps-confirm) did not exist, so
        # the drafts directory had never been created -- a caller-less writer
        # feeding a reader-less sink, which no liveness gate could see because
        # there were no fires to compare records against.
        ("ceps-corrections",
         [PY, str(PP / "tools" / "test_ceps_corrections.py")],
         45),
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
         # 9s typical, but the confirm-on-failure retry makes the WORST
         # case two inner 55s timeouts. The retry only fires when the host
         # is already slow -- exactly when a 60s budget would kill the row
         # and render it as a failure it never reached. Budget the worst
         # case, not the happy-path measurement.
         150),
        # The gate above judges performance; this one judges THAT gate.
        # It compared against the raw target while printing "over 1.5x
        # target", so it manufactured 5 false alarms and buried the one
        # real regression among them. Pure -- no subprocess, no clock.
        ("bench-gate",
         [PY, str(PP / "tools" / "test_bench_gate.py")],
         30),
        # SessionStart must not pay for what it does not use. Asserts what
        # is LOADED and what is SPAWNED, never wall time -- a timing gate
        # on this host is a coin flip (measured spreads of 79-418%).
        # Spawns 3 fresh interpreters + node, so the budget is generous.
        ("session-start-cost",
         [PY, str(PP / "tools" / "test_session_start_cost.py")],
         90),
        # mirror-parity compares 28 pairs and reports the other 345 files
        # as a bare count, which reads as accounted-for. This dispositions
        # them, and fails only on a registration pointing at a file that
        # does not exist -- wired and dead.
        ("mirror-unpaired",
         [PY, str(PP / "tools" / "test_mirror_unpaired.py")],
         45),
        # The path normaliser proposed 26 rewrites that would corrupt the
        # file or contradict doctrine. These pin the exemptions NARROW --
        # each one bookended by a plain leak that must still be rewritten,
        # because a silent gate is worse than a noisy one.
        ("path-exemptions",
         [PY, str(PP / "tools" / "test_path_exemptions.py")],
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
        # The umbrella's own report is the estate's most-read output, and
        # this row is what keeps its fail count honest about which reds it
        # measured and which it caused.
        ("umbrella-contention",
         [PY, str(PP / "tools" / "test_umbrella_contention.py")],
         60),
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
        # Registration PRESENCE is not registration COVERAGE. The bridge was
        # wired, firing and recording -- and blind to 75.5% of the command
        # traffic on this host, because the entry carrying its name matched
        # Bash while the hook declares Bash and PowerShell.
        # The AUDIT, not only its unit tests. verify_spp ran
        # test_mirror_unpaired.py, whose gate asserts "exit 1 GIVEN a
        # divergence" -- so the suite was green while session_delta_stop.js
        # was wired canonically and did not run in production. A test that
        # the detector works is not a run of the detector.
        ("mirror-divergence",
         [PY, str(PP / "tools" / "mirror_unpaired_audit.py")],
         90),
        ("capture-coverage",
         [PY, str(PP / "tools" / "test_capture_coverage.py")],
         60),
        # mirror-parity is branch-flip-immune BY DESIGN -- it reads the
        # committed blob on a named ref so a concurrent pane switching
        # branches cannot fake DRIFT. That fix removed the only aperture
        # onto the opposite failure: eleven registrations execute straight
        # out of the PP working tree, so the bytes that run are whatever
        # branch was last checked out there. Measured 2026-09-02, 45
        # commits on a pushed branch put 0 of 27 files into the running
        # tree. Committed and pushed is not installed when the install
        # location is a working tree.
        ("effective-state",
         [PY, str(PP / "tools" / "test_effective_state.py")],
         90),
        # The detector above reports SHADOWED. This row proves the report is
        # CONSEQUENTIAL: is_done was a weighted score, so a deliverable
        # could lose the delivery check and still clear 70 on the rest.
        # Replayed against a claim a prior session really made, the score
        # model returns OQS 100 and Done while the executing bytes are a
        # different version. A weight cannot express a precondition.
        ("effective-precondition",
         [PY, str(PP / "tools" / "test_effective_precondition.py")],
         90),
        # One registration should widen, not five: the Bash-chain carries the
        # guard that blocks git/npm via Bash to force them onto PowerShell,
        # so widening it would block the surface doctrine redirects to.
        ("capture-surface",
         [PY, str(PP / "tools" / "test_capture_surface_migration.py")],
         60),
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
        # USEA completeness baseline. Phases I and II shipped these gates and
        # registered none of them, so the constitutional floor was enforced by
        # whoever remembered to run it -- which is the Liveness Standard's own
        # finding wearing a different hat. All eight are cheap; measured
        # together they add about twelve seconds to the suite.
        ("usea-corpus",
         [PY, str(PP / "tools" / "usea_corpus_gate.py"), "--self-test"],
         30),
        ("usea-law2",
         [PY, str(PP / "tools" / "test_architectural_truth.py")],
         30),
        ("usea-ladder",
         [PY, str(PP / "tools" / "test_done_strength_ladder.py")],
         30),
        ("usea-inheritance",
         [PY, str(PP / "tools" / "test_baseline_inheritance.py")],
         30),
        ("usea-benchmark",
         [PY, str(PP / "tools" / "test_usea_cross_domain_benchmark.py")],
         45),
        ("usea-convergence",
         [PY, str(PP / "tools" / "test_convergence_bounds.py")],
         60),
        # The ownership audit was itself unwired -- an audit of who owns what,
        # that nothing ran. It fails when a cited owner is not on disk, and now
        # also when an agent defined here is neither dispatchable nor declared
        # dormant, which is the seed/subject gap the liveness sweep cannot see.
        ("usea-ownership",
         [PY, str(PP / "tools" / "usea_ownership_audit.py")],
         45),
        ("completion-authority",
         [PY, str(PP / "tools" / "test_completion_authority.py")],
         30),
        ("hunk-guard",
         [PY, str(PP / "tools" / "test_foreign_hunk_guard.py")],
         60),
        ("commit-scope",
         [PY, str(PP / "tools" / "test_commit_scope.py")],
         90),
        ("git-invocation",
         [PY, str(PP / "tools" / "test_git_invocation.py")],
         60),
        # The umbrella's own honesty gates. A gate nobody runs is the orphan
        # trap this very surface was built to close, so they are rows here.
        #
        # tools/test_verify_spp_preflight.py is DELIBERATELY ABSENT: it drives
        # this file through real subprocesses, so registering it as a row would
        # make the umbrella invoke itself once per row, recursively. It is run
        # directly, and this comment is the reason it looks unwired.
        ("row-unmeasured",
         [PY, str(PP / "tools" / "test_verify_spp_unmeasured.py")],
         120),
        ("conhost-leak",
         [PY, str(PP / "tools" / "test_conhost_hook_leak.py")],
         30),
        # Its sibling, and a different question. conhost-leak proves repair()
        # works on fixtures; this one asks whether the Owner's registry is
        # infected right now. The wrappers were removed at 21:37 on 2026-09-11
        # and were back by 22:27, and the suite stayed green throughout --
        # because every subject in it was synthetic. ADVISORY: the repair is
        # Owner-side by HR-001.
        ("live-hook-wrappers",
         [PY, str(PP / "tools" / "check_live_hook_wrappers.py")],
         20),
        # Incident 2026-09-16 20:02 -> 2026-09-18 13:55: a settings rewrite dropped
        # --event= from all six dispatcher registrations and every Power Pack hook
        # went dark for ~42 h while this whole suite stayed green -- no row had the
        # live REGISTRY as its subject. The drills (tree subject) block; the live
        # judgement is advisory for the same HR-001 reason as live-hook-wrappers.
        ("hook-registration-gate",
         [PY, str(PP / "tools" / "test_hook_registration_integrity.py")],
         60),
        ("settings-writer-argv",
         [PY, str(PP / "tools" / "test_settings_writer_argv.py")],
         30),
        ("live-hook-registry",
         [PY, str(PP / "tools" / "test_hook_registration_integrity.py"), "--live-only"],
         30),
        # This one DOES drive the umbrella through a real subprocess, and is a
        # row anyway -- the child is forced into the refusal branch by an
        # inflated --peak-mb, so it returns before dispatching a single row.
        # Bounded at depth one by construction, not by convention: a child that
        # refuses cannot reach the code that would spawn a grandchild.
        ("outcome-propagation",
         [PY, str(PP / "tools" / "test_outcome_propagation.py")],
         240),
        # Only the CONTROLS half is a regression gate. It proves every outcome
        # oracle still discriminates -- reference implementation passes, naive
        # one fails -- and spends no model call doing it. The arms are a paid
        # experiment and are deliberately NOT wired here; turning every
        # measurement into standing CI cost is its own antipattern.
        ("outcome-oracles",
         [PY, str(PP / "tools" / "usea_outcome_contrast.py"), "--controls-only"],
         120),
        ("fresh-inheritance",
         [PY, str(PP / "tools" / "test_fresh_session_inheritance.py")],
         30),
    ]

    if args.row:
        rows_spec = [r for r in rows_spec if r[0] == args.row]
        if not rows_spec:
            print(f"verify_spp: no row named {args.row!r}", file=sys.stderr)
            return 2

    print("=" * 72)
    print("verify_spp â€” S++ end-to-end umbrella")
    print(f"  PP root : {PP}")
    print(f"  rows    : {len(rows_spec)}")
    print(f"  budget  : {ROW_BUDGET_S}s per row default")
    print("=" * 72)

    # ---- Preflight: qualify the HOST before believing anything it says -------
    env = _preflight(PP, workers, int(args.peak_mb), int(args.reserve_mb))
    print("  PREFLIGHT (SQI-03 host capacity)")
    if env["available_mb"] is not None:
        print(f"    memory   : {env['available_mb']} MB available, "
              f"{env['required_mb']} MB required "
              f"({env['peak_mb_per_unit']} MB/row estimated Ã— "
              f"{env['workers']} in flight + reserve)")
    else:
        print(f"    memory   : NOT MEASURABLE ({env.get('error') or 'no probe'})")
    print(f"    state    : {env['state']}   ceiling: {env['verdict_ceiling']}")
    if env["dirty_before"] is not None:
        print(f"    tree     : {len(env['dirty_before'])} dirty path(s) at open")
    else:
        print("    tree     : NOT READABLE â€” contamination cannot be bracketed")

    # A SCOPED run is not a sweep, and must not inherit a sweep's ceremony. The
    # caller who typed --row has already done the thing the refusal would ask
    # them to do; refusing them is the gate punishing the correct move. It is
    # reported and it lowers the ceiling -- it just does not block.
    scoped = bool(args.row)
    if env["capacity"] is False and not args.ignore_preflight and not scoped:
        # Refuse, and name the scoped alternative. Silently shrinking the sweep
        # to whatever still fits would report a green that measured less than it
        # claims; refusing says so out loud and leaves the Owner a real move.
        print("=" * 72)
        print(f"  REFUSED â€” {env['blocker']}")
        print("  A sweep the host cannot carry does not produce a verdict about")
        print("  this code; it produces a verdict about this afternoon. Options:")
        print("    * free memory and re-run")
        print("    * run a scoped row:  verify_spp.py --row <name>")
        print("    * lower the load:    verify_spp.py --parallel 1")
        print("    * override (records BLOCKED): --ignore-preflight")
        print("=" * 72)
        # RECORD THE REFUSAL. This return used to leave the store untouched,
        # which is the worst of the four outcomes to be silent about: the
        # previous entry keeps vouching for the tree for up to an hour, so a
        # sweep the host could not even start reads downstream as a green that
        # merely has not expired yet. A refusal is a fact about this run and it
        # overwrites the fact that is no longer current.
        _record_outcome(EXIT_PREFLIGHT_REFUSED, f"refused: {env['blocker']}")
        return EXIT_PREFLIGHT_REFUSED
    if env["capacity"] is None:
        print("    NOTE     : capacity is MARGINAL or unmeasured. A row that dies")
        print("               on this host is UNMEASURED, not a defect of its subject.")

    # WRITE-AHEAD, stamped before a single row is dispatched. MEASURED
    # 2026-09-11: this sweep was taken by the OS at roughly row 50 of 87 and
    # recorded NOTHING, because the process that writes the outcome is the
    # process that died. The store could not tell a sweep that died from a
    # sweep that never ran -- the founding incident of this whole ladder,
    # recurring one layer further in, in the code written to prevent it.
    #
    # A STARTED still standing at read time is the only evidence a death
    # leaves. It reads as None, so it can neither vouch nor accuse; it just
    # stops the previous green from quietly outliving the run that replaced it.
    if not scoped:
        _record_outcome_started(len(rows_spec))

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

    # CONTENTION CONFIRMATION. A parallel run measures the row and the
    # harness together, and cannot say which one produced a red. Measured
    # 2026-09-02: of fourteen strict fails and three unmeasured rows in one
    # parallel run, four passed cleanly when re-run alone -- including one
    # that had exited 1, so this is not only about timeouts. Reporting all
    # seventeen as defects would have been wrong by four, and raising the
    # budgets to make the timeouts go away would have converted unmeasured
    # into measured without measuring anything.
    #
    # Opt-in, because re-running every red doubles the cost of a bad run.
    # Nothing is suppressed: both observations are printed, and a row that
    # fails alone stays exactly as red as it was.
    contended = []
    if args.confirm_fails and workers > 1 and not args.row:
        suspect = suspect_rows(results, ADVISORY_ROWS)
        if suspect:
            print("=" * 72)
            print(f"  [confirm] re-running {len(suspect)} red row(s) alone -- "
                  "a parallel red measures the row AND the harness",
                  flush=True)
            by_spec = {n: (a, b) for (n, a, b) in rows_spec}
            for r in suspect:
                argv, budget = by_spec[r["name"]]
                solo = _row(r["name"], argv, budget=budget)
                verdict = ("still red" if solo["rc"] != 0 else "PASSED ALONE")
                print(f"    {r['name'].ljust(28)} {verdict}"
                      f"  ({solo['elapsed']:.1f}s alone vs "
                      f"{r['elapsed']:.1f}s under load)")
                if apply_solo(r, solo):
                    contended.append(r["name"])
            if contended:
                print("    -> these reds did not reproduce without the "
                      "harness's own load. That is a fact about this run, "
                      "not a clean bill for the rows.")

    total_elapsed = time.monotonic() - t_total
    print("=" * 72)
    print(f"  total elapsed: {total_elapsed:.2f}s")
    if contended:
        print(f"  CONTENDED: {len(contended)} row(s) red only under "
              f"parallel load — {contended}")

    # Separated from failures on purpose: a timeout is an unmeasured row.
    timed_out = [r for r in results if r.get("timed_out")]
    if timed_out:
        print(f"  UNMEASURED: {len(timed_out)} row(s) did not finish â€” "
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

    # ---- Bracket: did the tree move while the oracle was looking? -----------
    # An oracle's verdict is about its subject only if its observation domain
    # equals its subject. This umbrella's domain is the whole repository, so a
    # concurrent writer can turn a green or a red into a statement about timing.
    # The SET is diffed, not the count, so the moved paths can be NAMED -- and a
    # named movement is often demonstrably out of scope, which is the difference
    # between an INCONCLUSIVE you can act on and one you cannot.
    dirty_after = _dirty_paths(PP)
    moved: list[str] = []
    if env["dirty_before"] is not None and dirty_after is not None:
        before, after = set(env["dirty_before"]), set(dirty_after)
        moved = sorted((before - after) | (after - before))
        if moved:
            print(f"  TREE MOVED during the run: {len(moved)} path(s)")
            for p in moved[:12]:
                side = "left" if p in before - after else "entered"
                print(f"    {side:<8s} {p}")
            if len(moved) > 12:
                print(f"    ... and {len(moved) - 12} more")

    # ---- Bracket: did the HOST hold up while the oracle was looking? --------
    # The precondition is asserted at the END of the observation window, not only
    # at the start. A run that silently lost its precondition mid-flight is
    # indistinguishable from a subject that did nothing, and the convenient
    # reading of that ambiguity is always the one that blames the subject.
    #
    # Deliberately NOT a veto over a clean green: rows that ran and passed on a
    # degrading host still ran and still passed. Headroom collapse is an
    # EXPLANATION for a failure or a non-finish, never an eraser for a success.
    env_close = _preflight(PP, workers, int(args.peak_mb), int(args.reserve_mb))
    host_degraded = (env["capacity"] is True and env_close["capacity"] is not True)
    if host_degraded:
        print(f"  HOST DEGRADED during the run: "
              f"{env['available_mb']} MB -> {env_close['available_mb']} MB available")
        print("    (a row that failed or died on this host is not attributable"
              " to its subject)")

    # ---- Verdict ------------------------------------------------------------
    # A row that did not FINISH has said nothing about the thing it measures.
    # Counting it as a failure conflates "the gate found a defect" with "the gate
    # never ran", and sends an engineer to repair code that may be fine.
    # Two ways to produce no verdict: run out of clock, or be taken by the OS.
    # The second was the founding incident and had no name here until today.
    unmeasured = [r for r in results if r.get("timed_out") or r.get("killed")]
    unmeasured_names = {r["name"] for r in unmeasured}
    killed_rows = [r for r in results if r.get("killed")]
    if killed_rows:
        print(f"  TERMINATED: {len(killed_rows)} row(s) were killed, not failed â€” "
              f"{[r['name'] for r in killed_rows]}")
        print("    (the OS removed the process; it judged nothing. This is the"
              " same epistemic state as a timeout, not a defect.)")
    failed_strict = [r for r in results
                     if r["rc"] != 0
                     and r["name"] not in ADVISORY_ROWS
                     and r["name"] not in unmeasured_names]
    advisory_failing = [r for r in results
                        if r["rc"] != 0 and r["name"] in ADVISORY_ROWS
                        and r["name"] not in unmeasured_names]
    measured = len(results) - len(unmeasured)

    if failed_strict:
        print(f"  STRICT FAIL: {len(failed_strict)} row(s) â€” "
              f"{[r['name'] for r in failed_strict]}")
        if moved or host_degraded:
            cause = []
            if moved:
                cause.append(f"the tree moved ({len(moved)} path(s))")
            if host_degraded:
                cause.append("host headroom collapsed mid-run")
            print(f"    CONTAMINATED: {' and '.join(cause)}, so these failures")
            print("    are not attributable to the changeset. Re-run them scoped")
            print("    (--row) on a still tree and a healthy host before acting.")
            rc = EXIT_INCONCLUSIVE
        else:
            rc = EXIT_MEASURED_FAILURE
    elif unmeasured or moved or env["capacity"] is not True:
        # `is not True` deliberately, not `is None`. MEASURED 2026-09-11: the
        # first draft tested only None, so a run that OVERRODE a BLOCKED
        # preflight (--ignore-preflight, or a scoped run on a starved host)
        # printed STRICT PASS -- on a host the gate had just said could not
        # carry it. The flag's own help text promised it "suppresses the
        # refusal, never the finding", and the code suppressed the finding.
        # That is the exact defect this whole surface exists to prevent, written
        # by the surface that prevents it. An override must change what the run
        # DOES, never what the run may CLAIM.
        why = []
        if unmeasured:
            why.append(f"{len(unmeasured)} row(s) did not finish "
                       f"({sorted(unmeasured_names)})")
        if moved:
            why.append(f"{len(moved)} path(s) moved in the tree")
        if env["capacity"] is None:
            why.append("host capacity was marginal or unmeasurable")
        if env["capacity"] is False:
            why.append(f"host capacity REFUSED and was overridden: "
                       f"{env['blocker']}")
        if host_degraded:
            why.append(f"host headroom collapsed during the run "
                       f"({env['available_mb']} MB -> "
                       f"{env_close['available_mb']} MB)")
        print(f"  INCONCLUSIVE â€” {measured} of {len(results)} rows measured, "
              f"none of them failing.")
        for w in why:
            print(f"    * {w}")
        print("    This is neither a pass nor a failure. Nothing here says the")
        print("    code is wrong, and nothing here licenses a done claim.")
        rc = EXIT_INCONCLUSIVE
    else:
        print(f"  STRICT PASS â€” {measured - len(advisory_failing)} "
              f"of {len(results)} rows OK"
              + (f", {len(advisory_failing)} advisory rows failing "
                 f"({[r['name'] for r in advisory_failing]})"
                 if advisory_failing else ""))
        rc = EXIT_OK
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
        _record_outcome(
            rc,
            f"{measured - len(failed_strict)}/{len(results)} rows measured"
            + (f"; strict fail {[r['name'] for r in failed_strict]}"
               if failed_strict else "")
            + (f"; {len(unmeasured)} unmeasured" if unmeasured else ""))
    return rc


if __name__ == "__main__":
    sys.exit(main())
