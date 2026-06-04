#!/usr/bin/env python3
"""verify_hook_dispatcher.py -- HOOK_DISPATCHER done-gate probe (M5).

Regression guard for the hook-hub fold. V-gate convention (PP doctrine):
each check prints OK/FAIL with evidence; exit 0 iff all pass.

Gates
-----
V-HOOK-DISP-MIRROR    : live ~/.claude/hooks/hook-dispatcher.js is LF-normalized
                        byte-identical to the PP canonical copy (split-brain
                        parity -- the live mirror must match the committed
                        canonical or the runtime is stale; T-HOOK-MIRROR-001).
V-HOOK-DISP-HSO       : mergeOutputs->sanitizeForSchema routes UserPromptSubmit
                        additionalContext INTO hookSpecificOutput.additionalContext
                        (model-reaching), NOT stranded to systemMessage.
V-HOOK-DISP-COMPANION : the companion-in-process-bundle path is present (a
                        "<fam>-chain" event also runs its "<fam>-default" bundle).
V-HOOK-DISP-BOUNDED   : settings.json top-level hook entries per FOLDED event are
                        within threshold (UserPromptSubmit<=1, Stop<=2). Unfolded
                        events are reported (advisory) but not gated.

Usage:  python tools/verify_hook_dispatcher.py
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys

HOME = os.path.expanduser("~")
LIVE = os.path.join(HOME, ".claude", "hooks", "hook-dispatcher.js")
PP = os.path.join(HOME, ".claude", "skills", "claude-power-pack",
                  "hooks", "hook-dispatcher.js")
SETTINGS = os.path.join(HOME, ".claude", "settings.json")

# Thresholds for events that have been folded. An event NOT listed here is
# reported advisory-only (not yet folded -> not gated).
FOLDED_MAX_ENTRIES = {"UserPromptSubmit": 1, "Stop": 2}

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


def _lf_sha(path: str) -> str | None:
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError:
        return None
    lf = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(lf).hexdigest()


def _node_exe() -> str:
    p = shutil.which("node")
    if p:
        return p
    cand = r"C:\Program Files\nodejs\node.exe"
    return cand if os.path.isfile(cand) else "node"


def gate_mirror() -> None:
    if not os.path.isfile(LIVE):
        _fail("V-HOOK-DISP-MIRROR", f"live dispatcher missing: {LIVE}")
        return
    if not os.path.isfile(PP):
        _fail("V-HOOK-DISP-MIRROR", f"PP dispatcher missing: {PP}")
        return
    lh, ph = _lf_sha(LIVE), _lf_sha(PP)
    if lh and lh == ph:
        _ok("V-HOOK-DISP-MIRROR", f"live==pp sha={lh[:12]}")
    else:
        _fail("V-HOOK-DISP-MIRROR",
              f"DRIFT live={str(lh)[:12]} pp={str(ph)[:12]} -- re-mirror "
              f"PP->live (Copy-Item) so the runtime is not stale")


def gate_hso() -> None:
    # Functional: require the LIVE dispatcher and exercise the exact merge path.
    js = (
        "const d=require(%s);"
        "const fam=d.familyOf('UserPromptSubmit-chain');"
        "const m=d.mergeOutputs([{hookSpecificOutput:{hookEventName:fam,"
        "additionalContext:'PROBE'}}],'UserPromptSubmit-chain');"
        "const s=d.sanitizeForSchema(m,fam);"
        "process.stdout.write(JSON.stringify({hso:!!(s.hookSpecificOutput&&"
        "s.hookSpecificOutput.additionalContext),sys:!!s.systemMessage}));"
    ) % json.dumps(LIVE.replace("\\", "/"))
    try:
        r = subprocess.run([_node_exe(), "-e", js], capture_output=True,
                           text=True, timeout=20)
    except (OSError, subprocess.SubprocessError) as e:
        _fail("V-HOOK-DISP-HSO", f"node probe failed: {e}")
        return
    try:
        out = json.loads(r.stdout.strip())
    except (ValueError, AttributeError):
        _fail("V-HOOK-DISP-HSO", f"unparseable node output: {r.stdout[:120]!r}")
        return
    if out.get("hso") and not out.get("sys"):
        _ok("V-HOOK-DISP-HSO",
            "UPS additionalContext routed to hookSpecificOutput (not stranded)")
    else:
        _fail("V-HOOK-DISP-HSO",
              f"hso={out.get('hso')} systemMessage={out.get('sys')} -- "
              f"UPS context not reaching model channel")


def gate_companion() -> None:
    try:
        src = open(LIVE, encoding="utf-8").read()
    except OSError as e:
        _fail("V-HOOK-DISP-COMPANION", f"cannot read live: {e}")
        return
    if "COMPANION IN-PROCESS BUNDLE" in src and "-default" in src:
        _ok("V-HOOK-DISP-COMPANION", "companion in-process bundle path present")
    else:
        _fail("V-HOOK-DISP-COMPANION", "companion path marker absent")


def gate_bounded() -> None:
    try:
        with open(SETTINGS, encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as e:
        _fail("V-HOOK-DISP-BOUNDED", f"settings.json unreadable: {e}")
        return
    hooks = data.get("hooks", {})
    violations = []
    advisory = []
    for event, groups in hooks.items():
        n = sum(len(g.get("hooks", [])) for g in groups)
        if event in FOLDED_MAX_ENTRIES:
            cap = FOLDED_MAX_ENTRIES[event]
            if n > cap:
                violations.append(f"{event}={n}>{cap}")
            else:
                advisory.append(f"{event}={n}<={cap}")
        else:
            advisory.append(f"{event}={n}(unfolded)")
    if violations:
        _fail("V-HOOK-DISP-BOUNDED", "; ".join(violations))
    else:
        _ok("V-HOOK-DISP-BOUNDED",
            "folded events within cap | " + "  ".join(advisory))


def main() -> int:
    print("=== verify_hook_dispatcher (HOOK_DISPATCHER done-gate) ===")
    gate_mirror()
    gate_hso()
    gate_companion()
    gate_bounded()
    total = _passes + _fails
    print(f"\nHOOK_DISPATCHER_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
