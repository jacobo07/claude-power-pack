"""Discover the system-family axis from repo file composition.

P3 of docs/superpowers/specs/2026-09-23-torre-universal-persistent-state-design.md:
the family catalogue must be DISCOVERED from a structural signal of the estate,
never curated by hand -- a curated list measures memory, not reality.

The first candidate signal (`task_class` on FD-07 deposits) was measured and
REJECTED: it carries a lesson-topic axis, not a family axis
(vault/audits/ucr_cif/13_FAMILY_SIGNAL_PROBE.md).

This is the second candidate: file composition. Structural by construction --
it does not depend on anyone having labelled anything.

Subjects and failure conditions were PREDECLARED before this file existed:
vault/audits/ucr_cif/14_P2_PREDECLARATION.md, commit 3b3ae85.

  exit 0  scan valid (whatever it found)
  exit 2  population floor failed -- the sweep may have stopped seeing repos
  exit 3  a predeclared subject was not visited -- result invalid, not negative

LIVENESS APERTURE: this lives under tools/, which
modules/liveness/reachability.py does NOT scan. Its silence about this file is
absence from the denominator, never health.
"""
from __future__ import annotations

import json
import os
import re
import sys

# Declared in 14_P2_PREDECLARATION.md §1, before this file was written.
MARKERS: dict[str, tuple[str, ...]] = {
    "migrations_dir": ("migrations", "priv/repo/migrations", "alembic"),
    "declared_schema": ("schema.prisma", "schema.sql"),
    "orm_dependency": ("prisma", "sqlalchemy", "ecto", "sqlite3", "better-sqlite3"),
    "durable_ledger": (".db", ".sqlite", ".sqlite3"),
}

# Files whose CONTENT is read for dependency names. Bounded on purpose: reading
# every file in 149 repos is a load generator, and a load generator is part of
# the system under test.
DEP_MANIFESTS = ("package.json", "mix.exs", "requirements.txt", "pyproject.toml")

SCAN_ROOTS = (
    r"C:\Users\User\Desktop\Cursor Projects",
    r"C:\Users\User\Apps",
    r"C:\Users\User\.claude\skills",
)

# FLOOR MOVED, ON THE RECORD -- 120 -> 35.
#
# 14_P2_PREDECLARATION.md declared a floor of 120 "repos". That floor was
# declared over the WRONG UNIT: it counted CHECKOUTS. Collapsing git worktrees
# to their main repository took the population from 164 checkouts to 42 distinct
# PROJECTS -- a 3.9x inflation, driven by TUA-X and InfinityOps worktrees.
#
# So the first run of the collapsed sweep exited 2 against its own floor. That is
# the predeclaration working, not failing: it refused to report a clean result on
# a population it did not recognise.
#
# The new floor is set over projects, AFTER 42 was measured. Moving a threshold
# after seeing the number is normally forbidden, and it is allowed here for one
# reason that has to be stated rather than assumed: the original threshold was
# not too strict, it was about a different quantity. 35 leaves ~17% shrinkage
# before the sweep fails, and the sweep still fails rather than reporting clean.
POPULATION_FLOOR = 35

PREDECLARED = {
    "InfinityOps": {
        "path": r"C:\Users\User\Desktop\Cursor Projects\InfinityOps",
        "expect": "IN",
    },
    "ABSW2-Wii": {
        "path": r"C:\Users\User\Desktop\Cursor Projects\Wii Projects\ABSW2-Wii",
        "expect": "OUT",
    },
}

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist",
             "build", ".next", "target", "_build", "deps", ".claude"}


