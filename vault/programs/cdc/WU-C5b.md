# WU-C5b -- C5 remainder: proof of closure vs full suite, with baseline-red control

Common brief: `vault/programs/cdc/PROGRAMME.md`. Continues C5 (receipt WU-C5-receipt.md; code landed there).
Why: the first proof (`tools/c5_proof.py`, WU-C5-proof.json) was NOT valid: 10 parallel workers + 90 s cap gave
~125 red suites of 463 (timeouts/contention + real pre-existing reds), and the python-import closure of a widely
imported tool (tier_routing, land_worktree) is ~272 suites, i.e. not "local".
Steps:
1. Serial (or 2 workers), per-suite cap 300 s, run the 463 suites ONCE at base commit 7aaff610 -> baseline red set B (record timeouts as such, not red).
2. For 3 past landings with Python-only paths (pick small leaf tools, not tier_routing/change_impact): closure verdict = (closure reds) minus B; full verdict = (all reds) minus B. Agree iff both empty or same set. Record times + test counts.
3. Make `--affected` baseline-aware: optional `--baseline-red FILE` (suites known red before the change are reported, not blocking); receipt lists them. Test it.
4. Narrow the closure: report leaf-vs-hub (if closure > 25 % of suites, flag HUB in receipt and require explicit --test instead of silently running 272).
5. JS/vault paths: `--exempt` is explicit; add hooks/*.js -> tools/test_<name>.py mapping by name where one exists.
6. Land via land_worktree `--affected`. Receipt `WU-C5b-receipt.md` Status: DONE.
