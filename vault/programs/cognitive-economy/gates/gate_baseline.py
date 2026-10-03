#!/usr/bin/env python
"""gate_baseline.py -- pillar A gate of the cognitive-economy campaign.

Re-runs `tools/usage_index.py window` for the two frozen denominators and compares the
result with the figures pre-registered in the ledger's `frozen.denominators`:

  * anchor  -- calls, cache_read, subagent_calls must reproduce EXACTLY;
  * D-W7    -- calls, subagent_calls, input, cache_write, cache_read, output must each be
               within 0.5 % of the frozen value (the index may gain late rows for a past
               window, which is why the raw figures were frozen).

The expected values are read from the ledger, never copied into this file, so the gate and
the pre-registration cannot drift apart. `--perturb DENOM.KEY=VALUE` replaces one expected
value; it exists only to drive the red branch (a gate never seen failing is a rumour).

Exit codes: 0 every figure holds; 1 any figure fails OR the index could not be read
(an unanswered question is never a pass).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
LEDGER = REPO / "vault/programs/cognitive-economy/ledger.json"
EXACT = {"anchor": ("calls", "cache_read", "subagent_calls")}
TOLERANT = {"D-W7": ("calls", "subagent_calls", "input", "cache_write", "cache_read", "output")}
TOLERANCE = 0.005
WINDOW = re.compile(r"^python tools/usage_index\.py window (\S+) (\S+)$")


def window_args(source: str) -> tuple[str, str]:
    m = WINDOW.match(source.strip())
    if not m:
        raise ValueError(f"frozen source is not a usage_index window command: {source!r}")
    return m.group(1), m.group(2)


def observe(start: str, end: str) -> dict:
    r = subprocess.run([sys.executable, str(REPO / "tools/usage_index.py"), "window", start, end],
                       cwd=str(REPO), capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=900)
    if r.returncode != 0:
        raise RuntimeError(f"usage_index window rc {r.returncode}: {(r.stderr or r.stdout)[-300:]}")
    return json.loads(r.stdout)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--perturb", action="append", default=[],
                    help="DENOM.KEY=VALUE: replace one expected value (red drill only)")
    a = ap.parse_args(argv)

    frozen = json.loads(LEDGER.read_text(encoding="utf-8"))["frozen"]["denominators"]
    expected = {d: {k: frozen[d][k] for k in keys} for d, keys in {**EXACT, **TOLERANT}.items()}
    for p in a.perturb:
        lhs, _, val = p.partition("=")
        denom, _, key = lhs.rpartition(".")
        if denom not in expected or key not in expected[denom] or not val.lstrip("-").isdigit():
            print(f"GATE_BASELINE=FAIL bad --perturb {p!r}")
            return 1
        expected[denom][key] = int(val)
        print(f"  perturbed {denom}.{key} expected -> {val}")

    fails = []
    for denom in expected:
        try:
            got = observe(*window_args(frozen[denom]["source"]))
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            fails.append(f"{denom}: could not observe ({exc})")
            continue
        for key, want in expected[denom].items():
            have = got.get(key)
            if not isinstance(have, int):
                fails.append(f"{denom}.{key}: observed {have!r}, not a number")
                continue
            if denom in EXACT:
                ok, how = have == want, "exact"
            else:
                drift = abs(have - want) / want if want else float(have != 0)
                ok, how = drift <= TOLERANCE, f"drift {drift:.4%} (limit {TOLERANCE:.1%})"
            print(f"  {'ok  ' if ok else 'FAIL'} {denom}.{key} expected {want} observed {have} {how}")
            if not ok:
                fails.append(f"{denom}.{key}")
    print(f"GATE_BASELINE={'PASS' if not fails else 'FAIL'} failures={len(fails)}")
    for f in fails:
        print(f"  failed: {f}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
