---
phase: 08-owner-reconciliation-and-creation-governance
fixed_at: 2026-10-04T00:00:00Z
review_path: .planning/workstreams/skill-capability/phases/08-owner-reconciliation-and-creation-governance/08-REVIEW.md
iteration: 1
findings_in_scope: 10
fixed: 9
skipped: 1
status: partial
---

# Phase 8: Code Review Fix Report

**Fixed at:** 2026-10-04
**Source review:** .planning/workstreams/skill-capability/phases/08-owner-reconciliation-and-creation-governance/08-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 10 (WR-01..06, IN-01..04)
- Fixed: 9 (all 6 warnings, IN-01, IN-02, IN-03)
- Skipped: 1 (IN-04: report only, by caller instruction)

**Where it ran:** every edit, commit and gate below ran in the worktree
`/home/kobii/missions/skill-capability/.claude/worktrees/sc-run` (branch `mission/skill-capability-run`), host
kobicraft-gex44, python3 3.12.3. No nested worktree was created because the caller pinned this one. The final
checks ran after the last commit, with `tools/`, `vault/programs/`, `modules/` and `skills/` clean against HEAD.
That means they judged the committed blobs. Each commit used an explicit pathspec, and `git log -1 --format=%s`
was checked after each one.

**Red inputs:** the reviewer's scripts in `/home/kobii/.claude/jobs/06c5c0e4/tmp/p8review/`. I added two runners
there for this fix, `fix_mutants_handoffs.py` and `fix_mutants_gate.py`. Each one puts back one reviewed defect
inside the tool, runs the suite's `main()` in-process, and lists the V-lines that turned red.

## Fixed Issues

### WR-01: skill_handoffs reported git failures as FAIL or UNMEASURED, never INCONCLUSIVE

**Files modified:** `tools/skill_handoffs.py`, `tools/test_skill_handoffs.py`
**Commit:** fa8e85f8
**Applied fix:**
- Added `git_failed(why)`. Only git's own rc-128 messages `path '...' does not exist in` and
  `exists on disk, but not in` count as an absence. Every other reason is a git failure: timeout, killed or
  missing git, lock, invalid object, or any other rc.
- All five sites now use it: `load_ctx` (both the freeze pointer and the ledger), `contract`, the K control, the
  M control, and I skills. `_skill_candidates` now separates a git failure from a missing source.

**Evidence:**
- `red_git_failure_not_inconclusive.py`: rc 1 before (4 sites), rc 0 after.
- New in-suite lines:
  - `V-SKH-GIT-TIMEOUT-{CTX,CONTRACT,K-CONTROL,M-CONTROL,I-SKILLS}`. Each line checks both poles: a timeout gives
    INCONCLUSIVE, and the path absent from the commit gives FAIL or UNMEASURED.
  - `V-SKH-GIT-FAILED-CLASSIFIER`, which runs on reasons that git itself produced.
- Red mutant `WR01-old-classifier`: `SKH_PASS=23/29`, all 6 lines red.

### WR-02: handoff claim parts and contract clauses with no red mutant

**Files modified:** `tools/test_skill_handoffs.py`
**Commit:** 73c80794
**Applied fix:**
- The base fixture now also holds `handoffs/I.md`.
- New exact-outcome drills:
  - CONTRACT-MEASURED-OFF-HISTORY: `measured_at_commit` points at an orphan commit.
  - CONTRACT-NOT-LANDED-AFTER-FREEZE: the freeze is moved past the handoffs commit.
  - CONTRACT-WORKTREE-EDIT
  - CONTRACT-L-NON-OWNER
  - I-SKILLS-NO-PLANE
  - I-NOWRITE-SCANNER-WRITES: a reachability stub that writes into the export.
  - I-CONTRACT-NON-OWNER
- I-NO-SCANNERS now judges the I contract.
- `need` grew from 11 parts to 17. It reached 18 after WR-03.

