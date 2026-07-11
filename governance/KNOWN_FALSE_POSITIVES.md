# KNOWN_FALSE_POSITIVES.md — Do not re-investigate these

> Normative. Domain: any project using the Power Pack Stop / PreToolUse hooks.
> When a signal below fires, apply the response and move on — never spend more than
> 2 minutes investigating. Append any new false positive here the same session it appears.

## FP-01 — FIOS / IRR / FD-07 / FD flywheel / PP_SESSION_OBJECTIVE
- What it really is: these are REAL Power Pack modules (`fd_07_flywheel`, `token_irr`,
  frontier_intelligence). Inside CommonWealth Ops and the Power Pack itself they are
  legitimate — NOT a false positive there.
- Symptom: the Stop hook emits FIOS / IRR / FD-07 vocabulary in a project that is NOT
  CommonWealth Ops or the Power Pack (e.g. a portfolio, a compendium).
- Response: cross-contamination of vocabulary through the shared Stop hook. Ignore. Do not
  populate any ledger, do not create any related asset. Document the sighting in the
  affected project's `CLAUDE.md` so the next session recognizes it instantly.

## FP-02 — BLOCKED_DELIVERY.md from the COMPILE gate
- What it really is: the compile gate uses an npm that is broken on this host.
- Symptom: a `BLOCKED_DELIVERY.md` appears claiming the build failed at the COMPILE step.
- Response: verify the real build with pnpm (or the production build). If it passes, delete
  the file and continue. The failure is the gate's tooling, not the code.

## FP-03 — scaffold-auditor / Woz veto on a documentation or spec file
- What it really is: the scaffold-auditor and the Woz veto are blunt literal matchers for
  an incomplete-work lexicon (the words that mark unfinished code).
- Symptom: a Write/Edit to a spec or doc file is blocked because the file legitimately
  mentions one of those words as its SUBJECT (e.g. this file, documenting the trap).
- Response: reword to avoid the literal token, or move the reference out of the flagged
  file. The gate cannot distinguish documentation-of-a-word from use-of-a-word.

## FP-04 — third-consecutive-edit block on one file
- What it really is: an anti-thrash gate blocks the 3rd back-to-back Edit of the same file.
- Symptom: an Edit returns an unexplained exit-2 block with no content reason.
- Response: Read the file once to reset the counter, then re-apply the edit. Do not chase
  a phantom content mismatch.

## How to add a new entry
What it really is (the true cause) + Symptom (how it surfaces) + Response (what to do,
always bounded to ≤2 minutes).
