# Phase 2: KME-L challenger - Context

**Gathered:** 2026-10-06
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss), unattended worker epoch 2. Facts below
are carried from `vault/specs/autonomous-optimization.md` and the Phase 1 artifacts; each names its source.

<domain>
## Phase Boundary

Goal: ordinary KME analytics stop rescanning raw history.

Success criteria (ROADMAP Phase 2):
1. `kme_pillars` access plan: certified index -> project-scoped raw -> global raw only on an explicit
   cross-project question. A guard failure deopts with a logged reason. Invalidation keyed on source
   watermark, parser version, attribution version, metric definition.
2. Equivalence: the 7 KME-L measurement files (D, E, F, G, H, I, L) reproduce identically from the challenger.
3. Champion vs scoped vs challenger table: wall, raw bytes, unique bytes, raw files opened, cross-project bytes
   exposed. A KME-only query opens zero CostaLuz bytes (a negative control proves the check can fail).
4. Stale-cache control: changing a source or the parser version invalidates exactly the affected closure.
5. If the challenger does not beat the scoped path on repeated queries, narrow or reject it and record why.

Requirements: AO-07 (champion/challenger, shadow/canary/certify/deopt), AO-09 (KME-L measured, challenger by
extension, equal-or-stronger, no unrelated-project raw reads). Ledger pillar: AOP-P (spec line 101).
Kill switch KS-4 (spec line 179): a forced champion or scoped path for `kme_pillars`.

</domain>

<decisions>
## Implementation Decisions

### Carried facts (measured, with source)
- Champion Run 5, unscoped: wall 869 s, read 101.53 GB (spec line 61). Champion Run 6, scoped to
  `KobiiCraft-Core-Files|kme-wt-arena2`: 24 s, 2.83 GB (spec line 62). These are the numbers to beat.
- Frozen KME-L denominator: 102 sessions, 34,871 calls, cache_read 11,549,646,300
  (`vault/programs/incremental-cognition/denominators/kme_audit_2026-10-03.json`).
- Phase 1 substrate: `tools/usage_index.py` v5. `population --select kme --until 2026-10-03T16:13:37Z
  --expect KME-L` on `/home/kobii/ao-scratch/p1/cold.sqlite` is EXACT (01-EVIDENCE.md, re-run 2026-10-06 after
  the review fixes). The index reports MEASURED / EXACT / DRIFTED / UNMEASURED and refuses (UNMEASURED) on a
  legacy file, parse errors, file errors, pattern drift, or an unreadable `--until`.
- Corpus: `/home/kobii/kme-corpus/projects` (Owner-authorized copy), passed explicitly as a root; results are
  labelled `plane: gex44` (spec line 163).

### Claude's Discretion (recorded choices)
- The challenger is an EXTENSION of `wiki/tools/kme_pillars.py` (and `kme_token_audit.py` / `kme_replay.py`
  where they produce the measurement files) that reads from the usage_index; no new parallel engine (AO-09
  "challenger by extension", HR-NOVELTY-001). Reason: the owners exist and the spec names them.
- The champion and the scoped path stay callable unchanged (KS-4); the challenger is opt-in until certified.
- Any UNMEASURED answer from the index is a deopt to the scoped raw path with the index's reason logged, never a
  zero or a partial number.
- Equivalence is byte-identical output of the 7 measurement files, compared by hash, with a negative control
  (one perturbed file must be reported as different).
- Cross-project exposure is measured by the files actually opened (strace or an open-hook), not by the selector's
  intention; the negative control is a deliberately unscoped run that must show non-zero CostaLuz bytes.
- Never write the literal slop marker words in any file (Owner directive 2026-10-06); build such lists from
  fragments.

</decisions>

<code_context>
## Existing Code Insights

Codebase context is gathered during plan-phase research. Start points: `wiki/tools/kme_pillars.py`,
`wiki/tools/kme_token_audit.py`, `wiki/tools/kme_replay.py`, `tools/usage_index.py` (`population`, `_kme_selector`,
`attribution`), `vault/programs/incremental-cognition/gen2/evidence/O-parity-gex44.md` and `O-cost-gex44.md`,
and the scratch logs in `/home/kobii/ao-scratch/p1/` (outside the repo).

</code_context>

<specifics>
## Specific Ideas

Open review notes from Phase 1 that touch this phase (01-REVIEW.md, info level, no false pass): IN-02
(`--perturb` without `--expect` is silently ignored), IN-03 (booleans accepted as counts in `expected`), IN-04
(a session with no `first_ts` drops out under `--until` without a reason). The planner may fold IN-04 in if the
challenger relies on `--until`.

</specifics>

<deferred>
## Deferred Ideas

None beyond the info-level review notes above.

</deferred>
