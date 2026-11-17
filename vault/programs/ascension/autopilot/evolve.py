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
import re
import subprocess
import sys

MAX_REPAIR = 2               # attempts per instrument; the next failure parks the lane with the instrument named
_HYP_ID = re.compile(r"^(H-[A-Za-z0-9]+)\b")
_MEASURED = re.compile(r"\s*\([^)]*\)")


def instrument_key(name: str) -> str:
    """The identity a repair is counted under. The judge's instrument names embed measurements ("... (frozen rule,
    n=2<22)"), so a repeat failure with another n was a NEW key and MAX_REPAIR never tripped (S31T -> S33T, 2026-11-12).
    A leading hypothesis id (H-T1a) is the identity; otherwise the name without parenthesised parts, case-folded
    (or the whole name case-folded when nothing is left, so "(n=2)" and "(x)" never share one empty key)."""
    s = " ".join(str(name).split())
    m = _HYP_ID.match(s)
    if m:
        return m.group(1)
    return " ".join(_MEASURED.sub("", s).split()).lower() or s.lower()


RESEARCH_FAIL_STOP = 2       # consecutive research generations without verified INFORMATION/CAPABILITY park the lane
RESEARCH_GEN_CAP = 10_000_000
RESEARCH_LANE_CAP = 100_000_000
RESEARCH_WORDS = ("rival", "positive control", "decision rule")
OWNER_RESUME = "owner_resume"  # lane-state key the Owner sets to "research" for a one-shot method transition
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


def save_levers(home, levers: dict) -> None:
    tmp = home / "levers.json.tmp"
    tmp.write_text(json.dumps(levers, indent=2))
    tmp.replace(home / "levers.json")


def lever_by_id(levers: dict, lane: str, lid):
    return next((x for x in levers.get(lane, []) if x["id"] == lid), None)


# ---------------------------------------------------------------- autonomous lever design
# Owner 2026-11-16 (pane 08cba76c, after WIIPARTY waited on him for a new lever): "deberia haberse hecho de forma
# autonoma". Standing authorization (pane f3df357a, 2026-11-14): new routes are always authorized until everything is
# reconstructed. So where the lane used to park for "no admissible lever", the autopilot designs one from the residual
# (a model call, `designer`), admits it deterministically, appends it to levers.json (origin "autopilot") and researches
# with it. Budgets stay the Owner's: the research caps, the lane envelope and the day cap still bind. Bounded: SYNTH_MAX
# designed levers in a row without a verified CAPABILITY or CERT park the lane for an Owner look.
SYNTH_MAX = 3
SYNTH_MIN_WHAT = 200
_SYNTH_ID = re.compile(r"[a-z0-9_]{4,48}")


def synth_problems(lv, levers: dict, lane: str, product: str, family, residual) -> list[str]:
    """Deterministic admission of a designed lever. Empty list = admitted."""
    if not isinstance(lv, dict) or lv.get("none"):
        return [f"designer proposed no lever: {str((lv or {}).get('none') if isinstance(lv, dict) else lv)[:200]}"]
    bad = []
    lid = str(lv.get("id") or "")
    if not _SYNTH_ID.fullmatch(lid):
        bad.append("id must be 4-48 chars of [a-z0-9_]")
    if any(x.get("id") == lid for xs in levers.values() if isinstance(xs, list) for x in xs if isinstance(x, dict)):
        bad.append(f"id {lid} already exists")
    if not lv.get("family") or lv.get("family") == family:
        bad.append(f"family must be set and differ from {family}")
    if lv.get("kind") not in (None, "research"):
        bad.append("kind must be research")
    if not lv.get("blockers"):
        bad.append("no blockers named")
    what = str(lv.get("what") or "")
    if len(what) < SYNTH_MIN_WHAT:
        bad.append(f"what shorter than {SYNTH_MIN_WHAT} chars")
    if residual and os.path.basename(str(residual)) not in what:
        bad.append(f"what does not cite the residual it answers ({os.path.basename(str(residual))})")
    for r in lv.get("requires") or []:
        if not os.path.exists(os.path.join(product, r)):
            bad.append(f"requires {r} does not exist in the product")
    return bad


