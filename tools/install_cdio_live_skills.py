#!/usr/bin/env python3
"""install_cdio_live_skills.py -- install the CDIO-13 live skills into ~/.claude/skills.

Called by install.ps1 / install.sh. The three skills (impeccable, ui-ux-pro-max,
anydesign) ship as complete folders under vault/knowledge_base/cdio/web-pack/live/,
pinned by live-manifest.json (upstream commit + sha256 per file).

Per skill, in order:
  1. integrity: every manifest file present with its sha256 and NO unlisted file
     in the folder, else FAIL (nothing copied)
  2. already installed at <target>/<name>                     -> SKIP present (never overwritten)
  3. provided by an installed AND enabled plugin (plugins/installed_plugins.json
     installPath + settings.json enabledPlugins)              -> SKIP plugin (no duplicate)
  4. copy the listed files into <target>/.<name>.partial, then rename -> INSTALLED
An OS error on one skill is reported as FAIL for that skill; the others still run.

usage: python tools/install_cdio_live_skills.py [--target DIR] [--plugins DIR]
                                                [--settings FILE] [--dry-run]
exit 0 = every skill INSTALLED or SKIPPED; 1 = any FAIL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIVE = ROOT / "vault" / "knowledge_base" / "cdio" / "web-pack" / "live"
HOME_CLAUDE = Path(os.path.expanduser("~")) / ".claude"


def integrity_gaps(skill: dict, live: Path = LIVE) -> list[str]:
    """Return problems in one skill folder: missing, sha256 mismatch, or unlisted files."""
    gaps = []
    base = live / skill["name"]
    listed = set()
    for f in skill["files"]:
        listed.add(f["path"])
        p = base.joinpath(*f["path"].split("/"))
        if not p.is_file():
            gaps.append(f"missing {f['path']}")
        elif hashlib.sha256(p.read_bytes()).hexdigest() != f["sha256"]:
            gaps.append(f"sha256 {f['path']}")
    if base.is_dir():
        for p in base.rglob("*"):
            if p.is_file():
                rel = p.relative_to(base).as_posix()
                if rel not in listed:
                    gaps.append(f"unlisted {rel}")
    return gaps


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def plugin_has(plugins: Path, settings: Path, name: str) -> Path | None:
    """Return the SKILL.md of an installed AND enabled plugin that provides this skill.

    Only Claude Code's registry counts: a marketplace clone, a trashed or an old cached
    version on disk is not an installed plugin.
    """
    registry = _load_json(plugins / "installed_plugins.json").get("plugins", {})
    enabled = _load_json(settings).get("enabledPlugins", {})
    for key, entries in registry.items():
        if enabled.get(key) is not True:
            continue
        for entry in entries if isinstance(entries, list) else [entries]:
            install_path = entry.get("installPath") if isinstance(entry, dict) else None
            if not install_path:
                continue
            root = Path(install_path)
            for cand in (root / "skills" / name / "SKILL.md",
                         root / ".claude" / "skills" / name / "SKILL.md"):
                if cand.is_file():
                    return cand
    return None


def _copy_listed(skill: dict, src: Path, dest: Path) -> None:
    for f in skill["files"]:
        rel = f["path"].split("/")
        out = dest.joinpath(*rel)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src.joinpath(*rel), out)


def install(target: Path, plugins: Path, settings: Path | None = None, dry_run: bool = False,
            live: Path = LIVE) -> tuple[int, list[tuple[str, str, str]]]:
    """Install every live skill. Return (exit code, [(name, outcome, detail)])."""
    settings = settings if settings is not None else plugins.parent / "settings.json"
    manifest = json.loads((live / "live-manifest.json").read_text(encoding="utf-8"))
    results, code = [], 0
    for skill in manifest["skills"]:
        name = skill["name"]
        gaps = integrity_gaps(skill, live)
        if gaps:
            results.append((name, "FAIL", f"integrity: {gaps[:3]} (+{max(0, len(gaps) - 3)})"))
            code = 1
            continue
        dest = target / name
        if dest.exists():
            results.append((name, "SKIP", f"present at {dest} (not overwritten)"))
            continue
        hit = plugin_has(plugins, settings, name)
        if hit:
            results.append((name, "SKIP", f"provided by enabled plugin {hit.parent}"))
            continue
        if dry_run:
            results.append((name, "WOULD-INSTALL", str(dest)))
            continue
        partial = target / f".{name}.partial"
        if partial.exists():
            results.append((name, "FAIL", f"stale {partial} from an interrupted install; "
                                          "inspect and remove it, then re-run"))
            code = 1
            continue
        try:
            target.mkdir(parents=True, exist_ok=True)
            _copy_listed(skill, live / name, partial)
            partial.rename(dest)
        except OSError as exc:
            results.append((name, "FAIL", f"copy error: {exc} (partial left at {partial})"))
            code = 1
            continue
        results.append((name, "INSTALLED", f"{dest} ({len(skill['files'])} files, "
                                           f"{skill['repo']}@{skill['commit'][:8]}, {skill['licence']})"))
    return code, results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--target", type=Path, default=HOME_CLAUDE / "skills")
    ap.add_argument("--plugins", type=Path, default=HOME_CLAUDE / "plugins")
    ap.add_argument("--settings", type=Path, default=HOME_CLAUDE / "settings.json")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    code, results = install(a.target, a.plugins, a.settings, a.dry_run)
    for name, outcome, detail in results:
        print(f"[{outcome}] {name}: {detail}")
    return code


if __name__ == "__main__":
    sys.exit(main())
