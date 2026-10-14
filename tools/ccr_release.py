"""Release, activate, roll back and switch off the CPP Cognitive Runtime mod (goal ccr).

Layout under --root (default ~/.claude/ccr):
  releases/<version>-<hash8>/  immutable copies of mods/cpp-cognitive-runtime (tests and dev state excluded)
  active/                      the release Claude Code loads (folder marketplace entry "./active")
  active.prev/                 the release before it; `rollback` swaps the two
  state/                       receipts, modes.json, and OFF (kill switch read at every session start)
  releases/*/RELEASE.json      the release id; the runtime reads it from its own load path into the `start` receipt
  .claude-plugin/marketplace.json

`status --sessions` joins the host's live-session listing (~/.claude/sessions/<pid>.json) with the `start`
receipts: per live session, the release it LOADED (receipt `releaseId`) vs the active one. No start receipt, or one
written before A1 (no `releaseId` field), is UNKNOWN: a version is never inferred from an absence.

This tool never runs `claude plugin ...`: registering the marketplace and installing the plugin are the
Owner's step (goal ccr, option 2). `install-commands` prints them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
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
    (tmp / "RELEASE.json").write_text(json.dumps({"release": dest.name, "version": _version(mod)}) + "\n", encoding="utf-8")
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
    record = {"release": _release_id(active) or "rolled-back", "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
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


def _release_id(d: Path) -> str | None:
    try:
        rid = json.loads((d / "RELEASE.json").read_text(encoding="utf-8")).get("release")
    except (OSError, ValueError, AttributeError):
        return None  # a release built before A1, or no release here
    return rid if isinstance(rid, str) else None


def _alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        k32 = ctypes.windll.kernel32
        h = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k32.GetExitCodeProcess(h, ctypes.byref(code))
        k32.CloseHandle(h)
        return bool(ok) and code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, owned by someone else
    return True


def _proc_start(pid: int) -> str | None:
    """Linux start time in clock ticks (field 22 of /proc/<pid>/stat): guards against pid reuse. None elsewhere."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return None
    return stat[stat.rindex(")") + 2:].split()[19]


def live_sessions(listing: Path, alive=_alive, proc_start=_proc_start) -> list[dict]:
    out = []
    for f in sorted(listing.glob("*.json")) if listing.is_dir() else []:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            pid, sid = int(d["pid"]), str(d["sessionId"])
        except (OSError, ValueError, KeyError, TypeError):
            continue  # a half-written or foreign file is not a session
        if not alive(pid):
            continue
        ps = proc_start(pid)
        if ps is not None and d.get("procStart") is not None and str(d["procStart"]) != ps:
            continue  # the pid was reused by another process
        out.append({"pid": pid, "sid": sid, "cwd": d.get("cwd"), "host": d.get("version"), "kind": d.get("kind")})
    return out


def last_start(receipt_dirs: list[Path], sid: str) -> dict | None:
    """The newest `start` receipt of sid across receipt dirs (a --resume appends another start to the same file)."""
    best = None
    for rd in receipt_dirs:
        for f in rd.glob(f"*/{sid}.jsonl") if rd.is_dir() else []:
            for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if isinstance(r, dict) and r.get("ev") == "start" and (best is None or r.get("ts", 0) >= best.get("ts", 0)):
                    best = r
    return best


def session_status(root: Path, listing: Path, receipt_dirs: list[Path], alive=_alive, proc_start=_proc_start) -> dict:
    active = json.loads((root / "ACTIVE.json").read_text(encoding="utf-8")).get("release") if (root / "ACTIVE.json").exists() else None
    rows = []
    for s in live_sessions(listing, alive, proc_start):
        st = last_start(receipt_dirs, s["sid"])
        loaded = st.get("releaseId") if st else None
        if st is None:
            state = "UNKNOWN"  # no start receipt: the runtime never ran in it, or wrote elsewhere
        elif "releaseId" not in st:
            state = "UNKNOWN"  # a start receipt from a runtime older than A1 names no release
        elif loaded is None:
            state = "DEV"  # loaded from a directory with no RELEASE.json (--plugin-dir on the repo)
        elif active is None:
            state = "UNKNOWN"  # nothing is active to compare against
        else:
            state = "CURRENT" if loaded == active else "STALE"
        rows.append({**s, "loaded": loaded, "release": st.get("release") if st else None,
                     "policyGen": st.get("policyGen") if st else None, "state": state, "stale": state == "STALE"})
    return {"active": active, "sessions": rows,
            "counts": {k: sum(r["state"] == k for r in rows) for k in ("CURRENT", "STALE", "DEV", "UNKNOWN")}}


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
    st = sub.add_parser("status")
    st.add_argument("--sessions", action="store_true", help="loaded vs active release per live claude session")
    st.add_argument("--listing", type=Path, default=Path.home() / ".claude" / "sessions")
    st.add_argument("--receipts", type=Path, action="append", default=[],
                    help="extra receipt dir (e.g. mods/cpp-cognitive-runtime/.state-dev/receipts); <root>/state/receipts is always read")
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
    elif a.cmd == "status" and a.sessions:
        out = session_status(root, a.listing, [root / "state" / "receipts", *a.receipts])
    elif a.cmd == "status":
        out = status(root)
    else:
        out = {"commands": install_commands(root)}
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
