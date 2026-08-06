# CDICF — Manifest, Registry, Installer (A2 · A3 · A3b)

The canonical knowledge unit for one component in the Claude Power Pack Design
Intelligence & Component Fabric, and the two stages that act on it. A pile of code
becomes intelligence-selectable infrastructure only once every member carries one of
these and the machinery refuses the ones that may not travel.

Lives in `modules/` because **`lib/` is gitignored in this repo** — `lib/license_gate.js`
survives only because it was already tracked. New executables placed there vanish silently.

## Files

| File | Role |
|---|---|
| `component_manifest.schema.json` | The schema. Canonical. Declares six cross-field invariants JSON Schema cannot express |
| `validate_manifest.js` | A2 validator + CLI. Dependency-free, matching `lib/license_gate.js` |
| `registry_emitter.js` | A3. Manifest → shadcn registry entry + install manifest. Refuses to redistribute |
| `installer.js` | A3b. Install manifest → files on disk, as a recoverable, reversible transaction |
| `examples/react-bits.split-text.json` | A **prohibited** component: `gateway_upstream`, nothing ships from CPP |
| `examples/shadcn-ui.button.json` | An **allowed** component: `fork_canonical` |

The pipeline is `manifest → emit → install`, and each stage refuses independently.

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
test suites (`component_manifest` 21 · `registry_emitter` 16 · `installer` 24 = 61 cases)
and by nothing else.

## The installer (A3b)

```
node modules/cdicf/installer.js install  --from <emitDir> --target <proj> [--dry-run]
node modules/cdicf/installer.js rollback --component <id>  --target <proj>
node modules/cdicf/installer.js recover  --target <proj>
node modules/cdicf/installer.js verify   --target <proj> [--component <id>]
```

State lives in `<target>/.cdicf/` — `installed.json` (the state of record), `journal.json`
(present only during a transaction), plus `backups/` and `staging/`. It is stored in the
**consuming project**, not in PP's vault, because the only question an installer must be
able to answer is *what is installed in this project*, and a record held elsewhere cannot
answer it for a project it has never seen.

### What "atomic" honestly means

No portable filesystem offers multi-file atomicity, and claiming it here would be the
confident-but-false statement this subsystem exists to prevent. What holds:

- Nothing is ever **committed** partially — `installed.json` only names installs that
  completed *and* verified.
- Partial state is always **detectable** — the journal is fsynced before the first
  mutation and removed after the last, so its presence proves an interruption.
- Partial state is always **reversible** — the journal carries the prior sha256 of every
  path it touches.
- The window is **bounded to the rename sweep** — all content is written and hash-verified
  in staging first, so committing is N metadata operations, not N file writes.

The residual truth, stated rather than hidden: between an abrupt kill and the next
invocation, a partial tree does sit on disk. It is detected and reverted before any
further work. That is recovery, not prevention. `V-INST-03` and `V-INST-04` prove it
against a real `exit 137` from inside the rename sweep — not a thrown error, and not a
hand-built directory that a crash might never actually produce.

Recovery **declines** to delete a file that was edited after the interruption
(`V-INST-07`). Recovery that over-reaches destroys work that was never its own, so it
stops and names the path instead.

### Why the installer re-checks the licence

The emitter already refuses to emit a redistribution-prohibited component carrying code.
The installer derives the posture again, from the install manifest's own `license_tier`.
Two independent checks on one fact is the point: the emitter guards what leaves CPP, the
installer guards what lands in a project, and an entry can reach a project by a path that
never went through the emitter — a hand-copied directory, a third-party registry. A guard
that trusts an upstream guard is one guard.

Registry entries are untrusted data by project doctrine, so every destination is resolved
and asserted to be inside the target. One escaping path refuses the **whole** install: an
entry containing one is not an entry to partially trust.

## Tests

```
node --test "tests/**/*.test.js"
```

Use the glob. On Node 24 `node --test tests/` resolves `tests` as a *module path* and dies
with `MODULE_NOT_FOUND` before running anything — a failure that looks like a broken suite
rather than a broken invocation. The glob also excludes `tests/fixtures/`, which holds a
deliberately self-killing process and is not a test.
