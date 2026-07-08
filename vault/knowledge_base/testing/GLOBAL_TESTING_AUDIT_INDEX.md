# GLOBAL TESTING AUDIT — INDEX

> Generated 2026-07-08 · Owner stack: 8 repos across 4 domains · Method: read-only
> inventory + side-effect-free test-runner execution (AUDIT-B scope confirmed at STOP #1).
> Every finding is backed by an observed command result — no invented falencias.

## Datasets in this directory

| File | Scope |
|---|---|
| `testing_failure_taxonomy.md` | F1–F8 sealed taxonomy + cross-repo heatmap |
| `testing_universal_standards.md` | V-gates ×3 hermetic reference + per-stack adaptation + priority ladder |
| `testing_claude-power-pack_audit.md` | PP — Python/PS/JS |
| `testing_TUA-X_audit.md` | TUA-X — Python/Next.js |
| `testing_KobiiCraft_audit.md` | KobiiCraft — Java 21/Paper + Python |
| `testing_InfinityOps_audit.md` | InfinityOps — Elixir/Phoenix ×3 |
| `testing_CostaLuz-Lawyers_audit.md` | CostaLuz — Elixir ×3 + Python |
| `testing_GEO-audit_audit.md` | GEO-audit — Python |
| `testing_KobiiSports-Resort_audit.md` | KobiiSports Resort — C/C++ Wii homebrew |
| `testing_KobiiAI_audit.md` | KobiiAI — content/vault (no code, N/A) |

## Domain classification (corrected against disk)

- **Minecraft:** KobiiCraft. *(KobiiAI was re-classified OUT — it is a content/vault repo,
  not a plugin repo. KobiiAI grouping in the original plan was disproved.)*
- **Wii/videojuego:** KobiiSports Resort (C/C++, libogc+GX, devkitPPC).
- **Business/SaaS:** TUA-X, InfinityOps, CostaLuz Lawyers, GEO-audit.
- **PP:** claude-power-pack.
- **Content/vault (no test surface):** KobiiAI.

## Observed AUDIT-B results (the evidence spine)

| repo | runner result | status |
|---|---|---|
| claude-power-pack | `pytest tests/` → 43 passed | GREEN (but 70/76 files out-of-tree) |
| TUA-X | default 4,368 collected; `tests/` 157 passed; `CW_UGC` 232 passed/1 skip | GREEN where run; 390 orphaned |
| KobiiCraft | `mvn -o test` JDK21 → KobiMapEngine 1,596/0/15; kobicore 10/0 | GREEN (needs JDK 21) |
| GEO-audit | `pytest tests/` → 203 passed, 1 failed | 1 hermeticity break (host pollution) |
| InfinityOps | `mix compile` FAILS (deps unlocked) | UNVERIFIED — needs deps.get + PG |
| CostaLuz | `mix compile` FAILS (deps unlocked) | UNVERIFIED — needs deps.get + PG |
| KobiiSports | C drivers link GX; need devkitPPC | NOT RUNNABLE on host |
| KobiiAI | no code | N/A |

## The five findings that matter (ranked by ROI)

1. **InfinityOps + CostaLuz Elixir won't compile** (unlocked deps) → 149 ExUnit files
   unverifiable. Highest ROI: fixing the env unblocks auditing two whole repos.
2. **TUA-X orphans 390 passing tests** via `testpaths` scope → one config line from
   protecting nothing.
3. **GEO-audit hermeticity break** pollutes `C:\nonexistent` on the host and defeats a
   sibling suite's real assertion.
4. **KobiiCraft `EconomyService` has zero test references** → F1/F8 at the most abusable
   surface, despite 1,596 passing tests one plugin over.
5. **PP runs 6 of its 76 test files** in the canonical invocation → F5 collection gap in
   the self-described most-audited repo.

## Cross-references

- Taxonomy heatmap: `testing_failure_taxonomy.md` § Cross-repo F-class heatmap.
- Priority ladder + per-stack done-gates: `testing_universal_standards.md` §§ 3–4.
- Seals produced by this audit: PR-TEST-AUDIT-BEFORE-FEATURE-001,
  T-MINECRAFT-TESTING-CONCENTRATION-001 (rewritten from the plan's
  BLIND-SPOT wording per evidence), SCS C81. See SUMMARY.md in the Downloads copy.
