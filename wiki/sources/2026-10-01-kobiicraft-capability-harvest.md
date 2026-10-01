---
type: source
created: 2026-10-01
updated: 2026-10-01
sources: [2026-10-01-kobiicraft-capability-harvest]
raw: raw/2026-10-01-kobiicraft-capability-harvest.md
kind: note
origin: read-only harvest subagent, 2026-10-01, ~84 tool calls; KobiiCraft Core Files @ 7f8f9d66
---

# KobiiCraft capability harvest (2026-10-01)

Source side of the maturity-transfer pilot ([[maturity-transfer]],
[[maturity-transfer-pilot-kobiicraft-ksr]]). 50 capabilities, KC-01..KC-50, harvested from code
and config. Each has a level, enabling traits, a portable form, and what is KobiiCraft-specific.

Per level: L1 1 · L2 10 · L3 8 · L4 12 · L5 6 · LG 13. L1 is thin on purpose: gameplay was sampled
for mechanism, not enumerated.

**Dominant pattern:** "an absent check must not read as a pass".
- An unmapped change fails (KC-02).
- An empty patrol selection is CANNOT_EVALUATE (KC-17).
- A restart is proven by uptime going backwards (KC-22).
- Gates fire on drift, not on existing debt (KC-24).
- CI fails if zero tests ran (KC-19).

## What I re-verified myself

- KC-27 invariants (atomic save, quarantine never regenerate): `scripts/network/world_persistence_gate.py:7-16`.
- KC-19 zero-tests tripwire: `.github/workflows/ci.yml:49`.
- The harvest's own finding that CI silently skips the absent praxis guard: `ci.yml:52-59`.

## Taken without re-checking

The other 47 capabilities' file:line evidence. These items stay DOC-ONLY per the harvest: the KIS
done-gate, K-ADOS, the wiring gates' behaviour and the runbooks. Test figures are file counts, not
pass counts.
