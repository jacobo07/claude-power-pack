"""V-BCAP2-CLI15 gate: BI-15..35 on the real CCF path (BCAP2B phase 5, spec vault/specs/bcap2-activation.md rule).

The `package` stage of modules.ccf.creative_checks, reached through the REAL `modules.ccf.cli package`. No provider,
no network. Rule: absent input = UNASSESSED never FAIL; report mode never changes the exit code; under enforce a
FAIL or an absent input stops the stage BEFORE the brand package is written. Each check is driven from both poles.
    python tools/test_bcap2_cli15.py   (exit 0 == PASS)
"""
from __future__ import annotations

import contextlib
import copy
import io
import json
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from modules.ccf import cli, creative_checks  # noqa: E402

FAILS: list = []


def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (f" -- {d}" if d and not c else ""))
    if not c:
        FAILS.append(n)


def base_cfg():
    return {"schema_version": "1.0", "theme": "modern", "accent": "#112233", "headFont": "Poppins", "labels": [],
            "concepts": [{"id": "ring", "font": "Poppins", "colours": ["#112233"], "bg": "#FFFFFF",
                          "wordmark": "Orbit", "avoid": [], "icon": "hexagonal honeycomb of amber cells"}]}


SVG_OK = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><g data-part="icon"><rect width="4" height="4"/></g><g data-part="wordmark"><rect x="5" width="4" height="4"/></g></svg>'
SVG_TRACE_OK = b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0L1.5 1.5Z"/></svg>'
SVG_TRACE_BAD = b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0.123456 0L1.123456 1.5Z"/></svg>'
LENS_OK = {k: {"observed": True, "instrument": "scan-v1"} for k in
           ("spelling", "small_size", "silhouette", "negative_space", "monochrome", "dark_light", "print_web",
            "file_format", "font_glyph", "token_consumption", "provenance", "human_signoff")}
CATS = ("creation", "refresh_keep", "icon_only", "wordmark", "multilingual", "fashion_luxury", "software",
        "hospitality", "professional_services", "consumer_product", "adversarial_imitation")
BRIEFS_OK = [{"id": f"b{i}", "categories": [CATS[i % len(CATS)]] + ([CATS[(i + 1) % len(CATS)]] if i < 11 else []),
              "frozen_sha256": "ab" * 32} for i in range(12)]
PREVIEW_OK = {"contexts": [{"context": c, "visual_dna": "dna-1", "is_mock": True} for c in
                           ("masthead", "avatar", "favicon", "photography", "packaging", "print", "ad_overlay",
                            "mobile_screen", "social_canvas")]}
REG = {"Poppins": {"glyphs": "áéíóúüñÁÉÍÓÚÜÑ¿¡"}}
REVIEW_OK = {"reviewer": "alice", "implementer": "bob", "refusal_cases_proven": True, "commit_refs": ["abc"],
             "test_counts": {"pass": 3}, "revert_path": "git revert abc", "status": "DONE"}


def _w(p, rel, data):
    (p / rel).write_bytes(data)


# name -> (declare PASS input, declare FAIL input); both mutate config (and may write files into the project)
def _col_p(c, p): c["palette"] = {"ink": "#000000", "paper": "#FFFFFF"}; c["contrast_pairs"] = [{"fg": "ink", "bg": "paper", "context": "body"}]
def _col_f(c, p): c["palette"] = {"ink": "#777777", "paper": "#888888"}; c["contrast_pairs"] = [{"fg": "ink", "bg": "paper", "context": "body"}]
def _ex_p(c, p): c["export_profile"] = {"source_sha256": "a" * 64, "derivatives": [{"format": "svg"}]}
def _ex_f(c, p): c["export_profile"] = {"derivatives": [{"format": "png", "size": 64, "generated_independently": True}]}
def _tk_p(c, p): c["design_tokens"] = {"color": {"ink": {"$value": "#000", "$type": "color"}}}
def _tk_f(c, p): c["design_tokens"] = {"color": {"ink": {"$value": "{color.nope}", "$type": "color"}}}
def _pv_p(c, p): c["visual_dna"] = {"id": "dna-1"}; c["application_preview"] = copy.deepcopy(PREVIEW_OK)
def _pv_f(c, p):
    c["visual_dna"] = {"id": "dna-1"}
    c["application_preview"] = {"contexts": [dict(PREVIEW_OK["contexts"][0], visual_dna="other")]}
