# Ascension deep research: synthesis (2026-11-20, pane 5a77ca0e, backlog D43)

Sources: `NEAR-MISS-ATLAS-2026-11-20.md` (measured on GEX44 today), `EXTERNAL-STATE-OF-ART-2026-11-20.md` (web research,
each claim tagged MEASURED/UNVERIFIED), the permuter pilot (below), `factory/AUTONOMY-CAPABILITIES-2026-11-20.md`.

## 1. A host defect that silently taxed every compile in /tmp (measured)
- GEX44 `/tmp`: 735,445 entries (712,120 directories), leaked temp dirs of test suites and gates: `orca-prepare-gate-*`
  99,864; `au-cli-*` 22,872; `au-mut-*` families ~11,436 each; `chkpat-*` 13,570; `lca-c-led-*` 14,808; ~398k generic
  `mkdtemp` names. Oldest permuter temp file 2026-10-30.
- wibo scans the working directory on file lookup: the same mwcc compile takes **25.15 s with cwd /tmp vs 0.022 s in an
  empty dir (~1,100x)**.
- Effect seen: the first permuter pilot got 23-62 iterations per 300 s; with per-compile private dirs it gets
  **8,938-16,701** (~300x). The factory sweeps were not hit (judge() compiles in a fresh mkdtemp subdir).
- Two causes to fix: (a) suites that leak temp dirs (a recurring-work-cardinality defect, one per run, never reaped);
  (b) any tool that compiles with cwd = a shared temp dir. (b) is fixed in the pilot's compile.sh. (a) and cleaning
  /tmp are **Owner decisions** (other systems' files).

## 2. Where the work is (bytes first; measured)
NO_COMPILE is the largest byte bucket in every game (WIIPARTY 44.9%, TENNIS 31.4%, MKW base 85.6%, WSR base 38.1%), then
WSR TARGET_AMBIGUOUS (24.0%, never attempted), then the 70-90% band (14-24%). Near misses >=90% are 3.5-20% of bytes.
Near-miss anatomy: >=99% is 74% register-allocation-only; 90-95% is never register-only (INSDEL 44%, OPC+INSDEL 47%);
below 90% structure dominates (OPC+INSDEL 75-83%).

## 3. What the outside world adds (from the external report; MEASURED where marked there)
- Nobody has published autonomous matching of large mwcc functions; Snowboard Kids 2 (N64): "Claude usually gives up"
  above ~1,000 instructions; Melee's tail needed agents + human experts.
- Highest published yields come from **reuse**, not generation: decomp.wtf Mario Party 6, 762 functions in 12 min by
  "twins" (identical bodies of matched code); pbr-decomp PR #38: 15 NW4R `ut` TUs transplanted from ogws, +143 matches.
- LLM tier that worked (SK2, 25% -> 75%): similarity-first queue, matched neighbours as examples, objdiff callable by the
  agent, bigger attempt budgets on fewer functions (p85 = 28 attempts). Mizuchi's top failure: the agent could not run
  objdiff and claimed matches falsely.
- Permuter: works late (register allocation), must never be fed to an LLM (SK2 doom loops); accept score 0 only.
- Per-TU compiler versions differ inside one game (petari: libraries GC 3.0, game code GC 3.0a3).

## 4. Ranked plan for the self-certifying loop (D43), each step 0-lost-gated by the factory lane
| # | step | addresses | basis | tokens |
|---|---|---|---|---|
| 1 | per-function ledger, targets pinned by content hash | everything (memory of tries) | atlas defect: 416 rows pointed at rebuilt objects | 0 |
| 2 | twin propagation: masked-body identity across our 5 games + 6 donors | library code, duplicates | ours 3,541 ready; MP6 762 / 12 min | 0 |
| 3 | library TU transplant by SDK banner version | library code (12-91% of bytes) | pbr-decomp +143; m3a proved 2,563 WSR fns identical | 0 |
| 4 | vs2 full sweeps on MKW, MKWLIB, WSR | NO_COMPILE (largest bytes) | WIIPARTY NO_COMPILE -58% | 0 |
| 5 | address-keyed targets | WSR 24% of bytes | never attempted | 0 |
| 6 | per-TU compiler/flag arms (+ lmw/stmw off) | OPC near misses, compile fails | atlas: 31 lmw/stmw substitutions at >=90; petari versions | 0 |
| 7 | permuter post-stage on >=95% (private compile dirs) | REGALLOC near misses | pilot below | 0 |
| 8 | deterministic rewrite operators for named patterns (types widths, boolean idioms, branch polarity, locals) | 90-99% INSDEL/OPC | atlas pattern table | 0 |
| 9 | m2c `--context` with donor/SDK headers, fallback re-lifts | lift + compile fails | external (effect unpublished) | 0 |
| 10 | LLM tier on the residual, SK2 pattern + ledger history; agent-written operators adopted only after held-out gain | far misses, large fns | SK2 25->75%; ours ~2 certs/1M tokens today | yes |

## 5. Permuter pilot (pre-registered: 30 REGALLOC_ONLY + 20 INSDEL at >=95, WIIPARTY+TENNIS vs2, 300 s each, success =
our compile + objdiff 100.0)
- Run 1 (compile cwd = /tmp): invalid instrument (23-62 iterations per budget). Run 2 (TMPDIR clean, compile.sh cwd =
  same growing dir): invalid (throughput fell as the dir filled). Run 3 (private dir per compile): valid.
