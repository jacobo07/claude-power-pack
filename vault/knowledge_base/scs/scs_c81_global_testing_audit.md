# SCS C81 -- Global-Testing-Audit-Active

Sealed: 2026-07-08 | State: Sealed | UKDL: `PR-TEST-AUDIT-BEFORE-FEATURE-001`, `T-MINECRAFT-TESTING-CONCENTRATION-001`

## Summary

Exhaustive testing audit across the Owner's 8 active repos, evidence-first. Taxonomy
F1-F8 sealed. Every finding backed by an observed test-runner result -- zero invented
falencias. Dataset in `vault/knowledge_base/testing/` + copy in
`C:\Users\User\Downloads\PP-Testing-Audit-2026-07-08\`. **V-gates x3 hermetic** is the
reference standard.

## Repos audited (domain-classified, corrected against disk)

| repo | domain | AUDIT-B result |
|---|---|---|
| claude-power-pack | PP | GREEN 43/43, but 70/76 test files out-of-tree (F5) |
| TUA-X | SaaS | 4,368 default + 157 + 232 green; 390 orphaned by `testpaths` (F5) |
| KobiiCraft | Minecraft | GREEN 1,596 + 10 (JDK21); `EconomyService` zero refs (F1/F8) |
| GEO-audit | SaaS | 203/204; hermeticity break polluting `C:\nonexistent` (F5) |
| InfinityOps | SaaS | UNVERIFIED -- `mix compile` fails, deps unlocked (F2) |
| CostaLuz Lawyers | SaaS | UNVERIFIED -- Elixir won't compile; `sobelow` inert (F2/F8) |
| KobiiSports Resort | Wii | NOT host-runnable -- GX-coupled C drivers (F1/F6) |
| KobiiAI | content/vault | N/A -- no code (classification corrected) |

## Premises disproved before writing (evidence discipline)

- **KobiiAI is not a Minecraft repo** (zero Java, no pom/gradle) -> re-classified to
  content/vault; prevented a fabricated F1.
- **KobiiCraft is not untested** -> 268 JUnit files, 1,596 passing assertions. The plan's
  `T-MINECRAFT-TESTING-BLIND-SPOT-001` wording ("sin ningun test") was empirically false;
  rewritten as `T-MINECRAFT-TESTING-CONCENTRATION-001` (232/268 files in one plugin,
  MockBukkit in 1 of 90 poms, `EconomyService` zero test references).

## What shipped

| Piece | Artifact |
|---|---|
| F1-F8 taxonomy + heatmap | `vault/knowledge_base/testing/testing_failure_taxonomy.md` |
| Universal standard + per-stack adaptation | `testing_universal_standards.md` |
| 8 per-repo datasets (each >=2000 words) | `testing_<repo>_audit.md` |
| Index + summary | `GLOBAL_TESTING_AUDIT_INDEX.md`, `SUMMARY.md` |
| Downloads copy (12 files) | `C:\Users\User\Downloads\PP-Testing-Audit-2026-07-08\` |

## The five ROI-ranked findings

1. InfinityOps + CostaLuz Elixir won't compile (unlocked deps) -> 149 ExUnit files
   unverifiable. Fixing the env unblocks two whole repos.
2. TUA-X `testpaths` orphans 390 passing tests from the default run.
3. GEO-audit hermeticity break pollutes the host drive root, defeats a sibling suite.
4. KobiiCraft `EconomyService` -- zero test references (most abusable surface).
5. PP runs 6 of 76 test files in the canonical invocation.

## Evidence (observed, side-effect-free AUDIT-B)

- `pytest tests/` PP 43 passed; GEO-audit 203 passed / 1 failed (traced to
  `test_no_fake_output.py:185` global write).
- `mvn -o test` JDK21: KobiMapEngine 1,596/0/15, kobicore 10/0.
- TUA-X: default 4,368 collected; `tests/` 157 passed; `CW_UGC_SYSTEM/tests` 232 passed.
- `mix compile` InfinityOps + CostaLuz: FAIL, "dependency is not locked".
- KobiiSports C drivers `#include` `gx_*` -> hardware-coupled, not host-runnable.

## Scope boundaries (honest non-execution)

Did NOT: run `mix deps.get` / provision Postgres (Elixir = unverified, not failed);
stand up devkitPPC (Wii = not runnable); run the full 4,368-test TUA-X suite to
completion (collected-clean); delete `C:\nonexistent` (HR-CASCADE-002, Owner decision);
run JS/TS suites (counted, not executed).
