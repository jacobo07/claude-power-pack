# GSD X — resumption contract, wave N7

**Opened 2026-09-25.** Self-contained: a fresh worker continues from this file
with no prior conversation. `gsd-x-n6.RESUMPTION.md` is **not superseded** —
everything in its "must NOT be re-litigated" list still binds. This file records
what N7 measured on top of it.

## Identity

- Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch
  `feature/knowledge-acquisition`, worktree = **repo root**.
- **Do not move to `.claude/worktrees/gsd-x`.** That worktree is branch `gsd-x`
  at `a3411c9` (2026-09-15) and does **not** contain this mission.

## Correct the handoff before trusting it (third wave running)

N5 recorded this trap. N6 recorded that it recurred verbatim. It recurred again.

| N6→N7 handoff reported | measured at N7 start |
|---|---|
| HEAD `f91b451` | `d309865` — **~46 commits later** |
| "0 ahead of origin, all pushed" | **44 commits unpushed** |
| tree stable | **493 dirty paths** |

HEAD moved **five times during this session alone**
(`d309865`→`926ce75`→`9ae2eca`→`7f8412a`→`3be5780`→`13c66b0`), all foreign
(`product-demo`, `keos-qwen`, `tower`, `mission-continuity`, `provider-routing`).

**The instrument that works is the refuse-on-move guard, and it FIRED this
session**: the C2 commit was refused because HEAD had moved `7a7e419 →
13c66b0` between hunk inspection and commit. Classified (unrelated), then
re-committed. Prose in a handoff does not stop the next reader trusting a
snapshot; a guard does.

## What N7 has SEALED

### `7a7e419` — the loader learns v2

- `load_document()` reads v1 and v2 whole; `load()` keeps returning held facts
  and now accepts both (refusing v2 there would make every produced document
  unreadable). After this, `load()` has **no production caller**.
- v2 **requires** `state` and `depends_on`; unsupported version refused **by
  name**; one name may sit in exactly **one** bucket (a name in both `facts`
  and `unknown` is a contradiction and is refused, not resolved); a held entry
  with state `UNKNOWN` is refused.
- `SCHEMA` kept as a **live v1 alias** — the sealed parity proof reads it in six
  places — and `dump()` pinned to `SCHEMA_V1` explicitly.
- Fact-state vocabulary gets ONE owner beside `Fact`. Prose facts are
  `EXTRACTED`, never `DECLARED`.

### `41483b1` — freshness gets one owner

- `fingerprint`, `freshness_rows`, `freshness_verdict`, `reconcile_document`
  move into `structured_facts.py`; the producer imports and **re-exports**
  `reconcile` + the state constants (its own gates call `FP.SCHEMA`,
  `FP.UNKNOWN`, `FP.reconcile` by name), and gains a `sys.path` bootstrap **in
  the same commit as the import**.
- Per-entry rows split from the one-word aggregate. The aggregate answers
  `UNKNOWN` for **zero rows**, the same word a vanished source gets; its
  docstring says a blocking caller must never read it.

## What N7 MEASURED that changes the architecture

**F1 — the absence→completeness chain, proven at source.** `load()` had no state
field → `_has()` is set-membership → an absent fact derives no obligation →
`project_closure` can only block on obligations that exist → `may_close=True`.
"Measured false" and "could not measure" produced a byte-identical receipt.

**F2 — a verdict asymmetry.** The same missing fact passes at derive time and
goes `STALE` (blocking) at `invalidate_if_parent_gone`. Freshness already failed
closed; derivation failed open.

**F3 — §23's premise is REFUTED. Do not build a decision layer on gsd-core's
drift detector.** `gsd_run verify codebase-drift` counts new directories, barrel
exports, migrations and route modules against `STRUCTURE.md`
(`workflow.drift_threshold`, default 3; actions `warn|auto-remap`) and is
**"non-blocking by contract"**. It is codebase-structure currency, **not plan
premise validity**. There is no substrate for that slice.

