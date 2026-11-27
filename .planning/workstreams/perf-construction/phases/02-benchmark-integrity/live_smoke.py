#!/usr/bin/env python3
"""Live smoke for tools/bench_all.py on THIS host, without touching the
tracked ledger (plan 02-03, threat T-02-03-01).

Loads bench_all either from the working tree or, with --rev <hash>, from
`git show <hash>:tools/bench_all.py` executed into a fresh module whose
__file__ is the real path (so PP_PATH resolves to this repository). Points
LEDGER_PATH at a temp file, restricts ALL_BENCHES to the three real,
read-mostly benchmarks pytest, uqf_scan and proactive_dispatch (never the
session hub, vgate_suites or verify_spp), calls main(["--label",
"phase2-smoke"]) twice and prints each exit code plus the second temp-ledger
entry. Stdlib only; run with `python3 -I`.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import types
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
BENCH_PATH = REPO / "tools" / "bench_all.py"
TRACKED_LEDGER = REPO / "vault" / "benchmarks" / "ledger.json"
ALLOWED = ("pytest", "uqf_scan", "proactive_dispatch")


def load_module(rev):
    if rev:
        src = subprocess.run(
            ["git", "show", f"{rev}:tools/bench_all.py"], cwd=str(REPO),
            capture_output=True, text=True, timeout=30, check=True).stdout
    else:
        src = BENCH_PATH.read_text(encoding="utf-8")
    mod = types.ModuleType("bench_all_smoke")
    mod.__file__ = str(BENCH_PATH)
    sys.modules["bench_all_smoke"] = mod
    sys.path.insert(0, str(REPO))
    exec(compile(src, str(BENCH_PATH), "exec"), mod.__dict__)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rev", default=None,
                    help="git revision to load bench_all.py from")
    args = ap.parse_args()
    mod = load_module(args.rev)
    with tempfile.TemporaryDirectory() as td:
        tmp_ledger = Path(td) / "ledger.json"
        mod.LEDGER_PATH = tmp_ledger
        if Path(mod.LEDGER_PATH).resolve() == TRACKED_LEDGER.resolve():
            print("REFUSING: LEDGER_PATH is still the tracked ledger")
            return 2
        mod.ALL_BENCHES = [(n, f) for n, f in mod.ALL_BENCHES
                           if n in ALLOWED]
        names = [n for n, _f in mod.ALL_BENCHES]
        if sorted(names) != sorted(ALLOWED):
            print(f"REFUSING: benchmarks {names} != {list(ALLOWED)}")
            return 2
        print(f"SMOKE source={'rev ' + args.rev if args.rev else 'working tree'}"
              f" benches={names} ledger={tmp_ledger}")
        codes = []
        for i in (1, 2):
            print(f"\n=== call {i} ===", flush=True)
            try:
                rc = mod.main(["--label", "phase2-smoke"])
            except SystemExit as e:
                rc = e.code
            codes.append(rc)
            print(f"=== call {i} exit code: {rc} ===", flush=True)
        ledger = json.loads(tmp_ledger.read_text(encoding="utf-8"))
        last = ledger[-1] if isinstance(ledger, list) else ledger
        print(f"\nEXIT_CODES={codes} entries_in_temp_ledger={len(ledger)}")
        print("SECOND_ENTRY=" + json.dumps(
            {k: last.get(k) for k in ("results", "errors", "host_state",
                                     "verdicts", "ledger_schema", "quick")
             if k in last},
            indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
