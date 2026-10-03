---
name: instrument-before-claim
description: Measurement-integrity doctrine. Use BEFORE reporting any measured number, count, timing, size or percentage; before asserting an absence ("not found", "no callers", "zero", "nothing uses it", "unused", "never ran"); before trusting or declaring green a test, gate, sweep, detector, comparator, probe or verdict; and when WRITING one (fixtures, thresholds, tolerances, mutation drills, population floors, A/A baselines). Also when two instruments disagree, when a result looks too clean, or when a verdict contradicts the evidence it quotes. Core question - could this instrument have returned the other answer?
metadata:
  opportunity_detector: none
  opportunity_detector_reason: coverage class none; no registered card hook and no CO-12 adapter names this skill
---

# Instrument Before Claim

Five measurement failures across two sessions (2026-08-27, 2026-09-01), each of
which produced a confident, well-formatted, **wrong** number. None was a reasoning
error. Every one was a wrong instrument, and in each case the prose built on top
of it was fluent and plausible.

## Pattern

Before reporting a measured claim, name the instrument and ask:

> **Could this instrument return the other answer?**

An instrument that can only ever return one answer carries no information when it
returns it. A code-scoped grep cannot see a doctrine-scoped owner, so its "absent"
means nothing. A diff against HEAD cannot see a commit, so its "no work" means
nothing.

## DO

- **State the instrument beside the number.** "36 NPCs (regex over the raw export)"
  is checkable; "36 NPCs" is a claim.
- **Before asserting an absence, prove the instrument could have found the thing.**
  Search the expansion as well as the acronym; search doctrine as well as code.
- **Corroborate any load-bearing number with a second, differently-built
  instrument.** When they disagree, report both and promote neither.
- **Check the window and scope of any diff, report or gate before trusting its
  subject.** Ask what it is blind to by construction, not just what it says.
- **Pivot the instrument after two failures of the same shape** rather than
  retrying it a third time.

## DON'T

- **Don't infer activity from a producer's output directory.** A folder of
  receipts measures production, not whether the gate that consumes them ever ran.
- **Don't infer "ran" from a commit date.** That measures writing.
- **Don't read a summary field for data that lives in the body** (`git log %s`
  will never show a trailer).
- **Don't treat N copies of one source as N data points.** Five exports of one
  shared database is a sample of one. Four machine-generated deltas with an
  identical takeaway is one observation, not four.
- **Don't call a green earned until something drove the red branch.** A gate whose
  failure path nobody exercised could have every clause commented out and return
  the same green.
- **Don't trust a test double to be as permissive as the runtime it stands for.**
  A mock missing one method, called inside a `try/catch` that fails open, turns a
  loud `TypeError` into a plausible value — and every test using that harness then
  takes the catch branch forever, silently, while staying green.
- **Don't verify on a substitute that is more PERMISSIVE than the real target.**
  This is the previous entry's twin, and it bites harder because the substitute is
  not a mock — it is a real system that simply says yes more often. An emulator's
  stock IME honours `showSoftInput(SHOW_IMPLICIT)`; the flag is documented as a
  hint, and OEM keyboards drop it. A test on the permissive side can only ever
  return "works". Ask which side of the leniency gap the check is standing on.
- **Don't let a tolerance exceed the distance between the right and the wrong
  answer.** A colour gate compared the canvas against the chrome constant with a
  ±8 window when the two candidate values are 6 apart: it returned OK for the
  correct value and would have returned OK for the wrong one. A threshold is part
  of the instrument — size it against the error you are trying to catch, not
  against noise in general.
- **Don't apply one threshold to several KINDS of subject.** The sibling of the
  entry above, and it fails in the opposite direction: the number is right and the
  *question* is wrong, so the instrument returns confident failures about things it
  was never entitled to judge. Measured 2026-09-21: a colour gate held every token
  to WCAG's 4.5:1 body-text floor and reported 14 failures, of which 10 were a
  focus ring and an accent surface — a ring answers to 1.4.11's 3:1, and a fill is
  judged against the foreground painted *on* it, not against the page behind it.
  Fixing the roles cleared all 10 and left 5 genuine pre-existing misses that had
  been invisible underneath the noise. The tell is a failure list where the
  offenders have nothing in common except being measured; before believing it, ask
  what kind each subject is and whether one number can be right for all of them.
- **Don't build a synthetic fixture out of real values.** The rule above says a
  fixture must not inherit the assumption it tests; this is the sharper case — a
  fixture that copies production values inherits production's *debt*, and then the
  GREEN control fails for a reason that has nothing to do with the clause under
  test. Measured the same day: a synthetic stylesheet copied `--muted-foreground:
  #737373` and `--muted: #f5f5f5` from the real one, which are 4.35:1 and genuine
  frozen debt, so the happy path went red and looked like a broken gate. A
  synthetic subject has to be clean by construction, and the values that differ
  from production are worth a comment saying why.
