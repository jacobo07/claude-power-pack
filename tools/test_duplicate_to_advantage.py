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
import re
import shutil
import subprocess
import sys
import uuid
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
# Every gate call gets a session id unique across RUNS, not merely within one.
#
# d2a_gate.js throttles on (sanitised session_id, sha1(prompt)[:12]) for 15 minutes,
# and the marker lives in a GLOBAL directory (~/.claude/state/d2a) that outlives the
# process. A pid is not enough for two compounding reasons:
#   1. Windows recycles pids, and the suite's own prompt literals are constant, so the
#      whole key reduces to the pid.
#   2. The gate's sanitiser strips every non-alphanumeric character, INCLUDING the '_'
#      that separated pid from counter -- so `vgate1044_7`, `vgate104_47` and
#      `vgate10447_<n>` all collapse to the same marker. The collision surface is far
#      wider than pid reuse alone.
# A collision silences the gate, the advisory never appears, and the assertion fails
# with "live registered but advisory absent" -- observed once as a 32/33 flake that
# then hid for six consecutive runs. A uuid4 never recycles and is already
# alphanumeric, so the sanitiser cannot fold two of them together.
_RUN_TOKEN = uuid.uuid4().hex
_SID = itertools.count()


def _sid(prefix: str) -> str:
    """A throttle-proof session id. `_RUN_TOKEN` is fixed-length, so prefix, token and
    counter stay unambiguous after the gate strips the separators."""
    return f"{prefix}{_RUN_TOKEN}x{next(_SID)}"


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
    payload = json.dumps({"prompt": prompt, "session_id": _sid("t")})
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
                "CAVEX-GOV", "CRAWLOS", "KOBII-IDENTITY",
                # Added auditing the CPP-UKR Runtime Residue family sizing
                # (2026-07-30, vault/plans/ukr-runtime-2026-07-30.md). D2A's raw
                # 18-candidate run scored 5 candidates (B, E, H, M, N) as KEEP
                # purely because their real owner had no vault/knowledge_base/
                # presence -- verified directly this session (Glob returned no
                # matches for ksf*/akos*/*liveness*/*secret* under
                # vault/knowledge_base/):
                #   KSF             -- Knowledge Sovereignty Fabric (authority/
                #                      precedence), named as an owner in the
                #                      UKR prompt's own text.
                #   AKOS            -- knowledge/AKOS_KNOWLEDGE_BRIEF.md, its
                #                      domain-matched injector observed firing
                #                      live this session.
                #   LIVENESS        -- modules/liveness/reachability.py,
                #                      vault/liveness/reachability_registry.json
                #                      (both verified on disk this session).
                #   SECRET-FIREWALL -- vault/secret_firewall/, HR-SECRET-001..007
                #                      sealed in this repo's own CLAUDE.md.
                #   RULE-COMPILER   -- modules/rule_compiler/ (digest.py,
                #                      hardrule_compile.py, effect_harness.py,
                #                      all verified on disk prior session).
                "KSF", "AKOS", "LIVENESS", "SECRET-FIREWALL", "RULE-COMPILER"}
    doctrine = _DOCTRINE.read_text(encoding="utf-8", errors="replace") if \
        _DOCTRINE.is_file() else ""
    n_datasets = len([p for p in _KB.glob("*.md")
                      if p.name.lower().startswith("d2a_")
                      and "index" not in p.name.lower()])
    declares = ("does NOT duplicate" in doctrine or "not duplicate" in doctrine.lower()
                or "non-duplication" in doctrine.lower())
    # The allow-list above governs CURATED rows only. Derived rows (2026-07-20) prove
    # themselves by construction: each must resolve to a real knowledge_base directory
    # on disk. Asserting a hand-maintained allow-list over a filesystem-derived registry
    # would re-impose the very hand-enrollment the derivation exists to remove -- the
    # gate would have to be edited by hand every time a family is added, which is how
    # the registry went blind to 68% of the estate in the first place.
    # Two substrates prove themselves the same way (2026-08-18): KB- rows against
    # vault/knowledge_base/, MOD- rows against modules/. The second was added when
    # T-D2A-REGISTRY-BLIND-SPOT-001 was found to recur one level up -- the 07-20 fix
    # discovered doctrine families and left the 81 executable modules unregistered,
    # which produced false-NEW verdicts on proposals whose owner is a module.
    from modules.duplicate_to_advantage.d2a_engine import _KB_ROOT, _MOD_ROOT
    curated_ids = {k for k, v in FAMILY_REGISTRY.items() if not v.get("derived")}
    derived_ids = {k for k, v in FAMILY_REGISTRY.items() if v.get("derived")}

    def _resolves(fid):
        if fid.startswith("KB-"):
            root, prefix = _KB_ROOT, "KB-"
        elif fid.startswith("MOD-"):
            root, prefix = _MOD_ROOT, "MOD-"
        else:
            return False
        if not root.is_dir():
            return False
        return any(
            d.is_dir()
            and prefix + d.name.upper().replace("_", "-").replace(" ", "-") == fid
            for d in root.iterdir())

    unreal_derived = sorted(fid for fid in derived_ids if not _resolves(fid))
    registry_ok = (curated_ids <= real_ids) and not unreal_derived
    if registry_ok and declares and n_datasets == 1:
        _ok("V-D2A-NO-DUPLICATE",
            f"{len(curated_ids)} curated + {len(derived_ids)} derived families, all real; "
            f"1 prose dataset (anti-inflation)")
    else:
        _fail("V-D2A-NO-DUPLICATE",
              f"curated_ok={curated_ids <= real_ids} unreal_derived={unreal_derived} "
              f"declares={declares} datasets={n_datasets}")

    # V-D2A-REGISTRY-COMPLETE -- every knowledge_base family resolves to a registry
    # entry. T-D2A-REGISTRY-BLIND-SPOT-001: a duplication detector blind to a family
    # reports false-NEW for it and binds false parents at high confidence for everything
    # else. This gate is what keeps the registry honest as the estate grows.
    from modules.duplicate_to_advantage.d2a_engine import registry_gaps
    gaps = registry_gaps()
    n_kb = len([d for d in (_KB_ROOT.iterdir() if _KB_ROOT.is_dir() else []) if d.is_dir()])
    if not gaps:
        _ok("V-D2A-REGISTRY-COMPLETE",
            f"all {n_kb} knowledge_base families resolve to a registry entry")
    else:
        _fail("V-D2A-REGISTRY-COMPLETE", f"unregistered families: {gaps}")

    # V-D2A-MODULE-REGISTRY -- the executable substrate's half of the same law.
    #
    # Standing debt is a NAMED SET, never a count: a threshold is satisfied by
    # deleting a module and a ratio by adding a registered one, so only names force
    # the number down for the right reason. The baseline below is every module that
    # derives too little vocabulary to discriminate -- all but two carry no .py at
    # all. A NEW module landing unregistered is a real regression and fails here;
    # one of these gaining a Python surface and registering also fails, which is the
    # correct direction to be told about.
    from modules.duplicate_to_advantage.d2a_engine import module_registry_gaps
    mod_baseline = {
        # zero .py -- doc/config-only directories, nothing to derive from
        "agent-governance", "bug-hunter", "cdicf", "daemon", "design-md",
        "governance-overlay", "harness", "omniram-sentinel", "oracle", "rtk-core",
        # single .py whose name repeats the directory -- under the 3-token floor
        "dispatcher", "memory-engine",
    }
    mod_gaps = set(module_registry_gaps())
    n_mod = len([d for d in (_MOD_ROOT.iterdir() if _MOD_ROOT.is_dir() else [])
                 if d.is_dir() and not d.name.startswith((".", "__"))])
    if mod_gaps == mod_baseline:
        _ok("V-D2A-MODULE-REGISTRY",
            f"{n_mod - len(mod_gaps)}/{n_mod} modules resolve to a registry entry; "
            f"{len(mod_gaps)} named-baseline gaps unchanged")
    else:
        _fail("V-D2A-MODULE-REGISTRY",
              f"new unregistered: {sorted(mod_gaps - mod_baseline)}; "
              f"newly registered: {sorted(mod_baseline - mod_gaps)}")

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

    # V-D2A-FAMILY-DEFER-NOT-KEEP -- a candidate the plausibility floor CAPS (a parent's
    # vocabulary matched but precision too low to justify: pre-floor coverage >= 50, capped
    # to 45) is reported as DEFER, never as KEEP "genuinely new". This is the STOP #2
    # section-5 defect made a gate: World Model Federation (a measured false FOLD) lands at
    # sem=17/func=4, capped to 45 -- it must NOT be counted as a new build, while the truly
    # novel sibling still is. The empirical proof the fix works on the exact defect input.
    _fam_defer_case = [
        Proposal("competing world models registry model assumption ledger model scope "
                 "authority model contradiction engine model ensemble reasoner model "
                 "falsification laboratory model replacement protocol model uncertainty "
                 "surface plural beliefs held simultaneously adjudicated",
                 "World Model Federation"),
        Proposal("holographic tactile feedback surface for underwater sonar imaging",
                 "Sonar Haptics 3"),
    ]
    fam_defer = run_family(_fam_defer_case)
    defer_names = {it.name for it in fam_defer.defer}
    keep_names = {it.name for it in fam_defer.keep if it.disposition == "KEEP"}
    wmf_v = run(Proposal(_fam_defer_case[0].description, "WMF"))
    if ("World Model Federation" in defer_names
            and "World Model Federation" not in keep_names
            and "Sonar Haptics 3" in keep_names
            and wmf_v.dupe.deferred
            and all(it.disposition == "DEFER" for it in fam_defer.defer)
            and fam_defer.recommended_count == 1):
        _ok("V-D2A-FAMILY-DEFER-NOT-KEEP",
            f"defer={defer_names} keep={keep_names} "
            f"recommended={fam_defer.recommended_count}/{fam_defer.proposed_count} "
            "(45%-capped candidate is DEFER, not counted as 'genuinely new')")
    else:
        _fail("V-D2A-FAMILY-DEFER-NOT-KEEP",
              f"defer={defer_names} keep={keep_names} "
              f"deferred={wmf_v.dupe.deferred} rec={fam_defer.recommended_count}")

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

        # V-D2A-GATE-MEGA-PROPOSAL: a long multi-system brief is SEEN and answered.
        #
        # Two structural blind spots made this class of proposal -- the only class
        # D2A exists for -- permanently silent, measured 2026-08-18 on a 26,034-byte
        # 25-system brief:
        #   1. MAX_LEN 8000 SKIPPED anything longer, so the brief never reached the
        #      engine at all.
        #   2. NOT_CREATION disqualified the whole prompt on one incidental token,
        #      and "extend"/"rollback"/"test"/"reference" are unavoidable SUBJECT
        #      MATTER in any serious architecture document.
        # A third made it silent even once seen: a plausibility-capped verdict
        # (deferred) was collapsed into the `!is_duplicate` silence, so UNDETERMINED
        # and GENUINELY-NEW -- opposite conditions -- rendered identically.
        mega = (
            "Build the complete corpus of 25 sibling systems and their constitution. "
            "Each system is a dataset family with its own architecture, registry and "
            "engine. The corpus must define ownership, authority, rollback, migration, "
            "supersession and retirement for every capability, extend existing owners "
            "where they exist, reference prior art, and test every claim against "
            "production reality. Design the intent compiler, the architecture synthesis "
            "engine, the verification engine, the debugging system, the knowledge graph, "
            "the capability promotion engine and the governance layer. "
        ) * 12   # ~4k -> comfortably over MEGA_LEN, and full of negative-guard tokens
        rc, out = _run_gate(mega)
        ctx_m = ""
        try:
            hso_m = (json.loads(out) or {}).get("hookSpecificOutput", {})
            ctx_m = hso_m.get("additionalContext", "")
        except Exception:  # noqa: BLE001
            ctx_m = ""
        # Either answer is correct -- a named duplicate parent, or an honest
        # UNDETERMINED. Silence is the one outcome that is not.
        if rc == 0 and ctx_m.strip() and ("DUPE VERDICT" in ctx_m
                                          or "UNDETERMINED" in ctx_m):
            kind = "UNDETERMINED" if "UNDETERMINED" in ctx_m else "DUPE VERDICT"
            _ok("V-D2A-GATE-MEGA-PROPOSAL",
                f"{len(mega)}B multi-system brief carrying negative-guard vocabulary "
                f"-> answered ({kind}, {len(ctx_m)}B), rc={rc}; never silent")
        else:
            _fail("V-D2A-GATE-MEGA-PROPOSAL",
                  f"len={len(mega)} rc={rc} ctx_len={len(ctx_m)} -- a mega-corpus "
                  "proposal went unanswered")

        # ---- Family wiring (vault/specs/d2a-family-wiring.md) ------------------
        # The expansion machinery was reachable ONLY from render_family() and the
        # --family-file CLI, while the sole automatic surface (this hook) calls
        # --stdin. Two working halves, no joint. These four gates assert the joint.

        # V-D2A-FAMILY-COMMAND: the live surface exists. Reachability seeds from
        # commands/*.md -- without this file build_stop1_menu() is live code behind
        # a CLI nothing invokes.
        _cmd = _PP_ROOT / "commands" / "d2a-family.md"
        _cmd_src = _cmd.read_text(encoding="utf-8", errors="replace") if _cmd.is_file() else ""
        if "--family-file" in _cmd_src and "d2a_engine.py" in _cmd_src:
            _ok("V-D2A-FAMILY-COMMAND",
                f"commands/d2a-family.md present ({len(_cmd_src)}B) and names the "
                "--family-file invocation")
        else:
            _fail("V-D2A-FAMILY-COMMAND",
                  f"exists={_cmd.is_file()} names_flag={'--family-file' in _cmd_src}")

        # V-D2A-FAMILY-REACHABLE: the command's instruction must match the engine's
        # REAL flag. Asserted against d2a_engine.py source so the instruction cannot
        # rot into a flag that no longer exists -- a dead instruction is worse than
        # none, because it reads as a working route.
        _eng_src = (_PP_ROOT / "modules" / "duplicate_to_advantage"
                    / "d2a_engine.py").read_text(encoding="utf-8", errors="replace")
        _flag_real = '"--family-file"' in _eng_src
        _menu_on_family = "build_stop1_menu" in _eng_src and "args.family_file" in _eng_src
        if _flag_real and _menu_on_family:
            _ok("V-D2A-FAMILY-REACHABLE",
                "--family-file is a real engine flag and the family path builds the "
                "STOP #1 menu; the command's instruction resolves")
        else:
            _fail("V-D2A-FAMILY-REACHABLE",
                  f"flag_real={_flag_real} menu_on_family={_menu_on_family}")

        # V-D2A-ADVISORY-DECOMPOSITION: the UNDETERMINED advisory must carry the
        # structured request AND name the command -- prose steps were what left the
        # agent to improvise the next action.
        _mega2 = (
            "Build the complete corpus of 25 sibling systems and their constitution. "
            "Each system is a dataset family with its own architecture, registry and "
            "engine. Design the intent compiler, the architecture synthesis engine, "
            "the verification engine, the debugging system, the knowledge graph, the "
            "capability promotion engine and the governance layer. "
        ) * 12
        _rc, _o = _run_gate(_mega2)
        try:
            _ctx = (json.loads(_o) or {}).get(
                "hookSpecificOutput", {}).get("additionalContext", "")
        except Exception:  # noqa: BLE001
            _ctx = ""
        if "DECOMPOSITION REQUEST" in _ctx and "/d2a-family" in _ctx:
            _ok("V-D2A-ADVISORY-DECOMPOSITION",
                f"multi-system brief -> advisory carries the structured request and "
                f"names /d2a-family ({len(_ctx)}B)")
        else:
            _fail("V-D2A-ADVISORY-DECOMPOSITION",
                  f"rc={_rc} has_req={'DECOMPOSITION REQUEST' in _ctx} "
                  f"has_cmd={'/d2a-family' in _ctx} ctx={len(_ctx)}B")

        # V-D2A-DUPLICATE-ROUTES-FAMILY: scope. A multi-system brief routes to the
        # family path; an ORDINARY single proposal must NOT -- there the contract is
        # the whole answer and a family directive would be noise.
        _short_rc, _short_o = _run_gate(
            "build a new system to plan and allocate the frontier token budget, "
            "pricing cost as capital")
        try:
            _short_ctx = (json.loads(_short_o) or {}).get(
                "hookSpecificOutput", {}).get("additionalContext", "")
        except Exception:  # noqa: BLE001
            _short_ctx = ""
        _long_routes = "/d2a-family" in _ctx
        _short_quiet = "/d2a-family" not in _short_ctx
        if _long_routes and _short_quiet:
            _ok("V-D2A-DUPLICATE-ROUTES-FAMILY",
                "multi-system brief routes to the family path; single proposal does "
                f"not (short advisory {len(_short_ctx)}B, no directive)")
        else:
            _fail("V-D2A-DUPLICATE-ROUTES-FAMILY",
                  f"long_routes={_long_routes} short_quiet={_short_quiet}")

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
            "session_id": _sid("vgate"),
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

    # ---------------------------------------------------------------------
    # D2A+ expansion at STOP #1 (PR-D2A-EXPANSION-001). The five gates named
    # in vault/plans/d2a-expansion-2026-08-03.md sec.5 -- the feature shipped
    # code, config and doctrine, and its own acceptance criteria were never
    # written. Built is not verified.
    # ---------------------------------------------------------------------
    # NOTE: `run_family` is deliberately NOT imported here. A function-local
    # import makes the name local to ALL of main(), so importing it would
    # break the earlier fam_fold call with UnboundLocalError -- the same trap
    # this file already documents for `json` below.
    from modules.duplicate_to_advantage.d2a_engine import (
        build_stop1_menu, compute_expansion)

    # A family whose duplication is real but SMALL: two of its three items
    # collapse into one merge group, so exactly one slot is vacated (33%) --
    # under the default 50% threshold.
    _dupe_family = [
        Proposal(name="Duplicate Detection Fabric",
                 description=_CANON.description),
        Proposal(name="Duplicate Ownership Auditor",
                 description=_CANON.description + " overlap ownership audit"),
        Proposal(name="Sonar Haptics",
                 description="haptic feedback for underwater sonar contact "
                             "rendering on a diver wrist unit"),
    ]
    _rep = run_family(_dupe_family)
    _plan = compute_expansion(_rep)
    _menu = build_stop1_menu(_rep)
    _letters = [o[0] for o in _menu.options]

    # V-D2A-EXPANSION-BELOW-THRESHOLD -- under the threshold D never appears,
    # and it is withheld for a STATED reason: no slot was vacated, or the
    # vacated fraction did not clear the threshold. Anything else is the
    # absolute fail-open masking a crash -- exactly how the missing
    # reinforces_id / connects_to arguments stayed hidden.
    _reason_ok = (_plan.expansion_slots == 0
                  or _plan.overlap_pct <= _plan.threshold_pct)
    if ("D" not in _letters and not _plan.applies and _reason_ok
            and "fail-open" not in (_plan.note or "")):
        _ok("V-D2A-EXPANSION-BELOW-THRESHOLD",
            f"overlap {_plan.overlap_pct}% <= threshold {_plan.threshold_pct}% "
            f"(slots={_plan.expansion_slots}, defer={len(_rep.defer)}) -> "
            "option D correctly withheld, and not via fail-open")
    else:
        _fail("V-D2A-EXPANSION-BELOW-THRESHOLD",
              f"applies={_plan.applies} slots={_plan.expansion_slots} "
              f"letters={_letters} note={_plan.note!r}")

    # A family engineered to CLEAR the threshold: three items each restate a
    # DIFFERENT sealed parent (FD-05 budget capital, GK-04 typed edges,
    # SECRET-FIREWALL redaction), so each folds on its own instead of merging
    # into its siblings, and one genuinely-new item survives as the residue.
    # 3 of 4 slots vacated = 75% > 50%.
    #
    # This family exists because the family above can only ever observe option D
    # ABSENT. Asserting "offered" and "withheld" through ONE gate with two _ok
    # branches let the suite report the option-D path green while never once
    # observing option D present: a gate satisfied by its negative branch is
    # bounded by whichever case it happens to be handed, and the positive path
    # -- the whole point of PR-D2A-EXPANSION-001 -- went unmeasured.
    _expand_family = [
        Proposal(name="Token Budget Planner Clone",
                 description=_CANON.description),
        Proposal(name="Graph Coordinate Navigator",
                 description="navigate the knowledge graph by coordinate, register "
                             "typed edges with provenance and confidence between "
                             "nodes"),
        Proposal(name="Secret Redaction Boundary",
                 description="detect credential leaks, redact secrets before any "
                             "emission, enforce a rotation boundary on the firewall"),
        Proposal(name="Sonar Haptics", description=_NOVEL.description),
    ]
    _xrep = run_family(_expand_family)
    _xplan = compute_expansion(_xrep)
    _xletters = [o[0] for o in build_stop1_menu(_xrep).options]

    # V-D2A-EXPANSION-OFFERED -- above the threshold option D is PRESENT and
    # carries real candidates. There is deliberately no withheld branch here:
    # withholding on this family IS the failure.
    if (_xplan.applies and "D" in _xletters and "C" in _xletters
            and _xplan.overlap_pct > _xplan.threshold_pct
            and _xplan.n_requested == _xplan.expansion_slots
            and _xplan.n_survived >= 1
            and len(_xplan.candidates) == _xplan.n_survived):
        _ok("V-D2A-EXPANSION-OFFERED",
            f"overlap {_xplan.overlap_pct}% > threshold {_xplan.threshold_pct}% -> "
            f"options C+D present; requested={_xplan.n_requested} "
            f"survived={_xplan.n_survived} harvested={_xplan.harvested} "
            f"(observed at the DEFAULT config, not a forced threshold)")
    else:
        _fail("V-D2A-EXPANSION-OFFERED",
              f"applies={_xplan.applies} letters={_xletters} "
              f"overlap={_xplan.overlap_pct}/{_xplan.threshold_pct} "
              f"requested={_xplan.n_requested} slots={_xplan.expansion_slots} "
              f"survived={_xplan.n_survived} cands={len(_xplan.candidates)} "
              f"note={_xplan.note!r}")

    # V-D2A-EXPANSION-SILENT -- config suppression, asserted on the family that
    # DOES offer at the default. Suppressing a family that was never going to
    # offer proves nothing about the threshold.
    _lo = compute_expansion(_xrep, {"expansion_threshold_pct": 100,
                                    "expansion_candidate_multiplier": 2})
    _lo_menu = build_stop1_menu(_xrep, {"expansion_threshold_pct": 100,
                                        "expansion_candidate_multiplier": 2})
    if not _lo.applies and "D" not in [o[0] for o in _lo_menu.options] \
            and "C" not in [o[0] for o in _lo_menu.options]:
        _ok("V-D2A-EXPANSION-SILENT",
            f"same family that offers D at 50% -> threshold 100% withholds it; "
            f"both C and D absent (C is expansion-dependent too); "
            f"slots={_lo.expansion_slots} still measured")
    else:
        _fail("V-D2A-EXPANSION-SILENT",
              f"applies={_lo.applies} letters={[o[0] for o in _lo_menu.options]}")

    # V-D2A-EXPANSION-CONFIG -- the threshold is config, not a literal.
    _c0 = compute_expansion(_xrep, {"expansion_threshold_pct": 0,
                                    "expansion_candidate_multiplier": 2})
    _c100 = compute_expansion(_xrep, {"expansion_threshold_pct": 100,
                                      "expansion_candidate_multiplier": 2})
    # The threshold must be READ from config (not a literal) and must actually
    # change the verdict when slots exist. A fail-open plan reports the default
    # threshold, so a mismatch here also catches a masked crash.
    _thresholds_honoured = (_c0.threshold_pct == 0 and _c100.threshold_pct == 100)
    _verdict_moves = (_c0.applies != _c100.applies if _c0.expansion_slots > 0
                      else _c0.applies is False and _c100.applies is False)
    if _thresholds_honoured and _verdict_moves:
        _ok("V-D2A-EXPANSION-CONFIG",
            f"same family, threshold 0% -> applies={_c0.applies}; 100% -> "
            f"applies={_c100.applies} (threshold read from config, not hardcoded)")
    else:
        _fail("V-D2A-EXPANSION-CONFIG",
              f"t0={_c0.threshold_pct}/{_c0.applies} "
              f"t100={_c100.threshold_pct}/{_c100.applies}")

    # The two filter gates below run against `_xplan` -- the plan produced at
    # the DEFAULT config by a family that genuinely clears the threshold. They
    # previously ran against a threshold-0 plan, because the only family in this
    # suite withheld and therefore carried an empty candidate list; a filter
    # asserted over zero items passes for the wrong reason (`all([])` is True),
    # and this repo has already been bitten by exactly that. Both the empty-set
    # escape and the forced-threshold workaround are now gone.
    _cands = _xplan.candidates

    # V-D2A-EXPANSION-NO-SELF-DUPLICATE -- no survivor re-owns a THIRD family.
    _foreign = [c for c in _cands
                if c.self_coverage_pct >= 50
                and c.self_parent not in (c.reinforces_id, c.connects_to)]
    if _cands and not _foreign:
        _ok("V-D2A-EXPANSION-NO-SELF-DUPLICATE",
            f"{len(_cands)} survivor(s), 0 re-owning a foreign parent "
            f"({_xplan.rejected_self_duplicate} rejected during filtering)")
    elif not _cands:
        _fail("V-D2A-EXPANSION-NO-SELF-DUPLICATE",
              "no candidates harvested -- the filter is untested "
              f"(harvested={_xplan.harvested}, note={_xplan.note!r})")
    else:
        _fail("V-D2A-EXPANSION-NO-SELF-DUPLICATE",
              f"{len(_foreign)} survivor(s) re-own a foreign parent: "
              f"{[(c.name, c.self_parent) for c in _foreign][:3]}")

    # V-D2A-EXPANSION-NOVELTY-CHECKED -- every candidate carries a disposition,
    # and a triggered one ships all 13 questions.
    _missing = [c.name for c in _cands if not c.novelty_disposition]
    _short = [c.name for c in _cands
              if c.novelty_disposition == "NEEDS_NOVELTY_PROOF"
              and len(c.novelty_questions) != 13]
    if _cands and not _missing and not _short:
        _ok("V-D2A-EXPANSION-NOVELTY-CHECKED",
            f"{len(_cands)} candidate(s) all carry a novelty disposition "
            f"({sorted({c.novelty_disposition for c in _cands})}); every "
            "NEEDS_NOVELTY_PROOF carries 13 questions")
    elif not _cands:
        _fail("V-D2A-EXPANSION-NOVELTY-CHECKED",
              "no candidates harvested -- the novelty check is untested")
    else:
        _fail("V-D2A-EXPANSION-NOVELTY-CHECKED",
              f"missing={_missing[:3]} wrong_question_count={_short[:3]}")

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
