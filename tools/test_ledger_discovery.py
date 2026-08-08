#!/usr/bin/env python3
"""Gates for discovered cumulative ledgers.

Spec: vault/specs/ledger-discovery.md

Synthetic trees in a tempdir, so the suite does not depend on the estate's
current ledger population -- except the two gates that deliberately read the
real repo, which assert enrolment and an invariant rather than a frozen count.
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

from modules.liveness import liveness_ledger as L  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"PASS  {gate:26s} {evidence}")


def _fail(gate: str, why: str) -> None:
    global _fails
    _fails += 1
    print(f"FAIL  {gate:26s} {why}")


def mk(root: Path, rel: str, rows: int = 1) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join('{"n":%d}\n' % i for i in range(rows)), encoding="utf-8")
    return p


UUIDS = ["11111111-1111-1111-1111-111111111111",
         "22222222-2222-2222-2222-222222222222",
         "33333333-3333-3333-3333-333333333333"]


def main() -> int:
    # ---- V-LD-DISCOVERED ------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        mk(root, "vault/mydomain/events.jsonl", 3)
        with_it, _ = L.discover_ledgers(root)
        (root / "vault" / "mydomain" / "events.jsonl").unlink()
        without, _ = L.discover_ledgers(root)
        if "vault/mydomain/events.jsonl" in with_it and not without:
            _ok("V-LD-DISCOVERED", "ledger appears when on disk, disappears when removed")
        else:
            _fail("V-LD-DISCOVERED", f"with={with_it} without={without}")

    # ---- V-LD-SERIES-EXCLUDED -------------------------------------------
    # Exercised synthetically ON PURPOSE: on the real estate every per-session
    # series lives in a directory the store gate already removes, so this gate
    # is the only thing that ever runs the family branch.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for u in UUIDS:
            mk(root, f"vault/sess/run_{u}.jsonl")
        mk(root, "vault/sess/real_ledger.jsonl", 5)
        kept, exc = L.discover_ledgers(root)
        series_reported = sum(exc["series"].values())
        if kept == ["vault/sess/real_ledger.jsonl"] and series_reported == len(UUIDS):
            _ok("V-LD-SERIES-EXCLUDED",
                f"{series_reported} uuid-shaped files excluded as a series and reported; "
                "the lone ledger beside them survives")
        else:
            _fail("V-LD-SERIES-EXCLUDED", f"kept={kept} series={exc['series']}")

    # ---- V-LD-STORE-EXCLUDED --------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for i in range(L.MAX_JSONL_IN_LEDGER_DIR + 1):
            mk(root, f"vault/store/distinct_name_{chr(97 + i)}.jsonl")
        mk(root, "vault/keep/ledger.jsonl", 2)
        kept, exc = L.discover_ledgers(root)
        if kept == ["vault/keep/ledger.jsonl"] and exc["store_dirs"].get("vault/store") == 9:
            _ok("V-LD-STORE-EXCLUDED",
                "a directory over the jsonl threshold is excluded as a store, with its count")
        else:
            _fail("V-LD-STORE-EXCLUDED", f"kept={kept} stores={exc['store_dirs']}")

    # ---- V-LD-LEDGER-KEPT -----------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        mk(root, "vault/decision_registry/records.jsonl", 1)
        kept, exc = L.discover_ledgers(root)
        if kept == ["vault/decision_registry/records.jsonl"] and not exc["series"]:
            _ok("V-LD-LEDGER-KEPT", "a lone one-row ledger is kept, not filtered as thin")
        else:
            _fail("V-LD-LEDGER-KEPT", f"kept={kept} exc={exc}")

    # ---- V-LD-EMPTY-VS-MISSING ------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        mk(root, "vault/d/empty.jsonl", 0)
        now = datetime.now(timezone.utc)
        empty = L._probe_ledger_rows({"path": "vault/d/empty.jsonl"},
                                     repo_root=root, now=now, max_age_h=36)
        missing = L._probe_ledger_rows({"path": "vault/d/nope.jsonl"},
                                       repo_root=root, now=now, max_age_h=36)
        if empty[0] == L.SILENT and missing[0] == L.ORPHANED and empty[0] != missing[0]:
            _ok("V-LD-EMPTY-VS-MISSING",
                f"0 rows -> {empty[0]}, absent file -> {missing[0]} (never collapsed)")
        else:
            _fail("V-LD-EMPTY-VS-MISSING", f"empty={empty} missing={missing}")

    # ---- V-LD-ROWS-IN-EVIDENCE ------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        p = mk(root, "vault/d/led.jsonl", 7)
        now = datetime.now(timezone.utc)
        fresh = L._probe_ledger_rows({"path": "vault/d/led.jsonl"},
                                     repo_root=root, now=now, max_age_h=36)
        stale = L._probe_ledger_rows({"path": "vault/d/led.jsonl", "max_age_h": 0.0001},
                                     repo_root=root, now=now + timedelta(hours=5),
                                     max_age_h=36)
        if fresh[0] == L.LIVE and stale[0] == L.SILENT \
           and "7 row" in fresh[1] and "7 row" in stale[1]:
            _ok("V-LD-ROWS-IN-EVIDENCE",
                "row count named in BOTH the live and the gone-quiet evidence")
        else:
            _fail("V-LD-ROWS-IN-EVIDENCE", f"fresh={fresh} stale={stale}")

    # ---- V-LD-NO-RATIO --------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        mk(root, "vault/d/led.jsonl", 3)
        rows = L._discovered_ledgers(root)
        bad = [k for r in rows for k in r
               if any(t in k.lower() for t in ("ratio", "pct", "percent"))]
        floats = [k for r in rows for k, v in r.items() if isinstance(v, float)]
        if rows and not bad and not floats:
            _ok("V-LD-NO-RATIO", f"{len(rows)} row(s), no ratio-like key and no float value")
        else:
            _fail("V-LD-NO-RATIO", f"rows={len(rows)} bad={bad} floats={floats}")

    # ---- V-LD-EXISTING-UNCHANGED ----------------------------------------
    # An INVARIANT, not a frozen count: a pinned 358 would go red on the next
    # pane's legitimate module. Every non-ledger row must judge identically
    # whether or not the ledger rows are present in the registry.
    full = L.default_registry()
    without_ledgers = [e for e in full if (e.get("probe") or {}).get("type") != "ledger-rows"]
    a = {r["id"]: r["verdict"] for r in L.audit(registry=full) if r["surface"] != "ledger"}
    b = {r["id"]: r["verdict"] for r in L.audit(registry=without_ledgers)}
    moved = sorted(k for k in b if a.get(k) != b[k])
    if a == b and not moved:
        _ok("V-LD-EXISTING-UNCHANGED",
            f"{len(b)} pre-existing rows judge identically with and without ledger enrolment")
    else:
        _fail("V-LD-EXISTING-UNCHANGED", f"{len(moved)} moved: {moved[:5]}")

    # ---- V-LD-LIVE-FINDS-THE-THREE --------------------------------------
    live_paths, live_exc = L.discover_ledgers(PP)
    want = ["vault/done_gate/receipts.jsonl",
            "vault/ias/c2_opportunity_cost_ledger.jsonl",
            "vault/anti_fragility/hacks.jsonl"]
    missing = [w for w in want if w not in live_paths]
    if not missing and live_exc["store_dirs"]:
        _ok("V-LD-LIVE-FINDS-THE-THREE",
            f"{len(live_paths)} ledgers enrolled incl. the 3 previously unwatched; "
            f"{len(live_exc['store_dirs'])} store dir(s) excluded and named")
    else:
        _fail("V-LD-LIVE-FINDS-THE-THREE", f"missing={missing} stores={live_exc['store_dirs']}")

    # ---- V-LD-FAIL-OPEN -------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)          # no vault/ at all
        try:
            paths, exc = L.discover_ledgers(root)
            rows = L._discovered_ledgers(root)
            if paths == [] and rows == [] and isinstance(exc, dict):
                _ok("V-LD-FAIL-OPEN", "a tree with no vault/ returns empty rather than raising")
            else:
                _fail("V-LD-FAIL-OPEN", f"paths={paths} rows={rows}")
        except Exception as exc:  # noqa: BLE001
            _fail("V-LD-FAIL-OPEN", f"raised {type(exc).__name__}: {exc}")

    # ---- V-LD-HERMETIC --------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        mk(root, "vault/a/one.jsonl", 2)
        mk(root, "vault/b/two.jsonl", 0)
        for u in UUIDS:
            mk(root, f"vault/c/s_{u}.jsonl")
        runs = [json.dumps(L.discover_ledgers(root), sort_keys=True, default=str)
                for _ in range(3)]
        if len(set(runs)) == 1:
            _ok("V-LD-HERMETIC", "3 consecutive discoveries byte-identical")
        else:
            _fail("V-LD-HERMETIC", f"{len(set(runs))} distinct outputs")

    total = _passes + _fails
    print()
    print(f"LEDGER_DISCOVERY_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