- **Don't let a fixture inherit the assumption it is meant to test.** A synthetic
  case set can only express states you already believe exist, so it confirms the
  belief rather than checking it. A process-reaping rule self-tested 4/4 against
  four states of "a main process" — and the real process table showed the app's
  renderer, GPU and utility children all carry the same exe name and all match the
  dead-main signature exactly. Enumerate the real population once before deriving
  a signature from it, and verify against a live instance, not only fixtures.
- **Don't let a hand-picked sample of REAL subjects stand in for the population.** The
  entry above is about a synthetic fixture; this is its harder sibling, because nothing
  here is synthetic and every subject is genuine — which is exactly why the answer feels
  earned. A sample chosen by the person holding the hypothesis is selected, however
  honestly, for the reasons those subjects came to mind. Measured 2026-09-21: asked
  whether any function in a 7 MB binary is dispatched by BOTH a direct branch and a
  vtable slot, I checked the eight I had been working with — the Draw, BUILD, SHOW, CALC,
  the registrar, the accessor — and **all eight were single-mechanism**. I was one
  sentence from recording "the gap has no instance in this binary" and closing a live
  defect as theoretical. The whole-image sweep cost one script and two minutes,
  intersected 45,750 branch targets with 14,456 data-held addresses, and found **1,718**.
  The tell is that the sample shared a provenance: mine were all functions this
  investigation had already surfaced, which is a selection criterion wearing the costume
  of a coincidence. When the question is "does this class have members", enumerate the
  class — a sample can only ever raise the floor.
- **Don't spend a rare observation window on only the question you came with.** Where
  observation is budgeted — a paid run, a production window, a device you get once — the
  marginal cost of reading an adjacent field is near zero and its marginal value is a
  whole cycle. Measured the same day: a run censused a list and read each node's sort
  key, proving the membership claim it was designed for. The next question was already
  visible in the disassembly — what the draw-root pointer and two sibling flags hold on
  our object versus a working one — and those live at fixed offsets on objects the census
  already had in hand. Reading them would have cost three more printed words. They were
  not read, so answering them needs another whole run. **Before an expensive observation,
  write down the question you expect to have AFTERWARDS and carry its fields too.** The
  cheapest instrument for the next wave is the one already pointed at the subject.
- **Don't verify a shipped feature anywhere upstream of the copy that runs.** Source,
  commit and build output can all be correct while the installed tree is not.
  An NSIS install replaced Orca's exe but could not overwrite `app.asar` — a
  stale process memory-maps it — and reported success, leaving a new binary on a
  nine-day-old bundle. The version string reads the exe, so it says the new
  number while running the old code. Only a file-by-file comparison of installed
  against built could tell the two worlds apart. Measure the artifact the user
  actually launches.
- **Don't read "fast on a no-op payload" as fast.** A probe drives the subject with an input, and
  an input that cannot reach the expensive path measures startup. Measured 2026-09-15: a Stop-chain
  budget gate fed every member `transcript_path: ''`, so a hook whose cost is proportional to the
  session transcript exited early at 334 ms — while the dispatcher's own comment recorded **712
  timeouts at 8000 ms** for that same script. The gate then demanded the deletion of its exemption
  as "no longer over budget", which would have removed a live protection on the strength of a
  question never asked. Before trusting any timing, ask what the payload makes the subject *do*;
  where the probe cannot reach the real path, report UNMEASURED and keep the protection, because
  absence of the measurement is not a measurement of absence.
- **Don't conclude a property is uncovered because the file you are editing does not cover it.**
  Coverage lives in the estate, not in the file under your cursor. Measured 2026-09-16: a freshness
  case primed through a function that memoizes nothing, so it could not observe the reuse it was
  named for — a correct finding about that file. The property was already covered in a sibling,
  and covered *better*: it primed through the reader that does populate the memo and asserted
  exactly one further query against my "more than zero". The same mutation reds it on
  `expected +0 to be 1`. Before adding a gate, grep the estate for the *property* — the mutation
  you would use to break it — not for the module you are looking at.
  And the cost is not merely a redundant test: **a looser duplicate can satisfy the stricter
  gate's subject and disarm the drill that proves the stricter copy still works**, silently, while
  every suite stays green. This repository had that lesson written down, in prose, from a previous
  incident. It did not travel, for the same reason the others in this file do not: prose does not
  reach the moment you type an assertion. Retracting the duplicate is cheaper than keeping it.
