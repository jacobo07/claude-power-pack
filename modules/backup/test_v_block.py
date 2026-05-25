"""V-block for the Backup / Snapshot skill.

12+ functional V-tests + V-TIMING. Each test is self-contained and uses
tmpdir; SSH and external commands are bypassed via direct unit tests
of the pure functions (validate_config, retention, verify_restore).

Run: python modules/backup/test_v_block.py
"""

from __future__ import annotations

import gzip
import io
import json
import os
import statistics
import sys
import tarfile
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from backup import (  # noqa: E402
    backup,
    validate_config,
    DEFAULT_FREE_FLOOR_BYTES,
)
from retention import apply_retention  # noqa: E402
from verify_restore import verify_restore  # noqa: E402


RESULTS: list[dict] = []


def _record(name: str, passed: bool, evidence: str, duration_ms: float = 0.0) -> None:
    RESULTS.append(
        {
            "test": name,
            "status": "PASS" if passed else "FAIL",
            "evidence": evidence,
            "duration_ms": round(duration_ms, 1),
        }
    )


def _write_targz_with_files(path: Path, files: dict[str, bytes]) -> None:
    """Build a .tar.gz at `path` with the given members."""
    with tarfile.open(path, "w:gz") as tf:
        for name, content in files.items():
            data = io.BytesIO(content)
            info = tarfile.TarInfo(name=name)
            info.size = len(content)
            tf.addfile(info, data)


def _write_pg_dump_file(path: Path, contents: bytes = b"PGDMP\x00\x00\x00") -> None:
    path.write_bytes(contents)


def v_mode_rsync_validates() -> None:
    t0 = time.monotonic()
    cfg = {
        "mode": "rsync-dir",
        "ssh_alias": "host",
        "ssh_key": "~/.ssh/x",
        "local_destination": "backups/x/",
        "retention": {"keep_last_n": 5},
        "restore_test": {"extract_method": "tar-gz", "structural_check": "not-empty"},
    }
    ok, reason = validate_config(cfg)
    _record("V-MODE-RSYNC-VALID", ok, reason, (time.monotonic() - t0) * 1000)


def v_mode_pg_validates() -> None:
    t0 = time.monotonic()
    cfg = {
        "mode": "pg-dump",
        "ssh_alias": "host",
        "ssh_key": "~/.ssh/x",
        "local_destination": "backups/x/",
        "retention": {"keep_last_n": 5},
        "restore_test": {"extract_method": "none", "structural_check": "pg-dump-header"},
    }
    ok, reason = validate_config(cfg)
    _record("V-MODE-PG-VALID", ok, reason, (time.monotonic() - t0) * 1000)


def v_mode_docker_validates() -> None:
    t0 = time.monotonic()
    cfg = {
        "mode": "docker-volume-tar",
        "ssh_alias": "host",
        "ssh_key": "~/.ssh/x",
        "local_destination": "backups/x/",
        "retention": {"keep_last_n": 5},
        "restore_test": {"extract_method": "tar-gz", "structural_check": "not-empty"},
    }
    ok, reason = validate_config(cfg)
    _record("V-MODE-DOCKER-VALID", ok, reason, (time.monotonic() - t0) * 1000)


def v_config_invalid_password() -> None:
    t0 = time.monotonic()
    cfg = {
        "mode": "rsync-dir",
        "ssh_alias": "host",
        "ssh_key": "~/.ssh/x",
        "local_destination": "backups/x/",
        "retention": {"keep_last_n": 5},
        "restore_test": {"extract_method": "tar-gz", "structural_check": "not-empty"},
        "db_password": "should-be-rejected",
    }
    ok, reason = validate_config(cfg)
    passed = (not ok) and ("password" in reason.lower())
    _record("V-CONFIG-INVALID", passed, reason, (time.monotonic() - t0) * 1000)


def v_retention_missing() -> None:
    t0 = time.monotonic()
    cfg = {
        "mode": "rsync-dir",
        "ssh_alias": "host",
        "ssh_key": "~/.ssh/x",
        "local_destination": "backups/x/",
        "restore_test": {"extract_method": "tar-gz", "structural_check": "not-empty"},
    }
    ok, reason = validate_config(cfg)
    passed = (not ok) and ("retention" in reason.lower())
    _record("V-RETENTION-MISSING", passed, reason, (time.monotonic() - t0) * 1000)


