"""Plan Graph check for GSD phase plans (assimilation item 18, genesis-plan-graph -> CONNECT).

GSD executes the plans of one wave IN PARALLEL. Two plans of one wave that write the same file are
two writers in one tree, and the loser's hunks land under the winner's commit. Nothing checked the
`files_modified` a plan declares against its wave siblings before the wave ran.

This reads each phase's *-PLAN.md frontmatter (wave, depends_on, files_modified) and judges the
PENDING plans (a plan whose <id>-SUMMARY.md exists is done). The rules are the vendored ones,
reached through the one bridge (modules/external_assimilation/node_bridge.py), never copied:
    validateGraph(nodes)           cycle, depth, unknown dependency
    createPlanGraph(...).ready()   per wave: which plans may run together; one held back = overlap
One rule is GSD's own and is native here: a dependency must sit in an EARLIER wave.

Verdicts, never collapsed (a check that could not judge is not a check that passed):
    OK        every pending plan judged; nothing refused
    REFUSED   a cycle, an unknown same-phase dependency, a wave-order violation, or same-wave
              plans with overlapping writes
    UNJUDGED  something needed was absent: unparseable frontmatter, no `wave`, `files_modified`
              never declared (a declared empty list means "writes nothing" and is judged), a path
              outside the work tree, or the bridge could not answer

    python tools/plan_graph_check.py <phase-dir | .planning dir | project root> [--workstream WS] [--json]
exit 0 OK · 3 REFUSED · 2 UNJUDGED · 4 nothing pending
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules.external_assimilation import node_bridge as nb  # noqa: E402

OK, REFUSED, UNJUDGED = "OK", "REFUSED", "UNJUDGED"
_FRONT = re.compile(r"\A﻿?---\r?\n(.*?)\r?\n---\r?\n", re.S)
_PREFIX = re.compile(r"^(\d+(?:\.\d+)?)-")


def _yaml(text: str):
    import yaml
    return yaml.safe_load(text)


def read_plan(path: Path) -> dict:
    """One plan's facts. `error` set means the plan could not be read -- never a default."""
    pid = path.name[: -len("-PLAN.md")]
    out = {"id": pid, "path": str(path), "done": path.with_name(f"{pid}-SUMMARY.md").is_file()}
    try:
        m = _FRONT.match(path.read_text(encoding="utf-8"))
        fm = _yaml(m.group(1)) if m else None
    except Exception as exc:  # noqa: BLE001 -- unreadable is its own answer
        return {**out, "error": f"frontmatter unreadable: {exc.__class__.__name__}"}
    if not isinstance(fm, dict):
        return {**out, "error": "no frontmatter"}
    deps = fm.get("depends_on") or []
    if isinstance(deps, str):
        deps = [deps]
    out["depends_on"] = [str(d) for d in deps]
    out["wave"] = fm.get("wave")
    out["files_modified"] = fm.get("files_modified", None) if "files_modified" in fm else None
    out["declared_files"] = "files_modified" in fm
    return out


def _git_root(path: Path) -> Path | None:
    return next((a for a in [path, *path.parents] if (a / ".git").exists()), None)


def _common_repo(root: Path | None) -> Path | None:
    """The repository a work tree belongs to. A worktree's `.git` is a FILE naming its gitdir,
    whose `commondir` names the main repository's; a clone's `.git` is the directory itself."""
    if root is None:
        return None
    g = root / ".git"
    try:
        if g.is_dir():
            return g.resolve()
        gitdir = Path(g.read_text(encoding="utf-8").split("gitdir:", 1)[1].strip())
        gitdir = gitdir if gitdir.is_absolute() else (root / gitdir)
        common = gitdir / "commondir"
        return (gitdir / common.read_text(encoding="utf-8").strip()).resolve() if common.is_file() else gitdir.resolve()
    except (OSError, IndexError):
        return None