**Evidence:**
- `mutant_survival_handoffs.py`: rc 1 before (4 survivors at 23/23), rc 0 after. Each mutant is now killed:
  - contract-line1-only: 32/36
  - contract-L-always-pass: 32/36
  - I-nowrite-always-pass: 34/36
  - I-skills-always-pass: 33/36
- The positive control `control-K-router-pass` is killed at 33/36.

### WR-03: pillar M's named-denominator clause was rendered but never judged

**Files modified:** `tools/skill_handoffs.py`, `tools/test_skill_handoffs.py`,
`vault/programs/skill-capability/handoffs/M.md`, `vault/programs/skill-capability/ledger.json`
**Commit:** 8941d4fa (requires human verification: this is a logic change)
**Applied fix:** a new `denominator` part in `measure_M`.

| Condition | Outcome |
|---|---|
| A savings[] entry has no denominator, or a delta line sits under an UNNAMED header | FAIL |
| Git fails while reading a delta source | INCONCLUSIVE |
| A delta source is absent | UNMEASURED |
| The delta pattern hits no line (dead positive control) | UNMEASURED |
| Otherwise | PASS |

The hard-coded sentence "E reports no turn or token delta ..." is replaced by a per-source summary computed from
the measured delta lines.

**Rendered evidence and ledger:**
- `handoffs/M.md` was re-rendered through `--write M`. It is measured at 73c80794, the figures are unchanged, and
  the claim now includes `denominator=PASS`.
- `state.M` sha256 was re-pinned to `e8c8a4f563154c0f9414d95d254bf6dd38fe31d81a388a57603ceb7cd8d28462`
  (LF-normalized).
- The `state.M` reason now records the re-render and the re-check that includes the new part.
- The [M] owner-bundle line still matches: it cites the same denominators and line numbers.
- `frozen`, `state.E` and the [E] line were not touched.

**Evidence:**
- `red_m_denominator_unjudged.py`: rc 1 before, rc 0 after.
- New drills: M-DENOMINATOR-UNNAMED, M-SAVINGS-NO-DENOMINATOR, M-DELTA-DEAD-CONTROL, GIT-TIMEOUT-M-DENOMINATOR.
- Red mutants: with the part removed, and with it forced to PASS, the suite reads `SKH_PASS=35/40` for each.

### WR-04: the J reason grammar admitted YAML null and boolean literals

**Files modified:** `tools/skill_creation_gate.py`, `tools/test_skill_creation_gate.py`
**Commit:** 4774aa29
**Applied fix:**
- FORM now also refuses `YAML_NON_STRING`, which covers:
  - null and `~`
  - the YAML 1.1 booleans (yes/no/on/off/y/n) and true/false
  - ints, including `_` separators and the 0x/0o/0b forms
  - floats
  - dates
- `declaration_lines` checks generated reasons with the same `reason_form_ok()`.

**Evidence:**
- `red_reason_yaml_null.py`: rc 1 before (7 literals admitted), rc 0 after.
- New drill REASON-NULL-S gives `{S:FORM}`, with its flip.
- New line `V-SCG-REASON-YAML-SCALARS`: 25 literals refused; 7 texts plus 23 generated reasons admitted. PyYAML
  cross-check: 21 of the 25 resolve to non-str.
- Red mutant (check removed): `SCG_PASS=32/34`.
- The J render is unchanged.

### WR-05: FORM's reason sub-checks had no red mutant

**Files modified:** `tools/test_skill_creation_gate.py`
**Commit:** c26b87c4
**Applied fix:** three singleton drills, each with its forced-PASS flip, paired with WR-04's REASON-NULL-S:
- REASON-TOPLEVEL-S
- REASON-COLON-S
- REASON-HASH-S

**Evidence:**
- `mutant_survival_creation_gate.py`: rc 1 before (FORM-ignores-reason-lines survived at 32/32), rc 0 after.
  FORM-ignores-reason-lines is now killed at 33/37, and the control at 25/35.

### WR-06: the declaration polluted the router description after a block-scalar description

