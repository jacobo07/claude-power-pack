---
name: guard-event-reachability
description: Guard, hook and gate liveness doctrine. Use when a guard, hook, gate, detector or CI check failed to catch something, or when writing or registering one: prove it RAN before debugging its predicate (replay the escaped bytes), check the event still fires in the abnormal state it exists for (interrupt, deny, timeout), hook timeouts that fail open silently, a block whose reason goes to a channel nobody reads, a parser (BOM) in front of the predicate, a CI job no runner ever picked up (runner_id 0), and optional build parts missing before any guard runs. Core rule - a gate that cannot fire is indistinguishable from one that passes.
metadata:
  opportunity_detector: none
  opportunity_detector_reason: coverage class none; no registered card hook and no CO-12 adapter names this skill
---

# Guard Event Reachability

A guard is a pair: **a predicate** and **an event that delivers the subject to it**. Almost all
review attention goes to the predicate, because that is the part that looks like logic. The event is
a one-line registration nobody re-reads, and it is where the guard dies.

> **Before debugging a guard that failed, prove the guard RAN.**

A predicate that never received the case and a predicate that received it and passed produce the same
observable: nothing happened. They need opposite fixes, and the convenient reading — "my patterns are
wrong, let me add another" — sends you to rewrite code that was already correct.

## The measurement that separates them

Replay the guard against the exact bytes of the case that escaped, with a control:

- **it blocks on replay** → the predicate is fine; you have an *event* problem, and no amount of
  pattern work will fix it.
- **it passes on replay** → now it is a predicate problem, and you know which case to drive.

This costs one script and it inverts the diagnosis often enough to be worth doing first, every time.
Then confirm the event independently: a guard that writes a heartbeat on *every* judgement — not only
on the blocking ones — answers "did it run?" with one read. A counter that did not advance across the
window of the escaped case is proof of non-delivery. Build that counter before you need it; after the
incident the evidence is already gone.

## The failure has a shape: the highest-value case is the unreachable one

This is not bad luck. A guard is usually mounted on the event that fires when things go **normally**,
because that is the event the author was looking at while writing it. The cases the guard exists for
are, by construction, the abnormal ones — and abnormal paths frequently skip the normal event.

Measured instances of the same shape, one estate:

| guard | mounted on | the case it exists for | why it never arrived |
|---|---|---|---|
| dead-screen closer | `Stop` | a turn that died after a user interrupt | an interrupted turn does not reach `Stop` |
| per-tool safety gate | `PreToolUse` | a denied call | returning `{continue:false}` *halts the agent*, ending the turn at the tool boundary — so `Stop` never runs either |
| bridge guard | `PreToolUse` | a banned shell call | the hook timed out under turn-boundary fan-out and **failed open, silently** |
| agent-exit marking (Orca) | OSC 133;D from the shell | an agent Orca itself launched | the command rode in PowerShell's launch args, ran before the first prompt, and so emitted no C and no D |

So ask, of every guard: **what is the state of the world when this guard matters, and does the event
still fire in that state?** If the answer is "the system is mid-abort", assume it does not.

The same question applies to **delivery paths**, not only abnormal states. A lifecycle keyed on
markers the subject emits is only as complete as the paths that make it emit them. A faster or
shorter route for the same work (launch arguments instead of typed input, a batch call instead of a
loop, a cached reply instead of a round trip) can skip the marker. Every test that drove the familiar
path then stays green. Drive each delivery path the product actually uses, not only the one a person
would type.

A related trap, from the same session: **a signal a restarted client must re-learn belongs with
whoever saw every byte.** An "is idle" flag kept only in the client disappears on restart. The event
that set it had already fired before the new client existed. Nothing in the client can recover it,
so the long-lived host must record the fact and answer when asked.

## Timeouts convert a guard into a no-op with no error