- **Don't write an absolute "never happened" assertion about a window you did not bracket.** A
  control asserting a publish function was never called failed because the subject's own
  initialization publishes once, before the code under test runs. That is a precondition failing,
  not the claim — and it reads as a genuine defect. Capture the count before the action and assert
  the delta, so the assertion is about the window the claim is about.
- **Don't let a sweep's own contention become its finding.** The same run flagged a member at 6338 ms
  against a 6000 ms budget as a NEW standing defect. Timed alone, warm, three times: 377 / 311 /
  292 ms against a 203 ms interpreter floor — a 17× drift. The host headroom check had *passed*,
  because it was read BEFORE a sweep that then spawned 25 processes back to back: a pre-flight
  reading cannot see contention the flight creates. Take a median, not a reading, and bracket the
  headroom check on both sides of the sweep rather than only in front of it.
- **Don't read a monotonic curve on a drifting host as a curve.** When the quantity you are sweeping
  and the host's own condition move in the same direction, they are confounded and the curve proves
  nothing, however clean it looks. Run the sweep **in both directions**: if the effect is real, the
  reversed sweep tracks the variable while the host keeps drifting the other way. Measured
  2026-09-18, memory per remembered session: free host memory fell monotonically 5,049 → 4,382 MB
  across the run, so the forward sweep's rise with row count was unusable on its own; reversed, rows
  fell, the host kept draining, and the subject's bytes fell **with the rows**. Drift would have held
  them flat or pushed them up. Report the two sweeps' disagreement as the uncertainty (here ±13 MB on
  a ~48 MB effect) rather than averaging it away, and treat any point smaller than that disagreement
  as below detection — the one-unit point read −0.9 MB one way and +15.6 MB the other.
- **Don't act on a detector's "this record is stale" without opening the file.** When a codebase
  introduces a wrapper around the primitive a text-scanning detector greps for, the detector goes
  blind and then *accuses its own inventory*: it reports the entries it can no longer see as stale
  and tells you to delete them. Deleting them leaves a perfectly clean report describing nothing.
  Measured 2026-09-18: a recurring-work sweep matching `new Worker(`, `utilityProcess.fork(` and a
  bare `fork(` lost six child-process producers — the terminal daemon among them — when the estate
  moved to a `forkIpcChild()` wrapper, and the blind spot grew from two entries to four within one
  session as more call sites migrated, which reads exactly like ordinary refactor churn. The only
  clause that could tell instrument failure from an honest refactor was the **population floor**
  (`found 7 worker sites, expected at least 8; the sweep may have stopped seeing code`) — a stale
  list alone cannot. So: put a floor under every structural sweep, and treat a stale report as a
  question about the sweep before it is a question about the record. Beware also that adding the
  wrapper to the pattern matches its own `export function wrapper(` declaration; scope the pattern
  out of the defining module rather than letting the definition count as a call site.
- **Don't assert on a field a lower layer rewrites.** Before claiming a thing is absent, ask who
  writes that field last. If the layer under the subject normalizes it — a hydration step, a
  serializer, a schema default, an ORM hook — the assertion is about *that* layer and can only ever
  return the safe answer, whatever the subject did. Measured 2026-09-17: a test proving a restored
  row starts no runtime asserted `ptyId === null`, and a mutation installing a pty on every row
  passed, because hydration resets the field regardless of the payload. The repair is not a stricter
  assertion on the same field; it is to ask the predicate the product actually consults
  (`decideTerminalTabMount`), and to pass it the *weakest* surrounding condition so only the property
  under test can hold the answer. Both versions read identically green, so only the driven mutation
  tells them apart.
- **Don't enumerate writers by which ones can report failure.** A sweep that
  collects "everything here that returns a status" has its population defined by
  the property it is checking, so a writer with no status channel is not merely
  unchecked — it is invisible, and its absence reads as evidence that it is not a
  writer at all. Measured 2026-09-22 (CavEX II): a repair comment named the defect
  correctly — "world enumeration lists a directory only if its level.dat parses,
  so a failed write makes the world invisible" — and then fixed *"all three of
  these [that] return bool"*. All three were in-memory edits. The one function
  that actually wrote the card returned `void`, was therefore not in the
  enumeration, and was also the one truncating the file before serializing. It
  destroyed three of the Owner's worlds. Enumerate writers by **what they do** (a
  truncating open, an unlink, a dirty-bit clear), never by what they return, and
  treat a `void` return on anything touching durable state as a finding in
  itself — it is the one shape that cannot appear in a status audit.
- **Don't diagnose the app before measuring the host.** Three ANRs in one session
  read as an application bug; the measurement was 904 MB free of 32 GB, and the
  blocked stack was entirely inside the platform renderer with no application
  frame in it. Resource exhaustion imitates every failure mode you already suspect.
