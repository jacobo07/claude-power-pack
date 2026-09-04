#!/usr/bin/env python3
"""V-GRAPHIFY-DEFERRED-* -- gate for the deferred-repo refresher (GK-10).

Origin (2026-08-27): the GK-08 Stop hook caps a Stop-time index at
MAX_MD_FILES and emits verdict="deferred" with the hint "refresh via
'indexer --all'". Nothing scheduled --all, and --all discovers from
terminal_slots.json inside a 7-day recency window, so a big repo not opened
inside that window was never revisited. "deferred" was a terminal state
wearing the word "temporary": KobiiSports Resort's CursorProjects sat at 0
nodes for a month while every component passed its own tests.

These gates pin the three properties that make the debt recoverable:
  1. a deferral is DISCOVERED from the append-only log, not curated;
  2. a repo repaired out-of-band (a --repo run, which never writes the log)
     leaves the debt set -- otherwise the gate cries wolf forever;
  3. a repo re-deferred AFTER its last successful index is debt again --
     staleness must be able to come back, or the gate can only fall once.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PP_ROOT / "modules" / "graphify"))

import indexer  # noqa: E402
import global_store as gs  # noqa: E402

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


def _write_log(path: Path, rows: list) -> None:
    path.write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8"
    )


def main() -> int:
    print("== V-GRAPHIFY-DEFERRED gates ==")

    # The production _EPHEMERAL regex matches `appdata/local/temp`, which is
    # exactly where TemporaryDirectory lives -- so a naive fixture is filtered
    # out and every gate below passes vacuously (they did, on the first run:
    # 5/7 green for the wrong reason). Narrow the filter to the `l3proj-`
    # marker for the fixture block, and prove the REAL regex separately
    # against a real temp path in V-GRAPHIFY-DEFERRED-EPHEMERAL.
    _production_ephemeral = indexer._EPHEMERAL
    indexer._EPHEMERAL = __import__("re").compile(r"l3proj-", __import__("re").IGNORECASE)

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        # Arrange -- two real directories so the is_dir() filter cannot mask a
        # logic error, plus one path that does not exist.
        stuck = tmp / "stuck_repo"
        fixed = tmp / "fixed_repo"
        stuck.mkdir()
        fixed.mkdir()
        gone = tmp / "deleted_repo"
        log = tmp / "writeback.log"

        # ---- V-GRAPHIFY-DEFERRED-DISCOVERS -------------------------------
        _write_log(log, [
            {"verdict": "indexed", "repo": str(stuck), "at": "2026-08-01T00:00:00Z"},
            {"verdict": "deferred", "repo": str(stuck), "at": "2026-08-20T00:00:00Z",
             "reason": "9000+ md files > 4000 cap"},
            {"verdict": "indexed", "repo": str(fixed), "at": "2026-08-20T00:00:00Z"},
        ])
        debt = indexer.deferred_repos(log)
        names = [d["repo"] for d in debt]
        if names == [str(stuck)]:
            _ok("V-GRAPHIFY-DEFERRED-DISCOVERS",
                f"latest-verdict wins; 1 of 2 repos is debt ({stuck.name})")
        else:
            _fail("V-GRAPHIFY-DEFERRED-DISCOVERS",
                  f"expected only {stuck!s}, got {names}")

        # ---- V-GRAPHIFY-UNHEALED-ERROR -----------------------------------
        # The gap this gate exists for: session_writeback emits verdict="error"
        # when the index actually RAISED, and deferred_repos() collected only
        # "deferred", so an errored repo was filtered out of the debt set and
        # --repair could never reach it. Nothing else healed it either, which
        # made a hook fault the one permanent knowledge-loss path in the
        # capture layer. This assertion fails against the pre-fix code.
        _write_log(log, [
            {"verdict": "indexed", "repo": str(stuck), "at": "2026-08-01T00:00:00Z"},
            {"verdict": "error", "repo": str(stuck), "at": "2026-08-20T00:00:00Z",
             "reason": "MemoryError during build_nodes"},
            {"verdict": "indexed", "repo": str(fixed), "at": "2026-08-20T00:00:00Z"},
        ])
        debt = indexer.deferred_repos(log)
        if [d["repo"] for d in debt] == [str(stuck)]:
            _ok("V-GRAPHIFY-UNHEALED-ERROR",
                "a raised writeback is debt, not a terminal state")
        else:
            _fail("V-GRAPHIFY-UNHEALED-ERROR",
                  f"an errored repo was not collected as debt: "
                  f"{[d['repo'] for d in debt]}")

        # ---- V-GRAPHIFY-UNHEALED-VERDICT-NAMED ---------------------------
        # --repair treats both alike, but an operator must be able to tell a
        # size deferral from a crash: they have different causes and only one
        # of them is expected. An unlabelled debt row hides that difference.
        if debt and debt[0].get("verdict") == "error":
            _ok("V-GRAPHIFY-UNHEALED-VERDICT-NAMED",
                "debt row carries its originating verdict")
        else:
            _fail("V-GRAPHIFY-UNHEALED-VERDICT-NAMED",
                  f"debt row lost its verdict: {debt[:1]}")

        # ---- V-GRAPHIFY-UNHEALED-NEGATIVE-CONTROL ------------------------
        # The widening must not swallow every verdict. A successful index is
        # never debt -- without this, "collect everything" would pass the two
        # gates above while destroying the gate's meaning.
        _write_log(log, [
            {"verdict": "indexed", "repo": str(stuck), "at": "2026-08-20T00:00:00Z"},
        ])
        if indexer.deferred_repos(log) == []:
            _ok("V-GRAPHIFY-UNHEALED-NEGATIVE-CONTROL",
                "a healthy verdict stays out of the debt set")
        else:
            _fail("V-GRAPHIFY-UNHEALED-NEGATIVE-CONTROL",
                  "the widened filter swallowed a successful index")

        # ---- V-GRAPHIFY-DEFERRED-LATEST-WINS -----------------------------
        # A deferral FOLLOWED by a successful index is not debt: the log is
        # append-only, so only the last verdict per repo may speak.
        _write_log(log, [
            {"verdict": "deferred", "repo": str(stuck), "at": "2026-08-20T00:00:00Z"},
            {"verdict": "indexed", "repo": str(stuck), "at": "2026-08-21T00:00:00Z"},
        ])
        if indexer.deferred_repos(log) == []:
            _ok("V-GRAPHIFY-DEFERRED-LATEST-WINS",
                "deferral superseded by a later index -> not debt")
        else:
            _fail("V-GRAPHIFY-DEFERRED-LATEST-WINS",
                  "a superseded deferral was still reported as debt")

        # ---- V-GRAPHIFY-DEFERRED-MISSING-DIR -----------------------------
        _write_log(log, [
            {"verdict": "deferred", "repo": str(gone), "at": "2026-08-20T00:00:00Z"},
        ])
        if indexer.deferred_repos(log) == []:
            _ok("V-GRAPHIFY-DEFERRED-MISSING-DIR",
                "a deleted repo is not standing debt")
        else:
            _fail("V-GRAPHIFY-DEFERRED-MISSING-DIR",
                  "a non-existent path was reported as debt")

        # ---- V-GRAPHIFY-DEFERRED-EPHEMERAL -------------------------------
        # Temp worktrees churn constantly; they are not durable debt. Asserted
        # against the PRODUCTION regex, on both idioms it must catch: the
        # l3proj- worktree marker and a bare Windows temp root.
        eph = tmp / "l3proj-ABC123"
        eph.mkdir()
        missed = [
            probe for probe in (str(eph),
                                r"C:\Users\User\AppData\Local\Temp\some-repo")
            if not _production_ephemeral.search(probe.replace("\\", "/"))
        ]
        _write_log(log, [
            {"verdict": "deferred", "repo": str(eph), "at": "2026-08-20T00:00:00Z"},
        ])
        if not missed and indexer.deferred_repos(log) == []:
            _ok("V-GRAPHIFY-DEFERRED-EPHEMERAL",
                "production regex rejects l3proj- and AppData temp roots")
        else:
            _fail("V-GRAPHIFY-DEFERRED-EPHEMERAL",
                  f"ephemeral path treated as durable debt: "
                  f"{missed or 'filter not applied'}")

        # ---- V-GRAPHIFY-DEFERRED-NO-LOG ----------------------------------
        # Fail-open: an absent log is an empty debt set, never an exception.
        # A gate that raises on a fresh install blocks the work it protects.
        try:
            empty = indexer.deferred_repos(tmp / "does_not_exist.log")
            if empty == []:
                _ok("V-GRAPHIFY-DEFERRED-NO-LOG", "absent log -> [] (fail-open)")
            else:
                _fail("V-GRAPHIFY-DEFERRED-NO-LOG", f"expected [], got {empty}")
        except Exception as e:  # noqa: BLE001 -- the gate IS "does not raise"
            _fail("V-GRAPHIFY-DEFERRED-NO-LOG", f"raised instead of degrading: {e}")

        # ---- V-GRAPHIFY-DEFERRED-CORRUPT-LINE ----------------------------
        # One unparseable line must not blind the gate to the rest of the log.
        log.write_text(
            "not json at all\n"
            + json.dumps({"verdict": "deferred", "repo": str(stuck),
                          "at": "2026-08-20T00:00:00Z"}) + "\n",
            encoding="utf-8",
        )
        if [d["repo"] for d in indexer.deferred_repos(log)] == [str(stuck)]:
            _ok("V-GRAPHIFY-DEFERRED-CORRUPT-LINE",
                "a malformed line is skipped, the rest still parsed")
        else:
            _fail("V-GRAPHIFY-DEFERRED-CORRUPT-LINE",
                  "a malformed line suppressed real debt")

    # Fixture window over: the live-store gate below must see the real filter.
    indexer._EPHEMERAL = _production_ephemeral

    # ---- V-GRAPHIFY-DEFERRED-STORE-CROSSCHECK ----------------------------
    # The live store must be consulted, not just the log: `indexer --repo`
    # repairs a repo WITHOUT writing writeback.log, so a log-only gate would
    # keep reporting an already-fixed repo. This is the exact case that
    # closed on 2026-08-27 for KobiiSports Resort's CursorProjects.
    try:
        store_path = gs.state_dir() / "graphify_global.json"
        repos = json.loads(store_path.read_text(encoding="utf-8")).get("repos", {})
        live_debt = {d["repo"] for d in indexer.deferred_repos()}
        leaked = [
            r["path"] for rid, r in repos.items()
            if r.get("path") in live_debt and r.get("node_count", 0) > 0
            and str(r.get("indexed_at", "")) > next(
                d["deferred_at"] for d in indexer.deferred_repos()
                if d["repo"] == r.get("path")
            )
        ]
        if not leaked:
            _ok("V-GRAPHIFY-DEFERRED-STORE-CROSSCHECK",
                f"no repo indexed after its deferral is still called debt "
                f"(store holds {len(repos)} repos)")
        else:
            _fail("V-GRAPHIFY-DEFERRED-STORE-CROSSCHECK",
                  f"repaired repos still reported as debt: {leaked}")
    except (OSError, json.JSONDecodeError, ValueError, StopIteration) as e:
        # No live store (CI checkout) -- the property is untestable here, and
        # an untestable property must not read as a pass.
        print(f"  SKIP  V-GRAPHIFY-DEFERRED-STORE-CROSSCHECK  no live store ({e})")

    total = _passes + _fails
    print(f"GRAPHIFY_DEFERRED_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
