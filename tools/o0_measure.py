"""O0 -- the estate's baseline coverage BEFORE family baselines are injected.

Method PREDECLARED in vault/audits/ucr_cif/20_O0_METHOD_PREDECLARATION.md
(commit bf69726), probes in vault/tower/o0/probes.json, both committed before
this file existed. This tool applies them; it decides nothing.

    python tools/o0_measure.py            measure every family repo, write the O0 record
    python tools/o0_measure.py --dry      print, write nothing

The record carries the sha256 of probes.json: O1 is comparable to O0 only if
that hash is identical (method §5).

  exit 0  measured (whatever the verdicts)
  exit 2  probes do not cover B0 exactly once -- refuses to measure
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
for p in (_PP_ROOT, _HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

PROBES = os.path.join(_PP_ROOT, "vault", "tower", "o0", "probes.json")
OUT_DIR = os.path.join(_PP_ROOT, "vault", "tower", "o0")
FAMILIES = ("web_surface", "persistent_state", "kobiicraft_mode", "wii_homebrew")
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
             ".next", "target", "_build", "deps", ".claude", "vendor", "third_party"}
MAX_ENTRIES = 100_000
MAX_READ = 256 * 1024

MET, NOT_MET, NA, UNJUDGED = "MET", "NOT_MET", "NOT_APPLICABLE", "UNJUDGED"


def collect(repo: str, globs: list) -> tuple:
    """Files under repo whose basename matches any glob -> (paths, truncated)."""
    pats = [g.lower() for g in globs]
    out, seen = [], 0
    for dirpath, dirnames, filenames in os.walk(repo):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            seen += 1
            if seen > MAX_ENTRIES:
                return out, True
            if any(fnmatch.fnmatch(fn.lower(), g) for g in pats):
                out.append(os.path.join(dirpath, fn))
    return out, False


def _read(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read(MAX_READ)
    except OSError:
        return ""


def evaluate(repo: str, probe: dict, files_cache: dict | None = None) -> dict:
    """One probe against one repo -> {verdict, evidence}. Never raises."""
    try:
        mode = probe["mode"]
        if mode == "remote_visibility":
            return _remote_visibility(repo)
        key = tuple(probe["glob"])
        if files_cache is not None and key in files_cache:
            files, truncated = files_cache[key]
        else:
            files, truncated = collect(repo, probe["glob"])
            if files_cache is not None:
                files_cache[key] = (files, truncated)
        met = re.compile(probe["met"])
        applies = re.compile(probe["applies_if"]) if probe.get("applies_if") else None
        texts = {f: _read(f) for f in files}
        pool = [f for f in files if applies is None or applies.search(texts[f])]
        rel = lambda f: os.path.relpath(f, repo)                    # noqa: E731
        if mode == "no_file":
            hits = [f for f in files if met.search(texts[f])]
            if hits:
                return {"verdict": NOT_MET, "evidence": "%d file(s), e.g. %s"
                        % (len(hits), rel(hits[0]))}
            if truncated:
                return {"verdict": UNJUDGED, "evidence": "walk truncated"}
            return {"verdict": MET if files else NA,
                    "evidence": "%d file(s) scanned" % len(files)}
        if not pool:
            return {"verdict": UNJUDGED if truncated else NA,
                    "evidence": "walk truncated" if truncated else "no applicable file"}
        if mode == "any_file":
            hit = next((f for f in pool if met.search(texts[f])), None)
            if applies is not None and hit is None:
                # the requirement may be satisfied anywhere in the repo, not only
                # in the files that triggered it (e.g. one global reduced-motion rule)
                hit = next((f for f in files if met.search(texts[f])), None)
            return {"verdict": MET if hit else NOT_MET,
                    "evidence": rel(hit) if hit else "%d applicable, none met" % len(pool)}
        if mode == "every_applicable_file":
            bad = [f for f in pool if not met.search(texts[f])]
            return {"verdict": NOT_MET if bad else MET,
                    "evidence": ("%d/%d applicable fail, e.g. %s"
                                 % (len(bad), len(pool), rel(bad[0]))) if bad
                    else "%d/%d applicable met" % (len(pool), len(pool))}
        return {"verdict": UNJUDGED, "evidence": "unknown mode %r" % mode}
    except Exception as exc:  # noqa: BLE001 -- one probe must not sink the run
        return {"verdict": UNJUDGED, "evidence": "probe failed: %s" % type(exc).__name__}


def _remote_visibility(repo: str) -> dict:
    # gh shells out to git, and git is not on this host's non-interactive PATH
    # (measured: 13/13 UNJUDGED "unable to find git executable in PATH" on the
    # first O0 run -- an environment failure, not a fact about any repo).
    env = dict(os.environ)
    git_dir = r"C:\Program Files\Git\cmd"
    if os.path.isdir(git_dir) and git_dir.lower() not in env.get("PATH", "").lower():
        env["PATH"] = git_dir + os.pathsep + env.get("PATH", "")
    try:
        res = subprocess.run(["gh", "repo", "view", "--json", "visibility"], cwd=repo,
                             capture_output=True, text=True, timeout=30, env=env)
    except Exception as exc:  # noqa: BLE001
        return {"verdict": UNJUDGED, "evidence": "gh unavailable: %s" % type(exc).__name__}
    if res.returncode != 0:
        return {"verdict": UNJUDGED,
                "evidence": "gh could not answer: %s" % (res.stderr.strip().splitlines() or ["?"])[0][:80]}
    vis = (json.loads(res.stdout or "{}").get("visibility") or "").upper()
    if vis in ("PRIVATE", "INTERNAL"):
        return {"verdict": MET, "evidence": vis}
    if vis == "PUBLIC":
        return {"verdict": NOT_MET, "evidence": vis}
    return {"verdict": UNJUDGED, "evidence": "visibility=%r" % vis}


def load_probes() -> tuple:
    with open(PROBES, "rb") as fh:
        raw = fh.read()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()


def coverage_check(spec: dict) -> list:
    """B0 ids not covered exactly once by probes + unjudged_class."""
    from modules.tower import baselines as bl
    ids = [e["id"] for f in FAMILIES for e in bl.active_entries(f)]
    probed = [p["entry"] for p in spec["probes"]]
    listed = probed + list(spec["unjudged_class"])
    return sorted({i for i in ids if listed.count(i) != 1}
                  | {i for i in listed if i not in ids})


def main(argv: list) -> int:
    from modules.tower import families as fm
    from family_scan import find_repos, main_repo_of
    spec, sha = load_probes()
    bad = coverage_check(spec)
    if bad:
        print("REFUSED: probes do not cover B0 exactly once: %s" % bad)
        return 2
    fams = fm.load_families()
    repos = sorted({main_repo_of(r) for r in find_repos()})
    record = {"probes_sha256": sha, "measured_at": time.time(), "repos": {},
              "excluded": {}}
    for repo in repos:
        rep = fm.repo_family_report(repo, fams)
        for fid in rep["unjudged"]:
            record["excluded"].setdefault(os.path.basename(repo), []).append(fid)
        for fid in rep["in"]:
            cache: dict = {}
            verdicts = {}
            for probe in spec["probes"]:
                if probe["entry"].startswith(fid + "-"):
                    verdicts[probe["entry"]] = evaluate(repo, probe, cache)
            for eid, cls in spec["unjudged_class"].items():
                if eid.startswith(fid + "-"):
                    verdicts[eid] = {"verdict": UNJUDGED, "evidence": cls}
            vals = [v["verdict"] for v in verdicts.values()]
            met, nmet = vals.count(MET), vals.count(NOT_MET)
            record["repos"].setdefault(repo, {})[fid] = {
                "coverage": round(met / (met + nmet), 3) if met + nmet else None,
                "met": met, "not_met": nmet, "not_applicable": vals.count(NA),
                "unjudged": vals.count(UNJUDGED), "verdicts": verdicts}
            print("  %-30s %-17s cov=%-5s met=%d not_met=%d na=%d unjudged=%d"
                  % (os.path.basename(repo)[:30], fid,
                     record["repos"][repo][fid]["coverage"], met, nmet,
                     vals.count(NA), vals.count(UNJUDGED)))
    best = {}
    for repo, fams_ in record["repos"].items():
        for fid, r in fams_.items():
            if r["coverage"] is not None and r["coverage"] > best.get(fid, (-1, ""))[0]:
                best[fid] = (r["coverage"], os.path.basename(repo))
    record["best_demonstrated"] = {k: {"coverage": v[0], "repo": v[1]} for k, v in best.items()}
    print("best demonstrated:", record["best_demonstrated"])
    print("excluded (family UNJUDGED):", record["excluded"] or "none")
    if "--dry" not in argv:
        out = os.path.join(OUT_DIR, "O0_%s.json" % time.strftime("%Y-%m-%d"))
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(record, fh, indent=1, ensure_ascii=False)
        print("written", out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
