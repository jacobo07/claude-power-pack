# USEA Traps — Phase VII (2026-09-13)

> **Staging file, not a second corpus.** These entries belong in
> `vault/knowledge_base/ukdl-universal.md`. They are parked here because that file
> currently holds ~70 uncommitted prose lines belonging to another author plus ~72
> auto-appended capture rows, and `tools/foreign_hunk_guard.py` returned
> `VERIFY_MISMATCH` twice — it could name the foreign lines but not subtract them.
> Absorbing another writer's seventy lines under this session's message is the exact
> defect the pathspec doctrine exists to prevent, so the append was backed out and
> verified gone (five distinct needles, all zero).
>
> **Merge instruction:** whoever next commits `ukdl-universal.md` — which means the
> author of those seventy lines, who has to commit them anyway — should move the
> section below into it and delete this file. One corpus, searched by rule id, is
> the whole point; a permanent second store would be the fragmentation this estate
> already refuses elsewhere.

---

## A Detector That Flagged Its Own Documentation

One trap, paid for by a failure observed the hour it was written. It generalises
well past the naming question that produced it.

### Traps

**`T-DETECTOR-FLAGS-ITS-OWN-DOCUMENTATION-001`** — A gate whose subject is a
confusion will fire on the prose that explains the confusion, because correct
disambiguation necessarily places the forbidden token beside the very vocabulary
the gate treats as evidence of the defect. WHY IT LOOKS CORRECT: the detector is
right about the neighbourhood. The words really are there, the window really does
carry them, and every clause behaves exactly as designed — it is the CLASS that is
missing, not the matching. ORIGEN: `tools/test_usea_identity.py` was written to stop
two four-letter acronyms in this repository being merged by a future rename, one
naming a live sealed corpus and the other a proposal that was measured and
rejected. It scored 8/8 against the tree that motivated it. One commit later it
scored 7/8, and the single offender was the sentence the gate existed to make
possible: a line in `RESUMPTION_FILE.md` warning a future session not to reconcile
the two. Its window carried the live system's vocabulary and none of the rejected
system's, which is precisely the misattribution signature. WHY THE RECORDED FIX WAS
THE WRONG ONE: this estate had already met the sibling — a document naming
quarantined literals vetoed like a real defect — and the prescription on file was to
describe the subject obliquely. Applied here that destroys the artifact, because a
disambiguation record that may not spell either name cannot disambiguate. The
prescription repaired the PROSE when the defect was in the DETECTOR, which is why
the class recurred. PREVENTION: give the detector an explicit class for deliberate
contrast, and scope that class to the hit's own LINE while topic detection stays
window-scoped — a window wide enough to establish what a passage is ABOUT is far too
wide to establish what a sentence INTENDS. Count the class in the report rather than
dropping it, so an exemption stays auditable; and keep the equivalence clause
separate, so contrast wording cannot launder an alias claim. Both poles of the new
clause are driven synthetically, including a control proving the original red branch
is still reachable through it. DETECTION, and it costs nothing: write the
documentation for the rule FIRST, then run the gate against that documentation. A
gate that cannot survive its own explanation is not finished. SCOPE: universal —
banned-token linters, secret scanners, slop detectors, deprecation sweeps, profanity
filters, any gate whose subject is a string its own docs must quote.

### Candidates REJECTED from this corpus (recorded to prevent re-derivation)

- **"Pathspec-scoped commits and hunk-scoped staging conflict, so the pathspec
  doctrine needs an exception"** — REJECTED as already owned. `git commit -- <path>`
  takes the WORKING TREE and discards a carefully built index, so the two prescribed
  mechanisms genuinely cannot both be obeyed — and `tools/test_commit_scope.py`
  already states the decision table and drives it: guard used, commit from the index
  with no pathspec; guard unused, commit with a pathspec at file granularity.
  Recorded only because it was independently re-derived this session, which is
  evidence the owner is correct and unread rather than absent.

- **"The capture bus writing into a hand-maintained corpus is a defect"** — NOT
  filed. The rows are the estate's own failure-capture layer doing its job, and a
  spec on file (`vault/specs/capture-layer-liveness.md`) shows that layer was silent
  for ~80 days and was deliberately repaired. Noisy diffs in a shared corpus are the
  cost of a producer that works. The real observation is narrower and belongs to the
  hunk guard, not here: its subtract step fails when the foreign lines are near-
  duplicates of rows already in the file, and it fails CLOSED, which is the correct
  half.

---

## Admission on a Machine That Will Not Hold Still (Phase VIII, 2026-09-13)

### Process Rules

