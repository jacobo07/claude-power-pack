# CDICF — NEXT ACTIONS

Ordered. Each is one sitting. Do not reorder without recording why in
`CDICF_DECISION_LOG.md`.

## Immediate — CLOSED 2026-08-06

| # | Action | State |
|---|---|---|
| 1 | Resolve Tailark's copyright holder | **DONE** — MIT © 2025 **Irung**, read from `LICENCE.md`. Confidence OBSERVED → VERIFIED |
| 2 | Resolve `nilbuild/driver.js` canonicality | **DONE** — rename redirect, not a fork. Both API paths return one identical object (`fork: false`, no parent, 2018-03-11, 26,544 stars). Canonical: `nilbuild/driver.js` |
| 3 | Pin all 5 upstream commits + fingerprints | **PARTIAL** — all 5 commits pinned from the API. Fingerprints deliberately `PENDING_CLONE` (decision D-008): fetched license text can be whitespace-reflowed, so a hash of it would not match repository bytes and would false-positive on `--expect` |

Remaining legal debt: **fingerprints only**, and only at clone time. Holders and
canonicality are settled; attribution rows can now be written.

## A2 — Component Manifest — SEALED 2026-08-06

Shipped in `modules/cdicf/` (schema, dependency-free validator + CLI, two examples,
README) with 21 tests. Six invariants enforced; INV-02 refuses to record a
redistribution-prohibited component as a fork — the structural form of the React Bits
decision.

| # | Remaining | Done when |
|---|---|---|
| 5 | Emit Upstream Mirror Ledger rows from `license_gate.js --json` rather than by hand | A ledger row is produced by the tool, not typed |

**Trap (confirmed in practice):** new files under `lib/` are **gitignored**.
`lib/license_gate.js` commits only because it was already tracked; `git add lib/...`
prints "The following paths are ignored". A2 therefore lives in `modules/cdicf/`.

**Trap (confirmed in practice):** three of five upstreams do not name their license file
`LICENSE` — `LICENSE.md`, `LICENCE.md` (British), and lowercase `license`. Fixed in
`findLicenseFiles`; assume nothing about the filename or the default branch (`driver.js`
is on `master`).

**Gap (D-009):** `modules/liveness/reachability.py` enumerates Python packages only, so
`modules/cdicf/` is absent from its 343 modules rather than passing. Its reachability is
asserted by its tests and nothing else until the scanner discovers JS subjects.

## A3 — Registry producer — SEALED 2026-08-06 (partial: rollback outstanding)

`modules/cdicf/registry_emitter.js`, 16 tests.

| # | Action | State |
|---|---|---|
| 6 | shadcn-format registry entry + install manifest per component | **DONE** — `registry-item.json` + `install-manifest.json`, checksummed, artifacts sorted so the digest is filesystem-independent |
| 7 | Commit-pinned deterministic install **+ rollback + interrupted-install recovery** | **PARTIAL** — pinning and determinism done (`pinned`, `deterministic`, per-artifact sha256, roll-up checksum). **Rollback and interrupted-install recovery are NOT implemented.** No installer exists yet to interrupt; this moves to A3b |
| 8 | **Redistribution guard** — refuse any prohibited component | **DONE** — refused at exit 5 with zero bytes written (`V-EMIT-01`, `V-EMIT-02`). Posture is *derived* from `license_tier` via the gate, never read from the manifest field, so a hand-edited manifest cannot walk past it (`V-EMIT-03`) |

Action 8 was the load-bearing one: INV-02 is no longer a schema opinion, it is a system
boundary. The registry is the distribution channel, so refusing here is refusing to
redistribute.

**Open for ratification (D-011):** `--reference-only`. The brief's two rules collide on
React Bits — it is both PROHIBITED and `gateway_upstream` by construction. Strict refusal
is the default; the code-free pointer path is implemented, gated, warned, and unratified.
Deleting it costs one commit and puts the Motion Gateway namespace formally out of scope.

## A3b — Installer, rollback, recovery (NEW, carved out of action 7)

| # | Action | Done when |
|---|---|---|
| 9 | Transactional installer consuming `install-manifest.json` | An install killed mid-write leaves the project in its prior state |
| 10 | Checksum verification on install | A tampered artifact is refused, naming the file |

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
