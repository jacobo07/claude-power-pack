# P3 instruction ablation — predeclared protocol (2026-09-28)

Committed BEFORE any counted run. A threshold chosen after seeing numbers is not a threshold.
Runs are DEFERRED to subscription quota (Owner, 2026-09-27: no paid spend for experiments).
Owner consent (2026-09-27): relocate `~/.claude/rules` content only if this ablation shows
non-inferior quality; one reversible commit per move.

## Question
Does removing a candidate rule set R from the always-loaded prefix degrade VERIFIED task
outcomes? Tokens are the secondary metric and never decide on their own.

## Candidates (from `prefix_inventory.py`, 2026-09-28)
Unconditional ~102k tok est.; rules 56.8k across 22 files, none path-scoped. After the peer's
evidence move (rule text kept, incident history moved to `knowledge_vault/rules-evidence/`)
the rules are mostly general doctrine, NOT project-specific — so per-project relocation has
few candidates. The lever under test is ON-DEMAND loading (skill / path-scoped) of large
general rules. First candidate set R1 = the three largest: instrument-before-claim (~11.9k),
destructive-state-authorization (~6.3k), real-context-reachability (~5.8k).

## Pre-flight (must pass before any counted run) — measure, do not assume
P0 How to run arm B without R and WITHOUT editing the Owner's global config or copying
   credentials. Candidates to test, in order: a `--setting-sources` / settings flag that skips
   user rules (verify it affects rules, not only settings); a per-run config dir only if it can
   reuse auth without copying the credential file. If none works: STOP, report, do not improvise.
P1 A/A: arm A twice on one task; report the spread of every metric. Noise floor first.

## Task set (frozen by commit, graded by tests, not by a model)
Seed = mutation-drill tasks already proven in this repo: take a known mutant (e.g. the three
`tis_observed` drills: no-dedupe, no-bom, no-synthetic-skip; `pricing_source` newest-wins),
apply it to a clean worktree, prompt "tests fail, fix it", grade = the V-gate suite exit code.
Plus 2 tasks inside R1's domain (a destructive-effect guard, a measurement claim) where the
rule SHOULD matter. Minimum 8 tasks; list frozen in `p3-tasks.json` in the first run commit.

## Arms
A = current prefix. B = prefix minus R1 (R1 reachable on demand in B-prime, a second arm, once
P0 shows how). Same model, same effort, same worktree commit, one task per fresh session.

## Metrics (observed via tools/tis_observed.py on the run transcripts)
Primary: task pass (V-gate exit 0) — binary per task. Secondary: first-call context,
total context tokens, calls, wall time. Per-run validity: the worker session must be
`sdk-cli`, the transcript must be MEASURED, and the gate must actually run (count its PASS lines).

## Decision table
- B passes every task A passes, in 2 of 2 replicates → R1 is a relocation candidate; move one
  file per commit, re-run its domain tasks after each move.
- Any task A passes and B fails (either replicate) → R1 stays; record which rule mattered.
- Any invalid run (UNMEASURED transcript, gate did not run, wrong entrypoint) → replace it, max 2
  replacements per task, then declare the instrument unreliable and stop.
- Token savings are reported, never used to break a tie on quality.
