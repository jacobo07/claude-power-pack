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

## Verify

```bash
python tools/test_capability_runtime.py     # 29 V-gates, exit 0 = healthy
```

## Boundaries

Does **not** activate anything (`hooks/hook-dispatcher.js` does), select models
(`cognitive_os/router.py` does), propose new systems (`d2a_engine.py` does), or
persist activation records (CDP owns provenance — see
`vault/audits/apir/NON_DUPLICATION_LEDGER.md` §3).