def synthesize(levers: dict, lane: str, ls: dict, product: str, family, designer, residual):
    """-> (lever, None) when a designed lever is admitted (and appended to `levers`), else (None, why)."""
    if designer is None:
        return None, "no lever designer"
    streak = int(ls.get("synth_streak") or 0)
    if streak >= SYNTH_MAX:
        return None, f"{SYNTH_MAX} autopilot-designed levers in a row without a verified CAPABILITY or CERT"
    lv = designer(family)
    if not isinstance(lv, dict) or lv.get("none"):  # structural, before admission: nothing to admit or persist
        return None, f"designer proposed no lever: {str((lv or {}).get('none') if isinstance(lv, dict) else lv)[:200]}"
    bad = synth_problems(lv, levers, lane, product, family, residual)
    if bad:
        return None, "designed lever refused: " + "; ".join(bad)[:400]
    lv = dict(lv, kind="research", status="open", origin="autopilot", requires=list(lv.get("requires") or []),
              cost=lv.get("cost", 1))
    levers.setdefault(lane, []).append(lv)
    ls["synth_streak"] = streak + 1
    return lv, None


def _synth_or_park(ls, levers, lane, product, family, designer, residual, why: str, src: str) -> dict:
    lever, swhy = synthesize(levers, lane, ls, product, family, designer, residual)
    if lever is None:
        return {"action": "park", "why": f"{why} ({swhy})" if designer is not None else why}
    ls.update(mode="RESEARCH", info_streak=0, no_conversion=0, research_fail=0, repair={})
    return {"action": "research", "lever": lever, "designed": True,
            "why": f"{src}: autopilot-designed lever {lever['id']} ({lever.get('family')})",
            "directive": directive(lever, "RESEARCH")}


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


def select(levers: dict, lane: str, ls: dict, product: str, graph, family_not=None, kind=None, repairs_for=None):
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
        if kind == "repair" and not repair_admits(x, repairs_for):  # a repair lever repairs only what it declares
            continue
        pri = max([graph.prior(b).get(x["id"], 0.0) for b in x.get("blockers", [])] or [0.0])
        cands.append((-pri, float(x.get("cost", 99)), x["id"], x))
    cands.sort(key=lambda t: t[:3])
    return cands[0][3] if cands else None


def repair_admits(x: dict, failed: dict | None) -> bool:
    """Whether repair lever `x` repairs the instrument of `failed` (the lever whose positive control failed): the failed
    lever's id is in x's `repairs`, or the two share a blocker class. 2026-11-15 (KSR S50K, S62K): every KSR
    INSTRUMENT_FAIL went to tu_boundary_repair, whose work was done, and the planner stopped the lane twice."""
    if not failed:
        return False
    return (failed.get("id") in (x.get("repairs") or [])
            or bool(set(x.get("blockers") or []) & set(failed.get("blockers") or [])))


def repair_in_place(levers: dict, lane: str, ls: dict, product: str) -> dict | None:
    """The lane's own lever, to repair its failed instrument when no repair lever declares it: open, not retired by
    this lane, preconditions met. None parks."""
    retired = set(ls.get("retired") or [])
    return next((x for x in levers.get(lane, []) if x.get("id") == ls.get("lever") and x.get("status") == "open"
                 and x["id"] not in retired and _requires_met(x, product)), None)


def owner_lever(levers: dict, lane: str, ls: dict, product: str, want: str, family) -> dict | None:
    """The lever the Owner named in owner_resume="research:<id>", under the same admission as select: open, not retired
    by this lane, preconditions met, research kind, and of another family than the one the lane leaves. None refuses."""
    retired = set(ls.get("retired") or [])
    return next((x for x in levers.get(lane, []) if x.get("id") == want and x.get("status") == "open"
                 and x["id"] not in retired and _requires_met(x, product) and x.get("kind") != "repair"
                 and x.get("family") != family), None)


