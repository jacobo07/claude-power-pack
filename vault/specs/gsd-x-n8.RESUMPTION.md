# GSD X — resumption contract, wave N8 (in flight)

**Opened 2026-09-27.** Self-contained: a fresh worker continues from this file with
no prior conversation. `gsd-x-n7.RESUMPTION.md` and `gsd-x-n6.RESUMPTION.md` are
**not superseded** — everything in their "must NOT be re-litigated" lists still
binds except where this file records new evidence against a specific item.

## Identity

- Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch
  `feature/knowledge-acquisition`, worktree = **repo root**.
- **Do not move to `.claude/worktrees/gsd-x`.** That worktree is branch `gsd-x` and
  does not contain this mission.

## Correct the handoff before trusting it (FOURTH wave running)

N5 recorded this trap, N6 recorded it recurring, N7 recorded it recurring verbatim.
It recurred again, twice, inside this session alone.

| N7 handoff reported | measured at N8 start |
|---|---|
| HEAD `9459d5f` | **`24d404c`** — 8 commits later |
| `bc73a94`, `a82da97` local-only | **all five N7 commits are on origin** |
| — | ~48 modified, ~380 untracked |

Then HEAD moved twice more **during** this session: `24d404c` → `360b42cc` while
the plan was being written, and `360b42cc` → `ca69a044` between two of my own
commits. Ten foreign commits landed (keos-qwen, gsd-mission, TIS, pricing). The
refuse-on-move guard was run before every commit and did not need to fire, because
each capture-to-commit window was short.

**Measured and recorded so the next reader does not have to:** none of the ten
touched a file this mission depends on. `tools/gsd_mission.py` is a **different
file** from `tools/gsd_x_mission.py`; they are one underscore apart and they are
owned by different panes.

## What N8 has SEALED

### `312717f` — the upstream D1/D2/D4 draft, owed since N6

`vault/upstream/gsd-core-1.14.0-D1-D2-D4.md`. **NOT FILED** — Owner answer 1 stands.
All three sites re-read at the installed `VERSION 1.14.0`, which N6 measured as
identical to the registry's `latest`:

- **D1** `check-command-router.cjs:1099-1108` forwards five fields and drops
  `error`, which `shell-command-projection.cjs:588-593` deliberately preserves.
- **D2** `gate-predicate-evaluator.cjs:78-102` branches three ways; line 94's own
  comment concedes non-zero ⇒ block. **D2 cannot be fixed without D1** — the
  evidence it needs is the field D1 drops.
- **D4** `capability-trust.cjs:635` omits gates from `hasExecutable`; line 1181
  prints "declarative only" for a capability that runs `sh -c`.

**New, and it changes the report:** lines 633-634 carry an **ADR-2363 D3** comment
recording a deliberate decision to keep *instruction* surfaces out of that same
expression, because including them would perturb `executableSetChanged` and the
re-consent trigger. A one-line "add gates" patch walks into a documented ADR, so
the draft argues the distinction instead — an instruction surface changes what the
agent is told, a gate predicate changes what the machine executes — and states the
compatibility cost a maintainer will ask about: a one-time re-consent wave for
every installed capability declaring a gate.

### `5067866` — a mutation drill must prove its own mutation happened

`tools/test_mutation_harness_validity.py`, MHV_PASS=7/7.

N7 fixed **its two** drills after F6 and nobody swept the class. Swept: 12
harnesses, 11 real drills, **exactly 2 prove their perturbation applied** — the two
N7 fixed. Nine are frozen in `KNOWN_WEAK`; the list may only shrink.

Enforced: an applied-proof, a HARNESS class distinct from a subject verdict, and a
hash-verified restore. EOL/CONTROL/REASON are reported and not enforced, because
charging ceremony is how a gate gets switched off.

The instrument is guarded before its verdicts are: a population floor of 8, a
positive control verified by reading, a **synthetic** red/green pair so the drill
represents the class rather than an instance, and NOT-A-DRILL decided by
measurement rather than a skip list.

## What N8 MEASURED that changes the architecture

**F7 IS CLOSED.** `modules/gsd_x/mission/coverage.py`. The required set is
`GATING_FACT_NAMES` minus the gating facts of DEAD operators, and nothing wider.

The justification is arithmetic, not taste: **the prose adapter evaluates all ten
patterns on every run**, so absence of an obligation there means ten questions were
asked and none matched. A structured document disclosing one of six gating names
has been asked one question. That difference *is* the cutover loss.

- `UNPRODUCED` is a new category, kept distinct from `UNKNOWN`. Unknown = a
  producer tried and could not measure. Unproduced = nobody asked. Different
  repairs, so they never share a field.
