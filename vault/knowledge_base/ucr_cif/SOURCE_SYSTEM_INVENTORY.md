---
title: UCR-CIF Compendium — Source System Inventory
date: 2026-08-25
status: Phase 1 — mechanically extracted, KIND-classified, deduped by name+alias
source: "Dataset Claude Power Pack Universal Construction Ratchet & Compounding Intelligence Fabric 1.txt"
full_records: SOURCE_INVENTORY_FULL.json (every field, every record)
---

# Source System Inventory

Produced by reading the corpus in slices and typing every named concept. Counts
below are measured from the record files, never from a subagent's self-report —
two agents mis-stated their own totals (70 vs 133, 90 vs 121), so the files are
the authority.

**1326 unique concepts** after dedupe by normalized name and alias.

## 1. The distribution that sizes this mission

| Group | Count | Share |
|---|---:|---:|
| **System-bearing** (system · subsystem · registry · compiler · graph · kernel · ledger) | **250** | **18 %** |
| **Not dataset-bearing** (law · protocol · metric · capability · gate · artifact · …) | **1076** | **81 %** |

Per-KIND, descending:

| KIND | Count |
|---|---:|
| law | 324 |
| protocol | 198 |
| metric | 174 |
| capability | 117 |
| gate | 103 |
| artifact | 84 |
| system ·systemic | 69 |
| subsystem ·systemic | 68 |
| registry ·systemic | 61 |
| concept | 33 |
| loop | 31 |
| compiler ·systemic | 29 |
| graph ·systemic | 21 |
| taxonomy | 8 |
| pipeline | 2 |
| kernel ·systemic | 1 |
| framework | 1 |
| ledger ·systemic | 1 |
| failure | 1 |

**This ratio held constant at 19 % / 81 % across every partial aggregate**
(648 records → 1,326 records), so it is a property of the corpus, not of sampling.

`law` is the single largest category at 324 entries. A law is dataset
*content* and a UKDL candidate — it is not a dataset subject. The headline
"~1,300 named concepts" was therefore never a dataset count.

## 2. System-bearing concepts

Ordered by substance, then kind. `SUBSTANCE: HIGH` means the source devotes
sustained design detail; `LOW` means named in passing.

