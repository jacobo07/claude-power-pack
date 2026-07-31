# Emergence Runtime — Novelty Audit

Generated 2026-07-31. Hypothesis under test: "No mechanism in the Power Pack
detects the same pattern appearing simultaneously in distinct Owner
projects." Budget: 30 minutes (per brief); audit completed within budget.

## Verdict: EXTEND_EXISTING_OWNER (not novel)

A real, live, cross-repo pattern detector already exists:
**`tools/dataset_enricher.py::write_cross_project_patterns()`**.

## What it does

- Scans "Power-Pack vault PLUS every Cursor Projects repo"
  (`CURSOR_PROJECTS = Desktop/Cursor Projects`, `tools/dataset_enricher.py:41`)
  — genuinely cross-repo, the Owner's real active project portfolio, not a
  single-repo scope.
- `harvest()` collects error/lesson/mistake entries per project.
- Each entry is classified into a keyword TAXONOMY (categories).
- `write_cross_project_patterns()` groups entries by category, keeps only
  categories present in **2+ distinct projects** ("transversal patterns"),
  ranks them by project-breadth then frequency, and writes
  `CROSS-PROJECT-PATTERNS.md`.

This is structurally exactly what "Emergence Runtime" describes — for the
error/lesson pattern type specifically. The done-gate's own worked example
("the orphan hook pattern that appeared in multiple projects") is itself an
error/lesson-taxonomy pattern, squarely inside this existing scope.

## What it's missing (the real gap)

`CROSS-PROJECT-PATTERNS.md` has **zero consumers anywhere in the repo** —
grep confirms it's referenced only inside its own producer file. It is a
report nobody reads, not a decision pipeline: no abstraction proposal ever
reaches `OWNER_QUEUE` or any other owner. This is the identical
orphan-producer shape as `corpus_roi.py` (see the corpus_roi consumer
resolution the same session, `vault/OWNER_QUEUE.md`) — a real signal with no
live surface to act on it.

That gap is wiring, not architecture. See Sprint C (this plan) for the fix:
`escalate_transversal_patterns()`, feeding the already-computed transversal
list into `modules/owner_queue/owner_queue.py::append()`.

## Candidates checked, evidence per mechanism (not name)

| Candidate | Mechanism read | Cross-repo scope? | Verdict |
|---|---|---|---|
| `duplicate_to_advantage/d2a_engine.py` (D2A) | `_PP_ROOT`-scoped (`Path(__file__).resolve().parents[2]`); no other-repo read | No | Not it |
| `modules/liveness/reachability.py` | `_repo_root()` returns `_PP_ROOT`; module inventory + live seeds both scoped to this repo | No | Not it |
| `modules/daif/` | No cross-project / other-repo reference found in sweep | No | Not it |
| CPCSC / AISHF | No matching module directories exist under these names anywhere in the repo — prior *proposal* names in vault prose only (see `project_ksf_deferred_after_igef` memory: proposed families, never implemented) | N/A | Not it — never built |
| KSF | Same as above | N/A | Not it — never built |
| `modules/autoresearch/cross_signal_bus.py::find_cross_project_matches()` | Matches *external* RSS/YouTube research signals against a per-project `cross_project_keywords` config — triages incoming news relevance, not the PP's own recurring code/behavior patterns | Cross-project by name, wrong domain | False positive on name only |
| `modules/token-optimizer/cross_project_dedup.py` | Genuinely scans `Desktop/Cursor Projects`; compares CLAUDE.md rule-text similarity via `difflib` for token dedup | Yes | Adjacent, different purpose (token savings, not pattern/abstraction detection) |
| `tools/dataset_enricher.py::write_cross_project_patterns()` | Genuinely scans `Desktop/Cursor Projects`; detects error/lesson-taxonomy categories recurring in 2+ projects | Yes | **Real owner** |

Full keyword sweep run: `cross_project`, `cross-project`, `emergence`,
`multi_project`/`multi-project`, `pattern_detection`, `shared_pattern`,
`antipattern_federation`, `project_federation`, `simultaneous`,
`cross_repo_pattern` — 13 `.py` files matched; every mechanism above was read
directly, not inferred from the matching name (this is the failure mode
HR-NOVELTY-001 exists to prevent — a proposal's own curated "doesn't exist"
list, unchecked against a discovered sweep).

## Reopen condition

If the Owner later wants pattern types beyond error/lesson — e.g. a
"solution" pattern or a "benchmark candidate" pattern recurring across
projects — that is a TAXONOMY extension to `dataset_enricher.py`'s existing
category list, a small, scoped follow-up. It is NOT grounds to reopen this
novelty question or to build a parallel system: the cross-repo scan,
per-project harvesting, and transversal-detection logic all already exist and
would be reused as-is.

## Relation to HR-NOVELTY-001

This is the 7th recorded instance (per `HR-NOVELTY-001` evidence log in
`CLAUDE.md`) of a proposed new institutional mechanism turning out to be
majority- or fully-owned once checked against a discovered sweep instead of
the proposal's own assumed-absent list. Consistent with the prior six:
AISHF, RE Baseline, KSF, the UKR Compendium, and now Emergence Runtime.
