"""V-block tests for the Monitoring/Alert Axis.

15 V-gates total (target was 14, V-RETENTION-PURGE split into KEEP +
DROP for clearer evidence). All MUST PASS before seal. Each test is
self-contained in a tempfile.TemporaryDirectory(); none of them hit
the live network -- check_tcp / check_http / check_curl_grep are
mocked at the monitor.run_check boundary.

Run from repo root:
  python tools/test_monitoring.py
"""

from __future__ import annotations

import datetime as _dt
import io
import json
import re
import sys
import tempfile
import threading
import time
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any
from unittest import mock

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
MONITOR_DIR = REPO / "modules" / "monitoring"

if str(MONITOR_DIR) not in sys.path:
    sys.path.insert(0, str(MONITOR_DIR))

import monitor as monitor_mod  # noqa: E402
import alert as alert_mod  # noqa: E402
import observe as observe_mod  # noqa: E402
from monitor import (  # noqa: E402
    MonitorState,
    STATUS_DOWN,
    STATUS_UNKNOWN,
    STATUS_UP,
    TRANS_DOWN_TO_UP,
    TRANS_UP_TO_DOWN,
    evaluate_transition,
    load_config,
    load_state,
    poll_once,
    save_state,
)


RESULTS: list[tuple[str, bool, str]] = []


def _record(name: str, ok: bool, evidence: str) -> None:
    RESULTS.append((name, ok, evidence))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {evidence}")


def _make_fixture(td: Path, *, project: str = "fixproj", hc_type: str = "tcp") -> Path:
    """Build a tempfile repo_root with vault/monitor/<project>.json."""
    cfg_dir = td / "vault" / "monitor"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    hc: dict[str, Any]
    if hc_type == "tcp":
        hc = {"type": "tcp", "host": "127.0.0.1", "port": 65530, "timeout_sec": 1}
    elif hc_type == "http":
        hc = {"type": "http", "url": "http://example.invalid/", "expect_status": 200, "timeout_sec": 1}
    else:
        hc = {"type": "curl_grep", "url": "http://example.invalid/", "grep_pattern": "br.jula", "timeout_sec": 1}
    cfg = {
        "project": project,
        "interval_sec": 30,
        "debounce_consecutive_failures": 3,
        "debounce_consecutive_successes": 2,
        "min_state_duration_sec": 30,
        "alert_on": [TRANS_UP_TO_DOWN, TRANS_DOWN_TO_UP],
        "retention_days": 30,
        "healthcheck": hc,
    }
    (cfg_dir / f"{project}.json").write_bytes(json.dumps(cfg, indent=2).encode("utf-8"))
    return td


# ---------------------------------------------------------------------------
# V-gates
# ---------------------------------------------------------------------------


def v_poll_once_up() -> None:
    """Single check returning ok=True keeps state at UNKNOWN until
    consecutive_successes >= 1 promotes UNKNOWN -> UP (per the
    monitor's UNKNOWN-friendly opening: no debounce against a never-
    polled state). No alert because UNKNOWN -> UP is not in alert_on
    by default contract."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _make_fixture(repo, project="fix1", hc_type="tcp")
        with mock.patch.object(monitor_mod, "run_check", return_value=(True, "tcp OK fake")):
            state, alert_kind = poll_once("fix1", repo_root=repo)
        _record(
            "V-POLL-ONCE-UP",
            state.status == STATUS_UP and alert_kind is None,
            f"status={state.status} alert={alert_kind}",
        )


def v_poll_once_down() -> None:
    """3 consecutive failures => UP_TO_DOWN alert (after first promo to UP)."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _make_fixture(repo, project="fix2", hc_type="tcp")
        # Boot it to UP first.
        with mock.patch.object(monitor_mod, "run_check", return_value=(True, "tcp OK")):
            poll_once("fix2", repo_root=repo)
        # 3 failures.
        alert_kind = None
        with mock.patch.object(monitor_mod, "run_check", return_value=(False, "tcp refused")):
            for _ in range(3):
                state, alert_kind = poll_once("fix2", repo_root=repo)
        _record(
            "V-POLL-ONCE-DOWN",
            state.status == STATUS_DOWN and alert_kind == TRANS_UP_TO_DOWN,
            f"status={state.status} alert={alert_kind} consec_f={state.consecutive_failures}",
        )


