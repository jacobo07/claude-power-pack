#!/usr/bin/env python3
"""M11 -- atomic append of `Skill Completion Axis v2 (sealed 2026-05-26)`
section to apex-completion-standard.md on both loose and PP mirrors.

Per SCS C6 (atomic write) + C8 (evidence archived at commit-time), this
helper writes via tempfile + os.replace so the 2026-05-23 `cat >>`
corruption pattern cannot recur. Idempotent: skips if the v2 marker
is already present.
"""
from __future__ import annotations
import os
import sys
import tempfile
from pathlib import Path

PP = Path("knowledge_vault/core/apex-completion-standard.md")
LOOSE = Path(os.path.expanduser(
    "~/.claude/knowledge_vault/core/apex-completion-standard.md"))

V2_MARKER = "## Skill Completion Axis v2 (sealed 2026-05-26)"
V2_AXIS = """

## Skill Completion Axis v2 (sealed 2026-05-26) -- S+++ regression-prevention cycle

The v1 axis (sealed 2026-05-25) sealed 7 clauses derived from the LT+CEPS
bootstrap pair. The post-merge S+++ cycle on 2026-05-26 surfaced 3 real
gaps that the v1 clauses did NOT catch:

1. **NIT 1** -- the schema declared a max_chars contract that no code
   enforced. The output happened to be within bounds in practice; the
   contract was load-bearing for nothing until a long-subsystem seed
   would have silently exceeded it.
2. **NIT 3** -- `from_verify_fail` recorded duplicate events on re-run
   of the same verify_spp stdout. The schema declared `id:
   stable_across_reruns: true` but the code did not honour it.
3. **PR-passage prose** -- multiple commits cited "tests pass" without
   the test output being part of the diff. The green moment was
   unreproducible after the fact.

These gaps motivate three new clauses in the Skill Completion Standard:

### C8 -- Evidence-archive at commit-time

The empirical pass-gate output (test stdout, fixture JSON, verify_*
receipts) MUST be committed alongside the code that satisfies it.
"Trust me, it passed" is not evidence. Verbal claims of passage in
commit messages do NOT satisfy C8.

### C9 -- Schema-test reciprocity

Every invariant declared in a `schema.json` (max_chars, enum values,
format, derived_from) MUST have a corresponding test that enforces it.
A schema without a test is a comment, not a contract.

### C10 -- Idempotency-by-default for persistent-state triggers

Any skill trigger that writes to a persistent store (events.jsonl,
FTS5 db, markdown append, JSON fixture) MUST be idempotent under re-
invocation with identical input, unless the skill's plan explicitly
documents a rationale for non-idempotency.

### Enforcement (extends v1)

The Owner-facing PR description must include all TEN rows of the SCS
table. Missing rows or `[ ]` checkboxes on C8/C9/C10 block the merge
in addition to C1-C7.

### Cross-references

- `knowledge_vault/core/skill-completion-standard.md` -- full v2 spec.
- `tools/test_ceps_edge_cases.py` -- the V-NIT1 / V-NIT3 / V-EDGE-*
  tests that empirically grounded C9 + C10.
- `tools/normalize_paths.py`, `tools/verify_global_mirrors.py`,
  `tools/verify_rtk_fusion.py` -- the M7/M8/M9 host-portability fixes
  that empirically grounded C8 (each fix proved by re-running the
  failing probe and capturing the post-fix output).

### DONE-gate

`python tools/test_ceps_edge_cases.py` (6/6) +
`python tools/verify_spp.py` (post-commit: 7/7 OK or documented Owner-
authed FAIL with rationale in `vault/standards/`) +
SCS v2 visible at `knowledge_vault/core/skill-completion-standard.md`
in both loose and PP with byte-identical sha256 -- all three satisfied
= axis v2 sealed.
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


def append_axis(target: Path) -> bool:
    if not target.is_file():
        print(f"missing: {target}", file=sys.stderr)
        return False
    body = target.read_text(encoding="utf-8")
    if V2_MARKER in body:
        print(f"v2 axis already present in {target} (idempotent skip)")
        return True
    if not body.endswith("\n"):
        body += "\n"
    _atomic_write(target, body + V2_AXIS)
    print(f"v2 axis appended to {target} (bytes={target.stat().st_size})")
    return True


def main() -> int:
    ok = True
    ok &= append_axis(PP)
    ok &= append_axis(LOOSE)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