def _owns(files, work_root: Path) -> tuple[list[str] | None, str]:
    """Ownership keys: ONE path for every entry, relative or absolute.

    Plans executed in a git worktree name that worktree's absolute paths (measured: KobiiCraft
    luckyarena-arena2 -> <home>/Apps/kme-wt-arena2/...), while their siblings name the same files
    relative to the project. So each entry is resolved (a relative one against the work root that
    holds .planning) and keyed under ITS OWN git work tree: worktrees of our repository share
    relative paths and collide as they must; a symlink or junction keys like its target; a tree
    of ANOTHER repository -- including a submodule -- keeps its own namespace. Two real reviewers
    (2026-09-28) found every one of these as a missed or invented overlap while relative and
    absolute entries took different paths."""
    import hashlib
    import os
    base = work_root.resolve()
    home = _common_repo(_git_root(base))
    rel = []
    for f in files or []:
        p = str(f).strip()
        if not p:
            continue
        pp = Path(p)
        pp = (pp if pp.is_absolute() else base / pp).resolve()
        root = _git_root(pp)
        try:
            p = pp.relative_to(root or base).as_posix()
        except ValueError:
            return None, f"path outside any git work tree: {f}"
        if root is not None and _common_repo(root) != home:
            # A namespace, not a path: a key never carries a home directory. normcase folds case
            # only where the filesystem does, so case-distinct repos stay distinct on Linux.
            ident = os.path.normcase(str(_common_repo(root) or root))
            p = f"[repo-{hashlib.sha1(ident.encode()).hexdigest()[:10]}]/{p}"
        rel.append(p)
    return rel, ""


def check_phase(phase_dir: Path, work_root: Path, timeout: float = 30.0, include_done: bool = False) -> dict:
    plans = [read_plan(p) for p in sorted(phase_dir.glob("*-PLAN.md"))]
    if include_done:  # audit mode: judge the whole phase as planned, finished plans included
        plans = [{**p, "done": False} for p in plans]
    res = {"phase": phase_dir.name, "verdict": OK, "refused": [], "unjudged": [], "pending": []}
    if not plans:
        return {**res, "verdict": None}
    ids = {p["id"] for p in plans}
    done = {p["id"] for p in plans if p.get("done")}
    pending = [p for p in plans if not p.get("done")]
    res["pending"] = [p["id"] for p in pending]
    if not pending:
        return {**res, "verdict": None}
    # Wave and ownership exist to separate SIBLINGS. A lone pending plan has none, so their
    # absence cannot hide a collision (measured: arena7 03-01 declares neither, correctly).
    alone = len(pending) == 1
    prefix = {(_PREFIX.match(i) or [None, None])[1] for i in ids} - {None}
    nodes, wave_of = [], {}
    for p in pending:
        if p.get("error"):
            res["unjudged"].append(f"{p['id']}: {p['error']}")
            continue
        if alone:
            p = {**p, "wave": p.get("wave") if isinstance(p.get("wave"), int) else 1,
                 "declared_files": True, "files_modified": p.get("files_modified") or []}
        if not isinstance(p.get("wave"), int):
            res["unjudged"].append(f"{p['id']}: no integer `wave`")
            continue
        if not p["declared_files"]:
            res["unjudged"].append(f"{p['id']}: `files_modified` never declared; write ownership unknown")
            continue
        owns, why = _owns(p["files_modified"], work_root)
        if owns is None:
            res["unjudged"].append(f"{p['id']}: {why}")
            continue
        wave_of[p["id"]] = p["wave"]
        # A dependency on a finished plan, or on another phase's plan, is satisfied, not unknown.
        # A same-phase dependency with no plan file stays in the graph so upstream refuses it.
        same_phase = [d for d in p["depends_on"] if d not in done and
                      ((_PREFIX.match(d) or [None, None])[1] in prefix)]
        nodes.append({"id": p["id"], "task": f"{phase_dir.name} plan {p['id']}", "dependsOn": same_phase,
                      "owns": owns, "readOnly": not owns})
    if res["unjudged"]:
        res["verdict"] = UNJUDGED
        return res
    for n in nodes:
        for d in n["dependsOn"]:
            if d in wave_of and wave_of[d] >= wave_of[n["id"]]:
                res["refused"].append(f"wave order: {n['id']} (wave {wave_of[n['id']]}) depends on {d} "
                                      f"(wave {wave_of[d]}); a dependency must run in an earlier wave")
    size = max(50, len(nodes))
    v = nb.call("planning", "validateGraph", [nodes, {"maxNodes": size}], timeout=timeout)
    if not v.ok:
        res["unjudged"].append(f"bridge {v.outcome}: {v.error}")
    elif not (v.value or {}).get("ok"):
        res["refused"] += [f"graph: {e}" for e in (v.value or {}).get("errors") or []]
    waves: dict[int, list[dict]] = {}
    for n in nodes:
        waves.setdefault(wave_of[n["id"]], []).append({**n, "dependsOn": []})
    for w, members in sorted(waves.items()):
        if len(members) < 2:
            continue
        r = nb.call("planning", None, [[], []], factory={"fn": "createPlanGraph", "args": [
            {"nodes": members, "capacity": min(100, len(members)), "maxNodes": max(50, len(members))}]},
            method="ready", timeout=timeout)
        if not r.ok:
            res["unjudged"].append(f"wave {w}: bridge {r.outcome}: {r.error}")
            continue
        together = {x["id"] for x in (r.value or {}).get("ready") or []}
        held = [m["id"] for m in members if m["id"] not in together]
        if not together:
            res["unjudged"].append(f"wave {w}: the planner selected no plan; overlap not judged")
        elif held:
            # The planner says who it held back, not with whom it collides: claim only that.
            res["refused"].append(f"wave {w}: {', '.join(held)} held back for writes overlapping one of "
                                  f"{', '.join(sorted(together))}; run them one at a time, not in parallel")
    res["verdict"] = REFUSED if res["refused"] else UNJUDGED if res["unjudged"] else OK
    return res


