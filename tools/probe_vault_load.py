#!/usr/bin/env python
"""BL-0047 — Empirical probe: measure 'primary cerebrum' coverage.

For each project session under ~/.claude/projects/ and each working
directory the user actually has on disk, report:
  - Does ~/.claude/CLAUDE.md exist + size?
  - Does ~/.claude/vault/INDEX.md exist?            (governance vault)
  - Does ~/.claude/knowledge_vault/INDEX.md exist?  (K-Router v2.1)
  - Per project: _knowledge_graph/INDEX.md present?  (per-project KG)
  - Per project: vault/INDEX.md or progress.md present? (per-project pulse)

This is read-only verification — no edits. Output is empirical evidence
of which projects already have the cerebrum vs which ones load CLAUDE.md
without any Vault to consult (= hallucination risk).
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path

HOME = Path.home()
PROJECTS_DIR = HOME / ".claude" / "projects"
GLOBAL_FILES = {
    "CLAUDE_md": HOME / ".claude" / "CLAUDE.md",
    "governance_vault_INDEX": HOME / ".claude" / "vault" / "INDEX.md",
    "knowledge_vault_INDEX": HOME / ".claude" / "knowledge_vault" / "INDEX.md",
    "GLOBAL_ALIGNMENT_LEDGER": HOME / ".claude" / "governance" / "GLOBAL_ALIGNMENT_LEDGER.md",
}

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "vault" / "audits" / "probe_vault_load.json"


def _stat(p: Path) -> dict:
    if not p.exists():
        return {"exists": False}
    try:
        return {
            "exists": True,
            "bytes": p.stat().st_size,
            "is_file": p.is_file(),
        }
    except Exception as e:
        return {"exists": True, "error": str(e)}


def _decode_session_dir(session_dir: Path) -> Path | None:
    """Claude Code stores per-project session JSONLs under
    ~/.claude/projects/<flattened-cwd>/. The dir name is the user's
    cwd with separators replaced by '-'. Reconstruct best-effort."""
    name = session_dir.name
    if not name.startswith("C--") and not name.startswith("--"):
        return None
    rebuilt = name.replace("-", "/")
    if rebuilt.startswith("C//"):
        rebuilt = "C:/" + rebuilt[3:]
    candidate = Path(rebuilt)
    if candidate.is_dir():
        return candidate
    return None


def _project_cerebrum(cwd: Path) -> dict:
    return {
        "cwd": str(cwd),
        "CLAUDE_md": _stat(cwd / "CLAUDE.md"),
        "knowledge_graph_INDEX": _stat(cwd / "_knowledge_graph" / "INDEX.md"),
        "vault_INDEX": _stat(cwd / "vault" / "INDEX.md"),
        "vault_progress": _stat(cwd / "vault" / "progress.md"),
        "dotclaude_progress": _stat(cwd / ".claude" / "progress.md"),
    }


def main() -> int:
    iso_ts = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    globals_state = {k: _stat(v) for k, v in GLOBAL_FILES.items()}

    project_records = []
    if PROJECTS_DIR.is_dir():
        for sd in sorted(PROJECTS_DIR.iterdir()):
            if not sd.is_dir():
                continue
            cwd = _decode_session_dir(sd)
            rec: dict = {
                "session_dir": sd.name,
                "decoded_cwd": str(cwd) if cwd else None,
                "decoded_cwd_exists": bool(cwd and cwd.is_dir()),
            }
            if cwd and cwd.is_dir():
                rec.update(_project_cerebrum(cwd))
            project_records.append(rec)

    decoded = [r for r in project_records if r.get("decoded_cwd_exists")]
    with_kg = sum(1 for r in decoded if r.get("knowledge_graph_INDEX", {}).get("exists"))
    with_vault = sum(1 for r in decoded if r.get("vault_INDEX", {}).get("exists"))
    with_progress = sum(
        1
        for r in decoded
        if r.get("vault_progress", {}).get("exists") or r.get("dotclaude_progress", {}).get("exists")
    )
    with_claude_md = sum(1 for r in decoded if r.get("CLAUDE_md", {}).get("exists"))

    verdict = {
        "probe": "BL-0047 / MC-SYS-94 — primary cerebrum coverage",
        "iso_ts": iso_ts,
        "globals": globals_state,
        "globals_all_present": all(s.get("exists") for s in globals_state.values()),
        "projects_total": len(project_records),
        "projects_decoded": len(decoded),
        "projects_with_CLAUDE_md": with_claude_md,
        "projects_with_knowledge_graph": with_kg,
        "projects_with_vault_INDEX": with_vault,
        "projects_with_progress_md": with_progress,
        "details": project_records,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "globals_all_present": verdict["globals_all_present"],
                "projects_decoded": len(decoded),
                "with_kg": with_kg,
                "with_vault": with_vault,
                "with_progress": with_progress,
                "out": str(OUT),
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
