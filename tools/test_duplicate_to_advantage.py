#!/usr/bin/env python3
"""test_duplicate_to_advantage.py -- done-gate for the D2A Engine (SCS C85).

V-D2A-* gates, hermetic (re-runnable ×3, byte-identical). Behavior gates over the engine
plus depth/no-duplicate gates over the doctrine dataset. Baseline gate re-runs the FD and
FIOS suites to prove no regression.

Run: python tools/test_duplicate_to_advantage.py [--json]
"""
from __future__ import annotations

import itertools
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.duplicate_to_advantage import (  # noqa: E402
    Proposal, run, OPERATIONS, ANTI_INFLATION_RULES, GAP_DIMENSIONS,
    PORTFOLIO_DIMENSIONS, run_family,
)
from modules.duplicate_to_advantage.d2a_engine import render  # noqa: E402

_KB = _PP_ROOT / "vault" / "knowledge_base" / "duplicate_to_advantage"
_DOCTRINE = _KB / "d2a_00_duplicate_to_advantage_doctrine.md"

# The canonical Token-Budget-Planner proposal (a genuine duplicate of FD-05 + budget owners).
_CANON = Proposal(
    "route the model budget, price frontier token cost as capital, plan reuse and "
    "deterministic conversion, adapt the session budget",
    "Token Budget Planner")
# A genuinely-novel proposal (should NOT be flagged as a high-coverage duplicate).
_NOVEL = Proposal("holographic tactile feedback surface for underwater sonar imaging",
                  "Sonar Haptics")

_passes = 0
_fails = 0
_log: list = []


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    _log.append(("PASS", gate, evidence))


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    _log.append(("FAIL", gate, diag))


def _part_word_counts(md_path: Path) -> list:
    """Words per top-level Part (## Part ...) section. Real prose words only (excludes the
    front-matter blockquote before the first Part)."""
    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    # Split on '## Part' headings.
    parts = re.split(r"(?m)^##\s+Part\b", text)
    counts = []
    for seg in parts[1:]:                       # [0] is the pre-Part front matter
        words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-]*", seg))
        counts.append(words)
    return counts


_GATE = _PP_ROOT / "hooks" / "d2a_gate.js"
_NODE = shutil.which("node")
# Every gate call gets a unique session id: the gate throttles per (session, prompt),
# so a shared id would silence the second assertion and make the suite non-hermetic.
_SID = itertools.count()


def _run_gate_raw(raw_stdin: str, cwd: str | None = None) -> tuple:
    """Spawn the gate exactly as the dispatcher does (shell-free, stdin->stdout).
    Returns (exit_code, stdout)."""
    if not _NODE or not _GATE.is_file():
        return (99, "")
    try:
        p = subprocess.run([_NODE, str(_GATE)], input=raw_stdin, capture_output=True,
                           text=True, timeout=60, cwd=cwd or str(_PP_ROOT))
        return (p.returncode, p.stdout or "")
    except Exception:  # noqa: BLE001
        return (99, "")


def _run_gate(prompt: str, cwd: str | None = None) -> tuple:
    payload = json.dumps({"prompt": prompt,
                          "session_id": f"t{os.getpid()}_{next(_SID)}"})
    return _run_gate_raw(payload, cwd=cwd)


def _run_suite(script: str) -> tuple:
    """Run another test script; return (exit_code, tail)."""
    exe = sys.executable
    try:
        p = subprocess.run([exe, str(_PP_ROOT / "tools" / script)],
                           capture_output=True, text=True, cwd=str(_PP_ROOT), timeout=180)
        tail = (p.stdout or "").strip().splitlines()[-1:] or [""]
        return p.returncode, tail[0]
    except Exception as e:  # noqa: BLE001
        return 99, f"{type(e).__name__}"


