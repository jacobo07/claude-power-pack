"""V-LAZY-* gates for tools/mcp_lazy_shim.py + the lazy/unlazy verbs of tools/mcp_scope.py (Resource Residency P2).

Real byte shapes: a fake MCP server speaking newline-delimited JSON-RPC over real pipes, driven through the
shim as a subprocess. The server logs every birth and every message it receives to a marker file, so
"the real server was NOT spawned" is observed from outside, not inferred.
Mutation drill: the same lazy gates run against a copy of the shim with SERVE_FROM_CACHE flipped; they must go RED.
Exit 0 only if every gate passes AND the mutant is caught.
"""
import contextlib
import importlib
import io
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
SHIM = os.path.join(HERE, "mcp_lazy_shim.py")
MARKER = "zz-marker-4f9a"      # stands in for a credential: must never appear in the host config

FAKE = r'''
import json, os, sys
mark = os.environ["FAKE_MARK"]
def log(kind, **kw):
    with open(mark, "a", encoding="utf-8") as f:
        f.write(json.dumps({"k": kind, **kw}) + "\n")
log("birth", pid=os.getpid(), ver=os.environ.get("FAKE_VER", "?"))
def out(m): sys.stdout.write(json.dumps(m) + "\n"); sys.stdout.flush()
for line in sys.stdin:
    m = json.loads(line); meth = m.get("method"); mid = m.get("id")
    log("recv", method=meth)
    if meth == "initialize":
        log("init_params", pv=m["params"].get("protocolVersion"), client=m["params"].get("clientInfo", {}).get("name"))
        out({"jsonrpc": "2.0", "id": mid, "result": {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}},
             "serverInfo": {"name": "fake", "version": os.environ.get("FAKE_VER", "?")}}})
    elif meth == "tools/list":
        out({"jsonrpc": "2.0", "id": mid, "result": {"tools": [
            {"name": "echo", "description": "echo", "inputSchema": {"type": "object"}},
            {"name": "add", "description": "add", "inputSchema": {"type": "object"}}]}})
    elif meth == "tools/call":
        if os.environ.get("FAKE_DIE") == "1":
            sys.exit(3)
        out({"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": json.dumps(m["params"], ensure_ascii=False)}]}})
    elif meth == "ping":
        out({"jsonrpc": "2.0", "id": mid, "result": {}})
'''

results = []


def check(gid, ok, detail=""):
    results.append((gid, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + gid + (f"  -- {detail}" if detail and not ok else ""))


class Shim:
    """Drive `shim run fake` over pipes with a timeout on every read."""

    def __init__(self, shim, store, cache, env_extra=None):
        env = {**os.environ, **(env_extra or {})}
        self.p = subprocess.Popen([sys.executable, shim, "--store", store, "--cache", cache, "run", "fake"],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env)
        self.q = queue.Queue()
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self):
        for raw in self.p.stdout:
            self.q.put(raw)

    def send(self, m):
        self.p.stdin.write((json.dumps(m, ensure_ascii=False) + "\n").encode("utf-8"))
        self.p.stdin.flush()

    def recv(self, t=15):
        try:
            return json.loads(self.q.get(timeout=t))
        except queue.Empty:
            return None

    def close(self):
        try:
            self.p.stdin.close()
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def births(mark):
    if not os.path.exists(mark):
        return 0
    return sum(1 for line in open(mark, encoding="utf-8") if '"k": "birth"' in line)


def recvs(mark):
    if not os.path.exists(mark):
        return []
    return [json.loads(line)["method"] for line in open(mark, encoding="utf-8") if '"k": "recv"' in line]


def setup(tmp, name="fake"):
    os.makedirs(tmp, exist_ok=True)
    fake = os.path.join(tmp, "fake_server.py")
    open(fake, "w", encoding="utf-8").write(FAKE)
    mark = os.path.join(tmp, "mark.jsonl")
    env = {"FAKE_MARK": mark, "FAKE_VER": "cached", "FAKE_CRED": MARKER}
    store = os.path.join(tmp, "store.json")
    json.dump({name: {"type": "stdio", "command": sys.executable, "args": [fake], "env": env}}, open(store, "w"))
    return fake, mark, store, os.path.join(tmp, "cache")


