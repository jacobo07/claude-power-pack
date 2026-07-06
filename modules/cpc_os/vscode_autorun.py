"""vscode_autorun.py -- auto-run `claude --resume <id>` per pane on Cursor open.

Auto-Run enhancement for CPC-OS crash restore (2026-06-06). The base restore
flow (restore_panes.ps1) reopens each repo as a Cursor window and PRINTS the
`claude --resume <id>` line for the Owner to paste. This module closes the last
manual step: it writes a `.vscode/tasks.json` into each repo so that, on the
next folder-open, Cursor AUTO-RUNS the resume command(s) -- each distinct pane
session in its own dedicated terminal panel. The Owner opens Cursor and the
panes come back on their exact conversations with zero pasting.

Mechanism (standard VS Code / Cursor): a task with
``"runOptions": {"runOn": "folderOpen"}`` executes when the workspace folder is
opened in a trusted window. Multiple such tasks all fire; each with
``presentation.panel == "dedicated"`` gets its own terminal. So N distinct pane
sessions -> N dedicated terminals, each launching ``claude --resume <sid>``.

Design contract (non-destructive, opt-in):
  * MERGE, never clobber: a pre-existing tasks.json keeps every task the Owner
    authored; only ``CPC-Restore:``-labelled tasks are replaced.
  * BACKUP first: the prior tasks.json is copied to ``tasks.json.cpc-bak``
    before any write (also the safety net when the existing file is JSONC the
    strict parser cannot read -- we never silently lose Owner data).
  * DEDUP per repo: panes that resolve to the SAME resume command produce ONE
    task (matches restore_panes.ps1's per-repo dedup).
  * STALE by nature: session_ids change every session, so the tasks.json is a
    point-in-time restore artifact -- regenerate it at each restore.

Composes the snapshot sidecar (SCS C28): reads the same
``session_snapshot.json`` the restore script reads; no new pane discovery.

API (all hermetic -- pass explicit paths so tests touch only temp dirs):
  parse_resume(resume)              -> (command, args)
  build_pane_task(resume, pane_id)  -> dict (one folderOpen task)
  build_cpc_tasks(panes_for_cwd)    -> list[dict] (deduped, labelled)
  merge_tasks(existing, cpc_tasks)  -> dict (preserve non-CPC tasks)
  write_autorun_for_cwd(cwd, panes, vscode_dir=None, dry_run=False) -> dict
  generate_from_snapshot(snapshot_json, cwds=None, dry_run=False)   -> list[dict]
"""
from __future__ import annotations

import json
import shutil
from collections import OrderedDict
from pathlib import Path

# Every injected task carries this label prefix so a re-generate replaces ONLY
# our tasks and leaves the Owner's own tasks untouched.
RESTORE_LABEL_PREFIX = "CPC-Restore:"
TASKS_VERSION = "2.0.0"
BACKUP_SUFFIX = ".cpc-bak"


def parse_resume(resume: str) -> tuple[str, list[str]]:
    """Split a snapshot ``resume`` string into (command, args) for a VS Code
    task. The snapshot emits one of:
      * ``claude --resume <sid>``      -> ("claude", ["--resume", "<sid>"])
      * ``cd "<cwd>" && claude``       -> ("claude", [])  (cwd is the workspace)
    Anything unrecognised falls back to a bare ``claude`` in the workspace, so a
    task is always launchable (never an empty command)."""
    s = (resume or "").strip()
    if "--resume" in s:
        # The session id is the token right after --resume.
        toks = s.split()
        try:
            idx = toks.index("--resume")
            sid = toks[idx + 1]
            return "claude", ["--resume", sid]
        except (ValueError, IndexError):
            return "claude", []
    return "claude", []


def build_pane_task(resume: str, label_key: str) -> dict:
    """One folderOpen task that launches a pane's resume command in its own
    dedicated terminal panel. ``label_key`` makes the label unique+stable."""
    _command, args = parse_resume(resume)
    # Run via kclaude.bat -- the SAME wrapper the Owner's "Claude" terminal
    # profile uses (cmd /K kclaude.bat ...). It passes args straight through to
    # `claude` on first launch (claude %*) and adds the /restart loop, so a
    # restored tab behaves exactly like a hand-opened Claude terminal but pinned
    # to the exact session. args are ["--resume","<sid>"] (exact) or [] (fresh).
    kclaude = "${env:USERPROFILE}\\.claude\\kclaude.bat"
    return {
        "label": f"{RESTORE_LABEL_PREFIX} {label_key}",
        "type": "shell",
        "command": kclaude,
        "args": args,
        "options": {"cwd": "${workspaceFolder}"},
        "presentation": {
            "panel": "dedicated",
            # NO shared "group": in VS Code / Cursor a shared presentation.group
            # SPLITS every task into one terminal group (side-by-side panes).
            # The Owner wants each restored chat as its OWN terminal TAB, so we
            # omit group entirely -> panel:"dedicated" alone gives one dedicated
            # tab per task (BL-CPCOS-RESTORE-002, 2026-06-08).
            "reveal": "always",
            "focus": False,
            "echo": False,
            "clear": False,
        },
        "runOptions": {"runOn": "folderOpen"},
        "problemMatcher": [],
    }


