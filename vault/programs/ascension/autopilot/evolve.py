"""EVO: strategy evolution for the Ascension autopilot (Owner "y" 2026-11-12 to vault/programs/ascension/EVO-PLAN.md).

What it adds to autopilot.lane_tick, nothing else:
- an outcome class INSTRUMENT_FAIL (a verified failed positive control) that is never a negative result: it never
  increments blank / no_conversion and opens INSTRUMENT REPAIR (at most MAX_REPAIR attempts per instrument);
- the stagnation -> research transition. The existing INFO_PARK / NO_CONVERSION_PARK triggers no longer park on their
  own: they ask the Mission Runtime's pivot_decision (tools/gsd_mission.py, reused, not copied) whether a pivot is
  allowed. If so, the lane enters RESEARCH with a lever of a DIFFERENT mechanism family, chosen deterministically from
  levers.json and ranked by a MethodGraph (recon-general, reused) learned from verified outcomes. Research has its own
  budget and stop rule;
- continuity: a lane parked on a budget reason resumes when the ledger admits again (an Owner release), and a
  checkpoint that lives on a worktree branch is fast-forwarded into the product (only fast-forward, only from a clean
  tree) or the lane parks naming the branch.
Kill switch: file EVO_OFF in the autopilot home -> the pre-EVO behaviour everywhere."""
from __future__ import annotations

import json
import os
import subprocess
import sys

MAX_REPAIR = 2               # attempts per instrument; the next failure parks the lane with the instrument named
RESEARCH_FAIL_STOP = 2       # consecutive research generations without verified INFORMATION/CAPABILITY park the lane
RESEARCH_GEN_CAP = 10_000_000
RESEARCH_LANE_CAP = 40_000_000
RESEARCH_WORDS = ("rival", "positive control", "decision rule")
REPAIR_WORDS = ("positive control", "thresholds unchanged")
RECON = os.environ.get("AP_RECON", "/home/kobii/missions/recon-general")


def enabled(home) -> bool:
    return not (home / "EVO_OFF").exists()


# ---------------------------------------------------------------- reused machinery
def _method_graph():
    if RECON not in sys.path:
        sys.path.insert(0, RECON)
    from modules.reconstruction_factory.method_graph import MethodGraph  # noqa: PLC0415  (recon-general, reused)
    return MethodGraph


def _pivot_decision():
    pp_tools = os.path.join(os.environ.get("AP_PP", "/home/kobii/.claude/skills/claude-power-pack"), "tools")
    if pp_tools not in sys.path:
        sys.path.insert(0, pp_tools)
    import gsd_mission  # noqa: PLC0415  (the Mission Runtime pivot rules, reused)
    return gsd_mission.pivot_decision


def load_graph(home):
    mg = _method_graph()
    p = home / "method_graph.json"
    return mg.from_json(p.read_text()) if p.exists() else mg()


def save_graph(home, g) -> None:
    tmp = home / "method_graph.json.tmp"
    tmp.write_text(g.to_json())
    tmp.replace(home / "method_graph.json")


def load_levers(home) -> dict:
    p = home / "levers.json"
    return json.loads(p.read_text()) if p.exists() else {}


def lever_by_id(levers: dict, lane: str, lid):
    return next((x for x in levers.get(lane, []) if x["id"] == lid), None)


# ---------------------------------------------------------------- outcome taxonomy
def verify_instrument_failures(v: dict, product: str, base, ap) -> list[str]:
    """Instruments whose failure is anchored in this generation: the judge names a data file and the commit that wrote it
    inside base..HEAD, and that file (as written by that commit) says INSTRUMENT_FAIL. A claim that fails a check is dropped."""
    out = []
    for f in v.get("instrument_failures") or []:
        if not isinstance(f, dict):
            continue
        name, path, commit = str(f.get("instrument") or ""), str(f.get("file") or ""), str(f.get("commit") or "")
        if not (name and path and commit and base):
            continue
        if not (ap.in_window(product, base, commit) and path in ap._changed(product, commit) and ap.DATA.search(path)):
            continue
        body = ap._git(product, "show", f"{ap._sha(product, commit)}:{path}")[1]
        if "INSTRUMENT_FAIL" in body:
            out.append(name)
    return sorted(set(out))


