#!/usr/bin/env python3
"""
Oracle Delta — OVO delta-audit wrapper.

Thin wrapper over audit_cache.py. Produces the delta JSON that feeds the
Council, persists verdicts to vault/audits/verdicts.jsonl, and freezes
pre/post source_map.json snapshots for atomic vaulting.

Reuses audit_cache primitives (hash_file, build_cache, load_cache,
should_skip, DEFAULT_PATTERNS) — does NOT re-implement hashing or scanning.

Usage:
    python tools/oracle_delta.py --project . --json
    python tools/oracle_delta.py --project . --record-verdict A+ --council-text "<block>"
    python tools/oracle_delta.py --project . --vault-post
    python tools/oracle_delta.py --project . --report-md vault/audits/ovo_latest.md
"""

import argparse
import hashlib
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
# audit_cache's module init already rewraps sys.stdout for UTF-8 on Windows;
# do NOT double-wrap here or GC will close the shared buffer.
from audit_cache import (  # noqa: E402 — local import after path insert
    CACHE_DIR,
    CACHE_FILE,
    DEFAULT_PATTERNS,
    build_cache,
    hash_file,
    load_cache,
    should_skip,
)

VAULT_AUDITS_DIR = "vault/audits"
SNAPSHOTS_DIR = "vault/audits/snapshots"
VERDICTS_FILE = "vault/audits/verdicts.jsonl"
BREADCRUMB_DIR = "_audit_cache"
BREADCRUMB_TTL_SEC = 120
COUNCIL_BLOCK_MAX_CHARS = 1200  # ~300 tokens

VALID_VERDICTS = ("A+", "A", "B", "REJECT")


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def iso_for_filename() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_delta(project: Path) -> dict:
    """Return {changed, new, deleted, cold_start} without printing.

    Auto-builds the cache on first run; flags cold_start so the Council
    can weight its reasoning appropriately.
    """
    cache = load_cache(project)
    cold_start = False
    if cache is None:
        print("[oracle_delta] no audit cache — building (cold start, ~20s)…",
              file=sys.stderr)
        cache = build_cache(project)
        cold_start = True

    old_files = cache.get("files", {})
    changed: list[dict] = []
    new_files: list[dict] = []
    deleted: list[str] = []
    current: set[str] = set()

    for pattern in DEFAULT_PATTERNS:
        for fp in sorted(project.glob(pattern)):
            rel_parts = fp.relative_to(project)
            if should_skip(rel_parts) or not fp.is_file():
                continue
            rel = str(rel_parts).replace("\\", "/")
            current.add(rel)
            new_hash = hash_file(fp)
            if rel not in old_files:
                new_files.append({
                    "path": rel,
                    "hash": new_hash,
                    "summary": "(new file — no cached summary yet)",
                })
            elif new_hash != old_files[rel]["sha256"]:
                changed.append({
                    "path": rel,
                    "old_hash": old_files[rel]["sha256"],
                    "new_hash": new_hash,
                    "summary": old_files[rel].get("summary", ""),
                })

    for rel in old_files:
        if rel not in current:
            deleted.append(rel)

    return {
        "changed": changed,
        "new": new_files,
        "deleted": deleted,
        "cold_start": cold_start,
    }


def build_council_block(delta: dict) -> tuple[str, bool]:
    """Render delta as ≤300-token markdown context for the Council.

    Returns (block_text, truncated).
    """
    lines = ["### Delta Context"]
    c, n, d = delta["changed"], delta["new"], delta["deleted"]
    lines.append(f"Changed: {len(c)} · New: {len(n)} · Deleted: {len(d)}")
    if delta["cold_start"]:
        lines.append("⚠ cold_start — cache freshly built; no prior baseline.")

    truncated = False
    def budget() -> int:
        return COUNCIL_BLOCK_MAX_CHARS - sum(len(l) + 1 for l in lines)

    if c:
        lines.append("")
        lines.append("**Changed:**")
        for entry in c:
            row = f"- `{entry['path']}` — {entry['summary'][:80]}"
            if budget() - len(row) < 80:
                truncated = True
                break
            lines.append(row)

    if n and not truncated:
        lines.append("")
        lines.append("**New:**")
        for entry in n:
            row = f"- `{entry['path']}` (new)"
            if budget() - len(row) < 60:
                truncated = True
                break
            lines.append(row)

    if d and not truncated:
        lines.append("")
        tail = ", ".join(d[:5]) + (" …" if len(d) > 5 else "")
        lines.append(f"**Deleted:** {tail}")

    if truncated:
        lines.append("")
        lines.append("_…truncated; request specific files for detail._")

    return "\n".join(lines), truncated


