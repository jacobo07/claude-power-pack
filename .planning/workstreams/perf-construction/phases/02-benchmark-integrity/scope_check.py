"""scope_check.py - phase-local fixture: fail when git status lists a path outside the allowed set.

Usage: python3 -I scope_check.py --allow PREFIX [--allow PREFIX ...]
Exit 0 when every changed or untracked path equals an allowed path or sits under an allowed
prefix (or is one of the known harness markers), exit 1 otherwise, exit 2 on a git error.
Stdlib only, read-only, registered nowhere. It exists so verify commands stay single, simple
commands (the isolated-worktree guard refuses compound shell lines).
"""
import argparse
import subprocess
import sys

MARKERS = {".planning/active-workstream", ".pp-capabilities"}
ALWAYS_PREFIXES = ("_audit_cache/",)


def changed_paths():
    r = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("scope_check: git status failed: " + r.stderr.strip(), file=sys.stderr)
        sys.exit(2)
    out = []
    for line in r.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        out.append(path.strip().strip('"'))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow", action="append", default=[], required=True)
    args = ap.parse_args()
    bad = []
    for p in changed_paths():
        if p in MARKERS or p.startswith(ALWAYS_PREFIXES):
            continue
        # a file is allowed by exact name; only an entry ending in "/" acts as a directory prefix,
        # so "tools/bench_all.py" cannot also admit "tools/bench_all.py.bak"
        if any(p == a or (a.endswith("/") and p.startswith(a)) for a in args.allow):
            continue
        bad.append(p)
    for p in bad:
        print("SCOPE_VIOLATION: " + p)
    print("SCOPE_CHECK violations=%d" % len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