def find_repos() -> list[str]:
    """Every git repo under the scan roots, one level deep plus one nested level.

    Two levels because the estate nests (Wii Projects/ABSW2-Wii), and the
    predeclared OUT subject lives at depth two. A one-level sweep would not
    visit it, which is exit 3, not a negative.
    """
    found: list[str] = []
    for root in SCAN_ROOTS:
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            d = os.path.join(root, name)
            if not os.path.isdir(d):
                continue
            if os.path.exists(os.path.join(d, ".git")):
                found.append(d)
                continue
            try:
                subs = sorted(os.listdir(d))
            except OSError:
                continue
            for sub in subs:
                s = os.path.join(d, sub)
                if os.path.isdir(s) and os.path.exists(os.path.join(s, ".git")):
                    found.append(s)

    # COLLAPSE WORKTREES TO THEIR MAIN REPO.
    # The first run reported 118 IN of 164, and the IN list was dominated by
    # TUA-X-acmf, TUA-X-bdci, TUA-X-brand001 ... and InfinityOps-gscfix,
    # -journal, -bis-capab: git WORKTREES of two projects, each counted as an
    # independent repo. One project with fifteen worktrees contributed fifteen
    # classifications, so the "distribution over the estate" was a distribution
    # over checkouts.
    #
    # repo_identity.canonical_repo does NOT fix this, and correctly so: it treats
    # a worktree's `.git` FILE as a valid VCS marker precisely so each worktree
    # keeps its own state (identity.py:46-49). That is right for per-repo state
    # and wrong for a population. The collapse has to read the worktree pointer.
    seen: dict[str, str] = {}
    for path in found:
        seen.setdefault(main_repo_of(path), path)
    return sorted(seen.values())


def main_repo_of(path: str) -> str:
    """The MAIN repository a checkout belongs to.

    A worktree's `.git` is a file containing `gitdir: <main>/.git/worktrees/<n>`.
    Resolve that back to the main working tree so N worktrees count once.
    """
    dotgit = os.path.join(path, ".git")
    if os.path.isdir(dotgit):
        return os.path.normpath(path)
    try:
        with open(dotgit, "r", encoding="utf-8", errors="replace") as fh:
            line = fh.read().strip()
    except OSError:
        return os.path.normpath(path)
    if not line.startswith("gitdir:"):
        return os.path.normpath(path)
    gitdir = line.split(":", 1)[1].strip()
    # A worktree created from Git Bash records its pointer in MSYS form,
    # `/c/Users/...`. Read verbatim on Windows that became `\c\Users\...`, a
    # directory that does not exist -- so TUA-X was counted twice, once as
    # itself and once as a phantom, and the phantom got its own capsule
    # (measured 2026-09-24, `tower_capsule.py --all`).
    m = re.match(r"^/([a-zA-Z])/(.*)$", gitdir)
    if m and os.name == "nt":
        gitdir = m.group(1).upper() + ":\\" + m.group(2)
    marker = os.sep + "worktrees" + os.sep
    idx = gitdir.replace("/", os.sep).find(marker)
    if idx == -1:
        return os.path.normpath(path)
    main_git = gitdir.replace("/", os.sep)[:idx]      # <main>/.git
    return os.path.normpath(os.path.dirname(main_git))


