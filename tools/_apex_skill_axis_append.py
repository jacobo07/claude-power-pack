#!/usr/bin/env python3
"""M19 -- atomic append of `Skill Completion Axis` to apex on both loose
and PP mirrors + sync of skill-completion-standard.md loose -> PP.

Per C6 of the new Skill Completion Standard, never use `cat >>` against
tracked markdown. This helper writes atomically (tempfile + os.replace)
to avoid the 2026-05-23 corruption pattern.

Idempotent: skips the apex append if the axis marker is already present.
"""
from __future__ import annotations
import os
import sys
import tempfile
from pathlib import Path

PP = Path("knowledge_vault/core/apex-completion-standard.md")
LOOSE_APEX = Path(os.path.expanduser(
    "~/.claude/knowledge_vault/core/apex-completion-standard.md"))
PP_SCS = Path("knowledge_vault/core/skill-completion-standard.md")
LOOSE_SCS = Path(os.path.expanduser(
    "~/.claude/knowledge_vault/core/skill-completion-standard.md"))

APEX_MARKER = "## Skill Completion Axis (sealed 2026-05-25)"
APEX_AXIS = """

## Skill Completion Axis (sealed 2026-05-25) -- baseline raised post LT+CEPS

A new PP skill is complete only when all seven clauses of the Skill
Completion Standard (`knowledge_vault/core/skill-completion-standard.md`)
are satisfied with empirical evidence. Missing evidence == not complete.
Reality Contract applies: the evidence is the test output, not the
description of the test.

### The seven clauses (short form -- full spec in the SCS document)

1. **C1**: empirical pass-gate declared before the first byte of skill content.
2. **C2**: side-by-side with-vs-without-skill comparison on the same prompts.
3. **C3**: no-collision against the 10 JIT trigger families + Intent-Lock + Arch-Check + vague-lint + active hooks + 29 baseline tests.
4. **C4**: distribution integrated with CEPS (`tools/ceps.py::record_error` + `vault/ceps/events.jsonl`).
5. **C5**: auto-test stub via `tools/ceps_test_gen.py` for any regression / security / drift invariant.
6. **C6**: atomic write for every markdown append (no `cat >>` -- direct consequence of the 2026-05-23 apex corruption).
7. **C7**: RTK proxy compatibility -- no raw-stdout byte slicing in skill tooling.

### Enforcement

A skill that fails any clause cannot be merged to `main`. The Owner-facing
PR description must carry a Skill Completion Standard table with one row
per clause + evidence path + checked status. Missing rows or unchecked
clauses block the merge.

### Bootstrap references (the two skills that defined this axis)

- `lateral-thinking` skill (`~/.claude/skills/lateral-thinking/`): 11 V-* gates passing in `tools/test_lateral_thinking.py`.
- CEPS substrate (`tools/ceps.py` + `tools/ceps_test_gen.py`): 10/10 closed-loop in `tools/test_ceps_closed_loop.py`, 8/8 full-cycle in `tools/test_ceps_full_cycle.py`.

These two were built simultaneously and bootstrap each other. The axis
freezes the pattern they established.

### DONE-gate

`python -m pytest tests/test_forensic_probes.py tests/test_mistake_frequency_xplat.py -q`
+ `python tools/test_lateral_thinking.py`
+ `python tools/test_ceps_closed_loop.py`
+ `python tools/test_ceps_full_cycle.py`
-- all four exit 0 = axis sealed.
"""


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp",
                               dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def append_apex(target: Path) -> bool:
    if not target.is_file():
        print(f"missing: {target}", file=sys.stderr)
        return False
    body = target.read_text(encoding="utf-8")
    if APEX_MARKER in body:
        print(f"axis already present in {target} (idempotent skip)")
        return True
    if not body.endswith("\n"):
        body += "\n"
    _atomic_write(target, body + APEX_AXIS)
    print(f"axis appended to {target} (bytes={target.stat().st_size})")
    return True


def sync_scs() -> bool:
    if not LOOSE_SCS.is_file():
        print(f"loose SCS missing: {LOOSE_SCS}", file=sys.stderr)
        return False
    content = LOOSE_SCS.read_text(encoding="utf-8")
    PP_SCS.parent.mkdir(parents=True, exist_ok=True)
    if PP_SCS.is_file() and PP_SCS.read_text(encoding="utf-8") == content:
        print(f"PP SCS already in sync with loose")
        return True
    _atomic_write(PP_SCS, content)
    print(f"PP SCS synced from loose (bytes={PP_SCS.stat().st_size})")
    return True


def main() -> int:
    ok = True
    ok &= append_apex(PP)
    ok &= append_apex(LOOSE_APEX)
    ok &= sync_scs()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