def sha256_of_source_map(project: Path) -> str:
    cache_path = project / CACHE_DIR / CACHE_FILE
    if not cache_path.exists():
        return ""
    return sha256_file(cache_path)


def write_breadcrumb(project: Path, delta_id: str, sha_pre: str) -> Path:
    bc_dir = project / BREADCRUMB_DIR
    bc_dir.mkdir(parents=True, exist_ok=True)
    bc = bc_dir / f".ovo_delta_{delta_id}.json"
    bc.write_text(json.dumps({
        "delta_id": delta_id,
        "iso_ts": iso_now(),
        "sha256_pre": sha_pre,
    }), encoding="utf-8")
    return bc


def find_fresh_breadcrumb(project: Path, delta_id: str | None) -> dict | None:
    bc_dir = project / BREADCRUMB_DIR
    if not bc_dir.exists():
        return None
    pattern = f".ovo_delta_{delta_id}.json" if delta_id else ".ovo_delta_*.json"
    candidates = sorted(
        bc_dir.glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for bc in candidates:
        age = time.time() - bc.stat().st_mtime
        if age <= BREADCRUMB_TTL_SEC:
            try:
                return json.loads(bc.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
    return None


def cmd_json(args) -> int:
    project = args.project.resolve()
    delta = compute_delta(project)
    sha_pre = sha256_of_source_map(project)
    delta_id = str(uuid.uuid4())[:8]
    council_block, truncated = build_council_block(delta)

    snap_dir = project / SNAPSHOTS_DIR
    snap_dir.mkdir(parents=True, exist_ok=True)
    snap_pre = snap_dir / f"source_map_pre_{iso_for_filename()}.json"
    cache_path = project / CACHE_DIR / CACHE_FILE
    if cache_path.exists():
        snap_pre.write_bytes(cache_path.read_bytes())

    write_breadcrumb(project, delta_id, sha_pre)

    output = {
        "iso_ts": iso_now(),
        "delta_id": delta_id,
        "project": project.name,
        "sha256_pre": sha_pre,
        "cold_start": delta["cold_start"],
        "changed": delta["changed"],
        "new": delta["new"],
        "deleted": delta["deleted"],
        "council_block": council_block,
        "truncated": truncated,
        "snapshot_pre_path": str(snap_pre.relative_to(project)).replace("\\", "/"),
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


def cmd_record_verdict(args) -> int:
    project = args.project.resolve()
    verdict = args.record_verdict.strip()
    if verdict not in VALID_VERDICTS:
        print(f"ERROR: verdict must be one of {VALID_VERDICTS}, got {verdict!r}",
              file=sys.stderr)
        return 1

    bc = find_fresh_breadcrumb(project, args.delta_id)
    if bc is None:
        print("ERROR: no fresh breadcrumb (TTL 120s). Run "
              "`oracle_delta.py --json` before --record-verdict.",
              file=sys.stderr)
        return 2

    council_text = args.council_text or ""
    advisor_hash = hashlib.sha256(council_text.encode("utf-8")).hexdigest()[:16]

    record = {
        "iso_ts": iso_now(),
        "delta_id": bc["delta_id"],
        "verdict": verdict,
        "sha256_pre": bc["sha256_pre"],
        "sha256_post": None,
        "advisor_block_hash": advisor_hash,
    }

    verdicts_path = project / VERDICTS_FILE
    verdicts_path.parent.mkdir(parents=True, exist_ok=True)
    line = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")
    with open(verdicts_path, "ab") as f:
        f.write(line)

    print(f"[oracle_delta] verdict {verdict} recorded (delta_id={bc['delta_id']})")
    if verdict in ("B", "REJECT"):
        print("⚠ BLOCK verdict — route to Rejection Recovery "
              "(modules/governance-overlay/post-output.md).",
              file=sys.stderr)
    return 0


def cmd_vault_post(args) -> int:
    project = args.project.resolve()
    cache = build_cache(project)
    sha_post = sha256_of_source_map(project)

    snap_dir = project / SNAPSHOTS_DIR
    snap_dir.mkdir(parents=True, exist_ok=True)
    snap_post = snap_dir / f"source_map_post_{iso_for_filename()}.json"
    cache_path = project / CACHE_DIR / CACHE_FILE
    snap_post.write_bytes(cache_path.read_bytes())

    verdicts_path = project / VERDICTS_FILE
    patched = False
    if verdicts_path.exists():
        text = verdicts_path.read_text(encoding="utf-8").rstrip()
        if text:
            lines = text.splitlines()
            last = json.loads(lines[-1])
            if last.get("sha256_post") is None:
                last["sha256_post"] = sha_post
                lines[-1] = json.dumps(last, ensure_ascii=False)
                verdicts_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                patched = True

    print(json.dumps({
        "iso_ts": iso_now(),
        "sha256_post": sha_post,
        "snapshot_post_path": str(snap_post.relative_to(project)).replace("\\", "/"),
        "verdict_patched": patched,
        "file_count": cache.get("file_count", 0),
    }, indent=2))
    return 0


def cmd_report_md(args) -> int:
    project = args.project.resolve()
    verdicts_path = project / VERDICTS_FILE
    if not verdicts_path.exists():
        print("ERROR: no verdicts.jsonl yet — run --record-verdict first.",
              file=sys.stderr)
        return 1
    lines = verdicts_path.read_text(encoding="utf-8").splitlines()
    if not lines:
        print("ERROR: verdicts.jsonl is empty.", file=sys.stderr)
        return 1
    last = json.loads(lines[-1])

    out_path = Path(args.report_md)
    if not out_path.is_absolute():
        out_path = project / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    post_shown = last.get("sha256_post") or "(pending --vault-post)"
    body = [
        f"# OVO Audit Report — {last['iso_ts']}",
        "",
        f"- **Verdict:** `{last['verdict']}`",
        f"- **delta_id:** `{last.get('delta_id', '?')}`",
        f"- **sha256_pre:**  `{(last.get('sha256_pre') or '?')[:16]}…`",
        f"- **sha256_post:** `{post_shown if post_shown.startswith('(') else post_shown[:16] + '…'}`",
        f"- **advisor_block_hash:** `{last.get('advisor_block_hash', '?')}`",
        "",
        "Frozen source_map snapshots live in `vault/audits/snapshots/`. ",
        "Full append-only verdict log is `vault/audits/verdicts.jsonl`.",
    ]
    out_path.write_text("\n".join(body) + "\n", encoding="utf-8")
    print(f"[oracle_delta] report: {out_path.relative_to(project)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Oracle Delta — OVO wrapper")
    parser.add_argument("--project", type=Path, default=Path("."),
                        help="Project root (default: cwd)")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--json", action="store_true",
                      help="Emit delta + sha256_pre + council_block JSON")
    mode.add_argument("--vault-post", action="store_true",
                      help="Freeze post-snapshot; patch sha256_post onto last verdict")
    mode.add_argument("--record-verdict", metavar="VERDICT",
                      help="Append verdict to verdicts.jsonl (requires fresh --json breadcrumb)")
    mode.add_argument("--report-md", metavar="PATH",
                      help="Write human-readable report based on last verdict")
    parser.add_argument("--delta-id", default=None,
                        help="Specific delta_id to match breadcrumb (optional)")
    parser.add_argument("--council-text", default=None,
                        help="Council block text (hashed into advisor_block_hash)")
    args = parser.parse_args()

    project = args.project.resolve()
    if not project.exists():
        print(f"ERROR: project path does not exist: {project}", file=sys.stderr)
        return 1

    if args.json:
        return cmd_json(args)
    if args.vault_post:
        return cmd_vault_post(args)
    if args.record_verdict:
        return cmd_record_verdict(args)
    if args.report_md:
        return cmd_report_md(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
