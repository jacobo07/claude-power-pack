# P3 instruction ablation — REPORT (2026-09-29)

Protocol: `vault/plans/cognitive-resource-os-P3-ablation-protocol.md` (committed before any counted run)
+ `ADDENDUM.md`. Raw data: `results.jsonl` (32 rows), `run.log`. Analysis script re-derives every figure
below from `results.jsonl` alone.

## Run
- Host laptop, claude 2.1.284, model `claude-opus-5-5` in both arms, BASE = the commit freezing
  `p3-tasks.json`. 8 tasks x 2 arms x 2 replicates = 32 runs, one `claude -p` session each.
- Validity: **32/32 valid on the first attempt, 0 replacements.** Every transcript MEASURED, every
  entrypoint `sdk-cli`, every grade printed its `_PASS=` line.

## Positive control (arm B really lacked R1)
first-call context, all 16 pairs: A 166,585–166,709; B 137,207–137,605. Per-pair A−B delta 28,996–29,488
tokens, which is the size of the three R1 files. `claudeMdExcludes` applied in every B run.

## Primary metric — task pass (the only one that decides)

| task | A r1 | A r2 | B r1 | B r2 |
|---|---|---|---|---|
| T1-tis-dedupe | pass | pass | pass | pass |
| T2-tis-bom | pass | pass | pass | pass |
| T3-tis-synthetic | pass | pass | pass | pass |
| T4-pricing-newest | pass | pass | pass | pass |
| T5-pricing-missing | pass | pass | pass | pass |
| T6-rollover-sealed-hash (R1 domain) | pass | pass | pass | pass |
| T7-budget-population (R1 domain) | pass | pass | pass | pass |
| T8-budget-unknown-not-zero (R1 domain) | pass | pass | pass | pass |

## Verdict (decision table row 1)
**B passes every task A passes, in 2 of 2 replicates -> R1 is a relocation candidate.**

## What this verdict does NOT show (read before acting on it)
- **Ceiling.** Both arms solved 16/16. The instrument could have returned "A-pass/B-fail" (B was a
  genuinely different prefix, proven above), but no task came near failing in either arm, so the set
  has no measured power to detect a small quality loss. The claim is "no degradation observed on
  8 seeded single-defect tasks graded by an existing test", not "R1 has no effect".
- **Task shape.** Every task hands the agent a failing test that points at the defect. R1's rules are
  about judgement where no test exists yet (choosing an identity, proving an absence, reachability).
  That behaviour is outside what this set can observe, including in the three R1-domain tasks.
- **B-prime (R1 reachable on demand) was not run.** The protocol names it; relocation should give B-prime,
  not B, so the moved rules must still be loadable when relevant.
- One host, one model, one CLI version.

## Secondary metrics (reported, never a tie-breaker)

| arm | runs | wall mean / median s | total context mean | total context sum | output mean | calls mean |
|---|---|---|---|---|---|---|
| A | 16 | 103.5 / 97.2 | 1,152,714 | 18,443,425 | 1,510 | 6.8 |
| B | 16 | 104.1 / 102.2 | 914,439 | 14,631,024 | 1,533 | 6.4 |

Total context read per task fell 20.7 % in arm B (mostly cache reads; ~29k per call x ~6.5 calls).
Wall time and output are unchanged within noise. A/A spread (the two A replicates of one task) reaches
1.73M vs 1.03M total context on T6 and 168 vs 99 s on T7, so per-task secondary differences below that
are not interpretable; only the 16-run aggregate is.

## Next step (Owner consent 2026-09-27: one reversible commit per move)
Per the table: move ONE R1 file at a time from always-loaded `~/.claude/rules/` to on-demand loading
(the B-prime shape), re-run that file's domain tasks after each move. Order by size:
instrument-before-claim, destructive-state-authorization, real-context-reachability. Recommended
before the first move: add at least 2 tasks per file with no pre-existing test (judgement tasks) so the
re-run can actually fail. (Done: section J below.)

## J. Judgement tasks (ADDENDUM-J.md, 2026-09-29) — no pre-existing test, hidden graders
6 tasks (2 per R1 file) x 2 arms x 2 replicates = 24 runs, BASE `103d0808` (no bank in the tree).
**24/24 valid on the first attempt.** Positive control held: A first-call 165,082–165,580, B 136,249–136,467.

| task (rule) | A r1 | A r2 | B r1 | B r2 |
|---|---|---|---|---|
| J-ibc1_flag_sweep (IBC) | 3/3 | 3/3 | 3/3 | 3/3 |
| J-ibc2_manifest_gate (IBC) | 5/5 | 5/5 | 5/5 | 5/5 |
| J-dsa1_draft_discard (DSA) | 3/3 | 3/3 | 3/3 | 3/3 |
| J-dsa2_bulk_delete (DSA) | 3/3 | 3/3 | 3/3 | 3/3 |
| J-rcr1_error_count (RCR) | 3/3 | 3/3 | 3/3 | 3/3 |
| J-rcr2_ad_purchases (RCR) | 3/3 | 3/3 | 3/3 | 3/3 |

