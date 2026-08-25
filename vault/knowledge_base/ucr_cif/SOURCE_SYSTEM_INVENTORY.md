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

**1394 unique concepts** after dedupe by normalized name and alias.

## 1. The distribution that sizes this mission

| Group | Count | Share |
|---|---:|---:|
| **System-bearing** (system · subsystem · registry · compiler · graph · kernel · ledger) | **262** | **18 %** |
| **Not dataset-bearing** (law · protocol · metric · capability · gate · artifact · …) | **1132** | **81 %** |

Per-KIND, descending:

| KIND | Count |
|---|---:|
| law | 336 |
| protocol | 213 |
| metric | 184 |
| capability | 121 |
| gate | 110 |
| artifact | 87 |
| subsystem ·systemic | 73 |
| system ·systemic | 71 |
| registry ·systemic | 63 |
| loop | 36 |
| concept | 33 |
| compiler ·systemic | 31 |
| graph ·systemic | 22 |
| taxonomy | 8 |
| pipeline | 2 |
| kernel ·systemic | 1 |
| framework | 1 |
| ledger ·systemic | 1 |
| failure | 1 |

**This ratio held constant at 19 % / 81 % across every partial aggregate**
(648 records → 1,326 records), so it is a property of the corpus, not of sampling.

`law` is the single largest category at 336 entries. A law is dataset
*content* and a UKDL candidate — it is not a dataset subject. The headline
"~1,300 named concepts" was therefore never a dataset count.

## 2. System-bearing concepts

Ordered by substance, then kind. `SUBSTANCE: HIGH` means the source devotes
sustained design detail; `LOW` means named in passing.

