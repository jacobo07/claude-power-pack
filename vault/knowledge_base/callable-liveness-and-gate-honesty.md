# Callable liveness and gate honesty — UKDL distillation, 2026-09-13

Origin: a CDIO hardening pass that set out to improve a design-review subsystem and
instead found that most of it had never run. Every rule below is drawn from a defect
measured in this repository on this date, with the instrument named.

> **Router pointer OWED.** The canonical corpus is
> `vault/knowledge_base/ukdl-universal.md`, and it carried another session's uncommitted
> work while this was written. Extending it would have packaged their changes under this
> commit, so this landed as a new file instead — a new file cannot be swallowed. The
> one-line pointer into the corpus is the outstanding half, and it is named in the
> handoff rather than left to be noticed.

---

## HARD RULES

### HR-GATE-NAMES-ITS-CALLER-001
**TRIGGER** — writing, or reviewing, a normative sentence in governance that says a
specific function, gate or check RUNS.

**ACCIÓN** — STOP. Name the caller, or mark the rule agent-invoked. A governance sentence
asserting that `f()` runs, when nothing calls `f`, is not a weak rule — it is
indistinguishable from a fiction, and it actively suppresses the investigation that would
find the gap, because everyone who reads it believes the check exists.

**ORIGEN** — `DESIGN_GOVERNANCE.md` §8.2 stated that dependency resolution "is checked
again at review time … `review_gate(verdicts, target=<proj>)` runs it as a hard filter
BEFORE the score". `review_gate` had zero production callers. The automatic entrypoint
called `score_review` directly. Two consecutive sessions read that sentence and did not
check it.

### HR-UNEVALUABLE-IS-NOT-DONE-001
**TRIGGER** — a gate, check or verifier returning a result after failing to evaluate its
subject (unreadable input, crash, timeout, missing dependency, skipped run).

**ACCIÓN** — STOP. The ACTION may fail open; the ASSESSMENT may not. Return the two as
separate fields. A `SKIP` that carries `is_done: True` makes "we could not look" identical
to "we looked and it passed", and the consumer has no way to tell them apart.

**ORIGEN** — `design_gate.py` returned `{"verdict": "SKIP", "is_done": True}` on an
unreadable artifact and on any internal exception. This is a **recurrence** of a rule
already sealed at `ukdl-universal.md:7035`, which is the more alarming half: the rule
existed, in this repo, and the code did it anyway.

---

## PROCESS RULES

### PR-CALLABLE-LIVENESS-001
Reachability has at least three granularities, and each hides the one below it: does
anything reach this **module** · is this registered **handler** ever invoked · is this
exported **function** ever called. Auditing at module granularity and reporting health is
the package→module mistake one level finer. Run
`python -m modules.liveness.callable_reach` before claiming a subsystem is wired.

*Evidence*: `modules/cdio/scorer.py` was correctly REACHABLE. 6 of its 26 public symbols
were on the automatic path. Estate-wide the first honest sweep found 1641 public symbols
under `modules/`, 272 called.

### PR-COVERAGE-DOWNSTREAM-OF-PRODUCTION-001
A test that calls the capability directly proves the capability works. It proves nothing
about whether production reaches it, and it stays green when the wiring is deleted. For
any capability that is supposed to run automatically, own at least one gate that enters
through the **production entrypoint** and would fail if the wiring were removed.

*Evidence*: four CDIO suites were 44/44 green across the entire period in which the
hard-filter layer had no production caller. `V-DESIGN-HARD-FILTERS-REACHED` is the gate
that can fail; reverting `target=` to `None` turns it red.

### PR-MEASURE-BLAST-RADIUS-BEFORE-STRICTENING-001
Before shipping a repair that makes an existing **deny** path stricter, re-score the real
population under both the old and the new predicate and report how many subjects flip. A
correctness fix and a new refusal are the same commit, and only one of them is safe by
construction.

*Evidence*: the font-parser repair was measured against every `DESIGN.md` reachable from
`~/.claude`, `Cursor Projects` and `Repos-GitHub`: 2 documents, 0 flips. It shipped strict
because the measurement said it could — not because the fix was obviously right.

---

## TRAPS

### T-GREEN-SUITE-AS-WIRING-EVIDENCE-001
**The seduction**: 44/44 passing, therefore the subsystem works.
**Why it fails**: a suite that imports the capability directly has an observation domain
that excludes the production path entirely. Deleting the wiring cannot turn it red.
**The tell**: every test file imports the module under test. No test starts at the
entrypoint the product actually calls.

### T-ALIAS-RECEIVER-BY-NAME-LIST-001
**The seduction**: match the receiver against the names people usually use.
**Why it fails**: a receiver is whatever the importing module bound it to. A hardcoded
list misses `import x as y`, a factory return, and a local rebinding — and it fails
*silently*, reporting live code as dead.
**Third occurrence in this estate** (2026-09-10, 2026-09-11, 2026-09-13). The first two
were written down as prose and the lesson did not transfer, because prose does not travel
to the moment you type a matcher. What transferred was
`modules/liveness/callable_reach.py::bindings` plus a synthetic drill — which caught the
bug a third time, *in the commit that was fixing it*, before it shipped. Fixing it moved
real-repo CALLED from 261 to 272.
**Corollary**: record the **exported** name, never the local one. `from m import f as g`
that records `g` reports `f` uncalled *and* invents a caller for a symbol `m` does not
have — two wrong answers from one slip, and the accusing one is silent.

### T-FLOOR-CONDITIONED-ON-A-DECLARATION-001
**The seduction**: a contract-conformance check naturally reads the contract first.
**Why it fails**: an accessibility floor is a property of the surface, not of the
document. Returning `unassessed` when no contract is declared means the projects that
declared nothing — which is most of them — get no floor at all, and the filter reports
CONFORMING, which a reviewer reads as "behaviour checked".
**The tell**: an early return for "nothing declared" sitting **above** the floor check.
The comment above it may even claim the floor is unconditional; it was conditioned on the
contract *existing*.
**Measured**: only 2 `DESIGN.md` documents exist across this entire estate, so the
undeclared path was not an edge case — it was every case.

### T-REJECTION-SUITE-NEVER-REMOVES-THE-CONTAINER-001
**The seduction**: a thorough suite of malformed-input cases proves the validator is
strict.
**Why it fails**: cases that supply a *wrong* value never exercise an *absent* one, and
cases that remove a *field* never exercise a missing *container*.
**The tell**: `V-EXP-FLOOR-NOT-DECLARABLE-AWAY` removed the `reduced_motion` field and
proved no declaration buys the exemption — while both of its fixtures still declared a
contract, so neither could reach `declared=None`. For every rejection suite, ask what it
removes, and then remove the thing one level up.

---

## Instrument limitations, stated so the numbers are not over-read

`callable_reach` resolves **Python import edges only**. A module a JS hook spawns via
`spawnSync(python, [...])`, a shell entrypoint, and anything reached through dynamic
dispatch all read as unreached. Its count is an **upper bound** on dead callables, and a
row is a question to ask, not a verdict to act on. `dispatch.py` and this file are
complements: the shape that defeats static reading is precisely why the other exists.

The earlier hand sweep in this session classified `check_color_discipline` as PROSE_ONLY
because its name appears in *some* markdown file. The external reviewer showed it is
absent from the reviewer agent's own instruction list — genuinely no caller. "Named in a
document" and "instructed as a runnable command" are different states, and conflating them
launders a corpse into a documented capability. `_named_in_prose` is deliberately narrow
for this reason.