def selection_evidence(lever, graph) -> dict | None:
    """What the MethodGraph contributed to selecting `lever`: its prior and every learned edge (blocker -> lever) with a
    positive prior. The graph learns only from verified CERT/CAPABILITY, so a non-empty `edges` is the reuse pointer
    (E5); `edges == []` says the pick came from cost/id alone. None when no lever was selected."""
    if not lever:
        return None
    edges = [[b, lever["id"], round(p, 4)] for b in lever.get("blockers", [])
             if (p := graph.prior(b).get(lever["id"], 0.0)) > 0]
    return {"prior": max([e[2] for e in edges] or [0.0]), "edges": edges}


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
                   triggers: tuple[int, int, int], designer=None, residual=None) -> dict:
    """-> {"action": continue|stop|park|research|repair, "why", "lever"?, "directive"?, "designed"?}. Mutates the lane
    counters. triggers = (BLANK_STOP, INFO_PARK, NO_CONVERSION_PARK) of the autopilot. `designer(family) -> dict` designs
    a lever from `residual` where the lane would otherwise park for want of one (see synthesize)."""
    blank_stop, info_park, noconv_park = triggers
    cur = lever_by_id(levers, lane, ls.get("lever"))
    family = (cur or {}).get("family") or "UNREGISTERED"
    if cls in ("CERT", "CAPABILITY"):
        ls["synth_streak"] = 0

    def synth_or_park(why: str, src: str) -> dict:
        return _synth_or_park(ls, levers, lane, product, family, designer, residual, why, src)
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
    # Owner-directed method transition, one-shot (Owner 2026-11-13 "y", pane c84eb8e1: TENNIS parked on H-T1a x2 with
    # every lever retired). The Owner is the pivot authority: no pivot-streak rule and the closed instrument is not
    # counted again; the lever of another family is still chosen by select (MethodGraph prior, preconditions).
    # 2026-11-14 (Owner "crea las capacidades directamente y pegalas a las misiones", session 423c9c50): the value may
    # name the lever, "research:<id>"; a new lever has no MethodGraph prior, so select alone would never reach it.
    ro = ls.pop(OWNER_RESUME, None)
    if ro == "research" or (isinstance(ro, str) and ro.startswith("research:")):
        ls["repair"] = {}
        want = ro.split(":", 1)[1] if ":" in ro else None
        lever = (owner_lever(levers, lane, ls, product, want, family) if want
                 else select(levers, lane, ls, product, graph, family_not=family))
        if lever is None:
            return {"action": "park", "why": (f"Owner resume: lever {want} is not open, is retired, is of family {family}, "
                                              "or lacks its preconditions" if want else
                                              f"Owner resume: no open lever of another family than {family} with its "
                                              "preconditions met")}
        ls.update(mode="RESEARCH", blank=0, info_streak=0, no_conversion=0, research_fail=0, synth_streak=0)
        return {"action": "research", "lever": lever, "why": f"Owner-directed method transition from {family}: "
                                                             f"research with {lever['id']} ({lever.get('family')})",
                "directive": directive(lever, "RESEARCH")}
    # one count per instrument per judgment; legacy free-text keys fold onto their identity (max, not sum: the old
    # code wrote one key per name, and two names of one instrument in one judgment were one failure)
    rep: dict = {}
    for k, v in (ls.get("repair") or {}).items():
        kk = instrument_key(k)
        rep[kk] = max(rep.get(kk, 0), int(v))
    if instruments or ls.get("repair") is not None:
        ls["repair"] = rep
    for key in dict.fromkeys(instrument_key(n) for n in instruments):
        rep[key] = rep.get(key, 0) + 1
        if rep[key] > MAX_REPAIR:
            return synth_or_park(f"instrument {key} failed its positive control {rep[key]} times "
                                 f"(repair cap {MAX_REPAIR}); a new instrument needs a new idea", "repair cap")
    if cls == "CERT":
        ls.update(mode="EXPLOIT", blank=0, info_streak=0, no_conversion=0, research_fail=0, pivot_streak=0)
        return {"action": "continue", "why": "certificates: exploit"}
    if cls == "INSTRUMENT_FAIL":
        name = instruments[0]
        failed = next((x for x in levers.get(lane, []) if x.get("id") == ls.get("lever")), None) if lane else None
        lever = select(levers, lane, ls, product, graph, kind="repair", repairs_for=failed) if lane else None
        if lever is None and lane:
            lever = repair_in_place(levers, lane, ls, product)
        if lever is None:
            return synth_or_park(f"instrument {name} failed and no repair lever for {ls.get('lever')} is open in {lane}",
                                 "no repair lever")
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
            return synth_or_park(f"{RESEARCH_FAIL_STOP} research generations without verified "
                                 "INFORMATION or CAPABILITY: research stop rule", "research stop rule")
    if ls["blank"] >= blank_stop:
        return {"action": "stop", "why": f"{blank_stop} consecutive generations with no verified progress of any class"}
    if ls["info_streak"] >= info_park or ls["no_conversion"] >= noconv_park:
        return plateau(ls, levers, lane, product, graph, family, cls in ("INFORMATION", "CAPABILITY"), designer, residual)
    if ls.get("mode") == "REPAIR":
        ls["mode"] = "EXPLOIT"
    return {"action": "continue", "why": f"{cls}: continue in {ls.get('mode') or 'EXPLOIT'}"}


def plateau(ls: dict, levers: dict, lane: str, product: str, graph, family: str, evidence_delta: bool,
            designer=None, residual=None) -> dict:
    """The protection rule fired. Ask the Mission Runtime pivot rule; on 'pivot' enter RESEARCH with a lever of another
    family: an open one from levers.json, else one the autopilot designs from the residual (synthesize)."""
    d = _pivot(ls, family, evidence_delta, "METHOD_PLATEAU", f"lane {lane} plateau on {family}")
    if d.get("action") != "pivot":
        return {"action": "park", "why": f"pivot rule: {d.get('why')}"}
    lever = select(levers, lane, ls, product, graph, family_not=family)
    if lever is None:
        r = _synth_or_park(ls, levers, lane, product, family, designer, residual,
                           f"plateau on {family} and no open lever of another family with its preconditions met",
                           f"plateau on {family}")
        if r["action"] != "research":
            return r
        lever = r["lever"]
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


