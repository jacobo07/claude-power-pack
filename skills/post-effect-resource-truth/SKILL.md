---
name: post-effect-resource-truth
metadata:
  opportunity_detector: none
  opportunity_detector_reason: "doctrine skill relocated from ~/.claude/rules by cognitive-economy E1; no opportunity detector exists for it yet"
description: "Use when reporting what a destructive or releasing action freed or changed (stopping processes, evicting a cache, deleting files, closing connections, sleeping agents), i.e. any 'freed N GB' style figure. Keep the estimate, the effect and the observation apart, attribute only to the cohort that succeeded by exact subject identity, treat a failed read as unknown rather than absence, prove the reading began after the effect, and keep measured zero apart from unmeasured. Core rule - a successful effect does not measure its own consequence."
---

# Post-Effect Resource Truth

A destructive or releasing action — stop a process, evict a cache, delete files, close
connections, sleep an agent — invites a closing number: "freed 1.2 GB". Three different
claims hide in that sentence, and they are routinely merged:

- **the estimate** — what the subjects appeared to cost before anyone acted;
- **the effect** — what the authority says it actually did, per subject;
- **the observation** — what a reading taken afterwards proved about those subjects.

Only the third may produce a "released" figure, and only under the conditions below.

## Rules

- **A successful effect does not measure its own consequence.** Never reuse the estimate as
  the result, and never derive bytes from a success count.
- **Attribute to the cohort that actually succeeded,** by exact subject identity carried
  from the baseline (pids, object ids, paths) — never the requested set, never an
  aggregate delta. An aggregate moves for reasons that are not yours.
- **Absence counts only under a usable observation.** A failed read that returns an empty
  set is not "everything is gone" (see U-33). Give the observation an explicit outcome.
- **Presence after the effect is unknown, not "still ours".** A listed identifier may be a
  lingering subject or a reused number. Count neither way; report it separately.
- **The reading must provably begin after the effect.** Beware merged in-flight reads and
  timestamps stamped at completion: both can hand you a pre-effect table dressed as a
  post-effect one. Prove "request after effect" by control flow, and judge any remaining
  ordering on one clock. Two processes' wall clocks are not an ordering instrument at
  millisecond scale.
- **Compare like with like:** same metric, same host authority. A mismatch is a refusal
  with a reason, not a conversion.
- **Measured zero is a result; unmeasured is not.** Keep them apart in the type and in the
  copy, and name what could not be measured.
- **Show the effect first and the measurement separately.** A failed measurement must never
  read as a failed effect, and an effect failure must never hide behind "not measured".
- **One bounded observation per action.** No polling until the number looks good, no
  per-subject timer.

## Proving it

- Drive the refusals with unit cases: failed read, unavailable read, early read, metric
  change, no baseline, nothing succeeded, partial batch, lingering identifier, measured zero.
- **In the end-to-end test, observe the decider at its boundary.** On the happy path the
  estimate and a real observation produce the same number, so the number alone cannot prove
  the observation ran. Wrap the real handler, count the calls, tie every displayed number to
  its answer, and add a fault mode where the real handler answers "failed". A build that
  fakes the figure must go red on the call count.

## Source

Incident evidence moved to `~/.claude/knowledge_vault/rules-evidence/post-effect-resource-truth.md` (2026-09-28) so it is not re-read on every call. The rule text above is unchanged.
