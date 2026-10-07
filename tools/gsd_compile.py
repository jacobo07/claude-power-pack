#!/usr/bin/env python3
"""Compile one ROADMAP phase into a dossier + a work-unit packet, and optionally arm it (spec law 5).

    gsd_compile.py compile --repo R --workstream W --phase N [--gate CMD] [--out DIR] [--arm | --dry-run]

Zero model calls. The packet's `done_gate:` is deterministic and mandatory: a packet without one cannot
end its own mission (law 4), so it is not admissible and nothing is written. The budget comes from the
measured floor table through route_admission (floor x calls x (1 + margin)), never from a guess.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gsd_dossier as gd  # noqa: E402
import route_admission as ra  # noqa: E402

DEFAULT_CALLS = 60
WINDOW_STEP = 10_000
ESTIMATE_STEP = 1_000_000
PROFILE = "top-level-worker"
_PHASE_RE = r"^### Phase {n}:[ \t]*(.*)$"
_GATE_LINE = re.compile(r"^\**Gate\**:\**[ \t]*(\S.*?)[ \t]*$", re.MULTILINE | re.IGNORECASE)


class CompileError(ValueError):
    pass


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def parse_phase(roadmap: str, n: int) -> dict:
    """Goal, Requirements and Success Criteria of `### Phase N:` verbatim; refuses an absent or `[x]` phase."""
    m = re.search(_PHASE_RE.format(n=n), roadmap, re.MULTILINE)
    if not m:
        raise CompileError(f"phase {n} is not in the roadmap")
    nxt = re.search(r"^### Phase \d+", roadmap[m.end():], re.MULTILINE)
    section = roadmap[m.start(): m.end() + (nxt.start() if nxt else len(roadmap) - m.end())].rstrip() + "\n"
    done = re.search(rf"^- \[[xX]\] \*\*Phase {n}:", roadmap, re.MULTILINE)
    if done:
        raise CompileError(f"phase {n} is already complete ([x] in the roadmap)")
    goal = re.search(r"^\*\*Goal\*\*:[ \t]*(.+)$", section, re.MULTILINE)
    req = re.search(r"^\*\*Requirements\*\*:[ \t]*(.+)$", section, re.MULTILINE)
    sc = re.search(r"^\*\*Success Criteria\*\*:[^\n]*\n(.*?)(?=^\*\*|\Z)", section, re.MULTILINE | re.DOTALL)
    criteria: list[str] = []
    for ln in (sc.group(1) if sc else "").splitlines():
        if re.match(r"^\s*\d+\.\s", ln):
            criteria.append(ln.strip())
        elif ln.strip() and criteria:
            criteria[-1] += "\n" + ln.rstrip()
    if not criteria:
        raise CompileError(f"phase {n} has no Success Criteria: there is nothing to verify")
    return {"title": m.group(1).strip(), "goal": goal.group(1).strip() if goal else "",
            "requirements": req.group(1).strip() if req else "", "criteria": criteria, "section": section}


def phase_gate(phase: dict, gate: str | None) -> str:
    chosen = (gate or "").strip()
    if not chosen:
        g = _GATE_LINE.search(phase["section"])
        chosen = g.group(1).strip().strip("`").strip() if g else ""
    if not chosen:
        raise CompileError("no gate: give --gate CMD or a `Gate:` line in the phase. A packet without a "
                           "deterministic done_gate cannot end its mission and is not admissible")
    if "\n" in chosen:
        raise CompileError("the gate must be one command line")
    return chosen


def module_roots(section: str, repo: Path) -> list[str]:
    """Directories the phase text names in backticks (`tools/`, `modules/x`) that exist in the repo."""
    found: list[str] = []
    for tok in re.findall(r"`([A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-]+)*)/?`", section):
        if "/" in tok or (repo / tok).is_dir():
            top = tok.rstrip("/")
            p = repo / top
            if p.is_dir() and top not in found and ".planning" not in top:
                found.append(top)
            elif p.is_file() and p.suffix == ".py":
                parent = str(Path(top).parent)
                if parent not in (".", "") and (repo / parent).is_dir() and parent not in found:
                    found.append(parent)
    return found


def budget(packet_bytes: int, *, calls: int, margin: float, floors_path=None) -> dict:
    """token_estimate and autocompact from the measured floor: route_admission is the judge."""
    floors = ra.load_floors(floors_path)
    floor = (floors["profiles"].get(PROFILE) or {}).get("floor")
    if isinstance(floor, bool) or not isinstance(floor, int) or floor <= 0:
        raise CompileError(f"no measured floor for profile {PROFILE!r}: the budget cannot be derived")
    packet_tokens = -(-packet_bytes // 4)
    route = {"workers": [{"name": "worker", "profile": PROFILE, "calls": calls, "packet": packet_tokens}]}
    need = ra.admit({**route, "envelope": {"target": 1, "warn": 1, "stop": 1}}, floors, margin=margin)
    estimate = -(-need["need_with_margin"] // ESTIMATE_STEP) * ESTIMATE_STEP
    verdict = ra.admit({**route, "envelope": {"target": estimate, "warn": estimate, "stop": 2 * estimate,
                                              "calls": calls}}, floors, margin=margin)
    if verdict["verdict"] != ra.ADMISSIBLE:
        raise CompileError(f"route_admission refuses the derived budget: {verdict['verdict']} {verdict['reasons']}")
    import gsd_mission as gm
    need_window = floor + packet_tokens + gm.GRAMMAR_WINDOW_MARGIN
    window = -(-need_window // WINDOW_STEP) * WINDOW_STEP
    return {"floor": floor, "packet_tokens": packet_tokens, "calls": calls, "margin": margin,
            "need": need["need"], "need_with_margin": need["need_with_margin"], "token_estimate": estimate,
            "autocompact": window, "route": route}


def render_packet(*, phase: dict, n: int, ws: str, gate: str, work_tree: str, worktree_name: str,
                  out_dir: str, budget_info: dict, module_dirs: list[str]) -> str:
    crit = "\n".join(phase["criteria"])
    b = budget_info
    return f"""done_gate: {gate}
