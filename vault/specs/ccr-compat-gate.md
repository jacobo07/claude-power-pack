---
covers: [ccr-compat-gate, ccr-compat-probe, ccr_compat_gate, COMPAT]
status: DRAFT 2026-10-17 (Owner "y" to "start with the version gate" after Unit Zero UZ2; the design below is mine and not yet reviewed)
tier: SDD T2 (new tool + versioned probe plugin + gate; no hook registration, no settings.json)
---

# CCR compat gate: detect an uncovered host version and re-measure it, never auto-widen

## Problem
`mods/cpp-cognitive-runtime/hooks/policy.ts` pins `COMPAT` to the Claude Code builds whose hook semantics were measured.
Any other build runs every mode as shadow. The host auto-updates: on 2026-10-16, 69 of 71 CCR session starts in 30 h ran on
2.1.299-2.1.301 with `compatible=false`, and on 2026-10-17 2.1.302 did the same. Recovery was manual and took four units
(UZ x3 and UZ2), because the probe did not exist, a release built from the wrong tree regressed the runtime, and a
spend-goal binding blocked the steward. The alert already exists (the status-line warning). The remedy was not repeatable.

## Existing owners (extend, never duplicate)
- `hooks/policy.ts` `COMPAT` and `register.ts` `compatible = COMPAT.includes(version)`: the pin and its reader.
- `tools/ccr_release.py release|rollback`: the only way a release is built. Nothing here replaces it.
- `vault/programs/ccr/unitzero/uz_probe_run.py` + `~/.claude/state/ccr/uz-probe`: the probe that passed 6/6 on 2.1.302 in UZ2.
  Both are uncommitted scratch; this spec makes them durable (versioned) under new names.

## Contract
1. `ccr_compat_gate.py check`: zero model calls. Resolves the host version (`claude --version`) and reads `COMPAT` from the
   ACTIVE release's `policy.ts` (the file the runtime really loads), not from a source tree.
   Verdict `COVERED` / `UNCOVERED` / `UNKNOWN`. An unreadable version or an unparseable policy is UNKNOWN, never COVERED.
   Exit 0 only for COVERED. It prints the active release id, the host version and the COMPAT list it read.
2. `ccr_compat_gate.py reprobe --confirm`: runs the probe (`tools/ccr_compat_probe.py`, plugin `mods/ccr-uz-probe`) on the host.
   It spends up to the probe guard (1,500,000 processed tokens, haiku), so it refuses to run without `--confirm`.
   It writes `vault/programs/ccr/compat/verdict-<version>.json` with the per-case verdicts, the host version and the active
   release id at probe time. It never edits `policy.ts` and never releases.
3. `ccr_compat_gate.py plan`: reads the verdict file for the CURRENT host version. Only when `all_required_pass` is true and
   its recorded host version equals `claude --version` now, it prints the exact steps to widen (edit line 8 in a source tree
   whose `policy.ts` and `register.ts` are identical to the active release except `COMPAT`, run the gates, `ccr_release.py
   release`, diff against the previous release). Otherwise it prints why it refuses. It changes nothing.
4. Required cases for a widen: S1b, S2, S3, S4. S5 may be PASS or INCONCLUSIVE and is named as a limit. INCONCLUSIVE is
   never PASS (a surface that did not fire proves nothing).

## Out of scope (Owner-gated or separate)
Auto-releasing; a scheduled task or a SessionStart hook that runs `check` (a hook registration returns to the Owner); editing
`settings.json`; spending tokens without `--confirm`.

## Done gate
`python tools/test_ccr_compat_gate.py` exit 0, V-COMPAT-* gates, each driven from both poles on real shapes:
`check` COVERED and UNCOVERED against the real policy.ts shape and a mutant that drops the version; UNKNOWN when the
version or policy is unreadable; `reprobe` refuses without `--confirm`; `plan` refuses a verdict for another version,
a failing verdict and an INCONCLUSIVE required case; and a mutant `plan` that ignores the version must turn the gate red.
Plus the driver selftest (`ccr_compat_probe.py --selftest`, 13 checks) and `claude plugin validate mods/ccr-uz-probe`.
