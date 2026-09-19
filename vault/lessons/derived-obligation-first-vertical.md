# A Requirement Nobody Stated, and the Controls That Decide Whether You Found It

**Measured 2026-09-20**, GSD X wave N4, `claude-power-pack`.

One sentence of human intent — *"Write a CLI that watches D:\incoming and uploads
each new file to S3, then deletes the local copy so the disk does not fill up"* —
against a project whose own description says the camera controller emits no
completion signal, bucket versioning is off, and the nightly job treats every
object present as a complete recording.

Three material obligations follow and none of them is in the sentence. The
mission's closure was denied while its explicit backlog was empty.

That result is the easy half. The useful half is what the controls did to it.

## The transfer control caught the operators fitted, twice

Recall against a holdout is the weakest evidence a derivation system can offer,
because the same hand usually writes both. The question that matters is whether
the operators are **rules** or a lookup table wearing a rule's name, and one
control answers it: run them on a domain they were never written for.

- **Domain 2** (an ETL copying batches to an archive and dropping staging rows)
  failed **2 of 3**. `destructive_act_commanded` required the object to be
  spelled `local|copy|file|original|source`, so "drops the staging **rows**" did
  not match. `measured_failure_mode` required the frequency digit to follow its
  noun, because the fixture happened to say *"3 to 12 short outages"* while the
  new domain said *"2 to 5 outages per week"*. The patterns encoded the
  fixture's **phrasing**, not the fact.

- Generalised to structure — a transfer verb followed by a destructive verb is a
  shape; a frequency may sit on either side of its noun — domain 2 passed. But
  domain 2 had **informed the fix**, so it stopped being clean evidence, and a
  third domain was written as the re-test.

- **Domain 3** failed again, on one operator, because `publish` was not in the
  transfer-verb list.

> **A closed vocabulary over natural language is fitted by construction.** Every
> new wording costs exactly one more word, and the cost never stops.

The verb was added because it belongs to the class. The claim was not raised.
What this supports is *"survives three wordings after three corrections"*, never
*"generalises"* — and the gate's own evidence string says so, so a future reader
sees the caveat at the same moment they see the pass.

The operators are general over **facts**. Getting facts out of prose is not
general over **sources**. That is the boundary, and it is the next wave's target.

## Candidate is not authority, and the reasons must stay apart

Derivation proposes; a gate dispositions. Reaching ACCEPTED requires three
independent conditions — a named consequence, evidence found in *this* project's
reality, and a closure condition — and they are kept separate because collapsing
them loses which one failed:

- no consequence → **REJECTED**: a requirement whose omission costs nothing is a
  preference.
- no evidence → **NOT_APPLICABLE**: the rule fired, this project does not
  support it.
- no closure condition → **REJECTED**: an obligation that can never be closed
  blocks the mission forever.

Without the negative control this says nothing: a reality supporting nothing
must yield **zero** obligations, and a destructive act whose reality *has* a
recovery path must raise no irreversibility obligation. A detector that speaks
everywhere says nothing anywhere.

## Worker narrative is not transition authority

The executor's own account of completion is taken as an **input** and never
consulted as evidence. Leaving the parameter out of the signature would hide the
decision; taking it and refusing it makes the refusal testable.

Three outcomes, never two: *no verdict supplied*, *the gate ran and failed*, and
*the obligation names no gate* are different facts needing different fixes, and
a test asserts the first two are **distinguishable** rather than merely both
refusing.

## Two ledgers that look alike and must not merge

Program knowledge about GSD X ("has GSD X proven X?") and mission work state
("does this service preserve ordering after a reconnect?") share epistemic
manners and share no storage. The mission store is one JSON file under the
mission's own root. A vocabulary that looks similar is not a reason to merge two
owners — which is the same correction this programme already paid for once.

## Reuse by contract, not by noun

`modules/daif/obligation_extractor.py` owns "obligation" with closure and gate
semantics. Audited rather than assumed: its input is a session transcript, it
**requires a commitment frame** and refuses wishes, so it extracts obligations
someone **stated**. A derived obligation is defined by never having been stated,
so DAIF's own intake would discard the entire population.

