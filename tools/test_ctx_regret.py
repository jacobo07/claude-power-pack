"""ICC Phase 6: regret per Work Class (tools/ctx_rent.py regret), on the V-CTXR hand-computed fixture."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctx_rent as cx  # noqa: E402
from test_ctx_rent import session  # noqa: E402


def test_regret_matches_dead_rent_and_splits_classes(tmp_path):
    a, b = tmp_path / "w1.jsonl", tmp_path / "t1.jsonl"
    a.write_text(session(), encoding="utf-8")
    b.write_text(session(late_ref=True), encoding="utf-8")
    r = cx.regret([a, b], {"w1": "background"}, min_calls=3)
    assert set(r["classes"]) == {"worker:background", "top-level"}
    assert r["classes"]["worker:background"]["regret_dead_rent_UPPER_BOUND"] == cx.dead_rent(a)["dead_rent_tokens_UPPER_BOUND"]
    # positive control: a late reference lowers regret, so the instrument can return the other answer
    assert r["classes"]["top-level"]["regret_dead_rent_UPPER_BOUND"] < r["classes"]["worker:background"]["regret_dead_rent_UPPER_BOUND"]


def test_short_transcripts_are_skipped_not_averaged(tmp_path):
    a = tmp_path / "s.jsonl"
    a.write_text(session(), encoding="utf-8")
    r = cx.regret([a], {}, min_calls=50)
    assert r["classes"] == {} and r["skipped"][0]["file"] == "s.jsonl" and r["sessions_measured"] == 0
