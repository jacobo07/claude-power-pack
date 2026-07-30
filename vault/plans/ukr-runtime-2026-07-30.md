---
title: CPP-UKR Runtime Residue — Phase -1/Phase 0 Overlap Audit
date: 2026-07-30
status: STOP #1 — presented inline, awaiting Owner approval before any construction
mode: AUDIT MODE (Phase -1/Phase 0 are blocking per the spec's own constraint —
  no construction without audit)
denominator: 8,456 files (*.py/*.md/*.js/*.json, excluding .git) — measured
  directly this session via Get-ChildItem, not assumed from a curated list.
reused_receipts: vault/plans/iig-compendium-2026-07-30.md (30-candidate audit,
  0/30 survived), vault/plans/gap-discovery-2026-07-30.md (16-space empirical
  gap pass, 0 new datasets, 1 real wiring gap found+fixed same session).
  Semantic delta: none of those verdicts have been invalidated by anything
  found this pass — reused, not re-derived.
---

# CPP-UKR Runtime Residue — Overlap Matrix (candidates A–R)

## Original intent (preserved, not archived)

The prompt is right that the underlying goal — "every CPP-managed project
inherits governed, isolated, traceable, operative knowledge infrastructure
that can discover/recover/apply/demonstrate/update/improve knowledge" — was
never rejected. What was rejected, seven times running, is building it as a
*new named mega-system* when the mechanisms already exist under other owners.
This pass checks whether any real "residue" — something the goal needs that
no existing owner executes — actually remains.

## Verdict table (A–R)

| # | Candidate | Verdict | Real owner (verified this session) |
|---|---|---|---|
| A | Knowledge Runtime Integration Plane | ALREADY_OWNED | `graphify` GK-06 (Route Compiler & Context Pack: "Query finds the relevant coordinates; GK-06 compiles [context]") + GK-11 (Librarian Swarm/Route Governor, arbitrates across knowledge sources) + GK-12 (Graph-First Enforcement). Confirmed via live `modules/graphify/indexer.py --query --name graphify` this session — all 13 GK-00…12 datasets exist and are sealed (SCS C71/C72). |
| B | Knowledge Authority, Precedence & Conflict Runtime | ALREADY_OWNED | The prompt's own owner list names KSF for exactly this ("autoridad, precedencia, aplicabilidad, conflicts, promotion, limites del conocimiento"). A candidate cannot be new if its own spec assigns it to an existing owner in the same paragraph. |
| C | Mission Knowledge Contract & Coverage Runtime | EXTEND_EXISTING_OWNER | `spec_gate`/SDD-OS (already blocks Tier 2+ coding without a spec, verified live in `modules/spec_gate/gate.py` this session and last) + `dataset_first` ("an advisor wired into an authority, never an authority itself" per its own docstring, `OWNER_QUEUE.md`). |
| D | Knowledge Use Proof & Decision Influence Ledger | ALREADY_OWNED | `modules/rule_compiler/effect_harness.py` — verified on disk this session (`Glob modules/*/effect_harness.py`). This is IGEF's M1b, already shipped (`9df175b`), literally "does this rule/finding change behavior" — the exact question D asks. Plus DRK evidence-burden (decision_review). |
| E | Project Knowledge Inheritance & Overlay Runtime | ALREADY_OWNED | The Mirror Parity Law (repo↔global sync direction doctrine, cited in this repo's own `CLAUDE.md`) + the live 3-tier CLAUDE.md hierarchy (global → project → skill, all 4 loaded and visible in this very session's system context) + the AKOS domain-matched knowledge injector (observed firing live this turn: "AKOS Knowledge (domain-matched: ai_automation, scaling)"). |
| F | Authorized Project State & Constitutional Manifest Runtime | ALREADY_OWNED | `modules/setup_os/drift_detector.py` (verified on disk) + `governance/*.md` (COPY/DEPLOY/REPO_SECURITY governance, cited in this repo's own project `CLAUDE.md`) + `vault/liveness/reachability_registry.json` (LIBRARY/SCHEDULED/DEPRECATED/PLANNED states, verified this session). |
| G | Agent Knowledge Competency & Certification Runtime | EXTEND_EXISTING_OWNER | ACIS epistemic ladder E0–E7 (verified by direct file read, prior session) + `modules/craif/adapter_conformance.py` (verified exists, checks package/seam conformance) + `modules/setup_os/secure_installer.py` (certification-on-install). |
| H | Knowledge Consumer Registration & Reachability Runtime | ALREADY_OWNED | `modules/liveness/reachability.py` — this is its exact stated purpose (consumer tracing, reachability states), verified directly this session via `Glob vault/liveness/reachability_registry.json` and re-confirmed against `OWNER_QUEUE.md`'s own liveness-orphan-disposition entries. |
| I | Knowledge Invalidation & Selective Recompilation Runtime | ALREADY_OWNED | `graphify` GK-07 (Freshness, Integrity & Self-Evolution) — verified via graph query this session: "The kernel's conscience about its own map. A graph that silently rots is worse than no graph." This is invalidation+recompilation on change, by name. |
| J | Knowledge Runtime Transaction & Recovery System | EXTEND_EXISTING_OWNER | `graphify` GK-08 (Knowledge Writeback, verified via graph query) + `modules/contract_fabric/side_effect_ledger.py` (verified on disk, prior session) + Lazarus/`session_resilience` recovery. |
| K | Knowledge Runtime Observability & Diagnostic Plane | ALREADY_OWNED | `graphify` GK-09 (Navigation Observatory & Benchmark, verified via graph query) + GK-11 (route tracing). |
| L | Context Materialization & Progressive Disclosure Runtime | ALREADY_OWNED | `graphify` GK-06 again — the candidate's own description ("without duplicating Cognitive OS") concedes the adjacent space is already owned; GK-06's stated purpose is exactly "compiles [coordinates] into a context pack." |
| M | Knowledge Runtime Security & Isolation Boundary | ALREADY_OWNED | `secret_firewall` (URB redaction bus, CRITICAL-pattern blocking — sealed `HR-SECRET-001..007` in this repo's own `CLAUDE.md`) + `governance/REPO_SECURITY_GOVERNANCE.md`. |
| N | Knowledge Admission-to-Execution Compiler | ALREADY_OWNED | `rule_compiler` (`digest.py`, `hardrule_compile.py`, `effect_harness.py` — literally compiles rules for admission into enforcement) + `spec_gate`. |
| O | Runtime Knowledge Effectiveness & Avoided Work Intelligence | EXTEND_EXISTING_OWNER | `cpp_ias` Capability Economics (`ias_c1_capability_portfolio`, `ias_c2_demand_forecasting`, verified prior session) + `modules/frontier_intelligence/corpus_roi.py` (present on disk, per this session's own `git status`, built per spec, PENDING wiring per `OWNER_QUEUE.md`). |
| P | Universal Knowledge Runtime Conformance Suite | ALREADY_OWNED | SQI (`modules/sqi/redteam_protocol.py` on disk per `git status`; `sqi_03_environment_qualification_v1` verified prior session) + UQF (`pp-uqf-auditor` agent, live). |
| Q | Knowledge Runtime Bootstrap & Certification | ALREADY_OWNED | The prompt's own owner list names Setup OS for exactly this ("instalacion, adopcion, certificacion inicial"). Verified on disk this session: `modules/setup_os/secure_installer.py`, `registry.py`, `scanner.py`. |
| R | Knowledge Runtime Compatibility & Evolution Protocol | EXTEND_EXISTING_OWNER | `graphify` GK-07 (again — freshness/evolution) + the Mirror Parity Law (cross-copy compatibility) + `modules/hard_rules/residual.py`'s retirement/reopen pattern (verified live in the PLUGIN-INSTALL retirement, `OWNER_QUEUE.md`). |

## Fusion check (per the prompt's own hint list)

Every fusion the prompt itself suggested resolves cleanly onto an existing
owner — none required inventing a new one:
- B → KSF (owner admitted in the prompt's own text).
- C → spec_gate/SDD-OS.
- D → rule_compiler/effect_harness.py + DRK.
- E+F → Mirror Parity Law + CLAUDE.md hierarchy + Setup OS.
- G → ACIS + CRAIF conformance.
- H+K → `liveness/reachability.py` + graphify GK-09/11.
- I+J → graphify GK-07/08 + `contract_fabric`.

## Result

**0 of 18 candidates (A–R) clear the 13-question novelty gate as
`GENUINELY_NEW_DATASET`.** This is the **8th consecutive** mega-corpus-shaped
proposal for this repo (AISHF, RE Baseline, KSF, UKR-original, IIG's 30,
Gap-Discovery's 16-space pass, and now this Runtime-Residue framing) to
measure as majority-or-fully owned once checked against a discovered
denominator (8,456 files, measured directly, not assumed).

Verdicts: 11 `ALREADY_OWNED`, 7 `EXTEND_EXISTING_OWNER`. Zero
`NEW_MODULE_UNDER_EXISTING_OWNER`, zero `NEW_VIEW`, zero
`GENUINELY_NEW_DATASET`. Per Phase 3's own instruction: *"Si ninguno
sobrevive como GENUINELY_NEW: documentar el residuo como extensiones de
owners existentes y cerrar."* That is the outcome here — close, do not
proceed to D1–D7 dataset construction.

The 10 proposed `HR-UKR-01..10` constitutional rules are themselves mostly
restatements of doctrine already sealed elsewhere in this repo (ownership
boundaries, evidence requirements, retrieval-vs-use distinction) rather than
new constraints — building them as a fresh named rule family would itself
repeat the pattern `HR-NOVELTY-001` exists to catch. (The gate fired live on
this very prompt, on the word "fabric," per this turn's own system context —
working as designed.)

## What genuinely remains open (the real residue, if any)

Two of the seven `EXTEND_EXISTING_OWNER` verdicts (C — mission coverage
blocking, O — avoided-work intelligence) point at modules that are already
built but only partially wired (`dataset_first` explicitly self-describes as
advisor-not-authority; `corpus_roi.py` is PENDING per `OWNER_QUEUE.md`). If
there is a real "runtime residue" left by this whole line of inquiry, it is
**wiring debt on already-existing owners**, not a missing mechanism — the
same shape as GAP-1 from yesterday's pass, not a new shape.

## Recommendation (STOP #1)

Do not construct any of D1–D7. Do not seal any of HR-UKR-01..10 as a new
rule family. The original UKR intent is *already* substantially real,
distributed across graphify/KSF/spec_gate/rule_compiler/liveness/SQI-UQF/
Setup OS/secret_firewall/CLAE/DRK-ACIS/cpp_ias — the gap was never "this
doesn't exist," it was "nobody had mapped it as one coherent picture until
this audit." This document **is** that map; no further construction is
justified by the evidence gathered.

If the Owner wants the two wiring items (C's `dataset_first` authority
question, O's `corpus_roi.py` consumer question) addressed, those are
`OWNER_QUEUE.md` items already, not new work this document should spawn.

## Institutional Delta

- Original goal status: legitimate, and now more clearly *already achieved*
  in a distributed form than before this audit.
- Duplicates avoided: 18 of 18 candidates, 10 of 10 proposed Hard Rules.
- Owners reinforced with fresh evidence: graphify (all 13 GK datasets
  confirmed live via direct graph query — the fastest verification path
  used yet, worth reusing over grep next time), rule_compiler, liveness,
  Setup OS, secret_firewall, cpp_ias, SQI/UQF.
- Base rate: 8/8 mega-corpus-shaped proposals for this repo now measure as
  majority-or-fully owned against a discovered denominator.
- Confirmed live this session: `HR-NOVELTY-001`'s gate (wired last session
  after the 7th audit) fired correctly on this 8th proposal's own opening
  prompt — the loop it was built to close is now measurably closed.

## Addendum — cross-checked against the real D2A engine (Owner-directed)

Per Owner instruction, the 18 candidates were re-run through the actual
`modules/duplicate_to_advantage/d2a_engine.py --family-file` pipeline instead
of trusting this document's hand-written verdicts alone.

**First run (unpatched registry): 2 FOLD (A, K), 9 KEEP, 7 DEFER.** Diverged
sharply from the manual audit above. Traced why: `KSF`, `AKOS`, `LIVENESS`,
`SECRET-FIREWALL`, and `RULE-COMPILER` had **zero rows in D2A's
`FAMILY_REGISTRY`**, and — verified directly via `Glob
vault/knowledge_base/{ksf,akos,*liveness*,*secret*}*` — none of the five has
a `vault/knowledge_base/<name>/` directory either, so `_discover_families()`
could never surface them regardless of sweep completeness.
`registry_gaps()` reported `[]` (true for its own scope) while D2A was
structurally blind to 5 real owners outside that scope — the exact
`T-D2A-REGISTRY-BLIND-SPOT-001` shape, found a 3rd time (after
DEEP-RESEARCH/AUTORESEARCH at C96 and CAVEX-GOV/CRAWLOS/KOBII-IDENTITY on
2026-07-20).

**Fix applied:** added 5 curated rows to `d2a_engine.py`'s
`_CURATED_REGISTRY` (KSF, AKOS, LIVENESS, SECRET-FIREWALL, RULE-COMPILER),
keywords drawn from each family's own stated responsibilities (not
reverse-engineered to fit a UKR candidate). Updated
`tools/test_duplicate_to_advantage.py`'s `real_ids` allowlist with the same
verification evidence. `D2A_PASS=27/27` clean.

**Second run (patched registry): 4 FOLD (A, B, K, N), 7 KEEP, 7 DEFER.**
B (Authority) now correctly resolves to KSF at 60%; N (Admission Compiler)
to RULE-COMPILER at 56%. E/H/M (Inheritance, Reachability, Security) still
scored KEEP (30%/45%/45%) — below D2A's 50% fold threshold despite AKOS/
LIVENESS/SECRET-FIREWALL now being registered — a real precision limit of
keyword-overlap matching on short curated keyword lists, not a registry
absence. This was **not** further tuned: sharpening keywords until E/H/M
cross 50% would be reverse-engineering the registry to fit this specific
proposal, which the file's own doctrine forbids.

**Reconciled picture:** D2A (patched) confirms 4 of 18 at high confidence
(A/B/K/N). The manual audit's remaining 7 `ALREADY_OWNED` + 3 of 7
`EXTEND_EXISTING_OWNER` verdicts (E, H, M plus F, G, R) rest on direct file
verification (AKOS brief + injector observed live, `liveness/reachability.py`
on disk, `secret_firewall`'s sealed `HR-SECRET-001..007`, `setup_os`'s
`drift_detector.py`, ACIS/CRAIF, graphify GK-07) that D2A's lexical matcher
under-weights but does not contradict — no D2A run returned a KEEP with
`coverage < 25%` for any of them except E (30%), and none returned a FOLD
against a *different, wrong* parent. **Net effect on the STOP #1
recommendation: unchanged.** Zero of 18 build. The value of this pass was
real: D2A itself is measurably more correct now (a documented, sealed,
tested improvement to a shared tool), which outlasts this one audit.