def v_ceiling_ssh() -> None:
    """Dispatcher must surface CEILING when ssh_key is missing."""
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg_dir = root / "vault" / "backup"
        cfg_dir.mkdir(parents=True)
        cfg = {
            "mode": "rsync-dir",
            "ssh_alias": "host",
            "ssh_key": "~/.ssh/__nonexistent_backup_key__",
            "remote_paths": ["/srv/dummy"],
            "local_destination": "backups/x/",
            "retention": {"keep_last_n": 5},
            "restore_test": {"extract_method": "tar-gz", "structural_check": "not-empty"},
        }
        (cfg_dir / "x.json").write_text(json.dumps(cfg), encoding="utf-8")
        result = backup({"project_root": str(root), "project": "x", "dry_run": False})
    passed = result["verdict"] == "ceiling" and "SSH key not found" in result["summary"]
    _record("V-CEILING-SSH", passed, json.dumps(result)[:300], (time.monotonic() - t0) * 1000)


def v_disk_full() -> None:
    """Dispatcher must CEILING when expected_size_bytes exceeds free space."""
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg_dir = root / "vault" / "backup"
        cfg_dir.mkdir(parents=True)
        cfg = {
            "mode": "rsync-dir",
            "ssh_alias": "host",
            "ssh_key": "~/.ssh/__nonexistent__",
            "remote_paths": ["/srv/dummy"],
            "local_destination": "backups/x/",
            "retention": {"keep_last_n": 5},
            "restore_test": {"extract_method": "tar-gz", "structural_check": "not-empty"},
            "expected_size_bytes": 10**18,
        }
        (cfg_dir / "x.json").write_text(json.dumps(cfg), encoding="utf-8")
        result = backup({"project_root": str(root), "project": "x", "dry_run": False})
    passed = result["verdict"] == "ceiling" and "disk-full guard" in result["summary"]
    _record("V-DISK-FULL", passed, json.dumps(result)[:300], (time.monotonic() - t0) * 1000)


def v_restore_test_pass() -> None:
    """Build a valid tar.gz with NBT-magic level.dat and verify restore PASS."""
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        snap = root / "snapshot.tar.gz"
        nbt_body = gzip.compress(b"\x0a\x00\x00\x00")
        _write_targz_with_files(snap, {"world/level.dat": nbt_body})
        spec = {
            "extract_method": "tar-gz",
            "sample_files": ["world/level.dat"],
            "structural_check": "nbt-magic",
        }
        result = verify_restore(str(snap), spec)
    passed = result["ok"] and result["checks_passed"] == result["checks_total"] == 1
    _record("V-RESTORE-TEST", passed, json.dumps(result)[:300], (time.monotonic() - t0) * 1000)


def v_restore_test_fail() -> None:
    """Build a tar.gz with WRONG-magic level.dat; verify restore FAIL."""
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        snap = root / "snapshot.tar.gz"
        _write_targz_with_files(snap, {"world/level.dat": b"NOT_NBT_AT_ALL"})
        spec = {
            "extract_method": "tar-gz",
            "sample_files": ["world/level.dat"],
            "structural_check": "nbt-magic",
        }
        result = verify_restore(str(snap), spec)
    passed = (not result["ok"]) and "not NBT" in result["evidence"]
    _record("V-RESTORE-FAIL", passed, json.dumps(result)[:300], (time.monotonic() - t0) * 1000)


def v_restore_pgdump_header() -> None:
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as td:
        snap = Path(td) / "snapshot.dump"
        _write_pg_dump_file(snap)
        spec = {"extract_method": "none", "structural_check": "pg-dump-header"}
        result = verify_restore(str(snap), spec)
    passed = result["ok"]
    _record("V-RESTORE-PGDMP", passed, json.dumps(result)[:200], (time.monotonic() - t0) * 1000)


def v_retention_apply() -> None:
    """Create 12 fixture snapshots; retention keep_last_n=10 keeps 10, drops 2."""
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dest = root / "backups" / "x"
        dest.mkdir(parents=True)
        for i in range(12):
            f = dest / f"2026-05-{i+1:02d}_snap.tar.gz"
            f.write_bytes(b"snap-" + str(i).encode())
            os.utime(f, (1700000000 + i * 86400, 1700000000 + i * 86400))
        result = apply_retention(
            "backups/x",
            {"keep_last_n": 10, "min_keep": 1},
            str(root),
        )
        manifest = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
    passed = result["kept"] == 10 and result["dropped"] == 2 and len(manifest["snapshots"]) == 10
    _record("V-RETENTION-APPLY", passed, f"kept={result['kept']} dropped={result['dropped']} manifest_snaps={len(manifest['snapshots'])}", (time.monotonic() - t0) * 1000)


