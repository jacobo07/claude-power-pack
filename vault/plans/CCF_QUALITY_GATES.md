# CCF Production Quality Gates — Phase 5

> Per-stage gates (not just at release), plus the release-wide Production Reality Gate. The
> critical addition this phase specifies is `TRADEMARK_COLLISION_GATE`, derived directly from
> CCF-F01 — everything else follows the CCF's own Phase 6 template from the original spec, scoped
> down to the 8 components actually specified in `CCF_ARCHITECTURE.md`.

## Per-stage gates

| Stage (component) | Gate | Pass condition | Fail behavior |
|---|---|---|---|
| Creative Contract Engine (#1) | `CONTRACT_RESOLVED` | No blocking ambiguity remains in the Creative Specification | `cpp creative compile` exits `3`, halts pipeline until re-run with answers |
| Config-Driven Pipeline (#2) | `CONFIG_VALID` | Every concept entry has required fields (font, colours, bg, wordmark, `avoid`, icon description, `icon_direction`) | Refuses to fan out; lists missing fields per concept |
| Prompt Compiler (#3) | `PROMPT_ASSEMBLED` | Prompt non-empty, `avoid_list.named` and `avoid_list.semantic` both populated (semantic list must never be empty — an empty semantic list is itself a defect signal, not a clean pass, since every icon description has *some* shape category) | Concept marked `unschedulable`, excluded from generation with reason recorded |
| Model Adapter Layer (#4) | `GENERATION_SUCCEEDED` | `ImageArtifact` returned, resolution/format match request | `ProviderError` recorded; concept marked failed, pipeline continues for remaining concepts (per CLI spec exit-code `5` behavior) |
| **Trademark Collision Scanner (#7)** | **`TRADEMARK_COLLISION_GATE`** | See dedicated section below | See dedicated section below |
| Artifact Compiler (#5) | `ARTIFACT_NONEMPTY` | The direct, mandatory fix for CCF-F02: before building any PDF, confirm at least one non-BLOCKed `ImageArtifact` exists for that entry | Entry skipped, structured warning emitted (`{entry_id, reason: "no_generated_images", skipped: true}`) — never a silent near-empty PDF |
| Creative Evaluation Engine (#6) | `OBJECTIVE_CHECKS_PASSED` | Wordmark spelling correct, named `avoid` absent, resolution/format correct, PDF page count/size within bounds | Package still written for inspection but marked non-release-eligible (`package` CLI exit `7`) |
| Release Manager (#8) | `PRODUCTION_REALITY_GATE` | See below | Release refused |

## TRADEMARK_COLLISION_GATE (the gate this failure demanded)

- **BLOCK verdict on any concept:** that concept is hard-excluded from the showcase and from any
  future package — it cannot be re-included by re-running `select` on it; it requires a
  respecified concept (new icon description, explicit named ban added) and a fresh `generate`
  pass, exactly as the reference-repo creator actually did after discovering the Airbnb collision.
- **WARN verdict:** the concept may proceed to showcase inclusion **only** with an explicit human
  acknowledgment recorded (`human_ack: {by, timestamp, reasoning}`) in the human_gate_queue —
  never a default-allow. The acknowledgment is itself provenance: if a WARN-then-shipped concept
  is later found to be a real collision, the record shows who accepted the risk and why, rather
  than the tool having silently let it through.
- **PASS verdict:** proceeds normally, but still logged with `corpus_version` so a later corpus
  update can retroactively flag it (`cpp creative audit` re-scan path).
- **Release-wide rule:** the Release Manager (#8) refuses release if **any** artifact in the
  package carries a BLOCK, or a WARN with no recorded human acknowledgment. This is the one gate
  with zero silent-pass paths anywhere in the architecture — a direct, structural response to the
  fact that the founding failure was caught by luck (a human happened to notice), not by a gate.

## Production Reality Gate (release-wide, adapted from the original CCF spec to the 8 real components)

| Check | Verified by |
|---|---|
| `artifact_integrity` | Release Manager — every artifact hash-verified via `done_gate` pattern |
| `traceability` | Every artifact links to its compiled prompt and Model Adapter call record |
| `provenance` | DAIF-21 chain complete: brief → contract → concept configs → prompts → model calls → scanner verdicts → human approvals → package |
| `qa_passed` | All `OBJECTIVE_CHECKS_PASSED` gates green across every included artifact |
| `evaluation_complete` | Human concept-selection recorded (`selection.json` exists and references a non-BLOCKed concept) |
| `consistency` | Recolor variants (on-white/on-green/mono) derive from the same SVG `<symbol>` source, not independently regenerated — checked structurally, not visually |
| `completeness` | Every contract-declared output present (showcase PDF + brandkit PDF + evaluation report + scan report) |
| `provider_metadata` | Model id, params, cost, latency recorded for every generation call |
| `trademark_cleared` | Zero un-acknowledged BLOCK or WARN anywhere in the package — restates `TRADEMARK_COLLISION_GATE` at the release layer as a final belt-and-braces check |
| `production_ready` | Correct output formats for real use (A4 print-ready PDF, correctly-sized PNG/SVG where applicable) |

## What this phase deliberately does not gate

No gate exists yet for vectorization quality, provider-fallback success, or parallel-generation
throughput — consistent with `CCF_KNOWLEDGE_SYSTEMS.md`'s non-goals: gating a capability that
doesn't exist in v1 would be theater, not quality control. When those capabilities ship, their
gates are specified alongside them, not stubbed in now.
