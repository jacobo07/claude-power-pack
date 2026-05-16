#!/usr/bin/env python3
"""verify_global_mirrors.py — BL-0064 enforcement.

SHA-256 compares the PP version-controlled mirrors against the global
~/.claude/{commands,agents}/ canonical files. Exit 5 on any drift so a
pre-commit hook can block merges that diverge from the global standard.
"""
from __future__ import annotations
import hashlib
import os
import sys

PAIRS = [
    (r"C:\Users\User\.claude\commands\ultra.md",
     r"C:\Users\User\.claude\skills\claude-power-pack\commands\ultra.md"),
    (r"C:\Users\User\.claude\agents\oneshot-architect-auditor.md",
     r"C:\Users\User\.claude\skills\claude-power-pack\agents"
     r"\oneshot-architect-auditor.md"),
    # Sovereign Baseline (2026-05-15): cpp-resume-sovereign global mirror.
    # PP filename is resume-sovereign.md; global filename is cpp-prefixed
    # for namespacing. Content must remain byte-identical.
    (r"C:\Users\User\.claude\commands\cpp-resume-sovereign.md",
     r"C:\Users\User\.claude\skills\claude-power-pack\commands"
     r"\resume-sovereign.md"),
    # Apex Completion Standard (BL-0069, 2026-05-16): JIT Aggressive
    # Activation law. Byte-identical; pinned `-text` in .gitattributes so
    # core.autocrlf cannot break sha parity.
    (r"C:\Users\User\.claude\knowledge_vault\core\apex-completion-standard.md",
     r"C:\Users\User\.claude\skills\claude-power-pack\knowledge_vault"
     r"\core\apex-completion-standard.md"),
]


def _sha(p):
    if not os.path.isfile(p):
        return None
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    fails = []
    for g, p in PAIRS:
        gh, ph = _sha(g), _sha(p)
        if gh is None or ph is None:
            fails.append(f"MISSING: g={gh is not None} p={ph is not None} {p}")
            continue
        ok = gh == ph
        tag = "OK" if ok else "DRIFT"
        print(f"  [{tag}] {os.path.basename(g)}: "
              f"global={gh[:12]} pp={ph[:12]}")
        if not ok:
            fails.append(p)
    if fails:
        print("VERIFY_GLOBAL_MIRRORS FAIL:", " | ".join(fails))
        return 5
    print("VERIFY_GLOBAL_MIRRORS OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
