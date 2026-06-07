#!/usr/bin/env python3
"""Setup Drift Detector -- CPP Setup OS Pillar 6 (build-everything B3).

Detects when a repo drifts from a captured baseline: both ProjectProfile
field changes AND content changes in key config files (settings.json,
CLAUDE.md, package.json, requirements.txt, pyproject.toml). This is the
gap the existing `modules/monitoring` does NOT cover -- monitoring is
SERVICE health (TCP/HTTP), this is repo-CONFIG drift.

Composes `modules/setup_os/scanner` (SCS C28: no re-implementation).
stdlib-only. Baseline is a JSON sidecar the Owner places under version
control or .gitignore as they choose.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field as dc_field
from pathlib import Path

from .scanner import scan

# Config files whose CONTENT drift matters (hashed, not stored raw).
_WATCH_FILES = (
    "settings.json", ".claude/settings.json", "CLAUDE.md",
    "package.json", "requirements.txt", "pyproject.toml",
    ".mcp.json",
)
# Profile fields whose VALUE drift matters (presence/identity).
_WATCH_FIELDS = (
    "language_primary", "framework_primary", "package_manager",
    "test_runner", "ci_cd", "docker_presence", "existing_claude_md",
    "existing_hooks", "mcp_config_presence",
    "secret_sensitive_files_presence",
)


@dataclass
class DriftItem:
    kind: str          # "field" | "file"
    name: str
    baseline: str
    current: str


@dataclass
class DriftReport:
    drifted: bool
    items: list[DriftItem] = dc_field(default_factory=list)
    baseline_missing: bool = False


def _file_hash(root: Path, rel: str) -> str | None:
    p = root / rel
    if not p.is_file():
        return None
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    except OSError:
        return None


def snapshot(path: str | Path | None = None) -> dict:
    """Capture a baseline: watched profile fields + config-file hashes."""
    root = Path(path).resolve() if path else Path.cwd()
    prof = scan(root)
    fields = {name: repr(getattr(prof, name).value) for name in _WATCH_FIELDS}
    files = {rel: _file_hash(root, rel) for rel in _WATCH_FILES}
    return {"fields": fields, "files": files}


def write_baseline(path: str | Path, baseline_file: str | Path) -> dict:
    bl = snapshot(path)
    Path(baseline_file).write_text(json.dumps(bl, indent=2), encoding="utf-8")
    return bl


def detect_drift(path: str | Path, baseline: dict | str | Path) -> DriftReport:
    """Compare the current repo state against a baseline snapshot."""
    if isinstance(baseline, (str, Path)):
        bp = Path(baseline)
        if not bp.is_file():
            return DriftReport(drifted=False, baseline_missing=True)
        try:
            baseline = json.loads(bp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return DriftReport(drifted=False, baseline_missing=True)

    current = snapshot(path)
    items: list[DriftItem] = []
    for name, cur in current["fields"].items():
        base = baseline.get("fields", {}).get(name)
        if base is not None and base != cur:
            items.append(DriftItem("field", name, str(base), str(cur)))
    for rel, cur in current["files"].items():
        base = baseline.get("files", {}).get(rel)
        if base != cur:  # added, removed, or content changed
            items.append(DriftItem("file", rel, str(base), str(cur)))
    return DriftReport(drifted=bool(items), items=items)


def render(report: DriftReport) -> str:
    if report.baseline_missing:
        return "No baseline found. Run snapshot/write_baseline first."
    if not report.drifted:
        return "No drift: repo matches baseline."
    lines = [f"DRIFT detected: {len(report.items)} change(s)"]
    for it in report.items:
        lines.append(f"  [{it.kind}] {it.name}: {it.baseline} -> {it.current}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Setup Drift Detector")
    ap.add_argument("--path", default=".")
    ap.add_argument("--baseline", required=True,
                    help="baseline JSON path (written if --snapshot)")
    ap.add_argument("--snapshot", action="store_true",
                    help="write a fresh baseline instead of comparing")
    args = ap.parse_args(argv)
    if args.snapshot:
        write_baseline(args.path, args.baseline)
        print(f"Baseline written: {args.baseline}")
        return 0
    print(render(detect_drift(args.path, args.baseline)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