def classify(cls: str, instruments: list[str]) -> str:
    """The autopilot's class, with INSTRUMENT_FAIL split out of NONE: a generation whose only outcome is a verified
    instrument failure did not test its hypothesis, so it is not 'no progress' and not a negative result."""
    return "INSTRUMENT_FAIL" if cls == "NONE" and instruments else cls


# ---------------------------------------------------------------- selection
def _requires_met(lever: dict, product: str) -> bool:
    return all(os.path.exists(os.path.join(product, r)) for r in lever.get("requires", []))


def select(levers: dict, lane: str, ls: dict, product: str, graph, family_not=None, kind=None):
    """A lever that is open (not retired by levers.json or by this lane's history), whose preconditions exist in the
    product, whose mechanism family differs from `family_not` (materially different), and of `kind` when given
    ('repair' for an instrument repair). Ranked by the MethodGraph prior on its blocker classes, then cost, then id."""
    retired = set(ls.get("retired") or [])
    cands = []
    for x in levers.get(lane, []):
        if x.get("status") != "open" or x["id"] in retired or not _requires_met(x, product):
            continue
        if family_not and x.get("family") == family_not:
            continue
        if (x.get("kind") == "repair") != (kind == "repair"):  # repair levers only repair; research never picks one
            continue
        pri = max([graph.prior(b).get(x["id"], 0.0) for b in x.get("blockers", [])] or [0.0])
        cands.append((-pri, float(x.get("cost", 99)), x["id"], x))
    cands.sort(key=lambda t: t[:3])
    return cands[0][3] if cands else None


def directive(lever: dict, mode: str, instrument: str | None = None) -> str:
    if mode == "REPAIR":
        return (f"EVO MODE REPAIR (instrument {instrument}, attempt counted by the autopilot). The previous generation's "
                f"positive control failed, so its hypothesis is untested, not refuted. Selected lever {lever['id']}: "
                f"{lever.get('what', '')} Pre-register a repaired instrument whose positive control is demonstrated "
                "adequate AT FREEZE TIME, keep every decision threshold unchanged (write 'thresholds unchanged'), then "
                "re-run the same hypothesis. Name the lever id in Phase 1.")
    return (f"EVO MODE RESEARCH (method transition decided by the autopilot after a plateau). Selected lever {lever['id']} "
            f"(family {lever.get('family')}, blockers {', '.join(lever.get('blockers', []))}): {lever.get('what', '')} "
            "Phase 1 must name the lever id and pre-register a DISCRIMINATING test: two rival hypotheses with different "
            "predicted outcomes (write 'rival'), a positive control (write 'positive control') and a decision rule "
            f"(write 'decision rule'), frozen in a commit before any run. Phase caps sum <= {RESEARCH_GEN_CAP // 1_000_000}M. "
            "A certificate, if the lever yields one, still goes only through the unchanged certify.decide.")


def packet_problems(mode: str, lever_id, phases: list[str], caps: int, ls: dict) -> list[str]:
    """Deterministic refusal of a research/repair packet that does not carry its discriminating test or budget."""
    if mode not in ("RESEARCH", "REPAIR"):
        return []
    text = " ".join(phases).lower()
    bad = []
    if lever_id and lever_id.lower() not in text:
        bad.append(f"EVO {mode}: the packet does not name the selected lever {lever_id}")
    for w in (RESEARCH_WORDS if mode == "RESEARCH" else REPAIR_WORDS):
        if w not in text:
            bad.append(f"EVO {mode}: no '{w}' in the phases")
    if mode == "RESEARCH":
        if caps > RESEARCH_GEN_CAP:
            bad.append(f"EVO RESEARCH: caps {caps:,} > research generation cap {RESEARCH_GEN_CAP:,}")
        if int(ls.get("research_spent") or 0) + caps > RESEARCH_LANE_CAP:
            bad.append(f"EVO RESEARCH: lane research budget {RESEARCH_LANE_CAP:,} would be exceeded")
    return bad


