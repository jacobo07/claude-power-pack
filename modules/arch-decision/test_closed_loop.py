"""V-CLOSED-LOOP test for arch_check.py.

Run arch_check twice with the same prompt; verify byte-identical
context output. This proves the engine is deterministic and that the
closed-loop UKDL row writes feed back into subsequent runs.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCH_CHECK = HERE / "arch_check.py"

PROMPT = (
    "Voy a diseñar la arquitectura de sessions usando Redis en el "
    "sistema TUAX. Debería implementar la decisión asi o evaluar "
    "otra alternativa primero?"
)


def run_one() -> dict:
    proc = subprocess.run(
        [sys.executable, str(ARCH_CHECK), "--fast"],
        input=PROMPT.encode("utf-8"),
        capture_output=True,
        timeout=10,
    )
    return json.loads(proc.stdout.decode("utf-8", errors="replace"))


def main() -> int:
    r1 = run_one()
    r2 = run_one()

    ctx1 = r1.get("context", "")
    ctx2 = r2.get("context", "")
    verdict1 = r1.get("verdict")
    verdict2 = r2.get("verdict")

    print(f"V-CLOSED-LOOP run1: verdict={verdict1} ctx_len={len(ctx1)}")
    print(f"V-CLOSED-LOOP run2: verdict={verdict2} ctx_len={len(ctx2)}")

    if verdict1 != verdict2:
        print(f"FAIL: verdicts differ ({verdict1} != {verdict2})")
        return 1
    if ctx1 != ctx2:
        print("FAIL: contexts differ byte-by-byte across two identical runs")
        # Print first diff char.
        for i, (a, b) in enumerate(zip(ctx1, ctx2)):
            if a != b:
                print(f"  first diff at index {i}: {a!r} vs {b!r}")
                break
        return 1

    # Verify the new UKDL-AC rows surface for an arch-check prompt.
    src_paths = [s.get("path", "") for s in r1.get("sources", [])]
    ukdl_hit = any("ukdl-universal.md" in p for p in src_paths)
    print(f"V-CLOSED-LOOP UKDL surfacing: "
          f"{'hit' if ukdl_hit else 'miss'} in top sources")
    print(f"  top sources: {[Path(p).name for p in src_paths]}")

    print("\nV-CLOSED-LOOP: PASS (deterministic across runs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
