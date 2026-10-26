# Cognitive Economy datasets: full-read digests (2026-10-26)

Source: the Owner's zip `Dataset CPP Context Intelligence Fabric.zip` (15 markdown datasets, ~3.0 MB, from the Downloads folder).
Each file here is a digest written by a Sonnet subagent that read its dataset start to end. Coverage per file (total lines, last
line read) is in a "Coverage" or "FINAL COVERAGE" block, sometimes at the END of the digest because it was appended while reading.

Provenance and limits:
- Digests are model output. Line numbers cite the source dataset line as the agent counted it (`[IO.File]::ReadAllLines`); they were
  not re-verified by a second reader. Treat every number as a lead until checked against the dataset.
- The datasets themselves are mostly Owner-to-Claude Code transcript pastes with long assistant replies. Their proposals are
  hypotheses, not measurements, unless a digest says "measured".
- `ksr_kme_opt` and `skyparty_opt` sources are partly mojibake (UTF-8 read as Latin-1); the Spanish stays readable.
- `tok18` source elides a 4,262-line brief (source L73); only its head and tail exist.

| digest | source dataset | source lines |
|---|---|---:|
| tok18 | Dataset CPP TOK-18 Optimization 1 | 23,676 |
| ce_gen1gen2 | Dataset CE Gen1 Gen2 Optimization and Evolution 1 | 2,782 |
| cif | Dataset Context Intelligence Fabric 1 | 17,681 |
| quicklease_seo_geo | Dataset QuickLease SEO + GEO Token Optimization 1 | 5,165 |
| selective_semantic | Dataset CPP Selective Semantic Materialization 1 | 20,439 |
| skyparty_spawn | Dataset CPP SkyParty Spawn Optimization 1 | 2,247 |
| cognitive_virtual_memory | Dataset Cognitive Virtual Memory 1 | 21,451 |
| gsdx_edd | Dataset CPP GSD X EDD Optimization 1 | 5,583 |
| recon_factory | Dataset CPP Recon Factory 1 | 6,696 |
| gsdx_recon_opt | CPP GSD X Reconstruction Factory Optimization 1 | 7,964 |
| skyparty_opt | Dataset CPP SkyParty Optimization 1 | 6,763 |
| ksr_kme_opt | Dataset CPP KSR + KME Optimization 1 | 8,014 |
| orca_dws | Dataset Orca X DWS Optimization 1 | 5,914 |
| cwops_opt | Dataset CPP CW Ops Optimization Mission 1, 1 | 5,743 |
| sidecar_liveqa_opt | Dataset InfinityOps Sidecar Live QA Optimization 1 | 4,930 |

Backlog entry that cites these: `vault/plans/deferred-backlog.md` D37.
Earlier gap scan of `a5/inputs/dataset-dws-optimization-1.md`: reported only in D37 (that dataset was already dispositioned in
`vault/programs/cognitive-economy/a5/LEDGER.md`).
