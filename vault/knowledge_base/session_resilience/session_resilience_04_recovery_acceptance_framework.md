# Session Resilience OS — Dataset 04 — Recovery Acceptance Framework (RAF)

**Family:** Session Resilience OS (Path A, residual-gap family)
**Gap closed:** G4 — a system-level "was this recovery actually successful?" contract,
above the existing per-pane verification
**Depends on:** Crash-to-Exact-Terminal-Topology Guarantee (pp_dataset XI / CETTG, esp. pane
restore verification §223 and completion report §220), Resilient Workbench OS (pp_dataset XIV,
stability score), UI / Editor State Persistence Layer (Dataset 01), Multi-Window Coordinator
(Dataset 02), Incremental Snapshot & Session Versioning Engine (Dataset 03)
**Does NOT duplicate:** per-pane restore verification (CETTG §223), workspace stability score
(RW-OS §295) — RAF *consumes and composes* these into a session-level verdict

---

## 1. System name and exact purpose

The Recovery Acceptance Framework is the system that decides, at the level of the **whole
session**, whether a recovery is *accepted* — whether the restored state is genuinely
equivalent to what existed before the crash. The PP already verifies recovery in pieces: CETTG
checks each restored pane (cwd, conversation, heartbeat), and RW-OS computes a workspace
stability score. What is missing is the unifying judgment that turns these fragments into a
single, defensible answer to the Owner's actual question: *"Is my session back, or only
partly back?"* Without it, recovery can report ten green panes and still leave the Owner with
a session that feels wrong — a missing window, a lost editor layout, the foreground in the
wrong place — because nothing measured the *whole* against the *before*.

RAF exists to be that judgment. Its purpose is to define, in one authoritative place, what
"recovered" means for an entire session; to score an actual recovery against that definition;
to render the verdict that gates the "recovery complete" claim; and to hold the equivalence
standard that the family's fundamental property — *post-OOM state == post-Reload-Window state*
— is measured against. It is the acceptance gate of the entire Session Resilience OS.

## 2. Fundamental property guaranteed

No recovery is ever declared complete unless it has been scored against the canonical
acceptance criteria and met the threshold those criteria define. The framework guarantees that
the family's headline property — that a crash recovery is indistinguishable from a Reload
Window — is not an aspiration asserted by hope but a measured verdict: every "recovered" claim
carries a scorecard naming what was checked, what matched the pre-crash version, and what did
not. A recovery that is partial is *named* partial, with each missing or degraded element
enumerated; it is never rounded up to "complete".

## 3. Contracts offered to consumers

- **Definition contract.** RAF is the single source of truth for what counts as a recovered
  session; all consumers defer to its criteria rather than inventing local notions of success.
- **Scoring contract.** Given a recovery and the version it was restored from, RAF produces a
  deterministic scorecard: per-dimension match/mismatch and an overall verdict
  (accepted / partial / failed).
- **Gate contract.** The "recovery complete" claim is *blocked* until RAF returns accepted;
  consumers may not self-declare completion. A partial or failed verdict surfaces the exact
  gaps and the recommended next action (auto-retry of a sub-element, or manual instruction).
- **Equivalence contract.** RAF holds the operational definition of "indistinguishable from a
  Reload Window" and judges each recovery against it, so the family's headline property is
  testable and not merely declared.
- **Benchmark contract.** RAF maintains baseline expectations (how long a clean recovery
  should take, what fidelity it should reach) so a recovery can be judged not only correct but
  *acceptably good*, and so regressions are detectable across releases.
- **Honesty contract.** RAF never manufactures a passing verdict; a clean failure to recover is
  reported as failed, consistent with the Reality Contract and the "no classified FAILs" rule.

## 4. Responsibilities — what it does and what it does NOT do

RAF **does**: hold the canonical acceptance criteria for a recovered session; score an actual
post-recovery state against the version it was restored from, dimension by dimension (terminal
topology, editor surface, window census, focus, conversation mapping); classify the result as
accepted, partial or failed with per-element detail; act as the gate that blocks a "complete"
claim until acceptance; maintain recovery benchmarks (time, fidelity, completeness baselines);
operate the equivalence oracle that judges crash-recovery-vs-Reload-Window indistinguishability;
and detect acceptance regressions over time.

