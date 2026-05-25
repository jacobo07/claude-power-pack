"""V-block tests for the Rollback Axis.

Per vault/specs/rollback-skill.md sec 16, all 15 tests must PASS before
seal. Each test prints PASS or FAIL and accumulates into a final exit code:
0 = 15/15 PASS, non-zero = at least one FAIL.

Run from repo root:
  python modules/rollback/test_v_block.py
"""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import statistics
import sys
import tempfile
import time
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any
from unittest import mock

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent.parent

if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

DEPLOYMENT_DIR = THIS_DIR.parent / "deployment"
if str(DEPLOYMENT_DIR) not in sys.path:
    sys.path.append(str(DEPLOYMENT_DIR))

import rollback as rb_mod  # noqa: E402
from rollback import rollback, validate_config  # noqa: E402
from source_selector import list_verified, select_source  # noqa: E402


RESULTS: list[tuple[str, bool, str]] = []


def record(test_id: str, ok: bool, evidence: str) -> None:
    RESULTS.append((test_id, ok, evidence))
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {test_id}: {evidence}")


def _make_fixture_repo(tmp: Path, *, with_manifest: bool, with_orphan_snapshot: bool = False) -> tuple[Path, Path]:
    """Build a fixture project_root with a backups/<proj>/manifest.json
    (and optionally an orphan snapshot file not in the manifest).
    Returns (project_root, fake_ssh_key_path).
    """
    project = "fixproj"
    backups_dir = tmp / "backups" / project
    backups_dir.mkdir(parents=True, exist_ok=True)

    snap_name = "2026-05-25-120000.tar.gz"
    snap_path = backups_dir / snap_name
    snap_path.write_bytes(b"fixture-bytes-not-a-real-tar-gz")

    if with_manifest:
        manifest = {
            "generated_utc": "2026-05-25T12:00:01+00:00",
            "destination": f"backups/{project}",
            "retention": {"keep_last_n": 5, "drop_older_than_days": 30, "min_keep": 1},
            "snapshots": [
                {
                    "name": snap_name,
                    "size_bytes": snap_path.stat().st_size,
                    "mtime_utc": "2026-05-25T12:00:00+00:00",
                    "sha256": "deadbeef" * 8,
                }
            ],
        }
        (backups_dir / "manifest.json").write_bytes(
            json.dumps(manifest, indent=2).encode("utf-8")
        )

    if with_orphan_snapshot:
        orphan_name = "2026-05-26-000000.tar.gz"
        (backups_dir / orphan_name).write_bytes(b"orphan-not-in-manifest")

    fake_key = tmp / ".ssh" / "fake_key"
    fake_key.parent.mkdir(parents=True, exist_ok=True)
    fake_key.write_text("FAKE PRIVATE KEY")
    return tmp, fake_key


def _write_rollback_config(project_root: Path, project: str, fake_key: Path, mode: str = "rsync-dir", **overrides: Any) -> Path:
    cfg_dir = project_root / "vault" / "rollback"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    base: dict[str, Any] = {
        "project": project,
        "mode": mode,
        "ssh_alias": "fixhost",
        "ssh_key": str(fake_key),
        "healthcheck": {"kind": "tcp", "target": "127.0.0.1", "port": 65530, "retries": 1, "delay_sec": 1},
    }
    if mode == "pg-dump":
        base.update({
            "pg_container": "fix-pg",
            "pg_user": "fix",
            "pg_database": "fix_db",
        })
    if mode == "rsync-dir":
        base.setdefault("post_restore_cmd", "echo restored")
    base.update(overrides)
    cfg = cfg_dir / f"{project}.json"
    cfg.write_bytes(json.dumps(base, indent=2).encode("utf-8"))
    return cfg


# ---------------------------------------------------------------- V-tests


def v_list_verified() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _make_fixture_repo(tmp, with_manifest=True)
        result = list_verified(tmp, "fixproj", limit=5)
        ok = (
            result.get("ok") is True
            and len(result.get("snapshots", [])) == 1
            and result["snapshots"][0]["name"] == "2026-05-25-120000.tar.gz"
        )
        record("V-LIST-VERIFIED", ok, f"snapshots={[s['name'] for s in result.get('snapshots', [])]}")


def v_list_empty() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        result = select_source(tmp, "noproj", None)
        ok = result.get("ok") is False and result.get("reason") == "manifest_absent"
        record("V-LIST-EMPTY", ok, f"reason={result.get('reason')}")


