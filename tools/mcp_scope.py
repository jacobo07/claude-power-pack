"""mcp_scope.py -- Resource Residency Fabric P1 (plan vault/plans/resource-residency-fabric-20261120.md).

Moves MCP servers out of Claude Code's USER scope (~/.claude.json `mcpServers`, spawned by EVERY session)
into the local scope of the projects that use them (`projects[<path>].mcpServers`), or into a catalog only.
Availability stays: `enable <server> --project <path>` rematerialises a catalogued server in one command.

Secrets: server configs carry API keys in args/env. Full configs live ONLY in the private store
(~/.claude/state/mcp_catalog_private.json, outside any repo). The repo catalog
(vault/registry/mcp_catalog.json) holds names, transport, homes and usage -- never args or env.
Nothing here prints args or env.

Rollback: every mutation writes a timestamped backup of the config first; `restore-user <server>` puts a
server back in user scope. Kill switch CPP_MCP_SCOPE=off refuses demote/enable (restore stays allowed).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time

HOME = os.path.expanduser("~")
DEFAULT_CONFIG = os.path.join(HOME, ".claude.json")
DEFAULT_PRIVATE = os.path.join(HOME, ".claude", "state", "mcp_catalog_private.json")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CATALOG = os.path.join(REPO, "vault", "registry", "mcp_catalog.json")
SHIM_MARK = "mcp_lazy_shim"             # a config whose args name the shim is a pointer, never the real server config
DEFAULT_LAZY_CACHE = os.path.join(HOME, ".claude", "state", "mcp_lazy_cache")
# The host executes the shim from a stable copy, so a deleted worktree / moved checkout can never break a live session.
STABLE_SHIM = os.path.join(HOME, ".claude", "state", "mcp_lazy", "mcp_lazy_shim.py")


def norm_project(path: str) -> str:
    """~/.claude.json keys projects with forward slashes and the drive letter as typed (C:/Users/...)."""
    p = os.path.normpath(path).replace("\\", "/")
    return p[0].upper() + p[1:] if len(p) > 1 and p[1] == ":" else p


def _sha(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _load(path: str, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _atomic_write(path: str, data) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = f"{path}.tmp-{os.getpid()}"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


class Scope:
    def __init__(self, config: str, private: str, catalog: str):
        self.config, self.private, self.catalog = config, private, catalog

    # -- config transaction: read, mutate, compare-and-swap (live sessions rewrite this file) --
    def mutate(self, fn) -> dict:
        for attempt in range(5):
            before = _sha(self.config)
            data = _load(self.config, {})
            result = fn(data)
            if _sha(self.config) != before:      # a session wrote in between: redo on the fresh file
                time.sleep(0.2 * (attempt + 1))
                continue
            bk = f"{self.config}.mcp-scope-{time.strftime('%Y%m%d-%H%M%S')}.bak"
            shutil.copy2(self.config, bk)
            _atomic_write(self.config, data)
            result["backup"] = bk
            return result
        raise RuntimeError("config kept changing under 5 attempts; nothing written")

    def _remember(self, name: str, cfg: dict) -> None:
        if SHIM_MARK in json.dumps(cfg.get("args", [])):
            return                       # a lazy shim entry is a pointer, never the real config: keep the stored original
        store = _load(self.private, {})
        store[name] = cfg
        _atomic_write(self.private, store)

    def lazy(self, name: str, project: str, shim: str, cache_dir: str) -> dict:
        """Replace a project-scope entry with the P2 shim (real config stays in the private store; schema is recorded first)."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("mcp_lazy_shim", shim)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        home = norm_project(project)
        rec = mod.record(name, self.private, cache_dir)           # raises if the real server cannot be reached: nothing changes
        entry = {"type": "stdio", "command": sys.executable,
                 "args": [os.path.abspath(shim), "--store", self.private, "--cache", cache_dir, "run", name], "env": {}}

        def fn(d):
            ms = d.get("projects", {}).get(home, {}).get("mcpServers", {})
            if name not in ms:
                raise KeyError(f"{name} is not enabled in {home}")
            if SHIM_MARK not in json.dumps(ms[name].get("args", [])):
                self._remember(name, ms[name])                    # keep the real config before replacing it
            ms[name] = entry
            return {"server": name, "lazy_in": home, "tools_cached": rec["tools"]}

        res = self.mutate(fn)
        self._catalog_note(name, lazy_in=sorted(set(_load(self.catalog, {"servers": {}})["servers"].get(name, {}).get("lazy_in", [])) | {home}))
        return res

    def unlazy(self, name: str, project: str) -> dict:
        store = _load(self.private, {})
        if name not in store:
            raise KeyError(f"{name} is not in the private store")
        home = norm_project(project)

        def fn(d):
            ms = d.get("projects", {}).get(home, {}).get("mcpServers", {})
            if name not in ms:
                raise KeyError(f"{name} is not enabled in {home}")
            ms[name] = store[name]
            return {"server": name, "unlazy_in": home}

        res = self.mutate(fn)
        cur = _load(self.catalog, {"servers": {}})["servers"].get(name, {}).get("lazy_in", [])
        self._catalog_note(name, lazy_in=[h for h in cur if h != home])
        return res

    def _catalog_note(self, name: str, **fields) -> None:
        cat = _load(self.catalog, {"schema": 1, "servers": {}})
        entry = cat["servers"].setdefault(name, {"homes": []})
        for k, v in fields.items():
            if k == "add_homes":
                entry["homes"] = sorted(set(entry.get("homes", [])) | set(v))
            elif k == "drop_home":
                entry["homes"] = [h for h in entry.get("homes", []) if h != v]
            else:
                entry[k] = v
        _atomic_write(self.catalog, cat)

    def demote(self, name: str, projects: list[str], usage: dict | None = None) -> dict:
        homes = [norm_project(p) for p in projects]

        def fn(d):
            user = d.setdefault("mcpServers", {})
            if name not in user:
                raise KeyError(f"{name} is not in user scope")
            cfg = user[name]
            self._remember(name, cfg)            # private store first: the config can never be lost
            for h in homes:
                d.setdefault("projects", {}).setdefault(h, {}).setdefault("mcpServers", {})[name] = cfg
            del user[name]
            return {"server": name, "homes": homes, "transport": cfg.get("type", "stdio")}

        res = self.mutate(fn)
        self._catalog_note(name, transport=res["transport"], scope="project" if homes else "catalog",
                           demoted=time.strftime("%Y-%m-%d"), add_homes=homes, **({"usage": usage} if usage else {}))
        return res

    def enable(self, name: str, project: str) -> dict:
        store = _load(self.private, {})
        if name not in store:
            raise KeyError(f"{name} is not in the private store ({self.private})")
        home = norm_project(project)

        def fn(d):
            d.setdefault("projects", {}).setdefault(home, {}).setdefault("mcpServers", {})[name] = store[name]
            return {"server": name, "enabled_in": home}

        res = self.mutate(fn)
        self._catalog_note(name, add_homes=[home])
        return res

    def disable(self, name: str, project: str) -> dict:
        home = norm_project(project)

        def fn(d):
            ms = d.get("projects", {}).get(home, {}).get("mcpServers", {})
            if name not in ms:
                raise KeyError(f"{name} is not enabled in {home}")
            self._remember(name, ms[name])
            del ms[name]
            return {"server": name, "disabled_in": home}

        res = self.mutate(fn)
        self._catalog_note(name, drop_home=home)
        return res

    def restore_user(self, name: str) -> dict:
        store = _load(self.private, {})
        if name not in store:
            raise KeyError(f"{name} is not in the private store")

        def fn(d):
            d.setdefault("mcpServers", {})[name] = store[name]
            return {"server": name, "restored": "user"}

        res = self.mutate(fn)
        self._catalog_note(name, scope="user")
        return res

    def status(self) -> dict:
        d = _load(self.config, {})
        homes = {}
        for p, pv in d.get("projects", {}).items():
            for s in (pv.get("mcpServers") or {}):
                homes.setdefault(s, []).append(p)
        return {"user_scope": sorted(d.get("mcpServers", {})), "project_scope": homes,
                "catalogued": sorted(_load(self.private, {}))}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--config", default=DEFAULT_CONFIG)
    ap.add_argument("--private", default=DEFAULT_PRIVATE)
    ap.add_argument("--catalog", default=DEFAULT_CATALOG)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("demote"); p.add_argument("server"); p.add_argument("--project", action="append", default=[])
    p.add_argument("--calls", type=int); p.add_argument("--window-days", type=int)
    for c in ("enable", "disable"):
        p = sub.add_parser(c); p.add_argument("server"); p.add_argument("--project", required=True)
    p = sub.add_parser("restore-user"); p.add_argument("server")
    for c in ("lazy", "unlazy"):
        p = sub.add_parser(c); p.add_argument("server"); p.add_argument("--project", required=True)
    sub.add_parser("status")
    a = ap.parse_args(argv)
    sc = Scope(a.config, a.private, a.catalog)
    if a.cmd in ("demote", "enable", "lazy") and os.environ.get("CPP_MCP_SCOPE", "").lower() == "off":
        print(json.dumps({"refused": "CPP_MCP_SCOPE=off"})); return 2
    try:
        if a.cmd == "lazy":
            os.makedirs(os.path.dirname(STABLE_SHIM), exist_ok=True)
            shutil.copy2(os.path.join(REPO, "tools", "mcp_lazy_shim.py"), STABLE_SHIM)
            out = sc.lazy(a.server, a.project, STABLE_SHIM, DEFAULT_LAZY_CACHE)
        elif a.cmd == "unlazy":
            out = sc.unlazy(a.server, a.project)
        elif a.cmd == "demote":
            usage = {"calls": a.calls, "window_days": a.window_days} if a.calls is not None else None
            out = sc.demote(a.server, a.project, usage)
        elif a.cmd == "enable":
            out = sc.enable(a.server, a.project)
        elif a.cmd == "disable":
            out = sc.disable(a.server, a.project)
        elif a.cmd == "restore-user":
            out = sc.restore_user(a.server)
        else:
            out = sc.status()
    except (KeyError, RuntimeError) as e:
        print(json.dumps({"error": str(e)})); return 1
    print(json.dumps(out, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
