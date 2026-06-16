"""V-gates for topology-authoritative CPC-OS tab count (BL-CPCOS-RESTORE-004).

Proves the fix for "a veces no regenera el mismo numero de cursor tabs":
the restore tab COUNT is taken from Cursor's live ``terminal.integrated.layoutInfo``
(via lib.lazarus.topology_engine), collapsing stale duplicate workspaces, and
vscode_autorun emits EXACTLY that many tasks (pad fresh / truncate extras) so the
count is deterministic regardless of registry pruning / resume-string collapse /
transcript-birth races.

Hermetic: a hand-built envelope (no Cursor install) + explicit tab_counts into
the autorun generator (no live topology read). Designed to pass identically on
rapid back-to-back runs.

Run: python tools/test_topology_reconcile.py   ->   TOPORECON_PASS=N/N
"""
from __future__ import annotations

import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parent.parent
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.cpc_os import topology_reconcile as tr  # noqa: E402
from modules.cpc_os import vscode_autorun as va  # noqa: E402

passes = 0
fails = 0


def _ok(gate: str, ev: str) -> None:
    global passes
    passes += 1
    print(f"OK   {gate}: {ev}")


def _fail(gate: str, ev: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {ev}")


def _layout(n_terminals_per_tab: list[int]) -> dict:
    """A layoutInfo with one tab per entry; the entry value is how many split
    terminals that tab holds."""
    tabs = []
    pid = 10
    for k in n_terminals_per_tab:
        terms = [{"relativeSize": 1, "terminal": (pid := pid + 1)} for _ in range(k)]
        tabs.append({"isActive": False, "activePersistentProcessId": pid, "terminals": terms})
    return {"workspaceId": "ws", "tabs": tabs}


def _snap(folder: str, layout: dict | None, db_mtime: float) -> dict:
    topo = {}
    if layout is not None:
        topo["terminal.integrated.layoutInfo"] = layout
    return {"folder": folder, "topology": topo, "db_mtime": db_mtime}


def _cpc_labels(tasks: list[dict]) -> list[str]:
    return [t["label"] for t in tasks]


def main() -> int:
    # ---- folder_uri_to_path -------------------------------------------------
    p = tr.folder_uri_to_path(
        "file:///c%3A/Users/U/Desktop/Cursor%20Projects/GEO-audit"
    )
    if p == r"c:\Users\U\Desktop\Cursor Projects\GEO-audit":
        _ok("V-TOPO-URI-DECODE", p)
    else:
        _fail("V-TOPO-URI-DECODE", repr(p))

    if tr.folder_uri_to_path(None) is None and tr.folder_uri_to_path("") is None:
        _ok("V-TOPO-URI-EMPTY", "None/empty -> None")
    else:
        _fail("V-TOPO-URI-EMPTY", "empty uri not None")

    # ---- terminal_count -----------------------------------------------------
    if tr.terminal_count(_layout([1, 1])) == 2 and tr.terminal_count(_layout([2])) == 2:
        _ok("V-TOPO-COUNT-TERMINALS", "2 tabs x1 == 2; 1 tab x2 splits == 2")
    else:
        _fail("V-TOPO-COUNT-TERMINALS", "terminal count wrong")

    if tr.terminal_count(None) == 0 and tr.terminal_count({"tabs": []}) == 0:
        _ok("V-TOPO-COUNT-EMPTY", "no layout / no tabs -> 0")
    else:
        _fail("V-TOPO-COUNT-EMPTY", "empty layout not 0")

    # ---- live_tab_counts: stale-duplicate collapse + 0-skip -----------------
    geo = "file:///c%3A/Users/U/Desktop/Cursor%20Projects/GEO-audit"
    nex = "file:///c%3A/Users/U/Desktop/Cursor%20Projects/NexumOps"
    closed = "file:///c%3A/Users/U/Desktop/Cursor%20Projects/Closed"
    envelope = {
        "snapshots": [
            # GEO-audit appears 3x under stale hashes; live (newest mtime) has 2.
            _snap(geo, _layout([1]), db_mtime=100.0),       # stale, 1 tab
            _snap(geo, _layout([1, 1]), db_mtime=300.0),    # LIVE, 2 tabs
            _snap(geo, _layout([1]), db_mtime=200.0),       # stale, 1 tab
            # NexumOps single live workspace with 1 tab.
            _snap(nex, _layout([1]), db_mtime=500.0),
            # A closed/terminal-less workspace must contribute nothing.
            _snap(closed, _layout([]), db_mtime=900.0),
            _snap(closed, None, db_mtime=950.0),
        ]
    }
    counts = tr.live_tab_counts(envelope)
    geo_key = tr.norm_path(r"C:\Users\U\Desktop\Cursor Projects\GEO-audit")
    nex_key = tr.norm_path(r"C:\Users\U\Desktop\Cursor Projects\NexumOps")
    closed_key = tr.norm_path(r"C:\Users\U\Desktop\Cursor Projects\Closed")
    if counts.get(geo_key) == 2:
        _ok("V-TOPO-LIVE-WINS", "GEO-audit collapses 3 stale hashes -> live count 2")
    else:
        _fail("V-TOPO-LIVE-WINS", f"GEO count={counts.get(geo_key)} all={counts}")

    if counts.get(nex_key) == 1 and closed_key not in counts:
        _ok("V-TOPO-SKIP-CLOSED", "NexumOps=1; terminal-less workspace omitted")
    else:
        _fail("V-TOPO-SKIP-CLOSED", f"nex={counts.get(nex_key)} closed_in={closed_key in counts}")

    # ---- vscode_autorun: target_count=None keeps legacy behaviour -----------
    # Two distinct resumable panes + a third sharing a resume string -> the
    # resume-string dedup yields 2 tasks (unchanged contract).
    panes = [
        {"resume": "claude --resume aaaaaaaa1111", "resume_kind": "exact",
         "repo": "GEO-audit", "cwd": r"C:\x\GEO-audit"},
        {"resume": "claude --resume bbbbbbbb2222", "resume_kind": "exact",
         "repo": "GEO-audit", "cwd": r"C:\x\GEO-audit"},
        {"resume": "claude --resume aaaaaaaa1111", "resume_kind": "exact",
         "repo": "GEO-audit", "cwd": r"C:\x\GEO-audit"},
    ]
    legacy = va.build_cpc_tasks(panes)
    if len(legacy) == 2:
        _ok("V-AUTORUN-LEGACY", "target=None -> dedup-by-resume (2 tasks), unchanged")
    else:
        _fail("V-AUTORUN-LEGACY", f"legacy task count={len(legacy)}")

    # ---- target_count pads fresh tabs (RC-2 cure) ---------------------------
    # Repo had 3 terminals but only 1 resumable session known -> emit EXACTLY 3
    # tasks: 1 exact + 2 uniquely-labelled fresh (so they survive as 3 terminals
    # instead of collapsing to 1).
    one_known = [
        {"resume": "claude --resume aaaaaaaa1111", "resume_kind": "exact",
         "repo": "GEO-audit", "cwd": r"C:\x\GEO-audit"},
        {"resume": 'cd "C:\\x\\GEO-audit" && claude', "resume_kind": "missing",
         "repo": "GEO-audit", "cwd": r"C:\x\GEO-audit"},
        {"resume": 'cd "C:\\x\\GEO-audit" && claude', "resume_kind": "missing",
         "repo": "GEO-audit", "cwd": r"C:\x\GEO-audit"},
    ]
    padded = va.build_cpc_tasks(one_known, target_count=3)
    labels = _cpc_labels(padded)
    if len(padded) == 3 and len(set(labels)) == 3:
        _ok("V-AUTORUN-PAD", f"3 terminals -> 3 distinct tasks ({len(set(labels))} unique labels)")
    else:
        _fail("V-AUTORUN-PAD", f"count={len(padded)} labels={labels}")

    # ---- target_count truncates extras (closed-tab cure) --------------------
    # Registry knows 2 resumable sessions but Cursor shows only 1 tab now (the
    # other was closed) -> emit EXACTLY 1.
    two_known = [
        {"resume": "claude --resume aaaaaaaa1111", "resume_kind": "exact",
         "repo": "GEO-audit", "cwd": r"C:\x\GEO-audit"},
        {"resume": "claude --resume bbbbbbbb2222", "resume_kind": "exact",
         "repo": "GEO-audit", "cwd": r"C:\x\GEO-audit"},
    ]
    truncated = va.build_cpc_tasks(two_known, target_count=1)
    if len(truncated) == 1:
        _ok("V-AUTORUN-TRUNCATE", "2 known sessions, 1 live tab -> 1 task")
    else:
        _fail("V-AUTORUN-TRUNCATE", f"count={len(truncated)}")

    # ---- exact match needs no pad/truncate ----------------------------------
    exact = va.build_cpc_tasks(two_known, target_count=2)
    if len(exact) == 2:
        _ok("V-AUTORUN-EXACT", "2 known == 2 live tabs -> 2 tasks unchanged")
    else:
        _fail("V-AUTORUN-EXACT", f"count={len(exact)}")

    # ---- generate_from_snapshot honours explicit tab_counts (hermetic wire) -
    import json
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        snap_json = Path(td) / "session_snapshot.json"
        cwd = str(Path(td) / "GEO-audit")
        # ONE resumable pane in the snapshot, but topology says 3 tabs.
        snap_json.write_text(json.dumps([
            {"resume": "claude --resume aaaaaaaa1111", "resume_kind": "exact",
             "repo": "GEO-audit", "cwd": cwd},
        ]), encoding="utf-8")
        results = va.generate_from_snapshot(
            snap_json, dry_run=True,
            tab_counts={tr.norm_path(cwd): 3},
        )
        n = results[0]["n_tasks"] if results else -1
        if len(results) == 1 and n == 3:
            _ok("V-AUTORUN-WIRED", "snapshot 1 pane + topology 3 -> 3 tasks")
        else:
            _fail("V-AUTORUN-WIRED", f"results={[(r['cwd'], r['n_tasks']) for r in results]}")

        # Fail-open: unknown cwd in tab_counts -> legacy derived behaviour (1).
        results2 = va.generate_from_snapshot(
            snap_json, dry_run=True, tab_counts={},
        )
        if results2 and results2[0]["n_tasks"] == 1:
            _ok("V-AUTORUN-FAILOPEN", "no topology count -> legacy 1 task (no regression)")
        else:
            _fail("V-AUTORUN-FAILOPEN", f"n={results2[0]['n_tasks'] if results2 else None}")

    total = passes + fails
    print(f"TOPORECON_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
