# Required-Input Closure, and the false-completeness family

**Source: GSD X N8, 2026-09-27.** Written as a separate file rather than appended
to `ukdl-universal.md` because another pane was writing that file during this
session; extending a shared file while a live writer is in it is how a commit
swallows someone else's hunks.

Every defect below is one shape at a different altitude:

> **A decision cannot be stronger than the closure of its required inputs — and
> the absence of a required input is silent by construction, because nothing
> downstream can distinguish "asked and answered no" from "never asked".**

---

## T-UNPRODUCED-REQUIRED-INPUT-DISAPPEARS-001 (TRAP)

**Symptom.** Placing a `FACTS.json` in a fresh mission root silently deleted
every obligation the prose adapter would have derived. Same INTENT, same README:

    prose       -> DO-1 ACCEPTED, check exit 1
    structured  -> derived 0,     check exit 0, unmeasured_facts []

**Root cause.** The blindness channel read the document's `unknown[]` bucket. All
three buckets cover facts a producer *tried* to establish. A gating fact with no
producer at all is in none of them, so `_has()` was False, no obligation derived,
and `project_closure` — which can only block on obligations that EXIST — reported
ALLOWED.

**Enabling condition.** A richer input format replacing a poorer one, where the
poorer one was *exhaustive by construction*. The prose adapter evaluates all ten
patterns on every run; a structured document answers only the questions its
author thought to answer. Nobody compared the two counts.

**Violated invariant.** Absence of evidence is not evidence that no obligation is
owed.

**Fix.** `modules/gsd_x/mission/coverage.py`. Required = `GATING_FACT_NAMES` minus
the gating facts of DEAD operators. Anything required and in no bucket is
`UNPRODUCED` and blocks, named.

**Minimal reproducer.** A v2 document holding one gating fact, in a root with an
intent the prose adapter would derive an obligation from.

**Regression.** `V-FACTSV2-CUTOVER-CANNOT-LOSE-OBLIGATIONS` — the inverted
characterization; the diff between its two versions is the evidence.

**Counterexample that must keep passing.** A document disposing of every gating
fact exits 0 (`V-FACTSV2-GREEN-CLEAN-V2`). Without it, a gate that refuses every
document would satisfy every assertion above.

---

## PR-SCOPE-REQUIRED-TO-THE-GATING-SET-001 (PROCESS)

Two extremes are both wrong and both tempting:

- **require the whole vocabulary** → a ten-name dictionary becomes a universal
  prerequisite list, every mission blocks over facts that cannot change a
  verdict, and the gate gets switched off;
- **require nothing** → the trap above.

The line is the distinction the estate already computes: a GATING read decides
whether an obligation exists; an ENRICHING read only extends one that exists
either way; an ORPHAN read is consumed by nobody. Require the first, never the
other two.

**And a DEAD operator requires nothing further.** `_has()` is `all(...)`, so an
operator with any gating fact measured FALSE can never fire. Demanding its
siblings is production nobody can act on.

---

## T-UNKNOWN-AND-UNPRODUCED-ARE-DIFFERENT-REPAIRS-001 (TRAP)

Collapsing them is the same category error one level in. `unknown` means a
producer ran and could not measure — someone repairs a measurement. `UNPRODUCED`
means nobody asked — someone writes a producer. They never share a field, and a
receipt that reports one as the other sends the wrong person to work.

---

## T-BLOCKING-WITHOUT-A-READABLE-REASON-001 (TRAP)

**Symptom (caught in audit, before shipping).** Adding UNPRODUCED to
`Blindness.blocks` alone would have produced: `cmd_check` exit 1 with an **empty**
`message` and empty `block_reasons`, while `cmd_closure` printed
`MISSION CLOSURE: ALLOWED` on the same root.

**Root cause.** The message is built by joining `receipt.blocking`, which
`project_closure` populates. Changing the predicate without changing the
projection gives a gate that refuses and cannot say why.

**Why it matters more than it looks.** A block the caller cannot learn from is a
blind-retry loop wearing the costume of a guard. The only move left is to vary
the call and try again — which the two-consecutive-failures law forbids and
which cannot be followed, because the cause was never stated.

**Rule.** When a predicate gains a term, every surface that RENDERS that
predicate gains it in the same commit: the projection, the receipt, the envelope
and the command whose job is to report what is owed.

---

## T-GATE-WIDENING-BURNS-THE-GREEN-POLES-001 (TRAP, third occurrence)

`cmd_check`'s exit code has now been widened three times. The first two attempts
each blocked every wave on the host (`closure` is DENIED for a phase with no
obligations; `receipt.blocking` also carries "explicit backlog is not empty").

The third attempt — "a root nobody derived exits 2" — was caught by an
adversarial audit, **not by the suite**, because the suite's own helper runs
`check` without a preceding `derive` in nearly every case. It would have moved 8
pinned gates off their exit codes, including the two poles the source file names
as survivors of the previous two widenings.

**Rule.** Never widen a gate predicate without first driving every GREEN pole.
And when a fixture exercises one variable, make the baseline complete: after this
change, a fixture mentioning one fact blocked for *two* reasons, so several cases
would have passed on a compound verdict.

---

## T-BLIND-SWEEP-REPORTS-A-UNIFORM-DEFECT-001 (TRAP)

