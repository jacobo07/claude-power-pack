"""V-BCAP2-ACT gate: BCAP-2 activation slice A (vault/specs/bcap2-activation.md), driven through the REAL
`modules.ccf.cli` with a counting fake provider. No network, no API key, no paid call.

AC2 report mode is neutral: a config with no declared inputs gives UNASSESSED everywhere and the run is unchanged;
    a config with FAILING inputs in report mode yields the same exit code, prompts, scans and provider calls.
AC3 per check, under enforce: FAIL input blocks (exit 3), PASS input passes, absent input blocks (UNASSESSED).
AC4 provider_policy under enforce refuses BEFORE the provider: adapter call count stays 0.
AC5 critique under enforce: a non-human actor cannot approve, and no selection is persisted.
AC6 seeded mutants (UNASSESSED counted as passing; enforce branch skipped) each turn a named pole red.
    python tools/test_bcap2_activation.py   (exit 0 == PASS)
"""
from __future__ import annotations

import base64
import contextlib
import copy
import io
import json
import struct
import sys
import tempfile
import types
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from modules.ccf import cli, creative_checks, knowledge_feed, model_adapter  # noqa: E402

FAILS: list = []
CALLS: list = []


def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (f" -- {d}" if d and not c else ""))
    if not c:
        FAILS.append(n)


