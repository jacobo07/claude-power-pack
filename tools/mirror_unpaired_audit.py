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
import subprocess
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
    """Path comparison form: forward slashes, collapsed, lowercased.

    The collapse is load-bearing, not tidiness. settings.json holds
    JSON-ESCAPED Windows paths, so `C:\\\\Users\\\\User\\\\.claude\\\\hooks\\\\x.js`
    read as raw text becomes `c://users//user//.claude//hooks//x.js` once
    backslashes are swapped -- doubled separators that never match a probe
    built from a real Path. Every registration spelled with backslashes
    therefore read as UNREGISTERED, and the one class that fails this
    audit, BROKEN_REGISTRATION, could not fire. It survived only because
    the current settings.json happens to use forward slashes; an audit
    that depends on a spelling is not an audit.
    """
    return re.sub(r"/{2,}", "/", s.replace("\\", "/")).lower()


def live_dispatcher(live_root: Path, settings_text: str,
                    repo_root: Path | None = None) -> Path | None:
    """Which hook-dispatcher copy does Claude Code actually execute?

    Decided from settings.json, never assumed: the answer determines how
    every relative './x.js' registration resolves, and both copies exist.
    """
    live_disp = live_root / "hooks" / "hook-dispatcher.js"
    # repo_root, not PP. Half-applying the fix is how the same trap
    # survives in the same file: --repo-root X must decide about X.
    repo_disp = (Path(repo_root) if repo_root else PP) / "hooks" \
        / "hook-dispatcher.js"
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
    # Comment lines are not registrations. A retired entry left commented
    # out, or a log string naming a script, would otherwise be extracted
    # and report an unregistered hook as live -- the exact inverse of the
    # bug this tool was built to find.
    lines = [ln for ln in _read(disp).splitlines()
             if not re.match(r"\s*(?://|\*|/\*)", ln)]
    text = "\n".join(lines)
    # Registrations are PATH-shaped: `'./x.js'`, `'../a/b.js'`, or absolute.
    # Requiring the prefix rejects a bare `'ghost-hook.js'` mentioned in
    # prose and any quoted sentence that merely contains a filename.
    for m in re.finditer(
            r"""['"](\.{1,2}/[^'"\s]*?\.js|[A-Za-z]:[\\/][^'"\s]*?\.js)['"]""",
            text):
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


EFFECTIVE = "EFFECTIVE"
SHADOWED = "SHADOWED"
ABSENT_RUNNING = "ABSENT_RUNNING"
NOT_HERE = "NOT_HERE"
LOCAL_EDIT = "LOCAL_EDIT"

# A PP checkout path as settings.json spells it. Both separator styles and
# the JSON-escaped doubling are accepted, because this file holds all three
# on this host and a probe that knows one spelling is a probe that reports
# UNREGISTERED for the other two.
_CHECKOUT_RE = re.compile(
    r"([A-Za-z]:(?:\\\\|[\\/])(?:[^\"'\s]*?)claude-power-pack)"
    r"(?:\\\\|[\\/])", re.I)


def registered_repo_root(settings_text: str) -> Path | None:
    """Which PP checkout does settings.json actually execute from?

    None when zero appear (nothing registered) or when two distinct roots
    appear (ambiguous). Refusing to pick is the point: an arbitrary choice
    would make every verdict below describe a tree nobody runs, and it
    would do so silently.
    """
    seen: dict = {}
    for m in _CHECKOUT_RE.finditer(settings_text):
        raw = m.group(1).replace("\\\\", "\\")
        seen[_norm(raw)] = raw
    if len(seen) != 1:
        return None
    return Path(next(iter(seen.values())))


def registered_executables(settings_text: str, reg_root: Path,
                           targets: dict | None = None) -> dict:
    """rel-path -> absolute path, for every file settings.json (or the live
    dispatcher) will EXECUTE out of the registered checkout."""
    out: dict = {}
    norm_root = _norm(str(reg_root))
    for m in re.finditer(
            r"""([A-Za-z]:(?:\\\\|[\\/])[^\"'\s]*?\.(?:js|py|ps1|cjs|mjs))""",
            settings_text):
        raw = m.group(1).replace("\\\\", "\\")
        n = _norm(raw)
        if n.startswith(norm_root + "/"):
            out[n[len(norm_root) + 1:]] = Path(raw)
    for resolved in (targets or {}).values():
        n = _norm(str(resolved))
        if n.startswith(norm_root + "/"):
            out.setdefault(n[len(norm_root) + 1:], Path(resolved))
    return out