- **Run 3 final (50/50): 5 MATCH (10%), 19 IMPROVED, 26 NONE**, every MATCH re-verified by our compile + objdiff 100.0.
  REGALLOC_ONLY 4/30 MATCH (sizes 16, 28, 76, 148 B) + 4 improved; INSDEL 1/20 MATCH (284 B) + 15/20 improved. 300 s
  per function, 8,938-16,701 iterations. Reading: the permuter is a real 0-token operator at >=95% (about 1 in 10 per
  5 minutes of 2 cores), and improvements are worth keeping as the next starting source (the ledger records them).

## 7. After the Owner's "rec" (measured, 2026-11-20 ~13:00-13:50Z)
- **/tmp cleanup:** `research/tmpclean.py` (dry run first; per item re-stat of owner + mtime > 2 days + no live cwd/fd
  inside, immediately before its own deletion). DELETED 486,087 (= manifest `research/tmp_cleanup_manifest.txt` lines);
  kept 35,617 recent, 76 in use, 1 gone. /tmp 737,395 -> 251,877 entries, and growing again (~+320 in minutes: the
  leaking suites still run).
- **Mechanism, corrected by a 2x2:** the cost is the compile's *working directory* being the crowded dir (mwcc via wibo
  with cwd = /tmp: 25 s at 737k entries, 3.75 s at 251k); TMPDIR, an absolute input path in /tmp, or a sparse subdir of
  /tmp cost nothing (0.013-0.023 s, rc 0, object written). Rule: **every compile runs in its own empty working dir.**
  (An intermediate 6.9 s reading came from a stale copy of the run-1 compile.sh; discarded.)
- **Ledger built** (`factory/ledger.py`, spec `vault/specs/ascension-function-ledger.md`): 21 runs discovered, 0
  unmapped, 86,925 functions, 6,315 target objects hashed, build 15 s. AC (a) per-run counts == census.json for all four
  atlas runs; (b) states sum per binary; (c) two builds -> identical report; (d) selftest both poles PASS. Bytes by state:
  RMCP01 CERT 9.7% / NO_COMPILE 60.7% / LIFT_FAIL 18.6%; RZTP01 CERT 3.9% / LIFT_FAIL 29.6% / NO_COMPILE 26.8% /
  TARGET_AMBIGUOUS 16.6%; SUPP01 CERT 2.7% (+1.3% MATCH gated) / NO_COMPILE 36.3%; TENNIS MATCH 5.1% (no lane carve yet,
  D4) / COMPILES 31.1%; FIFA main.dol only, 90.4% UNATTEMPTED (the fifaf module split is not swept yet).
- **Target drift is massive on MKW and WSR:** 15,457 (RMCP01) and 14,787 (RZTP01) functions have sweep attempts whose
  target object no longer holds that symbol; their stored % describes rebuilt objects, so the ledger caps them at
  COMPILES. The MKW/WSR sweeps must be re-run against pinned objects before their near misses can be worked.
  80 MKW/MKWLIB snapshot names do not map to an address (34 + 44 unmapped, 2 ambiguous): counted, not dropped.
- **Still open from the rulings:** the leaking suites (orca-prepare-gate, au-cli/au-mut-*, chkpat, lca-c-led, generic
  mkdtemp) are not fixed; /tmp refills. PADDED detection is not built (column exists, NULL = not assessed).

## 6. Owner decisions
**Owner 2026-11-20: "rec" (all three as recommended).** (1) Clean GEX44 /tmp of the leaked temp dirs (kobii-owned, idle
> 2 days, known leaked prefixes; a name manifest is kept) and queue the leaking suites for a fix. (2) PADDED: a
byte-identical match that needed stack padding counts as certified, tagged `PADDED`, reported separately. (3) Build the
D43 ledger (step 1).
1. Clean GEX44 `/tmp` (leaked test dirs of other systems) and fix the leaking suites? It taxes any compile run there.
2. Does a byte-identical match that needed stack padding count as certified? (SMS rejects such matches as fake; our
   oracle is bytes, so it would count unless tagged.) Recommendation: count it, tag it `PADDED`, report it separately.
3. Go for D43 step 1 (ledger) now?
