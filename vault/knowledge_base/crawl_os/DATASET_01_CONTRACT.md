# Dataset Contract — Crawl OS #01: Constitutional Architecture

Created 2026-07-20, retroactively — this dataset SEALED 2026-07-19, before the contract-first
convention began with Dataset #10. Backfilled per `CRAWLOS_RESUMPTION.md` action 2 (flagged
twice, unresolved across two prior handoffs) so the contract-first pattern is consistent across
every sealed Crawl OS dataset. Written from the dataset's actual sealed text, not from what was
speculated about it before it was drafted — every claim below is grounded in a specific Part
read directly from `crawl_os_01_constitutional_architecture.txt` this session, not carried
forward from an earlier plan.

## Ownership

This is the founding, constitutional dataset of the Crawl OS family; every other dataset in the
family inherits its ownership boundaries as binding rather than advisory (Part XXV §25.5). It
owns: the mission and founding failure mode (Part I — a system must not accept Markdown as
proof of success); the adapters-are-not-identity doctrine governing all eleven execution engines
(Part II); the affirmative and negative ownership boundary for the whole family (Parts III–IV);
the fourteen-engine constitutional architecture and each engine's one-sentence charter (Part V);
the seven-rung cost ladder and least-costly-sufficient-evidence principle (Part VI); the Evidence
Object schema as the family's constitutional unit of work (Part VII); the prohibition of
Markdown-as-proof as an enforceable article (Part VIII); the anti-detection-is-not-authorization
doctrine (Part IX); the no-secrets-in-corpus doctrine (Part X); the no-megafork doctrine (Part
XI); the no-default-browser doctrine (Part XII); the ten Production Reality Gates (Part XIII);
the institutionalization-is-not-automatic doctrine (Part XIV); the composition boundaries with
CO-01, GK-04, DRK-03, and Deep Research/Autoresearch (Parts XV–XVIII); the seven-verdict
ontology for acquisition (Part XIX); deployment-plane separation of powers (Part XX); the
five-verb interface discipline (Part XXI); the family-wide, eleven-pattern failure and
anti-pattern catalog (Part XXII); the institutional learning loop and negative memory (Part
XXIII); the amendment and versioning process binding on every dataset in the family, including
itself (Part XXIV); and this dataset's own done criteria and closing restatement of the founding
law (Part XXV).

## Non-ownership (Part IV's own explicit list, restated as the contract's boundary)

