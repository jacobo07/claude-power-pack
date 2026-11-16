#!/usr/bin/env python3
"""V-ASC-B7-* -- the web_surface B7 (Taste) promotion tooling, both poles, never calls a model.

Covers: the B7 delta is promotable and its origin quote is real; the candidate block a fresh builder would get carries
the taste entry; asc_inherit_run refuses a pair that would test nothing; and the evidence builder over a SYNTHETIC
recorded pair (a clean treated page, a sloppy control page) emits evidence the tower ratchet accepts, while a
sloppy treated page makes it exit 1. Once the real pair is recorded, V-ASC-B7-RECORDED re-judges it from disk.
Run: python tools/test_asc_b7.py   (exit 0 = all gates pass)
"""
from __future__ import annotations

import json
import linecache
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
B7 = ROOT / "vault/programs/ascension/bcap-1/b7"
RESULTS: list = []


def ok(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(cond)))
    print("  %s %-32s %s" % ("PASS" if cond else "FAIL", name, "" if cond else str(detail)[:300]))


def test_delta() -> None:
    from modules.backlog_autopilot import promotion as P
    from modules.tower import baselines as bl
    ds = P.load_deltas(str(B7 / "deltas.json"))
    v = P.classify(ds[0], bl.active_entries("web_surface"))
    ok("V-ASC-B7-DELTA-PROMOTABLE", len(ds) == 1 and v.promotable and not P.check_problem(ds[0]), v.as_dict())
    o = ds[0].origin
    ok("V-ASC-B7-ORIGIN-REAL", linecache.getline(str(ROOT / o["file"]), o["line"]).strip() == o["quote"], o)


def test_block() -> None:
    import asc_inherit_run as R
    from modules.gsd_x import cli
    from modules.tower import baselines as bl
    cand = R.candidate_root(B7 / "deltas.json")
    os.environ["CPP_TOWER_STATE_DIR"] = tempfile.mkdtemp(prefix="v-b7-state-")
    block = cli.family_block(R.TASKS["saas"], {"session_id": "v-b7"}, root=cand)
    n = bl.generations("web_surface", cand)[-1]
    ok("V-ASC-B7-CANDIDATE-NEXT-GEN", n == bl.generations("web_surface")[-1] + 1, n)
    ok("V-ASC-B7-BLOCK-CARRIES-TASTE", "web_surface/B%d" % n in block and "[web_surface-taste-hard-bans]" in block,
       block[:300])
    ok("V-ASC-B7-TASK-NAMES-NO-BAN", not any(w in R.TASKS["saas"].lower() for w in ("dash", "taste", "slop", "scroll")))
    rc = R.main(["--dry-run"])                       # phase-5 deltas are all active: the pair would test nothing
    ok("V-ASC-B7-REFUSES-EMPTY-PAIR", rc == 3, rc)


def _fake_pair(out: Path, treated_html: str, control_html: str) -> None:
    for label, html in (("treated", treated_html), ("control", control_html)):
        d = out / "inherit" / label
        d.mkdir(parents=True)
        (d / "index.html").write_text(html, encoding="utf-8")
    run = {"task_key": "saas", "candidate_generation": "web_surface/B7", "candidate_sha256": "0" * 64,
           "runs": {"treated": {"files": ["index.html"]}, "control": {"files": ["index.html"]}}}
    (out / "inheritance_run.json").write_text(json.dumps(run), encoding="utf-8")


def test_evidence() -> None:
    import asc_b7_evidence as E
    from modules.tower import ratchet as rt
    saved = E.OUT
    try:
        good = Path(tempfile.mkdtemp(prefix="v-b7-good-"))
        _fake_pair(good, E.CLEAN, E.SLOP)
        E.OUT = good
        rc = E.main()
        ev = json.loads((good / "evidence.json").read_text(encoding="utf-8"))
        ok("V-ASC-B7-EVIDENCE-OK", rc == 0 and ev["improvement"]["before"] == "FAIL"
           and ev["improvement"]["after"] == "PASS", ev.get("improvement"))
        ok("V-ASC-B7-NEGATIVES-FAIL", len(ev["negative_controls"]) == 3
           and all(c["rc"] == 1 for c in ev["negative_controls"]), ev["negative_controls"])
        ok("V-ASC-B7-DISCRIMINATED", ev["discriminated"] is True and ev["control_agent"]["rc"] == 1, ev["control_agent"])
        ok("V-ASC-B7-RATCHET-ACCEPTS", rt.evidence_problems(ev) == [], rt.evidence_problems(ev))
        bad = Path(tempfile.mkdtemp(prefix="v-b7-bad-"))
        _fake_pair(bad, E.SLOP, E.SLOP)
        E.OUT = bad
        rc = E.main()
        evb = json.loads((bad / "evidence.json").read_text(encoding="utf-8"))
        ok("V-ASC-B7-SLOPPY-TREATED-REFUSED", rc == 1 and evb["positive_control"]["rc"] == 1
           and "VIOLATED" in evb["positive_control"]["detail"], evb["positive_control"])
        ok("V-ASC-B7-BROKEN-JUDGE-NOT-A-CONTROL", E.judge_rc(str(bad / "no-such-candidate"), bad)[0] == 4)
        quiet = Path(tempfile.mkdtemp(prefix="v-b7-quiet-"))
        _fake_pair(quiet, E.CLEAN, E.CLEAN)
        E.OUT = quiet
        rc = E.main()
        evq = json.loads((quiet / "evidence.json").read_text(encoding="utf-8"))
        ok("V-ASC-B7-QUIET-CONTROL-REPORTED", rc == 0 and evq["discriminated"] is False, evq.get("control_agent"))
    finally:
        E.OUT = saved


def test_recorded() -> None:
    if not (B7 / "inheritance_run.json").exists():
        print("  ---- V-ASC-B7-RECORDED              not yet recorded (pair runs on GEX44)")
        return
    rec = json.loads((B7 / "inheritance_run.json").read_text(encoding="utf-8"))
    ok("V-ASC-B7-RECORDED", rec.get("candidate_generation", "").startswith("web_surface/B")
       and all(r.get("rc") == 0 for r in rec.get("runs", {}).values()) and "index.html" in rec["runs"]["treated"]["files"],
       {k: (v.get("rc"), v.get("files")) for k, v in rec.get("runs", {}).items()})


def main() -> int:
    for t in (test_delta, test_block, test_evidence, test_recorded):
        try:
            t()
        except Exception as exc:  # noqa: BLE001 -- a crashed section is a FAIL, never a skip
            ok("V-ASC-B7-CRASH-%s" % t.__name__, False, "%s: %s" % (type(exc).__name__, exc))
    passed = sum(1 for _, c in RESULTS if c)
    print("V-ASC-B7: %d passed, %d failed" % (passed, len(RESULTS) - passed))
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