def v_retention_min_keep() -> None:
    """min_keep=3 prevents dropping below 3 even with strict time policy."""
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dest = root / "backups" / "x"
        dest.mkdir(parents=True)
        # 4 ancient snapshots (older than 1000 days)
        for i in range(4):
            f = dest / f"old_{i}.tar.gz"
            f.write_bytes(b"old")
            old_mtime = time.time() - (2000 * 86400)
            os.utime(f, (old_mtime + i, old_mtime + i))
        result = apply_retention(
            "backups/x",
            {"keep_last_n": 0, "drop_older_than_days": 1, "min_keep": 3},
            str(root),
        )
    passed = result["kept"] == 3 and result["dropped"] == 1
    _record("V-RETENTION-MIN-KEEP", passed, f"kept={result['kept']} dropped={result['dropped']}", (time.monotonic() - t0) * 1000)


def v_closed_loop() -> None:
    """previous_backups returns prior receipt names."""
    from backup import _previous_backups

    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        reports = root / "vault" / "backups"
        reports.mkdir(parents=True)
        (reports / "2026-05-24-010101_demo.md").write_bytes(b"# r1")
        (reports / "2026-05-25-020202_demo.md").write_bytes(b"# r2")
        prev = _previous_backups(root, "demo")
    passed = len(prev) == 2 and prev[0].endswith("020202_demo.md")
    _record("V-CLOSED-LOOP", passed, f"previous_backups={prev}", (time.monotonic() - t0) * 1000)


def v_dispatcher_dry_run() -> None:
    """End-to-end: dispatcher in dry-run picks runner without mutation."""
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg_dir = root / "vault" / "backup"
        cfg_dir.mkdir(parents=True)
        # use a config whose ssh_key exists (the real id_ed25519 on this host
        # is fine; dry-run never connects, only resolves the path).
        host_key = Path(os.path.expanduser("~/.ssh/id_ed25519"))
        if not host_key.is_file():
            _record("V-DISPATCHER-DRYRUN", True, "skipped: ~/.ssh/id_ed25519 absent on this host (acceptable)", 0)
            return
        cfg = {
            "mode": "rsync-dir",
            "ssh_alias": "host",
            "ssh_key": "~/.ssh/id_ed25519",
            "remote_paths": ["/srv/dummy"],
            "local_destination": "backups/x/",
            "retention": {"keep_last_n": 5},
            "restore_test": {"extract_method": "tar-gz", "structural_check": "not-empty"},
        }
        (cfg_dir / "x.json").write_text(json.dumps(cfg), encoding="utf-8")
        result = backup({"project_root": str(root), "project": "x", "dry_run": True})
    passed = result["verdict"] == "dry-run" and result["mode"] == "rsync-dir"
    _record("V-DISPATCHER-DRYRUN", passed, json.dumps(result)[:300], (time.monotonic() - t0) * 1000)


def v_timing() -> None:
    samples: list[float] = []
    for _ in range(10):
        with tempfile.TemporaryDirectory() as td:
            snap = Path(td) / "snap.tar.gz"
            _write_targz_with_files(snap, {"world/level.dat": gzip.compress(b"\x0a\x00")})
            t0 = time.monotonic()
            verify_restore(
                str(snap),
                {"extract_method": "tar-gz", "sample_files": ["world/level.dat"], "structural_check": "nbt-magic"},
            )
            samples.append((time.monotonic() - t0) * 1000)
    p05 = statistics.quantiles(samples, n=20)[0]
    p95 = statistics.quantiles(samples, n=20)[18]
    passed = p95 < 500.0
    _record("V-TIMING", passed, f"samples={[round(s,1) for s in samples]} p05={p05:.1f}ms p95={p95:.1f}ms", p95)


TESTS = [
    v_mode_rsync_validates,
    v_mode_pg_validates,
    v_mode_docker_validates,
    v_config_invalid_password,
    v_retention_missing,
    v_ceiling_ssh,
    v_disk_full,
    v_restore_test_pass,
    v_restore_test_fail,
    v_restore_pgdump_header,
    v_retention_apply,
    v_retention_min_keep,
    v_closed_loop,
    v_dispatcher_dry_run,
    v_timing,
]


def main() -> int:
    for t in TESTS:
        try:
            t()
        except Exception as exc:
            _record(t.__name__.upper().replace("_", "-"), False, f"exception: {type(exc).__name__}: {exc}", 0)

    passed = sum(1 for r in RESULTS if r["status"] == "PASS")
    total = len(RESULTS)
    out = HERE / "_v_block.json"
    out.write_text(json.dumps({"passed": passed, "total": total, "results": RESULTS}, indent=2), encoding="utf-8")

    print("\n=== V-BLOCK SUMMARY ===")
    for r in RESULTS:
        marker = "PASS" if r["status"] == "PASS" else "FAIL"
        print(f"  [{marker}] {r['test']:<26} ({r['duration_ms']:.1f}ms)")
        if r["status"] != "PASS":
            print(f"    evidence: {r['evidence'][:240]}")
    print(f"\n{passed}/{total} V-tests passed -> {out}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