def phase_dirs(target: Path, workstream: str | None = None) -> list[Path]:
    if list(target.glob("*-PLAN.md")):
        return [target]
    planning = target if target.name == ".planning" else target / ".planning"
    base = planning / "workstreams" / workstream / "phases" if workstream else planning / "phases"
    return sorted(d for d in base.iterdir() if d.is_dir()) if base.is_dir() else []


def check_tree(target: str, workstream: str | None = None, include_done: bool = False) -> list[dict]:
    t = Path(target)
    work_root = t
    while work_root.name and not (work_root / ".planning").is_dir() and work_root != work_root.parent:
        work_root = work_root.parent
    if not (work_root / ".planning").is_dir():
        work_root = t
    return [r for r in (check_phase(d, work_root, include_done=include_done)
                        for d in phase_dirs(t, workstream)) if r["verdict"]]


def card_lines(results: list[dict]) -> str:
    """For the successor card: what a worker must know before running a wave. Empty = nothing pending."""
    if not results:
        return ""
    bad = [r for r in results if r["verdict"] != OK]
    n = sum(len(r["pending"]) for r in results)
    if not bad:
        return f"PLAN GRAPH: {n} pending plan(s) in {len(results)} phase(s) judged; no same-wave write overlap."
    lines = ["PLAN GRAPH (checked at hand-off; the repository wins if it has changed):"]
    for r in bad:
        for x in (r["refused"] or r["unjudged"])[:4]:
            lines.append(f"  {r['verdict']} {r['phase']}: {x}")
    return "\n".join(lines)


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("target")
    ap.add_argument("--workstream")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--include-done", action="store_true", help="audit: judge finished plans too")
    a = ap.parse_args(argv)
    results = check_tree(a.target, a.workstream, a.include_done)
    if a.json:
        print(json.dumps(results, indent=1))
    else:
        for r in results:
            print(f"{r['verdict']:9} {r['phase']}  pending={','.join(r['pending'])}")
            for x in r["refused"] + r["unjudged"]:
                print(f"          - {x}")
    if not results:
        print("nothing pending")
        return 4
    verdicts = {r["verdict"] for r in results}
    return 3 if REFUSED in verdicts else 2 if UNJUDGED in verdicts else 0


if __name__ == "__main__":
    sys.exit(main())
