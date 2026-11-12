# Ascension reorientation brief (Owner-approved 2026-11-11; plan: laptop vault/programs/ascension/AUTOPILOT-REORIENT-PLAN.md)

Goal: every generation must increase the real capacity to certify the functions that can legitimately be certified,
not repeat attempts. The first task is discovering which structural limitation has the largest demonstrated potential.
Candidate counts below are BINARY_EXACT or diagnostic, never certificates; no past rate is extrapolated to the residue.

## Measured state (re-derive before use)
- KSR main frontier 8,687 / 30,388 CERTIFIED; CNM 9,941; NO_COMPILE 5,453; FLAGS_SPLIT 3,447; NO_TARGET 2,858
  (evidence/ksr-frontier/counters.json). Profile ksr-v5r-s25stage receipts: S26C 582, S26D 24, S28K fwidth 15
  (separate files; transformed-source certificates are outside the lane frontier until the Owner decides).
- Tennis 1,198 / 1,797; S23-S27 added 0. No demonstrated byte mechanism for Tennis.

## Causal portfolio (shared causes)
- FLAGS_SPLIT: all 3,447 fns sit in 6 objects; both -sdata arms hold exclusive matches, so the lane admits no arm for the
  whole object. 673 fns are BINARY_EXACT under some arm (652 under the best single arm), raw m2c source, existing recipes
  (evidence/ascension/s25/flags/census.json: excl sd0 21, excl sd8 181, 16 arm switches in address order).
- No admissible arm strands the exacts of other levers: S26D D3 37 of 60, S28K fwidth 15 of 30.
- COMPILES_NO_MATCH: float width (target stfs/lfs/psq vs ours stfd/fctiwz) dominates INLINING_OR_CALLSHAPE 66/200
  (s26d/cnm/gaps.md); grammar gaps without an operator: OTHER_CODEGEN 24, SAVEAREA 11 of 200.
- NO_COMPILE: missing types/prototypes/struct layout; compile movement rarely becomes bytes (S27 T2/T4: 0 exact).

## Ranked opportunities
A. Object arm admissibility (TU ownership). B. Float-width typing (fwidth; S28K certified 15 via unchanged certify.decide).
C. Type recovery for NO_COMPILE (feeds CNM; lowest demonstrated byte yield).

## Next KSR generation (Owner-approved): A1 + A2, measured only, no certificates, cap 6.5M total
A1, on the 6 main-frontier FLAGS_SPLIT objects:
- Fit set: the 202 exclusive matches; fit the minimal contiguous segmentation of each object consistent with them.
- Held-out oracle: functions labelled by the target object's own relocations (SDA21 vs HALO_small) that are NOT in the
  fit set, using the S26D D2 label rule and V0 validity check unchanged (evidence/ascension/s26d/flags/criteria.md).
- Rivals: R-int per-function interleaved recipes; R-flag the arm difference comes from another flag (V0 fails).
- Per object: SUPPORTED = V0 valid, >= 3 labelled held-out fns per side, 0 contradictions; REFUTED = V0 valid and >= 1
  contradiction; otherwise UNDETERMINED.
- Measure: BINARY_EXACT under per-segment arms (prediction <= 673), diagnostic only.
- Expansion: SUPPORTED on objects covering >= 50% of the 3,447 -> report for the Owner (a re-split stage would need an
  additive profile with all six S26C conditions; it is not part of A1). Stop: REFUTED on auto_03_80007EE0 and
  auto_03_800C4EE4 -> negative row with reopen condition "a second independent TU-boundary signal".
A2: of the 52 stranded exacts (D3 37, fwidth 15), how many sit in FLAGS_SPLIT vs NO_MATCH objects (a join, ~0.5M).
Progress class expected: INFORMATION (criteria file frozen in a commit before the run; result as json in a later commit).

## After A1 (by measured outcome)
- B1: deterministic float-evidence scan over the 9,941 main CNM (and Tennis 164), then a frozen 200-fn held-out under the
  unchanged certify.decide only if applicability >= 10%. Expand when held-out certified >= 3% at <= 300K tokens per
  certificate; stop at < 1% or when certify.decide rejects claimed exacts. Cap 8M.
- C1: pair NO_COMPILE->COMPILES fns from S27/D3 with fwidth (does compile movement become bytes?). Cap 6M, after B1.
- Tennis lane (Owner-approved 2026-11-11): the ONLY admitted Tennis generation is B1-T, cap 5M total: a deterministic
  float-evidence scan of the 164 Tennis COMPILES_NO_MATCH (target stfs/lfs/psq vs ours stfd/fctiwz), criteria file
  frozen in a commit before the scan; only if applicability >= 10%, a frozen held-out pilot of the S28K fwidth operator
  under the unchanged certify.decide of an EXISTING Tennis profile (no new profile in B1-T). Below 10%: record the
  refuted hypothesis as a json result and a negative row. Nothing else is planned for Tennis.

## Boundaries (unchanged)
Existing profiles and certify.decide untouched; receipts and canonical context untouched; additive profiles only under all
six S26C conditions; the autopilot's unlocked ceiling is fixed by the Owner and is not a planner topic.

## Owner decisions 2026-11-12 (laptop pane ddf4990e; Owner "1. 120M 2. rec 3. hazlo todo y rec")
- Budget: unlocked ceiling raised by 120M (unlocked = total = 405,261,779; nothing frozen). Not a planner topic.
- Headline: t1 tools/ksr_headline.py (gate test_ksr_headline) derives KSR main CERTIFIED 9,308 / 30,388 =
  ksr-v5r 8,687 + ksr-v5r-s25stage 582 verbatim + 39 transformed_source (S26D 24, S28K 15), labelled apart. The lane
  frontier and its counters stay 8,687; receipts untouched. New certificate files of profile ksr-v5r-s25stage enter
  the headline only by adding a pinned component to that tool (with its gate), never by editing receipts or counters.
- S26C `?` fallback defect fixed (t1 8057ec26): re-measured 869 -> 100 compile -> 45 BINARY_EXACT experimental
  (evidence/ascension/s26c/fallback_fix/summary.json), 0 control bytes changed by the policy. These 45 are an admitted
  certification candidate set through the UNCHANGED certify.decide of the existing profile ksr-v5r-s25stage, with the
  S26D controls (pre/post, A2 negatives, historical receipts byte-identical), only after excluding ids already
  certified anywhere (they may overlap S26D's 23).
- Per-function arm rule for FLAGS_SPLIT objects: NOT adopted. Two measurements of the TU-boundary signal ended
  INSTRUMENT_FAIL (S29K A1, S32K T2), so choosing an arm per function would be fitting flags to bytes. The 3,447 stay
  uncertified. Reopen condition: a second independent TU-boundary signal whose positive control passes.
- The alternative-ctx certificate identity (ctx 9907081b, S23 E01: 6/6 units byte-identical, no certificate gained):
  not promoted; no new certificate identity. Reopen condition: a function set that certifies under that ctx and not
  under the canonical one.
