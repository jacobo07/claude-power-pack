#!/usr/bin/env python3
"""M12 -- CEPS closed-loop empirical pass-gate.

Plan P7 (CEPS): inject 10 errors (7 real + 3 synthetic), present prompts
matching each error's category, count how many trigger a relevant
`[ceps-pattern]` injection via propagate(). Pass-gate: >= 7/10 (70%).

Test isolates from the production patterns.db / events.jsonl /
session_lessons.md by monkeypatching the module-level paths to a
throwaway tmpdir. Production data is never touched.
"""
from __future__ import annotations
import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ceps  # noqa: E402  -- module under test


# 7 real patterns (paraphrased from vault/knowledge_base/session_lessons.md
# memory entries) + 3 synthetic patterns.
ERRORS = [
    # 1) real -- PowerShell git PATH gap
    {
        "category": "env",
        "subsystem": "powershell-git-path",
        "root_cause": "git not on PowerShell NonInteractive PATH on this "
                      "Windows host; bare git status fails with command-"
                      "not-found and falls back to Bash MSYS2 bridge",
        "prompt": "Running git status from PowerShell errors with command "
                  "not recognized on Windows; should I retry via Bash?",
    },
    # 2) real -- Parallel Write batch limit
    {
        "category": "tooling",
        "subsystem": "parallel-write-batch",
        "root_cause": "more than 2 parallel Write tool calls per response "
                      "trigger atomic batch failure with internal error "
                      "missing tool result",
        "prompt": "Plan: 4 parallel Write calls to scaffold templates in "
                  "one turn -- safe?",
    },
    # 3) real -- cat >> apex corruption
    {
        "category": "drift",
        "subsystem": "shell-heredoc-append",
        "root_cause": "cat heredoc append to a large markdown file under "
                      "post-write hook activity can lose a section and "
                      "place the new content at the wrong offset",
        "prompt": "Going to cat heredoc append a new axis section to "
                  "the apex-completion-standard markdown",
    },
    # 4) real -- hook fanout cost
    {
        "category": "tooling",
        "subsystem": "hook-fanout",
        "root_cause": "PreToolUse fires 7 to 15 hooks per Write or Bash; "
                      "spawn overhead and pipe pressure cause transversal "
                      "internal-error hangs across all repos",
        "prompt": "Adding a new PreToolUse hook for telemetry across all "
                  "Bash and Write events",
    },
    # 5) real -- parallel Explore cascade
    {
        "category": "tooling",
        "subsystem": "parallel-explore",
        "root_cause": "two or more file-read-heavy Explore subagents in "
                      "parallel on the same repo return missing tool "
                      "result on agents two and beyond",
        "prompt": "Want to dispatch 3 Explore agents in parallel to map "
                  "the repo by topic",
    },
    # 6) real -- Windows os.open text-mode compounding
    {
        "category": "tooling",
        "subsystem": "windows-os-open",
        "root_cause": "os.open without O_BINARY on Windows translates "
                      "newline to carriage-return newline per write and "
                      "re-reads compound into double carriage-return",
        "prompt": "Opening a log file with os.open on Windows in text "
                  "mode for incremental writes",
    },
    # 7) real -- bypassPermissions defeats deny
    {
        "category": "security",
        "subsystem": "bypass-permissions",
        "root_cause": "defaultMode bypassPermissions silently skips the "
                      "permissions deny array; hooks are the only "
                      "reliable mutation guard under bypass mode",
        "prompt": "Setting defaultMode bypassPermissions to skip the "
                  "deny rules and speed up the session",
    },
    # 8) synthetic -- JIT loader cache invalidation
    {
        "category": "drift",
        "subsystem": "jit-loader-cache",
        "root_cause": "JIT skill loader caches the discovery card per "
                      "session; cache invalidation race when the skill "
                      "body is edited mid-session means stale card text",
        "prompt": "Editing a skill mid-session -- will the JIT loader "
                  "discovery card refresh?",
    },
    # 9) synthetic -- verify_spp false positive on stub paths
    {
        "category": "tooling",
        "subsystem": "verify-spp-stub",
        "root_cause": "verify_spp.py flags ceps_generated test stub paths "
                      "as missing references when scanning the mirror "
                      "manifest even though they are skip-marked",
        "prompt": "verify_spp keeps flagging the ceps_generated stub "
                  "files as untracked mirror entries",
    },
    # 10) synthetic -- ATG flaky in CI
    {
        "category": "regression",
        "subsystem": "auto-testing-gate-ci",
        "root_cause": "Auto Testing Gate is flaky in CI due to timeout "
                      "on the rtk-fusion row when the runner has no "
                      "warm cache",
        "prompt": "Auto Testing Gate intermittently fails on the "
                  "rtk-fusion row in CI when the runner has a cold cache",
    },
]


def _isolated_paths(tmp: Path) -> dict:
    return {
        "EVENTS_PATH": tmp / "events.jsonl",
        "DB_PATH": tmp / "patterns.db",
        "LESSONS_PATH": tmp / "session_lessons.md",
        "UKDL_PATH": tmp / "ukdl.md",
        "DRAFTS_DIR": tmp / "drafts",
    }


def run_closed_loop() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="ceps-closed-loop-"))
    paths = _isolated_paths(tmp)
    # Monkeypatch -- the module reads these as module-level globals.
    for k, v in paths.items():
        setattr(ceps, k, v)

    # Seed: record all 10 errors.
    recorded: list[str] = []
    for e in ERRORS:
        ev = ceps.record_error(
            category=e["category"],
            subsystem=e["subsystem"],
            root_cause=e["root_cause"],
            confidence="high",
        )
        assert ev is not None, f"record_error failed for {e['subsystem']}"
        recorded.append(ev["pattern_signature"])

    # Closed loop: for each error, query propagate(prompt) and check
    # the recorded signature is in the returned top-k.
    hits = 0
    miss_detail = []
    for e, sig in zip(ERRORS, recorded):
        lines = ceps.propagate(e["prompt"], top_k=3)
        joined = "\n".join(lines)
        if any(sig[:8] in line for line in lines):
            hits += 1
            print(f"PASS  V-CEPS  {e['subsystem']:30s} "
                  f"sig={sig[:8]} top-{len(lines)} hit")
        else:
            print(f"FAIL  V-CEPS  {e['subsystem']:30s} "
                  f"sig={sig[:8]} not in top-{len(lines)}")
            miss_detail.append({
                "subsystem": e["subsystem"],
                "prompt": e["prompt"],
                "returned": lines,
            })

    print()
    print(f"CEPS_PASS={hits}/{len(ERRORS)}  threshold=>=7/10")
    if miss_detail:
        print("\nMisses (first detail):")
        print(json.dumps(miss_detail[0], indent=2, ensure_ascii=False))
    return 0 if hits >= 7 else 1


if __name__ == "__main__":
    raise SystemExit(run_closed_loop())
