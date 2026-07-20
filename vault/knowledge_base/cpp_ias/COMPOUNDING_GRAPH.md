# CPP-IAS — COMPOUNDING GRAPH

> How the 14 datasets make each other — and the whole estate — more valuable. The corpus is
> not 14 systems; it is one loop where each node's output raises another node's input.
> Directional: `A → B` means A's output improves B's function.

## The primary loop (the ensemble's circulatory system)

```
IAS-E1 Observability Fabric
   │  reveals which systems are used / dead / dark, and real flow + bottlenecks
   ▼
IAS-C1 Capability Portfolio ──────────────────────────────────┐
   │  uses usage+ROI data to allocate cognitive capital        │
   ▼                                                           │
IAS-A1 Capability Router                                       │
   │  allocation informs which systems a mission routes to     │
   ▼                                                           │
(mission executes across systems via IAS-A2 Control Bus)       │
   │  produces outcomes + events                               │
   ▼                                                           │
IAS-D1 System Ecology                                          │
   │  outcomes update fitness / symbiosis / parasitism         │
   ▼                                                           │
IAS-G1 Architecture Intelligence                               │
   │  fitness informs topology + complexity-budget decisions   │
   ▼                                                           │
IAS-C1 (allocation improves) ─────────────────────────────────┘
   the loop tightens: better observation → better allocation →
   better routing → better outcomes → better fitness → better
   architecture → better allocation.
```

## The amplification spine (intelligence compounding)

```
IAS-E1 usage data
   → IAS-B1 Cognitive Multiplier  (finds the highest-leverage change)
   → IAS-B2 Insight Synthesis     (cross-dataset insights feed new FD deposits / ACIS laws)
   → strengthens the whole estate's knowledge (FD, ACIS, hard_rules)
   → which raises the baseline every other IAS system reasons from
   → IAS-E1 observes the improvement → the spine compounds.
```

## The defense loop (immunity compounding)

```
IAS-A2 Control Bus  carries failure events
   → IAS-D2 Immune System  fingerprints + federates them cross-project
   → IAS-E2 Cognitive Reliability  turns recurring failures into SLOs + failure budgets
   → IAS-F3 Digital Twin  simulates the failure before it recurs
   → IAS-D2 immunizes exposed projects preventively
   → fewer recurrences → IAS-E1 observes lower failure flow → capacity freed for IAS-C1.
```

## The foresight loop (forecasting compounding)

```
IAS-E1 + IAS-D1 history
   → IAS-C2 Demand Forecasting  predicts next-needed capabilities
   → IAS-F3 Digital Twin  simulates whether building them pays off
   → IAS-C1 Portfolio  pre-allocates to the winners
   → IAS-A1 Router  finds them ready when the real mission arrives
   → outcome confirms/refutes the forecast → IAS-C2 recalibrates → tighter forecasts.
```

## Cross-dataset feedback edges (the "what feeds what" ledger)

| Producer | Signal | Consumer | Decision improved |
|---|---|---|---|
| IAS-E1 | usage / dead-capability / dark-matter | IAS-C1, IAS-D1, IAS-G1 | allocation, extinction, topology |
| IAS-F2 | fusion / advantage scores | IAS-C1, IAS-B1, IAS-D1 | portfolio ranking, leverage ranking, fitness |
| IAS-A2 | cross-system events | IAS-D2, IAS-E1, IAS-C2 | immunity, observation, demand signal |
| IAS-D1 | fitness / parasitism | IAS-G1, IAS-C1 | topology, retire-vs-invest |
| IAS-D2 | failure fingerprints | IAS-E2, IAS-F3 | SLO/budget, simulation |
| IAS-B1/B2 | leverage points / insights | FD, ACIS, hard_rules (estate) | knowledge baseline for all |
| IAS-C2 | demand forecast | IAS-F3, IAS-C1 | simulate-before-build, pre-allocate |
| IAS-F3 | simulated outcomes | DRK, one_shot, IAS-G1 | decision, mission plan, architecture |

## The compounding law
No IAS dataset is an island: each must declare, in its own text, **what it receives, what it
produces, who consumes it, what decision it improves, and which other IAS/estate system it makes
more valuable.** A dataset with no inbound and no outbound edge here is an orphan and is REJECTED —
it cannot be part of a compounding fabric if nothing compounds through it.

## The single sentence
> Observation feeds allocation; allocation feeds routing; routing feeds outcomes; outcomes feed
> ecology; ecology feeds architecture; architecture feeds allocation — and along the way,
> amplification raises the knowledge baseline, immunity lowers the failure baseline, and foresight
> pre-positions capability. The estate does not just run; it gets better at getting better.

## LOOP EVIDENCE — concrete cross-dataset scenarios

For each of the four loops, one worked scenario showing the sum of the datasets involved
producing an outcome none of them could produce alone. Sealed word/Part counts for the cited
datasets are in `BUILD_STATUS.md` and `QUALITY_REPORT.md`.

### Circulation loop — IAS-E1 → IAS-C1 → IAS-A1 → IAS-D1 → IAS-G1 → IAS-C1

