# R1 REFORECAST - recon-factory critical path to Checkpoint 50 (ANALYSIS ONLY)
Mission: UNKNOWN (no m-<12hex> id found in route-R1.json or env) | Source: gen3/recon-reforecast/DOSSIER.md (sha-pinned, recon HEAD 2ca5ee3) | Nothing armed, nothing run.
Anything not in the dossier is UNKNOWN. Floor 110,835/call (route-floors.json, cited in packet). Frontier 12,000/call = the
packet's own per-call packet growth ASSUMPTION; no dossier line measures CP50 frontier. Call counts are my estimates: LOW confidence.

## 1. Remaining items
Format: Non-Work proof | CP class | work class / capital class | cost (PREREQ only).

### Phase 2 - GEX44 leg of oracle parity (S1)
1. Non-Work proof: the local half is done: 02-01 cross-plane 77/77 byte-identical, ac1f1ae, 02-PARITY.json present
   (DOSSIER 151, 187, 199-200). NOT proven done: returned-object A/A leg + drill, deferred in 02-02 (DOSSIER 179-185).
2. Class: PREREQUISITE_FOR_CP50 (GAP-1 CRITICAL blocks Ph 7 and 8, DOSSIER 89, 108, 129). Route was ruled: split judge, no patch 07 (edf82a8, DOSSIER 193).
3. Work: engineering. Capital: WII_NINTENDO (pinned mwcceppc f54d5644 under wibo, DOSSIER 30).
4. Cost: lower 3 calls x 110,835 = 332,505 | expected 8 x (110,835+12,000) = 8 x 122,835 = 982,680 | envelope 982,680 x 1.2 = 1,179,216.
   Confidence LOW. Not in the cost: GAP-10 Owner ratification of the job budget (blocker, DOSSIER 35, 143).

### Phase 3 - Capital promotion
1. Non-Work proof: SRC PROVEN is 5 of 34,159 (DOSSIER 214), so the 289 donors are not promoted. Not NO_WORK.
2. Split. (a) Verified-bundle seam in levels.py + donor registration (GAP-2/6/12, DOSSIER 51, 53, 59): PREREQUISITE_FOR_CP50,
   because Ph 7 checkpoint promotions use the same seam (DOSSIER 90). (b) Bulk promotion of 289 donors + model matches:
   DETERMINISTIC (GEX44 compiles through promote()) and POST_CP50 (calibration evidence, not an input to the draw).
3. Work: engineering (a), compute (b). Capital: WII_NINTENDO for the toolchain, GAME_SPECIFIC for donor source text.
4. Cost (a) only: lower 3 x 110,835 = 332,505 | expected 6 x 122,835 = 737,010 | envelope 737,010 x 1.2 = 884,412. Confidence LOW-MEDIUM.
   (b) POST_CP50: no number.

### Phase 5 - Closure census + population matrix (S6 + W3)
1. Non-Work proof: levels.jsonl carries class only (5 values, DOSSIER 218); no shape family, anchor, closure or depth keys (DOSSIER 211). Not NO_WORK.
2. PREREQUISITE_FOR_CP50: the Ph 7 draw is stratified by CXX/PS/SDA/LIB/size/centrality (DOSSIER 86), which only the matrix supplies.
   Mostly DETERMINISTIC: "existing evidence only, absent fields stay absent" (DOSSIER 67-68).
3. Work: deterministic extraction + one reproduction drill (1,131/541/302/148/115/25 with Jsk/Png controls). Capital: ENGINE_FAMILY.
4. Cost: lower 4 x 110,835 = 443,340 | expected 9 x 122,835 = 1,105,515 | envelope 1,105,515 x 1.2 = 1,326,618. Confidence LOW.

### Phase 6 - Router (S3)
1. Non-Work proof: none; BEHAV/XFORM are UNKNOWN for all 34,159 rows (DOSSIER 212, 217). Not NO_WORK.
2. PREREQUISITE_FOR_CP50: CP50 reports a tier histogram and cost vectors per tier (DOSSIER 87). Inference: the routed arm needs it;
   the dossier does not define arms A/B/control, so this is the weakest classification here. DETERMINISTIC fast path is part of the build.
3. Work: engineering. Capital: UNIVERSAL (routing, not game-bound).
4. Cost: lower 3 x 110,835 = 332,505 | expected 7 x 122,835 = 859,845 | envelope 859,845 x 1.2 = 1,031,814. Confidence LOW.

### Phase 7 - G0 freeze + Checkpoint 50
1. Non-Work proof: none; nothing drawn or sealed (DOSSIER 20, 86).
2. Two parts. G0 freeze (draw ~300, sealed holdout, preregistered "materially falls", DETERMINISTIC): PREREQUISITE_FOR_CP50,
   it must be committed before the first run (DOSSIER 86). The CP50 run itself is the target, not a prerequisite.
3. Work: deterministic draw + cognitive run. Capital: GAME_SPECIFIC for the run, UNIVERSAL for the freeze protocol.
4. Cost, freeze only: lower 2 x 110,835 = 221,670 | expected 4 x 122,835 = 491,340 | envelope 491,340 x 1.2 = 589,608. Confidence MEDIUM.
   The 50-function run: no number (see section 4; "~10M x plans" is not used anywhere).

### Phase 8 - Checkpoints 150/300
Non-Work: none. Class POST_CP50 ("only if checkpoint 50 meets the criterion", DOSSIER 20, 105). Capital: UNIVERSAL. No number.