work_tree: {work_tree}

# WU-P{n} -- {phase['title']}

Compiled from `.planning/workstreams/{ws}/ROADMAP.md` phase {n} by `tools/gsd_compile.py`; zero model calls.
This file is your scope, done-gate and budget. Fresh worker, no parent transcript.

## 0. Where you work
- FIRST action: EnterWorktree with name `{worktree_name}`. All edits, tests and commits happen in `{work_tree}`
  (the `work_tree:` line above) and only there. Never edit the main clone, never push, never touch another
  mission's directory. Pathspec commits on the worktree branch.
- Do not run GSD commands and do not spawn agents unless this packet names one.

## 1. Inputs (read in this order)
1. `{out_dir}/dossier.md` -- bounded zero-model reality scan of this phase; it is your map, trust its file:line
   candidates only after you open the file. `{out_dir}/refs.jsonl` holds every hit: page it, never guess.
2. The roadmap section for this phase (below), and the files the dossier names.
{('3. Module roots scanned: ' + ', '.join('`' + d + '`' for d in module_dirs)) if module_dirs else '3. No module root was named in the phase text.'}

## 2. Goal
{phase['goal'] or '(the roadmap states none; the success criteria below are the goal)'}
{('Requirements: ' + phase['requirements']) if phase['requirements'] else ''}

## 3. Outputs -- the success criteria, verbatim
{crit}

## 4. Budget
Measured floor {b['floor']:,} per call ({PROFILE}) x {b['calls']} calls x (1 + {b['margin']:g}) = {b['need_with_margin']:,}
-> token estimate {b['token_estimate']:,}. At most {b['calls']} model calls. The cost breaker parks you at twice the
estimate, so stay lean. Redirect test output to logs; read only the summary and failing lines.

## 5. Boundary reasons
Stop and write the open point to the progress file instead of ending on a question when: a success criterion
cannot be met inside the scope above, a file you must change is owned by another mission, or the gate cannot be
made to pass. A finished packet is one whose done_gate exits 0; do not wait for anything after that.

## 6. Done
In the worktree: `{gate}` exits 0. Commit, then end with `HANDOFF NOTE:` and one line. Do not wait.

