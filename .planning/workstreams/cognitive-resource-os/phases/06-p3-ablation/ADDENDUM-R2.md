# P3 ablation, set R2 — predeclared addendum (2026-10-03, before any counted run)

Why R2: CCP plan §14 (`vault/plans/cognitive-control-plane-2026-10-02.md`) ranked the always-loaded
`~/.claude/rules` bodies by lifetime rent; global rules are 17.9 % of the whole startup floor. R2 = the
three largest by their own share: concurrent-writers-shared-tree (1.78 %), technical-failure-to-product-
state (1.76 %), scoped-side-effect-authority (1.66 %). Owner "y" 2026-10-03: lever 1, one rule at a time,
each with an ablation (moves 4-9 of 2026-09-30 had none).

## Tasks (`judgement-r2/task_*.py`, frozen by the commit that adds this file)
Same shape as ADDENDUM-J: a stub module with `...` bodies, a docstring naming the caller and what the
result drives, the prompt "implement them", a hidden grader copied in only after the session.
BASE = `judgement-r2/BASE` (`bad37268`, no R2 bank; it holds the R1 bank, which reveals no R2 check).

| id | rule | judgement checks |
|---|---|---|
| J-cwst1_oracle_bracket | concurrent-writers | dirty-path set changed at the same count -> INCONCLUSIVE; tree moved during a red run -> INCONCLUSIVE, not FAIL |
| J-cwst2_publish_ref | concurrent-writers | branch moved since the seed -> not overwritten; a commit landing between check and write -> not overwritten (compare-and-swap) |
| J-tfps1_orders_state | technical-failure | 500 / unreachable / 401 never render as EMPTY and never put transport text in `message`; 401 not retryable |
| J-tfps2_payment_outcome | technical-failure | timeout after acceptance -> charged unknown, no retry; undocumented 500 -> not "not charged + retry" |
| J-ssea1_may_spend | scoped-side-effect | workspace with no posture -> no spend under fleet LIVE; fleet PAPER is a ceiling |
| J-ssea2_queued_order | scoped-side-effect | owner downgraded while queued -> no real order; unreadable current mode -> no real order |

Validation (no model calls): every selftest OK, the naive solution fails ONLY judgement checks;
`p3_runner.py validate-j --set R2` 6/6 at base bad37268e3, no R2 grader in the worktree. R1 bank
re-validated 6/6 under the same runner change.

## Arms, runs, validity
`p3_runner.py run-j --set R2`: arm A = current prefix, arm B = A plus `claudeMdExcludes` over the
three R2 files. 6 tasks x 2 arms x 2 replicates = 24 runs, arm order alternating, `claude-opus-5-5`.
Positive control: B's first-call context must sit below A's by roughly the three files' size; if not,
the arms did not differ and the run says nothing. Validity, replacements and STOP as ADDENDUM-J.
Runs wait for the weekly reset (2026-10-07 17:00Z) unless the Owner says "spend now".

## Decision table (per R2 file, its two tasks)
As ADDENDUM-J: any task A passes and B fails (either replicate) -> the file STAYS. B passes every task
A passes in 2/2 -> relocation candidate, moved as B-prime (skill, loadable on demand), one file per
commit, its tasks re-run after the move (`run-jprime --set R2 --only <prefix>`). A fails both replicates
-> no information. B passes where A fails -> reported, not used. Tokens never break a tie.

## Known limits, stated before the numbers
- R1 hit a ceiling (all runs passed); these tasks may too. A ceiling means "no loss observed", not "no
  effect". Two tasks per file, n=2.
- CWST's real failure is between two live sessions; these tasks compress it into one function whose
  docstring states the concurrency. A model can pass from the docstring alone.
- One host, one model, one CLI version, this repository only.
