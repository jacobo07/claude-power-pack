"""V-PRR-CENSUS-* gates: attribution rules of modules.prr.census on synthetic process tables."""
from modules.prr.census import Proc, classify

NOW = 1_000_000.0


def _table():
    return [
        Proc(10, 1, "powershell.exe", NOW - 9000, "powershell -File C:\\Users\\U\\bin\\kclaude.ps1"),
        Proc(11, 10, "claude.exe", NOW - 7200, "", 900.0, 300.0),
        Proc(12, 11, "claude.exe", NOW - 7100, "", 130.0, 40.0),
        Proc(13, 11, "node.exe", NOW - 60, "node C:\\Users\\U\\.claude\\hooks\\hook-dispatcher.js", 30.0, 50.0),
        Proc(20, 5, "cmd.exe", NOW - 4000),
        Proc(21, 20, "claude.exe", NOW - 3600, "", 700.0, 200.0),
        Proc(30, 999, "node.exe", NOW - 86400, "node -e \"require('./.planning/config.json')\"", 4.0, 0.0),
        # PID reuse: ppid 21 exists but was created AFTER this process -> dead parent
        Proc(31, 21, "node.exe", NOW - 90000, "node mcp-server.js", 40.0, 5.0),
    ]


def test_main_and_helper_roles():
    # Arrange
    rep = classify(_table(), now=NOW)
    # Act
    by_pid = {s["pid"]: s for s in rep["sessions"]}
    # Assert
    assert set(by_pid) == {11, 21}
    assert by_pid[11]["descendants"]["claude_helper"]["count"] == 1
    assert by_pid[11]["tree_private_mb"] == 900.0 + 130.0 + 30.0


def test_kclaude_wrapper_is_found_only_for_wrapped_session():
    rep = classify(_table(), now=NOW)
    by_pid = {s["pid"]: s for s in rep["sessions"]}
    assert by_pid[11]["kclaude_wrapper"] == 10
    assert by_pid[21]["kclaude_wrapper"] is None


def test_dead_parent_is_orphan_candidate():
    rep = classify(_table(), now=NOW)
    pids = {o["pid"]: o["role"] for o in rep["orphan_candidates"]}
    assert pids.get(30) == "gsd_probe"


def test_pid_reuse_parent_does_not_count_as_live_parent():
    rep = classify(_table(), now=NOW)
    pids = {o["pid"] for o in rep["orphan_candidates"]}
    assert 31 in pids
    # and the recycled-pid "parent" session does not absorb it
    s21 = next(s for s in rep["sessions"] if s["pid"] == 21)
    assert "mcp" not in s21["descendants"]


def test_live_child_is_not_orphan_control():
    # Control: the same hook process with a live, older parent is NOT a candidate.
    rep = classify(_table(), now=NOW)
    pids = {o["pid"] for o in rep["orphan_candidates"]}
    assert 13 not in pids and 12 not in pids


def test_private_and_wset_are_kept_separate():
    rep = classify(_table(), now=NOW)
    t = rep["totals_by_role"]["claude_main"]
    assert t["private_mb"] == 1600.0
    assert t["wset_mb"] == 500.0


def test_age_correlation_abstains_below_three_sessions():
    rep = classify(_table(), now=NOW)
    assert rep["age_private_pearson"] is None
