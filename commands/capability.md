---
name: capability
description: Compile the minimum sufficient capability stack for a mission — which capabilities apply, which stay dormant, which are blocked and why.
---

# /cpp-capability

The capability layer (CPP-APIR Option A). Every other registry in this estate is
module-, skill-, or model-level; this one reasons about capabilities.

## Compile a stack for a mission

```bash
python modules/capability_runtime/applicability.py "<mission description>" \
  --evidence "hardware_boot_log,runtime_trace" \
  --runtime powerpc \
  --held-scopes "architecture reconstruction" \
  --budget-pressure
```

Emits four groups:

- **activate** — `MANDATORY` + `RECOMMENDED` only. This is HR-APA-005: the
  minimum sufficient stack, never "activate everything for safety".
- **escalate** — activated capabilities whose `risk_class` is architecture-,
  production- or safety-changing. Automatic activation grants no authority to
  change those (HR-APA-010); the Owner decides.
- **dormant** — `AVAILABLE_ON_TRIGGER`. Reported, never loaded (HR-APA-014).
- **blocked** — with the reason: missing evidence, unresolved owner, duplicate
  scope, or insufficient capability.

`--json` emits the same groups machine-readably.

## Why a verdict is what it is

Five blocking gates run **before** any score, so a capability that would score
well is still blocked when its evidence is absent. The score only chooses among
the four non-blocking verdicts, weighing trigger relevance, the counterfactual
cost of omission, leverage, evidence and maturity against activation, context
and operational cost.

## Where the mission context comes from

The engine ranks contracts against a `MissionContext`. That context is not typed
by hand — it is projected from the repo by the Setup-OS graph emitters:

```bash
python modules/setup_os/graph.py --path . --mission "<mission description>"
```

Four graphs are emitted, each node carrying the provenance of the scanner field
it came from, so an inference is never presented as a fact:

- **architecture** — the layers observed, and only the edges whose endpoints
  both exist.
- **capability_demand** — work this project's shape creates (`demand`) and work
  it creates with no mechanism to absorb it (`gap`).
- **human_dependency** — where a person is currently the routing mechanism.
  This is the class CPP-APIR exists for.
- **risk_topology** — what an automated write here could break; consumed by
  HR-APA-010.

`held_scopes` from that projection feeds gate 4, so a capability whose territory
an incumbent already holds is `REJECTED_AS_DUPLICATE` rather than activated.

## Seeding and specializing

```bash
python tools/seed_capability_contracts.py            # the universal kernel set
python modules/universal-meta-systems/runtime/specialization.py \
  --propose-from . --project <name>                  # a PROPOSED specialization
```

The seeder is idempotent — an existing contract is kept unless `--force`. Every
seeded contract names a live owner; a contract with no owning module is a claim,
and this registry stores no claims.

Specialization compiles six components (domain pack, runtime adapter, evidence
adapter, quality policy, activation policy, project contracts) into the override
set `derive()` consumes. Fewer than two populated components is refused as
name-level specialization (HR-APA-016).

## Contracts and derivatives

Contracts live in `vault/capability_runtime/contracts/*.json`; project
derivatives in `vault/capability_runtime/derivatives/*.json`.

A derivative is cut from a parent, never copied. `derivatives.derive()` refuses
a rename-only delta (HR-APA-016) and refuses to weaken an inherited boundary
without a named approver (HR-APA-017).

## Mining a corpus into capability proposals (UCEIMR R1)

The seeder above is **introspective** — it writes contracts for capabilities
this repo already has. This is the other writer: it turns already-acquired
external evidence into proposals.

```bash
python modules/capability_runtime/corpus_adapter.py --mine --corpus-dir <dir>
python modules/capability_runtime/corpus_adapter.py --mine --save --json
python modules/capability_runtime/corpus_adapter.py --approve <id> --owner <path>
```

It acquires nothing (HR-UCEIMR-02 — CrawlOS/AKOS/autoresearch acquire; this
reads what they wrote). Every claim is routed through `d2a.run()` before it is
shown, so the boundary above holds: the adapter surfaces, **d2a still decides
ownership**. Three dispositions: `CANDIDATE`, `DEFER` (d2a capped coverage
without confidently naming a parent — unknown ownership, never novelty) and
`OWNED`.

Propose-only is structural, not a convention: a proposal carries no owner, so
`CapabilityContract.validate()` (HR-APA-018) makes it impossible to activate
one by accident. `--approve` demands an Owner-supplied owner and refuses both
`OWNED` and `DEFER`.

Measured on this repo 2026-08-04: `akos=55 + research=83` units → **0**
proposals. AKOS persists a ~220-char lead per unit and `vault/research/` holds
the estate's own notes; `enricher.py` fetches transcripts at runtime and never
writes them down. Nothing on disk is authored corpus at mining granularity —
which is why `--corpus-dir` exists.

## Retirement conditions (UCEIMR R2)

`retirement_condition` was defined on every contract and read by nothing.

```bash
python modules/capability_runtime/retirement.py --record
python modules/capability_runtime/retirement.py --strict   # exit 1 on a retirement
```

A condition with a deterministic probe is measured against real repo state; one
without a probe is reported `UNEVALUABLE` and is **never** counted as `ACTIVE`.
`never --` is `NEVER`; an empty condition is `NO_CONDITION`. Retirement is
proposed, never executed — nothing is deleted or deactivated.

## Verify

```bash
python tools/test_capability_runtime.py     # 29 V-gates, exit 0 = healthy
python tools/test_uceimr_residues.py        # 20 V-gates for R1 + R2
```

## Boundaries

Does **not** activate anything (`hooks/hook-dispatcher.js` does), select models
(`cognitive_os/router.py` does), propose new systems (`d2a_engine.py` does), or
persist activation records (CDP owns provenance — see
`vault/audits/apir/NON_DUPLICATION_LEDGER.md` §3).