**`PR-ADMIT-ON-THE-TROUGH-NOT-THE-INSTANT-001`** — A capacity gate admitting a job
that will run longer than its own measurement must keep the WORST of several
samples, and must re-admit between units. WHY A SINGLE SAMPLE LOOKS CORRECT: the
reading is real, the comparison is right, and the gate genuinely refuses on a
genuinely small host — so on any machine that happens to be stable it is
indistinguishable from a correct gate. It is the sampling RATE that is wrong.
ORIGEN: measured while trying to admit the USEA outcome contrast. Available
memory on this host swung 277 → 3943 MB inside two minutes, and 1563 → 1183 MB
across nine seconds; a later five-sample admission read 949, 1032, 878, 871,
1247. A gate that sampled once at 3943 would have admitted eight model sessions
that then met 871, and for a job whose units are model sessions the OOM does not
present as an OOM — it presents as an arm that produced no artefact, which the
grader scores as a failure of the subject. COROLLARY, and the reason the rule is
about sampling rather than about memory: **two readings of a volatile quantity
taken minutes apart are not two instruments disagreeing.** Win32
`FreePhysicalMemory` reported 3943 MB and SQI-03's `available_mb` reported 554 MB
about two minutes later, which reads exactly like an instrument bug worth
chasing. Sampled in the same second they agreed three times running (387/277,
732/714, 719/694). Before indicting an instrument on a disagreement, check
whether the subject moved between the two readings. PREVENTION:
`tools/usea_outcome_contrast.py::admit` keeps `min(samples)` and re-admits before
each arm; `tools/test_outcome_admission.py` drives both poles on the same host in
the same second, because a gate that refuses everything and a gate that refuses
nothing both pass a single-pole drill. SCOPE: any capacity gate on a shared or
interactive machine — developer laptops, CI runners, burstable containers.

### Candidates REJECTED (Phase VIII)

- **"An experiment with no resource admission gate is a new trap"** — REJECTED as
  an instance, not a rule. `T-DOCTRINE-OWNER-EXISTS-AND-IS-ORPHANED-001` already
  owns it exactly: SQI-03 existed, owned the verdict, and the one consumer that
  most needed it never asked. Recorded here only because the orphan this time was
  pointed at the single experiment the whole programme exists to run.

- **"Grading a missing artefact as FAIL is a new trap"** — REJECTED, owned by
  `PR-CLASSIFY-THE-TEARDOWN-NOT-ONLY-THE-CLOCK-001`. The novelty was the blast
  radius, not the mechanism: here the misclassification would have landed in the
  treatment column of the programme's own falsification test.

---

## The Gate That Refused One State And Admitted Three (Phase VIII, 2026-09-14)

### Process Rules

**`PR-TEST-THE-STATE-THAT-PERMITS-001`** — A consumer deciding whether to ACT on
a multi-valued gate must test for the single state that PERMITS the action, never
for the state that refuses it. Written the second way, every value the author did
not enumerate — every state added later, every tri-state middle, every unreadable
reading — falls through to the action. WHY IT LOOKS CORRECT: the refusing value
is the one you are thinking about while you write the branch, it is the value
your drill supplies, and on a gate that currently returns only two states the two
forms are exactly equivalent. The defect is invisible until the gate returns its
third answer, which is the day you most need the refusal.

ORIGEN, and the reason this is a rule rather than an anecdote: **it was measured
TWICE on one day, in two subsystems that share no code.**

1. `usea_outcome_contrast.py` asked `state == "BLOCKED"` before dispatching eight
   live model sessions. SQI-03 returns four states, and its middle pole says in
   its own words that such a run "may complete or may be killed, and which one
   happens is not a fact about the subject". This host read `PARTIALLY_QUALIFIED`
   with a worst-of-five trough of 476 MB against 1724 MB required, and the
   experiment would have run. The producer carried the mirror-image fault: the
   trough correction was guarded on the healthy pole, so the worst reading was
   compared against the requirement only when the instant probe had already
   called the host fine.
2. `closer-guard.js` asked whether a turn carried a `tool_use` block before
   exempting it from every dead-screen class but one. A tool call that the Owner
   REFUSED still satisfied that test, so a rejected Edit bought the turn its
   silence and the session ended on "No response requested." — the exact sentence
   the `NULL_ACK` class had been sealed for twelve days earlier. Measured on the
   live transcript: `classify(text)` returns `NULL_ACK` and
   `classify(text, {toolTurn:true})` returns null.

Two systems, one morning, the same shape: a predicate that asks whether something
was ATTEMPTED where the decision needs to know whether it SUCCEEDED.