A hook killed at its deadline has its stdout discarded, and the chain then reports **exactly what a
clean pass reports**. Fan-out at a turn boundary makes this correlated rather than random: in one
measurement 38 of a guard's 45 timeouts landed in the same second as another hook's, with three hooks
of one chain dying inside a 7 ms window. Each measured 4× headroom when run alone.

Two consequences:

- **The fix is scheduling, not budget.** Raising a timeout moves the cliff. Run the guards whose
  failure is the actual harm *before* the pool opens, sequentially, on an uncontended host.
- **A guard that could not run must be logged as its own class**, distinct from "ran and passed".
  Grep for the class, never for one script's name, or the next guard to go inert is invisible again.

## Cover the event you can prove fires, even if it is later

When the right event does not exist, an after-the-fact event is worth far more than nothing — because
the escaped artifact is usually still observable. A turn that ended on a banned closer is still the
last turn when the user types again, so the *next* prompt can carry the correction. That converts a
silent failure into a self-healing, counted one.

Such a backstop must: never block the user's own action; **import** the primary guard's predicate
rather than copy it, so the two cannot drift; and suppress the cases where the abnormal state was the
user's deliberate choice, or it becomes noise on every interrupt and gets switched off.

## DON'T

- **Don't read "the guard is wired" as "the guard runs."** Registration is a line in a config;
  reachability is a measurement. Drive the real dispatcher with a real payload and require the
  output to survive the merge.
- **Don't add a pattern because a case escaped.** Replay first. A new pattern beside a correct one
  that never receives input adds maintenance and no coverage.
- **Don't trust a guard whose log has no recent entries** — and don't trust the absence of a log
  file either. Check *where it actually writes* before concluding it never ran; `state/` and `logs/`
  are different directories, and searching the wrong one manufactures a finding.
- **Don't let a test suite stand in for delivery.** Every red-branch test can pass against a guard
  that nothing ever calls. Tests prove the predicate; only an end-to-end drive proves the event.
- **Don't reuse one hook's event conclusion for another.** Two guards in one file can sit on
  different events with different failure modes; check each one's event before its logic.

## A guard that fires but cannot be heard

The rungs are: the guard never ran · the guard ran and passed · **the guard ran, blocked
correctly, and its reason went to a channel nobody reads.** The third produces a *working*
block, so every liveness check above it stays green — the heartbeat advances, the log fills,
the call is refused. What is missing is the only part the agent consumes.

> **A block the caller cannot learn from is a blind-retry loop wearing the costume of a guard.**

This is worse than a silent gate, because a silent gate merely fails to stop you. A mute
gate stops you *and* withholds the pivot, so the only move left is to vary the call and try
again — which is precisely what the two-consecutive-failures law forbids and cannot be
followed, because you cannot pivot away from a cause you were never told. The loop burns
turns and ends in a narrated turn with no tool call, i.e. the dead screen.

**Check the channel against the exit code's contract, not against the code's intent.** Where
a host defines separate channels for "result" and "reason", writing a perfect message to the
wrong one is indistinguishable, from the outside, from computing no message at all.

The cheap detector is a **sibling comparison**: another guard on the same event, with the same
exit code, whose reason *does* arrive. If one speaks and one does not, the harness is fine and
the mute one has a channel bug. That single contrast turns an assumption about the host's
contract into an observation.

### An allow-list entry is not evidence that anything is said

The trap that let this live thirteen days: a test asserted the dispatcher was *permitted* to
surface that guard's stderr, and passed. Permission and production are different claims, and
the permission one is the easy one to write.

**A clearance for a silent producer is a permanent green.** So for every "X may be forwarded"
assertion, require a sibling "X actually emits something, and here is its content" assertion —
asserting on the *content* (the token, the pivot), never on non-emptiness, since a bare newline
satisfies the latter and teaches nothing.

And drive it end-to-end on **that guard's own event**. A suite whose only end-to-end half
exercises a different hook on a different chain has proven the plumbing for the hook it drove
and nothing at all for its neighbours.

## Source

