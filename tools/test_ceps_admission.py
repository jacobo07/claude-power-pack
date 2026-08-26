#!/usr/bin/env python3
"""V-CEPS-ADMIT-* -- semantic admission for the CEPS event store.

Reproducer for three producer defects found on 2026-08-25, all in the same
family: THE PRODUCER CLASSIFIED TEXT, NEVER WHETHER THE TOOL FAILED.

  P1  `/\\b\\d+ failed\\b/ -> regression` matched "0 failed" -- a pytest
      SUCCESS line filed as a regression (event 2026-08-25T14:50:20Z).
  P2  the sentinel branch fired on any tool whose output CONTAINED the
      literal, so reading the hook's own source recorded an integration
      failure it had merely quoted (events 14:15:51Z and 16:13:03Z).
  P3  subsystemOf() took the leading token of a chained command, so
      `cd X && pytest` bucketed as `cd` -- 15 of 19 stored regressions
      carried the subsystem `bash:cd`, which is a navigation prefix and
      not a failing tool.

Two layers are asserted because the defect has two earliest-prevention
points. The bridge is the earliest (never emit it); admission is the
universal net (no producer may write a vacuous failure claim). Each gate
has a BOOKEND: a detector that can only reject is indistinguishable from
one that is broken.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PP))

BRIDGE = PP / "hooks" / "bug-hunter-ceps-bridge.js"

# Declared gate count. Enforced in main(), not merely printed.
EXPECTED_GATES = 20

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diag}")


# --------------------------------------------------------------------------
# Layer 1 -- admission (tools/ceps.py). Universal: covers every producer.
# --------------------------------------------------------------------------
def _admission_gates() -> None:
    from tools import ceps  # noqa: PLC0415

    fn = getattr(ceps, "is_vacuous_failure_claim", None)
    if fn is None:
        _fail("V-CEPS-ADMIT-GATE-EXISTS",
              "tools.ceps.is_vacuous_failure_claim is not defined")
        return
    _ok("V-CEPS-ADMIT-GATE-EXISTS", "tools.ceps.is_vacuous_failure_claim")

    # P1: the exact stored root_cause that started this.
    vacuous = ["0 failed", "0 failed.", "0 errors", "no errors",
               "0 failures", "  0 failed  ", "0 warnings"]
    bad = [t for t in vacuous if not fn(t)]
    if bad:
        _fail("V-CEPS-ADMIT-ZERO-IS-NOT-A-FAILURE", f"admitted {bad!r}")
    else:
        _ok("V-CEPS-ADMIT-ZERO-IS-NOT-A-FAILURE",
            f"{len(vacuous)} zero-quantity claims rejected")

    # BOOKEND. A real failure, and a real finding that merely MENTIONS a
    # zero count, must both survive -- the gate rejects vacuity, not the
    # digit zero.
    real = ["3 failed", "12 failed, 4 passed", "AssertionError: x != y",
            "reported 0 failed but exit code was 1",
            "[Tool result missing due to internal error]"]
    lost = [t for t in real if fn(t)]
    if lost:
        _fail("V-CEPS-ADMIT-BOOKEND-REAL-SURVIVES", f"rejected {lost!r}")
    else:
        _ok("V-CEPS-ADMIT-BOOKEND-REAL-SURVIVES",
            f"{len(real)} real claims admitted, incl. a 0-mentioning finding")

    # End-to-end through record_error, against a redirected store, so the
    # gate is proven on the real write path and not only on the predicate.
    tmp = Path(tempfile.mkdtemp(prefix="ceps_admit_"))
    # EVERY write target, not just the obvious three. record_error() also
    # calls distribute(), which appends to the LIVE UKDL corpus and to
    # session_lessons. Redirecting only the store let the bookend below --
    # a deliberate REAL failure, recorded to prove the gate does not eat
    # them -- append ten synthetic entries into the knowledge base, once per
    # run of this suite. A test that writes to a global path is not hermetic
    # however carefully it cleans up the parts it remembered.
    old = (ceps.EVENTS_PATH, ceps.REJECTIONS_PATH, ceps.DB_PATH,
           ceps.LESSONS_PATH, ceps.UKDL_PATH)
    try:
        ceps.EVENTS_PATH = tmp / "events.jsonl"
        ceps.REJECTIONS_PATH = tmp / "rejections.jsonl"
        ceps.DB_PATH = tmp / "ceps.db"
        ceps.LESSONS_PATH = tmp / "session_lessons.md"
        ceps.UKDL_PATH = tmp / "ukdl-universal.md"

        got = ceps.record_error("regression", "bash:pytest", "0 failed")
        if got is not None:
            _fail("V-CEPS-ADMIT-RECORD-REJECTS",
                  "record_error persisted a vacuous failure claim")
        elif not ceps.REJECTIONS_PATH.exists():
            _fail("V-CEPS-ADMIT-RECORD-REJECTS",
                  "rejected but wrote no rejection record")
        else:
            body = ceps.REJECTIONS_PATH.read_text(encoding="utf-8")
            if "vacuous" not in body:
                _fail("V-CEPS-ADMIT-RECORD-REJECTS",
                      f"rejection reason not attributable: {body[:120]}")
            else:
                _ok("V-CEPS-ADMIT-RECORD-REJECTS",
                    "record_error -> None + attributable rejection")

        kept = ceps.record_error("regression", "bash:pytest", "3 failed")
        if kept is None:
            _fail("V-CEPS-ADMIT-RECORD-BOOKEND",
                  "record_error dropped a REAL failure")
        else:
            _ok("V-CEPS-ADMIT-RECORD-BOOKEND",
                f"real failure persisted as {kept['id']}")

        # Hermeticity, asserted rather than assumed. If a future write
        # target is added to distribute() and not redirected here, this
        # fails instead of quietly editing the knowledge base again.
        live_ukdl = Path(old[4])
        live_lessons = Path(old[3])
        leaked = [p.name for p in (live_ukdl, live_lessons)
                  if p.exists() and kept and kept["id"] in
                  p.read_text(encoding="utf-8-sig", errors="replace")]
        if leaked:
            _fail("V-CEPS-ADMIT-HERMETIC",
                  f"this suite wrote into the LIVE {leaked}")
        else:
            _ok("V-CEPS-ADMIT-HERMETIC",
                "no synthetic event reached the live corpora")
    finally:
        (ceps.EVENTS_PATH, ceps.REJECTIONS_PATH, ceps.DB_PATH,
         ceps.LESSONS_PATH, ceps.UKDL_PATH) = old
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------
# Layer 2 -- the producer (hooks/bug-hunter-ceps-bridge.js). Earliest point.
# --------------------------------------------------------------------------
def _node() -> str | None:
    return shutil.which("node")


def _bridge_eval(expr: str) -> tuple[bool, str]:
    """Evaluate `expr` against the bridge's exported pure functions."""
    node = _node()
    if node is None:
        return False, "node not on PATH"
    script = (
        f"const b = require({json.dumps(str(BRIDGE))});\n"
        f"process.stdout.write(JSON.stringify({expr}));\n"
    )
    try:
        out = subprocess.run([node, "-e", script], capture_output=True,
                             text=True, timeout=20)
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"
    if out.returncode != 0:
        return False, (out.stderr or "").strip()[:200]
    body = out.stdout.strip()
    # A bridge that runs its main() on require() returns exit 0 and no
    # stdout. Report that as a failed gate, never as an exception -- an
    # instrument that crashes cannot tell you what it measured.
    try:
        json.loads(body)
    except Exception:  # noqa: BLE001
        return False, f"non-JSON output {body[:120]!r} (main() ran on require?)"
    return True, body


