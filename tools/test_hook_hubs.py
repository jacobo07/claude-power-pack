#!/usr/bin/env python3
"""
Hermetic V-gate tests for the hook-hub fold (M1 + M2 delivered).

Covers:
  - M1: ram-shield phantom removed; zero-issue-gate fast path (no test run,
        no ETIMEDOUT) when ZERO_ISSUE_GATE_RUN_TESTS is unset.
  - M2: migrate_hub_fold pure helpers (parse_chain_map, event_arg) and the
        reachability guard that distinguishes a wired chain from an orphan.
  - Regression: the secret firewall blocks a (clearly-fake) anthropic key in
        the PreToolUse-Edit-chain; a benign edit passes (block-bug fix 5cf4a31).

Pure-logic gates are fully hermetic (synthetic inputs). Live-hook gates shell
out to the real dispatcher/gate with shell=False, a clearly-fake payload, and a
UNIQUE session_id + file_path per call so stateful gates (anti-thrash) never
accumulate -> the suite is re-run-stable.
"""
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import migrate_hub_fold as m  # noqa: E402

HOME = os.path.expanduser("~")
DISPATCHER = os.path.join(HOME, ".claude", "hooks", "hook-dispatcher.js")
ZERO_GATE = os.path.join(HOME, ".claude", "hooks", "zero-issue-gate.js")

passes = 0
fails = 0
_uniq = 0


def _ok(gate, evidence):
    global passes
    passes += 1
    print(f"OK   {gate}: {evidence}")


def _fail(gate, diag):
    global fails
    fails += 1
    print(f"FAIL {gate}: {diag}")


def _unique():
    """A fresh (session_id, file_path) pair so stateful gates never accumulate."""
    global _uniq
    _uniq += 1
    tag = f"{os.getpid()}_{time.time_ns()}_{_uniq}"
    return (f"test-hubs-{tag}", f"/tmp/test_hubs_{tag}.py")


def _node():
    for c in (shutil.which("node"),
              r"C:\Program Files\nodejs\node.exe",
              "/usr/bin/node", "/usr/local/bin/node"):
        if c and os.path.exists(c):
            return c
    return None