| # | Name | Kind | Sub | Parent |
|---|---|---|---|---|
| 1 | Architectural Truth Compiler | compiler | HIGH | KADOS |
| 2 | Baseline Compiler | compiler | HIGH | Baseline Capability Pack (UCR-CIF) |
| 3 | Failure-Aware Baseline Compiler | compiler | HIGH | NONE |
| 4 | Hardware Experiment Compiler | compiler | HIGH | Zero-Boot Engineering |
| 5 | KIFS Recursive Causal Funnel Compiler | compiler | HIGH | KIFS |
| 6 | Knowledge Compiler | compiler | HIGH | Baseline Compiler |
| 7 | Knowledge Compiler (institutional) | compiler | HIGH | Institutional State Governance |
| 8 | Knowledge-to-Production Compiler | compiler | HIGH | Knowledge Sovereignty Fabric |
| 9 | Mode Compiler | compiler | HIGH | Universal Baseline Compiler |
| 10 | Production Reality Contract Compiler | compiler | HIGH | Universal Baseline Compiler |
| 11 | Universal Baseline Compiler (UBC) | compiler | HIGH | NONE |
| 12 | Bug-Driven Knowledge Graph | graph | HIGH | NONE |
| 13 | Capability Graph | graph | HIGH | Compositional Baselines |
| 14 | Causal Construction Graph | graph | HIGH | Causal Construction Graph |
| 15 | Institutional Engineering State Graph | graph | HIGH | IFC Non-Executor Constraint |
| 16 | Institutional Leverage Graph | graph | HIGH | Capability Graph |
| 17 | Institutional State Graph | graph | HIGH | Universal Engineering Foundation |
| 18 | Instruction Provenance Graph | graph | HIGH | Institutional State Governance |
| 19 | Recursive Feedback Topology | graph | HIGH | Recursive Baseline Law |
| 20 | Universal Ownership Graph | graph | HIGH | Universal Software Integrity & Foresight Bas |
| 21 | CPP Constitutional Kernel | kernel | HIGH | Universal Engineering Foundation Runtime |
| 22 | Institutional Event Log | ledger | HIGH | Institutional State Governance |
| 23 | Capability Authority Registry (UCR-CIF) | registry | HIGH | Claude Power Pack Universal Construction Rat |
| 24 | Capability Composition Contracts | registry | HIGH | Constitutive Baseline Ratchet |
| 25 | Certified Engineering Primitives | registry | HIGH | Golden Paths (UCR-CIF) |
| 26 | Construction Memory | registry | HIGH | KME Universal Excellence Ratchet Flywheel |
| 27 | Existing Wii engineering systems inventory | registry | HIGH | NONE |
| 28 | Fable 5 derived UBC Baseline Packs | registry | HIGH | Universal Baseline Compiler |
| 29 | Failure Genome Library | registry | HIGH | Cross-Project Adversarial Recombination |
| 30 | Failure Hypothesis Library | registry | HIGH | Universal Software Integrity & Foresight Bas |
| 31 | Four-genome UFIA-EBF extension from Fable incidents | registry | HIGH | UFIA-EBF |
| 32 | Human Intervention Gap Registry | registry | HIGH | HIC-OAR |
| 33 | Human Intervention Ledger | registry | HIGH | Claude Power Pack Human Intervention Collaps |
| 34 | NEGATIVE EXPERIMENT MEMORY | registry | HIGH | NONE |
| 35 | Override Ledger | registry | HIGH | Universal Baseline Compiler |
| 36 | Self-Evolving Benchmark Genome for Wii | registry | HIGH | CPP Software Engineering Evolution & Intelli |
| 37 | Universal Capability Authority Registry | registry | HIGH | NONE |
| 38 | Universal Construction Ledger | registry | HIGH | Construction Intelligence Record |
| 39 | Wii Failure Mutation Genome | registry | HIGH | NONE |
| 40 | Wii Production Capability Genome | registry | HIGH | NONE |
| 41 | CPP Project Activation vs Resident Institutional Kernel | subsystem | HIGH | Host-Resident Construction Observer |
| 42 | Composition Intelligence | subsystem | HIGH | Capability Baseline Graph |
| 43 | Compositional Baselines | subsystem | HIGH | KME Universal Excellence Ratchet Flywheel |
| 44 | Engineering Reality Encoder / Universal Semantic IR | subsystem | HIGH | UEFB |
| 45 | Existing Systems as Flywheel Stations | subsystem | HIGH | Claude Power Pack Universal Construction Rat |
| 46 | Global Construction Stream | subsystem | HIGH | Host-Resident Construction Observer |
| 47 | Host-Resident Construction Observer | subsystem | HIGH | Claude Power Pack Universal Construction Rat |
| 48 | Institutional Flywheel Controller | subsystem | HIGH | Claude Power Pack Recursive Compounding Inte |
| 49 | Intent-to-Reality Diff universal | subsystem | HIGH | Universal Software Integrity & Foresight Bas |
| 50 | Intervention Prediction | subsystem | HIGH | Human-Burden Compounding Loop |
| 51 | QueryOptions for baseline compilation | subsystem | HIGH | Universal Baseline Compiler |
| 52 | Representation Revolution Detector | subsystem | HIGH | Exploration Budget |
| 53 | Risk Forecasting | subsystem | HIGH | Predictive Institutional Knowledge |
| 54 | Skill Projection Layer | subsystem | HIGH | Institutional Intelligence Engine / Knowledg |
| 55 | Supervision Collapse Engine | subsystem | HIGH | Claude Power Pack Human Intervention Collaps |
| 56 | Universal Capability Extraction Layer | subsystem | HIGH | KME Universal Excellence Ratchet Flywheel |
| 57 | Autonomous Integrity Hunter | system | HIGH | Universal Software Integrity & Foresight Bas |
| 58 | CPP Software Engineering Evolution & Intelligence Platform | system | HIGH | NONE |
| 59 | Capability Economy | system | HIGH | Capability Economy |
| 60 | Claim-Evidence Type System | system | HIGH | Production Reality Contract Compiler |
| 61 | Claude Power Pack Human Intervention Collapse & One-Shot Autonomy Ratchet | system | HIGH | Claude Power Pack Recursive Autonomous Engin |
| 62 | Claude Power Pack Institutional Flywheel Controller | system | HIGH | Institutional Flywheel Controller |
| 63 | Claude Power Pack Recursive Compounding Intelligence & Engineering Acceleratio | system | HIGH | Claude Power Pack Universal Construction Rat |
| 64 | Claude Power Pack Universal Construction Ratchet & Compounding Intelligence Fa | system | HIGH | NONE |
| 65 | Context Substitution Failures | system | HIGH | RELATIONAL FAILURE GENOMES |
| 66 | Crawl OS | system | HIGH | Universal Engineering Foundation Runtime |
| 67 | Fable 5 World Demo | system | HIGH | NONE |
| 68 | Failure Science Layer | system | HIGH | NONE |
| 69 | GEX44 as Player/Hardware Reality Cortex | system | HIGH | NONE |
| 70 | Immunity Maturity Ladder | system | HIGH | NONE |
| 71 | Instance Baseline / System-Family Baseline / Architecture-Archetype Baseline / | system | HIGH | Universal Baseline Compiler |
| 72 | Institutional Flywheel Controller (IFC) | system | HIGH | NONE |
| 73 | Institutional Replay Engine | system | HIGH | Institutional Branches / Institutional State |
| 74 | Institutional State Governance | system | HIGH | Universal Engineering Foundation Runtime |
| 75 | Interactive-Only Failure Families | system | HIGH | RELATIONAL FAILURE GENOMES |
| 76 | KIFS (Kobii Institutional Foresight System) | system | HIGH | NONE (foundational; later evolves into RCFC) |
| 77 | KME Universal Excellence Ratchet Flywheel | system | HIGH | NONE |
| 78 | Knowledge Sovereignty Fabric | system | HIGH | Universal Engineering Foundation Runtime |
| 79 | KobiMapEngine (KME) Production Baseline | system | HIGH | NONE |
| 80 | LuckPerms Longitudinal State & Policy Maturity Corpus | system | HIGH | Historical Software Maturity Distillation |
| 81 | Network of Flywheels | system | HIGH | Claude Power Pack Universal Construction Rat |
| 82 | Production Maturity Ladder (P0-P10) | system | HIGH | NONE |
| 83 | RELATIONAL FAILURE GENOMES | system | HIGH | Failure Genome system |
| 84 | Recursive Institutional Acceleration | system | HIGH | Claude Power Pack Recursive Compounding Inte |
| 85 | Reliability Confidence Ladder (R0-R9) | system | HIGH | NONE |
| 86 | Resident Institutional Kernel | system | HIGH | NONE |
| 87 | Self-Accelerating Engineering Institution | system | HIGH | Claude Power Pack Recursive Compounding Inte |
| 88 | Seven Planes Architecture | system | HIGH | NONE |
| 89 | Shared institutional primitive planes | system | HIGH | NONE |
| 90 | Universal Autonomous Experimental Engineering Corpus | system | HIGH | Fable 5 World Demo |
| 91 | Universal Discovery, Failure & Learning Ledger | system | HIGH | NONE (feeds all major CPP subsystems) |
| 92 | Universal Engineering Civilization Layer | system | HIGH | Universal Engineering Foundation Runtime |
| 93 | Universal Engineering Foundation Baseline | system | HIGH | NONE (top-level foundation layer) |
| 94 | Universal Engineering Integrity Envelope | system | HIGH | Universal Baseline Compiler |
| 95 | Universal External Reality Acquisition & Evolution Layer | system | HIGH | UEFB |
| 96 | Universal Game Production & Evolution Platform | system | HIGH | NONE (peer of UBC/KIFS in the flywheel) |
| 97 | Universal Knowledge Runtime (UKR) | system | HIGH | Universal Engineering Foundation Runtime |
| 98 | Universal Production System Evolution & Intelligence Platform | system | HIGH | NONE (peer system, KSEIP is its KobiiCraft v |
| 99 | Universal Software Integrity & Foresight Baseline | system | HIGH | Universal Baseline Compiler |
| 100 | Autonomy Knowledge Compiler | compiler | MEDIUM | Autonomous Session Continuity |
| 101 | Constraint Envelope Compilation | compiler | MEDIUM | Baseline Completeness Genome |
| 102 | Evidence Mission Compiler | compiler | MEDIUM | Crawl OS |
| 103 | Failure Investigation Compiler improvement per bug | compiler | MEDIUM | Meta-Immunity |
| 104 | Kill-Switch Compiler | compiler | MEDIUM | Universal Baseline Compiler |
| 105 | Knowledge Compilation Pipeline | compiler | MEDIUM | Knowledge Sovereignty Fabric |
| 106 | Knowledge → Enforcement Compiler | compiler | MEDIUM | Capability Bytecode |
| 107 | Micro-Commit Compiler | compiler | MEDIUM | Universal Baseline Compiler |
| 108 | PATCH/ADAPT/REIMPLEMENT/EMULATE/SUBSTITUTE/HYBRID decision compiler | compiler | MEDIUM | Constrained Reimplementation Compiler |
| 109 | Plan Compiler (Execution Protocol) | compiler | MEDIUM | Inline Plan Contract |
| 110 | User Intent Compiler | compiler | MEDIUM | Intent Drift Detector |
| 111 | Work-Class Compilers | compiler | MEDIUM | Playbook Evolution |
| 112 | Capability Baseline Graph | graph | MEDIUM | Capability Authority Registry (UCR-CIF) |
| 113 | Capability Dependency Graph (UCR-CIF) | graph | MEDIUM | Capability Graph |
| 114 | Escalation Debt Graph | graph | MEDIUM | Institutional Debt Taxonomy |
| 115 | Global Bottleneck Map | graph | MEDIUM | IFC Bottleneck Cascade |
| 116 | IFC Causal Edge Types | graph | MEDIUM | IFC Node Universality |
| 117 | Mechanism Graph | graph | MEDIUM | Universalization Compiler |
| 118 | Opportunity Graph | graph | MEDIUM | Opportunity Discovery (IFC) |
| 119 | State Transition Failure Graph | graph | MEDIUM | NONE |
| 120 | Temporal Capability Graph | graph | MEDIUM | Bidirectional Institutional Evolution |
| 121 | Temporal Decision Graph | graph | MEDIUM | Decision Reopening Engine |
| 122 | Assumption Registry | registry | MEDIUM | NONE |
| 123 | Autonomy Benchmark Vault | registry | MEDIUM | Autonomy Canary |
| 124 | Baseline Packages by Archetype | registry | MEDIUM | Baseline Packages |
| 125 | Baseline Propagation Set | registry | MEDIUM | Universal Baseline Compiler |
| 126 | Baseline generation per family | registry | MEDIUM | System Family Identity |
| 127 | Benchmark Retirement | registry | MEDIUM | Benchmark Retirement |
| 128 | Capability Authority Registry | registry | MEDIUM | Capability Ratchet |
| 129 | Certified Construction Primitives | registry | MEDIUM | Baseline Packages by Archetype |
| 130 | Cheap Falsification Library | registry | MEDIUM | Trap Registry |
| 131 | Claim-surface coverage matrix | registry | MEDIUM | NONE |
| 132 | Comparison harness confound registry | registry | MEDIUM | NEVER TRUST A DIFF UNTIL YOU KNOW WHAT ELSE  |
| 133 | Constitutive Capability Set | registry | MEDIUM | Constitutive Baseline Ratchet |
| 134 | Decision Memory | registry | MEDIUM | User Intent Compiler |
| 135 | Drift families universal | registry | MEDIUM | Continuous Integrity Mode |
| 136 | Execution Memory | registry | MEDIUM | Decision Memory |
| 137 | External Assumption Registry | registry | MEDIUM | Crawl OS |
| 138 | Failure Family Authority | registry | MEDIUM | NONE |
| 139 | Family Completeness Genome | registry | MEDIUM | Capability Registry / Baseline Completeness  |
| 140 | HARD/TARGET/TIER-2/DEVIATION requirement tiering | registry | MEDIUM | DEVIATION IS A STATE, NOT A SECRET |
| 141 | Hypothesis Seeds structure | registry | MEDIUM | Failure Hypothesis Library |
| 142 | Institutional One-Shot Memory | registry | MEDIUM | Autonomy Compression |
| 143 | Intervention Genomes | registry | MEDIUM | Intervention Root-Cause Analysis |
| 144 | Knowledge Vault as Evidence Memory | registry | MEDIUM | UKDL Three-Level Distillation |
| 145 | Numerical degeneracy guards | registry | MEDIUM | SCALE-DEGENERACY TESTING |
| 146 | RICH_INTERACTIVE_APP baseline | registry | MEDIUM | Constitutive Baseline Ratchet |
| 147 | Regression Vault | registry | MEDIUM | NONE |
| 148 | Semantic Identity Registry | registry | MEDIUM | Capability Authority Registry |
| 149 | Sensory Benchmarks | registry | MEDIUM | GEX44 as Player/Hardware Reality Cortex |
| 150 | Seven mission capital types | registry | MEDIUM | NONE |
| 151 | Simulator Coverage Map | registry | MEDIUM | Zero-Boot Engineering |
| 152 | Six mission capital types | registry | MEDIUM | NONE |
| 153 | System Family Identity | registry | MEDIUM | Universal Baseline Compiler |
| 154 | Trap Registry | registry | MEDIUM | Negative Knowledge Compounding |
| 155 | Universal Pattern Families | registry | MEDIUM | Cross-Runtime Transfer |
| 156 | Universal Unknown-Unknown Frontier | registry | MEDIUM | Universal Software Integrity & Foresight Bas |
| 157 | Architecture Evolution Engine | subsystem | MEDIUM | Architecture Evolution Engine |
| 158 | Assumption Explosion Engine | subsystem | MEDIUM | RCFC |
| 159 | Assumption Interaction Engine | subsystem | MEDIUM | RCFC |
| 160 | Autonomous Experiment Factory | subsystem | MEDIUM | Autonomous Experiment Factory |
| 161 | Autonomous Frontier Discovery | subsystem | MEDIUM | Institutional Leverage Graph |
| 162 | Capability Consumption Telemetry | subsystem | MEDIUM | Context Outcome Attribution |
| 163 | Causal Blast Radius / Prevention Ascension Funnel | subsystem | MEDIUM | RCFC |
| 164 | Composition Opportunity Mining | subsystem | MEDIUM | Emergent Capability Detection |
| 165 | Consolidation Opportunity Miner | subsystem | MEDIUM | Duplication As Institutional Failure |
| 166 | Context Outcome Attribution | subsystem | MEDIUM | Context ROI Ratchet |
| 167 | Counterfactual Capability Mining | subsystem | MEDIUM | Improvement Propagation Simulator |
| 168 | Crawl Cortex | subsystem | MEDIUM | Crawl OS |
| 169 | Emergent Capability Detection | subsystem | MEDIUM | Capability Graph |
| 170 | Escape Funnel / Meta-Escape Funnel | subsystem | MEDIUM | RCFC |
| 171 | Failure Frontier Generator | subsystem | MEDIUM | Synthetic Adversarial Worlds |
| 172 | Falsification-first routing / Information Gain Planner | subsystem | MEDIUM | RCFC |
| 173 | Friction Mining | subsystem | MEDIUM | Counterfactual Capability Mining |
| 174 | Funnel Self-Red-Team / Blind-Domain Detector / Funnel Coverage Graph | subsystem | MEDIUM | RCFC |
| 175 | Game Instrumentation Factory | subsystem | MEDIUM | UGPEP |
| 176 | Geometry Comparator / Visual Comparator / Semantic Comparator / Perceptual Del | subsystem | MEDIUM | Reference Reconstruction Pipeline |
| 177 | Improvement Propagation Simulator | subsystem | MEDIUM | Institutional Leverage Graph |
| 178 | Inflection Point Mining | subsystem | MEDIUM | Temporal Capability Graph |
| 179 | Institutional Autofactoring | subsystem | MEDIUM | Pattern-to-Primitive Ascension |
| 180 | Institutional Duplicate Detection | subsystem | MEDIUM | Knowledge Linker |
| 181 | Institutional Garbage Collector | subsystem | MEDIUM | Institutional State Governance |
| 182 | Institutional Observability | subsystem | MEDIUM | Institutional State Governance |
| 183 | Institutional Replay | subsystem | MEDIUM | Institutional Replay |
| 184 | Knowledge Linker | subsystem | MEDIUM | Institutional State Governance |
| 185 | Measurement methodology as baseline | subsystem | MEDIUM | NONE |
| 186 | Opportunity Clustering | subsystem | MEDIUM | Opportunity Graph |
| 187 | Opportunity Discovery (IFC) | subsystem | MEDIUM | Hard Safety Floors |
| 188 | Positive Loop Miner | subsystem | MEDIUM | Improvement Chain Attribution |
| 189 | Self-Healing Selector Fabric | subsystem | MEDIUM | Crawl OS |
| 190 | Session Discovery Stream | subsystem | MEDIUM | UDFLL |
| 191 | Source Authority Resolver | subsystem | MEDIUM | Crawl OS |
| 192 | Subtraction Funnel | subsystem | MEDIUM | RCFC |
| 193 | Temporal Funnel / Long-horizon funnel | subsystem | MEDIUM | RCFC |
| 194 | Time-Machine Evaluation | subsystem | MEDIUM | Institutional Replay |
| 195 | Universal Provenance & Lineage Intelligence | subsystem | MEDIUM | Universal Software Integrity & Foresight Bas |
| 196 | Universal Transfer Evaluator | subsystem | MEDIUM | Knowledge Upward Movement |
| 197 | Accidental-Pass Failures | system | MEDIUM | RELATIONAL FAILURE GENOMES |
| 198 | Agent Failure Observatory | system | MEDIUM | Behavioral Failure Forensics |
| 199 | Approximation Regime Failures | system | MEDIUM | RELATIONAL FAILURE GENOMES |
| 200 | Capital Allocation Model | system | MEDIUM | IFC |
| 201 | Engineering Policy VM | system | MEDIUM | Institutional State Governance |
| 202 | Hardware Truth Network | system | MEDIUM | NONE |
| 203 | Institutional Intelligence Engine | system | MEDIUM | Universal Engineering Foundation Runtime |
| 204 | Instrumentation Reality Failures | system | MEDIUM | RELATIONAL FAILURE GENOMES |
| 205 | KIFS | system | MEDIUM | NONE |
| 206 | KME Universal Capability Ratchet & Compounding Excellence Flywheel | system | MEDIUM | KME Universal Excellence Ratchet Flywheel |
| 207 | Masking Layer Failures | system | MEDIUM | RELATIONAL FAILURE GENOMES |
| 208 | Measurement Confound Failures | system | MEDIUM | RELATIONAL FAILURE GENOMES |
| 209 | Multi-Runtime Portability Pack | system | MEDIUM | Universal Baseline Compiler |
| 210 | Multi-Writer Institutional Runtime | system | MEDIUM | Institutional State Governance |
| 211 | Observability Difficulty Engine | system | MEDIUM | Self-Evolving Diagnostic Instrumentation |
| 212 | Project Operational Memory / Knowledge Vault / UKDL three-layer memory | system | MEDIUM | NONE |
| 213 | Scrapling | system | MEDIUM | Crawl OS |
| 214 | Software Evolution Intelligence | system | MEDIUM | Universal Engineering Foundation Runtime |
| 215 | Software Evolution Intelligence (external acquisition integration) | system | MEDIUM | NONE (peer system consuming UERAL) |
| 216 | Temporal Staleness Failures | system | MEDIUM | RELATIONAL FAILURE GENOMES |
| 217 | UERAL (Universal External Reality Acquisition Layer) | system | MEDIUM | Crawl OS (absorbed into) |
| 218 | Acquisition Router (Tier 0-4) | compiler | LOW | UERAL |
| 219 | Capability Budget Compiler | compiler | LOW | Constrained Reimplementation Compiler |
| 220 | Game Development Session Compiler | compiler | LOW | UGPEP |
| 221 | Question-to-Policy Compiler | compiler | LOW | Autonomous Experimentation |
| 222 | Question-to-Primitive Compiler | compiler | LOW | Question-to-Policy Compiler |
| 223 | Self-evolving Skill Compiler | compiler | LOW | Skill Projection Layer |
| 224 | Institutional System Graph | graph | LOW | Shared institutional primitive planes |
| 225 | Unlock Graph | graph | LOW | Capability Option Value |
| 226 | Algorithm properties as capability metadata | registry | LOW | Optimize using domain invariants |
| 227 | Baseline Cache (UCR-CIF) | registry | LOW | Baseline Caching |
| 228 | Claim vocabulary epistemic precision | registry | LOW | Epistemic Integrity |
| 229 | Context Source Registry | registry | LOW | UBC |
| 230 | Game-Class Baselines | registry | LOW | Wii Production Capability Genome |
| 231 | Implementation debt vs accepted deviation distinction | registry | LOW | DEVIATION IS A STATE, NOT A SECRET |
| 232 | Parameter ownership baseline | registry | LOW | ONE VALUE CONTROLLING MULTIPLE SEMANTIC DOMA |
| 233 | Twin Divergence Incident | registry | LOW | TWIN != TRUTH |
| 234 | Authority Funnel | subsystem | LOW | RCFC |
| 235 | Boundary Funnel | subsystem | LOW | RCFC |
| 236 | Capability Challenger System | subsystem | LOW | IFC (Institutional Frontier/allocation) |
| 237 | Contrafactual/Reverse Counterfactual Reconstruction | subsystem | LOW | RCFC |
| 238 | Funnel Compression Engine | subsystem | LOW | RCFC |
| 239 | Funnel Reopen Trigger / Counterexample Memory | subsystem | LOW | RCFC |
| 240 | MarkItDown | subsystem | LOW | Crawl OS |
| 241 | Masking-Layer Funnel | subsystem | LOW | RCFC |
| 242 | Representation Funnel | subsystem | LOW | RCFC |
| 243 | Scale Inversion | subsystem | LOW | RCFC |
| 244 | Source Authority Router | subsystem | LOW | UERAL |
| 245 | Symmetry Breaking Funnel | subsystem | LOW | RCFC |
| 246 | Baseline & Policy Plane | system | LOW | Shared institutional primitive planes |
| 247 | Construction/Failure/Intervention Event Stream | system | LOW | Shared institutional primitive planes |
| 248 | Evidence & Knowledge Plane | system | LOW | Shared institutional primitive planes |
| 249 | Time-step invariance pack | system | LOW | Universal Baseline Compiler |
| 250 | Universal Evaluation Plane | system | LOW | Shared institutional primitive planes |

## 3. Cross-range spine concepts

Concepts the corpus returns to in more than one region — its connective tissue,
and the strongest candidates for Part-level treatment under any coverage form.

| Name | Kind | Sub | Ranges |
|---|---|---|---:|
| Baseline Inheritance Debt | law | HIGH | 2 |
| Composition Intelligence | subsystem | HIGH | 2 |
| Engineering Interest Rate | metric | HIGH | 2 |
| Institutional Flywheel Controller | subsystem | HIGH | 2 |
| Meta-Immunity | law | HIGH | 2 |
| Project Genome | artifact | HIGH | 2 |
| Time To Production Excellence | metric | HIGH | 2 |
| UKDL Promotion Gate | gate | HIGH | 2 |
| Assumption Registry | registry | MEDIUM | 2 |
| Baseline Gap Report | artifact | MEDIUM | 2 |
| Baseline Revocation States | taxonomy | MEDIUM | 2 |
| Emergent Capability Detection | subsystem | MEDIUM | 2 |
| Generator / Evaluator / Adversary triad | protocol | MEDIUM | 2 |
| Human Intervention Burden | metric | MEDIUM | 2 |
| Institutional Compression Ratio | metric | MEDIUM | 2 |
| Prediction Gate | gate | MEDIUM | 2 |
| Ratchet-on-Touch | law | MEDIUM | 2 |
| Root-Cause Reuse Multiplier | metric | MEDIUM | 2 |
| Search Space Collapse | concept | MEDIUM | 2 |
| Capability Yield per Construction | metric | LOW | 2 |

## 4. Method and its limits

- Every line outside the measured contamination runs was read; nothing sampled.
- Records were written per-slice to their own files, so a killed agent lost
  nothing — adopted after two agents died on the 64k output cap.
- Dedupe is by normalized name plus declared alias. Two agents naming the same
  object differently with no shared alias remain two rows; §2's count is
  therefore an **upper bound** on distinct systems.
- KIND is the extracting agent's judgement. It drives whether a concept is a
  dataset subject, so it is re-verified in Phase 2 against the source text for
  every row typed `system` or `subsystem`.