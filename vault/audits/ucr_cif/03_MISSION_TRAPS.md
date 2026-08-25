---
title: UCR-CIF Compendium — Dataset-Generation Failure & Trap Record
date: 2026-08-25
status: OPEN — appended during the mission, not written at the end
mandate: mission brief §62 (UKDL evaluation) · §63 (error protocol) · deliverable #16
---

# Mission Traps — failures observed while building this compendium

Every entry below was **observed in this session**, with the evidence that produced it.
None is hypothetical. Each carries a proposed disposition; none is auto-promoted to UKDL —
evidence and applicability first (§62).

---

## T-INVENTORY-OUTPUT-CAP-001 — a dense corpus range silently exceeds a subagent's output cap

**Observed.** The inventory agent assigned lines 17,500–35,000 terminated with
`API Error: Claude's response exceeded the 64000 output token maximum`. The entire range's
work was lost. A sibling agent had already reported **259 concepts** in that same range —
at ~250 output tokens per full record, 259 records is ~65k tokens, i.e. the range was over
budget before the agent read its first line.

**Mechanism.** Range size was chosen by *line count* (a uniform 17,500-line split), but the
output cost is driven by *concept density*, which is not uniform. Lines 35,000–52,500
yielded 133 records; 17,500–35,000 yielded 259 — nearly double from an identically sized
range.

**Why it is not just a retry.** Re-running the same shape reproduces the same overflow.
Regla 12 applies: the second attempt must change the mechanism, not the parameters alone.

**First fix — insufficient, recorded as such.** Two changes: split the dense range in half
(17,500–26,250 and 26,250–35,000), and switch to a **compact one-line-per-field record**
(`DEF`/`OWNS`/`IO`/`LAW`). The aggregator was taught to parse both formats so ranges already
written verbose did not need regenerating.

**Second failure, same shape.** The agent on lines **1–17,500** — a range I had judged
*less* dense and dispatched in the verbose format before the pivot landed — died with the
identical error. Two consecutive failures of the same shape triggers Regla 12: the next
attempt must change the **mechanism**, not the parameters.

Note the diagnostic error inside the first fix: I treated range size as the variable and
halved it. But 1–17,500 was never halved and failed anyway, which proves density is high
across the corpus generally, not concentrated in one range. **Halving a range is a parameter
change wearing a mechanism's clothes** — it moves the same design closer to a cliff instead
of stepping away from it.

**Real fix — per-slice files.** The cap is on a *single response*, not on cumulative work.
So the agent now performs **one Read then one Write per 2,000-line slice**, each slice to its
own file (`inv_r1_slice1.txt` … `inv_r1_slice9.txt`), never accumulating records across
slices. No single response can exceed one slice of records (~8–15k tokens against a 64k cap).

Two properties the earlier fixes lacked:
- **Bounded by construction**, not by an estimate of density.
- **Crash-survivable** — a killed agent leaves every completed slice on disk, where the
  previous design lost the entire range.

The agent is also instructed to stop and report partial coverage rather than risk the cap,
because partial coverage recorded honestly outranks a killed agent.

**Generalizes to.** Any fan-out where work is partitioned by a cheap proxy (lines, files,
bytes) while cost is driven by an unmeasured property (density, nesting, match count).
**Partition by the thing that costs, or measure the proxy's correlation to it first.**

**Disposition.** UKDL trap candidate. Applicability is broad (every corpus sweep, every
parallel audit) and the evidence is a hard failure, not an inference.

---

## T-AGENT-BAND-OVEREXTENSION-001 — a subagent reported one contiguous band where the region was interleaved

**Observed.** The range-4 agent reported `CONTAMINATION_BAND: 60177-70365` as a single
contiguous block of pasted harness documentation. Measurement at 100-line resolution using
two independent signals found **nine discontinuous runs totalling ~3,900 lines**, with
genuine Spanish corpus at 66,000–68,100 and continuously from 70,300 onward.

