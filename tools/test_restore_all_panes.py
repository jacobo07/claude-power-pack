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

    # V-REVIVAL-TIER-FILTER: _panes_from_pane_map(tiers={OPEN-NOW,ACTIVE}) drops
    # RECENT-tier history so the always-on writer restores only what was actually
    # open, not 7 days of every session (T-REVIVAL-NOTRUNCATE-AUTORUN-HAZARD-001).
    pm = {"panes": [
        {"cwd": r"C:\r", "sessionId": "a" * 8, "tier": "OPEN-NOW"},
        {"cwd": r"C:\r", "sessionId": "b" * 8, "tier": "ACTIVE"},
        {"cwd": r"C:\r", "sessionId": "c" * 8, "tier": "RECENT"},
        {"cwd": r"C:\r", "sessionId": "d" * 8, "tier": "RECENT"},
    ]}
    all_panes = va._panes_from_pane_map(pm)
    scoped = va._panes_from_pane_map(pm, tiers={"OPEN-NOW", "ACTIVE"})
    if (len(all_panes) == 4 and len(scoped) == 2
            and {p["session_id"] for p in scoped} == {"a" * 8, "b" * 8}):
        _ok("V-REVIVAL-TIER-FILTER",
            "4 panes -> 2 kept under {OPEN-NOW, ACTIVE} (RECENT history dropped)")
    else:
        _fail("V-REVIVAL-TIER-FILTER",
              f"all={len(all_panes)} scoped={len(scoped)} "
              f"sids={sorted(p['session_id'] for p in scoped)}")

    # V-REVIVAL-STRIP-EMPTY: a repo that drops to 0 open panes under the tier
    # filter but HAS an existing tasks.json gets its CPC tasks STRIPPED (not left
    # as a stale no-truncate swarm), while foreign (non-CPC) tasks are preserved.
    # This is the other half of T-REVIVAL-NOTRUNCATE-AUTORUN-HAZARD-001.
    with tempfile.TemporaryDirectory() as td:
        repo = os.path.join(td, "StaleRepo")
        vdir = os.path.join(repo, ".vscode")
        os.makedirs(vdir)
        seed = {"version": "2.0.0", "tasks": [
            {"label": "old-restore", "detail": va.RESTORE_DETAIL, "command": "x", "args": []},
            {"label": "keepme", "type": "shell", "command": "echo"},
        ]}
        with open(os.path.join(vdir, "tasks.json"), "w", encoding="utf-8") as f:
            json.dump(seed, f)
        pm = os.path.join(td, "pane_map.json")
        with open(pm, "w", encoding="utf-8") as f:
            json.dump({"panes": [{"cwd": repo, "sessionId": "e" * 8, "tier": "RECENT"}]}, f)
        va.generate_from_pane_map(pm, tiers={"OPEN-NOW", "ACTIVE"})
        with open(os.path.join(vdir, "tasks.json"), encoding="utf-8") as f:
            after = json.load(f)
        labels = [t.get("label") for t in after["tasks"]]
        cpc_left = [t for t in after["tasks"] if t.get("detail") == va.RESTORE_DETAIL]
        if not cpc_left and "keepme" in labels:
            _ok("V-REVIVAL-STRIP-EMPTY", "0 open panes -> CPC tasks stripped, foreign task kept")
        else:
            _fail("V-REVIVAL-STRIP-EMPTY", f"cpc_left={len(cpc_left)} labels={labels}")

    print(f"RESTORE_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
