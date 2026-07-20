# Dataset Contract — Crawl OS #16: Authorization, Compliance and Safety

Created 2026-07-20, before Part I is drafted, per `CRAWLOS_RESUMPTION.md` action 1 and the
PASO -1 requirement that an L/XL Crawl OS dataset establish its contract before any Part body.

## Ownership

This dataset elaborates the Governance, Safety, and Authorization engine chartered in Dataset
#01's Part V §5.13 ("bound every other engine's behavior against authorized domains, authorized
authentication, and the estate's compliance requirements") operationally, and is the engine that
turns Dataset #01 Part IX's anti-detection-is-not-authorization doctrine from a constitutional
prohibition into an actual, checkable adjudication. It owns: access-boundary adjudication — the
mechanics that convert a mission's already-compiled permitted-domains and authorized-
authentication fields (Dataset #02 Part IX) into an actual granted, denied, or escalated
verdict for a specific target; the consent framework distinguishing a legitimately granted
session from a merely technically reachable one; authentication isolation — the procedural
separation ensuring mere possession of a working credential never itself constitutes
authorization to use it beyond what was actually granted; rate-limit policy consultation and
the recording of a target's stated or inferred limits as an authorization input (operationalizing
Dataset #01 Part IX §9.6); robots.txt and site-policy consultation, caching, and interpretation
mechanics (operationalizing Dataset #01 Part IX §9.4's designation of robots.txt as the primary
default authorization signal); terms-aware policy — turning a site's terms of service into a
machine-checkable authorization signal where one exists; the operator-approval workflow that
authorizes the Acquisition Strategy Router's seventh cost-ladder rung (Dataset #01 Part VI
§6.6's authorized human intervention) to actually be invoked for a given mission; a closed
restricted-actions taxonomy naming the action classes — form submission with side effects,
purchase-like or state-changing actions, irreversible actions — that require explicit operator
approval regardless of technical feasibility; a data-minimization policy declaring what a
mission may collect and retain given its consent and compliance posture; and this engine's own
authorization audit trail, recording every grant, denial, and escalation it produces.

## Non-ownership (explicit, checked against Dataset #01 Part IV's test)

Does not own: credential storage, capture, or redaction mechanics (Dataset #01 Part X, the
no-secrets-in-corpus doctrine, owns that outright); this dataset decides whether an existing
credential or session may be used for a given target, it never stores, handles, transmits, or
redacts the credential itself. Does not own: the constitutional doctrine that technical capacity
to evade a barrier is not authorization to pass it (Dataset #01 Part IX owns that doctrine at
the founding level); this dataset operationalizes the doctrine into a checkable adjudication
mechanism, it never re-litigates or restates the doctrine itself as though newly discovered
here. Does not own: retention or freshness mechanics once acquisition is underway (Dataset #10
Part XII owns that operational machinery); this dataset's data-minimization field is a policy
ceiling that machinery must operate within, never a second, competing retention engine. Does
not own: cost-ladder rung selection (Dataset #01 Part VI, the Acquisition Strategy Router's own
territory per Dataset #01 Part V §5.4); this dataset decides only whether the seventh rung's
human intervention is authorized to be invoked for a specific mission, never which of the seven
rungs a router should select. Does not own: the Crawl Mission Contract schema or the population
of its permitted-domains and authorized-authentication fields (Dataset #02's own owned
territory per its Part III §3.2 and Part IX); this dataset consumes those already-populated
fields as declared input and adjudicates them, it never re-populates, redefines, or overrides
what Dataset #02's compiler recorded as a mission's stated scope. Does not own: general,
estate-wide governance or compliance unrelated to crawling — only the authorization layer
specific to Crawl OS's own acquisition activity, per this dataset's own founding instruction not
to appropriate universal governance. Does not own: Evidence Object provenance (Dataset #01 Part
VII / Dataset #10's own territory); this dataset's authorization audit trail is a distinct
record of its own grant/deny/escalate decisions, composed with, never duplicating, the Evidence
Object's separate acquisition-lineage provenance chain.

## Consumers

Primary: graphify, permanent, per `CONSUMER_DECLARATIONS.md`'s Tier 1 model — this dataset's
`.txt` file is indexed identically to every other Crawl OS dataset. Downstream execution
consumer: PLANNED `modules/crawl_os/authz.py`, per `CONSUMER_DECLARATIONS.md` row 16. Secondary
interface consumers, all PLANNED and stated honestly: Dataset #02's Crawl Intent Compiler, whose
already-sealed Parts IX and X hand this dataset the permitted-domains and authorized-
authentication fields it adjudicates; the future Dataset #03 Acquisition Strategy Router, which
must consult this dataset's verdict before dispatching any acquisition and before invoking the
seventh cost-ladder rung; the future Dataset #05 Browser Interaction Fabric, which must hold
this dataset's clearance before executing any authenticated session; the future Dataset #04
Fetch Runtime Fabric, which enforces robots.txt and rate-limit findings this dataset supplies at
the uniform-interface layer; and Dataset #10's already-sealed Evidence Integrity Fabric, whose
Gate C (Authorization Reality, per Dataset #01 Part XIII §13.4) consumes this dataset's verdict
as the specific input that gate checks.

## Dependencies

Dataset #01 (binding, sealed) — Part V §5.13's engine charter; Part IX in full, the anti-
detection-is-not-authorization doctrine this dataset exists to operationalize; Part VI §6.6, the
seventh cost-ladder rung this dataset's operator-approval workflow authorizes; Part X, the
no-secrets doctrine this dataset composes with as a boundary it does not own; Part XIII §13.4,
Gate C, which this dataset's verdict feeds; Part XIX, the verdict ontology whose VOID assignment
(§19.6) is triggered specifically by this dataset's own Gate C failures. Dataset #02 (binding,
sealed) — Parts IX and X especially, which hand this dataset the permitted-domains and
authorized-authentication fields, each carrying the fine-grained provenance tag Part IX §9.11
requires specifically so this dataset's adjudication can weight an explicit request differently
from a broad default. Dataset #10 (binding, sealed) — Part XII, the retention/freshness
machinery this dataset's data-minimization policy bounds without operating.

## Inputs / Outputs

Inputs: a compiled Crawl Mission Contract's permitted-domains, authorized-authentication, and
required-evidence fields per Dataset #02; a target's robots.txt directives, stated or inferred
rate limits, and terms-of-service text where available; the estate's own compliance requirements
where they bear specifically on crawling activity; an existing authenticated session's own
scope, where one is claimed. Outputs: a per-target authorization verdict (granted, denied, or
escalated for operator approval) that Dataset #01 Part XIII's Gate C consumes directly; an
operator-approval grant or denial for a specific restricted action or seventh-rung invocation;
a data-minimization ceiling a mission's acquisition and retention machinery must respect; and
this dataset's own authorization audit trail recording every decision with its basis.

## Invariants

No authorization verdict is ever granted on the basis of technical feasibility alone — an
adjudication that cannot cite a specific authorization signal (an explicit request-level scope,
a resolved entity's own domain, an existing authenticated session's actual granted scope, or a
target's own robots.txt/terms permitting the access) defaults to denied or escalated, never
granted (Dataset #01 Part IX §9.9's ambiguity default, inherited here as this dataset's own
operating rule). No credential or session is used beyond the scope its own grant actually
covers, regardless of what the session's mere existence would technically permit (Dataset #01
Part IX §9.5). No restricted action is executed without a recorded operator approval, and no
approval is inferred from a mission's general authorization to proceed. No authorization
decision is made silently — every grant, denial, and escalation is recorded in this dataset's
own audit trail with the specific signal it was based on. A denied or escalated verdict is never
silently retried through a different technical path in the hope of a different outcome; a
target denied once remains denied for that mission unless the mission's own contract is amended
per Dataset #02 Part XVIII, or an operator explicitly re-authorizes it.

## Failure taxonomy (this dataset's own, distinct from Dataset #01 Part XXII's family-wide catalog)

Authorization-by-capability drift (this dataset's own adjudication logic quietly reintroducing
the exact failure Dataset #01 Part IX exists to forbid, by treating a technically successful
access as evidence the access was authorized); consent conflation (treating a broad or ambiguous
signal — a session's mere existence, a domain's general public reachability — as though it were
the specific consent a particular access actually requires); silent escalation avoidance
(denying outright what should have been escalated for operator approval, foreclosing a
legitimate mission rather than surfacing the decision to a human); silent escalation overuse
(escalating routine, clearly-authorized access to avoid making an adjudication this dataset was
chartered to make); restricted-action misclassification (failing to route a genuinely
restricted action through operator approval, or over-classifying an ordinary action as
restricted to avoid the harder judgment); audit-trail omission (a grant, denial, or escalation
made without a corresponding recorded basis); data-minimization overreach (a policy ceiling set
so narrow it forecloses acquisition the mission's own consent and compliance posture genuinely
support, confused with the caution this dataset otherwise requires); and stale-verdict reuse (an
authorization verdict reused for a target whose robots.txt, terms, or rate-limit posture has
since changed, without re-adjudication).

## Test strategy

Mirrors `tools/test_crawl_os.py`'s per-Part word-count-floor and FINAL LAW presence gates,
extended to this dataset's own 25 Parts, plus the same contamination-baseline discipline already
covering Datasets #01, #02, and #10. No dedicated schema-citation check is required the way
Dataset #10 needed one, because this dataset owns its own adjudication vocabulary outright
rather than elaborating a schema another dataset already owns — the citation discipline that
matters here runs toward never reimplementing Dataset #01 Part X's credential-handling mechanics
or Dataset #10 Part XII's retention machinery under a different name.

## Completion contract

SEALED requires: 25/25 Parts at or above the 1,200-word floor; every Part closing with its own
PART N FINAL LAW; zero contamination hits beyond the audited estate-wide baseline; all
forward-references resolved; zero reimplementation of Dataset #01 Part X's credential-handling
mechanics or Dataset #10 Part XII's retention machinery; this dataset's row already present and
accurate in `CONSUMER_DECLARATIONS.md` (verified, not re-written, since row 16 already exists
and is accurate); `CRAWLOS_RESUMPTION.md` updated with the sealed state; REMOTE_DELTA = 0 0
after a pathspec-scoped commit.