def worktree_rel(product: str, checkpoint: str):
    """(tree dir, path inside it) when `checkpoint` is an absolute path under <product>/.claude/worktrees/<w>/, else None.
    2026-11-15 S63F: such a path sat inside the product dir, so it read as 'in the product' (OK) while the product lacked
    the branch; the judge found its gates absent (rc=2) and said INCONCLUSIVE."""
    if not os.path.isabs(checkpoint):
        return None
    base = os.path.join(os.path.realpath(product), ".claude", "worktrees") + os.sep
    p = os.path.realpath(checkpoint)
    if not p.startswith(base):
        return None
    tree, _, rel = p[len(base):].partition(os.sep)
    return (base + tree, rel) if tree and rel else None


def ff_to(product: str, head, dry: bool = False) -> tuple[bool, str]:
    """Fast-forward the product to `head` (a commit on a generation branch) before a continuation is armed. Only a
    fast-forward, only from a clean product. 2026-11-16 (S71F, S69T): the continuation's packet was committed on a
    product that lacked the branch, the two lines diverged, and gsd_mission held the relaunch for 8 h after both
    workers had finished."""
    if not head:
        return False, "the halted generation's branch head is unknown"
    rc, cur = _git(product, "rev-parse", "HEAD")
    if rc != 0:
        return False, f"product HEAD unreadable: {cur[-200:]}"
    if cur == head:
        return True, f"product already at {head[:12]}"
    if _git(product, "merge-base", "--is-ancestor", "HEAD", head)[0] != 0:
        return False, f"the branch head {head[:12]} is not a fast-forward of the product HEAD {cur[:12]}"
    if _git(product, "status", "--porcelain", "--untracked-files=no")[1]:
        return False, "the product has tracked changes"
    if dry:
        return True, f"dry: would fast-forward the product to {head[:12]}"
    rc, out = _git(product, "merge", "--ff-only", head)
    if rc != 0:
        return False, f"fast-forward failed: {out[-200:]}"
    return True, f"fast-forwarded the product to {head[:12]}"


def _branch_heads(product: str) -> list[tuple[str, str]]:
    """(branch, tip sha) for every local branch of the product's repository."""
    rc, out = _git(product, "for-each-ref", "--format=%(refname:short) %(objectname)", "refs/heads")
    return [tuple(l.rsplit(" ", 1)) for l in out.splitlines() if rc == 0 and " " in l]


def discover_checkpoint(product: str, checkpoint: str, dry: bool = False) -> tuple[str, str]:
    """-> (OK|FF|PARK, note). OK: the checkpoint is in the product. FF: exactly one worktree branch holds it COMMITTED,
    the product HEAD is its ancestor and the product has no tracked changes -> `merge --ff-only` was run. Otherwise PARK.
    A path inside a worktree (worktree_rel) must be committed there, then follows the same branch rule by its rel path."""
    wr = worktree_rel(product, checkpoint)
    if wr:
        if _git(wr[0], "cat-file", "-e", f"HEAD:{wr[1].replace(os.sep, '/')}")[0] != 0:
            return "PARK", f"CHECKPOINT_UNCOMMITTED: {wr[1]} is in worktree {os.path.basename(wr[0])} but not committed there"
        checkpoint = wr[1]
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
    cands = [t for t in trees if os.path.realpath(t["worktree"]) != os.path.realpath(product) and t.get("HEAD")]
    # 2026-11-17 (Owner "b"): a --worktree checkout Claude removed on exit leaves its branch; the branch tip still
    # holds the checkpoint (MKWLIB s100l, 2026-11-16). Local branch tips count; one commit counts once.
    cands += [{"HEAD": h, "branch": b} for b, h in _branch_heads(product)]
    by_sha = {}
    for t in cands:
        if t["HEAD"] not in by_sha and _git(product, "cat-file", "-e", f"{t['HEAD']}:{rel}")[0] == 0:
            by_sha[t["HEAD"]] = t
    # a tip that is an ancestor of another holder is the same line of work, not a second candidate
    hits = [t for s, t in by_sha.items()
            if not any(o != s and _git(product, "merge-base", "--is-ancestor", s, o)[0] == 0 for o in by_sha)]
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