def _content(path: Path) -> bytes | None:
    """Bytes with line endings normalised.

    Raw bytes would report SHADOWED for a file whose only difference is
    CRLF, which this repo produces on every checkout. A gate that fires on
    line endings is noise, and noise is how a real red gets ignored.
    """
    try:
        return path.read_bytes().replace(b"\r\n", b"\n")
    except OSError:
        return None


def _head_blob(repo_root: Path, rel: str) -> bytes | None:
    """This checkout's COMMITTED bytes for one path, newline-normalised.

    Without it, SHADOWED conflates two opposite situations: a file this
    checkout has committed and the running tree lacks (delivery failure),
    and a file this checkout has merely edited in the working tree
    (nothing committed, nothing owed). Reporting both as one red is how a
    real red gets ignored.
    """
    git = os.environ.get("GIT_EXE") or "git"
    for exe in (git, r"C:\Program Files\Git\cmd\git.exe"):
        try:
            out = subprocess.run(
                [exe, "-C", str(repo_root), "show",
                 "HEAD:" + rel.replace("\\", "/")],
                capture_output=True, timeout=20)
        except (OSError, subprocess.SubprocessError):
            continue
        if out.returncode == 0:
            return out.stdout.replace(b"\r\n", b"\n")
        return None
    return None


def effective_state(repo_root: Path, settings_text: str,
                    targets: dict | None = None) -> dict:
    """Does the code THIS checkout holds reach the tree that executes?

    `mirror_unpaired_audit` already answers "is this hook registered, and
    is the file there" and classes the answer LIVE_FROM_REPO. It has never
    asked WHICH VERSION is there, because for a hook installed by mirroring
    the question does not arise -- the mirror comparator owns it. For the
    eleven registrations that execute straight out of the PP repo, the
    installed copy IS a git working tree, so the version that runs is
    whatever branch a pane last checked out, and no instrument in the
    estate could name it.

    Measured 2026-09-02: of 27 files carried by 45 commits on a pushed
    branch, 0 were identical to the running tree, 16 differed and 11 were
    absent. Two fixes sealed six days earlier were not the bytes executing,
    and the live corpus still carried rows produced by the unfixed code.

    `verify_global_mirrors` cannot see this by construction. It was
    rebuilt to read the committed blob on a named ref precisely so that a
    concurrent pane flipping branches could not produce false DRIFT -- a
    correct fix for a real false positive, which also removed the only
    aperture through which this true positive was visible.
    """
    reg_root = registered_repo_root(settings_text)
    if reg_root is None:
        return {"resolved": False, "registered_root": None, "rows": [],
                "counts": {}, "reason": "settings.json names zero or "
                                        "several PP checkouts"}

    rows = []
    for rel, running_path in sorted(
            registered_executables(settings_text, reg_root, targets).items()):
        here = _content(Path(repo_root) / rel)
        there = _content(running_path)
        if here is None:
            status = NOT_HERE
        elif there is None:
            status = ABSENT_RUNNING
        elif here == there:
            status = EFFECTIVE
        else:
            # Committed-here-and-not-running is a delivery failure. Merely
            # edited-here is not: if the running tree already holds this
            # checkout's COMMITTED bytes, the difference is uncommitted
            # local work and nothing is owed to production.
            status = (LOCAL_EDIT
                      if _head_blob(Path(repo_root), rel) == there
                      else SHADOWED)
        rows.append({"rel": rel, "status": status,
                     "running": str(running_path)})

    counts: dict = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return {"resolved": True, "registered_root": str(reg_root),
            "same_checkout": _norm(str(reg_root)) == _norm(str(repo_root)),
            "rows": rows, "counts": counts}