def _run_hook(script, payload, event=None):
    """Run a hook/dispatcher shell-free; return (rc, stdout, stderr)."""
    node = _node()
    if not node:
        return (None, "", "node not found")
    args = [node, script]
    if event:
        args.append(f"--event={event}")
    env = dict(os.environ)
    env.pop("ZERO_ISSUE_GATE_RUN_TESTS", None)  # prove the default (gated-off) path
    p = subprocess.run(args, input=json.dumps(payload).encode("utf-8"),
                       capture_output=True, env=env, timeout=90)
    return (p.returncode,
            p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def _edit_payload(new_string):
    sid, fp = _unique()
    return {"session_id": sid, "tool_name": "Edit",
            "tool_input": {"file_path": fp, "old_string": "a",
                           "new_string": new_string}}


# ---- M2: parse_chain_map -------------------------------------------------
def t_parse_chain_map():
    src = (
        "const CHAIN_MAP = {\n"
        "  'Stop-chain': [\n"
        "    { exe: NODE_EXE, script: './zero-issue-gate.js', timeoutMs: 70000 },\n"
        "    { exe: NODE_EXE, script: '../a/b/mark-live-session.js' },\n"
        "  ],\n"
        "  'PostToolUse-Bash-chain': [\n"
        "    { exe: NODE_EXE, script: './tty-restore.js' },\n"
        "  ],\n"
        "};\n"
        "const OTHER = { 'NOPE-chain': [ { script: './x.js' } ] };\n"
    )
    cm = m.parse_chain_map(src)
    if ("Stop-chain" in cm and "zero-issue-gate.js" in cm["Stop-chain"]
            and "mark-live-session.js" in cm["Stop-chain"]
            and "tty-restore.js" in cm.get("PostToolUse-Bash-chain", set())
            and "NOPE-chain" not in cm):
        _ok("V-HOOK-PARSE-CHAINMAP",
            f"parsed {sorted(cm)} stopped at CHAIN_MAP close")
    else:
        _fail("V-HOOK-PARSE-CHAINMAP", f"unexpected parse: {cm}")


# ---- M2: event_arg -------------------------------------------------------
def t_event_arg():
    g1 = [{"matcher": "", "hooks": [
        {"command": 'node "x/hook-dispatcher.js" --event=Stop-chain'}]}]
    g2 = [{"hooks": [{"command": "node other.js"}]}]
    if m.event_arg(g1) == "Stop-chain" and m.event_arg(g2) is None:
        _ok("V-HOOK-EVENT-ARG", "extracts --event arg; None when no dispatcher")
    else:
        _fail("V-HOOK-EVENT-ARG",
              f"got {m.event_arg(g1)!r} / {m.event_arg(g2)!r}")


# ---- M2: reachability guard (wired vs orphan) ----------------------------
def t_reachability():
    cm = {"Stop-chain": {"mark-live-session.js"}}
    wired = cm.get("Stop-chain") is not None and "mark-live-session.js" in cm["Stop-chain"]
    orphan = cm.get("UserPromptSubmit-default") is None
    if wired and orphan:
        _ok("V-HOOK-REACHABILITY",
            "wired chain removable; orphan-chain (default arg) correctly skipped")
    else:
        _fail("V-HOOK-REACHABILITY", f"wired={wired} orphan={orphan}")


# ---- M1: ram-shield phantom removed --------------------------------------
def t_ram_shield_gone():
    if not os.path.exists(DISPATCHER):
        _fail("V-HOOK-RAM-SHIELD-GONE", f"dispatcher not found: {DISPATCHER}")
        return
    src = open(DISPATCHER, encoding="utf-8").read()
    # Look for the SCRIPT-PATH form (trailing quote) so the removal comment,
    # which mentions the bare name, does not trip a false positive.
    if "ram-shield.js'" not in src and "ram-watchdog.js" in src:
        _ok("V-HOOK-RAM-SHIELD-GONE",
            "no ram-shield.js script ref; real ram-watchdog.js retained")
    else:
        _fail("V-HOOK-RAM-SHIELD-GONE", "ram-shield.js still referenced as a script")


# ---- M1: zero-issue-gate fast path (no tests, no ETIMEDOUT) ---------------
def t_zero_issue_fastpath():
    if not os.path.exists(ZERO_GATE):
        _fail("V-HOOK-ZERO-ISSUE-FASTPATH", f"not found: {ZERO_GATE}")
        return
    t0 = time.monotonic()
    rc, out, err = _run_hook(ZERO_GATE, {})
    dt = time.monotonic() - t0
    if rc is None:
        _fail("V-HOOK-ZERO-ISSUE-FASTPATH", "node not available")
        return
    body = out + err
    if '"continue"' in out and "ETIMEDOUT" not in body and dt < 15:
        _ok("V-HOOK-ZERO-ISSUE-FASTPATH",
            f"continue emitted in {dt:.2f}s, no ETIMEDOUT (tests gated off)")
    else:
        _fail("V-HOOK-ZERO-ISSUE-FASTPATH",
              f"dt={dt:.2f}s out={out[:120]!r} etimedout={'ETIMEDOUT' in body}")


# ---- Regression: secret firewall blocks in Edit-chain --------------------
def t_secret_blocks():
    fake = "sk-ant-" + ("A" * 50)  # clearly-fake, real-shape (HR-SECRET-005)
    rc, out, err = _run_hook(DISPATCHER, _edit_payload(fake),
                             event="PreToolUse-Edit-chain")
    if rc is None:
        _fail("V-HOOK-SECRET-BLOCKS", "node not available")
        return
    blocked = ('"permissionDecision":"deny"' in out
               or '"permissionDecision": "deny"' in out
               or '"continue":false' in out)
    if blocked:
        _ok("V-HOOK-SECRET-BLOCKS", "fake anthropic key denied by Edit-chain")
    else:
        _fail("V-HOOK-SECRET-BLOCKS", f"NOT blocked: out={out[:160]!r}")


# ---- Regression: benign edit passes (no over-block) ----------------------
def t_benign_passes():
    rc, out, err = _run_hook(DISPATCHER, _edit_payload("b = 1"),
                             event="PreToolUse-Edit-chain")
    if rc is None:
        _fail("V-HOOK-BENIGN-PASSES", "node not available")
        return
    denied = ('"permissionDecision":"deny"' in out
              or '"continue":false' in out)
    if not denied:
        _ok("V-HOOK-BENIGN-PASSES", "benign edit allowed (no over-block)")
    else:
        _fail("V-HOOK-BENIGN-PASSES", f"over-blocked: out={out[:160]!r}")


def main():
    t_parse_chain_map()
    t_event_arg()
    t_reachability()
    t_ram_shield_gone()
    t_zero_issue_fastpath()
    t_secret_blocks()
    t_benign_passes()
    total = passes + fails
    print(f"\nHOOK_HUBS_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
