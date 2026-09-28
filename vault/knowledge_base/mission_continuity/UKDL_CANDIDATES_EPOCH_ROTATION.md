---
title: Hard-rule candidates + baseline classification -- turn continuation vs context rotation
date: 2026-09-28
status: CANDIDATES -- NOT promoted; the Owner (or a second occurrence) promotes
evidence: vault/lessons/turn-end-is-not-context-rotation.md; vault/lessons/retired-stage-starves-live-supervisor.md;
  commits 5eee90a 717554f dce125b add6828 5bf5729; traps/process rules already filed as T-CONT-21..24, PR-CONT-11..12 (1c981fd)
sibling: UKDL_CANDIDATES_DURABLE_SUBSTRATE.md (pane e9) -- owners cited below are not re-drafted
---

# 1. Ownership sweep (before drafting)
ukdl-universal.md searched for synthetic proof/relay/evidence, historical residue, hot path, cold
state, supervisor liveness, pass contract, self-certification: owners found only for
self-certification (`PR-NO-SELF-CERTIFICATION-001`) and, in the sibling file, the scheduled-job pass
contract (`PR-CAND-A-SCHEDULED-JOB-OWNS-ITS-PASS-CONTRACT`) and measured-progress relays
(`PR-CAND-RELAY-AND-RENEWAL-REQUIRE-MEASURED-PROGRESS`). Provider-quota churn is owned by
`T-A-QUOTA-REFUSAL-IS-NOT-A-FINISHED-EPOCH-001` + `30ccdeb`. None of those is re-drafted here.

# 2. Hard-rule candidates

## HR-CAND-RESTART-CAUSES-NEVER-SHARE-A-CERTIFICATION
Turn continuation, context rotation, recovery and retry are different lifecycle events. A claim
about one of them may be certified only by evidence specific to it (a recorded cause plus the
witnesses that event leaves), never by a count of restarts. Evidence: 499 fresh launches read as
"rotations proven in production"; 434 were turn ends (census 2026-09-28). Irreversible cost: a
false durability claim ships long-run infrastructure on the strength of the wrong event. #CROSS-PROJECT

## HR-CAND-CONTROL-PLANE-COST-INDEPENDENT-OF-HISTORY
A recurring control-plane pass must not cost in proportion to unbounded historical residue
(completed runs, their markers, their logs). Evidence: 403 leftover markers x > 45 s per query under
starvation made one supervisor pass outlive the schedule; seven piled up and a 24 h budget ran 46 h
(`9f750fa`). Distinct from the sibling's pass contract, which bounds a pass in TIME; this bounds the
pass's WORK by the live population, not the historical one. #CROSS-PROJECT

## HR-CAND-SYNTHETIC-TRANSITION-IS-NOT-PRODUCTION-PROOF
A synthetic run proves a mechanism's transport; it says nothing about how often production takes
that transition or why. A "production verified" claim needs the transition observed in a real run
and attributed by cause. Evidence: one W8 synthetic relay (2026-09-24) underwrote the claim
"rotation production-proven"; the census found the production counts were a different event.
Sibling of PR-NO-SELF-CERTIFICATION-001 (producer vs claim), not a duplicate of it (synthetic vs real).

# 3. Constitutive Baseline Ratchet / UCR-CIF classification

| candidate standard | reuse multiplier | evidence tier | classification |
|---|---|---|---|
| long-running work separates logical run / session / context epoch / turn | every agent runtime | one repo, one host, measured | CPP-wide candidate |
| every restart of a unit of work records its cause at decision time | every supervisor | implemented + 71 gates + live cause rows | CPP-wide candidate |
| a turn end continues the same context when the host allows it | agent runtimes with resume | host-verified, economics measured | local baseline (cpp-gsd-long) |
| background children survive (or hold) a parent's turnover | agent runtimes | implemented, real-transcript validated | local baseline |
| control-plane hot path independent of historical residue | every scheduler | one incident + fix | cross-project candidate (HR candidate above) |
| rotation priced before chosen (floor vs continuation cost) | agent runtimes | 2 probes + 1 autopsy | local baseline |

Nothing here is a promoted Constitutive Baseline. Promotion needs a second repository or the
Owner; higher reuse multiplier -> higher burden, so the two CPP-wide rows need the live
multi-rotation proof (spec §5, S10) before they are even proposed.