def v_debounce_no_alert() -> None:
    """2 failures only (< threshold 3) => state stays UP, no alert."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _make_fixture(repo, project="fix3", hc_type="tcp")
        # Boot to UP.
        with mock.patch.object(monitor_mod, "run_check", return_value=(True, "ok")):
            poll_once("fix3", repo_root=repo)
        alerts: list[str | None] = []
        with mock.patch.object(monitor_mod, "run_check", return_value=(False, "refused")):
            for _ in range(2):
                state, alert_kind = poll_once("fix3", repo_root=repo)
                alerts.append(alert_kind)
        _record(
            "V-DEBOUNCE-NO-ALERT",
            state.status == STATUS_UP and all(a is None for a in alerts),
            f"status={state.status} alerts={alerts}",
        )


def v_debounce_recovery() -> None:
    """DOWN + 2 successes => UP with DOWN_TO_UP alert."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _make_fixture(repo, project="fix4", hc_type="tcp")
        # Boot UP, drop to DOWN.
        with mock.patch.object(monitor_mod, "run_check", return_value=(True, "ok")):
            poll_once("fix4", repo_root=repo)
        with mock.patch.object(monitor_mod, "run_check", return_value=(False, "refused")):
            for _ in range(3):
                poll_once("fix4", repo_root=repo)
        # Now recover with 2 successes.
        with mock.patch.object(monitor_mod, "run_check", return_value=(True, "ok")):
            for _ in range(2):
                state, alert_kind = poll_once("fix4", repo_root=repo)
        _record(
            "V-DEBOUNCE-RECOVERY",
            state.status == STATUS_UP and alert_kind == TRANS_DOWN_TO_UP,
            f"status={state.status} alert={alert_kind}",
        )


def v_state_persist() -> None:
    """save_state -> load_state round-trip preserves all fields."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _make_fixture(repo, project="fix5", hc_type="tcp")
        s_in = MonitorState(
            project="fix5",
            status=STATUS_DOWN,
            last_change_iso="2026-05-26T10:00:00Z",
            consecutive_failures=3,
            consecutive_successes=0,
            last_check_iso="2026-05-26T10:01:00Z",
            last_evidence="fake evidence",
        )
        save_state(s_in, repo_root=repo)
        s_out = load_state("fix5", repo_root=repo)
        _record(
            "V-STATE-PERSIST",
            s_out.status == STATUS_DOWN
            and s_out.consecutive_failures == 3
            and s_out.last_change_iso == "2026-05-26T10:00:00Z"
            and s_out.last_evidence == "fake evidence",
            f"roundtrip ok: status={s_out.status} cf={s_out.consecutive_failures}",
        )


def v_alert_file_created() -> None:
    """emit_alert writes a real markdown file with required fields."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        p = alert_mod.emit_alert(
            "fix6",
            "UP_TO_DOWN",
            "TCP refused mock",
            {"interval_sec": 30, "debounce_consecutive_failures": 3, "debounce_consecutive_successes": 2},
            repo_root=repo,
            print_stdout=False,
        )
        body = p.read_text(encoding="utf-8")
        ok = (
            p.is_file()
            and "Alert: fix6 UP_TO_DOWN" in body
            and "TCP refused mock" in body
            and "/rollback --project fix6" in body
        )
        _record("V-ALERT-FILE-CREATED", ok, f"path={p.name} body_len={len(body)}")


