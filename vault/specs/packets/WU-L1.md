done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/gsd_dossier.py dispose --obligations vault/specs/gsdx-factory/l1/obligations.json --out vault/specs/gsdx-factory/l1/dispositions.json --check
work_tree: C:\Users\User\Apps\pp-gsdx-factory-2
receipt: vault/specs/gsdx-factory.RECEIPT-L1.json
successor: vault/specs/packets/WU-W3.md (compiled by the coordinator from GRAPH.md; do not write it)

# WU-L1 -- Obligation ledger: every section of the Owner's GSD X prompts gets a probed disposition

Plan (binding, Owner "y" 2026-10-09): `vault/plans/gsdx-factory-master-plan.md` section 2 W2. Fresh worker, no Agents,
no GSD commands, never push, never Set-Location / cd (git -C and absolute paths; child-process cwd only).
Work class: EXTRACTION + CLASSIFICATION. Most rows are doctrine, not work; prove that with probes, do not narrate it.

## 0. Facts (verified by the coordinator 2026-10-09; do not re-derive)
- Sources (pinned): `vault/specs/gsdx-factory/sources/*.txt`, 4 Owner prompts. Already segmented by
  `tools/gsdx_obligation_extract.py` into `vault/specs/gsdx-factory/l1/sections.json`: 595 rows, 526 distinct titles,
  each {id, title, body_sha, lines, sources, body}. `--check` says FRESH. Do NOT read the sources; read sections.json
  rows in slices (python one-liners that print id/title/first lines), never the whole file into context.
- Gate tool: `tools/gsd_dossier.py dispose` (lines 185-280). Vocabulary: NO_WORK ALREADY_SATISFIED REUSE_EXISTING MERGE
  DETERMINISTIC CERTIFIED_CAPABILITY CHEAP_COGNITION STRONG_COGNITION FRONTIER_COGNITION DEFERRED_EXTERNAL UNKNOWN.
  NO_WORK/ALREADY_SATISFIED/REUSE_EXISTING/MERGE/CERTIFIED_CAPABILITY need a probe (file_exists | commit | grep |
  cmd_rc0) that passes NOW; MERGE needs merge_into = an obligation id. Absolute probe paths are allowed.
- Where finished work lives (evidence for probes):
  - Canonical Reconstruction Factory: `C:\Users\User\Apps\recon_work\wt_keosdtk_home\.planning\workstreams\recon-factory\ROADMAP.md`
    (phases 1, 01.1, 4, 5, 6 checked [x]; 3a seam dcd9178; 7 G0 freeze e3b0b82; 2 A/A PASS cfedba3). Phases 2 close,
    3 promotion, 7 CP50, 8 (conditional), 9 seal are open. Never write in that worktree (569 dirty paths).
  - gen3 receipts: `C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cognitive-economy\gen3\*-receipt.md`.
  - ce-lifecycle-v3 (owns call units / estimator / lease edge / steward install): `C:\Users\User\Apps\pp-ce-lifecycle-v3\vault\programs\cognitive-economy\lifecycle\*-receipt.md`
    (WU-S3 growth estimator ea5cf9c8, WU-S4 lease edge + physical-call pricing 753a2a4a).
  - This tree: RECEIPT-AG1/S4/S1 in `vault/specs/`, the Master Plan, `vault/specs/gsdx-factory/obligations.json` (A-G1's 22 rows).
  - Full WSR is out of scope (DEFERRED_EXTERNAL, recorded): gsdx program plan section 5, TRANCHE-CP50.

## 1. Steps (commit after each green step, pathspec only, -F msgfile)
1. Vocabulary: add SUPERSEDED (needs a probe that the superseding row id exists in the same obligations file; field
   `superseded_by`) and WAIT_DEPENDENCY (needs `depends_on` naming an obligation id or an external unit) to
   DISPOSITIONS in gsd_dossier.py, with gates in tools/test_gsd_dispose.py: V-DISPOSE-SUPERSEDED-NEEDS-TARGET and
   V-DISPOSE-WAIT-NEEDS-DEP, both poles. The suite must stay green (17/17 before + yours).
2. Write `tools/gsdx_l1_classify.py` (deterministic): read sections.json, emit `l1/obligations.json`
   {expect: [all 595 ids], obligations: [...]}. Rules, in order:
   - an older version of a title that also appears in a newer source (normalized title) -> SUPERSEDED, superseded_by = newest;
   - title or first 3 body lines that are doctrine (law, rule, trap, kernel, principle, contract, mode, role, handoff,
     iteration, delegation, loops, concurrent writers, micro-commits, scope boundary, traps) -> ALREADY_SATISFIED with a
     grep probe into the Master Plan or the rule's enforcing file (if no enforcing text exists: CHEAP_COGNITION, reason
     "doctrine without an enforcer", never a fake probe);
   - everything else -> UNKNOWN with reason "needs review" (this is the review queue).
   Print counts per disposition. Commit.
3. Review queue (cognition, the only model-heavy step): for each UNKNOWN row read title + first 12 lines only. Map it to
   recon-factory phase, gsdx Part A unit (A-G2..A-G5), ce-lifecycle-v3 unit, or Master Plan W-step. Assign
   ALREADY_SATISFIED / MERGE (merge_into a row id) / REUSE_EXISTING with a passing probe, or a work disposition
   (DETERMINISTIC / CHEAP_COGNITION / STRONG_COGNITION / FRONTIER_COGNITION / WAIT_DEPENDENCY / DEFERRED_EXTERNAL) with a
   one-line reason. Write overrides into `l1/review.json` {id: {claimed, evidence?, merge_into?, reason}} which the
   classifier applies last. Work in slices of about 40 rows per tool call. UNKNOWN may remain only with a stated reason.
4. Run the done_gate until exit 0 (errors list empty). Then `l1/GRAPH.md` (<= 80 lines): every non-terminal row grouped
   into proposed work units: unit, rows, work class, resolver tier (ZERO_MODEL / slim-t2 / top / frontier), estimated
   model calls n, and cost C(n) = n*F + g*n*(n-1)/2 with slim-t2 F=19,000 g=1,700, top F=121,000 g=2,000; a dependency
   column (WAIT on ce-lifecycle-v3 INST2, GEX44 port, CP50 criterion).
5. Receipt `vault/specs/gsdx-factory.RECEIPT-L1.json`: counts per disposition, unknown count with reasons, gate output
   line, commits, the 5 largest work units from GRAPH.md. Commit. Do not arm anything.

## 2. Budget and closeout (protected)
Envelope: about 28 model calls / 45 tool calls. At 38 tool calls STOP new review work: run the gate, commit what is
green, write the receipt with Status PARTIAL and the exact remaining row ids. A receipt with PARTIAL is a valid end; dirty
uncommitted work is not. End your final message with `HANDOFF NOTE:` and one line.
