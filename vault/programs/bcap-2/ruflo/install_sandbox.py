"""Hardened, inert Ruflo install in an isolated sandbox dir (plan law 6). Reproducible: python3 install_sandbox.py <version> <sandbox_dir>
Order: registry integrity -> gate.install_plan_error (refuses on any violation) -> npm install --ignore-scripts with a scrubbed
environment -> tarball integrity re-check from the lockfile -> lifecycle scan of every installed manifest -> smoke with a network-blocking
preload. Nothing is started, no hook/daemon/config is written outside the sandbox."""
import json, os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from modules.ruflo_gate import gate as G

ver, sb = sys.argv[1], Path(sys.argv[2]).resolve()
sb.mkdir(parents=True, exist_ok=True)
inst = sb / "install"; inst.mkdir(exist_ok=True)
env = G.scrub_env(dict(os.environ), str(sb / "home")); Path(env["HOME"]).mkdir(exist_ok=True)
integ = subprocess.run(["npm", "view", f"ruflo@{ver}", "dist.integrity"], capture_output=True, text=True, env=env, cwd=inst, timeout=90).stdout.strip()
plan = dict(version=ver, integrity=integ, ignore_scripts=True, lockfile=True, sandbox_dir=str(sb), registry="https://registry.npmjs.org/",
            env=env, **{"global": False})
err = G.install_plan_error(plan, os.path.expanduser("~"))
print("plan gate:", err or "ACCEPTED", "| integrity", integ[:20] + "...")
if err:
    sys.exit(2)
(inst / "package.json").write_text(json.dumps({"name": "ruflo-sandbox", "private": True, "version": "0.0.0"}))
r = subprocess.run(["npm", "install", f"ruflo@{ver}", "--save-exact", "--ignore-scripts", "--no-audit", "--no-fund", "--registry=https://registry.npmjs.org/"],
                   capture_output=True, text=True, env=env, cwd=inst, timeout=500)
print("npm install rc", r.returncode, r.stderr.strip()[-300:])
if r.returncode:
    sys.exit(3)
lock = json.loads((inst / "package-lock.json").read_text())
got = lock["packages"].get(f"node_modules/ruflo", {}).get("integrity")
print("lock integrity matches registry:", got == integ)
if got != integ:
    sys.exit(4)
fl = []
for pj in (inst / "node_modules").rglob("package.json"):
    try:
        for f in G.lifecycle_findings(json.loads(pj.read_text())):
            fl.append((str(pj.relative_to(inst)), *f))
    except Exception:
        pass
print("lifecycle findings (NOT executed, ignore-scripts):", len(fl))
for x in fl[:15]:
    print("  ", x)
(sb / "lifecycle_findings.json").write_text(json.dumps(fl, indent=1))
(sb / "no_net.cjs").write_text("const n=require('net'),d=require('dns'),t=require('tls'),h=require('http'),s=require('https');"
    "const b=()=>{throw new Error('NET_BLOCKED_BY_SANDBOX')};n.Socket.prototype.connect=b;n.connect=b;d.lookup=b;t.connect=b;h.request=b;s.request=b;h.get=b;s.get=b;")
smoke = subprocess.run(["node", "--require", str(sb / "no_net.cjs"), "node_modules/ruflo/bin/ruflo.js", "--version"], capture_output=True, text=True,
                       env=env, cwd=inst, timeout=40)
print("smoke --version rc", smoke.returncode, "|", (smoke.stdout + smoke.stderr).strip()[:300])
