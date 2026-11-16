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

---
# OBSERVED on the laptop plane (coordinator pane 72497d57, 2026-11-16, worktree Apps\pp-bcap-verify @ a92635f6)

1. Taste Skill: INSTALLED (`~/.claude/skills/design-taste-frontend/SKILL.md` exists; description "Anti-slop frontend skill
   for landing pages..."). No hook or command references it. `~/.claude/settings.json` `skillOverrides` lists it as
   `"name-only"`, so the agent's skill list shows the bare name with no description. Verdict: REACHABLE by name, NOT
   AUTONOMOUSLY ACTIVATED (no trigger text reaches the model). This is the installed-but-not-activated discontinuity the
   campaign predicted.
2. ASTRYX: NOT FOUND in `~/.claude/knowledge_vault`, `vault/plans`, or `C:\Users\User\Downloads\Promptsss` (Grep, case-
   insensitive). Observer scope: those three roots only. The repo-wide vault Grep timed out earlier, so absence is
   NOT certified. It stays UNKNOWN (origin unknown).
3. B5 delivery, through the exact hook entrypoint (subprocess `python modules/gsd_x/cli.py`, raw JSON on stdin, as
   hooks/gsd_x_tier.js spawns it), prompt "Hazme una landing page para una academia de yoga, con hero, precios y formulario
   de contacto":
   - live tree 2f9386f6 -> `Family baseline web_surface/B4 (sha256 722d88c9a7ba)`, no legal-page rules;
   - this branch -> `Family baseline web_surface/B5 (sha256 c883b025c0df)`, first lines `web_surface-privacy-page-linked`,
     `web_surface-terms-page-linked`.
   The hook is live in this pane: its inherited block reached this session's own UserPromptSubmit context. Remaining
   after merge: one live-prompt observation.
   ! Instrument trap: piping the payload from PowerShell 5.1 prepends a UTF-8 BOM, `json.loads` fails, and cli.py
   records NO_PROMPT with empty stdout. That looks like "no delivery". Node's spawnSync sends no BOM.
   ! NOT autonomous: the family done-gate. No Stop hook or dispatcher entry runs `tools/family_baseline.py judge`. Only
   the `/family-done-gate` command and the block's instruction to the model reach it.
4. Laptop plane, branch a92635f6: `test_family_baselines.py` rc 3 (registry has 6 families, its predeclared list has 4)
   and `test_baseline_generations.py` 15/16 (V-BGEN-REAL-B0-CITATIONS-HOLD, 16 FILE_MISSING). They fail on Windows
   TOO, so "Linux-only" was wrong. Root cause: B0 `origin.file` cites `C:\Users\User\.claude\rules\<rule>.md`, and those
   rules moved to `~/.claude/skills/<rule>/SKILL.md` in the 2026-09-29..10-31 context diet (checked:
   destructive-state-authorization rules/ False, skills/ True). The branch only adds web_surface/B5.json, so this is
   pre-existing. `test_asc_baseline.py` 32/32 on the laptop.
   RESOLVED 2026-11-16 (pane 58263a19, Owner chose "New generations" and "predeclared subset of registry"):
   - re-cite generations written through `baselines.write_generation`: persistent_state B1 (14), wii_homebrew B1 (1),
     web_surface B6 (1). Only origin file/line moved; every quote was re-located verbatim; `verify_chain` ok, 0
     tampered, 0 regressions; each re-citation recorded in `changes` with reason and authority.
   - the planned Taste promotion is now **web_surface B7** (B6 is the re-citation).
   - V-FAMB / V-FINJ-POPULATION: INVALID only when a predeclared family is missing; later families are named as
     out of scope. V-TCHK-REAL-POPULATION was also stale since B5 (two evaluable regex checks read UNREADABLE on an
     empty root); its invariant is now "none reads PASS".
   - measured: family_baselines, family_injection, baseline_generations, tower_ratchet, tower_checks 23/23,
     tower_select, asc_baseline 32/32, taste_absorption: all rc 0.

## 5. Live merge + live wiring (DONE 2026-11-16, pane 58263a19, Owner "y")
- UKDL split: branch commit 99ccba19 restores `ukdl-universal.md` to 9a55747d bytes; the campaign section waits in
  `vault/knowledge_base/ukdl_pending/ascension-campaign1-2026-11-16.md` until the other pane's uncommitted edit to
  that file lands. Overlap with the live dirty set after the split: 0 of 74 files (2823 dirty paths incl. untracked).
- Live `feature/knowledge-acquisition` fast-forwarded 9a55747d -> 99ccba19 (rc 0); the dirty ukdl file untouched.
- `~/.claude/hooks/hook-dispatcher.js`: Stop-chain + family_donegate_stop.py, SessionStart-chain +
  backlog_ledger_refresh.js (backup `~/.claude/backups/bcap-live-20261116/`). `node --check` rc 0.
- `~/.claude/settings.json`: `design-taste-frontend` name-only override removed (133 overrides left, JSON parses).
- Observed through the LIVE dispatcher, private state dirs:
  - SessionStart-chain rc 0 in 1.4 s; the gate spawned a worker (free 4823 MB) -> gate row + lock.
  - Stop-chain rc 0 in 9.3 s; donegate ledger row `skipped` for a cwd outside web_surface (reach proven).
  - test_hook_registration_integrity 15/15 on the live install.
- ! The worker on the LIVE tree was still building after ~13 min (CPU 39 s, below-normal priority), against 118 s
  in the worktree. Within its 1 h lock; result unobserved at the time of writing.
- Still open: item 4 (web_surface B7 Taste promotion pair on GEX44). The `web_surface-taste-hard-bans` delta does
  not exist as data yet (only named in NOTICE.md / taste-absorption.json); `tools/asc_inherit_run.py` is hard-wired
  to the phase-5 deltas and output dir.
