import json

import pytest

from modules.prr import pgo


def _sample(turn, epoch, anon, hwm=300):
    return {"mode": "policy", "turn": turn, "epoch": epoch, "pid": epoch, "sid": "s",
            "main": {"RssAnon": anon, "VmHWM": hwm}, "tree": {}, "tree_n": 1}


def _receipt(turn, epoch):
    return {"mode": "policy", "event": "receipt", "turn": turn, "epoch": epoch, "pid": epoch, "receipt": {}}


def _epoch(epoch, anon, resume_s=0.4):
    return {"mode": "policy", "event": "epoch", "epoch": epoch, "sid_in": "s", "sid_out": "s",
            "resume_s": resume_s, "main": {"RssAnon": anon, "VmHWM": anon}, "tree": {}, "tree_n": 1}


def _recycled_run():
    # fresh 110; each epoch starts at 120 after the resume at turn 11/21 and ends 9 turns later at 138
    return [_sample(1, 1, 110, 238), _sample(10, 1, 140), _receipt(11, 1), _epoch(2, 120),
            _sample(20, 2, 138, 320), _receipt(21, 2), _epoch(3, 120),
            _sample(30, 3, 138, 330),
            {"fit": {"slope_mb_per_100_turns": 9.9}, "epoch_start_drift": {"n": 2, "mb_per_epoch": 0.0},
             "mode": "policy", "turns": 30, "epochs": 3}]


def test_profile_reads_epoch_start_growth_and_peak_from_a_recycled_run():
    # Arrange
    rows = _recycled_run()
    # Act
    p = pgo.profile_run(rows, workload="bash", plane="gex44", source={"path": "r.jsonl", "sha256": "x"})
    # Assert
    assert p["fresh_anon_mb"] == 110
    assert p["epoch_start_anon_mb"] == 120
    assert p["growth_mb_per_turn"] == 2.0  # (138 - 120) / (20 - 11)
    assert p["peak_hwm_mb"] == 330
    assert p["epochs"] == 3 and p["resume_s_median"] == 0.4


def test_profile_of_an_unrecycled_run_has_no_epoch_start():
    rows = [_sample(1, 1, 110), _sample(100, 1, 160),
            {"fit": {"slope_mb_per_100_turns": 53.3}, "epoch_start_drift": {"n": 0, "mb_per_epoch": None},
             "mode": "policy", "turns": 100, "epochs": 1}]
    p = pgo.profile_run(rows, workload="bash", plane="gex44", source={"path": "n.jsonl", "sha256": "y"})
    assert p["epoch_start_anon_mb"] is None
    assert p["growth_mb_per_turn"] == 0.533


def test_ledger_is_append_only_and_refuses_a_duplicate_source(tmp_path):
    led = tmp_path / "profiles.jsonl"
    p = pgo.profile_run(_recycled_run(), workload="bash", plane="gex44", source={"path": "r", "sha256": "x"})
    assert pgo.append(led, p) is True
    before = led.read_bytes()
    assert pgo.append(led, p) is False
    assert led.read_bytes() == before  # nothing rewritten, nothing added


def test_recommend_admits_with_a_profile_and_refuses_another_plane(tmp_path):
    led = tmp_path / "profiles.jsonl"
    pgo.append(led, pgo.profile_run(_recycled_run(), workload="bash", plane="gex44",
                                    source={"path": "r", "sha256": "x"}))
    profiles = pgo.load(led)
    # Control: the fact exists on this plane, so a cadence is admitted: (150 - 120) / 2.0 = 15 turns.
    ok = pgo.recommend_epoch(profiles, workload="bash", plane="gex44", anon_budget_mb=150)
    assert ok["turns"] == 15 and ok["basis"] == "x"
    # The profile measured 9-turn epochs; 15 turns is past what was observed and must say so.
    assert ok["measured_epoch_turns"] == 9 and ok["extrapolated"] is True
    inside = pgo.recommend_epoch(profiles, workload="bash", plane="gex44", anon_budget_mb=136)
    assert inside["turns"] == 8 and inside["extrapolated"] is False
    # A GEX44 profile never answers for Windows.
    win = pgo.recommend_epoch(profiles, workload="bash", plane="windows", anon_budget_mb=150)
    assert win["turns"] is None and "no recycled profile" in win["reason"]
    # A budget at or under the epoch start cannot be met by any epoch length.
    low = pgo.recommend_epoch(profiles, workload="bash", plane="gex44", anon_budget_mb=120)
    assert low["turns"] is None and "epoch start" in low["reason"]


def test_load_skips_corrupt_lines(tmp_path):
    led = tmp_path / "profiles.jsonl"
    led.write_text('not json\n' + json.dumps({"workload": "bash"}) + "\n", encoding="utf-8")
    assert pgo.load(led) == [{"workload": "bash"}]


def test_profile_refuses_rows_without_samples():
    with pytest.raises(ValueError):
        pgo.profile_run([{"fit": {}}], workload="bash", plane="gex44", source={"path": "e", "sha256": "z"})
