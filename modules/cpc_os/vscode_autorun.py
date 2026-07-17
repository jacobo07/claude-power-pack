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

# Legacy label prefix (pre-2026-07-06). Still detected on merge so a regenerate
# CLEANS old-format tasks, but new tasks no longer carry it in the visible label
# (the tab name is now the pane_map topic -- T-TERMINAL-NAME-FROM-PROFILE-001).
RESTORE_LABEL_PREFIX = "CPC-Restore:"
# The stable sentinel that marks a task as ours now lives in the task `detail`
# field, NOT the label -- so the label is free to be the human-readable topic
# while merge_tasks/_is_cpc_task still replace only our tasks idempotently.
RESTORE_DETAIL = "CPC-Restore autorun (pane_map label)"
TASKS_VERSION = "2.0.0"
BACKUP_SUFFIX = ".cpc-bak"
# Visible topic budget for the terminal/tab name (~40 chars "legible"); the
# 8-hex session id is appended AFTER this as the join key tab_order.js reads.
TERM_LABEL_MAX = 40

# Wave stagger (T-FOLDEROPEN-STAMPEDE-001). Every pane task carries
# runOn:folderOpen, and Cursor fires ALL of a repo's folderOpen tasks at once --
# so a 30-pane repo spawns 30 concurrent `claude --resume` handshakes on window
# open. dependsOn/dependsOrder cannot serialize them: a Claude session never
# exits, so a sequence chain would deadlock on the first task forever. The delay
# therefore lives INSIDE each task's command. Pane i waits
# (i // WAVE_SIZE) * WAVE_INTERVAL_S seconds, so panes start in waves of
# WAVE_SIZE. 0 disables the stagger (every task launches immediately).
WAVE_SIZE_DEFAULT = 5
WAVE_INTERVAL_S_DEFAULT = 8


