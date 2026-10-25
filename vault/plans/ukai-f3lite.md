# ukai F3-lite -- index vault/lessons/ and vault/hard_rules/ as recall sources

Goal `ukai-f3` (capital packet sha 0c8d2ff0416f, Owner "approve ukai-f3 only" 2026-10-11). cwd = C:\Users\User\Apps\pp-ukai-f3
(branch ukai/f3 from ukai/f0 d3e64cd6). Lease L1 cap 2,100,000. Route: vault/plans/route-ukai-f3lite.json (10 calls).
git = & 'C:\Program Files\Git\cmd\git.exe' -C 'C:\Users\User\Apps\pp-ukai-f3'; python = & 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'.
Never Set-Location; absolute paths only. Never read transcripts. Never write the LIVE recall index: every index build and
eval in this unit runs with $env:CPP_RECALL_DIR = a fresh temp dir and $env:CPP_RECALL_NO_SPAWN = '1'.

## Evidence (from F0, commit d3e64cd6)
- vault/evals/recall/misses-baseline.md: 3 source-not-indexed misses -- q18 `vault/lessons/parallel-explore-cascade.md`,
  q19 `vault/lessons/plan-files-not-allowlisted.md`, q48 `vault/hard_rules/HARD_RULES.md`.
- modules/gsd_x/recall.py:86 default_sources() lists memories, UKDL, the global HARD-RULES.md, CLAE, plans, SEO maps --
  not PP_ROOT/vault/lessons/*.md and not PP_ROOT/vault/hard_rules/HARD_RULES.md.
- Baseline: recall@5 0.64 (32/50), MRR 0.5857, FP rate 0.3333, report vault/evals/recall/report-baseline.json.

## Obligation (scope -- nothing else)
1. Gate FIRST (RED): in tools/test_recall_eval.py (or a new tools/test_recall_sources.py) assert default_sources() yields
   kind "lesson" for vault/lessons/*.md and kind "hard-rules-pp" (or reuse "hard-rules") for vault/hard_rules/HARD_RULES.md,
   with a positive control (an existing kind still present). Record RED, commit.
2. Add both sources to default_sources() (discovered by glob, scope "global"). GREEN, commit.
3. Build a private index (CPP_RECALL_DIR temp) with recall.refresh(); run tools/recall_eval.py --db <that db> --label f3lite
   writing vault/evals/recall/report-f3lite.json. Compare to report-baseline.json: q18/q19/q48 status, recall@5, MRR,
   FP rate, latency p95. Commit the report.
4. Receipt vault/plans/ukai-f3lite-receipt.md (<= 20 lines): `Status: DONE` (or PARTIAL + blocker), commits, gate red->green,
   before/after metrics table, call count.

## Stop-loss and limits
- Stop if recall@5 falls below 0.64 twice after a local fix, or the lease nears its cap before step 3 is committed.
- Excluded: F4 vocabulary bridge / score floor, F2, F1, F5-F7; any file other than modules/gsd_x/recall.py, the recall tests
  and vault/evals/recall/ (+ the receipt). Do not copy anything into ~/.claude.

End with `HANDOFF NOTE: F3-lite done` (or the blocker).
