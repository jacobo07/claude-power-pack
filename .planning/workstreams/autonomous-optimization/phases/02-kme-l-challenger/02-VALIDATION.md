---
phase: "2"
slug: "kme-l-challenger"
# status lifecycle: draft (seeded by plan-phase) -> validated (set by validate-phase)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-07"
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Source: 02-RESEARCH.md
> "## Validation Architecture". Governing spec: `vault/specs/autonomous-optimization.md`.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | repo-native gate scripts (no pytest): `V-<DOMAIN>-<NAME>` gates, `--drill` mutation drill, summary `*_PASS=n/m threshold=m/m` |
| **Config file** | none |
| **Quick run command** | `python3 -I tools/test_kme_pillars.py` and `python3 -I tools/test_kme_challenger.py` |
| **Full suite command** | both with `--drill`; `python3 -I tools/test_usage_index_v5.py` (+ `--drill`) if `tools/usage_index.py` changed; `python3 tools/test_incremental_cognition_program.py --generation 2 --final` |
| **Estimated runtime** | quick ~30 s; full ~6 min (drills); real-corpus equivalence ~25-31 s per scoped run |

---

## Sampling Rate

- **After every task commit:** the quick run commands (hermetic part).
- **After every plan wave:** both suites with `--drill`, then the real-corpus equivalence gates.
- **Before `/gsd-verify-work`:** full suite green, the comparison table committed, every negative control shown red once.
- **Max feedback latency:** 60 seconds for the quick run.

---

## Per-Criterion Verification Map

The planner maps each task to one or more rows; task IDs are filled when PLAN.md files exist.

| Criterion / Req | Behaviour | Test type | Gate (proposed) | Negative control |
|---|---|---|---|---|
| 1 / AO-07 access plan | tier order index -> scoped raw -> global raw only on an explicit cross-project flag | hermetic | `V-KMEC-PLAN-ORDER` | flag unset: an out-of-scope fixture file is never opened (spy) |
| 1 / AO-07 deopt | a guard failure falls back and logs its reason | hermetic | `V-KMEC-DEOPT-LOGGED` | each guard (index missing, schema < 5, DRIFTED, UNMEASURED, watermark, pattern drift, no first_ts per IN-04) driven red once with the reason asserted; all-green control takes the index tier |
| 1 / KS-4 | forced champion / scoped plan honoured; unknown plan exits 2 | hermetic | `V-KMEC-KS4-FORCED` | forced champion opens the out-of-scope fixture; forced challenger with a failing guard exits non-zero |
| 1 invalidation keys | source watermark, parser version, attribution version, metric definition recorded; each change detected | hermetic | `V-KMEC-KEYS-FOUR` | one mutant per key |
| 2 / AO-09 equivalence | D, E, F, G, H, I, L reproduce the committed files after masking `measured_at`, `command`, H `commit` | real corpus | `V-KMEC-EQUIV-REAL-{D..L}` | `V-KMEC-EQUIV-PERTURB`: one perturbed copy per file is reported DIFFERENT; `corpus.sessions_scanned == 568` asserted |
| 3 table | wall, raw bytes, unique bytes, files opened, cross-project bytes, index bytes for champion (cited Run 5), scoped (cited Run 6 + re-measured `all`+`rank`), challenger cold / warm / post-delta | real corpus | `tools/strace_io_sum.py` over `strace -f -y` logs; evidence `gen2/evidence/P-table-gex44.md` | `V-KMEC-SUM-EXACT`: a synthetic log with a known byte count sums exactly |
| 3 KME-only opens zero CostaLuz | forbidden bytes == 0 for the challenger | real corpus | `V-KMEC-COSTALUZ-ZERO-REAL` | same query with `|CostaLuz` added reports > 0 (about 99.7 MB / 44 files); a synthetic fixture pins the detector hermetically |
| 4 stale cache | one source changed -> only its closure invalidated; parser change -> all; metric change -> that pillar only | hermetic (fixture tree copy) | `V-KMEC-STALE-SOURCE`, `-PARSER`, `-METRIC` | unchanged tree -> all hits; invalidate-all and invalidate-none mutants killed |
| 5 allowed loss | challenger vs scoped on N=5 repeats (median wall, raw bytes); narrow or reject with a falsification artifact naming [P] | measurement + ledger | `tools/ic_gen2.py` P rows | a P close without an artifact naming [P] is rejected by the existing gate |
| read-only | corpus manifest and index DB sha unchanged | real corpus | manifest before / after | a deliberate touch of a scratch copy changes the manifest |

*Status per row is tracked in the plans' SUMMARY files.*

---

## Wave 0 Requirements

- [ ] `tools/test_kme_challenger.py` — gates for criteria 1, 2, 4 and the hermetic part of 3
- [ ] `tools/strace_io_sum.py` — tracked replacement for scratch `strace_sum.py` (per-project, distinct opens, unique bytes, forbidden-regex columns)
- [ ] fixture transcript tree builder reusing `tools/test_kme_pillars.py` helpers, with an out-of-scope project dir
- [ ] comparator normalisation list in code, pinned by the perturb control
- Framework install: none (stdlib only)

---

## Manual-Only Verifications

All phase behaviours have automated verification. Real-corpus gates run on the gex44 plane only and are labelled `plane: gex44`.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60 s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