def wave_delay_s(index: int, wave_size: int, interval_s: int) -> int:
    """Seconds pane ``index`` (0-based, within its repo) waits before launching.
    Wave 0 launches immediately, so the first WAVE_SIZE panes are never delayed
    and keep the exact pre-stagger task shape."""
    if wave_size <= 0 or interval_s <= 0 or index < 0:
        return 0
    return (index // wave_size) * interval_s


def _term_label(topic: str | None, repo: str | None, sid8: str) -> str:
    """Terminal/tab name for a restored pane: ``<repo> - <topic>`` truncated to
    TERM_LABEL_MAX, with the 8-hex session id appended so tab_order.js's
    ``sidPrefixOf`` can still join the tab back to a pane_map record. Fail-open
    (T-TERMINAL-NAME-FROM-PROFILE-001): no topic -> the repo name alone; no repo
    either -> a bare ``claude`` -- never an empty label (VS Code needs a label)."""
    topic = (topic or "").strip()
    repo = (repo or "").strip()
    if topic:
        base = f"{repo} - {topic}" if repo else topic
    else:
        base = repo or "claude"
    base = base[:TERM_LABEL_MAX].rstrip()
    return f"{base} {sid8}".strip()


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


def build_pane_task(resume: str, sid8: str, topic: str | None = None,
                    repo: str | None = None, delay_s: int = 0) -> dict:
    """One folderOpen task that launches a pane's resume command in its own
    dedicated terminal panel. The task ``label`` is the pane_map topic (VS Code
    names the task's terminal after its label -> the tab shows the topic, not the
    shell name "claude"/"cmd"). ``sid8`` (the 8-hex session id) keeps the label
    unique+stable AND is the join key tab_order.js reads back.

    ``delay_s`` > 0 staggers the launch (see WAVE_SIZE_DEFAULT): the task runs
    ``cmd /c timeout /t <delay_s> & bin/kclaude.cmd --resume <sid>``. Notes on the
    exact shape, both load-bearing:
      * ``type: process`` (not ``shell``) -- args reach cmd.exe as argv with no
        second round of shell quoting, which the default profile ("Last session")
        makes unpredictable.
      * ``&`` and NOT ``&&`` -- an unconditional chain. If ``timeout`` ever fails
        (e.g. stdin not a console), kclaude STILL launches: the stagger degrades
        to "no delay", never to "pane never came back"."""
    _command, args = parse_resume(resume)
    # Run via bin\kclaude.cmd -- the SAME wrapper the Owner's " kClaude" terminal
    # profile uses. kclaude.cmd is an 86-byte shim to bin\kclaude.ps1 (the W6
    # orchestrator), so a restored tab inherits the FULL CO gate stack (prelaunch
    # resume/coord + CO-08 cap eval + CO-00 advisory + scope recall/export + FIOS
    # preflight + the /restart loop that re-runs the gates) AND resumes the exact
    # session -- NOT the old ~/.claude/kclaude.bat (`claude %*`, no gates, itself
    # superseded 2026-06-23). Split-brain fix: T-REVIVAL-WRAPPER-SPLITBRAIN-001.
    # args are ["--resume","<sid>"] (exact) or [] (fresh).
    kclaude = "${env:USERPROFILE}\\.claude\\bin\\kclaude.cmd"
    if delay_s > 0:
        tail = (" " + " ".join(args)) if args else ""
        task_type = "process"
        command = "cmd"
        task_args = [
            "/c",
            f'timeout /t {delay_s} /nobreak >nul & "{kclaude}"{tail}',
        ]
    else:
        task_type = "shell"
        command = kclaude
        task_args = args
    return {
        "label": _term_label(topic, repo, sid8),
        # Stable sentinel (NOT the label) so merge_tasks replaces only our tasks.
        "detail": RESTORE_DETAIL,
        "type": task_type,
        "command": command,
        "args": task_args,
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
    wave_size: int = WAVE_SIZE_DEFAULT,
    wave_interval_s: int = WAVE_INTERVAL_S_DEFAULT,
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
        topic = p.get("topic")
        repo = p.get("repo") or (Path(p["cwd"]).name if p.get("cwd") else "")
        # Wave index is the POST-dedup position, so two panes sharing a session
        # (one task) never burn a slot. Truncation below keeps the first N tasks,
        # so the surviving delays stay a contiguous 0, 0.., interval, .. ladder.
        delay_s = wave_delay_s(len(seen), wave_size, wave_interval_s)
        seen[resume] = build_pane_task(resume, sid[:8], topic=topic, repo=repo,
                                       delay_s=delay_s)
    tasks = list(seen.values())

    if target_count and target_count > 0 and len(tasks) > target_count:
        # Truncate extras -- closed tabs. Keep the first (snapshot order =
        # active-first, most-recent-first) so the survivors are the live ones.
        tasks = tasks[:target_count]
    return tasks


def _is_cpc_task(task: dict) -> bool:
    # Match new tasks by the stable `detail` sentinel; still match the legacy
    # label prefix so a regenerate cleans pre-2026-07-06 tasks (topic labels
    # carry no prefix). Either signal -> ours -> replaced idempotently.
    if not isinstance(task, dict):
        return False
    if task.get("detail") == RESTORE_DETAIL:
        return True
    return str(task.get("label", "")).startswith(RESTORE_LABEL_PREFIX)


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
    wave_size: int = WAVE_SIZE_DEFAULT,
    wave_interval_s: int = WAVE_INTERVAL_S_DEFAULT,
) -> dict:
    """Generate/merge ``<cwd>/.vscode/tasks.json`` for one repo. Returns a
    result dict: {cwd, tasks_path, n_tasks, action, backed_up, parse_ok}.
    ``vscode_dir`` overrides the .vscode location (hermetic tests). dry_run
    computes everything and returns the doc WITHOUT touching disk.
    ``target_count`` (Cursor-authoritative tab count) forces exactly that many
    tasks; None keeps the legacy derived count (BL-CPCOS-RESTORE-004)."""
    cpc_tasks = build_cpc_tasks(panes_for_cwd, target_count=target_count,
                                wave_size=wave_size,
                                wave_interval_s=wave_interval_s)
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
    truncate: bool = True,
) -> list[dict]:
    """Read the snapshot sidecar and write an auto-run tasks.json per repo.
    ``cwds`` restricts to specific repos. ``tab_counts`` maps norm_path(cwd) to
    a live terminal-tab count; None captures it live (fail-open to {}).
    ``truncate`` False -> write ALL panes per repo (no tab-count cap): the
    pane_map-driven "restore every pane" mode (restore_panes.ps1 --no-truncate).
    When False we never import topology (no Cursor-state read needed)."""
    path = Path(snapshot_json)
    panes = json.loads(path.read_text(encoding="utf-8-sig"))
    norm_path = None
    if truncate:
        if tab_counts is None:
            try:
                from . import topology_reconcile
                tab_counts = topology_reconcile.current_tab_counts()
            except Exception:
                tab_counts = {}
        try:
            from .topology_reconcile import norm_path as norm_path
        except ImportError:  # run as a script (restore_panes.ps1 passes a file
            from topology_reconcile import norm_path as norm_path  # path, not -m)
    wanted = set(cwds) if cwds else None
    results: list[dict] = []
    for cwd, group in _group_by_cwd(panes).items():
        if wanted is not None and cwd not in wanted:
            continue
        target = (tab_counts or {}).get(norm_path(cwd)) if truncate else None
        results.append(write_autorun_for_cwd(
            cwd, group, dry_run=dry_run, target_count=target))
    return results