| # | Name | Kind | Sub | Parent |
|---|---|---|---|---|
| 1 | Architectural Truth Compiler | compiler | HIGH | KADOS |
| 2 | Baseline Compiler | compiler | HIGH | Baseline Capability Pack (UCR-CIF) |
| 3 | Diff-Aware Failure Prediction | compiler | HIGH | Predictive Failure Pack |
| 4 | Failure-Aware Baseline Compiler | compiler | HIGH | NONE |
| 5 | Hardware Experiment Compiler | compiler | HIGH | Zero-Boot Engineering |
| 6 | KIFS Recursive Causal Funnel Compiler | compiler | HIGH | KIFS |
| 7 | Knowledge Compiler | compiler | HIGH | Baseline Compiler |
| 8 | Knowledge Compiler (institutional) | compiler | HIGH | Institutional State Governance |
| 9 | Knowledge-to-Production Compiler | compiler | HIGH | Knowledge Sovereignty Fabric |
| 10 | Mode Compiler | compiler | HIGH | Universal Baseline Compiler |
| 11 | Production Reality Contract Compiler | compiler | HIGH | Universal Baseline Compiler |
| 12 | Universal Baseline Compiler (UBC) | compiler | HIGH | NONE |
| 13 | Bug-Driven Knowledge Graph | graph | HIGH | NONE |
| 14 | Capability Graph | graph | HIGH | Compositional Baselines |
| 15 | Causal Construction Graph | graph | HIGH | Causal Construction Graph |
| 16 | Institutional Engineering State Graph | graph | HIGH | IFC Non-Executor Constraint |
| 17 | Institutional Leverage Graph | graph | HIGH | Capability Graph |
| 18 | Institutional State Graph | graph | HIGH | Universal Engineering Foundation |
| 19 | Instruction Provenance Graph | graph | HIGH | Institutional State Governance |
| 20 | Recursive Feedback Topology | graph | HIGH | Recursive Baseline Law |
| 21 | Universal Ownership Graph | graph | HIGH | Universal Software Integrity & Foresight Bas |
| 22 | CPP Constitutional Kernel | kernel | HIGH | Universal Engineering Foundation Runtime |
| 23 | Institutional Event Log | ledger | HIGH | Institutional State Governance |
| 24 | Capability Authority Registry (UCR-CIF) | registry | HIGH | Claude Power Pack Universal Construction Rat |
| 25 | Capability Composition Contracts | registry | HIGH | Constitutive Baseline Ratchet |
| 26 | Certified Engineering Primitives | registry | HIGH | Golden Paths (UCR-CIF) |
| 27 | Construction Memory | registry | HIGH | KME Universal Excellence Ratchet Flywheel |
| 28 | Engineering Investment Dataset | registry | HIGH | Dynamic Frontier Recomputation |
| 29 | Existing Wii engineering systems inventory | registry | HIGH | NONE |
| 30 | Fable 5 derived UBC Baseline Packs | registry | HIGH | Universal Baseline Compiler |
| 31 | Failure Genome Library | registry | HIGH | Cross-Project Adversarial Recombination |
| 32 | Failure Hypothesis Library | registry | HIGH | Universal Software Integrity & Foresight Bas |
| 33 | Four-genome UFIA-EBF extension from Fable incidents | registry | HIGH | UFIA-EBF |
| 34 | Human Intervention Gap Registry | registry | HIGH | HIC-OAR |
| 35 | Human Intervention Ledger | registry | HIGH | Claude Power Pack Human Intervention Collaps |
| 36 | NEGATIVE EXPERIMENT MEMORY | registry | HIGH | NONE |
| 37 | Override Ledger | registry | HIGH | Universal Baseline Compiler |
| 38 | Self-Evolving Benchmark Genome for Wii | registry | HIGH | CPP Software Engineering Evolution & Intelli |
| 39 | Session Failure Stream | registry | HIGH | Failure Mechanism as Fundamental Unit |
| 40 | Universal Capability Authority Registry | registry | HIGH | NONE |
| 41 | Universal Construction Ledger | registry | HIGH | Construction Intelligence Record |
| 42 | Wii Failure Mutation Genome | registry | HIGH | NONE |
| 43 | Wii Production Capability Genome | registry | HIGH | NONE |
| 44 | CPP Project Activation vs Resident Institutional Kernel | subsystem | HIGH | Host-Resident Construction Observer |
| 45 | Composition Intelligence | subsystem | HIGH | Capability Baseline Graph |
| 46 | Compositional Baselines | subsystem | HIGH | KME Universal Excellence Ratchet Flywheel |
| 47 | Engineering Reality Encoder / Universal Semantic IR | subsystem | HIGH | UEFB |
| 48 | Existing Systems as Flywheel Stations | subsystem | HIGH | Claude Power Pack Universal Construction Rat |
| 49 | Failure-Derived Adversarial Generation | subsystem | HIGH | Test Selection from Failure Memory |
| 50 | Generalization Search and Exposure Graph | subsystem | HIGH | Causal Abstraction (Failure Genome Example) |
| 51 | Global Construction Stream | subsystem | HIGH | Host-Resident Construction Observer |
| 52 | Host-Resident Construction Observer | subsystem | HIGH | Claude Power Pack Universal Construction Rat |
| 53 | IFC Causal Attribution | subsystem | HIGH | Historical Replay Economics |
| 54 | Institutional Flywheel Controller | subsystem | HIGH | Claude Power Pack Recursive Compounding Inte |
| 55 | Intent-to-Reality Diff universal | subsystem | HIGH | Universal Software Integrity & Foresight Bas |
| 56 | Intervention Prediction | subsystem | HIGH | Human-Burden Compounding Loop |
| 57 | Latent Failure Discovery | subsystem | HIGH | Generalization Search and Exposure Graph |
| 58 | Opportunity Mining Signals | subsystem | HIGH | IFC Time Horizon Balancing |
| 59 | QueryOptions for baseline compilation | subsystem | HIGH | Universal Baseline Compiler |
| 60 | Representation Revolution Detector | subsystem | HIGH | Exploration Budget |
| 61 | Risk Forecasting | subsystem | HIGH | Predictive Institutional Knowledge |
| 62 | Skill Projection Layer | subsystem | HIGH | Institutional Intelligence Engine / Knowledg |
| 63 | Supervision Collapse Engine | subsystem | HIGH | Claude Power Pack Human Intervention Collaps |
| 64 | Universal Capability Extraction Layer | subsystem | HIGH | KME Universal Excellence Ratchet Flywheel |
| 65 | Autonomous Integrity Hunter | system | HIGH | Universal Software Integrity & Foresight Bas |
| 66 | CPP Software Engineering Evolution & Intelligence Platform | system | HIGH | NONE |
| 67 | Capability Economy | system | HIGH | Capability Economy |
| 68 | Claim-Evidence Type System | system | HIGH | Production Reality Contract Compiler |
| 69 | Claude Power Pack Human Intervention Collapse & One-Shot Autonomy Ratchet | system | HIGH | Claude Power Pack Recursive Autonomous Engin |
| 70 | Claude Power Pack Institutional Flywheel Controller | system | HIGH | Institutional Flywheel Controller |
| 71 | Claude Power Pack Recursive Compounding Intelligence & Engineering Acceleratio | system | HIGH | Claude Power Pack Universal Construction Rat |
| 72 | Claude Power Pack Universal Construction Ratchet & Compounding Intelligence Fa | system | HIGH | NONE |
| 73 | Claude Power Pack Universal Failure Immunity, Anticipation & Error-Derived Bas | system | HIGH | Failure Immunity Ratchet |
| 74 | Context Substitution Failures | system | HIGH | RELATIONAL FAILURE GENOMES |
| 75 | Crawl OS | system | HIGH | Universal Engineering Foundation Runtime |
| 76 | Fable 5 World Demo | system | HIGH | NONE |
| 77 | Failure Science Layer | system | HIGH | NONE |
| 78 | GEX44 as Player/Hardware Reality Cortex | system | HIGH | NONE |
| 79 | Immunity Maturity Ladder | system | HIGH | NONE |
| 80 | Instance Baseline / System-Family Baseline / Architecture-Archetype Baseline / | system | HIGH | Universal Baseline Compiler |
| 81 | Institutional Flywheel Controller (IFC) | system | HIGH | NONE |
| 82 | Institutional Replay Engine | system | HIGH | Institutional Branches / Institutional State |
| 83 | Institutional State Governance | system | HIGH | Universal Engineering Foundation Runtime |
| 84 | Interactive-Only Failure Families | system | HIGH | RELATIONAL FAILURE GENOMES |
| 85 | KIFS (Kobii Institutional Foresight System) | system | HIGH | NONE (foundational; later evolves into RCFC) |
| 86 | KME Universal Excellence Ratchet Flywheel | system | HIGH | NONE |
| 87 | Knowledge Sovereignty Fabric | system | HIGH | Universal Engineering Foundation Runtime |
| 88 | KobiMapEngine (KME) Production Baseline | system | HIGH | NONE |
| 89 | LuckPerms Longitudinal State & Policy Maturity Corpus | system | HIGH | Historical Software Maturity Distillation |
| 90 | Network of Flywheels | system | HIGH | Claude Power Pack Universal Construction Rat |
| 91 | Production Maturity Ladder (P0-P10) | system | HIGH | NONE |
| 92 | RELATIONAL FAILURE GENOMES | system | HIGH | Failure Genome system |
| 93 | Recursive Institutional Acceleration | system | HIGH | Claude Power Pack Recursive Compounding Inte |
| 94 | Reliability Confidence Ladder (R0-R9) | system | HIGH | NONE |
| 95 | Resident Institutional Kernel | system | HIGH | NONE |
| 96 | Self-Accelerating Engineering Institution | system | HIGH | Claude Power Pack Recursive Compounding Inte |
| 97 | Seven Planes Architecture | system | HIGH | NONE |
| 98 | Shared institutional primitive planes | system | HIGH | NONE |
| 99 | UCR-CIF plus HIC-OAR plus IFC Convergence | system | HIGH | Claude Power Pack Institutional Flywheel Con |
| 100 | Universal Autonomous Experimental Engineering Corpus | system | HIGH | Fable 5 World Demo |
| 101 | Universal Discovery, Failure & Learning Ledger | system | HIGH | NONE (feeds all major CPP subsystems) |
| 102 | Universal Engineering Civilization Layer | system | HIGH | Universal Engineering Foundation Runtime |
| 103 | Universal Engineering Foundation Baseline | system | HIGH | NONE (top-level foundation layer) |
| 104 | Universal Engineering Integrity Envelope | system | HIGH | Universal Baseline Compiler |
| 105 | Universal External Reality Acquisition & Evolution Layer | system | HIGH | UEFB |
| 106 | Universal Game Production & Evolution Platform | system | HIGH | NONE (peer of UBC/KIFS in the flywheel) |
| 107 | Universal Knowledge Runtime (UKR) | system | HIGH | Universal Engineering Foundation Runtime |
| 108 | Universal Production System Evolution & Intelligence Platform | system | HIGH | NONE (peer system, KSEIP is its KobiiCraft v |
| 109 | Universal Software Integrity & Foresight Baseline | system | HIGH | Universal Baseline Compiler |
| 110 | Autonomy Knowledge Compiler | compiler | MEDIUM | Autonomous Session Continuity |
| 111 | Bug-to-Invariant Compiler | compiler | MEDIUM | Pre-Incident Immunity |
| 112 | Constraint Envelope Compilation | compiler | MEDIUM | Baseline Completeness Genome |
| 113 | Evidence Mission Compiler | compiler | MEDIUM | Crawl OS |
| 114 | Failure Investigation Compiler improvement per bug | compiler | MEDIUM | Meta-Immunity |
| 115 | Kill-Switch Compiler | compiler | MEDIUM | Universal Baseline Compiler |
| 116 | Knowledge Compilation Pipeline | compiler | MEDIUM | Knowledge Sovereignty Fabric |
| 117 | Knowledge → Enforcement Compiler | compiler | MEDIUM | Capability Bytecode |
| 118 | Micro-Commit Compiler | compiler | MEDIUM | Universal Baseline Compiler |
| 119 | PATCH/ADAPT/REIMPLEMENT/EMULATE/SUBSTITUTE/HYBRID decision compiler | compiler | MEDIUM | Constrained Reimplementation Compiler |
| 120 | Plan Compiler (Execution Protocol) | compiler | MEDIUM | Inline Plan Contract |
| 121 | User Intent Compiler | compiler | MEDIUM | Intent Drift Detector |
| 122 | Work-Class Compilers | compiler | MEDIUM | Playbook Evolution |
| 123 | Capability Baseline Graph | graph | MEDIUM | Capability Authority Registry (UCR-CIF) |
| 124 | Capability Dependency Graph (UCR-CIF) | graph | MEDIUM | Capability Graph |
| 125 | Critical Capability Paths | graph | MEDIUM | Institutional Ascension Ladder |
| 126 | Escalation Debt Graph | graph | MEDIUM | Institutional Debt Taxonomy |
| 127 | Global Bottleneck Map | graph | MEDIUM | IFC Bottleneck Cascade |
| 128 | IFC Causal Edge Types | graph | MEDIUM | IFC Node Universality |
| 129 | Mechanism Graph | graph | MEDIUM | Universalization Compiler |
| 130 | Opportunity Graph | graph | MEDIUM | Opportunity Discovery (IFC) |
| 131 | State Transition Failure Graph | graph | MEDIUM | NONE |
| 132 | Temporal Capability Graph | graph | MEDIUM | Bidirectional Institutional Evolution |
| 133 | Temporal Decision Graph | graph | MEDIUM | Decision Reopening Engine |
| 134 | Assumption Registry | registry | MEDIUM | NONE |
| 135 | Autonomy Benchmark Vault | registry | MEDIUM | Autonomy Canary |
| 136 | Baseline Packages by Archetype | registry | MEDIUM | Baseline Packages |
| 137 | Baseline Propagation Set | registry | MEDIUM | Universal Baseline Compiler |
| 138 | Baseline generation per family | registry | MEDIUM | System Family Identity |
| 139 | Benchmark Retirement | registry | MEDIUM | Benchmark Retirement |
| 140 | Capability Authority Registry | registry | MEDIUM | Capability Ratchet |
| 141 | Certified Construction Primitives | registry | MEDIUM | Baseline Packages by Archetype |
| 142 | Cheap Falsification Library | registry | MEDIUM | Trap Registry |
| 143 | Claim-surface coverage matrix | registry | MEDIUM | NONE |
| 144 | Comparison harness confound registry | registry | MEDIUM | NEVER TRUST A DIFF UNTIL YOU KNOW WHAT ELSE  |
| 145 | Constitutive Capability Set | registry | MEDIUM | Constitutive Baseline Ratchet |
| 146 | Decision Memory | registry | MEDIUM | User Intent Compiler |
| 147 | Drift families universal | registry | MEDIUM | Continuous Integrity Mode |
| 148 | Execution Memory | registry | MEDIUM | Decision Memory |
| 149 | External Assumption Registry | registry | MEDIUM | Crawl OS |
| 150 | Failure Family Authority | registry | MEDIUM | NONE |
| 151 | Family Completeness Genome | registry | MEDIUM | Capability Registry / Baseline Completeness  |
| 152 | HARD/TARGET/TIER-2/DEVIATION requirement tiering | registry | MEDIUM | DEVIATION IS A STATE, NOT A SECRET |
| 153 | Hypothesis Seeds structure | registry | MEDIUM | Failure Hypothesis Library |
| 154 | Institutional One-Shot Memory | registry | MEDIUM | Autonomy Compression |
| 155 | Intervention Genomes | registry | MEDIUM | Intervention Root-Cause Analysis |
| 156 | Knowledge Vault as Evidence Memory | registry | MEDIUM | UKDL Three-Level Distillation |
| 157 | Numerical degeneracy guards | registry | MEDIUM | SCALE-DEGENERACY TESTING |
| 158 | RICH_INTERACTIVE_APP baseline | registry | MEDIUM | Constitutive Baseline Ratchet |
| 159 | Regression Vault | registry | MEDIUM | NONE |
| 160 | Semantic Identity Registry | registry | MEDIUM | Capability Authority Registry |
| 161 | Sensory Benchmarks | registry | MEDIUM | GEX44 as Player/Hardware Reality Cortex |
| 162 | Seven mission capital types | registry | MEDIUM | NONE |
| 163 | Simulator Coverage Map | registry | MEDIUM | Zero-Boot Engineering |
| 164 | Six mission capital types | registry | MEDIUM | NONE |
| 165 | System Family Identity | registry | MEDIUM | Universal Baseline Compiler |
| 166 | Trap Registry | registry | MEDIUM | Negative Knowledge Compounding |
| 167 | Universal Pattern Families | registry | MEDIUM | Cross-Runtime Transfer |
| 168 | Universal Unknown-Unknown Frontier | registry | MEDIUM | Universal Software Integrity & Foresight Bas |
| 169 | Architecture Evolution Engine | subsystem | MEDIUM | Architecture Evolution Engine |
| 170 | Assumption Explosion Engine | subsystem | MEDIUM | RCFC |
| 171 | Assumption Interaction Engine | subsystem | MEDIUM | RCFC |
| 172 | Autonomous Experiment Factory | subsystem | MEDIUM | Autonomous Experiment Factory |
| 173 | Autonomous Frontier Discovery | subsystem | MEDIUM | Institutional Leverage Graph |
| 174 | Capability Consumption Telemetry | subsystem | MEDIUM | Context Outcome Attribution |
| 175 | Causal Blast Radius / Prevention Ascension Funnel | subsystem | MEDIUM | RCFC |
| 176 | Composition Opportunity Mining | subsystem | MEDIUM | Emergent Capability Detection |
| 177 | Consolidation Opportunity Miner | subsystem | MEDIUM | Duplication As Institutional Failure |
| 178 | Context Outcome Attribution | subsystem | MEDIUM | Context ROI Ratchet |
| 179 | Counterfactual Capability Mining | subsystem | MEDIUM | Improvement Propagation Simulator |
| 180 | Crawl Cortex | subsystem | MEDIUM | Crawl OS |
| 181 | Emergent Capability Detection | subsystem | MEDIUM | Capability Graph |
| 182 | Escape Funnel / Meta-Escape Funnel | subsystem | MEDIUM | RCFC |
| 183 | Failure Frontier Generator | subsystem | MEDIUM | Synthetic Adversarial Worlds |
| 184 | Falsification-first routing / Information Gain Planner | subsystem | MEDIUM | RCFC |
| 185 | Friction Mining | subsystem | MEDIUM | Counterfactual Capability Mining |
| 186 | Funnel Self-Red-Team / Blind-Domain Detector / Funnel Coverage Graph | subsystem | MEDIUM | RCFC |
| 187 | Game Instrumentation Factory | subsystem | MEDIUM | UGPEP |
| 188 | Geometry Comparator / Visual Comparator / Semantic Comparator / Perceptual Del | subsystem | MEDIUM | Reference Reconstruction Pipeline |
| 189 | Improvement Propagation Simulator | subsystem | MEDIUM | Institutional Leverage Graph |
| 190 | Inflection Point Mining | subsystem | MEDIUM | Temporal Capability Graph |
| 191 | Institutional Autofactoring | subsystem | MEDIUM | Pattern-to-Primitive Ascension |
| 192 | Institutional Duplicate Detection | subsystem | MEDIUM | Knowledge Linker |
| 193 | Institutional Garbage Collector | subsystem | MEDIUM | Institutional State Governance |
| 194 | Institutional Observability | subsystem | MEDIUM | Institutional State Governance |
| 195 | Institutional Replay | subsystem | MEDIUM | Institutional Replay |
| 196 | Knowledge Linker | subsystem | MEDIUM | Institutional State Governance |
| 197 | Measurement methodology as baseline | subsystem | MEDIUM | NONE |
| 198 | Opportunity Clustering | subsystem | MEDIUM | Opportunity Graph |
| 199 | Opportunity Discovery (IFC) | subsystem | MEDIUM | Hard Safety Floors |
| 200 | Positive Loop Miner | subsystem | MEDIUM | Improvement Chain Attribution |
| 201 | Self-Healing Selector Fabric | subsystem | MEDIUM | Crawl OS |
| 202 | Session Discovery Stream | subsystem | MEDIUM | UDFLL |
| 203 | Source Authority Resolver | subsystem | MEDIUM | Crawl OS |
| 204 | Subtraction Funnel | subsystem | MEDIUM | RCFC |
| 205 | Temporal Funnel / Long-horizon funnel | subsystem | MEDIUM | RCFC |
| 206 | Time-Machine Evaluation | subsystem | MEDIUM | Institutional Replay |
| 207 | Universal Provenance & Lineage Intelligence | subsystem | MEDIUM | Universal Software Integrity & Foresight Bas |
| 208 | Universal Transfer Evaluator | subsystem | MEDIUM | Knowledge Upward Movement |
| 209 | Accidental-Pass Failures | system | MEDIUM | RELATIONAL FAILURE GENOMES |
| 210 | Agent Failure Observatory | system | MEDIUM | Behavioral Failure Forensics |
| 211 | Approximation Regime Failures | system | MEDIUM | RELATIONAL FAILURE GENOMES |
| 212 | Capital Allocation Model | system | MEDIUM | IFC |
| 213 | Engineering Policy VM | system | MEDIUM | Institutional State Governance |
| 214 | Hardware Truth Network | system | MEDIUM | NONE |
| 215 | Institutional Intelligence Engine | system | MEDIUM | Universal Engineering Foundation Runtime |
| 216 | Instrumentation Reality Failures | system | MEDIUM | RELATIONAL FAILURE GENOMES |
| 217 | KIFS | system | MEDIUM | NONE |
| 218 | KME Universal Capability Ratchet & Compounding Excellence Flywheel | system | MEDIUM | KME Universal Excellence Ratchet Flywheel |
| 219 | Masking Layer Failures | system | MEDIUM | RELATIONAL FAILURE GENOMES |
| 220 | Measurement Confound Failures | system | MEDIUM | RELATIONAL FAILURE GENOMES |
| 221 | Multi-Runtime Portability Pack | system | MEDIUM | Universal Baseline Compiler |
| 222 | Multi-Writer Institutional Runtime | system | MEDIUM | Institutional State Governance |
| 223 | Observability Difficulty Engine | system | MEDIUM | Self-Evolving Diagnostic Instrumentation |
| 224 | Project Operational Memory / Knowledge Vault / UKDL three-layer memory | system | MEDIUM | NONE |
| 225 | Scrapling | system | MEDIUM | Crawl OS |
| 226 | Software Evolution Intelligence | system | MEDIUM | Universal Engineering Foundation Runtime |
| 227 | Software Evolution Intelligence (external acquisition integration) | system | MEDIUM | NONE (peer system consuming UERAL) |
| 228 | Temporal Staleness Failures | system | MEDIUM | RELATIONAL FAILURE GENOMES |
| 229 | UERAL (Universal External Reality Acquisition Layer) | system | MEDIUM | Crawl OS (absorbed into) |
| 230 | Acquisition Router (Tier 0-4) | compiler | LOW | UERAL |
| 231 | Capability Budget Compiler | compiler | LOW | Constrained Reimplementation Compiler |
| 232 | Game Development Session Compiler | compiler | LOW | UGPEP |
| 233 | Question-to-Policy Compiler | compiler | LOW | Autonomous Experimentation |
| 234 | Question-to-Primitive Compiler | compiler | LOW | Question-to-Policy Compiler |
| 235 | Self-evolving Skill Compiler | compiler | LOW | Skill Projection Layer |
| 236 | Institutional System Graph | graph | LOW | Shared institutional primitive planes |
| 237 | Unlock Graph | graph | LOW | Capability Option Value |
| 238 | Algorithm properties as capability metadata | registry | LOW | Optimize using domain invariants |
| 239 | Baseline Cache (UCR-CIF) | registry | LOW | Baseline Caching |
| 240 | Claim vocabulary epistemic precision | registry | LOW | Epistemic Integrity |
| 241 | Context Source Registry | registry | LOW | UBC |
| 242 | Game-Class Baselines | registry | LOW | Wii Production Capability Genome |
| 243 | Implementation debt vs accepted deviation distinction | registry | LOW | DEVIATION IS A STATE, NOT A SECRET |
| 244 | Parameter ownership baseline | registry | LOW | ONE VALUE CONTROLLING MULTIPLE SEMANTIC DOMA |
| 245 | Twin Divergence Incident | registry | LOW | TWIN != TRUTH |
| 246 | Authority Funnel | subsystem | LOW | RCFC |
| 247 | Boundary Funnel | subsystem | LOW | RCFC |
| 248 | Capability Challenger System | subsystem | LOW | IFC (Institutional Frontier/allocation) |
| 249 | Contrafactual/Reverse Counterfactual Reconstruction | subsystem | LOW | RCFC |
| 250 | Funnel Compression Engine | subsystem | LOW | RCFC |
| 251 | Funnel Reopen Trigger / Counterexample Memory | subsystem | LOW | RCFC |
| 252 | MarkItDown | subsystem | LOW | Crawl OS |
| 253 | Masking-Layer Funnel | subsystem | LOW | RCFC |
| 254 | Representation Funnel | subsystem | LOW | RCFC |
| 255 | Scale Inversion | subsystem | LOW | RCFC |
| 256 | Source Authority Router | subsystem | LOW | UERAL |
| 257 | Symmetry Breaking Funnel | subsystem | LOW | RCFC |
| 258 | Baseline & Policy Plane | system | LOW | Shared institutional primitive planes |
| 259 | Construction/Failure/Intervention Event Stream | system | LOW | Shared institutional primitive planes |
| 260 | Evidence & Knowledge Plane | system | LOW | Shared institutional primitive planes |
| 261 | Time-step invariance pack | system | LOW | Universal Baseline Compiler |
| 262 | Universal Evaluation Plane | system | LOW | Shared institutional primitive planes |

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
| Session Failure Stream | registry | HIGH | 2 |
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