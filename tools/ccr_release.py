"""Release, activate, roll back and switch off the CPP Cognitive Runtime mod (goal ccr).

Layout under --root (default ~/.claude/ccr):
  releases/<version>-<hash8>/  immutable copies of mods/cpp-cognitive-runtime (tests and dev state excluded)
  active/                      the release Claude Code loads (folder marketplace entry "./active")
  active.prev/                 the release before it; `rollback` swaps the two
  state/                       receipts, modes.json, and OFF (kill switch read at every session start)
  .claude-plugin/marketplace.json

This tool never runs `claude plugin ...`: registering the marketplace and installing the plugin are the
Owner's step (goal ccr, option 2). `install-commands` prints them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MOD = REPO / "mods" / "cpp-cognitive-runtime"
DIGEST = Path.home() / ".claude" / "knowledge_vault" / "core" / "HARD-RULES-DIGEST.md"
DEFAULT_ROOT = Path.home() / ".claude" / "ccr"
MARKETPLACE = "cpp-local"
PLUGIN = "cpp-cognitive-runtime"
EXCLUDE_DIRS = {".state-dev", "types"}


def _included(path: Path, mod: Path) -> bool:
    rel = path.relative_to(mod)
    return not (set(rel.parts) & EXCLUDE_DIRS) and not path.name.endswith(".test.ts")


def _version(mod: Path) -> str:
    return json.loads((mod / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]


def _inside(root: Path, target: Path) -> Path:
    target = target.resolve()
    if root.resolve() not in target.parents:
        raise SystemExit(f"refused: {target} is outside {root}")
    return target


def build(root: Path, mod: Path = MOD, digest: Path = DIGEST) -> Path:
    files = sorted(p for p in mod.rglob("*") if p.is_file() and _included(p, mod))
    if not digest.is_file():
        raise SystemExit(f"refused: kernel digest missing at {digest}; a release without it keeps full subagent instructions")
    h = hashlib.sha256()
    for p in files:
        if p.relative_to(mod).as_posix() == "kernel/HARD-RULES-DIGEST.md":
            continue  # the kernel is taken fresh from the compiled digest below
        h.update(p.relative_to(mod).as_posix().encode())
        h.update(p.read_bytes())
    h.update(digest.read_bytes())
    dest = _inside(root, root / "releases" / f"{_version(mod)}-{h.hexdigest()[:8]}")
    if dest.exists():
        return dest  # same content already released: releases are immutable
    tmp = dest.with_name(dest.name + ".tmp")
    if tmp.exists():
        shutil.rmtree(_inside(root, tmp))
    for p in files:
        out = tmp / p.relative_to(mod)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, out)
    (tmp / "kernel").mkdir(parents=True, exist_ok=True)
    shutil.copy2(digest, tmp / "kernel" / "HARD-RULES-DIGEST.md")
    tmp.rename(dest)
    return dest


def _write_marketplace(root: Path, version: str) -> None:
    mp = root / ".claude-plugin" / "marketplace.json"
    mp.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "name": MARKETPLACE,
        "owner": {"name": "Claude Power Pack"},
        "plugins": [{"name": PLUGIN, "source": "./active", "version": version,
                     "description": "CPP Cognitive Runtime (goal ccr)"}],
    }
    tmp = mp.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    tmp.replace(mp)


def activate(root: Path, release: Path) -> dict:
    release = _inside(root, release)
    if not (release / ".claude-plugin" / "plugin.json").is_file():
        raise SystemExit(f"refused: {release} is not a built release")
    active, prev, staged = root / "active", root / "active.prev", root / "active.new"
    if staged.exists():
        shutil.rmtree(_inside(root, staged))
    shutil.copytree(release, staged)
    if prev.exists():
        shutil.rmtree(_inside(root, prev))  # only ever a copy this tool made from releases/
    if active.exists():
        active.rename(prev)
    staged.rename(active)
    record = {"release": release.name, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    (root / "ACTIVE.json").write_text(json.dumps(record) + "\n", encoding="utf-8")
    _write_marketplace(root, _version(active))
    (root / "state").mkdir(exist_ok=True)
    return record


def rollback(root: Path) -> dict:
    active, prev, swap = root / "active", root / "active.prev", root / "active.swap"
    if not prev.exists():
        raise SystemExit("refused: no previous release to roll back to")
    active.rename(swap)
    prev.rename(active)
    swap.rename(prev)
    record = {"release": "rolled-back", "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    (root / "ACTIVE.json").write_text(json.dumps(record) + "\n", encoding="utf-8")
    _write_marketplace(root, _version(active))
    return record


def set_off(root: Path, off: bool) -> bool:
    flag = root / "state" / "OFF"
    flag.parent.mkdir(parents=True, exist_ok=True)
    if off:
        flag.write_text("", encoding="utf-8")
    elif flag.exists():
        flag.unlink()
    return flag.exists()


def status(root: Path) -> dict:
    active = root / "active"
    return {
        "root": str(root),
        "active": json.loads((root / "ACTIVE.json").read_text(encoding="utf-8")) if (root / "ACTIVE.json").exists() else None,
        "version": _version(active) if active.exists() else None,
        "previous": (root / "active.prev").exists(),
        "off": (root / "state" / "OFF").exists(),
        "releases": sorted(p.name for p in (root / "releases").glob("*") if p.is_dir()) if (root / "releases").exists() else [],
    }


def install_commands(root: Path) -> list[str]:
    return [
        f'claude plugin marketplace add "{root}"',
        f"claude plugin install {PLUGIN}@{MARKETPLACE} --scope user",
    ]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("release", help="build from mods/ and activate it")
    sub.add_parser("rollback")
    sub.add_parser("off")
    sub.add_parser("on")
    sub.add_parser("status")
    sub.add_parser("install-commands")
    a = ap.parse_args(argv)
    root = a.root
    root.mkdir(parents=True, exist_ok=True)
    if a.cmd == "release":
        out = activate(root, build(root))
    elif a.cmd == "rollback":
        out = rollback(root)
    elif a.cmd in ("off", "on"):
        out = {"off": set_off(root, a.cmd == "off")}
    elif a.cmd == "status":
        out = status(root)
    else:
        out = {"commands": install_commands(root)}
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