### Phase 9 - Seal
Non-Work: none. Class POST_CP50; the family PROPOSAL cites CP50 numbers (DOSSIER 118). No MERGE_EXTINGUISH covers it; the
red team stays with oneshot-architect-auditor. Capital: UNIVERSAL. No number.

NO_WORK / MERGE_EXTINGUISH: no remaining item qualifies in full; only the Ph 2 local half is NO_WORK.

## 2. Minimal path to CP50 (before the first CP50 run)
Order: Ph 2 GEX44 leg -> Ph 3 seam -> Ph 5 -> Ph 6 -> Ph 7 G0 freeze. Ph 5 and 6 do not need GEX44 and can run in a parallel lane.
| figure | calls | tokens |
|---|---|---|
| lower bound | 15 | 1,662,525 |
| expected verified completion | 34 | 4,176,390 |
| safety envelope | 34 x 1.2 | 5,011,668 |
Sensitivity (measured anchor): T3 plan 04-03 averaged 10,269,382 / 63 = 163,006 per call (DOSSIER 241-246). At that rate the
same 34 calls cost 5,542,204. So the expected figure is 4.18M-5.54M; the 12k frontier is likely too low. Excludes the CP50 run, Owner ratifications, and any repair of a failed phase.

## 3. CP50 design amendments TO PROPOSE (ROADMAP not edited)
(a) CP50 runs under the Context Rent architecture: each cohort or family gets a fresh small context and ends checkpoint ->
    SAFE_TO_FORGET -> process ends. Owner: ce-lifecycle-v. Dependency: ctx-rent S2 = WU-5 on tranche T-S2 = 1.9M (DOSSIER 281-283, 289-291).
    CP50 must not start before WU-5 reports. Not designed here; do not touch the S2 diff.
(b) Unit = novelty cluster or family frontier, not a function. Basis: recurrence 75-77% of DELTA episodes (DOSSIER 264).
(c) Preregistered learning-curve test: new-cognition cost of functions 31-50 vs 1-20. No fall means stop and fix family solving
    before Ph 8. Freeze the threshold in G0 together with the "materially falls" rule.
(d) Per function or cohort, record: fresh floor; live frontier; mean and p95 physical context; marginal Context Rent; physical calls;
    deterministic vs cognitive; novelty; cost to verified completion; proof cost; rehydrations; family reuse; capital class.

## 4. T3 leaks to fix before CP50 (saving per plan, with basis)
T3 plan 04-03: 10,269,382 processed, 63 calls vs champion 16.6M (ratio 0.62, one sample, DOSSIER 245-248).
| leak | saving per plan | basis |
|---|---|---|
| no gsd_dossier.py (plan file used as dossier) | <= 489,018 | 3 calls over the 60 bound x 163,006 (DOSSIER 253). Same 3 calls as the 63>60 row: counted once |
| 63 > 60 calls | included above | DOSSIER 241, 253 |
| truncated source_packet (PARTIAL) | UNKNOWN | worker read source directly; no per-read split in the dossier |
| worker re-reading the code | UNKNOWN | same; worker is 42 calls, 7,256,620 |
| main pane 3,174,989 of 10,269,382 (30.9%) | UNKNOWN | ceilings only: meta-work -18..-23% at c=0, fresh-worker -23..-43% (DOSSIER 261, 263); stage0 says "Ceiling, not saving" |
| no separate RED | none (gate integrity) | worker wrote code and gates in one step; gates have red controls (DOSSIER 252) |
| receipt without a mission id | none (attribution) | spend cannot be tied to a mission without it |
Only 489,018 is derivable (4.8% of T3). Everything else stays UNKNOWN until the CP50 per-call record (3(d)) exists.

## 5. Metrics
Cross-Title Reconstruction Reuse Rate = functions in title B verified by reusing a family, donor or solution proven in another title,
divided by functions verified in title B. A reused solution counts only if it passed the same oracle pair. Higher is better.
 - WSR baseline: UNKNOWN. The dossier has no cross-title record. Verdict counts only: SRC PROVEN 5, STRUCT PROVEN 82, 34,159 total (DOSSIER 214-215).
Novel Cognitive Cost per 1,000 functions = (processed tokens in cognitive calls excluding fresh floor, rehydration and proof) / verified functions x 1,000.
 - WSR baseline: UNKNOWN. Reference level only: irreducible new-cognition floor 6.3 / 7.0 / 9.8% of processed for KSR / InfinityOps / KME
   (gen3_t2, DOSSIER 264). It is a ratio of whole-mission spend, not a per-1,000 figure; the verified denominator is 5 SRC PROVEN, too small to divide.

## 6. FULL_WSR
Stays a hypothesis. No budget figure. These CP50 measurements would collapse its range: the 31-50 vs 1-20 curve; deterministic share by
class (LEAF_INT 11,656, FRAME_INT 11,594, FP 4,516, CXX 3,336, PS 3,057 - DOSSIER 218); mean and p95 cost per function; family reuse rate;
proof cost per function; rehydrations per cohort.

## 7. Open points (decided here, none left as a question)
 - Ph 6 as a prerequisite rests on an inference; marked weakest. Confirm by reading the arm definitions when Ph 7 is planned.
 - Frontier 12k is an assumption; use the 163,006/call sensitivity until CP50 data exists.