def v_dryrun_rsync() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _, fake_key = _make_fixture_repo(tmp, with_manifest=True)
        _write_rollback_config(tmp, "fixproj", fake_key, mode="rsync-dir")
        result = rollback({"project_root": str(tmp), "project": "fixproj", "dry_run": True})
        ok = (
            result.get("verdict") == "dry-run"
            and result.get("exit_code") == 0
            and "would execute" in (result.get("runner_receipt") or "")
        )
        record("V-DRYRUN-RSYNC", ok, f"verdict={result.get('verdict')} exit={result.get('exit_code')}")


def v_dryrun_pgdump() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _, fake_key = _make_fixture_repo(tmp, with_manifest=True)
        _write_rollback_config(tmp, "fixproj", fake_key, mode="pg-dump")
        result = rollback({"project_root": str(tmp), "project": "fixproj", "dry_run": True})
        receipt = result.get("runner_receipt") or ""
        ok = (
            result.get("verdict") == "dry-run"
            and "pg_restore -c" in receipt
        )
        record("V-DRYRUN-PGDUMP", ok, f"verdict={result.get('verdict')}; pg_restore present={'pg_restore -c' in receipt}")


def v_config_invalid() -> None:
    ok, reason = validate_config({"mode": "rsync-dir", "ssh_alias": "x", "ssh_key": "y", "healthcheck": {}, "db_secret": "oops"})
    record("V-CONFIG-INVALID", ok is False and "secret" in reason, f"reason={reason!r}")


def v_ceiling_ssh_key() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _make_fixture_repo(tmp, with_manifest=True)
        cfg_dir = tmp / "vault" / "rollback"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        cfg = cfg_dir / "fixproj.json"
        cfg.write_bytes(json.dumps({
            "project": "fixproj",
            "mode": "rsync-dir",
            "ssh_alias": "fixhost",
            "ssh_key": str(tmp / "definitely_does_not_exist"),
            "healthcheck": {"kind": "tcp", "target": "127.0.0.1", "port": 65530, "retries": 1, "delay_sec": 1},
        }, indent=2).encode("utf-8"))
        result = rollback({"project_root": str(tmp), "project": "fixproj", "dry_run": True})
        ok = result.get("verdict") == "dry-run"
        # Note: dry-run path doesn't hit the SSH key check inside runner.
        # The ssh-key CEILING fires in non-dry-run. Run that too:
        result2 = rollback({"project_root": str(tmp), "project": "fixproj", "dry_run": False})
        ok = result2.get("verdict") == "ceiling" and result2.get("exit_code") == 4
        record("V-CEILING-SSH-KEY", ok, f"verdict={result2.get('verdict')} exit={result2.get('exit_code')}")


def v_target_not_found() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _, fake_key = _make_fixture_repo(tmp, with_manifest=True)
        _write_rollback_config(tmp, "fixproj", fake_key)
        result = rollback({
            "project_root": str(tmp),
            "project": "fixproj",
            "dry_run": True,
            "target_snapshot": "2099-01-01-000000.tar.gz",
        })
        ok = result.get("verdict") == "ceiling" and "target_unverified" in (result.get("summary") or "")
        record("V-TARGET-NOT-FOUND", ok, f"verdict={result.get('verdict')}; summary~={result.get('summary')!s:.80}")