**Consequence had it been accepted.** ~2,000 lines of real corpus discarded — a coverage
loss in precisely the direction the mission's §5 zero-omission rule forbids. The error is
*asymmetric*: an over-wide exclusion band silently deletes source material, while an
over-narrow one merely admits noise that later classification catches.

**Mechanism.** An agent reading sequentially sees contamination start, sees it continue
across several slices, and reports the outer envelope. It has no cheap way to notice a
corpus island *inside* the envelope, because confirming absence of contamination requires a
different signal than detecting its presence.

**Generalizes to.** Any boundary reported by a sequential reader. **A range boundary
asserted by a reader is a hypothesis; boundaries that exclude material must be measured
with a signal independent of the one that found them.** Prefer two orthogonal signals
(here: harness markers *and* Spanish function-word density — a pasted English prompt cannot
score on both).

**Disposition.** UKDL trap candidate, sibling of the existing
`PR-COVERAGE-BY-CONSTRUCTION-001` family.

---

## T-VOCABULARY-ZERO-IS-NOT-ABSENCE-002 — my own grep declared a built system missing

**Observed.** I recorded in the D2A audit that a grep for UBC's function
(`minimum sufficient`, `maturity capsule`, `compile … applicable … mission`) returned
**zero matches across all 84 modules**, and concluded the compiler might not exist.
`modules/capability_runtime/applicability.py` is a *"Capability Applicability Engine —
decides which capability contracts apply to a mission, and how strongly,"* implementing
anti-triggers, graded activation, evidence gates and duplicate-scope rejection.

**Mechanism.** The probe searched the **source corpus's** vocabulary; the module uses its
**own** vocabulary. A gate is bounded by the words it knows, and an unrecognised idiom
reads as zero. **Zero cannot fall.**

**Why it is recorded here rather than silently fixed.** This is the second instance in this
audit (the first being the 24 DEFER rows) and the only one that was mine. The estate's
sealed lesson `feedback_zero_cannot_fall` already names the mechanism — it did not prevent
the recurrence, which is itself the finding: *knowing the rule did not stop me applying a
vocabulary-bounded instrument and believing its zero.*

**Fix applied.** Before any CREATE verdict, a capability-level sweep is now mandatory —
probing the **function under any name**, with the source's acronym deliberately excluded
from the query. Where that still returns near-zero (Certified Primitives & Golden Paths:
2 hits estate-wide across two independent sweeps), the signal is trustworthy.

**Disposition.** Not a new UKDL rule — an **enforcement gap on an existing one**. The right
output is a procedural gate ("no CREATE verdict without a capability-level sweep"), not a
fourth restatement of a lesson already sealed three times.

---

## T-D2A-CONSTANT-FLOOR-001 — 24 of 28 verdicts returned the same number

**Observed.** `d2a_engine.py --family-file --repo-evidence` on 28 spine systems returned
4 KEEP and 24 DEFER, where **every one of the 24 scored coverage = exactly 45 %** — the
engine's plausibility floor.

**Mechanism.** A score identical across 24 items carries no information and cannot rank
them. This is the estate's own sealed pattern *constant factors rank nothing*, appearing
here in the instrument built to prevent duplication.

**Consequence.** The engine's DEFER output is unusable as a build signal in either
direction. Treating it as novelty would repeat the CRPF/IGEF/E1–E5 strikes; treating it as
ownership would suppress genuine gaps. It must be read as **UNKNOWN** and resolved by
per-system evidence sweeps — which, done manually, resolved 9 of the 24 immediately.

**Note on scope.** This is an observation about the engine's behaviour on a 28-item family,
not a defect report against it. The engine correctly declines to name a parent it cannot
evidence; the trap is in *consuming* the floor as if it were a measurement.

**Disposition.** Feed to the D2A owner as a measured observation. Candidate improvement:
emit `UNRESOLVED` as a distinct verdict rather than a capped coverage number, so the
floor cannot be mistaken for a score.

---

## Standing obligation

New failures are appended here **in the session they occur** (zero knowledge debt), and
evaluated for UKDL promotion at Phase 9 — never auto-promoted, never silently dropped.
