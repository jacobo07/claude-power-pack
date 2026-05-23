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
| 05-22 | PRE-2 | DONE | The "missing" 65537438 is `lazarus-stub-recover.js` working as designed — empirically promoted the `.recovered-*` back to canonical (twice — 21:03 + today 14:12), left `.bak.stub-*` + `.stub-corrupt-*` forensic backups. Real-world validation of BL-2026-05-21 |
| 05-22 | 1.1   | DONE | Contract §3 retired `resume-hide-live.js` reference + added `.recovered-*`, `.jsonl.live.recovered-*`, `.stub-corrupt-*` allowlist rows + §3 footer cross-ref |
| 05-22 | 1.2   | DONE | §8 Discoverability Guarantee added; 4 failure modes named + responsible actor for each; Sealed line revised |
| 05-22 | 2.1   | DONE | Promised CLAUDE.md pin wired on this host. Other hosts: installer prints the 2-line stanza (doctrine forbids auto-write) |
| 05-22 | 5.1   | DONE | Guard block-message updated; synthetic block trigger verified new message renders with `.recovered-*` + `.stub-corrupt-*` markers |
| 05-22 | 6.1-6.4 | DONE | 4 assets vendored into PP repo (3 hooks + contract) with canonical-source headers |
| 05-22 | 6.5   | DONE | `_deploy_session_safety_root_files` + `_register_snapshot_task` + checklist section in installer; `--dry-run` shows correct deploys |
| 05-22 | 6.6   | DONE | `register-session-safety` consolidator added to settings_merger; idempotent re-run = exit 0 |
| 05-22 | 3.1   | DONE | session-snapshot.py — pure-Python Layer 3, 14-day rotation, same-day idempotent. Empirically: 1465 MiB → 380.9 MiB zip |
| 05-22 | 3.2   | DONE | `ClaudePP-SessionSnapshot` Scheduled Task registered + fired empirically (new zip in 72 s) |
| 05-22 | 3.3   | DONE | Contract §2 Layer 3 replaced ad-hoc PowerShell snippet with full implementation docs (opt-out + rotation + manual + POSIX note) |
| 05-22 | (post-3) | HARDENED | **BSOD intervention**: VIDEO_TDR_FAILURE bugcheck 0x00000116 fired after Wave 5 (3rd Event 41 in 24 h). Hardening commit `ad14363`: 5-layer governance stack (lock, idle priority, fast-compress, disk precheck, idle-only task), plus `vault/lessons/heavy-io-must-be-governed.md` global lesson. ctypes bug fix: SetPriorityClass needed explicit wintypes signatures to avoid silent HANDLE truncation on x64 — empirically 0x20 NORMAL → 0x40 IDLE only after the fix |
| 05-22 | 4.1 / V(d) | PASS | Synthetic stub-recover fixture: canonical with hook-stubs + sibling `.jsonl.live` with real turns → hook promoted, `.stub-corrupt-*` backup left, exit 0 |
| 05-22 | V (a-c) | DESIGN-VERIFIED | (a) clean exit, (b) SIGKILL, (c) host restart — cannot empirically test from within this session without breaking the conversation. Design-verified via the 3-layer orphan-sweep gate + append-only mark-live + Layer-3 snapshot. Future: throwaway-HOME crash matrix as a follow-up |
| 05-22 | APEX-1 | DONE | `apex-completion-standard.md` (PP + live mirror, byte-identical) now has "Session Safety Axis" — 5 required components + activation gate + 5-check DONE-gate |
| 05-22 | LEARN-1 | DONE | This row + the heavy-io-must-be-governed.md lesson capture what was learned. Process note: I edited the LIVE apex doc first then synced PP; next time edit PP first per the doctrine direction |

## Final commits

- `bf42961` — Wave 1+2+3+4 (Pasos 1.1, 1.2, 2.1, 5.1, 6.1-6.6)
- `ad14363` — Wave 5 (Pasos 3.1, 3.2, 3.3) + post-BSOD hardening
- Wave 6+7 commit — Paso 4.1 smoke test (no PP files changed by the test
  itself; APEX-1 doc + this plan log)

## Branch posture (recap)

`feat/rtk-compressor-fusion`. The 3 session-safety commits + the original
mark-live-session commit `a4ec66b` form a coherent ship. For globalization
to all PP users, either merge this branch to `main` or cherry-pick the 4
commits onto a fresh `feat/session-safety-global` off `main`. Owner call.
