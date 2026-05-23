"""V-block empirical test runner for arch_check.py.

Runs every V-test, captures the JSON verdict, prints a table, and
returns exit 0 iff all V-tests met their expected verdict.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCH_CHECK = HERE / "arch_check.py"

V_TESTS = [
    # (test_id, prompt, expected_verdict)
    ("V-COLLISION",
     "Vamos a montar un workflow con n8n para automatizar X. "
     "Debería diseñar la arquitectura asi?",
     "COLLISION"),
    ("V-COLLISION-2",
     "Quiero que un hook auto-fire un slash command para implementar "
     "la arquitectura automaticamente. Debería disenar asi?",
     "COLLISION"),
    ("V-WARNING",
     "Voy a escribir 5 archivos en paralelo en un Write batch. "
     "Debería diseñar la arquitectura asi?",
     "WARNING"),
    ("V-WARNING-2",
     "Llevamos meses sin mergear la rama feat a main, ahora la merge-amos "
     "en una sola pasada. Debería implementar la arquitectura asi?",
     "WARNING"),
    ("V-CLEAR",
     "Explica este snippet de Rust:\n"
     "fn add(a: i32, b: i32) -> i32 { a + b }",
     "CLEAR"),
]


def run_one(prompt: str) -> tuple[dict, float]:
    """Run arch_check.py with stdin=prompt. Return (parsed_json, elapsed_s)."""
    t0 = time.monotonic()
    proc = subprocess.run(
        [sys.executable, str(ARCH_CHECK), "--fast"],
        input=prompt.encode("utf-8"),
        capture_output=True,
        timeout=30,
    )
    elapsed = time.monotonic() - t0
    try:
        out = json.loads(proc.stdout.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        out = {"verdict": "ERROR",
               "raw_stdout": proc.stdout.decode("utf-8", errors="replace"),
               "raw_stderr": proc.stderr.decode("utf-8", errors="replace")}
    return out, elapsed


def main() -> int:
    print(f"V-block runner: {ARCH_CHECK}")
    print("=" * 80)
    fails = 0
    rows = []
    for tid, prompt, expected in V_TESTS:
        out, elapsed = run_one(prompt)
        actual = out.get("verdict", "ERROR")
        ok = (actual == expected)
        if not ok:
            fails += 1
        rows.append({
            "id": tid,
            "expected": expected,
            "actual": actual,
            "ok": ok,
            "timing_ms": out.get("timing_ms", -1),
            "wall_ms": int(elapsed * 1000),
            "sources": [s.get("path", "")[-60:]
                        for s in out.get("sources", [])[:2]],
            "is_veto_top": out.get("sources", [{}])[0].get("is_veto")
                          if out.get("sources") else None,
        })

    # Print table.
    print(f"{'ID':16s} {'EXP':12s} {'ACT':12s} {'OK':4s} "
          f"{'INT_MS':8s} {'WALL_MS':8s}")
    for r in rows:
        ok_mark = "PASS" if r["ok"] else "FAIL"
        print(f"{r['id']:16s} {r['expected']:12s} {r['actual']:12s} "
              f"{ok_mark:4s} {r['timing_ms']:8d} {r['wall_ms']:8d}")
        for src in r["sources"]:
            print(f"    -> ...{src}")

    # V-TIMING: 10 runs of V-COLLISION-1.
    print("\nV-TIMING: 10 runs of V-COLLISION-1")
    timings = []
    for _ in range(10):
        _, e = run_one(V_TESTS[0][1])
        timings.append(int(e * 1000))
    timings.sort()
    p05 = timings[0]
    p50 = timings[len(timings) // 2]
    p95 = timings[int(len(timings) * 0.95)] if len(timings) >= 20 else timings[-1]
    print(f"  p05={p05}ms  p50={p50}ms  p95={p95}ms  all={timings}")
    timing_ok = p95 < 3000 and p05 < 500
    print(f"  V-TIMING {'PASS' if timing_ok else 'FAIL'}")
    if not timing_ok:
        fails += 1

    # Persist for later reference.
    out_dir = HERE.parent.parent / "vault" / ".arch-index"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "timings.json").write_text(
        json.dumps({"runs": timings, "p05": p05, "p50": p50, "p95": p95,
                    "ok": timing_ok}, indent=2),
        encoding="utf-8",
    )
    (out_dir / "v_block.json").write_text(
        json.dumps({"rows": rows, "timing": {"p05": p05, "p50": p50,
                                              "p95": p95, "all": timings}},
                   indent=2),
        encoding="utf-8",
    )

    print("\n" + "=" * 80)
    if fails == 0:
        print(f"V-BLOCK: ALL {len(rows)+1} TESTS PASSED")
        return 0
    print(f"V-BLOCK: {fails} FAILURES (of {len(rows)+1} total)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
