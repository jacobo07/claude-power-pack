---
covers: [auto_rule, worktree_safe_cmd, branch_retry_due, ff_to_dirty_disjoint, ascension_autopilot]
tier: T2
owner_turn: "2026-11-27 pane 31498a3e, Owner: \"sí, y todas estas deberian haber continuado de forma autónoma toda la noche. debemos aprovechar las noches al 100%. subele el nivel de autonomia brutalmente\""
---
# Ascension autopilot: the night runs without the Owner (round 9)

## PRD
At 07:30Z on 2026-11-27 the day cap was nearly spent (477.9M of 500M). Five lanes had stopped on things nobody was
awake to clear:
- **FIFATC S383C and TENNIS S428T** parked `CHECKPOINT_ON_BRANCH ...: the product has tracked changes`. In both
  cases it was one dirty product file that the branch never touches. Round 8 aligned such a product only for
  RUNNING lanes. `evolve.ff_to` still refused any tracked change.
- **KSR S441K** parked `CHECKPOINT_ON_BRANCH`: its checkpoint was committed on 0 branches because the worker
  stopped first. A park of kind `branch` is lifted only by an Owner answer, so the lane would never have looked
  again after a relaunch committed the file.
- **WIIPARTY S400W** sat all night on a worktree-local `rm build; cp -a <product>/build build; python3 configure.py`.
- **WSR S405R** sat all night on "R2 first or certify first", a question it had answered itself ("Agent recommends
  R2 first").

## Behaviour
- **`evolve.ff_to` / `_dirty_overlap`**: a fast-forward runs over tracked dirty paths the range `cur..head` does
  not change, and reports "(N uncommitted file(s) kept)". A dirty path the branch also changes still refuses,
  and its paths are named. The merge path (`_merge_over_factory`) still requires a clean product.
- **`branch_retry_due`**: a lane PARKED with `park_kind == "branch"` and a mission is set back to RUNNING, with its
  judgment cleared, every `BRANCH_RETRY_S` (900 s). If discovery parks again with the same note
  (`ls.branch_note`), the lane goes back to PARKED silently: no queue line, no digest. A new note is told as
  before. A successful discovery clears `branch_note` and `branch_retry_at`.
- **`auto_rule`**: runs every tick before `take_answers`. A question that `open_question` still shows, asked at least
  `AUTO_RULE_S` (1800 s) ago, is answered once (per `ls.auto_ruled` key) through `record_answer`. The answer is
  then taken, delivered and planned exactly like an Owner-typed one.
  - **`approve Bash: <cmd>`**: approved only if `worktree_safe_cmd` says the command plainly stays inside the
    worker's tree:
    - no pipe, redirect, background, substitution, glob or extra line;
    - none of the denied programs (git, ssh, curl, sudo, kill, pip, find, bash and others);
    - no `..` or `~`;
    - absolute paths only under the product (as a read) or under `/tmp`;
    - every written path, and every `mv` source, relative and not `.`.
  - **Any other question**: answered "decide it yourself inside the mission envelope; where you stated a
    recommendation, take it; write the choice in your next checkpoint; the Owner may overrule it later".
  - **Left to the Owner**: a question matching `AUTO_RULE_DENY_RE` (budget, tokens, authority, cost, money,
    credentials, push, publish, deploy, production, email, send, post, sudo, account, force, legal, licence and
    similar). So is a command that fails the check. Each gets one owner_queue line, and its question alert keeps
    mailing.
  - Every auto-ruling writes a ledger row (`auto_ruling`), a log line and an `AUTO-RULING` digest line.

## Never
- No answer on budget, authority, money, credentials or outside effects. The autopilot never raises its own cap.
- No reset, rebase, stash or force. No merge into a dirty product. No write outside the worker's tree is approved.
- No change to gsd_mission, the day cap, the breaker or the judge.

## Acceptance
- V-EVO-FF-TO-DIRTY-REFUSED (an overlapping dirty path refuses, names it, and leaves product and file untouched)
- V-EVO-FF-TO-DIRTY-DISJOINT-KEPT
- V-AP-BRANCH-PARK-RETRIED (due -> RUNNING with judgment cleared and the next retry about 900 s out; not due -> PARKED)
- V-AP-AUTO-RULE-DECIDES, -APPROVES-WORKTREE-CMD, -REFUSES-OUTSIDE, -WAITS, -ONCE, -CMD-CLASSES

Mutants:
- ff_dirty_ignores_overlap, ff_dirty_refuses_all
- branch_retry_never, branch_retry_ignores_clock, branch_retry_no_spacing
- auto_rule_off, auto_rule_approves_any, auto_rule_ignores_deny, auto_rule_immediate, auto_rule_repeats

Known gap: the silent re-park (same `branch_note`) has no lane_tick-level test.

## Round 10 addendum (Owner 2026-11-27: "both, y dejalas todas running")
- **Caps:**
  - DAY_CAP 500M -> 1B.
  - TOTAL_CAP and UNLOCKED_CAP 4.7B -> 5.7B (+1B at 4.47B booked).
  - Pinned by V-AP-BUDGET-OWNER-5700M.
- **Weekly guard:** `~/.claude/state/account-governor-override.json` renewed until 2026-11-28T08:50:34Z, the
  governor's 24 h maximum. Backup `*.bak-3149-r10-*`. Renewing it again is the Owner's call each day.
- **`control_checkpoint`** (KSR S441K): the hold's residual is a relative path absent from the product. If it is
  committed at the HEAD of the lane's control repo (`cwd`), it is judged there as an absolute path. Otherwise the
  path is unchanged.
  - Test: V-AP-CONTROL-CHECKPOINT.
  - Mutants: control_checkpoint_never, control_checkpoint_uncommitted.

## Rollback
In `~/agora/ascension-autopilot`, restore these files from `*.bak-3149-r9autonomy-<ts>`:
- autopilot.py
- test_autopilot.py
- evolve.py
- state.json (if needed)

The new lane keys (`branch_retry_at`, `branch_note`, `auto_ruled`) are ignored by the old code. If an auto-ruling was
wrong, overrule it with `autopilot.py answer <LANE> "<ruling>"`: the newest ruling binds.

## Gate
Staging is `/tmp/ap-r9-stage-3149`. `deploy_on_green.sh` deploys only if all of these hold:
- AUTOPILOT_GATE_PASS, with "MUTANTS SURVIVED: none";
- both cron.lock and autopilot.lock are held;
- the live files still hash to ff7a9ee8 (autopilot), a5589aa0 (test) and 7e89fa2f (evolve).