def _lc_p(c, p): c["language_coverage"] = {"font": "Poppins", "registry": REG, "langs": ["ES", "EN"]}
def _lc_f(c, p): c["language_coverage"] = {"font": "Ghost", "registry": REG}
def _ll_p(c, p): c["logo_review"] = copy.deepcopy(LENS_OK)
def _ll_f(c, p): c["logo_review"] = dict(copy.deepcopy(LENS_OK), spelling={"observed": False, "instrument": "scan-v1"})
def _sm_p(c, p): c["similarity"] = {"corpus": {"size": 100, "provenance_logged": True}, "nearest": [{"score": 0.2}]}
def _sm_f(c, p): c["similarity"] = {"corpus": {"size": 100, "provenance_logged": True}, "nearest": [{"score": 0.95}]}
def _bm_p(c, p): c["benchmark_briefs"] = copy.deepcopy(BRIEFS_OK)
def _bm_f(c, p): c["benchmark_briefs"] = copy.deepcopy(BRIEFS_OK)[:3]
def _ir_p(c, p): c["independent_review"] = dict(REVIEW_OK)
def _ir_f(c, p): c["independent_review"] = dict(REVIEW_OK, reviewer="bob")
def _tp_p(c, p): _w(p, "logo.svg", SVG_OK); c["typed_parts"] = {"svg_path": "logo.svg"}
def _tp_f(c, p): _w(p, "logo.svg", b'<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>'); c["typed_parts"] = {"svg_path": "logo.svg"}
def _tr_p(c, p): _w(p, "t.svg", SVG_TRACE_OK); c["trace"] = {"svg_path": "t.svg", "decision": "inspect"}
def _tr_f(c, p): _w(p, "t.svg", SVG_TRACE_BAD); c["trace"] = {"svg_path": "t.svg", "decision": "inspect"}

import hashlib
def _man(p, tamper=False):
    data = b"logo-bytes"
    _w(p, "mark.svg", b"tampered" if tamper else data)
    return {"manifest": {"version": "1", "files": {"mark.svg": {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}}},
            "files": ["mark.svg"]}
def _rm_p(c, p): c["release_manifest"] = _man(p)
def _rm_f(c, p): c["release_manifest"] = _man(p, True)

POLES = {"release_manifest": (_rm_p, _rm_f), "brand_color": (_col_p, _col_f), "export_profile": (_ex_p, _ex_f), "design_tokens": (_tk_p, _tk_f),
         "application_preview": (_pv_p, _pv_f), "language_coverage": (_lc_p, _lc_f), "logo_lens": (_ll_p, _ll_f),
         "similarity": (_sm_p, _sm_f), "benchmark": (_bm_p, _bm_f), "independent_review": (_ir_p, _ir_f),
         "typed_parts": (_tp_p, _tp_f), "trace": (_tr_p, _tr_f)}


def project(tmp, name, config, mutate=None):
    p = tmp / name
    (p / ".ccf").mkdir(parents=True)
    if mutate:
        mutate(config, p)
    (p / "config.json").write_text(json.dumps(config), encoding="utf-8")
    (p / "spec.json").write_text(json.dumps({"brand_name": "Orbit", "industry": "tools", "audience": "devs",
                                              "values": ["craft"]}), encoding="utf-8")
    (p / ".ccf" / "selection.json").write_text(json.dumps({"concept_id": "ring", "by": "owner"}), encoding="utf-8")
    return p


def package(p):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli.main(["package", str(p)])
    return code, buf.getvalue()


def rec(p, name):
    f = p / ".ccf" / "creative_checks.json"
    return json.loads(f.read_text(encoding="utf-8"))["package"]["checks"][name] if f.exists() else None


def poles(tmp, tag, runner):
    res = {}
    for name, (mk_p, mk_f) in POLES.items():
        for kind, mk in (("pass", mk_p), ("fail", mk_f)):
            c = base_cfg()
            c["creative_checks"] = {name: "enforce"}
            res[(name, kind)] = runner(project(tmp, f"{tag}-{name}-{kind}", c, mk), name)
        res[(name, "absent")] = runner(project(tmp, f"{tag}-{name}-absent", dict(base_cfg(), creative_checks={name: "enforce"})), name)
    return res