RAF **does NOT**: capture state (capture systems do); store history (ISVE does); *perform* the
recovery or the retries (the recovery orchestrator and RW-OS retry/queue do — RAF *tells* them
what is still unaccepted, then they act); verify a *single pane* in isolation (CETTG §223 does
that, and RAF consumes its result); or govern resources. RAF is a judge and a gate, not an
actor — it measures and decides, then hands the decision to the systems that act.

## 5. Relationships with existing PP systems

- **CETTG (pp_dataset XI).** RAF consumes CETTG's per-pane verification results and completion
  report as inputs to the terminal-topology dimension of its scorecard, rather than re-checking
  panes itself. CETTG answers "is this pane restored?"; RAF answers "is the *session* restored?"
- **RW-OS (pp_dataset XIV).** RAF consumes the workspace stability score as a health input and
  feeds its acceptance verdict back into RW-OS's recovery-loop prevention: a failed dimension
  becomes a bounded retry target, and repeated acceptance failure triggers RW-OS's degrade-to-
  manual rule rather than an infinite retry.
- **Dataset 01 / 02 / 03.** RAF scores the editor-surface dimension against the Dataset 01
  description, the window-census dimension against the Dataset 02 topology, and uses the exact
  version reconstructed by ISVE (Dataset 03) as its *reference* — the thing the recovery is
  scored *against*.
- **Recovery Telemetry & Diagnostics (Dataset 05).** RAF emits scorecards and verdicts into the
  telemetry layer, which aggregates acceptance rate and time-to-accept and drives regression
  alerts.
- **Reality Contract / OQS / governance (CLAUDE.md).** RAF's honesty contract is a direct
  application of the Reality Contract and the "DONE = observed evidence" doctrine — a recovery
  is done when *observed* accepted, never when merely attempted.

## 6. Entities that compose the system

### 6.1 Acceptance Criteria Registry
Purpose: hold the canonical rules defining a recovered session. Inputs: the dimensions that
matter (pane topology, editor surface, window census, focus, conversation mapping, locks) and
their required match levels. Outputs: the authoritative criteria set. Behaviour: criteria are
explicit and versioned so "what counts as recovered" cannot drift silently. Success: every
dimension the Owner would perceive is covered by a criterion. Failure: an uncovered dimension
is a registry gap to be filled, not silently excused. Evolution: criteria tighten as fidelity
systems improve.

### 6.2 Recovery Scorecard Engine
Purpose: score an actual recovery against the reference version. Inputs: the post-recovery
state, the reference version reconstructed by ISVE, and the criteria registry. Outputs: a
per-dimension match/mismatch scorecard with detail. Behaviour: deterministic — the same inputs
yield the same scorecard. Success: each dimension is scored with evidence. Failure: a dimension
that cannot be measured is scored as unknown-with-reason, never assumed passing. Evolution:
finer-grained sub-dimension scoring.

### 6.3 Equivalence Oracle
Purpose: judge whether the recovered session is indistinguishable from a Reload Window of the
same prior state — the family's headline property. Inputs: the scorecard plus the equivalence
definition. Outputs: an equivalence verdict. Behaviour: equivalence requires that every
Owner-perceptible dimension matches to its required level; the oracle is the operational
embodiment of the acceptance criterion. Success: a true Reload-Window-equivalent recovery
passes. Failure: any perceptible mismatch fails equivalence, with the specific difference named.
Evolution: the equivalence definition expands as new perceptible dimensions are captured.

### 6.4 Partial-Recovery Classifier
Purpose: turn a non-perfect scorecard into a precise partial/failed verdict with an element
list. Inputs: the scorecard. Outputs: a classification (accepted / partial / failed) and, for
partial/failed, the enumerated missing or degraded elements with each one's recommended
remedy. Behaviour: mirrors CETTG's no-loss accounting — every shortfall is named, never summed
away. Success: the Owner sees exactly what is and is not back. Failure: an unclassifiable
result defaults to failed (safe) and is reported. Evolution: remedy recommendations grow more
specific.

### 6.5 Acceptance Gate
Purpose: block the "recovery complete" claim until acceptance is reached. Inputs: the verdict.
Outputs: a gate decision (allow-complete / hold-with-gaps). Behaviour: only an accepted verdict
permits a completion claim; partial/failed holds it open and routes the gaps to the actors.
Success: no "complete" is ever emitted on an unaccepted recovery. Failure: if the gate cannot
evaluate, it holds (fails safe) rather than allowing. Evolution: integrates with output-
contract / OQS gating so completion claims are uniformly enforced.

