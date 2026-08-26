# knowledge_acquisition

Ask a large prompt corpus of an authenticated third-party knowledge interface,
over many hours, without losing a captured answer or re-asking an answered one.

First instance: EVA (Consultoria.io), 2,200 prompts. The interface is one
adapter; the engine is interface-agnostic.

Spec: [`SPEC.md`](./SPEC.md) (SPEC-KACQ-001).

## Delivery guarantee

**At-least-once execution with idempotent reconciliation. Not exactly-once.**

Send and persist cannot share a transaction across a browser boundary. What is
guaranteed instead: raw is persisted before the row that describes it, artifacts
are content-addressed so a re-capture of the same answer is a no-op, and a
crashed job returns to the queue by lease expiry. An answer is never lost and
never stored twice; a prompt may occasionally be asked twice.

## Control surface

```
python -m modules.knowledge_acquisition.cli <command>
```

| Command | What it does |
|---|---|
| `ingest` | Load corpora declared in `corpora.json`. Idempotent. Prompts that already carry an answer import as COMPLETE. |
| `status` | Counts by state and corpus, vault size, progress. |
| `next [--limit N]` | Show what would be claimed next. Claims nothing. |
| `run [--limit N]` | The acquisition loop. `--dry-run` sends nothing. `--headed` to watch. |
| `search <query>` | Full-text search over prompts (FTS5). |
| `history <prompt_id>` | Full audit trail for one prompt. |
| `recover` | Return crashed jobs to PENDING, requeue eligible failures. |
| `verify` | Re-hash every raw artifact and report corruption. |
| `session-bootstrap` | Open a real window so the Owner can log in. |
| `session-probe` | Check the session is still authenticated. |
| `session-status` | Show session state. |
| `assess-backfill` | Judge answers already captured. Reads raw, never writes it. |
| `quality` | What the source can answer, and what it has declared it cannot. |

## What the assessment layer decides

Spec: [`SPEC-PHASE5.md`](./SPEC-PHASE5.md) (SPEC-KACQ-005). Every answer is
judged as it lands, against the question that asked for it.

Two outputs, deliberately separate. **Epistemic level** is how much to bet on
the answer, produced by the deep-research engine's `cap_epistemic` called
unmodified. **Disposition** is what the pipeline should do with it. They vary
independently: nearly everything from one unverifiable vendor source lands at
DERIVED, which is honest and uninformative on its own -- the actionable
variance is in the disposition.

A third output is orthogonal to both. `route_to_expert` marks a question this
source has *declared* it cannot satisfy, so re-asking it is spend with a known
outcome. It is independent of whether the answer was worth keeping: a reply
that refuses on case data while teaching the conditions is extractable AND
routed away.

The **boundary ledger** is what makes that possible. When the source says "no
tenemos acceso a los datos financieros de otros clientes", that is recorded. A
later quantified claim about that same cohort is then unsourced by the source's
own admission, and is rejected rather than merely doubted. Honest hedges ("no
hay un numero magico, depende del producto") are recorded separately and route
nothing -- they say something about the question, not about the source.

Measured on this corpus (38 answers, `kacq-assess/1.3.0`): 30 extractable,
8 carrying unsourced cohort statistics, 14 questions routed to a human expert,
26 context-bound.

Assessment is derived data. It runs after the response row is durable, it is
versioned by classifier version and never overwritten, and its failure is
recorded as unrated. No classifier defect can cost a captured answer.

## First run

```
python -m modules.knowledge_acquisition.cli session-bootstrap   # log in, close window
python -m modules.knowledge_acquisition.cli session-probe       # expect READY
python -m modules.knowledge_acquisition.cli ingest
python -m modules.knowledge_acquisition.cli run --limit 5       # start small
```

## After a crash

A killed run leaves a job RUNNING and the browser profile locked. Neither needs
cleanup from the dead process:

```
python -m modules.knowledge_acquisition.cli recover              # job -> PENDING
python -m modules.knowledge_acquisition.cli run --steal-lock     # clear the lock
```

`--steal-lock` is explicit on purpose. Inferring liveness from a PID is
unreliable (PIDs are recycled; a signal-0 probe is not portable on Windows), and
a wrong guess puts two browsers on one profile. Use it when you know the run is
dead. Otherwise the lock lapses on its own after 900s.

## What this module owns, and what it borrows

Owns the four primitives the estate lacked: the prompt registry, the durable job
ledger, the authenticated browser session, and the immutable raw vault.

Borrows everything else rather than reimplementing it -- claim extraction and
confidence scoring (`deep-research/research_engines.py`), the epistemic ladder
and promotion gates (`fable_distillation`, `dataset_first`, `hard_rules`),
redaction (`secret_firewall`), throttling (`osa/throttle`), and human escalation
(`owner_queue`).

## Boundaries

EVA is **not** a source of truth. Captured answers are source-derived candidate
knowledge and stop at the validation queue; nothing here promotes a vendor
answer into institutional truth.

No access control is ever bypassed. On a login wall, challenge, or rate limit
the run pauses durably and reports what human action is needed.

The browser profile holds live session cookies for a private paid account. It is
git-ignored twice over, never parsed, and never logged. No credential appears in
source or configuration.

## Runtime state

Everything under `vault/knowledge_acquisition/` is runtime state and is not
committed: the registry database, the raw artifact vault, and the session
profile. The corpus is reproduced by `ingest`; the answers by `run`.
