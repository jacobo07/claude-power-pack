# kClaude Startup + /restart Fix -- 2026-07-01

Status: **Shipped + verified** (all V-gates green, launcher mirrored to bin)
Mode: EXECUTION

## Three bugs (video-observed + conceptual)

1. **15s blank terminal** on kClaude launch.
2. **Blocking "Resumir? [S/n]" dialog** before claude starts, even with one session.
3. **/restart bypasses kclaude** -> Cognitive OS (CO-00/CO-08) inactive after restart.

## Root causes (measured, this host)

| Feature | Time | Launch-critical? |
|---|---|---|
| FAST bundle (W2 resume + W4 coord + CO-08 gate + known) | ~30 ms | YES |
| W1 turn_counter | ~1.3 s | advisory |
| **W5 cost_gate** | **17-27 s** | advisory (full-corpus 24h+7d scans via token_ground_truth.window_output) |

- **Bug 1:** cost_gate scans the whole transcript corpus every launch. prelaunch's
  1s timeout silently DROPS the advisory and, under GIL/cold-cache, fails to clip
  -> the 15s blank. Launch-critical work is only ~30ms.
- **Bug 2:** `kclaude.ps1` fired `Read-Host` on `coord.active` for BOTH single and
  multiple sessions; `coordinate()` already exposes `source` (active/multiple).
- **Bug 3:** the kclaude restart loop relaunched bare `& claude --resume` (skipping
  prelaunch); restart-claude.ps1's clipboard fallback targeted bare claude.

## Fixes

- **F1 (`modules/wrapper/prelaunch.py`):** added `--mode fast` (launch-critical
  only) and `--mode advisories` (W1/W5/parallel_burn -> detached, writes
  `~/.claude/cache/kclaude_advisories.json`). `run()` full mode kept for
  back-compat. Fast measured 163ms; advisories ~22s detached.
- **F1/F2 (`tools/kclaude.ps1`):** run `--mode fast`; print cached advisories +
  spawn detached refresh; SINGLE active session -> silent auto-resume; MULTIPLE ->
  numbered list with 3s timed default; honor explicit `--resume/--continue`;
  `-n/--new` escape hatch. Time-to-launch 333ms.
- **F3a (`tools/kclaude.ps1`):** restart loop re-runs the fast CO gates before
  relaunch -> CO-00/CO-08 active after every restart.
- **F3b (`~/.claude/scripts/restart-claude.ps1`):** clipboard fallback + resume
  target resolve the live `bin/kclaude.ps1` (then repo copy, then bare claude --
  fail-open).
- **Mirror:** copied `tools/kclaude.ps1` -> `~/.claude/bin/kclaude.ps1` (the file
  the Cursor kClaude profile actually runs; was out of sync).

## Verification (observed)

- `tools/test_wrapper.py` **21/21 x3** hermetic (added V-STARTUP-FAST-BUNDLE,
  V-FAST-NO-SCAN, V-ADVISORY-CACHE, V-SINGLE-SESSION-SILENT,
  V-MULTI-SESSION-PROMPT, V-NO-SESSION-SILENT).
- `tools/test_restart_and_lag.py` **17/17 x3** (added V-RESTART-VIA-KCLAUDE,
  V-RESTART-FAILOPEN).
- `tools/test_cognitive_os_build.py` **68/68** (no regression on `prelaunch.run`).
- restart-claude.ps1 dry-run: clipboard now launches `bin/kclaude.ps1 --resume <sid>`.
- Time-to-launch (full blocking path, no `& claude`): **333ms < 3s**.
- bin/kclaude.ps1 mirror IN SYNC; both live scripts parse clean.

## Seal

- UKDL: T-KCLAUDE-STARTUP-BLANK-001, T-W4-DIALOG-SINGLE-SESSION-001,
  HR-RESTART-VIA-KCLAUDE-001 + SCS C48 addendum v2 + SCS C63 addendum.
- `vault/knowledge_base/wrapper_kclaude_scs_c48.md` Addendum v2.

## Known / out of scope

- restart-claude.ps1 line 43 has a pre-existing `§` (non-ASCII) in a comment I did
  not touch -- unrelated to this fix, left as-is.
- HR-RESTART-VIA-KCLAUDE-001 recorded in UKDL; formal HARD_RULES.md sealing is via
  `tools/bug_to_hardrule.py` (digest + CLAUDE.md regen) if the Owner wants the
  inline-router mirror.
- Owner visual gate: click kClaude in Cursor, confirm prompt < 3s + no dialog.
