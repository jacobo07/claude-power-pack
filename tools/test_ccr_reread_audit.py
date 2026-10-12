"""V-CCRREREAD-*: an unchanged re-read is counted, a changed file is not, a cross-session repeat is counted apart."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ccr_reread_audit as ra  # noqa: E402

passes = fails = 0


def _ok(gate: str, ev: str) -> None:
    global passes
    passes += 1
    print(f"PASS {gate}: {ev}")


def _fail(gate: str, ev: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {ev}")


def session(path: Path, reads: list[tuple[str, str]], calls_after: int = 3) -> None:
    lines = []
    for i, (fp, content) in enumerate(reads):
        lines.append({"type": "assistant", "message": {"id": f"{path.stem}m{i}", "usage": {"input_tokens": 1000},
                      "content": [{"type": "tool_use", "id": f"{path.stem}t{i}", "name": "Read", "input": {"file_path": fp}}]}})
        lines.append({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": f"{path.stem}t{i}", "content": content}]}})
    for j in range(calls_after):
        lines.append({"type": "assistant", "message": {"id": f"{path.stem}z{j}", "usage": {"input_tokens": 1000}, "content": []}})
    path.write_text("\n".join(json.dumps(l) for l in lines), encoding="utf-8")


def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    a = tmp / "s1.jsonl"
    session(a, [("C:\\x\\A.py", "aaaa" * 100), ("c:/x/a.py", "aaaa" * 100), ("C:\\x\\B.py", "v1" * 100), ("C:\\x\\B.py", "v2" * 100)])
    r = ra.audit(tmp, None)
    if r["same_session_rereads"] == 1:
        _ok("V-CCRREREAD-UNCHANGED-COUNTED-ONCE", "A.py read twice unchanged (path case and separator normalized) = 1")
    else:
        _fail("V-CCRREREAD-UNCHANGED-COUNTED-ONCE", json.dumps(r))
    if r["reads"] == 4 and r["same_session_rereads"] == 1:
        _ok("V-CCRREREAD-CHANGED-NOT-COUNTED", "B.py v1 -> v2 is a new read, not a re-read")
    else:
        _fail("V-CCRREREAD-CHANGED-NOT-COUNTED", json.dumps(r))
    b = tmp / "s2.jsonl"
    session(b, [("C:\\x\\B.py", "v2" * 100)])
    import os
    os.utime(b, (a.stat().st_mtime + 10, a.stat().st_mtime + 10))  # s2 is the later session
    r2 = ra.audit(tmp, None)
    if r2["cross_session_rereads"] == 1 and r2["same_session_rereads"] == 1:
        _ok("V-CCRREREAD-CROSS-SESSION-APART", "B.py v2 again in a later session = 1 cross-session")
    else:
        _fail("V-CCRREREAD-CROSS-SESSION-APART", json.dumps(r2))
    if r2["processed"] > 0 and 0 < r2["same_session_share"] < 1:
        _ok("V-CCRREREAD-SHARE-OF-PROCESSED", f"share {r2['same_session_share']}")
    else:
        _fail("V-CCRREREAD-SHARE-OF-PROCESSED", json.dumps(r2))
    print(f"CCRREREAD_PASS={passes}/{passes + fails}  threshold=4/4")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
