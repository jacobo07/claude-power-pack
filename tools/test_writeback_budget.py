#!/usr/bin/env python3
"""V-WRITEBACK-* -- the Stop-budget guards on GK-08 session writeback.

Origin (2026-09-15, measured on this host). The dispatcher gives
session_writeback.py 8000 ms and KILLS it at the budget. A killed child never
reaches its receipt writer, so writeback.log contains only the runs that
FINISHED -- and a repo sitting under MAX_MD_FILES that is still too slow
retried, died, and wrote nothing, once per turn, forever, leaving no trace
anywhere that it was happening. The budget detector measured one such repo at
2906 nodes / ~180 s, comfortably under the 4000-file cap.

The existing cap was the right idea in the wrong unit: MAX_MD_FILES bounds FILE
COUNT and the chain enforces TIME. Nothing converts between them.

What these gates pin:
  1. an attempt killed last turn is DETECTED, via the in-flight marker written
     before the slow part -- the receipt it never wrote cannot be read, but the
     marker it wrote before dying can;
  2. the guards SKIP THE EXPENSIVE CALL, not merely relabel the verdict. Every
     case below asserts on whether index_repo was invoked, because a guard that
     returns "throttled" after doing the work has saved nothing;
  3. a skip NEVER lands in writeback.log. `indexer.deferred_repos` takes the
     last row per repo whatever its verdict, so a throttle receipt there would
     supersede a pending deferral and retire real debt in silence. That is a
     regression this change could easily have introduced, and gate
     V-WRITEBACK-SKIP-NOT-IN-DEBT-LOG is what forbids it;
  4. the negative controls -- an empty state, an expired throttle, an expired
     cost deferral, and force -- all still INDEX. Without them a guard that
     refused everything would pass every gate above and look like a fix.
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PP_ROOT / "modules" / "graphify"))

import session_writeback as sw  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS  {gate}  {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL  {gate}  {diagnostic}")


def main() -> int:
    print("== V-WRITEBACK-BUDGET gates ==")

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        state_dir = tmp / "state"
        state_dir.mkdir()
        repo = tmp / "repo"
        repo.mkdir()
        (repo / "a.md").write_text("# a", encoding="utf-8")

        # Isolate every file this module touches, and replace the expensive
        # call with a recorder. The subject here is the GUARD, so the real
        # indexer would only add wall time and a write to the live store.
        sw.gs.state_dir = lambda: state_dir  # type: ignore[assignment]

        calls: list = []
        delay = {"s": 0.0}

        def fake_index(rp, quiet=True):
            calls.append(str(rp))
            if delay["s"]:
                time.sleep(delay["s"])
            return {"ok": True, "repo": str(rp), "nodes": 1,
                    "promoted": 0, "error": None}

        sw.gs.index_repo = fake_index  # type: ignore[assignment]

        key = str(repo.resolve())
        log = state_dir / "writeback.log"
        skips = state_dir / "writeback_skips.log"

        def set_state(rec: dict) -> None:
            (state_dir / "writeback_state.json").write_text(
                json.dumps({key: rec}), encoding="utf-8")

        def reset() -> None:
            calls.clear()
            for f in (log, skips, state_dir / "writeback_state.json"):
                if f.exists():
                    f.unlink()

        now = time.time()

        # ---- V-WRITEBACK-KILLED-RUN-DETECTED -------------------------------
        # The load-bearing one. An in-flight marker older than the budget can
        # only have been left by a run that died; nothing else survives a kill.
        reset()
        set_state({"inflight_at": now - 120, "inflight_pid": 4242})
        v = sw.writeback(repo)
        if v["verdict"] == "deferred" and "killed" in v["reason"] and not calls:
            _ok("V-WRITEBACK-KILLED-RUN-DETECTED",
                "stale in-flight marker -> deferred, indexer not called")
        else:
            _fail("V-WRITEBACK-KILLED-RUN-DETECTED",
                  f"verdict={v.get('verdict')} reason={v.get('reason')} calls={len(calls)}")

        # ---- V-WRITEBACK-KILLED-RUN-IS-RECOVERABLE -------------------------
        # A deferral is only useful if the repairer can discover it, which it
        # does from writeback.log. So THIS verdict must reach that log.
        if v.get("_suppress_log") is not True and "indexer --deferred" in v.get("hint", ""):
            _ok("V-WRITEBACK-KILLED-RUN-IS-RECOVERABLE",
                "debt row is logged and names the repairer")
        else:
            _fail("V-WRITEBACK-KILLED-RUN-IS-RECOVERABLE",
                  f"a killed repo would not be rediscovered: {v}")

        # ---- V-WRITEBACK-CONCURRENT-RUN-SKIPPED ----------------------------
        reset()
        set_state({"inflight_at": now - 5, "inflight_pid": 4242})
        v = sw.writeback(repo)
        if v["verdict"] == "skip" and not calls:
            _ok("V-WRITEBACK-CONCURRENT-RUN-SKIPPED",
                "a fresh marker reads as a live sibling, not a corpse")
        else:
            _fail("V-WRITEBACK-CONCURRENT-RUN-SKIPPED",
                  f"verdict={v.get('verdict')} calls={len(calls)}")

        # ---- V-WRITEBACK-THROTTLED -----------------------------------------
        reset()
        set_state({"last_ok_at": now - 10, "last_ms": 500})
        v = sw.writeback(repo)
        if v["verdict"] == "throttled" and not calls:
            _ok("V-WRITEBACK-THROTTLED", "indexed 10s ago -> no second index")
        else:
            _fail("V-WRITEBACK-THROTTLED",
                  f"verdict={v.get('verdict')} calls={len(calls)}")

        # ---- V-WRITEBACK-SKIP-NOT-IN-DEBT-LOG ------------------------------
        # The regression this change could have introduced. deferred_repos()
        # takes the LAST row per repo from writeback.log whatever its verdict.
        if not log.exists() and skips.exists() and "throttled" in skips.read_text(encoding="utf-8"):
            _ok("V-WRITEBACK-SKIP-NOT-IN-DEBT-LOG",
                "throttle receipt went to the skips log, debt log untouched")
        else:
            _fail("V-WRITEBACK-SKIP-NOT-IN-DEBT-LOG",
                  f"debt_log_exists={log.exists()} skips_exists={skips.exists()}")

        # ---- V-WRITEBACK-COST-DEFERRAL-HOLDS -------------------------------
        reset()
        set_state({"cost_deferred_at": now - 100, "cost_logged": True})
        v = sw.writeback(repo)
        if v["verdict"] == "deferred" and not calls:
            _ok("V-WRITEBACK-COST-DEFERRAL-HOLDS",
                "a repo known not to fit the budget is not retried")
        else:
            _fail("V-WRITEBACK-COST-DEFERRAL-HOLDS",
                  f"verdict={v.get('verdict')} calls={len(calls)}")

        # ---- V-WRITEBACK-COST-DEFERRAL-EXPIRES -----------------------------
        # A one-way door would be its own defect: a repo that shrank could
        # never come back. This is the stale-entry clause in state form.
        reset()
        set_state({"cost_deferred_at": now - (sw.COST_RECHECK_SEC + 60),
                   "cost_logged": True})
        v = sw.writeback(repo)
        if v["verdict"] == "indexed" and len(calls) == 1:
            _ok("V-WRITEBACK-COST-DEFERRAL-EXPIRES",
                f"re-probed after {sw.COST_RECHECK_SEC}s")
        else:
            _fail("V-WRITEBACK-COST-DEFERRAL-EXPIRES",
                  f"verdict={v.get('verdict')} calls={len(calls)}")

        # ---- V-WRITEBACK-FRESH-STATE-INDEXES -------------------------------
        reset()
        v = sw.writeback(repo)
        if v["verdict"] == "indexed" and len(calls) == 1:
            _ok("V-WRITEBACK-FRESH-STATE-INDEXES",
                "no state -> the ordinary path still runs")
        else:
            _fail("V-WRITEBACK-FRESH-STATE-INDEXES",
                  f"verdict={v.get('verdict')} calls={len(calls)}")

        # ---- V-WRITEBACK-ELAPSED-RECORDED ----------------------------------
        if isinstance(v.get("elapsed_ms"), int):
            _ok("V-WRITEBACK-ELAPSED-RECORDED", f"{v['elapsed_ms']}ms on the receipt")
        else:
            _fail("V-WRITEBACK-ELAPSED-RECORDED", f"no elapsed_ms: {v}")

        # ---- V-WRITEBACK-THROTTLE-EXPIRES ----------------------------------
        reset()
        set_state({"last_ok_at": now - (sw.THROTTLE_SEC + 60), "last_ms": 500})
        v = sw.writeback(repo)
        if v["verdict"] == "indexed" and len(calls) == 1:
            _ok("V-WRITEBACK-THROTTLE-EXPIRES", f"older than {sw.THROTTLE_SEC}s -> indexes")
        else:
            _fail("V-WRITEBACK-THROTTLE-EXPIRES",
                  f"verdict={v.get('verdict')} calls={len(calls)}")

        # ---- V-WRITEBACK-FORCE-BYPASSES ------------------------------------
        # The repairer and the tests must be able to reach the work.
        reset()
        set_state({"last_ok_at": now - 10, "last_ms": 500})
        v = sw.writeback(repo, force=True)
        if v["verdict"] == "indexed" and len(calls) == 1:
            _ok("V-WRITEBACK-FORCE-BYPASSES", "force reaches the index past a live throttle")
        else:
            _fail("V-WRITEBACK-FORCE-BYPASSES",
                  f"verdict={v.get('verdict')} calls={len(calls)}")

        # ---- V-WRITEBACK-SLOW-RUN-SELF-DEFERS ------------------------------
        # A run that only finished because nothing killed it must hand itself
        # over. Driven by shrinking the budget rather than by sleeping 6s.
        reset()
        real_budget = sw.STOP_BUDGET_MS
        sw.STOP_BUDGET_MS = 40          # 0.75x = 30ms
        delay["s"] = 0.10               # 100ms > 30ms
        try:
            sw.writeback(repo)
            rec = json.loads((state_dir / "writeback_state.json").read_text(encoding="utf-8"))[key]
            marked = "cost_deferred_at" in rec
            # and the very next turn must now refuse
            calls.clear()
            v2 = sw.writeback(repo)
        finally:
            sw.STOP_BUDGET_MS = real_budget
            delay["s"] = 0.0
        if marked and v2["verdict"] in ("deferred", "throttled") and not calls:
            _ok("V-WRITEBACK-SLOW-RUN-SELF-DEFERS",
                f"over-budget run marked itself; next turn -> {v2['verdict']}, no index")
        else:
            _fail("V-WRITEBACK-SLOW-RUN-SELF-DEFERS",
                  f"marked={marked} next={v2.get('verdict')} calls={len(calls)}")

        # ---- V-WRITEBACK-FAST-RUN-DOES-NOT-SELF-DEFER ----------------------
        # Without this half, marking every run would pass the gate above.
        reset()
        sw.writeback(repo)
        rec = json.loads((state_dir / "writeback_state.json").read_text(encoding="utf-8"))[key]
        if "cost_deferred_at" not in rec and "last_ms" in rec:
            _ok("V-WRITEBACK-FAST-RUN-DOES-NOT-SELF-DEFER",
                "a run inside budget stays on the Stop path")
        else:
            _fail("V-WRITEBACK-FAST-RUN-DOES-NOT-SELF-DEFER",
                  f"a healthy run deferred itself: {rec}")

        # ---- V-WRITEBACK-NEVER-RAISES --------------------------------------
        # Fail-open is the module's absolute contract: it must never block Stop.
        reset()
        (state_dir / "writeback_state.json").write_text("{ not json", encoding="utf-8")
        try:
            v = sw.writeback(repo)
            ok_corrupt = v.get("verdict") in ("indexed", "error", "deferred", "skip", "throttled")
        except Exception as e:  # noqa: BLE001 -- the gate IS "does not raise"
            ok_corrupt = False
            v = {"raised": str(e)}
        if ok_corrupt:
            _ok("V-WRITEBACK-NEVER-RAISES", f"corrupt state degraded to {v['verdict']}")
        else:
            _fail("V-WRITEBACK-NEVER-RAISES", f"raised or returned nonsense: {v}")

    total = _passes + _fails
    print(f"WRITEBACK_BUDGET_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