- **Don't let the instrument consume the resource it is measuring.** A gate written to
  prove a feature worked on a live server dispatched two full map generations fifteen
  seconds apart at a container capped at 2048 MB, idling at 1510 MB, with no swap. The
  container OOM-killed the JVM mid-run and the log rotated. The gate measured "new log
  bytes since a byte offset", so the rotated file returned an empty slice — and it
  reported four confident failures, the first being *"the command never reached the
  plugin."* The rotated log showed the command arriving and generation starting
  normally. **A load generator is part of the system under test.** Measure headroom
  before dispatching, wait between runs, and give the gate a third verdict: a run whose
  host died is INCONCLUSIVE, never a failure of the subject. Uptime that went backwards
  and a log that got shorter are the two cheap detectors, and both are one API call.
- **Don't assert an output format you never saw.** The same gate parsed the seal receipt
  for `blocksPlaced=`, the field name of the record that produces it. The line the server
  actually prints is `landmarks=1 evicted=0 placed=3360`. So it reported *"the seal ran
  and placed nothing"* on a line whose own evidence string, printed immediately beside
  the verdict, read `placed=3360`. **When a verdict contradicts the evidence it quotes,
  the parser is wrong, not the world** — and that contradiction is free to check, because
  a gate that prints what it matched against makes its own bugs visible.

## A predicate whose two branches are not both reachable

The tolerance entries above are about a threshold sized wrongly. There is a sharper version where
no threshold is involved at all: **the predicate's two answers are decided by an ordering the
system itself fixes, so one branch cannot occur for a correct implementation.** The probe then
executes perfectly, observes correct values, and emits a verdict that is semantically impossible —
which is worse than failing, because nothing looks wrong.

Measured 2026-09-21 (KobiiSports Resort, Set B run A). A co-residency test asked whether a
newly-allocated object lay inside the min–max span of twelve sibling objects. The allocation
happens *before* those siblings exist, so a correct same-arena allocation is necessarily **below
their minimum**: `OUTSIDE` was the only reachable answer. Both branches were named in the source
comment. Only one could ever be taken.

> **Before trusting a decision-critical binary predicate, name a valid state that produces each
> answer. If one of them has no such state, the predicate is measuring the ordering, not the
> property.**

Three things make the repair durable, and the second is the one usually skipped:

- **Ask the property where the substrate states it.** "Same allocation domain" is answerable from
  the heap's own `[start, end)` and does not depend on allocation order at all. The span of
  sibling objects was a proxy that happened to be easy to compute — which is the same failure as
  choosing an identity because it is the one already in hand.
- **Make every run exercise both poles, on real inputs nobody chose for the purpose.** The fixed
  version prints `obj=IN desc=OUT` on every sample: the descriptor is a static pointer belonging
  to no heap, so the OUT branch is *demonstrated live, every frame*, beside the IN branch it must
  discriminate from. A predicate that had silently started answering IN for everything would be
  visible in the same line that carries the verdict. This is cheaper than a mutation drill and it
  never decays.
- **Keep UNMEASURED as a third answer with its own validity bit.** A span that could not be read
  says nothing about where anything lives, and folding it into the negative answer manufactures a
  finding.

The sibling rule, from the same estate and the same day: **a claim about an OBJECT may not be
promoted from a read of ONE FUNCTION in its lifecycle.** Two claims had been recorded as VERIFIED
off a static read taken at the depth that was convenient — "the constructor does not retain the
descriptor" (it is retained two frames down, by code the read never reached) and "heap risk is
zero" (the constructor allocates almost nothing; the object's *build step*, not yet identified when
the claim was written, allocates 2.9 MB). Neither was a wrong measurement. Both were a correct
measurement of the wrong frame, generalised silently from a function to the thing it operates on.

## A zero has three independent causes, and fixing one does not fix the others

A sweep's controls prove the tool works. They say nothing about whether the question was
answerable by it, and an unanswerable question returns **zero** — byte-identical to a clean
result. Measured three times in two sessions on one binary, each with the tool healthy:

| variant | asked | returned | cause |
|---|---|---|---|
| **scope** | whole-image writers of one struct offset | **767 hits**, nearly all stack frames | the offset is common and the question had no owner; scoping to the class took it to **1** |
| **aperture** | a byte flag's accesses | **0** | the scanner decoded only word-width forms; the byte instruction was invisible. A second tool found it instantly |
| **access pattern** | a sub-object's offset, at full aperture | **0** | correct and not an answer: the sub-object is passed **by address**, so its members are addressed relative to itself and never as `offset(parent)` |

