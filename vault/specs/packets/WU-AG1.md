done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_gsd_dispose.py
work_tree: C:\Users\User\Apps\pp-gsdx-factory
receipt: vault/specs/gsdx-factory.RECEIPT-AG1.json

# WU-AG1 -- Proof of Non-Work: every obligation gets a disposition before any worker is armed

Plan (binding, Owner "y" 2026-10-08): `vault/plans/gsdx-econ-recon-program-plan.md` on the LIVE tree
(`C:\Users\User\.claude\skills\claude-power-pack`, commit 3356f615) -- sections 4 (unit A-G1) and 5 (the obligation
table). Read only those two sections. Fresh worker; no Agents, no GSD commands; never push.

## 0. Facts (verified 2026-10-08 ~22:50Z; re-check, do not trust)
- This worktree = branch `gsdx-factory/main`, cut from `cost-collapse/main` at 42ac887c. Goal `gsdx-factory` binds
  this root (cap 8,000,000 for tranche T1 = all of Part A).
- `tools/gsd_dossier.py` exists HERE (branch-only, not on live). It has: `concepts_from_contract`, `rg`, `module_map`,
  `concept_hits`, `run_cmd`, `build`, `main`; CLI flags `--repo --contract --out --module-root --glob --cmd
  --salvage --per-concept(6) --max-bytes(160000) --cmd-timeout(300)`. Outputs `dossier.md`, `refs.jsonl`,
  `dossier.summary.json`. Zero model calls.
- `cost-collapse` has a live worker chain editing `tools/gsd_mission.py` and `tools/route_admission.py`
  (E4a -> E3C1 -> E3C2 -> E4b). **Do NOT edit either file.** Wiring the arm-time refusal into them is unit A-G3.
- Windows: PowerShell tool; git `C:\Program Files\Git\cmd\git.exe` (use -C, no cd); python = done_gate path;
  `$env:PYTHONIOENCODING='utf-8'`; test output to a log file, read only `_PASS=` and FAIL lines.

## 1. Disposition vocabulary (closed set, exact strings)
NO_WORK, ALREADY_SATISFIED, REUSE_EXISTING, MERGE, DETERMINISTIC, CERTIFIED_CAPABILITY, CHEAP_COGNITION,
STRONG_COGNITION, FRONTIER_COGNITION, DEFERRED_EXTERNAL, UNKNOWN.
NO_WORK / ALREADY_SATISFIED / REUSE_EXISTING / MERGE / CERTIFIED_CAPABILITY are admitted ONLY with an `evidence`
entry that a deterministic probe re-checked (probe kinds: `file_exists`, `commit` (sha reachable from a named ref),
`grep` (pattern + path, >=1 hit), `cmd_rc0` (command + expected marker line)). A claimed disposition whose probe
fails becomes UNKNOWN with the probe's output -- never silently kept. MERGE names its target obligation id.

## 2. Build (extend gsd_dossier.py; no new module unless the file passes ~500 lines)
`gsd_dossier.py dispose --obligations <json> --out <dir> [--check]`:
- input: list of {id, text, block, claimed, evidence[], merge_into?}.
- output: `dispositions.json` (every input id exactly once, final disposition, probe results) + a summary line
  `DISPOSE counts=<per disposition> unknown=<n> undisposed=<n>`.
- `--check`: exit 1 if any obligation is missing, duplicated, outside the vocabulary, or a non-cognitive claim
  failed its probe; exit 0 otherwise. This is the gate A-G3 will call at arm time.
`tools/test_gsd_dispose.py` (V-DISPOSE-*, hermetic temp dir, BOTH poles): vocabulary closed; missing id -> red;
duplicate id -> red; ALREADY_SATISFIED with a passing probe -> kept; same claim with a failing probe -> UNKNOWN;
MERGE without target -> red; a control where every claim is valid -> exit 0. Print `DISPOSE_PASS=n/n`.
Mutation drill (`tools/mutation_drill.py`, isolated copy): make the probe always pass -> a V-DISPOSE gate goes red.

## 3. Real input -- canaries A1 and B1
Write `vault/specs/gsdx-factory/obligations.json`: one row per row of plan section 5 (17 rows) plus Part A units
A-G1..A-G5 (section 4), each with the plan's claimed disposition and probes you can actually run from this laptop
(GEX44-only evidence -> claim UNKNOWN with reason `gex44_probe_pending`; do not ssh in this unit). Run `dispose
--check`. Record the honest counts. Canary A1/B1 PASS = at least one obligation ends NO_WORK/ALREADY_SATISFIED/
REUSE_EXISTING/MERGE with a re-checked probe, AND zero undisposed. If every claim collapses to UNKNOWN, that is the
result: record it, do not weaken the probes.

## 4. Close
Pathspec commits in this worktree only (tool + test, then obligations + dispositions). Write the receipt (gate lines,
drill result, counts, commit shas, metered calls). Update `RESUMPTION_FILE.md` (worktree root, create if absent, <400
words): A-G1 done, next A-G2 (proof reuse by dependency fingerprint, slim-t2), A-G3 waits for cost-collapse E4b.
Do not arm the next unit: the program's next coordinator does.

## Budget
At most 14 model calls (route-AG1.json). On checkpoint: write the receipt and stop. End with `HANDOFF NOTE:` and one line.
