#!/usr/bin/env python3
"""M5 -- Seed the 9 CEPS categories with real historical patterns.

Each seed is a real incident the Owner / agent lived through in this
repo, NOT a synthetic example. Source memories are cited in
`evidence_path`. Idempotent: signatures already present in
events.jsonl are skipped (relies on M3 dedup primitive).

Run once after every CEPS deployment to materialize the schema's 9-
category surface so downstream `propagate()` queries have meaningful
top-3 hits even before the system has organically accrued events.

Usage: python tools/ceps_seed_categories.py
"""
from __future__ import annotations
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ceps  # noqa: E402

SEEDS = [
    # regression
    {
        "category": "regression",
        "subsystem": "windows-text-mode-io",
        "root_cause": (
            "Windows os.open without os.O_BINARY translates the LF "
            "byte into CRLF on write; subsequent reads compound the "
            "regression (extra CR before each LF) until the file is "
            "corrupted. Caught by BL-0014 self-test 2026-05-02."
        ),
        "affected_modules": ["modules/zero-crash/hooks", "tools/atomic_write"],
        "evidence_path": "memory/feedback_windows_text_mode_compounding.md",
    },
    # security
    {
        "category": "security",
        "subsystem": "claude-settings-permissions",
        "root_cause": (
            "defaultMode bypassPermissions silently skips "
            "permissions.deny rules. Any deny entry under that mode is "
            "a false sense of security; only hooks are reliable "
            "mutation guards. Caught MC-OVO-114 on 2026-04-26."
        ),
        "affected_modules": ["~/.claude/settings.json", "hooks/*"],
        "evidence_path": "memory/feedback_bypasspermissions_defeats_deny.md",
    },
    # drift
    {
        "category": "drift",
        "subsystem": "mirror-parity",
        "root_cause": (
            "Loose ~/.claude/{commands,agents,knowledge_vault}/ mirror "
            "diverges from PP-tracked counterpart when an edit is made "
            "to loose without back-sync to PP. CRLF vs LF + bare git "
            "working-tree reads make false-drift indistinguishable "
            "from real drift unless the verifier reads committed blobs "
            "via deterministic ref and LF-normalizes both sides."
        ),
        "affected_modules": ["tools/verify_global_mirrors.py"],
        "evidence_path": "knowledge_vault/core/apex-completion-standard.md#Zero-Drift",
    },
    # scaffold
    {
        "category": "scaffold",
        "subsystem": "reality-contract",
        "root_cause": (
            "Scaffold illusion: emitting button shells, completion-"
            "pending anchors, unimplemented-stub exception raisers, or "
            "silent exception swallowers creates the appearance of "
            "completion without the wiring. Compiles != works. Grep "
            "callers + run an integration smoke before marking done."
        ),
        "affected_modules": ["hooks/scaffold-auditor.js"],
        "evidence_path": "CLAUDE.md#Reality-Contract",
    },
    # incomplete-shell
    {
        "category": "incomplete-shell",
        "subsystem": "agent-emission",
        "root_cause": (
            "Agent ships a function / file / endpoint whose body "
            "describes the intended behavior in comments but executes "
            "no real work, or returns a fixture / hardcoded value. "
            "Static verification (type-check, linter) does NOT prove "
            "runtime works. The shell looks complete; the call site "
            "discovers the gap on first real invocation."
        ),
        "affected_modules": ["modules/*"],
        "evidence_path": "knowledge_vault/core/mistakes-global.md",
    },
    # integration
    {
        "category": "integration",
        "subsystem": "parallel-tool-cascade",
        "root_cause": (
            "Parallel batches that mix heavy-IO operations (Bash with "
            "hook-decorated output, multiple Reads on same Explore "
            "subagent) drop neighbor results as internal-error under "
            "harness pipe pressure. Hook fanout (7-15 hooks per Write/"
            "Bash, 3 per Read) is the systemic cost behind transversal "
            "internal-error hangs."
        ),
        "affected_modules": ["hooks/*", "tools/jit_skill_loader.py"],
        "evidence_path": "vault/lessons/parallel-batch-large-output-cascade.md",
    },
    # spec-violation
    {
        "category": "spec-violation",
        "subsystem": "ultra-q-and-a-skip",
        "root_cause": (
            "ULTRA / ONESHOT protocol mandates 7 phases with Q&A as "
            "phase 2 (6 questions, MANDATORY stop). Skipping Q&A and "
            "jumping to plan presentation is REJECTED because plan-"
            "quality is bounded by prompt-quality. Six honest answers "
            "beat one vague paragraph (BL-0064)."
        ),
        "affected_modules": ["commands/ultra.md", "agents/oneshot-architect-auditor.md"],
        "evidence_path": "CLAUDE.md#ULTRA-ONESHOT-Protocol",
    },
    # tooling
    {
        "category": "tooling",
        "subsystem": "powershell-git-path-gap",
        "root_cause": (
            "git executable is NOT on PowerShell -NonInteractive PATH "
            "on this Windows host. Bare `git status` errors and a "
            "silent fallback to Bash re-triggers the MSYS2 hang the "
            "Windows Bash Bridge Reliability rule was sealed to "
            "prevent. Use absolute path: & 'C:\\Program Files\\Git\\"
            "cmd\\git.exe'."
        ),
        "affected_modules": ["hooks/*.ps1", "tools/*.ps1"],
        "evidence_path": "vault/lessons/powershell-git-path-gap.md",
    },
    # env
    {
        "category": "env",
        "subsystem": "host-detection",
        "root_cause": (
            "Failure to probe host before deciding execution path. On "
            "a remote target host the agent IS that host and must exec "
            "natively; wrapping in an outbound ssh-into-self from "
            "inside the remote is a self-detect failure. On the local "
            "workstation the agent uses SSH bridges. The per-project "
            "SSH key MUST be declared, never assumed."
        ),
        "affected_modules": ["CLAUDE.md", "tools/probe_host.py"],
        "evidence_path": "memory/feedback_local_vs_vps.md",
    },
]


def main() -> int:
    existing = ceps._existing_sigs()
    seeded = 0
    skipped = 0
    for seed in SEEDS:
        sig = ceps.pattern_signature(seed["root_cause"])
        if sig in existing:
            skipped += 1
            print(f"skip  {seed['category']:<18} sig={sig[:8]} (already seeded)")
            continue
        ev = ceps.record_error(
            category=seed["category"],
            subsystem=seed["subsystem"],
            root_cause=seed["root_cause"],
            affected_modules=seed["affected_modules"],
            evidence_path=seed["evidence_path"],
            confidence="high",
        )
        if ev is None:
            print(f"FAIL  {seed['category']:<18} record_error returned None")
            continue
        seeded += 1
        print(f"seed  {seed['category']:<18} sig={ev['pattern_signature'][:8]}")
    # Verify 9 distinct categories now in events.jsonl
    cats = set()
    if ceps.EVENTS_PATH.is_file():
        import json
        for line in ceps.EVENTS_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                cats.add(json.loads(line).get("category", ""))
            except json.JSONDecodeError:
                continue
    expected = {s["category"] for s in SEEDS}
    missing = expected - cats
    print(f"\nseeded={seeded}  skipped={skipped}  "
          f"distinct_cats_in_jsonl={len(cats & expected)}/9  "
          f"missing={sorted(missing) if missing else 'none'}")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
