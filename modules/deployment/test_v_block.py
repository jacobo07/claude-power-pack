"""V-block for the deployment skill.

12 functional V-tests + V-NO-AUTO-PUSH grep check + V-CLOSED-LOOP +
V-TIMING. Each test is self-contained and uses tmpdir; SSH and gh
CLI are mocked via monkeypatch where needed.

Run: python modules/deployment/test_v_block.py
Output: writes _v_block.json + prints PASS/FAIL summary.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from detectors import detect_deploy_target  # noqa: E402
from healthcheck import check_tcp, check_http, run_healthcheck  # noqa: E402
from runners import gh_workflow as gh_workflow_mod  # noqa: E402
from runners import scp_systemd as scp_mod  # noqa: E402
from runners.git_push import run_git_push  # noqa: E402


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_gh_repo(tmp: Path) -> Path:
    (tmp / ".github" / "workflows").mkdir(parents=True)
    (tmp / ".github" / "workflows" / "deploy-vps.yml").write_text(
        "name: Deploy\n'on':\n  workflow_dispatch:\n  push:\n    branches: [main]\n",
        encoding="utf-8",
    )
    return tmp


def _make_git_push_repo(tmp: Path) -> Path:
    (tmp / "deploy").mkdir(parents=True)
    (tmp / "deploy" / "post-receive").write_text("#!/bin/bash\necho deployed\n", encoding="utf-8")
    return tmp


def _make_scp_repo(tmp: Path) -> Path:
    (tmp / "pom.xml").write_text("<project/>\n", encoding="utf-8")
    deploy_dir = tmp / "vault" / "deploy"
    deploy_dir.mkdir(parents=True)
    cfg = {
        "project": "test",
        "mode": "scp-systemd",
        "ssh_alias": "test-host",
        "ssh_key": "~/.ssh/test_key_nonexistent",
        "build_cmd": "mvn package",
        "artefact_glob": "target/*.jar",
        "remote_path": "/srv/test/",
        "post_deploy_cmd": "sudo systemctl restart test",
        "healthcheck": {"kind": "tcp", "target": "127.0.0.1", "port": 25565, "retries": 1, "delay_sec": 0},
    }
    (deploy_dir / "test.json").write_text(json.dumps(cfg), encoding="utf-8")
    return tmp


# ---------------------------------------------------------------------------
# V-DETECT-*
# ---------------------------------------------------------------------------


def v_detect_gh() -> None:
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as td:
        repo = _make_gh_repo(Path(td))
        result = detect_deploy_target(repo)
    dur = (time.monotonic() - t0) * 1000
    passed = result["mode"] == "gh-workflow" and "deploy-vps.yml" in result["evidence"]
    _record("V-DETECT-GH", passed, json.dumps(result), dur)


def v_detect_push() -> None:
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as td:
        repo = _make_git_push_repo(Path(td))
        result = detect_deploy_target(repo)
    dur = (time.monotonic() - t0) * 1000
    passed = result["mode"] == "git-push-to-deploy" and "post-receive" in result["evidence"]
    _record("V-DETECT-PUSH", passed, json.dumps(result), dur)


def v_detect_scp() -> None:
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as td:
        repo = _make_scp_repo(Path(td))
        result = detect_deploy_target(repo)
    dur = (time.monotonic() - t0) * 1000
    passed = result["mode"] == "manual-scp" and "pom.xml" in result["evidence"]
    _record("V-DETECT-SCP", passed, json.dumps(result), dur)


def v_detect_none() -> None:
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as td:
        result = detect_deploy_target(Path(td))
    dur = (time.monotonic() - t0) * 1000
    passed = result["mode"] == "none"
    _record("V-DETECT-NONE", passed, json.dumps(result), dur)


# ---------------------------------------------------------------------------
# V-CEILING-SSH / V-CONFIG-INVALID / V-HEALTHCHECK-MISSING
# ---------------------------------------------------------------------------


def v_ceiling_ssh() -> None:
    t0 = time.monotonic()
    config = {
        "ssh_alias": "test-host",
        "ssh_key": "~/.ssh/__nonexistent_key_for_v_ceiling_test__",
        "build_cmd": "echo build",
        "artefact_glob": "*.jar",
        "remote_path": "/srv/",
        "post_deploy_cmd": "echo restart",
        "healthcheck": {"kind": "tcp", "target": "127.0.0.1", "port": 1, "retries": 1, "delay_sec": 0},
        "project_root": str(REPO_ROOT),
    }
    result = scp_mod.run_scp_systemd(config, dry_run=False)
    dur = (time.monotonic() - t0) * 1000
    passed = (
        result["verdict"] == "ceiling"
        and "SSH key not found" in result["summary"]
        and "__nonexistent_key_for_v_ceiling_test__" in result["receipt"]
    )
    _record("V-CEILING-SSH", passed, json.dumps(result), dur)


def v_config_invalid() -> None:
    t0 = time.monotonic()
    bad_config = {
        "ssh_alias": "x",
        "ssh_key": "~/.ssh/x",
        "build_cmd": "x",
        "artefact_glob": "x",
        "remote_path": "x",
        "post_deploy_cmd": "x",
        "healthcheck": {"kind": "tcp"},
        "db_password": "should-trigger-rejection",
    }
    ok, reason = scp_mod.validate_config(bad_config)
    dur = (time.monotonic() - t0) * 1000
    passed = (not ok) and ("password" in reason.lower())
    _record("V-CONFIG-INVALID", passed, f"ok={ok} reason={reason}", dur)


def v_healthcheck_missing() -> None:
    t0 = time.monotonic()
    bad_config = {
        "ssh_alias": "x",
        "ssh_key": "~/.ssh/x",
        "build_cmd": "x",
        "artefact_glob": "x",
        "remote_path": "x",
        "post_deploy_cmd": "x",
    }
    ok, reason = scp_mod.validate_config(bad_config)
    dur = (time.monotonic() - t0) * 1000
    passed = (not ok) and ("healthcheck" in reason.lower())
    _record("V-HEALTHCHECK-MISSING", passed, f"ok={ok} reason={reason}", dur)


# ---------------------------------------------------------------------------
# V-HEALTHCHECK-NC (tcp success) / V-HEALTHCHECK-FAIL
# ---------------------------------------------------------------------------


def _open_listener() -> tuple[socket.socket, int]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    port = s.getsockname()[1]

    def _accept_loop() -> None:
        try:
            while True:
                conn, _ = s.accept()
                conn.close()
        except OSError:
            return

    th = threading.Thread(target=_accept_loop, daemon=True)
    th.start()
    return s, port


def v_healthcheck_nc() -> None:
    t0 = time.monotonic()
    sock, port = _open_listener()
    try:
        result = check_tcp("127.0.0.1", port, retries=2, delay_sec=0)
    finally:
        sock.close()
    dur = (time.monotonic() - t0) * 1000
    passed = result["ok"] is True and result["attempts"] >= 1
    _record("V-HEALTHCHECK-NC", passed, json.dumps(result), dur)


def v_healthcheck_fail() -> None:
    t0 = time.monotonic()
    result = check_tcp("127.0.0.1", 1, retries=2, delay_sec=0, connect_timeout=0.5)
    dur = (time.monotonic() - t0) * 1000
    passed = result["ok"] is False and "failed" in result["evidence"].lower()
    _record("V-HEALTHCHECK-FAIL", passed, json.dumps(result), dur)


# ---------------------------------------------------------------------------
# V-NO-AUTO-PUSH (grep over runner sources)
# ---------------------------------------------------------------------------


def v_no_auto_push() -> None:
    t0 = time.monotonic()
    runners_dir = HERE / "runners"
    pattern = re.compile(r"(?:^|\s)git\s+push\s+origin\b")
    hits: list[str] = []
    for py in runners_dir.glob("*.py"):
        text = py.read_text(encoding="utf-8")
        for ln_no, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                hits.append(f"{py.name}:{ln_no}:{line.strip()[:80]}")
    deploy_py = HERE / "deploy.py"
    text = deploy_py.read_text(encoding="utf-8")
    for ln_no, line in enumerate(text.splitlines(), 1):
        if pattern.search(line):
            hits.append(f"deploy.py:{ln_no}:{line.strip()[:80]}")
    dur = (time.monotonic() - t0) * 1000
    passed = len(hits) == 0
    _record(
        "V-NO-AUTO-PUSH",
        passed,
        f"hits={len(hits)} files-scanned={len(list(runners_dir.glob('*.py'))) + 1}; details={hits}",
        dur,
    )


# ---------------------------------------------------------------------------
# V-FORBIDDEN-REMOTE (git_push guards against origin)
# ---------------------------------------------------------------------------


def v_forbidden_remote() -> None:
    """Verify the pure forbidden-remote guard (_is_forbidden_remote)
    rejects forbidden names AND forbidden host tokens, and ALLOWS
    legitimate deploy-only remotes (e.g. 'vps204', 'prod', etc).

    Unit-level test of the guard. Independent of subprocess git
    availability on the host (avoids the Windows PATH gap).
    """
    from runners.git_push import _is_forbidden_remote

    t0 = time.monotonic()
    cases = [
        # (name, url, expected_forbidden, why)
        ("origin", "git@github.com:user/repo.git", True, "name=origin AND github.com"),
        ("origin", "kobicraft@vps204:/repo.git", True, "name=origin"),
        ("upstream", "kobicraft@vps204:/repo.git", True, "name=upstream"),
        ("github", "anywhere", True, "name=github"),
        ("vps204", "git@github.com:foo/bar.git", True, "url=github.com"),
        ("vps204", "kobicraft@204.168.166.63:/repo.git", False, "legitimate deploy remote"),
        ("prod", "deploy@example.org:/repo.git", False, "legitimate prod remote"),
    ]
    failures: list[str] = []
    for name, url, expect, why in cases:
        actual, reason = _is_forbidden_remote(name, url)
        if actual != expect:
            failures.append(f"({name},{url}) expect={expect} actual={actual} reason={reason}")
    dur = (time.monotonic() - t0) * 1000
    _record(
        "V-FORBIDDEN-REMOTE",
        len(failures) == 0,
        f"cases={len(cases)} failures={len(failures)}; {failures}",
        dur,
    )


# ---------------------------------------------------------------------------
# V-DOCTRINE-CITE (gh_workflow cites §77 on deploy-vps.yml)
# ---------------------------------------------------------------------------


def v_doctrine_cite() -> None:
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as td:
        repo = _make_gh_repo(Path(td))
        config = {
            "workflow_file": str(repo / ".github" / "workflows" / "deploy-vps.yml"),
            "project_root": str(repo),
            "ref": "main",
        }
        result = gh_workflow_mod.run_gh_workflow(config, dry_run=True)
    dur = (time.monotonic() - t0) * 1000
    cite = (result.get("doctrine_cite") or "").lower()
    passed = "§77" in (result.get("doctrine_cite") or "") and "deploy-vps.yml" in cite
    _record("V-DOCTRINE-CITE", passed, json.dumps(result), dur)


# ---------------------------------------------------------------------------
# V-CLOSED-LOOP
# ---------------------------------------------------------------------------


def v_closed_loop() -> None:
    """Run the dispatcher twice as dry-run; second run surfaces the
    first run's report (if any). The dry-run path does NOT write a
    report, so closed-loop is exercised with a real (mocked) deploy:
    we instead call _previous_deploys directly on a fixture vault/deploys/.
    """
    from deploy import _previous_deploys

    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        deploys_dir = root / "vault" / "deploys"
        deploys_dir.mkdir(parents=True)
        (deploys_dir / "2026-05-24-010101_demo_prod.md").write_text("# r1\n", encoding="utf-8")
        (deploys_dir / "2026-05-24-020202_demo_prod.md").write_text("# r2\n", encoding="utf-8")
        prev = _previous_deploys(root, "demo")
    dur = (time.monotonic() - t0) * 1000
    passed = len(prev) == 2 and prev[0].endswith("020202_demo_prod.md")
    _record("V-CLOSED-LOOP", passed, f"previous_deploys={prev}", dur)


# ---------------------------------------------------------------------------
# V-TIMING (cheap path: 10x detect on tmpdir)
# ---------------------------------------------------------------------------


def v_timing() -> None:
    samples_ms: list[float] = []
    for _ in range(10):
        with tempfile.TemporaryDirectory() as td:
            repo = _make_gh_repo(Path(td))
            t0 = time.monotonic()
            detect_deploy_target(repo)
            samples_ms.append((time.monotonic() - t0) * 1000)
    p05 = statistics.quantiles(samples_ms, n=20)[0]
    p95 = statistics.quantiles(samples_ms, n=20)[18]
    evidence = f"samples={[round(s,1) for s in samples_ms]} p05={p05:.1f}ms p95={p95:.1f}ms"
    passed = p95 < 500.0
    _record("V-TIMING", passed, evidence, p95)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def v_backup_first() -> None:
    """When pre_deploy_backup=true and the backup config is absent or
    invalid, deploy must short-circuit with CEILING. We construct a
    deploy config that has pre_deploy_backup=true but NO matching
    backup config; the dispatcher must refuse the deploy.
    """
    from deploy import deploy as _deploy

    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as td:
        repo = _make_gh_repo(Path(td))
        cfg_dir = repo / "vault" / "deploy"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        cfg = {
            "project": "x",
            "mode": "gh-workflow",
            "workflow_file": ".github/workflows/deploy-vps.yml",
            "ref": "main",
            "healthcheck": {"kind": "tcp", "target": "127.0.0.1", "port": 1, "retries": 1, "delay_sec": 0},
            "pre_deploy_backup": True,
        }
        (cfg_dir / "x.json").write_text(json.dumps(cfg), encoding="utf-8")
        result = _deploy({"project_root": str(repo), "project": "x", "env": "prod", "dry_run": False})
    dur = (time.monotonic() - t0) * 1000
    passed = (
        result["verdict"] == "ceiling"
        and "pre-deploy backup gate FAILED" in result["summary"]
    )
    _record("V-BACKUP-FIRST", passed, json.dumps(result)[:300], dur)


def v_rollback_suggest() -> None:
    """When deploy returns fail|ceiling|deploy-warn, the dispatcher
    surfaces the rollback suggestion line. ALSO grep-asserts that
    deploy.py never imports the rollback module (sec 10 invariant).
    """
    from deploy import deploy as _deploy

    t0 = time.monotonic()
    # CEILING path: re-use v_backup_first's setup (pre_deploy_backup=true,
    # no matching backup config) -> CEILING -> summary must mention /rollback.
    with tempfile.TemporaryDirectory() as td:
        repo = _make_gh_repo(Path(td))
        cfg_dir = repo / "vault" / "deploy"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        cfg = {
            "project": "ceilproj",
            "mode": "gh-workflow",
            "workflow_file": ".github/workflows/deploy-vps.yml",
            "ref": "main",
            "healthcheck": {"kind": "tcp", "target": "127.0.0.1", "port": 1, "retries": 1, "delay_sec": 0},
            "pre_deploy_backup": True,
        }
        (cfg_dir / "ceilproj.json").write_text(json.dumps(cfg), encoding="utf-8")
        result = _deploy({"project_root": str(repo), "project": "ceilproj", "env": "prod", "dry_run": False})

    deploy_py_text = (HERE / "deploy.py").read_text(encoding="utf-8")
    import_hits = re.findall(r"^\s*(?:from|import)\s+.*rollback", deploy_py_text, re.MULTILINE)
    call_hits = re.findall(r"(?<![\w\"\'])rollback\s*\(", deploy_py_text)

    dur = (time.monotonic() - t0) * 1000
    passed = (
        result["verdict"] == "ceiling"
        and "/rollback --project ceilproj" in result["summary"]
        and len(import_hits) == 0
        and len(call_hits) == 0
    )
    _record(
        "V-ROLLBACK-SUGGEST",
        passed,
        f"verdict={result['verdict']}; suggest_in_summary={'/rollback --project ceilproj' in result['summary']}; rollback-imports={len(import_hits)}; rollback-calls={len(call_hits)}",
        dur,
    )


TESTS = [
    v_detect_gh,
    v_detect_push,
    v_detect_scp,
    v_detect_none,
    v_ceiling_ssh,
    v_config_invalid,
    v_healthcheck_missing,
    v_healthcheck_nc,
    v_healthcheck_fail,
    v_no_auto_push,
    v_forbidden_remote,
    v_doctrine_cite,
    v_closed_loop,
    v_backup_first,
    v_rollback_suggest,
    v_timing,
]


def main() -> int:
    for t in TESTS:
        try:
            t()
        except Exception as exc:  # noqa: BLE001
            _record(t.__name__.upper().replace("_", "-"), False, f"exception: {type(exc).__name__}: {exc}", 0)

    passed = sum(1 for r in RESULTS if r["status"] == "PASS")
    total = len(RESULTS)
    out_path = HERE / "_v_block.json"
    out_path.write_text(json.dumps({"passed": passed, "total": total, "results": RESULTS}, indent=2), encoding="utf-8")

    print(f"\n=== V-BLOCK SUMMARY ===")
    for r in RESULTS:
        marker = "PASS" if r["status"] == "PASS" else "FAIL"
        print(f"  [{marker}] {r['test']:<24} ({r['duration_ms']:.1f}ms)")
        if r["status"] != "PASS":
            print(f"    evidence: {r['evidence'][:240]}")
    print(f"\n{passed}/{total} V-tests passed -> {out_path}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
