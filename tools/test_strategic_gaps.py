#!/usr/bin/env python3
"""test_strategic_gaps.py -- V-gates for the D1-D5 strategic-gaps systems.

Hermetic: every gate builds its own tmp state/repo so re-runs are byte-stable and
independent of the live host. V-* naming per the PP done-gate convention.

Covered so far: D1 (Liveness Ledger), D4 (OWNER_QUEUE activation), D5 (session_active
guard + miner stdout hardening). D2/D3 gates are appended when those sprints land.
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

_PP = Path(__file__).resolve().parents[1]
if str(_PP) not in sys.path:
    sys.path.insert(0, str(_PP))
sys.path.insert(0, str(_PP / "tools"))

_passes = 0
_fails = 0


def _ok(gate, evidence):
    global _passes
    _passes += 1
    print(f"  PASS  {gate}: {evidence}")


def _fail(gate, diag):
    global _fails
    _fails += 1
    print(f"  FAIL  {gate}: {diag}")


# --------------------------------------------------------------------------- #
# D1 -- Liveness Ledger
# --------------------------------------------------------------------------- #
def gate_d1():
    from modules.liveness import liveness_ledger as L

    now = datetime(2026, 7, 10, 16, 0, tzinfo=timezone.utc)

    # V-D1-LEDGER-GENERATED: write_report emits the markdown.
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "liveness_report.md"
        L.write_report(out_path=out, now=now)
        if out.is_file() and "Liveness Ledger" in out.read_text(encoding="utf-8"):
            _ok("V-D1-LEDGER-GENERATED", f"report written ({out.stat().st_size} B)")
        else:
            _fail("V-D1-LEDGER-GENERATED", "report missing or malformed")

    # V-D1-DETECTS-DRIFT: hash mismatch repo vs live -> DRIFTED.
    with tempfile.TemporaryDirectory() as repo, tempfile.TemporaryDirectory() as live:
        (Path(repo) / "hooks").mkdir()
        (Path(repo) / "hooks" / "x.js").write_text("canonical", encoding="utf-8")
        (Path(live) / "x.js").write_text("STALE DIFFERENT", encoding="utf-8")
        reg = [{"id": "x", "surface": "hooks-dir", "desc": "",
                "probe": {"type": "hash-drift", "name": "x.js", "repo_rel": "hooks/x.js"}}]
        rows = L.audit(reg, repo_root=repo, hooks_live_dir=live, now=now)
        if rows[0]["verdict"] == L.DRIFTED:
            _ok("V-D1-DETECTS-DRIFT", rows[0]["evidence"])
        else:
            _fail("V-D1-DETECTS-DRIFT", f"got {rows[0]['verdict']}")

        # in sync -> LIVE
        (Path(live) / "x.js").write_text("canonical", encoding="utf-8")
        rows = L.audit(reg, repo_root=repo, hooks_live_dir=live, now=now)
        if rows[0]["verdict"] == L.LIVE:
            _ok("V-D1-DETECTS-INSYNC", "hash match -> LIVE")
        else:
            _fail("V-D1-DETECTS-INSYNC", f"got {rows[0]['verdict']}")

    # V-D1-DETECTS-ORPHANED: live artifact with no repo source.
    with tempfile.TemporaryDirectory() as repo, tempfile.TemporaryDirectory() as live:
        (Path(live) / "y.js").write_text("orphan code", encoding="utf-8")
        reg = [{"id": "y", "surface": "hooks-dir", "desc": "",
                "probe": {"type": "hash-drift", "name": "y.js", "repo_rel": "hooks/y.js"}}]
        rows = L.audit(reg, repo_root=repo, hooks_live_dir=live, now=now)
        if rows[0]["verdict"] == L.ORPHANED:
            _ok("V-D1-DETECTS-ORPHANED", rows[0]["evidence"])
        else:
            _fail("V-D1-DETECTS-ORPHANED", f"got {rows[0]['verdict']}")

    # V-D1-DETECTS-SILENT: a co12-signal never recorded -> WIRED-BUT-SILENT.
    with tempfile.TemporaryDirectory() as state:
        reg = [{"id": "z", "surface": "stop-chain", "desc": "",
                "probe": {"type": "co12-signal", "kind": "never_emitted_kind"}}]
        rows = L.audit(reg, state_dir=state, now=now)
        if rows[0]["verdict"] == L.SILENT:
            _ok("V-D1-DETECTS-SILENT", rows[0]["evidence"])
        else:
            _fail("V-D1-DETECTS-SILENT", f"got {rows[0]['verdict']}")


# --------------------------------------------------------------------------- #
# D4 -- OWNER_QUEUE activation layer
# --------------------------------------------------------------------------- #
def gate_d4():
    from modules.owner_queue import owner_queue as Q

    now = datetime(2026, 7, 10, 16, 0, tzinfo=timezone.utc)

    # V-D4-INGEST + V-D4-RESOLVE: ingest [PENDING] sections; untag -> resolve.
    with tempfile.TemporaryDirectory() as repo, tempfile.TemporaryDirectory() as state:
        vault = Path(repo) / "vault"
        vault.mkdir()
        md = ("# OWNER_QUEUE\n\n## 1. Do a thing  [PENDING]\n**System:** `hooks/a.js`\n\n"
              "## 2. Untagged section\n- note\n")
        (vault / "OWNER_QUEUE.md").write_text(md, encoding="utf-8")
        r = Q.ingest_vault_queue(repo_root=repo, state_dir=state, now=now)
        pend = Q.pending(state_dir=state)
        if r["ingested"] == 1 and len(pend) == 1 and pend[0]["component"] == "hooks/a.js":
            _ok("V-D4-INGEST", f"ingested 1 vault [PENDING] section")
        else:
            _fail("V-D4-INGEST", f"{r}, pending={len(pend)}")

        (vault / "OWNER_QUEUE.md").write_text(md.replace("[PENDING]", "[DONE]"), encoding="utf-8")
        r2 = Q.ingest_vault_queue(repo_root=repo, state_dir=state, now=now)
        if r2["resolved"] == 1 and not Q.pending(state_dir=state):
            _ok("V-D4-RESOLVE", "untagged section flipped its row done")
        else:
            _fail("V-D4-RESOLVE", f"{r2}, pending={len(Q.pending(state_dir=state))}")

    # V-D4-AUTOCLEAR: a LIVE component closes its row.
    with tempfile.TemporaryDirectory() as state:
        rid = Q.append("wire x", "cmd", component="comp-x", state_dir=state, now=now)
        Q.append("wire y", "cmd", component="comp-y", state_dir=state, now=now)
        closed = Q.autoclear(["comp-x"], state_dir=state, now=now)
        if closed == [rid]:
            _ok("V-D4-AUTOCLEAR", "only the LIVE-component row closed")
        else:
            _fail("V-D4-AUTOCLEAR", f"closed={closed}")

    # V-D4-GRACE: digest surfaces only rows past the grace window.
    with tempfile.TemporaryDirectory() as state:
        old = now - timedelta(hours=48)
        Q.append("old residual", "cmd", state_dir=state, now=old)
        Q.append("fresh residual", "cmd", state_dir=state, now=now)
        dig = Q.sessionstart_digest(state_dir=state, min_age_h=24, now=now)
        if dig and "old residual" in dig and "fresh residual" not in dig:
            _ok("V-D4-GRACE", "only > 24h residual surfaced")
        else:
            _fail("V-D4-GRACE", f"digest={dig!r}")


# --------------------------------------------------------------------------- #
# D5 -- session_active guard + miner stdout hardening
# --------------------------------------------------------------------------- #
def gate_d5():
    import session_active as SA
    import sovereign_miner as SM

    now = datetime(2026, 7, 10, 16, 0, tzinfo=timezone.utc)

    def _mk_transcript(base: Path, sid: str, ts: datetime):
        d = base / "proj"
        d.mkdir(exist_ok=True)
        (d / f"{sid}.jsonl").write_text(
            '{"type":"user","timestamp":"%s"}\n' % ts.isoformat(), encoding="utf-8")

    # V-D5-GUARD-SKIPS: a stale-only corpus -> IDLE (would skip a gated task).
    with tempfile.TemporaryDirectory() as pb:
        base = Path(pb)
        _mk_transcript(base, "a" * 12, now - timedelta(hours=3))
        active = SA.is_session_active(15, proj_base=base, now=now)
        if active is False:
            _ok("V-D5-GUARD-SKIPS", "stale corpus (3h) -> IDLE")
        else:
            _fail("V-D5-GUARD-SKIPS", f"expected IDLE, got active={active}")

        # fresh entry -> ACTIVE
        _mk_transcript(base, "b" * 12, now - timedelta(minutes=2))
        if SA.is_session_active(15, proj_base=base, now=now) is True:
            _ok("V-D5-GUARD-ACTIVE", "fresh entry (2m) -> ACTIVE")
        else:
            _fail("V-D5-GUARD-ACTIVE", "expected ACTIVE")

    # V-D5-GUARD-FAILOPEN: no corpus -> fail-open ACTIVE (never silently stop a task).
    with tempfile.TemporaryDirectory() as pb:
        if SA.is_session_active(15, proj_base=Path(pb), now=now) is True:
            _ok("V-D5-GUARD-FAILOPEN", "empty corpus -> ACTIVE (fail-open)")
        else:
            _fail("V-D5-GUARD-FAILOPEN", "expected fail-open ACTIVE")

    # V-D5-MINER-HARDEN: a broken std stream is redirected, not fatal.
    class _Raising:
        def write(self, x): raise OSError("bad fd")
        def flush(self): raise OSError("bad fd")

    _o, _e = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = _Raising(), _Raising()
        SM._harden_std_streams()
        broken_fixed = not isinstance(sys.stdout, _Raising)
        print("post-harden line")  # must not raise
        sys.stdout.flush()
        buf = io.StringIO()
        sys.stdout = buf
        SM._harden_std_streams()
        print("kept")
        preserved = sys.stdout is buf and buf.getvalue().strip() == "kept"
    finally:
        sys.stdout, sys.stderr = _o, _e
    if broken_fixed and preserved:
        _ok("V-D5-MINER-HARDEN", "broken stream redirected; valid stream preserved")
    else:
        _fail("V-D5-MINER-HARDEN", f"fixed={broken_fixed} preserved={preserved}")


# --------------------------------------------------------------------------- #
# D2 -- Federated FD ledger
# --------------------------------------------------------------------------- #
def gate_d2():
    import json
    from modules.fable_distillation import federated_ledger as F

    with tempfile.TemporaryDirectory() as sd:
        Path(sd, "deposits_a.jsonl").write_text(
            '{"portability_target":"portable"}\n{"portability_target":"frontier-only"}\n',
            encoding="utf-8")
        agg = F.aggregate(state_dir=sd)
        if (agg["repos"] == 1 and agg["global"]["total_assets"] == 2
                and agg["global"]["total_frontier_only"] == 1):
            _ok("V-D2-AGGREGATE", f"1 repo, 2 assets, fdi {agg['per_repo'][0]['fdi']}")
        else:
            _fail("V-D2-AGGREGATE", json.dumps(agg))

    with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as tgt:
        (Path(src) / "vault" / "knowledge_base").mkdir(parents=True)
        (Path(tgt) / "vault" / "knowledge_base").mkdir(parents=True)
        (Path(src) / "vault" / "knowledge_base" / "ukdl-universal.md").write_text(
            "### PROCESS RULE PR-A-001 -- t\nbody\n\n### UKDL TRAP T-X-001 -- local\n"
            "local\n\n### HARD RULE HR-B-002 -- t\nhr\n", encoding="utf-8")
        r = F.propagate_critical(src, [tgt])
        slug = F._slug(tgt)
        prop = (Path(tgt) / "vault" / "knowledge_base" / "UKDL_PROPAGATED.md").read_text(encoding="utf-8")
        if (r[slug]["added"] == 2 and "PR-A-001" in prop and "HR-B-002" in prop
                and "T-X-001" not in prop):
            _ok("V-D2-PROPAGATE", "PR+HR mirrored, repo-local T excluded")
        else:
            _fail("V-D2-PROPAGATE", json.dumps(r))
        r2 = F.propagate_critical(src, [tgt])
        if r2[slug]["added"] == 0 and r2[slug]["skipped"] == 2:
            _ok("V-D2-IDEMPOTENT", "re-run mirrors nothing new")
        else:
            _fail("V-D2-IDEMPOTENT", json.dumps(r2))

    with tempfile.TemporaryDirectory() as sd:
        pp = F.fdi_advisory(r"C:\x\claude-power-pack", state_dir=sd)
        non = F.fdi_advisory(r"C:\x\Other", state_dir=sd)
        if pp is None and non and "FDI 0" in non:
            _ok("V-D2-ADVISORY", "PP silent; non-PP 0-deposit nudges declare-objective")
        else:
            _fail("V-D2-ADVISORY", f"pp={pp!r} non={non!r}")


# --------------------------------------------------------------------------- #
# D3 -- Recall-ROI instrumentation
# --------------------------------------------------------------------------- #
def gate_d3():
    import json
    import time
    from modules.recall_roi import recall_roi as R

    now = time.time()
    with tempfile.TemporaryDirectory() as td:
        # 'used.md' injected long ago AND recently; 'unused.md' never.
        rows = [
            {"module": "__spec__", "spec_path": "vault/specs/used.md", "bytes": 1000,
             "session_id": "s0", "ts": now - 200 * 86400},
            {"module": "__spec__", "spec_path": "vault/specs/used.md", "bytes": 1000,
             "session_id": "s1", "ts": now - 100},
        ]
        Path(td, "jit_usage_s.jsonl").write_text(
            "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

        stats = R.injection_stats(td=td, now=now)
        if stats["total_injections"] == 2 and "used.md" in stats["raw"]:
            _ok("V-D3-METRICS-EXIST", "injections read from the JIT usage log")
        else:
            _fail("V-D3-METRICS-EXIST", json.dumps({k: v for k, v in stats.items() if k != "raw"}))

        # corpus spans 200d >= 90d window (sufficient); used.md recent, unused never.
        r = R.retirement_candidates(kb_items=["used.md", "unused.md"], td=td,
                                    window_days=90, now=now)
        if "unused.md" in r["firm"] and "used.md" not in r["firm"]:
            _ok("V-D3-RETIREMENT-LOGIC", "never-injected item flagged FIRM; used item spared")
        else:
            _fail("V-D3-RETIREMENT-LOGIC", json.dumps(r))

        m = R.co12_metrics(td=td, now=now)
        if m["measured"] and m["kb_injection_count"] == 2:
            _ok("V-D3-CO12-METRICS", "co12_metrics measured (kb_injection_count live)")
        else:
            _fail("V-D3-CO12-METRICS", json.dumps(m))


# --------------------------------------------------------------------------- #
# Baseline import sanity
# --------------------------------------------------------------------------- #
def gate_baseline():
    try:
        from modules.liveness import liveness_ledger  # noqa: F401
        from modules.owner_queue import owner_queue    # noqa: F401
        import session_active                          # noqa: F401
        import sovereign_miner                         # noqa: F401
        import miner_v2                                # noqa: F401
        _ok("V-BASELINE-IMPORTS", "all strategic-gap modules import clean")
    except Exception as e:  # noqa: BLE001
        _fail("V-BASELINE-IMPORTS", repr(e))


def main():
    print("[D1 Liveness Ledger]")
    gate_d1()
    print("[D4 OWNER_QUEUE]")
    gate_d4()
    print("[D5 session_active + miner harden]")
    gate_d5()
    print("[D2 Federated FD ledger]")
    gate_d2()
    print("[D3 Recall-ROI]")
    gate_d3()
    print("[baseline]")
    gate_baseline()
    total = _passes + _fails
    print(f"\nSTRATEGIC_GAPS_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
