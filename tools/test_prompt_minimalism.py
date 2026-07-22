#!/usr/bin/env python3
"""Validation harness for hooks/prompt_minimalism_gate.js (CGF Workstream D).

Runs the hook's exported `isOverPrescriptive` via node -e against real and
representative historical cases -- not synthetic toy strings alone. Prints
V-PROMPT-MINIMALISM-* gate lines per the project's V-* convention.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "prompt_minimalism_gate.js"

# Real historical case: the actual CGF Phase 2 kickoff prompt from this session
# (vault/plans/cgf-phase2-2026-07-22.md backs it up). Long, imperative, Spanish,
# heavily constrained -- but zero code fences. Must NOT trip.
CGF_REAL_PROMPT = """PREFLIGHT:
git fetch origin && git log --oneline -5

EXECUTION MODE
CGF Workstreams B -> D -> E -> C -- continuar straight through
"A y F sellados (8d1f12f, 5b99223). Continuar con los
cuatro workstreams restantes sin detenerse salvo
contradiccion constitucional, evidencia nueva que invalide
el scope, o riesgo irreversible no previsto."

WORKSTREAM B -- ORPHAN DISPOSITION (~175 items)
  Clasificar cada orphan con evidencia contra estas categorias:
    CONNECT: consumidor identificado, wiring claro, bajo riesgo
    LIBRARY: disponible para uso pero no requiere consumidor activo
  No conectar ciegamente. Cada CONNECT requiere evidencia de:
    consumidor real, ruta de activacion, ausencia de conflicto.
  Done-gate: cada orphan tiene disposicion explicita.
CONSTRAINTS:
  NUNCA git add -A.
  Sin codigo inline.
"""

# A KobiiAI-stack-style non-negotiable-technology prompt (real project pattern,
# vault/knowledge_base/stacks/kobiicraft-ai.md). Names exact frameworks/versions
# as hard constraints -- must NOT trip; naming required tech is not "code".
STACK_CONSTRAINT_PROMPT = """Build the session-restore endpoint.
Frontend=frozen (Next.js 16+React 19+Prisma+SQLite). Backend=Elixir/OTP/Phoenix.
Must use the existing Prisma schema at prisma/schema.prisma -- do not add a
new migration. Done-gate: `mix test` green + a manual curl against the
running Phoenix endpoint returns 200.
"""

# Existing-code-as-context prompt: quotes real code but frames it as reference,
# per the Agent tool's own guidance ("explain what you've already learned").
# Must NOT trip (exempted by the "current implementation" cue).
CONTEXT_CODE_PROMPT = """Investigate why session restore drops the 6th window.
The current implementation looks like this:
```js
function restoreWindow(id) {
  const w = windows.find(x => x.id === id);
  if (!w) return null;
  return openWindow(w);
}
```
Find why window 6 of 6 is under-counted and report back; do not fix it yet.
"""

# Clearly over-prescriptive: hands the sub-agent a function to transcribe
# verbatim instead of a contract. Must trip.
OVERPRESCRIPTIVE_PROMPT = """Implement the retry helper exactly like this:
```python
def retry(fn, times=3):
    for i in range(times):
        try:
            return fn()
        except Exception as e:
            if i == times - 1:
                raise
            continue
```
Put it in modules/util/retry.py and use it everywhere.
"""

# Borderline: a short one-line code fence (a path/import), below CODE_LINE_MIN.
# Must NOT trip.
SHORT_FENCE_PROMPT = """Run this and report the output:
```
python tools/test_prompt_minimalism.py
```
"""

CASES = [
    ("V-PROMPT-MIN-01-cgf-real-contract", CGF_REAL_PROMPT, False),
    ("V-PROMPT-MIN-02-stack-constraint", STACK_CONSTRAINT_PROMPT, False),
    ("V-PROMPT-MIN-03-context-code-exempt", CONTEXT_CODE_PROMPT, False),
    ("V-PROMPT-MIN-04-overprescriptive-detected", OVERPRESCRIPTIVE_PROMPT, True),
    ("V-PROMPT-MIN-05-short-fence-not-code", SHORT_FENCE_PROMPT, False),
]


def classify(prompt: str) -> bool:
    payload = json.dumps({"tool_name": "Task", "tool_input": {"prompt": prompt}})
    result = subprocess.run(
        ["node", str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=10,
        encoding="utf-8",
    )
    out = (result.stdout or "").strip()
    return bool(out)


def main() -> int:
    passes = 0
    fails = 0
    for gate_id, prompt, expect_trip in CASES:
        got_trip = classify(prompt)
        ok = got_trip == expect_trip
        if ok:
            passes += 1
            print(f"PASS {gate_id}: tripped={got_trip} expected={expect_trip}")
        else:
            fails += 1
            print(f"FAIL {gate_id}: tripped={got_trip} expected={expect_trip}")
    total = passes + fails
    fp_rate = 0 if total == 0 else fails / total
    print(f"PROMPT_MINIMALISM_PASS={passes}/{total}  false_positive_rate={fp_rate:.2f}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