def main(argv=None) -> int:
    as_json = "--json" in (argv or sys.argv[1:])

    v = run(_CANON)
    nov = run(_NOVEL)

    # V-D2A-DETECTION-SEMANTIC -- duplicate detected > 80%.
    if v.dupe.coverage_pct > 80 and v.dupe.is_duplicate:
        _ok("V-D2A-DETECTION-SEMANTIC",
            f"coverage={v.dupe.coverage_pct}% parent={v.dupe.parent_id} dup=True")
    else:
        _fail("V-D2A-DETECTION-SEMANTIC",
              f"coverage={v.dupe.coverage_pct}% dup={v.dupe.is_duplicate} (need >80% & True)")

    # V-D2A-GAP-MAPPED -- >= 8 of 14 dimensions classified.
    classified = sum(1 for x in v.gap.dimensions.values()
                     if x in ("covered", "partial", "absent"))
    if classified >= 8 and len(GAP_DIMENSIONS) == 14:
        _ok("V-D2A-GAP-MAPPED", f"{classified}/14 dims classified")
    else:
        _fail("V-D2A-GAP-MAPPED", f"{classified} classified, {len(GAP_DIMENSIONS)} dims")

    verticals = [c for c in v.portfolio if c.axis == "vertical"]
    horizontals = [c for c in v.portfolio if c.axis == "horizontal"]

    # V-D2A-VERTICAL-GENERATED -- >= 3 verticals with numeric scores.
    if len(verticals) >= 3 and all(c.scores and all(isinstance(x, (int, float))
                                                    for x in c.scores.values())
                                   for c in verticals):
        _ok("V-D2A-VERTICAL-GENERATED", f"{len(verticals)} verticals, all numeric")
    else:
        _fail("V-D2A-VERTICAL-GENERATED", f"{len(verticals)} verticals")

    # V-D2A-HORIZONTAL-GENERATED -- >= 3 horizontals with numeric scores.
    if len(horizontals) >= 3 and all(c.scores and all(isinstance(x, (int, float))
                                                     for x in c.scores.values())
                                    for c in horizontals):
        _ok("V-D2A-HORIZONTAL-GENERATED", f"{len(horizontals)} horizontals, all numeric")
    else:
        _fail("V-D2A-HORIZONTAL-GENERATED", f"{len(horizontals)} horizontals")

    # V-D2A-PORTFOLIO-SCORED -- every candidate carries all 16 dimension scores.
    dims16 = [k for k, _ in PORTFOLIO_DIMENSIONS]
    if len(dims16) == 16 and v.portfolio and all(
            set(c.scores.keys()) == set(dims16) for c in v.portfolio):
        _ok("V-D2A-PORTFOLIO-SCORED",
            f"{len(v.portfolio)} candidates x 16 dims each")
    else:
        bad = next((c.name for c in v.portfolio if set(c.scores.keys()) != set(dims16)),
                   "n/a")
        _fail("V-D2A-PORTFOLIO-SCORED", f"16 dims? {len(dims16)}; offender={bad}")

    # V-D2A-CONTRACT-MINIMAL -- Part over dataset when coverage warrants.
    if v.contract and v.contract.artifact == "dataset_part":
        _ok("V-D2A-CONTRACT-MINIMAL",
            f"artifact={v.contract.artifact} (not 'dataset') at coverage "
            f"{v.dupe.coverage_pct}%")
    else:
        got = v.contract.artifact if v.contract else "none"
        _fail("V-D2A-CONTRACT-MINIMAL", f"artifact={got} (expected dataset_part)")

    # V-D2A-ANTIINFLATION -- all 10 rules recorded on the contract.
    if (v.contract and len(ANTI_INFLATION_RULES) == 10
            and set(v.contract.anti_inflation.keys()) == set(ANTI_INFLATION_RULES)
            and all(isinstance(b, bool) for b in v.contract.anti_inflation.values())):
        npass = sum(1 for b in v.contract.anti_inflation.values() if b)
        _ok("V-D2A-ANTIINFLATION", f"10 rules recorded, {npass}/10 pass on canonical")
    else:
        _fail("V-D2A-ANTIINFLATION", "contract missing the 10-rule ledger")

    # V-D2A-NO-DUPLICATE -- registry references real sealed families; doctrine declares
    # non-duplication of each family axis. Also: exactly one prose dataset (not 6).
    from modules.duplicate_to_advantage.d2a_engine import FAMILY_REGISTRY
    real_ids = {"CO-01", "CO-03", "CO-05", "CO-08", "CO-12", "PM-02", "PM-03", "PM-04",
                "GK-01", "GK-04", "GK-08", "GK-09", "FD-01", "FD-03", "FD-05", "FD-06",
                "FIOS-EVO", "FIOS-IRR", "CDIO-05",
                # Families sealed after D2A shipped (C85). Each has a real master index on
                # disk; the gate's contract is "the registry names REAL sealed families",
                # and these are real. Added 2026-07-12 (DFP) -- without them the engine was
                # structurally blind to the newest half of the stack.
                "DRK-01", "DRK-02", "DRK-03", "ACIS", "SQI-02", "SPEC-GATE", "HR", "D2A",
                # Added auditing Crawl OS STOP #1 (C96): two real, git-verified, live
                # modules (modules/deep-research/deep_research.py, 1810 lines, sealed;
                # modules/autoresearch/nightcrawler.py + rss_sniffer.py + youtube_firehose.py,
                # scheduled) the registry was blind to before.
                "DEEP-RESEARCH", "AUTORESEARCH",
                # Added auditing the CavEX II Asset Foundry STOP #1 (2026-07-20). All three
                # verified by direct read this session, not assumed:
                #   CAVEX-GOV      -- CONSTITUTION.md (10 Laws), governance/HARD_RULES.md
                #                     (HR-01..HR-15), governance/PRD.md, ARCHITECTURE.md
                #   CRAWLOS        -- vault/knowledge_base/crawl_os/: dataset 01 SEALED
                #                     (25 Parts, 32,888 words), dataset 10 at 12/25 Parts
                #   KOBII-IDENTITY -- knowledge-vault/kobiicraft-identity/, 7 documents
                # NOTE: CAVEX-GOV and KOBII-IDENTITY are the first rows in this registry
                # that live OUTSIDE this repository (they are in the CavEX repo). That is
                # deliberate -- the detector serves any corpus this estate builds, and a
                # family it cannot see is a family it cannot protect -- but it does widen
                # the gate's "real sealed family" contract from PP-internal to cross-repo.
                # Flagged here rather than blurred silently.
                "CAVEX-GOV", "CRAWLOS", "KOBII-IDENTITY"}
    doctrine = _DOCTRINE.read_text(encoding="utf-8", errors="replace") if \
        _DOCTRINE.is_file() else ""
    n_datasets = len([p for p in _KB.glob("*.md")
                      if p.name.lower().startswith("d2a_")
                      and "index" not in p.name.lower()])
    declares = ("does NOT duplicate" in doctrine or "not duplicate" in doctrine.lower()
                or "non-duplication" in doctrine.lower())
    if set(FAMILY_REGISTRY.keys()) <= real_ids and declares and n_datasets == 1:
        _ok("V-D2A-NO-DUPLICATE",
            f"registry {len(FAMILY_REGISTRY)} real families; 1 prose dataset (anti-inflation)")
    else:
        _fail("V-D2A-NO-DUPLICATE",
              f"registry_ok={set(FAMILY_REGISTRY.keys()) <= real_ids} "
              f"declares={declares} datasets={n_datasets}")

    # V-D2A-DEPTH -- each doctrine Part > 2500 real words.
    counts = _part_word_counts(_DOCTRINE)
    if len(counts) >= 3 and all(c > 2500 for c in counts):
        _ok("V-D2A-DEPTH", f"{len(counts)} Parts, words={counts} (all >2500)")
    else:
        _fail("V-D2A-DEPTH", f"Parts={len(counts)} words={counts} (need 3x >2500)")

    # V-D2A-NUMERIC-BENCHMARKS -- every score in every candidate is a number 0-10.
    all_numeric = all(
        isinstance(x, (int, float)) and 0 <= x <= 10
        for c in v.portfolio for x in c.scores.values())
    if all_numeric and v.portfolio:
        _ok("V-D2A-NUMERIC-BENCHMARKS",
            f"all {len(v.portfolio)}x16 scores numeric in [0,10]")
    else:
        _fail("V-D2A-NUMERIC-BENCHMARKS", "a non-numeric or out-of-range score exists")

    # V-D2A-FAILOPEN -- pathological input -> DEFER, never raise.
    try:
        empty = run(Proposal("", ""))
        weird = run(Proposal("\x00﻿   ", "x" * 5000))
        if empty.contract is None and "DEFER" in empty.note and weird is not None:
            _ok("V-D2A-FAILOPEN", "empty -> DEFER; pathological -> no raise")
        else:
            _fail("V-D2A-FAILOPEN", f"empty.note={empty.note!r}")
    except Exception as e:  # noqa: BLE001
        _fail("V-D2A-FAILOPEN", f"raised {type(e).__name__} (must never raise)")

    # V-D2A-NOVEL-NOT-FLAGGED -- a genuinely-new proposal is not a high-coverage duplicate.
    if not nov.dupe.is_duplicate and nov.dupe.coverage_pct < 50:
        _ok("V-D2A-NOVEL-NOT-FLAGGED",
            f"novel coverage={nov.dupe.coverage_pct}% dup=False")
    else:
        _fail("V-D2A-NOVEL-NOT-FLAGGED",
              f"novel coverage={nov.dupe.coverage_pct}% dup={nov.dupe.is_duplicate}")

    # V-D2A-OPERATIONS -- exactly 15 operations; every candidate uses a valid one.
    if len(OPERATIONS) == 15 and "DO_NOT_BUILD" in OPERATIONS and all(
            c.operation in OPERATIONS for c in v.portfolio):
        _ok("V-D2A-OPERATIONS", "15 operations; every candidate uses a valid op")
    else:
        _fail("V-D2A-OPERATIONS", f"{len(OPERATIONS)} ops")

    # ---- Family Sizing Mode (Owner directive, C96 -- "always offered" for a proposed
    # family of N candidate datasets/systems, not just a single proposal) ----
    _fam_fold_case = [
        Proposal("route the model budget, price frontier token cost as capital, plan "
                 "reuse and deterministic conversion, adapt the session budget",
                 "Budget Planner A"),
        Proposal("holographic tactile feedback surface for underwater sonar imaging",
                 "Sonar Haptics"),
    ]
    fam_fold = run_family(_fam_fold_case)
    # V-D2A-FAMILY-DETECTS-FOLD -- a known-duplicate item in the family is FOLDed, the
    # genuinely-novel sibling is KEPT.
    fold_names = {it.name for it in fam_fold.fold}
    kept_names = {it.name for it in fam_fold.keep if it.disposition == "KEEP"}
    if "Budget Planner A" in fold_names and "Sonar Haptics" in kept_names:
        _ok("V-D2A-FAMILY-DETECTS-FOLD",
            f"fold={fold_names} keep={kept_names} recommended={fam_fold.recommended_count}"
            f"/{fam_fold.proposed_count}")
    else:
        _fail("V-D2A-FAMILY-DETECTS-FOLD", f"fold={fold_names} keep={kept_names}")

    _fam_merge_case = [
        Proposal("crawl web pages and extract structured evidence with provenance and "
                 "source hashes for later verification", "Evidence Capture Engine"),
        Proposal("extract structured evidence from crawled web pages, hash the content "
                 "and preserve provenance for verification later", "Provenance Extractor"),
        Proposal("holographic tactile feedback surface for underwater sonar imaging",
                 "Sonar Haptics 2"),
    ]
    fam_merge = run_family(_fam_merge_case)
    # V-D2A-FAMILY-DETECTS-MERGE -- two near-identical siblings collapse into one group;
    # the unrelated third item stays separate.
    merged_pair = any({"Evidence Capture Engine", "Provenance Extractor"} <= set(g)
                      for g in fam_merge.merge_groups)
    sonar_not_merged = not any("Sonar Haptics 2" in g for g in fam_merge.merge_groups)
    if merged_pair and sonar_not_merged and fam_merge.recommended_count < 3:
        _ok("V-D2A-FAMILY-DETECTS-MERGE",
            f"groups={fam_merge.merge_groups} recommended={fam_merge.recommended_count}"
            f"/{fam_merge.proposed_count}")
    else:
        _fail("V-D2A-FAMILY-DETECTS-MERGE",
              f"groups={fam_merge.merge_groups} recommended={fam_merge.recommended_count}")

    # V-D2A-FAMILY-FAILOPEN -- empty family list and a pathological item never raise.
    try:
        empty_fam = run_family([])
        weird_fam = run_family([Proposal("\x00﻿   ", "x" * 5000)])
        if (empty_fam.proposed_count == 0 and weird_fam.proposed_count == 1
                and weird_fam is not None):
            _ok("V-D2A-FAMILY-FAILOPEN",
                "empty list -> 0 items; pathological item -> no raise")
        else:
            _fail("V-D2A-FAMILY-FAILOPEN", f"empty={empty_fam.proposed_count}")
    except Exception as e:  # noqa: BLE001
        _fail("V-D2A-FAMILY-FAILOPEN", f"raised {type(e).__name__} (must never raise)")

    # ---- D2A gate (SCS C85 addendum) -- wiring gates over the real CLI path ----
    gate_ok = _NODE is not None and _GATE.is_file()
    if not gate_ok:
        _fail("V-D2A-GATE-FIRES", f"node={_NODE} gate_exists={_GATE.is_file()}")
    else:
        # V-D2A-GATE-FIRES: a creation proposal that duplicates -> gate emits advisory.
        rc, out = _run_gate("build a new system to plan and allocate the frontier token "
                            "budget, pricing cost as capital")
        if rc == 0 and out.strip():
            _ok("V-D2A-GATE-FIRES", f"creation+duplicate -> advisory ({len(out)} B), rc=0")
        else:
            _fail("V-D2A-GATE-FIRES", f"rc={rc} stdout_len={len(out)}")

        # V-D2A-ADVISORY-VISIBLE: the advisory rides additionalContext (Owner-visible),
        # and carries the DUPE VERDICT + the BUILD CONTRACT alternative.
        ctx = ""
        try:
            hso = (json.loads(out) or {}).get("hookSpecificOutput", {})
            ctx = hso.get("additionalContext", "") if \
                hso.get("hookEventName") == "UserPromptSubmit" else ""
        except Exception:  # noqa: BLE001
            ctx = ""
        if ("DUPE VERDICT" in ctx and "BUILD CONTRACT" in ctx
                and "RECOMMENDED ACTION" in ctx and "never blocks" in ctx):
            _ok("V-D2A-ADVISORY-VISIBLE",
                "additionalContext carries DUPE VERDICT + RECOMMENDED + BUILD CONTRACT")
        else:
            _fail("V-D2A-ADVISORY-VISIBLE", f"ctx_len={len(ctx)} (missing sections)")

        # V-D2A-SILENCE-ON-NOVEL: a genuinely-new proposal -> zero gate output.
        rc, out = _run_gate("create a new system for holographic tactile feedback in "
                            "underwater sonar imaging")
        if rc == 0 and not out.strip():
            _ok("V-D2A-SILENCE-ON-NOVEL", "novel creation proposal -> silent, rc=0")
        else:
            _fail("V-D2A-SILENCE-ON-NOVEL", f"rc={rc} stdout={out[:120]!r}")

        # V-D2A-GATE-KEYWORD-SCOPE: use/extend/fix/read are NEVER intercepted
        # (T-D2A-GATE-KEYWORD-SCOPE-001: false positives are the expensive failure).
        negatives = [
            "extend CO-03 router with a new deterministic rung",
            "fix the typo in line 5",
            "read the dataset and tell me what it says",
            "run the test suite for the router module",
        ]
        noisy = [p for p in negatives if _run_gate(p)[1].strip()]
        if not noisy:
            _ok("V-D2A-GATE-KEYWORD-SCOPE",
                f"{len(negatives)} non-creation prompts -> all silent")
        else:
            _fail("V-D2A-GATE-KEYWORD-SCOPE", f"false positives: {noisy}")

        # V-D2A-GATE-FAILOPEN: garbage / non-JSON stdin -> exit 0, empty stdout.
        rc1, o1 = _run_gate_raw("this is not json at all")
        rc2, o2 = _run_gate_raw("")
        rc3, o3 = _run_gate_raw('{"prompt": 12345}')
        if (rc1, rc2, rc3) == (0, 0, 0) and not (o1.strip() or o2.strip() or o3.strip()):
            _ok("V-D2A-GATE-FAILOPEN",
                "non-JSON / empty / wrong-type stdin -> exit 0, empty stdout (never 2)")
        else:
            _fail("V-D2A-GATE-FAILOPEN", f"rcs={(rc1, rc2, rc3)}")

        # V-D2A-GATE-GLOBAL: works from ANY cwd (engine + registry resolved absolutely),
        # so a proposal in another repo still gets the PP ecosystem verdict.
        rc, out = _run_gate("build a new system to plan and allocate the frontier token "
                            "budget, pricing cost as capital", cwd=str(Path.home()))
        if rc == 0 and out.strip():
            _ok("V-D2A-GATE-GLOBAL", f"advisory from cwd={Path.home()} (no per-repo config)")
        else:
            _fail("V-D2A-GATE-GLOBAL", f"rc={rc} stdout_len={len(out)} from home cwd")

    # V-D2A-GATE-REGISTERED: the canonical dispatcher's UserPromptSubmit chain carries
    # the gate. NOTE: a string match proves REGISTRATION, never EXECUTION -- see
    # V-D2A-GATE-LIVE-WIRED below, which drives the real dispatcher. Built != wired.
    disp = _PP_ROOT / "hooks" / "hook-dispatcher.js"
    dtext = disp.read_text(encoding="utf-8", errors="replace") if disp.is_file() else ""
    ups = dtext.split("'UserPromptSubmit-chain'", 1)[-1].split("],", 1)[0]
    if "d2a_gate.js" in ups:
        _ok("V-D2A-GATE-REGISTERED", "d2a_gate.js present in canonical UserPromptSubmit-chain")
    else:
        _fail("V-D2A-GATE-REGISTERED", "d2a_gate.js missing from UserPromptSubmit-chain")

    # V-D2A-GATE-LIVE-WIRED: drive the LIVE dispatcher exactly as settings.json does
    # (--event=UserPromptSubmit-chain) and require the advisory to reach its merged
    # output. The only gate proving the chain EXECUTES d2a_gate and that mergeOutputs
    # preserves additionalContext. Doubles as the drift detector for
    # T-HOOK-DISPATCHER-DRIFT-001 (canonical edited, live not Copy-Item'd yet).
    live_disp = Path.home() / ".claude" / "hooks" / "hook-dispatcher.js"
    if not (_NODE and live_disp.is_file()):
        _ok("V-D2A-GATE-LIVE-WIRED",
            f"SKIPPED (no live dispatcher at {live_disp}) -- canonical registration verified")
    else:
        payload = json.dumps({
            "prompt": "quiero crear un router de modelos que elija entre haiku sonnet "
                      "y opus segun el coste",
            "session_id": f"vgate{os.getpid()}_{next(_SID)}",
            "cwd": str(Path.home()),
        })
        try:
            p = subprocess.run([_NODE, str(live_disp), "--event=UserPromptSubmit-chain"],
                               input=payload, capture_output=True, text=True, timeout=120,
                               cwd=str(_PP_ROOT))
            merged, rc = (p.stdout or ""), p.returncode
        except Exception:  # noqa: BLE001
            merged, rc = "", 99
        live_txt = live_disp.read_text(encoding="utf-8", errors="replace")
        if rc == 0 and "D2A duplicate advisory" in merged and "DUPE VERDICT" in merged:
            _ok("V-D2A-GATE-LIVE-WIRED",
                f"live dispatcher emits the D2A advisory ({len(merged)} B, rc=0)")
        elif "d2a_gate.js" not in live_txt:
            _fail("V-D2A-GATE-LIVE-WIRED",
                  "live dispatcher is STALE (no d2a_gate.js) -- run the Copy-Item "
                  "(T-HOOK-DISPATCHER-DRIFT-001)")
        else:
            _fail("V-D2A-GATE-LIVE-WIRED",
                  f"live registered but advisory absent (rc={rc}, {len(merged)} B) -- "
                  "chain executed but output not merged")

    # V-D2A-BASELINE -- FD + FIOS suites still green (no regression).
    fd_rc, fd_tail = _run_suite("test_fable_distillation.py")
    fi_rc, fi_tail = _run_suite("test_frontier_intelligence_os.py")
    if fd_rc == 0 and fi_rc == 0:
        _ok("V-D2A-BASELINE", f"FD rc=0 ({fd_tail}); FIOS rc=0 ({fi_tail})")
    else:
        _fail("V-D2A-BASELINE", f"FD rc={fd_rc}; FIOS rc={fi_rc}")

    total = _passes + _fails
    if as_json:
        # NOTE: no local `import json` here -- a function-local import would make
        # `json` local to all of main(), and the earlier json.loads() would raise
        # UnboundLocalError (silently swallowed into a false ADVISORY-VISIBLE fail).
        print(json.dumps({"passes": _passes, "fails": _fails,
                          "log": [{"status": s, "gate": g, "evidence": e}
                                  for s, g, e in _log]}, indent=2))
    else:
        for status, gate, ev in _log:
            print(f"[{status}] {gate}: {ev}")
        print(f"\nD2A_PASS={_passes}/{total}  threshold={total}/{total}  "
              f"VERDICT={'PASS' if _fails == 0 else 'FAIL'}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
