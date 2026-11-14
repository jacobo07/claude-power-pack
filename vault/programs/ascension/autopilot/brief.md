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

## Mutant wording (Owner 2026-11-12, pane c26eafbf)
Describe each planted mutant by the check that must catch it, e.g. "M2: a receipts path outside evidence/ascension/s35k/qf
is refused", never as an act on receipts, the certifier or canonical files. The policy reads such a phrase as the act
itself and refuses the whole generation (S35K was refused for "M2 receipts written to a historical receipts path").

## One coordinator for KSR (Owner 2026-11-12, pane c26eafbf)
Only this autopilot arms KSR generations. A generation adds its own profile or receipts file and never edits what an
earlier generation froze or pinned (tools/ksr_lane.py pins, freeze.json, receipts). Every new receipts file gets a new
entry in evidence/ascension/receipt_registry.json (path, sha256, gen, commit); tools/test_s30k_cert.py admits it only so.

## CNM operator coverage route (Owner 2026-11-13 "y, presupuesto 300M", pane c84eb8e1)
Admitted next KSR lever: cnm_operator_coverage (levers.json): operator coverage for the 3,653 NO_OPERATOR_FOR_CLASS ids
of the S36K sweep (t1 evidence/ascension/s36k/pivot2/residual.md). New route code in a new generation; existing route
tools stay frozen. Pilot first, with a gate with planted mutants; certification only through the unchanged certify.decide.
Its certificates land in an additive profile proposed in ONE phase line that states: an independent target oracle on the original DOL bytes; a frozen pilot committed before the draw; pre/post controls; A2 negatives; historical receipts byte-identical; separate counters.
Its receipts file gets a receipt_registry.json entry. (S37K was refused 2026-11-13 for an earlier wording of
this paragraph: describe a profile only in a line that carries all six conditions.) Budget: Owner
envelope of 300M tokens for this route on the KSR lane from 2026-11-13; each generation <= 25M; the 90M day cap still
applies. Name the lever id cnm_operator_coverage in Phase 1.

## Tennis route transfer (Owner 2026-11-13 "y", pane c84eb8e1)
Supersedes "Nothing else is planned for Tennis" above. The TENNIS lane may run the KSR routes that certified,
transferred unchanged: q_fallback_cert (S26C fallback, 31 KSR certificates) and cnm_operator_coverage (s37-callee
operator, 57 KSR certificates); see levers.json TENNIS. Route tools are imported read-only from
/home/kobii/missions/t1-campaign at a pinned commit and are never edited. Certification only through the unchanged
certify.decide under an existing Tennis profile; any profile line follows the S26C rule (all six conditions in that one
line). Budget: a 50M Tennis lane envelope from 2026-11-13 (lanes.json), research generations of at most 10M each. Name
the lever id in Phase 1.

## Missing capabilities as levers (Owner 2026-11-14 "crea las capacidades directamente y pegalas a las misiones", pane 423c9c50)
New research levers in levers.json, each a pre-registered pilot judged BINARY_EXACT through the unchanged certify path:
KSR `cnm_variant_search` (S41K 'other' residual, source-variant search), `tu_boundary_floatdup` (second TU-boundary
signal, the registered reopen condition of FLAGS_SPLIT and H-S41PX), `whole_program_type_model` (program-wide fixpoint;
Tennis P1-P1e evidence against it is stated in the lever); TENNIS `cnm_variant_search` (164 CNM). Both lanes resume once
with owner_resume=research:cnm_variant_search; the other two KSR levers are selectable afterwards.