def set_env(store, name, **kv):
    d = json.load(open(store))
    d[name]["env"].update(kv)
    json.dump(d, open(store, "w"))


def record(shim, store, cache):
    return subprocess.run([sys.executable, shim, "--store", store, "--cache", cache, "record", "fake"],
                          capture_output=True, text=True, timeout=60)


def init_msg(i=1):
    return {"jsonrpc": "2.0", "id": i, "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                       "clientInfo": {"name": "claude-code-test", "version": "9"}}}


def lazy_gates(shim, label):
    """The gates that PROVE laziness. Returns the booleans for the mutation drill."""
    out = []
    tmp = tempfile.mkdtemp(prefix="lazy-")
    try:
        fake, mark, store, cache = setup(tmp)
        rc = record(shim, store, cache)
        rec_ok = rc.returncode == 0 and json.loads(rc.stdout).get("tools") == 2
        out.append(("V-LAZY-01 record spawns the real server once and caches 2 tools", rec_ok and births(mark) == 1, rc.stdout + rc.stderr))
        b0 = births(mark)
        set_env(store, "fake", FAKE_VER="live")          # distinguishes a cached answer from a live one
        s = Shim(shim, store, cache)
        s.send(init_msg(1))
        r1 = s.recv()
        s.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        s.send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        r2 = s.recv()
        s.send({"jsonrpc": "2.0", "id": 3, "method": "ping"})
        r3 = s.recv()
        out.append(("V-LAZY-02 initialize answered from cache, real server NOT born",
                    births(mark) == b0 and r1 and r1["result"]["serverInfo"]["version"] == "cached" and r1["id"] == 1,
                    f"{r1} births={births(mark)}"))
        out.append(("V-LAZY-03 tools/list + ping answered with no birth, full schema intact",
                    births(mark) == b0 and r2 and [t["name"] for t in r2["result"]["tools"]] == ["echo", "add"]
                    and r3 and r3["id"] == 3, f"{r2} {r3}"))
        arg = {"name": "echo", "arguments": {"q": "ñandú ✓ \u2603", "n": 7}}
        s.send({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": arg})
        r4 = s.recv()
        txt = json.loads(r4["result"]["content"][0]["text"]) if r4 and "result" in r4 else None
        out.append(("V-LAZY-04 first tools/call spawns the real server exactly once and answers correctly (unicode round trip)",
                    births(mark) == b0 + 1 and r4 and r4["id"] == 4 and txt == arg, f"{r4} births={births(mark)}"))
        ml = [json.loads(line) for line in open(mark, encoding="utf-8")]
        ip = [m for m in ml if m["k"] == "init_params"]
        out.append(("V-LAZY-05 real server received the HOST's own initialize params, then notifications/initialized",
                    bool(ip) and ip[-1]["client"] == "claude-code-test" and "notifications/initialized" in recvs(mark), f"{ip}"))
        s.send({"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "add", "arguments": {}}})
        r5 = s.recv()
        out.append(("V-LAZY-06 second call reuses the same real server (no second birth)",
                    births(mark) == b0 + 1 and r5 and r5["id"] == 5, f"{r5}"))
        s.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for gid, ok, d in out:
        check(f"{gid} [{label}]", ok, str(d)[:200])
    return [bool(ok) for _, ok, _ in out]


def main():
    shim_src = open(SHIM, encoding="utf-8").read()
    lazy_gates(SHIM, "real")

    root = tempfile.mkdtemp(prefix="lazy-")
    try:
        # V-LAZY-07 kill switch: real server born immediately, answers live
        fake, mark, store, cache = setup(os.path.join(root, "ks"))
        record(SHIM, store, cache)
        set_env(store, "fake", FAKE_VER="live")
        b0 = births(mark)
        s = Shim(SHIM, store, cache, {"CPP_MCP_LAZY": "off"})
        s.send(init_msg(1))
        r = s.recv()
        check("V-LAZY-07 CPP_MCP_LAZY=off: real server born at start, live answer, not the cache",
              births(mark) == b0 + 1 and r and r["result"]["serverInfo"]["version"] == "live", str(r))
        s.close()

        # V-LAZY-08 no cache -> eager
        fake, mark, store, cache = setup(os.path.join(root, "nc"))
        s = Shim(SHIM, store, cache)
        s.send(init_msg(1))
        r = s.recv()
        check("V-LAZY-08 no cache: falls back to eager pass-through (old behaviour), still answers",
              births(mark) == 1 and r and r["result"]["serverInfo"]["version"] == "cached", str(r))
        s.close()

        # V-LAZY-09 stale cache (command/args changed) -> eager
        fake, mark, store, cache = setup(os.path.join(root, "sg"))
        record(SHIM, store, cache)
        d = json.load(open(store))
        d["fake"]["args"] = [fake, "--changed"]
        json.dump(d, open(store, "w"))
        b0 = births(mark)
        s = Shim(SHIM, store, cache)
        s.send(init_msg(1))
        r = s.recv()
        check("V-LAZY-09 cache recorded for different args is ignored (signature mismatch -> eager, never a wrong schema)",
              births(mark) == b0 + 1 and r is not None, str(r))
        s.close()

        # V-LAZY-10 real server dies on first call -> shim exits, no hung host pipe
        fake, mark, store, cache = setup(os.path.join(root, "dd"))
        record(SHIM, store, cache)
        set_env(store, "fake", FAKE_DIE="1")
        s = Shim(SHIM, store, cache)
        s.send(init_msg(1))
        s.recv()
        s.send({"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": {"name": "echo", "arguments": {}}})
        try:
            s.p.wait(timeout=15)
            exited = True
        except subprocess.TimeoutExpired:
            exited = False
        check("V-LAZY-10 real server dying mid-call: shim exits (no hung host pipe)", exited, "shim still alive after 15s")
        s.close()

        # V-LAZY-11/12/13 mcp_scope lazy/unlazy on a temp config
        fake, mark, store, cache = setup(os.path.join(root, "sc"))
        proj = "C:/Proj/Home"
        real = json.load(open(store))["fake"]
        cfgp = os.path.join(root, "sc", "claude.json")
        json.dump({"mcpServers": {}, "projects": {proj: {"mcpServers": {"fake": real}}}}, open(cfgp, "w"))
        sys.path.insert(0, HERE)
        ms = importlib.import_module("mcp_scope")
        sc = ms.Scope(cfgp, store, os.path.join(root, "sc", "cat.json"))
        res = sc.lazy("fake", proj, SHIM, cache)
        txt = open(cfgp, encoding="utf-8").read()
        e = json.load(open(cfgp))["projects"][proj]["mcpServers"]["fake"]
        check("V-LAZY-11 lazy: project entry now points at the shim; no credential value anywhere in the host config",
              res["tools_cached"] == 2 and "mcp_lazy_shim" in json.dumps(e["args"]) and MARKER not in txt and e["env"] == {}, txt[:200])
        sc.disable("fake", proj)
        stored = json.load(open(store))
        check("V-LAZY-12 disabling a lazy entry never replaces the stored real config with the shim pointer",
              stored["fake"]["command"] == real["command"] and MARKER in json.dumps(stored), "store overwritten")
        sc.enable("fake", proj)
        sc.lazy("fake", proj, SHIM, cache)
        sc.unlazy("fake", proj)
        check("V-LAZY-13 unlazy restores the real config byte-for-byte from the private store",
              json.load(open(cfgp))["projects"][proj]["mcpServers"]["fake"] == real)

        # Mutation drill: flip the lazy point; the lazy gates MUST go red.
        assert "SERVE_FROM_CACHE = True" in shim_src
        mutant = os.path.join(root, "mutant_shim.py")
        open(mutant, "w", encoding="utf-8").write(shim_src.replace("SERVE_FROM_CACHE = True", "SERVE_FROM_CACHE = False"))
        before = len(results)
        with contextlib.redirect_stdout(io.StringIO()):
            oks = lazy_gates(mutant, "MUTANT")
        del results[before:]          # the mutant's own FAILs are the expected outcome, not suite failures
        check("V-LAZY-MUT mutant (cache never served) is caught: at least one lazy gate goes red", not all(oks),
              "mutant passed every lazy gate: the gates cannot see eager spawning")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    bad = [g for g, ok, _ in results if not ok]
    print(f"\n{len(results) - len(bad)}/{len(results)} gates PASS")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