Same noun, inverted predicate. The **shape** transferred — `closure_condition`,
`done_gate`, `owner`, `authority`, `evidence`, and the rule that a candidate
naming no closure condition is a wish. The **ownership** did not.

## The polarity trap that would have eaten the wave

GSD Core already owns *"narrative is not evidence"* — at the **verification**
boundary, with the opposite polarity. `verifier-evidence-gate.md` requires
deterministic evidence for a new-scope finding to **BLOCK**, and downgrades one
without it to advisory.

A derived obligation arriving as a verifier finding is exactly a new-scope
finding with no failing test. It would have been **silently demoted to
advisory**, and the whole mechanism would have evaporated into a report nobody
acts on — discoverable only by the feature quietly never working.

Evidence gating a *block* and evidence gating a *close* are complementary. Read
the neighbouring owner's polarity before joining to it.

## Gates that caught their own author, three times in one wave

1. The **pin-currency** gate did not exist: `STALE_DEPENDENCY` had been computed,
   printed and exited on since N3, and no gate read the number. Invisible for
   exactly as long as the count was zero.
2. On its second run it flagged a claim whose **standing half had become false** —
   a contract asserted to be blocked on every prompt is blocked on none, because
   its engine now evaluates dormancy before evidence.
3. The **dependency ratchet** refused nine claims this wave landed unpinned.

## Rule candidates — PROMOTION_PENDING_CONCURRENT_WRITER

`vault/knowledge_base/ukdl-universal.md` was modified **2 minutes 44 seconds**
before this file was written, with 17 uncommitted lines from a writer outside
this session. It is not touched. Recorded here with intended level, **not
promoted**:

| intended | rule |
|---|---|
| HARD RULE | A derived requirement must retain machine-traceable provenance to the facts and the rule that made it material. Without it the requirement is an assertion with a confident tone. |
| HARD RULE | A model-generated requirement is a CANDIDATE until applicability and materiality are established by something other than the model. |
| HARD RULE | Explicit backlog completion does not authorise mission completion while a required derived obligation is open. |
| HARD RULE | A derived obligation goes stale when its causal parent stops holding — including from SATISFIED, because proof of something no longer required is not a reason to keep requiring it. |
| HARD RULE | Worker narrative is not transition authority. Only a verdict from a gate that ran moves a state. |
| PROCESS RULE | Test a derivation rule against a domain it was NOT written for before reporting recall; a domain that catches it becomes part of the fix and stops being evidence, so the re-test needs a further one. |
| PROCESS RULE | A detector's red branch must reach a gate. A verdict that is computed, printed and read by nobody is indistinguishable from a gate that passes. |
| PROCESS RULE | Pin a standing property to the surface it was observed against and a dated measurement to the commit that produced it. Pinning a dated fact to a live blob manufactures a permanent false stale, and a staleness gate nobody can legitimately green gets switched off. |
| TRAP | A closed vocabulary over natural language is fitted by construction; adding the word each new domain reveals is chasing, not generalising. |
| TRAP | A mutant that crashes the suite is not a survivor. Non-zero with no failing gate is a malformed mutant, and scoring it either way lies about the suite. |
| TRAP | Proving two of three inputs identical and concluding "unchanged" — the third input is the one that decides. |
| TRAP | Splitting prose on a conjunction to manufacture a requirement list. It reads well and it is a fabrication. |
| TRAP | A seal whose hash depends on a line-ending policy is not a seal: it cannot distinguish an edit from a checkout. |

## Evidence

`c63d480` · `977223e` · `b0c0d1d` · `b9e7816` · `4b301cc` · `025f604` ·
`5d09fad` · `94f4c15`.

Dataset 11/11 exit 0 · drill 10/10 both poles, skip accounting 3 ·
GSDX suite 15/15 · GSDX mutations 2/2 · mission suite 17/17 ·
mission mutations 6/6 · reconciler 0 uncovered, 0 stale, exit 0.

Production Reality: **FIRST_VERTICAL_SLICE**. One fixture, three operators.
`UNIVERSAL_CAPABILITY_UNPROVEN`, and the gate is proven at the contract, not at
the event — no GSD capability manifest was registered, so nothing has yet called
it from a real run.
