"""V-gates for restore_panes / vscode_autorun ALL-panes-per-repo behavior.

Hermetic: imports vscode_autorun in script mode, uses only in-memory data and a
temp dir. Proves the fix for the "1 pane per repo" bug (T-RESTORE-PANES-ONE-PER-
REPO-001): all panes become tasks, order is preserved (LIVE-first as fed), each
task launches via kclaude, and the default tab-count cap still works when asked.
"""
import sys, os, json, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "modules", "cpc_os"))
import vscode_autorun as va  # noqa: E402  (script-mode import)

passes = 0
fails = 0


def _ok(gate, ev):
    global passes
    passes += 1
    print(f"[OK] {gate}: {ev}")


def _fail(gate, ev):
    global fails
    fails += 1
    print(f"[FAIL] {gate}: {ev}")


def mk_panes(cwd, sids):
    return [{"cwd": cwd, "resume": f"claude --resume {s}", "resume_kind": "exact"} for s in sids]


def main():
    cwd = r"C:\repo\InfinityOps"
    sids = [f"{i:08d}-0000-0000-0000-000000000000" for i in range(13)]
    panes = mk_panes(cwd, sids)

    # V-RESTORE-ALL-PANES: 13 panes -> 13 tasks with no cap (the core bug fix)
    tasks = va.build_cpc_tasks(panes, target_count=None)
    if len(tasks) == 13:
        _ok("V-RESTORE-ALL-PANES", "13 panes -> 13 tasks (no cap)")
    else:
        _fail("V-RESTORE-ALL-PANES", f"expected 13 got {len(tasks)}")

    # A task now has TWO possible shapes (T-FOLDEROPEN-STAMPEDE-001): wave 0
    # launches immediately (command = kclaude.bat, args = ["--resume", sid]),
    # later waves launch through a delay wrapper (command = cmd, args =
    # ["/c", 'timeout /t N ... & "<kclaude>" --resume <sid>']). Both gates below
    # assert the INVARIANT that must hold in EITHER shape -- so they get stronger,
    # not weaker, as the stagger is applied.
    def launch_text(t: dict) -> str:
        return (str(t.get("command", "")) + " " + " ".join(map(str, t.get("args", [])))).lower()

    # V-RESTORE-ORDER: task order preserves input order (LIVE-first as fed)
    if all(sids[i] in launch_text(tasks[i]) for i in range(len(tasks))):
        _ok("V-RESTORE-ORDER", "task order preserves fed (LIVE-first) order, both shapes")
    else:
        _fail("V-RESTORE-ORDER", "order not preserved")

    # V-RESTORE-USES-KCLAUDE: every task launches through the kclaude wrapper,
    # whether directly (wave 0) or inside the delay wrapper (later waves).
    if tasks and all("kclaude" in launch_text(t) for t in tasks):
        n_delayed = sum(1 for t in tasks if t["type"] == "process")
        _ok("V-RESTORE-USES-KCLAUDE",
            f"13/13 launch via kclaude ({len(tasks) - n_delayed} immediate, {n_delayed} staggered)")
    else:
        _fail("V-RESTORE-USES-KCLAUDE", launch_text(tasks[0]) if tasks else "no tasks")

    # V-RESTORE-TRUNCATE-DEFAULT: the Cursor-tab cap still works when requested
    capped = va.build_cpc_tasks(panes, target_count=2)
    if len(capped) == 2:
        _ok("V-RESTORE-TRUNCATE-DEFAULT", "target_count=2 -> 2 tasks (cap intact)")
    else:
        _fail("V-RESTORE-TRUNCATE-DEFAULT", f"expected 2 got {len(capped)}")

    # V-RESTORE-GEN-NO-TRUNCATE: generate_from_snapshot(truncate=False) writes all
    with tempfile.TemporaryDirectory() as td:
        snap = os.path.join(td, "snap.json")
        with open(snap, "w", encoding="utf-8") as f:
            json.dump(panes, f)
        res = va.generate_from_snapshot(snap, dry_run=True, truncate=False)
        n = res[0]["n_tasks"] if res else 0
        if n == 13:
            _ok("V-RESTORE-GEN-NO-TRUNCATE", "generate_from_snapshot(truncate=False) -> 13 tasks")
        else:
            _fail("V-RESTORE-GEN-NO-TRUNCATE", f"expected 13 got {n}")

    print(f"RESTORE_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
