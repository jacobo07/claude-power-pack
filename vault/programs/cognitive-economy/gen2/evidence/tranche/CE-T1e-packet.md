done_gate: python tools/test_ce_t1_paneloss.py

# CE-T1e -- C4: pane-loss canary resumes model-free to first verified progress; T1 close

Contract: `vault/programs/cognitive-economy/gen2/COMPLETION-PLAN.md` -- read ONLY "Master Done-Gate" C4.
Fresh worker, no parent transcript. Do NOT spawn agents. Do NOT re-read files you do not edit.

## State you start from (do not rediscover)
- Read `CE-T1a..d-receipt.md` (same dir) first; reuse helpers from `tools/test_ce_t1_state.py` by import.
- Pane loss = the holder session dies without /kclear: there is no fresh seal, the transcript may be truncated, the
  claim marker may still name the dead holder. Owners: `tools/rollover.py` (`observe`, `seal`, `newest_capsule`,
  `claim` stale-takeover, `resume_flow`, `certify_flow`).

## Do
1. New `tools/test_ce_t1_paneloss.py` (V-CE-T1-PANE-* gates, `CE_T1_PANE_PASS=n/n`, exit 0 only if all pass), real
   functions, temp state_dir + temp git repo, zero model calls (inject a recording launcher; assert 0 calls):
   a. Holder A seals mid-work, claims, then dies (holder marked dead) with an uncertified claim. Successor B finds
      the capsule via `newest_capsule`, takes over the stale claim, refreshes, certifies -> RESUME_CERTIFIED.
   b. "First verified progress": after certify, B makes one commit in the temp repo matching the capsule's first
      obligation and a deterministic check (the capsule's next obligation now differs / the commit is reachable)
      passes. No transcript of A is read at any point (delete it before B starts).
   c. Controls (red): A still alive -> B refused (exit 5); capsule bytes edited -> gate REFUSED, B cannot certify.
2. Set C4 in `gen2/ledger.json`: `status: CHECKED`, `check: ["tools/test_ce_t1_paneloss.py"]` (one object, indent=1).
3. Run `python tools/test_cep_gen2_obligations.py` (green) and
   `python tools/test_cognitive_economy_program.py --generation 2 --final` ONCE: it must still FAIL, and C2, C3, C4
   must NOT be among the named failures. Paste the failure-name lines in the receipt.

## Receipt
`vault/programs/cognitive-economy/gen2/evidence/tranche/CE-T1e-receipt.md`: gate table, CE_T1_PANE_PASS line, the
`--final` failure lines (C2/C3/C4 absent), `COMMITS: <hash ...>`. Pathspec commits only. Never push. Write the receipt
BEFORE your last 2 calls.
