# ExecutionOS Lite -- Artifacts (FORENSIC Tier)

## Runtime Artifacts Table

| ID  | Artifact                  | Generated At     | Purpose                                  |
|-----|---------------------------|------------------|------------------------------------------|
| A01 | Intent Statement          | Phase 1          | Single-sentence goal for traceability     |
| A02 | Source Manifest            | Phase 2          | List of all files read with classification|
| A03 | Depth Routing Decision    | Phase 3          | Why this tier was selected                |
| A04 | Discovery Notes           | Phase 4          | Mental model, gaps, assumptions           |
| A05 | Task Plan                 | Phase 5          | Ordered task list with dependencies       |
| A06 | Scaffold Map              | Phase 6          | Files created, stubs, types defined       |
| A07 | Implementation Log        | Phase 7          | Per-task: what changed, why, verification |
| A08 | Integration Checklist     | Phase 8          | Wire points verified, imports confirmed   |
| A09 | Test Report               | Phase 9          | Tests run, pass/fail, coverage            |
| A10 | Review Findings           | Phase 10         | Issues found during self-review + E11 path audit |
| A11 | Validation Gate Results   | Phase 11         | Each gate: pass/fail/skipped + reason     |
| A12 | Security Scan             | Phase 12         | Vulnerabilities found, mitigations        |
| A13 | Performance Assessment    | Phase 13         | Bottlenecks identified, optimizations     |
| A14 | Deviation Log             | Any phase        | Rule applied, what changed, why           |
| A15 | Session Summary           | Phase 20         | Final status, open items, handoff notes   |

## Artifact Rules

1. **FORENSIC tier only** -- Artifacts A01-A15 are generated only at FORENSIC depth. Lower tiers may generate A01 (Intent) and A14 (Deviations) if useful.
2. **Structured format** -- Each artifact is a markdown section with: ID, timestamp, content, linked phase.
3. **Append-only** -- Artifacts are never modified after creation. Corrections are new entries referencing the original.
4. **Session-scoped** -- Artifacts live for one session. Persistent learnings go to MEMORY.md or project docs.
5. **On-demand** -- Artifacts are generated when their phase executes, not preemptively.
6. **Traceability chain** -- A01 (intent) links to A05 (plan) links to A07 (implementation) links to A11 (validation). Any output traces back to intent.
7. **Deviation artifacts (A14)** -- Created whenever a deviation rule (1-4) fires. Format: `[Rule N] Phase X: description, impact, resolution`.
8. **Minimal overhead** -- If an artifact would be empty (no findings, no deviations), skip it. Do not create placeholder artifacts.
