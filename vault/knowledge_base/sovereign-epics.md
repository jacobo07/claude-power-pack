# Sovereign Epics ROI Gate (SCS C42)

## SCS C42 -- Sovereign-Epics-ROI-gate: useful-in-theory is not enough (sealed 2026-06-07, BL-SOVEREIGN-TRIAGE-001)

**Standard.** No Sovereign Epic (PP Dataset v2 Parts XIX-XXIII) -- and by
extension no large dataset-defined system -- is built without passing a
triage of **immediate utility**: it must solve a problem the Owner
experiences *today*, on the current stack, that is not already covered by
an existing module. "Useful in theory" / "the dataset defines it" is NOT
sufficient justification to write code.

**Triage outcome 2026-06-07: 0 of 5 built.** All 5 epics
(SSGN / Control Plane / Agent Fleet / Execution Runtime / Assurance OS)
are XL, form a strict dependency chain, and target autonomous multi-agent
fleets across many repos -- a scenario the solo, <=2-pane Owner does not
operate. The parts that would help today are already covered:
- cross-repo rules -> global `~/.claude/CLAUDE.md` + `verify_global_mirrors`
- multi-pane locks -> `cpc_os` (pane registry + `plan_parallel_backlog`)
- cross-project status -> `pp_health_report` + `monitoring`
- anti-false-done -> `output_contracts` (OQS) + HR-OUTPUT-001/002/003 + V-gates

Per-epic verdicts + the activation criterion that flips each from DEFER
to BUILD live in `vault/plans/sovereign-roadmap.md`.

**Why this gate exists (empirical).** Three consecutive dataset-build
plans found the same pattern: the datasets describe grand future infra,
most of which PP already does at the scale the Owner needs. Without a
hard utility gate, "build everything in the dataset" produces orphan
modules (no consumer) and duplicates (Reality-Contract / SCS C28
violations). C42 makes the triage mandatory and "build nothing" a valid,
documented outcome.

**Orphan rule (reinforced).** An upper-layer epic built without its lower
layer is an orphan by construction -- XX without XIX, XXI without XX, etc.
have no consumer. Build order, if ever activated, is strictly
XIX -> XX -> XXI -> XXII -> XXIII.

Cross-ref C28 (read source / compose), C41 (vault-without-module is
documentation; do-not-build-what-exists), the orphan-module lesson, and
HR-001 (cross-repo writes = Owner-side).

Sealed BL-SOVEREIGN-TRIAGE-001 2026-06-07.
