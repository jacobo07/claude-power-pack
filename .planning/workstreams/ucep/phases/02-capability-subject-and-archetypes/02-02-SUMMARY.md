---
phase: 02-capability-subject-and-archetypes
plan: 02
subsystem: capability-runtime
tags: [ucep, archetypes, strength-ceiling, intent-facts, demoters, falsification-drill, bilingual, g16]

requires:
  - phase: 02-capability-subject-and-archetypes
    provides: 02-01 vocabulary (TRAITS, Strength, UNJUDGED_CAUSES, reading, assess, resolve) and the producer/reader split
provides:
  - archetypes.ceiling() -- the single function that decides every archetype strength
  - archetypes.TRAIT_INTENT -- bilingual verb-object vocabulary for six traits, with a near-linear bounded pair finder
  - demoters applied in assess() (REQUIRED -> CONDITIONAL, never NONE) and active_archetypes()
  - tools/test_capability_archetypes.py -- 29 hermetic V-ARCH gates including two falsification drills
affects: [02-03 structural detectors, 02-04 freshness and CLI, 02-05 subject signature, phase 5 envelope compiler]

plan_head_before: 9e9953b3fc0deed94222db65e1326b7ed1aed11f

actuals:
  tokens: 12200
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "one ceiling function decides strength; callers resolve it by module-global name so a drill can replace it"
    - "intent is a verb-object structure with a character window; a lone noun is never an intent fact"
    - "every negative control is paired with a drill that mutates the code and requires the control to go red, the wrapper to be reached, and the restore to go green"

key-files:
  created: []
  modified:
    - modules/capability_runtime/archetypes.py
    - tools/test_capability_archetypes.py

key-decisions:
  - "ceiling() treats PRESENT-without-intent and WEAK as CONDITIONAL (structural), intent-only as CONDITIONAL (intent, EXTRACTED), and only PRESENT+intent+no demoter as REQUIRED"
  - "TRAIT_INTENT is declared closed and fitted (GSDX-M04); structure-only CONDITIONAL compensates for a vocabulary miss"
  - "_spans mirrors applicability._hits exactly and is called only after families._match confirmed presence; a parity gate compares them over 18833 phrase/text pairs"
  - "traits without an intent detector (multi_actor, distributed, policy_layers, ui) read UNJUDGED no-intent-detector rather than getting a noun bag"
  - "ES escribir is deliberately NOT a persistent verb, because it is a WORLD_MUTATION demoter phrase (sin escribir)"

patterns-established:
  - "drill gate = mutation + counting wrapper + named sub-assertion in the red evidence + restore check + green re-run"
  - "intent pair search: objects sorted by start and by end, one bisect per verb on each side"

requirements-completed: [UCEP-02]

coverage:
  - id: D1
    description: "A single ceiling function decides every archetype strength: REQUIRED only for a PRESENT anchor plus an intent fact and no demoter; intent over an ABSENT or UNJUDGED anchor is at most CONDITIONAL stamped EXTRACTED; WEAK never reaches REQUIRED; structure alone is CONDITIONAL (R-1)"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-INTENT-ONLY-CAP"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-INTENT-CONTROL"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-WEAK-CAP"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-STRUCTURE-ONLY-CONDITIONAL"
        status: pass
    human_judgment: false
  - id: D2
    description: "Vocabulary alone never makes an archetype: noun-only prompts yield no intent fact, a docs-only repo with the bare prompt `schema` has no active archetype while the family matcher still hits persistent_state, and family and archetype are independent outputs"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-NOUN-ONLY-NEG"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-VOCAB-OVERLAP-NEG"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-ORTHOGONAL-A"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-ORTHOGONAL-B"
        status: pass
    human_judgment: false
  - id: D3
    description: "Bilingual verb-object intent for six traits (persistent, external_effect, scheduled, destructive, bulk, money), demoters that lower REQUIRED to CONDITIONAL and never to NONE, one Spanish and one English positive per archetype, matcher parity with _hits, and bounded input (200000 characters in under 1 s)"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-DEMOTE-NOT-VETO"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-POSITIVE-UNIT-WORLD_MUTATION"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-POSITIVE-UNIT-EXTERNAL_EFFECT"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-POSITIVE-UNIT-BACKGROUND_JOB"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-TRAIT-INTENT-SHAPE"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-MATCHER-PARITY"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-INTENT-BOUNDED"
        status: pass
    human_judgment: false
  - id: D4
    description: "The two central controls are shown falsifiable: a weakened ceiling turns the intent-only cap red and a bag-of-nouns intent detector turns the vocabulary-overlap and noun-only controls red, each with the mutation reached and the restore green"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-DRILL-CEILING"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-DRILL-NOUN-LIST"
        status: pass
    human_judgment: false

