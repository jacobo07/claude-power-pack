---
type: improvement
created: 2026-10-02
updated: 2026-10-02
sources: [2026-10-02-token-economy-external-research-2]
status: IDEA
effort: M
graduated_to:
---

# Let session starts read the prefix instead of writing it

## Problem (measured, 7 d)

- Main first calls write 85 % of their context fresh (mean 109k written, median 2,494 read);
  subagent first calls 91 %. Reading instead would cost ~$1,028 less, 12.4 % of est. spend
  (`wiki/tools/token_economy_coldstart.2026-10-02.out`).
- By directory: interactive project dirs read ~32k (tools + system prompt shared) and still write
  ~80-95k; worktree / mission dirs (~550 sessions) read only ~2.5k
  (`token_economy_coldstart_bydir.2026-10-02.out`).
- Tool definitions are identical across 673/673 same-dir session pairs within 1 h; system-prompt
  sections almost always too (`token_economy_prefix_stability.2026-10-02.out`). The break sits
  after the system prompt.

## Why it matters twice

Every rollover, every mission epoch and every subagent is a session start. Cheaper starts make
the context-cap and rollover levers cheaper too ([[token-economy-brainstorm]], A1, B4).

## Candidate mechanisms (documented, unverified here)

- `--exclude-dynamic-system-prompt-sections` moves per-user context into the first user message
  ("improves prompt-cache reuse"); present in CLI 2.1.288
  ([[2026-10-02-token-economy-external-research-2]]).
- Worktree / mission epochs: find what makes their system prompt differ after ~2.5k (hypothesis:
  per-epoch text appended to the system prompt) and move it to the first user message.
- Keep listings and instructions byte-stable between sessions (no per-session text before them).

## Proposed steps

1. Diff the recorded `prompt_snapshot` of two consecutive epochs in `wt_keosdtk_home` (zero quota).
2. Experiment (needs a small amount of quota, Owner go): two sessions per arm in one dir, one
   minute apart, with and without the flag; compare the second session's first-call cache read.
3. If the read rises, apply to the launchers that start most sessions (mission epochs first).

Owner: none for interactive starts; Ralph / `gsd_epoch` for mission epochs.

## Experiment result (2026-10-03, Owner approved the quota)

Six Haiku `-p` calls (`wiki/tools/cache_experiment.2026-10-03.out`):
- **Identical consecutive sessions share everything**: in a clean scratch repo the second session
  read 69,796 and wrote 0.
- **The flag is not the fix**: with `--exclude-dynamic-system-prompt-sections` the second session
  read 21.8k and wrote 48.8k (worse). Candidate 1 above is refuted for this setup.
- **In the PP repo the second identical session read 22k of ~88k.** The diff
  (`wiki/tools/token_economy_prefix_diff.py`, `.2026-10-03.out`) names the cause. The first
  pre-call items are SessionStart hook outputs, and they changed between two runs 45 s apart:
  - the superpowers plugin hook and the PP dispatcher finished in swapped order;
  - PP's text carries relative times and timestamps ("cache pulled 4.2h ago", Compound Learnings
    "Detected at", pending count);
  - the first-prompt JIT injection added a 3.4 KB project spec in one run only.
  All of it precedes the 172k-char instructions block and the listings, so one changed byte at
  the top rewrites everything after it.

n = 1 per arm; direction clear, magnitudes single observations.

## Revised proposal (PP-owned)

1. **Byte-stable SessionStart output**: no relative times, timestamps or counters in the injected
   text (move them to a file the agent reads on demand, or to a later turn).
2. **Deterministic order**: the two SessionStart hooks race; emit PP's block from one hook, or ask
   the Owner whether the plugin's SessionStart is needed.
3. **First-prompt injections stable**: the JIT spec injection should not differ between two
   sessions given the same prompt.
4. Re-run the same R1/R2 pair; success = R2 reads ≥ 80k.

Bound unchanged (≤ 12.4 %), now with a named, PP-owned cause.
