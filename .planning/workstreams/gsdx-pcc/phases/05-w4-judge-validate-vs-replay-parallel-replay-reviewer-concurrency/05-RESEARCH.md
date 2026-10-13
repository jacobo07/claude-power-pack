# Phase 5 Research -- premise verification (HR-PREMISE-001)

Every symbol a Phase 5 plan touches, read in source at `d639bf16` (P = read in source). No code was run for this file.

## 1. The judge today (P)

- `modules/gsd_x/goal/judge.py:120-191` `judge(state, tree_hash, worktree, scope_paths=None, timeout_s=900.0, env=None) -> JudgeReceipt`. One serial loop over `[o for o in cv.obligations.values() if o.disposition == SATISFIED]` (:138-147). Per obligation: pin check (`:150-160`, `digest_matches` per pinned file, appends a REFUSED row and `continue`s), then `subprocess.run(argv, cwd=worktree, capture_output=True, text=True, timeout=timeout_s, env=...)` (:165-167). `OSError/ValueError/SubprocessError` -> an UNJUDGEABLE row (:174-179), which outranks REFUSED (:181-188).
- Guards, in order: `GSDX_GOAL_EPOCH` set -> UNJUDGEABLE (:125); no worktree dir (:130); `tree_id(worktree, scope) != tree_hash` (:132-136); no SATISFIED obligation (:140-144).
- Only callers of `judge()`: `tools/gsd_x_goal.py:322` (`cmd_judge`) and `tools/test_gsd_x_goal_judge.py`. The sweep reads `jd.current(...)` (`sweep.py:371`) and uses `jd._argv` (`:476`); it never calls `judge()`. So the judge is a CLI/operator action, and `reconcile.py:179-184` consumes its banked receipt.
- `JudgeReceipt` fields: `verdict, reason, goal_id, revision, tree_hash, gates, ts`. Each replay row: `obligation, gate, verdict, exit_status, observed, seconds`.
- Mutation-suite anchors on `judge.py` (`tools/test_gsd_x_goal_mutation.py:254-266, :327`): `        if moved:`, `    if environ.get(EPOCH_ENV):`, `    if actual != tree_hash:`, `    if not satisfied:`, and the `current()` line `        if d.get("tree_hash") == tree_hash and d.get("revision") == revision:`. Phase 5 must leave each textually intact and unique.

## 2. Phase 2-4 seams the judge can reuse (P)

- `inherit.py:68-80` `observe_current(state, ob, contract, root) -> dict` derives the six premises from the working tree (None = unreadable). `:49-65` `ineligible(ob, contract, cert_data) -> str` ('' = may be inherited). `:39-46` `_latest_live(ledger, cid) -> (cert, payload, seq, ts) | None`. `:167-190` `inherited_ids(state, candidate)` trusts a `proof.inherited` event whose premises `_agrees` with the certificate; the judge must NOT use this as evidence (spec S3: the event is a claim).
- `proof.py:218-231` `observe_premises(cert, current, now)` and `:234-248` `state_from_premises(obs, has_inherited_event, inheritance_on) -> (state, why)`; PS_INHERITED only when all six equal. `:447` `effective_contract(ledger, ob)`; `:112-130` `project_proofs(state) -> ProofLedger`; `:599-612` `independent(a, b)`; `:65` `inheritance_enabled()`.
- `frontier.py:58-86` `gate_unit(ob, state)` (reads, writes `run:<oid>`, resources `integration-env` / `reality-env`); `:122-129` `bound(ctx)` reads `ctx.budget` then `ctx.state.budget` (posture ECONOMY=1, BALANCED=2, WALL_CLOCK=4, `max_parallel` only lowers it; bool ignored). `:38-43` `frontier_enabled()` (env `GSDX_FRONTIER` and no `FRONTIER.off`).
- `GoalState.budget: dict` (`contract.py:77`).
- Memory probe precedent: `tools/gsdx_reality_baseline.py:127-146` `free_ram_mb()` (ctypes `GlobalMemoryStatusEx` / `/proc/meminfo`, None when unreadable). It is in `tools/`, so the judge cannot import it; the probe is re-implemented in the new `replay.py`.

## 3. evidence_bundle (P)

- `tools/evidence_bundle.py:95-108` `ticket()` hashes `artifacts` through `_proofs` (which re-reads each file) and writes `review-ticket.json` with a `secrets.token_hex(12)` nonce. `:111-131` `write_review` takes the ticket's hashes as "what the reviewer saw" and fails when the reply lacks the nonce line. The vendored collector re-reads artifact bytes after assembly and compares.
- The hole (`:140-141`): between `ticket()` and the reviewer's read, an A->B->A rewrite leaves the final bytes equal to the ticket's, so the review passes although the reviewer may have read B. Nothing records a write, only content.
- Existing suite: `tools/test_evidence_bundle.py` (`EVB_PASS=n/n`, hermetic temp root, uses `eb.ticket/write_review/collect`). `bundle()` takes `edit_after_ticket`; the new gates extend this pattern in a new suite, not by editing it.

## 4. The event vocabulary (P)

- `proof.py:41-74`: `NEW_TYPES`, `REQUIRED_FIELDS`, `ProofLedger` slots (`:102-109`), `project_proofs` slot map (`:114-116`), `append_pcc` (`:133-145`, calls `log.append(state.last_seq + 1, ...)`, so a concurrent writer gets `LostRace`, `log.py:54`).
- Spec S7 frozen table (`vault/specs/gsdx-proof-conserving-convergence.md:138-144`) lists `review.received | 5 | claim_id, candidate, ticket | 1`. `tools/test_gsd_x_goal_pcc_semantics.py:1212-1227` pins `frozen == [review.received, adapter.maturity, continuation.sealed]` and `landed == set(proof.NEW_TYPES)`; `:70-90` `sample_payloads()` and `tools/test_gsd_x_goal_pcc_replay.py:719` carry a per-type sample. Phase 4 moved `candidate.promoted` the same way, so these are updated in the same commit.

## 5. CLI (P)

`tools/gsd_x_goal.py:319-330` `cmd_judge`; subparsers registered `:379-476` with `common(sub.add_parser(..))` and `set_defaults(fn=..)`. A `review` subcommand follows the same shape.

## 6. Premises the plans must NOT assume (checked, not found)

- No existing review module or `review.*` event in `modules/gsd_x/goal/` (Grep: only the frozen row). `review_intake.intake(reply, agent, model)` lives in `tools/review_intake.py` and is used by `evidence_bundle`.
- `judge()` is never called from the sweep, so "VALIDATE at sweep time" would be a new consumer; this phase keeps the judge a separate action.
- There is no write journal for the working tree; `candidate.snapshot` hashes a tree through git objects, not through a change log.

## 7. Risks carried into the plans

- Windows mtime granularity: a stat journal can miss a rewrite inside one clock tick. The journal gate therefore sets distinct mtimes explicitly in tests; the residual (deliberate mtime restore on Windows) is recorded as a limit.
- Gate commands can write into the worktree; independence only covers the declared sets (`run:<oid>`), so a gate that writes shared files is a Phase 6/9 concern, stated in the SUMMARY.
- Laptop RAM: every suite runs alone, one per call; drills one per call, UNRUN on a kill.
