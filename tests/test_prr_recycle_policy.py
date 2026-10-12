"""V-PRR-RECYCLE-*: decision table, boundary reader and clear markers of modules.prr.recycle_policy."""
import json

from modules.prr import recycle_policy as rp

P0 = 1_000_000.0


def _d(**kw):
    base = dict(proc_start=P0, boundary_ts=None, cleared_ts=None, has_wrapper=True,
                background_tasks=0, session_crons=0)
    base.update(kw)
    return rp.decide(**base)


def test_compact_after_process_start_recycles():
    assert _d(boundary_ts=P0 + 600).action == "RECYCLE"


def test_clear_marker_recycles():
    d = _d(cleared_ts=P0 + 900)
    assert d.action == "RECYCLE" and "clear" in d.reasons[0]


def test_fresh_pane_first_prompt_late_keeps_regression():
    # Measured 2026-10-12: a fresh pane's first transcript row came 85 s after launch.
    # With no compact boundary and no clear marker this must stay KEEP.
    assert _d(boundary_ts=None, cleared_ts=None).action == "KEEP"


def test_resumed_process_after_boundary_keeps_control():
    assert _d(boundary_ts=P0 - 5).action == "KEEP"


def test_background_tasks_pin():
    assert _d(boundary_ts=P0 + 600, background_tasks=2).action == "PIN"


def test_session_crons_pin():
    assert _d(cleared_ts=P0 + 600, session_crons=1).action == "PIN"


def test_no_wrapper_keeps():
    d = _d(boundary_ts=P0 + 600, has_wrapper=False)
    assert d.action == "KEEP" and "kclaude" in d.reasons[-1]


def test_subagent_stop_keeps():
    assert _d(boundary_ts=P0 + 600, is_subagent=True).action == "KEEP"


def test_skew_window_keeps():
    assert _d(boundary_ts=P0 + 1.0).action == "KEEP"


def test_clear_marker_keyed_by_pid_and_create_time(tmp_path, monkeypatch):
    monkeypatch.setattr(rp, "MARKERS", tmp_path / "cleared")
    rp.mark_clear(4242, P0, "sid-a")
    assert rp.cleared_in_process(4242, P0) is not None
    # a recycled pid with a different create_time does not inherit the marker
    assert rp.cleared_in_process(4242, P0 + 3600) is None


def _write(tmp_path, rows):
    p = tmp_path / "s.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return p


def test_last_boundary_found_backwards_across_chunks(tmp_path, monkeypatch):
    monkeypatch.setattr(rp, "TAIL_CHUNK", 64)
    rows = [{"type": "mode"}, {"type": "user", "timestamp": "2026-10-12T10:00:00Z", "pad": "x" * 200},
            {"type": "system", "subtype": "compact_boundary", "timestamp": "2026-10-12T11:00:00Z"},
            {"type": "user", "timestamp": "2026-10-12T11:05:00Z", "pad": "y" * 300},
            {"type": "system", "subtype": "compact_boundary", "timestamp": "2026-10-12T12:00:00Z"},
            {"type": "assistant", "timestamp": "2026-10-12T12:01:00Z", "pad": "z" * 500}]
    p = _write(tmp_path, rows)
    assert rp.last_boundary_ts(p) == rp._ts("2026-10-12T12:00:00Z")


def test_no_boundary_returns_none(tmp_path):
    p = _write(tmp_path, [{"type": "user", "timestamp": "2026-10-12T10:00:00Z"}])
    assert rp.last_boundary_ts(p) is None


def test_mem_fields_never_reports_virtual_size_as_private():
    from types import SimpleNamespace
    from modules.prr.recycle_policy import mem_fields
    linux = mem_fields(SimpleNamespace(rss=128 * 2**20, vms=5484 * 2**20))
    assert linux == {"private_mb": None, "wset_mb": 128.0}
    win = mem_fields(SimpleNamespace(rss=1, vms=9 * 2**30, private=300 * 2**20, wset=200 * 2**20))
    assert win == {"private_mb": 300.0, "wset_mb": 200.0}