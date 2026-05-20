# Ultra Plan — Context Watchdog Tier-2 Zero-Keystroke Auto-Compact

Origin: video instruction `Downloads/20260520_152847.mp4` (whisper `base`
transcript, 118 s). Owner decisions locked 2026-05-20 via Q&A:
**1c** SendKeys default + 1-keystroke fallback ·
**2a** kclear → compact (save then free) ·
**3a** exact /kclear v3 fields ·
**4a** 60% warn / 70% auto ·
**5a** global, every pane/project ·
**6a** empirical `_TEST_CONTEXT_PCT=70` evidence.

## The order (audio literal)

At 60 % warn; at 70 % AUTO-execute `/compact` AND save important info to the
knowledge vault first; session continues from where it was. "Yo no estoy en
casa" = zero-keystroke when Cursor focused, honest 1-keystroke fallback
otherwise (per BL-0003, hooks can NOT directly auto-fire slash commands).

## Verified state (No Guessing — grounded 2026-05-20)

- `modules/zero-crash/hooks/context-watchdog.py` ALREADY implements Tier 1
  (60 %) + Tier 2 (70 %) per BL-0033. Tier 2 returns `decision:"block" +
  reason` which re-invokes the model with the message as injected context.
  Missing vs the audio: (a) no `/kclear`-equivalent vault write, (b) still
  1-keystroke.
- `~/.claude/CLAUDE.md` is at exactly 100 lines (cap). Updating Context
  Pressure Response paragraph requires REPLACING line 73, not appending.
- `apex-completion-standard.md` byte-identical PP vs global (sha 3e23ed8d).
  Adding the new "Context Pressure Standard" section must write identical
  bytes to BOTH copies (Zero-Drift Mirror Completion Law from 2026-05-16).
- BL-0003 cited in CLAUDE.md:73 AND watchdog:201-204. Bypass = SendKeys
  out-of-band, same precedent as `/restart` Path 2 (already approved).

## Plan (6 micro-batched steps, scope-bounded)

| # | File | Action | Verification |
|---|------|--------|--------------|
| **0** | `vault/plans/context-watchdog-tier2-2026-05-20.md` | this file | exists |
| **1** | `modules/zero-crash/hooks/context-watchdog.py` | edit: add `_kclear_equivalent()` (mechanical extraction, no LLM) + `_TEST_CONTEXT_PCT` env override + trigger flag write; call from Tier 2 BEFORE the message | synth `_TEST_CONTEXT_PCT=70` payload → vault files written + flag created |
| **2** | `~/.claude/hooks/auto-compact-sendkeys-daemon.ps1` (new) | detached PS daemon: poll `~/.claude/hooks/auto-compact-trigger.flag`, SendKeys Enter to focused Cursor pane when present, demote to `auto-compact-pending.flag` if Cursor not focused | manual test: drop flag, daemon detects <2 s |
| **3** | `~/.claude/settings.json` (via `settings_merger.py`) | wire daemon: SessionStart (clear stale flags) — Stop daemon spawn is INSIDE the watchdog itself; settings wiring is the SessionStart cleanup hook | bounded-diff +1 per event, JSON valid |
| **4** | `~/.claude/CLAUDE.md` | edit: REPLACE Context Pressure Response paragraph in-place (≤ 100-line cap) | line count ≤ 100 |
| **5** | empirical | `_TEST_CONTEXT_PCT=70` synth Stop payload → assert handoff.md + session_lessons.md append + insights.json + telemetry written + trigger flag exists | all 5 artifacts present with timestamps post-trigger |
| **6** | `session_lessons.md` + `apex-completion-standard.md` (BOTH global+PP, byte-identical) | snowball + new "Context Pressure Standard" apex section | apex sha equal on both sides post-write |

## Kclear-equivalent contract (Tier 2, mechanical, no LLM)

The watchdog is a Python Stop hook → no LLM call possible. The structural
checkpoint it writes contains:

- `summary` ≤ 400 chars: first sentence / line of the last assistant message
  in the transcript (or a default if transcript unreadable).
- `pending` ≤ 5: text of the last 5 user prompts (each ≤ 200 chars).
- `insights` += 1 entry: tier-2 checkpoint metadata.
- `lesson`: omitted (real lessons need LLM judgement; the field stays empty
  rather than padded with fluff — `kclear.md` says "empty list > padded").

Atomic writes via `lib/atomic_write.py` to:
- `<cwd>/memory/project_session_handoff.md` (replace)
- `<cwd>/vault/knowledge_base/session_lessons.md` (append)
- `<cwd>/_audit_cache/insights.json` (update)
- `<cwd>/vault/telemetry/context_watchdog/<ts>_<sid8>.json` (replace, empirical evidence per Owner DONE gate)
- `~/.claude/hooks/auto-compact-trigger.flag` (replace, daemon signal)

## Reality Contract (sealed)

Zero placeholders. Mechanical extraction is honest "kclear-equivalent under
hook constraints" — NOT a fake LLM summary. SendKeys path falls back to
1-keystroke when Cursor not focused, documented loudly (not silenced).
Empirical `_TEST_CONTEXT_PCT=70` test must produce all 5 artifacts on disk
or the system is NOT done.

## Out of scope (honest)

A true LLM-quality kclear summary inside a Stop hook (impossible — hooks
cannot call the model). User can still run a manual `/kclear` to get the
semantic summary; the auto-checkpoint guarantees a structural floor.
Hook input format change requires harness changes outside our scope.
