#!/usr/bin/env python3
"""exact_push -- publish the SHA that was scanned, not whatever the ref points at now.

Root cause (2026-10-25): a scan of origin/B..B at tip f4db3d41 was followed by `git push origin B:B`,
which re-resolved the moving ref and published 0b4aa4ce unscanned. ovo-push-gate binds its verdict to
a 10-minute TTL, not to a subject; this tool binds the subject.

    exact_push.py scan --remote R --ref REF [--sha S] [--repo DIR] [--out FILE]
    exact_push.py push --receipt FILE [--sha S] [--repo DIR]

scan resolves S once (default: the local tip of REF), scans the added lines and paths of every commit in
base..S, and writes a sealed receipt. push re-verifies every binding and pushes `S:refs/heads/REF` without
force, then reads the remote back. Policy (Owner 2026-10-25): secrets only; the policy object is hashed
into the receipt, so changing it invalidates every earlier receipt. Exit 0 = PASS, 1 = REFUSE/BLOCK, 2 = usage.
Findings carry the commit, pattern name and severity -- never the matched value (HR-SECRET-002).
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from modules.secret_firewall.detector import PATTERNS, Severity, scan_text  # noqa: E402

GIT = os.environ.get("GIT_BIN") or (r"C:\Program Files\Git\cmd\git.exe" if os.name == "nt" else "git")
BLOCKED_PATHS = (".env", ".env.*", "*.pem", "*.key", "id_rsa", "id_rsa.*", "id_ed25519", "id_ed25519.*")


class Refuse(Exception):
    pass


def policy() -> dict:
    return {
        "name": "secrets-only",
        "block_severity": Severity.CRITICAL.name,
        "scanner": "modules.secret_firewall.detector.PATTERNS",
        "patterns": {n: [p.pattern, s.name] for n, (p, s) in sorted(PATTERNS.items())},
        "blocked_paths": list(BLOCKED_PATHS),
    }


def digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def git(repo: str, *args: str, check: bool = True) -> str:
    r = subprocess.run([GIT, "-C", repo, *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode:
        raise Refuse(f"git {args[0]} failed: {r.stderr.strip()[:200]}")
    return r.stdout.strip()


def remote_url(repo: str, remote: str) -> str:
    r = subprocess.run([GIT, "-C", repo, "remote", "get-url", remote], capture_output=True, text=True, encoding="utf-8")
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else remote


def remote_tip(repo: str, remote: str, ref: str) -> str | None:
    out = git(repo, "ls-remote", remote, f"refs/heads/{ref}")
    return out.split()[0] if out else None


def scan_range(repo: str, base: str | None, sha: str) -> dict:
    spec = f"{base}..{sha}" if base else sha
    log = git(repo, "log", "-m", "-U0", "--no-color", "--format=@@COMMIT %H", "-p", spec)
    findings: list[dict] = []
    added = 0
    commit = ""
    buf: list[str] = []

    def flush() -> None:
        if commit and buf:
            for h in scan_text("\n".join(buf)):
                findings.append({"commit": commit[:12], "pattern": h.pattern_name, "severity": h.severity.name})

    for line in log.splitlines():
        if line.startswith("@@COMMIT "):
            flush()
            commit, buf = line.split()[1], []
        elif line.startswith("+++ b/"):
            path = line[6:]
            if any(fnmatch.fnmatch(Path(path).name, pat) for pat in BLOCKED_PATHS):
                findings.append({"commit": commit[:12], "pattern": "blocked_path", "severity": "CRITICAL", "path": path})
        elif line.startswith("+") and not line.startswith("+++"):
            added += 1
            buf.append(line[1:])
    flush()
    blocked = [f for f in findings if f["severity"] == Severity.CRITICAL.name]
    findings.sort(key=lambda f: (f["commit"], f["pattern"], f.get("path", "")))
    return {"range": spec, "added_lines": added, "findings": findings,
            "result": "BLOCK" if blocked else "PASS"}


def cmd_scan(a) -> int:
    repo = a.repo
    sha = git(repo, "rev-parse", "--verify", f"{a.sha or 'refs/heads/' + a.ref}^{{commit}}")
    base = remote_tip(repo, a.remote, a.ref)
    if base and git(repo, "cat-file", "-t", base, check=False) != "commit":
        raise Refuse(f"remote tip {base[:12]} is not in this repository; fetch first, cannot scan an unknown base")
    body = scan_range(repo, base, sha)
    receipt = {"repo": str(Path(repo).resolve()), "remote": a.remote, "remote_url": remote_url(repo, a.remote),
               "ref": a.ref, "base_sha": base, "sha": sha, "policy": policy()["name"], "policy_hash": digest(policy()),
               "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **body}
    sealed = {"receipt": receipt, "sha256": digest(receipt)}
    if a.out:
        Path(a.out).write_text(json.dumps(sealed, indent=1), encoding="utf-8")
    print(f"{receipt['result']} {receipt['range']} added_lines={receipt['added_lines']} "
          f"findings={len(receipt['findings'])} sha256={sealed['sha256'][:12]}")
    for f in receipt["findings"]:
        print(f"  [REDACTED {f['pattern']} severity={f['severity']}] commit {f['commit']}")
    return 0 if receipt["result"] == "PASS" else 1


def cmd_push(a) -> int:
    repo = a.repo
    sealed = json.loads(Path(a.receipt).read_text(encoding="utf-8-sig"))
    r = sealed["receipt"]
    if digest(r) != sealed.get("sha256"):
        raise Refuse("receipt does not match its own sha256")
    if r["result"] != "PASS":
        raise Refuse(f"receipt result is {r['result']}")
    if r["policy_hash"] != digest(policy()):
        raise Refuse("policy changed since the scan")
    want = a.sha or git(repo, "rev-parse", "--verify", f"refs/heads/{r['ref']}^{{commit}}", check=False)
    if want != r["sha"]:
        raise Refuse(f"push subject {want[:12] or '(none)'} is not the scanned sha {r['sha'][:12]}")
    if remote_url(repo, r["remote"]) != r["remote_url"]:
        raise Refuse("remote URL differs from the receipt")
    if remote_tip(repo, r["remote"], r["ref"]) != r["base_sha"]:
        raise Refuse("remote ref moved since the scan")
    again = scan_range(repo, r["base_sha"], r["sha"])
    if (again["result"], again["added_lines"], again["findings"]) != (r["result"], r["added_lines"], r["findings"]):
        raise Refuse("rescan of the range disagrees with the receipt")
    git(repo, "push", r["remote"], f"{r['sha']}:refs/heads/{r['ref']}")
    got = remote_tip(repo, r["remote"], r["ref"])
    if got != r["sha"]:
        raise Refuse(f"read-back mismatch: remote is {str(got)[:12]}, expected {r['sha'][:12]}")
    print(f"PUSHED {r['ref']} == {r['sha'][:12]} (read back from {r['remote']})")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--remote", required=True)
    s.add_argument("--ref", required=True)
    s.add_argument("--sha")
    s.add_argument("--out")
    s.add_argument("--repo", default=".")
    q = sub.add_parser("push")
    q.add_argument("--receipt", required=True)
    q.add_argument("--sha")
    q.add_argument("--repo", default=".")
    a = p.parse_args(argv)
    try:
        return cmd_scan(a) if a.cmd == "scan" else cmd_push(a)
    except Refuse as e:
        print(f"REFUSE: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