def v_alert_stdout() -> None:
    """emit_alert with print_stdout=True emits a [ALERT] tagged line."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        buf = io.StringIO()
        with redirect_stdout(buf):
            alert_mod.emit_alert(
                "fix7",
                "DOWN_TO_UP",
                "recovered",
                {"interval_sec": 60, "debounce_consecutive_failures": 3, "debounce_consecutive_successes": 2},
                repo_root=repo,
                print_stdout=True,
            )
        out = buf.getvalue()
        _record(
            "V-ALERT-STDOUT",
            "[ALERT]" in out and "fix7" in out and "DOWN_TO_UP" in out,
            f"stdout_chars={len(out)}; tag_present={'[ALERT]' in out}",
        )


def v_no_auto_rollback() -> None:
    """grep monitor.py + observe.py + alert.py for any function-call
    site of rollback()/the rollback dispatcher. The literal '/rollback
    --project X' string IS allowed (it is the suggestion text the
    monitor surfaces to the Owner)."""
    bad_files: list[str] = []
    for fname in ("monitor.py", "observe.py", "alert.py"):
        text = (MONITOR_DIR / fname).read_text(encoding="utf-8")
        # Look for `rollback(` as a call site at any token boundary
        # not inside a string. Negative lookbehind on word/quote chars.
        for m in re.finditer(r"(?<![\w\"\'])rollback\s*\(", text):
            ctx = text[max(0, m.start() - 30) : m.end() + 30]
            bad_files.append(f"{fname}: ...{ctx}...")
    _record(
        "V-NO-AUTO-ROLLBACK",
        len(bad_files) == 0,
        f"call sites of rollback() across monitor/observe/alert: {len(bad_files)}",
    )


def v_config_inherit() -> None:
    """Config with missing optional keys gets defaults from load_config."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        cfg_dir = repo / "vault" / "monitor"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        thin_cfg = {
            "project": "fix8",
            "healthcheck": {"type": "tcp", "host": "x", "port": 1, "timeout_sec": 1},
        }
        (cfg_dir / "fix8.json").write_bytes(json.dumps(thin_cfg).encode("utf-8"))
        loaded = load_config("fix8", repo_root=repo)
        _record(
            "V-CONFIG-INHERIT",
            loaded["debounce_consecutive_failures"] == 3
            and loaded["debounce_consecutive_successes"] == 2
            and loaded["min_state_duration_sec"] == 30
            and loaded["interval_sec"] == 60,
            f"defaults applied: deb_f={loaded['debounce_consecutive_failures']}, deb_s={loaded['debounce_consecutive_successes']}, min_dur={loaded['min_state_duration_sec']}, interval={loaded['interval_sec']}",
        )


def v_once_flag() -> None:
    """--once with mocked check -> exit 0 if UP, prints 'P2.3 health-all absorbed'."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _make_fixture(repo, project="fix9", hc_type="tcp")
        with mock.patch.object(monitor_mod, "run_check", return_value=(True, "ok")):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = observe_mod.main(["--once", "--project", "fix9", "--repo-root", str(repo)])
        out = buf.getvalue()
        _record(
            "V-ONCE-FLAG",
            rc == 0
            and "fix9" in out
            and "P2.3 health-all absorbed" in out,
            f"rc={rc} table_has_project={('fix9' in out)} p23_line={('P2.3' in out)}",
        )


def v_once_multiproject() -> None:
    """--once --project all covers every config in vault/monitor/."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _make_fixture(repo, project="fixA", hc_type="tcp")
        _make_fixture(repo, project="fixB", hc_type="http")
        _make_fixture(repo, project="fixC", hc_type="curl_grep")
        with mock.patch.object(monitor_mod, "run_check", return_value=(True, "ok")):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = observe_mod.main(["--once", "--project", "all", "--repo-root", str(repo)])
        out = buf.getvalue()
        _record(
            "V-ONCE-MULTIPROJECT",
            rc == 0 and all(p in out for p in ("fixA", "fixB", "fixC")),
            f"rc={rc} all 3 projects in table: {all(p in out for p in ('fixA','fixB','fixC'))}",
        )


def v_daemon_no_install() -> None:
    """--daemon prints instructions but never runs schtasks/crontab.

    We verify two things:
      (a) the stdout contains both VPS cron syntax + Windows Task Scheduler instructions.
      (b) by reading the source of cmd_daemon, we grep-assert NO call sites of subprocess
          execute schtasks / crontab / Register-ScheduledTask.
    """
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _make_fixture(repo, project="fixD", hc_type="tcp")
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = observe_mod.main(["--daemon", "--project", "fixD", "--repo-root", str(repo)])
        out = buf.getvalue()

        src = (MONITOR_DIR / "observe.py").read_text(encoding="utf-8")
        bad = re.findall(
            r"subprocess\.\w+\s*\([^)]*(schtasks|crontab|Register-ScheduledTask)",
            src,
        )

        _record(
            "V-DAEMON-NO-INSTALL",
            rc == 0
            and "crontab -e" in out
            and "Task Scheduler" in out
            and len(bad) == 0,
            f"rc={rc} cron+TS in stdout=True install_calls={len(bad)}",
        )


