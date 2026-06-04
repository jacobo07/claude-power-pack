#!/usr/bin/env python3
"""walk_cache_guard.py - bound the size + age of ~/.claude/state walk caches.

FASE -1 forensics (2026-06-04) measured the state-dir walk caches at a
modest 190 KB total (skill-index.json 31.8 KB the largest). They are NOT
a RAM problem today. This guard is INSURANCE against unbounded growth over
time: it prunes cache files that are either stale (older than a TTL) or
oversized, so the walk caches can never silently balloon.

Conservative by design:
  * Only files matching the walk-cache allowlist are ever touched. The
    registry (cpc_os_registry.json) and session snapshot are NEVER pruned
    here -- those have their own owners (registry.prune_stale, snapshot).
  * Oversized files are TRUNCATED to an empty cache ({} or []) -- the
    producer (e.g. jit_skill_loader) rebuilds them on next run. Never
    deleted, so a concurrent reader never hits FileNotFound.
  * Stale files (mtime older than TTL) are truncated the same way.
  * Default --dry-run; pass --apply to mutate.

Env-tunable:
  PP_CACHE_MAX_KB   per-file max size before truncation (default 512)
  PP_CACHE_TTL_DAYS age before a cache is considered stale (default 7)

Importable: prune_walk_caches(apply=False) -> list[dict] (one row per
candidate). The SessionStart hub calls prune_walk_caches(apply=True).
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

STATE_DIR = Path.home() / ".claude" / "state"

# Files the guard is allowed to bound. Anything not listed is left alone.
# These are rebuildable walk/index caches -- truncating them costs only a
# rebuild on next producer run.
WALK_CACHE_NAMES = (
    "skill-index.json",
    "open-composers.json",
    "recovered-composers.tombstones.json",
)
# Glob patterns for families of caches (e.g. per-walk jit caches).
WALK_CACHE_GLOBS = (
    "jit-walk-*.json",
    "*-walk-cache.json",
)

MAX_KB = float(os.environ.get("PP_CACHE_MAX_KB", "512"))
TTL_DAYS = float(os.environ.get("PP_CACHE_TTL_DAYS", "7"))
_SECONDS_PER_DAY = 86400


def _empty_payload_for(path: Path) -> str:
    """Return the empty-cache literal matching the file's top-level shape
    so the producer reads a valid-but-empty cache, not garbage."""
    try:
        head = path.read_text(encoding="utf-8").lstrip()[:1]
    except OSError:
        head = ""
    return "[]" if head == "[" else "{}"


def _candidates() -> list[Path]:
    if not STATE_DIR.is_dir():
        return []
    seen: dict[str, Path] = {}
    for name in WALK_CACHE_NAMES:
        p = STATE_DIR / name
        if p.is_file():
            seen[p.name] = p
    for pat in WALK_CACHE_GLOBS:
        for p in STATE_DIR.glob(pat):
            if p.is_file():
                seen[p.name] = p
    return list(seen.values())


def prune_walk_caches(apply: bool = False,
                      max_kb: float = MAX_KB,
                      ttl_days: float = TTL_DAYS,
                      now: float | None = None) -> list[dict]:
    """Inspect (and optionally truncate) walk caches. Returns one row per
    candidate: {name, kb, age_days, reason, action}. reason is '' when the
    file is within bounds (action='keep')."""
    now = time.time() if now is None else now
    rows: list[dict] = []
    ttl_s = ttl_days * _SECONDS_PER_DAY
    for p in _candidates():
        try:
            st = p.stat()
        except OSError:
            continue
        kb = round(st.st_size / 1024, 1)
        age_days = round((now - st.st_mtime) / _SECONDS_PER_DAY, 2)
        reason = ""
        if kb > max_kb:
            reason = f"oversize {kb}KB>{max_kb}KB"
        elif (now - st.st_mtime) > ttl_s:
            reason = f"stale {age_days}d>{ttl_days}d"
        action = "keep"
        if reason:
            action = "would-truncate"
            if apply:
                try:
                    p.write_text(_empty_payload_for(p), encoding="utf-8")
                    action = "truncated"
                except OSError as exc:
                    action = f"error:{type(exc).__name__}"
        rows.append({"name": p.name, "kb": kb, "age_days": age_days,
                     "reason": reason, "action": action})
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--apply", action="store_true",
                    help="truncate oversized/stale caches (default dry-run)")
    ap.add_argument("--json", action="store_true",
                    help="emit JSON rows on stdout")
    args = ap.parse_args(argv)

    rows = prune_walk_caches(apply=args.apply)
    touched = [r for r in rows if r["action"] in ("truncated", "would-truncate")]

    if args.json:
        print(json.dumps({"apply": args.apply, "rows": rows}))
    else:
        mode = "APPLY" if args.apply else "DRY-RUN"
        print(f"walk_cache_guard [{mode}] {len(rows)} cache(s), "
              f"{len(touched)} over bounds")
        for r in rows:
            mark = "*" if r["reason"] else " "
            print(f"  {mark} {r['name']:<40s} {r['kb']:>7.1f}KB  "
                  f"{r['age_days']:>6.2f}d  {r['action']}"
                  + (f"  ({r['reason']})" if r["reason"] else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
