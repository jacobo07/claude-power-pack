#!/usr/bin/env python3
"""Hermetic done-gate for the Cognitive Leak Taxonomy sprint (SCS C70).

Five V-gates:
  V-TAXONOMY-COMPLETE   -- every leak family + hypothesis is in the backing doc
  V-ROI-RANKED          -- doc ranks by ROI (quick-wins / strategic / not-worth)
  V-FIXES-MEASURED      -- the 3 built fixes' measurement fns work on synthetic
                           input (L-SCHED classify, L-SELFCORR gate, P5/PM-03)
  V-NO-REGRESSION       -- C68 + C69 hermetic suites still pass (run them)
  V-EXTENDS-NOT-DUPLICATES -- fixes extend existing tools; no parallel .jsonl reader

Pure classifiers only touch synthetic dicts/strings; the OS/live readers are not
exercised. Run 3x -> DOMAIN_PASS constant.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent

_passes = 0
_fails = 0


def _ok(g, ev):
    global _passes
    _passes += 1
    print(f"  PASS {g}: {ev}")


def _fail(g, ev):
    global _fails
    _fails += 1
    print(f"  FAIL {g}: {ev}")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # dataclass string-annotation resolution needs this
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    STH = _load(_HERE / "scheduled_task_health.py", "scheduled_task_health")
    VBE = _load(_ROOT / "modules" / "wrapper" / "verify_before_emit.py",
                "verify_before_emit")
    CQA = _load(_HERE / "conversation_quality_audit.py",
                "conversation_quality_audit")

    # ---- V-FIXES-MEASURED : L-SCHED classifier (pure) --------------------
    fail_v = STH.classify_task({"name": "a", "last_result": 2,
                                "last_run_epoch": 900, "now_epoch": 1000,
                                "interval_seconds": 86400})
    stale_v = STH.classify_task({"name": "b", "last_result": 0,
                                 "last_run_epoch": 0, "now_epoch": 2 * 3600,
                                 "interval_seconds": 300})
    hf_v = STH.classify_task({"name": "c", "last_result": 0,
                              "last_run_epoch": 940, "now_epoch": 1000,
                              "interval_seconds": 300})
    ok_v = STH.classify_task({"name": "d", "last_result": 0,
                              "last_run_epoch": 940, "now_epoch": 1000,
                              "interval_seconds": 86400})
    # a DISABLED task with a failing last_result is resolved, NOT a live leak
    dis_v = STH.classify_task({"name": "e", "state": "Disabled",
                               "last_result": 2, "now_epoch": 1000})
    if (fail_v.verdict == "FAILING" and stale_v.verdict == "STALE"
            and hf_v.verdict == "HIGH_FREQ" and ok_v.verdict == "OK"
            and dis_v.verdict == "DISABLED"):
        _ok("V-FIXES-MEASURED/L-SCHED",
            "FAILING/STALE/HIGH_FREQ/OK/DISABLED classified correctly")
    else:
        _fail("V-FIXES-MEASURED/L-SCHED",
              f"{fail_v.verdict}/{stale_v.verdict}/{hf_v.verdict}/"
              f"{ok_v.verdict}/{dis_v.verdict}")

    # ---- V-FIXES-MEASURED : L-SELFCORR verify-before-emit ----------------
    a_advise = VBE.verify_before_emit("All done, I fixed the bug.", "")
    a_evid_draft = VBE.verify_before_emit("Fixed it. exit=0, 6/6 passed.", "")
    a_evid_stream = VBE.verify_before_emit("It works now.", "PASS DOMAIN_PASS=6/6")
    a_negated = VBE.verify_before_emit("This is not done yet.", "")
    a_noclaim = VBE.verify_before_emit("Here is the analysis of the module.", "")
    if (a_advise.advise is True and a_evid_draft.advise is False
            and a_evid_stream.advise is False and a_negated.advise is False
            and a_noclaim.advise is False):
        _ok("V-FIXES-MEASURED/L-SELFCORR",
            "claim-without-evidence advises; evidence(draft|stream)/negation/"
            "no-claim stay silent")
    else:
        _fail("V-FIXES-MEASURED/L-SELFCORR",
              f"{a_advise.advise}/{a_evid_draft.advise}/{a_evid_stream.advise}/"
              f"{a_negated.advise}/{a_noclaim.advise}")

    # ---- V-FIXES-MEASURED : P5/PM-03 population probe ---------------------
    with tempfile.TemporaryDirectory() as td:
        empty = Path(td) / "empty"
        empty.mkdir()
        h_empty = CQA.pm03_health(state_dir=str(empty))
        (empty / "findings_bus_repoX.jsonl").write_text(
            json.dumps({"topic": "t", "claim": "c"}) + "\n"
            + json.dumps({"topic": "t2", "claim": "c2"}) + "\n",
            encoding="utf-8")
        h_pop = CQA.pm03_health(state_dir=str(empty))
    if (h_empty["wired"] is False and h_pop["wired"] is True
            and h_pop["findings"] == 2):
        _ok("V-FIXES-MEASURED/P5-PM03",
            f"bus population measured: empty->wired=False, 2 lines->findings=2")
    else:
        _fail("V-FIXES-MEASURED/P5-PM03", f"{h_empty} / {h_pop}")

    # ---- V-EXTENDS-NOT-DUPLICATES ---------------------------------------
    sth_src = (_HERE / "scheduled_task_health.py").read_text(encoding="utf-8")
    extends = hasattr(CQA, "pm03_health") and hasattr(CQA, "iter_transcripts")
    no_parallel_reader = "jsonl" not in sth_src.lower()  # L-SCHED reads schtasks
    if extends and no_parallel_reader:
        _ok("V-EXTENDS-NOT-DUPLICATES",
            "pm03_health added to CQA (reuses its reader); scheduled_task_health "
            "reads schtasks, no parallel .jsonl reader")
    else:
        _fail("V-EXTENDS-NOT-DUPLICATES",
              f"extends={extends} no_parallel_reader={no_parallel_reader}")

    # ---- V-PM03-WIRED : consume hook shipped in the hub + bus round-trips -
    hub_src = (_ROOT / "hooks" / "session_start_hub.js").read_text(
        encoding="utf-8")
    hub_wired = ("function hookFindingsBusDigest(" in hub_src
                 and "const busLine = hookFindingsBusDigest(cwd)" in hub_src)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "findings_bus_r.jsonl").write_text(
            json.dumps({"topic": "t", "claim": "c", "ts": "2026-07-03"}) + "\n",
            encoding="utf-8")
        bus_wired = CQA.pm03_health(state_dir=str(d))["wired"]
    if hub_wired and bus_wired is True:
        _ok("V-PM03-WIRED",
            "SessionStart Findings-Bus digest hook shipped in hub + main() calls "
            "it; bus-consume round-trips (live sync + restart is Owner-side)")
    else:
        _fail("V-PM03-WIRED", f"hub_wired={hub_wired} bus_wired={bus_wired}")

    # ---- V-SCS-NO-COLLISION : the C69 dual-seal was reassigned to C71 -----
    kb = _ROOT / "vault" / "knowledge_base"
    gdir = kb / "graphify"
    old_gone = not (gdir / "graphify_scs_c69.md").exists()
    new_exists = (gdir / "graphify_scs_c71.md").exists()
    # A graphify file "still seals C69" only if a line claims SCS C69 WITHOUT
    # naming C71. A reassignment/history line names BOTH (e.g. "SCS C69->C71
    # collision fix") -- that documents the fix, it is not a live collision.
    def _still_seals_c69(text: str) -> bool:
        return any("SCS C69" in ln and "C71" not in ln
                   for ln in text.splitlines())
    graphify_still_c69 = any(
        _still_seals_c69(p.read_text(encoding="utf-8")) for p in gdir.glob("*.md"))
    c69_scs = list((kb / "scs").glob("scs_c69*.md"))
    one_canonical_c69 = (len(c69_scs) == 1
                         and "conversation_quality" in c69_scs[0].name)
    if old_gone and new_exists and not graphify_still_c69 and one_canonical_c69:
        _ok("V-SCS-NO-COLLISION",
            "graphify reassigned C69->C71; C69 = conversation_quality only, "
            "no graphify file still seals C69")
    else:
        _fail("V-SCS-NO-COLLISION",
              f"old_gone={old_gone} new={new_exists} "
              f"graphify_c69={graphify_still_c69} one_c69={one_canonical_c69}")

    # ---- V-TAXONOMY-COMPLETE + V-ROI-RANKED ------------------------------
    doc = _ROOT / "vault" / "plans" / "cognitive-leak-taxonomy-2026-07-03.md"
    txt = doc.read_text(encoding="utf-8") if doc.exists() else ""
    families = ["L-SCHED", "L-XPANE", "L-SELFCORR", "L-REREAD", "L-CTXINFLATE",
                "L-OWNERREPEAT", "L-REPEATQ", "L-PLANDIV"]
    hyps = ["H1", "H2", "H3", "H4", "H5", "H6", "H7"]
    missing = [k for k in families + hyps if k not in txt]
    if txt and not missing:
        _ok("V-TAXONOMY-COMPLETE",
            f"{len(families)} families + {len(hyps)} hypotheses all in doc")
    else:
        _fail("V-TAXONOMY-COMPLETE", f"missing={missing} (doc_exists={bool(txt)})")

    roi = all(s in txt for s in ("QUICK WINS", "STRATEGIC", "NOT WORTH", "ROI"))
    if roi:
        _ok("V-ROI-RANKED", "quick-wins / strategic / not-worth tiers present")
    else:
        _fail("V-ROI-RANKED", "ROI ranking tiers missing")

    # ---- V-NO-REGRESSION : C68 + C69 suites still green ------------------
    try:
        t68 = _load(_HERE / "test_token_corpus_audit.py",
                    "test_token_corpus_audit")
        t69 = _load(_HERE / "test_conversation_quality_audit.py",
                    "test_conversation_quality_audit")
        r68 = t68.main()
        r69 = t69.main()
        if r68 == 0 and r69 == 0:
            _ok("V-NO-REGRESSION", f"C68 exit={r68}, C69 exit={r69}")
        else:
            _fail("V-NO-REGRESSION", f"C68 exit={r68}, C69 exit={r69}")
    except Exception as e:  # noqa: BLE001
        _fail("V-NO-REGRESSION", f"suite raised: {e}")

    total = _passes + _fails
    print(f"COGLEAK_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
