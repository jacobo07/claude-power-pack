---
title: UCR-CIF Compendium — Phase 0 Reality Scan
date: 2026-08-25
status: MEASURED (every number in this file was produced by a filesystem sweep this session)
source_corpus: "Dataset Claude Power Pack Universal Construction Ratchet & Compounding Intelligence Fabric 1.txt"
source_path: C:\Users\User\Downloads\
governing_law: PR-COVERAGE-BY-CONSTRUCTION-001 (denominator must be DISCOVERED, never curated)
---

# Phase 0 — Reality Scan

This file answers one question before any dataset is written: **what does this estate
already own?** Every prior corpus build in this repository that skipped this step lost the
families it chartered. Every number below is a measurement, not a recollection.

## 1. The source corpus, measured

| Property | Observed |
|---|---|
| Bytes | 1,521,366 |
| Lines | 75,350 |
| Words | 204,153 |
| Format | **Not** markdown. A continuous Spanish/English design conversation. |
| Markdown headings | 23 total, and all 23 fall inside the contamination band below |
| Origin context | Opens in **KME** (a Minecraft map-engine), generalizes to CPP by ~line 2,200 |
| Content distribution | Uniform: ~2,300–2,800 non-empty lines per 5,000-line block, end to end |

### 1.1 Contamination region (material finding — re-measured, two prior figures were wrong)

Part of the file is pasted-in Claude/Codex harness documentation — escalation-request
semantics, sandbox modes, a `slides` skill folder, PDF/DOCX recipes, plugin-naming rules,
and a Codex/GPT-5 system-prompt fragment. It is **not** corpus.

Two earlier estimates were both wrong and are recorded here rather than quietly replaced:

| Estimate | Claim | Verdict |
|---|---|---|
| This file's first pass | one band, ≈60,000–65,500, ~7 % | **too narrow** — missed runs at 69,300 and 70,000 |
| Range-4 inventory agent | one contiguous band, 60,177–70,365, ~13.5 % | **too wide** — lines 66,000–68,100 and 70,300+ are Spanish corpus |

**Measured** at 100-line resolution using two independent signals (harness markers vs
Spanish function-word density; a pasted English system prompt cannot score on both):

```
60200..60899   61700..62799   63200..63499   63800..64299   64700..65099
65400..65499   68200..68299   69300..69699   70000..70299
```

**Nine discontinuous runs, ~3,900 confirmed lines ≈ 5 %.** The region is *interleaved*, not
contiguous: genuine corpus sits between the runs, most clearly at 66,000–68,100 (Spanish
density 3–8 per 100 lines) and continuously from 70,300 to the end of file (5–17 per 100).

A residual ambiguity is stated rather than smoothed: windows 68,300–69,200 score zero on
*both* signals. They are likelier continued harness text than corpus, but the detector
cannot prove it, so the true contaminated figure is **5–8 %**, not a point value.

Accepting the agent's contiguous band would have discarded roughly 2,000 lines of real
corpus — a coverage loss, in the direction §5 forbids. The runs are classified
`NON-SYSTEM CONCEPT / external reference` in the coverage matrix, **not dropped**.

**Corpus lines available for inventory: ~71,450 of 75,350.**

### 1.2 Mechanically extracted candidates

809 capitalized multi-word phrases ending in a system-suffix; 1,281 raw acronyms
(779 appearing twice or more). Highest-frequency system acronyms with their line spans:

`UKDL`(185) · `UBC`(183, L23434–75323) · `IFC`(170, L7208–75323) · `KIFS`(158, L27810–74873) ·
`KME`(140) · `UCR-CIF`(57) · `HIC-OAR`(55) · `UFIA`(46) · **`KSEIP`(41)** · `TTPE`(36) ·
`LAAS`(35) · **`UPSEIP`(28)** · **`UERAL`(26)** · `KMEIP`(25) · `UFIA-EBF`(23) ·
**`UEFB`(23)** · `RCFC`(22) · `USIFB`(21)

**The four bolded acronyms appear nowhere in the mission prompt's §6 seed list.** This
confirms the instruction that the seed list is an anti-omission aid and the file is the
coverage authority — a build scoped to §6 would have missed real systems outright.

