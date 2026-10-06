#!/usr/bin/env python
"""V-BR-* gates for tools/boundary_receipts.py, driven by small synthetic transcripts."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import boundary_receipts as br  # noqa: E402

passes = fails = 0
PACKET = "---\nfingerprint: x\nunit: U\n---\n\n## Claims\n\n- c1: first [gates: G1]\n- c2: second [gates: G2]\n\n" \
         "## Context\n\n- src/*.ts\n\n## Acceptance\n\n- pytest tests/test_a.py\n"
USAGE = {"input_tokens": 10, "cache_read_input_tokens": 90, "cache_creation_input_tokens": 0, "output_tokens": 5}


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


class T:
    """Synthetic transcript builder: one assistant call (+ its results) per add()."""

    def __init__(self):
        self.lines, self.n = [], 0

    def add(self, tools=(), text="", dup_line=False):
        self.n += 1
        mid, ts = f"msg_{self.n}", f"2026-10-06T10:00:{self.n:02d}Z"
        blocks = [{"type": "text", "text": text}] if text else []
        results = []
        for i, (name, inp, result, *err) in enumerate(tools):
            tid = f"t{self.n}_{i}"
            blocks.append({"type": "tool_use", "id": tid, "name": name, "input": inp})
            results.append({"type": "tool_result", "tool_use_id": tid, "content": result, "is_error": bool(err and err[0])})
        row = {"type": "assistant", "timestamp": ts,
               "message": {"id": mid, "model": "m", "usage": USAGE, "content": blocks}}
        self.lines.append(json.dumps(row))
        if dup_line:
            self.lines.append(json.dumps(row))
        if results:
            self.lines.append(json.dumps({"type": "user", "timestamp": ts, "message": {"content": results}}))

    def run(self):
        d = Path(tempfile.mkdtemp(prefix="br-test-"))
        (d / "s.jsonl").write_text("\n".join(self.lines), encoding="utf-8")
        (d / "p.md").write_text(PACKET, encoding="utf-8")
        calls, results = br.read_transcripts(br.transcript_paths(d / "s.jsonl"))
        return br.build_receipts(calls, results, br.load_packet(d / "p.md"))


def count(receipts, kind):
    return sum(1 for r in receipts for e in r["events"] if e["kind"] == kind)


def bash(cmd, result, err=False):
    return ("Bash", {"command": cmd}, result, err)


def main() -> int:
    fail_out = "FAILED tests/test_x.py::test_boom - AssertionError: boom\n1 failed"
    r = T()
    for i in range(3):
        r.add([bash(f"pytest -k boom # try {i}", fail_out)])
    rc = r.run()
    check("V-BR-SAME-FAILING-TEST-COUNTS-ONCE", count(rc, "test_transition") == 1 and count(rc, "failure_signature_new") == 1,
          f"{count(rc, 'test_transition')}/{count(rc, 'failure_signature_new')}")

    r = T()
    r.add([bash("run a", "Traceback\nAssertionError at src/foo.py:12:5 token deadbeef01")])
    r.add([bash("run b", "Traceback\nAssertionError at src/foo.py:34:9 token cafebabe99")])
    rc = r.run()
    check("V-BR-SAME-SIGNATURE-DIFFERENT-LINES-ONCE", count(rc, "failure_signature_new") == 1, str(count(rc, "failure_signature_new")))
    r.add([bash("run c", "TypeError: cannot read property of undefined at src/bar.ts:3")])
    rc = r.run()
    check("V-BR-NEW-FAILURE-SIGNATURE-COUNTS", count(rc, "failure_signature_new") == 2, str(count(rc, "failure_signature_new")))

    r = T()
    w = ("Write", {"file_path": "C:/repo/src/a.ts", "content": "const a = 1;"}, "ok")
    r.add([w])
    r.add([w])
    rc = r.run()
    check("V-BR-IDENTICAL-REWRITE-NOT-COUNTED", count(rc, "artifact_delta") == 1, str(count(rc, "artifact_delta")))
    r.add([("Write", {"file_path": "C:/repo/src/a.ts", "content": "const a = 2;"}, "ok")])
    r.add([("Write", {"file_path": "C:/repo/docs/outside.md", "content": "x"}, "ok")])
    rc = r.run()
    check("V-BR-CHANGED-REWRITE-COUNTS-OUTSIDE-GLOB-DOES-NOT", count(rc, "artifact_delta") == 2, str(count(rc, "artifact_delta")))

    r = T()
    r.add([("Read", {"file_path": "a"}, "alpha contents")])
    r.add([("Read", {"file_path": "b"}, "beta contents")])
    r.add([("Read", {"file_path": "a"}, "alpha contents")])
    rc = r.run()
    check("V-BR-NEW-EVIDENCE-COUNTS-REPEAT-DOES-NOT", count(rc, "evidence_new") == 2 and rc[2]["duplicates"] == 1,
          f"{count(rc, 'evidence_new')} dup={rc[2]['duplicates']}")

    r = T()
    r.add([bash("pytest -v", "tests/test_x.py::test_a FAILED")])
    r.add([bash("pytest -v", "tests/test_x.py::test_a PASSED")])
    rc = r.run()
    check("V-BR-TEST-FAIL-TO-PASS-COUNTS", [e["key"] for x in rc for e in x["events"] if e["kind"] == "test_transition"]
          == ["tests/test_x.py::test_a:fail", "tests/test_x.py::test_a:pass"])

    r = T()
    r.add([bash("pytest tests/test_a.py -q", "1 passed in 0.1s")])
    r.add([bash("pytest tests/test_a.py -q", "1 passed in 0.2s")])
    rc = r.run()
    check("V-BR-OBLIGATION-CLOSURE-COUNTS-ONCE", count(rc, "obligation_closed") == 1, str(count(rc, "obligation_closed")))
    r = T()
    r.add([bash("pytest tests/test_a.py -q", "1 failed", True)])
    check("V-BR-FAILED-ACCEPTANCE-NOT-CLOSED-CONTROL", count(r.run(), "obligation_closed") == 0)

    r = T()
    r.add(text="Thinking.\nADVANCED: discriminator: flag set before load")
    r.add(text="ADVANCED: Discriminator -- flag set before load!")
    rc = r.run()
    check("V-BR-ADVANCED-DISCRIMINATOR-ONCE", sum(len(x["advancements"]) for x in rc) == 1 and rc[1]["duplicates"] == 1)

    r = T()
    for i in range(3):
        r.add([("Read", {"file_path": f"f{i}"}, f"content {i}")], dup_line=True)
    rc = r.run()
    check("V-BR-RECEIPT-PER-CALL-NO-LOGGING-TOOLS", len(rc) == 3 and all(x["consumer_claims"] == ["c1", "c2"]
          and x["unit"] == "U" and x["context"] == 100 and x["processed"] == 105 for x in rc), f"{len(rc)}")

    r = T()
    r.add([bash("echo hi", "same output")])
    for _ in range(6):
        r.add([bash("echo hi", "same output")])
    s = br.summarize(r.run())
    check("V-BR-SIX-CALLS-NO-NEW-IDENTITY-ONE-STALL", s["stalls"] == 1 and s["longest_run_without_new_identity"] == 6,
          str(s))
    r2 = T()
    for i in range(6):
        r2.add([("Read", {"file_path": f"f{i}"}, f"unique {i}")])
    s2 = br.summarize(r2.run())
    check("V-BR-FRESH-CALLS-NO-STALL-CONTROL", s2["stalls"] == 0 and s2["semantic_interrupt_density"] == 1.0, str(s2))

    print(f"BR_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