def scan_repo(path: str, max_entries: int = 4000) -> dict:
    """Structural markers for one repo. Bounded walk: a repo is characterised by
    its shape near the top, and an unbounded walk over 149 repos is the
    instrument consuming the host it measures."""
    hits: dict[str, list[str]] = {k: [] for k in MARKERS}
    seen = 0
    deps_text: list[str] = []

    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            seen += 1
            if seen > max_entries:
                break
            low = fn.lower()
            # A real repo in this estate holds a file literally named `nul`,
            # which Windows resolves to the reserved device \\.\nul, and
            # os.path.relpath then raises ValueError because the mount differs.
            # A sweep of real trees meets real filesystem debris: skipping the
            # entry is correct, taking the whole sweep down with it is not.
            try:
                rel = os.path.relpath(os.path.join(dirpath, fn), path)
            except ValueError:
                continue
            if low in ("schema.prisma", "schema.sql"):
                hits["declared_schema"].append(rel)
            if any(low.endswith(ext) for ext in MARKERS["durable_ledger"]):
                hits["durable_ledger"].append(rel)
            if fn in DEP_MANIFESTS:
                try:
                    with open(os.path.join(dirpath, fn), "r",
                              encoding="utf-8", errors="replace") as fh:
                        deps_text.append(fh.read()[:20000])
                except OSError:
                    pass
        # directory-shaped markers
        reldir = os.path.relpath(dirpath, path).replace("\\", "/")
        for d in dirnames:
            cand = (reldir + "/" + d).lstrip("./")
            for m in MARKERS["migrations_dir"]:
                if cand.endswith(m):
                    hits["migrations_dir"].append(cand)
        if seen > max_entries:
            break

    blob = "\n".join(deps_text).lower()
    # WORD BOUNDARIES, not substring. The first run of this scanner used a plain
    # `dep in blob` and reported orm_dependency on 129 of 163 repos -- because
    # "ecto" is a substring of vector, detector, selector, director, inspector,
    # all of which are ordinary package.json content. The two predeclared
    # subjects still landed correctly, which is exactly why the POPULATION
    # distribution had to be checked too: a predicate can be right about the
    # cases you chose and wrong about the class.
    for dep in MARKERS["orm_dependency"]:
        if re.search(r"(?<![a-z0-9_-])" + re.escape(dep) + r"(?![a-z0-9_])", blob):
            hits["orm_dependency"].append(dep)

    present = [k for k, v in hits.items() if v]
    return {"markers": hits, "present": present, "entries_seen": seen}


def main() -> int:
    repos = find_repos()
    print("FAMILY SIGNAL SCAN -- PERSISTENT_STATE")
    print("  repos visited      %d" % len(repos))
    print("  population floor   %d (predeclared)" % POPULATION_FLOOR)

    if len(repos) < POPULATION_FLOOR:
        print("  SWEEP FAILED: %d < %d. The sweep may have stopped seeing repos."
              % (len(repos), POPULATION_FLOOR))
        print("  Refusing to report a clean result.")
        return 2

    results: dict[str, dict] = {}
    for r in repos:
        results[r] = scan_repo(r)

    inside = {r: v for r, v in results.items() if v["present"]}
    outside = {r: v for r, v in results.items() if not v["present"]}

    print("  classified IN      %d" % len(inside))
    print("  classified OUT     %d" % len(outside))
    print()

    both = len(inside) > 0 and len(outside) > 0
    print("  BOTH POLES REACHED: %s" % both)
    if not both:
        print("    A classifier that answers one way passes every test of the other.")
    print()

    print("  marker frequency across the population:")
    for m in MARKERS:
        n = sum(1 for v in results.values() if v["markers"][m])
        print("    %-18s %4d repos" % (m, n))
    print()

    print("  PREDECLARED SUBJECTS (14_P2_PREDECLARATION.md, commit 3b3ae85):")
    verdict_ok = True
    missing = False
    for name, spec in PREDECLARED.items():
        p = os.path.normpath(spec["path"])
        match = next((r for r in results if os.path.normpath(r) == p), None)
        if match is None:
            print("    %-12s NOT VISITED -- result INVALID, not negative" % name)
            missing = True
            continue
        got = "IN" if results[match]["present"] else "OUT"
        ok = got == spec["expect"]
        verdict_ok = verdict_ok and ok
        print("    %-12s expected %-3s  got %-3s  %s   markers=%s"
              % (name, spec["expect"], got, "OK" if ok else "**MISMATCH**",
                 results[match]["present"] or "none"))

    if missing:
        return 3

    print()
    if not verdict_ok:
        print("  PREDECLARED EXPECTATION NOT MET.")
        print("  Per 14_P2_PREDECLARATION.md §3 the signal or the taxonomy is wrong.")
        print("  The threshold is NOT adjusted until the subject fits.")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "vault", "audits", "ucr_cif", "family_scan_result.json")
    payload = {
        "repos_visited": len(repos),
        "classified_in": len(inside),
        "classified_out": len(outside),
        "both_poles": both,
        "predeclared_met": verdict_ok,
        "in_repos": sorted(os.path.basename(r) for r in inside),
    }
    with open(os.path.normpath(out), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    print("  result written: vault/audits/ucr_cif/family_scan_result.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
