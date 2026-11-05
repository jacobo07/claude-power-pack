"""ICC Phase 4 (spec vault/specs/icc-model-call-accounting.md AC1-AC3): done-gate closeout + call report, both poles."""
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402
import mission_spend as ms  # noqa: E402


@pytest.fixture
def world(tmp_path, monkeypatch):
    (tmp_path / "gate.py").write_text("print('ok')\n", encoding="utf-8")
    pkt = tmp_path / "pkt.md"
    pkt.write_text("goal x\ndone-gate: gate.py --check\n", encoding="utf-8")
    rec = {"mission_id": "m-t", "epoch": 3, "state": "RUNNING", "wu_packet": {"path": str(pkt)}}
    calls = []
    monkeypatch.setattr(gm.mb, "execution_root", lambda r: str(tmp_path))
    monkeypatch.setattr(gm.lr, "state_dir", lambda: tmp_path / "state")
    monkeypatch.setattr(gm.lr, "ledger_append", lambda *a, **k: calls.append(("ledger", a[1])))
    monkeypatch.setattr(gm, "transition", lambda mid, **k: calls.append(("transition", k["event"], k["state"])))
    monkeypatch.delenv("GSD_ZERO_MODEL_CLOSE", raising=False)
    return rec, calls


def runner(rc):
    return lambda argv, cwd: types.SimpleNamespace(returncode=rc, stdout="out", stderr="boom")


def test_passing_gate_closes_without_model(world):
    rec, calls = world
    res = gm.try_done_gate_close(rec, 1.0, run=runner(0))
    assert res and res["ok"] and res["model_calls"] == 0
    assert ("transition", "done_gate_completed", gm.COMPLETED) in calls


def test_failing_gate_falls_through_to_model(world):
    rec, calls = world
    assert gm.try_done_gate_close(rec, 1.0, run=runner(1)) is None
    assert not [c for c in calls if c[0] == "transition"]


def test_kill_switch(world, monkeypatch):
    rec, calls = world
    monkeypatch.setenv("GSD_ZERO_MODEL_CLOSE", "0")
    assert gm.try_done_gate_close(rec, 1.0, run=runner(0)) is None
    assert not calls


def test_gate_outside_root_is_ignored(world):
    rec, calls = world
    Path(rec["wu_packet"]["path"]).write_text("done-gate: ../evil.py\n", encoding="utf-8")
    assert gm.try_done_gate_close(rec, 1.0, run=runner(0)) is None
    assert not calls


def test_model_call_report_fraction_and_absence():
    ev = [{"event": "launched"}, {"event": "launched"}, {"event": "done_gate_completed"}, {"event": "noise"}]
    r = ms.model_call_report(ev)
    assert r["total"]["model_epochs"] == 2 and r["total"]["zero_model_closes"] == 1
    assert abs(r["total"]["zero_model_fraction"] - 1 / 3) < 1e-9
    assert ms.model_call_report([])["total"]["zero_model_fraction"] is None
