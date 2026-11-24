"""V-R6 -- correction-guard.js (Anti-Antipattern R6) fires on corrections, not on "para".

Drives the REAL hook (node, stdin JSON) from both poles. The negatives are the
prompt shapes that produced 201 of 220 injections in 14 days (2026-11-24 census):
the Spanish preposition "para" and a label like "STOP:" inside ordinary text.
Exit 0 = all pass. Optional argv[1] = alternative hook path (control run).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

NODE = r"C:\Program Files\nodejs\node.exe"
HOOK = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    Path(__file__).resolve().parent.parent / "hooks" / "correction-guard.js")
LIVE = Path.home() / ".claude" / "hooks" / "correction-guard.js"

FIRE = [
    "para", "Para.", "stop!", "para, eso no es lo que pedi", "Detente ya.",
    "ok. stop", "no es eso", "that's wrong", "stop doing that", "ya lo dije",
    "no es lo que pedi", "eso no es verdad, quita esas coletillas", "no es correcto",
    "no, así no", "eso no.", "stop it", "para por favor", "ok, stop, that's not it",
]
QUIET = [
    "cual es la mayor palanca para todos los lanes para reconstruir todo?",
    "haz un script para medir el censo",
    "W4 STOP: HR-COST-002 reached, owner decision",
    "para eso sirve el gate, sigue",
    "go ahead",
    "stop at the first failing gate and report it",
    "no es mejor que lleve a la landing?",
    "explicame por que un 50% no es una moneda al aire",
    "pero eso no es malo, no?",
    "dime para que sirve.",
]

fails = 0


def fires(prompt: str) -> bool:
    p = subprocess.run([NODE, str(HOOK)], input=json.dumps({"prompt": prompt}),
                       capture_output=True, text=True, encoding="utf-8", timeout=20)
    return "CORRECTION DETECTED" in p.stdout


def check(name, cond, detail):
    global fails
    print(f"{'PASS' if cond else 'FAIL'} {name}: {detail}")
    fails += 0 if cond else 1


for p in FIRE:
    check("V-R6-FIRE", fires(p), repr(p))
for p in QUIET:
    check("V-R6-QUIET", not fires(p), repr(p))
if len(sys.argv) == 1:
    same = LIVE.is_file() and LIVE.read_bytes() == HOOK.read_bytes()
    check("V-R6-MIRROR", same, f"{LIVE} == repo copy")
print(f"V-R6: {'ALL PASS' if not fails else f'{fails} FAIL'}")
sys.exit(1 if fails else 0)
