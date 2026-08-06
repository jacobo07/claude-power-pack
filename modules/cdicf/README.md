# CDICF — Component Manifest (A2)

The canonical knowledge unit for one component in the Claude Power Pack Design
Intelligence & Component Fabric. A pile of code becomes intelligence-selectable
infrastructure only once every member carries one of these.

Lives in `modules/` because **`lib/` is gitignored in this repo** — `lib/license_gate.js`
survives only because it was already tracked. New executables placed there vanish silently.

## Files

| File | Role |
|---|---|
| `component_manifest.schema.json` | The schema. Canonical. Declares six cross-field invariants JSON Schema cannot express |
| `validate_manifest.js` | Validator + CLI. Dependency-free, matching `lib/license_gate.js` |
| `examples/react-bits.split-text.json` | A **prohibited** component: `gateway_upstream`, nothing ships from CPP |
| `examples/shadcn-ui.button.json` | An **allowed** component: `fork_canonical` |

## Use

```
node modules/cdicf/validate_manifest.js <manifest.json> [--json]
node modules/cdicf/validate_manifest.js --all modules/cdicf/examples
```

Exit: `0` valid · `1` invalid · `2` argv · `3` io.
An `--all` sweep that finds zero manifests exits **1**, not 0 — zero manifests validated
is zero evidence, not a pass.

## Why the invariants exist

The schema can say "`integration_mode` is one of these six values". It cannot say
*"a component whose license forbids redistribution may not be forked."* That second
sentence is the one that matters, so it is enforced in code:

| ID | Rule |
|---|---|
| INV-01 | `redistribution_posture` must equal what `license_gate.js` derives from `license_tier` |
| **INV-02** | `prohibited` ⇒ `integration_mode` ∈ {`gateway_upstream`, `metadata_only`} |
| INV-03 | `prohibited` ⇒ `notice_required` true |
| INV-04 | `VERIFIED` ⇒ commit and fingerprint both pinned |
| INV-05 | `prefer` ⇒ `wcag_level` not `fail`/`unassessed` |
| INV-06 | `motion_budget: high` ⇒ `reduced_motion_compliant` true |

**INV-02 is the load-bearing one.** It is the structural form of the Owner's 2026-08-06
decision that React Bits is never redistributed, in the internal or the public path.
A decision that lives only in a document is a decision everyone eventually forgets;
this one fails a test.

**INV-01 imports `REDISTRIBUTION_BY_TIER` from the gate rather than restating it.** The
manifest vocabulary and the gate vocabulary are one vocabulary. A copy would drift, and
the drift would stay invisible until an installer acted on the wrong half.

**INV-04** exists because `VERIFIED` is a claim about a specific artifact. Unpinned,
there is no artifact for the claim to be about.

## Scope limit of the validator

`validate_manifest.js` is **not** a general JSON Schema engine. It implements exactly the
keywords this schema uses — `type`, `required`, `properties`, `additionalProperties:false`,
`enum`, `const`, `pattern`, `minLength`, `minimum`, `maximum`, `items`, `oneOf`,
`format: date`. Pointed at an arbitrary schema it would silently under-validate, which is
why it is scoped to this one. Stated here rather than discovered later.

## Known gap — this module is invisible to the Liveness gate

`modules/liveness/reachability.py` enumerates **Python packages** (it gates on
`__init__.py`) and reads `.js` only as reference text when resolving who calls a Python
module. A JavaScript module is therefore never a *subject* of the reachability audit.

`modules/cdicf/` does not appear in the ledger's 343 modules. That is **not** a pass —
it is absence being read as health, which is precisely
`PR-COVERAGE-BY-CONSTRUCTION-001`: an audit whose subjects are enrolled by construction
cannot fail you if it never enrolled you. Recorded in `CDICF_DECISION_LOG.md` as D-009.
Until the scanner discovers JS subjects, this module's reachability is asserted by its
test suite (`tests/component_manifest.test.js`, 21 cases) and by nothing else.

## Tests

```
node --test tests/component_manifest.test.js
```
