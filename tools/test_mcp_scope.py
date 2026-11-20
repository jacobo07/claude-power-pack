"""V-MCPSCOPE-* gates for tools/mcp_scope.py (Resource Residency Fabric P1). Runs on temp files only."""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "mcp_scope.py")
MARKER = "PLACEHOLDER_" + "CREDENTIAL_" + "MARKER"   # stands in for a real secret; must never leak
fails = []


def gate(name: str, ok: bool, why: str = "") -> None:
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f" -- {why}"))
    if not ok:
        fails.append(name)


def run(tmp: dict, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    e = dict(os.environ); e.pop("CPP_MCP_SCOPE", None); e.update(env or {})
    cmd = [sys.executable, TOOL, "--config", tmp["config"], "--private", tmp["private"],
           "--catalog", tmp["catalog"], *args]
    return subprocess.run(cmd, capture_output=True, text=True, env=e)


with tempfile.TemporaryDirectory() as d:
    tmp = {k: os.path.join(d, f"{k}.json") for k in ("config", "private", "catalog")}
    cfg = {"mcpServers": {"dead": {"command": "npx", "args": ["x", "--key", MARKER]},
                          "used": {"command": "python", "args": ["s.py"], "env": {"TOKEN": MARKER}}},
           "projects": {"C:/Proj/A": {"allowedTools": []}}, "otherKey": 7}
    json.dump(cfg, open(tmp["config"], "w"))

    r = run(tmp, "demote", "dead", "--calls", "0", "--window-days", "90")
    c = json.load(open(tmp["config"]))
    gate("V-MCPSCOPE-DEMOTE-REMOVES-USER", r.returncode == 0 and "dead" not in c["mcpServers"], r.stdout + r.stderr)
    gate("V-MCPSCOPE-PRESERVES-OTHER-KEYS", c.get("otherKey") == 7 and "used" in c["mcpServers"])
    priv = json.load(open(tmp["private"]))
    gate("V-MCPSCOPE-PRIVATE-KEEPS-CONFIG", priv.get("dead") == cfg["mcpServers"]["dead"])
    cat_text = open(tmp["catalog"]).read()
    gate("V-MCPSCOPE-CATALOG-HAS-NO-SECRET", MARKER not in cat_text and "dead" in cat_text)
    gate("V-MCPSCOPE-STDOUT-HAS-NO-SECRET", MARKER not in r.stdout)
    gate("V-MCPSCOPE-BACKUP-WRITTEN", r.returncode == 0 and os.path.exists(json.loads(r.stdout)["backup"]))

    r = run(tmp, "demote", "used", "--project", r"C:\Proj\A", "--project", r"c:\Proj\B")
    c = json.load(open(tmp["config"]))
    gate("V-MCPSCOPE-PROJECT-HOMES", c["projects"]["C:/Proj/A"]["mcpServers"]["used"] == cfg["mcpServers"]["used"]
         and "used" in c["projects"]["C:/Proj/B"]["mcpServers"], r.stdout + r.stderr)
    gate("V-MCPSCOPE-EXISTING-PROJECT-KEYS-KEPT", c["projects"]["C:/Proj/A"].get("allowedTools") == [])

    r = run(tmp, "enable", "dead", "--project", "C:/Proj/A")
    c = json.load(open(tmp["config"]))
    gate("V-MCPSCOPE-ENABLE-REMATERIALISES", c["projects"]["C:/Proj/A"]["mcpServers"].get("dead") == cfg["mcpServers"]["dead"])
    gate("V-MCPSCOPE-ENABLE-NOT-USER", "dead" not in c["mcpServers"])

    r = run(tmp, "disable", "dead", "--project", "C:/Proj/A")
    c = json.load(open(tmp["config"]))
    gate("V-MCPSCOPE-DISABLE", r.returncode == 0 and "dead" not in c["projects"]["C:/Proj/A"]["mcpServers"])

    r = run(tmp, "enable", "dead", "--project", "C:/Proj/A", env={"CPP_MCP_SCOPE": "off"})
    c = json.load(open(tmp["config"]))
    gate("V-MCPSCOPE-KILL-SWITCH-REFUSES", r.returncode == 2 and "dead" not in c["projects"]["C:/Proj/A"]["mcpServers"])

    r = run(tmp, "restore-user", "dead", env={"CPP_MCP_SCOPE": "off"})
    c = json.load(open(tmp["config"]))
    gate("V-MCPSCOPE-RESTORE-UNDER-KILL-SWITCH", c["mcpServers"].get("dead") == cfg["mcpServers"]["dead"])

    r = run(tmp, "demote", "nope")
    gate("V-MCPSCOPE-UNKNOWN-SERVER-REFUSED", r.returncode == 1 and "error" in r.stdout)

    r = run(tmp, "status")
    st = json.loads(r.stdout)
    gate("V-MCPSCOPE-STATUS", "dead" in st["user_scope"] and "C:/Proj/A" in st["project_scope"]["used"])

print(f"{'ALL PASS' if not fails else 'FAILED: ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