- A **DEAD operator** (any gating fact in `not_held[]`) requires nothing further:
  `_has()` is `all(...)`, so it can never fire and its siblings are ceremony.
- Enriching (3) and orphan (1) names are **never** required. Requiring the whole
  vocabulary would turn a ten-name dictionary into a universal prerequisite list.

**Six poles measured against the live CLI, all correct on the first run:**

| pole | result |
|---|---|
| F7 shape (1 gating fact disclosed) | exit 1, names 5 unproduced, 5 reasons, non-empty message |
| all 6 dispositioned | exit 0 — the requirement is SATISFIABLE |
| enriching + orphan unknown | exit 0, 1 disclosure |
| dead operator | exit 0 — no ceremony tax |
| prose | exit 0, unchanged |
| empty document | exit 1, 6 unproduced, **`stale=[]`** |
| `closure` on the F7 root | **DENIED**, exit 1 — agrees with `check` |

## What the AUDIT killed, and why it was right

`oneshot-architect-auditor` returned 10 gaps. Three were fatal to the approved plan
and are recorded here so nobody rebuilds them.

1. **F5 as "never derived → exit 2" is REJECTED.** `_run_check()` runs `check` with
   no preceding `derive` in nearly every pinned case, so it moved **8 gates** off
   their pinned codes — including `V-FACTSV2-GREEN-PROSE` and
   `V-FACTSV2-GREEN-EMPTY-DIR`, the exact poles `gsd_x_mission.py:356-359` names as
   survivors of the previous two widenings. It would have been the **third**
   burning of that predicate, and at runtime it blocks every wave on the host until
   a human runs `derive`. **F5 folds into coverage instead**: an F7 root blocks
   because the DOCUMENT is incomplete, which is computed without the store.
2. **The prose extractor as a coverage oracle is REJECTED.** Its documented dominant
   failure is a SILENT MISS (`obligation.py:162-170`), so its errors point
   **fail-open** — the wrong way for a floor. And `README.md`/`INTENT.txt` reach the
   CLI through `_read()`, which refuses nothing and returns `""` for an absent file,
   so an author could lower the requirement floor by writing less.
3. **"Operator is active if one of its gating facts is disposed" is REJECTED.** A
   document carrying only `unattended_operation` plus thin prose activates nothing
   under that rule, and F7 survives untouched — in exactly the serious-mission case,
   since `obligation.py:108-110` already says a real mission's reality is a codebase
   and a runbook, **not one README**.

Also accepted from the audit and fixed: `project_closure` must carry UNPRODUCED or
`cmd_closure` prints ALLOWED while `cmd_check` exits 1 with an **empty** message
(gap 8); `cmd_derive` must report coverage or the two surfaces disagree about one
root (gap 9); `structured_facts.load()`'s claim that "a gate asserts this function
has no production caller" is **false twice over** — no such gate exists, and
`gsd_x_mission.py:64` calls it (gap 7).

## Open, and named rather than hidden

- **Gap 10 — a new ratchet family would reach ZERO repos.** `families.py:155-159`:
  a family with empty `repo_markers` and no `delegate` lands in **neither**
  `report["in"]` nor `report["unjudged"]` — silently OUT of every repo, with no
  UNJUDGED signal. All four existing families have a structural route
  (`persistent_state` via `delegate: "family_scan"`). **Fix that hole before
  promoting anything**, or the promotion is documentation.
