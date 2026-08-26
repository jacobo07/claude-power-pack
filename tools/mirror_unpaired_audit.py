#!/usr/bin/env python3
"""Classify the files the mirror comparator cannot speak about.

verify_global_mirrors compares 28 pairs and reports "345 file(s) present on
one side only" as a single number. A count is not a disposition. Parity
therefore speaks for 7.5% of the surface, and the other 92.5% has been
reported in a way that reads as accounted-for.

That gap is not hypothetical. This session found `research-intent-detector`
edited canonically and never running, because hook-dispatcher registers it
as './research-intent-detector.js' -- a RELATIVE path resolving against the
dispatcher's own directory. Whether that lands in the repo or in the live
tree depends on which dispatcher copy Claude Code actually executes. One
character of path decided whether an edit reached production, and nothing
in the estate could have told me which way it went.

WHAT THIS CLASSIFIES, AND WHAT IT REFUSES TO. Hooks are decided from
evidence: registration in settings.json and in whichever hook-dispatcher
copy is the live one, with relative references resolved against the
dispatcher that owns them. Commands, agents and vault documents are
reported as UNCLASSIFIED, because proving a command is reachable means
proving how Claude Code discovers it, and this tool has no evidence for
that. Unknown is printed as unknown. It never silently reads as fine.

    REPO_ONLY  + registered by a repo path -> LIVE_FROM_REPO   (correct)
    REPO_ONLY  + registered by a live path -> BROKEN_REGISTRATION
    REPO_ONLY  + unregistered              -> CANONICAL_DORMANT
    LIVE_ONLY  + registered                -> UNVERSIONED_LIVE
    LIVE_ONLY  + unregistered              -> LIVE_DORMANT

BROKEN_REGISTRATION is the only class that fails this audit: something is
registered at a path where no file exists, so it is wired and dead.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
if str(PP) not in sys.path:
    sys.path.insert(0, str(PP))

from modules.mirror_discovery.discovery import (  # noqa: E402
    discover, resolve_live_root,
)

LIVE_FROM_REPO = "LIVE_FROM_REPO"
BROKEN_REGISTRATION = "BROKEN_REGISTRATION"
CANONICAL_DORMANT = "CANONICAL_DORMANT"
UNVERSIONED_LIVE = "UNVERSIONED_LIVE"
LIVE_DORMANT = "LIVE_DORMANT"
UNCLASSIFIED = "UNCLASSIFIED"

# Only this domain has machine-checkable registration.
DECIDABLE = "hooks"


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


def _norm(s: str) -> str:
    return s.replace("\\", "/").lower()


def live_dispatcher(live_root: Path, settings_text: str) -> Path | None:
    """Which hook-dispatcher copy does Claude Code actually execute?

    Decided from settings.json, never assumed: the answer determines how
    every relative './x.js' registration resolves, and both copies exist.
    """
    live_disp = live_root / "hooks" / "hook-dispatcher.js"
    repo_disp = PP / "hooks" / "hook-dispatcher.js"
    st = _norm(settings_text)
    if _norm(str(repo_disp)) in st:
        return repo_disp
    if _norm(str(live_disp)) in st:
        return live_disp
    # Fall back to the path shape rather than a guess about the filesystem.
    if "skills/claude-power-pack/hooks/hook-dispatcher.js" in st:
        return repo_disp
    if ".claude/hooks/hook-dispatcher.js" in st:
        return live_disp
    return None


def dispatcher_targets(disp: Path | None) -> dict:
    """basename -> resolved absolute path, for every script the dispatcher
    registers. Relative refs resolve against the DISPATCHER's directory,
    which is the whole point."""
    out: dict = {}
    if disp is None or not disp.is_file():
        return out
    text = _read(disp)
    for m in re.finditer(r"""['"]([^'"]*?[\w./\\-]+\.js)['"]""", text):
        ref = m.group(1)
        if not ref.strip():
            continue
        base = Path(ref).name
        try:
            resolved = (disp.parent / ref).resolve() if not \
                Path(ref).is_absolute() else Path(ref)
        except (OSError, ValueError):
            continue
        out.setdefault(base, resolved)
    return out


def classify_hook(rel: str, side: str, settings_text: str,
                  targets: dict, live_root: Path,
                  repo_root: Path | None = None) -> tuple[str, str]:
    """(status, evidence) for one unpaired hook file.

    repo_root is a PARAMETER, not the literal installed path. The first
    version matched the string "skills/claude-power-pack/hooks", which is
    true of the installed tree and false of every worktree, clone and CI
    checkout -- so the tool silently reported LIVE_FROM_REPO hooks as
    CANONICAL_DORMANT anywhere but one directory. An audit that only tells
    the truth from its home address is not an audit. Caught by its own
    gate, which runs from a worktree.
    """
    repo_root = Path(repo_root) if repo_root is not None else PP
    base = Path(rel).name
    st = _norm(settings_text)
    repo_hooks = _norm(str(repo_root / "hooks"))
    registered_repo = f"{repo_hooks}/{_norm(base)}" in st
    # A live-tree registration is a .claude/hooks reference that is NOT the
    # repo path -- when the repo lives under ~/.claude (the installed
    # case), the substring check would otherwise match both.
    registered_live = (f"{_norm(str(live_root / 'hooks'))}/{_norm(base)}"
                       in st and not registered_repo)

    target = targets.get(base)
    via = ""
    if target is not None:
        t = _norm(str(target))
        if repo_hooks in t:
            registered_repo = True
            via = " (via dispatcher, repo path)"
        elif _norm(str(live_root / "hooks")) in t:
            registered_live = True
            via = " (via dispatcher, live path)"

    if side == "repo":
        if registered_repo:
            return LIVE_FROM_REPO, f"settings/dispatcher -> repo copy{via}"
        if registered_live:
            return (BROKEN_REGISTRATION,
                    f"registered at {live_root}/hooks/{base}, which does "
                    f"not exist{via}")
        return CANONICAL_DORMANT, "no registration found"
    if registered_repo or registered_live:
        return UNVERSIONED_LIVE, f"registered, no repo copy{via}"
    return LIVE_DORMANT, "no registration found"


def audit(repo_root: Path, live_root: Path) -> dict:
    d = discover(repo_root, live_root)
    settings_text = _read(live_root / "settings.json")
    disp = live_dispatcher(live_root, settings_text)
    targets = dispatcher_targets(disp)

    rows = []
    for domain, rel in d.repo_only:
        if domain == DECIDABLE:
            status, why = classify_hook(rel, "repo", settings_text,
                                        targets, live_root, repo_root)
        else:
            status, why = UNCLASSIFIED, "reachability not machine-checkable"
        rows.append({"domain": domain, "rel": rel, "side": "repo",
                     "status": status, "evidence": why})
    for domain, rel in d.live_only:
        if domain == DECIDABLE:
            status, why = classify_hook(rel, "live", settings_text,
                                        targets, live_root, repo_root)
        else:
            status, why = UNCLASSIFIED, "reachability not machine-checkable"
        rows.append({"domain": domain, "rel": rel, "side": "live",
                     "status": status, "evidence": why})

    # Compare what each dispatcher copy registers. Basenames, because the
    # two copies legitimately spell the same target differently (one
    # relative, one absolute) -- the question is WHICH hooks are wired,
    # not how the string was written.
    repo_disp = PP / "hooks" / "hook-dispatcher.js"
    live_disp = live_root / "hooks" / "hook-dispatcher.js"
    repo_side = dispatcher_targets(repo_disp)
    live_side = dispatcher_targets(live_disp)

    return {
        "paired": len(d.pairs),
        "unpaired": d.unpaired_total,
        # Does settings.json register hooks from THIS checkout? When it
        # does not, every reachability verdict below is about a tree that
        # is not the one running, and saying so is the difference between
        # a report and a misreading.
        "checkout_is_registered":
            _norm(str(Path(repo_root) / "hooks")) in _norm(settings_text),
        "dispatcher": str(disp) if disp else None,
        "dispatcher_registers": len(targets),
        "divergence": {
            "repo_copy": str(repo_disp),
            "live_copy": str(live_disp),
            "repo_only": sorted(set(repo_side) - set(live_side)),
            "live_only": sorted(set(live_side) - set(repo_side)),
        },
        "rows": rows,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=str(PP))
    ap.add_argument("--live-root", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true",
                    help="counts and failures only")
    a = ap.parse_args(argv)

    live_root = resolve_live_root(
        Path(a.live_root) if a.live_root else None)
    res = audit(Path(a.repo_root), live_root)

    if a.json:
        print(json.dumps(res, indent=2))
        return 1 if any(r["status"] == BROKEN_REGISTRATION
                        for r in res["rows"]) else 0

    counts: dict = {}
    for r in res["rows"]:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    # "Is this hook live?" is a question about the INSTALLED tree. Run from
    # a worktree or a clone, the honest answer changes -- those hooks are
    # genuinely not the ones registered -- and 29 rows reading
    # CANONICAL_DORMANT would otherwise be mistaken for a finding about
    # production. Say which tree is being judged, every time.
    if not res["checkout_is_registered"]:
        print(f"NOTE: judging {a.repo_root}, which is NOT the checkout "
              f"registered in settings.json.")
        print("      Reachability verdicts below describe THIS checkout. "
              "For the production answer, run from the installed tree.")
        print()

    print(f"MIRROR_UNPAIRED: {res['paired']} paired, "
          f"{res['unpaired']} unpaired")
    print(f"  live dispatcher: {res['dispatcher']}")
    print(f"  it registers   : {res['dispatcher_registers']} script(s)")
    print()
    for status in (BROKEN_REGISTRATION, UNVERSIONED_LIVE, LIVE_FROM_REPO,
                   CANONICAL_DORMANT, LIVE_DORMANT, UNCLASSIFIED):
        n = counts.get(status, 0)
        if not n:
            continue
        print(f"  {status:22s} {n}")
        if a.quiet and status != BROKEN_REGISTRATION:
            continue
        if status == UNCLASSIFIED:
            doms: dict = {}
            for r in res["rows"]:
                if r["status"] == status:
                    doms[r["domain"]] = doms.get(r["domain"], 0) + 1
            for dom, c in sorted(doms.items()):
                print(f"      {dom}: {c} (UNKNOWN, not assumed fine)")
            continue
        for r in res["rows"]:
            if r["status"] == status:
                print(f"      {r['rel']:44s} {r['evidence']}")

    # The dispatcher itself is a PAIRED file, so the classification above
    # says nothing about it -- and it is the single point that decides
    # whether any hook edit reaches production. If the two copies register
    # different sets, the difference IS the set of hooks that are wired
    # canonically and do not run. That is how the research-intent-detector
    # skip was found, and finding it by luck once is not a mechanism.
    div = res["divergence"]
    if div["repo_only"] or div["live_only"]:
        print("\n  dispatcher divergence (canonical vs live):")
        for base in div["repo_only"]:
            print(f"      WIRED-CANONICAL-ONLY  {base}")
        for base in div["live_only"]:
            print(f"      WIRED-LIVE-ONLY       {base}")
        print("      -> the first list is registered in the repo copy and "
              "NOT in the copy that runs.")
        print("      -> Owner action: reconcile hook-dispatcher.js "
              "(this repo cannot write ~/.claude/hooks).")

    broken = [r for r in res["rows"]
              if r["status"] == BROKEN_REGISTRATION]
    if broken:
        print(f"\nMIRROR_UNPAIRED FAIL: {len(broken)} registration(s) point "
              f"at a file that does not exist -- wired and dead")
        return 1
    print("\nMIRROR_UNPAIRED OK: no registration points at a missing file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
