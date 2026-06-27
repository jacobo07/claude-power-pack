# Session Resilience OS — Dataset 05 — Recovery Telemetry & Diagnostics Layer (RTDL)

**Family:** Session Resilience OS (Path A, residual-gap family)
**Gap closed:** G5 — a unified recovery observability surface (today scattered across OOM
incident records, crash-replay logs and the stability score)
**Depends on:** RAM Stewardship OS (pp_dataset XII, OOM incident/autopsy), Resilient Workbench
OS (pp_dataset XIV, crash replay log + stability score), Recovery Acceptance Framework
(Dataset 04), Multi-Window Coordinator (Dataset 02), Secret Firewall / Universal Redaction Bus
(HR-SECRET family)
**Does NOT duplicate:** the *recording* of OOM incidents (RS-OS) or crash-replay events
(RW-OS) — RTDL *aggregates, correlates and presents* what those systems already record

---

## 1. System name and exact purpose

The Recovery Telemetry & Diagnostics Layer is the observability surface for the entire Session
Resilience OS. The PP already *records* recovery-relevant facts in scattered places: RS-OS
writes OOM incident records and autopsies, RW-OS writes a crash-replay log and computes a
stability score, CETTG writes completion reports, and the new acceptance framework writes
scorecards. What does not exist is a single layer that *collects* these streams, *aggregates*
them into the metrics that answer operational questions — how often do recoveries succeed, how
long do they take, which elements fail most, is recovery getting worse over time — and
*diagnoses* why a given recovery failed or degraded. Today, after a bad recovery, the evidence
is real but dispersed; nobody can ask "show me recovery health" and get an answer.

RTDL exists to be that answer. Its purpose is to give the family a memory and a mirror: to
collect every recovery lifecycle event from every contributing system, turn the raw stream
into meaningful metrics and trends, correlate a failure back to its root cause across the
scattered records, present a unified health view to the Owner, and do all of this without ever
leaking a secret. It is what makes the family *improvable* — without telemetry, the headline
property cannot be measured over time, only hoped for.

## 2. Fundamental property guaranteed

Every recovery the system performs is observable after the fact: its lifecycle, its outcome,
its timing, its failed elements and its probable root cause are recorded, aggregated and
retrievable through one surface. No recovery happens "in the dark". The guarantee is twofold —
completeness (every contributing system's recovery events reach the layer) and safety (nothing
the layer collects, stores or presents contains a raw secret; all egress passes through
redaction). Recovery health is therefore always knowable and always safe to look at.

## 3. Contracts offered to consumers

- **Collection contract.** Any recovery lifecycle event emitted by a contributing system is
  reliably ingested; a contributor that emits an event can trust it lands in the layer.
- **Aggregation contract.** The layer exposes the operational metrics — success/acceptance
  rate, time-to-recover, time-to-accept, count and identity of failed elements, recovery
  volume — derived consistently from the event stream.
- **Diagnosis contract.** For a failed or degraded recovery, the layer can produce a root-cause
  analysis that links the outcome to the contributing records (which OOM incident, which replay
  timeline, which acceptance dimension failed).
- **Observatory contract.** A single unified view presents current recovery health across all
  windows and sessions, with enough signal for the Owner to know whether the system is healthy
  without reading raw logs.
- **Trend contract.** The layer detects degradation trends and predictive warnings (recovery
  times creeping up, acceptance rate slipping) and surfaces them before they become incidents.
- **Redaction contract.** Every record stored and every view presented is secret-safe by
  construction; the layer adds a redaction stage on all egress and never persists raw captured
  text, consistent with HR-SECRET-002 and HR-SECRET-006.

## 4. Responsibilities — what it does and what it does NOT do

RTDL **does**: ingest recovery lifecycle events from RS-OS, RW-OS, CETTG, MWC and RAF;
aggregate them into recovery metrics; correlate a given recovery's events across the scattered
source records into one timeline; diagnose probable root cause for failures and degradations;
present a unified recovery-health observatory; detect anomalies and degradation trends; and
route every stored record and presented view through redaction.

