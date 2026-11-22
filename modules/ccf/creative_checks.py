"""Creative checks on the real CCF path (spec vault/specs/bcap2-activation.md, BCAP-2 activation slice A).

Runs the seven absorbed BCAP-2 checks (BI-08..14) at the CLI stage that owns their input and returns one record
per check. The rule that keeps every existing project unchanged: an input the project did not declare is
UNASSESSED, never FAIL. A check blocks only where the project opts in with config["creative_checks"][name] = "enforce";
under enforce, UNASSESSED blocks too (the project asked for the check and did not supply its inputs).

No provider call, no repair of input, no network. Statuses: PASS | FAIL | NARROW_BRIEF_EXCEPTION | UNASSESSED.
"""
from __future__ import annotations

import os

from modules.ccf import (brand_color, brand_release, brand_review, brand_truth, critique, identity_set,
                         provider_policy, techniques, territories, trace_lane, visual_dna)

STAGES = {
    "generate": ("brand_truth", "territories", "techniques", "identity_set", "visual_dna", "provider_policy"),
    "select": ("critique",),
    # BI-15..35 (BCAP2B phase 5): the package stage, every input declared in config, absent = UNASSESSED.
    "package": ("brand_color", "export_profile", "design_tokens", "application_preview", "language_coverage",
                "logo_lens", "similarity", "benchmark", "independent_review", "typed_parts", "trace",
                "release_manifest"),
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


def _declared(config, key, what=None):
    v = config.get(key)
    return v if isinstance(v, dict) and v else None


def _problems(problems, ok_detail, **extra):
    return _rec("FAIL" if problems else "PASS", "; ".join(problems) or ok_detail, problems=problems, **extra)


def _read_svg(project_dir, rel):
    """-> (bytes|None, why). A declared path that cannot be read is a FAIL input, never silently absent."""
    if not project_dir or not isinstance(rel, str) or os.path.isabs(rel) or ".." in rel.replace("\\", "/").split("/"):
        return None, f"svg_path {rel!r} must be relative inside the project"
    try:
        with open(os.path.join(project_dir, rel), "rb") as handle:
            return handle.read(), None
    except OSError as exc:
        return None, f"svg_path {rel!r} unreadable ({exc.__class__.__name__})"


def _brand_color(config, concepts, **_):
    palette, pairs = _declared(config, "palette"), config.get("contrast_pairs")
    if not palette:
        return _unassessed("config.palette")
    r = brand_color.check_palette(palette, pairs if isinstance(pairs, list) else [])
    un = [row for row in r["rows"] if row["status"] == "UNASSESSED"]
    detail = f"{len(r['rows'])} pair(s) measured" + (f", {len(un)} UNASSESSED" if un else "")
    if not pairs:
        detail += "; no contrast_pairs declared"
    return _rec("FAIL" if r["problems"] else "PASS", "; ".join(r["problems"]) or detail, result=r)


def _export_profile(config, concepts, **_):
    prof = _declared(config, "export_profile")
    if not prof:
        return _unassessed("config.export_profile")
    return _problems(brand_release.check_export_profile(prof), "export profile valid")


def _design_tokens(config, concepts, **_):
    toks = _declared(config, "design_tokens")
    if not toks:
        return _unassessed("config.design_tokens")
    return _problems(brand_release.check_dtcg(toks), "DTCG tokens valid")


def _application_preview(config, concepts, **_):
    prev = _declared(config, "application_preview")
    if not prev:
        return _unassessed("config.application_preview")
    dna = config.get("visual_dna") if isinstance(config.get("visual_dna"), dict) else {}
    if not dna.get("id"):
        return _rec("UNASSESSED", "application_preview declared but config.visual_dna.id is not")
    return _problems(brand_release.check_preview(prev, dna["id"]), "all 9 contexts tested on one Visual DNA")


def _language_coverage(config, concepts, selected=None, **_):
    spec = _declared(config, "language_coverage")
    if not spec:
        return _unassessed("config.language_coverage")
    r = brand_review.language_coverage(spec.get("font"), spec.get("registry") or {},
                                       tuple(spec.get("langs") or ("ES", "EN", "PT", "FR", "DE")))
    return _rec("PASS" if r["ok"] else "FAIL", r["why"], result=r)


def _logo_lens(config, concepts, **_):
    ev = _declared(config, "logo_review")
    if not ev:
        return _unassessed("config.logo_review")
    r = brand_review.logo_lens(ev)
    status = "FAIL" if r["verdict"] == "BLOCK" else ("PASS" if r["verdict"] == "APPROVE_PENDING_HUMAN" else "UNASSESSED")
    return _rec(status, f"lens verdict {r['verdict']}", result=r)


def _similarity(config, concepts, **_):
    spec = _declared(config, "similarity")
    if not spec:
        return _unassessed("config.similarity")
    r = brand_release.similarity_report(spec.get("corpus") or {}, spec.get("nearest") or [],
                                        bool(spec.get("human_review")))
    status = {"REVIEW": "FAIL", "SCREEN_NO_NEAR_MATCH": "PASS"}.get(r["verdict"], "UNASSESSED")
    return _rec(status, f"{r['verdict']} (screening only; clearance {r['clearance']})", result=r)


def _benchmark(config, concepts, **_):
    briefs = config.get("benchmark_briefs")
    if not isinstance(briefs, list) or not briefs:
        return _unassessed("config.benchmark_briefs")
    return _problems(brand_review.check_benchmark(briefs), "frozen benchmark set valid (denominators only)")


def _independent_review(config, concepts, **_):
    rev = _declared(config, "independent_review")
    if not rev:
        return _unassessed("config.independent_review")
    return _problems(brand_review.review_independent(rev), "independent review record valid")


def _typed_parts(config, concepts, project_dir=None, **_):
    spec = _declared(config, "typed_parts")
    if not spec:
        return _unassessed("config.typed_parts")
    svg, why = _read_svg(project_dir, spec.get("svg_path"))
    if svg is None:
        return _rec("FAIL", why)
    r = brand_review.split_parts(svg)
    return _rec("PASS" if r["ok"] else "FAIL", r["why"] if not r["ok"] else f"parts: {sorted(r['parts'])}")


def _trace(config, concepts, project_dir=None, **_):
    spec = _declared(config, "trace")
    if not spec:
        return _unassessed("config.trace")
    svg, why = _read_svg(project_dir, spec.get("svg_path"))
    if svg is None:
        return _rec("FAIL", why)
    return _problems(trace_lane.check_trace(svg, spec.get("decision"), spec.get("limits")),
                     "traced SVG acceptable", measured=trace_lane.measure_trace(svg))


def _release_manifest(config, concepts, project_dir=None, **_):
    """BI-26: a declared immutable manifest is verified against the files it names (relative, inside the project)."""
    spec = _declared(config, "release_manifest")
    if not spec:
        return _unassessed("config.release_manifest")
    manifest, names = spec.get("manifest"), spec.get("files")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict) or not isinstance(names, list):
        return _rec("FAIL", "release_manifest needs {manifest: {files: {...}}, files: [relative paths]}")
    files = {}
    for rel in names:
        data, why = _read_svg(project_dir, rel)
        if data is None:
            return _rec("FAIL", why.replace("svg_path", "file"))
        files[rel] = data
    return _problems(brand_release.verify_manifest(manifest, files), f"{len(files)} file(s) match the manifest")


CHECKS = {"brand_truth": _brand_truth, "territories": _territories, "techniques": _techniques,
          "identity_set": _identity_set, "visual_dna": _visual_dna, "provider_policy": _provider_policy,
          "critique": _critique, "brand_color": _brand_color, "export_profile": _export_profile,
          "design_tokens": _design_tokens, "application_preview": _application_preview,
          "language_coverage": _language_coverage, "logo_lens": _logo_lens, "similarity": _similarity,
          "benchmark": _benchmark, "independent_review": _independent_review, "typed_parts": _typed_parts,
          "trace": _trace, "release_manifest": _release_manifest}


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