## 2. The discovered denominator

Enumerated from the filesystem, not from memory or any registry:

| Surface | Count |
|---|---|
| `modules/` | 84 |
| `vault/knowledge_base/` families | 26 |
| `vault/knowledge_base/` loose files | 40 |
| `commands/` | 73 |
| `agents/` | 12 |
| `hooks/` | 39 |
| `governance/` | 11 |
| `vault/` subdirectories | 70 |
| `tools/*.py` | 328 |
| `rules/` | 20 |
| **Searchable text corpus** | **4,458 files · 59 MB** |

### 2.1 Existing dataset corpus — the number that reframes this mission

| | Observed |
|---|---|
| Dataset families | **26** |
| Parts written | **266** |
| Words | **1,841,936** |

Ten largest families by volume:

| Family | Parts | Words | Words/Part |
|---|---:|---:|---:|
| `cpp_ias` | 23 | 496,679 | 20,322 |
| `d2a_fabric` (DAIF) | 9 | 303,231 | 33,198 |
| `crawl_os` | 12 | 181,996 | 15,166 |
| `clae` | 37 | 156,953 | 3,570 |
| `sqi` | 8 | 119,069 | 14,076 |
| `pp_dataset` | 24 | 86,059 | 3,585 |
| `cpcsc` | 9 | 81,212 | 8,733 |
| `fable_distillation` | 8 | 76,046 | 9,240 |
| `craif` | 6 | 69,937 | 11,171 |
| `dataset_first` | 4 | 45,121 | 9,594 |

**The existing corpus is roughly ten times the total volume of the CommonWealth reference
set**, and its largest per-dataset files (30,000–42,000 words) are four to five times
deeper than a CommonWealth system folder (~7,500 words across 5 parts).

## 3. The quality bar already exists — inherit it, do not re-derive it

§59 of the mission asks for reference-depth benchmarking against CommonWealth,
human-resonance-os and operator-essence. **That measurement has already been performed and
sealed** in `d2a_fabric/DAIF_CANONICAL_MAP.md` §5, which records: CommonWealth UAE
20,502–91,789 words per dataset; human-resonance ~8,000 words/Part; SQI 1,357 words/Part.

The fabrication contract it derives (`sqi/CANONICAL_ONTOLOGY.md` §9) is the standing depth
law: one `.txt` per dataset · `PART I…PART XX` · a `FINAL LAW` closing every Part · dense
prose with numbered subsections and arrow flows · **no markdown headings, bullets, tables or
code fences inside a dataset body** · **1,200–1,500 words per Part**.

Re-deriving a parallel depth standard would itself be the duplication this mission is
supposed to prevent. This build inherits the contract verbatim.

Independent confirmation measured this session against the CommonWealth folders directly:
30 sampled parts, min 995 / median 1,517 / mean 1,717 / max 3,342 words. Consistent.

### 3.1 The contamination gate already exists

§60 asks for a CommonWealth-contamination scan. `SQI_CONTAMINATION_AUDIT` already
quarantines the exact literal set (`CommonWealth`, `CW Ops`, `operator`, `revenue`, `brand`,
`Shopify`, `SKU`, …) at zero hits per Part. This build reuses that gate rather than
building a second one.

## 4. First-pass vocabulary coverage of the source's systems

Each source system's acronym plus its distinctive vocabulary was searched across all 4,458
files. **Interpretation warning, stated up front:** a high score is evidence of ownership;
a **zero is UNKNOWN, never evidence of novelty.** A gate is bounded by its vocabulary, and
an unrecognised idiom reads as zero — zero cannot fall. Every zero row below requires a
second, capability-level sweep before any verdict.

