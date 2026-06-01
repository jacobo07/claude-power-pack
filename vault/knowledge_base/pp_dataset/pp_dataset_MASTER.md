# PP Dataset -- Master Index

**Source:** C:\\Users\\User\\Downloads\\PP_DATASET_20260531T122242Z (1).md
**Sealed:** 2026-06-01 BL-DATASET-001
**Total source lines:** 15,425 / 329 KB
**Sections ingested:** 10 content files + 1 cross-ref + this master

This dataset is the **canonical quality baseline** for the Power Pack as of
2026-06-01. Any new system built after this date MUST satisfy the contracts
documented here or explicitly declare why not (SCS C25, sealed in M14).

## Table of Contents

| # | File | Dataset Part | Lines | Bytes |
|---|---|---|---|---|
| 01 | [pp_dataset_01_identity.md](pp_dataset_01_identity.md) | see file header | 1217 | 58929 |
| 02 | [pp_dataset_02_capabilities.md](pp_dataset_02_capabilities.md) | see file header | 1122 | 32094 |
| 03 | [pp_dataset_03_perf_metrics.md](pp_dataset_03_perf_metrics.md) | see file header | 1550 | 31616 |
| 04 | [pp_dataset_04_gaps.md](pp_dataset_04_gaps.md) | see file header | 1407 | 33884 |
| 05 | [pp_dataset_05_improvements.md](pp_dataset_05_improvements.md) | see file header | 1157 | 24967 |
| 06 | [pp_dataset_06_tech_debt.md](pp_dataset_06_tech_debt.md) | see file header | 966 | 19713 |
| 07 | [pp_dataset_07_architecture.md](pp_dataset_07_architecture.md) | see file header | 976 | 20549 |
| 08 | [pp_dataset_08_onboarding.md](pp_dataset_08_onboarding.md) | see file header | 1908 | 31692 |
| 10 | [pp_dataset_10_cpc_os_spec.md](pp_dataset_10_cpc_os_spec.md) | see file header | 5122 | 92712 |
| 09 | [pp_dataset_09_benchmarks.md](pp_dataset_09_benchmarks.md) | cross-ref | - | - |

## How to read this

- Each file is a contiguous slice of the source dataset with a header.
- Headers state the exact line range and the dataset Part label.
- pp_dataset_10_cpc_os_spec.md is the CPC-OS spec (Parts VIII+IX+X, ~5,100 lines).
- For metrics/benchmarks indexes see pp_dataset_09_benchmarks.md.

## Doctrine reference

- knowledge_vault/core/apex-completion-standard.md -- v15 axis sealed by M14 references this dataset as the baseline.
- ault/knowledge_base/ukdl-universal.md -- Hard Rules and Traps derived from the dataset land here.
- CLAUDE.md -- HR-001..HR-NNN, with dataset-derived HRs sealed by M3+M12.
