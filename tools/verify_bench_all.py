"""verify_bench_all.py -- verify_spp BENCHMARKS_OK probe.

Runs `python tools/bench_all.py --quick --json` and asserts that the
quick-mode results fit within 1.5x of the SCS C26 targets. The 1.5x
band accounts for T-WIN-AV-001 cold-scan variance (300-700 ms can
land on any Python subprocess spawn on Windows).

That paragraph has been the docstring since the probe shipped. The code
under it compared against the RAW target and then printed "over 1.5x
target", so the gate was stricter than its contract and its report named
a threshold it had not used. Measured 2026-08-26, three back-to-back
runs on an idle host: spreads of 79%, 103%, 418% and 109% of the minimum.
The band is not decoration -- without it a single sample against a raw
target is a coin flip, and this gate was flipping it four times per run.

Two consequences, both fixed here:

  1. THE BAND IS APPLIED, as documented. `tis_report_ms: 268>225` was
     inside the band all along; so was `tco_gate_ms` at its median.
  2. A FAILURE MUST REPRODUCE. Process creation is where the variance
     enters (an ablation put the noise-free floor at 6 ms spread and the
     spawn-bearing run at 160 ms), so noise here is additive and
     independent per run. A second sample and the MIN of the two is the
     right statistic for "is this achievable": noise can only add.
     Costs nothing on the green path -- the retry is only paid when
     something already looks broken.

A MISSING benchmark is a failure, not a skip. The previous version
`continue`d past any name bench_all did not emit, so a benchmark that
stopped reporting made this gate greener. A denominator that shrinks
when a probe breaks measures memory, not performance.

This probe is wired into `tools/verify_spp.py` as the BENCHMARKS_OK row.
It exits 0 on PASS and 1 with the failing list otherwise.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]

# The documented allowance for T-WIN-AV-001 spawn variance. Named, so the
# report can print the number it actually compared against.
BAND = 1.5

# Samples taken before a failure is REPORTED. Only the first is paid on a
# healthy run; the others fire solely when something already looks over.
MAX_SAMPLES = 3

QUICK_TARGETS = {
    "tco_gate_ms": 270,
    "tis_report_ms": 225,
    "osa_dispatcher_ms": 300,
    "proactive_dispatch_ms": 30,
    "anti_patterns_ms": 120,
    # 38 was never a threshold for this operation. The probe called
    # record_error with category 'bench_all', which is not in
    # VALID_CATEGORIES, so it returned at the first guard: all 22 historical
    # ledger samples (0.4-3.3 ms) timed a REFUSAL, and 38 gave that refusal a
    # 12-95x margin it could never exceed. Repaired 2026-08-27; the record
    # path measured in isolation, n=9, all recorded: min 29.0, p50 39.5,
    # p90 65.0, max 73.3, worst min-of-3 window 44.2. 60 (band 90) clears
    # that worst window by ~2x and still catches a genuine doubling. This is
    # the FIRST threshold this operation has had, not a relaxed one.
    "ceps_record_ms": 60,
    "session_hub_ms": 300,
    "never_again_ms": 30,
}


def sample() -> tuple[dict | None, str]:
    """One bench_all --quick run. Returns (results, error_message)."""
    try:
        r = subprocess.run(
            [sys.executable, str(PP / "tools" / "bench_all.py"),
             "--quick", "--json"],
            capture_output=True,
            text=True,
            # 45, not 55: MAX_SAMPLES of these must fit inside the row's
            # 150s budget, or the retry that exists to prevent a false
            # failure becomes the cause of one.
            timeout=45,
            cwd=str(PP),
        )
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT -- bench_all --quick > 55 s wall"
    except Exception as exc:  # noqa: BLE001
        return None, f"subprocess error -- {type(exc).__name__}: {exc}"

    out = r.stdout.strip()
    if not out:
        return None, (f"empty stdout from bench_all (rc={r.returncode}; "
                      f"stderr head: {r.stderr.strip()[:200]})")

    # bench_all --json prints progress lines THEN a JSON object THEN a
    # closing "bench_all exit rc=..." trailer. Find the first open-brace
    # that begins a complete JSON object and raw_decode from there.
    decoder = json.JSONDecoder()
    for i, ch in enumerate(out):
        if ch != "{":
            continue
        try:
            payload, _ = decoder.raw_decode(out[i:])
            return payload.get("results", {}) or {}, ""
        except json.JSONDecodeError:
            continue
    return None, "no parseable JSON in bench_all stdout"


def _value(results: dict, name: str) -> float | None:
    v = results.get(name)
    return float(v) if isinstance(v, (int, float)) else None


def evaluate(first: dict, *rest: dict) -> tuple[list[str], dict]:
    """Judge one or more samples. Pure -- no subprocesses, no clock.

    Returns (missing, over). `over` maps benchmark -> the value held
    against it, which is the MIN across supplied samples.
    """
    second = rest[0] if rest else None
    extra = rest[1:]
    # Absent is not OK. bench_all emits `<name>_error` instead of a value
    # when a probe breaks, so a missing name means that benchmark FAILED
    # to run -- surfacing it is the whole point.
    missing = [n for n in QUICK_TARGETS if _value(first, n) is None]
    over = {n: v for n in QUICK_TARGETS
            if (v := _value(first, n)) is not None
            and v > QUICK_TARGETS[n] * BAND}
    if not over or second is None:
        return missing, over

    confirmed = {}
    for n, v1 in over.items():
        # min() because spawn noise is additive: the smallest sample is
        # the closest estimate of the real cost.
        vals = [v1] + [v for v in
                       (_value(s, n) for s in (second,) + extra)
                       if v is not None]
        best = min(vals)
        if best > QUICK_TARGETS[n] * BAND:
            confirmed[n] = best
    return missing, confirmed


def main() -> int:
    first, err = sample()
    if first is None:
        print(f"BENCHMARKS_OK: {err}")
        return 1

    missing, over = evaluate(first)

    # Confirm before accusing. Only paid when something already looks bad,
    # so a healthy run still costs exactly one sample.
    #
    # TWO was not enough. Measured over four consecutive invocations on
    # this host, one still reported extra alarms -- including
    # `proactive_dispatch_ms 52>45`, whose median is 25. The noise is
    # heavy-tailed, so a single retry can draw two slow samples in a row.
    # A third cuts that sharply and is never reached on a healthy run.
    samples = [first]
    while over and len(samples) < MAX_SAMPLES:
        nxt, _err = sample()
        if nxt is None:
            break
        samples.append(nxt)
        missing, over = evaluate(*samples)
    retried = len(samples) > 1

    checked = len(QUICK_TARGETS) - len(missing)
    if not over and not missing:
        print(f"BENCHMARKS_OK: {checked}/{len(QUICK_TARGETS)} quick "
              f"benchmarks within {BAND}x SCS C26 targets")
        return 0

    parts = []
    if missing:
        parts.append("MISSING (probe did not report): " + ", ".join(missing))
    if over:
        detail = ", ".join(
            f"{n}: {v:.0f}>{QUICK_TARGETS[n] * BAND:.0f}"
            f" ({BAND}x{QUICK_TARGETS[n]})"
            for n, v in sorted(over.items()))
        how = (f"min of {len(samples)} samples" if retried
               else "single sample")
        parts.append(f"{len(over)}/{checked} over {BAND}x target "
                     f"[{how}]: {detail}")
    print("BENCHMARKS_OK: " + " | ".join(parts))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