# ---------------------------------------------------------------- the decision after a judged generation
def _pivot(ls: dict, family: str, evidence_delta: bool, failure_class: str, residual: str) -> dict:
    left = max(0, RESEARCH_LANE_CAP - int(ls.get("research_spent") or 0))
    rec = {"pivot_streak": int(ls.get("pivot_streak") or 0), "pivot_history": list(ls.get("pivot_history") or []),
           "authority_tokens": left, "cost_mark": {"tokens": 0}}
    hold = {"checkpoint": "METHOD_PIVOT_REQUIRED", "reason": f"method plateau on {family}", "residual": residual,
            "gain": False, "receipt": {"method_class": family, "evidence_delta": evidence_delta,
                                       "failure_class": failure_class, "authority_objects": [], "methods_falsified": []}}
    return _pivot_decision()(rec, hold)


def after_judgment(ls: dict, cls: str, instruments: list[str], levers: dict, lane: str, product: str, graph,
                   triggers: tuple[int, int, int]) -> dict:
    """-> {"action": continue|stop|park|research|repair, "why", "lever"?, "directive"?}. Mutates the lane counters.
    triggers = (BLANK_STOP, INFO_PARK, NO_CONVERSION_PARK) of the autopilot."""
    blank_stop, info_park, noconv_park = triggers
    cur = lever_by_id(levers, lane, ls.get("lever"))
    family = (cur or {}).get("family") or "UNREGISTERED"
    # learning: a verified conversion teaches the graph; repeated zero evidence on a lever retires it
    if cur:
        if cls in ("CERT", "CAPABILITY"):
            for b in cur.get("blockers", []):
                graph.learn(b, [cur["id"]], solved=True)
        hist = ls.setdefault("lever_history", [])
        hist.append({"lever": cur["id"], "cls": cls})
        del hist[:-20]
        zero = [h for h in hist if h["lever"] == cur["id"] and h["cls"] == "NONE"]
        if len(zero) >= 2 and cur["id"] not in ls.setdefault("retired", []):
            ls["retired"].append(cur["id"])
    for name in instruments:
        rep = ls.setdefault("repair", {})
        rep[name] = int(rep.get(name, 0)) + 1
        if rep[name] > MAX_REPAIR:
            return {"action": "park", "why": f"instrument {name} failed its positive control {rep[name]} times "
                                             f"(repair cap {MAX_REPAIR}); a new instrument needs a new idea"}
    if cls == "CERT":
        ls.update(mode="EXPLOIT", blank=0, info_streak=0, no_conversion=0, research_fail=0, pivot_streak=0)
        return {"action": "continue", "why": "certificates: exploit"}
    if cls == "INSTRUMENT_FAIL":
        name = instruments[0]
        lever = select(levers, lane, ls, product, graph, kind="repair") if lane else None
        if lever is None:
            return {"action": "park", "why": f"instrument {name} failed and no repair lever is registered for {lane}"}
        ls.update(mode="REPAIR", repair_instrument=name)
        return {"action": "repair", "lever": lever, "why": f"instrument {name} failed: repair, not a negative result",
                "directive": directive(lever, "REPAIR", name)}
    conv = cls == "CAPABILITY"
    ls["blank"] = ls.get("blank", 0) + 1 if cls == "NONE" else 0
    ls["info_streak"] = ls.get("info_streak", 0) + 1 if cls == "INFORMATION" else 0
    ls["no_conversion"] = 0 if conv else ls.get("no_conversion", 0) + 1
    if ls.get("mode") == "RESEARCH":
        ls["research_fail"] = 0 if cls in ("INFORMATION", "CAPABILITY") else int(ls.get("research_fail") or 0) + 1
        if ls["research_fail"] >= RESEARCH_FAIL_STOP:
            return {"action": "park", "why": f"{RESEARCH_FAIL_STOP} research generations without verified "
                                             "INFORMATION or CAPABILITY: research stop rule"}
    if ls["blank"] >= blank_stop:
        return {"action": "stop", "why": f"{blank_stop} consecutive generations with no verified progress of any class"}
    if ls["info_streak"] >= info_park or ls["no_conversion"] >= noconv_park:
        return plateau(ls, levers, lane, product, graph, family, cls in ("INFORMATION", "CAPABILITY"))
    if ls.get("mode") == "REPAIR":
        ls["mode"] = "EXPLOIT"
    return {"action": "continue", "why": f"{cls}: continue in {ls.get('mode') or 'EXPLOIT'}"}