## New lanes FIFA and WIIPARTY (Owner 2026-11-14 "go ahead with both new lanes", pane 4246d04c)
- FIFA: FIFA 11 Wii PAL (SELX69), product /home/kobii/missions/fifa11-decomp. Target: byte-exact reconstruction of the 24,482 named functions of fifaf.code.rso (6.46 MB .text) and of main.dol. The source image is CONTAMINATED-BUT-VALUABLE (three injected data files; the code files are untouched), so every match reads "matches this image" until the Owner's re-dump hashes equal (U-001).
- WIIPARTY: Wii Party PAL (SUPP01), product /home/kobii/missions/wiiparty-decomp. Target: byte-exact reconstruction of main.dol (1.93 MB .text, no symbols).
- Both lanes start with instruments, not certificates: compiler identification and the byte oracle or split (levers fifa_compiler_matrix, fifa_rso_target_oracle, wp_dtk_split, wp_compiler_matrix). Certification needs a later Owner-approved certify route per lane; until then every count is a measurement in its own file, never a headline.
- Game bytes, decompiled source and assets stay on GEX44 and the laptop. orig/ is read-only and pinned by sha256 in lanes.json. /home/kobii/wsr-decomp is read-only. These lanes never touch the KSR or Tennis repositories, receipts or gates.
- Envelopes: 20M tokens each (starter); the shared day cap applies, and these lanes tick after KSR and TENNIS.

## New lane MKW (Owner 2026-11-14 route "a" + "y", pane 4de9b293)
- MKW: Mario Kart Wii PAL (RMCP01), product /home/kobii/missions/mkw-decomp, branch lane/mkw. Its base is the public CC0-1.0 decomp github.com/snailspeed3/mkw at commit 78572c9. Target: byte-exact reconstruction of main.dol and StaticR.rel. At base, upstream matches 1,837 of 26,639 functions. This lane counts only the functions it moves from unmatched to matched, against a target list frozen in a commit before the work.
- The oracle is the decomp's own build: ninja must keep ending with build/RMCP01/main.dol: OK and build/RMCP01/StaticR/StaticR.rel: OK (config/RMCP01/build.sha1), and build/RMCP01/report.json from objdiff decides each function.
- The lane starts with measurements (levers mkw_dol_game_match, mkw_rel_match). Certification needs a later Owner-approved certify route for this lane; until then every count is a measurement in its own file, never a headline.
- The repository stays local to GEX44. Game bytes, build outputs and assets stay on GEX44 and the laptop. orig/ is read-only and pinned by sha256 in lanes.json. This lane never touches the KSR, Tennis, FIFA or Wii Party repositories, receipts or gates.
- Envelope: 20M tokens (starter). The shared day cap applies, and this lane ticks after the others.

## Known-boundary sources: standing Owner authorization (Owner 2026-11-14 "authorize a 3rd independent boundary source and thus infinitely", pane f3df357a)
- The Owner authorizes a third independent known-boundary source for the TU-boundary positive control, and every further one after it. S45K stopped at n_known 31 with 3 of 4 families (runtime absent). Whenever the admitted sources do not reach adequacy, the next generation admits another independent source, until the reconstruction is complete. A missing source is never a reason to stop the lane or to ask the Owner again.
- On disk, cloned at pinned commits, read-only, public decomps without game bytes (orig/ empty): /home/kobii/donors/ss 96f2dd54 (Skyward Sword SOUE01), /home/kobii/donors/xenoblade ea25691b, /home/kobii/donors/spm 07e430b7 (Super Paper Mario), /home/kobii/donors/tp c8fa8c9e (Twilight Princess, Wii versions RZDE01 RZDP01 RZDJ01). Each declares Runtime.PPCEABI.H, MSL, RVL SDK and NW4R libraries in its configure.py.
- When these are exhausted, a generation may clone another public decomp into /home/kobii/donors/<name> at a pinned commit, recording its URL, commit and licence in the criteria before any count.
- Admission works as ogws did in S45K. Only library TUs whose configure.py status is Matching count. Each is compiled from the donor's source with the compiler and flags its configure.py declares, and the output goes to scratch outside every repo. A TU that does not compile is FAILED or ABSENT and contributes nothing. Each source is pinned and asserted clean before and after. A source whose DOL sha1 equals the KSR main.dol sha1 is excluded as non-independent.
- These stay unchanged and are not arbitrable: n_min 30, at least 4 distinct families of rvl nw4r MSL runtime, recall bar 0.80, and the agreement rule (a pair is KNOWN only if every admitted source that matched both fns agrees). mask_fn and match come from tools/s44k_known.py, read-only. Sources are pre-registered in criteria committed before any count of the new generation, and the matching rule is never loosened after seeing n.
- Donor code stays on GEX44. Nothing from it enters the public PP repo, a receipts file or the canonical context.