**F4 — the orphan fact, computed not asserted.** `ORPHAN_FACT_NAMES` =
`{unattended_operation}`: produced by the Fact Producer, named in `FACT_NAMES`,
read by no operator. It can never change a verdict and must never hold a wave.

**F5 — `cmd_check` NEVER DERIVES (third door into the same defect, PRE-EXISTING
AND STILL OPEN).** It reads `.gsd-x/obligations.json`. Measured on one root,
same facts: **exit 0 before `derive`, exit 1 after**. A root nobody derived
passes the gate. Out of N7's approved scope; **this is the highest-value open
defect in the mission.**

**F6 — the v1 mutation drill had never produced a verdict on this host.**
`core.autocrlf=true`, so a file clean from checkout is CRLF while a dirty one
keeps LF. Anchors written with `\n` matched 0x in `gsd_x_mission.py`
(LF=302/CRLF=302) and the drill exited 2 as HARNESS — which says nothing about
the subject — while the regression line still quoted a mutation count. Both
drills now translate anchors to each file's own convention.

## Owner decisions, recorded — do not re-litigate

1. **Upstream report: draft locally, DO NOT FILE.** `open-gsd/gsd-core` is not
   ours. (Still owed — see below.)
2. **Push nothing.** Most unpushed commits are other panes' missions.
3. **Cut over into a SEPARATE mission root.** The benchmark stays on prose;
   `source_of()` there must not move under the parity proof.
4. **Leave `unattended_operation` produced-and-unconsumed.** No new operator —
   that would change what "done" means.
5. **Stop after S5** (Facts v2 end-to-end + cutover).
6. **Defer plan-premise validity** (and see F3: its premise was refuted anyway).

## What must NOT be re-litigated without new evidence

All ten items from N6, plus:

11. **A gating read and an enriching read are different things.** Only GATING
    unknowns may block. Of the two facts the producer can emit,
    `unattended_operation` is the orphan and `bounded_local_capacity` is
    **enriching-only** — so treating every read alike would make the ONLY
    producible unknown hold a wave over a missing clause, and the gate would be
    switched off. Enriching unknowns are DISCLOSED, never blocked on.
12. **Blindness is read from the DOCUMENT at check time, never from the
    obligation store** — because of F5. A store-driven blindness inherits that
    hole exactly.
13. **`UNMEASURED` is not measured-empty.** A receipt built without consulting a
    facts document and one built from a document with nothing unknown are
    different claims, and collapsing them commits this wave's own defect inside
    its own artifact.
14. **Blindness computes AFTER the goal-bound fork.** Goal-bound roots are out
    of scope: computing before the fork reds `V-CLI-BOUND-GATE-ASKS-THE-GOAL`
    and `V-CLI-BOUND-GATE-NOT-AN-ERROR` (both measured green at 25/25).
15. **Freshness for a blocking decision reads per-entry rows, never the
    aggregate.** Zero rows answers `UNKNOWN`, so the aggregate would let an
    empty facts file hold every wave.

## The honest boundary, and the next wave's first job

`V-FACTSV2-PRODUCER-REACH` asserts that **no fact the producer can emit is a
gating fact**. The blindness block branch is therefore **correct and not
reachable from the real producer**; it is proved on a constructed document. That
gate FAILS the day a producer emits a gating fact — which is exactly when this
paragraph must be rewritten.

**So the next wave's first action is to produce a GATING fact** (a real source
for `no_completion_signal`, `measured_failure_mode`, `destructive_act_commanded`,
`no_recovery_mechanism`, `reconstruction_relation` or `fidelity_requirement`),
so the mechanism becomes reachable from the world rather than from a fixture.

## Next exact valid actions, in order

1. **Produce a gating fact** (above). Until then the wave is proven but inert
   against real input.
2. **Close F5**: `cmd_check` must not pass a root nobody derived. This is the
   third door into the mission's own thesis and it is still open.
3. **Draft the upstream report** for D1/D2/D4 (do not send) — still owed from
   N6, unchanged.
4. Trust / executable-surface (C) — N6's D4, deferred by Owner answer 5.