def v_target_unverified() -> None:
    """Snapshot file exists on disk but NOT in manifest -> CEILING target_unverified."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _, fake_key = _make_fixture_repo(tmp, with_manifest=True, with_orphan_snapshot=True)
        _write_rollback_config(tmp, "fixproj", fake_key)
        result = rollback({
            "project_root": str(tmp),
            "project": "fixproj",
            "dry_run": True,
            "target_snapshot": "2026-05-26-000000.tar.gz",
        })
        ok = result.get("verdict") == "ceiling" and "target_unverified" in (result.get("summary") or "")
        record("V-TARGET-UNVERIFIED", ok, f"verdict={result.get('verdict')}; orphan rejected")


def v_rescue_creates() -> None:
    """rescue_current=True invokes backup runner, writes vault/rescues/<proj>/<ts>.tar.gz."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _, fake_key = _make_fixture_repo(tmp, with_manifest=True)
        _write_rollback_config(tmp, "fixproj", fake_key, mode="rsync-dir")
        # Also need a backup config so _take_rescue can locate paths
        backup_cfg = tmp / "vault" / "backup" / "fixproj.json"
        backup_cfg.parent.mkdir(parents=True, exist_ok=True)
        backup_cfg.write_bytes(json.dumps({
            "project": "fixproj",
            "mode": "rsync-dir",
            "ssh_alias": "fixhost",
            "ssh_key": str(fake_key),
            "remote_paths": ["/tmp/fixtree"],
            "local_destination": "backups/fixproj/",
            "retention": {"keep_last_n": 3, "min_keep": 1},
            "restore_test": {"extract_method": "tar-gz", "sample_files": [], "structural_check": "not-empty"},
        }, indent=2).encode("utf-8"))

        # Mock subprocess.run for ssh+tar inside rescue (the rsync_dir runner uses ssh)
        # and skip the real verify_restore via env opt-out.
        os.environ["CLAUDEPP_BACKUP_SKIP_RESTORE_TEST"] = "1"
        try:
            fake_completed = mock.Mock()
            fake_completed.returncode = 0
            fake_completed.stderr = b""

            def fake_run(cmd, **kwargs):
                # Simulate ssh+tar succeeding: write something into the output file
                stdout = kwargs.get("stdout")
                if hasattr(stdout, "write"):
                    stdout.write(b"FAKE_RESCUE_BYTES" * 100)
                return fake_completed

            with mock.patch("subprocess.run", side_effect=fake_run):
                result = rollback({
                    "project_root": str(tmp),
                    "project": "fixproj",
                    "dry_run": False,
                    "rescue_current": True,
                })
        finally:
            os.environ.pop("CLAUDEPP_BACKUP_SKIP_RESTORE_TEST", None)

        rescues_dir = tmp / "vault" / "rescues" / "fixproj"
        rescue_files = list(rescues_dir.glob("*.tar.gz")) if rescues_dir.is_dir() else []
        ok = len(rescue_files) >= 1
        record("V-RESCUE-CREATES", ok, f"rescue files written={len(rescue_files)}; verdict={result.get('verdict')}")


def v_healthcheck_pass() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _, fake_key = _make_fixture_repo(tmp, with_manifest=True)
        _write_rollback_config(tmp, "fixproj", fake_key, mode="rsync-dir")

        # Make runner appear to pass, healthcheck pass
        with mock.patch.object(rb_mod, "_dispatch_runner", return_value={"ok": True, "verdict": "pass", "summary": "fake pass", "receipt": "fake"}):
            with mock.patch.object(rb_mod, "run_healthcheck", return_value={"ok": True, "kind": "tcp", "attempts": 1, "evidence": "fake hc OK"}):
                result = rollback({
                    "project_root": str(tmp),
                    "project": "fixproj",
                    "dry_run": False,
                })
        ok = result.get("verdict") == "pass" and result.get("exit_code") == 0 and result.get("healthcheck_result", {}).get("ok") is True
        record("V-HEALTHCHECK-PASS", ok, f"verdict={result.get('verdict')}; hc_ok={result.get('healthcheck_result', {}).get('ok')}")


def v_healthcheck_fail() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _, fake_key = _make_fixture_repo(tmp, with_manifest=True)
        _write_rollback_config(tmp, "fixproj", fake_key, mode="rsync-dir")
        with mock.patch.object(rb_mod, "_dispatch_runner", return_value={"ok": True, "verdict": "pass", "summary": "fake pass", "receipt": "fake"}):
            with mock.patch.object(rb_mod, "run_healthcheck", return_value={"ok": False, "kind": "tcp", "attempts": 3, "evidence": "fake hc FAIL"}):
                result = rollback({
                    "project_root": str(tmp),
                    "project": "fixproj",
                    "dry_run": False,
                })
        ok = result.get("verdict") == "rollback-warn" and result.get("exit_code") == 3
        record("V-HEALTHCHECK-FAIL", ok, f"verdict={result.get('verdict')} exit={result.get('exit_code')}")


def v_no_auto() -> None:
    """Grep deploy.py for any call to rollback() function (NOT the literal
    suggestion string). Allowed mention is only inside a string literal.
    """
    deploy_py = REPO_ROOT / "modules" / "deployment" / "deploy.py"
    if not deploy_py.is_file():
        record("V-NO-AUTO", False, f"deploy.py not at {deploy_py}")
        return
    text = deploy_py.read_text(encoding="utf-8")
    # Look for `rollback(` as a call site (not preceded by " or ' which would
    # mean it's inside a string). Match identifier rollback followed by (
    # at start-of-token boundary.
    bad = re.findall(r"(?<![\w\"\'])rollback\s*\(", text)
    ok = len(bad) == 0
    record("V-NO-AUTO", ok, f"call sites of rollback() in deploy.py = {len(bad)}")


