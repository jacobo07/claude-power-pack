# Handoff [Q] -- technical capital accounting -> the campaign ledger

Pillar: [Q] technical capital accounting. Terminal: MERGED_INTO_EXISTING_OWNER (frozen rule: "CAPEX/OPEX
recorded per pillar in this ledger; no dashboard").

Owner (frozen): `vault/programs/cognitive-economy/ledger.json`.

## The accounting contract (applies to every pillar's `state.<P>`)

Each closed pillar carries a `capital` object beside `terminal`/`evidence`/`savings`:

```
"capital": {
  "capex": {"files_created": [...], "lines_added": N, "model_calls": "mission epoch share, not separately metered"},
  "opex":  {"recurring": "<what runs again and how often>", "gate_seconds": S, "model_calls_per_run": 0}
}
```

- CAPEX = what the campaign built once for the pillar (files, lines). Model spend is not split per pillar:
  `tools/usage_index.py` attributes calls to sessions, not to pillars, so a per-pillar token figure would be
  invented. It is stated as the mission epoch share instead of a number.
- OPEX = what keeps running: a gate that the done-gate re-runs, a scheduled task, a recurring human decision.
  Measured in seconds of wall time and model calls per run.
- A MERGED/DEFERRED pillar normally has CAPEX = its handoff file only and OPEX = 0 (the owner already pays it).

## Why no dashboard

The ledger is already the single committed authority the verifier reads. A second view would be a second
store to keep consistent, with no consumer that the ledger does not already serve.

## What the owner keeps

The ledger stays the campaign's authority; `frozen` is immutable, `state.<P>.capital` is written by the phase
that closes `<P>`.