**Files modified:** `tools/skill_creation_gate.py`, `tools/test_skill_creation_gate.py`,
`vault/programs/skill-capability/owner-bundle.md`
**Commit:** 3f873803
**Applied fix:**
- `insert_declaration` now inserts the `metadata:` block immediately before the top-level `description:` line.
  It appends at the end only when the frontmatter has no `description:`.
- `modules/skill_router/skill_index.py` was not touched.
- The `[J]` owner-bundle line now states the placement constraint for skill-creator.

**Evidence:**
- `red_insert_declaration_block_scalar.py`: rc 1 before, rc 0 after.
- `red_skill_index_description_pollution.py` stays at rc 0 (0 of 24 descriptions changed).
- New line `V-SCG-ROUTER-DESCRIPTION` compares 38 insertions and finds no change. The 38 are 7 frontmatter shapes
  times 2 declaration kinds, plus every repo skill in three forms: undeclared, inserted and committed. Its
  positive control is the old append placement, which does change a folded description.
- Red mutant (append-at-end put back): `SCG_PASS=41/42`.
- The J render is unchanged.

### IN-01: FORM admitted non-canonical paths

**Files modified:** `tools/skill_creation_gate.py`, `tools/test_skill_creation_gate.py`
**Commit:** fba93b31
**Applied fix:** `_value_form_ok` now also requires `posixpath.normpath(value) == value`.
**Evidence:**
- Drills DOT-SEGMENT-CWST and TRAILING-SLASH-CWST give `{CWST:FORM}`, each with its flip.
- Red mutant: `SCG_PASS=42/44`.
- In `red_form_noncanonical_and_dup_reason.py`, the non-canonical half went from 3 admitted to `[]`.

### IN-02: a duplicated `opportunity_detector_reason` key passed all four clauses

**Files modified:** `tools/skill_creation_gate.py`, `tools/test_skill_creation_gate.py`
**Commit:** 8d4947ae
**Applied fix:** DECLARED now fails when there is more than one reason line.
**Evidence:**
- Drill DUPLICATE-REASON-S gives `{S:DECLARED}`, with its flip.
- Red mutant: `SCG_PASS=46/47`.
- `red_form_noncanonical_and_dup_reason.py`: rc 1 before, rc 0 after (together with IN-01).

### IN-03: K's row-count reason was inferred from the host name

**Files modified:** `tools/skill_handoffs.py`, `tools/test_skill_handoffs.py`,
`vault/programs/skill-capability/handoffs/K.md`, `vault/programs/skill-capability/ledger.json`
**Commit:** 419d35ac
**Applied fix:**
- `_report_rows` now reads `skill_opportunity_signals.card_state_dir()/ledger.jsonl` and states
  `card ledger present: <bool>`, or the read error.
- It says "no card ledger on this host" only when the ledger is absent.

**Rendered evidence and ledger:**
- `handoffs/K.md` was re-rendered (measured at 8d4947ae, sweep figures unchanged). On gex44 it reads
  `card ledger present: False; CO-12 file present: True, rows 0`.
- `state.K` sha256 was re-pinned to `496af4f7b6171a2b124f602f3e2830a29cf52427e9df56e86a278ba05edb08fe`, and its
  reason notes the change.

**Evidence:**
- Drill `V-SKH-K-ROWS-CARD-LEDGER` runs once with an empty HOME and once with a HOME that holds the card ledger.
- Red mutant (host-name reason put back): `SKH_PASS=40/41`.

## Skipped Issues

### IN-04: 7 of the 24 declared SKILL.md frontmatters are not valid YAML

**File:** `skills/{concurrent-writers-shared-tree,develop-here-prove-there,evaluation-corpus-governance,guard-event-reachability,monetary-quantity-integrity,presence-is-not-residency,recurring-work-cardinality}/SKILL.md`
**Reason:**
- The caller said to report this one only and not rewrite the 7 frontmatters.
- The defect predates phase 8: there is a `: ` inside plain-scalar descriptions, already a ScannerError at
  419c00a2.
