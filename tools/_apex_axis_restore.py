#!/usr/bin/env python3
"""One-shot recovery: restore loose apex-completion-standard.md from PP
canonical AND atomically append the Prompt Quality Axis to both files.

Triggered manually after the `cat >>` append on loose lost the Testing
Gate Axis section (root-cause inconclusive; could be a shell heredoc /
post-write-hook interaction). Atomic write avoids re-triggering whatever
broke the file the first time.

Run from PP root: `python tools/_apex_axis_restore.py`. Self-deletes
nothing; safe to re-run (idempotent — checks for the axis presence
before appending).
"""
from __future__ import annotations
import os
import sys
import tempfile
from pathlib import Path

PP = Path("knowledge_vault/core/apex-completion-standard.md")
LOOSE = Path(os.path.expanduser(
    "~/.claude/knowledge_vault/core/apex-completion-standard.md"))

AXIS_HEADER = "## Prompt Quality Axis (sealed 2026-05-23)"
AXIS = """

## Prompt Quality Axis (sealed 2026-05-23) -- PP Signal Layer

Companion to the Architecture Decision Axis and Code Review Axis. Where
those two axes intercept on concrete tool/decision signals, the Prompt
Quality Axis intercepts on the *absence* of signal -- short prompts
whose referent is unresolved get a single-line lint advisory in
`additionalContext`, never a rewrite.

### The law

`tools/jit_skill_loader.py::_detect_vague_prompt(prompt, spec)` returns
`VAGUE_LINT_MESSAGE` (one line) when AND of three conditions holds:

1. `len(prompt.split()) < 30` (Owner spec threshold)
2. `_VAGUE_REFERENT_RX` matches (definite-article+opaque-noun in EN/ES,
   enclitic-lo Spanish imperatives, "this/that/it/esto/eso", "lo de")
3. None of these mitigators fire:
   - `_FILE_HINT_RX` (filename with recognized extension)
   - `_LINE_HINT_RX` ("line 42", "linea 42", ":42")
   - `_FUNCTION_HINT_RX` ("function foo", "foo(x, y)")
   - `>1` `_ARCH_DESIGN_VERBS` hit (already covered by `_arch_check_inject`)
   - Active `.specify` spec (already covered by PASO -1 spec injection)
   - `CLAUDEPP_VAGUE_LINT_DISABLE=1` env opt-out
   - `CLAUDEPP_JIT_RUNNING=1` recursion guard

When the signal fires it is composed alongside `arch_block` in the
`extras` slot of `run()` -- inserted into all three composition paths
(no-mods+no-spec early return, no-injected+no-spec early return, and
the main `ctx` assembly). Telemetry: the JIT log line carries
`vague={yes|no}` next to `arch={yes|no}` for empirical recalibration.

### What this rule rules OUT

- **Auto-rewriter**: explicitly vetoed (Owner directive 2026-05-23).
  Silent prompt mutation breaks Owner intent reproducibility. The
  agent receives the signal and decides whether to pause for
  clarification.
- **Blocking the prompt**: the signal is advisory -- never returns
  anything but `continue: true`. Fail-open semantics (Ley 24) apply
  to every internal failure: any exception in `_detect_vague_prompt`
  is logged to `~/.claude/logs/jit-skill-loader.log` and returns
  `None`, never disrupting the user's prompt.
- **LLM-based vagueness scoring**: deterministic regex only. Allows
  the `<100 ms` budget to hold (measured p95 0.2 ms) and keeps
  Reality Contract intact (no model-call confounders).

### DONE-gate

`tools/test_vague_lint.py` -- 6 gates:
- V-VAGUE-1: "fix the auth bug" -> signal
- V-VAGUE-2: "hazlo mas rapido" -> signal (Spanish enclitic-lo)
- V-CLEAN-1: "fix the null pointer in PlayerManager.java line 42" -> no signal
- V-CLEAN-2: prompt with >= 30 tokens -> no signal (any content)
- V-TIMING: 10 runs < 100 ms each (p95 0.2 ms measured)
- DISABLE-ENV: `CLAUDEPP_VAGUE_LINT_DISABLE=1` short-circuits

Exit 0 = sealed. Re-run on any regex / mitigator edit.

### Telemetry future-work

Count signal-fired prompts vs signal-acted-on prompts (agent paused
to ask Owner) over 2 weeks. If acted-on rate < 20%, the regex or
mitigators need recalibration -- the signal must earn its presence in
`additionalContext`. Until empirical data exists, the signal is on
by default; opt-out is per-prompt via env var.
"""


def _atomic_write(path: Path, text: str) -> None:
    """tempfile + os.replace, same parent dir (cross-FS safe)."""
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".apex.", suffix=".tmp", dir=parent)
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


def main() -> int:
    if not PP.is_file():
        print(f"PP canonical missing: {PP}", file=sys.stderr)
        return 2
    canonical = PP.read_text(encoding="utf-8")
    if AXIS_HEADER in canonical:
        print(f"Axis already present in PP canonical; aborting (idempotent).")
        # Still mirror to loose in case it's stale.
        if LOOSE.read_text(encoding="utf-8") != canonical:
            _atomic_write(LOOSE, canonical)
            print(f"Mirrored PP -> loose (PP already had axis).")
        return 0
    # Append axis to canonical content (single source of truth pre-axis = PP)
    if not canonical.endswith("\n"):
        canonical += "\n"
    new = canonical + AXIS.lstrip("\n") + "\n"
    # Write atomically to both
    _atomic_write(PP, new)
    _atomic_write(LOOSE, new)
    print(f"PP   bytes after = {len(new.encode('utf-8'))}")
    print(f"loose bytes after = {LOOSE.stat().st_size}")
    print(f"axis sealed in both files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