def audit(repo_root: Path, live_root: Path) -> dict:
    d = discover(repo_root, live_root)
    settings_text = _read(live_root / "settings.json")
    disp = live_dispatcher(live_root, settings_text, repo_root)
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
    repo_disp = Path(repo_root) / "hooks" / "hook-dispatcher.js"
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
            # Counts, so a gate can tell "no divergence" from "no inputs".
            # An empty comparison yields an empty diff, which reads as
            # agreement and is exactly the state in which a
            # wired-canonical-only hook is invisible.
            "repo_registers": len(repo_side),
            "live_registers": len(live_side),
            "repo_only": sorted(set(repo_side) - set(live_side)),
            "live_only": sorted(set(live_side) - set(repo_side)),
        },
        "rows": rows,
        "effective": effective_state(
            Path(repo_root), settings_text, targets),
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
        d = res["divergence"]
        return 1 if (any(r["status"] == BROKEN_REGISTRATION
                         for r in res["rows"])
                     or (d["repo_registers"]
                         and (not d["live_registers"]
                              or d["repo_only"] or d["live_only"]))) else 0

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

    eff = res["effective"]
    if not eff["resolved"]:
        print("\n  effective state: UNRESOLVED -- " + eff["reason"] + ".")
        print("      Not a pass. Nothing here claims these hooks are live.")
    else:
        c = eff["counts"]
        shadowed = [r for r in eff["rows"]
                    if r["status"] in (SHADOWED, ABSENT_RUNNING)]
        print("\n  effective state (" + str(len(eff["rows"]))
              + " registration(s) executing from "
              + eff["registered_root"] + "):")
        for status in (SHADOWED, ABSENT_RUNNING, LOCAL_EDIT,
                       EFFECTIVE, NOT_HERE):
            if c.get(status):
                print("      " + status.ljust(16) + str(c[status]))
        for r in shadowed[:12]:
            print("      -> " + r["status"] + "  " + r["rel"])

    broken = [r for r in res["rows"]
              if r["status"] == BROKEN_REGISTRATION]
    if broken:
        print(f"\nMIRROR_UNPAIRED FAIL: {len(broken)} registration(s) point "
              f"at a file that does not exist -- wired and dead")
        return 1
    # A divergence printed inside a passing audit is the shape that let a
    # producer fire 63 times into an empty sink for 80 days: reported, and
    # read by nobody. A hook wired canonically and absent from the copy that
    # RUNS is a live capability loss, so it fails. Guarded on both sides
    # having inputs -- an empty comparison yields an empty diff, which reads
    # as agreement and is exactly the state that hides the defect.
    # `live_registers == 0` is NOT agreement. If the live dispatcher is
    # missing, renamed, or stops parsing, every hook reads
    # WIRED-CANONICAL-ONLY and the old guard turned total capability loss
    # into exit 0 -- contradicted by this tool's own output twenty lines
    # above. Unmeasured is not measured-zero.
    if div["repo_registers"] and not div["live_registers"]:
        print("\nMIRROR_UNPAIRED FAIL: the live dispatcher registers NOTHING "
              f"while the canonical copy registers {div['repo_registers']}. "
              "Either it is absent, renamed, or no longer parses -- every "
              "hook it should route is dead. This is not agreement.")
        return 1
    if div["repo_registers"] and (
            div["repo_only"] or div["live_only"]):
        names = ", ".join(sorted(div["repo_only"]) + sorted(div["live_only"]))
        print(f"\nMIRROR_UNPAIRED FAIL: canonical and live dispatchers "
              f"register different sets ({names}). Edits to those hooks do "
              f"not reach production. Owner: copy hooks/hook-dispatcher.js "
              f"to ~/.claude/hooks/ (this repo cannot write there).")
        return 1
    if eff["resolved"] and (eff["counts"].get(SHADOWED)
                            or eff["counts"].get(ABSENT_RUNNING)):
        n = (eff["counts"].get(SHADOWED, 0)
             + eff["counts"].get(ABSENT_RUNNING, 0))
        print("\nMIRROR_UNPAIRED FAIL: " + str(n) + " registration(s) hold "
              "different bytes here than in the tree that executes ("
              + eff["registered_root"] + "). Work committed in THIS "
              "checkout does not run. Committed and pushed is not "
              "installed when the install location is a working tree.")
        return 1
    print("\nMIRROR_UNPAIRED OK: no registration points at a missing file, "
          "and the canonical dispatcher matches the one that runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
