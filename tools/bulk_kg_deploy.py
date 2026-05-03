#!/usr/bin/env python
"""BL-0054 — Bulk KG deploy via kobi_graphify.py.

Iterates a list of project paths (passed as args), invokes
kobi_graphify on each in sequence (not parallel — process-sandbox
treats repeated identical signatures as anti-pattern), writes
audit JSON.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRAPHIFY = ROOT / "tools" / "kobi_graphify.py"


def run_one(project: Path) -> dict:
    rec = {"project": str(project)}
    if not project.is_dir():
        rec["status"] = "missing"
        return rec
    if (project / "_knowledge_graph" / "INDEX.md").exists():
        rec["status"] = "skipped_already_has_kg"
        return rec
    try:
        proc = subprocess.run(
            [sys.executable, str(GRAPHIFY), "-p", str(project), "--quiet"],
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        rec["status"] = "timeout"
        return rec
    rec["returncode"] = proc.returncode
    rec["status"] = "ok" if proc.returncode == 0 else "failed"
    rec["stdout_tail"] = (proc.stdout or "").splitlines()[-6:]
    rec["stderr_tail"] = (proc.stderr or "").splitlines()[-3:]
    return rec


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: bulk_kg_deploy.py <project1> [project2] ...", file=sys.stderr)
        return 2
    projects = [Path(p) for p in sys.argv[1:]]
    results = []
    ok = skipped = failed = 0
    for p in projects:
        r = run_one(p)
        results.append(r)
        if r["status"] == "ok":
            ok += 1
            print(f"[OK]   {p}")
        elif r["status"] == "skipped_already_has_kg":
            skipped += 1
            print(f"[SKIP] {p}")
        else:
            failed += 1
            print(f"[FAIL] {p} -> {r['status']}")
    summary = {"ok": ok, "skipped": skipped, "failed": failed, "details": results}
    out = ROOT / "vault" / "audits" / "bulk_kg_deploy.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nSummary: ok={ok} skipped={skipped} failed={failed} -> {out}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