**Symptom.** A sweep of 12 mutation harnesses reported "proves its mutation
applied: NO" for **all 12**, including the two known-good ones.

**Root cause.** The predicate looked for `applied|occurrences|count == 0`. The
real proof is spelled `text.count(old_a) != 1`. The detector could not see it.

**The tell, and it is general.** A uniform answer across a whole swept population
is the signature of a blind detector, not a uniform defect. A population floor
does not catch this — the floor validates the population, not the predicate.
**Only a positive control does**: a subject verified by reading, which must light
every column or the run is HARNESS rather than a clean bill.

Calibrated, the true figure was 2 of 11 — exactly the two a previous wave had
fixed, which is also the shape of "a class was repaired one instance at a time
and never swept".

---

## T-A-KILLED-DRILL-LEAVES-A-MUTANT-IN-THE-TREE-001 (TRAP)

**Symptom, measured the same session the gate above shipped.** The 13-mutant
drill was killed mid-run by the harness for host memory pressure. Afterwards,
`modules/gsd_x/mission/structured_facts.py:223` held `if False:` where
`if state == UNKNOWN:` belongs — the `held-unknown-allowed` mutant, live in the
working tree, in a file nobody had edited.

**Root cause.** The drill restores inside `try/finally`, which is correct against
exceptions and useless against a kill: `finally` does not run when the process is
terminated. Worse, the drill's own **sha256 restore verification is on the
success path** — the one code path a killed run never reaches. So the strongest
restore guarantee in the harness is precisely the one that cannot fire when it is
most needed.

**Why it is dangerous rather than merely untidy.** The residue is a *weakened
guard*: a held entry carrying state UNKNOWN would have been readmitted as a fact
that holds. Every suite would still pass, because the suites assert the guard's
message and this mutant removes the branch that raises it — and the next commit
would have carried it.

**What caught it.** Not the drill, which was dead, and not any suite. A residue
scan run deliberately on the four mutation targets because the kill notice said
the command was stopped rather than failed. `git diff` showed one changed line in
a file I had never touched, which is the tell.

**Rules.**
1. **A restore in `finally` is not durable.** Where a drill mutates tracked
   files, durability needs an EXTERNAL record: write a sentinel naming the file
   and the mutant *before* mutating, and have the next run refuse to start while
   a sentinel exists, restoring first.
2. **After any interrupted drill, scan for residue before doing anything else** —
   and scan by comparing against the authority (`git hash-object` vs
   `rev-parse HEAD:<path>`), not by eye.
3. **Write the residue scan so it can be wrong in the safe direction.** My first
   scan row for `closure.py` matched the real method signature as well as the
   mutant and raised a false alarm; that is the correct direction for a scan of
   this kind, but the row should still name the mutant BODY, never a line both
   versions share.

## PR-INVENTORY-FROM-THE-INSTRUMENT-THAT-CHECKS-IT-001 (PROCESS)

The first frozen inventory for the new gate was seeded from the earlier, looser
sweep. It was wrong three ways at once: four real drills omitted, and one file
named that mutates only a scratch copy. All three ratchet clauses caught it on
the first run.

**An inventory derived from a different instrument than the one that checks it is
not an inventory; it is a second opinion that nothing reconciles.** Generate the
frozen list with the gate itself.

---

## T-FAMILY-WITH-NO-ROUTE-IS-SILENTLY-OUT-001 (TRAP)

**Symptom.** `modules/tower/families.py:repo_family_report` dropped a family with
empty `repo_markers` and no `delegate` into **neither** `report["in"]` nor
`report["unjudged"]`. `repo_families()` returns only `in`, so such a family was
silently OUT of every repo on the host.

**Why it is worse than it looks.** A constitutive baseline promoted under that
family would have reached nothing, with no UNJUDGED signal to say so — presence
without reachability, inside the mechanism whose entire job is to make a promoted
rule reach future work.

**Fix.** A family that declares no membership route has not been judged OUT; it
has not been judged. Proven with both poles: the route-less family returns
UNJUDGED, and a family *with* a route and no marker hit is still honestly OUT.

---

## PR-DOC-CLAIM-ABOUT-CALLERS-IS-A-CLAIM-001 (PROCESS)

`structured_facts.load()` documents that "a gate asserts this function has no
production caller." Measured: **no such gate exists** anywhere in the repo, and
the claim is false — `tools/gsd_x_mission.py:64` calls it on the production
derive path. The same sentence had been copied into a resumption file, giving it
a third life.

A docstring that asserts an enforcement is a claim like any other. If it matters,
it is a check with a name and a failing branch.

---

## Applicability

| rule | earned scope | why not broader |
|---|---|---|
| required-input closure; UNPRODUCED ≠ absent requirement | GSD X evidence-backed decision features | one measured instance |
| scope the requirement to the gating set | same | same |
| a predicate's new term reaches every renderer in the same commit | GSD / agentic engineering | two instances (this, and the twice-burned exit code) |
| a mutation test must prove it mutated | ALL CPP | two independent instances (F6 anchors, and the blind sweep) |
| a uniform sweep answer is a blind detector | ALL CPP | transferable by construction; costs one positive control |
| an inventory comes from the instrument that checks it | ALL CPP | same |

Broader promotion than these requires transfer evidence, and is not claimed here.
