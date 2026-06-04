#!/usr/bin/env python3
"""test_ram_optimization.py - V-gates for the RAM Optimization Sprint.

Covers (2026-06-04):
  * C1  registry.prune_stale       -- removes dead/stale >24h, keeps active
  * C2  walk_cache_guard           -- truncates oversize/stale, spares others
  * B1  ram_guard.evaluate         -- ok / warn / critical / no-measurement
  * A1  bench_ram_footprint        -- live PP-overhead <= SCS C34 ceiling
                                      (ADVISORY when PowerShell/psutil absent)

Hermetic: every mutating test writes to a tempfile / temp dir and monkey-
patches the module global, so re-running the suite back-to-back is
deterministic (no global ~/.claude writes, no time-window coupling).

V-gate convention: _ok / _fail, DOMAIN_PASS=passes/total, exit 0 iff
fails == 0. Wired into verify_spp.py (ram-optimization row) and picked up
automatically by bench_all.py vgate_suites (tools/test_*.py glob).
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

OVERHEAD_CEIL_MB = 300
_SECONDS_PER_DAY = 86400

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [OK]   {gate}: {evidence}")


def _fail(gate: str, detail: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate}: {detail}")


def _adv(gate: str, detail: str) -> None:
    # Advisory: neither pass nor fail (e.g. measurement unavailable in CI).
    print(f"  [ADV]  {gate}: {detail}")


# --------------------------------------------------------------------------
# C1 -- PaneRegistry.prune_stale
# --------------------------------------------------------------------------
def test_prune_stale() -> None:
    from modules.cpc_os.registry import PaneRegistry, PaneRecord
    now = 1_000_000.0
    old = now - 2 * _SECONDS_PER_DAY      # 2 days old
    recent = now - 60                     # 1 min old
    with tempfile.TemporaryDirectory() as td:
        reg_path = Path(td) / "reg.json"
        reg = PaneRegistry(_path=reg_path)
        reg.panes = {
            "active-fresh": PaneRecord("active-fresh", "/a", "t", old, recent,
                                       status="active"),
            "active-old": PaneRecord("active-old", "/a", "t", old, old,
                                     status="active"),
            "stale-old": PaneRecord("stale-old", "/a", "t", old, old,
                                    status="stale"),
            "dead-old": PaneRecord("dead-old", "/a", "t", old, old,
                                   status="dead"),
            "stale-fresh": PaneRecord("stale-fresh", "/a", "t", old, recent,
                                      status="stale"),
        }
        removed = reg.prune_stale(max_age_s=_SECONDS_PER_DAY, now=now)
        remaining = set(reg.panes.keys())

        if removed == 2 and remaining == {"active-fresh", "active-old",
                                          "stale-fresh"}:
            _ok("V-RAM-PRUNE-STALE",
                f"removed {removed} (stale-old+dead-old); kept active + "
                "recent-stale")
        else:
            _fail("V-RAM-PRUNE-STALE",
                  f"removed={removed} remaining={sorted(remaining)}")

        # Idempotence + persistence: reload from disk, no further removals.
        reg2 = PaneRegistry.load(reg_path)
        again = reg2.prune_stale(max_age_s=_SECONDS_PER_DAY, now=now)
        if again == 0 and set(reg2.panes.keys()) == remaining:
            _ok("V-RAM-PRUNE-STALE-IDEMPOTENT",
                "second prune removed 0; state persisted to disk")
        else:
            _fail("V-RAM-PRUNE-STALE-IDEMPOTENT",
                  f"again={again} keys={sorted(reg2.panes.keys())}")


# --------------------------------------------------------------------------
# C2 -- walk_cache_guard.prune_walk_caches
# --------------------------------------------------------------------------
def test_walk_cache_guard() -> None:
    import tools.walk_cache_guard as wcg
    now = 1_000_000.0
    with tempfile.TemporaryDirectory() as td:
        state = Path(td)
        big = state / "skill-index.json"            # allowlisted, oversize
        big.write_text("[" + "0," * 400_000 + "0]", encoding="utf-8")
        small = state / "open-composers.json"        # allowlisted, in-bounds
        small.write_text("{}", encoding="utf-8")
        foreign = state / "cpc_os_registry.json"     # NOT allowlisted
        foreign.write_text("x" * 800_000, encoding="utf-8")

        orig = wcg.STATE_DIR
        try:
            wcg.STATE_DIR = state
            rows = wcg.prune_walk_caches(apply=True, max_kb=512,
                                         ttl_days=7, now=now)
        finally:
            wcg.STATE_DIR = orig

        by = {r["name"]: r for r in rows}
        big_trunc = by.get("skill-index.json", {}).get("action") == "truncated"
        small_kept = by.get("open-composers.json", {}).get("action") == "keep"
        foreign_untouched = "cpc_os_registry.json" not in by
        big_now_small = big.stat().st_size < 512 * 1024
        foreign_intact = foreign.stat().st_size == 800_000

        if (big_trunc and small_kept and foreign_untouched
                and big_now_small and foreign_intact):
            _ok("V-RAM-WALK-CACHE-GUARD",
                "oversize allowlisted cache truncated; in-bounds + "
                "non-allowlisted spared; valid JSON written")
        else:
            _fail("V-RAM-WALK-CACHE-GUARD",
                  f"big_trunc={big_trunc} small_kept={small_kept} "
                  f"foreign_untouched={foreign_untouched} "
                  f"big_now_small={big_now_small} "
                  f"foreign_intact={foreign_intact}")

        # Truncated cache must be valid, empty JSON of the right shape.
        import json as _json
        try:
            payload = _json.loads(big.read_text(encoding="utf-8"))
            if payload == []:
                _ok("V-RAM-WALK-CACHE-VALID-JSON",
                    "truncated list-cache is valid empty []")
            else:
                _fail("V-RAM-WALK-CACHE-VALID-JSON",
                      f"unexpected payload {payload!r}")
        except Exception as exc:  # noqa: BLE001
            _fail("V-RAM-WALK-CACHE-VALID-JSON", f"invalid JSON: {exc}")


# --------------------------------------------------------------------------
# B1 -- ram_guard.evaluate (pure verdict logic)
# --------------------------------------------------------------------------
def test_ram_guard_evaluate() -> None:
    from tools.ram_guard import evaluate
    gb = 1024
    cases = [
        (None, "no-measurement", False),
        (5 * gb, "ok", False),
        (20 * gb, "warn", True),
        (20 * gb - 1, "ok", False),     # just below warn
        (28 * gb, "critical", True),
        (40 * gb, "critical", True),
    ]
    all_ok = True
    detail = []
    for ws, want_level, want_snap in cases:
        v = evaluate(ws, warn_gb=20, crit_gb=28)
        if v["level"] != want_level or v["snapshot"] != want_snap:
            all_ok = False
            detail.append(f"ws={ws} got {v['level']}/{v['snapshot']} "
                          f"want {want_level}/{want_snap}")
    if all_ok:
        _ok("V-RAM-GUARD-EVALUATE",
            "ok/warn/critical/no-measurement thresholds + snapshot flags "
            "correct across 6 cases")
    else:
        _fail("V-RAM-GUARD-EVALUATE", "; ".join(detail))


# --------------------------------------------------------------------------
# A1 -- bench_ram_footprint (live; advisory if no measurement)
# --------------------------------------------------------------------------
def test_bench_ram_footprint() -> None:
    from tools.bench_all import bench_ram_footprint
    r = bench_ram_footprint()
    if "ram_footprint_error" in r:
        _adv("V-RAM-PP-OVERHEAD",
             f"measurement unavailable -- {r['ram_footprint_error']}")
        return
    pp = r.get("ram_footprint_mb")
    if not isinstance(pp, (int, float)):
        _fail("V-RAM-PP-OVERHEAD", f"no numeric ram_footprint_mb: {r}")
        return
    if pp <= OVERHEAD_CEIL_MB:
        _ok("V-RAM-PP-OVERHEAD",
            f"PP overhead {pp}MB <= {OVERHEAD_CEIL_MB}MB "
            f"(node {r.get('ram_node_mb')} + python {r.get('ram_python_mb')}; "
            f"claude.exe {r.get('claude_ws_mb')}MB ungated)")
    else:
        _fail("V-RAM-PP-OVERHEAD",
              f"PP overhead {pp}MB > {OVERHEAD_CEIL_MB}MB ceiling")


def main() -> int:
    print("=" * 64)
    print("test_ram_optimization -- RAM Optimization Sprint V-gates")
    print("=" * 64)
    for fn in (test_prune_stale, test_walk_cache_guard,
               test_ram_guard_evaluate, test_bench_ram_footprint):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            _fail(fn.__name__, f"{type(exc).__name__}: {exc}")
    total = _passes + _fails
    print(f"RAM_PASS={_passes}/{total}  fails={_fails}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
