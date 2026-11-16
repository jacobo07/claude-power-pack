# LAPTOP_STEPS: ascension

(numbered, copy-pasteable laptop-plane steps; each marked BLOCKED-ON-LAPTOP)

## 1. Taste Skill reachability (BLOCKED-ON-LAPTOP)
Phase 1 saw `design-taste-frontend` only as a name in skill keep-lists (REFERENCED_ELSEWHERE), with no backlog/plan source on GEX44.
Whether it is installed, reachable and consumed is a laptop-plane fact. Run on the laptop:
`ls ~/.claude/skills/design-taste-frontend/SKILL.md && grep -rl "design-taste-frontend" ~/.claude/hooks ~/.claude/commands ~/.claude/settings.json`
Record the output here as OBSERVED (laptop). Until then it stays UNKNOWN, not AVAILABLE.

## 2. Meta ASTRYX source (BLOCKED-ON-LAPTOP, origin unknown)
`astryx` appears on GEX44 only inside the campaign plan (NOT_OBSERVED elsewhere). If the Owner's backlog entry lives in a laptop-only
file, find it: `grep -rli astryx "<laptop repo>/vault" ~/.claude/knowledge_vault`. Absence on GEX44 is not absence on the laptop.

## 3. Live delivery of web_surface B5 (BLOCKED-ON-LAPTOP / coordinator)
The live hook path reads the live `~/.claude/skills/claude-power-pack` tree, which has no `vault/tower/baselines/web_surface/B5.json` until branch `mission/ascension-run` is merged and synced. After that: run `python3 tools/test_asc_baseline.py` and then a real prompt "build a landing page" through the live hook and confirm the block says `web_surface/B5`. Until then delivery is proven only through `gsd_x.cli.family_block` with the worktree root.

## 4. Pre-existing Linux failures not caused by this campaign (informational)
`tools/test_family_baselines.py` (rc 3) and `tools/test_baseline_generations.py` V-BGEN-REAL-B0-CITATIONS-HOLD (Windows-path citations FILE_MISSING on Linux) fail identically with B5 removed. Verify on the laptop plane.