def _panes_from_pane_map(pane_map: dict,
                         tiers: "set[str] | None" = None) -> list[dict]:
    """Adapt pane_map.json records to the internal pane shape generate_from_snapshot
    consumes. The pane_map (built by build_pane_map.ps1 from disk truth) is the
    CORRECTED, all-repos/all-panes manifest -- it does not under-record repos/sids
    the way the legacy session_snapshot.json does, and its panel-facing `panes`
    array already excludes ARCHIVE-tier (stale-content) panes. Each record carries
    {cwd, sessionId, resumeCmd, topic, repo}; we map it to {cwd, session_id,
    resume:"claude --resume <sid>", topic, repo}. A pane with no sessionId or cwd is
    dropped (build_cpc_tasks would reject it anyway as an empty shell).

    ``tiers`` (upper-case pane_map tier names, e.g. {"OPEN-NOW", "ACTIVE"}) scopes
    the result to panes that were ACTUALLY OPEN, dropping RECENT-tier history. This
    is the fix for T-REVIVAL-NOTRUNCATE-AUTORUN-HAZARD-001: the always-on
    folderOpen writer must restore where the Owner WAS, not 7 days of every session
    (PP measured 33 panes -> 4 under {OPEN-NOW, ACTIVE}). None = no tier filter (the
    full-restore behavior the interactive restore_panes.ps1 -AutoRun keeps)."""
    out: list[dict] = []
    for p in (pane_map.get("panes") or []):
        if not isinstance(p, dict):
            continue
        sid = p.get("sessionId")
        cwd = p.get("cwd")
        if not sid or not cwd:
            continue
        if tiers is not None and (p.get("tier") or "").upper() not in tiers:
            continue                             # scope to what was actually open
        out.append({
            "cwd": cwd,
            "session_id": sid,
            # Normalize to the "claude --resume <sid>" form parse_resume expects;
            # build_pane_task rewrites the command to bin\kclaude.cmd regardless.
            "resume": f"claude --resume {sid}",
            "topic": p.get("topic"),
            "repo": p.get("repo") or (Path(cwd).name if cwd else ""),
        })
    return out


def generate_from_pane_map(
    pane_map_json: Path | str,
    cwds: list[str] | None = None,
    dry_run: bool = False,
    wave_size: int = WAVE_SIZE_DEFAULT,
    wave_interval_s: int = WAVE_INTERVAL_S_DEFAULT,
    tiers: "set[str] | None" = None,
) -> list[dict]:
    """Write an auto-run tasks.json per repo from the pane_map (disk-truth) source.

    This is the ALL-PANES, ALL-REPOS restore path: unlike generate_from_snapshot
    (which reads the under-recording session_snapshot.json and truncates to the
    live Cursor tab count), this reads the corrected pane_map.json and NEVER
    truncates (target_count=None) -- so every resumable pane of every repo becomes
    its own folderOpen task. Fixes the "1 pane per repo" + "only works in PP"
    automatic-path regressions at the source (the tasks.json Cursor auto-runs on a
    reboot). ``cwds`` restricts to specific repos; None = all repos in the map.

    Shared by tools/snapshot_auto_writer.ps1 (15-min background writer) and
    tools/restore_panes.ps1 -AutoRun so the pane_map->task transform lives in ONE
    place (no PowerShell/Python duplication)."""
    path = Path(pane_map_json)
    pane_map = json.loads(path.read_text(encoding="utf-8-sig"))
    all_panes = _panes_from_pane_map(pane_map)              # every repo (full set)
    kept = _panes_from_pane_map(pane_map, tiers=tiers)      # tier-scoped subset
    kept_by_cwd = _group_by_cwd(kept)
    # Iterate the repo order from the FULL set, not just the tier-scoped one: a repo
    # that drops to zero open panes under the filter must still be VISITED so its
    # stale CPC tasks (from a prior no-truncate write) get STRIPPED -- otherwise a
    # repo with nothing open keeps auto-launching its old 7-day swarm
    # (T-REVIVAL-NOTRUNCATE-AUTORUN-HAZARD-001). With tiers=None kept == all_panes,
    # so every group is non-empty and this is byte-identical to the old behavior.
    repo_order = list(_group_by_cwd(all_panes).keys())
    wanted = set(cwds) if cwds else None
    results: list[dict] = []
    for cwd in repo_order:
        if wanted is not None and cwd not in wanted:
            continue
        group = kept_by_cwd.get(cwd, [])
        # Never CREATE an empty tasks.json where none exists; only visit an
        # empty-after-filter repo when it HAS a tasks.json whose CPC tasks need
        # stripping. merge_tasks preserves the repo's non-CPC tasks either way.
        if not group and not (Path(cwd) / ".vscode" / "tasks.json").is_file():
            continue
        # target_count=None -> no truncation WITHIN the (already tier-scoped) group.
        results.append(write_autorun_for_cwd(
            cwd, group, dry_run=dry_run, target_count=None,
            wave_size=wave_size, wave_interval_s=wave_interval_s))
    return results


