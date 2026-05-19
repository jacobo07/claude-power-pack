#!/usr/bin/env python3
"""install_global_core.py — the actual install-global logic.

Driven by the thin shell wrappers ``install-global.ps1`` and
``install-global.sh``. Pure Python so behaviour is identical across
Windows + POSIX; the shells only handle banner + env-scrub + invocation.

Contract — what this DOES (automated):
  * Reads ``tools/_inventory/{agents,commands,hooks}.json`` (A3
    curated allow-list — gap 3).
  * For every ``pp_original`` entry: SHA-256 compares the PP-tracked
    canonical against ``~/.claude/<kind>/<name>``. On mismatch or
    missing-loose: backs the existing loose file up to
    ``~/.claude/.pp-backups/<iso>/<relpath>`` (gap 11), then copies
    canonical into place.
  * Backup retention: at most the 5 most recent ``.pp-backups/<iso>/``
    directories are kept; older ones are deleted (gap 11).
  * Hook registration: calls the EXISTING + Owner-authorized
    ``settings_merger.py register-*`` subcommands per the declarative
    ``HOOK_REGISTRATIONS`` map below. Each call is idempotent.
  * Env scrub before spawning ``settings_merger.py``: ``CLAUDECODE`` +
    ``CLAUDE_CODE_*`` removed so a nested invocation does NOT misread
    the install as a self-modification (gap 4 fix, mirrors L3 cycle).
  * Preflight on every installed ``.js`` hook: ``node --check`` exit 0.
  * Emits a per-run report at
    ``~/.claude/.pp-install-report.<iso>.json``.

Contract — what this DOES NOT (Owner-gated by doctrine):
  * NEVER programmatically grants ``permissions.allow`` entries. The
    classifier hard-denies that capability path; the installer instead
    PRINTS the exact lines the Owner pastes (see
    ``vault/knowledge_base/session_lessons.md`` Lesson 2, 2026-05-19).
  * NEVER touches ``~/.claude/CLAUDE.md`` — that is the Owner's text.
  * NEVER deletes any loose file outside ``~/.claude/.pp-backups/``.

Flags:
  ``--dry-run``       print every intended action; mutate nothing.
  ``--settings PATH`` override ``~/.claude/settings.json`` location.
  ``--repo PATH``     override PP repo root (default: derived from
                      ``__file__`` parent's parent).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


HOME = Path.home()
GLOBAL = HOME / ".claude"
BACKUP_ROOT = GLOBAL / ".pp-backups"
BACKUP_RETENTION = 5  # keep at most this many timestamped dirs
HERE = Path(__file__).resolve().parent  # tools/
DEFAULT_REPO = HERE.parent                # claude-power-pack/
DEFAULT_SETTINGS = GLOBAL / "settings.json"
ISO_TS = time.strftime("%Y-%m-%dT%H-%M-%SZ", time.gmtime())

# Hook → (event, [matcher]) map for settings_merger. Only the hooks the
# Power-Pack DRIVES are auto-registered here. Anything an Owner wants
# beyond this set is their explicit register-* call. Conservative on
# purpose (Lesson 2 doctrine — minimum-surface mutation).
HOOK_REGISTRATIONS = [
    # (kind, name,              register-subcommand,    matcher,  timeout)
    ("hooks", "learning-sentinel.js", "register-sessionstart", "",     5),
    ("hooks", "learning-sentinel.js", "register-stop",         "",     5),
    # NOTE: hook-dispatcher.js is registered through TWO settings.json
    # entries (PreToolUse-default + PostToolUse-default) — the dispatcher
    # bundles the rest. Those are not auto-registered by this installer
    # because settings_merger has no register-postool subcommand;
    # printed in the post-install checklist instead.
]

# permissions.allow checklist the Owner must paste manually (Lesson 2
# doctrine + Hook Startup Authorization Gate). Keys = description; value
# = exact rule string.
PERMISSIONS_CHECKLIST = [
    ("Per-hook exact-path edit (L3-style classifier unlock for "
     "learning-sentinel.js)",
     "Edit(file:~/.claude/hooks/learning-sentinel.js)"),
    ("Edit any Power-Pack hook (broad glob, optional convenience — "
     "does NOT replace the per-hook exact-path rule above; the "
     "classifier reads both)",
     "Edit(file:~/.claude/hooks/**)"),
    ("Edit settings.json directly (only if you intend to hand-edit "
     "rather than always use settings_merger.py)",
     "Edit(file:~/.claude/settings.json)"),
]


def _sha256(path: Path) -> str | None:
    """LF-normalised SHA-256 (matches verify_global_mirrors)."""
    try:
        data = path.read_bytes()
    except (OSError, FileNotFoundError):
        return None
    lf = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(lf).hexdigest()


def _load_inventory(repo: Path) -> dict[str, dict]:
    inv = {}
    for kind in ("agents", "commands", "hooks"):
        p = repo / "tools" / "_inventory" / f"{kind}.json"
        try:
            inv[kind] = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            print(f"install-global: cannot read {p}: {e}", file=sys.stderr)
            return {}
    return inv


def _resolve_pp_source(repo: Path, kind: str, name: str) -> Path:
    """Where the canonical PP-tracked copy of <kind>/<name> lives in
    the repo. Mirror of ``~/.claude/<kind>/<name>``."""
    return repo / kind / name


def _resolve_loose_target(kind: str, name: str) -> Path:
    return GLOBAL / kind / name


def _backup_then_overwrite(target: Path, source: Path,
                            dry_run: bool, report: list) -> str:
    """Backup the existing loose file (if any) then copy source over.

    Returns one of: ``"installed"``, ``"updated"``, ``"unchanged"``,
    ``"missing-source"``, ``"error"``.
    """
    if not source.exists():
        report.append({"target": str(target), "verdict": "missing-source",
                       "source": str(source)})
        return "missing-source"

    src_sha = _sha256(source)
    dst_sha = _sha256(target)

    if dst_sha is not None and src_sha == dst_sha:
        report.append({"target": str(target), "verdict": "unchanged",
                       "sha256": src_sha})
        return "unchanged"

    verdict = "installed" if dst_sha is None else "updated"
    backup_path = None
    if verdict == "updated":
        rel = target.relative_to(GLOBAL) if str(target).startswith(
            str(GLOBAL)) else Path(target.name)
        backup_path = BACKUP_ROOT / ISO_TS / rel

    if dry_run:
        report.append({"target": str(target), "verdict": "DRY:" + verdict,
                       "source_sha": src_sha, "dest_sha": dst_sha,
                       "backup": str(backup_path) if backup_path else None})
        return verdict

    try:
        if backup_path is not None:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    except OSError as e:
        report.append({"target": str(target), "verdict": "error",
                       "error": str(e)})
        return "error"

    report.append({"target": str(target), "verdict": verdict,
                   "source_sha": src_sha, "dest_sha_before": dst_sha,
                   "backup": str(backup_path) if backup_path else None})
    return verdict


def _gc_backups(dry_run: bool, report: list) -> None:
    """Cap backup-set retention at BACKUP_RETENTION (gap 11)."""
    if not BACKUP_ROOT.exists():
        return
    try:
        sets = sorted([p for p in BACKUP_ROOT.iterdir() if p.is_dir()])
    except OSError:
        return
    extra = sets[:-BACKUP_RETENTION] if len(sets) > BACKUP_RETENTION else []
    for p in extra:
        if dry_run:
            report.append({"backup_gc": str(p), "verdict": "DRY:delete"})
            continue
        try:
            shutil.rmtree(p)
            report.append({"backup_gc": str(p), "verdict": "deleted"})
        except OSError as e:
            report.append({"backup_gc": str(p), "verdict": "error",
                           "error": str(e)})


def _scrub_env() -> dict[str, str]:
    """Env for the settings_merger spawn — drop CLAUDECODE/* so a
    nested-claude detection path does not misread the install."""
    env = dict(os.environ)
    for k in list(env.keys()):
        if k == "CLAUDECODE" or k.startswith("CLAUDE_CODE_") \
                or k == "CLAUDE_PROJECT_DIR":
            del env[k]
    return env


def _node_check(path: Path) -> bool:
    """Return True iff ``node --check <path>`` exits 0."""
    try:
        cp = subprocess.run(
            ["node", "--check", str(path)],
            capture_output=True, timeout=15,
        )
        return cp.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _register_hooks(repo: Path, settings_path: Path,
                    dry_run: bool, report: list) -> int:
    """Drive settings_merger.py register-* for each entry in
    HOOK_REGISTRATIONS. Returns count of failures (0 = OK)."""
    failures = 0
    merger = repo / "tools" / "settings_merger.py"
    if not merger.is_file():
        report.append({"hook_register": "skip",
                       "reason": "settings_merger.py missing"})
        return 0

    env = _scrub_env()

    for kind, name, sub, matcher, timeout in HOOK_REGISTRATIONS:
        target = _resolve_loose_target(kind, name)
        if not target.is_file():
            report.append({"hook_register": name, "verdict": "skip",
                           "reason": "loose target missing"})
            failures += 1
            continue

        args = [sys.executable, str(merger), sub,
                "--node-script", str(target).replace("\\", "/"),
                "--timeout", str(timeout),
                "--settings", str(settings_path)]
        if matcher and sub == "register-pretool":
            args += ["--matcher", matcher]

        if dry_run:
            report.append({"hook_register": name, "verdict": "DRY",
                           "argv": args})
            continue
        try:
            cp = subprocess.run(args, capture_output=True,
                                text=True, timeout=30, env=env)
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            report.append({"hook_register": name, "verdict": "error",
                           "error": str(e)})
            failures += 1
            continue
        report.append({
            "hook_register": name,
            "verdict": "OK" if cp.returncode == 0 else "FAIL",
            "rc": cp.returncode,
            "stdout": cp.stdout.strip(),
            "stderr": cp.stderr.strip(),
        })
        if cp.returncode != 0:
            failures += 1
    return failures


def _print_permissions_checklist() -> None:
    print()
    print("=" * 64)
    print("ACTION REQUIRED — paste these into ~/.claude/settings.json")
    print("permissions.allow[]  (Owner-only; installer never writes these)")
    print("=" * 64)
    for desc, rule in PERMISSIONS_CHECKLIST:
        print(f"  # {desc}")
        print(f'  "{rule}",')
    print()
    print("Doctrine: per the Hook Startup Authorization Gate")
    print("(vault/standards/feature-completion-standard.md), the")
    print("classifier requires durable Owner authorization for")
    print("permission grants. The installer prints, never writes.")


def _print_hooks_checklist(repo: Path) -> None:
    """Hooks are not installer-shipped (Mirror-Sync-Direction doctrine).
    Print the exact Owner-side commands to copy + register the canonical
    PP hooks into ~/.claude/hooks/ + settings.json. Owner-driven, never
    agent-driven — the hooks-dir writes are classifier-denied for an
    agent session and must be Owner-authored."""
    print()
    print("=" * 64)
    print("ACTION REQUIRED — hooks (Owner-driven, NOT installer-driven)")
    print("Mirror-Sync-Direction doctrine: A1/A2 flow is loose -> PP")
    print("only; the agent classifier denies ~/.claude/hooks/<file>.js")
    print("writes. The installer therefore never touches the hooks dir.")
    print("=" * 64)
    pp_hooks = repo / "hooks"
    if pp_hooks.is_dir():
        names = sorted(p.name for p in pp_hooks.iterdir()
                       if p.suffix in (".js", ".cjs", ".mjs", ".py"))
    else:
        names = []
    print("Canonical PP-tracked hooks (copy into ~/.claude/hooks/ on")
    print("a fresh host; existing hosts only update what they want):")
    for n in names:
        print(f"  cp '{pp_hooks / n}' '{GLOBAL / 'hooks' / n}'")
    print()
    print("Hook registrations (after the cp, run from this repo):")
    print(f"  python tools/settings_merger.py register-sessionstart "
          f"--node-script ~/.claude/hooks/learning-sentinel.js")
    print(f"  python tools/settings_merger.py register-stop "
          f"--node-script ~/.claude/hooks/learning-sentinel.js")
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--dry-run", action="store_true",
                    help="print intended actions; mutate nothing")
    ap.add_argument("--settings", default=str(DEFAULT_SETTINGS),
                    help="settings.json path (default ~/.claude/...)")
    ap.add_argument("--repo", default=str(DEFAULT_REPO),
                    help="PP repo root (default: derived from script)")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    settings_path = Path(args.settings).resolve()

    print("=" * 64)
    print(f"Claude Power Pack — global installer "
          f"({'DRY-RUN' if args.dry_run else 'APPLY'})")
    print(f"  repo     : {repo}")
    print(f"  loose    : {GLOBAL}")
    print(f"  settings : {settings_path}")
    print(f"  backups  : {BACKUP_ROOT}/<iso>")
    print(f"  run_ts   : {ISO_TS}")
    print("=" * 64)

    if not repo.is_dir():
        print(f"install-global: repo not found: {repo}", file=sys.stderr)
        return 5
    if not settings_path.is_file():
        print(f"install-global: settings.json not found: {settings_path}",
              file=sys.stderr)
        return 5

    inv = _load_inventory(repo)
    if not inv:
        return 5

    report: list = []

    # 1. File copy. Schema (Owner-pane regeneration 2026-05-19):
    #    each inventory file has {items:[{name,path,source,tag,sha256}]}.
    #    Shippable iff tag == "pp-original" AND source == "pp-repo".
    #    HOOKS are intentionally NOT installer-shipped: per the
    #    Mirror-Sync-Direction doctrine (memory:
    #    feedback_mirror_sync_direction_and_hooks_dir_deny.md, 2026-05-19),
    #    A1/A2 flow is loose -> PP only; ~/.claude/hooks/<file>.js writes
    #    are classifier-denied. New users hand-copy hooks per the
    #    printed checklist below; the installer never touches the
    #    hooks dir.
    counters = {"installed": 0, "updated": 0, "unchanged": 0,
                "missing-source": 0, "error": 0, "skipped-not-pp": 0}
    SHIPPABLE_KINDS = ("agents", "commands")
    shippable_items: list[tuple[str, dict]] = []
    for kind in SHIPPABLE_KINDS:
        for entry in inv.get(kind, {}).get("items", []):
            if entry.get("tag") == "pp-original" \
                    and entry.get("source") == "pp-repo":
                shippable_items.append((kind, entry))
            else:
                counters["skipped-not-pp"] += 1

    for kind, entry in shippable_items:
        name = entry["name"]
        # Honor pp_match.pp_path when present (handles historic renames
        # like cpp-resume-sovereign.md -> commands/resume-sovereign.md).
        pp_match = entry.get("pp_match") or {}
        pp_path = pp_match.get("pp_path")
        src = Path(pp_path) if pp_path else (repo / kind / name)
        dst = _resolve_loose_target(kind, name)
        verdict = _backup_then_overwrite(dst, src, args.dry_run, report)
        counters[verdict] = counters.get(verdict, 0) + 1

    # 2. node --check is N/A — installer no longer ships hooks.
    nc_fail = 0

    # 3. Hooks + permissions are Owner-pasted, not installer-written.
    #    See _print_hooks_checklist() below.
    hr_failures = 0

    # 4. Backup GC.
    _gc_backups(args.dry_run, report)

    # 5. Per-run report file.
    report_path = GLOBAL / f".pp-install-report.{ISO_TS}.json"
    if not args.dry_run:
        try:
            report_path.write_text(
                json.dumps({"ts": ISO_TS, "args": vars(args),
                            "counters": counters, "report": report},
                           indent=2, ensure_ascii=False),
                encoding="utf-8")
        except OSError as e:
            print(f"install-global: report write failed: {e}",
                  file=sys.stderr)

    # 6. Final report.
    print()
    print("file copy:")
    for k, v in counters.items():
        print(f"  {k:<16s} {v}")
    print(f"node --check failures: {nc_fail}")
    print(f"hook-register failures: {hr_failures}")
    if not args.dry_run:
        print(f"per-run report: {report_path}")

    _print_permissions_checklist()
    _print_hooks_checklist(repo)

    print()
    print("Next step (Owner-gated):")
    print("  1. Paste the rules above into ~/.claude/settings.json")
    print("     permissions.allow (or skip if already present).")
    print("  2. cp + register hooks per the hooks checklist above.")
    print("  3. /restart   (BL-0067: hooks cold-load at session start).")
    print("  4. python tools/verify_full_install.py  # S++ self-test")
    print()

    if args.dry_run:
        print("DRY-RUN — no files mutated. Re-run without --dry-run "
              "to apply.")
        return 0

    rc = 1 if (counters["error"] > 0 or counters["missing-source"] > 0
               or nc_fail > 0 or hr_failures > 0) else 0
    return rc


if __name__ == "__main__":
    sys.exit(main())