def build_cpc_tasks(
    panes_for_cwd: list[dict],
    target_count: int | None = None,
) -> list[dict]:
    """Deduped list of CPC-Restore tasks for one repo. Dedup key is the resume
    command itself (panes that resolve to the same session share one terminal,
    mirroring restore_panes.ps1). Label key prefers a readable session tail.

    EMPTY-SHELL EXCLUSION (BL-CPCOS-RESTORE-005, 2026-07-03, Owner decision "no
    recrear empty shells"): a pane whose resume does NOT resolve to an explicit
    ``--resume <sid>`` is an EMPTY SHELL -- a tab that opened but never produced
    a transcript (its ``<sid>.jsonl`` was never born, verified absent on disk).
    Recreating it launches a THROWAWAY fresh ``claude`` (+ the CO-08 "opening a
    new one anyway" advisory + Cursor's "History restored"), which the Owner
    reads as a lost session. So a non-resumable pane emits NO task and is NEVER
    padded back in. This SUPERSEDES the BL-CPCOS-RESTORE-004 count-parity
    padding: an unused shell is not worth resurrecting as an empty Claude tab.

    ``target_count`` (Cursor-authoritative) now serves ONLY to TRUNCATE: when
    more distinct RESOLVED sessions exist than live tabs, the extras belong to
    tabs the Owner has since closed. It never pads. ``None`` / non-positive ->
    no truncation (every resolved session becomes a task)."""
    seen: "OrderedDict[str, dict]" = OrderedDict()
    for p in panes_for_cwd:
        resume = (p.get("resume") or "").strip()
        if not resume or resume in seen:
            continue
        _cmd, args = parse_resume(resume)
        if len(args) != 2:                       # empty shell -> never recreate
            continue
        sid = args[1]                            # args == ["--resume", "<sid>"]
        kind = p.get("resume_kind") or "exact"
        seen[resume] = build_pane_task(resume, f"{sid[:8]} [{kind}]")
    tasks = list(seen.values())

    if target_count and target_count > 0 and len(tasks) > target_count:
        # Truncate extras -- closed tabs. Keep the first (snapshot order =
        # active-first, most-recent-first) so the survivors are the live ones.
        tasks = tasks[:target_count]
    return tasks


def _is_cpc_task(task: dict) -> bool:
    return isinstance(task, dict) and str(
        task.get("label", "")
    ).startswith(RESTORE_LABEL_PREFIX)


def merge_tasks(existing: dict | None, cpc_tasks: list[dict]) -> dict:
    """Return a tasks.json doc that keeps every NON-CPC task from ``existing``
    and (re)installs ``cpc_tasks``. Idempotent: running twice yields the same
    set (old CPC tasks are dropped before the new ones are added)."""
    doc: dict = {}
    kept: list[dict] = []
    if isinstance(existing, dict):
        doc = dict(existing)                     # shallow copy of top-level keys
        for t in existing.get("tasks", []) or []:
            if not _is_cpc_task(t):
                kept.append(t)
    doc["version"] = doc.get("version", TASKS_VERSION)
    doc["tasks"] = kept + cpc_tasks
    return doc


def _read_existing(tasks_path: Path) -> tuple[dict | None, bool]:
    """(parsed_doc, parse_ok). parse_ok is False when the file exists but is not
    strict JSON (e.g. JSONC with comments/trailing commas) -- the caller then
    relies on the backup so no Owner data is lost."""
    if not tasks_path.is_file():
        return None, True
    try:
        return json.loads(tasks_path.read_text(encoding="utf-8-sig")), True
    except (OSError, ValueError):
        return None, False


