#!/usr/bin/env python3
"""V-XPB-* -- gates for the cross-project baseline (promote + inject).

Spec: vault/specs/cross-project-baseline.md (Owner chose option B, 2026-08-31).

Origin: measured 2026-08-31, the estate captured diligently and propagated
nothing. `promote_to_global` was a pure predicate whose only caller was a test;
`graph_first_gate` read the promoted store and emitted a COUNT. So a fix made
in one project could never reach another.

The gates below pin the two properties that make this safe to run ALWAYS in
EVERY project, which is what the Owner asked for:

  1. Only real, portable error identities promote. The bare >=2-projects
     predicate admits `FAILED`, JavaScript source, and a Spanish doc template
     -- injecting those into every project forever is worse than silence.
  2. Injection is silent unless the pattern matches the command at hand.
     Relevance must be NECESSARY, not weighted.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PP_ROOT / "tools"))

import ceps  # noqa: E402

_NODE = os.environ.get("NODE_EXE") or "node"
_GATE = _PP_ROOT / "hooks" / "graph_first_gate.js"

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS  {gate}  {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL  {gate}  {diagnostic}")


def _ev(sig, project, root_cause, status="valid", subsystem="bash:python"):
    return {"pattern_signature": sig, "project_id": project,
            "root_cause": root_cause, "admission_status": status,
            "subsystem": subsystem, "category": "tooling",
            "prevention_rule": f"rule for {root_cause}",
            "ts": "2026-08-31T00:00:00Z"}


def _node_eval(script: str) -> str:
    """Run a snippet against the real hook module and return its stdout."""
    res = subprocess.run([_NODE, "-e", script], capture_output=True,
                         text=True, timeout=30)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip()[:400])
    return res.stdout.strip()


def main() -> int:
    print("== V-XPB gates (cross-project baseline) ==")

    # ---- V-XPB-PROMOTES ---------------------------------------------------
    events = [
        _ev("sigA", "projA", "ModuleNotFoundError"),
        _ev("sigA", "projB", "ModuleNotFoundError"),
        _ev("sigLocal", "projA", "ValueError"),
        _ev("sigLocal", "projA", "ValueError"),
        _ev("sigLocal", "projA", "ValueError"),
    ]
    got = {r["pattern_signature"] for r in ceps.compute_promotions(events)}
    if got == {"sigA"}:
        _ok("V-XPB-PROMOTES", "a 2-project identity promotes; 1-project does not")
    else:
        _fail("V-XPB-PROMOTES", f"expected {{'sigA'}}, got {got}")

    # ---- V-XPB-NO-SELF-PROMOTION -----------------------------------------
    # Recurrence is not portability. Three hits in ONE project must not travel.
    many = [_ev("sigOne", "projA", "ImportError") for _ in range(9)]
    if ceps.compute_promotions(many) == []:
        _ok("V-XPB-NO-SELF-PROMOTION",
            "9 occurrences in 1 project -> no promotion")
    else:
        _fail("V-XPB-NO-SELF-PROMOTION",
              "a single-project pattern was promoted")

    # ---- V-XPB-REJECTS-NON-IDENTITY --------------------------------------
    # The three real corpus offenders, verbatim. Each reaches >=2 projects and
    # carries admission_status=valid, so ONLY the identity control stops them.
    offenders = {
        "FAILED": "a bare word scraped from output",
        "Error ? err.message : String(err": "JavaScript source",
        "Error exacto: [mensaje completo": "a Spanish doc template",
    }
    leaked = []
    for text, why in offenders.items():
        evs = [_ev("sigX", "projA", text), _ev("sigX", "projB", text)]
        if ceps.compute_promotions(evs):
            leaked.append(f"{text!r} ({why})")
    if not leaked:
        _ok("V-XPB-REJECTS-NON-IDENTITY",
            f"{len(offenders)} real corpus offenders rejected on identity alone")
    else:
        _fail("V-XPB-REJECTS-NON-IDENTITY", f"leaked: {leaked}")

    # ---- V-XPB-ADMISSION-REQUIRED ----------------------------------------
    suspect = [_ev("sigS", "projA", "KeyError", status="identity_suspect"),
               _ev("sigS", "projB", "KeyError", status="identity_suspect")]
    if ceps.compute_promotions(suspect) == []:
        _ok("V-XPB-ADMISSION-REQUIRED",
            "identity_suspect events cannot argue portability")
    else:
        _fail("V-XPB-ADMISSION-REQUIRED",
              "a pattern promoted on identity_suspect evidence")

    # ---- V-XPB-WRITER-IS-A-SET -------------------------------------------
    # promote_to_global has been a pure predicate since it landed. The writer
    # must be idempotent, or the injector shows the same rule twice.
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "events.jsonl"
        dst = Path(td) / "promoted.jsonl"
        src.write_text("".join(json.dumps(e) + "\n" for e in events),
                       encoding="utf-8")
        r1 = ceps.promote_patterns(src, dst)
        n1 = len(dst.read_text(encoding="utf-8").strip().splitlines())
        ceps.promote_patterns(src, dst)
        n2 = len(dst.read_text(encoding="utf-8").strip().splitlines())
        if r1.get("ok") and n1 == n2 == 1:
            _ok("V-XPB-WRITER-IS-A-SET",
                f"two runs -> {n2} record (idempotent by signature)")
        else:
            _fail("V-XPB-WRITER-IS-A-SET",
                  f"ok={r1.get('ok')} first={n1} second={n2}")

    # ---- V-XPB-INJECTS-CONTENT + V-XPB-SILENT-ON-NO-MATCH ----------------
    # Exercised through the REAL hook module, not a reimplementation.
    try:
        rec = json.dumps({
            "pattern_signature": "sigA", "root_cause": "ModuleNotFoundError",
            "prevention_rule": "Probe the env before assuming the runtime.",
            "subsystems": ["bash:python", "bash:cd"], "project_count": 3,
        })
        script = (
            f"const g=require({str(_GATE).replace(chr(92), '/')!r});"
            f"const recs=[{rec}];"
            "const hit=g.relevantPromotions(recs,g.programTokens("
            "'python -m pytest tests/'));"
            "const miss=g.relevantPromotions(recs,g.programTokens("
            "'cd /tmp && echo hello'));"
            "console.log(JSON.stringify({hit:hit.length,miss:miss.length,"
            "text:hit.length?g.buildBaselineAdvisory(hit):''}));"
        )
        out = json.loads(_node_eval(script))
        if out["hit"] == 1 and "ModuleNotFoundError" in out["text"] \
                and "Probe the env" in out["text"]:
            _ok("V-XPB-INJECTS-CONTENT",
                "a matching command receives the rule TEXT, not a count")
        else:
            _fail("V-XPB-INJECTS-CONTENT", f"got {out}")

        # `cd` and `echo` are navigation tokens and appear in the record's own
        # subsystem list. If they matched, every shell command in every project
        # would carry this advisory forever -- the exact noise failure.
        if out["miss"] == 0:
            _ok("V-XPB-SILENT-ON-NO-MATCH",
                "navigation-only command matches nothing (relevance necessary)")
        else:
            _fail("V-XPB-SILENT-ON-NO-MATCH",
                  f"a `cd`/`echo` command drew {out['miss']} advisories")
    except (RuntimeError, OSError, ValueError, KeyError,
            subprocess.SubprocessError) as e:
        _fail("V-XPB-INJECTS-CONTENT", f"node harness failed: {e}")
        _fail("V-XPB-SILENT-ON-NO-MATCH", "not reached")

    # ---- V-XPB-FAIL-OPEN --------------------------------------------------
    try:
        script = (
            f"const g=require({str(_GATE).replace(chr(92), '/')!r});"
            "const out=g.run({tool_name:'Bash',tool_input:{command:'python x.py'},"
            "cwd:'/nonexistent-repo',session_id:'t'});"
            "console.log(typeof out==='object'?'object':'BAD');"
        )
        if _node_eval(script).endswith("object"):
            _ok("V-XPB-FAIL-OPEN", "hook returns an object, never throws")
        else:
            _fail("V-XPB-FAIL-OPEN", "hook did not return an object")
    except (RuntimeError, subprocess.SubprocessError) as e:
        _fail("V-XPB-FAIL-OPEN", f"hook threw: {e}")

    total = _passes + _fails
    print(f"XPB_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