- Re-measured after the fixes: `yaml_parse_all.py` still prints `bad= 7 n= 24`.
- The J ledger line "adding the declaration changed 0 of 72 validator outcomes" stays true only because these 7
  already fail. A YAML-based consumer, including the official validator, reads no declaration for them. That
  includes concurrent-writers-shared-tree, the only `opportunity_detector` skill.
- The fix is an Owner decision: quote or fold the 7 descriptions, or record the limit in the J evidence and
  ledger reason.

**Original issue:** the J gate is a line grammar, so it reports DECLARED PASS for these 7 while every YAML reader
sees none.

## Verification (committed blobs, after the last fix commit 419d35ac)

Verbatim:

```
$ python3 tools/test_skill_creation_gate.py | tail -3
[PASS] V-SCG-LIVE verdict=PASS population=24 fail_set_size=0 fail_set={}
# wall=6.5s
SCG_PASS=48/48

$ python3 tools/test_skill_handoffs.py | tail -3
[PASS] V-SKH-SELF-CLEAN (router, cost, writer, name) {'tools/skill_handoffs.py': (0, 0, 0, 0), 'tools/test_skill_handoffs.py': (0, 0, 0, 0)}
# wall=6.2s
SKH_PASS=41/41

$ python3 tools/skill_handoffs.py --check        (rc=0)
HANDOFF_I PASS reachability=PASS retirement=PASS nowrite=PASS skills=PASS contract=PASS
HANDOFF_K PASS aperture=PASS router=PASS control=PASS contract=PASS rows=UNMEASURED(no card ledger on this host (card ledger present: False; CO-12 file present: True, rows 0))
HANDOFF_L PASS absence=PASS control=PASS writer=PASS contract=PASS
HANDOFF_M PASS aperture=PASS cost=PASS control=PASS denominator=PASS contract=PASS
SKILL_HANDOFFS PASS pillars=4

$ python3 tools/skill_creation_gate.py | tail -1
SKILL_CREATION PASS population=24

$ python3 tools/test_contribution_verdict.py | tail -2
verdict: NOT_SEPARABLE
CT_PASS=14/14

$ python3 tools/test_skill_capability_program.py --status     (rc=0)
{"open": ["N"], "closed": ["A".."M"], "violations": []}

$ python3 tools/test_skill_capability_program.py --pillar A .. --pillar M
CEP_PILLAR_A=PASS  CEP_PILLAR_B=PASS  CEP_PILLAR_C=PASS  CEP_PILLAR_D=PASS  CEP_PILLAR_E=PASS
CEP_PILLAR_F=PASS  CEP_PILLAR_G=PASS  CEP_PILLAR_H=PASS  CEP_PILLAR_I=PASS  CEP_PILLAR_J=PASS
CEP_PILLAR_K=PASS  CEP_PILLAR_L=PASS  CEP_PILLAR_M=PASS
```

Reviewer RED scripts after the fixes:

| Script | Result |
|---|---|
| red_git_failure_not_inconclusive.py | rc 0 |
| red_m_denominator_unjudged.py | rc 0 |
| red_reason_yaml_null.py | rc 0 |
| red_insert_declaration_block_scalar.py | rc 0 |
| red_skill_index_description_pollution.py | rc 0 |
| red_form_noncanonical_and_dup_reason.py | rc 0 |
| mutant_survival_handoffs.py | rc 0 (control-K-router-pass killed) |
| mutant_survival_creation_gate.py | rc 0 (control killed) |
| yaml_parse_all.py | bad=7 (IN-04, not fixed) |

The J evidence render still matches its pin. The sha256 of `--render` output equals the sha256 of
HEAD:`evidence/J-creation-gate.md`, which equals the ledger state.J pin
`9a81387fb6b3e28b587aed8eb8fdc7d5e3843388f8e1dc4f6866c11081c9f7d2`. So no J re-pin was needed.

Not committed by this fixer: this report, `vault/progress.md` (a pre-existing modification),
`docs/{arch,changelog,constitution,prd}/*`, `.gsd/`, and `phases/07-contribution/07-VERIFICATION.md`.

---

_Fixed: 2026-10-04_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
