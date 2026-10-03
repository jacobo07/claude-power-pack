---
phase: 02-capability-subject-and-archetypes
verified: 2026-10-03T00:00:00Z
status: passed
score: 4/4 must-haves verified
covered_files:
  - .planning/workstreams/ucep/REQUIREMENTS.md
  - .planning/workstreams/ucep/phases/02-capability-subject-and-archetypes/02-01-PLAN.md
  - .planning/workstreams/ucep/phases/02-capability-subject-and-archetypes/02-01-SUMMARY.md
  - .planning/workstreams/ucep/phases/02-capability-subject-and-archetypes/02-02-PLAN.md
  - .planning/workstreams/ucep/phases/02-capability-subject-and-archetypes/02-02-SUMMARY.md
  - .planning/workstreams/ucep/phases/02-capability-subject-and-archetypes/02-03-PLAN.md
  - .planning/workstreams/ucep/phases/02-capability-subject-and-archetypes/02-03-SUMMARY.md
  - .planning/workstreams/ucep/phases/02-capability-subject-and-archetypes/02-04-PLAN.md
  - .planning/workstreams/ucep/phases/02-capability-subject-and-archetypes/02-04-SUMMARY.md
  - .planning/workstreams/ucep/phases/02-capability-subject-and-archetypes/02-05-PLAN.md
  - .planning/workstreams/ucep/phases/02-capability-subject-and-archetypes/02-05-SUMMARY.md
  - modules/capability_runtime/archetypes.py
  - modules/capability_runtime/trait_scan.py
  - tools/capability_traits.py
  - tools/test_capability_archetypes.py
  - tools/test_capability_trait_scan.py
  - vault/liveness/reachability_registry.json
covered_digest: "v1:sha256:ac982d83b07bc5707f42494a05c10466802c40adc9dcd1a467d4612c8966179b"
behavior_unverified: 0
overrides_applied: 0
gaps: []
deferred:
  - truth: "prompt-path delivery of the capability subject (no hook, command or module outside the tests imports archetypes or trait_scan)"
    addressed_in: "Phase 5 (envelope compiler) and Phase 6 (delivery)"
    evidence: "02-EVIDENCE section 8 and the two PLANNED registry rows; ROADMAP Phase 2 does not require wiring, only the reader contract."
  - truth: "producer hosting on a schedule (O-1); until done every real read of the cache is no-cache / UNJUDGED"
    addressed_in: "Owner step O-1 after merge (02-OWNER-QUEUE.md); not a ROADMAP phase"
    evidence: "02-EVIDENCE section 9. The SC requires miss -> UNJUDGED, which this state exercises."
owner_review_items:
  - id: WR-01
    item: "intent false positives: a generic verb-object pair plus a PRESENT structural anchor reads REQUIRED"
    verifier_decision: "does not break SC3 (see Criterion 3); errs toward more obligations, never fewer"
  - id: WR-02
    item: "a worktree root reads NO_CACHE because the producer keys the main repo and the reader keys the worktree"
    verifier_decision: "does not break SC2 (see Criterion 2); fails safe to UNJUDGED. Practical effect: the feature is inert for every .claude/worktrees/* mission, including this one, until decided"
  - id: WR-03
    item: "name-only evidence (migrations dir, schema.prisma, first five ui files) turns the cache STALE on the mission's own first edit"
    verifier_decision: "does not break SC2 (see Criterion 2); fails safe, pinned as intended by V-ARCH-STALE-EVIDENCE-FILE"
advisory:
  - finding: "02-EVIDENCE.md is stale against HEAD for two figures after the CR-01 fix (d61b5c23)"
    category: other
    reason: "EVIDENCE records CAPABILITY_TRAIT_SCAN_PASS=27/27 and 'all 9 causes reachable'; HEAD measures 28/28 and 10 causes (manifest-unparsed added). The verdicts are unchanged; the figures are older. 02-REVIEW-FIX.md records the new numbers."
    evidence_status: "verifier runs below"
  - finding: "V-ARCH-REAL-POLES (uncounted) makes the gate's exit code depend on two mutable repositories on this host (IN-06, left untouched)"
    category: other
    reason: "If InfinityOps changes its dependencies the archetypes gate goes red for a reason outside the phase. A missing path reads UNJUDGED, not FAIL. Does not affect any success criterion."
    evidence_status: "02-REVIEW IN-06"
  - finding: "the liveness exemption is a declaration (PLANNED), not reachability"
    category: other
    reason: "archetypes and trait_scan are ORPHAN and declared PLANNED with an Owner queue pointer; nothing live imports them yet. This is the honest state for Phase 2 and is what ROADMAP Phases 5 and 6 are for."
    evidence_status: "reachability.py --json row for each unit"