def _bridge_gates() -> None:
    if _node() is None:
        _fail("V-CEPS-BRIDGE-EXPORTS", "node not on PATH -- cannot assert "
              "the producer half; refusing to score it as passing")
        return

    ok, payload = _bridge_eval("Object.keys(b).sort()")
    if not ok:
        _fail("V-CEPS-BRIDGE-EXPORTS", f"bridge is not requirable: {payload}")
        return
    keys = json.loads(payload)
    need = {"classify", "subsystemOf"}
    if not need.issubset(set(keys)):
        _fail("V-CEPS-BRIDGE-EXPORTS", f"missing {sorted(need - set(keys))}")
        return
    _ok("V-CEPS-BRIDGE-EXPORTS", f"pure functions exported: {keys}")

    # P3: the failing tool, not the navigation prefix that preceded it.
    cases = [
        ("Bash", "cd /repo && pytest -q", "bash:pytest"),
        ("Bash", "cd /repo; python tools/x.py", "bash:python"),
        ("PowerShell", "$env:PYTHONIOENCODING='utf-8'; & 'C:\\py\\python.exe' a.py",
         "powershell:python.exe"),
        ("Bash", "pytest -q", "bash:pytest"),
        ("Bash", "cd /repo", "bash:cd"),  # nav ONLY -> nav is the truth
    ]
    bad = []
    for tool, cmd, want in cases:
        ok, got = _bridge_eval(f"b.subsystemOf({json.dumps(tool)}, {json.dumps(cmd)})")
        got = json.loads(got) if ok else f"<err {got}>"
        if got != want:
            bad.append(f"{cmd!r} -> {got!r} (want {want!r})")
    if bad:
        _fail("V-CEPS-BRIDGE-SUBSYSTEM-IS-THE-TOOL", "; ".join(bad))
    else:
        _ok("V-CEPS-BRIDGE-SUBSYSTEM-IS-THE-TOOL",
            f"{len(cases)} commands bucketed by failing tool, nav skipped")

    # P2: quoted is not experienced. A long file dump that CONTAINS the
    # sentinel is the file's content; a dropped frame IS the sentinel.
    sentinel = "[Tool result missing due to internal error]"
    quoted = "const SENTINEL = '" + sentinel + "';\n" + ("x" * 400)
    ok, got = _bridge_eval(f"b.classify({json.dumps(quoted)})")
    if ok and json.loads(got) is None:
        _ok("V-CEPS-BRIDGE-QUOTED-IS-NOT-EXPERIENCED",
            "a 400-char source dump containing the sentinel is not a failure")
    else:
        _fail("V-CEPS-BRIDGE-QUOTED-IS-NOT-EXPERIENCED",
              f"classified quoted sentinel as {got}")

    # BOOKEND. The genuine dropped frame must still be caught.
    ok, got = _bridge_eval(f"b.classify({json.dumps(sentinel)})")
    hit = json.loads(got) if ok else None
    if hit and hit.get("category") == "integration":
        _ok("V-CEPS-BRIDGE-BOOKEND-REAL-SENTINEL",
            "a bare dropped frame is still integration")
    else:
        _fail("V-CEPS-BRIDGE-BOOKEND-REAL-SENTINEL", f"got {got}")

    # P1 at the earliest point: never emit it in the first place.
    ok, got = _bridge_eval('b.classify("=== 12 passed, 0 failed in 3.1s ===")')
    hit = json.loads(got) if ok else None
    if hit is None or hit.get("category") != "regression":
        _ok("V-CEPS-BRIDGE-ZERO-NOT-EMITTED",
            f"pytest success line -> {hit}")
    else:
        _fail("V-CEPS-BRIDGE-ZERO-NOT-EMITTED",
              f"success line classified {hit}")

    # BOOKEND. A real pytest failure line must still be a regression.
    ok, got = _bridge_eval('b.classify("=== 2 failed, 10 passed in 3.1s ===")')
    hit = json.loads(got) if ok else None
    if hit and hit.get("category") == "regression":
        _ok("V-CEPS-BRIDGE-BOOKEND-REAL-FAILURE",
            "a real pytest failure line is still a regression")
    else:
        _fail("V-CEPS-BRIDGE-BOOKEND-REAL-FAILURE", f"got {got}")

    # P2 at its true scale. 51 of the first 75 stored events were source
    # code printed by a grep or a cat, filed as tooling failures.
    src = ("    except Exception as e:  # noqa: BLE001 -- fail-open\n"
           "        loadError: null,\n"
           "  const msg = err instanceof Error ? err.message : String(err);\n")
    quoted_cases = [
        ("cd /repo && grep -rn 'fail-open' modules/", src),
        ("cat modules/graphify/global_store.py", src),
        ("sed -n '1,80p' hooks/x.js", src),
    ]
    bad = []
    for cmd, out in quoted_cases:
        ok, got = _bridge_eval(
            f"b.classify({json.dumps(out)}, {json.dumps(cmd)}, 'unknown')")
        hit = json.loads(got) if ok else "<err>"
        if hit is not None:
            bad.append(f"{cmd!r} -> {hit!r}")
    if bad:
        _fail("V-CEPS-BRIDGE-SOURCE-IS-NOT-A-FAILURE", "; ".join(bad))
    else:
        _ok("V-CEPS-BRIDGE-SOURCE-IS-NOT-A-FAILURE",
            f"{len(quoted_cases)} read commands printing source -> no event")

    # BOOKEND ONE. The same text from a command that RUNS things is a real
    # failure and must still record -- the rule is about who printed it.
    ok, got = _bridge_eval(
        f"b.classify({json.dumps(src)}, 'cd /repo && python tools/x.py', 'unknown')")
    hit = json.loads(got) if ok else None
    if hit and hit.get("category") == "tooling":
        _ok("V-CEPS-BRIDGE-BOOKEND-EXECUTOR-RECORDS",
            "identical text from `python x.py` is still a tooling failure")
    else:
        _fail("V-CEPS-BRIDGE-BOOKEND-EXECUTOR-RECORDS", f"got {got}")

    # BOOKEND TWO. A read command that GENUINELY fails still records: its
    # own failure text is not content it was asked to print.
    ok, got = _bridge_eval(
        "b.classify('grep: /etc/shadow: Permission denied', "
        "'grep -r x /etc/', 'unknown')")
    hit = json.loads(got) if ok else None
    if hit and hit.get("category") == "env":
        _ok("V-CEPS-BRIDGE-BOOKEND-READ-CAN-FAIL",
            "a grep that is denied is still an env failure")
    else:
        _fail("V-CEPS-BRIDGE-BOOKEND-READ-CAN-FAIL", f"got {got}")

    # An explicit success signal is decisive over any text.
    ok, got = _bridge_eval(
        f"b.classify({json.dumps(src)}, 'python tools/x.py', 'no')")
    if ok and json.loads(got) is None:
        _ok("V-CEPS-BRIDGE-SIGNAL-BEATS-TEXT",
            "exit-0 suppresses error-shaped text from an executor")
    else:
        _fail("V-CEPS-BRIDGE-SIGNAL-BEATS-TEXT", f"got {got}")

    # ...and an ABSENT signal must never suppress. Unknown is not false.
    sig_cases = [("{error: 'boom'}", "yes"), ("{exit_code: 0}", "no"),
                 ("{exit_code: 2}", "yes"), ("{}", "unknown"),
                 ("{output: 'x'}", "unknown")]
    bad = []
    for js, want in sig_cases:
        ok, got = _bridge_eval(f"b.failureSignal({js})")
        got = json.loads(got) if ok else f"<err {got}>"
        if got != want:
            bad.append(f"{js} -> {got!r} (want {want!r})")
    if bad:
        _fail("V-CEPS-BRIDGE-UNKNOWN-IS-NOT-FALSE", "; ".join(bad))
    else:
        _ok("V-CEPS-BRIDGE-UNKNOWN-IS-NOT-FALSE",
            f"{len(sig_cases)} signal shapes resolved, absent -> unknown")