PREVENTION: one named predicate answering "may this proceed", returning true for
the permitting state alone, called by every decision site — a shared predicate
travels where a convention does not. Drive it over the gate's FULL vocabulary,
and over an empty record, so a state added later is refused by construction
rather than by whoever remembers. When you write an exemption, name the premise
it rests on and falsify it: construct one input where the premise holds and the
damage happens anyway. SCOPE: universal — capacity and health probes, auth and
entitlement checks, migration and readiness gates, any verdict that is not a
boolean, and any guard whose exemption is phrased as "this case did some work".

### Candidates REJECTED (2026-09-14)

- **"A lesson left as a comment beside the fixed line does not travel"** — NOT
  filed as new. Already owned by the global rule on a recorded lesson recurring
  anyway, which prescribes the same remedy this session reached independently:
  ship the helper, not the advice. Recorded because this is a second measured
  instance and a sharp one. `verify_spp.py` met this exact class on 2026-09-11
  and left the reason beside the line it fixed — test `is not True`, deliberately,
  not `is None`, because an override "must change what the run DOES, never what
  the run may CLAIM". Two days later the sibling consumer of the same gate, one
  directory away, was written with the defect. The prose was correct, present,
  and in the repository. It did not reach the keystroke, which is the whole point
  of the owning rule.

- **"A suite can be green while blind to its subject's decision"** — REJECTED as
  an instance of the existing rule that a gate nobody has driven the red branch
  of is indistinguishable from one that passes. The specific shape is worth
  naming inside that owner rather than beside it, and both of today's cases wear
  it: the USEA suite asserted the gate's VOCABULARY — that its state string was
  one of four — and never asked what the caller DOES with each word; the
  closer-guard suite, eight files and two hundred cases deep, had never once
  written a `tool_result` into a fixture, so a refused call was UNREPRESENTABLE
  and the patterns could only ever be exercised against calls that worked.
  Thirteen of thirteen and twenty-one of twenty-two, and in both the one branch
  that mattered was not merely untested but inexpressible.

---

## The Gate That Refused One State And Admitted Three (Phase VIII, 2026-09-14)

### Process Rules

**`PR-TEST-THE-STATE-THAT-PERMITS-001`** — A consumer deciding whether to ACT on a
multi-valued gate must test for the single state that PERMITS the action, never for
the state that refuses it. Written the second way, every value the author did not
enumerate — every state added later, every tri-state middle, every unreadable
reading — falls through to the action. WHY IT LOOKS CORRECT: the refusing value is
the one you are thinking about while you write the branch, it is the value your
drill supplies, and on a gate that currently returns only two states the two forms
are exactly equivalent. The defect is invisible until the gate returns its third
answer, which is the day you most need the refusal. ORIGEN: measured here.
`usea_outcome_contrast.py` asked `state == "BLOCKED"` before dispatching eight live
model sessions. SQI-03 returns four states, and its middle pole says in its own
words that such a run "may complete or may be killed, and which one happens is not
a fact about the subject". On 2026-09-14 this host read `PARTIALLY_QUALIFIED` with a
worst-of-five trough of 476 MB against 1724 MB required, and the experiment would
have run. The producer carried the mirror-image fault: the trough correction was
guarded on the healthy pole, so the worst reading was compared against the
requirement only when the instant probe had already called the host fine.
PREVENTION: one named predicate answering "may this proceed", returning true for the
permitting state alone, called by every decision site — a shared predicate travels
where a convention does not. Drive it over the gate's FULL vocabulary, and over an
empty record, so a state added later is refused by construction rather than by
whoever remembers. SCOPE: universal — capacity and health probes, auth and
entitlement checks, migration and readiness gates, any verdict that is not a boolean.

### Candidates REJECTED (2026-09-14)

- **"A lesson left as a comment beside the fixed line does not travel"** — NOT filed
  as new. Already owned by the global rule on a recorded lesson recurring anyway,
  which prescribes the same remedy this session reached independently: ship the
  helper, not the advice. Recorded here because this is a second measured instance
  and a sharp one. `verify_spp.py` met this exact class on 2026-09-11 and left the
  reason beside the line it fixed — test `is not True`, deliberately, not `is None`,
  because an override "must change what the run DOES, never what the run may CLAIM".
  Two days later the sibling consumer of the same gate, one directory away, was
  written with the defect. The prose was correct, present, and in the repository.
  It did not reach the keystroke, which is the whole point of the owning rule.

- **"A suite can be green while blind to its subject's decision"** — REJECTED as an
  instance of the existing rule that a gate nobody has driven the red branch of is
  indistinguishable from one that passes. The specific shape is worth naming inside
  that owner rather than beside it: the suite asserted the gate's VOCABULARY — that
  its state string was one of four — and never asked what the caller DOES with each
  word. Thirteen of thirteen, and the one branch that mattered was untested.
