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
Existing profiles and certify.decide untouched; historical receipts and the canonical ctx untouched (headers: OR-3); additive profiles only under all
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
- Both lanes start with instruments, not certificates: compiler identification and the byte oracle or split (levers fifa_compiler_matrix, fifa_rso_target_oracle, wp_dtk_split, wp_compiler_matrix). Certification goes through the standing rulings OR-1 and OR-5 below; objdiff progress counts as MATCH. A count that is neither stays a measurement in its own file, never a headline.
- Game bytes, decompiled source and assets stay on GEX44 and the laptop. orig/ is read-only and pinned by sha256 in lanes.json. /home/kobii/wsr-decomp is read-only. These lanes never touch the KSR or Tennis repositories, receipts or gates.
- Envelopes: 20M tokens each (starter); the shared day cap applies, and these lanes tick after KSR and TENNIS.

## New lane MKW (Owner 2026-11-14 route "a" + "y", pane 4de9b293)
- MKW: Mario Kart Wii PAL (RMCP01), product /home/kobii/missions/mkw-decomp, branch lane/mkw. Its base is the public CC0-1.0 decomp github.com/snailspeed3/mkw at commit 78572c9. Target: byte-exact reconstruction of main.dol and StaticR.rel. At base, upstream matches 1,837 of 26,639 functions. This lane counts only the functions it moves from unmatched to matched, against a target list frozen in a commit before the work.
- The oracle is the decomp's own build: ninja must keep ending with build/RMCP01/main.dol: OK and build/RMCP01/StaticR/StaticR.rel: OK (config/RMCP01/build.sha1), and build/RMCP01/report.json from objdiff decides each function.
- The lane started with measurements (levers mkw_dol_game_match, mkw_rel_match). Functions it moves to 100% in report.json count as MATCH (verified by the autopilot); certification goes through OR-1 below.
- The repository stays local to GEX44. Game bytes, build outputs and assets stay on GEX44 and the laptop. orig/ is read-only and pinned by sha256 in lanes.json. This lane never touches the KSR, Tennis, FIFA or Wii Party repositories, receipts or gates.
- Envelope: 20M tokens (starter). The shared day cap applies, and this lane ticks after the others.

## Known-boundary sources: standing Owner authorization (Owner 2026-11-14 "authorize a 3rd independent boundary source and thus infinitely", pane f3df357a)
- The Owner authorizes a third independent known-boundary source for the TU-boundary positive control, and every further one after it. S45K stopped at n_known 31 with 3 of 4 families (runtime absent). Whenever the admitted sources do not reach adequacy, the next generation admits another independent source, until the reconstruction is complete. A missing source is never a reason to stop the lane or to ask the Owner again.
- On disk, cloned at pinned commits, read-only, public decomps without game bytes (orig/ empty): /home/kobii/donors/ss 96f2dd54 (Skyward Sword SOUE01), /home/kobii/donors/xenoblade ea25691b, /home/kobii/donors/spm 07e430b7 (Super Paper Mario), /home/kobii/donors/tp c8fa8c9e (Twilight Princess, Wii versions RZDE01 RZDP01 RZDJ01). Each declares Runtime.PPCEABI.H, MSL, RVL SDK and NW4R libraries in its configure.py.
- When these are exhausted, a generation may clone another public decomp into /home/kobii/donors/<name> at a pinned commit, recording its URL, commit and licence in the criteria before any count.
- Admission works as ogws did in S45K. Only library TUs whose configure.py status is Matching count. Each is compiled from the donor's source with the compiler and flags its configure.py declares, and the output goes to scratch outside every repo. A TU that does not compile is FAILED or ABSENT and contributes nothing. Each source is pinned and asserted clean before and after. A source whose DOL sha1 equals the KSR main.dol sha1 is excluded as non-independent.
- These stay unchanged and are not arbitrable: n_min 30, at least 4 distinct families of rvl nw4r MSL runtime, recall bar 0.80, and the agreement rule (a pair is KNOWN only if every admitted source that matched both fns agrees). mask_fn and match come from tools/s44k_known.py, read-only. Sources are pre-registered in criteria committed before any count of the new generation, and the matching rule is never loosened after seeing n.
- Donor code stays on GEX44. Nothing from it enters the public PP repo, a receipts file or the canonical context.

## Third known-boundary source authorised (2026-11-14T15:39:05Z)