def plateau(ls: dict, levers: dict, lane: str, product: str, graph, family: str, evidence_delta: bool) -> dict:
    """The protection rule fired. Ask the Mission Runtime pivot rule; on 'pivot' enter RESEARCH with a lever of another family."""
    d = _pivot(ls, family, evidence_delta, "METHOD_PLATEAU", f"lane {lane} plateau on {family}")
    if d.get("action") != "pivot":
        return {"action": "park", "why": f"pivot rule: {d.get('why')}"}
    lever = select(levers, lane, ls, product, graph, family_not=family)
    if lever is None:
        return {"action": "park", "why": f"plateau on {family} and no open lever of another family with its "
                                         "preconditions met"}
    hist = list(ls.get("pivot_history") or [])
    hist.append({"method_class": family, "evidence_delta": bool(evidence_delta)})
    ls.update(mode="RESEARCH", pivot_streak=d.get("streak", 1), pivot_history=hist[-20:], info_streak=0, no_conversion=0,
              research_fail=0)
    return {"action": "research", "lever": lever, "why": f"plateau on {family}: research with {lever['id']} "
                                                         f"({lever.get('family')}); {d.get('why')}",
            "directive": directive(lever, "RESEARCH")}


# ---------------------------------------------------------------- continuity
def budget_resume(ls: dict, why) -> bool:
    """A lane parked on a budget reason resumes only when the ledger admits again (why is None); any other park waits."""
    return ls.get("status") == "PARKED" and ls.get("park_kind") == "budget" and why is None


def _git(cwd: str, *args) -> tuple[int, str]:
    p = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=120)
    return p.returncode, (p.stdout + p.stderr).strip()


def discover_checkpoint(product: str, checkpoint: str, dry: bool = False) -> tuple[str, str]:
    """-> (OK|FF|PARK, note). OK: the checkpoint is in the product. FF: exactly one worktree branch holds it COMMITTED,
    the product HEAD is its ancestor and the product has no tracked changes -> `merge --ff-only` was run. Otherwise PARK."""
    rel = os.path.relpath(checkpoint, product) if os.path.isabs(checkpoint) else checkpoint
    if rel.startswith("..") or os.path.exists(os.path.join(product, rel)):
        return "OK", checkpoint  # in the product, or outside it (no branch to discover): the judge reads it as before
    rc, out = _git(product, "worktree", "list", "--porcelain")
    trees, cur = [], {}
    for line in out.splitlines() + [""]:
        if not line.strip():
            if cur.get("worktree"):
                trees.append(cur)
            cur = {}
        elif " " in line:
            k, val = line.split(" ", 1)
            cur[k] = val
    hits = [t for t in trees if os.path.realpath(t["worktree"]) != os.path.realpath(product) and t.get("HEAD")
            and _git(t["worktree"], "cat-file", "-e", f"HEAD:{rel}")[0] == 0]
    if len(hits) != 1:
        return "PARK", f"CHECKPOINT_ON_BRANCH: {rel} is not in the product and is committed on {len(hits)} worktree branches"
    t = hits[0]
    if _git(product, "merge-base", "--is-ancestor", "HEAD", t["HEAD"])[0] != 0:
        return "PARK", f"CHECKPOINT_ON_BRANCH {t.get('branch', t['HEAD'])}: not a fast-forward of the product HEAD"
    if _git(product, "status", "--porcelain", "--untracked-files=no")[1]:
        return "PARK", f"CHECKPOINT_ON_BRANCH {t.get('branch', t['HEAD'])}: the product has tracked changes"
    if dry:
        return "FF", f"dry: would fast-forward to {t['HEAD'][:12]}"
    rc, out = _git(product, "merge", "--ff-only", t["HEAD"])
    if rc != 0 or not os.path.exists(os.path.join(product, rel)):
        return "PARK", f"CHECKPOINT_ON_BRANCH {t.get('branch')}: fast-forward failed: {out[-200:]}"
    return "FF", f"fast-forwarded product to {t.get('branch', '')} {t['HEAD'][:12]}"
