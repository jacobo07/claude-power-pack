"""GSD X universal, autonomous half (Owner 2026-11-03: "si no tiene el milestone, debe crearse autónomamente, no esperar
a que yo lo abra"). Spec vault/specs/gsd-x-universal-mission.md.

`ensure(cwd, ...)` is called by gsd_mission.arm / arm_chain BEFORE the preflight. When GSD answers NO_PHASES or
ALL_COMPLETE for cwd, it writes a milestone (.planning/ROADMAP.md + STATE.md + PROJECT.md) whose phases are the work
packet's phases, then asks GSD again. Only a GSD `OK` keeps the files; anything else restores what was there before.
Prior .planning files are moved to .planning/milestones/auto-archived-<stamp>/, never deleted.
The preflight stays read-only: it judges what this module wrote, exactly as it would judge a hand-written roadmap.
CLI: python tools/gsd_milestone_scaffold.py ensure --cwd DIR [--wu-packet P] [--command C]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_long_run as lr  # noqa: E402

FILES = ("ROADMAP.md", "STATE.md", "PROJECT.md")
_PHASE_LINE = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?(?:(?:Phase|Fase|Step|Paso)\s+(\d+)|([QPW]\d+)|(\d+)[.)])\s*[:.\-—–]*\s*(.+)$",
                         re.IGNORECASE)


def absent_roadmap(st: dict) -> dict:
    """gsd-tools EXITS 1 with "No ROADMAP.md found" on a repo with no milestone, which gsd_status reports as UNAVAILABLE.
    That is GSD answering (a measured absence), not GSD unreachable: read it as NO_PHASES. Measured 2026-11-03 on a
    fresh temp dir; it is why the first GSD X refusal (37b2abaf) never fired on the commonest case."""
    m = re.search(r"No (ROADMAP|STATE)\.md found", str(st.get("reason") or ""))
    if st.get("outcome") == "UNAVAILABLE" and m:
        return dict(st, outcome="NO_PHASES", reason=f"GSD finds no {m.group(1)}.md (gsd-tools: {m.group(0)})")
    return st


def enabled() -> bool:
    return (os.environ.get("CPP_GSD_X_AUTOSCAFFOLD") or "").strip().lower() != "off"


def phases_from_packet(text: str, fallback: str) -> list[str]:
    """Ordered, de-duplicated phase names read from the packet; one fallback phase when it names none."""
    seen, out = set(), []
    for line in (text or "").splitlines():
        m = _PHASE_LINE.match(line)
        if not m:
            continue
        label = (m.group(2) or "").upper()
        name = re.sub(r"[`*_]", "", m.group(4)).strip().rstrip(":")
        name = re.split(r"(?<=[a-z0-9)])[.;] ", name, maxsplit=1)[0][:70].strip()
        if len(name) < 4:
            continue
        key = label or name.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(f"{label} {name}".strip() if label and not name.upper().startswith(label) else name)
        if len(out) >= 12:
            break
    return out or [fallback[:70]]


def render(phases: list[str], *, title: str, source: str, today: str) -> dict[str, str]:
    checklist = "\n".join(f"- [ ] **Phase {i}: {p}**" for i, p in enumerate(phases, 1))
    details = "\n\n".join(
        f"### Phase {i}: {p}\n**Goal**: {p} -- as the work packet defines it\n"
        f"**Depends on**: {'Nothing' if i == 1 else f'Phase {i - 1}'}\n**Requirements**: {source}\n"
        f"**Success Criteria** (what must be TRUE):\n  1. The packet's acceptance for this phase holds, with evidence committed\n"
        f"**Plans**: TBD" for i, p in enumerate(phases, 1))
    progress = "\n".join(f"| {i}. {p} | 0/0 | Not started | - |" for i, p in enumerate(phases, 1))
    roadmap = (f"# Roadmap: {title}\n\n## Milestones\n\n- 🚧 **auto-{today}** -- Phases 1-{len(phases)} (in progress)\n\n"
               f"## Phases\n\n{checklist}\n\n## Phase Details\n\n{details}\n\n## Progress\n\n"
               f"| Phase | Plans Complete | Status | Completed |\n|-------|----------------|--------|-----------|\n{progress}\n")
    state = (f"---\ngsd_state_version: \"1.0\"\nmilestone: auto-{today}\nmilestone_name: {title}\nstatus: Executing\n"
             f"last_activity: {today}\nlast_activity_desc: milestone auto-scaffolded at arm from {source}\n"
             f"progress:\n  total_phases: {len(phases)}\n  completed_phases: 0\n  total_plans: 0\n  completed_plans: 0\n"
             f"current_phase: 01\ncurrent_phase_name: {phases[0]}\n---\n\n# STATE -- {title}\n\n"
             f"milestone: auto-{today}\n\n## NEXT\nPhase 1: {phases[0]} (rules: {source})\n")
    project = (f"# {title}\n\n## What This Is\nMilestone scaffolded automatically when a mission was armed without one "
               f"(GSD X universal). The work packet is the source of truth: {source}\n")
    return {"ROADMAP.md": roadmap, "STATE.md": state, "PROJECT.md": project}


def ensure(cwd, *, wu_packet: str | None = None, command: str | None = None, workstream: str | None = None,
           status_reader=None, now: float | None = None) -> dict:
    """{'action': 'none'|'scaffolded'|'failed'|'skipped', ...}. Never raises on an instrument fault."""
    raw = status_reader or (lambda c, w: lr.gsd_status(c, workstream=w))
    reader = lambda c, w: absent_roadmap(raw(c, w))  # noqa: E731
    if not enabled():
        return {"action": "skipped", "why": "CPP_GSD_X_AUTOSCAFFOLD=off"}
    if workstream:
        return {"action": "skipped", "why": "workstream layouts are not scaffolded"}
    root = Path(cwd)
    if not root.is_dir():
        return {"action": "skipped", "why": f"cwd {cwd} is not a directory"}
    try:
        st = reader(str(root), None)
    except Exception as exc:  # noqa: BLE001
        return {"action": "skipped", "why": f"gsd_status raised {type(exc).__name__}"}
    if st.get("outcome") not in ("NO_PHASES", "ALL_COMPLETE"):
        return {"action": "none", "outcome": st.get("outcome")}
    text, source = "", "the arm command"
    if wu_packet and Path(wu_packet).is_file():
        text = Path(wu_packet).read_text(encoding="utf-8", errors="replace")
        source = str(wu_packet)
    title = (text.splitlines()[0].lstrip("# ").strip()[:80] if text.strip() else root.name) or root.name
    phases = phases_from_packet(text, fallback=f"Execute {Path(wu_packet).name if wu_packet else (command or 'the mission')}")
    stamp = time.strftime("%Y%m%dT%H%M%S", time.localtime(now))
    plan = root / ".planning"
    archive = plan / "milestones" / f"auto-archived-{stamp}"
    moved = []
    plan.mkdir(exist_ok=True)
    for f in FILES:
        if (plan / f).exists():
            archive.mkdir(parents=True, exist_ok=True)
            shutil.move(str(plan / f), str(archive / f))
            moved.append(f)
    for f, body in render(phases, title=title, source=source, today=time.strftime("%Y-%m-%d", time.localtime(now))).items():
        (plan / f).write_text(body, encoding="utf-8", newline="\n")
    try:
        after = reader(str(root), None)
    except Exception as exc:  # noqa: BLE001
        after = {"outcome": "UNAVAILABLE", "reason": f"{type(exc).__name__}"}
    if after.get("outcome") == "OK":
        return {"action": "scaffolded", "phases": phases, "archived": [str(archive / f) for f in moved],
                "before": st.get("outcome"), "after": after.get("reason")}
    for f in FILES:                       # not judged OK: put back exactly what was there
        (plan / f).unlink(missing_ok=True)
        if f in moved:
            shutil.move(str(archive / f), str(plan / f))
    if moved and archive.is_dir() and not any(archive.iterdir()):
        archive.rmdir()
    return {"action": "failed", "why": f"GSD answered {after.get('outcome')}: {after.get('reason')}", "phases": phases}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("ensure")
    e.add_argument("--cwd", required=True)
    e.add_argument("--wu-packet")
    e.add_argument("--command")
    a = ap.parse_args(argv)
    res = ensure(a.cwd, wu_packet=a.wu_packet, command=a.command)
    print(json.dumps(res, indent=1))
    return 0 if res["action"] in ("none", "scaffolded", "skipped") else 1


if __name__ == "__main__":
    sys.exit(main())
