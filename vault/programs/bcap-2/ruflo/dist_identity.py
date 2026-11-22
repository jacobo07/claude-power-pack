#!/usr/bin/env python3
"""BCAP-2B Phase 7: structural identity of the published @claude-flow/cli tarball versus the source checkout.
Read-only, offline, runs no package code. usage: dist_identity.py <src_pkg_dir> <installed_pkg_dir>
A byte-identical dist/ cannot be proven (dist is not in git; rebuilding would execute upstream build scripts), so this measures what can be:
shipped non-dist files vs source, package.json drift, and dist/*.js coverage of src/*.ts."""
import hashlib, json, os, sys

def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()

def files(root, sub):
    out = {}
    base = os.path.join(root, sub)
    for d, _, fs in os.walk(base):
        for f in fs:
            p = os.path.join(d, f)
            out[os.path.relpath(p, root).replace(os.sep, "/")] = p  # POSIX keys on every OS (Windows gave bin\c.js)
    return out

def measure(src, inst):
    res = {"shipped_vs_source": {}}
    for sub in ("bin", "scripts", "templates", "assets", "plugins"):
        a, b = files(src, sub), files(inst, sub)
        common = set(a) & set(b)
        res["shipped_vs_source"][sub] = {
            "identical": sum(1 for k in common if sha(a[k]) == sha(b[k])),
            "differ": sorted(k for k in common if sha(a[k]) != sha(b[k])),
            "source_only": len(set(a) - set(b)),
            "shipped_only": sorted(set(b) - set(a)),
        }
    ps, pi = (json.load(open(os.path.join(r, "package.json"))) for r in (src, inst))
    drift = {}
    for sec in ("dependencies", "optionalDependencies", "peerDependencies"):
        for k in set(ps.get(sec, {})) | set(pi.get(sec, {})):
            if ps.get(sec, {}).get(k) != pi.get(sec, {}).get(k):
                drift[f"{sec}:{k}"] = [ps.get(sec, {}).get(k), pi.get(sec, {}).get(k)]
    res["package_json"] = {"version": [ps.get("version"), pi.get("version")], "dep_drift": drift}
    ts = {os.path.splitext(os.path.relpath(p, os.path.join(src, "src")))[0]
          for p in files(src, "src").values()
          if p.endswith(".ts") and not p.endswith(".d.ts") and "__tests__" not in p and ".test." not in p}
    js = {os.path.splitext(os.path.relpath(p, os.path.join(inst, "dist")))[0]
          for p in files(inst, "dist").values() if p.endswith(".js")}
    # dist/src is the tsc outDir layout when rootDir is the package
    js |= {j[4:] for j in js if j.startswith("src/")}
    res["dist_coverage"] = {"src_ts": len(ts), "dist_js": len(js), "src_without_js": sorted(ts - js)[:20],
                            "src_without_js_count": len(ts - js), "dist_js_without_src_count": len(js - ts)}
    res["verdict"] = ("DIST_BYTES_UNPROVEN: dist not in git; source/tarball diverge" if drift or any(
        v["differ"] for v in res["shipped_vs_source"].values()) else "STRUCTURALLY_CONSISTENT_BYTES_UNPROVEN")
    return res

if __name__ == "__main__":
    print(json.dumps(measure(sys.argv[1], sys.argv[2]), indent=1, sort_keys=True))
