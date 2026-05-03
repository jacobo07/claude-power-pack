#!/usr/bin/env python
"""BL-0052 — Bulk vault extraction for projects under a root path.

Reads a list of CLAUDE.md paths (file or stdin), and for each whose
sibling vault/INDEX.md is absent, runs vault_extractor.py extract
into <project>/vault/. Reports per-project pass/fail with token cost.

Idempotent: re-running on a project that already has vault/INDEX.md
is a no-op (skipped). Token-budget conscious.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTRACTOR = ROOT / "tools" / "vault_extractor.py"


def extract_one(claude_md: Path) -> dict:
    project_dir = claude_md.parent
    vault_dir = project_dir / "vault"
    index_path = vault_dir / "INDEX.md"
    rec = {"project": str(project_dir), "claude_md": str(claude_md)}
    if index_path.exists():
        rec["status"] = "skipped_already_has_vault"
        return rec
    try:
        proc = subprocess.run(
            [sys.executable, str(EXTRACTOR), "extract", str(claude_md), "--vault", str(vault_dir)],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        rec["status"] = "timeout"
        return rec
    rec["returncode"] = proc.returncode
    rec["stdout_tail"] = (proc.stdout or "").splitlines()[-3:] if proc.stdout else []
    rec["stderr_tail"] = (proc.stderr or "").splitlines()[-3:] if proc.stderr else []
    rec["status"] = "ok" if proc.returncode == 0 and index_path.exists() else "failed"
    if rec["status"] == "ok":
        try:
            rec["index_bytes"] = index_path.stat().st_size
            rec["vault_files"] = sum(1 for _ in vault_dir.rglob("*.md"))
        except Exception:
            pass
    return rec


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: bulk_vault_extract.py <paths_file>", file=sys.stderr)
        return 2
    paths_file = Path(sys.argv[1])
    if not paths_file.exists():
        print(f"paths file missing: {paths_file}", file=sys.stderr)
        return 2

    targets = []
    for line in paths_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("TOTAL:") or line.startswith("#"):
            continue
        if line.startswith("(") and "CLAUDE.md" in line:
            try:
                path_str = line.split("'")[1]
                p = Path(path_str)
                if p.is_file():
                    targets.append(p)
            except (IndexError, ValueError):
                continue

    results = []
    ok = 0
    skipped = 0
    failed = 0
    for t in targets:
        r = extract_one(t)
        results.append(r)
        if r["status"] == "ok":
            ok += 1
            print(f"[OK]      {r['project']} -> {r.get('vault_files', '?')} files")
        elif r["status"] == "skipped_already_has_vault":
            skipped += 1
            print(f"[SKIP]    {r['project']} (already has vault)")
        else:
            failed += 1
            print(f"[FAILED]  {r['project']} -> {r['status']}")

    summary = {
        "total_targets": len(targets),
        "ok": ok,
        "skipped": skipped,
        "failed": failed,
        "details": results,
    }
    out_path = ROOT / "vault" / "audits" / "bulk_vault_extract.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nSummary: ok={ok} skipped={skipped} failed={failed} -> {out_path}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