## Roadmap section (verbatim)
{phase['section']}"""


def compile_phase(repo: str, ws: str, n: int, *, gate: str | None = None, out: str | None = None,
                  calls: int = DEFAULT_CALLS, margin: float = ra.DEFAULT_GROWTH_MARGIN, arm: bool = False,
                  dry_run: bool = False, floors_path=None) -> dict:
    root = Path(repo).resolve()
    road = root / ".planning" / "workstreams" / ws / "ROADMAP.md"
    if not road.is_file():
        raise CompileError(f"no roadmap at {road}")
    phase = parse_phase(road.read_text(encoding="utf-8-sig"), n)
    chosen = phase_gate(phase, gate)
    out_dir = Path(out).resolve() if out else root / ".planning" / "workstreams" / ws / "packets" / f"phase-{n}"
    wt_name = f"wu-{_slug(ws)}-p{n}"
    work_tree = str(root / ".claude" / "worktrees" / wt_name)
    mods = module_roots(phase["section"], root)
    kw = dict(phase=phase, n=n, ws=ws, gate=chosen, work_tree=work_tree, worktree_name=wt_name,
              out_dir=str(out_dir), module_dirs=mods)
    first = render_packet(budget_info=budget(0, calls=calls, margin=margin, floors_path=floors_path), **kw)
    b = budget(len(first.encode("utf-8")), calls=calls, margin=margin, floors_path=floors_path)
    packet = render_packet(budget_info=b, **kw)
    b = budget(len(packet.encode("utf-8")), calls=calls, margin=margin, floors_path=floors_path)
    result = {"phase": n, "title": phase["title"], "gate": chosen, "work_tree": work_tree, "worktree": wt_name,
              "out_dir": str(out_dir), "packet": str(out_dir / f"WU-P{n}.md"), "module_roots": mods,
              "budget": {k: v for k, v in b.items() if k != "route"}, "packet_bytes": len(packet.encode("utf-8")),
              "dry_run": bool(dry_run), "mission": None}
    if dry_run:
        return result
    out_dir.mkdir(parents=True, exist_ok=True)
    contract = out_dir / "contract.md"
    heads = [re.sub(r"^\s*\d+\.\s*", "", c.splitlines()[0])[:160] for c in phase["criteria"]]
    contract.write_text("\n".join("### " + h for h in heads) + "\n\n" + phase["section"], encoding="utf-8")
    dargs = ["--repo", str(root), "--contract", str(contract), "--out", str(out_dir)]
    for m in mods:
        dargs += ["--module-root", m]
    result["dossier"] = gd.build(_dossier_args(dargs))
    Path(result["packet"]).write_text(packet, encoding="utf-8")
    est = b["token_estimate"]
    route = {**b["route"], "envelope": {"target": est, "warn": est, "stop": 2 * est, "calls": calls}}
    result["route"] = str(out_dir / "route.json")
    Path(result["route"]).write_text(json.dumps(route, indent=1), encoding="utf-8")
    if arm:
        result["mission"] = arm_mission(str(root), ws, result["packet"], result["route"], b, floors_path)
    return result


def _dossier_args(argv: list[str]):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo")
    ap.add_argument("--contract")
    ap.add_argument("--out")
    ap.add_argument("--module-root", action="append", default=[])
    a = ap.parse_args(argv)
    a.glob, a.cmd, a.salvage = ["."], [], []
    a.per_concept, a.max_bytes, a.cmd_timeout = 6, 160_000, 300
    return a


def arm_mission(repo: str, ws: str, packet: str, route: str, b: dict, floors_path=None) -> str:
    """arm(no launch) -> hold -> envelope -> admit -> release, through gsd_mission's own functions.
    launch_worker refuses a packet whose route was never admitted, so admission is part of arming. A refusal
    anywhere leaves the record held: nothing launches on a half-set envelope."""
    import gsd_mission as gm
    mid = gm.arm(repo, f"/gsd-autonomous --ws {ws}", launch=False, workstream=ws)["mission"]["mission_id"]
    gm.set_owner_hold(mid, "gsd_compile: envelope is being set")
    gm.set_envelope(mid, token_estimate=b["token_estimate"], model="sonnet", autocompact=b["autocompact"],
                    wu_packet=packet)
    verdict = gm.admit_route(mid, route, floors_path=floors_path)["admission"]["verdict"]
    if verdict != "ADMISSIBLE":
        raise CompileError(f"mission {mid} stays held: route admission says {verdict}")
    gm.release_owner_hold(mid)
    return mid


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compile")
    c.add_argument("--repo", required=True)
    c.add_argument("--workstream", required=True)
    c.add_argument("--phase", type=int, required=True)
    c.add_argument("--gate")
    c.add_argument("--out")
    c.add_argument("--calls", type=int, default=DEFAULT_CALLS)
    c.add_argument("--margin", type=float, default=ra.DEFAULT_GROWTH_MARGIN)
    g = c.add_mutually_exclusive_group()
    g.add_argument("--arm", action="store_true")
    g.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    try:
        res = compile_phase(a.repo, a.workstream, a.phase, gate=a.gate, out=a.out, calls=a.calls,
                            margin=a.margin, arm=a.arm, dry_run=a.dry_run)
    except (CompileError, ValueError, OSError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(res, indent=1))
    if res["mission"]:
        print(f"MISSION {res['mission']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