Incident evidence moved to `~/.claude/knowledge_vault/rules-evidence/guard-event-reachability.md` (2026-09-28) so it is not re-read on every call. The rule text above is unchanged.

## The predicate's INPUT is a third place the guard dies

The file separates two rungs — the guard never ran, and the guard ran and passed. There is a rung
between them: **the guard ran, and the thing that feeds its predicate threw.** Every `catch` that
returns a default turns a parse failure into a verdict, and the default is almost always the
permissive one, because that is what fail-open means.

So the guard is live, registered, reachable, correctly patterned, and answers the wrong question on
every invocation. Nothing logs, because nothing failed — a caught exception is not an error.

Measured 2026-09-15, adding a path filter to the PreToolUse Edit chain. The predicate was correct in
isolation and returned `false` for its whole life in production. The cause was **three invisible
bytes**: PowerShell 5.1 prepends a UTF-8 BOM when piping to a native exe, `JSON.parse` throws on it,
and the catch returned "not a match". 204 bytes sent, 207 received. This estate already had the BOM
trap written down for `ssh`; it did not transfer to `JSON.parse`, because prose does not travel to
the moment you type a `try`.

> **Wherever a guard's subject arrives through a parser, the parser is part of the guard.** Assert
> the predicate against a malformed input that a real producer can actually emit — not only against
> the well-formed one you constructed.

### On a starved host, the instrument must count, never time

The same fix was nearly reported as a win on timing. A scratchpad write measured **12,438 ms**
against a project write's **7,925 ms** — the wrong way round, on a change that was doing nothing at
all, because at 753 MB free of 32 GB the variance swamps any signal (identical no-op payloads
measured 2,870 / 5,335 / 3,580 ms the same hour). Output could not discriminate either: both runs
emitted the same 17 bytes, since a synthetic payload never reaches the hooks that speak.

What settled it in one read was an env-gated stderr line naming **what was about to run**:
`scratch=false runnable=11/11`. A count of members is load-independent, it can come back either way,
and it keeps answering for every future change to that chain. **When the clock cannot resolve the
question, stop taking readings and build the counter.**

Two harness failures followed, both of which produced a red that looked exactly like the feature
breaking. A fixture directory renamed without renaming the chain's paths → `runChain` silently
dropped both steps as `script missing` → "nobody ran", which is indistinguishable from a filter that
skipped everything. And a shared fixture file on a host running dozens of concurrent sessions → one
unattributable 16/17. Fixes: derive every path from one constant, isolate fixtures per PID, and
**assert the precondition** — a missing fixture now exits 2 as `HARNESS-FAILED`, never as a finding.

And one about the author, not the code: **the agent's own tool calls are part of the load.** The turn
before this one died on a large multi-step PowerShell probe — two dispatcher spawns plus timing loops
— proposed and never executed, leaving the Owner on a frozen screen. On a host at 97 % memory the
measurement apparatus is the thing tipping it over. One small command per call is not tidiness; it is
the difference between a reading and a dead pane.

Proof: `hooks/tests/test-scratchpad-fast-path.js` 17/17, both poles plus a negative control that the
full chain still runs on a project path. Two mutation drills, each landing on its own assertion:
deleting the filter line → 16/17 on `V-SCRATCH-E2E-SKIP`; deleting the BOM strip → 16/17 on
`V-SCRATCH-BOM`. Both restores verified by SHA-256.

## The rung below every other one: no machine ran it

Every rung above assumes something executed. There is one beneath them all, and it is invisible
from inside the system: **the guard was correct, registered, reachable, mounted on a live event
with a real executor — and no machine was ever allocated to it.**

> **A gate with a correct executor and no runner is indistinguishable from a passing gate.**

Measured 2026-09-21 (Orca X). A commit added a check to a `lint` chain without the matching CI
step, which makes an existing gate red — a gate written for exactly that defect class, with a
correct pull-request executor running the whole test suite. Nothing reported it for eleven hours.
Every run created in that window completed in 2–6 seconds having been assigned no runner and
having started no step, so the failing gate never ran.

