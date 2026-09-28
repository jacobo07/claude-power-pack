# External Capability Assimilation — resumption contract

**Read this first; it is self-contained.** Spec: `vault/specs/external-capability-assimilation.md`.
Worktree `C:\Users\User\Apps\pp-assim`, branch `feat/external-assimilation` (off
`feature/knowledge-acquisition@2b6f183`, pushed to origin). Source: `Downloads\for cpp-gsd-long.zip`.

## Thesis
Every capability (Genesis 21 modules + runner, Context Budget, loop kit, self-continuation) gets ONE
CPP owner/disposition in `vault/assimilation/genesis-2026-09/ASSIMILATION_MANIFEST.json`. Hot path
native Python; cold path vendored MIT Node via `modules/external_assimilation/node_bridge.py`.

## Owner decisions (2026-09-28)
Worktree, full scope, hybrid runtime, autonomy gate LIVE, night research VPS-only (VPS Node v22.22.2
< ^22.23.2: install user-level Node 24 first), experiments hybrid, push everything.

## Sealed
T1 `f9a8391` `6ab1b06` vendor+provenance+bridge+manifest · T2a `0efa0ba` Context Budget as epoch
evidence + Fresh Context Tax (median 185,930 tokens fixed bootstrap; 389/445 sessions were quota
refusals) · T3a `6fedb1d` provider circuit breaker · T3b (this commit) autonomy gate extending DRK +
rubric/wake-order in the Ralph Stop hook + decision receipts.
Gates: test_genesis_bridge 9/9 · test_assimilation_manifest 9/9 · test_vendor_provenance 5/5 ·
test_context_budget 8/8 · test_gsd_epoch_context_budget 6/6 · test_fresh_context_tax 3/3 ·
test_provider_breaker 15/15 · test_gsd_mission 191/191 · test_gsd_epoch pass · test_autonomy_gate
22/22 · node tools/test_gsd_stop_continuation.js 17/17.

## LIVE since 2026-09-28 (`2f8cc5b`)
`90ba1d5` successor card carries rubric + wake order; 4 self-continuation entries LIVE (manifest
9/9 runs 14 LIVE proofs). `2f8cc5b` merged `feature/knowledge-acquisition` INTO this branch, then
the live checkout fast-forwarded to it: 14 suites green on the merged tree, hook + gate suites
green again on the live copy (the dispatcher runs `hooks/gsd_stop_continuation.js` from the repo
path, no mirror). Both branches pushed at `2f8cc5b`.
Go-live pattern for later tranches: commit here, merge the live branch in, rerun gates, then
`merge --ff-only` in the main checkout after checking HEAD unmoved and no dirty-path overlap.

## T4-T7 LIVE since 2026-09-28 (`6fdd61a`, fast-forwarded; both branches pushed)
Item 18 plan graph (card `_plan_facts`) · 20 batch drafts · 21 task contracts · 23 evidence
bundle (REAL end-to-end OK: real gates + nonce-ticketed pp-code-reviewer review; 3 real reviews,
two found real false greens, both fixed) · 24 review intake (+ modules/code_review
unrecognised-severity APPROVE fixed) · 25 regression memory · 26 constraint compiler (pinned on
the batch path; UKDL crosswalk NOT claimed) · 27 change impact (graph from AST imports, NOT
audit_cache: its depends_on is stem-resolved and would have said "no suite affected").
Tool only / not LIVE: 12 source packet (card 8000-byte cap vs 24000-byte packet -> T8 decides).
SEAM: 22 task ledger (Goal Spine owns the only live caller; decision 1a).
Also fixed on the way: rollover `resume` claimed uncertifiable capsules + test leak (d10bd31);
test_mission_watchdog control inverted for active rollover (was red on live since 42da3d1).
Owner-side, not done (HR-001): add REPLY_INSTRUCTION to ~/.claude/agents/pp-code-reviewer.md.
Known limits recorded in code: review ticket A->B->A window; test_cpp_gsd_long_routing reads
red in a CRLF worktree only (content identical; 9/9 on the live checkout).

## Next 3 actions
1. T8: routing metrics (epoch/worker receipts), verified reuse, the paired experiment
   (current card vs bounded-packet card: decides item 12's consumer).
2. T9-T10: task adaptation, charter lab; night research on the VPS (user Node 24 first).
3. T11-T12: live smoke mission, red team, Knowledge Vault / UKDL capture.

## Start instruction
`git -C C:\Users\User\Apps\pp-assim log --oneline -8`, run the gates, then action 1.
