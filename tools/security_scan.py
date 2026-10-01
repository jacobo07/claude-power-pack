"""Security scan of the user's change: SAST on changed lines + dependency CVEs (Gap 4 v1).

Spec: vault/specs/security-scan.md.

    python tools/security_scan.py --repo <project> [--base HEAD] [--json]

    SAST  semgrep (registry rules, metrics off) on the changed source files; a finding is
          reported only when it touches a line changed since --base. Others are counted
          `pre_existing`, never silently dropped.
    SCA   osv-scanner over every lockfile in the project. A vulnerable package is `introduced`
          when its lockfile is part of the change.

Each scanner ends CLEAN, FINDINGS or UNCHECKED(reason) -- UNCHECKED is never read as clean.
Exit 0 = measured (findings or not), 2 = nothing could be checked or the project moved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCAN_TIMEOUT_S = 300
OSV_DEFAULT = Path(r"C:\Users\User\Apps\osv-scanner\osv-scanner.exe")
SEMGREP_DEFAULT = Path(r"C:\Users\User\Apps\semgrep-venv\Scripts\semgrep.exe")
SEMGREP_CONFIG = "p/default"
SOURCE_EXT = {".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".go", ".java", ".rb", ".php",
              ".cs", ".rs", ".kt", ".scala", ".c", ".cc", ".cpp", ".h", ".sh", ".yaml", ".yml"}
LOCKFILES = {"requirements.txt", "poetry.lock", "Pipfile.lock", "uv.lock", "pdm.lock",
             "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "go.mod", "Cargo.lock",
             "Gemfile.lock", "composer.lock", "pom.xml", "gradle.lockfile", "packages.lock.json"}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "env", "__pycache__", "dist", "build",
             ".tox", "vendor", "target"}
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def _git() -> str:
    found = shutil.which("git")
    if found:
        return found
    win = Path(r"C:\Program Files\Git\cmd\git.exe")
    return str(win) if win.is_file() else "git"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def changed(repo: Path, base: str) -> dict[str, set[int]]:
    """{posix relpath: changed lines}, tracked diff vs base plus untracked files (all lines)."""
    git = _git()
    out = subprocess.run([git, "-C", str(repo), "diff", "-U0", "--no-color", "--no-ext-diff", base],
                         capture_output=True, text=True, encoding="utf-8", errors="replace",
                         check=True).stdout
    res: dict[str, set[int]] = {}
    cur = None
    for line in out.splitlines():
        if line.startswith("+++ "):
            t = line[4:].strip()
            cur = None if t == "/dev/null" else (t[2:] if t.startswith("b/") else t)
            if cur:
                res.setdefault(cur, set())
            continue
        m = HUNK.match(line)
        if m and cur:
            start, count = int(m.group(1)), int(m.group(2) or 1)
            res[cur].update(range(start, start + count))
    untracked = subprocess.run([git, "-C", str(repo), "ls-files", "--others", "--exclude-standard"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace",
                               check=True).stdout
    for rel in filter(None, (r.strip() for r in untracked.splitlines())):
        p = repo / rel
        try:
            n = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
        except OSError:
            continue
        res[rel] = set(range(1, n + 1))
    return {k: v for k, v in res.items() if (repo / k).is_file()}


def _run(cmd: list[str], cwd: Path, timeout: float):
    """(returncode | None, stdout, reason-if-not-run)."""
    try:
        p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout,
                           env=dict(os.environ, PYTHONIOENCODING="utf-8", SEMGREP_SEND_METRICS="off"))
    except FileNotFoundError:
        return None, "", f"binary not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return None, "", f"timed out after {timeout:.0f}s"
    return p.returncode, p.stdout, (p.stderr or "").strip()[-300:]


def sast(repo: Path, chg: dict[str, set[int]], semgrep: Path, timeout: float) -> dict:
    targets = sorted(k for k in chg if Path(k).suffix.lower() in SOURCE_EXT and chg[k])
    out: dict = {"scanner": "semgrep", "config": SEMGREP_CONFIG, "files": len(targets),
                 "findings": [], "pre_existing": 0}
    if not targets:
        out["outcome"] = "CLEAN"
        out["reason"] = "no changed source files"
        return out
    code, stdout, err = _run([str(semgrep), "scan", "--config", SEMGREP_CONFIG, "--json",
                              "--metrics=off", "--disable-version-check", "--quiet", *targets],
                             repo, timeout)
    if code is None:
        out["outcome"], out["reason"] = "UNCHECKED", err
        return out
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        out["outcome"] = "UNCHECKED"
        out["reason"] = f"semgrep exit {code}, output not JSON: {err}"
        return out
    errors = data.get("errors") or []
    # A rules-fetch or config failure leaves `results` empty and puts the cause in `errors`;
    # reading that as CLEAN would report "no flaws" for a scan that never ran.
    if code not in (0, 1) or (not data.get("results") and any(
            e.get("level") == "error" for e in errors)):
        out["outcome"] = "UNCHECKED"
        out["reason"] = f"semgrep exit {code}: " + "; ".join(
            str(e.get("message") or e.get("type"))[:160] for e in errors[:3])
        return out
    for r in data.get("results") or []:
        rel = Path(r["path"]).as_posix()
        lines = set(range(r["start"]["line"], r["end"]["line"] + 1))
        if lines & chg.get(rel, set()):
            out["findings"].append({"file": rel, "line": r["start"]["line"],
                                    "rule": r["check_id"],
                                    "severity": r.get("extra", {}).get("severity", "?"),
                                    "message": " ".join(str(r.get("extra", {}).get("message", "")).split())[:240]})
        else:
            out["pre_existing"] += 1
    out["scan_errors"] = len(errors)
    out["outcome"] = "FINDINGS" if out["findings"] else "CLEAN"
    return out


def lockfiles(repo: Path) -> list[str]:
    found = []
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f in LOCKFILES:
                found.append(Path(root, f).relative_to(repo).as_posix())
    return sorted(found)


def sca(repo: Path, chg: dict[str, set[int]], osv: Path, timeout: float) -> dict:
    locks = lockfiles(repo)
    out: dict = {"scanner": "osv-scanner", "lockfiles": locks, "findings": []}
    if not locks:
        out["outcome"], out["reason"] = "CLEAN", "no lockfiles in the project"
        return out
    args = [str(osv), "scan", "source", "--format", "json"]
    for lf in locks:
        args += ["--lockfile", lf]
    code, stdout, err = _run(args, repo, timeout)
    if code is None:
        out["outcome"], out["reason"] = "UNCHECKED", err
        return out
    # osv-scanner: 0 = no vulnerabilities, 1 = vulnerabilities found, anything else = it failed.
    if code not in (0, 1):
        out["outcome"], out["reason"] = "UNCHECKED", f"osv-scanner exit {code}: {err}"
        return out
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        out["outcome"], out["reason"] = "UNCHECKED", f"osv-scanner exit {code}, output not JSON"
        return out
    seen = set()
    for res in data.get("results") or []:
        src = Path(res.get("source", {}).get("path", ""))
        try:
            rel = src.resolve().relative_to(repo.resolve()).as_posix()
        except ValueError:
            rel = src.as_posix()
        for pkg in res.get("packages") or []:
            ids = sorted(v["id"] for v in pkg.get("vulnerabilities") or [])
            if not ids:
                continue
            p = pkg["package"]
            # osv-scanner can list one requirement twice (`5.3` and `5.3.0`) with the same
            # advisories; one row per (lockfile, package, advisory set).
            key = (rel, p.get("ecosystem"), p["name"].lower(), tuple(ids))
            if key in seen:
                continue
            seen.add(key)
            out["findings"].append({"lockfile": rel, "ecosystem": p.get("ecosystem"),
                                    "package": p["name"], "version": p.get("version"),
                                    "advisories": ids, "introduced": rel in chg})
    if code == 1 and not out["findings"]:
        out["outcome"], out["reason"] = "UNCHECKED", "osv-scanner exit 1 but no findings parsed"
        return out
    out["outcome"] = "FINDINGS" if out["findings"] else "CLEAN"
    return out


def scan(repo: Path, base: str = "HEAD", osv: Path = OSV_DEFAULT,
         semgrep: Path = SEMGREP_DEFAULT, timeout: float = SCAN_TIMEOUT_S) -> dict:
    repo = repo.resolve()
    chg = changed(repo, base)
    before = {k: _sha(repo / k) for k in chg}
    res = {"repo": str(repo), "base": base, "changed_files": len(chg),
           "sast": sast(repo, chg, semgrep, timeout), "sca": sca(repo, chg, osv, timeout)}
    moved = [k for k, h in before.items() if not (repo / k).is_file() or _sha(repo / k) != h]
    if moved:
        res["verdict"], res["reason"] = "UNMEASURABLE", f"project files changed during the scan: {moved}"
    elif res["sast"]["outcome"] == "UNCHECKED" and res["sca"]["outcome"] == "UNCHECKED":
        res["verdict"], res["reason"] = "UNMEASURABLE", "no scanner could run"
    else:
        res["verdict"] = "MEASURED"
    return res


def render(res: dict) -> str:
    out = [f"SECURITY_SCAN repo={res['repo']} base={res['base']} changed files={res['changed_files']}",
           f"  verdict={res['verdict']}  {res.get('reason', '')}".rstrip()]
    s, d = res["sast"], res["sca"]
    out.append(f"  SAST {s['outcome']}  ({s['scanner']} {s['config']}, {s['files']} changed source "
               f"files, {s.get('pre_existing', 0)} pre-existing findings on unchanged lines)"
               + (f"  reason: {s['reason']}" if s.get("reason") else ""))
    for f in s["findings"]:
        out.append(f"    {f['severity']:<8} {f['file']}:{f['line']}  {f['rule']}\n             {f['message']}")
    out.append(f"  SCA  {d['outcome']}  ({d['scanner']}, {len(d['lockfiles'])} lockfile(s))"
               + (f"  reason: {d['reason']}" if d.get("reason") else ""))
    for f in d["findings"]:
        tag = "INTRODUCED" if f["introduced"] else "existing  "
        out.append(f"    {tag} {f['ecosystem']} {f['package']} {f['version']} ({f['lockfile']}): "
                   f"{', '.join(f['advisories'])}")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="SAST on changed lines + dependency CVEs")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--base", default="HEAD")
    ap.add_argument("--osv", default=str(OSV_DEFAULT))
    ap.add_argument("--semgrep", default=str(SEMGREP_DEFAULT))
    ap.add_argument("--timeout", type=float, default=SCAN_TIMEOUT_S)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        res = scan(Path(a.repo), a.base, Path(a.osv), Path(a.semgrep), a.timeout)
    except subprocess.CalledProcessError as exc:
        res = {"repo": a.repo, "base": a.base, "verdict": "UNMEASURABLE",
               "reason": f"git failed (exit {exc.returncode}); is --repo a git repository?"}
        print(json.dumps(res, indent=1) if a.json else f"SECURITY_SCAN verdict=UNMEASURABLE  {res['reason']}")
        return 2
    print(json.dumps(res, indent=1) if a.json else render(res))
    return 0 if res["verdict"] == "MEASURED" else 2


if __name__ == "__main__":
    sys.exit(main())
