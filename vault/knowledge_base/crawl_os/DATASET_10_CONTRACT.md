# Dataset Contract — Crawl OS #10: Evidence Provenance and Integrity Fabric

Created 2026-07-19, before Part I is drafted, per `CRAWLOS_RESUMPTION.md` action 3 and the
PASO -1 requirement that an L/XL Crawl OS dataset establish its contract before any Part body.

## Ownership

This dataset elaborates the Evidence Integrity Fabric engine chartered in Dataset #01's Part V
§5.9: the operational mechanics of constructing, verifying, storing, retaining, querying, and
retiring the Evidence Object defined structurally in Dataset #01's Part VII. It owns: the
Evidence Object's lifecycle state machine; provenance-chain construction mechanics; the
dual-hash discipline in practice; the anomaly-signal taxonomy; the redaction pass that enforces
Dataset #01 Part X's no-secrets doctrine at the object level; chain-of-custody; tamper-evidence;
change-history recording; evidence-package composition for the Knowledge Distillation Fabric;
retention and freshness-window mechanics; dispute resolution over a contested Evidence Object;
the replay discipline; cross-mission evidence reuse; storage architecture; and the query
interface other engines use to consume Evidence Objects.

## Non-ownership (explicit, checked against Dataset #01 Part IV's test)

Does not own: the Evidence Object's field schema (Dataset #01 Part VII owns the schema itself;
this dataset owns how the schema is populated, verified, and operated over time — a schema
restated here instead of cited would violate Dataset #01 Part XXV's 25.5 inheritance rule).
Does not own: confidence-to-verdict mapping logic (DRK-03's CONNECT vocabulary owns that,
per Dataset #01 Part XVII; this dataset supplies signals, never redefines the scale). Does not
own: the general estate knowledge graph, its storage, or its query surface (GK-04 owns that,
per Dataset #01 Part XVI; this dataset owns constructing edge content, not writing or storing
it). Does not own: the cost ladder or engine selection (Part VI/the Acquisition Strategy
Router). Does not own: extraction or normalization logic (Parts V §5.7/5.8's own engines).
Does not own: the Production Reality Gates' pass/fail logic (Part XIII; this dataset supplies
the object that the gates evaluate).

## Consumers

Primary: graphify, permanent, per `CONSUMER_DECLARATIONS.md`'s Tier 1 model — this dataset's
`.txt` file is indexed identically to every other Crawl OS dataset. Downstream execution
consumer: PLANNED `modules/crawl_os/evidence.py`, per `CONSUMER_DECLARATIONS.md` row 10.
Secondary interface consumer: the future GK-04 edge writer, per Dataset #01 Part XVI — this
dataset's Part XVIII elaborates that composition's operational detail without re-declaring it.

## Dependencies

Dataset #01 (all Parts, especially III, IV, VII, X, XIII, XVI, XVII, XIX) — binding, sealed,
cited throughout rather than restated. DRK-03 (CONNECT vocabulary) — composed with, not owned,
per the same boundary Dataset #01 Part XVII already drew; this dataset does not re-litigate
that boundary, only operates within it. GK-04 — composed with per Part XVI; writer still
PLANNED, stated honestly per the same convention.

## Inputs / Outputs

Inputs: raw acquisition results from the Fetch Runtime Fabric and Document Normalization
Fabric (Dataset #01 Part V §5.5/§5.8); the mission's stated evidence requirement (Part III);
site memory's baseline expectations (Part V §5.11) informing anomaly detection. Outputs: a
fully populated, verified Evidence Object per acquisition; an Evidence Package bundling
related objects for the Knowledge Distillation Fabric; a change-history entry on re-
acquisition; a GK-04-bound edge payload once institutionalization is judged (Part XIV).

## Invariants

No Evidence Object field is ever fabricated or plausibly-inferred in place of an actually
observed value (Dataset #01 Part VII §7.9, binding here without exception). No Evidence
Object is institutionalized before Part XIII's ten gates are satisfied. No raw secret ever
survives the redaction pass into a persisted Evidence Object field (Dataset #01 Part X).
Every Evidence Object's provenance chain resolves to exactly one mission and exactly one
frontier item. A superseded Evidence Object is retained in change history, never deleted.

## Failure taxonomy (this dataset's own, distinct from Dataset #01 Part XXII's family-wide catalog)

Fabricated-field insertion; premature institutionalization (skipping a gate); redaction
bypass (a secret reaching storage); provenance-chain breakage (an object with no traceable
mission); silent object overwrite (losing change history); confidence-scale duplication
(reimplementing CONNECT instead of composing with it); orphaned GK-04 edge payload (built
but never handed to the writer once it exists).

## Test strategy

Mirrors Dataset #01's `test_crawl_os.py` gate (per-Part word-count floor, FINAL LAW presence,
no-markdown-fence check, contamination scan) applied to this dataset's own 25 Parts, extended
with a schema-citation check: this dataset's text must reference Dataset #01's Evidence Object
field list by citation, never reproduce the field list verbatim as though newly defined here.

## Completion contract

SEALED requires: 25/25 Parts at or above the 1,200-word floor; every Part closing with its own
PART N FINAL LAW; zero contamination hits; all forward-references resolved; zero verbatim
restatement of Dataset #01's Evidence Object schema (elaboration and citation only); this
dataset's row already present and accurate in `CONSUMER_DECLARATIONS.md` (verified, not
re-written, since row 10 already exists and is accurate); `CRAWLOS_RESUMPTION.md` updated
with the sealed state; REMOTE_DELTA = 0 0 after a pathspec-scoped commit.