They are independent. Repairing the aperture made that tool's zeros trustworthy about member
accesses of every width and did **nothing** for the third case, whose zero still looked like a
finding. So before believing any zero, state three things: the scope's owner, the tool's
**aperture** (which widths/forms it decodes), and the subject's **access pattern** (member offset,
or pointer to a sub-object).

Two cheap defences, both worth building once:

- **Print the aperture beside the count, never separately**, and emit a warning when a narrowed
  sweep finds nothing — a zero is uninterpretable until the reader knows what was in scope.
- **Scope by a proven receiver where a call site gives you one.** A load immediately preceding the
  call (`lwz r3, <field>(rX)` then `bl f`) proves `f`'s receiver by construction; that beats any
  filter over hundreds of same-offset hits, and it costs one disassembly.

### "Our code never calls X" is not "X never ran"

The same session lost a wave to a promotion that looks like nothing: a grep of *our* module found
no call to a library function, and that was recorded as the function never having executed. Our
module calls **someone else's** code, and that code called it. The grep was true; the conclusion
was not, and it produced a confident evidence document whose central claim was false.

Whenever an absence is established over a boundary you own, name what crosses it. Ask what the
code you call calls — especially when "our code" is a thin reconstruction driving a large
third-party or retail runtime, because then almost everything that happens is someone else's.

## When the instrument itself is what failed

Everything above assumes the instrument ran and returned an answer. There is a third
case, and it is the easiest to misread because it looks like a verdict:

> **A verifier that rejected its subject and a verifier that could not judge its
> subject are different evidence. Both are non-zero, and that is exactly what makes
> them easy to conflate.**

Fail-closed is not sufficient. A gate that dies on a malformed input still exits
non-zero, still blocks, and still reads as "your thing is wrong" — sending you to fix a
subject that may be fine. Worse, a crash partway through a loop means everything after
it was never judged, while the run still presents as a complete verdict.

So give a verifier at least four outcomes — **valid**, **subject invalid**, **verifier
failed**, **unreadable input** — with the verifier's own failure *outranking* subject
failures found in the same run, because that run proves nothing about what it skipped.
Isolate per item so one unanticipated shape cannot take down the whole verdict.

The same shape one layer out, in tests: **a fixture that could not establish the
precondition has not observed the behaviour under test.** A setup failure and a product
failure must be distinguishable in the result, or one flaky fixture silently
contaminates every verdict in the run — and a real regression hides behind the same red.
Retrying until green characterises a flake; it never substitutes for classifying one.
When classifying, refuse to guess: return "product failure" only on positive evidence
that the failure came from the test's own body, and leave anything unattributed as
**unknown**. Resolving an unknown toward the convenient answer is the misattribution the
model exists to prevent.

Two traps that come with this territory:

- **A rejection suite that never removes a field has a hole shaped like a hand-edited
  config.** Twenty-odd cases each supplying a well-formed but *wrong* value could not
  catch an *absent* one.
- **The guard you add for unanticipated inputs cannot be tested with anticipated ones.**
  Driving that branch needs an input the normal format cannot express — a throwing
  getter where the real source is JSON, say. Without it, a verifier that had quietly
  stopped catching reports the same clean green as one that still does.

## The stimulus half

Everything above asks whether the instrument could have seen the answer. There is a
second half that is easier to skip, because the reading looks reasonable either way:

> **Before concluding a system ignored an input, prove the input reached it.**

A press that never landed and a component that ignored the press produce identical
geometry. A request that was never sent and an endpoint that dropped it produce
identical logs. So a measurement of a response is worth nothing until something
independently confirms the stimulus occurred — ideally the system's *own* signal
that it accepted the input (the drag state it enters, the span it opens, the row it
writes), not a synthetic restatement of the input you sent.

Corollary with teeth: **a hit target is not a layout box.** An element's reported
box does not shrink when an ancestor clips it, so a control can report full width
while owning none of those pixels — `elementFromPoint` names the element that would
actually receive the press, and that one call is the difference between fixing the
control and rewriting everything downstream of it.

And the sharper version, where the instrument is not merely blind but actively
self-defeating: **a stimulus that can destroy the precondition it depends on will
report a working mechanism as broken.**

Measured 2026-09-11, proving Windows delivers taskbar-thumbnail demand to an Electron
window. The demand fires only while the window is minimized, and the stimulus used to
provoke it — ALT+TAB, to make the shell display the iconic representation — selects a
window and *restores* it on release. When the switcher happened to land on the subject,
the run observed nothing at all, which is precisely what a platform that never delivers
would produce.

