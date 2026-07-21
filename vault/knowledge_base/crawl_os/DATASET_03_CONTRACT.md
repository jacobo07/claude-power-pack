# Dataset Contract — Crawl OS #03: Adaptive Acquisition Strategy Routing

Created 2026-07-21, before Part I is drafted, per `CRAWLOS_RESUMPTION.md` action 1 and the
PASO -1 requirement that an L/XL Crawl OS dataset establish its contract before any Part body.

## Ownership

This dataset elaborates the Acquisition Strategy Router engine chartered in Dataset #01's Part V
§5.4 ("select, for each item on the frontier, the least costly engine from the cost ladder... that
can plausibly satisfy the mission's evidence requirement... and escalate only upon an observed,
stated failure at a cheaper rung, never by default and never by habit") operationally, turning
Dataset #01 Part VI's seven-rung cost-ladder doctrine from a constitutional principle into an
actual, checkable routing procedure. It owns: the routing pipeline that consumes a VALIDATED
Mission Contract (Dataset #02 Part XXI handoff) and a per-target authorization verdict (Dataset
#16 Part XIV composite, handed off per Dataset #16 Part XX) and produces a rung selection for each
frontier item; the attempt-cheapest-first decision procedure across all seven rungs; the
observed-reason discipline distinguishing a valid, falsifiable escalation trigger from an
untested prediction; site memory consultation, population, and staleness handling as this
dataset's own operational instantiation of Dataset #01 Part VI §6.4's site-memory concept;
the bidirectional de-escalation discipline (Part VI §6.5); the uniform adapter interface
(discover/map/fetch/render/interact/extract/normalize/validate/persist/replay, per Dataset #01
Part V §5.5) as the routing target every rung selection actually dispatches through; multi-mission
scheduling and pacing of acquisitions within whatever ceiling Dataset #16 has cleared; the
routing table itself (this dataset's own §3.2, the operational counterpart to Dataset #01 Part
VI's seven-rung description) that `modules/crawl_os/strategy_router.py` will implement verbatim
per `CONSUMER_DECLARATIONS.md` row 3; and this dataset's own routing-specific failure taxonomy.

## Non-ownership (explicit, checked against Dataset #01 Part IV's test)

Does not own: the cost-ladder doctrine itself, its seven-rung definition, or the
least-costly-sufficient-evidence principle (Dataset #01 Part VI owns that constitutional
statement outright); this dataset operationalizes the doctrine into an executable decision
procedure, it never restates or re-derives the doctrine as though discovered here. Does not own:
authorization adjudication — whether a target is permitted to be acquired at all, whether a
credential may be used, whether the seventh rung is authorized for a given mission (Dataset #16
owns every one of those decisions outright, per Dataset #16 Part XX §20.5-20.6); this dataset
consumes Dataset #16's composite verdict as a fixed constraint and never adjudicates authorization
itself, regardless of how strong its own view of a target's likely authorization status might be.
Does not own: Mission Contract compilation or field population (Dataset #02's own territory); this
dataset consumes a VALIDATED contract via Dataset #02 Part XXI's one-time handoff, it never
re-parses a raw request or re-populates a compiled field. Does not own: the actual execution
mechanics of any individual rung — issuing an HTTP request, rendering a page, driving a browser
session (the future Dataset #04 HTTP Fetch and Transport Intelligence, Dataset #05 Browser
Interaction and Session Governance, and Dataset #06 Large-Scale Crawl Frontier Engineering each
own their own rung's actual execution); this dataset selects a rung and dispatches to it, it never
performs the acquisition itself. Does not own: the Evidence Object schema or acquisition
provenance (Dataset #01 Part VII / Dataset #10's own territory). Does not own: retention or
freshness mechanics once content is acquired (Dataset #10 Part XII). Does not own: estate-wide
token, session, or cross-project cost accounting (CO-01's own territory per Dataset #01 Part XV
§15.2); this dataset's "cost ladder" concerns acquisition-method expense — which engine to invoke
for a given target — never the estate's own token-budget or model-routing economics, a boundary
this dataset must draw as precisely as Dataset #01 Part XV already drew it for the family as a
whole. Does not own: frontier prioritization — which candidate URLs to visit and in what order
(the future Dataset #01 Part V §5.3-chartered Resource Discovery and Frontier Engine, elaborated
by the future Dataset #06); this dataset receives an already-prioritized frontier and decides only
how, not whether or in what order, to acquire each item on it.

## Consumers

Primary: graphify, permanent, per `CONSUMER_DECLARATIONS.md`'s Tier 1 model — this dataset's
`.txt` file is indexed identically to every other Crawl OS dataset. Downstream execution
consumer: PLANNED `modules/crawl_os/strategy_router.py`, per `CONSUMER_DECLARATIONS.md` row 3 —
this dataset's own routing table (§3.2) becomes the module's routing table verbatim, so a future
diff between the two is itself a drift check once the module exists. Secondary interface
consumers, all PLANNED and stated honestly: Dataset #02's Crawl Intent Compiler, whose
already-sealed Part XXI hands this dataset the VALIDATED contract it routes; Dataset #16's
Authorization engine, whose already-sealed Part XIV composite verdict this dataset consumes as a
fixed constraint before dispatching any acquisition; the future Dataset #04 HTTP Fetch and
Transport Intelligence, Dataset #05 Browser Interaction and Session Governance, and Dataset #06
Large-Scale Crawl Frontier Engineering, each of which this dataset's rung selections dispatch to;
Dataset #01's Crawl Cortex Supervisor (Part VI §6.8), which monitors this dataset's own routing
decisions for anomalous cost patterns.

## Dependencies

Dataset #01 (binding, sealed) — Part V §5.4's engine charter; Part VI in full, the seven-rung cost
ladder this dataset exists to operationalize; Part XV §15.2, the CO-01 boundary this dataset must
respect; Part XIII, the Production Reality Gates a routing decision's downstream acquisition must
still pass regardless of which rung produced it. Dataset #02 (binding, sealed) — Part XXI, the
mission-to-engine handoff interface that is this dataset's primary input channel. Dataset #16
(binding, sealed) — Part XIV, the composite authorization verdict this dataset consumes as a fixed
constraint; Part XX §20.5-20.9, which already states this dataset's own boundary with Dataset #16
in full detail from Dataset #16's own side, including the authorization-laundering-through-routing
failure this dataset's own Part XXII must guard against from its own side; Part VII and Part XII,
the rate-limit ceiling and seventh-rung authorization this dataset's scheduling must respect.

## Inputs / Outputs

Inputs: a VALIDATED Crawl Mission Contract per Dataset #02 Part XXI's handoff, complete with all
sixteen fields and their provenance tags; a prioritized frontier item from the future Dataset #01
Part V §5.3-chartered Frontier Engine; a per-target composite authorization verdict per Dataset
#16 Part XIV, including any rate-limit ceiling and seventh-rung clearance; this dataset's own site
memory, recording prior rung outcomes per target or site class. Outputs: a rung selection for each
frontier item, dispatched through the uniform adapter interface; a recorded observed reason at the
moment of any escalation; a recorded observed reason at the moment of any de-escalation; updated
site memory reflecting the outcome of a dispatched rung; a scheduling and pacing plan for a
mission's own sequence of acquisitions, respecting Dataset #16's rate-limit ceiling.

## Invariants

No rung is selected without first attempting every cheaper rung the mission's own site memory does
not already, on the basis of an observed prior failure, exempt (Dataset #01 Part VI §6.2). No
escalation occurs without a specific, falsifiable, actually-observed reason recorded at the moment
of escalation — a prediction, however plausible, is never sufficient on its own (Part VI §6.4).
No rung selection proceeds for a target this dataset has not first confirmed carries a granted
composite authorization verdict from Dataset #16; an absent or non-granted verdict halts routing
for that target regardless of how technically reachable it appears (Dataset #16 Part XX §20.5-6).
No denial issued by Dataset #16 is worked around by attempting a different rung or adapter on the
theory that the new path was never itself specifically adjudicated (Dataset #16 Part XX §20.9).
The seventh rung is never invoked without Dataset #16's own operator-approval clearance for that
specific mission (Dataset #01 Part VI §6.6; Dataset #16 Part XII). Site memory is revisited
periodically rather than treated as a permanent verdict, and a rung once escalated to must be
re-evaluated for de-escalation as conditions change (Part VI §6.5). This dataset's own cost-ladder
routing table is never used as a substitute for CO-01's estate-wide token or session accounting,
and CO-01's economics are never consulted to make a rung-selection decision this dataset's own
routing table already governs (Dataset #01 Part XV §15.2).

## Failure taxonomy (this dataset's own, distinct from Dataset #01 Part XXII's family-wide catalog)

Habitual escalation (selecting an expensive rung by default or by familiarity rather than an
observed reason, the specific failure Part VI §6.4 exists to forbid); untested-prediction
escalation (treating an unverified assumption about a site's rendering requirements as though it
were an observed failure); escalation-without-de-escalation (a monotonically growing cost curve
produced by never revisiting a site whose requirements have since simplified); authorization
bypass (dispatching an acquisition for a target without a confirmed granted verdict from Dataset
#16, or treating a denial as scoped to a single rung rather than the target); rung-authorization
inversion (this dataset independently judging whether a target is authorized rather than
consulting Dataset #16's composite verdict, the precise failure Dataset #16 Part XX §20.6 already
forecloses from its own side); seventh-rung bypass (invoking authorized human intervention without
Dataset #16's own operator-approval clearance); CO-01 boundary violation (this dataset's routing
logic reasoning about estate-wide token or session budget rather than acquisition-method cost);
site-memory staleness (a rung selection made on site memory that no longer reflects the target's
current posture, without a triggering re-evaluation); scheduling-pacing violation (a mission's own
acquisition pacing, individually compliant, contributing to a cross-mission rate-limit breach
Dataset #16 Part XXI's own aggregate mechanism is positioned to catch, but which this dataset's
own single-mission scheduling logic failed to coordinate against once flagged).

## Test strategy

Mirrors `tools/test_crawl_os.py`'s per-Part word-count-floor and FINAL LAW presence gates, extended
to this dataset's own 25 Parts, plus the same contamination-baseline discipline already covering
Datasets #01, #02, #10, and #16. No dedicated schema-citation check is required the way Dataset
#10 needed one, because this dataset owns its own routing vocabulary and routing table outright
rather than elaborating a schema another dataset already owns — the citation discipline that
matters here runs toward never reimplementing Dataset #01 Part VI's cost-ladder doctrine, Dataset
#16's authorization adjudication, or Dataset #02's mission-compilation mechanics under a different
name.

## Completion contract

SEALED requires: 25/25 Parts at or above the 1,200-word floor; every Part closing with its own
PART N FINAL LAW; zero contamination hits beyond the audited estate-wide baseline; all
forward-references resolved; zero reimplementation of Dataset #01 Part VI's cost-ladder doctrine,
Dataset #16's authorization adjudication, or Dataset #02's mission-compilation mechanics; this
dataset's row already present and accurate in `CONSUMER_DECLARATIONS.md` (verified, not
re-written, since row 3 already exists and is accurate); `CRAWLOS_RESUMPTION.md` updated with the
sealed state; REMOTE_DELTA = 0 0 after a pathspec-scoped commit.
