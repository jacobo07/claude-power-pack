#!/usr/bin/env python3
"""quality_audit.py — Jobs & Woz enforced quality gate.

The runnable heart of the two SUPREME guardians. Scans a file (or the 22
KobiiDistillerOS distilled sections) for slop, routes the verdict to the
JOBS lens (UI/product) or the WOZ lens (engineering), and on a VETO appends
a permanent prohibition to the global veto ledger.

Exit codes
----------
0  clean   — ship it
5  VETO    — slop detected (Jobs/Woz blocked it)
2  usage   — bad invocation (no target / unreadable)

Usage
-----
  quality_audit.py <path>
  quality_audit.py <scan-file> <logical-path>   # read scan-file, classify+skip as logical-path
  quality_audit.py --distilled [<dataset-dir>]

This module has zero placeholders in its own logic. The token strings below
are detector DATA, not scaffolding — and this file is on the skip-set so the
gate never vetoes itself (audit gap #3).
"""
from __future__ import annotations

import os
import re
import sys
import time
import glob
from datetime import date

LEDGER = r"C:\Users\User\.claude\knowledge_vault\global_vetoes.md"
DEFAULT_DISTILLED = (
    r"C:\Users\User\.claude\skills\claude-power-pack"
    r"\vault\distilled\Dataset_KobiiDistillerOS_1.txt"
)

# Files that legitimately CONTAIN slop tokens as data/documentation. Scanning
# them would make the gate veto itself (audit gaps #2, #3).
SKIP_BASENAMES = {
    "quality_audit.py", "jobs-woz-gatekeeper.js", "scaffold-auditor.js",
    "zero-fiction-gate.js", "secret-scanner.js", "session_lessons.md",
    "JOBS_MANIFESTO.md", "global_vetoes.md", "steve-jobs.md", "woz.md",
    "INDEX.md",
}
# Path fragments (normalised to '/') whose files are governance/meta, not
# shippable project surface — out of the gate's jurisdiction.
SKIP_DIR_FRAGMENTS = (
    "/.claude/agents/", "/knowledge_vault/", "/.claude/hooks/",
    "/node_modules/", "/.git/", "/__pycache__/",
)

UI_EXTS = {".tsx", ".jsx", ".vue", ".svelte", ".css", ".scss", ".sass",
           ".html", ".htm"}
CODE_EXTS = {".py", ".js", ".ts", ".mjs", ".cjs", ".go", ".rs", ".java",
             ".rb", ".sh", ".ps1"}

# token regex -> (lens, permanent prohibition for the ledger)
SLOP_RULES: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"\bcoming\s+soon\b", re.I), "JOBS",
     "Never ship user-facing surface containing 'Coming Soon' — build it or cut it."),
    (re.compile(r"\bunder\s+construction\b", re.I), "JOBS",
     "Never ship an 'Under Construction' screen — an empty room is not a product."),
    (re.compile(r"\blorem\s+ipsum\b", re.I), "JOBS",
     "Never ship Lorem Ipsum — placeholder copy is a broken promise to the user."),
    (re.compile(r"on(?:Click|Submit|Change)\s*=\s*\{?\s*\(\s*\)\s*=>\s*\{\s*\}\s*\}?"),
     "JOBS", "Never ship a control wired to an empty handler — a dead button is a lie."),
    (re.compile(r'href\s*=\s*["\']#["\']'), "JOBS",
     "Never ship href=\"#\" as a real navigation target — it goes nowhere."),
    (re.compile(r"\bTODO\b"), "WOZ",
     "Never ship a TODO in delivered code — finish it this turn or do not scaffold it."),
    (re.compile(r"\bFIXME\b"), "WOZ",
     "Never ship a FIXME — a known defect left in place is an unshipped defect."),
    (re.compile(r"\b(?:HACK|XXX)\b"), "WOZ",
     "Never ship a HACK/XXX marker — fragile by author's own admission."),
    (re.compile(r"\bPLACEHOLDER\b", re.I), "WOZ",
     "Never ship a PLACEHOLDER — zero placeholders in delivered code."),
    (re.compile(r"raise\s+NotImplementedError"), "WOZ",
     "Never ship raise NotImplementedError in a delivered path — wire it end-to-end."),
    (re.compile(r"pass\s*#\s*TODO", re.I), "WOZ",
     "Never ship 'pass # TODO' — an empty body is not an implementation."),
    (re.compile(r"except\s*:\s*\n\s*pass\b"), "WOZ",
     "Never ship a bare 'except: pass' — silent failure is the worst failure."),
    (re.compile(r"catch\s*\([^)]*\)\s*\{\s*\}"), "WOZ",
     "Never ship an empty catch block — a swallowed error is an unhandled error."),
]


def _norm(path: str) -> str:
    return path.replace("\\", "/")


def _skip(path: str) -> bool:
    # `path` here is the CLASSIFY path (logical target), never the temp copy:
    # recursion-safety is provided by the hook (Node fs, not Claude tool) +
    # the `logical` arg, so a tmpdir skip is unnecessary and would blind the
    # gate to every hook-staged scan. Skip only governance/meta surface.
    n = _norm(path)
    if os.path.basename(n) in SKIP_BASENAMES:
        return True
    return any(frag in n for frag in SKIP_DIR_FRAGMENTS)


