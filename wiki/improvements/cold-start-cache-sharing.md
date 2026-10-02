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
