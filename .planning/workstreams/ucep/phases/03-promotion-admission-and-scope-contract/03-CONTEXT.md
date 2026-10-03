# Phase 3: Promotion admission and scope contract - Context

**Gathered:** 2026-10-03
**Status:** Ready for planning
**Mode:** smart discuss, unattended. Every grey area below was answered with the recommended option by
the orchestrator (epoch 3) because nobody is available to answer. Each answer carries its reason, so a
reviewer can disagree with something specific. The governing spec is
`vault/plans/ucep-naked-verb-2026-10-02.md` (S4, items 8-9) and its audit
`vault/plans/ucep-naked-verb-2026-10-02.audit.md` (gaps 5, 6, 15).

<domain>
## Phase Boundary

Admission to a constitutive baseline becomes a checked property of the chain instead of a convention.
This phase delivers:

- `modules/tower/admission.py` (new): judges a proposed entry against an evidence bar proportional to
  its scope, derives the scope itself, and returns AUTO_ADMITTED / PENDING_OWNER / REFUSED with reasons.
- `ratchet.promote` and archetype B0 creation require an admission record.
- `ratchet.verify_chain` refuses any entry, in any generation outside the grandfathered set, that lacks
  a valid admission record. This is what stops a raw `write_generation` from bypassing admission.
- `baselines.propagation_scope(entry, gen)`: projects grandfathered entries as LEGACY_UNSPECIFIED.

Out of scope: seeding the three archetype B0s (Phase 4), any change to B0/B1 bytes of the four
existing families, and binding authority to something a caller cannot type (see Deferred).

</domain>

<decisions>
## Implementation Decisions

### A. The grandfathered set and the cutover

- A1. **Grandfathering is pinned by identity, not by generation number.** The set is the seven existing
  generation files (kobiicraft_mode B0; persistent_state, web_surface, wii_homebrew B0+B1), each pinned
  by `(family, generation, LF sha256 of the blob)` in code. Reason: a number rule (`gen <= 1`) would
  admit a NEW family's B0 and B1 with no record, and Phase 4 creates exactly such families
  (`archetype/<ID>`). Pinning by sha also means an edited legacy file stops being grandfathered.
  The roadmap's "gen <= 1 grandfathered" is honoured for the families it was written about.
- A2. The cutover is therefore "every generation not in the pinned set", including any new family's
  B0. Recorded as the roadmap reading, not a change to it.
- A3. Synthetic chains in test roots are not grandfathered. The planner chooses how existing suites
  that build synthetic chains stay green (an explicit `legacy=`/`grandfathered=` parameter on
  `verify_chain`, or admission records in their fixtures). It must not be a default that switches the
  requirement off for the real tree (`root=None`). Every Phase 1 suite stays at its current n/n or
  grows; none shrinks.
- A4. B0/B1 bytes of the four families do not change. The F0 sha table from Phase 1 is re-checked at
  the end of the phase.

### B. The admission record and where it lives

- B1. **Records live inside the generation that adds the entry**, as `admissions: {<entry_id>: record}`.
  Reason: the record is then covered by the next child's `parent_sha256` like everything else, needs
  no second store, and cannot drift from the entry it admits. A separate store would be a second
  write path to keep consistent.
- B2. Record fields: `origin_status` (must be VERIFIED at admission time), `check` (a runnable check
  kind, or `manual:` with a non-empty do-confirm text), `evidence_ref` (commit sha or incident id),
  `production_evidence_ref`, `negative_applicability` (non-empty: where the rule does NOT apply),
  `counterfactual` (one of instance / product / archetype / constitutive), `derived_scope`,
  `verdict`, `status: provisional`, `admitted_at`, and a `schema` version string.
- B3. `verify_chain` re-validates a stored record's STRUCTURE and re-derives its scope from the
  generation's location. It does NOT re-run `verify_origin` at chain time. Reason: origin rot is owned
  by the citations gate (Phase 1 decision, documented in `ratchet.py`), and making the chain go red on
  later rot would merge two separate claims.
- B4. An admission record whose fields are well-formed but whose derived scope disagrees with the
  generation's location is a chain regression (kind `ADMISSION_INVALID`), as is a missing record
  (`UNADMITTED`). Both named kinds are new and listed in the module docstring.

### C. Scope derivation and refusals

- C1. Scope is derived from the write location: `baselines/<family>/` gives `family`;
  `baselines/archetype/<ID>/` gives `archetype`. Applicability widens it: an applicability that names
  more than one family, or matches everything, gives `cross-family` or `universal`. The counterfactual
  `constitutive` gives `constitutive`.
- C2. A declared `propagation_scope` narrower than the derived scope is refused (gap 6). A declared
  scope wider than derived is allowed and treated as the declared value (it only raises the bar).
- C3. family / archetype scope gives AUTO_ADMITTED (status provisional). cross-family / universal /
  constitutive gives PENDING_OWNER.
