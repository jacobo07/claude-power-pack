---
title: Session Safety Global + Bulletproof — ULTRA PLAN
date_started: 2026-05-22
status: ACCEPTED — execution in progress
branch: feat/rtk-compressor-fusion (auto-mode call; Owner may re-route)
contract: SESSION_SAFETY_CONTRACT.md (BL-SESSION-SAFETY-001, sealed 2026-05-21)
sister_law: BL-2026-05-21 (Lazarus Stub-Canonical Race Vaccine)
---

# Session Safety Global + Bulletproof

## Objective

Any user with the Claude Power Pack installed never loses a session
involuntarily — both **durability** (the `.jsonl` survives on disk) and
**discoverability** (the user can find it via `/resume`). The contract
lives in the PP repo and ships through `install-global.ps1`.

## Grounding (PASO 0, 2026-05-22)

Verified empirically before planning. Findings:

1. **`mark-live-session.js`**: registered Stop[2] + SessionStart[8].
   Replaces `resume-hide-live.js` (.jsonl-rename cloak) with append-only
   `custom-title` marker. No `.jsonl.live` is produced by any active
   hook anymore.
2. **`lazarus-stub-recover.js`**: registered SessionStart, timeout 5 s,
   statusMessage "Lazarus stub recovery (vaccine BL-2026-05-21)". Active.
   FIX 4 is verify-only.
3. **Scheduled task for Layer-3 snapshot**: NONE on this host. The 367.7 MB
   ZIP from 2026-05-21 is one-shot. Layer 3 is aspirational, not implemented.
4. **`.recovered-*` files**: 3 present on disk (anomaly — 4 were renamed
   yesterday; 65537438 is missing — see PRE-2).
5. **`install-global.ps1` session-safety coverage**: ZERO. The Python core
   (`tools/install_global_core.py`) has no references to any safety asset.
   Today's host has the stack by historical accident; other users get the
   `SESSION_SAFETY_CONTRACT.md` Sacred-Invariant promise with no enforcement.

**Cross-document gaps**:
- `~/.claude/CLAUDE.md` has 0 matches for the contract (the claimed pin
  doesn't exist).
- `~/.claude/governance/GLOBAL_ALIGNMENT_LEDGER.md` has 0 matches.
- `knowledge_vault/core/apex-completion-standard.md` has 0 matches — session
  safety is not in the apex law.
- `session-file-guard.js` line 196 still names `resume-hide-live.js` in the
  user-visible BLOCK message.

## The 6 fixes (mapped to 19 Pasos)

| Fix | Concern | Pasos |
|-----|---------|-------|
| 1   | Contract truth (no stale lore in §3) | 1.1, 1.2 |
| 2   | Wire the promised CLAUDE.md pin       | 2.1     |
| 3   | Layer-3 snapshot automation           | 3.1, 3.2, 3.3 |
| 4   | Verify lazarus-stub-recover wiring    | 4.1     |
| 5   | Guard self-references current state   | 5.1     |
| 6   | Installer deploys safety stack         | 6.1–6.6 |

Plus PRE-1 (branch), PRE-2 (anomaly probe), V (clean-install crash matrix),
APEX-1 (apex standard update), LEARN-1 (iteration capture). Total = 19.

## Done-gates (one per Paso)

The clickable plan is in the conversation transcript — see the
"PLAN — Session Safety Global + Bulletproof (clickable)" emission of
2026-05-22. This file mirrors it; the canonical version is the chat for
provenance, this file is for grep-ability + post-run review.

## Execution order

Linear by dependency (contract → CLAUDE.md → guard → assets → installer →
snapshot → smoke → V → apex → learn). Each Paso = atomic + own micro-commit
+ empirical done-gate. Failure rollback = single `git revert`.

## Iteration loop

Per Owner template
(`Downloads/Promptsss/Prompts pa iterar/Universal/iteracion-avanzada-universal.txt`):
any done-gate failure → row in
`vault/knowledge_base/session_lessons.md` + cross-ref in `ukdl-universal.md`.
LEARN-1 enforces this.

## Branch posture

`feat/rtk-compressor-fusion` (current). Yesterday's `mark-live-session`
work commits are here (a4ec66b among others). The new session-safety work
builds on that foundation, so continuing here keeps the dependency chain
intact. Globalization (Paso V passing) is the trigger to either:
- (a) merge `feat/rtk-compressor-fusion` → main, OR
- (b) cherry-pick the session-safety commits + a4ec66b onto a fresh
      `feat/session-safety-global` off main.

Decided post-V, not now.

## Status log

| Date  | Paso | Result | Notes |
|-------|------|--------|-------|
| 05-22 | PRE-1 | DONE | auto-mode call: continue on feat/rtk-compressor-fusion |
