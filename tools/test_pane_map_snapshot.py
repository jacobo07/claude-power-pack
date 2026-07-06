"""V-gates for pane_map_snapshot -- hermetic, deterministic (injected `now`).

Run: python tools/test_pane_map_snapshot.py   (exit 0 == all gates pass)
Also importable by pytest (test_* functions assert).
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import pane_map_snapshot as pms  # noqa: E402

T0 = datetime(2026, 7, 6, 12, 0, 0, tzinfo=timezone.utc)

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [PASS] {gate} :: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate} :: {diag}")


def _write_pane_map(state_dir: Path, panes: list[dict]) -> None:
    payload = {"generatedAt": T0.isoformat(), "counts": {}, "panes": panes}
    (state_dir / "pane_map.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    (state_dir / "pane_map.md").write_text("# stub md\n", encoding="utf-8")


def _pane(sid: str, repo: str, tier: str, topic: str = "t") -> dict:
    return {"sessionId": sid, "repo": repo, "tier": tier, "topic": topic}


# --- pytest-visible assertions ----------------------------------------------

def test_snapshot_created_on_change():
    with tempfile.TemporaryDirectory() as d:
        sd = Path(d)
        _write_pane_map(sd, [_pane("a1", "TUA-X", "OPEN-NOW")])
        res = pms.take_snapshot(sd, now=T0)
        assert res["created"] is True, res
        assert (sd / pms.HISTORY_DIRNAME / res["file"]).is_file()


def test_dedup_unchanged_and_too_soon():
    with tempfile.TemporaryDirectory() as d:
        sd = Path(d)
        _write_pane_map(sd, [_pane("a1", "TUA-X", "OPEN-NOW")])
        assert pms.take_snapshot(sd, now=T0)["created"] is True
        # same topology, 20 min later -> unchanged
        r2 = pms.take_snapshot(sd, now=T0 + timedelta(minutes=20))
        assert r2["created"] is False and r2["reason"] == "unchanged", r2
        # changed topology but only 5 min later -> too-soon
        _write_pane_map(sd, [_pane("a1", "TUA-X", "OPEN-NOW"), _pane("b2", "PP", "OPEN-NOW")])
        r3 = pms.take_snapshot(sd, now=T0 + timedelta(minutes=5))
        assert r3["created"] is False and r3["reason"] == "too-soon", r3
        # changed topology AND >=15 min -> new snapshot
        r4 = pms.take_snapshot(sd, now=T0 + timedelta(minutes=16))
        assert r4["created"] is True, r4


def test_retention_prunes_beyond_7_days():
    with tempfile.TemporaryDirectory() as d:
        sd = Path(d)
        _write_pane_map(sd, [_pane("a1", "TUA-X", "OPEN-NOW")])
        pms.take_snapshot(sd, now=T0)
        # 8 days later, a changed map -> old snapshot must be pruned
        _write_pane_map(sd, [_pane("z9", "TUA-X", "OPEN-NOW")])
        res = pms.take_snapshot(sd, now=T0 + timedelta(days=8))
        assert res["created"] is True
        remaining = sorted(p.name for p in (sd / pms.HISTORY_DIRNAME).glob("pane_map_*.json"))
        assert len(remaining) == 1 and remaining[0].endswith(
            (T0 + timedelta(days=8)).strftime(pms.STAMP_FMT) + ".json"), remaining


def test_workspace_registry_records_repos_live():
    with tempfile.TemporaryDirectory() as d:
        sd = Path(d)
        _write_pane_map(sd, [_pane("a1", "TUA-X", "OPEN-NOW"),
                             _pane("b2", "PP", "OPEN-NOW"),
                             _pane("c3", "PP", "RECENT")])  # RECENT excluded
        pms.take_snapshot(sd, now=T0)
        lines = (sd / pms.WORKSPACE_LOG).read_text(encoding="utf-8").splitlines()
        entry = json.loads(lines[-1])
        assert entry["repos_live"] == ["PP", "TUA-X"], entry
        assert entry["pane_count"] == 2, entry


def test_diff_added_closed_tier():
    older = {"panes": [_pane("a1", "TUA-X", "OPEN-NOW"), _pane("b2", "PP", "OPEN-NOW")]}
    newer = {"panes": [_pane("a1", "TUA-X", "ACTIVE"), _pane("c3", "GEO", "OPEN-NOW")]}
    dd = pms.diff_snapshots(older, newer)
    assert [x["sessionId"] for x in dd["added"]] == ["c3"], dd
    assert [x["sessionId"] for x in dd["closed"]] == ["b2"], dd
    assert dd["tier_changed"][0]["sessionId"] == "a1", dd


# --- gate runner (evidence + exit code) -------------------------------------

def _run_gate(gate: str, fn) -> None:
    try:
        fn()
        _ok(gate, "assertions held")
    except AssertionError as exc:
        _fail(gate, f"assert: {exc}")
    except Exception as exc:  # noqa: BLE001
        _fail(gate, f"{exc.__class__.__name__}: {exc}")


def _live_filter_check() -> None:
    """V-LIVE-FILTER (integration, soft): if the live pane_map.json exists, every
    shown pane must carry a non-ARCHIVE tier and no repo's OPEN-NOW count is
    absurd. Skips (does not fail) when the live map is absent -- keeps hermetic."""
    live = pms._default_state_dir() / "pane_map.json"
    if not live.is_file():
        _ok("V-LIVE-FILTER", "skipped (no live pane_map.json)")
        return
    data = pms._read_json(live)
    panes = data.get("panes", [])
    tiers = {p.get("tier") for p in panes}
    if tiers <= {None}:
        _ok("V-LIVE-FILTER", "skipped (live map predates tier field)")
        return
    if tiers - {"OPEN-NOW", "ACTIVE", "RECENT"}:
        _fail("V-LIVE-FILTER", f"ARCHIVE leaked into main map: {sorted(str(t) for t in tiers)}")
        return
    by_repo: dict[str, int] = {}
    for p in pms._open_now(panes):
        by_repo[p.get("repo")] = by_repo.get(p.get("repo"), 0) + 1
    worst = max(by_repo.values(), default=0)
    if worst > 10:
        _fail("V-LIVE-FILTER", f"a repo has {worst} OPEN-NOW panes (>10 implausible)")
        return
    _ok("V-LIVE-FILTER", f"tiers={sorted(tiers)} max OPEN-NOW/repo={worst}")


def main() -> int:
    print("== V-gates: pane_map_snapshot ==")
    _run_gate("V-SNAPSHOT-CREATED", test_snapshot_created_on_change)
    _run_gate("V-SNAPSHOT-DEDUP", test_dedup_unchanged_and_too_soon)
    _run_gate("V-SNAPSHOT-RETAINED", test_retention_prunes_beyond_7_days)
    _run_gate("V-WORKSPACE-SESSIONS", test_workspace_registry_records_repos_live)
    _run_gate("V-DIFF", test_diff_added_closed_tier)
    _live_filter_check()
    total = _passes + _fails
    print(f"PANE_MAP_SNAPSHOT_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
