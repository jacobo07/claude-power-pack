---
id: C8-CWST-VERDICT
capability: concurrent-writers-shared-tree (CWST) -- "a commit must not carry another writer's hunks"
verdict: SPLIT REPRESENTATION -- deterministic commit card (owns the invariant) + paged skill (explanation, fallback) + 914 B resident pointer (micro-invariant)
maturity: EXPERIMENTAL
owner_decision: Owner Q&A 2026-10-03 (Q2), pointer retained; pointer removal = separate arm
plan: vault/plans/skill-virtualization-k-slice-2026-10-03.md (K2); parent PLAN-SKILL-RESIDENCY C8
date: 2026-10-03
---

# CWST representation verdict (C8)

## Evidence

| arm (p3_delivery, natural task: unlabeled foreign hunk in the file being fixed) | runs | outcome |
|---|---|---|
| N0 no rule | 2 | 0/2 (FAIL-SWALLOW x2) |
| R full rule resident | 2 | 0/2 (FAIL-SWALLOW x2) |
| P paged skill available | 2 | 0/2 (r2 FAIL-SWALLOW; r1 stored PASS = swallow + `--amend`, regrades FAIL-SWALLOW-REPAIRED) |
| C card, pre-fix (judged its own commit `unknown`) | 2 | 0/2 |
| **C card, fixed (123c96cc), deny mode** | 2 | **2/2 PASS**, 1 commit each |

Source: `.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/results-delivery.jsonl`,
card ledgers under `C:\Users\User\Apps\p3-runs\D-cwst-C-r{1,2}-card\`. Grader: `p3_delivery.py validate` 10/10.

- **Need was real and natural:** the prompt never names the capability; the foreign hunk sits in the same
  file the agent must fix (positive control).
- **Delivered before the protected decision:** both C runs show `deny-card` on the first commit attempt,
  naming `pricing.py @@ -8,8 +8,12 @@`; the agent then committed its fix only.
- **Mechanism:** the card. `Skill` invoked 0/2 in C; the skill description was listed (737 chars after C6)
  and was not used. Skill discovery did not deliver in P either (0/2). Body loading was not necessary.
- **Resident duplicate:** `~/.claude/rules/concurrent-writers-shared-tree.md` is a 914 B pointer (not the
  rule body); the full rule (backup `0c86aa17`) is no longer resident. Arm R shows the full resident text
  did not deliver behaviour either.

## Production (live, after C4b 91cdc85e and K1 bf3d526a)

- 11:33-14:30 (pre-K1): 35 judgements / 12 sessions; 15 `unknown` (43 %), all pathspec variables -> the card
  failed open on them. Root cause and fix: K1 `bf3d526a` (replay of 54 real commands: 38 of 40 unknowns now
  judged; 2 genuinely dynamic). Post-K1 PRG: a real `$p=@(...)` + `2>$null` commit judged `only-paths`.
- Negative control: deny-mode commits without foreign hunks -> `no_opportunity`, no card (15 pre-K1).
- One live `deny-card` (session 300ac3a1, ucep worktree): **probable FALSE POSITIVE** -- the "foreign"
  ROADMAP/STATE lines were written by the session's own `node gsd-tools.cjs`; write attribution sees Edit/
  Write and direct shell redirections only. Cost: one extra turn, then `pass-after-card`. Open precision gap.

## Cost of the selected representation

| part | where | cost |
|---|---|---|
| pointer rule | resident, every session | 914 B |
| skill description | native listing (capped; competes for the ~30k budget) | 737 chars |
| skill body | paged, only on Skill invocation | 7,891 B; 0 loads observed in C |
| card | hook process; model-visible only when it denies | 0 tokens unless it fires; one deny per foreign set; non-commit calls return before I/O |

## What this does NOT prove
- Recall in the wild (n=2, one task shape); the false-positive rate (1 live deny, probably false).
- Behaviour on shapes K1 still leaves `unknown` (dynamic pathspecs, `--amend`, `--pathspec-from-file`,
  `GIT_INDEX_FILE`), where the card fails open.
- That the 914 B pointer contributes anything (no arm without it).
- Coverage outside git commits (e.g. publishing an index seeded earlier by another tool).

## Remaining failure modes
1. Card `unknown` -> fail open -> the skill/pointer are the only line, and arms N0/R/P say they do not deliver.
2. Tool-mediated own writes look foreign -> false deny (one extra turn, not a block: deny-once).
3. Native skill discovery misses (P 0/2): the skill is explanation, not protection.

## Verdict
SPLIT REPRESENTATION at **EXPERIMENTAL**: the deterministic card owns the invariant at commit time; the paged
skill stays as explanation and the procedure for the cases the card cannot judge; the pointer stays (Owner).
Not CANDIDATE: n=2, one false positive unexamined beyond a transcript read, no recall estimate in the wild.

## Rollback
`CLAUDE_DOCTRINE_CARDS=off` (card) or `ledger` (record only); full rule restore from
`~/.claude/backups/rules-20261003-090729/concurrent-writers-shared-tree.md`.

## Lineage
resident rule (until 2026-10-03 09:07) -> paged skill + pointer (move 4) -> + commit card ledger (C4)
-> + card deny (C4b 91cdc85e) -> pathspec resolution exact (K1 bf3d526a).

## Next evidence that would move it
Post-K1 live ledger over >= 1 week: unknown rate, deny count, each deny classified true/false from its
transcript; a fix or an explicit `unknown` for tool-mediated writes; a pointer-removal arm if the Owner wants it.
