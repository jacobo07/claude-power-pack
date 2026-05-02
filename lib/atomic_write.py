"""Atomic write helper — BL-0014 (MC-SYS-25).

Hardens hook persistence against:
  - Windows ERROR_SHARING_VIOLATION (32) when AV/indexer/Cursor holds the target
  - Partial-write torn files when the hook process is killed mid-write
  - Cross-process races between concurrent Cursor windows on shared files
    (baseline_ledger.jsonl, vault/sleepy/INDEX.md, pending_resume.txt)

Pattern: write to <target>.tmp.<pid>.<rand> in same directory, fsync, os.replace().
os.replace() is atomic on POSIX and on Windows when source+dest share a volume.
On PermissionError (Windows code 32), retry with exponential backoff up to max_retries.

Usage:
    from atomic_write import atomic_write_text, atomic_append_jsonl

    atomic_write_text("/path/to/file.json", json.dumps(data))
    atomic_append_jsonl("/path/to/ledger.jsonl", {"row": 1})

CLI self-test:
    python lib/atomic_write.py --self-test
"""
from __future__ import annotations

import json
import os
import secrets
import sys
import time
from pathlib import Path
from typing import Any

DEFAULT_MAX_RETRIES = 5
INITIAL_BACKOFF_MS = 25
ENCODING = "utf-8"


def _tmp_sibling(target: Path) -> Path:
    return target.with_name(f"{target.name}.tmp.{os.getpid()}.{secrets.token_hex(4)}")


_BINARY_FLAG = getattr(os, "O_BINARY", 0)


def atomic_write_bytes(path: str | os.PathLike[str], data: bytes, max_retries: int = DEFAULT_MAX_RETRIES) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = _tmp_sibling(target)

    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL | _BINARY_FLAG, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)

    last_err: Exception | None = None
    backoff_ms = INITIAL_BACKOFF_MS
    for attempt in range(max_retries):
        try:
            os.replace(str(tmp), str(target))
            return
        except PermissionError as e:
            last_err = e
            time.sleep(backoff_ms / 1000.0)
            backoff_ms *= 2
        except OSError as e:
            if getattr(e, "winerror", None) == 32:
                last_err = e
                time.sleep(backoff_ms / 1000.0)
                backoff_ms *= 2
                continue
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass
            raise

    try:
        tmp.unlink(missing_ok=True)
    except Exception:
        pass
    raise RuntimeError(f"atomic_write: gave up after {max_retries} retries on {target}") from last_err


def atomic_write_text(path: str | os.PathLike[str], text: str, encoding: str = ENCODING, max_retries: int = DEFAULT_MAX_RETRIES) -> None:
    atomic_write_bytes(path, text.encode(encoding), max_retries=max_retries)


def atomic_write_json(path: str | os.PathLike[str], obj: Any, indent: int | None = 2, max_retries: int = DEFAULT_MAX_RETRIES) -> None:
    payload = json.dumps(obj, indent=indent, ensure_ascii=False, sort_keys=False)
    atomic_write_text(path, payload, max_retries=max_retries)


def atomic_append_jsonl(path: str | os.PathLike[str], row: Any, max_retries: int = DEFAULT_MAX_RETRIES) -> None:
    """Append a single JSON object as a line to a JSONL file.

    Read-modify-write under atomic-replace. Safe for low-frequency appenders
    (ledger rows, audit verdicts). NOT a substitute for a proper append-only
    log under high concurrency — for that, prefer a real DB.
    """
    target = Path(path)
    existing = b""
    if target.exists():
        existing = target.read_bytes()
        if existing and not existing.endswith(b"\n"):
            existing += b"\n"
    line = (json.dumps(row, ensure_ascii=False) + "\n").encode(ENCODING)
    atomic_write_bytes(target, existing + line, max_retries=max_retries)


def _self_test() -> int:
    import tempfile

    failures: list[str] = []
    tmpdir = Path(tempfile.mkdtemp(prefix="atomic_write_test_"))
    try:
        f1 = tmpdir / "a.txt"
        atomic_write_text(f1, "hello\n")
        if f1.read_text(encoding=ENCODING) != "hello\n":
            failures.append("text round-trip mismatch")

        f2 = tmpdir / "nested" / "deep" / "b.json"
        atomic_write_json(f2, {"k": 1, "v": "x"})
        if json.loads(f2.read_text(encoding=ENCODING)) != {"k": 1, "v": "x"}:
            failures.append("json round-trip mismatch")

        f3 = tmpdir / "ledger.jsonl"
        atomic_append_jsonl(f3, {"row": 1})
        atomic_append_jsonl(f3, {"row": 2})
        atomic_append_jsonl(f3, {"row": 3})
        lines = f3.read_text(encoding=ENCODING).splitlines()
        if len(lines) != 3 or [json.loads(l)["row"] for l in lines] != [1, 2, 3]:
            failures.append(f"jsonl order mismatch: {lines!r}")

        leftover = list(tmpdir.rglob("*.tmp.*"))
        if leftover:
            failures.append(f"tmp leftover after success: {leftover!r}")

        f4 = tmpdir / "sub" / "c.txt"
        atomic_write_text(f4, "first\n")
        atomic_write_text(f4, "second\n")
        if f4.read_text(encoding=ENCODING) != "second\n":
            failures.append("overwrite mismatch")

    finally:
        try:
            for p in sorted(tmpdir.rglob("*"), reverse=True):
                if p.is_file():
                    p.unlink()
                else:
                    p.rmdir()
            tmpdir.rmdir()
        except Exception:
            pass

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1
    print("atomic_write self-test: PASS (4/4)")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(_self_test())
    print(__doc__)