def v_doctrine_cite_rollback() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _, fake_key = _make_fixture_repo(tmp, with_manifest=True)
        # Use 'infinityops' to trigger code-rollback path
        _write_rollback_config(tmp, "infinityops", fake_key, mode="pg-dump")
        # Plant a deploy receipt with a HEAD sha for the cite to reference
        deploys = tmp / "vault" / "deploys"
        deploys.mkdir(parents=True, exist_ok=True)
        (deploys / "2026-05-24-120000_infinityops.md").write_bytes(
            b"# Deploy receipt -- infinityops\n\n- Timestamp (UTC): 2026-05-24-120000\n- HEAD: abc1234def5678\n- Mode: gh-workflow\n"
        )
        # Also need a backups/infinityops/manifest.json so source selector passes
        bk = tmp / "backups" / "infinityops"
        bk.mkdir(parents=True, exist_ok=True)
        snap = bk / "2026-05-25-110000.dump"
        snap.write_bytes(b"PGDMP" + b"x" * 32)
        (bk / "manifest.json").write_bytes(json.dumps({
            "generated_utc": "2026-05-25T11:00:01+00:00",
            "destination": "backups/infinityops",
            "retention": {},
            "snapshots": [{"name": snap.name, "size_bytes": snap.stat().st_size, "mtime_utc": "2026-05-25T11:00:00+00:00", "sha256": "x" * 64}],
        }, indent=2).encode("utf-8"))

        buf = io.StringIO()
        with redirect_stdout(buf):
            result = rollback({
                "project_root": str(tmp),
                "project": "infinityops",
                "dry_run": True,
                "include_code_rollback": True,
            })
        printed = buf.getvalue()
        cite_detail = result.get("code_rollback_detail", {}) or {}
        cite_str = cite_detail.get("doctrine_cite", "") or ""
        ok = ("Deploy Sovereignty" in printed) and ("abc1234def5678" in printed) and ("Deploy Sovereignty" in cite_str)
        record("V-DOCTRINE-CITE-ROLLBACK", ok, f"cite_in_stdout={'Deploy Sovereignty' in printed}; ref_in_stdout={'abc1234def5678' in printed}")


def v_closed_loop() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _, fake_key = _make_fixture_repo(tmp, with_manifest=True)
        _write_rollback_config(tmp, "fixproj", fake_key, mode="rsync-dir")
        # Plant existing rollback receipts
        rb_dir = tmp / "vault" / "rollbacks"
        rb_dir.mkdir(parents=True, exist_ok=True)
        for ts in ["2026-05-20-010101", "2026-05-21-020202"]:
            (rb_dir / f"{ts}_fixproj.md").write_bytes(b"# fixture receipt\n")
        result = rollback({"project_root": str(tmp), "project": "fixproj", "dry_run": True})
        prev = result.get("previous_rollbacks") or []
        ok = len(prev) == 2 and all(p.endswith("_fixproj.md") for p in prev)
        record("V-CLOSED-LOOP", ok, f"previous_rollbacks count={len(prev)}")


def v_timing() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _, fake_key = _make_fixture_repo(tmp, with_manifest=True)
        _write_rollback_config(tmp, "fixproj", fake_key, mode="rsync-dir")
        timings_ms: list[float] = []
        for _ in range(7):
            t0 = time.perf_counter()
            rollback({"project_root": str(tmp), "project": "fixproj", "dry_run": True})
            timings_ms.append((time.perf_counter() - t0) * 1000)
        p95 = statistics.quantiles(timings_ms, n=20)[18]  # ~p95
        ok = p95 < 500
        record("V-TIMING", ok, f"p95 dry-run wall-time = {p95:.1f} ms (n=7; budget 500 ms)")


def main() -> int:
    print("V-block tests for Rollback Axis\n" + "=" * 60)

    v_list_verified()
    v_list_empty()
    v_dryrun_rsync()
    v_dryrun_pgdump()
    v_config_invalid()
    v_ceiling_ssh_key()
    v_target_not_found()
    v_target_unverified()
    v_rescue_creates()
    v_healthcheck_pass()
    v_healthcheck_fail()
    v_no_auto()
    v_doctrine_cite_rollback()
    v_closed_loop()
    v_timing()

    print("=" * 60)
    total = len(RESULTS)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    print(f"Result: {passed}/{total} PASS")
    if passed != total:
        print("FAILED tests:")
        for tid, ok, ev in RESULTS:
            if not ok:
                print(f"  {tid}: {ev}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