def write_autorun_for_cwd(
    cwd: str,
    panes_for_cwd: list[dict],
    vscode_dir: Path | str | None = None,
    dry_run: bool = False,
    target_count: int | None = None,
) -> dict:
    """Generate/merge ``<cwd>/.vscode/tasks.json`` for one repo. Returns a
    result dict: {cwd, tasks_path, n_tasks, action, backed_up, parse_ok}.
    ``vscode_dir`` overrides the .vscode location (hermetic tests). dry_run
    computes everything and returns the doc WITHOUT touching disk.
    ``target_count`` (Cursor-authoritative tab count) forces exactly that many
    tasks; None keeps the legacy derived count (BL-CPCOS-RESTORE-004)."""
    cpc_tasks = build_cpc_tasks(panes_for_cwd, target_count=target_count)
    vdir = Path(vscode_dir) if vscode_dir else Path(cwd) / ".vscode"
    tasks_path = vdir / "tasks.json"

    existing, parse_ok = _read_existing(tasks_path)
    merged = merge_tasks(existing if parse_ok else None, cpc_tasks)

    if dry_run:
        action = "dry-run"
    elif existing is None:
        action = "create"
    elif parse_ok and existing == merged:
        # Idempotent: the on-disk doc already matches. Critical for the 15-min
        # periodic writer -- skip the write so unchanged repos do not churn
        # (no mtime bump, no backup rewrite) every cycle.
        action = "unchanged"
    else:
        action = "update"

    result = {
        "cwd": cwd,
        "tasks_path": str(tasks_path),
        "n_tasks": len(cpc_tasks),
        "action": action,
        "backed_up": False,
        "parse_ok": parse_ok,
        "doc": merged,
    }
    if dry_run or action == "unchanged":
        return result

    vdir.mkdir(parents=True, exist_ok=True)
    if tasks_path.is_file():
        try:
            shutil.copy2(tasks_path, tasks_path.with_name(tasks_path.name + BACKUP_SUFFIX))
            result["backed_up"] = True
        except OSError:
            result["backed_up"] = False
    tasks_path.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    return result


def _group_by_cwd(panes: list[dict]) -> "OrderedDict[str, list[dict]]":
    groups: "OrderedDict[str, list[dict]]" = OrderedDict()
    for p in panes:
        cwd = p.get("cwd")
        if not cwd:
            continue
        groups.setdefault(cwd, []).append(p)
    return groups


def generate_from_snapshot(
    snapshot_json: Path | str,
    cwds: list[str] | None = None,
    dry_run: bool = False,
    tab_counts: dict[str, int] | None = None,
) -> list[dict]:
    """Read the snapshot sidecar and write an auto-run tasks.json per repo.
    ``cwds`` restricts to specific repos. ``tab_counts`` maps norm_path(cwd) to
    a live terminal-tab count; None captures it live (fail-open to {})."""
    path = Path(snapshot_json)
    panes = json.loads(path.read_text(encoding="utf-8-sig"))
    if tab_counts is None:
        try:
            from . import topology_reconcile
            tab_counts = topology_reconcile.current_tab_counts()
        except Exception:
            tab_counts = {}
    try:
        from .topology_reconcile import norm_path
    except ImportError:  # run as a script (restore_panes.ps1 passes a file path,
        from topology_reconcile import norm_path  # not -m): own dir is on sys.path
    wanted = set(cwds) if cwds else None
    results: list[dict] = []
    for cwd, group in _group_by_cwd(panes).items():
        if wanted is not None and cwd not in wanted:
            continue
        target = (tab_counts or {}).get(norm_path(cwd))
        results.append(write_autorun_for_cwd(
            cwd, group, dry_run=dry_run, target_count=target))
    return results


def _default_snapshot() -> Path:
    return Path.home() / ".claude" / "state" / "session_snapshot.json"


def main(argv=None) -> int:
    """CLI used by restore_panes.ps1 -AutoRun. Writes one .vscode/tasks.json per
    repo found in the snapshot (or --dry-run to preview). Exit 0 on success."""
    import argparse

    ap = argparse.ArgumentParser(
        description="Write per-repo .vscode/tasks.json that auto-runs "
                    "`claude --resume` when Cursor opens the folder."
    )
    ap.add_argument("--snapshot", default=None,
                    help="snapshot json (default ~/.claude/state/session_snapshot.json)")
    ap.add_argument("--cwd", action="append", default=None,
                    help="restrict to these repo cwd(s); repeatable")
    ap.add_argument("--dry-run", action="store_true",
                    help="preview without writing")
    args = ap.parse_args(argv)

    snap = Path(args.snapshot) if args.snapshot else _default_snapshot()
    if not snap.is_file():
        print(f"[ERROR] snapshot not found: {snap}")
        return 1
    try:
        results = generate_from_snapshot(snap, cwds=args.cwd, dry_run=args.dry_run)
    except (OSError, ValueError) as e:  # noqa: BLE001
        print(f"[ERROR] cannot read snapshot: {e}")
        return 1
    if not results:
        print("[INFO] no repos in snapshot; nothing to auto-run.")
        return 0
    for r in results:
        warn = "" if r["parse_ok"] else "  [existing tasks.json was JSONC -> backed up]"
        bak = "  (backup written)" if r.get("backed_up") else ""
        print(f"[{r['action']}] {r['cwd']}  ({r['n_tasks']} task(s)) "
              f"-> {r['tasks_path']}{bak}{warn}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