def _backfill_gates() -> None:
    """The classifier must not be able to destroy what it cannot read.

    Found by an adversarial pass, not by me: `load()` dropped unparseable
    lines and `--apply` rebuilt the whole file from the survivors, so a torn
    write or a stray BOM would be deleted permanently by the tool whose
    docstring promises it never purges.
    """
    import importlib  # noqa: PLC0415

    bf = importlib.import_module("tools.ceps_backfill_audit")

    tmp = Path(tempfile.mkdtemp(prefix="bf_"))
    saved = bf.EVENTS
    try:
        bf.EVENTS = tmp / "events.jsonl"
        good = json.dumps({"id": "a", "ts": "2026-08-26T10:00:00Z",
                           "category": "tooling", "subsystem": "bash:pytest",
                           "root_cause": "Traceback (most recent call last)"})
        torn = '{"id": "b", "ts": "2026-08-2'          # a half-written line
        bf.EVENTS.write_text(good + "\n" + torn + "\n",
                             encoding="utf-8", newline="\n")

        items = bf.load()
        if len(items) == 2 and any(isinstance(i, str) for i in items):
            _ok("V-CEPS-BACKFILL-KEEPS-UNREADABLE",
                "an unparseable line is loaded as text, not skipped")
        else:
            _fail("V-CEPS-BACKFILL-KEEPS-UNREADABLE", f"loaded {items!r}")

        sys.argv = ["ceps_backfill_audit.py", "--apply"]
        bf.main()
        body = bf.EVENTS.read_text(encoding="utf-8")
        if torn in body:
            _ok("V-CEPS-BACKFILL-NEVER-PURGES",
                "the torn line survives a full --apply rewrite verbatim")
        else:
            _fail("V-CEPS-BACKFILL-NEVER-PURGES",
                  "an unreadable line was destroyed by the rewrite")

        if "admission_status" in body:
            _ok("V-CEPS-BACKFILL-STILL-JUDGES",
                "readable events are still judged alongside preserved text")
        else:
            _fail("V-CEPS-BACKFILL-STILL-JUDGES", "no verdict written")
    finally:
        bf.EVENTS = saved
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    print("V-CEPS-ADMIT -- semantic admission for the CEPS event store")
    _admission_gates()
    _bridge_gates()
    _backfill_gates()
    total = _passes + _fails
    print(f"CEPS_ADMISSION_PASS={_passes}/{total}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if total != EXPECTED_GATES:
        # A count that is merely printed cannot notice a gate that stopped
        # running. Enforcing it means a silently skipped assertion fails
        # the suite instead of shrinking its own denominator.
        print(f"FAIL: {total} gates executed, {EXPECTED_GATES} declared -- "
              "a suite cannot pass by asserting less than it claims")
        return 1
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
