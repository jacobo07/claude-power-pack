# Owner standing rulings: DRAFT for approval (2026-11-18, pane 08cba76c)

Source: 77 "Owner question / NOT authorised / Owner-gated" lines in about 50 checkpoints and residuals since
2026-11-14 (KSR+TENNIS 17, FIFA 8, FIFATC 5, WIIPARTY 8, MKW 4, MKWLIB 8, WSR several). None of them reached
owner_queue.md as a question; generations routed around them.

Approval installs the approved text in `brief.md` under "Standing Owner rulings", which the planner, the judge and
the workers read. It also removes the contradicting lines (113, 120). Approve or reject each one separately (R1..R6).
Budget, capital and authority stay the Owner's. None of these rulings touches money.

## R1 CERTIFICATION_RULE: certify an exact binary match
Asked by: S66K, S115T, S135T/S107T, MKWLIB S100L/S127L.
> A function whose compiled object matches the original bytes exactly (BINARY_EXACT from the unchanged certify.decide,
> or objdiff 100% confirmed by the independent byte oracle on the original DOL/REL) may be certified in the
> generation that found it. Its receipts go in that generation's own receipts file, registered in
> receipt_registry.json. Historical receipts and counters are never edited. Compiler-local pool symbols (@N, sda21)
> normalised against the target's named symbol count as equal when the bytes and the relocation type are equal.

Effect: unblocks the 5 TENNIS fns at 99.87%, the 87 magic-literal fns and S66K's exact match. Risk: low; the byte
oracle is the truth.

## R2 HELD_OUT_CONTRACT: fresh draws without asking
Asked by: S102T, S122T, S131T, S69T, F16/F17, S70W/S75W, S136M, S99M, S87L, S103R/S105R.
> A generation may draw a fresh held-out set without an Owner ruling when: it is disjoint from every earlier cohort
> and control; it is seeded and frozen in a commit before any compile; it is size-stratified to match the population
> under test; and its size is >= the lane's floor. A burned held-out set is never reused. Changing a floor or
> threshold still needs the Owner.

Effect: the most frequent gate. Removes the "positive-control pool too small" class (S62K 8 of 644, S131 9 of 10959)
when combined with size-matched controls.

## R3 PRODUCT_SCOPE: canonical headers, splits and symbols, gated by the build
Asked by: MKW S60M, MKWLIB S127L, WSR S110R/S113R, FIFATC F16.
> A generation may edit canonical headers, ctx, splits.txt and symbols.txt only when, after its last commit: the full
> build passes; the objdiff report loses no function from 100% (the autopilot's MATCH check); and every certified
> function still verifies. Header changes toward a donor's layout cite the donor.

Effect: unblocks the type/ABI route (nw4r/egg headers, CharWidths) and the 7 WSR TUs that fail only on
canonical-header warnings or split externals. Risk: medium. It is bounded by "no function lost from 100%".

## R4 Successor generations need no question
Asked by: S102T, S122T, S69T, S98W, S99M, S103R, S87L, F16 ("authorise a new generation ...").
> A residual's "next route" is the planner's input, not an Owner question. Only capital, a truth-contract change
> (R1/R5) or an irreversible act asks the Owner.

Effect: already the standing doctrine (2026-11-14 / 11-16). This states it in the brief so the workers stop writing
it as a question.

## R5 New additive certification profiles (S26C)
Asked by: FIFA F17/F21-F23 (entry-address profile), WIIPARTY S64W (SUPP01 library-function profile).
> A lane may add a NEW additive profile when the profile line states all six S26C conditions, its first certificate
> is checked by an independent byte oracle, and it never edits an existing profile.

Effect: gives FIFA and WIIPARTY a certification route at all. Without it they cannot convert. Risk: medium; it is a
truth-contract extension. The S26C conditions are the guard.

## R6 Housekeeping without asking
Asked by: MKWLIB S138L (re-pin the frozen tool blob after an authorised amendment), WIIPARTY S142W (fast-forward
main to the worktree branch, no push).
> Re-pinning a frozen tool after an Owner-authorised amendment, and fast-forwarding a lane's main to its own
> generation branch (no push), need no question.

## Also proposed (code, not a ruling)
The judge or closeout detects "OWNER DECISION NEEDED / Owner question" in a checkpoint and copies it to
owner_queue.md as a QUESTION line, so a gate the rulings do not cover reaches the Owner instead of being routed around.
