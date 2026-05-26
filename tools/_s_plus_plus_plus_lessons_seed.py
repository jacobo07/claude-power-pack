#!/usr/bin/env python3
"""M14 -- atomic append of S+++ cycle lessons to session_lessons.md
and ukdl-universal.md. Each lesson follows the canonical schema:
TRAP -> DIAGNOSIS -> FIX -> RECOGNITION SIGNAL.

Idempotent: skips append if the lesson header is already present.
"""
from __future__ import annotations
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP = HERE.parent
LESSONS = PP / "vault" / "knowledge_base" / "session_lessons.md"
UKDL = PP / "vault" / "knowledge_base" / "ukdl-universal.md"

LESSONS_MARKER = "## S+++ cycle 2026-05-26 -- regression-prevention lessons"

LESSONS_BLOCK = """

## S+++ cycle 2026-05-26 -- regression-prevention lessons

### L1: PowerShell -NonInteractive PATH gap inside Python subprocess

- **trap**: `subprocess.check_output(['git', 'ls-files'], ...)` raises
  `FileNotFoundError: [WinError 2]` under PowerShell -NonInteractive
  even when the user's interactive PATH has `git` available.
- **diagnosis**: PowerShell harness PATH is a subset of the interactive
  shell PATH; Git's `cmd` dir is one of the omissions. Python inherits
  it; subprocess inherits Python's; `["git", ...]` resolves to nothing.
- **fix**: `_git_exe()` helper -- `shutil.which("git")` first, then
  fallback list `[r"C:\\Program Files\\Git\\cmd\\git.exe", ...]`.
  Sister fix for `shell=True`: inject Git's cmd dir into the
  subprocess `env=` PATH explicitly (verify_rtk_fusion._run).
- **recognition signal**: `FileNotFoundError [WinError 2]` from any
  `subprocess` call whose argv starts with a bare program name on
  Windows. Reproducer: bare `["mix"]`, `["pnpm"]`, `["node"]`, `["gh"]`
  all have the same exposure.

### L2: cp1252 default stdout breaks on non-ANSI codepoints

- **trap**: `print(f"...{excerpt}")` raises `UnicodeEncodeError:
  'charmap' codec can't encode character '\\u2192'` (right arrow) when
  the excerpt is from a file containing that codepoint.
- **diagnosis**: Python on Windows defaults stdout encoding to the ANSI
  codepage (cp1252 on this host). Anything outside CP1252 -> exception.
- **fix**: At the top of `main()`, call `sys.stdout.reconfigure(
  encoding="utf-8", errors="replace")` and same for stderr. Wrap in
  `try/except` because the method is Python 3.7+.
- **recognition signal**: `'charmap' codec can't encode character` in
  the traceback. Common offenders: arrow / em-dash / smart-quote in
  doc-prose excerpts.

### L3: subprocess `shell=True` inherits parental PATH

- **trap**: `verify_rtk_fusion._run` returned 26 cl100k tokens (reduction
  -169%) for a command that empirically produces 18k tokens.
- **diagnosis**: Inside `_run`, `subprocess.run(cmd, shell=True, ...)`
  invokes cmd.exe which uses the inherited Python-process PATH. If
  Python was started by a PATH-deficient parent (PowerShell
  -NonInteractive), the shell's `git` lookup fails and the captured
  output is the 26-token error message "git is not recognized as an
  internal or external command".
- **fix**: Pass `env=` to `subprocess.run` with `PATH` explicitly
  augmented to include Git's `cmd` dir. Affects every subprocess that
  relies on `shell=True` + bare program names.
- **recognition signal**: a benchmark suddenly producing implausibly
  small token counts vs documented prior runs. Always sanity-check
  the raw output before trusting the reduction ratio.

### L4: Schema declares -> code MUST enforce (SCS C9 motivation)

- **trap**: `vault/ceps/schema.json` declared `prevention_rule.max_chars
  = 300` but `tools/ceps.py::record_error` never measured or capped the
  rendered output. Could silently exceed under long-subsystem inputs.
- **diagnosis**: a schema invariant without an enforcing test is a
  comment, not a contract. Existing tests measured shape (key
  presence, type) but not numeric bounds.
- **fix**: After rendering `rule = RULE_TEMPLATES[category].format(...)`
  add `if len(rule) > 300: rule = rule[:297] + "..."`. Add
  V-NIT1-MAXCHARS test with 400-char subsystem to verify the cap is
  honoured.
- **recognition signal**: any schema with numeric or enum invariants
  whose enforcement path is not greppable in the code or tests.
  Reciprocity is the contract.

### L5: Persistent-state triggers must be idempotent (SCS C10 motivation)

- **trap**: `tools/ceps.py::from_verify_fail` recorded duplicate events
  on re-invocation with identical stdout. Schema declared
  `id.stable_across_reruns: true`; code did not honour it.
- **diagnosis**: a fresh `_existing_sigs()` scan at function entry +
  per-event sig check before `record_error` are the minimum
  idempotency primitive. Without it, every re-run of `verify_spp.py`
  would balloon events.jsonl by N rows.
- **fix**: Add `_existing_sigs()` helper reading events.jsonl ->
  set of sigs. Branch on `if sig in existing: continue`. Add
  V-NIT3-IDEMPOTENT test: 2 invocations on same input -> delta == N
  on run 1, 0 on run 2.
- **recognition signal**: any trigger that writes to persistent state
  (events.jsonl, FTS5 db, markdown append, JSON fixture) whose plan
  does NOT explicitly declare "this is intentionally non-idempotent
  because <X>" is a defect waiting for the second invocation.

### L6: A1/A2 sync direction propagates corruption byte-perfectly

- **trap**: `drift-report` flagged 2 loose-ahead files. Per A1/A2 law,
  the agent ran `Copy-Item loose -> PP` byte-perfectly. Side-effect:
  Pane-4's non-atomic destructive write to the loose copy of
  `apex-completion-standard.md` was imported verbatim into PP --
  stomp-included.
- **diagnosis**: A1/A2 says "loose is canonical, sync direction is
  loose -> PP". It does NOT say "loose is correct". A polluted loose
  is still loose. Sync without hygiene = byte-perfect corruption
  propagation.
- **fix**: Before any loose -> PP sync of a tracked file, sanity-check
  the loose head against `origin/main:<path>` -- if the first 10
  meaningful lines no longer match the committed structure, halt and
  surface to Owner. Recovery here used
  `tools/_apex_pane4_recovery.py`: git show origin/main:<path> +
  atomic-append the legitimate Pane-4 axis content to the tail.
- **recognition signal**: drift-report shows loose-ahead by an
  unexpectedly large byte delta (here: +12KB on a file the agent has
  not edited in the current session).

### L7: code-reviewer catches cross-pane stomps that drift-report misses

- **trap**: `drift-report` PASS (9/9 equal post-sync), but the synced
  content carried a destructive head stomp invisible to a byte-level
  drift check.
- **diagnosis**: byte-equality is necessary but not sufficient. The
  reviewer reads structure (head matches the expected canon? orphan
  fragments at section boundaries? new sections appended via
  atomic-write or via shell `cat >>` cat?). A drift-report is
  syntax-blind; the reviewer is structure-aware.
- **fix**: Run a code-reviewer pass on every push that includes a
  loose -> PP sync of tracked .md files. The reviewer is the line of
  defense against cross-pane stomps.
- **recognition signal**: A loose-ahead delta on a tracked .md that
  the agent has not edited in the current session -- always trigger
  a structural review, never a blind sync.
"""

