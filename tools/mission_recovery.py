"""AMR -- Autonomous Mission Recovery (plan vault/plans/amr-autonomous-mission-recovery-20261013.md).

A cost breaker stops an EXECUTOR. Before AMR it also stopped the durable goal: `_cost_breaker` set an
owner hold and `plan_next` answered `none` for every hold, so the mission sat until a person deleted a
file. Measured 2026-10-13 (m-342bc71ba415, KSP-FUSION): a gsd-planner subagent burned 4.47M with no
PLAN.md, the breaker fired correctly at 00:01 UTC, and the goal stayed idle 8 h 15 min while the
planner's own hand-back already held a complete design for the work.

This module decides what replaces the failed executor. Everything here is deterministic and model-free;
gsd_mission.recover_mission does the I/O (fence, admit, launch) and records each step on the hold.

  evidence -> progress class -> failure class -> strategy identity -> residual -> successor topology
  -> lease -> ContextImage packet + route -> (gsd_mission) fence old, admit, launch

Recover is not unhold: the failed worker's per-session guard file (stop=1) is never removed -- it is the
fence -- and the failed strategy is recorded so it cannot renew unchanged.

Kill switch CPP_MISSION_RECOVERY=off (and shadow: compile and record, never launch).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
from pathlib import Path

# --------------------------------------------------------------------------- vocabulary
HELD = "HELD_FOR_DIAGNOSIS"
SUCCESSOR_LAUNCHED = "SUCCESSOR_LAUNCHED"
OWNER_BOUNDARY = "OWNER_BOUNDARY"
DURABLE_WAIT = "DURABLE_WAIT"
SHADOW_COMPILED = "SHADOW_COMPILED"
NOT_APPLICABLE = "NOT_APPLICABLE"   # nothing AMR can recover (GSD complete / residual unreadable): legacy settle or park
# AMCR: an unreadable residual is a failed recovery (retried, then a surfaced liveness incident), never
# NOT_APPLICABLE and never an Owner wait. RECOVERY_FAILED is retried every pass; RECOVERY_EXHAUSTED is final.
RECOVERY_FAILED = "RECOVERY_FAILED"
RECOVERY_EXHAUSTED = "RECOVERY_EXHAUSTED"
MAX_RECOVERY_FAILURES = 3
TERMINAL_RECOVERY_STATES = (SUCCESSOR_LAUNCHED, OWNER_BOUNDARY, DURABLE_WAIT, SHADOW_COMPILED, NOT_APPLICABLE,
                            RECOVERY_EXHAUSTED)


def eligible(rec: dict) -> bool:
    """Missions whose residual AMR can compile: a GSD resume mission, or one AMR already leased. Packet and
    chain units keep their own halt-continue path (gsd_mission.halt_continue), which owns their residual."""
    if rec.get("amr"):
        return True
    if rec.get("rollover_protocol"):   # capsule-v2 rotation (seal/gate/authorize) is not wired into AMR (audit F4)
        return False
    return str(rec.get("resume_command") or "").startswith("/gsd-autonomous") and not rec.get("wu_packet")

PRODUCT, PROOF, KNOWLEDGE, PLAN, INFRA = "PRODUCT", "PROOF", "KNOWLEDGE", "PLAN", "INFRASTRUCTURE"
MIXED, ZERO, UNKNOWN = "MIXED", "ZERO", "UNKNOWN"

PLANNER_TOPOLOGY_FAILURE = "PLANNER_TOPOLOGY_FAILURE"
SUBAGENT_NEGATIVE_EVC = "SUBAGENT_NEGATIVE_EVC"
EXECUTOR_STALL = "EXECUTOR_STALL"
EXECUTOR_OVERRUN = "EXECUTOR_OVERRUN"
REPEATED_STRATEGY = "REPEATED_STRATEGY"
UNCLASSIFIED = "UNCLASSIFIED"
LEASE_EXHAUSTED_WITH_PROGRESS = "LEASE_EXHAUSTED_WITH_PROGRESS"   # a productive lease ran out: renew, never fence

# Read-only agent types are never fenced: they cannot be the planner topology that failed, and the packet allows
# them to locate a file (audit F8).
READ_ONLY_AGENTS = frozenset({"Explore", "oneshot-architect-auditor", "gsd-plan-checker", "pp-code-reviewer",
                              "claude-code-guide", "kcoo-g1", "kme-g1-ownership-arbiter"})

MAIN_THREAD, PLANNER_AGENT, AGENT, MULTI_AGENT = "main_thread", "planner_agent", "agent", "multi_agent"

MAX_RECOVERIES_PER_UNIT = 2      # each must carry a different strategy identity
MIN_LEASE_TOKENS = 1_000_000     # below this a successor cannot finish one plan: Owner boundary
RESERVE_FRACTION = 0.15          # recovery 10 % + closeout 5 % of the remaining authority stay unleased
PRICE_PER_ITEM = 2_000_000       # processed tokens per residual item; replaced by PGO once measured
LEASE_STOP_OVER_TARGET = 1.3     # route envelope: target = lease / 1.3, warn = lease / 1.15, stop = lease

# Paths a hook rewrites in every tree (mirror-drift counter, measured in the KSP worktree 01:20 UTC):
# never progress, in either direction.
HOOK_OWNED = (re.compile(r"^vault/handoffs/(ESCALATED\.md|escalations\.json)$"),)


def mode() -> str:
    v = str(os.environ.get("CPP_MISSION_RECOVERY") or "on").strip().lower()
    return v if v in ("on", "shadow", "off") else "on"


# --------------------------------------------------------------------------- strategy identity
def strategy_identity(goal: str, unit: str, topology: str, agent_types=(), decomposition: str = "") -> str:
    """Same goal + unit + topology + agent types + decomposition = same strategy, whatever the session,
    the model or the prompt wording. A new session running the same planner hashes equal (law 3)."""
    key = json.dumps([goal or "", unit or "", topology, sorted({str(a) for a in agent_types if a}),
                      decomposition or ""], separators=(",", ":"))
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def topology_of(agent_types) -> str:
    kinds = [a for a in agent_types if a]
    if not kinds:
        return MAIN_THREAD
    if len(set(kinds)) > 1:
        return MULTI_AGENT
    return PLANNER_AGENT if "plan" in kinds[0].lower() else AGENT


# --------------------------------------------------------------------------- evidence
_HANDBACK = "[Subagent hand-back]"


def _jsonl(path: Path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if isinstance(r, dict):
                    yield r
    except OSError:
        return


def _text_of(content) -> str:
    if isinstance(content, str):
        return content
    out = []
    for b in content or []:
        if isinstance(b, dict):
            if isinstance(b.get("text"), str):
                out.append(b["text"])
            elif b.get("type") == "tool_result":
                out.append(_text_of(b.get("content")))
    return "\n".join(out)


def window_evidence(transcript: Path | None, work_dir: str) -> dict:
    """What the failed executor did, read from its own transcript and its subagents' transcripts.
    Absence of a transcript is UNKNOWN evidence, never zero work."""
    ev = {"transcript": str(transcript) if transcript else None, "measured": False, "agents": [],
          "handbacks": [], "off_tree_writes": [], "in_tree_writes": [], "subagent_calls": 0}
    if not transcript or not Path(transcript).is_file():
        return ev
    ev["measured"] = True
    wd = os.path.normcase(os.path.abspath(work_dir)) if work_dir else ""
    agent_ids = {}
    for r in _jsonl(Path(transcript)):
        m = r.get("message") or {}
        content = m.get("content") if isinstance(m, dict) else None
        if r.get("type") == "assistant" and isinstance(content, list):
            for b in content:
                if not isinstance(b, dict) or b.get("type") != "tool_use":
                    continue
                inp = b.get("input") or {}
                if b.get("name") in ("Agent", "Task"):
                    agent_ids[b.get("id")] = inp.get("subagent_type") or "general-purpose"
                    ev["agents"].append({"type": inp.get("subagent_type") or "general-purpose",
                                         "description": str(inp.get("description") or "")[:120],
                                         "background": bool(inp.get("run_in_background"))})
                elif b.get("name") in ("Write", "Edit") and inp.get("file_path"):
                    fp = os.path.normcase(os.path.abspath(str(inp["file_path"])))
                    (ev["in_tree_writes"] if wd and fp.startswith(wd) else ev["off_tree_writes"]).append(
                        str(inp["file_path"]))
        elif r.get("type") == "user":
            text = _text_of(content)
            hit = _HANDBACK in text
            if not hit and isinstance(content, list):
                hit = any(isinstance(b, dict) and b.get("type") == "tool_result"
                          and b.get("tool_use_id") in agent_ids for b in content)
            if hit and len(text) > 200:
                ev["handbacks"].append(text[:40_000])
    sub = Path(transcript).with_suffix("") / "subagents"
    if sub.is_dir():
        for p in sorted(sub.glob("agent-*.jsonl")):
            for r in _jsonl(p):
                m = r.get("message") or {}
                c = m.get("content") if isinstance(m, dict) else None
                if r.get("type") == "assistant" and isinstance(c, list):
                    for b in c:
                        if isinstance(b, dict) and b.get("type") == "tool_use":
                            ev["subagent_calls"] += 1
                            fp_ = (b.get("input") or {}).get("file_path")
                            if b.get("name") in ("Write", "Edit") and fp_:
                                full = os.path.normcase(os.path.abspath(str(fp_)))
                                (ev["in_tree_writes"] if wd and full.startswith(wd)
                                 else ev["off_tree_writes"]).append(str(fp_))
    return ev


# --------------------------------------------------------------------------- progress
def path_class(path: str) -> str | None:
    p = path.replace("\\", "/").lstrip("./")
    if any(rx.match(p) for rx in HOOK_OWNED):
        return None
    name = p.rsplit("/", 1)[-1]
    if p.startswith(".planning/"):
        return PLAN
    if "/tests/" in f"/{p}" or name.startswith("test_") or name.endswith((".test.js", "_test.py")):
        return PROOF
    if p.startswith(("memory/", "vault/", "docs/")) or name.endswith(".md"):
        return KNOWLEDGE
    if p.startswith((".github/", "hooks/", "scripts/")):
        return INFRA
    return PRODUCT


def classify_progress(delta_paths, evidence: dict, required_missing: bool) -> dict:
    """Semantic progress, not commit count (law 10). `delta_paths` = what changed in the tree since the
    attempt began (porcelain + commits); off-tree evidence counts too: a hand-back that carries design for
    the missing required artifact is PLAN progress even with zero tree delta."""
    classes = sorted({c for c in (path_class(p) for p in delta_paths or []) if c})
    if any(len(h) > 1500 for h in evidence.get("handbacks") or []) and PLAN not in classes:
        classes = sorted(classes + [PLAN])
    if not classes:
        cls = ZERO if evidence.get("measured") else UNKNOWN
    elif len(classes) == 1:
        cls = classes[0]
    else:
        cls = MIXED
    return {"class": cls, "classes": classes, "required_artifact_missing": bool(required_missing),
            "product": PRODUCT in classes}


# --------------------------------------------------------------------------- failure
def classify_failure(hold_reason: str, evidence: dict, progress: dict, strategy: str, fenced) -> str:
    if strategy in set(fenced or ()):
        return REPEATED_STRATEGY
    kinds = [a["type"] for a in evidence.get("agents") or []]
    if kinds and any("plan" in k.lower() for k in kinds) and progress.get("required_artifact_missing"):
        return PLANNER_TOPOLOGY_FAILURE
    if kinds and not progress.get("product"):
        return SUBAGENT_NEGATIVE_EVC
    reason = str(hold_reason or "")
    if "since the work tree last changed" in reason:
        return EXECUTOR_STALL
    if "x estimate" in reason:
        return EXECUTOR_OVERRUN
    return UNCLASSIFIED


# --------------------------------------------------------------------------- residual (GSD workstream)
def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


_PHASE_RES = (re.compile(r'^current_phase:\s*"?(\d+(?:\.\d+)?)', re.MULTILINE),     # frontmatter (older GSD)
              re.compile(r"^\**Current Phase:?\**:?\s*(\d+(?:\.\d+)?)", re.MULTILINE),  # labelled body
              re.compile(r"^Phase:\s*(\d+(?:\.\d+)?)\s+of\s+\d+", re.MULTILINE))      # GSD 1.14 roadmapper body


def _phase_glob(num: str) -> str:
    whole, _, frac = str(num).partition(".")
    return f"{int(whole):02d}{'.' + frac if frac else ''}-*"


def _research_required(base: Path) -> bool:
    try:
        cfg = json.loads(_read(base / "config.json") or "{}")
    except ValueError:
        return False
    wf = cfg.get("workflow") if isinstance(cfg.get("workflow"), dict) else {}
    return bool(wf.get("research", cfg.get("research", False)))


def gsd_unit(work_dir: str, workstream: str | None, manager=None) -> dict:
    """The phase the mission is on, in this order: STATE.md `current_phase:` frontmatter (GSD's own field,
    when its state tooling wrote it); else GSD itself (`init.manager`, the relay's reader -- only when it
    sees both ROADMAP.md and STATE.md, as gsd_status requires); else the STATE.md body (`Current Phase:` or
    the 1.14 roadmapper's `Phase: N of M`). Unreadable = {} (residual UNKNOWN). Measured 2026-10-15
    (m-4e31db7aca3f): only the frontmatter was read, which a 1.14 roadmapper STATE.md never carries, so
    every recovery of that project was "unreadable"."""
    base = Path(work_dir) / ".planning" / (f"workstreams/{workstream}" if workstream else "")
    roadmap = _read(base / "ROADMAP.md")
    state = _read(base / "STATE.md")
    name = None
    fm = _PHASE_RES[0].search(state)
    data = None
    if not fm:                         # the frontmatter answers alone: no node call (review LOW-4)
        try:
            if manager is None:
                import gsd_long_run as lr
                manager = lr.gsd_manager
            data, _why = manager(work_dir, workstream=workstream)
        except Exception:  # noqa: BLE001 -- GSD unreachable: the file readings answer
            data = None
    if not (data and data.get("roadmap_exists") and data.get("state_exists")):
        data = None
    phases = (data or {}).get("phases") or []
    if fm:
        num = fm.group(1).lstrip("0") or "0"
    elif phases:
        cur = next((ph for ph in phases if not ph.get("phase_complete")), None)
        if cur is None:
            return {}
        num, name = str(cur.get("number")), cur.get("name")
    else:
        m = next((rx.search(state) for rx in _PHASE_RES[1:] if rx.search(state)), None)
        if not m:
            return {}
        num = m.group(1)
    gsd = next((ph for ph in phases if str(ph.get("number")) == str(num)), None)
    whole = int(str(num).split(".")[0])
    sec = re.search(rf"^#+ Phase {re.escape(str(num))}:\s*(.+?)$(.*?)(?=^#+ Phase |\Z)", roadmap, re.MULTILINE | re.DOTALL)
    name = name or (sec.group(1).strip() if sec else f"Phase {num}")
    criteria = re.findall(r"^\s*\d+\.\s+(.+)$", sec.group(2), re.MULTILINE) if sec else []
    pdir = next((d for d in sorted((base / "phases").glob(_phase_glob(num))) if d.is_dir()), None)
    plans = sorted(p.name for p in pdir.glob("*-PLAN.md")) if pdir else []
    summaries = {p.name.replace("-SUMMARY.md", "") for p in pdir.glob("*-SUMMARY.md")} if pdir else set()
    has = lambda suffix: bool(pdir and any(pdir.glob(f"*{suffix}")))  # noqa: E731
    total = len(re.findall(r"^#+ Phase \d+(?:\.\d+)?:", roadmap, re.MULTILINE))
    return {"phase": whole if "." not in str(num) else num, "name": name, "criteria": criteria,
            "dir": str(pdir) if pdir else None, "plans": plans,
            "executed": sorted(p for p in plans if p.replace("-PLAN.md", "") in summaries),
            "total_phases": int((data or {}).get("phase_count") or total),
            "has_context": bool(gsd.get("has_context")) if gsd else has("-CONTEXT.md"),
            "has_research": bool(gsd.get("has_research")) if gsd else has("-RESEARCH.md"),
            "research_required": _research_required(base), "source": "gsd" if gsd else "state.md",
            "unit": f"{workstream or 'root'}/phase-{_phase_glob(num)[:-2]}"}


def compile_residual(unit: dict, capital_paths) -> list[dict]:
    """Exact remaining obligations of the unit, after subtracting what exists. Each item names its proof."""
    if not unit:
        return []
    items = []
    if not unit["plans"] and unit.get("research_required") and not unit.get("has_research"):
        items.append({"do": f"Research Phase {unit['phase']} ({unit['name']}) and commit its RESEARCH.md"
                            + (" -- the CONTEXT.md is already committed: read it, do not redo the discussion"
                               if unit.get("has_context") else ""),
                      "proof": "the phase's *-RESEARCH.md exists and is committed", "kind": PLAN})
    if not unit["plans"]:
        items.append({"do": f"Write the plan files for Phase {unit['phase']} ({unit['name']}) in the main "
                            "thread, from the capitalized design; do not re-derive it.",
                      "proof": "the *-PLAN.md files exist and are committed", "kind": PLAN})
        items.append({"do": "Execute each plan you wrote, in order, and write its SUMMARY; commit after each plan",
                      "proof": "each plan's <verify> commands pass; every SUMMARY committed", "kind": PRODUCT})
    for p in unit["plans"]:
        if p not in unit["executed"]:
            items.append({"do": f"Execute {p} and write its SUMMARY", "proof": "its <verify> commands pass; "
                          "SUMMARY committed", "kind": PRODUCT})
    items.append({"do": f"Prove every success criterion of Phase {unit['phase']}, mark the phase complete in "
                        "ROADMAP/STATE, commit", "proof": "; ".join(unit["criteria"])[:900] or "phase gates",
                  "kind": PROOF})
    if capital_paths:
        items.insert(0, {"do": "Commit the uncommitted capital first: " + ", ".join(capital_paths),
                         "proof": "git status shows them committed", "kind": PLAN})
    return items


# --------------------------------------------------------------------------- topology
def recompile_topology(failure: str, unit_id: str, goal: str, old_agents, fenced) -> dict | None:
    """A materially different successor (law 12), or None when none is known: that is an Owner boundary,
    never a guess. Deflation order: planner/agents -> main thread; stall -> smaller decomposition."""
    fenced = set(fenced or ())
    if failure in (PLANNER_TOPOLOGY_FAILURE, SUBAGENT_NEGATIVE_EVC):
        deny = sorted({a for a in old_agents if a and a not in READ_ONLY_AGENTS} | {"gsd-planner"})
        cand = {"mode": "EXECUTION", "topology": MAIN_THREAD, "decomposition": "residual-in-order",
                "deny_agent_types": deny,
                "why": f"{failure}: the subagent spent without its artifact; the design exists, so the "
                       "residual is clear work for one main-thread executor"}
    elif failure in (EXECUTOR_STALL, EXECUTOR_OVERRUN):
        cand = {"mode": "EXECUTION", "topology": MAIN_THREAD, "decomposition": "first-item-then-commit",
                "deny_agent_types": ["gsd-planner"],
                "why": f"{failure}: the same executor stalled on the whole unit; the successor takes one "
                       "residual item at a time and commits after each"}
    else:
        return None
    cand["strategy"] = strategy_identity(goal, unit_id, cand["topology"], (), cand["decomposition"])
    if cand["strategy"] in fenced:
        return None
    return cand


# --------------------------------------------------------------------------- lease
def price_lease(spent: int | None, ceiling: int | None, residual) -> dict:
    """Bounded successor lease inside the remaining authority (`ceiling` = the hard processed-token ceiling
    the mission may reach: Owner authority when declared, else the breaker's own ratio x estimate).
    Never hands over everything left: RESERVE_FRACTION stays for recovery and closeout."""
    if spent is None or not ceiling:
        return {"ok": False, "why": "spend or authority unmeasured: a lease cannot be priced (absent is not zero)"}
    remaining = int(ceiling) - int(spent)
    usable = int(remaining * (1 - RESERVE_FRACTION))
    price = max(MIN_LEASE_TOKENS, PRICE_PER_ITEM * max(1, len(residual or [])))
    lease = min(price, usable)
    if lease < MIN_LEASE_TOKENS:
        return {"ok": False, "why": f"authority exhausted: {remaining:,} left of {int(ceiling):,}, "
                                    f"{usable:,} after reserve < minimum lease {MIN_LEASE_TOKENS:,}",
                "remaining": remaining}
    return {"ok": True, "lease": lease, "price": price, "remaining": remaining,
            "envelope": {"target": int(lease / LEASE_STOP_OVER_TARGET), "warn": int(lease / 1.15),
                         "stop": int(lease)}}


def route_for(envelope: dict, floors: dict, margin: float = 0.20) -> dict:
    """One top-level worker, as many calls as the envelope target holds at the measured floor."""
    top = (floors.get("profiles") or {}).get("top-level-worker") or {}
    floor = int(top.get("floor") or 110_835)
    packet = 3000   # the packet rides every call (route_admission: calls x (floor + packet))
    calls = max(int(floors.get("default_min_calls") or 3), int(envelope["target"] // ((1 + margin) * (floor + packet))))
    return {"envelope": {**envelope, "calls": calls},
            "workers": [{"name": "amr-successor", "profile": "top-level-worker", "calls": calls, "packet": packet}],
            "effect": "BOUNDED_COGNITION"}


# --------------------------------------------------------------------------- liveness
def goal_liveness(rec: dict) -> str:
    """Every open mission maps to exactly one valid continuation; LIVENESS_INCIDENT means none does."""
    st = rec.get("state")
    if st in ("COMPLETED", "HALTED", "ABANDONED"):
        return "TERMINAL"
    hold = rec.get("owner_hold")
    if not hold:
        return "ACTIVE" if st in ("RUNNING", "LAUNCHING", "HANDOFF", "PREPARED") else "WAITING"
    rs = (hold.get("recovery") or {}).get("state")
    if rs == RECOVERY_EXHAUSTED:
        return "LIVENESS_INCIDENT"       # AMCR: a failed recovery is surfaced, never parked on the Owner
    if rs == RECOVERY_FAILED:
        return "RECOVERING"
    if rs in (OWNER_BOUNDARY, NOT_APPLICABLE):
        return "OWNER_BOUNDARY"
    if rs == DURABLE_WAIT:
        return "DURABLE_WAIT"
    is_cost = hold.get("kind") == "cost" or str(hold.get("reason") or "").startswith("cost breaker")
    if not is_cost:
        return "OWNER_BOUNDARY"          # an Owner park is an Owner boundary by definition
    if mode() == "off":
        return "LIVENESS_INCIDENT"       # recoverable hold with recovery disabled: nothing will move it
    return "RECOVERING"


# --------------------------------------------------------------------------- WAIT_ON_RESOURCE (ccr-v5 phase 3)
# A DURABLE_WAIT row for "this unit needs a resource another writer holds dirty". Pure and model-free like the
# rest of this module: the row schema is code, the wake decision is a total function of (row, evidence, now).
# Reading/writing rows and probing evidence is gsd_mission's job. UNKNOWN is never zero: an unmeasured
# resource is blocked, an UNKNOWN writer is never abandoned, and an uncounted remainder is never landable.
WAIT_ON_RESOURCE = "WAIT_ON_RESOURCE"
WAIT_STATES = ("OPEN", "RESUMING", "DONE", "DONE_CARVED_OUT", "TIMED_OUT", "ESCALATED", "CANCELLED", "QUARANTINED")
WRITER_VERDICTS = ("LIVE", "DEAD", "UNKNOWN", "AMBIGUOUS")
WAKE_EVENTS = ("COMMIT", "LEASE_RELEASE", "CLEARED", "WRITER_DEAD", "TIMEOUT")
WAKE_ACTIONS = ("RESUME", "WAIT", "CARVE_OUT", "ESCALATE")
RESUME_KINDS = ("land_worktree",)          # the only action a row may ask for; no free-form command field
MIN_EPOCH = 1_000_000_000                  # timeout_at is an absolute epoch, never a relative duration


def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _is_str(x) -> bool:
    return isinstance(x, str) and bool(x.strip())


def _rel_posix_problem(p) -> str | None:
    """None when p is a relative posix path inside the repo; otherwise why not."""
    if not _is_str(p):
        return "not a non-empty string"
    if p.startswith("/") or p.startswith("\\") or "\\" in p:
        return "absolute or backslash path"
    if re.match(r"^[A-Za-z]:", p):
        return "drive letter"
    if any(seg == ".." for seg in p.split("/")):
        return "parent segment"
    return None


def validate_wait_row(row) -> list[str]:
    """Problems with a WAIT_ON_RESOURCE row; an empty list means valid. Never raises on bad input."""
    if not isinstance(row, dict):
        return ["row: not an object"]
    out: list[str] = []
    for k in ("wait_id", "goal", "wu", "live_head_at_open"):
        if k not in row:
            out.append(f"{k}: missing")
        elif not _is_str(row[k]):
            out.append(f"{k}: not a non-empty string")
    if row.get("kind") != WAIT_ON_RESOURCE:
        out.append(f"kind: must be {WAIT_ON_RESOURCE}")
    if row.get("state") not in WAIT_STATES:
        out.append("state: not in WAIT_STATES")
    opened, tmo = row.get("opened_at"), row.get("timeout_at")
    if "opened_at" not in row or not _is_num(opened):
        out.append("opened_at: missing or not a number")
    if "timeout_at" not in row:
        out.append("timeout_at: missing")
    elif not _is_num(tmo) or tmo <= MIN_EPOCH:
        out.append("timeout_at: must be an absolute epoch time")
    elif _is_num(opened) and tmo <= opened:
        out.append("timeout_at: must be after opened_at")
    res = row.get("resources")
    if "resources" not in row:
        out.append("resources: missing")
    elif not isinstance(res, list) or not res:
        out.append("resources: must be a non-empty list")
    else:
        for i, r in enumerate(res):
            if not isinstance(r, dict):
                out.append(f"resources[{i}]: not an object")
                continue
            why = _rel_posix_problem(r.get("path"))
            if why:
                out.append(f"resources[{i}].path: {why}")
            w = r.get("writer")
            if not isinstance(w, dict) or w.get("verdict") not in WRITER_VERDICTS:
                out.append(f"resources[{i}].writer: verdict not in WRITER_VERDICTS")
    ev = row.get("expected_event")
    if "expected_event" not in row:
        out.append("expected_event: missing")
    elif not isinstance(ev, list) or not ev or any(e not in WAKE_EVENTS for e in ev):
        out.append("expected_event: must be a non-empty list drawn from WAKE_EVENTS")
    ra = row.get("resume_action")
    if "resume_action" not in row:
        out.append("resume_action: missing")
    elif not isinstance(ra, dict):
        out.append("resume_action: not an object")
    else:
        if ra.get("kind") not in RESUME_KINDS:
            out.append("resume_action.kind: not in the allowlist")
        if ra.get("strategy") != "merge":
            out.append("resume_action.strategy: must be merge")
        for k in ("worktree", "live", "branch"):
            if not _is_str(ra.get(k)):
                out.append(f"resume_action.{k}: not a non-empty string")
        if "union" in ra:
            un = ra["union"]
            if not isinstance(un, list):
                out.append("resume_action.union: must be a list")
            else:
                for i, p in enumerate(un):
                    why = _rel_posix_problem(p)
                    if why:
                        out.append(f"resume_action.union[{i}]: {why}")
    va = row.get("validation")
    if "validation" not in row:
        out.append("validation: missing")
    elif not isinstance(va, dict):
        out.append("validation: not an object")
    else:
        tests = va.get("tests")
        if not isinstance(tests, list) or not tests or not all(_is_str(t) for t in tests):
            out.append("validation.tests: must be a non-empty list of non-empty strings")
        if va.get("rollback") != "any_red":
            out.append("validation.rollback: must be any_red")
        if not isinstance(va.get("baseline_red", []), list):
            out.append("validation.baseline_red: must be a list")
    return out


def _decision(action: str, event, reason: str, cleared=(), blocked=(), carve_out=()) -> dict:
    return {"action": action, "event": event, "reason": reason, "cleared": list(cleared),
            "blocked": list(blocked), "carve_out": list(carve_out)}


def wait_decision(row, evidence, now) -> dict:
    """Pure wake decision for a WAIT_ON_RESOURCE row. Total: never raises, never RESUMEs on doubt.

    evidence[path] = {dirty: True|False|None, committed_since_open: True|False|None,
    lease: None | {free: bool, state, holder}, writer: WRITER_VERDICTS value}; evidence["other_paths"] is the
    count of the landing's other paths (an int, or None when uncounted: never assumed landable).
    """
    probs = validate_wait_row(row)
    if probs or not _is_num(now):
        return _decision("ESCALATE", None, "invalid row or clock: " + ("; ".join(probs[:3]) or "now is not a number"))
    ev = evidence if isinstance(evidence, dict) else {}
    other = ev.get("other_paths")
    paths = [r["path"] for r in row["resources"]]
    cleared, blocked, dead_ok = [], [], []
    committed = released = False
    for p in paths:
        e = ev.get(p)
        e = e if isinstance(e, dict) else None
        if e is None:
            blocked.append(p)                     # no entry: unmeasured, never clear
            dead_ok.append(False)
            continue
        lease = e.get("lease")
        lease_free = lease is None or (isinstance(lease, dict) and lease.get("free") is True)
        dirty = e.get("dirty")
        if dirty is False and lease_free:
            cleared.append(p)
            committed = committed or e.get("committed_since_open") is True
            released = released or (isinstance(lease, dict) and lease.get("state") == "RELEASED")
        else:
            blocked.append(p)
            dead_ok.append(e.get("writer") == "DEAD" and dirty is True and lease_free)
    if not blocked:
        event = "COMMIT" if committed else ("LEASE_RELEASE" if released else "CLEARED")
        return _decision("RESUME", event, "every resource is measured clean and unleased", cleared=cleared)
    if all(dead_ok):
        return _decision("CARVE_OUT", "WRITER_DEAD", "every blocked resource has a DEAD writer", cleared=cleared,
                         blocked=blocked, carve_out=blocked)
    if now >= row["timeout_at"]:
        if isinstance(other, int) and not isinstance(other, bool) and other > 0:
            return _decision("CARVE_OUT", "TIMEOUT", "timeout reached with a counted remainder of landable paths",
                             cleared=cleared, blocked=blocked, carve_out=blocked)
        return _decision("ESCALATE", "TIMEOUT", "timeout reached and the rest of the landing is zero or uncounted",
                         cleared=cleared, blocked=blocked)
    return _decision("WAIT", None, "blocked resources before the timeout", cleared=cleared, blocked=blocked)


# --------------------------------------------------------------------------- ContextImage
def render_packet(*, mission_id: str, goal: str, unit: dict, residual, topology: dict, failure: str,
                  progress: dict, failed_strategy: str, delta_path: str | None, lease: dict,
                  receipt: str, work_dir: str, workstream: str | None) -> str:
    """The successor's whole context: goal, residual, certified delta (by reference), fence, budget.
    No transcript replay (law 14); detail is paged in from the referenced files only if needed."""
    lines = [
        f"# AMR successor work unit -- mission {mission_id}",
        "",
        f"Goal: {goal}",
        f"Work tree: {work_dir}" + (f" (GSD workstream {workstream})" if workstream else ""),
        f"Unit: Phase {unit.get('phase')} -- {unit.get('name')}",
        "",
        "## Why you exist",
        f"The previous executor was stopped by the cost breaker. Failure class {failure}; progress class "
        f"{progress.get('class')} ({', '.join(progress.get('classes') or []) or 'none'}). "
        f"Failed strategy {failed_strategy} is FENCED: {topology['why']}.",
        f"Your strategy {topology['strategy']}: mode {topology['mode']}, topology {topology['topology']}, "
        f"decomposition {topology['decomposition']}.",
        "",
        "## Rules",
        "- Work in the main thread. Do NOT spawn " + ", ".join(topology["deny_agent_types"])
        + " (the spawn hook refuses them for this mission). Read-only Explore is allowed only to find a file.",
        "- Do not re-derive the capitalized design: read it once, write from it.",
        "- Commit after each residual item with the repository's commit tool; a dirty tree at the end is a failure.",
        "- Never ask the Owner. Decisions reserved to the Owner go to the workstream STATE.md as "
        "OWNER DECISION NEEDED; continue with other items.",
        "",
        "## Capitalized semantic delta (already paid for)",
        f"- {delta_path}" if delta_path else "- none recorded",
        "",
        "## Residual, in order",
        *[f"{i}. {it['do']}  -- proof: {it['proof']}" for i, it in enumerate(residual, 1)],
        "",
        "## Budget",
        f"Lease {lease['lease']:,} processed tokens (stop). The session guard enforces it per call.",
        "",
        "## Done",
        f"When every residual item is proven, write the receipt {receipt} with a line `Status: DONE` and the "
        "commit hashes. If you must stop early, write `Status: PARTIAL` with the next exact item.",
    ]
    return "\n".join(lines) + "\n"


def pgo_append(row: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts": time.time(), **row}, ensure_ascii=False) + "\n")


def lease_estimate(spent: int, lease: int, ratio: float) -> int:
    """The breaker trips at ratio x estimate: the estimate that makes spent + lease that ceiling."""
    return math.ceil((int(spent) + int(lease)) / float(ratio))