---

# Phase 2: Capability subject and archetypes - Verification Report

**Phase Goal:** A capability subject (traits + archetypes) resolved from repo reality first, intent second.
**Requirement:** UCEP-02 (declared in the 02-02 and 02-04 PLAN frontmatter and in the 02-02 SUMMARY `requirements-completed`; present in REQUIREMENTS.md mapped to Phase 2; no orphaned requirement).
**Verified:** worktree `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\ucep`, HEAD `0b2953af` (code last changed at `d61b5c23`, the CR-01 fix). Tracked tree clean except the five pre-existing untracked/dirty paths listed in 02-EVIDENCE section 4.
**Status:** passed
**Re-verification:** No, initial verification.

All numbers below were produced by the verifier in this run, not copied from SUMMARY or EVIDENCE. The PowerShell tool was not available to this agent, so each command was run as `powershell.exe -NoProfile -Command ...` through the Bash tool, Python by absolute path, from the worktree root.

## Suite and liveness re-run

| command | rc | summary line |
|---|---|---|
| `tools\test_capability_archetypes.py` | 0 | `CAPABILITY_ARCHETYPES_REAL_POLES=PASS` then `CAPABILITY_ARCHETYPES_PASS=59/59  threshold=59/59` (60 PASS lines: 59 counted plus the uncounted real-poles line; 0 FAIL lines; ran twice, same result) |
| `tools\test_capability_trait_scan.py` | 0 | `CAPABILITY_TRAIT_SCAN_PASS=28/28  threshold=28/28` |
| `modules\liveness\reachability.py` | 1 (expected) | `modules: 488  \|  REACHABLE: 299  \|  ORPHAN: 189  \|  UNKNOWN: 0  \|  gate offenders: 63` |

Liveness, by name, via `reachability.py --json` (the offender objects key on `unit`): 63 offenders now, 63 in `02-liveness-before.json` (head `409dca89`), `only_now: []`, `only_before: []`, offenders matching `archetypes|trait_scan`: 0. The two new units are ORPHAN with class PLANNED in the registry (`vault/liveness/reachability_registry.json:70` onward), each note naming `02-OWNER-QUEUE.md`. The gate stays red on standing debt, as before the phase; Phase 2 added none and cleared none. Rows 486 before, 488 now.

Scope: `git diff --name-only 409dca89 HEAD -- modules tools vault` lists exactly `modules/capability_runtime/archetypes.py`, `modules/capability_runtime/trait_scan.py`, `tools/capability_traits.py`, `tools/test_capability_archetypes.py`, `tools/test_capability_trait_scan.py`, `vault/liveness/reachability_registry.json`. Nothing under `vault/tower`. A grep of the five code files for debt-marker comments found none.

## Criterion 1: traits and archetypes as trait conjunctions; family and archetype independent

**Verdict: VERIFIED**

- `modules/capability_runtime/archetypes.py:64-65`: `TRAITS` is exactly the ten roadmap names in roadmap order: persistent, multi_actor, bulk, destructive, distributed, external_effect, scheduled, money, policy_layers, ui.
- `archetypes.py:146-169`: `ARCHETYPES` has three entries, each a conjunction (`anchor` trait + `modifiers` + `demoters`). Ids are single path segments (`ARCHETYPE_ID_RE`, line 139).
- `archetypes.py:700-731` `ceiling()`: REQUIRED only when the anchor is PRESENT and an intent fact exists and no demoter (line 721-725). `modifiers_for` (746-765) never feeds `ceiling`, so a modifier cannot create or change a strength.
- Independence: `resolve` (852-874) emits `archetypes` from `assess(...)` and `families` from `classify_prompt(...)` in separate keys. `active_archetypes` (843-849) reads only archetype strengths. Observed gates: `V-ARCH-ORTHOGONAL-A  families=['persistent_state'] active_archetypes=[] (family hit, zero archetypes)` and `V-ARCH-ORTHOGONAL-B  families=[] WORLD_MUTATION=REQUIRED (archetype REQUIRED, zero families)`.
- Strength is decided in one place: the only `Strength.REQUIRED` assignment in `modules/capability_runtime` is `archetypes.py:725`.

## Criterion 2: structural traits from an off-path cache keyed by repo root + cheap fingerprint; prompt path only reads; miss -> UNJUDGED