duration: 14min
completed: 2026-10-03
status: complete
---

# Phase 2 Plan 02: The strength ceiling and bilingual intent facts Summary

**One `ceiling()` function now decides every archetype strength (REQUIRED needs PRESENT structure plus a verb-object intent and no demoter; intent alone is CONDITIONAL and EXTRACTED), over a closed bilingual verb-object vocabulary for six traits, with two falsification drills showing the cap and the noun-only control can go red**

## Performance

- **Duration:** about 14 min
- **Started:** 2026-10-03T17:38:59Z
- **Completed:** 2026-10-03T17:53:15Z (last task commit and final gate run)
- **Tasks:** 3 (1 tracer, 1 TDD auto, 1 auto)
- **Files modified:** 2 (`modules/capability_runtime/archetypes.py`, `tools/test_capability_archetypes.py`); no file created

## RED run 02-02 Task 1

HEAD at the time: `9e9953b3fc0deed94222db65e1326b7ed1aed11f` (02-01 close-out, the plan head ledger value). rc=1.

```
  FAIL V-ARCH-INTENT-ONLY-CAP    INTENT-ONLY-NOT-CAPPED[cache-miss/añade una tabla de suscr]: strength=NONE basis=none fact_state=UNKNOWN intent_fact_state=UNKNOWN span_len=0; INTENT-ONLY-NOT-CAPPED[cache-miss/save each player's coins]: strength=NONE basis=none ... intent_fact_state=EXTRACTED span_len=24; ...
  FAIL V-ARCH-INTENT-CONTROL     CONTROL-NOT-REQUIRED[añade una tabla de suscr]: strength=NONE basis=none anchor_fact_state=OBSERVED reason=intent persistent (no-intent-match)
CAPABILITY_ARCHETYPES_PASS=12/14  threshold=14/14
rc=1
```

The twelve 02-01 gates stayed green. The Spanish prompt was not matched at all (`no-intent-match`) and intent over missing structure read NONE, exactly the two behaviours the task builds.

## GREEN line, Task 1 (commit `f9ee905a`)

`CAPABILITY_ARCHETYPES_PASS=14/14  threshold=14/14` rc=0; `FAMILY_BASELINES_PASS=20/20  threshold=20/20`; `FINJ_PASS=24/24  threshold=24/24`. The tracer feedback gate (`<verify>` re-run) passed end to end before Task 2 started: Task 2's RED run shows all 14 earlier gates still PASS. Logged `Tracer verified end-to-end -- expanding`.

## RED run 02-02 Task 2

HEAD at the time: `f9ee905a`. rc=1, `CAPABILITY_ARCHETYPES_PASS=18/27  threshold=27/27`.

- **FAIL (9):**
  - `V-ARCH-WEAK-CAP` (EXTERNAL_EFFECT and BACKGROUND_JOB prompts read basis `structural`, there is no intent detector for them)
  - `V-ARCH-DEMOTE-NOT-VETO` (strength REQUIRED with `demoted_by=[]`, demoters not applied)
  - `V-ARCH-POSITIVE-UNIT-EXTERNAL_EFFECT` and `V-ARCH-POSITIVE-UNIT-BACKGROUND_JOB` (`intent UNJUDGED (no-intent-detector)`)
  - `V-ARCH-VOCAB-OVERLAP-NEG` and `V-ARCH-ORTHOGONAL-A` (`AttributeError: no attribute 'active_archetypes'`)
  - `V-ARCH-TRAIT-INTENT-SHAPE` (no-detector set was nine traits, wanted exactly four)
  - `V-ARCH-MATCHER-PARITY` (`AttributeError: no attribute 'TRAIT_INTENT'`)
  - `V-ARCH-INTENT-BOUNDED` (the 02-01 all-pairs detector took **2865 ms** on the 200000-character prompt against the 1000 ms limit; `INTENT_MAX_CHARS` absent)
