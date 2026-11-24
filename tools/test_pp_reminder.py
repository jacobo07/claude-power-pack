"""V-PPR -- the UserPromptSubmit Power Pack reminder (T3-CT W5, 2026-11-24).

The full reminder fires once per session and then sits in context as rent for
every later call. v4 keeps only what the always-loaded ~/.claude/CLAUDE.md does
not already deliver. This gate drives the REAL hook (node, stdin JSON, a fresh
session id) and checks both poles:
  - KEEP: the four lines only this hook delivers are still emitted;
  - DROP: the lines duplicated by CLAUDE.md (or pointing at nothing) are gone;
  - second prompt in the same session gets the 1-line pointer, not the block;
  - every DROP claim is re-checked: the duplicated concept must really be in
    ~/.claude/CLAUDE.md, or dropping it removed doctrine instead of a copy.
Exit 0 = all pass.
"""
from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path

NODE = r"C:\Program Files\nodejs\node.exe"
HOOK = Path.home() / ".claude" / "hooks" / "power-pack-reminder.js"
GLOBAL_MD = Path.home() / ".claude" / "CLAUDE.md"

KEEP = [
    "INVOKE the claude-power-pack skill",
    "LIGHT (lookup/fix) | STANDARD (1-5 files) | DEEP (5+ files) | FORENSIC (prod risk)",
    "Constitution Core 5",
    "SUPREMACY MODE",
]
# dropped line marker in the old text -> evidence it is in the global CLAUDE.md
DROP = {
    "GLOBAL_ALIGNMENT_LEDGER": "GLOBAL_ALIGNMENT_LEDGER.md",
    "CARL:": "<carl-rules>",
    "Governance Overlay": "Governance overlay",
    "USAP:": "(USAP)",
    "Intent Compiler:": "Intent compiler",
    "Completion Gates:": "Completion gates",
    "Token Efficiency:": "Token austerity",
    "Mistakes Registry": "mistakes-global.md",
    "Session Logging": None,  # dropped because the target does not exist
}
MAX_FULL_CHARS = 1100  # old v3 full block was 2,374 chars

fails = 0


def check(name: str, cond: bool, detail: str) -> None:
    global fails
    print(f"{'PASS' if cond else 'FAIL'} {name}: {detail}")
    if not cond:
        fails += 1


def run(session_id: str) -> str:
    p = subprocess.run([NODE, str(HOOK)],
                       input=json.dumps({"session_id": session_id, "prompt": "x"}),
                       capture_output=True, text=True, encoding="utf-8", timeout=20)
    out = json.loads(p.stdout)
    return out["hookSpecificOutput"]["additionalContext"]


def main() -> int:
    sid = f"vppr-{uuid.uuid4()}"
    full = run(sid)
    for k in KEEP:
        check("V-PPR-KEEP", k in full, repr(k))
    for k in DROP:
        check("V-PPR-DROP", k not in full, f"{k!r} absent")
    check("V-PPR-SIZE", len(full) <= MAX_FULL_CHARS, f"{len(full)} <= {MAX_FULL_CHARS}")
    second = run(sid)
    check("V-PPR-ONCE", second != full and len(second) < 200,
          f"2nd prompt {len(second)} chars")
    md = GLOBAL_MD.read_text(encoding="utf-8-sig", errors="replace")
    for k, ev in DROP.items():
        if ev is None:
            gone = not (Path.home() / ".claude" / "memory" / "sessions").exists()
            check("V-PPR-DROP-JUSTIFIED", gone, f"{k}: memory/sessions absent")
        else:
            check("V-PPR-DROP-JUSTIFIED", ev in md, f"{k}: {ev!r} in global CLAUDE.md")
    print(f"V-PPR: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
