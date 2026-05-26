#!/usr/bin/env python3
"""M2 -- core gates for TIS logger (Capa 1).

Six V-TIS-* gates. All paths isolated to a tmpdir so the production
vault/token_logs/ is never mutated by the test.

  V-TIS-APPEND      append 1 -> read_log returns 1
  V-TIS-IDEMPOTENT  append 2 different events -> count == 2
  V-TIS-SCHEMA      every dataclass field is present on read-back
  V-TIS-SESSION     get_session_id stable across two calls
  V-TIS-PERSIST     log file actually exists at expected path
  V-TIS-NONZERO     input_tokens=100 survives the round-trip
"""
from __future__ import annotations
import sys
import tempfile
from dataclasses import fields
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tis  # noqa: E402


def _isolate(tmp: Path) -> None:
    tis.LOGS_DIR = tmp / "token_logs"
    tis.SESSION_FILE = tis.LOGS_DIR / ".session_id"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _step(label: str, ok: bool, detail: str = "") -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}  {detail}")
    return ok


def v_tis_append() -> bool:
    sid = tis.get_session_id()
    ev = tis.TokenEvent(sid, _now(), "v-append", "claude-sonnet-4-6",
                        10, 5, 0, 0, "vt-append", "pp")
    tis.append_log(ev)
    entries = tis.read_log(session_id=sid)
    return _step("V-TIS-APPEND", len(entries) == 1,
                 f"entries={len(entries)}")


def v_tis_idempotent() -> bool:
    sid = tis.get_session_id()
    pre = len(tis.read_log(session_id=sid))
    tis.append_log(tis.TokenEvent(sid, _now(), "v-idem-a",
                                  "claude-sonnet-4-6",
                                  11, 6, 0, 0, "a", "pp"))
    tis.append_log(tis.TokenEvent(sid, _now(), "v-idem-b",
                                  "claude-sonnet-4-6",
                                  12, 7, 0, 0, "b", "pp"))
    post = len(tis.read_log(session_id=sid))
    delta = post - pre
    return _step("V-TIS-IDEMPOTENT", delta == 2,
                 f"delta={delta}")


def v_tis_schema() -> bool:
    sid = tis.get_session_id()
    expected = {f.name for f in fields(tis.TokenEvent)}
    entries = tis.read_log(session_id=sid)
    if not entries:
        return _step("V-TIS-SCHEMA", False, "no entries")
    keys = set(entries[-1].keys())
    missing = expected - keys
    return _step("V-TIS-SCHEMA", not missing,
                 f"missing={sorted(missing) if missing else 'none'} "
                 f"keys={len(keys)}")


def v_tis_session() -> bool:
    a = tis.get_session_id()
    b = tis.get_session_id()
    return _step("V-TIS-SESSION", a == b and len(a) == 8,
                 f"a={a} b={b}")


def v_tis_persist() -> bool:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fp = tis.LOGS_DIR / f"{date_str}.jsonl"
    return _step("V-TIS-PERSIST", fp.is_file(),
                 f"path={fp.relative_to(fp.parent.parent.parent) if fp.is_file() else 'MISSING'}")


def v_tis_nonzero() -> bool:
    sid = tis.get_session_id()
    tis.append_log(tis.TokenEvent(sid, _now(), "v-nonzero",
                                  "claude-sonnet-4-6",
                                  100, 50, 25, 5, "vt-nonzero", "pp"))
    entries = [e for e in tis.read_log(session_id=sid)
               if e.get("call_label") == "vt-nonzero"]
    if not entries:
        return _step("V-TIS-NONZERO", False, "entry missing")
    last = entries[-1]
    ok = (last["input_tokens"] == 100 and
          last["output_tokens"] == 50 and
          last["cache_read_tokens"] == 25 and
          last["cache_creation_tokens"] == 5)
    return _step("V-TIS-NONZERO", ok,
                 f"in={last['input_tokens']} out={last['output_tokens']} "
                 f"cr={last['cache_read_tokens']} cc={last['cache_creation_tokens']}")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="tis-core-"))
    _isolate(tmp)
    print(f"[isolate] tmp={tmp}")
    results = []
    results.append(v_tis_append())
    results.append(v_tis_idempotent())
    results.append(v_tis_schema())
    results.append(v_tis_session())
    results.append(v_tis_persist())
    results.append(v_tis_nonzero())
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"\nTIS_CORE_PASS={passed}/{total}  threshold={total}/{total}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
