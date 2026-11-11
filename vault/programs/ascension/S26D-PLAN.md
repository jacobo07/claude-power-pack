# S26D plan: the parts of the Owner's G-NT1 brief that S26C did not cover -- PROPOSED, needs budget approval

Brief: Owner paste 2026-11-11T16:23:46.409Z (laptop session d957c937, uuid c2d588e7), stored verbatim in gen3
vault/programs/gsdx-factory-2/S26D-BRIEF-VERBATIM.md (sha256 7e48d796...). Same message: "haz que se arme automaticamente" (S27).

## Reality (measured 16:24-16:33Z)
- S26C (m-077596a9935d) CLOSED COMPLETED by this pane under that message. Its checkpoint already meets the brief's
  Workstreams A (21-id reconcile, C0), B (independent DOL-bytes target oracle, C1), C (frozen pilot 25/25) and D (expansion
  100/300/582): **582 formerly NO_TARGET KSR fns CANONICALLY_CERTIFIED under profile ksr-v5r-s25stage**, unchanged certify.decide.
- Independent re-run by this pane: test_s26c_{reconcile,target_oracle,profile,pilot,expand,fallback} 6/6 rc=0; 582 receipts,
  582 distinct ids, 0 overlap with the 8,687 historical; historical receipts sha 02c80ae3 / 8687 unchanged.
- Caveat: per-fn structural check ran on the 25 pilot fns; the other 557 rest on replay sha == sweep sha + size (checkpoint table).
- Record spent 30.45M of 31.5M: no authority left for more work on it. The brief itself forbids inventing a new allowance.
- S27 Tennis (m-10566700b1fe, 15M) RUNNING on gen3 since 16:32:40Z: one writer per goal, so S26D starts after S27's checkpoint
  (the brief ranks KSR before Tennis; Tennis was already approved and armed first by the Owner's instruction).
- Owner acts still open from S26C: merge the 582 into the 8,687 headline; R2; FLAGS_SPLIT policy; push.

## Scope (only what S26C left)
D1 Structural audit of the 557 non-pilot certificates with the S24 other-TU oracle (read-only; a contradiction is reported, never
   auto-revoked; revocation is an Owner act). Cap 2M.
D2 FLAGS_SPLIT TU-ownership hypothesis (brief F2): the 117 any-arm-only exacts all sit in ONE object, auto_03_801639EC. Test
   "the split object merges functions from different compilation units" against per-fn arm, symbol and section evidence; if
   supported, propose a re-split of that object as a new versioned stage generation (proposal only; certifying on it = Owner). Cap 3M.
D3 New-stage NO_COMPILE 1,147 (brief F1/E10): run S26 typelift (method_card_v2 routing, frozen sha) + the S26C `?` fallback outputs
   through the unchanged ksr-v5r-s25stage certify path; S26 P4 measured 7 exact candidates there. Cap 3M.
D4 New-stage COMPILES_NO_EXACT 991 (brief F3/E11): residual-class census on a frozen sample; route only classes an existing
   operator can express; certify through the profile. Cap 2M.
D5 Fresh-agent reuse of the additive-profile mechanism (brief gate R) + land S26C ukdl_candidates.md + checkpoint. Cap 1.5M.
Total <= 11.5M processed (incl. 1.5M closeout), 0 fresh, USD 0, 8 cycles, 16 h. NOT authorised: as S26C, plus no revocation.

## Owner decision
Approve S26D at 11.5M processed / 0 fresh / USD 0, armed right after S27 reaches CHECKPOINT_COMPLETE?