def _lens_for(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in UI_EXTS:
        return "JOBS"
    if ext in CODE_EXTS:
        return "WOZ"
    return "WOZ"


def _read(path: str) -> str:
    # utf-8-sig: strip a BOM left by any PowerShell-written file (MEMORY:
    # feedback_python_utf8_bom). Never raise on a binary blob.
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
            return fh.read()
    except (OSError, ValueError):
        return ""


def _append_ledger(actor: str, prohibition: str) -> None:
    """Atomic, BOM-free, mutex-guarded append (audit gap #7)."""
    line = f"## {date.today().isoformat()} — {actor}-VETO: {prohibition}\n"
    lock = LEDGER + ".lock"
    deadline = time.time() + 10
    while True:
        try:
            os.mkdir(lock)
            break
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(lock) > 30:
                    os.rmdir(lock)  # stale lock recovery
                    continue
            except OSError:
                pass
            if time.time() > deadline:
                break  # never block the gate forever; degrade to racy append
            time.sleep(0.05)
    try:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_BINARY", 0)
        fd = os.open(LEDGER, flags, 0o644)
        try:
            os.write(fd, line.encode("utf-8"))
        finally:
            os.close(fd)
    finally:
        try:
            os.rmdir(lock)
        except OSError:
            pass


def scan(path: str, logical: str | None = None) -> list[tuple[int, str, str, str]]:
    """Return [(lineno, lens, token, prohibition)] for every slop hit.

    `path` is read; `logical` (when given) drives skip-set + lens routing so
    the PreToolUse hook can scan a temp copy of new content while classifying
    by the real target file (audit gaps #2/#3).
    """
    classify = logical or path
    if _skip(classify):
        return []
    text = _read(path)
    if not text:
        return []
    file_lens = _lens_for(classify)
    hits: list[tuple[int, str, str, str]] = []
    for rule, lens, prohibition in SLOP_RULES:
        # A WOZ-only code token in a UI file (or vice-versa) still counts —
        # but the verdict is attributed to the file's owning lens.
        for m in rule.finditer(text):
            lineno = text.count("\n", 0, m.start()) + 1
            hits.append((lineno, file_lens, m.group(0).strip(), prohibition))
    return hits


def _verdict(target: str, hits: list[tuple[int, str, str, str]]) -> int:
    if not hits:
        print(f"VERDICT: SHIP\n  {target}\n  Clean. Nothing to cut. Ship it.")
        return 0
    actor = hits[0][1]
    name = "STEVE JOBS" if actor == "JOBS" else "STEVE WOZNIAK"
    print(f"VERDICT: VETO  [{name}]")
    print(f"\nWHAT I SAW\n  {target} — {len(hits)} slop defect(s). "
          f"This is not shippable.")
    print("\nWHY")
    seen: set[str] = set()
    for lineno, _lens, token, prohibition in hits:
        print(f"  L{lineno}: '{token}' — mediocrity reaches the user/vault here.")
        seen.add(prohibition)
    print("\nCUT LIST")
    for lineno, _lens, token, _p in hits:
        print(f"  - {target}:{lineno}  delete/replace '{token}'")
    worst = hits[0][3]
    print(f"\nTHE ONE THING\n  {worst}")
    print(f"\nLEDGER\n  {actor}-VETO recorded permanently.")
    for prohibition in seen:
        _append_ledger(actor, prohibition)
    return 5


def _run_distilled(dataset_dir: str) -> int:
    sections = sorted(glob.glob(os.path.join(dataset_dir, "Tier_*", "Seccion_*.md")))
    if len(sections) != 22:
        print(f"VERDICT: VETO  [STEVE WOZNIAK]\n  {dataset_dir} — expected 22 "
              f"distilled sections, found {len(sections)}. Incomplete output.")
        _append_ledger("WOZ",
                        "Never accept a KobiiDistillerOS run with fewer than 22 "
                        "materialized sections — incomplete is unshipped.")
        return 5
    all_hits: list[tuple[int, str, str, str]] = []
    for sec in sections:
        all_hits += [(ln, ls, tk, pr) for (ln, ls, tk, pr) in scan(sec)]
    return _verdict(f"KobiiDistillerOS [{len(sections)} sections]", all_hits)


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: quality_audit.py <path> | --distilled [<dir>]",
              file=sys.stderr)
        return 2
    if argv[0] == "--distilled":
        dataset = argv[1] if len(argv) > 1 else DEFAULT_DISTILLED
        if not os.path.isdir(dataset):
            print(f"usage: distilled dir not found: {dataset}", file=sys.stderr)
            return 2
        return _run_distilled(dataset)
    target = argv[0]
    if not os.path.isfile(target):
        print(f"usage: not a readable file: {target}", file=sys.stderr)
        return 2
    logical = argv[1] if len(argv) > 1 and not argv[1].startswith("--") else None
    return _verdict(logical or target, scan(target, logical))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