What separated the two readings was not a retry. The probe recorded the precondition at
the **end** of the observation window as well as the start, so `WINDOW_MINIMIZED_AT_END=false`
named the contamination in one line and the run was classified inconclusive rather than
negative. The repair was to change the stimulus — cancel the switcher with ESC instead of
releasing onto a selection — not to run it again and accept whichever answer came back.

So whenever the stimulus and the precondition touch the same state, **assert the
precondition after the observation, not only before it.** A run that silently lost its
precondition mid-flight is indistinguishable from a subject that did nothing, and the
convenient reading of that ambiguity is always the negative one.

## The instrument's window in time

Scope has a temporal axis, and it fails in both directions.

- **Sampling before the thing settles** describes a state the verdict is not about.
  A computed style read at the top of a function and reported after a wait is a
  reading from the wrong moment, and it reads as authoritative because the numbers
  are real.
- **Waiting past the condition under test** silently changes the question. A check
  that waits for a focus-revealed control to appear, but keeps waiting after focus
  has moved away, stops measuring "focus lands somewhere visible" and starts
  measuring "focus survived a second and a half" — and the revert it then observes
  is correct behaviour being reported as a defect.
- **A time-boxed wait makes the verdict a function of machine load.** The same code
  reported two offenders, then one, then none, on three consecutive runs. A result
  that drifts is not a result. Size the wait generously against the thing you are
  willing to call *slow*, and bound it by the *condition* rather than only by the
  clock — a genuinely absent thing stays absent for any window you choose, so a
  generous window costs no strictness.

And when a check can legitimately skip cases — a stop where focus moved on, a row
that could not be evaluated — **count what it actually judged and assert a floor.**
Otherwise a run that concluded nothing reports exactly what a clean run reports.

## When two instruments disagree, the disagreement indicts both

The rule above says to corroborate a load-bearing number with a second,
differently-built instrument. What it does not say is what the disagreement is
*for*, and the assumption that slips in is that one instrument is the good one
and the other is the check.

Measured 2026-09-10, sweeping a task registry for members nothing dispatches. An
AST pass and a text pass disagreed on two entries out of nineteen. Both were
wrong, in opposite directions, and neither error would have surfaced alone:

- The **text** pass matched dispatch calls written inside **docstrings** — prose
  describing how a caller *would* enqueue the task. It reported two producers
  that do not exist.
- The **AST** pass missed a dispatch made through an **import alias**, because it
  compared the receiver's local name against the task's function name. It
  accused a genuinely produced task of having none.

The AST pass "won" on the docstrings and the text pass "won" on the alias. Had I
picked a favourite instrument first, I would have shipped one of the two errors
and never seen it. **Read every disagreement before deciding which side is
right**, and expect the answer to be "a bug in each".

Two more from the same sweep, both worth naming:

- **A lazy registry answers zero, and zero is not a measurement.** The first
  sweep reported *0 registered tasks* while the same process could see 22
  scheduled entries. A framework that populates its registry on first use
  returns an empty one to anything that reads it early — and an empty registry
  is indistinguishable from a healthy estate with nothing in it. The
  contradiction between the two numbers is the only reason it was caught; a
  sweep that had reported "0 unreachable capabilities, all clear" would have
  been believed.
- **Err toward accusing, not excusing.** A producer-detector that misses a
  dispatch shape reports a working thing as broken, which a human then
  investigates and corrects. One that over-matches reports a dead thing as
  alive, which nobody ever looks at again. When a predicate must be imperfect,
  point its imperfection at the loud failure.

## Two corollaries that are easy to miss

A gate that *cannot practically fire* is indistinguishable, from the outside, from
a gate that passes. Aperture is part of the instrument: check what a check is
scoped to before reading its verdict as coverage.

**To find every consumer of a changed behaviour, search for the value you REMOVED,
not the module you changed.** A test that exercises a component through the DOM
asserts on rendered output and never names the import, so a grep of test files for
the module name cannot see it — and the change-scoped run built from that grep
reports a confident green while a consumer sits broken. Grepping instead for the
class, string, or attribute the change deletes finds every test pinning the old
appearance regardless of how it reaches the code. Same shape for a renamed field
or a changed enum value: search the old value, not the definition site.

The instrument is not always the command you typed — it can be the fixture the
code runs against. When a behaviour cannot be observed in tests, suspect the
double before the code: grep the mock for the methods the code under test actually
calls, not the ones the mock's shape suggests.

It can also be the RECORDING MEDIUM. When evidence is a capture of a screen, the
medium decides what exists in it: Android screenshots exclude system overlays,
screen recordings include them. A pale bar cloned from a video frame as if it were
the app turned out to be the vendor's own edge-panel handle — visible in every
recording frame, absent from all six screenshots of the same app. Before copying
anything out of a capture, ask what that capture format adds and removes.

