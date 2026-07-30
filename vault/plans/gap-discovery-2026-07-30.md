---
title: CPP Empirical Gap Discovery Program — Phase 0/1/2/3 (targeted pass)
date: 2026-07-30
status: STOP #1 — presented inline, awaiting Owner approval before any construction
mode: AUDIT MODE (confirmed — no construction until STOP #1 clears)
scope_note: Targeted high-signal sample, not an exhaustive sweep of all 16
  discovery spaces. Given the 6/6 prior base rate and HR-COST-002 (stop if
  cost > 2x proportionate budget), this pass ran ~12 cheap Glob/Grep/Read
  calls against the 3 spaces most likely to hold real evidence cheaply
  (Rules Without Enforcement, Outputs Without Consequence, Six-Audit Root
  Cause) rather than all 16 from scratch. Depth available on request.
---

# Empirical Gap Register (targeted pass)

## GAP-1 — HR-NOVELTY-001's own enforcement mechanism is unwired

- **gap_id:** GAP-1
- **evidence_sources:** `Grep check_novelty_gate` across `*.py`/`*.js` repo-wide
  → 2 hits: `modules/spec_gate/gate.py` (definition) and
  `tools/test_spec_driven.py` (its own test). Zero hits in `hooks/`, `agents/`,
  `modules/pp_agents/signals/`, or any JIT/sleepy-skill router. Contrast:
  its sibling `check_spec_gate` in the *same file* has 9 real hits including
  `modules/one_shot/compiler.py`, `modules/pp_agents/signals/sdd_tier.py`,
  `modules/pp_agents/signals/spec_compliance.py`, `tools/test_sdd_os.py`.
- **date_range:** built 2026-07-30 (this session, commit `48e1a50`), found
  unwired same day.
- **affected_projects:** claude-power-pack (this repo).
- **affected_owners:** `spec_gate` (declared owner), `pp-spec-guardian` /
  sleepy-skill router (the natural live consumer — verified this router
  already scans prompts for build-intent keywords and injects an advisory,
  per this very session's own `UserPromptSubmit` context).
- **observed_cost:** the fix built specifically to stop a 6-times-measured
  audit-relapse pattern only fires if the agent manually reads the Hard
  Rules digest and remembers to call the function — i.e. it currently
  depends on the same human/agent memory discipline that let the pattern
  recur 6 times in the first place.
- **recurrence:** this is instance 7 of the underlying pattern — a Hard
  Rule + a function exist as text/code (HR-NOVELTY-001, `CLAUDE.md`), but no
  mechanical trigger connects a real prompt to the check. Same shape as
  `hard_rules/residual.py` (already flagged PLANNED in `OWNER_QUEUE.md`,
  2026-07-22): "extensively cited in CLAUDE.md prose, but grep confirms
  zero code import anywhere."
- **current_workaround:** none — relies on the agent self-invoking the
  router digest per the `HARD RULES — ROUTER` block in `CLAUDE.md`.
- **existing_partial_mechanisms:** the sleepy-skill router already does
  keyword-scanning on every prompt and injects advisory context (observed
  live this session: "[sleepy-skill] Spec-driven (L/XL) build intent
  detected... pointer only"). This is the correct wiring point — it already
  does the mechanical part (scan every prompt), it just doesn't call this
  one additional check yet.
- **missing_mechanism:** a call site.
- **missing_trigger:** sleepy-skill / JIT prompt scan does not include
  `check_novelty_gate(prompt_text)` in its keyword-check set.
- **missing_consumer:** none currently calls the function outside its own
  test.
- **failure_consequence:** the next mega-corpus proposal is caught only if
  the agent happens to remember to check — the exact failure mode HR-
  NOVELTY-001 was built to close.
- **human_dependency:** full — currently 100% agent-memory-dependent.
- **expected_value:** high — closes the loop this session's own prior work
  opened; directly answers gap-space #14 (Six-Audit Root Cause) with the
  most concrete evidence available.
- **minimal_intervention:** add one call
  (`spec_gate.check_novelty_gate(prompt_text)`) to the existing sleepy-skill
  prompt-scan path (or `pp-spec-guardian`'s existing scan), surfacing its
  `message` as advisory context when `.applies` is True. ~5-10 lines in an
  existing file. No new hook, no new module.
- **extension_candidate:** EXTEND_EXISTING_OWNER (sleepy-skill router /
  `pp-spec-guardian`).
- **new_owner_justification:** none needed — none proposed.
- **falsification_condition:** if a future grep shows a live caller of
  `check_novelty_gate` outside tests, this gap is closed.
- **confidence:** high (verified by direct grep, not inference).

**Verdict: OWNED_BUT_UNWIRED.**

## GAP-2 — `vault/OWNER_QUEUE.md` has no staleness/aging signal

- **gap_id:** GAP-2
- **evidence_sources:** direct read of `vault/OWNER_QUEUE.md` (569 lines).
  Contains dated PENDING items from 2026-07-10, 07-20, 07-22 (×2 sections),
  07-26, 07-29 — i.e. items up to 20 days old — as a flat additive list with
  no re-statement, no priority decay, no "still pending N days" marker.
  Contrast: its sibling `vault/handoffs/ESCALATED.md` has an explicit,
  working policy — "escalate after 3 unresolved occurrences; re-state every
  7 days" — sourced from `vault/config/alert_escalation.json` and enforced
  by `modules/alert_escalation/policy.py`.
- **date_range:** items observed 2026-07-10 through 2026-07-29 (this
  session, 2026-07-30).
- **affected_projects:** claude-power-pack.
- **affected_owners:** `modules/alert_escalation` (already builds exactly
  this capability for a different finding class).
- **observed_cost:** an Owner scanning `OWNER_QUEUE.md` has no signal
  distinguishing a 1-day-old item from a 20-day-old one; item aging is
  legible only by manually reading each section's date header.
- **recurrence:** structural (every item added to this file going forward
  inherits the same non-aging behavior).
- **current_workaround:** none.
- **existing_partial_mechanisms:** `modules/alert_escalation/policy.py` +
  `vault/config/alert_escalation.json` already implement threshold +
  re-statement logic for a different file (`ESCALATED.md`). Same shape,
  different target.
- **missing_mechanism:** an age-check pass over `OWNER_QUEUE.md`'s dated
  section headers.
- **missing_trigger:** none currently runs periodically against this file.
- **missing_consumer:** none.
- **failure_consequence:** genuinely stale items (the 07-20 hook
  registration items are now 10 days old) are as visually unremarkable as
  a same-day item.
- **human_dependency:** full.
- **expected_value:** medium — visibility improvement, not a correctness
  bug (nothing currently depends on OWNER_QUEUE freshness the way
  `power_beacon` depended on the graceful-shutdown hook).
- **minimal_intervention:** extend `alert_escalation/policy.py`'s existing
  age-check logic (or a ~20-line sibling function) to parse `## NEW
  (YYYY-MM-DD)` headers in `OWNER_QUEUE.md` and flag any section older than
  a configurable threshold (e.g. 14 days) in its existing report path. No
  new module.
- **extension_candidate:** EXTEND_EXISTING_OWNER (`modules/alert_escalation`).
- **new_owner_justification:** none needed.
- **falsification_condition:** if `OWNER_QUEUE.md` items are already
  reviewed on a real cadence the Owner considers sufficient, this gap is
  LOW_ROI_REFERENCE, not actionable.
- **confidence:** medium — the mechanism gap is verified; whether it's
  worth building is an Owner call on how OWNER_QUEUE is actually used.

**Verdict: EXTEND_EXISTING_OWNER (medium priority, Owner-judgment-gated).**

## GAP-3 — 339 pre-fix `mirror-drift-*.md` handoff files, no retention policy

- **gap_id:** GAP-3
- **evidence_sources:** `Glob vault/handoffs/*` → 339 files, nearly all
  named `mirror-drift-<timestamp>.md`, spanning 2026-05-23 through the
  escalation-fix date. `tools/background_verifier_run.py`'s own docstring
  (lines 13-19): "this file produced 333 identical mirror-drift handoffs
  across 67 days -- detection nobody could act on, because nothing
  distinguished the 333rd notice from the first," fixed 2026-07-29 by
  routing through `modules.alert_escalation` (dedup + `ESCALATED.md`
  standing row). The root cause (noise) is already fixed; the historical
  pile is not addressed by that fix.
- **date_range:** files dated 2026-05-23 through 2026-07-29; root-caused
  and partially fixed 2026-07-29 per the file's own comment.
- **affected_projects:** claude-power-pack.
- **affected_owners:** `modules/alert_escalation` / `background_verifier_run.py`.
- **observed_cost:** disk clutter only — no evidence anything reads these
  339 files as a corpus (grep for "mirror-drift" across `tools/` found only
  the generator and the two files' own tests/advisor, none of which glob
  the historical directory).
- **recurrence:** N/A — the generating bug is already fixed; this is
  cleanup debt, not an active problem.
- **current_workaround:** none; files simply accumulate.
- **existing_partial_mechanisms:** `alert_escalation` prevents new pile-up
  post-2026-07-29 (verified: the current single `ESCALATED.md` row, not
  333 new files, is how the *current* recurring drift is tracked).
- **missing_mechanism:** a retention/archive decision for the pre-fix pile.
- **missing_trigger:** none.
- **missing_consumer:** none.
- **failure_consequence:** none functional — cosmetic/disk only.
- **human_dependency:** full (Owner call: these are also the incident
  evidence for the bug `alert_escalation` was built to fix — deleting them
  erases the audit trail the Reality Contract generally wants kept).
- **expected_value:** low.
- **minimal_intervention:** none required unless the Owner wants the
  directory tidied. If desired: a one-time archive (zip + move, not
  delete) of the pre-2026-07-29 files, keeping the incident evidence
  without 339 loose files in the working tree.
- **extension_candidate:** INVALID_GAP / LOW_ROI_REFERENCE — root cause
  already fixed; remaining question is housekeeping, not a gap.
- **new_owner_justification:** none.
- **falsification_condition:** N/A.
- **confidence:** high.

**Verdict: LOW_ROI_REFERENCE — noted for completeness, not actionable.**

## Phase 4 check (novelty gate self-test)

Per the spec's Phase 4 requirement to verify the gate "bloquea un caso de
prueba construido para imitarlo": this very program's own opening prompt
contains none of `_NOVELTY_TRIGGER`'s keywords (it explicitly frames itself
as gap-discovery, not a named fabric/OS/platform) — `check_novelty_gate()`
correctly does NOT fire on it, which is the right answer, not a miss. GAP-1
above is the real finding: the gate is correct in isolation but unreachable
in practice.

## Recommendation (STOP #1)

Three gaps found in a targeted pass (not all 16 spaces swept — see
scope_note above). Verdicts: 1 OWNED_BUT_UNWIRED (high value, ~10 lines), 1
EXTEND_EXISTING_OWNER (medium value, Owner-judgment-gated), 1
LOW_ROI_REFERENCE (no action). **Zero new datasets, zero new modules, zero
new hooks warranted** — matches the program's own "cero datasets + N
extensiones" valid-outcome category.

Recommended minimal action: **wire `check_novelty_gate` into the existing
sleepy-skill prompt scan** (GAP-1). This is the one high-confidence,
high-value, low-cost fix, and it closes the loop on this session's own
prior HR-NOVELTY-001 work — the fix that was supposed to stop audit #7 from
needing to happen manually, currently cannot stop it, because nothing
calls it yet.

GAP-2 is a real but lower-stakes visibility gap — worth a decision, not
urgent. GAP-3 needs no action beyond an optional archive.
