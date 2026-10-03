# Phase 3 context: Turn advancement and non-convergence (H, J)

Discuss mode: unattended; no grey area needs the Owner. Decisions taken from the frozen rules and the evidence.

## Frozen rules (ledger `frozen.pillars`)

- H: "deliver a reproducible turn taxonomy (advancing/coordination/bookkeeping/recovery/proof/repeat/non-convergent)
  over usage_index joined to git; any optimization it suggests faces the 3 % rule". Owners: `tools/root_progress.py`,
  `modules/gsd_x/goal/`.
- J: "decided from H: non-advancing turns of interactive roots >= 3 % of D-W7 earns a detector proposal; also
  record (audit G5) that Ralph no_progress fingerprints the whole work dir, so in a shared checkout peer churn reads
  as progress". Owner: `tools/gsd_mission.py`.

## Decisions

- D1: J's decision input is the weighted share of repeat + recovery + non_convergent turns in HUMAN-rooted trees
  (pre-registered in `measure/turns.py`'s docstring before any figure existed, commit 8f7b6caf). The broader
  "every class except advancing" share is reported beside it, never used to decide.
- D2: UNSETTLED is not waste. An edit whose repo history could not be read is `edit_unknown`, which no class claims.
- D3: The hand-labelled control is labelled blind from a sheet that shows what each call did, never its class.
  An unattended run labels it itself; that is stated in the evidence as a limitation (one labeller, the same agent
  family as the classifier's author).
- D4: G5 verified in source: `tools/gsd_mission.py:1649-1671` (`progress_fingerprint`) hashes HEAD, whole-tree
  `status --porcelain` and `diff HEAD --shortstat` of the work dir.