## A fixture can leave the test suite

The rule above says a fixture must not inherit the assumption it is meant to
test. There is a worse version, and it does not look like a testing problem at
all: **the fixture stops being a stand-in and becomes the production input.**

Measured 2026-09-11. A function named for seeding a shadow loop, returning a
dict with constant economics and an id derived from its one argument, was
imported by the endpoint that publishes real storefronts. Its docstring
described the shadow loop and was accurate about its original purpose; nothing
in it mentioned the live path, because the live path arrived afterwards and
imported it rather than replacing it. Every guard downstream then judged a
constant, so none could refuse, and the identifier it minted -- a pure function
of the niche -- became the key that a real order's costs would later be
attributed through.

The tell is an import edge, not a test: a module under `api/`, `handlers/` or
any request path importing a symbol whose name or docstring says seed, sample,
demo, fixture, stub or example. Grep the import graph for those words in the
direction that matters -- who imports the fixture -- rather than reading the
fixture and trusting what it says it is for. And when you find one that cannot
be removed yet, say so *in the fixture*, because the docstring is what the next
reader will believe.

## An assertion taken before the work finished measures no moment at all

The wait between an action and its assertion is part of the instrument, and a wait
that is too SHORT fails differently from the temporal cases above: it does not
describe the wrong moment, it describes nothing.

Measured 2026-09-11. A test dispatched a destructive operation, flushed two
microtasks, and asserted the file still held newer bytes. It passed. The operation
had not run -- the path awaited a quiesce and then a subprocess, and the assertion
landed in between. What exposed it was the **negative control** in the same file: a
case asserting the operation DOES take effect, which failed, and could only fail for
a reason that also invalidated the case that passed.

The generalisation is about indistinguishable states. **An action that never happened
and an action that was correctly refused leave identical evidence.** So any "nothing
happened" assertion needs a precondition that something was attempted, and that
precondition has to be loud when it fails rather than silently satisfied. Block on
the subject's own promise or signal rather than on a duration, and raise when nothing
ever reached the boundary; otherwise inconclusive is reported as green.

The cheap detector is the one that caught it: pair every "it did not happen"
assertion with an "it does happen" case in the same harness, and distrust a green on
the first while the second is red.

Three more members of that family, measured later the same day while proving a
destructive refusal through a real Electron UI. Each produced a green for the wrong
reason, and none was found by reading the test — a control caught every one:

- **Reaching for the wrong control leaves the same evidence as the feature working.**
  The confirm helper clicked the dialog's last button, which was the content's close
  **X** rather than the footer's action. Cancelling leaves the file exactly where a
  successful refusal leaves it, so the stale case passed while nothing had been
  attempted. The paired success case going red is what exposed it, and the fix to the
  claim was to assert the refusal *notice* — which a cancel cannot produce. When the
  subject is "the destructive thing did not happen", assert the system's own
  acknowledgement, not only the surviving state.
- **An absence assertion keyed on a translated string is satisfied by the
  translation.** Asserting zero dialogs named `Delete "x"?` passes on a host running
  the app in another language, because the name never matched anything to begin with.
  This is worse than the sibling case where a *presence* assertion goes red and tells
  you: absence plus a locale-dependent selector is a permanent, silent pass. Use a
  role or a test id — a handle the translator never sees — and treat every
  "count is zero" as needing a selector you have separately proven can match
  something.
- **An ordering control must anchor on an event that occurs in both worlds.** A
  false-serialization check asserted the competing write preceded the destructive
  subprocess; the fix made that subprocess stop being invoked at all, so the anchor's
  index became −1 and the control failed against a correct implementation. An anchor
  has to exist whether the guard fires or not — re-point it at a step common to both
  outcomes and assert the now-absent step's absence separately.

## When a lesson is written down and repeats anyway, the write-up was the wrong artifact

The entry above about an AST pass missing a dispatch through an import alias was
recorded on 2026-09-10. On 2026-09-11 I wrote a new AST sweep, for a different
question in the same estate, and made the same class of error on its first run:
the receiver was matched against a hardcoded set of plausible variable names, so
it missed a pipeline reached through a factory function and would have missed
any local the module happened to name differently. A second, independent sweep
missed a different call site, so once again neither instrument was right alone.

The lesson had been written as prose in this file and it did not transfer,
because prose does not travel to the moment you type a matcher. What would have
transferred is a reusable resolver: **a receiver is whatever the module bound
it to.** Build the alias map from the module's own assignments, annotations,
attribute bindings and factory returns, and drive it with a synthetic drill
covering each shape, so the next sweep inherits the behaviour rather than the
advice.