- **Already PASS in RED (4 new):** `V-ARCH-STRUCTURE-ONLY-CONDITIONAL` and `V-ARCH-POSITIVE-UNIT-WORLD_MUTATION` (Task 1's `ceiling` already covers them), and `V-ARCH-NOUN-ONLY-NEG` and `V-ARCH-ORTHOGONAL-B` (the 02-01 English-and-structure detector already refuses a lone noun and the ORTHOGONAL-B prompt was already REQUIRED). Each carries its own instrument control (`add a table` must read PRESENT; the `classify_prompt == []` precondition), and `V-ARCH-NOUN-ONLY-NEG` is shown able to fail by the Task 3 drill rather than by a RED run.

## GREEN line, Task 2 (commit `7e69bc3d`)

`CAPABILITY_ARCHETYPES_PASS=27/27  threshold=27/27` rc=0; `FAMILY_BASELINES_PASS=20/20`; `FINJ_PASS=24/24`. Evidence lines:

- `V-ARCH-INTENT-BOUNDED`: 200000-char prompt `intent_facts=237 ms` (limit 1000); pair at 25000 -> UNJUDGED, at offset 100 -> PRESENT; max_chars=20000.
- `V-ARCH-VOCAB-OVERLAP-NEG`: `active=[] persistent=UNJUDGED AND classify_prompt('schema')=['persistent_state']` (both halves).
- `V-ARCH-MATCHER-PARITY`: `comparisons=18833 agree_true=155 agree_false=18678 mismatches=[]`.
- `V-ARCH-ORTHOGONAL-A`: families=['persistent_state'] active_archetypes=[]; `V-ARCH-ORTHOGONAL-B`: families=[] WORLD_MUTATION=REQUIRED.

## Task 3 drill evidence (commit `9d1b57c4`, test file only)

No RED run: the drill is the red branch of its target gate.

**V-ARCH-DRILL-CEILING** (weakened ceiling returns `(REQUIRED, "intent")` whenever `intent_hit`): `mutated ok=False calls=12 named_sub_assertion=True restored ok=True`. Mutated `V-ARCH-INTENT-ONLY-CAP` evidence:

```
INTENT-ONLY-NOT-CAPPED[cache-miss/añade una tabla de suscr]: strength=REQUIRED basis=intent fact_state=EXTRACTED intent_fact_state=EXTRACTED span_len=15;
INTENT-ONLY-NOT-CAPPED[cache-miss/save each player's coins]: strength=REQUIRED basis=intent ... span_len=24;
INTENT-ONLY-NOT-CAPPED[produced-ephemeral/añade una tabla de suscr]: strength=REQUIRED basis=intent ...;
INTENT-ONLY-NOT-CAPPED[produced-ephemeral/save each player's coins]: strength=REQUIRED basis=intent ...;
INTENT-BASIS-REQUIRED: ['cache-miss/añade una tabla de suscr/WORLD_M...
```

**V-ARCH-DRILL-NOUN-LIST** (intent detector degraded to any persistence noun, no verb): `mutated vocab ok=False noun-only ok=False calls=20 named_sub_assertions=True restored ok=True/True`. Mutated evidence:

```
V-ARCH-VOCAB-OVERLAP-NEG: VOCAB-ACTIVE-ARCHETYPE: ['WORLD_MUTATION'] active for the bare prompt `schema` over a docs-only repo
V-ARCH-NOUN-ONLY-NEG: NOUN-ONLY-INTENT['schema']: PRESENT for ['persistent']; NOUN-ONLY-REQUIRED['schema']: WORLD_MUTATION;
  NOUN-ONLY-INTENT['la tabla']: PRESENT for ['persistent']; NOUN-ONLY-REQUIRED['la tabla']: WORLD_MUTATION; ...
```

Neither target predicate stayed green under its mutation, so no predicate needed repair.

## Final gate lines (HEAD `9d1b57c4`)

```
CAPABILITY_ARCHETYPES_PASS=29/29  threshold=29/29   rc=0
FAMILY_BASELINES_PASS=20/20  threshold=20/20        rc=0
FINJ_PASS=24/24  threshold=24/24                    rc=0
```

`git diff --name-status 9e9953b3..HEAD` lists exactly `M modules/capability_runtime/archetypes.py` and `M tools/test_capability_archetypes.py`; `modules/tower/families.py` is in no diff. Measured `git rev-list --count 9e9953b3..HEAD` = 3 at SUMMARY write.

## Accomplishments

- `archetypes.ceiling(anchor_state, intent_hit, demoted)` is the only place a strength is decided; `assess` calls it by module-global name and derives `fact_state` (EXTRACTED for intent alone, OBSERVED when structure is in the basis, UNKNOWN for none). The live defect behind audit G16, a word alone producing a requirement, is unrepresentable: an intent-only archetype is CONDITIONAL and EXTRACTED in both languages.
- `TRAIT_INTENT` gives six traits a bilingual verb-object detector (persistent, external_effect, scheduled, destructive, bulk, money); four traits read `no-intent-detector`. Pair search is near-linear (bisect), input is cut at `INTENT_MAX_CHARS` = 20000, and a 200000-character worst case runs in about 240 ms where the old all-pairs detector took 2865 ms.
- Demoters are applied in `assess` and lower REQUIRED to CONDITIONAL only; `active_archetypes(subject)` exposes REQUIRED/CONDITIONAL ids so family and archetype can be shown independent.
- Two drills show the cap and the noun-only control can return the other answer.

## Task Commits

1. **Task 1 (tracer): single ceiling function** - `f9ee905a` (feat) -- `archetypes.py`, `test_capability_archetypes.py`
2. **Task 2: bilingual verb-object intent, demoters, orthogonality** - `7e69bc3d` (feat) -- same two files
3. **Task 3: falsification drills** - `9d1b57c4` (test) -- test file only

**Plan metadata:** the SUMMARY commit and the STATE/ROADMAP/REQUIREMENTS commit follow.

## TDD Gate Compliance

Task 2 is `tdd="true"`, and the plan prescribes ONE commit per task, so the RED state is recorded as a run (stdout, rc, HEAD above) rather than a separate `test(02-02)` commit. The only test-typed commit is Task 3's drill commit, by design. Both RED runs executed before any implementation line existed.

## Decisions Made

See `key-decisions`. The four choices the plan left open: the exact vocabulary inflections, the `bulk` quantifier set (over the destructive object set), excluding `escribir` from persistent verbs (it is a demoter phrase), and returning `no-intent-match` (not `no-intent-detector`) for a detected trait with no hit.

## Deviations from Plan

### Auto-fixed Issues

None - no Rule 1-3 fix was needed; the plan executed as written.

### Execution-environment notes (not code deviations)

1. **Woz write-gate veto on filler text.** The first draft of the bounded-input gate used a stock Latin filler phrase, which the write gate blocked as filler copy. The filler was changed to neutral words ("alpha beta"); no behaviour changed.
2. **Anti-thrash hook.** The hook blocked a third consecutive Edit on the same file more than once (the vetoed attempt counted); each time a Read of the path reset it and the work continued with consolidated edits.
3. **Branch namespace and Bash guard.** As in 02-01: this is the sequential executor on the orchestrator-designated branch `ucep/mission` (HEAD verified attached and not a protected branch before every commit, root pin passed before every commit); git calls carry the guard's `# bash-safe` marker and outputs were read with Read/Grep. No guard was disabled.

**Total deviations:** 0 auto-fixed, 3 environment notes. **Impact:** none on scope; the committed paths equal the frontmatter `files_modified`.

## Issues Encountered

None beyond the environment notes above.

## Known Stubs

None. The four traits without an intent detector read UNJUDGED `no-intent-detector` on purpose (a noun bag would reopen the D7 defect at trait level), and structural detectors for every trait other than `persistent` remain 02-03's scope; both are named, tested states.

## Threat Flags

None. The detector reads only the prompt text, bounded at 20000 characters, with escaped phrases and word boundaries and no nested quantifiers; it adds no network, file or auth surface. T-02-05, T-02-07, T-02-09 and T-02-11 are mitigated as planned and covered by `V-ARCH-INTENT-BOUNDED`, `V-ARCH-NOUN-ONLY-NEG`, `V-ARCH-VOCAB-OVERLAP-NEG`, the two drills and `V-ARCH-MATCHER-PARITY`.

## User Setup Required

None - no external service configuration.

## Next Phase Readiness

- 02-03 can extend `trait_scan` with manifest, dependency and marker detectors and the ABSENT entitlement rules; `ceiling` already maps ABSENT, WEAK and PRESENT anchors, so any new structural state flows through unchanged.
- The 02-01 API remains intact (names added only): `TRAITS`, trait states, `Strength`, `UNJUDGED_CAUSES`, `reading`, `unjudged_reading`, `subject_root`, `cache_path`, `read_traits`, `resolve`, and the assessment keys of `assess`.
- Enforcement stays report-only until Phase 8 (T-02-07).
- No blockers.

## Self-Check: PASSED

- Modified files exist: `modules/capability_runtime/archetypes.py`, `tools/test_capability_archetypes.py` (FOUND for each).
- Commits exist: `f9ee905a`, `7e69bc3d`, `9d1b57c4` (each in `git log 9e9953b3..HEAD`).
- Plan-level verification re-run at HEAD: `CAPABILITY_ARCHETYPES_PASS=29/29`, `FAMILY_BASELINES_PASS=20/20`, `FINJ_PASS=24/24`; the diff against the 02-01 head lists only the two frontmatter files; `modules/tower/families.py` untouched.

---
*Phase: 02-capability-subject-and-archetypes*
*Completed: 2026-10-03*
