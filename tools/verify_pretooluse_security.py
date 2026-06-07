#!/usr/bin/env python3
"""verify_pretooluse_security.py -- PreToolUse-fold security non-regression gate.

After folding windows-bash-bridge-guard into PreToolUse-Bash-chain and
claude_md_firewall + uqf_pre_edit_gate into PreToolUse-Edit-chain, this gate
proves the chains STILL block what they must -- i.e. the fold did not silently
drop a security gate's block (the split-brain recognizer: only continue:false /
permissionDecision:deny / exit-2 survive mergeOutputs).

It drives the LIVE dispatcher (~/.claude/hooks/hook-dispatcher.js) as a child
process with clean UTF-8 stdin (subprocess text mode -> no BOM, unlike a
PowerShell here-string pipe), then inspects the merged JSON for a deny.

Gates
-----
V-PTU-SEC-SECRET   : Edit-chain DENIES a Write whose content carries a CRITICAL
                     secret pattern (HR-SECRET-001 firewall reachable in-chain
                     even after appending uqf_pre_edit_gate + claude_md_firewall).
V-PTU-SEC-BASHGUARD: Bash-chain DENIES `git status` -- proves the FOLDED
                     windows-bash-bridge-guard still blocks (decision:block +
                     exit 2) via the chain. This is the exact gate this fold
                     moved from a standalone entry into the chain; the test
                     proves the move lost no enforcement. (Windows-only block;
                     on non-Windows the guard exits 0 and this gate is skipped.)
V-PTU-SEC-PASS     : Bash-chain ALLOWS a benign `ls` (no false-positive deny).

NOTE: the PreToolUse Bash-chain deliberately does NOT block `rm -rf /` -- the
dangerous-command / cascade stop (HR-CASCADE-002) is enforced at the Hard-Rule /
agent layer, not as a PreToolUse hook in this repo's wiring. The fold did not
change that (it added a guard, removed none), so it is out of scope here.

The secret literal is CONSTRUCTED at runtime ("sk-ant-" + "A"*50) so the source
file never contains a full real-shape key (HR-SECRET-005).

Usage:  python tools/verify_pretooluse_security.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

HOME = os.path.expanduser("~")
LIVE = os.path.join(HOME, ".claude", "hooks", "hook-dispatcher.js")

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"OK   {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"FAIL {gate}: {diagnostic}")


def _node_exe() -> str:
    p = shutil.which("node")
    if p:
        return p
    cand = r"C:\Program Files\nodejs\node.exe"
    return cand if os.path.isfile(cand) else "node"


def _run_chain(event: str, payload: dict) -> tuple[dict, int, str]:
    """Run the live dispatcher for `event` with `payload` on stdin. Returns
    (parsed_stdout_json, returncode, raw_stdout)."""
    r = subprocess.run(
        [_node_exe(), LIVE, f"--event={event}"],
        input=json.dumps(payload),  # text=True default with str input -> no BOM
        capture_output=True, text=True, timeout=60,
    )
    try:
        out = json.loads(r.stdout.strip() or "{}")
    except ValueError:
        out = {}
    return out, r.returncode, r.stdout


def _is_denied(out: dict) -> bool:
    """A PreToolUse deny lands as hookSpecificOutput.permissionDecision == 'deny'
    OR continue == false (firewall {continue:false}) after mergeOutputs."""
    hso = out.get("hookSpecificOutput") or {}
    if hso.get("permissionDecision") == "deny":
        return True
    if out.get("continue") is False:
        return True
    return False


def gate_secret() -> None:
    fake_key = "sk-ant-" + "A" * 50  # clearly-fake, real-shape (HR-SECRET-005)
    payload = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": os.path.join(HOME, "_ptu_sec_probe.txt"),
            "content": f"const KEY = '{fake_key}';\n",
        },
    }
    out, rc, raw = _run_chain("PreToolUse-Edit-chain", payload)
    if _is_denied(out):
        _ok("V-PTU-SEC-SECRET", "Edit-chain denies a secret-bearing Write")
    else:
        _fail("V-PTU-SEC-SECRET",
              f"secret NOT blocked in-chain: {raw[:200]!r}")


def gate_bashguard() -> None:
    # windows-bash-bridge-guard blocks only on Windows; skip elsewhere.
    if sys.platform != "win32":
        _ok("V-PTU-SEC-BASHGUARD", "skipped (non-Windows: guard is a no-op)")
        return
    payload = {"tool_name": "Bash", "tool_input": {"command": "git status"}}
    out, rc, raw = _run_chain("PreToolUse-Bash-chain", payload)
    if _is_denied(out):
        _ok("V-PTU-SEC-BASHGUARD",
            "Bash-chain denies git-status (folded bash-bridge-guard live)")
    else:
        _fail("V-PTU-SEC-BASHGUARD",
              f"folded bash-bridge-guard did NOT block git: {raw[:200]!r}")

def gate_pass() -> None:
    payload = {"tool_name": "Bash", "tool_input": {"command": "ls"}}
    out, rc, raw = _run_chain("PreToolUse-Bash-chain", payload)
    if not _is_denied(out):
        _ok("V-PTU-SEC-PASS", "Bash-chain allows benign `ls`")
    else:
        _fail("V-PTU-SEC-PASS", f"benign `ls` falsely denied: {raw[:200]!r}")


def main() -> int:
    print("=== verify_pretooluse_security (PreToolUse-fold security gate) ===")
    if not os.path.isfile(LIVE):
        print(f"FATAL: live dispatcher missing: {LIVE}")
        return 2
    gate_secret()
    gate_bashguard()
    gate_pass()
    total = _passes + _fails
    print(f"\nPTU_SECURITY_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
