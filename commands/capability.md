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