Every judgement check passed in every run, including the ones only a naive solution fails:
empty sweep refused, empty manifest not verified, autosave-after-preview draft kept (also at same
size and mtime), batch skipped the regenerated and the missing member and reported only what it
deleted, missing log not 0, absent `actions` not 0.

**Verdict per file (ADDENDUM-J decision table): instrument-before-claim, destructive-state-authorization
and real-context-reachability each stay relocation candidates** — B passed every task A passed, 2/2.

Bank-access audit: tool inputs of all 24 transcripts were searched for the bank's names, `git log
--all` and the phase directory. Two hits, both in J-ibc1_flag_sweep-A-r2 and both false: the agent
named its own scratch check `flag_sweep_check_p3j.py` after the module folder `p3j/`. No run read the bank.

Secondary (never a tie-breaker): total context mean A 1,229,284 / B 934,114 (−24.0 %); wall mean A 91.5 s /
B 84.4 s; output and calls unchanged within noise.

What this adds and what it does not: the naive failure modes these rules were written against were
avoided by the model WITHOUT the rules in context, on six small, single-function tasks whose docstrings
name the consequence (deletes, publishes, pages on-call, pauses spend). It says nothing about long,
multi-file sessions where the consequence is not written next to the code, and it was measured in this
repository only (Owner declined a neutral-repo replicate, 2026-09-29). The relocation is global
(`~/.claude/rules` loads in every repository), so it moves as B-prime: the rule stays loadable on demand.

## Move 1: instrument-before-claim -> PP skill (2026-09-29, commit efdb5e0)
Rule body moved byte-identical (sha256 55c37732...) to `skills/instrument-before-claim/SKILL.md` in PP,
live copy `~/.claude/skills/instrument-before-claim/SKILL.md`; `~/.claude/rules/` keeps a 592 B pointer
(was 45,948 B). Backup `~/.claude/backups/rules-20260929-134341/`. The skill was discovered live (it
appeared in the skill list of the session that made the move).

B-prime check (`run-jprime --only ibc`, arm P = the prefix as it now is, 2 tasks x 2 reps):
4/4 valid, 4/4 pass (3/3 and 5/5). first-call context 154,068–154,453, against 165,082–165,580 in arm A
before the move: **−11.0k to −11.5k tokens per session start.**
**Skill auto-activation: 0/4.** No run invoked the skill or read its file (tool inputs searched for the
skill name). The tasks passed without it, as they did in arm B. So the move is measured to save tokens
without a loss on these tasks; it is NOT measured to deliver the rule when it is needed, because the
model never asked for it here. Caveat: the runner's `--allowedTools` list does not name `Skill`; a
Skill call would still have appeared in the transcript as an attempt, and none did.

## Move 2: real-context-reachability -> PP skill (2026-09-29)
Same procedure: body byte-identical (sha256 9a24cdaa...), `skills/real-context-reachability/SKILL.md` +
live copy, 635 B pointer in rules/ (was 22,408 B), backup `~/.claude/backups/rules-20260929-135725/`.
B-prime (`run-jprime --only rcr`): 4/4 valid, 4/4 pass (3/3). first-call 146,046–147,711, i.e. a further
~−6.7k after move 1 and ~−18k against arm A before any move. **Skill auto-activation 0/4.**

## Move 3: destructive-state-authorization -> PP skill behind a deny-once card hook (commit 7f98579)
First attempts to write the hook were refused by the auto-mode classifier (Self-Modification); done after
the Owner left auto mode. Body byte-identical (sha256 5aaa3088...), 729 B pointer (was 24,495 B), backup
`~/.claude/backups/rules-20260929-142535/`.

Hook `hooks/destructive_doctrine_card.js` (PreToolUse-Bash-chain, both dispatchers): the first destructive
shell command of a session is denied once with the doctrine card. Test 15/15 alone; never-deny mutant 11/15.
**The end-to-end run found a dispatcher defect**: `mergeOutputs` merged hookSpecificOutput last-writer-wins,
so rtk-rewrite.js's `permissionDecision:'allow'` finishing after a gate's deny turned it into allow (the
card's deny came back as allow with the card's reason). The same exposure applied to cascade_check_bash.js
(HR-CASCADE-002). Fixed: deny > ask > allow, all deny reasons kept, updatedInput dropped on deny. E2E 17/17
after (red before); dispatcher regression suites all green (stop-schema 15, block-reason 20/20,
bash-channel 25/25, secret-failopen 3/3, priority-lane 4/4, sessionstart-routing 6/6, cascade 8/8).

B-prime (`run-jprime --only dsa`): 4/4 valid, 4/4 pass (3/3), first-call 137,556–139,781 (~−27k against arm A
before any move). Skill auto-activation 1/4 (J-dsa2 r2 invoked it unprompted). The card fired live once:
J-dsa2 r1 ran `Remove-Item` for cleanup, was denied with the card, re-issued 8 s later and passed
(ledger: deny-card then pass-already-shown); it did not load the skill afterwards and the task passed.

## Totals after the three moves
Always-loaded rule bytes 92,851 -> 1,956 (three pointers). First-call context ~165.5k -> ~138.5k (≈−27k
tokens at every session start, every repository). Quality: every task passed in every arm and after
every move (32 + 24 + 12 runs). Auto-activation of the moved skills: 1/12; the destructive rule is the
only one also delivered by event. Revert any move by copying its backup over the pointer.

## R2. Judgement tasks for the three highest-rent rules (ADDENDUM-R2.md, 2026-10-03)
Set chosen by CCP plan §14 (lifetime rent). Owner "spend now". `p3_runner.py run-j --set R2 --reps 2`,
BASE `bad37268`, claude 2.1.x, `claude-opus-5-5`, every run `sdk-cli`. Raw: `results-j-r2.jsonl`, `run-j-r2.log`.
**24/24 valid on the first attempt, 0 replacements.**

Positive control: first-call context A 114,823–116,185, B 109,378–109,494. Per-file diff of the startup
attachments (A-r1 vs B-r2, ssea1): the instructions differ by exactly the three R2 files (7,405 + 7,299 +
6,917 chars) and nothing else. The one low A value (114,823, ssea1 A-r2) came from SessionStart hook text
(−2.9k chars in `hook_additional_context`), not from the rules: instructions were 172,120 chars in both A runs.

| task (rule) | A r1 | A r2 | B r1 | B r2 |
|---|---|---|---|---|
| J-cwst1_oracle_bracket (CWST) | 5/5 | 5/5 | 5/5 | 5/5 |
| J-cwst2_publish_ref (CWST) | 3/3 | 3/3 | 3/3 | 3/3 |
| J-tfps1_orders_state (TFPS) | 5/5 | 5/5 | 5/5 | 5/5 |
| J-tfps2_payment_outcome (TFPS) | 5/5 | 5/5 | 5/5 | 5/5 |
| J-ssea1_may_spend (SSEA) | 5/5 | 5/5 | 5/5 | 5/5 |
| J-ssea2_queued_order (SSEA) | 5/5 | 5/5 | 5/5 | 5/5 |

**Verdict per file (ADDENDUM-R2 decision table): concurrent-writers-shared-tree,
technical-failure-to-product-state and scoped-side-effect-authority each stay relocation candidates** —
B passed every task A passed, 2/2. Each moves only as B-prime (skill loadable on demand), one file per
commit, its two tasks re-run after the move (`run-jprime --set R2 --only <cwst|tfps|ssea>`).

Bank-access audit: 133 tool calls across the 24 transcripts searched for the bank, grader, results and
addendum names and `git log --all`: 0 hits. Skill calls: 0.

Secondary (never a tie-breaker): total context mean A 708,838 / B 680,370 (−4.0 %); wall mean A 77.2 s /
B 75.6 s.

Same limits as J, stated before the run: a ceiling (every check passed in every run) means no loss was
OBSERVED, not that the rules do nothing; two tasks per file, n=2; the concurrency of CWST is compressed into
one function whose docstring states it; one host, one model, this repository only.

## Move 4: concurrent-writers-shared-tree -> PP skill (2026-10-03, Owner "y", auto mode off)
Body byte-identical (sha256 0c86aa17...), `skills/concurrent-writers-shared-tree/SKILL.md` + live copy
(both sha256 b1eda762...), pointer in rules/ (was 7,094 B), backup `~/.claude/backups/rules-20261003-090729/`.
The skill appeared in the live skill list of the session that made the move.

B-prime (`run-jprime --set R2 --only cwst`, arm P = the prefix as it now is, 2 tasks x 2 reps): 4/4 valid,
4/4 pass (5/5, 3/3). first-call 113,640–114,093 against arm A 116,069–116,185 before the move:
**about −2.0k to −2.5k tokens per session start.** Skill auto-activation 0/4: no Skill tool_use and no
tool input naming the rule or skill in 18 tool calls (counted on tool_use blocks; a raw text count reads
the skill listing and the pointer, 2 and 30 in every run, and is not an activation measure).