def v_retention_purge_drop() -> None:
    """Old alert receipt (60 days old) is purged at retention_days=30."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        old_ts = (
            _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=60)
        ).strftime("%Y%m%dT%H%M%SZ")
        alert_mod.emit_alert(
            "fixE",
            "UP_TO_DOWN",
            "old",
            {"interval_sec": 30, "debounce_consecutive_failures": 3, "debounce_consecutive_successes": 2},
            repo_root=repo,
            _now_iso=old_ts,
            print_stdout=False,
        )
        purged = alert_mod.purge_old_alerts(retention_days=30, repo_root=repo)
        _record(
            "V-RETENTION-PURGE-DROP",
            purged["dropped"] == 1 and len(list((repo / "vault" / "alerts").glob("*.md"))) == 0,
            f"dropped={purged['dropped']} files={purged['dropped_files']}",
        )


def v_retention_purge_keep() -> None:
    """Recent alert (today) is NOT purged at retention_days=30."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        alert_mod.emit_alert(
            "fixF",
            "UP_TO_DOWN",
            "fresh",
            {"interval_sec": 30, "debounce_consecutive_failures": 3, "debounce_consecutive_successes": 2},
            repo_root=repo,
            print_stdout=False,
        )
        purged = alert_mod.purge_old_alerts(retention_days=30, repo_root=repo)
        remaining = list((repo / "vault" / "alerts").glob("*.md"))
        _record(
            "V-RETENTION-PURGE-KEEP",
            purged["dropped"] == 0 and len(remaining) == 1,
            f"dropped={purged['dropped']} remaining={len(remaining)}",
        )


def v_alerts_list() -> None:
    """list_alerts returns newest-first; --alerts --last N respects N."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        # Plant 3 alerts at different timestamps.
        ts_list = [
            "20260524T120000Z",
            "20260525T120000Z",
            "20260526T120000Z",
        ]
        for ts in ts_list:
            alert_mod.emit_alert(
                "fixG",
                "UP_TO_DOWN",
                f"e@{ts}",
                {"interval_sec": 30, "debounce_consecutive_failures": 3, "debounce_consecutive_successes": 2},
                repo_root=repo,
                _now_iso=ts,
                print_stdout=False,
            )
        entries = alert_mod.list_alerts(repo_root=repo, limit=2)
        _record(
            "V-ALERTS-LIST",
            len(entries) == 2
            and entries[0]["ts_compact"] == "20260526T120000Z"
            and entries[1]["ts_compact"] == "20260525T120000Z",
            f"top-2 newest-first: {[e['ts_compact'] for e in entries]}",
        )


def v_status_no_check() -> None:
    """--status reads disk only; mock check_* is NEVER called."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _make_fixture(repo, project="fixH", hc_type="tcp")
        # Plant a state file.
        s = MonitorState(
            project="fixH",
            status=STATUS_DOWN,
            last_change_iso="2026-05-26T08:00:00Z",
            consecutive_failures=3,
            last_check_iso="2026-05-26T08:00:00Z",
            last_evidence="fake DOWN evidence",
        )
        save_state(s, repo_root=repo)
        # Wire a mock that explodes if called.
        called = {"n": 0}

        def boom(*a, **kw):  # pragma: no cover -- assertion target
            called["n"] += 1
            raise AssertionError("--status MUST NOT invoke run_check")

        with mock.patch.object(monitor_mod, "run_check", side_effect=boom):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = observe_mod.main(["--status", "--project", "fixH", "--repo-root", str(repo)])
        out = buf.getvalue()
        _record(
            "V-STATUS-NO-CHECK",
            rc == 0 and called["n"] == 0 and "fixH" in out and "DOWN" in out,
            f"rc={rc} run_check_calls={called['n']}",
        )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


TESTS = [
    v_poll_once_up,
    v_poll_once_down,
    v_debounce_no_alert,
    v_debounce_recovery,
    v_state_persist,
    v_alert_file_created,
    v_alert_stdout,
    v_no_auto_rollback,
    v_config_inherit,
    v_once_flag,
    v_once_multiproject,
    v_daemon_no_install,
    v_retention_purge_drop,
    v_retention_purge_keep,
    v_alerts_list,
    v_status_no_check,
]


def main() -> int:
    print("V-block tests for Monitoring/Alert Axis\n" + "=" * 60)
    for t in TESTS:
        try:
            t()
        except Exception as exc:  # noqa: BLE001
            _record(t.__name__.upper().replace("_", "-"), False, f"exception: {type(exc).__name__}: {exc}")
    print("=" * 60)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print(f"Result: {passed}/{total} PASS")
    if passed != total:
        print("FAILED:")
        for n, ok, ev in RESULTS:
            if not ok:
                print(f"  {n}: {ev}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