UKDL_MARKER = "## UKDL S+++ 2026-05-26"

UKDL_BLOCK = """

## UKDL S+++ 2026-05-26

- [tooling/host-portability] L1 -- `["git", ...]` bare in subprocess fails under PowerShell -NonInteractive on Windows. Use `shutil.which` + absolute-path fallback. Affects every Python tool that shells out to git/mix/pnpm/gh/node without resolution.
- [tooling/encoding] L2 -- cp1252 stdout default on Windows Python breaks on U+2192 (and any non-ANSI). `sys.stdout.reconfigure(encoding='utf-8', errors='replace')` at main() entry.
- [tooling/env-propagation] L3 -- `subprocess.run(shell=True)` inherits Python parent PATH. PATH-deficient parents silently degrade benchmarks (26-token error vs 18k real output). Inject Git cmd dir via `env=` to fix.
- [spec-violation/schema] L4 -- schema invariant without enforcing test is a comment. Reciprocity is the contract (SCS C9).
- [regression/idempotency] L5 -- persistent-state triggers must be idempotent. Plan declares "non-idempotent because X" or the V-*-IDEMPOTENT test is mandatory (SCS C10).
- [drift/sync-discipline] L6 -- A1/A2 loose->PP is byte-perfect including byte-perfect corruption. Always structural-check before sync.
- [drift/review] L7 -- drift-report PASS != safe sync. code-reviewer is the structure-aware backstop against cross-pane stomps.
"""


def _atomic_append(path: Path, marker: str, block: str) -> bool:
    if not path.is_file():
        sys.stderr.write(f"missing: {path}\n")
        return False
    body = path.read_text(encoding="utf-8")
    if marker in body:
        print(f"marker already present in {path.name} (idempotent skip)")
        return True
    if not body.endswith("\n"):
        body += "\n"
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp",
                               dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body + block)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    print(f"appended to {path.name} (bytes={path.stat().st_size})")
    return True


def main() -> int:
    ok = True
    ok &= _atomic_append(LESSONS, LESSONS_MARKER, LESSONS_BLOCK)
    ok &= _atomic_append(UKDL, UKDL_MARKER, UKDL_BLOCK)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
