# CDICF — NEXT ACTIONS

Ordered. Each is one sitting. Do not reorder without recording why in
`CDICF_DECISION_LOG.md`.

## Immediate

| # | Action | Done when |
|---|---|---|
| 1 | **Resolve Tailark's copyright holder** (inspect `LICENCE.md` body, not the badge) | A `Copyright (c) <year> <holder>` string is quoted in the NOTICE row and Confidence flips OBSERVED → VERIFIED |
| 2 | **Resolve `nilbuild/driver.js` canonicality** — is it the canonical repo or a rename-redirect of `kamranahmedse/driver.js`? | The NOTICE row names one canonical path with evidence |
| 3 | **Pin all 5 upstream commits**, run `node lib/license_gate.js <clone> --json` against each working tree, fill `Snapshot` + `Fingerprint` | Zero NOT PINNED / NOT MEASURED strings remain in the CDICF section of `vendor/NOTICE.md` |

Actions 1–3 are the *only* remaining legal debt. Everything downstream inherits it.

## A2 — Component Manifest (NEW)

| # | Action | Done when |
|---|---|---|
| 4 | Write `vault/schemas/component_manifest.json` — typed fields for provenance, commit, license, redistribution, capabilities, states, a11y, RSC/client boundary, bundle cost, motion intensity, maturity, known failures, alternatives, adoption/rejection history | Schema validates a hand-written manifest for one real component |
| 5 | Emit Upstream Mirror Ledger rows from `license_gate.js --json` rather than by hand | A ledger row is produced by the tool, not typed |

**Trap:** new files under `lib/` are **gitignored** in this repo. `lib/license_gate.js`
committed only because it was already tracked. Put new executables under `modules/` or
`tools/`, or `git add -f` deliberately and record the choice.

## A3 — Registry producer (NEW)

| # | Action | Done when |
|---|---|---|
| 6 | `registry.json` emitter with namespaces (Primitives, Marketing, AI Interfaces, Onboarding, Motion Gateway, Compositions, Pages) | A generated registry installs one real component into a scratch project |
| 7 | Commit-pinned deterministic install + rollback + interrupted-install recovery | Install is killed mid-write and the project is left in its prior state |
| 8 | **Redistribution guard**: the emitter refuses any component whose manifest says `redistribution: prohibited` | A React Bits component is attempted and refused, with the refusal explained |

Action 8 is the load-bearing one. It is the mechanism that makes the Owner's
"don't redistribute React Bits publicly" decision structural rather than remembered.

## A4 — Selection + Abstention (NEW)

| # | Action | Done when |
|---|---|---|
| 9 | Hard filters → soft scoring → explanation → abstention | The engine returns "no suitable component, build nothing" on a case where that is correct |
| 10 | Prior-adoption enters as a **tiebreak only**, never a scored term | A popularity-only candidate loses to a better-fitting unused one |

## A5 — Evaluation corpus (NEW)

| # | Action | Done when |
|---|---|---|
| 11 | ~40 adversarial scenarios as executable cases | The suite runs and at least one case fails honestly before being fixed |

## Extensions (after the NEW spine runs)

`DESIGN.md.template` (+9 decisions) · `design_index.py` (+3 FTS tables) · `graphify`
(+component node/edge types) · `capability_runtime` (+4 activation modes) ·
`modules/cdio` (+component-scope checks) · `DESIGN_GOVERNANCE.md` (+reuse-first,
+provenance-mandatory, +tour-as-last-resort).

## Standing gates

- `python modules/liveness/reachability.py` — every new module wired, declared or deleted.
- Gate on absolute counts, never ratios.
- No dataset prose describing an engine that does not run.
