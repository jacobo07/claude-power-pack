"""V-PED-* gates for hooks/post_edit_diagnostics.js (spec: vault/specs/post-edit-diagnostics.md).

Drives the real hook as a subprocess with the real PostToolUse stdin shape. Every
"silent" assertion is paired with a "surfaces" assertion from the same harness, so
a hook that never speaks cannot pass.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# PED_HOOK lets a mutation drill point the suite at an isolated mutant copy;
# tools/mutation_drill.py cannot, because it copies only the subject's directory.
HOOK = Path(os.environ.get("PED_HOOK") or ROOT / "hooks" / "post_edit_diagnostics.js")
NODE = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"

passes = 0
fails = 0


def _ok(gate: str, evidence: str) -> None:
    global passes
    passes += 1
    print(f"PASS {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {diag}")


def run_hook(payload, log: Path, extra_env: dict | None = None, raw: str | None = None):
    env = dict(os.environ)
    env.pop("CLAUDE_POST_EDIT_DIAG", None)
    env["POST_EDIT_DIAG_LOG"] = str(log)
    env.update(extra_env or {})
    stdin = raw if raw is not None else json.dumps(payload)
    r = subprocess.run([NODE, str(HOOK)], input=stdin, capture_output=True, text=True,
                       encoding="utf-8", env=env, timeout=20)
    ctx = ""
    if r.stdout.strip():
        ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
    return r.returncode, ctx


def edit_payload(path: Path, tool: str = "Edit") -> dict:
    return {
        "session_id": "test", "hook_event_name": "PostToolUse", "tool_name": tool,
        "tool_input": {"file_path": str(path), "old_string": "a", "new_string": "b"},
        "tool_response": {"filePath": str(path), "success": True},
    }


def last_log(log: Path) -> dict:
    lines = log.read_text(encoding="utf-8").strip().splitlines()
    return json.loads(lines[-1])


def expect_surfaces(gate, path, log, must_contain, tool="Edit", env=None):
    code, ctx = run_hook(edit_payload(path, tool), log, env)
    entry = last_log(log)
    if code == 0 and all(s in ctx for s in must_contain) and entry["outcome"] == "findings":
        _ok(gate, f"{path.name} -> {ctx.splitlines()[1].strip() if len(ctx.splitlines()) > 1 else ctx}")
    else:
        _fail(gate, f"exit={code} outcome={entry.get('outcome')} reason={entry.get('reason')} "
                    f"ctx={ctx!r} want={must_contain}")


def expect_silent(gate, payload, log, want_outcome, env=None, raw=None):
    code, ctx = run_hook(payload, log, env, raw)
    entry = last_log(log)
    if code == 0 and ctx == "" and entry["outcome"] == want_outcome:
        _ok(gate, f"silent, outcome={want_outcome} reason={entry.get('reason', '-')}")
    else:
        _fail(gate, f"exit={code} ctx={ctx!r} outcome={entry.get('outcome')} want={want_outcome}")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="ped_"))
    log = tmp / "log.jsonl"
    try:
        # Arrange
        undefined = tmp / "undefined_name.py"
        undefined.write_text("def f():\n    return missing_thing\n", encoding="utf-8")
        syntax = tmp / "syntax_err.py"
        syntax.write_text("def f(:\n    pass\n", encoding="utf-8")
        clean_py = tmp / "clean.py"
        clean_py.write_text("import os\n\n\ndef f():\n    return os.sep\n", encoding="utf-8")
        bad_js = tmp / "bad.js"
        bad_js.write_text("function f( {\n  return 1;\n}\n", encoding="utf-8")
        esm_js = tmp / "esm.js"
        esm_js.write_text("import fs from 'fs';\nexport const a = fs.sep;\n", encoding="utf-8")
        bad_json = tmp / "bad.json"
        bad_json.write_text('{"a": 1,}', encoding="utf-8")
        bom_json = tmp / "bom.json"
        bom_json.write_bytes(b"\xef\xbb\xbf" + b'{"a": 1}')
        clean_json = tmp / "clean.json"
        clean_json.write_text('{"a": 1}', encoding="utf-8")
        ts = tmp / "x.ts"
        ts.write_text("const a: number = ;\n", encoding="utf-8")

        # Act + Assert: findings surface
        expect_surfaces("V-PED-PY-UNDEFINED", undefined, log, ["F821", "L2:", "missing_thing"])
        expect_surfaces("V-PED-PY-SYNTAX", syntax, log, ["L1:", "issue(s)"])
        # node reports the line where parsing failed: `return 1;` on line 2.
        expect_surfaces("V-PED-JS-SYNTAX", bad_js, log, ["SyntaxError", "L2", "Unexpected number"])
        expect_surfaces("V-PED-JSON-PARSE", bad_json, log, ["JSONParse"], tool="Write")
        expect_surfaces("V-PED-JSON-BOM", bom_json, log, ["BOM"])
        expect_surfaces("V-PED-MULTIEDIT", undefined, log, ["F821"], tool="MultiEdit")

        # Controls: the same harness, clean inputs, must be silent
        expect_silent("V-PED-PY-CLEAN", edit_payload(clean_py), log, "clean")
        expect_silent("V-PED-JS-ESM-CLEAN", edit_payload(esm_js), log, "clean")
        expect_silent("V-PED-JSON-CLEAN", edit_payload(clean_json), log, "clean")

        # Scope and fail-open
        expect_silent("V-PED-TS-NOT-COVERED", edit_payload(ts), log, "skipped")
        expect_silent("V-PED-NON-EDIT-TOOL", {"tool_name": "Bash",
                      "tool_input": {"command": "ls"}}, log, "skipped")
        expect_silent("V-PED-RUFF-MISSING", edit_payload(undefined), log, "unchecked",
                      env={"POST_EDIT_DIAG_RUFF": str(tmp / "no_such_ruff.exe")})
        expect_silent("V-PED-BAD-STDIN", None, log, "unchecked", raw="not json")
        expect_silent("V-PED-MISSING-FILE", edit_payload(tmp / "gone.py"), log, "unchecked")
        expect_silent("V-PED-KILL-SWITCH", edit_payload(undefined), log, "disabled",
                      env={"CLAUDE_POST_EDIT_DIAG": "off"})

        # A BOM on stdin (PowerShell 5.1 piping to node) must not mute the hook.
        code, ctx = run_hook(None, log, raw="﻿" + json.dumps(edit_payload(undefined)))
        if code == 0 and "F821" in ctx:
            _ok("V-PED-STDIN-BOM", "BOM-prefixed stdin still surfaces F821")
        else:
            _fail("V-PED-STDIN-BOM", f"exit={code} log={last_log(log)} ctx={ctx!r}")

        # Output cap: 25 undefined names -> 20 listed + "and 5 more"
        many = tmp / "many.py"
        many.write_text("".join(f"x{i} = undefined_{i}\n" for i in range(25)), encoding="utf-8")
        code, ctx = run_hook(edit_payload(many), log)
        listed = [ln for ln in ctx.splitlines() if "F821" in ln]
        if code == 0 and len(listed) == 20 and "and 5 more" in ctx and "25 issue(s)" in ctx:
            _ok("V-PED-CAP", "25 findings -> 20 listed + 'and 5 more'")
        else:
            _fail("V-PED-CAP", f"listed={len(listed)} ctx_tail={ctx[-80:]!r}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"PED_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