def _png():
    def ch(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + b"".join(bytes((20, 20, 20) if (x // 8 + y // 8) % 2 else (240, 240, 240))
                                       for x in range(32)) for y in range(32))
    return (b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", 32, 32, 8, 2, 0, 0, 0))
            + ch(b"IDAT", zlib.compress(raw)) + ch(b"IEND", b""))


MARK = _png()


class FakeAdapter:
    def generate(self, prompt, params=None):
        CALLS.append(prompt)
        return model_adapter.ImageArtifact(status="OK", provider="fake", model_id="fake-1",
                                           bytes_=base64.b64encode(MARK), format="png", resolution="32x32",
                                           latency_ms=1.0, request_id="r1")


ICONS = {"ring": "hexagonal honeycomb of amber cells", "bars": "three offset vertical bars",
         "tri": "stacked triangular lattice of small nodes"}


def base_cfg(ids=("ring", "bars", "tri")):
    return {"schema_version": "1.0", "theme": "modern", "accent": "#112233", "headFont": "Poppins", "labels": [],
            "concepts": [{"id": i, "font": "Poppins", "colours": ["#112233"], "bg": "#FFFFFF", "wordmark": "Orbit",
                          "avoid": [], "icon": ICONS[i]} for i in ids]}


DNA_OK = {"schema_version": "1.0", "brand_id": "orbit", "approved_brief_ref": "brief-1", "territory": "craft",
          "symbol_strategy": "abstract", "geometric_constraints": ["grid 8"], "shape_language": "rounded",
          "relative_proportion": "1:1", "palette_roles": {"primary": "#112233", "surface": "#FFFFFF"},
          "typography": {"family": "Poppins", "source": "google-fonts"}, "spacing": "8pt", "variants": ["mono"],
          "forbidden_patterns": ["gradients"], "avatar_rules": "circle crop", "small_size_rules": "16px mark only",
          "applications": ["app icon"], "selection_evidence": {"selected_by": "owner", "critique_ref": "c-1"}}
IDSET_OK = {"comparison_axes": ["warm/cold", "geometric/organic"], "rationale": "craft over speed",
            "category_default_challenge": "dev tools default to blue; we use amber",
            "palette": {"text": "#111111", "surface": "#FFFFFF"}, "typography_test": {"observed": "legible at 12px"}}
HYP_OK = {"technique": "symbol_fusion", "brand_observation": "orbit tools are built slowly by careful devs",
          "recipe": ["union the ring and the bar", "offset the bar by one grid unit"]}
ALL_EVIDENCE = [{"criterion": c, "kind": "evidence", "value": True, "instrument": "scan-v1"}
                for c in ("meaningfulness", "silhouette", "category_fit", "genericity", "spelling",
                          "constructability", "emotion_fit", "user_intent")]

# per generate-stage check: (mutate config to PASS, mutate config to FAIL)
def _bt_pass(c): c["brand_truth"] = [{"field": "purpose", "value": "tools for craft", "origin": "stated"}]
def _bt_fail(c): c["brand_truth"] = [{"field": "purpose", "value": "tools", "origin": "observed"}]
def _te_pass(c):
    for i, k in enumerate(c["concepts"]):
        k["mechanism"], k["brand_fact"] = ("symbol", "monogram", "geometric")[i], f"fact {i}"
def _te_fail(c):
    for k in c["concepts"]:
        k["mechanism"], k["brand_fact"] = "symbol", "same fact"
def _hy_pass(c): c["concepts"][0]["hypothesis"] = dict(HYP_OK)
def _hy_fail(c): c["concepts"][0]["hypothesis"] = dict(HYP_OK, technique="magic sauce")
def _id_pass(c): c["identity_set"] = copy.deepcopy(IDSET_OK)
def _id_fail(c): c["identity_set"] = dict(copy.deepcopy(IDSET_OK), palette={"text": "#EEEEEE", "surface": "#FFFFFF"})
def _dn_pass(c): c["visual_dna"] = copy.deepcopy(DNA_OK)
def _dn_fail(c): c["visual_dna"] = {"schema_version": "1.0", "brand_id": "orbit"}
def _pp_pass(c):
    for k in c["concepts"]:
        k["provider_intent"] = {"deterministic_possible": False, "needs": ["photoreal texture"]}
def _pp_fail(c):
    for k in c["concepts"]:
        k["provider_intent"] = {"deterministic_possible": True}

GEN = {"brand_truth": (_bt_pass, _bt_fail), "territories": (_te_pass, _te_fail), "techniques": (_hy_pass, _hy_fail),
       "identity_set": (_id_pass, _id_fail), "visual_dna": (_dn_pass, _dn_fail), "provider_policy": (_pp_pass, _pp_fail)}


def project(tmp, name, config):
    p = tmp / name
    (p / ".ccf").mkdir(parents=True)
    (p / "config.json").write_text(json.dumps(config), encoding="utf-8")
    (p / "spec.json").write_text(json.dumps({"brand_name": "Orbit", "industry": "tools", "audience": "devs",
                                              "values": ["craft"]}), encoding="utf-8")
    return p


def run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli.main(argv)
    return code, buf.getvalue()


def gen(p):
    n0 = len(CALLS)
    code, out = run(["generate", str(p)])
    return code, len(CALLS) - n0, out


def report(p):
    f = p / ".ccf" / "creative_checks.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def state(p):
    """Behaviour-bearing outputs. `input_hash` is dropped: prompt_compiler records it as provenance of the concept
    dict ("not asserted"), so a concept that declares mechanism/hypothesis/provider_intent is honestly a different
    input. Prompt text, avoid lists and scan verdicts are what the run actually does."""
    prompts = json.loads((p / ".ccf" / "prompts.json").read_text(encoding="utf-8"))
    for rec in prompts.values():
        rec.pop("input_hash", None)
    return {"prompts": json.dumps(prompts, sort_keys=True),
            "scan_report.json": (p / ".ccf" / "scan_report.json").read_text(encoding="utf-8")}


def hashes(p):
    prompts = json.loads((p / ".ccf" / "prompts.json").read_text(encoding="utf-8"))
    return {k: v.get("input_hash") for k, v in prompts.items()}


def poles(tmp, tag):
    """The enforce poles as booleans, so a mutant can be judged on the same names."""
    res = {}
    c = base_cfg(); c["creative_checks"] = {"territories": "enforce"}
    code, calls, _ = gen(project(tmp, f"{tag}-absent", c))
    res["absent-enforce-blocks"] = code == cli.EXIT_GATE_BLOCKED and calls == 0
    c = base_cfg(); _te_fail(c); c["creative_checks"] = {"territories": "enforce"}
    code, calls, _ = gen(project(tmp, f"{tag}-fail", c))
    res["fail-enforce-blocks"] = code == cli.EXIT_GATE_BLOCKED and calls == 0
    return res


with tempfile.TemporaryDirectory() as t:
    t = Path(t)
    knowledge_feed.FEED_DIR = t / "feed"
    for n in ("CREATIVE_FAILURES_PATH", "PROVIDER_BENCHMARKS_PATH", "TRADEMARK_RISK_PATH"):
        setattr(knowledge_feed, n, knowledge_feed.FEED_DIR / getattr(knowledge_feed, n).name)
    cli.model_adapter.GPTImage2Adapter = FakeAdapter

    # ---- AC2: no declared inputs -> 6x UNASSESSED, exit and provider calls as before
    plain = project(t, "plain", base_cfg())
    code, calls, out = gen(plain)
    gr = report(plain).get("generate", {})
    check("AC2 plain config: exit 0 and every concept reaches the provider", code == 0 and calls == 3, f"code={code} calls={calls}")
    check("AC2 plain config: the 6 generate checks are UNASSESSED in report mode",
          len(gr.get("checks", {})) == 6 and all(r["status"] == "UNASSESSED" and r["mode"] == "report"
                                                for r in gr.get("checks", {}).values()), json.dumps(gr)[:300])
    check("AC2 plain config: one summary line is printed", "creative checks (generate):" in out)

    # report mode with FAILING inputs everywhere: same exit, same prompts/scans, same provider calls
    noisy_cfg = base_cfg()
    for _p, fail in GEN.values():
        fail(noisy_cfg)
    noisy = project(t, "noisy", noisy_cfg)
    code_n, calls_n, _ = gen(noisy)
    nr = report(noisy).get("generate", {}).get("checks", {})
    check("AC2 report mode is neutral: failing inputs do not change exit or provider calls",
          code_n == code and calls_n == calls, f"code={code_n} calls={calls_n}")
    check("AC2 report mode is neutral: prompt text, avoid lists and scans identical to the plain run",
          state(noisy) == state(plain))
    cfg_only = base_cfg()
    for name in ("brand_truth", "identity_set", "visual_dna"):
        GEN[name][1](cfg_only)
    co = project(t, "cfg-only", cfg_only)
    gen(co)
    check("AC2 config-level inputs leave even the concept input_hash untouched", hashes(co) == hashes(plain))
    check("AC2 concept-level inputs change only input_hash (declared provenance), never the prompt",
          hashes(noisy) != hashes(plain) and state(noisy) == state(plain))
    check("AC2 report mode still records every FAIL", all(r["status"] == "FAIL" for r in nr.values()),
          json.dumps({k: v["status"] for k, v in nr.items()}))

    # ---- AC3/AC4: per generate check, enforce + PASS passes, enforce + FAIL blocks before the provider
    for name, (mk_pass, mk_fail) in GEN.items():
        c = base_cfg(); mk_pass(c); c["creative_checks"] = {name: "enforce"}
        code, calls, _ = gen(project(t, f"{name}-pass", c))
        check(f"AC3 {name}: enforce + PASS input runs (exit 0, provider reached)", code == 0 and calls == 3,
              f"code={code} calls={calls} rep={json.dumps(report(t / f'{name}-pass').get('generate', {}).get('checks', {}).get(name))[:300]}")
        c = base_cfg(); mk_fail(c); c["creative_checks"] = {name: "enforce"}
        p = project(t, f"{name}-fail", c)
        code, calls, _ = gen(p)
        check(f"AC3/AC4 {name}: enforce + FAIL input blocks with exit 3 and 0 provider calls",
              code == cli.EXIT_GATE_BLOCKED and calls == 0, f"code={code} calls={calls}")
        check(f"AC3 {name}: the block is recorded in creative_checks.json",
              name in report(p).get("generate", {}).get("blocking", []))
        c = base_cfg(); c["creative_checks"] = {name: "enforce"}
        code, calls, _ = gen(project(t, f"{name}-absent", c))
        check(f"AC3 {name}: enforce + absent input blocks (UNASSESSED is not a pass)",
              code == cli.EXIT_GATE_BLOCKED and calls == 0, f"code={code} calls={calls}")

    # config errors are refused, not silently treated as report
    c = base_cfg(); c["creative_checks"] = {"territories": "maybe"}
    code, calls, _ = gen(project(t, "badmode", c))
    check("config: an unknown mode is a validation error (exit 1), no provider call", code == 1 and calls == 0)
    c = base_cfg(); c["creative_checks"] = {"vibes": "enforce"}
    code, calls, _ = gen(project(t, "badname", c))
    check("config: an unknown check name is a validation error (exit 1)", code == 1 and calls == 0)

    # dry run persists nothing
    c = base_cfg(); _te_fail(c); c["creative_checks"] = {"territories": "enforce"}
    p = project(t, "dry", c)
    code, out = run(["generate", str(p), "--dry-run"])
    check("dry-run: reports the would-block, persists no creative_checks.json",
          "would block" in out and not (p / ".ccf" / "creative_checks.json").exists(), out[-300:])

    # ---- AC5: critique at select
    def sel_project(name, crit, mode):
        c = base_cfg()
        if crit is not None:
            c["critiques"] = crit
        if mode:
            c["creative_checks"] = {"critique": mode}
        p = project(t, name, c)
        gen(p)
        return p

    two_ok = {"ring": ALL_EVIDENCE, "bars": ALL_EVIDENCE}
    p = sel_project("crit-owner", two_ok, "enforce")
    code, _ = run(["select", str(p), "--concept", "ring", "--by", "owner"])
    check("AC5 critique enforce: owner among 2 qualifying directions selects (exit 0, selection saved)",
          code == 0 and (p / ".ccf" / "selection.json").exists(), f"code={code}")
    p = sel_project("crit-llm", two_ok, "enforce")
    code, _ = run(["select", str(p), "--concept", "ring", "--by", "llm"])
    check("AC5 critique enforce: a non-human actor cannot approve (exit 3, no selection persisted)",
          code == cli.EXIT_GATE_BLOCKED and not (p / ".ccf" / "selection.json").exists(), f"code={code}")
    p = sel_project("crit-one", {"ring": ALL_EVIDENCE}, "enforce")
    code, _ = run(["select", str(p), "--concept", "ring", "--by", "owner"])
    check("AC5 critique enforce: one qualifying direction is not a choice (exit 3)", code == cli.EXIT_GATE_BLOCKED)
    p = sel_project("crit-absent", None, "enforce")
    code, _ = run(["select", str(p), "--concept", "ring", "--by", "owner"])
    check("AC5 critique enforce: no critiques declared blocks (UNASSESSED)", code == cli.EXIT_GATE_BLOCKED)
    p = sel_project("crit-report", None, None)
    code, _ = run(["select", str(p), "--concept", "ring", "--by", "llm"])
    check("AC5 report mode: select behaves as before (exit 0) and records critique UNASSESSED",
          code == 0 and report(p).get("select", {}).get("checks", {}).get("critique", {}).get("status") == "UNASSESSED")

    # ---- AC6: seeded mutants must turn a named pole red
    base = poles(t, "real")
    check("AC6 control: real module holds both poles", all(base.values()), json.dumps(base))
    src = (ROOT / "modules/ccf/creative_checks.py").read_text(encoding="utf-8")
    muts = [("unassessed-counts-as-pass", 'PASSING = ("PASS", "NARROW_BRIEF_EXCEPTION")',
             'PASSING = ("PASS", "NARROW_BRIEF_EXCEPTION", "UNASSESSED")', "absent-enforce-blocks"),
            ("enforce-branch-skipped", 'if rec["mode"] == "enforce" and rec["status"] not in PASSING:',
             "if False:", "fail-enforce-blocks")]
    real_mod = cli.creative_checks
    for mname, old, new, pole in muts:
        applied = src.count(old) == 1
        if applied:
            m = types.ModuleType("creative_checks_mutant")
            exec(compile(src.replace(old, new), "creative_checks_mutant", "exec"), m.__dict__)
            cli.creative_checks = m
            try:
                got = poles(t, mname)
            finally:
                cli.creative_checks = real_mod
        check(f"AC6 mutant {mname}: pole {pole} turns red", applied and got.get(pole) is False,
              f"applied={applied} got={got if applied else None}")

# --- Slice B: floor_guard in the done path, REPORT ONLY -------------------------------------------------
import importlib
import subprocess

floor_guard = importlib.import_module("modules.sqi.floor_guard")
SUPPRESS = "# no" + "qa"  # built, so this gate's own diff never reads as a new suppression


def _git(repo, *a):
    subprocess.run(["git", *a], cwd=repo, check=True, capture_output=True)


with tempfile.TemporaryDirectory() as td:
    repo = Path(td) / "r"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    (repo / "m.py").write_text("x = 1  # café\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "base")
    clean = floor_guard.report(repo)
    check("SB clean diff -> CLEAN", clean["status"] == floor_guard.CLEAN, json.dumps(clean))
    # A UTF-8 line beside the weakening: the cp1252 decoder used to turn every such diff into UNASSESSED.
    # Cyrillic A is bytes D0 90, and 0x90 is undefined in cp1252: without it this pole cannot go red.
    (repo / "m.py").write_text(f"x = 1  # café А\ny = 2  {SUPPRESS}\n", encoding="utf-8")
    dirty = floor_guard.report(repo)
    check("SB weakening diff (UTF-8 bytes) -> VIOLATIONS silenced-checker",
          dirty["status"] == floor_guard.VIOLATIONS
          and [v["rule"] for v in dirty["violations"]] == ["silenced-checker"], json.dumps(dirty))
    line = floor_guard.report_line(dirty)
    check("SB report line names status and rule", "VIOLATIONS 1 violation(s)" in line
          and "silenced-checker" in line, line)
    none = floor_guard.report(Path(td) / "not-a-repo-" / ".." / "nowhere")
    check("SB no repo -> UNASSESSED with reason, never CLEAN",
          none["status"] == floor_guard.UNASSESSED and none["error"], json.dumps(none))
    real_run = floor_guard.run
    floor_guard.run = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        crashed = floor_guard.report(repo)
    finally:
        floor_guard.run = real_run
    check("SB crashed guard -> UNASSESSED, does not raise",
          crashed["status"] == floor_guard.UNASSESSED and "boom" in crashed["error"], json.dumps(crashed))

# Both consumers call the report and neither lets it reach its exit code (report only, Owner pick (a)).
dg = (ROOT / "vault/programs/bcap-2/done_gate.py").read_text(encoding="utf-8")
sq = (ROOT / "tools/run_sqi.py").read_text(encoding="utf-8")
check("SB done_gate calls floor_guard.report and prints it",
      "floor_guard.report(ROOT" in dg and "floor_guard.report_line(fg)" in dg)
check("SB done_gate never adds floor_guard to bad", "bad.append" not in dg.split("floor_guard.report(ROOT")[1])
check("SB run_sqi calls floor_guard.report behind --floor-guard, prints and persists it",
      'if "--floor-guard" in argv:\n        fg = floor_guard.report(target)' in sq
      and '"floor_guard": fg' in sq and "SQI_FLOOR_GUARD" in sq)
nr = floor_guard.report_line({"status": "NOT_RUN", "base": "HEAD", "error": "opt-in: pass --floor-guard",
                              "violations": [], "waived": 0})
check("SB NOT_RUN prints its reason and no counts", "NOT_RUN -- opt-in" in nr and "violation" not in nr, nr)
check("SB run_sqi exit code ignores floor_guard",
      "fg" not in sq.split("if verdict.failing or weak.failing:")[1].split("if __name__")[0])

if FAILS:
    print(f"V-BCAP2-ACT FAIL ({len(FAILS)}): {FAILS}")
    sys.exit(1)
print("V-BCAP2-ACT PASS")