When a recorded failure recurs, the question is not why you forgot. It is which
artifact would have made forgetting harmless -- a helper, a template, a
positive-control drill -- and whether writing it costs less than the third
occurrence.

## A gate that supplies a precondition cannot testify about it

The fixture rules above are about a fixture that is *too narrow* or *too
permissive*. There is a fourth-instance pattern that is neither: the fixture is
correct, necessary, and still destroys the claim, because **the thing it
establishes is the thing production was missing**.

Measured four times in one estate, each a layer further in:

| the gate established | so it could not see |
|---|---|
| a signed session cookie | that no login could mint that role |
| an encrypted credential row | that no user path could write one |
| a verification timestamp | that no production code stamped it |
| **its own process environment** | **that the deployed service was passed no such variable** |

Every one was legitimate. A browser gate that did not supply a vault key would
exercise a refusal path while appearing to exercise storage; one that did not
supply an execution ceiling would measure a posture check instead of the feature.
The gate is not wrong. The *claim* is — and the fourth case is the sharpest,
because an environment feels like context rather than like a fixture, so nobody
counts it as something the test created.

**The detector is one question, asked of every precondition a green run stands
on: what legitimate production action creates this state, and is that action
inside the tested path?** Anything the harness set up itself — a row it inserted,
a token it signed, a variable it exported — is a state the product has not been
shown to reach.

Two things follow:

- **An explicit environment allowlist turns a missing variable into a silent
  absent branch.** Container orchestration that names the variables it forwards
  will not warn about one you left out; the process simply reads `None` and takes
  its fail-closed path forever, which looks exactly like the feature being
  switched off on purpose. Enumerate what the code READS — import closure plus
  the AST of every environment access, resolving names bound to module constants
  — and assert the deployment passes each. Never grep for the variable's name:
  that finds the places that have it.
- **And the mirror, which fails OPEN: an allowlist that filters an environment
  also drops the variable that would have DISABLED something.** The entry above
  assumes the absent branch is the safe one. When the third party's default is
  ON, the safe value is the one you have to send, and a containment boundary
  built as a filter silently removes it — so the wrapper written to contain a
  capability is the thing preventing the containment. Measured 2026-09-18: an
  adapter passed a vendor binary an allowlisted environment specifically to keep
  provider keys away from its screenshot-egress tier, which worked; the same
  filter dropped `GHOST_SHELL`, the vendor's own off-switch for arbitrary
  command execution, which upstream ships ON deliberately. Every safety test
  passed, the module docstring asserted the containment, and a resumption file
  had been recording "no shell" as settled fact for a day.
  So: **a deny is a value you SEND, never a value you let through.** Set the
  off-switches explicitly on the child rather than inheriting them, which also
  makes an ambient `ON` in the operator's own environment unable to re-enable
  the thing. Then verify against the vendor, not against your own intent — and
  pair the run with the switch flipped, because the same request errors in both
  worlds and only the *reason* distinguishes them (here: "GHOST_SHELL is off"
  and code -32002, against an argument-parsing error at -32000, which the
  request only reaches BECAUSE the capability is live). A first version of that
  gate asserted merely that an error came back, and passed in both worlds.
- **Say in the gate what the gate does not cover.** One paragraph naming the
  preconditions it supplies is what stops the next reader treating a green as
  evidence about production. The estate had fixed this exact class once and
  recorded it as a comment beside the fixed line; the comment did not travel, and
  the identical defect landed one activation later on a different variable.

## A surviving mutation is a question about reachability, not a missing test

A mutation drill answers "would the tests notice this regression?" A mutant that survives
is one of: a reachable undetected bug · an equivalent mutant · a state the real producer
cannot construct · a defensive-only path · a harness failure · unknown. Only the first is
a coverage gap, and naming it is a claim that needs its own instrument.

Measured 2026-09-16 (Orca X): removing "show a size only when a metric exists" turned
nothing red. The producer-side trace showed why: the metric is null only when there is
no snapshot, and then every pane is unmeasured, so measured bytes without a metric cannot
be built. The fix was **not** a test with a hand-assembled impossible plan — that tests a
world production never enters and inflates the score. The guard stayed, with a comment
saying it is unreachable today and why (the plan type does not encode the invariant, so a
future producer could reach it).

So: before writing a test for a surviving mutant, trace every producer of the state, check
whether the type forbids it, and ask whether serialization or a mixed-version peer can
deliver it. Write the test only if one of those says yes; otherwise record the
classification where the code is. And the inverse holds — the reachability sweep is
still owed; "it looks impossible" is not the proof.

## Source

Incident evidence moved to `~/.claude/knowledge_vault/rules-evidence/instrument-before-claim.md` (2026-09-28) so it is not re-read on every call. The rule text above is unchanged.
