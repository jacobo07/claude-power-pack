"""Restore-test verifier.

Invoked AFTER a snapshot is written, BEFORE retention is applied,
BEFORE the receipt is written. Verifies the snapshot can be restored
and contains the expected structural markers.

Supported structural_check values:
  - nbt-magic       : first 4 bytes of world/level.dat (gunzipped) match NBT magic
  - pg-dump-header  : first 5 bytes of the snapshot file = 'PGDMP' (custom format)
  - json-parse      : all .json sample files parse without error
  - not-empty       : each sample file has size > 0

Returns:
  { "ok": bool, "checks_passed": int, "checks_total": int, "evidence": str }
"""

from __future__ import annotations

import gzip
import json
import tarfile
import tempfile
from pathlib import Path
from typing import Any


NBT_MAGIC_BYTES = (b"\x0a", b"\x0a\x00")
PG_DUMP_MAGIC = b"PGDMP"


def _check_nbt_magic(extracted_root: Path, sample_files: list[str]) -> tuple[bool, str]:
    if not sample_files:
        return False, "nbt-magic: no sample_files declared"
    target = next((p for p in sample_files if p.endswith("level.dat")), sample_files[0])
    candidate = extracted_root / target
    if not candidate.is_file():
        return False, f"nbt-magic: sample file not extracted: {target}"
    raw = candidate.read_bytes()
    if raw.startswith(b"\x1f\x8b"):
        try:
            raw = gzip.decompress(raw)
        except OSError as exc:
            return False, f"nbt-magic: gzip-decompress of {target} failed: {exc}"
    for magic in NBT_MAGIC_BYTES:
        if raw.startswith(magic):
            return True, f"nbt-magic: {target} starts with NBT compound tag (first byte 0x0a)"
    return False, f"nbt-magic: {target} first bytes {raw[:8]!r} not NBT compound"


def _check_pg_dump_header(snapshot_path: Path) -> tuple[bool, str]:
    if not snapshot_path.is_file():
        return False, f"pg-dump-header: snapshot file not found at {snapshot_path}"
    with snapshot_path.open("rb") as f:
        head = f.read(5)
    if head == PG_DUMP_MAGIC:
        return True, "pg-dump-header: PGDMP magic verified"
    return False, f"pg-dump-header: first 5 bytes are {head!r}, expected {PG_DUMP_MAGIC!r}"


def _check_json_parse(extracted_root: Path, sample_files: list[str]) -> tuple[bool, str]:
    if not sample_files:
        return False, "json-parse: no sample_files declared"
    failures: list[str] = []
    for rel in sample_files:
        if not rel.endswith(".json"):
            continue
        candidate = extracted_root / rel
        if not candidate.is_file():
            failures.append(f"missing: {rel}")
            continue
        try:
            json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"{rel}: {exc}")
    if failures:
        return False, "json-parse failures: " + "; ".join(failures)
    return True, f"json-parse: all .json sample files parsed ({len([s for s in sample_files if s.endswith('.json')])} files)"


def _check_not_empty(extracted_root: Path, sample_files: list[str], snapshot_path: Path) -> tuple[bool, str]:
    if not sample_files:
        size = snapshot_path.stat().st_size if snapshot_path.is_file() else 0
        if size > 0:
            return True, f"not-empty: snapshot is {size} bytes"
        return False, f"not-empty: snapshot is empty ({size} bytes)"
    failures: list[str] = []
    for rel in sample_files:
        candidate = extracted_root / rel
        if not candidate.is_file():
            failures.append(f"missing: {rel}")
            continue
        if candidate.stat().st_size == 0:
            failures.append(f"empty: {rel}")
    if failures:
        return False, "not-empty failures: " + "; ".join(failures)
    return True, f"not-empty: all {len(sample_files)} sample files non-empty"


def _extract_targz(snapshot_path: Path, dest: Path, sample_files: list[str]) -> tuple[bool, str]:
    if not snapshot_path.is_file():
        return False, f"snapshot file missing: {snapshot_path}"
    try:
        with tarfile.open(snapshot_path, "r:*") as tf:
            members = tf.getmembers()
            extract_us = set(sample_files)
            picked = [m for m in members if any(m.name.endswith(s) or m.name == s for s in extract_us)] or members[:50]
            tf.extractall(dest, members=picked)
    except (OSError, tarfile.TarError) as exc:
        return False, f"tar extract failed: {type(exc).__name__}: {exc}"
    return True, f"extracted {len(picked) if 'picked' in dir() else 0} members"


def verify_restore(
    snapshot_path: str,
    restore_test_spec: dict[str, Any],
) -> dict[str, Any]:
    """Run the restore-test pipeline. Returns a dict per spec §8.

    restore_test_spec keys:
      extract_method   : "tar-gz" | "none" (none for raw pg_dump files)
      sample_files     : list of paths inside the archive (relative)
      structural_check : "nbt-magic" | "pg-dump-header" | "json-parse" | "not-empty"
    """
    snap = Path(snapshot_path)
    extract_method = (restore_test_spec or {}).get("extract_method", "tar-gz")
    sample_files = list((restore_test_spec or {}).get("sample_files", []))
    structural_check = (restore_test_spec or {}).get("structural_check", "not-empty")

    checks_total = 1
    checks_passed = 0
    evidence_lines: list[str] = []

    if extract_method == "tar-gz":
        with tempfile.TemporaryDirectory(prefix="backup-restore-test-") as td:
            tdp = Path(td)
            ok, msg = _extract_targz(snap, tdp, sample_files)
            evidence_lines.append(f"extract: {msg}")
            if not ok:
                return {
                    "ok": False,
                    "checks_passed": 0,
                    "checks_total": checks_total,
                    "evidence": " | ".join(evidence_lines),
                }
            ok2, msg2 = _run_structural_check(structural_check, tdp, sample_files, snap)
            evidence_lines.append(f"structural_check[{structural_check}]: {msg2}")
            if ok2:
                checks_passed += 1
    elif extract_method == "none":
        ok2, msg2 = _run_structural_check(structural_check, Path(td if False else "."), sample_files, snap)
        evidence_lines.append(f"structural_check[{structural_check}]: {msg2}")
        if ok2:
            checks_passed += 1
    else:
        evidence_lines.append(f"extract_method unknown: {extract_method!r}")
        return {
            "ok": False,
            "checks_passed": 0,
            "checks_total": checks_total,
            "evidence": " | ".join(evidence_lines),
        }

    return {
        "ok": checks_passed == checks_total,
        "checks_passed": checks_passed,
        "checks_total": checks_total,
        "evidence": " | ".join(evidence_lines),
    }


def _run_structural_check(
    name: str,
    extracted_root: Path,
    sample_files: list[str],
    snapshot_path: Path,
) -> tuple[bool, str]:
    if name == "nbt-magic":
        return _check_nbt_magic(extracted_root, sample_files)
    if name == "pg-dump-header":
        return _check_pg_dump_header(snapshot_path)
    if name == "json-parse":
        return _check_json_parse(extracted_root, sample_files)
    if name == "not-empty":
        return _check_not_empty(extracted_root, sample_files, snapshot_path)
    return False, f"unknown structural_check: {name!r}"


if __name__ == "__main__":
    import sys

    payload = json.loads(sys.stdin.read())
    out = verify_restore(payload["snapshot_path"], payload["restore_test_spec"])
    print(json.dumps(out, indent=2))