def blocked_before_build(p, code, out):
    return code == cli.EXIT_GATE_BLOCKED and "enforced creative check" in out and not (p / "brandkit.pdf").exists()


def main():
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        # AC2: a config declaring nothing -> every package check UNASSESSED, exit unchanged by the gate
        p = project(t, "empty", base_cfg())
        code, out = package(p)
        names = creative_checks.STAGES["package"]
        check("12 package checks registered (BI-15,17,18,19,20,22/23,25,26,28,29,31,35)", len(names) == 12, str(names))
        check("empty config: every package check UNASSESSED (absent is not FAIL)",
              all(rec(p, n)["status"] == "UNASSESSED" and rec(p, n)["mode"] == "report" for n in names),
              str({n: (rec(p, n) or {}).get("status") for n in names}))
        check("empty config: the gate never blocks (exit is not the gate's EXIT_GATE_BLOCKED with enforcement text)",
              "enforced creative check" not in out, out[-300:])
        check("summary line printed for package", "creative checks (package):" in out)

        # report mode with FAILING inputs: records FAIL, does not block
        for name, (_, mk_f) in POLES.items():
            c = base_cfg()
            q = project(t, f"rep-{name}", c, mk_f)
            code, out = package(q)
            r = rec(q, name)
            check(f"{name} report mode: FAIL input recorded as FAIL and does not enforce",
                  r is not None and r["status"] == "FAIL" and r["mode"] == "report" and "enforced creative check" not in out,
                  str(r))

        # enforce poles through the real CLI
        def run(p, name):
            code, out = package(p)
            return {"blocked": blocked_before_build(p, code, out), "status": (rec(p, name) or {}).get("status")}
        res = poles(t, "enf", run)
        for name in POLES:
            check(f"{name} enforce: PASS input is not blocked by this check",
                  not res[(name, "pass")]["blocked"] and res[(name, "pass")]["status"] == "PASS", str(res[(name, "pass")]))
            check(f"{name} enforce: FAIL input blocks BEFORE the package is written",
                  res[(name, "fail")]["blocked"] and res[(name, "fail")]["status"] == "FAIL", str(res[(name, "fail")]))
            check(f"{name} enforce: absent input blocks (asked for the check, supplied nothing)",
                  res[(name, "absent")]["blocked"] and res[(name, "absent")]["status"] == "UNASSESSED",
                  str(res[(name, "absent")]))

        # path inputs: traversal / missing file are FAIL, never a read outside the project
        for rel in ("../escape.svg", "/etc/passwd", "nope.svg"):
            c = base_cfg(); c["trace"] = {"svg_path": rel, "decision": "inspect"}
            q = project(t, f"path-{abs(hash(rel))}", c)
            package(q)
            r = rec(q, "trace")
            check(f"trace svg_path {rel!r}: FAIL, not read", r and r["status"] == "FAIL", str(r))

        # config errors are loud
        c = base_cfg(); c["creative_checks"] = {"brand_colour": "enforce"}
        q = project(t, "typo", c)
        code, out = package(q)
        check("unknown check name in creative_checks is a validation error at package",
              code == cli.EXIT_VALIDATION_ERROR and "unknown check" in out, out[-200:])

        # mutants: UNASSESSED counted as passing, enforce skipped -> a named pole turns red
        src = (ROOT / "modules/ccf/creative_checks.py").read_text(encoding="utf-8")
        real = cli.creative_checks
        for tag, old, new in (("unassessed-passes", 'PASSING = ("PASS", "NARROW_BRIEF_EXCEPTION")',
                               'PASSING = ("PASS", "NARROW_BRIEF_EXCEPTION", "UNASSESSED")'),
                              ("enforce-skipped", 'if rec["mode"] == "enforce" and', 'if False and')):
            check(f"mutant {tag}: the substitution applies", old in src)
            m = types.ModuleType("cc_mutant")
            exec(compile(src.replace(old, new), "cc_mutant", "exec"), m.__dict__)
            cli.creative_checks = m
            try:
                mres = poles(t, f"mut-{tag}", run)
            finally:
                cli.creative_checks = real
            red = [k for k in mres if k[1] != "pass" and not mres[k]["blocked"]]
            check(f"mutant {tag}: turns at least one enforce pole red", bool(red))

    print("V-BCAP2-CLI15", "FAIL " + str(FAILS) if FAILS else f"PASS")
    return 1 if FAILS else 0


sys.exit(main())
