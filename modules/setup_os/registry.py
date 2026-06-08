#!/usr/bin/env python3
"""Setup-OS profile registry -- central per-repo ProjectProfile store.

The scanner (`scanner.scan`) is cwd-aware but stateless; this module persists
its output so a cross-repo signal (`signals/setup_scan.py`) can ask "has this
repo been scanned?" without re-walking. Profiles live in the PP repo (absolute
path), NOT in the scanned repo -- external repos are never polluted and the
registry is queryable from ANY cwd.

Keyed by sanitized basename + an 8-char hash of the full resolved path so two
distinct repos that share a basename (e.g. two `Website` folders) never collide.
Stdlib-only, fail-open on reads.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

# modules/setup_os/registry.py -> parents[2] == PP repo root (absolute,
# cwd-independent: the registry is the PP repo's, not the scanned repo's).
PP_ROOT = Path(__file__).resolve().parents[2]
PROFILES_DIR = PP_ROOT / "vault" / "setup_os" / "profiles"


def _slug(cwd: str | Path) -> str:
    name = Path(cwd).name or "root"
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "root"


def profile_path_for(cwd: str | Path, profiles_dir: Path | None = None) -> Path:
    """Registry path for a repo. `profiles_dir` override keeps tests hermetic."""
    base = profiles_dir if profiles_dir is not None else PROFILES_DIR
    full = str(Path(cwd).resolve()).lower()
    h = hashlib.sha1(full.encode("utf-8")).hexdigest()[:8]
    return base / f"{_slug(cwd)}_{h}.json"


def has_profile(cwd: str | Path, profiles_dir: Path | None = None) -> bool:
    try:
        return profile_path_for(cwd, profiles_dir).is_file()
    except Exception:
        return False


def save_profile(cwd: str | Path, profile_dict: dict,
                 profiles_dir: Path | None = None) -> Path:
    """Atomically persist a profile dict. Returns the written path."""
    p = profile_path_for(cwd, profiles_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(profile_dict, indent=2, default=str),
                   encoding="utf-8")
    tmp.replace(p)
    return p


def load_profile(cwd: str | Path,
                 profiles_dir: Path | None = None) -> dict | None:
    try:
        return json.loads(
            profile_path_for(cwd, profiles_dir).read_text(encoding="utf-8"))
    except Exception:
        return None


__all__ = [
    "PROFILES_DIR", "profile_path_for", "has_profile",
    "save_profile", "load_profile",
]
