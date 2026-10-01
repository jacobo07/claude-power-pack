---
type: component
created: 2026-10-01
updated: 2026-10-01
sources: [2026-10-01-cbr-internal-inventory]
path: modules/tower/, tools/family_baseline.py, vault/tower/, modules/gsd_x/cli.py
status: LIVE
---

# Constitutive Baseline Ratchet (CBR, "Torre Universal")

Per-family rules that a new instance of that family is incomplete without. They are meant to be
applied without being asked, and to rise as projects teach PP something. Specs:
`docs/superpowers/specs/2026-09-23-torre-universal-persistent-state-design.md` (mother) and
`2026-09-24-family-baselines-design.md` (family slice S1-S6). Families: `web_surface`,
`kobiicraft_mode`, `persistent_state`, `wii_homebrew` (`vault/tower/families/`).

Not to be confused with `modules/sqi/ratchet.py` (SQI baseline ratchet) or the Mission Baseline
Capsule, which shares this module and is described in [[cbr-gap-analysis]].

## How it reaches the agent (LIVE)

`settings.json:601` UserPromptSubmit-chain → `hooks/hook-dispatcher.js:552` → `hooks/gsd_x_tier.js`
→ `modules/gsd_x/cli.py::family_block` (`:99-153`) → `additionalContext`. The rules are chosen by
prompt vocabulary (`modules/tower/families.py::classify_prompt`). At most 8 entries / 1,400
characters per family, up to 3 offers per session per family. Kill switch `CPP_FAMILY_BASELINES=off`
([[2026-10-01-cbr-internal-inventory]] §5).

Observed: 35 injections in 20 real sessions, 2026-09-30 → 2026-10-01
(`~/.claude/state/tower/consumption.jsonl`).

## Capability status @ 298975d

| capability | status |
|---|---|
| Family classification from the prompt | LIVE (vocabulary only) |
| Family membership of a repo (`repo_families`) | PLANNED (no production caller) |
| B0 generations, 4 × 15 entries, SHA-stamped injection | LIVE |
| Machine-checkable entries | ABSENT (0 of 60; grammar exists in `checks.py`) |
| Anti-downgrade chain check (`ratchet.verify_chain`) | PLANNED (CLI + tests; ORPHAN per liveness) |
| Review / revert | LIVE via CLI only (`tools/family_baseline.py`) |
| Auto-promotion of lessons into `B<n+1>` | ABSENT (`promote()` has no caller; no B1 exists) |
| Done-gate APPLIED / NOT-APPLICABLE (`donegate.judge`) | PLANNED (report-only, ORPHAN) |
| Telemetry beyond "offered" | ABSENT |
| Lift / Tower Score / CRR / RFR | ABSENT (O0 sealed, no O1) |

Gaps, verified defects, the full-potential path and ranked fixes: [[cbr-gap-analysis]].