**Verdict: VERIFIED**

- Reader/producer split: `archetypes.py:14-17` states the contract and the module never imports `trait_scan` (grep: only docstring/comment mentions at lines 14, 17, 106). `_read_traits` (523-583) does one bounded file read (`CACHE_MAX_BYTES`, 539-541), a depth-1 fingerprint and at most `EVIDENCE_FILES_MAX` stats; it contains no walk and no producer call.
- Key: `cache_path(sroot)` from `repo_key(sroot)`; freshness from `fp1` plus evidence re-stat plus a 7 day age backstop (574-577).
- Miss is UNJUDGED, never absent: every refusal path returns `_all_unjudged(<cause>)` (526-535, 553, 581). The `read_traits` wrapper (586-605) never raises and always returns ten traits. Observed: `V-ARCH-MISS-UNJUDGED  9 unusable shapes (no file, non-JSON, other schema, missing trait, state MAYBE, foreign repo_key, > 262144 bytes, no produced_at, evidence path climbing...` PASS.
- Read-only on the prompt path, with a positive control: `V-ARCH-READ-ONLY  walk=0 scan=0 produce=0 over 20 resolve calls (fresh, stale, missing); _HOME unchanged (90 paths); median=13.66 ms p95=32.45 ms; control saw walk=1 sc...` PASS.
- Falsification, both drills red then restored: `V-ARCH-DRILL-ABSENT-ON-MISS  mutated ok=False calls=102 named_sub_assertion=True restored ok=True | READ-ABSENT[no-file]: a refused cache answered ABSENT ...` and `V-ARCH-DRILL-READER-SCAN  mutated ok=False calls=20 ... READER-WALKED: os.walk calls=14 during 20 resolve calls`. A reader that walked, or answered ABSENT on a miss, would fail the gate.
- Producer honesty (CR-01 fix verified in code): `trait_scan.py:555-556` returns `UNJUDGED manifest-unparsed` when any dependency-class trait has a manifest error; the cause is in `UNJUDGED_CAUSES` (`archetypes.py:93-95`). `V-ARCH-CAUSES-REACHABLE` reaches all 10 causes.
- Real poles (uncounted, read-only): InfinityOps `persistent=PRESENT(dependency+marker)`, `external_effect=PRESENT(dependency)`; ABSW2-Wii `persistent=UNJUDGED(no-manifest-ecosystem)`, not ABSENT.