Owner 2026-11-14 'y' (session 423c9c50, S45K pending question): a THIRD independent known-boundary source is AUTHORISED for the KSR TU-boundary calibration set: one more public matching decomp (not wsr, not Tennis auto split, not FIFA, not Wii Party: those stay excluded), pinned to a commit before any count, covering runtime/MSL neighbours, joined to mkw+ogws under the UNCHANGED S45K agreement rule (masked-byte match, same compiler/flags its configure.py declares, 0 disagreements kept), and the UNCHANGED adequacy rule (n_known >= 30 AND >= 4 families). Adequacy is judged at freeze, before any segmentation is read. If no donor reaches the runtime family, report INSTRUMENT_FAIL again; never loosen the matching rule after seeing n. No signal under test (floatdup, sbss, statics_strpool) may be used as a known-boundary source.

## FMADD -fp_contract profile authorised (2026-11-14T19:53:24Z)

Owner 2026-11-14 'y' (session 423c9c50, S49K OWNER QUESTION CERTIFICATION_RULE): AUTHORISED a NEW ADDITIVE profile ksr-v5r-s25stage-s49fm that runs the lane with -fp_contract on for the FMADD class only, under ALL S26C conditions. Control redefined: negative pole = the 40+ certified non-float exact functions must stay byte-identical (any move = profile rejected); positive = every dev exact re-verified by the independent oracle on ORIGINAL DOL bytes (not by certified fma fixtures, which cannot exist). Existing profiles and certificates untouched. Criteria and the dev/held-out split stay as frozen in S49K; held-out 50 is opened once, only after the profile and controls are frozen and committed. No re-cut of the held-out after seeing results; INSTRUMENT_FAIL stays a valid outcome.


