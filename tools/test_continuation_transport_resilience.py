"""V-CXTR gates: the Orca CLI default finds the real install, and a crashed run-job is ledgered.

Origin 2026-11-12: ORCA_CLI_DEFAULT named Programs\\OrcaX, the host has Programs\\orca;
every delivery failed and the detached worker's stderr went to DEVNULL.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

STATE = Path(tempfile.mkdtemp(prefix="cxtr-state-"))
os.environ["GSD_LONG_RUN_STATE_DIR"] = str(STATE)

import continuation_transport as ct  # noqa: E402
import gsd_long_run as lr  # noqa: E402

RESULTS: list[bool] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append(ok)
    print(f"  {'PASS' if ok else 'FAIL'} {name}: {detail}")


def _with_localappdata(root: Path) -> Path:
    old = os.environ.get("LOCALAPPDATA")
    os.environ["LOCALAPPDATA"] = str(root)
    try:
        return ct._default_orca_cli()
    finally:
        if old is None:
            os.environ.pop("LOCALAPPDATA", None)
        else:
            os.environ["LOCALAPPDATA"] = old


def gate_default_finds_lowercase_install() -> None:
    root = Path(tempfile.mkdtemp(prefix="cxtr-lad-"))
    cli = root / "Programs" / "orca" / ct._ORCA_CLI_TAIL
    cli.parent.mkdir(parents=True)
    cli.write_text("// cli", encoding="utf-8")
    got = _with_localappdata(root)
    check("V-CXTR-DEFAULT-FINDS-ORCA", got == cli, str(got))


def gate_default_finds_orcax_install() -> None:
    root = Path(tempfile.mkdtemp(prefix="cxtr-lad-"))
    cli = root / "Programs" / "OrcaX" / ct._ORCA_CLI_TAIL
    cli.parent.mkdir(parents=True)
    cli.write_text("// cli", encoding="utf-8")
    got = _with_localappdata(root)
    check("V-CXTR-DEFAULT-FINDS-ORCAX", got == cli, str(got))


def gate_default_without_install_is_deterministic() -> None:
    root = Path(tempfile.mkdtemp(prefix="cxtr-lad-"))
    got = _with_localappdata(root)
    want = root / "Programs" / ct.ORCA_INSTALL_DIRS[0] / ct._ORCA_CLI_TAIL
    check("V-CXTR-DEFAULT-NO-INSTALL", got == want and not got.exists(), str(got))


def gate_run_job_crash_is_ledgered() -> None:
    job = STATE / "bad-job.json"
    job.write_text(json.dumps({"session_id": "cxtr-sid", "kind": "clear"}), encoding="utf-8")
    raised = False
    try:
        ct.run_job(job)
    except KeyError:
        raised = True
    rows = [e for e in lr.ledger_events("cxtr-sid") if e.get("event") == "delivery_job_crashed"]
    check("V-CXTR-CRASH-LEDGERED", raised and len(rows) == 1 and "KeyError" in rows[0].get("error", ""),
          f"raised={raised} rows={rows}")


def gate_unreadable_job_is_ledgered() -> None:
    job = STATE / "missing-job.json"
    raised = False
    try:
        ct.run_job(job)
    except OSError:
        raised = True
    rows = [e for e in lr.ledger_events("unknown") if e.get("event") == "delivery_job_crashed"]
    check("V-CXTR-UNREADABLE-LEDGERED", raised and len(rows) == 1, f"raised={raised} rows={rows}")


def main() -> int:
    gate_default_finds_lowercase_install()
    gate_default_finds_orcax_install()
    gate_default_without_install_is_deterministic()
    gate_run_job_crash_is_ledgered()
    gate_unreadable_job_is_ledgered()
    passed = sum(RESULTS)
    print(f"CXTR_PASS={passed}/{len(RESULTS)}  threshold={len(RESULTS)}/{len(RESULTS)}")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
