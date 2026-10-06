#!/usr/bin/env python
"""e1_mechanical.py -- E1 preflight gate 1: does excluding the 13 [B] rules shrink the BILLED context?

Owner condition (2026-10-05): before any counted E1 run, prove mechanically that the challenger's
exclusion removes resident context from what a call is billed for. Hiding skills did not shrink
the listing floor once; the same could be true here, and 24 sessions must not be bought to find out.

One minimal headless call per arm, in an empty temp directory, same prompt, same model:
  A = the host's current prefix;  B = A plus `--settings {"claudeMdExcludes": [the 13 files]}`.
The billed first-call context is input + cache_read + cache_creation from the CLI's own usage
report. The 13 files are checked against the packet's LF sha256 pins first: a host whose files
differ is reported, and its delta is not evidence about the packet's rules.

    python e1_mechanical.py --claude <path> [--model claude-opus-5-5] [--out result.json]

Prints one JSON object. Exit 0 = both arms measured; 2 = a pin mismatch or an unmeasured arm.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PINS = {
    "rules/technical-failure-to-product-state.md": "b9ba87293fa84d36dada997fbe887d669879a070f58062d88aa3004d245af08b",
    "rules/scoped-side-effect-authority.md": "cb133f55609810f2b601318af6cee9fa36e78ad30f88bcde14240d6debbf7d05",
    "rules/generated-content-needs-an-evidence-gate.md": "8f5de045a7b75630cc077ef53698ba1776489706a8640af8e8fb6e4d6f10ea1c",
    "rules/effect-authority-across-transports.md": "e1d11c9744a02adcb6f428adba3f803c74574ce2254d47e39e5d5e503afe7074",
    "rules/human-facing-external-effects.md": "f56914f38ee727840aec17c862f65dc13e04d0dc6d7d5b3ece78577c0d06bfdb",
    "rules/documented-capability-must-be-executable.md": "776b985fd3d5aaea8fb9eef0ac0aa003c327143d185b105efb4b8b269cab5136",
    "rules/validation-planes-do-not-transfer.md": "f7ac1415e3d40175828a96d7299c1d7b33c67302a8c0b6b4309840e3df745139",
    "rules/capability-preserving-compaction.md": "328a088e78ac4d7a47362e1c2814969bc075e560eea39943de0cd1713e5283f1",
    "rules/state-lifetime-and-incarnation.md": "fa5d6222f5ec57f915a1673d6f9fd8355428a85b19f5bc2b1466dd4a1eb72df0",
    "rules/post-effect-resource-truth.md": "4ffa7549ab80336cd7a6fd2988d9c4cefa336e3070594604e4176998b68e8248",
    "rules/durable-exit-transaction.md": "cb6f17aa3b4d7f790675f65c41c31f4bba6fd6a6fca01b1a74a07d2c491529e4",
    "rules/python/testing.md": "2ae141c9eaf5543034127fc33ec057efde849ea3151bf47ec85e4563f9f897bf",
    "rules/common/code-review.md": "befb119ebee31c378acad1a8fa8e815c600073c1d7924462f430ec01775b8002",
}
PROMPT = "Reply with the single word OK and nothing else."


def lf_sha(p: Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    except OSError:
        return None


def one_call(claude: str, model: str, excludes: list | None) -> dict:
    cmd = [claude, "-p", PROMPT, "--model", model, "--output-format", "json", "--max-turns", "1"]
    if excludes is not None:
        cmd += ["--settings", json.dumps({"claudeMdExcludes": excludes})]
    env = {k: v for k, v in os.environ.items()
           if not (k.startswith("CLAUDECODE") or k.startswith("CLAUDE_CODE_"))}
    # A process the CLI leaves behind (a hook child) can still hold the cwd on Windows; a cleanup
    # failure must not throw away a measurement that already happened (measured 2026-10-06).
    with tempfile.TemporaryDirectory(prefix="e1mech-", ignore_cleanup_errors=True) as wd:
        try:
            r = subprocess.run(cmd, cwd=wd, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=300, env=env)
        except subprocess.TimeoutExpired:
            return {"state": "UNMEASURED", "reason": "timeout"}
    try:
        j = json.loads(r.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {"state": "UNMEASURED", "reason": f"rc={r.returncode} unparseable stdout",
                "stderr_tail": r.stderr[-300:]}
    u = j.get("usage") or {}
    parts = {k: u.get(k) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens",
                                   "output_tokens")}
    if any(parts[k] is None for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")):
        return {"state": "UNMEASURED", "reason": "usage fields absent", "usage": u}
    ctx = parts["input_tokens"] + parts["cache_read_input_tokens"] + parts["cache_creation_input_tokens"]
    # A call that reached the model carries its whole prefix; zero means it never got there
    # (measured on GEX44 2.1.113: fields present, all 0). Absent is not zero.
    if ctx <= 0 or j.get("is_error"):
        return {"state": "UNMEASURED", "reason": f"context={ctx} is_error={j.get('is_error')}",
                "result": str(j.get("result", ""))[:300], "subtype": j.get("subtype")}
    return {"state": "MEASURED", "session_id": j.get("session_id"), "num_turns": j.get("num_turns"),
            "context": ctx, **parts}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--claude", required=True)
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--out")
    a = ap.parse_args()
    home = Path.home() / ".claude"
    files = {rel: home / rel for rel in PINS}
    pins = {rel: ("MATCH" if lf_sha(p) == PINS[rel] else ("MISSING" if lf_sha(p) is None else "DIFFERS"))
            for rel, p in files.items()}
    excl = [str(p).replace("\\", "/") for p in files.values()]
    ver = subprocess.run([a.claude, "--version"], capture_output=True, text=True).stdout.strip()
    res = {"claude_version": ver, "model": a.model, "pins": pins,
           "pinned_bytes": sum(p.stat().st_size for p in files.values() if p.is_file())}
    res["A"] = one_call(a.claude, a.model, None)
    res["B"] = one_call(a.claude, a.model, excl)
    ok = all(v == "MATCH" for v in pins.values()) and res["A"]["state"] == res["B"]["state"] == "MEASURED"
    if res["A"]["state"] == res["B"]["state"] == "MEASURED":
        res["delta_context_tokens"] = res["A"]["context"] - res["B"]["context"]
    res["verdict"] = "MEASURED" if ok else "NOT_EVIDENCE"
    text = json.dumps(res, indent=1)
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