- ~~**Gap 5 — UNPRODUCED is unclearable.**~~ **CLOSED.**
  `tools/gsd_x_fact_producer.py` now emits `measured_failure_mode`, **the first
  GATING fact any producer on this host has ever emitted**. OBSERVED from
  `vault/ceps/events.jsonl`: a `pattern_signature` seen twice or more is a
  failure mode with a measured frequency, which is exactly what
  `op_failure_consequence` gates on and exactly what its authority line ("the
  environment's own measurements") means. Live: **106 recurring signatures
  across 1,710 events**, HOLDS.

  Deliberately NOT mission-scoped, unlike `unattended_operation`. That fact
  asserts something about THIS root, so another pane's marker would be a
  cross-mission leak; this one asserts something about the ENVIRONMENT, which is
  shared. The evidence names the window and totals so a reader can disagree.

  **Two consequences the next worker must not be surprised by:**
  1. `V-FACTSV2-PRODUCER-REACH` asserts as a live measurement that no producible
     fact is gating. **It must now go red**, and its own text says so: *"That
     gate FAILS the day a producer emits a gating fact -- which is exactly when
     this paragraph must stop being true."* Invert it in place, and rewrite the
     HONEST BOUNDARY paragraph in that file's header.
  2. A produced document today disposes of 3 of 10 names, so **five gating facts
     are still UNPRODUCED** and a real structured mission still blocks --
     correctly, naming the five that need producers. That is clearable-but-not-
     yet-cleared, which is the honest state, not a deadlock.

  **Do not commit a produced FACTS.json.** Its `depends_on` fingerprints
  `host-memory-floor.json` and `events.jsonl`, both of which change every few
  minutes, so any committed document is STALE within minutes of landing. N7
  recorded this for the first source; the second has the same property.
- **The `message` field leads with the wrong reason.** `cmd_check` builds it from
  `receipt.blocking`, which includes "explicit backlog is not empty" — a mission
  closure condition the file says is explicitly not what a wave gate decides on.
  `block_reasons` carries the precise list. Cosmetic, pre-existing, now more
  visible.
- **Baseline ratchet inheritance is still unwired.** `families.classify_prompt` and
  `donegate.judge` have **zero production callers**; `donegate` is REPORT-ONLY by
  spec §7. Promotion and anti-downgrade are live; nothing reaches a future mission.

## What must NOT be re-litigated without new evidence

All items from N6 and N7, plus:

16. **The required set is the GATING set minus dead operators.** Not the whole
    vocabulary (universal prerequisite list, ceremony tax, gate gets switched off),
    and not a subset chosen by an activation heuristic (audit gaps 2 and 3 both
    falsify that, in opposite directions).
17. **UNPRODUCED and UNKNOWN never share a field.** A measurement that failed and a
    question nobody asked need different people doing different work.
18. **Do not widen `cmd_check`'s exit code again without driving every GREEN pole
    first.** It has now been widened three times and the third attempt was caught
    only by an adversarial audit, not by the suite.
19. **A uniform answer across a whole swept population is a blind detector, not a
    uniform defect.** The first mutation sweep reported `applied=NO` for all 12
    including the two good ones, because the predicate looked for
    `applied|occurrences` and the real proof is spelled `text.count(old_a) != 1`.

## GEX44-PROVEN (2026-09-28) — the F7 closure survives all 13 mutants

The local host fell to ~98 MB free of 32 GB and a local drill was killed mid-run
(the `held-unknown-allowed` residue above). Verification moved to GEX44 under
develop-here-prove-there, in an **isolated worktree** `/home/kobii/missions/_gsdx_n8_drill`
pinned at `1016b76` with the two test files shipped over scp and **sha256-matched at
both ends** (`4abafbb5…` gate, `89a3f4c9…` drill). Never run it in the shared
GEX44 checkout: that one has a live writer.

| run | result | what it meant |
|---|---|---|
| 1 | HARNESS | control red on `V-FACTSV2-PRODUCER-REACH` — the predicted inversion; fixed `8405cc6` |
| 2 | 10/13 | three survivors, **all instrument errors of mine**, fixed `784e446` |
| 3 | **13/13**, restore sha256-verified, worktree dirty only in the two shipped files | tier `GEX44-PROVEN` |

Run 2's three survivors, so nobody re-derives them:
- `blindness-from-aggregate` was CAUGHT and scored SURVIVED — its `must` still named
  the pre-inversion gate `GREEN-EMPTY-DOCUMENT`. A stale gate name reads exactly
  like a coverage gap.
- `coverage-requires-nothing` was **equivalent**: `frozenset() or X` returns X
  because the empty set is falsy. Re-anchored on the comprehension filter.
- `coverage-ignores-dead-operators` could not discriminate: the pole used an
  operator with ONE gating read, so killing it required nothing either way.
  Rebuilt on a two-read operator with a precondition asserting both names.

Commits after `1016b76` on this mission: `8405cc6`, `784e446`. **Local only.**
Owner N7 answer 2 (push nothing) stands.

## Next exact valid actions, in order

0. ~~Retranslate the `blindness-never-blocks` anchor.~~ DONE, drill 13/13 on GEX44.
1. ~~Produce a gating fact.~~ DONE `99e96e1`.
2. ~~Fix `repo_family_report`'s silent-OUT hole.~~ DONE `2a80b35`.
3. Run the earned laws through `modules/tower/ratchet.promote`, then prove one
   inheritance path end to end — or name the missing mechanism as the next blocker.
4. Recompile the frontier against `C:\Users\User\Downloads\Dataset GSD X 1.txt`
   (762 KB, 24,148 lines; §50's candidate list is its own section).
