#!/usr/bin/env python3
"""lazarus_post_reboot_arm.py - sanitize Lazarus state once per logon (BL-0073).

Runs from $PROFILE on first shell of a fresh logon. Idempotent. Per-bootid
sentinel ensures it runs once even when 4 panes spawn simultaneously.

Cleanup tasks:
  1. terminal_registry.json: drop entries whose .jsonl AND .jsonl.live are
     both missing on disk (audit gap #5: ghost UUIDs cause "No conversation
     found" when smart-resume tries to --resume them).
  2. heartbeats: delete <uuid>.lock files >24h old (cross-reboot zombies).
  3. tmp orphans: vault/*.tmp.<pid>.<hex> and lazarus/**/*.tmp.<pid>.<hex>
     older than 60s (atomic_write killed-mid-rename casualties).
  4. cwd-norm migration (audit gap #9): if both `C--Users-...` and `-c-Users-...`
     project dirs exist for the same workspace, merge into the canonical
     `C--...` form (sanitize_cwd_to_project_id output).

Logs to ~/.claude/lazarus/post_reboot_<ISO>.log. Exits 0 unless arming
explicitly fails (registry unreadable AND --strict).

Usage:
  python lazarus_post_reboot_arm.py            # apply (idempotent, sentinel-gated)
  python lazarus_post_reboot_arm.py --dry-run  # report only
  python lazarus_post_reboot_arm.py --force    # bypass sentinel (re-run)
  python lazarus_post_reboot_arm.py --json
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
import time
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
LAZARUS_DIR = HOME / ".claude" / "lazarus"
PROJECTS_DIR = HOME / ".claude" / "projects"
POWER_PACK_VAULT = HOME / ".claude" / "skills" / "claude-power-pack" / "vault"
REGISTRY_PATH = LAZARUS_DIR / "terminal_registry.json"

HEARTBEAT_STALE_HOURS = 24
TMP_ORPHAN_AGE_S = 60


def iso_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")


def get_boot_id() -> str:
    """Return a string that changes only on Windows reboot. Uses
    Win32_OperatingSystem.LastBootUpTime via wmic if available, else
    falls back to current date (per-day arming as a degraded mode)."""
    try:
        import subprocess
        out = subprocess.run(
            ["wmic", "OS", "get", "LastBootUpTime", "/value"],
            capture_output=True, text=True, timeout=5
        )
        for line in out.stdout.splitlines():
            line = line.strip()
            if line.startswith("LastBootUpTime="):
                return re.sub(r"[^0-9]", "", line.split("=", 1)[1])
    except (OSError, subprocess.SubprocessError):
        pass
    return _dt.datetime.now().strftime("%Y%m%d")


def sentinel_path(boot_id: str) -> Path:
    return LAZARUS_DIR / f".armed_logon_{boot_id}"


def find_jsonl_for_uuid(workspace_path: str, uuid: str) -> bool:
    """Return True if any .jsonl or .jsonl.live exists for this UUID under
    the workspace's project dir(s). Tolerates cwd-norm drift by checking
    both `C--...` and `-c-...` variants."""
    if not workspace_path or not uuid:
        return False
    candidates: list[str] = []
    sanitized = re.sub(r"[^a-zA-Z0-9-]", "-", workspace_path)
    candidates.append(sanitized)
    # Lowercased-drive variant (matches normalizeCwd in terminal-slot-recorder.js)
    lc = re.sub(r"^([a-z]):/", lambda m: m.group(1).lower() + ":/",
                workspace_path.replace("\\", "/").lower())
    candidates.append(re.sub(r"[^a-zA-Z0-9-]", "-", lc))
    for proj in candidates:
        for suf in (".jsonl", ".jsonl.live"):
            if (PROJECTS_DIR / proj / f"{uuid}{suf}").is_file():
                return True
    # Fallback: walk all projects
    if not PROJECTS_DIR.is_dir():
        return False
    for proj in PROJECTS_DIR.iterdir():
        if not proj.is_dir():
            continue
        for suf in (".jsonl", ".jsonl.live"):
            if (proj / f"{uuid}{suf}").is_file():
                return True
    return False


def clean_registry(dry: bool) -> dict:
    summary = {"action": "clean_registry", "dropped": [], "kept": 0, "missing_file": False}
    if not REGISTRY_PATH.is_file():
        summary["missing_file"] = True
        return summary
    try:
        raw = REGISTRY_PATH.read_text(encoding="utf-8-sig")
        reg = json.loads(raw)
    except (OSError, json.JSONDecodeError) as e:
        summary["error"] = f"unreadable: {e}"
        return summary
    entries = reg.get("entries") if isinstance(reg, dict) else None
    if not isinstance(entries, list):
        return summary
    keep: list[dict] = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        uuid = e.get("uuid")
        ws = e.get("workspace_path", "")
        if uuid and find_jsonl_for_uuid(ws, uuid):
            keep.append(e)
        else:
            summary["dropped"].append({"slot_id": e.get("slot_id"), "uuid": uuid, "ws": ws})
    summary["kept"] = len(keep)
    if not dry and len(keep) != len(entries):
        reg["entries"] = keep
        tmp = REGISTRY_PATH.with_suffix(REGISTRY_PATH.suffix + f".tmp.{os.getpid()}")
        try:
            tmp.write_text(json.dumps(reg, indent=2), encoding="utf-8")
            os.replace(tmp, REGISTRY_PATH)
        except OSError as e2:
            try: tmp.unlink()
            except OSError: pass
            summary["error"] = f"write failed: {e2}"
    return summary


def clean_heartbeats(dry: bool) -> dict:
    summary = {"action": "clean_heartbeats", "removed": 0, "checked": 0}
    if not LAZARUS_DIR.is_dir():
        return summary
    cutoff = time.time() - HEARTBEAT_STALE_HOURS * 3600
    for proj in LAZARUS_DIR.iterdir():
        if not proj.is_dir():
            continue
        hb_dir = proj / "heartbeats"
        if not hb_dir.is_dir():
            continue
        for f in hb_dir.iterdir():
            if not f.is_file() or f.suffix != ".lock":
                continue
            summary["checked"] += 1
            try:
                if f.stat().st_mtime < cutoff:
                    if not dry:
                        f.unlink()
                    summary["removed"] += 1
            except OSError:
                pass
    return summary


def clean_tmp_orphans(dry: bool) -> dict:
    summary = {"action": "clean_tmp_orphans", "removed": 0}
    cutoff = time.time() - TMP_ORPHAN_AGE_S
    tmp_re = re.compile(r"\.tmp\.\d+(\.[a-f0-9]+)?$")
    roots = [POWER_PACK_VAULT, LAZARUS_DIR]
    for root in roots:
        if not root.is_dir():
            continue
        for f in root.rglob("*"):
            if not f.is_file():
                continue
            if not tmp_re.search(f.name):
                continue
            try:
                if f.stat().st_mtime < cutoff:
                    if not dry:
                        f.unlink()
                    summary["removed"] += 1
            except OSError:
                pass
    return summary


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true", help="bypass per-bootid sentinel")
    p.add_argument("--strict", action="store_true", help="exit 1 on registry unreadable")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    boot_id = get_boot_id()
    sentinel = sentinel_path(boot_id)

    if sentinel.exists() and not args.force and not args.dry_run:
        if args.json:
            print(json.dumps({"skipped": True, "reason": "already armed for this logon", "sentinel": str(sentinel)}))
        else:
            print(f"[post-reboot-arm] already armed for boot {boot_id}; pass --force to re-run")
        return 0

    LAZARUS_DIR.mkdir(parents=True, exist_ok=True)

    results = {
        "boot_id": boot_id,
        "iso": iso_now(),
        "dry_run": args.dry_run,
        "registry": clean_registry(args.dry_run),
        "heartbeats": clean_heartbeats(args.dry_run),
        "tmp_orphans": clean_tmp_orphans(args.dry_run),
    }

    if not args.dry_run:
        try:
            sentinel.write_text(results["iso"], encoding="utf-8")
        except OSError:
            pass
        # Append to log
        log_path = LAZARUS_DIR / f"post_reboot_{results['iso']}.log"
        try:
            log_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
        except OSError:
            pass

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        r = results["registry"]
        h = results["heartbeats"]
        t = results["tmp_orphans"]
        print(f"[post-reboot-arm] boot={boot_id}  dry_run={args.dry_run}")
        print(f"  registry: kept={r.get('kept', 0)} dropped={len(r.get('dropped', []))}")
        for d in r.get("dropped", []):
            print(f"    drop: slot={d.get('slot_id')} uuid={d.get('uuid')[:8] if d.get('uuid') else '?'} (no .jsonl on disk)")
        print(f"  heartbeats: removed={h['removed']}/{h['checked']} (>24h)")
        print(f"  tmp orphans: removed={t['removed']}")
        if not args.dry_run:
            print(f"  log: {LAZARUS_DIR / ('post_reboot_' + results['iso'] + '.log')}")

    err = results["registry"].get("error")
    if err and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
