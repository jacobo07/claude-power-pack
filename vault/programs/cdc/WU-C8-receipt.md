# C8 receipt
Status: DONE

Commits: worktree "cdc C8: cognitive PGO, proof_digest primitive" (feat/cdc); live landing sha in the line below.

- PROVEN: tools/cognitive_pgo.py ran over 2993/2993 transcripts of the last 14 d (all projects, 43.7 G processed tokens, complete, newest first, junction duplicates counted once). Outputs in vault/programs/cdc/evidence/: cognitive-pgo.json, cognitive-pgo.md, unproductive-corpus.jsonl (18,115 calls, 1.22 G tokens in NO_PROGRESS_RUN beyond C4 trip 25; plus REREAD/RECOVERY/CONTEXT_FAULT, each with a causal class).
- Ranking by ROIC (fix cost and avoidable share are declared ESTIMATES): Context, Coordination, Proof, Recovery, Token, Decision, Research. Owner and Constitutional are UNKNOWN (not 0): transcripts do not carry them.
- Top motif compiled: proof run -> output re-fetch (PowerShell:proof>proof 1774 occ/504 sessions, proof>other 1558 occ/565 sessions). tools/proof_digest.py: `run` awaits the process, kills the tree on timeout, logs the full output, prints a digest; CPP_PROOF_DIGEST=off, fails open.
- PROVEN: tools/test_cognitive_pgo.py 25/25 incl. 4 mutants that flip RED (unknown-as-zero, trip disabled, bigram-only, digest dropping failures).
- Replay on one historical trace (KobiiCraft 43d7834b, call 31, pytest): before 3 calls / ~1237 tokens est, after 1 call / ~93 tokens est (evidence/proof-digest-replay.json). Token figures are chars/4 estimates of context entry, not provider usage; "3 calls" counts the 2 follow-up fetch calls observed within 3 calls, which is a heuristic upper bound.
- NOT_PROVEN: that the primitive is adopted (no hook routes test runs through it; nothing forces its use); unattributed is 32.3 % of tokens; "avoidable" shares are estimates.
Next unit must know: PGO is re-runnable (`python tools/cognitive_pgo.py`, ~15 min full scan); adoption of proof_digest needs a PreToolUse nudge, not built here. Calls used: ~30.