What makes this its own rung rather than a variant of "the guard never ran": the *repository* is
blameless and unfixable. Definition, wiring and event eligibility are owned by code; **capacity is
owned by an account**. Editing YAML to fix it is the diagnosis going wrong in the most expensive
direction.

**Classify by the field the platform gives you, not by the icon or the duration.** On GitHub the
discriminator is `runner_id` on the job: `> 0` a machine ran it, `0` a machine was requested and
never arrived, `null` the job was skipped by a condition and asked for nothing. All three can
surface as `conclusion: failure` or as a red tick. Duration is a proxy and a poor one — a skipped
job there reports `completed_at` *before* `started_at`.

Three rules follow, and the third is the one people skip:

- **`BLOCKED` is not `FAILED`, and the report must carry the highest rung actually reached.** "Run
  created, no runner" and "step started, gate failed" send an engineer to opposite places.
- **No executions is not zero flakes.** A promotion ladder fed by an absent runner accrues `NO
  DATA`, and recording that as stability is how a gate becomes required on the strength of nothing.
- **A system cannot use an unavailable executor to prove the executor's own availability.** Any
  check for capacity starvation has to run out of band — which also means it must not be shaped as
  a CI gate, or it inherits the very condition it is measuring.

And keep the symptom apart from the cause. "No runner was assigned" is observed; "the account's
minutes are exhausted" is an inference about billing, and unless billing was actually read, saying
it promotes an inference to a measurement. Name the rung; leave the cause labelled.

## A perfect guard ladder cannot see how its subject was ASSEMBLED

Every rung above is about a guard that failed to judge. There is a final one where nothing failed at
all: **each guard ran, received its subject, evaluated correctly, and refused for a true reason — and
the run was still void, because the subject had been built without the part the question needed.**

This is the worst-tasting failure of the set, because the output is a tidy cascade of correct
refusals. Nothing is red. Nothing is silent. Every message is accurate.

Measured 2026-09-21, on a budgeted emulator run. The subject is assembled from optional compile-time
stages, and the run was built with five of the six it needed. It compiled, linked, passed a lint gate
and a symbol gate, booted, and reached its target state. Then:

```
REFUSED step=1 ... built=0 -- placing an unbuilt card
REFUSED step=1 ... built=0 -- showing an unbuilt card
REFUSED step=1 ... built=0 shown=0
REFUSED step=1 ... built=0 shown=0
VERDICT=INCONCLUSIVE, PRECONDITION NOT REACHED
```

Four guards, four correct refusals, one correct verdict, and a wasted run — the classification was
right and useless, because **"the stage refused" and "the stage was never compiled in" are the same
observable from anywhere downstream of compilation.**

> **A runtime refusal ladder tests the subject. It says nothing about whether the subject was
> assembled with the parts the question needs, because composition is decided before any guard
> exists.**

So for anything assembled from optional parts — build flags, feature toggles, dependency-injected
collaborators, plugin sets, compose profiles, test fixtures wired by configuration:

- **Encode the dependencies where composition happens**, so an incomplete subject is a build error
  rather than an expensive null result. A stage may be requested only when every stage it will refuse
  without is present. This costs one `#error`-equivalent per edge and it retires the whole class.
- **Never infer the part list.** I read the available options and inferred which ones the run needed
  instead of reading which one sets the flag each guard tests. The list was one grep away.
- **Make the artifact state its own composition.** A subject that announces the stages it was built
  with turns this from an invisible precondition into a line in the log.
- **Drive the red branch with the exact composition that failed**, and put the cost in the message —
  the guard here names the run it cost, so the next reader meets the incident rather than a rule.

The generalisation, and the reason this belongs beside the other rungs: the guard ladder's domain is
the subject's *behaviour*. Composition is upstream of behaviour, so no amount of guarding reaches it,
and a defect there arrives dressed as the subject honestly declining.