- C4. **PENDING_OWNER is not written.** `promote` refuses with a RatchetRefusal that names the verdict
  and the missing Owner decision. Reason: writing a pending entry into a constitutive generation would
  make it consumable before anyone approved it. A queue file is deferred.
- C5. counterfactual `instance` is REFUSED: a lesson that only explains one instance is not
  baseline-worthy.
- C6. Refused outright, whatever the scope: an origin that is not VERIFIED; an origin path under
  `.claude/worktrees/` or any `worktrees/` segment, or a rules stub (a file under `~/.claude/rules/`
  whose body says it moved to a skill) (gap 15); a check that matches everything (`glob:**`, `glob:*`,
  `regex:<file>::.` and the equivalent empty-ish patterns); a missing evidence ref or negative
  applicability; a `manual:` check with empty do-confirm text.
- C7. Every refusal returns every failing reason, not the first (a compound claim is only as true as
  each part).

### D. Wiring and the legacy projection

- D1. `ratchet.promote` calls admission for every new entry before writing and stores the records in
  the generation. `ratchet.revert` and `ratchet.reanchor` do not add entries and need no admission.
- D2. Archetype B0 creation goes through one function (the planner names it; `promote` on an empty
  `archetype/<ID>` family is acceptable) that requires admission. `tools/family_baseline.py build_b0`
  must refuse to write into the `archetype/` axis without admission records.
- D3. `baselines.propagation_scope(entry, gen)` returns LEGACY_UNSPECIFIED for entries of a
  grandfathered generation and the stored derived scope otherwise. For a non-grandfathered generation
  with no record it returns UNADMITTED, never a guess. Entries C and D (the legacy kinds) gain no
  meaning from this projection.
- D4. The new module is registered with `/liveness` (wired from `ratchet`, so it is reachable through
  existing callers), and `python modules/liveness/reachability.py` stays exit 0.

### E. Tests

- E1. A new suite `tools/test_tower_admission.py` (V-ADM-* gates) written RED first against the
  unchanged code where a gate is about existing behaviour (raw `write_generation` adds pass today).
- E2. Refusal gates, each paired with a control in which the fact exists and the entry is admitted:
  bad origin, worktree origin, rules-stub origin, `glob:**`, self-declared narrow scope, missing
  negative applicability, counterfactual `instance`, an unadmitted raw `write_generation` at a
  non-grandfathered generation, a PENDING_OWNER entry not written.
- E3. Positive control: a fully evidenced archetype entry is AUTO_ADMITTED, written, and the chain
  reads ok.
- E4. The real tree: `verify_chain` is ok for all discovered subjects (discovery, not a list), and a
  mutation drill (record removed / scope widened in a copy) turns it red.

### Claude's Discretion

- Exact function names and signatures inside `admission.py`, provided the verdict vocabulary above is
  kept and every refusal reason is a named constant.
- Whether the legacy sha table lives in `admission.py` or `baselines.py`.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `modules/tower/baselines.py`: `verify_origin` (VERIFIED/WEAK/LINE_MISSING/FILE_MISSING/MALFORMED),
  `write_generation` (create-if-absent, refuses `extra` overriding core fields), `discover_subjects`
  (walks nested `archetype/<ID>` already), `generation_sha256`.
- `modules/tower/ratchet.py`: `promote`, `revert`, `reanchor`, `verify_chain`, `diff`, named regression
  kinds, `RatchetRefusal`, `AUTHORITIES` (self-declared token residual, WR-01).
- `modules/tower/checks.py`: `parse`, `STATIC_KINDS`, `DELEGATED_KINDS` for check classification.
- `modules/capability_runtime/archetypes.py`: `ARCHETYPES` (WORLD_MUTATION, EXTERNAL_EFFECT,
  BACKGROUND_JOB) and `ARCHETYPE_ID_RE` -- admission validates an `archetype/<ID>` against these.

### Established Patterns
- Plain-Python suites printing `<NAME>_PASS=n/m threshold=n/m`, exit 0 iff all pass; RED proof
  recorded in the phase EVIDENCE file.
- Named refusal kinds as module constants; every refusal names all reasons.
- Real-tree gates use discovery, never a hand-written family list.

### Integration Points
- `ratchet.promote` (writes a generation), `tools/family_baseline.py build_b0`, `ratchet.verify_chain`
  (read by `test_tower_ratchet` V-TRAT-REAL-CHAINS and the done-gate).

</code_context>

<specifics>
## Specific Ideas

- The authority residual WR-01 in `ratchet.py` names Phase 3 as the place where authority binds to
  something a caller cannot type. This phase binds ADMISSION to evidence; it does not make the
  "Owner" token unforgeable. That remains a named residual (see Deferred), and the docstring is
  updated to say so precisely instead of implying it was closed.

</specifics>

<deferred>
## Deferred Ideas

- An Owner approval channel that a caller cannot forge (signed approvals or a separate store the agent
  cannot write). Needed before PENDING_OWNER can ever become admitted without a human commit review.
- A queue file for PENDING_OWNER proposals so they are not lost when `promote` refuses.

</deferred>