def _default_snapshot() -> Path:
    return Path.home() / ".claude" / "state" / "session_snapshot.json"


def _default_pane_map() -> Path:
    return Path.home() / ".claude" / "state" / "pane_map.json"


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
    ap.add_argument("--pane-map", dest="pane_map", nargs="?", const="__default__",
                    default=None,
                    help="read the corrected pane_map.json (all repos, all panes) "
                         "instead of the legacy snapshot; implies --no-truncate. "
                         "Bare flag uses ~/.claude/state/pane_map.json.")
    ap.add_argument("--cwd", action="append", default=None,
                    help="restrict to these repo cwd(s); repeatable")
    ap.add_argument("--dry-run", action="store_true",
                    help="preview without writing")
    ap.add_argument("--no-truncate", action="store_true",
                    help="write ALL panes per repo (no Cursor tab-count cap) -- "
                         "the pane_map-driven full-restore mode")
    ap.add_argument("--wave-size", type=int, default=WAVE_SIZE_DEFAULT,
                    help=f"panes launched per wave on folder open "
                         f"(default {WAVE_SIZE_DEFAULT}; 0 disables the stagger)")
    ap.add_argument("--wave-interval", type=int, default=WAVE_INTERVAL_S_DEFAULT,
                    help=f"seconds between waves (default {WAVE_INTERVAL_S_DEFAULT}; "
                         f"0 disables the stagger)")
    ap.add_argument("--tiers", default=None,
                    help="comma-separated pane_map tiers to keep (e.g. "
                         "OPEN-NOW,ACTIVE); default keeps every resumable pane. "
                         "Scopes the always-on folderOpen file to what was actually "
                         "open, not 7 days of history "
                         "(T-REVIVAL-NOTRUNCATE-AUTORUN-HAZARD-001).")
    args = ap.parse_args(argv)
    tiers = ({t.strip().upper() for t in args.tiers.split(",") if t.strip()}
             if args.tiers else None)

    # pane_map source (all repos, all panes -- the corrected disk-truth manifest).
    # Takes precedence over --snapshot; never truncates (that is the whole point).
    if args.pane_map is not None:
        pm = _default_pane_map() if args.pane_map == "__default__" else Path(args.pane_map)
        if not pm.is_file():
            print(f"[ERROR] pane_map not found: {pm}")
            return 1
        try:
            results = generate_from_pane_map(
                pm, cwds=args.cwd, dry_run=args.dry_run,
                wave_size=args.wave_size, wave_interval_s=args.wave_interval,
                tiers=tiers)
        except (OSError, ValueError) as e:  # noqa: BLE001
            print(f"[ERROR] cannot read pane_map: {e}")
            return 1
        for r in results:
            warn = "" if r["parse_ok"] else "  [existing tasks.json was JSONC -> backed up]"
            bak = "  (backup written)" if r.get("backed_up") else ""
            print(f"[{r['action']}] {r['cwd']}  ({r['n_tasks']} task(s)) "
                  f"-> {r['tasks_path']}{bak}{warn}")
        if not results:
            print("[INFO] no repos in pane_map; nothing to auto-run.")
        return 0

    snap = Path(args.snapshot) if args.snapshot else _default_snapshot()
    if not snap.is_file():
        print(f"[ERROR] snapshot not found: {snap}")
        return 1
    try:
        results = generate_from_snapshot(snap, cwds=args.cwd, dry_run=args.dry_run,
                                         truncate=not args.no_truncate)
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
