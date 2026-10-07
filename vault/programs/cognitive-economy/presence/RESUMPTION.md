# RESUME: ce-presence (CE Presence Contract)

Identity: worktree C:\Users\User\Apps\pp-ce-presence, branch ce/presence (base 9658c5f2). Goal `ce-presence`, cap 6.0M
(declared 2026-10-07 21:17Z, root = this worktree). Card: vault/plans/ce-presence-contract-2026-10-07.md (approved,
Owner "y", pane 77cfae43). Thesis: an absent mission field must resolve to the certified cheap baseline at launch,
never to the host maximum (--bg, Opus 1M, 600k autocompact, generic briefing).

State (sealed / pending):
- SEALED: plan approved; goal declared; U6a armed m-dda8e4a0c960, ADMISSIBLE (need 702,252 / target 1.6M), launched
  slim-t2 sonnet, worker 6929ab8d, pid 35480, 2026-10-07 ~21:20Z.
- Planner pane 77cfae43 spent ~4.5M (MEASURED 4,084,237 at 21:17Z + ~6 calls x ~215k). Settle against ce-presence.
- PENDING: U6a receipt at vault/programs/cognitive-economy/presence/U6a-receipt.md. Coherence anchor: that file
  exists AND `git log ce/presence` shows the worker's commits.

Decisions: cap raise of ce-a3 is Owner-TTY-only (mission_spend goal-declare --owner), so the +6M lives in goal
`ce-presence` instead. CAA plan (3fe39764) runs AFTER U6. Deferred rows (GEX44, cross-account, scheduled entry points,
within-epoch compaction) stay DEFERRED. CPP_CE_BASELINE defaults to shadow until the U6c negative canary passes.

Next 3 actions (fresh pane, cwd = this worktree, bind first: `mission_spend.py session-declare` stop 0.8M):
1. Read ONLY U6a-receipt.md + `gsd_mission.py status`. If tests green and mutants red: merge ce/presence into the live
   branch of C:\Users\User\.claude\skills\claude-power-pack (fetch-first, check concurrent writers; the live
   supervisor runs from there). If BLOCKED: one repair packet, never a third same-shape attempt.
2. Arm U6b WITHOUT --model/--autocompact/route (the self-hosting negative canary). Verify from the worker's raw
   transcript that model=sonnet and the autocompact is the policy value, and that `baseline_resolved` is in the ledger.
3. Write U6c/U6d packets from card section 5; arm each the same way; then hand off to CAA T0.

Start: open a fresh pane in this worktree and run step 1. Do not reread the planner transcript.
