# APR resumption (coordinator) -- read this with zero prior context

Identity: programme APR (Autonomous Programme Recovery) in Claude Power Pack. Thesis: a recoverable, internal,
evidence-derivable unit-closure fault must never wait for the Owner. Origin: EWC K5 (`vault/programs/ewc/KNOWLEDGE.md`).
Brief: `vault/programs/apr/PROGRAMME.md`. Root cause and evidence: `vault/programs/apr/KNOWLEDGE.md` A1.

State (update after every sealed unit):
- SEALED: APR-1 (single receipt judge) -- wt_apr 6932f9b9, live 741479f3. Gates green (judge 5/5, halt 25/25,
  steward 25/25, chain 19/19, advance 12/12, mission 227/227, epoch 92/92).
- CHAIN: `vault/programs/apr/chain.json`, units APR2..APR6, goal `apr` cap 20,000,000, root `C:\Users\User\Apps\wt_apr`
  (branch apr/self-closing), task PP-AprChain-Tick (10 min). Progress: `~/.claude/state/gsdx-chain.jsonl` rows with
  goal apr; `~/.claude/state/apr-chain-tick.log`.
- EWC runs in parallel (goal ewc, wt_ewc); APR-4 changes its chain.json (max_residuals 2 + acceptance).
- Coherence anchor: `git -C C:\Users\User\Apps\wt_apr log --oneline 7501d939..HEAD` lists every APR code commit.

Decisions in force: extend, never a new engine; receipt_judge is the only receipt reader; the worker's receipt is
never rewritten (seal files carry the machine verdict); installs only by cherry-pick of clean files (APR-4).

Next actions:
1. If the chain is idle on `stopped_without_done` / `human_gate` / `residual_exhausted`: read the unit's receipt and
   seal/refusal files, decide whether it is internal (fix and re-tick) or a genuine Owner gate (ask).
2. After APR-6: read `vault/programs/apr/REPORT.md` and `PRODUCTION-REALITY.md`; report to the Owner.
3. Never re-run APR-1; never edit wt_ewc.

Start: `python tools/gsdx_chain.py tick --chain vault/programs/apr/chain.json --dry-run` from the live checkout.