Does not own: general reasoning over acquired evidence (belongs to whatever system or agent
consumes an Evidence Package). Does not own: the estate's institutional memory in general (owns
only the narrower judgment of whether a specific acquired item earns institutionalization, plus
its own eight specialized memories — source, site, extraction, session, evidence, change,
negative, procedural). Does not own: dataset creation in general (owns only the Web-to-Dataset
Compiler as a producer feeding the estate's already-sealed dataset-first protocols). Does not
own: universal quality assurance (the Crawl Cortex Supervisor audits crawl missions only, not
code quality or architecture unrelated to acquisition). Does not own: general automation. Does
not own: browser automation as a universal capability (only browser automation in service of an
acquisition mission). Does not own: agent orchestration in general (only the sequence of engines
within a single crawl mission). Does not own: domain knowledge unrelated to acquisition — no
Crawl OS dataset, including this one, may accumulate substantive expertise about commerce,
product research, or advertising; the contamination audit every sealed dataset runs enforces
this boundary mechanically (Part IV §4.9).

## Consumers

Primary: graphify, permanent, per `CONSUMER_DECLARATIONS.md`'s Tier 1 model — verified via
`modules/graphify/indexer.py --query --name "crawl_os_01"` returning this dataset as a real
`dataset` node. Downstream execution consumer: PLANNED `modules/crawl_os/__init__.py`, whose
docstring, once the module exists, restates this dataset's constitutional boundary by the same
convention `modules/duplicate_to_advantage/__init__.py` already follows (`CONSUMER_DECLARATIONS.md`
row 1). Universal secondary consumer: every one of the other eighteen Crawl OS datasets, sealed
or future, which must cite this dataset by name in their own front matter and compose with,
never redefine, its ownership boundaries, Evidence Object schema, Reality Gate discipline, and
verdict ontology (Part XXV §25.5).

## Dependencies

None upstream within the Crawl OS family — this is the family's founding dataset and every other
Crawl OS dataset depends on it, not the reverse. Composes with, without being owned by or owning:
CO-01 (estate-wide operating economics — Part XV), GK-04 (typed knowledge-graph write-back — Part
XVI), DRK-03 (CONNECT confidence/sufficiency vocabulary — Part XVII), and Deep Research /
Autoresearch (adjacent single-shot and recurring-sweep capabilities already sealed elsewhere in
the estate — Part XVIII). Each composition boundary is a live discipline, re-checked against
every future proposal via the same ownership test (Parts II, IV, XV §15.6, XVII §17.5), not a
static map consulted once.

## Inputs / Outputs

Inputs: the founding resource document's survey of eleven acquisition engines and the failure
modes they exhibited in practice (`Downloads/Dataset CrawlOS 1.txt`); the estate's own
already-sealed neighboring systems (CO-01, GK-04, DRK-03, Deep Research, Autoresearch, the
dataset-first corpus convention) against which every ownership claim in Parts III–IV and every
composition boundary in Parts XV–XVIII was checked before being allowed to stand. Outputs: the
binding constitutional text itself — the fourteen engine charters, the Evidence Object schema,
the cost ladder, the ten gates, the seven-verdict ontology, the five-verb interface, and the
eleven-pattern failure catalog — that every sibling Crawl OS dataset elaborates operationally
without being permitted to redefine.

## Invariants

No Crawl OS component may treat clean, well-formatted Markdown output as proof that an
acquisition retrieved the content actually sought (Part VIII §8.2, the article-level enforcement
of Part I's founding law). No Evidence Object field is ever fabricated or plausibly-inferred in
place of a genuinely observed value (Part VII §7.9). No gate's pass may be inferred from another
gate's pass; all ten Production Reality Gates are checked independently and reported cumulatively
(Part XIII §13.12). No acquisition obtained by defeating a deliberate authorization decision —
a robots.txt disallow, an authentication wall, a stated rate limit — may ever be institutionalized
as evidence, regardless of content quality (Part IX §9.10). No raw credential, token, or cookie
value may appear in anything this family persists, deliberately or by accident (Part X §10.2). No
engine may report an acquisition outcome using an eighth verdict word or a compound state outside
the seven this dataset defines (Part XIX §19.10). No engine may collapse execution, evidence
judgment, and authorization into a shared failure domain where one plane's misbehavior can
silence the oversight meant to catch it (Part XX §20.2). No sixth institutional verb, and no
change to the Evidence Object schema, the confidence-vocabulary computation, the verdict
ontology, an engine's charter, or an ownership boundary, may be made without the Part XXIV
amendment process — including a change to this constitution's own amendment process (Part XXIV
§24.10–24.11).

## Failure taxonomy (the family-wide catalog every sibling dataset's own taxonomy is explicitly distinct from)

Eleven named patterns, one shared root — a system optimizing for looking correct in the moment
over being verifiably correct on inspection (Part XXII): the Clean-Markdown Failure (mistaking
rendered output for verified content); the Router-Favorite Failure (silently collapsing many
engines or rungs into one habitual default); the Megafork Failure (copying an adapter's internals
to patch a narrow limitation); the Authorization-by-Capability Failure (treating technical
capacity to evade a barrier as license to pass it); the Secret-Leak-by-Convenience Failure
(persisting a credential because redaction felt unnecessary for one mission); the Default-Pass
Failure (treating an unchecked gate, authorization, or content check as though it had passed);
the Corpus-as-Log Failure (institutionalizing every gate-passing acquisition because declining
requires an active decision); the Confidence-Vocabulary-Drift Failure (a local approximation of
DRK-03's shared vocabulary silently substituted for the genuine import); the Plane-Collapse
Failure (the single most structurally dangerous pattern, since it can disable the very oversight
that would catch every other pattern in this list); the Provenance-Amnesia Failure (a
provenance chain partially or wholly reconstructed after the fact rather than genuinely
observed); and the Verdict-Flattening Failure (collapsing the seven-term ontology into a single
boolean or number when reporting to a downstream consumer). Every sibling dataset's own
Part XXII-adjacent section names a distinct, narrower taxonomy specific to what that dataset
itself owns operationally (see `DATASET_02_CONTRACT.md`, `DATASET_10_CONTRACT.md`) — this
catalog is the shared root every one of those narrower taxonomies ultimately traces back to.

## Test strategy

Mirrors `tools/test_crawl_os.py`'s per-Part word-count-floor and FINAL LAW presence gates,
already covering this dataset's own 25 Parts since the suite's original creation. This backfill
adds `V-CRAWLOS-DS01-CONTRACT`: this file exists and is non-empty, the same structural check
already covering `DATASET_02_CONTRACT.md` and `DATASET_10_CONTRACT.md`. No dedicated
schema-citation or non-reimplementation check is required the way Dataset #10 needed one for
Dataset #01's Evidence Object schema, because this dataset is the schema's origin, not an
elaboration of someone else's — the citation discipline that matters runs outward from this
dataset toward every sibling, already enforced by each sibling's own contract and test coverage,
not inward toward this one.

## Completion contract

This dataset was already SEALED 2026-07-19 under the done criteria it states for itself in Part
XXV §25.2–§25.4: all 25 Parts at or above the 1,200-word floor (32,888 words total, mean 1,315,
min 1,200), every Part closing with its own PART N FINAL LAW, zero contamination beyond the two
audited self-referential/governance-clause hits, front matter naming
`CONSUMER_DECLARATIONS.md` and its PLANNED downstream module path, Tier 1 graphify consumption
verified by a real `--query` return, and every forward reference made before its target Part
existed (Part VI §6.2, Part VIII §8.7, Part V §5.14, Part V §5.15) confirmed to resolve against
the real content those later Parts actually sealed. This backfill's own completion contract is
narrower: `DATASET_01_CONTRACT.md` exists and is non-empty; `V-CRAWLOS-DS01-CONTRACT` added to
`tools/test_crawl_os.py` and passing hermetically; `CRAWLOS_RESUMPTION.md` updated to record the
backfill as closed; REMOTE_DELTA = 0 0 after a pathspec-scoped commit.
