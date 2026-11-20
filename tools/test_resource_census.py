"""V-CENSUS-* gates for tools/resource_census.py (Resource Residency Fabric P0). Synthetic byte-shapes plus one live smoke."""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SECRET = "PLACEHOLDER_" + "CREDENTIAL_" + "MARKER9f3a1c77d2e0"   # stands in for a real key; must never leak
fails = []


def load():
    spec = importlib.util.spec_from_file_location("resource_census", os.path.join(HERE, "resource_census.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def gate(name, ok, why=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f" -- {why}"))
    if not ok:
        fails.append(name)


def P(pid, ppid, name, cmd, create=100.0, ws=10, private=20, commit=30):
    return {"pid": pid, "ppid": ppid, "name": name, "cmdline": cmd, "create": create, "ws": ws, "private": private, "commit": commit}


SERVERS = {
    "rea": {"command": "node", "args": ["C:/mcp/rea/server.js", "--api-key", SECRET]},
    "gads": {"command": "npx", "args": ["-y", "@acme/google-ads-mcp", f"TOKEN={SECRET}"]},
    "playwright": {"command": "mcp", "args": []},               # the defect shape: bare command, 0 args
    "pw2": {"command": "npx", "args": ["mcp"]},                  # generic-only args
    "remote": {"type": "http", "url": "https://x.example/mcp"},
}


def world():
    return [
        P(1, 0, "claude.exe", "claude --resume 11111111-2222-3333-4444-555555555555", create=10, ws=100, private=200, commit=300),
        P(2, 1, "node.exe", "node C:\\mcp\\rea\\server.js --api-key X", create=20, ws=1, private=2, commit=3),
        P(3, 2, "conhost.exe", "conhost.exe 0x4", create=21, ws=1, private=1, commit=1),
        P(4, 2, "node.exe", "node child-worker.js", create=22, ws=1, private=1, commit=1),
        P(5, 1, "node.exe", "npx -y @acme/google-ads-mcp", create=23, ws=2, private=4, commit=6),
        P(6, 999, "node.exe", "node some-unrelated.js mcp --serve", create=24),      # unrelated, contains "mcp"
        P(7, 1, "claude.exe", "claude", create=11, private=50),
    ]


def snap(mod, procs=None, servers=None):
    sigs, refused = mod.build_signatures(servers or SERVERS)
    return mod.build_snapshot(procs or world(), sigs, {"commit_total": 1000, "commit_limit": 2000}, refused, now=1.0)


def playwright_defect_refused(mod):
    """True when the matcher refuses the bare-command signature AND attributes none of 751 unrelated processes."""
    sigs, refused = mod.build_signatures({"playwright": SERVERS["playwright"]})
    junk = [P(1000 + i, 0, "node.exe", f"node tool{i}.js mcp") for i in range(751)]
    s = mod.build_snapshot(junk, sigs, {}, refused, now=1.0)
    return "playwright" in refused and not s["servers"]


mod = load()
sn = snap(mod)

gate("V-CENSUS-BARE-COMMAND-REFUSED", playwright_defect_refused(mod))
sigs, refused = mod.build_signatures(SERVERS)
gate("V-CENSUS-GENERIC-ARGS-REFUSED", "pw2" in refused and "playwright" in refused and "pw2" not in sigs, str(refused))
gate("V-CENSUS-BINARY-PATH-IS-SIGNATURE", mod.signature_tokens("C:/Apps/ghost-v1/ghost-mcp.exe", []) == ["ghost-mcp.exe"]
     and mod.signature_tokens("node", []) is None and mod.signature_tokens("C:/x/node.exe", []) is None)
gate("V-CENSUS-WRAPPER-KEY-NOT-A-SERVER", "mcpServers" not in mod.collect_configs(os.path.join(HERE, "no-such-home")))
gate("V-CENSUS-REMOTE-SKIPPED","remote" not in sigs and "remote" not in refused)
gate("V-CENSUS-ATTRIBUTES-BY-SIGNATURE", set(sn["servers"]) == {"rea", "gads"}, str(sn["servers"].keys()))
gate("V-CENSUS-DESCENDANTS-INHERIT", sn["servers"]["rea"]["procs"] == 3, str(sn["servers"]["rea"]))   # root + conhost + child
gate("V-CENSUS-UNRELATED-MCP-WORD-NOT-ATTRIBUTED", "6@24" not in sn["identities"])
gate("V-CENSUS-COUNTERS-SEPARATE", sn["servers"]["rea"]["ws"] == 3 and sn["servers"]["rea"]["private"] == 4 and sn["servers"]["rea"]["commit"] == 5,
     str(sn["servers"]["rea"]))
s1 = next(s for s in sn["sessions"] if s["claude_pid"] == 1)
gate("V-CENSUS-SESSION-GROUPING", set(s1["mcp"]) == {"rea", "gads"} and s1["session_id"] == "11111111-2222-3333-4444-555555555555", str(s1))
gate("V-CENSUS-SESSION-WITHOUT-ID-IS-NONE", next(s for s in sn["sessions"] if s["claude_pid"] == 7)["session_id"] is None)
gate("V-CENSUS-NPX-Y-PACKAGE-IS-SIGNATURE", sigs.get("gads") == ["@acme/google-ads-mcp"], str(sigs.get("gads")))
extra = world() + [P(9, 5, "node.exe", "node helper-of-gads.js", create=40)]
gate("V-CENSUS-UNATTRIBUTED-DESCENDANT-COUNTED", s1["unattributed_descendants"] == 0
     and snap(mod, extra)["servers"]["gads"]["procs"] == 2, str(s1))

amb = {"a": {"command": "node", "args": ["shared-lib-server.js"]}, "b": {"command": "node", "args": ["shared-lib-server.js"]}}
sa = snap(mod, [P(1, 0, "claude.exe", "claude"), P(2, 1, "node.exe", "node shared-lib-server.js")], amb)
gate("V-CENSUS-AMBIGUOUS-IS-UNKNOWN", not sa["servers"], str(sa["servers"]))

# pid reuse: the "parent" was created AFTER the child -> not a parent
reuse = [P(1, 0, "claude.exe", "claude", create=500), P(2, 1, "node.exe", "node C:/mcp/rea/server.js", create=100)]
sr = snap(mod, reuse)
gate("V-CENSUS-PID-REUSE-NOT-ANCESTRY", sr["servers"].get("rea", {}).get("live_sessions", 0) == 0 and sr["claude_sessions"] == 1, str(sr["sessions"]))

text = json.dumps(sn)
gate("V-CENSUS-SNAPSHOT-HAS-NO-SECRET-OR-SIGNATURE", SECRET not in text and "google-ads-mcp" not in text and "server.js" not in text)
sig_text = json.dumps(sigs)
gate("V-CENSUS-SIGNATURE-DROPS-SECRETS-AND-FLAG-VALUES", SECRET.lower() not in sig_text.lower() and "api-key" not in sig_text, sig_text)

later = world() + [P(8, 1, "node.exe", "npx -y @acme/google-ads-mcp", create=30, private=7)]
d = mod.diff_snapshots(sn, snap(mod, later))
gate("V-CENSUS-DIFF", d["mcp_born"] == 1 and d["servers"]["gads"]["procs"] == 1 and d["servers"]["gads"]["private"] == 7, str(d))

# mutation drill: remove the bare-command refusal -> the defect gate MUST go red
orig = mod.signature_tokens
mod.signature_tokens = lambda command, args: [command.lower()] if not args else orig(command, args)
mutant_caught = not playwright_defect_refused(mod)
mod.signature_tokens = orig
gate("V-CENSUS-MUTATION-DRILL-GOES-RED", mutant_caught, "mutant matcher was not detected")
gate("V-CENSUS-MUTATION-RESTORED", playwright_defect_refused(mod))

# live smoke: the real host
live = mod.take_snapshot()
gate("V-CENSUS-LIVE-SMOKE", live["process_count"] > 10 and live["host"].get("commit_total", 0) > 0
     and live["host"].get("commit_limit", 0) >= live["host"].get("commit_total", 0) and "identities" in live,
     str({k: live[k] for k in ("process_count", "claude_sessions")}))
cfgs = mod.collect_configs()
gate("V-CENSUS-LIVE-CONFIGS-READABLE", isinstance(cfgs, dict))

print("RESULT:", "FAIL " + ",".join(fails) if fails else "ALL PASS")
sys.exit(1 if fails else 0)
