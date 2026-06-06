#!/usr/bin/env python3
"""test_vscode_autorun.py -- V-gates for the CPC-OS auto-run enhancement.

Hermetic: every write goes to a tempfile.TemporaryDirectory; no real repo and
no user-scope path is touched. Exercises the pure builders AND the disk path
(merge / backup / idempotency / JSONC safety / from-snapshot).
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.cpc_os import vscode_autorun as va  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"OK   {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"FAIL {gate}: {diag}")


def _pane(cwd: str, resume: str, kind: str = "exact", repo: str = "r",
          pane_id: str = "p") -> dict:
    return {"cwd": cwd, "resume": resume, "resume_kind": kind, "repo": repo,
            "pane_id": pane_id}


def main() -> int:
    # --- parse_resume ---------------------------------------------------
    cmd, args = va.parse_resume("claude --resume abc12345")
    if cmd == "claude" and args == ["--resume", "abc12345"]:
        _ok("V-AUTORUN-PARSE-EXACT", f"{cmd} {args}")
    else:
        _fail("V-AUTORUN-PARSE-EXACT", f"got {cmd} {args}")

    cmd, args = va.parse_resume('cd "C:\\Users\\x" && claude')
    if cmd == "claude" and args == []:
        _ok("V-AUTORUN-PARSE-NEW", "cd-fallback -> bare claude in workspace")
    else:
        _fail("V-AUTORUN-PARSE-NEW", f"got {cmd} {args}")

    # --- task shape: folderOpen + dedicated -----------------------------
    task = va.build_pane_task("claude --resume zzz99999", "zzz99999 [exact]")
    ro = task.get("runOptions", {}).get("runOn")
    panel = task.get("presentation", {}).get("panel")
    if ro == "folderOpen" and panel == "dedicated" and task["args"] == ["--resume", "zzz99999"]:
        _ok("V-AUTORUN-TASK-FOLDEROPEN", f"runOn={ro}, panel={panel}")
    else:
        _fail("V-AUTORUN-TASK-FOLDEROPEN", f"runOn={ro}, panel={panel}, args={task['args']}")

    # --- dedup: same resume -> 1 task, distinct -> 2 --------------------
    panes = [
        _pane("C:\\repoA", "claude --resume aaa", "exact"),
        _pane("C:\\repoA", "claude --resume aaa", "repo-latest"),  # dup resume
        _pane("C:\\repoA", "claude --resume bbb", "exact"),
    ]
    tasks = va.build_cpc_tasks(panes)
    if len(tasks) == 2:
        _ok("V-AUTORUN-DEDUP", "3 panes / 2 distinct resume -> 2 tasks")
    else:
        _fail("V-AUTORUN-DEDUP", f"expected 2, got {len(tasks)}")

    # --- merge preserves the Owner's own tasks --------------------------
    existing = {
        "version": "2.0.0",
        "tasks": [
            {"label": "Build", "type": "shell", "command": "npm run build"},
            {"label": "CPC-Restore: old [exact]", "type": "shell", "command": "claude"},
        ],
    }
    merged = va.merge_tasks(existing, va.build_cpc_tasks(panes))
    labels = [t["label"] for t in merged["tasks"]]
    has_owner = "Build" in labels
    old_cpc_gone = "CPC-Restore: old [exact]" not in labels
    has_new_cpc = any(l.startswith("CPC-Restore:") for l in labels)
    if has_owner and old_cpc_gone and has_new_cpc:
        _ok("V-AUTORUN-MERGE-PRESERVES", f"kept Build; replaced old CPC; labels={labels}")
    else:
        _fail("V-AUTORUN-MERGE-PRESERVES",
              f"owner={has_owner} old_gone={old_cpc_gone} new={has_new_cpc} labels={labels}")

    # --- disk: write is hermetic + valid JSON + folderOpen --------------
    with tempfile.TemporaryDirectory() as td:
        vdir = Path(td) / ".vscode"
        res = va.write_autorun_for_cwd("C:\\repoA", panes, vscode_dir=vdir)
        tasks_path = Path(res["tasks_path"])
        doc = json.loads(tasks_path.read_text(encoding="utf-8"))
        n_folderopen = sum(
            1 for t in doc["tasks"]
            if t.get("runOptions", {}).get("runOn") == "folderOpen"
        )
        if tasks_path.is_file() and n_folderopen == 2 and res["action"] == "create":
            _ok("V-AUTORUN-WRITE-HERMETIC", f"{tasks_path.name}: {n_folderopen} folderOpen tasks")
        else:
            _fail("V-AUTORUN-WRITE-HERMETIC",
                  f"exists={tasks_path.is_file()} folderOpen={n_folderopen} action={res['action']}")

        # --- idempotent skip on unchanged + backup on real change ------
        res2 = va.write_autorun_for_cwd("C:\\repoA", panes, vscode_dir=vdir)
        bak = tasks_path.with_name(tasks_path.name + va.BACKUP_SUFFIX)
        unchanged_ok = (res2["action"] == "unchanged"
                        and not res2["backed_up"] and not bak.is_file())
        # change the panes -> a real update must back up first then rewrite
        panes_changed = panes + [_pane("C:\\repoA", "claude --resume ccc", "exact")]
        res3 = va.write_autorun_for_cwd("C:\\repoA", panes_changed, vscode_dir=vdir)
        doc3 = json.loads(tasks_path.read_text(encoding="utf-8"))
        n_cpc = sum(1 for t in doc3["tasks"] if t["label"].startswith("CPC-Restore:"))
        if (unchanged_ok and res3["action"] == "update"
                and res3["backed_up"] and bak.is_file() and n_cpc == 3):
            _ok("V-AUTORUN-IDEMPOTENT-SKIP",
                "unchanged rerun skipped (no write/backup); changed -> update+backup, 3 CPC")
        else:
            _fail("V-AUTORUN-IDEMPOTENT-SKIP",
                  f"unchanged={unchanged_ok} action3={res3['action']} "
                  f"backed3={res3['backed_up']} n_cpc={n_cpc}")

    # --- JSONC existing -> backed up, fresh written, parse_ok False -----
    with tempfile.TemporaryDirectory() as td:
        vdir = Path(td) / ".vscode"
        vdir.mkdir(parents=True)
        jsonc = vdir / "tasks.json"
        jsonc.write_text('{\n  // a comment JSON cannot parse\n  "version":"2.0.0",\n'
                         '  "tasks":[],\n}\n', encoding="utf-8")
        res = va.write_autorun_for_cwd("C:\\repoB",
                                       [_pane("C:\\repoB", "claude --resume ccc")],
                                       vscode_dir=vdir)
        bak = jsonc.with_name(jsonc.name + va.BACKUP_SUFFIX)
        doc = json.loads(jsonc.read_text(encoding="utf-8"))
        if res["parse_ok"] is False and bak.is_file() and len(doc["tasks"]) == 1:
            _ok("V-AUTORUN-JSONC-SAFE", "un-parseable existing backed up; fresh tasks written")
        else:
            _fail("V-AUTORUN-JSONC-SAFE",
                  f"parse_ok={res['parse_ok']} bak={bak.is_file()} tasks={len(doc['tasks'])}")

    # --- from-snapshot end-to-end (temp cwds = temp dirs) ---------------
    with tempfile.TemporaryDirectory() as td:
        repo1 = Path(td) / "repo1"
        repo2 = Path(td) / "repo2"
        repo1.mkdir()
        repo2.mkdir()
        snap = Path(td) / "snap.json"
        snap.write_text(json.dumps([
            _pane(str(repo1), "claude --resume r1aaa", "exact"),
            _pane(str(repo1), "claude --resume r1aaa", "repo-latest"),
            _pane(str(repo2), "claude --resume r2bbb", "exact"),
        ]), encoding="utf-8")
        results = va.generate_from_snapshot(snap)
        f1 = repo1 / ".vscode" / "tasks.json"
        f2 = repo2 / ".vscode" / "tasks.json"
        ok = (len(results) == 2 and f1.is_file() and f2.is_file()
              and len(json.loads(f1.read_text())["tasks"]) == 1
              and len(json.loads(f2.read_text())["tasks"]) == 1)
        if ok:
            _ok("V-AUTORUN-FROM-SNAPSHOT", "2 repos -> 2 tasks.json (repo1 deduped to 1)")
        else:
            _fail("V-AUTORUN-FROM-SNAPSHOT", f"results={len(results)} f1={f1.is_file()} f2={f2.is_file()}")

        # dry-run writes nothing new
        for f in (f1, f2):
            f.unlink()
        dry = va.generate_from_snapshot(snap, dry_run=True)
        if not f1.exists() and not f2.exists() and all(r["action"] == "dry-run" for r in dry):
            _ok("V-AUTORUN-DRYRUN", "dry-run touched no disk")
        else:
            _fail("V-AUTORUN-DRYRUN", f"f1={f1.exists()} f2={f2.exists()}")

    print(f"AUTORUN_PASS={_passes}/{_passes + _fails}  fails={_fails}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