## Owner levers 2026-11-16 (pane 08cba76c, Owner 'y')
- FIFA: fifa_anchorfree_entry (STRUCTURAL_ENTRY). the S84F residual route (evidence/f9/pivot_residual_f9.md). 377 of 391 F5-only tails have no internal-relocation referent, so every anchor-dependent entry route is blind to them. Decide entry-ness of those tails by ANCHOR-FREE structural evidence: prologue/epilogue shape plus inbound-reference classification from the reader cohort only. Reuse tools/rso_target.py (24,408-function oracle, gate 15/15
- MKWLIB: mkwl_band_17_64 (SOURCE_BAND). option (a) of evidence/ascension/s87l/pivot_residual.md (S87L2). SCOPE lib/nw4r and the RVL SDK only. First, in its own commit before any freeze: gate v2, which repairs what the judge DISAGREEd on for S87L (tools/test_mkwl_match.py rc=1, 3 silent functions, mutants not isolated, selftest red); the v2 selftest must be green and each mutant red in isolation. Then the S77M/S87L hand-written-source me
- TENNIS: tennis_handsource_cohort (SOURCE_BAND). transfer the MKWLIB hand-written-source smallest-cohort route (S77M, then S87L: 24/24 held-out at 100 on the 48 smallest lib functions) to Tennis. The CNM operator population (158 fns) is consumed and tennis_callee_type_model is refuted (S81T: 0 of 60 held-out exact). Cohort: the smallest non-certified Tennis functions, disjoint from the S69T 144 and S81T 60 cohorts, frozen by size then address, 5
- WIIPARTY: wp_laypair_shield (LAYOUT_PAIR). the reopen condition of S82W (evidence/ascension/s82w/checkpoint_s82w.md). S82W could not test H-LAYPAIR because every pre-registered second build (RZDP01, RZDJ01, RZDE01_02) is labelled GC/3.0a3p1, so there is no W label. Re-register the paired build set as tp GZ2E01 versus Shield, the release build that declares Wii/1.0 (166 switch pairs, counts only). Do not use ShieldD: it is a debug build and
- TENNIS bootstrap moved from t1-campaign/s27 to tennis-all-match/s81t (the lane re-plans from its own product).
- WIIPARTY: wp_lib_donor (DONOR_TRANSFER), Owner 'rec' 2026-11-16 (pane 08cba76c): SDK/NW4R library functions located by masked bytes against the ogws and mkw-lib donors.

## Standing Owner rulings OR-1..OR-6 (Owner 2026-11-18 "y", pane 08cba76c)
Source: 77 "Owner question / NOT authorised / Owner-gated" lines in about 50 checkpoints since 2026-11-14, none of which
reached the Owner. These rulings answer them once. Budget, capital and authority stay the Owner's.
- OR-1 (certification rule): a function whose compiled object matches the original bytes exactly (BINARY_EXACT from the
  unchanged certify.decide, or objdiff 100% confirmed by an independent oracle on the original DOL or REL bytes) may be
  certified in the generation that found it. Its receipts go in that generation's own receipts file, registered in
  receipt_registry.json; historical receipts and counters stay byte-identical. Compiler-local pool symbols (@N, sda21)
  count as equal to the target's named symbol when the bytes and the relocation type are equal.
- OR-2 (held-out contract): a generation draws a fresh held-out set without asking when the set is disjoint from every
  earlier cohort and control, seeded and frozen in a commit before any compile, size-stratified to match the population
  under test, and at least the lane's floor. A burned held-out set is never reused. A floor or threshold change still
  goes to the Owner.
- OR-3 (product scope): canonical headers, splits.txt and symbols.txt may change when, after the generation's last
  commit, the full build passes, no function leaves 100% in the objdiff report (the autopilot's MATCH check), and every
  certified function still verifies. A header change toward a donor's layout cites the donor. The canonical ctx of the
  KSR and Tennis profiles stays as it is: it is the certificate identity.
- OR-4 (successor generations): a residual's next route is the planner's input, never an Owner question. Only capital,
  a truth-contract change or an irreversible act goes to the Owner.
- OR-5 (additive profiles): a lane may add a new additive certification profile when its profile line states all six
  S26C conditions, its first certificate is checked by an independent oracle on the original bytes, and no existing
  profile changes.
- OR-6 (housekeeping): re-pinning a frozen tool after an Owner-authorised amendment, and fast-forwarding a lane's main
  to its own generation branch (no push), need no question.
- A checkpoint line "OWNER DECISION NEEDED" or "OWNER QUESTION" that these rulings do not answer is copied by the
  autopilot to the Owner queue; write it only for capital, a truth-contract change or an irreversible act.
- Progress classes: MATCH (functions newly at 100% in the objdiff report built by the autopilot, none lost) is a
  conversion like CERT. After a CERT or a MATCH the lane exploits the same lever at scale.

## Factory lane: standing Owner authorization (Owner 2026-11-20, pane 5a77ca0e)
- The factory lane (`/home/kobii/agora/factory/lane.py`, cron, 0 tokens) applies deterministic factory matches to a lane without an Owner turn, only under its gates: every binary OK, 0 functions lost against the lane's base report and its MATCH snapshot, at least 1 gained, lane HEAD unchanged and tracked-clean, autopilot status not RUNNING, the whole application under cron.lock.
- Its snapshot advance is not a generation's MATCH: no generation is credited for a factory application (ledger kind `factory_match`, tokens 0).
- Still the Owner's: anything that spends tokens, a ruling, a gate or certification-rule change, a lane config change, a dtk version change.
- Spec: PP `vault/specs/ascension-reconstruction-factory.md` F5. Kill switch: `~/.claude/state/factory-lane.ready`.

## Owner rulings 2026-11-21 (pane b9040a8e, Owner "on all rec": the recommended option of each open question)
- FIFA (pivot_residual_s234f_auto.md) and FIFATC (checkpoint_s212c_pivot1.md): option (a), AUTHORISED. A generation may
  add an additive FIFA / FIFATC certify profile under OR-5 (all six S26C conditions on its profile line, frozen pilot
  committed before the draw, pre/post controls, A2 negatives, separate counters, historical receipts byte-identical, no
  existing profile changes, first certificate checked by an independent oracle on the original bytes). The profile file,
  its own receipts file, its counters file and its receipt_registry.json entries are inside that generation's write
  scope. For the autopilot to count verdict-less rows, the receipts, the counters (decide.CERTIFIED == certified_total ==
  rows added) and both registry entries (sha256 of the committed bytes) must land in ONE commit; a registry entry added
  in a later commit does not count (S157W-S159W lost 57 certificates that way).
- TENNIS (pivot_residual_n2.md): AUTHORISED, a fresh-model-token source-generation generation (S209T reopen) on a new
  held-out set drawn under OR-2. Capital is the existing research_cap and the 2026-11-19 auto-extend grant; the 10M
  research generation cap is unchanged. Not a new budget.
- WIIPARTY (residual_pivot1.md): YES, extend wp_game_handsource_smallest to sizes 20 and 24: new frozen targets file,
  new generation, same truth contract and profile. The 2-revision cap is unchanged.
- MKWLIB (judge DISAGREE 2026-11-21T14:48Z on s207l/pivot_residual.md): re-judged under design-before-park instead of
  staying parked. A successor must not edit the S192L-sealed files lib/rvl/ax/rvlAxAlloc.c and rvlAxVpb.c: revert
  d249f5b's edits to them, or put new work in new files.
- Retro-credit (S216W + S147W-S159W wp-dol-link-v1): measured with autopilot.verify_cert, read-only. S216W verifies (40,
  receipts d275e45) and is ledgered as kind `retro_cert`. The 144 rows of S147W/S156W (counters without decide.CERTIFIED)
  and S157W/S158W/S159W (registry in a later commit than the receipts) do not verify under the current rule and stay
  uncredited; crediting them would be a certification-rule change (Owner).
