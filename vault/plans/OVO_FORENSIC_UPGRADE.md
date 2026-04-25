# OVO Forensic Upgrade Plan (MC-OVO-100..105)

**Owner:** kobig · **Started:** 2026-04-25 · **Status:** MC-OVO-100..104 in flight this session

## Goal

Close the 70% gap between "OVO emits A on a clean delta" and "a Hypixel/Nintendo SRE would approve this deploy in one shot". The OVO meta-audit identified 3 missing mental models:

1. **RLP** — Runtime Liveness Probe: knows the difference between "process running" and "process processing work".
2. **AFHL** — Anti-Fragility Hack Ledger: tracks every non-canonical stabilizer (NMS reflection, native shims, monkey-patches) and forces re-validation when its upstream changes.
3. **CGAR** — Cascade Graph + Adversarial Replay: models blast radius of a delta and replays real production inputs against the post-delta sandbox.

This plan ships the **foundation** for all three. Adversarial-replay execution is deferred (needs real production logs + sandbox runtime — multi-session subsystem).

## Reality Contract — what ships this session vs what's deferred

| MC | Title | This session? | Reason |
|----|-------|---------------|--------|
| MC-OVO-100 | Plan + 3 schema docs | ✅ ship | Pure paperwork, no external deps |
| MC-OVO-101 | `tools/forensic_probes.py` (RLP/AFHL/CGAR probe lib + CLI) | ✅ ship | Self-contained; NOT_CONFIGURED mode never fakes PASS |
| MC-OVO-102 | Tests + initial empty AFHL ledger | ✅ ship | Real fixtures, not mocks |
| MC-OVO-103 | Cascade graph schema v2 (blast_radius) + `tools/cascade_query.py` | ✅ ship (foundation only) | v1 graph is empty in the repo; v2 schema + reader land here, populator deferred |
| MC-OVO-104 | OVO protocol doc update + Mistake #53 | ✅ ship | Doc work that wires the probes into the agent's Phase B mental model |
| MC-OVO-105 | Verify + OVO-audit + push | ✅ ship | Required to honor zero-issue gate |
| **CGAR adversarial replay execution** | Sandbox replay of last-N production events | ❌ **DEFERRED** | Needs: (a) production event log, (b) sandbox runtime, (c) diff-comparison harness. Multi-session work. |
| **MC-OVO-104 (v9000) "Design Quality Ingestion"** (shanraisshan) | UI design tokens absorption | ❌ **BLOCKED** | Same blocker as MC-ABS-3 — no repo URL, no token files. |
| **MC-OVO-105 (v9000) "Global Baseline Elevation"** (VPS sync) | Push these protocols to VPS knowledge vault | ❌ **DEFERRED** | Premature — sync protocol itself is undesigned (per ROADMAP.md MC-OVO-34 piece 3). Builds on these foundations, not gates them. |
| **CGAR cascade graph populator** | Walk the codebase and populate event_to_listeners / event_to_publishers | ❌ DEFERRED | Stack-specific (Java reflection vs Python AST vs JS regex). Schema lands; populators are per-stack work. |

## What "honest probe" means

For each probe, three states are valid emissions; none of them fakes a PASS:

| State | When | Effect on verdict |
|-------|------|-------------------|
| `CONFIGURED` + clean | probe artifacts exist for project, no findings | no verdict cap |
| `CONFIGURED` + findings[] | artifacts exist, findings detected | verdict ≤ **B** unless findings addressed in same response |
| `NOT_CONFIGURED` | project hasn't opted into this probe | advisory note in Council block; no verdict cap, but no PASS claim from this probe |

The `NOT_CONFIGURED` state is the anti-scaffold guard. A project that has not implemented a probe gets a clear marker — never a silent "✅ probe passed" emission.

## Probe contracts (summary)

Detailed schemas in:
- `vault/forensic/RLP_SCHEMA.md` — `_audit_cache/runtime_probe.jsonl` per project
- `vault/forensic/AFHL_SCHEMA.md` — `vault/anti_fragility/hacks.jsonl` per project
- `vault/forensic/CGAR_SCHEMA.md` — `vault/audits/cascade_graph.json` v2

Per-project opt-in: a project signals "I want this probe enforced" by writing the artifact file. Power-Pack itself is not a daemon and has no production event log — it will run RLP and CGAR replay in `NOT_CONFIGURED` mode (correct, not a defect).

## Anti-pattern guard (Mistake #53)

Once the probe library lands, agents running OVO Phase B at FORENSIC tier MUST invoke `forensic_probes.py --probe all` and consult the JSON before grading. Skipping the probe at FORENSIC tier is logged as **Mistake #53 (Forensic Probe Skipped)** and caps the verdict at **B**. Below FORENSIC tier the probes are advisory.

## Out of scope for this session (and why)

- **Hardware-layer profiling (eBPF, perf, vtune)** — these are tool integrations not mental models; they need OS-level support that the power-pack-as-skill cannot bundle. They belong in a separate subsystem ("Subsystem T — Telemetry", future planning).
- **OmniCapture wire-up** — the meta-audit noted that OmniCapture exists and could feed RLP. That integration is real future work but requires API key management + per-project routing config — separate session.
- **Auto-ingest of cascade_graph.json** — populating the graph from source requires a stack-specific walker (Java reflection vs Python AST vs Go importer). The schema lands; populators are out of this batch.

## Gate criteria for this session

Each MC ends "done" only when:
- Tests written + green
- CLI smoke run captured
- No `TODO:`/`FIXME:`/`Coming Soon` in runtime code
- Council verdict ≥ A on the cumulative batch before push
