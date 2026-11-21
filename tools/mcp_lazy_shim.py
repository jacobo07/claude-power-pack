"""mcp_lazy_shim.py -- Resource Residency Fabric P2 (plan vault/plans/resource-residency-fabric-20261120.md).

Claude Code spawns every stdio MCP server of a scope at session start. This shim stands in for ONE server:
it answers `initialize` and `tools/list` from a cached schema and spawns the real server only when the
session sends anything else (the first `tools/call`, a resources/prompts request). After the spawn it is a
transparent pipe. Residency follows demand: a session that never calls the server never pays for its process.

  run <name>      what the host executes (cfg lives in the private store, NOT in ~/.claude.json)
  record <name>   spawn the real server once, cache its initialize result + full tools/list

Safety posture (every uncertainty degrades to the old behaviour, never to a broken tool):
  - CPP_MCP_LAZY=off, no cache, or a cache recorded for a different command/args -> spawn the real server
    immediately and pipe (exactly what the host did before).
  - A cached schema can go stale: `record` refreshes it; a server whose tools changed is a re-record.
  - Secrets: the real command/args/env come from the private store (~/.claude/state/mcp_catalog_private.json).
    The cache holds schemas only. Nothing here prints args or env.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time

HOME = os.path.expanduser("~")
DEFAULT_STORE = os.path.join(HOME, ".claude", "state", "mcp_catalog_private.json")
DEFAULT_CACHE = os.path.join(HOME, ".claude", "state", "mcp_lazy_cache")
SHIM_MARK = "mcp_lazy_shim"          # mcp_scope uses this to recognise a shim entry and never store it as a real config
PROTOCOL = "2025-06-18"
SERVE_FROM_CACHE = True             # the lazy point; the mutation drill flips it and the lazy gates must go red
INIT_ID = "__cpp_lazy_init__"


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def cfg_sig(cfg: dict) -> str:
    """Identity of WHAT is spawned (command + args). Env is excluded: it carries secrets and cannot change the schema."""
    return hashlib.sha256(json.dumps([cfg.get("command"), cfg.get("args", [])]).encode()).hexdigest()[:16]


def _event(cache_dir: str, name: str, event: str, **kw) -> None:
    try:
        os.makedirs(cache_dir, exist_ok=True)
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": os.getpid(), "server": name, "event": event, **kw}
        with open(os.path.join(cache_dir, "events.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except OSError:
        pass                        # telemetry must never break the pipe


def spawn(cfg: dict) -> subprocess.Popen:
    cmd = cfg["command"]
    exe = shutil.which(cmd) or cmd
    env = {**os.environ, **{k: str(v) for k, v in (cfg.get("env") or {}).items()}}
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.Popen([exe, *cfg.get("args", [])], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=None, env=env, creationflags=flags)


def _send(proc, msg: dict) -> None:
    proc.stdin.write((json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8"))
    proc.stdin.flush()


def _read_until(proc, want_id, timeout: float) -> dict:
    """Read child stdout lines until the response carrying want_id (other traffic is dropped)."""
    box: dict = {}

    def pump():
        for raw in proc.stdout:
            try:
                m = json.loads(raw)
            except ValueError:
                continue
            if m.get("id") == want_id and ("result" in m or "error" in m):
                box["m"] = m
                return
    t = threading.Thread(target=pump, daemon=True)
    t.start()
    t.join(timeout)
    if "m" not in box:
        raise RuntimeError(f"no response for {want_id!r} within {timeout}s")
    return box["m"]


def handshake(proc, init_params: dict, timeout: float = 30.0) -> dict:
    _send(proc, {"jsonrpc": "2.0", "id": INIT_ID, "method": "initialize", "params": init_params})
    resp = _read_until(proc, INIT_ID, timeout)
    if "error" in resp:
        raise RuntimeError(f"real server rejected initialize: {resp['error']}")
    _send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
    return resp["result"]


def record(name: str, store: str, cache_dir: str) -> dict:
    cfg = _load(store, {}).get(name)
    if not cfg:
        raise KeyError(f"{name} is not in the private store")
    proc = spawn(cfg)
    try:
        init = handshake(proc, {"protocolVersion": PROTOCOL, "capabilities": {},
                                "clientInfo": {"name": "cpp-lazy-record", "version": "1"}})
        tools, cursor, n = [], None, 0
        while True:
            n += 1
            _send(proc, {"jsonrpc": "2.0", "id": f"__tl{n}__", "method": "tools/list",
                         "params": ({"cursor": cursor} if cursor else {})})
            r = _read_until(proc, f"__tl{n}__", 30.0)
            if "error" in r:
                raise RuntimeError(f"tools/list failed: {r['error']}")
            tools += r["result"].get("tools", [])
            cursor = r["result"].get("nextCursor")
            if not cursor:
                break
    finally:
        proc.terminate()
    os.makedirs(cache_dir, exist_ok=True)
    data = {"server": name, "sig": cfg_sig(cfg), "recorded": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "initialize": init, "tools": tools}
    with open(os.path.join(cache_dir, f"{name}.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    _event(cache_dir, name, "recorded", tools=len(tools))
    return {"server": name, "tools": len(tools), "protocolVersion": init.get("protocolVersion")}


class Out:
    def __init__(self):
        self.lock = threading.Lock()

    def write(self, msg: dict) -> None:
        data = (json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8")
        with self.lock:
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()


def _pipe_child_to_host(proc, out: Out) -> None:
    for raw in proc.stdout:
        with out.lock:
            sys.stdout.buffer.write(raw if raw.endswith(b"\n") else raw + b"\n")
            sys.stdout.buffer.flush()
    # The real server closed its stdout (it died or exited). Mirror that to the host: a shim that outlives its
    # server is a server that never answers. The main loop is parked on the host's stdin, so exit from here.
    rc = proc.wait()
    os._exit(rc if rc else 1)


def run(name: str, store: str, cache_dir: str) -> int:
    cfg = _load(store, {}).get(name)
    if not cfg:
        sys.stderr.write(f"mcp_lazy_shim: {name} is not in the private store\n")
        return 1
    cache = _load(os.path.join(cache_dir, f"{name}.json"), None)
    lazy = (SERVE_FROM_CACHE and os.environ.get("CPP_MCP_LAZY", "").lower() != "off"
            and cache is not None and cache.get("sig") == cfg_sig(cfg))
    out = Out()
    proc = None
    client_init = None

    def ensure_spawned(trigger: str):
        nonlocal proc
        if proc is not None:
            return
        proc = spawn(cfg)
        _event(cache_dir, name, "spawn", trigger=trigger, lazy=lazy, child=proc.pid)
        if client_init is not None:
            handshake(proc, client_init["params"])   # replay the host's own initialize, then notifications/initialized
        threading.Thread(target=_pipe_child_to_host, args=(proc, out), daemon=True).start()

    if not lazy:
        # Old behaviour: the real server exists from the start and every byte passes through.
        proc = spawn(cfg)
        _event(cache_dir, name, "eager", reason=("kill-switch" if os.environ.get("CPP_MCP_LAZY", "").lower() == "off"
                                                  else "no-cache-or-sig" ), child=proc.pid)
        threading.Thread(target=_pipe_child_to_host, args=(proc, out), daemon=True).start()
        for raw in sys.stdin.buffer:
            try:
                proc.stdin.write(raw if raw.endswith(b"\n") else raw + b"\n")
                proc.stdin.flush()
            except OSError:
                break
        proc.terminate()
        return 0

    for raw in sys.stdin.buffer:
        try:
            msg = json.loads(raw)
        except ValueError:
            continue
        method, mid = msg.get("method"), msg.get("id")
        if proc is None:
            if method == "initialize":
                client_init = msg
                res = dict(cache["initialize"])
                _event(cache_dir, name, "served", method=method)
                out.write({"jsonrpc": "2.0", "id": mid, "result": res})
                continue
            if method == "notifications/initialized":
                continue                 # handshake() sends its own when the real server is born
            if method == "tools/list":
                _event(cache_dir, name, "served", method=method)
                out.write({"jsonrpc": "2.0", "id": mid, "result": {"tools": cache["tools"]}})
                continue
            if method == "ping":
                out.write({"jsonrpc": "2.0", "id": mid, "result": {}})
                continue
            if mid is None:              # any other notification before the real server exists: nothing to tell it
                continue
            try:
                ensure_spawned(method or "?")
            except Exception as e:       # noqa: BLE001 -- a failed spawn must answer the request, never hang the host
                out.write({"jsonrpc": "2.0", "id": mid,
                           "error": {"code": -32603, "message": f"lazy spawn failed: {type(e).__name__}"}})
                return 1
        try:
            _send(proc, msg)
        except OSError:
            if mid is not None:
                out.write({"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": "real server exited"}})
            return 1
        if proc.poll() is not None:
            break
    if proc is not None:
        proc.terminate()
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--store", default=DEFAULT_STORE)
    ap.add_argument("--cache", default=DEFAULT_CACHE)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("run", "record"):
        p = sub.add_parser(c)
        p.add_argument("server")
    a = ap.parse_args(argv)
    if a.cmd == "run":
        return run(a.server, a.store, a.cache)
    try:
        print(json.dumps(record(a.server, a.store, a.cache)))
        return 0
    except (KeyError, RuntimeError) as e:
        print(json.dumps({"error": str(e)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