RTDL **does NOT**: *cause* recovery actions or retries (it observes; the orchestrator and
RW-OS act); *decide* acceptance (RAF does — RTDL records RAF's verdicts); *record the primary
incident* (RS-OS owns OOM incidents, RW-OS owns crash-replay — RTDL aggregates them, it does
not replace them); *capture or store session state* (the capture systems and ISVE do); or
rotate/alter secrets (per HR-SECRET-003, secret handling is recommend-and-wait, Owner-decided).
It is strictly a read-aggregate-present-diagnose concern, deliberately powerless to act so that
observability can never itself become a source of risk.

## 5. Relationships with existing PP systems

- **RS-OS (pp_dataset XII).** RTDL ingests OOM incident records and autopsies as inputs to its
  metrics and diagnostics, rather than re-deriving OOM facts. RS-OS detects and records; RTDL
  aggregates and correlates.
- **RW-OS (pp_dataset XIV).** RTDL consumes the crash-replay log and stability score; the replay
  timeline is its primary correlation substrate for "what happened during this recovery".
- **Recovery Acceptance Framework (Dataset 04).** RTDL ingests RAF scorecards and verdicts; it
  computes the acceptance-rate and time-to-accept metrics RAF's benchmark engine and regression
  sentinel depend on — a deliberate two-way loop where RAF judges and RTDL remembers.
- **Multi-Window Coordinator (Dataset 02) / CETTG / Dataset 01 / ISVE.** Each emits lifecycle
  events (window restored/blocked, pane restored, version promoted, chain repaired) that RTDL
  collects, giving cross-system visibility into one recovery.
- **Secret Firewall / Universal Redaction Bus (HR-SECRET family, modules/secret_firewall).**
  RTDL's redaction contract is implemented by routing all egress through the existing URB, not a
  new redactor — reuse, not reinvention.
- **TCO / TIS observability (CLAUDE.md cost discipline).** RTDL is the recovery-domain sibling of
  the cost-telemetry surface; it follows the same "observe, summarize, never noise" posture.

## 6. Entities that compose the system

### 6.1 Recovery Event Collector
Purpose: ingest recovery lifecycle events from every contributing system. Inputs: events such as
crash-detected, recovery-started, window-restored, pane-restored, version-selected, acceptance-
scored, recovery-completed, recovery-failed. Outputs: a unified, ordered event stream. Behaviour:
accepts events from heterogeneous sources, normalizes them to a common shape, and timestamps
them on a shared timeline. Success: every emitted event is ingested exactly once. Failure: a
malformed event is quarantined for diagnosis, never silently dropped and never allowed to
corrupt the stream. Evolution: new event types from new systems are absorbed without schema
breakage.

### 6.2 Recovery Metrics Aggregator
Purpose: turn the event stream into operational metrics. Inputs: the collected stream. Outputs:
acceptance rate, time-to-recover, time-to-accept, failed-element counts and identities, recovery
volume, per-window and per-session breakdowns. Behaviour: derives metrics consistently so the
same stream always yields the same numbers; feeds RAF's benchmark engine. Success: a question
about recovery health has a single authoritative numeric answer. Failure: insufficient data
yields explicitly provisional metrics, never confident numbers on thin evidence. Evolution:
richer dimensional slicing.

### 6.3 Root-Cause Diagnostics Engine
Purpose: explain why a recovery failed or degraded. Inputs: a recovery's correlated timeline
plus the contributing records (OOM incident, replay, acceptance scorecard). Outputs: a probable
root cause with supporting evidence. Behaviour: traces an unaccepted dimension back through the
timeline to its likely origin (e.g., a missing window caused by an unresolved workspace path; a
degraded editor surface caused by an unrestorable host property). Success: a failed recovery
gets an actionable cause, not just a symptom. Failure: when cause is genuinely undetermined it
says so, listing candidates, never inventing a cause. Evolution: pattern-library-driven
diagnosis that improves as incidents accrue.

### 6.4 Recovery Health Observatory
Purpose: present a single unified view of recovery health across all windows and sessions.
Inputs: aggregated metrics and recent diagnostics. Outputs: a concise health surface (overall
status, recent recoveries, current trends, open failures). Behaviour: follows the "no noise"
posture — quiet when healthy, informative when not. Success: the Owner can judge recovery health
at a glance. Failure: missing data is shown as unknown, not as green. Evolution: surfaced
interactively through the PP Sessions extension.

### 6.5 Telemetry Redaction Bus
Purpose: guarantee secret-safety of everything stored and shown. Inputs: every record bound for
persistence or presentation. Outputs: redacted, safe-to-store, safe-to-show records. Behaviour:
routes all egress through the existing Universal Redaction Bus; never persists raw captured text;
treats diagnostic payloads as secret-bearing until redacted (the RS-OS "memory dumps are
secret-bearing" doctrine applied to telemetry). Success: no stored or presented record contains a
raw secret. Failure: a record that cannot be safely redacted is withheld, not stored partially.
Evolution: tracks new secret patterns as the firewall's catalog grows.

### 6.6 Anomaly & Trend Detector
Purpose: detect degradation trends and predictive warnings. Inputs: metric time series. Outputs:
trend signals and early warnings (rising recovery time, slipping acceptance, a window that fails
repeatedly). Behaviour: smooths noise before alerting; distinguishes a one-off from a trend.
Success: degradation is caught before it becomes the Owner's lived experience, feeding RAF's
regression sentinel. Failure: a transient blip does not raise a false alarm. Evolution:
predictive models estimating recovery risk before a crash.

### 6.7 Diagnostics Correlation Engine
Purpose: stitch one recovery's evidence together across the scattered source records. Inputs:
the event stream plus the source records (OOM incident, crash-replay, acceptance scorecard,
window/pane events). Outputs: a single correlated recovery timeline. Behaviour: joins records on
shared recovery and window/session identity so a human or the diagnostics engine sees one story
instead of four logs. Success: any recovery can be reconstructed as one coherent timeline.
Failure: an unjoinable record is attached as orphaned-with-reason rather than discarded.
Evolution: deeper joins as more systems emit correlatable identity.

## 7. Completion criteria for the system

RTDL is complete when: every contributing system's recovery events are reliably ingested and
normalized onto one timeline; metrics (acceptance rate, time-to-recover/accept, failed-element
counts, volume) are consistently derived and feed RAF's benchmarks; a failed recovery can be
diagnosed to a probable, evidence-backed root cause; a single unified health observatory
presents recovery health quietly-when-healthy; degradation trends and early warnings are
detected and feed the regression sentinel; and every stored record and presented view is
secret-safe by construction. A layer that shows metrics but cannot correlate a failure to its
cause, or that ever stores a raw secret, is incomplete.

## 8. Dependencies

RTDL requires: recovery lifecycle events from RS-OS, RW-OS, CETTG, MWC, ISVE and RAF; the
existing OOM-incident and crash-replay records as correlation substrate; the Universal Redaction
Bus for safe egress; and a durable, size-bounded storage substrate (honouring the RS-OS
"evidence must be size-limited and summarized" rule). It is purely downstream — it depends on
others to act and emit, and never acts itself.

## 9. Explicit anti-patterns

RTDL must never: cause or retry a recovery (it only observes); store or present a raw secret
(all egress is redacted, diagnostics are secret-bearing until proven safe); re-record primary
incidents that RS-OS/RW-OS already own (it aggregates, it does not duplicate the source of
truth); drop a malformed or unjoinable event silently (quarantine and report instead); raise
alarms on transient blips (smooth before alerting); grow storage unbounded (evidence must be
summarized and size-limited); or present missing data as healthy (unknown is not green). It must
also never become a side channel that leaks via "diagnostics" what the firewall blocks
elsewhere — the redaction contract is absolute.

## 10. Future evolution

RTDL evolves from after-the-fact observability toward predictive recovery health — estimating,
from resource and stability trends, the probability that the next interruption will recover
cleanly, and warning early enough to checkpoint or stabilize first. Its diagnostics engine
matures from heuristic tracing toward a growing pattern library that names recurring failure
modes and proposes structural fixes (feeding the Bug→Hard-Rule pipeline). Its observatory
becomes an interactive surface in the PP Sessions extension. As the metrics and benchmarks
accumulate across many real recoveries, RTDL becomes the evidence base that proves — release
over release — that the Session Resilience OS is holding its headline promise: that an OOM crash
and a Reload Window remain, measurably and durably, indistinguishable.