| Source system | Hits | Files | Dominant existing owner |
|---|---:|---:|---|
| Institutional Compression | 2,008 | 346 | `d2a_fabric`, `token-optimizer` |
| Epistemic Type System | 923 | 178 | **`daif_01_type_system_v1`** |
| Crawl OS | 829 | 30 | **`crawl_os` (12 parts, sealed)** |
| Construction Intelligence Record | 689 | 24 | **`daif_02_cir_fabric_v1` (469 hits in one file)** |
| Game Production | 267 | 67 | `knowledge_base`, `research` |
| Institutional Chaos/Mutation | 151 | 27 | `knowledge_base` |
| SEEIP (digital twin, experiment) | 100 | 38 | **`cpp_ias/ias_f3_digital_twin`** |
| Self-hosting governance planes | 75 | 27 | `knowledge_base` |
| KIFS (unknown-unknown) | 50 | 19 | `cpcsc/a2_theory_generator`, `frontier_intelligence` |
| UFIA-EBF (failure immunity) | 36 | 14 | `pp_dataset_18`, **`cpp_ias/ias_d2_immune_system`** |
| IFC (capital allocation) | 29 | 13 | **`cpp_ias/ias_c1_capability_portfolio`** |
| **HIC-OAR, UBC, USIFB, RCFC, KSEIP, UPSEIP, UEFB, TTPE, RIK, CMK, URCE** | **0** | **0** | **UNKNOWN — requires capability-level sweep** |

## 5. Prior art: three measured corpus builds in this repository

This mission is the fourth of its kind here. The three predecessors were all measured:

| Build | Candidates | Built | Rate | Outcome |
|---|---:|---:|---:|---|
| **CPP-IAS** | 150 | 14 | 9 % | ~90 folded as subengines, ~46 REFERENCE |
| **DAIF** | 22 | 8 | 36 % | 6 do-not-build, 8 folded |
| **RE Baseline** | 4 families | 1 | 25 % | CRPF, IGEF and E1–E5 struck *before writing*, saving ~66–80 Parts |

`COMPENDIUM_CLOSURE_REPORT.md` records five consecutive proposals measured as
majority-owned (AISHF 75–80 %, RE Baseline 55–60 %, KSF 70–80 %, CRPF ~80 %, IGEF 0-of-4,
E1–E5 15-of-17). The sealed diagnosis is not that the sources were weak — each source
analyzed itself correctly. It is that **a boundary column was filled in from memory instead
of swept.** CRPF was struck because its charter enumerated three non-owners and never named
`cognitive_os`, the family that actually held ~80 % of the territory.

**The correct prior for this mission is therefore: most of the source's named systems are
already owned at equal or greater maturity.** That is a starting hypothesis to be measured
per system, not an accusation against the source and not a reason to build less than the
mission requires.

## 6. What this does *not* license

The base rate above is an argument about **runtime owners**, not about **coverage**. The
mission's §3 already resolves the tension and its ruling is adopted here verbatim:

> DATASET IDENTITY ≠ RUNTIME PROCESS BOUNDARY.

Every system named by the source receives dataset-level coverage. What the D2A verdict
decides is the *form* that coverage takes — a sovereign dataset, an appended Part, a
Systems-Derived-Catalog entry naming its canonical owner, or a do-not-build ledger row with
the reason recorded. No source concept is left unmapped, and no redundant runtime owner is
manufactured. Both halves of that sentence are hard requirements.

## 7. Corrections to the mission brief's stated premises

Verified against the filesystem, offered as fact, not objection:

1. **Reference paths.** `human-resonance-os` and `operator-essence-intelligence-system` are
   not under `Downloads\Promptsss\`; all three references live under
   `Downloads\! Promptsss\` (leading bang-space). The iteration file *is* at the stated
   `Downloads\Promptsss\Prompts pa iterar\Universal\iteracion-avanzada-universal.txt`. Two
   distinct sibling directories exist and the brief's paths straddle both.
2. **§6 seed list is incomplete**, as the brief itself anticipated — `KSEIP`, `UPSEIP`,
   `UERAL`, `UEFB` and `TTPE` are real, repeatedly-used source acronyms absent from it.
3. **§59 and §60 are already owned.** Reference-depth benchmarking and the
   CommonWealth-contamination gate exist and are sealed; this build inherits both.
4. **§61's promotion targets are largely already baseline.** D2A-before-generation, the
   per-Part depth floor, the coverage matrix and the contamination scan are standing
   obligations in this repo, not novelties to be introduced by this mission.