**WR-02 and WR-03 against this criterion.** Neither contradicts the criterion as written. WR-02 (a worktree root keys a different file than the producer writes) yields `NO_CACHE` and all ten traits UNJUDGED `no-cache`, which is exactly what the criterion requires on a miss. WR-03 (evidence re-stat turns the cache STALE on a mission's own edit) yields UNJUDGED `stale`, also the required miss behaviour, and is pinned as intended by `V-ARCH-STALE-EVIDENCE-FILE`. Both fail toward UNJUDGED, never toward ABSENT. They are recorded as owner review items because they limit usefulness (the feature is inert for worktree missions until the repo-identity decision is made), not correctness.

## Criterion 3: intent-only traits are EXTRACTED and yield at most CONDITIONAL, never REQUIRED

**Verdict: VERIFIED**

- `ceiling()` lines 727-731: an ABSENT or UNJUDGED anchor with an intent hit returns `(CONDITIONAL, BASIS_INTENT)`; a WEAK anchor never reaches REQUIRED. `assess` (789-790) stamps `fact_state = EXTRACTED` whenever the basis is intent alone. Intent detectors return `fact_state: EXTRACTED` (`_intent_hit`, line 608-609).
- Observed: `V-ARCH-INTENT-ONLY-CAP  12 assessments over 2 intent-only subjects x 2 prompts: all CONDITIONAL/intent/EXTRACTED, no basis=intent REQUIRED`; the control `V-ARCH-INTENT-CONTROL  REQUIRED/structural+intent/OBSERVED for both` proves the cap is not a blanket refusal; `V-ARCH-STRUCTURE-ONLY-CONDITIONAL  9 checks: structure alone -> CONDITIONAL/structural, ABSENT and UNJUDGED -> NONE`.
- Falsification: `V-ARCH-DRILL-CEILING  mutated ok=False calls=12 named_sub_assertion=True restored ok=True | INTENT-ONLY-NOT-CAPPED[...]: strength=REQUIRED basis=intent ...`. A ceiling weakened to REQUIRED on any intent turns the gate red with the named sub-assertion.

**WR-01 against this criterion.** The criterion says INTENT-ONLY traits. WR-01's trace is a generic verb-object pair that coincides with a structural anchor that is already PRESENT, which is basis `structural+intent`, not intent-only. REQUIRED there is required by `ceiling`'s documented rule (anchor PRESENT and intent and no demoter), and the criterion is untouched: no input without a PRESENT structural anchor can reach REQUIRED. I read `ceiling` and confirmed there is no other path. WR-01 is a precision limit on the intent vocabulary, and when it errs it errs toward more obligations. It does not break the criterion; it is correctly an owner-review design item.

## Criterion 4: `tools/test_capability_archetypes.py` carries the four control classes

**Verdict: VERIFIED**

The file exists, its gates are registered in the run list, and the run above exited 0 with 59/59 and 0 FAIL lines. Each class, observed:

- Vocabulary-overlap negative control: `V-ARCH-VOCAB-OVERLAP-NEG  active=[] persistent=UNJUDGED AND classify_prompt('schema')=['persistent_state']` (a family fires on the word, no archetype does), plus `V-ARCH-DRILL-NOUN-LIST  mutated vocab ok=False noun-only ok=False calls=20 ... restored ok=True/True`.
- Intent-only control: `V-ARCH-INTENT-ONLY-CAP` and `V-ARCH-INTENT-CONTROL` (Criterion 3).
- Trait-transition recompiles differently: `V-ARCH-TRANSITION-PERSISTENT  CONDITIONAL/intent->REQUIRED/structural+intent sig=a2e66bc6c0a0b8ea->81cb73f56317c09c ... STALE seen; twin dir equa...` (ephemeral -> persistent; the signature is identical across runs and differs across the transition) and `V-ARCH-TRANSITION-DISTRIBUTED  BACKGROUND_JOB REQUIRED [] -> REQUIRED ['distributed'] after a compose file (STALE seen), sig 9fc8c35e204f177a -> 625c080109a00c59` (local -> distributed; the strength stays REQUIRED by design, the modifier and the signature change, which is the "recompiles differently" the design supports: modifiers raise consequence and never change strength).
- Positive controls per archetype: `V-ARCH-POSITIVE-WORLD_MUTATION`, `-EXTERNAL_EFFECT`, `-BACKGROUND_JOB` (each: Spanish and English prompts REQUIRED over real manifest evidence, the `-neg` variants CONDITIONAL/intent over an ABSENT anchor), and unit-level `V-ARCH-POSITIVE-UNIT-*` x3.

Each negative class has a drill that goes red when its target is mutated, so none of these is a gate that could not have failed.

## Requirements coverage

| Requirement | Source | Status | Evidence |
|---|---|---|---|
| UCEP-02 capability subject: traits from cached repo structure + intent; archetypes orthogonal to families; vocabulary alone never REQUIRED | 02-02, 02-04 PLAN frontmatter; REQUIREMENTS.md line 9 | SATISFIED | Criteria 1-4 above |

## Review items

| item | disposition |
|---|---|
| CR-01 (partial manifest read -> ABSENT) | Fixed at `d61b5c23`; code confirmed at `trait_scan.py:555-556`; `CAPABILITY_TRAIT_SCAN_PASS=28/28`, `V-ARCH-CAUSES-REACHABLE` reaches 10 causes |
| WR-01 intent false positives | Deferred; does not break SC3 (intent-only), owner review |
| WR-02 worktree roots read NO_CACHE | Deferred; fails safe, does not break SC2, owner review |
| WR-03 name-only evidence turns cache STALE | Deferred; fails safe, pinned as intended, does not break SC2, owner review |
| IN-01..IN-07 | Untouched; none changes a verdict a gate relies on (IN-06 noted as advisory) |

## Human verification

None required. Phase 2 has no rendered surface and no live path; the roadmap's four criteria are all code-and-gate properties that were exercised here. The Owner steps (O-1 hosting the producer, O-2 an optional SessionStart refresh) and the three deferred warnings are decisions, not unverified behaviour, and none blocks a success criterion.

## Production Reality

OBSERVED, not PROVEN, consistent with 02-EVIDENCE section 10: the code ran under real tests, fixtures and two real repositories read-only, on an unmerged branch, and nothing is wired to a live hook. No real cache exists under `~/.claude/state/tower` (02-EVIDENCE section 9), so every real-session read today is `no-cache` UNJUDGED until O-1 is done.

---

_Verified: 2026-10-03_
_Verifier: Claude (gsd-verifier)_