Scenario: IAS-E1's Observability Fabric flags that a project's `secret_firewall` module has zero
invocations across three months of usage telemetry — dead capability, not a broken one. IAS-C1's
Capability Portfolio reads that signal and reallocates the cognitive-capital budget previously
reserved for `secret_firewall` maintenance toward a capability IAS-E1 also flagged as
over-subscribed (`hardrule_compile.py`, called on every deploy trigger). IAS-A1's Capability
Router picks up the updated allocation and stops routing new missions toward the dead capability,
routing them instead to the reinforced one. The next mission that touches deploy governance
executes faster and with fewer routing misses — an outcome that becomes an event on IAS-A2's
Control Bus. IAS-D1's System Ecology reads that outcome as a fitness signal: `secret_firewall`
now scores as a parasitic capability (consuming allocation slots, producing no usage), while
`hardrule_compile.py` scores as symbiotic. IAS-G1's Architecture Intelligence consumes the fitness
delta and proposes a topology change — collapse `secret_firewall` into `hardrule_compile.py`'s
call path rather than maintaining it as a standalone module — which flows back into IAS-C1 as a
revised allocation candidate. No single dataset could have produced the topology proposal:
IAS-E1 alone only has usage counts, IAS-C1 alone only has a budget, IAS-G1 alone has no fitness
signal to act on. The loop is what turns "zero invocations" into "collapse this module."

### Amplification spine — IAS-E1 → IAS-B1 → IAS-B2 → estate baseline (FD/ACIS/hard_rules) → IAS-E1

Scenario: IAS-E1's usage data shows that four unrelated projects each independently hit the same
PowerShell/Bash-bridge failure mode within a two-week window (the MSYS2 hang documented elsewhere
in this estate's `windows-execution-detail.md`). IAS-B1's Cognitive Multiplier scans that
recurrence and identifies it as the single highest-leverage fix available this cycle — one change
(the PowerShell-first router) would prevent all four recurrences rather than four separate patches.
IAS-B2's Insight Synthesis takes that leverage finding and cross-references it against the
`ACIS` epistemic ladder and `hard_rules` archive, confirming no existing Hard Rule already covers
the Windows-Bash-bridge case at the router level (only at the retry level). It deposits a new FD
candidate and proposes an HR promotion. Once the estate's `hard_rules` baseline absorbs the new
rule, every project's baseline reasoning improves — not just the four that surfaced the bug.
IAS-E1 then observes the downstream effect: the failure-mode's recurrence rate across the whole
estate drops toward zero in the following observation window, which IAS-B1 reads as confirmation
the leverage call was correct. IAS-E1 alone would have kept logging the same four recurrences
forever; IAS-B1 alone has no mechanism to write to the estate's knowledge baseline; IAS-B2 alone
has no usage signal to know which insight is worth promoting. Only the three-dataset chain
compounds observation into a permanent baseline lift.

### Defense loop — IAS-A2 → IAS-D2 → IAS-E2 → IAS-F3 → IAS-D2 → IAS-E1 → IAS-C1

Scenario: A deploy-time crash event crosses IAS-A2's Control Bus from one project. IAS-D2's
Immune System fingerprints the failure (null-pointer on a missing config key under load) and
checks whether the same fingerprint has federated in from any other project — it has not, so this
is a first occurrence, but IAS-D2 still registers the fingerprint estate-wide as a preventive
signature. IAS-E2's Cognitive Reliability Engineering converts the fingerprint into a concrete
SLO: "config-key presence must be validated before the deploy substrate is written," backed by an
explicit failure budget. IAS-F3's Digital Twin then simulates that same failure class against
every OTHER live project's config schema before any of them hits it for real — the simulation
finds two more projects with the identical missing-key exposure. IAS-D2 immunizes both
preemptively (adds the null-guard per Ley 24) rather than waiting for a second live crash. IAS-E1
observes the resulting drop in deploy-crash volume across the estate in the next reporting window,
and that freed observability capacity (fewer incidents to triage) becomes capital IAS-C1 can
reallocate to new capability-building rather than firefighting. No dataset in isolation prevents
the second and third crash: IAS-A2 only carries the event, IAS-D2 only fingerprints what it has
already seen, IAS-F3 is the piece that turns "fingerprint of one" into "prevention across three."

### Foresight loop — IAS-E1 + IAS-D1 → IAS-C2 → IAS-F3 → IAS-C1 → IAS-A1 → IAS-C2

Scenario: IAS-E1's usage trend plus IAS-D1's ecology history show a capability category (headless
browser automation for blind-testing) climbing in demand across three of the estate's active
projects over two months. IAS-C2's Demand Forecasting projects that a fourth project will need the
same capability within the next cycle, before that project has asked for it. IAS-F3's Digital Twin
simulates two build paths against that forecast — a shared cross-project automation module versus
a fourth bespoke per-project implementation — and the simulation shows the shared module pays back
its build cost within the forecast window while the bespoke path does not. IAS-C1's Capability
Portfolio pre-allocates budget to the shared module ahead of the fourth project's actual request.
When that project's real mission arrives, IAS-A1's Capability Router finds the capability already
built and ready, routing to it with zero cold-start latency. The outcome (mission succeeded with
no build delay) flows back to IAS-C2 as a confirmed forecast, which recalibrates its confidence
weighting upward for the next demand signal of the same shape. IAS-E1/D1 alone only show a trend
line with no decision attached; IAS-C2 alone has a forecast nobody acts on; IAS-F3 alone has no
demand signal to simulate against. The loop is what turns a rising usage trend into capability that
exists before it is asked for.