### 6.6 Recovery Benchmark Engine
Purpose: hold baseline expectations for recovery quality — how long a clean recovery should
take and what fidelity it should reach. Inputs: historical accepted recoveries (via telemetry).
Outputs: baselines per dimension and overall. Behaviour: lets a recovery be judged not only
correct but acceptably fast and complete. Success: a recovery within baseline is "good"; one
far outside is flagged even if eventually accepted. Failure: insufficient history yields a
provisional baseline, marked provisional. Evolution: per-host, per-arrangement baselines.

### 6.7 Regression Sentinel
Purpose: detect when acceptance degrades across releases. Inputs: acceptance rate, time-to-
accept and fidelity trends from telemetry. Outputs: regression alerts. Behaviour: compares
current acceptance against the established benchmark and recent history; raises an alert when a
release lowers acceptance. Success: a recovery regression is caught before it becomes the
Owner's lived experience. Failure: noisy trends are smoothed before alerting to avoid false
alarms. Evolution: ties regressions to specific changed components via diagnostics correlation.

## 7. Completion criteria for the system

RAF is complete when: a canonical, versioned criteria registry covers every Owner-perceptible
recovery dimension; the scorecard engine deterministically scores a recovery against the exact
ISVE reference version; the equivalence oracle renders a Reload-Window-equivalence verdict; the
partial classifier enumerates every shortfall with a remedy; the acceptance gate provably
blocks "complete" on anything less than accepted and fails safe; benchmarks exist so quality
(not just correctness) is judged; and regressions across releases are detected. A framework
that scores recoveries but does not *gate* the completion claim, or that rounds partial up to
complete, is incomplete and self-defeating.

## 8. Dependencies

RAF requires: CETTG per-pane verification results; RW-OS stability score and retry/loop
machinery; Dataset 01/02 descriptions as the editor/window dimensions; the exact ISVE
reference version as the scoring baseline; and the telemetry layer (Dataset 05) for benchmark
history and regression input. It does not perform recovery and so depends on the orchestrator
and RW-OS to act on its verdicts.

## 9. Explicit anti-patterns

RAF must never: declare a recovery complete without scoring it; manufacture a passing verdict to
satisfy a flow (a direct Reality-Contract violation and the "no classified FAILs" antipattern);
round a partial recovery up to complete; re-verify individual panes itself instead of consuming
CETTG's results; perform retries or recovery actions (it judges, it does not act); allow the
acceptance gate to fail *open* (it must fail safe / held); or let acceptance criteria drift
silently without versioning. It must also never treat "all panes green" as session acceptance —
a session is more than its panes, which is the entire reason RAF exists.

## 10. Future evolution

A distinct evolution axis is **capability-aware acceptance**. Not every host version can
restore every captured property — some editors cannot reposition a panel, some cannot restore
a selection. A naive equivalence oracle would mark such recoveries as perpetual failures even
when they recovered everything the host *can* recover. RAF therefore evolves to consult a
per-host capability registry (shared with the UI / Editor State Persistence Layer's
unrestorable-marking contract) so that acceptance is judged against *achievable* fidelity, not
absolute fidelity: a property the host provably cannot restore is excluded from the equivalence
denominator and reported as a known host limitation, while a property the host *could* restore
but did not remains a genuine failure. This keeps the acceptance verdict honest in both
directions — it never excuses a real miss, and it never punishes a recovery for a host
limitation outside the system's control.

RAF evolves from a fixed criteria set toward Owner-tunable acceptance profiles (a "fast,
good-enough" recovery for quick restarts versus a "pixel-exact, full-fidelity" recovery after a
real crash), from coarse accepted/partial/failed verdicts toward graded fidelity scores per
dimension, and from reactive scoring toward predictive acceptance — estimating, before restore
even begins, whether the available version can reach acceptance, so the orchestrator can choose
a better version or warn the Owner early. As the equivalence oracle's perceptible-dimension set
grows to match everything the capture systems record, RAF becomes the formal, measurable proof
of the Session Resilience OS's headline promise: that after any crash, the Owner cannot tell it
apart from a Reload Window — because the framework checked, and said so.
