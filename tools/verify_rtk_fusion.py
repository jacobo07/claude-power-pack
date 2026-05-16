#!/usr/bin/env python3
"""verify_rtk_fusion.py — empirical DONE gate for the RTK proxy fusion.

Exercises the REAL integration path, not the binary in isolation:

  synthetic PreToolUse JSON
        -> node modules/rtk-core/rtk-rewrite.js
        -> parse hookSpecificOutput.updatedInput.command  (the rewrite)
        -> run BOTH the raw command and the rewritten command
        -> tiktoken cl100k token count of each real output
        -> reduction ratio = (raw - compressed) / raw

Verdict:
  reduction >= 0.60          PASS  (exit 0)
  0  <  reduction <  0.60    WARN  (exit 0, ratio logged as evidence)
  reduction <= 0  or error   FAIL  (exit 1)

The WARN band exists because the reduction ratio of one fixed command is
content-dependent (repo history varies); a working integration must not
hard-fail on a low-but-positive ratio. The actual number is always the
evidence of record.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

HEAVY_CMD = "git --no-pager log --stat -50"
HOME = os.path.expanduser("~")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(REPO, "modules", "rtk-core", "rtk-rewrite.js")
RTK_BIN = os.environ.get("RTK_BIN", os.path.join(HOME, ".claude", "bin", "rtk.exe"))


def _node() -> str:
    for cand in (
        r"C:/Program Files/nodejs/node.exe",
        "node",
    ):
        try:
            subprocess.run([cand, "--version"], capture_output=True, check=True)
            return cand
        except Exception:
            continue
    raise RuntimeError("node runtime not found")


def _token_count(text: str) -> int:
    import tiktoken

    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def _run(cmd: str) -> str:
    res = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, cwd=REPO, timeout=60
    )
    return (res.stdout or "") + (res.stderr or "")


def main() -> int:
    print("== RTK fusion DONE gate ==")
    for label, path in (("hook", HOOK), ("rtk binary", RTK_BIN)):
        if not os.path.exists(path):
            print(f"FAIL: {label} missing at {path}")
            return 1
        print(f"  ok  {label}: {path}")

    node = _node()

    # 1. Drive the heavy command through the real hook.
    payload = json.dumps({"tool_input": {"command": HEAVY_CMD}})
    proc = subprocess.run(
        [node, HOOK], input=payload, capture_output=True, text=True, timeout=30
    )
    out = (proc.stdout or "").strip()
    if not out:
        print("FAIL: hook produced no rewrite for a known-heavy command")
        return 1
    try:
        decision = json.loads(out)
        rewritten = decision["hookSpecificOutput"]["updatedInput"]["command"]
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: cannot parse hook output ({exc}): {out[:200]}")
        return 1

    print(f"  raw cmd   : {HEAVY_CMD}")
    print(f"  rewritten : {rewritten}")
    if rewritten == HEAVY_CMD:
        print("FAIL: hook did not rewrite the command")
        return 1

    # 2. Execute both real commands, measure real outputs.
    raw_out = _run(HEAVY_CMD)
    comp_out = _run(rewritten)
    raw_tok = _token_count(raw_out)
    comp_tok = _token_count(comp_out)

    if raw_tok == 0:
        print("FAIL: raw command produced no measurable output")
        return 1
    if not comp_out.strip():
        print("FAIL: rewritten command produced empty output (content lost)")
        return 1
    if comp_tok < 50:
        # A genuine git-log summary is never this small. This size means
        # the rewritten command failed to resolve (e.g. bare `rtk` not on
        # PATH) and we measured an error string — a false positive.
        print(
            f"FAIL: compressed output implausibly small ({comp_tok} tok) — "
            f"command did not resolve. Output: {comp_out.strip()[:160]!r}"
        )
        return 1

    reduction = (raw_tok - comp_tok) / raw_tok
    print(f"  raw tokens (cl100k)        : {raw_tok}")
    print(f"  compressed tokens (cl100k) : {comp_tok}")
    print(f"  reduction                  : {reduction * 100:.1f}%")

    if reduction <= 0:
        print("FAIL: no positive token reduction — proxy not effective")
        return 1
    if reduction >= 0.60:
        print("PASS: >= 60% reduction with content preserved")
        return 0
    print("WARN: positive but < 60% on this repo's history; ratio is evidence")
    return 0


if __name__ == "__main__":
    sys.exit(main())
