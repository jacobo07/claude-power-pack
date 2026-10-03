---
phase: 08-owner-reconciliation-and-creation-governance
reviewed: 2026-10-04T00:00:00Z
depth: deep
files_reviewed: 13
files_reviewed_list:
  - tools/skill_creation_gate.py
  - tools/test_skill_creation_gate.py
  - tools/skill_handoffs.py
  - tools/test_skill_handoffs.py
  - vault/programs/skill-capability/handoffs/I.md
  - vault/programs/skill-capability/handoffs/K.md
  - vault/programs/skill-capability/handoffs/L.md
  - vault/programs/skill-capability/handoffs/M.md
  - vault/programs/skill-capability/evidence/J-creation-gate.md
  - vault/programs/skill-capability/card_source_digests.json
  - vault/programs/skill-capability/evidence/G-lineage.md
  - vault/programs/skill-capability/evidence/H-drift.md
  - vault/programs/skill-capability/ledger.json
  - vault/programs/skill-capability/owner-bundle.md
  - skills/*/SKILL.md (24 metadata insertions)
findings:
  critical: 0
  warning: 6
  info: 4
  total: 10
status: issues_found
---

# Phase 8: Code Review Report

**Reviewed:** 2026-10-04
**Depth:** deep
**Base:** 419c00a2..HEAD (b3c89f3e), worktree `sc-run`, host kobicraft-gex44, python3 3.12.3
**Status:** issues_found

## Summary

Live state on gex44, all observed in this review:
- `python3 tools/test_skill_creation_gate.py`: `SCG_PASS=32/32`, rc 0, wall 5.2 s.
- `python3 tools/skill_creation_gate.py`: `SKILL_CREATION PASS population=24`.
- `python3 tools/test_skill_handoffs.py`: `SKH_PASS=23/23`.
- `python3 tools/skill_handoffs.py --check`: `SKILL_HANDOFFS PASS pillars=4`.
- The `--render` output equals the committed `evidence/J-creation-gate.md`.
- Every ledger `sha256` pin on handoffs/I, K, L, M and on J-creation-gate.md equals the sha256 of its HEAD blob.
- The G and H trailers, the digest record and the evidence moves are consistent with each other.
- Inserting the declaration changed no description returned by `skill_index._read_frontmatter` for the 24 repo skills.

No CRITICAL: no finding gives a false PASS on the current tree. The 6 warnings fall into four groups:
1. A git failure is reported as FAIL or UNMEASURED instead of INCONCLUSIVE (WR-01).
2. Three proven-load-bearing claims are not actually proven, because their red mutants survive the suites (WR-02, WR-05).
3. Pillar M's named-denominator clause is rendered but never judged (WR-03), and J's reason grammar admits YAML null and boolean literals as a reason (WR-04).
4. The J declaration shape, combined with the router's own frontmatter reader, damages the description of any future skill whose frontmatter ends in a block-scalar description (WR-06). That future skill is exactly what the `[J]` Owner item asks skill-creator to emit.

Every WARNING has a RED script under `/home/kobii/.claude/jobs/06c5c0e4/tmp/p8review/`. Run each from the worktree root; exit 1 means the defect is present.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: skill_handoffs reports git failures as FAIL or UNMEASURED, never INCONCLUSIVE

**File:** `tools/skill_handoffs.py:194, 423, 505, 630-631, 881`

**Issue:**
- `smd.is_git_failure(reason)` only recognises the `git-batch-*` reasons that `vgm.batch_blobs` produces.
- `blob()` reads through `smd.git_run`, whose failure reasons have the form `git cat-file failed: ...` or `git cat-file rc=N: ...`. `is_git_failure` is therefore False for every one of them.
- Result: a timed-out, killed or lock-blocked git reading a committed blob is misreported:
  - `contract()` returns `("FAIL", "handoffs/K.md not committed")`. That statement is false: the file is committed and git failed to read it.
  - The K and M controls read "dead controls" or "lacks marker kinds", which is UNMEASURED with a false cause.
  - I `skills` reads UNMEASURED "source missing".
  - `load_ctx` reaches INCONCLUSIVE only for a missing git executable (its `"not found"` heuristic); a timeout there is also UNMEASURED.
- No false PASS results, but the lesson "git failure -> INCONCLUSIVE" is violated and each reason names the wrong cause.

**Reproduction:** `red_git_failure_not_inconclusive.py` reports 4 git failures not reported INCONCLUSIVE (rc 1). It shows `is_git_failure(<git_run timeout reason>) == False`.

**Fix:** in `blob()`, return a structured failure kind. One option:
```python
def blob(repo, sha, rel):
    out, why = smd.git_run(repo, "cat-file", "-e", f"{sha}:{rel}")   # rc 128 / missing path = absent
    ...
```
A simpler option is to classify locally: treat a reason as absence only when it matches `rc=128: fatal: path '...' does not exist` (or `exists on disk, but not in`). Everything else (`failed:`, `not found`, other rc values) is a git failure and returns INCONCLUSIVE at all five sites. Add one drill per site that injects a `git_run` timeout.

### WR-02: Four handoff claim parts and three contract clauses have no red mutant, and the suite stays 23/23 when each is removed

**File:** `tools/test_skill_handoffs.py:181-195` (the drill list and the `need` set); `tools/skill_handoffs.py:745-752, 756-760, 870-912`

**Issue:**
- `V-SKH-EVERY-PART-RED` asserts only 11 parts. Its `need` set leaves out I:nowrite, I:skills, I:contract and L:contract.
- The I drill runs with `contract=()`.
- No drill touches the contract's working-copy, landed-after-freeze or `measured_at_commit` ancestry clauses.
- The positive-control mutant (K router forced PASS) is killed at 20/23, so the harness can see a mutant. Each of these mutants survives with `SKH_PASS=23/23`, rc 0:
  - `contract-line1-only`: the landed, measured_at and working-copy checks deleted.
  - `contract-L-always-pass` (also I).
  - `I-nowrite-always-pass`.
  - `I-skills-always-pass`.
- The ledger text "Re-checked ... HANDOFF_I PASS ... nowrite=PASS skills=PASS contract=PASS" therefore cites parts whose FAIL branch was never driven.

**Reproduction:** `mutant_survival_handoffs.py` reports 4 survivors (rc 1). `mutant_survival_handoffs.py control-K-router-pass` shows the control killed (rc 0).

**Fix:** add drills that each assert one exact outcome:
- A handoff whose `measured_at_commit` is not an ancestor of HEAD gives contract FAIL.
- A handoff whose only commit predates the freeze gives contract FAIL.
- An uncommitted working-copy edit gives contract FAIL.
- An L-handoff line-1 edit gives L:contract FAIL.
- D-coverage.md with no `## Plane <host>` table gives I:skills UNMEASURED.
- A scanner stub in the export that writes a file gives I:nowrite FAIL.

Add I and L to `need`, and run the I drill with `contract=("I",)`.

### WR-03: Pillar M's "named denominator" half of the rule is rendered but never judged

**File:** `tools/skill_handoffs.py:513-532, 549-550`

**Issue:**
- The frozen M rule is "reports token and turn deltas relative to a named denominator". `measure_M` judges only aperture, cost and control.
- These cases all leave every M part PASS, so `--check` prints `HANDOFF_M PASS`:
  - A delta line whose evidence file has no `-- D-XXX measurement` header (`denom = "UNNAMED"`).
  - An unreadable B or E evidence file (row `UNREADABLE`, denominator `-`).
  - A `savings[]` entry with no `denominator` (rendered `None`).
- Lines 549-550 also hard-code a factual sentence into every M handoff, whatever was measured: "E reports no turn or token delta. Its only effect figure is a pass-rate difference against arm N0, denominator D-SESSIONS." That is an unbacked claim in generated text.

**Reproduction:** `red_m_denominator_unjudged.py` prints `parts` all PASS, `deltas [('B-listing-floor.md', 0, '-'), ('E-contribution.md', 45, 'UNNAMED')]` and `savings denominators [None, None]` (rc 1).

**Fix:** add a `denominator` part:
- FAIL when any savings entry lacks a denominator, or a delta line's denominator is `UNNAMED`.
- UNMEASURED when a source file is unreadable (INCONCLUSIVE on a git failure, per WR-01).
- PASS otherwise, with a positive control that DELTA_LINE hits at least one line.

Derive the E sentence from the measured deltas (for example, list the E rows and their denominators), or delete it.

### WR-04: J reason grammar admits YAML null and boolean literals, so a reason YAML reads as absent passes

**File:** `tools/skill_creation_gate.py:104, 241`

**Issue:**
- `REASON_RE` accepts `null`, `Null`, `NULL`, `no`, `off`, `false` and `0`.
- `c_target` only requires the raw text to be non-blank. So `opportunity_detector: none` plus `opportunity_detector_reason: null` is DECLARED, FORM, TARGET and COVERAGE-AGREES PASS.
- PyYAML, which the official skill-creator validator uses, reads that reason as `None`, or as `False` or `0` for the others.
- The docstring claims the grammar keeps the reason "always a valid YAML plain scalar". It is valid YAML but not a string, which breaks the Agent Skills "metadata is a string map" premise. The lesson is that absent must never read as present.

**Reproduction:** `red_reason_yaml_null.py` reports 7 literals admitted (rc 1).

**Fix:** refuse YAML core-schema and YAML 1.1 non-string scalars in FORM. For example, reject when `value.lower()` is in `{"null","~","true","false","yes","no","on","off","y","n"}` or the value matches a number pattern (`^[-+]?(\d[\d_]*)(\.\d*)?([eE][-+]?\d+)?$`, plus `0x`/`0o` forms). Add a drill `S reason: null -> {S:FORM}`.

### WR-05: FORM's reason sub-checks (placement and grammar) have no red mutant

**File:** `tools/skill_creation_gate.py:225-229`; `tools/test_skill_creation_gate.py` (drill table)

**Issue:**
- `V-SCG-FLIP-*` proves FORM load-bearing through its detector branches only (dot-slash value, top-level detector key).
- A mutant FORM that ignores every `opportunity_detector_reason` line (placement and DJ-02 grammar) passes the whole suite at `SCG_PASS=32/32`.
- DJ-02 is the stated YAML-safety property of the declaration, and nothing proves the gate enforces it.

**Reproduction:** `mutant_survival_creation_gate.py`: the control (FORM always PASS) is killed at 24/30, and `FORM-ignores-reason-lines` survives at 32/32 (rc 1).

**Fix:** add two singleton drills, each with a forced-PASS flip:
- A reason line at top level (not a metadata child) gives `{S:FORM}`.
- A reason containing `:` or `#` gives `{S:FORM}`.

Pair them with WR-04's null drill.

### WR-06: The declaration shape corrupts the router's description of any new skill whose frontmatter ends in a block-scalar description

**File:** `tools/skill_creation_gate.py:181-196` (`insert_declaration`, appends at the end of the frontmatter); interacts with `modules/skill_router/skill_index.py:162-174`

**Issue:**
- `_read_frontmatter` collects a block-scalar description until it reaches a line matching `^[A-Za-z_][\w-]*:\s`.
- A bare `metadata:` line has nothing after the colon, so it does not stop the capture. `metadata:` and both declaration lines get appended to the description, which feeds `classify_domain` and `_extract_keywords`.
- Example: `'Use when reviewing frontend react components.'` becomes `'... metadata: opportunity_detector: none opportunity_detector_reason: coverage class none; no registered card hook ...'`.
- The 24 repo skills are unaffected: 0 of 24 descriptions changed. The `[J]` owner-bundle item asks skill-creator to emit this declaration in every new SKILL.md, and DJ-01 validated the shape only against `quick_validate.py`, never against the repo's own frontmatter reader.

**Reproduction:**
- `red_insert_declaration_block_scalar.py` shows the polluted description (rc 1).
- `red_skill_index_description_pollution.py` shows 0 of 24 repo skills changed (rc 0, kept as the regression guard).

**Fix:** pick one or both:
- Make `skill_index` stop on `^[A-Za-z_][\w-]*:(\s|$)`. That is outside phase 8's files, so it would be an owner item or a separate fix.
- Have `insert_declaration` place `metadata:` before any block-scalar `description:`, and add a J clause or drill asserting that `_read_frontmatter(description)` is unchanged by the declaration.

State the constraint in the `[J]` owner-bundle line.

## Info

### IN-01: FORM admits non-canonical paths

**File:** `tools/skill_creation_gate.py:142-147`

`hooks/./doctrine_cards.js`, `hooks/doctrine_cards.js/` and `hooks/doctrine_cards.js/.` pass FORM, and pass TARGET and COVERAGE-AGREES after `normpath`. `./hooks/...` is refused, which is inconsistent. A downstream reader that does not normalize sees a different path than the gate approved, and a trailing `/` names a directory.

**Fix:** require `posixpath.normpath(value) == value` in `_value_form_ok`. Reproduction: `red_form_noncanonical_and_dup_reason.py`.

### IN-02: A duplicated `opportunity_detector_reason` key passes all four clauses

**File:** `tools/skill_creation_gate.py:201-212`

DECLARED counts detector lines only. Two reason lines produce a duplicate YAML key: ruamel and other strict parsers reject it, and PyYAML keeps the last.

**Fix:** FAIL DECLARED (or FORM) when `len(decl["reason"]) > 1`. Reproduction: `red_form_noncanonical_and_dup_reason.py`.

### IN-03: K's row-count reason is inferred from the hostname, not measured

**File:** `tools/skill_handoffs.py:399`

`"gex44 has no card ledger"` is chosen whenever `platform.node() == "kobicraft-gex44"` and rows == 0. The card ledger directory (`skill_opportunity_signals.card_state_dir()`) is never checked. It is absent on gex44 today, so the text is currently true, but it is a host-plane claim made without reading the host.

**Fix:** state `card ledger present: <card_state_dir()/ledger.jsonl exists>` from the actual check.

### IN-04: 7 of the 24 declared SKILL.md frontmatters are not valid YAML, including the positive-control skill

**File:** the frontmatter of `skills/{concurrent-writers-shared-tree,develop-here-prove-there,evaluation-corpus-governance,guard-event-reachability,monetary-quantity-integrity,presence-is-not-residency,recurring-work-cardinality}/SKILL.md`

The cause predates this phase (`: ` inside plain-scalar descriptions, already a ScannerError at 419c00a2). The J gate is a line grammar, so it says DECLARED PASS. Any YAML-based consumer, including the official validator, reads no declaration at all for these 7. That includes concurrent-writers-shared-tree, the only `opportunity_detector` skill.

The J ledger line "adding the declaration changed 0 of 72 validator outcomes" is true only because these 7 already fail.

**Fix:** quote or fold the 7 descriptions, or record the limit in the J evidence and ledger reason. Reproduction: `yaml_parse_all.py` (bad=7).

---

_Reviewed: 2026-10-04_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
