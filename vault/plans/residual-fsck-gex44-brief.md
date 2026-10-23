---
covers: [cpp-fsck, residual-r5, residual-r6]
status: WORKER BRIEF for the GEX44 clone ~/missions/residual-fsck (Owner "2. GEX44", 2026-10-23). Bounded: --max-turns 45, sonnet.
---

# Worker brief: R5 cpp_fsck + R6 knowledge (residual plan aa97ebf8)

You are a headless worker in a clone of Claude Power Pack on GEX44 (Linux). Use Bash/Read/Edit/Write/Grep/Glob.
Do NOT touch `~/.claude`, settings, hooks, or any live install. Do NOT push. Commit in this clone only, one commit
per unit, message ending with `Co-Authored-By: Claude Sonnet <noreply@anthropic.com>`. Stop when both units are
committed and their tests pass, or when you cannot make progress. Write `RESULT.md` at the repo root at the end:
the commits, the test output lines, and anything left open.

Context to read first, and nothing more: `vault/plans/incremental-kernel-residual-2026-10-23.md` (sections 1-3),
`tools/rollover.py` function `dispositions`, `modules/provider_routing/ledger.py` (`_gfold`, `_summary`),
`vault/estate/worktree-lifecycle.json`.

## Unit 1 (R5): `tools/cpp_fsck.py` + `tools/test_cpp_fsck.py`
A read-only consistency checker. It needs no model, never mutates anything, and prints repairs as existing commands only.
Each check takes its roots as arguments (defaults: the laptop paths under `~/.claude/state` and the repo) so tests run
on fixtures in a temp dir. Output: one JSON object `{"findings":[...], "unknown":[...], "checks":{id: "PASS|FINDING|UNKNOWN"}}`;
exit 0 when every check is clean, 1 when any finding exists, 2 when a check could not see its subject.
An unreadable or missing source is UNKNOWN, never PASS (a negative result needs proof the observer could see).

Checks (each from a production incident on 2026-10-23):
- F1 `stranded_lease`. Source: `goal-budget/<goal>/spend.journal.jsonl`. A `reserve` row is open if no `settle` row
  lists its id in `closes`; a `leak` row marks it LEAKED. A finding is an open reserve older than 24 h whose session has
  no transcript write in 24 h (transcript `<projects>/**/<sid>.jsonl` mtime). If the transcript is missing, the result
  is UNKNOWN for that sid. Repair text: `python tools/mission_spend.py goal-settle --goal G --session S`.
  Fixture: three LEAKED reserves (952,270 / 1,060,540 / 750,000) on dead sessions, plus a control: one fresh reserve
  on a session whose transcript was written now, which must PASS.
- F2 `parked_chain_polled`. Sources: a chain.json and its tick log. A finding is `parked: true` plus any tick-log line
  newer than the chain file's mtime whose action is not `parked`/`held` (e.g. `ram_hold`, `arm_refused`).
  Control: parked chain with only `parked` lines.
- F3 `worktree_without_lifecycle`. Source: `git worktree list --porcelain` of a repo plus the lifecycle JSON. A finding
  is a DIRTY worktree (non-empty `git status --porcelain`) with no row, reported BY PATH. Clean worktrees without a row
  are listed under `info.unclassified_clean` by path. Use real temp git repos in the test.
- F4 `stale_resumption`. Source: every `vault/programs/*/RESUMPTION_FILE.md`. Read the `Coherence anchor` line's
  commit sha. If there is no anchor, report UNKNOWN_FRESHNESS. If the sha is not an ancestor of HEAD (`git merge-base
  --is-ancestor`), report STALE. Control: an anchor that is HEAD.
- F5 `capsule_without_disposition`. Source: the rollover ledger through `rollover.dispositions`. A finding is a capsule
  with disposition PENDING or CLAIMED_NO_VERDICT older than 24 h. Control: a certified capsule.
- F6 `denominators_unlabelled`. Build a GoalLedger in a temp state dir and assert `_summary` carries `scope`, `lease`
  and `programme_executable`. A missing key is a finding (regression guard for commit 2259ca87).

Tests: AAA, one `V-FSCK-<ID>` gate per finding fixture and one `V-FSCK-<ID>-CONTROL` per control, plus
`V-FSCK-UNKNOWN-NOT-PASS` (missing source gives exit 2) and `V-FSCK-READ-ONLY` (the fixture tree's file hashes are
identical before and after a run). Print `FSCK_PASS=n/N  threshold=N/N`, exit 1 on any fail. Then drill each check
once by inverting its predicate on a COPY with `tools/mutation_drill.py` if it supports this; otherwise copy the file
to a temp path yourself. Each drill must turn its gate red; record the drills in RESULT.md.

## Unit 2 (R6): knowledge
Grep `vault/knowledge_base/ukdl-universal.md` and `vault/` for an existing pattern covering "derived answer read
without checking whether its inputs moved" (look for invalidat, stale, recompute, denominator). If one exists, append
the 2026-10-23 evidence to it. Otherwise add ONE entry `RECOMPUTATION_WITHOUT_CAUSAL_INVALIDATION`, with:
symptom (58 identical E4b2 refusals; ASER events counted per day; an unlabelled lease remainder read as programme
headroom; a stale RESUMPTION_FILE), root cause, guard (commits 2259ca87, fa840b3c, 7eafc2b0, and cpp_fsck), and two
traps. No new files besides the entry.
