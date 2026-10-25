# Unit W4 — Tranche A benchmark: slim-t2 units vs the W1 baseline

Repo: C:\Users\User\.claude\skills\claude-power-pack (a git worktree on its own branch; the path is rewritten below).
Use PowerShell; git is `& 'C:\Program Files\Git\cmd\git.exe'` (not on PATH). Python is
`C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`. Measurement only: read transcripts, never edit them.

## Inputs
- New arm, four slim-t2 worker sessions (transcripts at `C:\Users\User\.claude\projects\*\<sid>.jsonl`; find the
  directory by glob, do not assume it):
  W3a c6c0e19d-c447-4de8-be77-4b4dd1abd63b · W3b dab6a4f1-5520-4887-b07c-604aeee8ebde ·
  W3c c3c64013-d65a-415d-b32d-e068f3c715a3 · W3d (cap-trip probe) 943a6303-6d4a-4794-ad85-6965b2412dd2 (its receipt claims the breaker tripped at
  processed 61,515; verify that from the transcript, do not copy it).
- Pricing: `vault/pricing/anthropic_2026-10.json` (refetched 2026-10-25). Price each assistant call by the model id
  in its transcript row; a model with no row is UNPRICED and reported as such, never priced as 0.
- Old arm (W1 baseline, measured 2026-10-25, Opus 5.5 rates, 1h cache write), per session type:
  gsd-executor n=21, 536 calls, call-1 floor median 84.0k, 69.2M processed, $57.1;
  worker (main) n=8, 274 calls, floor 127.2k, 45.3M, $28.0; gsd-planner n=3, 57 calls, 85.0k, 7.7M, $10.7;
  gsd-verifier n=1, 13 calls, 83.5k, 1.3M, $1.4. Mission total 880 calls, 123.5M processed, ~$97, cache read 94%.

## Build
1. `tools/w4_benchmark.py`: for each sid, from its transcript, using `mission_spend.session_tokens` where it gives
   the field (read it first): calls, call-1 processed (input + cache read + cache write of the first assistant
   call), processed total, fresh input, cache read, cache write (5m and 1h separately if the rows distinguish them),
   output, cache-hit ratio = cache_read / (input + cache_read + cache_write), priced $ at the transcript model, and
   priced $ re-computed at Opus 5.5 rates (so a model change is separated from the context change).
   Write `vault/programs/factory-tranche-a/W4-benchmark.json` and `W4-benchmark.md`.
2. In the .md, judge the Track A done-gate per criterion with the number beside it:
   - priced cost per unit <= 40% of the old arm: compare each new unit with the old gsd-executor session
     ($57.1/21 per session) AND with the old worker epoch ($28.0/8); report both, at transcript model and at Opus 5.5.
   - slim first call <= 20k; cache-hit ratio >= 85% (per unit and pooled).
   - W3d: did the budget hook stop it at or near its 150k cap? Quote the transcript evidence (the hook's denial or
     stop text, the last call's cumulative spend). If no stop is visible, say NOT OBSERVED; never infer it.
   - Second consumer (an unrelated PP task) was NOT run in this tranche: list it as OPEN, not as pass.
3. `tools/test_w4_benchmark.py` (V-* gate style), printing `W4_PASS=n/n`: a synthetic two-call transcript with known
   tokens gives the exact processed, ratio and price; an unknown model gives UNPRICED, not 0; a missing transcript
   gives an error, not zeros; a mutant that drops cache_write from processed makes a test fail.

## Done
- `python tools/test_w4_benchmark.py` exit 0, `python tools/w4_benchmark.py` exit 0 and writes both files.
- Commit with a pathspec: `git commit -m "<msg>" -- tools/w4_benchmark.py tools/test_w4_benchmark.py vault/programs/factory-tranche-a/W4-benchmark.json vault/programs/factory-tranche-a/W4-benchmark.md vault/pricing/anthropic_2026-10.json`.
- Receipt `vault/programs/factory-tranche-a/W4-receipt.md`: the verdict per done-gate criterion, test counts, open
  items, and `COMMITS: <hash>` reachable from HEAD.
