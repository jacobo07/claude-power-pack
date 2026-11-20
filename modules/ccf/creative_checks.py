"""Creative checks on the real CCF path (spec vault/specs/bcap2-activation.md, BCAP-2 activation slice A).

Runs the seven absorbed BCAP-2 checks (BI-08..14) at the CLI stage that owns their input and returns one record
per check. The rule that keeps every existing project unchanged: an input the project did not declare is
UNASSESSED, never FAIL. A check blocks only where the project opts in with config["creative_checks"][name] = "enforce";
under enforce, UNASSESSED blocks too (the project asked for the check and did not supply its inputs).

No provider call, no repair of input, no network. Statuses: PASS | FAIL | NARROW_BRIEF_EXCEPTION | UNASSESSED.
"""
from __future__ import annotations

from modules.ccf import (brand_truth, critique, identity_set, provider_policy, techniques, territories,
                         visual_dna)

STAGES = {
    "generate": ("brand_truth", "territories", "techniques", "identity_set", "visual_dna", "provider_policy"),
    "select": ("critique",),
}
MODES = ("report", "enforce")
PASSING = ("PASS", "NARROW_BRIEF_EXCEPTION")


def _rec(status, detail=None, **extra):
    out = {"status": status, "detail": detail}
    out.update(extra)
    return out


def _unassessed(what):
    return _rec("UNASSESSED", f"no {what} declared")


def _brand_truth(config, concepts, **_):
    items = config.get("brand_truth")
    if not items:
        return _unassessed("config.brand_truth items")
    r = brand_truth.intake(str(config.get("brand_id") or "project"), items)
    return _rec("FAIL" if r["rejected"] else "PASS",
                f"{len(r['facts'])} field(s) evidenced, {len(r['rejected'])} rejected, {len(r['unknown'])} unknown",
                result=r)


def _territories(config, concepts, **_):
    if not any(c.get("mechanism") or c.get("brand_fact") for c in concepts):
        return _unassessed("concept mechanism/brand_fact")
    r = territories.check_territories(concepts, config.get("narrow_brief"))
    return _rec(r["verdict"], f"{len(r['distinct'])} distinct territories", result=r)


def _techniques(config, concepts, **_):
    hyps = [dict(c["hypothesis"], id=c.get("id")) for c in concepts if isinstance(c.get("hypothesis"), dict)]
    if not hyps:
        return _unassessed("concept hypothesis")
    r = techniques.summarize(hyps)
    bad = [row["id"] for row in r["rows"] if row["problems"]]
    return _rec("FAIL" if bad else "PASS", f"{len(r['accepted'])}/{len(hyps)} hypotheses acceptable"
                + (f"; problems in {bad}" if bad else ""), result=r)


def _identity_set(config, concepts, **_):
    s = config.get("identity_set")
    if not isinstance(s, dict) or not s:
        return _unassessed("config.identity_set")
    probs = identity_set.validate_set(s, s.get("mode", "NEW"), s.get("original"))
    return _rec("FAIL" if probs else "PASS", "; ".join(probs) or "identity set valid", problems=probs)


def _visual_dna(config, concepts, **_):
    dna = config.get("visual_dna")
    if not dna:
        return _unassessed("config.visual_dna")
    probs = visual_dna.validate(dna)
    return _rec("FAIL" if probs else "PASS", "; ".join(probs) or "Visual DNA valid", problems=probs)


def _provider_policy(config, concepts, **_):
    """CCF generate always calls an image model, so a concept passes only if its declared intent justifies one."""
    per, declared = {}, False
    for c in concepts:
        intent = c.get("provider_intent")
        if not isinstance(intent, dict):
            per[c.get("id")] = {"route": None, "status": "UNASSESSED"}
            continue
        declared = True
        r = provider_policy.route(intent)
        per[c.get("id")] = dict(r, status="PASS" if r["route"] == "IMAGE_MODEL" else "FAIL")
    plan = config.get("provider_plan")
    plan_r = None
    if isinstance(plan, dict):
        declared = True
        plan_r = provider_policy.plan_call(plan.get("model"), plan.get("fallback_model"),
                                           int(plan.get("tool_calls") or 0), plan.get("imports") or ())
    if not declared:
        return _unassessed("concept provider_intent or config.provider_plan")
    statuses = [v["status"] for v in per.values()]
    fail = "FAIL" in statuses or "UNASSESSED" in statuses or (plan_r is not None and not plan_r["ok"])
    detail = f"{statuses.count('PASS')}/{len(statuses)} concept(s) justify an image model"
    if plan_r is not None and not plan_r["ok"]:
        detail += "; plan: " + "; ".join(plan_r["problems"])
    return _rec("FAIL" if fail else "PASS", detail, per_concept=per, plan=plan_r)


def _critique(config, concepts, selected=None, actor=None, **_):
    raw = config.get("critiques")
    if not isinstance(raw, dict) or not raw:
        return _unassessed("config.critiques")
    crits = [critique.build_critique(cid, items) for cid, items in raw.items()]
    r = critique.approve(crits, selected, actor)
    return _rec("PASS" if r["approved"] else "FAIL", r.get("reason") or f"approved {selected!r} by {actor!r}",
                result=r, qualifying=[c["concept"] for c in crits if critique.qualifies(c)])


CHECKS = {"brand_truth": _brand_truth, "territories": _territories, "techniques": _techniques,
          "identity_set": _identity_set, "visual_dna": _visual_dna, "provider_policy": _provider_policy,
          "critique": _critique}


def modes(config) -> tuple:
    """-> ({check: mode}, errors). An unknown check name or mode is a config error, never silently report."""
    raw = config.get("creative_checks") or {}
    errors, out = [], {name: "report" for name in CHECKS}
    if not isinstance(raw, dict):
        return out, ["creative_checks must be an object {check: report|enforce}"]
    for name, mode in raw.items():
        if name not in CHECKS:
            errors.append(f"creative_checks: unknown check {name!r} (known: {', '.join(CHECKS)})")
        elif mode not in MODES:
            errors.append(f"creative_checks.{name}: mode {mode!r} must be report or enforce")
        else:
            out[name] = mode
    return out, errors


def run(stage: str, config: dict, **ctx) -> dict:
    """-> {stage, checks: {name: record + mode}, blocking: [names], errors: [..]}."""
    concepts = [c for c in (config.get("concepts") or []) if isinstance(c, dict)]
    mode_of, errors = modes(config)
    checks, blocking = {}, []
    for name in STAGES[stage]:
        rec = CHECKS[name](config, concepts, **ctx)
        rec["mode"] = mode_of[name]
        checks[name] = rec
        if rec["mode"] == "enforce" and rec["status"] not in PASSING:
            blocking.append(name)
    return {"stage": stage, "checks": checks, "blocking": blocking, "errors": errors}


def summary(report: dict) -> str:
    parts = [f"{n} {r['status']}{' [enforce]' if r['mode'] == 'enforce' else ''}" for n, r in report["checks"].items()]
    line = f"creative checks ({report['stage']}): " + ", ".join(parts)
    if report["blocking"]:
        line += f" -- BLOCKED by {', '.join(report['blocking'])}"
    return line
