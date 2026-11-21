#!/usr/bin/env python3
"""V-READER-* -- every transcript reader survives the record shapes JSONL allows.

SI-01 (Self-Improve assimilation, 2026-11-21): a line that is valid JSON but
not an object (`[1,2]`, `"str"`, `7`) raised AttributeError in
token_ground_truth.parse_session, token_corpus_audit.parse_turns and
conversation_quality_audit.parse_conversation -- json.loads succeeded, so the
JSONDecodeError guard never saw it, and `.get` on a list killed the whole file.
The live corpus held 0 such lines on 2026-11-21 (census of 72,297 lines), so
this is adversarial robustness, not an incident -- which is exactly when it is
cheap to pin.

Each reader is driven from both poles on one hermetic fixture: the hostile
lines must not crash it, AND the one real assistant call next to them must
still be counted (a reader that skipped the whole file would also "not crash").

Run: python tools/test_reader_robustness.py   (exit 0 = all gates PASS)
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

_passes = 0
_fails = 0


def _ok(gate: str, ev: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS  {gate}  {ev}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL  {gate}  {diag}")


def _rec(obj) -> str:
    return json.dumps(obj)


HOSTILE_LINES = [
    "[1, 2]",                      # valid JSON, array
    '"just a string"',             # valid JSON, string
    "7",                           # valid JSON, number
    "null",                        # valid JSON, null
    _rec({"type": "assistant", "message": None}),          # message: null
    _rec({"type": "user", "message": {"content": None}}),  # content: null
    _rec({"type": "assistant", "message": {"content": [None, 3, "x"]}}),
    '{"type": "user", "message": {"role": "us',            # truncated
]

REAL_CALL = _rec({
    "type": "assistant", "requestId": "r1", "timestamp": "2026-11-20T10:00:01Z",
    "message": {"id": "m1", "role": "assistant", "model": "claude-x",
                "usage": {"input_tokens": 3, "output_tokens": 5},
                "content": [{"type": "text", "text": "ok"}]}})
OWNER = _rec({"type": "user", "timestamp": "2026-11-20T10:00:00Z",
              "message": {"role": "user", "content": "hola, revisa esto"}})


def _fixture(tmp: Path) -> Path:
    proj = tmp / "proj"
    proj.mkdir()
    fp = proj / "s1.jsonl"
    fp.write_text("\n".join([OWNER, *HOSTILE_LINES[:-1], REAL_CALL,
                             HOSTILE_LINES[-1]]) + "\n", encoding="utf-8")
    return fp


def main() -> int:
    print("== V-READER gates ==")
    import token_ground_truth as tgt
    import token_corpus_audit as tca
    import conversation_quality_audit as cqa

    with tempfile.TemporaryDirectory() as td:
        fp = _fixture(Path(td))
        cases = [
            ("V-READER-GROUND-TRUTH", lambda: tgt.parse_session(fp),
             lambda r: r and r["turns"] == 1 and r["agg"]["output_tokens"] == 5),
            ("V-READER-CORPUS-AUDIT", lambda: tca.parse_turns(fp),
             lambda r: r and r["n_turns"] == 1),
            ("V-READER-QUALITY-AUDIT", lambda: cqa.parse_conversation(fp),
             lambda r: r and sum(1 for m in r["msgs"] if m["is_owner"]) == 1
             and any(m["role"] == "assistant" and m["out"] == 5 for m in r["msgs"])),
        ]
        for gate, call, good in cases:
            try:
                got = call()
            except Exception as exc:  # noqa: BLE001 -- the gate IS "does not raise"
                _fail(gate, f"raised {type(exc).__name__}: {exc}")
                continue
            if good(got):
                _ok(gate, "hostile lines skipped, the real call still counted")
            else:
                _fail(gate, f"survived but lost the real record: {str(got)[:160]}")

    total = _passes + _fails
    print(f"READER_ROBUSTNESS_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
