---
title: UCEIMR Sprint 2 — expansion attempt and gap discovery
date: 2026-08-04
status: STOP #2 — BLOCKING, presented inline, no dataset written
verdict: 0 expansion slots mechanically derivable; 5 narrow mechanisms found, none a dataset
covers: [uceimr, expansion, gap_discovery, stop2]
---

# UCEIMR Sprint 2 — expansion attempt and gap discovery

## 1. The expansion machinery was run, and it refused

The Sprint-2 premise was "15 proposed − 2 genuine = 13 free slots; fill them".
That arithmetic was not adopted on faith — the shipped `compute_expansion()` was
driven with the real 15-item UCEIMR family:

```
proposed=15  keep=1  fold=0  defer=14  recommended=1
expansion_slots = 15 − 1 − 14 = 0     overlap = 0%     applies = False
menu = A, B, E     (C and D correctly withheld)
```

**14 of 15 items came back DEFER, not FOLD.** d2a's plausibility floor capped each at
45 %: a parent's vocabulary matched but precision was too low to name it. The engine
subtracts DEFER from the slot count by design, because a deferred item is *unknown*
ownership, not vacated space — counting it would over-claim the room.

So there are no 13 mechanically-derived slots. The premise is falsified by the very
mechanism the sprint specified for it. This is the engine behaving correctly:
`V-D2A-FAMILY-DEFER-NOT-KEEP` exists precisely so a 45 %-capped item is never reported
as genuinely new.

Note the asymmetry with the Phase-1 audit: **I** could name parents for those 15 items by
opening incumbents; the keyword engine could not. Both results are honest at their own
resolution, and the engine is right to refuse to convert its own uncertainty into slots.

## 2. Gap discovery — the ten spaces, swept from disk

| Space | Measured | Disposition |
|---|---|---|
| Open STOP #1 queue | **15** plan files carry `status: STOP #1`; oldest 9 days; none transitions | **G1 — real** |
| Liveness offenders | **1** (`dataset_first/transduction`) — not 337; that number was a gate-unpack bug, now fixed | closed this session |
| `retirement_condition` evaluability | 5 UNEVALUABLE · 2 ACTIVE · 2 NEVER | **G2 — real (probe coverage)** |
| Rule enforcement evidence | `effects.json` measures **3** rule effects against 156 compiled rules | **G3 — real (coverage)** |
| Decision records | `vault/decision_review/` **does not exist**; `accountability.py` has no producer | **G4 — real**, already in OWNER_QUEUE (SEIP D4) |
| Authored-corpus persistence | `enricher.py` fetches transcripts at runtime and never writes them; AKOS keeps ~220-char leads | **G5 — real**, exposed by R1 |
| Session Delta | wired — `hook-dispatcher.js` + `session_delta_stop.js` | not a gap |
| Outputs without consumer | `vault/OWNER_QUEUE.md` exists (40 KB); no `ESCALATED.md` | folded into G1 |
| Cross-project emergence | IAS-D2 owns cross-project immunity by name | owned |
| Epistemic debt registry | ACIS E0 (unfalsified intuition) + `frontier_intelligence` | owned |

## 3. Novelty gate — applied to the five survivors

All five were run against the 13 questions. **None answers Q4** ("why is extending an
existing owner insufficient") or Q5 ("what new primitive does it require"):

- **G1** extends `backlog_autopilot` + `OWNER_QUEUE` — a status-transition producer and a
  scanner over front matter. One module.
- **G2** extends `retirement.PROBES` — more probe functions on a registry shipped today.
- **G3** extends `rule_compiler/effect_harness.py` — coverage, not mechanism.
- **G4** extends `decision_review/accountability.py` — a producer for an existing consumer,
  the sealed `feedback_orphan_field_dead_recovery_path` shape.
- **G5** extends `autoresearch/enricher.py` — persist what it already fetches.

**Result: 0 of 13 slots filled with a dataset. 5 narrow mechanisms, every one an EXTEND on
a named living owner, each on the order of tens-to-hundreds of lines.**

Honouring the sprint's own instruction — "better 5 genuine than 13 artificial" — the honest
count is 5 genuine *extensions* and 0 genuine *datasets*.

## 4. Why this is the expected result, not a failure

The base rate across thirteen audits is that proposals measure majority-owned. An
expansion pass over an estate this dense finds adjacency, not territory. The one thing
that would change the answer is new *evidence*, which is exactly what G5 unblocks: the
estate cannot mine capabilities from a corpus it never wrote down.

## 5. Standing obligations honoured

- Denominator discovered from disk (`PR-COVERAGE-BY-CONSTRUCTION-001`); the STOP #1 count
  came back 15 against a remembered 5.
- No padding to reach 13 (`no-silent-caps`).
- Every gap re-tested against its nearest incumbent before being called a gap
  (`T-OWNERSHIP-AUDIT-ABSORPTION-BIAS-001`).

## 6. Blocking condition

No dataset content is written until the Owner selects from the inline STOP #2 options.
