"""V-BCAP2-D21-BC gate (Phase 8 Workstreams B/C slice): reference_intel. Both poles per scenario, no network.
Drives D21-B05/B06 and V-D21-12/13/18. python3 tools/test_bcap2_d21_bc.py (exit 0 == PASS)"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from modules.cdicf import reference_intel as RI  # noqa: E402

FAILS = []


def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (f" -- {d}" if d and not c else ""))
    if not c:
        FAILS.append(n)


# V-D21-12: missing token is UNKNOWN, an unevidenced value is dropped, not carried
t = RI.extract_tokens({"tokens": {"color": {"value": "#0a0a0a", "evidence": "OBSERVED"},
                                  "font": {"value": "Inter", "evidence": None},
                                  "radius": {"value": "8px", "evidence": "INFERRED"}}})
check("V-D21-12 pole: absent spacing is UNKNOWN with no value", t["spacing"] == {"value": None, "level": "UNKNOWN"})
check("V-D21-12 pole: font named without evidence is dropped to UNKNOWN", t["font"]["level"] == "UNKNOWN" and t["font"]["value"] is None)
check("V-D21-12 control: observed colour and inferred radius keep value and level",
      t["color"] == {"value": "#0a0a0a", "level": "OBSERVED"} and t["radius"]["level"] == "INFERRED")
check("V-D21-12 pole: empty reference yields all-UNKNOWN, no invented defaults",
      all(v["level"] == "UNKNOWN" and v["value"] is None for v in RI.extract_tokens({}).values()))

# V-D21-13: project contract wins
proj = {"color": "#111111", "font": None, "radius": "4px", "spacing": None, "size": None}
m = RI.merge_into_project(proj, t)
check("V-D21-13 pole: conflicting imported colour does not overwrite the project's", m["tokens"]["color"] == "#111111")
check("V-D21-13 pole: the conflict is reported, not silent", {"kind": "color", "kept": "#111111", "rejected": "#0a0a0a"} in m["conflicts"])
check("V-D21-13 control: an empty project slot may take an evidenced import, UNKNOWN stays None",
      RI.merge_into_project({k: None for k in RI.TOKEN_KINDS}, t)["tokens"]["color"] == "#0a0a0a"
      and RI.merge_into_project({k: None for k in RI.TOKEN_KINDS}, t)["tokens"]["font"] is None)
check("V-D21-13 control: identical value is not a conflict", not RI.merge_into_project({"radius": "8px"}, t)["conflicts"])

# D21-B06 brief
good = {"source": "ref-A hero", "transferable": ["type scale hierarchy"], "forbidden_copy": ["exact layout", "logo"],
        "differs_by": "product-specific proof strip", "test_plan": "render + contrast + responsive"}
check("D21-B06 control: complete brief passes", RI.validate_brief(good)[0])
for f in RI.BRIEF_FIELDS:
    b = dict(good); b.pop(f)
    check(f"D21-B06 pole: brief without {f} is refused", not RI.validate_brief(b)[0])
check("D21-B06 pole: empty forbidden_copy is refused", not RI.validate_brief({**good, "forbidden_copy": []})[0])
check("D21-B06 pole: result identical to source is refused", not RI.validate_brief({**good, "differs_by": good["source"]})[0])
check("D21-B06 pole: None brief is refused", not RI.validate_brief(None)[0])

# D21-B05 ranking
CAT = [
    {"id": "m1", "purpose": "pricing", "platform": "mobile", "sector": "fintech", "era": "2024", "source_rights": "OPEN_PERMISSIVE",
     "license_evidence": {"spdx": "MIT", "version": "1", "license_sha256": "h"}},
    {"id": "m2", "purpose": "pricing", "platform": "mobile", "sector": "fintech", "era": "2024", "source_rights": "OPEN_PERMISSIVE",
     "license_evidence": {"spdx": "MIT", "version": "1", "license_sha256": "h"}},
    {"id": "m3", "purpose": "pricing", "platform": "mobile", "sector": "health", "era": "2023", "source_rights": "OPEN_PERMISSIVE",
     "license_evidence": {"spdx": "MIT", "version": "1", "license_sha256": "h"}},
    {"id": "d1", "purpose": "pricing", "platform": "desktop", "sector": "fintech", "era": "2024", "source_rights": "OPEN_PERMISSIVE",
     "license_evidence": {"spdx": "MIT", "version": "1", "license_sha256": "h"}},
    {"id": "r1", "purpose": "pricing", "platform": "mobile", "sector": "retail", "era": "2022", "source_rights": "RESTRICTED"},
]
r = RI.rank({"purpose": "pricing", "platform": "mobile", "sector": "fintech", "need_code": True}, CAT)
ids = [p["id"] for p in r["picks"]]
check("D21-B05 control: best mobile+sector item ranks first", r["verdict"] == "RANKED" and ids[0] == "m1", str(r))
check("D21-B05 pole: desktop item never returned for a mobile query", "d1" not in ids)
check("D21-B05 pole: RESTRICTED source filtered when code is needed", "r1" not in ids)
check("D21-B05 pole: diversity guard drops the near-duplicate (same sector+era)", "m2" not in ids and "m3" in ids)
check("D21-B05 control: without need_code the restricted item may be a reference-only pick",
      "r1" in [p["id"] for p in RI.rank({"purpose": "pricing", "platform": "mobile", "sector": "retail"}, CAT)["picks"]])
a = RI.rank({"purpose": "kanban", "platform": "watch"}, CAT)
check("D21-B05 pole: no match ABSTAINs with a reason", a["verdict"] == "ABSTAIN" and a["picks"] == [] and a["reason"])
check("D21-B05 pole: purpose mismatch alone (platform match) falls under the floor and ABSTAINs",
      RI.rank({"purpose": "kanban", "platform": "mobile"}, CAT)["verdict"] == "ABSTAIN")
check("D21-B05 pole: empty catalog ABSTAINs", RI.rank({"purpose": "pricing", "platform": "mobile"}, [])["verdict"] == "ABSTAIN")

# V-D21-18: motion budget NONE
n = RI.rank({"purpose": "pricing", "platform": "mobile", "motion_budget": "NONE", "want_motion": True}, CAT)
check("V-D21-18 pole: motion budget NONE with a motion ask ABSTAINs, nothing proposed", n["verdict"] == "ABSTAIN" and not n["picks"])
check("V-D21-18 control: budget NONE without a motion ask still ranks normally",
      RI.rank({"purpose": "pricing", "platform": "mobile", "motion_budget": "NONE"}, CAT)["verdict"] == "RANKED")

# D21-C07: no unobserved fidelity claims
full = {c: True for c in RI.RENDER_CHECKS}
check("D21-C07 control: no fidelity claim needs no evidence", RI.fidelity_claims("Adapted hero with our own proof strip", {})[0])
check("D21-C07 pole: '1:1' claim with no evidence is refused", not RI.fidelity_claims("Delivers a 1:1 match of the reference", {})[0])
check("D21-C07 pole: absent check is unobserved, not passed", not RI.fidelity_claims("pixel-perfect", {**full, "fonts": None})[0])
check("D21-C07 pole: a failed check refuses and names it", any("a11y: failed" in r for r in RI.fidelity_claims("pixel-perfect", {**full, "a11y": False})[1]))
check("D21-C07 control: claim with all five checks observed true passes", RI.fidelity_claims("pixel-perfect clone of layout", full)[0])
check("D21-C07 pole: None claim text is not a claim", RI.fidelity_claims(None, None)[0])

# mutant drill: a permissive merge would overwrite the project; prove the check can fail
bad = {k: (v["value"] if v["value"] else None) for k, v in t.items()}
check("drill: a naive overwrite-merge would differ from the project value (the V-D21-13 check is live)", bad["color"] != proj["color"])

# D21-B07 corpus: author-created, no third-party content; measures ranking against a purpose-keyword baseline
import json as _json, os as _os
_c = _json.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "vault", "programs", "bcap-2", "design-resources", "TEST_CORPUS.json")))
check("D21-B07 control: corpus declares CPP authorship and its limits",
      "no third-party" in _c["authorship"] and "not evidence" in _c["limits"] and len(_c["items"]) >= 20)
check("D21-B07 pole: no corpus item carries a URL or screenshot field",
      all(not ({"url", "screenshot", "image"} & set(i)) and "http" not in i["description"] for i in _c["items"]))
def _prec(fn):
    out = []
    for x in _c["queries"]:
        got, rel = fn(x["q"]), set(x["relevant"])
        out.append(1.0 if not got and not rel else (sum(g in rel for g in got) / len(got) if got else 0.0))
    return sum(out) / len(out)
_rank = lambda q: [p["id"] for p in RI.rank(dict(q, need_code=True), _c["items"])["picks"]]
_base = lambda q: [i["id"] for i in _c["items"] if i["purpose"] == q["purpose"]][:3]
check("D21-B07 pole: rank precision@3 >= keyword baseline on the corpus", _prec(_rank) >= _prec(_base), f"{_prec(_rank):.2f} vs {_prec(_base):.2f}")
check("D21-B07 pole: unknown purpose ABSTAINs (no off-purpose pick)",
      RI.rank({"purpose": "checkout", "platform": "mobile", "sector": "retail", "need_code": True}, _c["items"])["verdict"] == "ABSTAIN")
check("D21-B07 pole: restricted item never appears when code is needed",
      all("c06" not in _rank(x["q"]) for x in _c["queries"]))
check("D21-B07 pole: diversity, no two picks share (sector, era)",
      all(len({(i["sector"], i["era"]) for i in _c["items"] if i["id"] in _rank(x["q"])}) == len(_rank(x["q"])) for x in _c["queries"]))
_old = RI.rank
def _mutant(q, cat, **kw):  # the pre-fix behaviour: purpose not required
    return _old(q, [dict(i, purpose=q["purpose"]) for i in cat], **kw)
RI.rank = _mutant
_m = _prec(_rank)
RI.rank = _old
check("D21-B07 drill: a ranker that ignores purpose scores lower (the precision check is live)", _m < _prec(_rank), f"{_m:.2f}")

# D21-B01..B04 record contracts
from modules.cdicf import reference_records as RR  # noqa: E402
_g = {f: "x" for f in RR.GALLERY_FIELDS}
check("D21-B01 control: complete gallery record passes", RR.validate_gallery_record(_g)[0])
check("D21-B01 pole: missing axis fails", not RR.validate_gallery_record({k: v for k, v in _g.items() if k != "era"})[0])
check("D21-B01 pole: cloning intent refused", not RR.validate_gallery_record(dict(_g, clone_intent=True))[0])
check("D21-B01 pole: all-UNKNOWN record carries no observation", not RR.validate_gallery_record({f: "UNKNOWN" for f in RR.GALLERY_FIELDS})[0])
check("D21-B01 control: UNKNOWN on one axis is allowed", RR.validate_gallery_record(dict(_g, era="UNKNOWN"))[0])
_t = {"reference_id": "r", "brief_id": "b", "render_evaluation": "e", "render_evaluation_observed": True, "stop_conditions": list(RR.STOP_CONDITIONS)}
check("D21-B02 control: full trace passes", RR.validate_transform_trace(_t)[0])
check("D21-B02 pole: missing stop condition fails", not RR.validate_transform_trace(dict(_t, stop_conditions=["exact_copy"]))[0])
check("D21-B02 pole: unobserved render evaluation fails", not RR.validate_transform_trace(dict(_t, render_evaluation_observed=False))[0])
_m = {f: "x" for f in RR.MOBILE_FIELDS}; _m.update(access_verified=True, licence_verified=True, feeds="CDIO-08")
check("D21-B03 control: verified mobile pattern passes", RR.validate_mobile_pattern(_m)[0])
check("D21-B03 pole: unverified licence fails", not RR.validate_mobile_pattern(dict(_m, licence_verified=False))[0])
check("D21-B03 pole: desktop feed target fails", not RR.validate_mobile_pattern(dict(_m, feeds="CDIO-05"))[0])
_c2 = {f: "x" for f in RR.COMPONENT_JOBS}
check("D21-B04 control: component entry passes", RR.validate_component_entry(_c2)[0])
check("D21-B04 pole: official-standard claim fails", not RR.validate_component_entry(dict(_c2, claims_official_standard=True))[0])
check("D21-B04 pole: missing states fails", not RR.validate_component_entry({k: v for k, v in _c2.items() if k != "states"})[0])

# D21-C03/C04/C05
from modules.cdicf import prompt_schema as PS  # noqa: E402
_p = {f: ["a"] if f == "acceptance_criteria" else "x" for f in PS.PROMPT_FIELDS}
check("D21-C03 control: complete prompt record passes", PS.classify_prompt(_p)[0])
check("D21-C03 pole: missing acceptance criteria fails", not PS.classify_prompt(dict(_p, acceptance_criteria=[]))[0])
check("D21-C03 pole: verbatim prompt text refused", not PS.classify_prompt(dict(_p, verbatim_text="..."))[0])
check("D21-C03 pole: blank criterion fails", not PS.classify_prompt(dict(_p, acceptance_criteria=[" "]))[0])
_v = {"identity_verified": True, "content_rights": "AUTHORIZED", "categories": ["hero", "pricing"]}
check("D21-C04 control: verified authorized source passes", PS.vibeprompt_import_allowed(_v)[0])
check("D21-C04 pole: unknown access refuses import", not PS.vibeprompt_import_allowed(dict(_v, content_rights="UNKNOWN_ACCESS"))[0])
check("D21-C04 pole: unverified identity refuses import", not PS.vibeprompt_import_allowed(dict(_v, identity_verified=False))[0])
check("D21-C04 pole: incompatible category refused", not PS.vibeprompt_import_allowed(dict(_v, categories=["meme"]))[0])
_mx = {s: {"maps_to_canonical": True, "reversible": True} for s in PS.SOURCES}
check("D21-C05 control: full matrix passes", PS.validate_matrix(_mx)[0])
check("D21-C05 pole: missing source fails", not PS.validate_matrix({k: v for k, v in _mx.items() if k != "jiro"})[0])
check("D21-C05 pole: second canonical truth fails", not PS.validate_matrix(dict(_mx, refero={"canonical": True}))[0])
check("D21-C05 pole: irreversible mapping without lossy fields fails", not PS.validate_matrix(dict(_mx, jiro={"reversible": False}))[0])
check("D21-C05 control: irreversible mapping naming lossy fields passes", PS.validate_matrix(dict(_mx, jiro={"reversible": False, "lossy_fields": ["prompt_text"]}))[0])

# D21-D03/D07/D09 selection before install
from modules.cdicf import component_install as CI  # noqa: E402
_ev = {"spdx": "MIT", "version": "1.2.0", "license_sha256": "ab"}
_it = {"name": "hero", "registry": "reg-a", "source_rights": "MIXED", "licence_evidence": _ev, "peers": ["react"],
       "latest_version": "1.2.0", "snapshot_version": "1.2.0", "supply_chain_ok": True, "states": ["empty", "error"],
       "cost": 0, "identity_fit": True, "rollback": "git revert"}
_pj = {"has_peers": ["react"], "accepted_registries": ["reg-a"], "required_states": ["empty"], "budget": 10}
check("D21-D07 control: fully qualified item is ALLOW", CI.plan_install(_it, _pj)["verdict"] == "ALLOW")
for _n, _mut in (("malicious registry", {"registry": "evil"}), ("missing peer", {"peers": ["react", "vue"]}),
                 ("stale snapshot", {"snapshot_version": "1.1.0"}), ("licence drift", {"licence_evidence": {"spdx": "GPL-3.0", "version": "1", "license_sha256": "x"}}),
                 ("no licence evidence", {"licence_evidence": None}), ("missing states", {"states": []}),
                 ("unmeasured cost", {"cost": None}), ("no rollback", {"rollback": ""}), ("pro asset", {"source_rights": "RESTRICTED"})):
    check(f"D21-D09 pole: {_n} is REFUSE", CI.plan_install(dict(_it, **_mut), _pj)["verdict"] == "REFUSE")
check("D21-D09 pole: same name from two registries refused", CI.plan_install(_it, _pj, {"hero": "reg-b"})["verdict"] == "REFUSE")
_log = []
def _boom(): raise RuntimeError("x")
_r = CI.run_install(CI.plan_install(_it, _pj), [lambda: _log.append(1), _boom], lambda d: _log.append(("rb", len(d))))
check("D21-D09 pole: failure partway rolls back what landed", _r["status"] == "FAILED_ROLLED_BACK" and ("rb", 1) in _log)
check("D21-D09 pole: REFUSE plan runs nothing", CI.run_install(CI.plan_install(dict(_it, registry="evil"), _pj), [lambda: _log.append(9)], None)["status"] == "NOT_RUN" and 9 not in _log)
check("D21-D09 control: clean run installs", CI.run_install(CI.plan_install(_it, _pj), [lambda: None], None)["status"] == "INSTALLED")
check("D21-D03 pole: restricted entry stays REFERENCE_ONLY", CI.reference_only_catalog({"rights_status": "RESTRICTED"})["mode"] == "REFERENCE_ONLY")
check("D21-D03 control: separately licensed item may be SOURCE_COPY", CI.reference_only_catalog({"rights_status": "MIXED", "licence_evidence": _ev})["mode"] == "SOURCE_COPY")

# D21-D05/D06/D08 metadata, stack, composition
from modules.cdicf import component_meta as CM  # noqa: E402
_m = {"kind": "hero", "frameworks": ["react"], "tailwind": "3.4", "ssr_safe": True, "semantic_html": True,
      "keyboard_focus": True, "aria": True, "responsive": True, "rtl": True, "theme_modes": ["dark"], "reduced_motion": True}
_pr = {"framework": "react", "tailwind": "3.3", "ssr": True, "rtl": True}
check("D21-D05 control: normalized meta passes", CM.validate_meta(_m)[0])
check("D21-D05 pole: kind outside the 18 normalized kinds fails", not CM.validate_meta(dict(_m, kind="carousel"))[0])
check("D21-D05 pole: 18 kinds pinned", len(CM.KINDS) == 18)
check("D21-D06 control: matching stack passes", CM.resolve_stack(_m, _pr)[0])
check("D21-D06 pole: wrong framework fails", not CM.resolve_stack(_m, dict(_pr, framework="vue"))[0])
check("D21-D06 pole: tailwind major mismatch fails", not CM.resolve_stack(_m, dict(_pr, tailwind="4.0"))[0])
check("D21-D06 pole: UNKNOWN a11y is not a pass", not CM.resolve_stack(dict(_m, aria="UNKNOWN"), _pr)[0])
check("D21-D06 pole: unconfirmed SSR fails under SSR project", not CM.resolve_stack(dict(_m, ssr_safe=None), _pr)[0])
_a = {"name": "a", "source": "x", "spacing_scale": "4", "type_scale": "t", "palette": "p", "z_index": 10, "button_variants": ["primary"], "deps": {"react": "18"}, "project_design_md": "d"}
_b = dict(_a, name="b", source="y", z_index=20, button_variants=["ghost"])
check("D21-D08 control: coherent parts pass", CM.composition_qa([_a, _b])[0])
check("D21-D08 pole: z-index collision", not CM.composition_qa([_a, dict(_b, z_index=10)])[0])
check("D21-D08 pole: duplicate button variant", not CM.composition_qa([_a, dict(_b, button_variants=["primary"])])[0])
check("D21-D08 pole: dependency version conflict", not CM.composition_qa([_a, dict(_b, deps={"react": "19"})])[0])
check("D21-D08 pole: mixed spacing scale", not CM.composition_qa([_a, dict(_b, spacing_scale="8")])[0])
check("D21-D08 pole: second DESIGN.md truth", not CM.composition_qa([_a, dict(_b, project_design_md="other")])[0])
check("D21-D08 pole: card soup", not CM.composition_qa([dict(_a, card=True, z_index=i, button_variants=[f"v{i}"]) for i in range(5)])[0])

# D21-E05/E06/E07 motion selection, semantics, runtime report
from modules.cdicf import motion_select as MS  # noqa: E402
_d = {"choice": "css_transition", "criteria": {c: "x" for c in MS.CRITERIA}, "baseline_no_motion_compared": True}
check("D21-E05 control: CSS choice with criteria and baseline passes", MS.check_motion_decision(_d)[0])
check("D21-E05 pole: library without CSS/WAAPI insufficiency reason fails", not MS.check_motion_decision(dict(_d, choice="anime_js"))[0])
check("D21-E05 control: library with insufficiency reason passes", MS.check_motion_decision(dict(_d, choice="anime_js", css_waapi_insufficient="timeline sequencing"))[0])
check("D21-E05 pole: popularity as reason fails", not MS.check_motion_decision(dict(_d, reasons=["trending"]))[0])
check("D21-E05 pole: missing no-motion baseline fails", not MS.check_motion_decision(dict(_d, baseline_no_motion_compared=False))[0])
check("D21-E05 pole: missing criterion fails", not MS.check_motion_decision(dict(_d, criteria={}))[0])
check("D21-E05 control: no_animation with reason is valid", MS.check_motion_decision({"choice": "no_animation", "purpose_absent_reason": "static ledger"})[0])
check("D21-E05 pole: no_animation without reason fails", not MS.check_motion_decision({"choice": "no_animation"})[0])
check("D21-E05 pole: bespoke JS without cleanup plan fails", not MS.check_motion_decision(dict(_d, choice="bespoke_js", css_waapi_insufficient="x"))[0])
_c = {"expressiveness": "restrained", "motion_budget": "low"}
_an = {"level": "low", "reduced_motion_equivalent": True, "fake_loading": False, "progress_illusion": False, "nondeterministic_state": False}
check("D21-E06 control: within budget with equivalents passes", MS.check_motion_semantics(_c, _an)[0])
check("D21-E06 pole: over budget fails", not MS.check_motion_semantics(_c, dict(_an, level="high"))[0])
check("D21-E06 pole: expressiveness none permits no animation", not MS.check_motion_semantics({"expressiveness": "none", "motion_budget": "none"}, _an)[0])
check("D21-E06 control: expressiveness none with level none passes", MS.check_motion_semantics({"expressiveness": "none", "motion_budget": "none"}, dict(_an, level="none"))[0])
check("D21-E06 pole: fake loading fails", not MS.check_motion_semantics(_c, dict(_an, fake_loading=True))[0])
check("D21-E06 pole: unmeasured progress illusion is not a pass", not MS.check_motion_semantics(_c, {k: v for k, v in _an.items() if k != "progress_illusion"})[0])
check("D21-E06 pole: no reduced-motion equivalent fails", not MS.check_motion_semantics(_c, dict(_an, reduced_motion_equivalent=None))[0])
check("D21-E06 pole: incoherent contract refused", not MS.check_motion_semantics({"expressiveness": "none", "motion_budget": "high"}, _an)[0])
_rep = {"results": {k: {"observed": True, "evidence": "trace", "pass": True} for k in MS.RUNTIME_CASES}}
check("D21-E07 control: full observed report passes", MS.check_runtime_report(_rep)[0])
check("D21-E07 pole: absent case is unobserved", not MS.check_runtime_report({"results": {k: v for k, v in _rep["results"].items() if k != "touch"}})[0])
check("D21-E07 pole: claimed pass without evidence fails", not MS.check_runtime_report({"results": dict(_rep["results"], keyboard={"observed": True, "pass": True})})[0])
check("D21-E07 pole: failed case fails", not MS.check_runtime_report({"results": dict(_rep["results"], interrupted={"observed": True, "evidence": "t", "pass": False})})[0])
check("D21-E07 pole: 12 runtime cases pinned", len(MS.RUNTIME_CASES) == 12)

# D21-H01/H02/F06 routing, selection, material arbitration
from modules.cdicf import source_route as SR  # noqa: E402
_ev = {"spdx": "MIT", "version": "1.0", "license_sha256": "ab"}
_idx = [{"id": "z-anim", "layer": "motion", "sources": ["s"]}, {"id": "a-anim", "layer": "motion", "sources": ["s"]}, {"id": "ungrounded", "layer": "motion"}]
check("D21-H01 control: motion goal routes to grounded motion rows only, sorted", [r["id"] for r in SR.route("add a spring animation", _idx)["rows"]] == ["a-anim", "z-anim"])
check("D21-H01 pole: goal with no layer ABSTAINs", SR.route("make it nicer", _idx)["verdict"] == "ABSTAIN")
check("D21-H01 pole: layer with no grounded entry ABSTAINs", SR.route("show a map with markers", _idx)["verdict"] == "ABSTAIN")
_cs = [{"id": "b", "rights_status": "OPEN", "evidence": _ev, "frameworks": ["react"], "bundle_bytes": 900, "popularity": 1},
       {"id": "a", "rights_status": "OPEN", "evidence": _ev, "frameworks": ["react"], "bundle_bytes": 500, "popularity": 0},
       {"id": "r", "rights_status": "RESTRICTED", "evidence": _ev, "frameworks": ["react"], "bundle_bytes": 1, "popularity": 999}]
_s = SR.select(_cs, {"framework": "react"})
check("D21-H02 control: cheapest eligible first, popularity ignored", [o["id"] for o in _s["ranked"]] == ["a", "b"])
check("D21-H02 pole: restricted source refused despite top popularity", [o["id"] for o in _s["refused"]] == ["r"])
check("D21-H02 pole: deterministic for equal input under reordering", SR.select(list(reversed(_cs)), {"framework": "react"}) == _s)
check("D21-H02 pole: wrong framework refused", not SR.select(_cs, {"framework": "vue"})["ranked"])
check("D21-H02 pole: unmeasured cost sorts last and is flagged, not zero", SR.select([dict(_cs[0], id="u", bundle_bytes=None), _cs[0]], {"framework": "react"})["unmeasured_cost"] == ["u"])
_mat = {"material": "gradient", "benefits": ["hierarchy"], "baseline_opaque_compared": True, "fallback": "flat fill", "trust_posture": "standard"}
check("D21-F06 control: justified material with fallback passes", SR.arbitrate_material(_mat)[0])
check("D21-F06 pole: no benefit fails", not SR.arbitrate_material(dict(_mat, benefits=["trendy"]))[0])
check("D21-F06 pole: no opaque baseline comparison fails", not SR.arbitrate_material(dict(_mat, baseline_opaque_compared=None))[0])
check("D21-F06 pole: no fallback fails", not SR.arbitrate_material(dict(_mat, fallback=""))[0])
check("D21-F06 pole: glass on trust-critical surface fails", not SR.arbitrate_material(dict(_mat, material="glass", trust_posture="critical"))[0])

print(f"{'PASS' if not FAILS else 'FAIL'}: {len(FAILS)} failures")
sys.exit(1 if FAILS else 0)
