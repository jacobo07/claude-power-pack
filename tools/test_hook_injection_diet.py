#!/usr/bin/env python
"""V-DIET-* gates: hook advisory text reaches the model once per session, not on every call.

Origin (wiki/improvements/hook-injection-diet.md; census 2026-10-04 over one 2.9 MB session):
34 injections, 65.5k chars (~28k tok) that stay resident and are re-read by every later call. The
same 6.8 KB active spec was re-injected on every prompt, the Tower baseline repeated verbatim, the
cascade-aperture notice fired 12 times. Each gate below pairs the dedupe with its control: a NEW
session and a CHANGED payload must still get the full text, or a gate that drops everything would
pass.

Run: python tools/test_hook_injection_diet.py   (DIET_TOOLS_DIR=<dir> runs a scratch copy)
"""
from __future__ import annotations

import importlib
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = Path(os.environ.get("DIET_TOOLS_DIR") or (ROOT / "tools"))

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def _jit():
    sys.path.insert(0, str(TOOLS))
    if "jit_skill_loader" in sys.modules:
        return importlib.reload(sys.modules["jit_skill_loader"])
    return importlib.import_module("jit_skill_loader")


def jit_gates():
    jit = _jit()
    with tempfile.TemporaryDirectory(prefix="diet_jit_") as tmp:
        spec = Path(tmp) / ".specify" / "specs" / "000-diet" / "spec.md"
        spec.parent.mkdir(parents=True)
        s1 = "DIET_SPEC_SENTINEL_A_" + os.urandom(4).hex()
        spec.write_text(f"# Diet\n\n## FR-001\n{s1}\n", encoding="utf-8")
        sid = f"diet-{os.urandom(4).hex()}"

        def run(session):
            out = jit.run({"prompt": "implement the feature", "cwd": tmp, "session_id": session}) or {}
            return out.get("additionalContext", "") or ""

        first, second = run(sid), run(sid)
        check("V-DIET-JIT-SPEC-FIRST", s1 in first, f"first call carries the spec ({len(first)} B)")
        check("V-DIET-JIT-SPEC-ONCE", s1 not in second and "spec.md" in second
              and len(second) < len(first),
              f"second call: sentinel absent, pointer names the file ({len(second)} B < {len(first)} B)")
        check("V-DIET-JIT-SPEC-NEW-SESSION", s1 in run(f"diet-{os.urandom(4).hex()}"),
              "a new session gets the full spec")
        s2 = "DIET_SPEC_SENTINEL_B_" + os.urandom(4).hex()
        spec.write_text(f"# Diet\n\n## FR-001\n{s2}\n", encoding="utf-8")
        check("V-DIET-JIT-SPEC-CHANGED", s2 in run(sid), "a changed spec is re-injected in the same session")


HOOKS_ROOT = Path(os.environ.get("DIET_HOOKS_ROOT") or ROOT)
NODE = os.environ.get("NODE_EXE") or "node"
NIE = "raise " + "NotImplemented" + "Error"   # built at runtime: the write gates scan this file too


def _hook(rel, payload, env_extra=None):
    import json
    import subprocess
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SESSION_KIND"}  # interactive unless asked
    env.update(env_extra or {})
    r = subprocess.run([NODE, str(HOOKS_ROOT / rel)], input=json.dumps(payload), capture_output=True,
                       text=True, encoding="utf-8", env=env, timeout=60)
    try:
        return json.loads(r.stdout or "{}")
    except Exception:
        return {"_raw": r.stdout, "_err": r.stderr}


def cascade_gates():
    with tempfile.TemporaryDirectory(prefix="diet_once_") as once:
        env = {"PP_ADVISORY_ONCE_DIR": once}
        cmd = "$s = @'\necho hello\n'@\n$s | Out-File x.txt"
        sid = f"diet-{os.urandom(4).hex()}"

        def note(session, command=cmd):
            out = _hook("hooks/cascade_check_bash.js",
                        {"tool_name": "PowerShell", "tool_input": {"command": command}, "session_id": session}, env)
            return ((out.get("hookSpecificOutput") or {}).get("additionalContext") or "")

        a, b = note(sid), note(sid)
        check("V-DIET-APERTURE-FIRST", "were elided before the dangerous-command scan" in a, a[:90])
        check("V-DIET-APERTURE-TAG", "[cascade-aperture]" in b and "see earlier note" in b
              and "were elided before" not in b, b[:90])
        check("V-DIET-APERTURE-NEW-SESSION", "were elided before" in note(f"diet-{os.urandom(4).hex()}"),
              "a new session gets the full sentence")
        sink = "$s = @'\necho hi\n'@\nInvoke-Expression $s"
        s1, s2 = note(sid, sink), note(sid, sink)
        check("V-DIET-SINK-NEVER-SHORTENED", "local execution sink" in s1 and "local execution sink" in s2,
              "the security note stays full on every call")


def graph_first_gate_structural():
    src = (HOOKS_ROOT / "hooks" / "graph_first_gate.js").read_text(encoding="utf-8")
    import re
    m = re.search(r"const THROTTLE_MS = ([0-9 *]+);", src)
    ms = 1 if m else 0
    for factor in (m.group(1).split("*") if m else []):
        ms *= int(factor.strip())
    check("V-DIET-GRAPH-FIRST-COOLDOWN-STRUCTURAL", ms >= 2 * 60 * 60 * 1000,
          f"THROTTLE_MS={ms} (structural: a fast test cannot tell a 15 min cooldown from 2 h)")


def zero_fiction_gates():
    gate = "modules/zero-crash/hooks/zero-fiction-gate.js"

    def verdict(content, env_extra=None):
        out = _hook(gate, {"tool_name": "Write", "tool_input": {"file_path": "x.py", "content": content}},
                    env_extra)
        return (out.get("hookSpecificOutput") or {}).get("permissionDecision") or "none"

    base_override = (f"class Observer:\n    def result(self, x):\n        {NIE}\n\n"
                     f"class D(Observer):\n    def result(self, x):\n        return x\n")
    decorated = f"import abc\nclass B(abc.ABC):\n    @abc.abstractmethod\n    def go(self):\n        {NIE}\n"
    stub = f"def compute(x):\n    {NIE}\n"
    check("V-DIET-ZF-BASE-OVERRIDE-ALLOWED", verdict(base_override) == "none", verdict(base_override))
    check("V-DIET-ZF-ABSTRACTMETHOD-ALLOWED", verdict(decorated) == "none", verdict(decorated))
    check("V-DIET-ZF-STUB-ASKS-INTERACTIVE", verdict(stub) == "ask", verdict(stub))
    v = verdict(stub, {"CLAUDE_CODE_SESSION_KIND": "bg"})
    check("V-DIET-ZF-STUB-DENIED-IN-BG", v == "deny", v)
    mixed = base_override + "\n" + stub
    check("V-DIET-ZF-MIXED-STILL-FLAGGED", verdict(mixed) == "ask", "one real stub beside an abstract method")


def main() -> int:
    jit_gates()
    cascade_gates()
    graph_first_gate_structural()
    zero_fiction_gates()
    print(f"DIET_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
