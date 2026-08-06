# CDICF — DECISION LOG

Append-only. Each entry: what was decided, by whom, on what evidence, and what would
overturn it. A decision with no overturn condition is a belief, not a decision.

---

## D-001 — Do not build the 25-dataset corpus
**Date:** 2026-08-06 · **Decided by:** Owner (STOP #1, Option A)

**Evidence:** `CPP_DESIGN_OVERLAP_MAP.md` — D2A over 25 candidates against a
**discovered** denominator (78 modules, 67 commands, 39 hooks, 12 agents, 26 knowledge
families, 1,238 graph coordinates). Result: 7 REJECT, 11 EXTEND, 5 NEW, 2 not-datasets;
≈72% duplication. Eighth consecutive majority-owned proposal in this estate.

**Decision:** build the 5 NEW items as executables + 6 extensions. No corpus.

**Overturned by:** a demonstration that one of the 7 REJECT rows names territory its
claimed owner does not actually hold — i.e. an opened artifact, not a recollection.

---

## D-002 — React Bits is gateway-only, in both distribution paths
**Date:** 2026-08-06 · **Decided by:** Owner ("1 + 2 but don't redistribute React Bits publically")

**Evidence:** `LICENSE.md` fetched verbatim. MIT + Commons Clause Restriction v1.0,
© 2026 David Haz: *"so long as you do not sell, sublicense, or redistribute the
components themselves-whether alone, in a bundle, or as a ported version."* Porting and
renaming are explicitly covered, so a renamed copy is not a workaround. Plain `LICENSE`
returns HTTP 404 — the terms are only in `LICENSE.md`.

**Decision:** index, recommend, install-from-upstream, apply tokens in the consuming
application. Never vendor into the CPP registry (internal or public). Never strip
provenance. Enforced structurally by A3 action 8, not by memory.

**Overturned by:** an upstream license change removing the Commons Clause — which the
`--expect <fingerprint>` drift check exists to surface.

---

## D-003 — Build for the strictest distribution case
**Date:** 2026-08-06 · **Decided by:** Owner (internal + public)

**Decision:** assume public distribution. Provenance on every artifact from the first
commit. An internal-only build can relax later; a public build cannot retrofit.

**Overturned by:** Owner restricting scope to internal-only, which would still not make
the provenance work wasted.

---

## D-004 — A1 gates all upstream contact
**Date:** 2026-08-06 · **Decided by:** agent, ratified by Option A ordering

**Evidence:** `lib/license_gate.js` returned `tier: PERMISSIVE` and *"Otherwise
unrestricted"* for React Bits. Root cause: the MIT grant matched inside a first-hit-wins
loop over `text.slice(0, 4000)`, and `TIER` had no restricted value to land in even had
detection worked.

**Decision:** no upstream is cloned until the gate is correct — otherwise the first
absorption is performed by the component that is wrong. **A1 sealed at `998d52c`;
cloning is now unblocked.**

**Overturned by:** nothing. This is the ordering constraint the whole plan rests on.

---

## D-005 — `redistribution` is the field installers branch on
**Date:** 2026-08-06 · **Decided by:** agent

**Evidence:** React Bits is honestly described as MIT and may not be redistributed. The
SPDX id is therefore not sufficient to decide registry admission.

**Decision:** `classify()` emits `redistribution: allowed | conditional | prohibited |
unknown`. `vendor/NOTICE.md` carries it per row. Registry emitters branch on it.

**Overturned by:** nothing foreseeable; the asymmetry is load-bearing.

---

## D-006 — Restriction false positives are fail-safe; false negatives are not
**Date:** 2026-08-06 · **Decided by:** agent

**Evidence:** a false positive over-restricts (gateway integration where a fork was
allowed — recoverable). A false negative authorizes an actual license violation
(not recoverable). The two are not symmetric and must not be tuned as if they were.

**Decision:** tune the restriction pass toward over-detection. Guard the specific
over-blocking risks with tests: `V-LICENSE-RESTRICT-05` (MIT's own grant verbs —
"without restriction", "sublicense", "sell" — must not trip) and `V-LICENSE-RESTRICT-06`
(GPL's "You may not propagate", "Sublicensing is not allowed" must not read as a
redistribution ban).

**Overturned by:** a real upstream mis-blocked in practice — then tighten the specific
pattern and add its text as a regression case. Never relax the pass wholesale.

---

## D-007 — Continuity files live under `vault/audits/cdicf/`, not repo root
**Date:** 2026-08-06 · **Decided by:** agent

**Evidence:** `git status` at session start showed the repo-root `RESUMPTION_FILE.md`
already modified by a concurrent pane.

**Decision:** scope CDICF continuity files to `vault/audits/cdicf/` so this work never
overwrites another pane's handoff.

**Overturned by:** CDICF becoming the sole active work in the repo.

---

## D-008 — Fingerprints are withheld, not estimated
**Date:** 2026-08-06 · **Decided by:** agent

**Evidence:** license bodies reaching this session pass through a markdown conversion
that can reflow whitespace. `assistant-ui`'s text arrived with its line wrapping
collapsed. A sha256 of reflowed text is not the repository's hash.

**Decision:** record `PENDING_CLONE` and measure at clone time against the pinned commit.
A fingerprint computed from a lossy transform would look authoritative, would not match
the repository bytes, and would fire `--expect` on the first genuine drift check —
manufacturing exactly the confident-but-wrong verdict A1 was built to stop. Commit SHAs
are pinned instead; they come from the API and are authoritative.

**Overturned by:** a clone. That is the whole point.

**RESOLVED + PROVED 2026-08-06 (same day).** The obstacle was the *transport*, not the
network. Requesting the raw blob at the pinned commit
(`raw.githubusercontent.com/<owner>/<repo>/<sha>/<file>`) and writing it to disk unmodified
removes the markdown conversion from the path entirely; all five fingerprints were then
measured in one pass. The decision was also vindicated concretely: the react-bits value
published in `998d52c` (`f4cfa839…`) does **not** match the measured value
(`cde2d145…`), and `--expect f4cfa839…` exits 4 with LICENSE DRIFT against a licence that
never changed. Recording the gap rather than a plausible number is what made that
correctable. Sealed as `T-FINGERPRINT-FROM-RENDERED-MARKDOWN-001`.

---

## D-011 — `--reference-only` is the lawful emission mode for the Motion Gateway
**Date:** 2026-08-06 · **Decided by:** agent, **RATIFIED by Owner 2026-08-06**

**Owner's ruling, verbatim in substance:** *redistribution is the movement of code; a URL
is not code.* The Motion Gateway namespace is in scope, with `--reference-only` as its
emission mode for React Bits. The flag is no longer provisional: the stderr line is a
NOTICE rather than a pending-ratification warning, and A3b installs a pointer entry as a
record with zero component bytes on disk (`V-INST-14`).

The original reasoning is preserved below because the conflict it resolves is real and
will recur the next time an upstream pairs a permissive grant with a redistribution
withdrawal.

---

**The conflict.** The A3 brief says both *"if PROHIBITED: refuse, exit 5, no output"* and
*"if integration_mode is gateway_upstream: emit an entry pointing at the upstream"*.
React Bits is **both** — INV-02 forces exactly that pairing. Read strictly, A3 can never
emit anything for it, and the sealed CPP Motion Gateway namespace (D-002: "index,
recommend, install-from-upstream") is unbuildable, because every component in it is
prohibited by construction.

**Decision:** the strict rule is the DEFAULT and is what ships. `--reference-only` is an
explicit opt-in that emits an `upstream-pointer`: a name, a provenance block and an
install command, with **no `files` key at all** and no byte of component code. It is
gated to `integration_mode` ∈ {`gateway_upstream`, `metadata_only`}, warns on stderr, and
is covered by `V-EMIT-06` (asserts the emitted artifact contains no source).

**Why this is not a loophole:** redistribution is the movement of the code. A pointer
moves a URL. If the Owner disagrees, deleting the flag costs one commit and the Motion
Gateway namespace is then formally out of scope — which is a legitimate answer, and
cheaper to choose now than after A4 depends on it.

**Overturned by:** Owner ratification either way. Until then, treat the default as the
only sanctioned behaviour.

---

## D-012 — Contradictory inputs are refused, not reconciled
**Date:** 2026-08-06 · **Decided by:** agent (bug found by its own test)

**Evidence:** the first A3 draft computed `pointer = referenceOnly || MODE_IS_POINTER`.
Passing `--reference-only` to a `fork_canonical` component therefore emitted a pointer —
the caller would believe they had shipped a fork and would have shipped a URL. `V-EMIT-07`
caught it.

**Decision:** a fork mode and `--reference-only` contradict; the emitter refuses with
`MODE_MISMATCH` (exit 7) rather than silently honouring one. A tool that discards half of
a contradictory instruction is untrustworthy in a way that is very hard to notice.

**Overturned by:** nothing foreseeable.

---

## D-009 — This module is invisible to the Liveness gate, and that is recorded, not claimed as a pass
**Date:** 2026-08-06 · **Decided by:** agent

**Evidence:** `modules/liveness/reachability.py:230` gates subject enumeration on
`(pkg / "__init__.py").is_file()` — it enumerates **Python packages**, and reads `.js`
only as reference text when resolving who calls a Python module. `modules/cdicf/` does
not appear among the ledger's 343 modules. The gate exits 1 on 9 pre-existing orphans,
none of them mine.

**Decision:** do not report "liveness passes". A JS module absent from the denominator is
`PR-COVERAGE-BY-CONSTRUCTION-001` — absence read as health, the estate's own named
failure. `modules/cdicf/` reachability is asserted by `tests/component_manifest.test.js`
(21 cases) and by nothing else, and the README says so.

**Overturned by:** teaching `reachability.py` to discover JS subjects. That is a change to
a governance gate and deserves its own decision, not a side effect of this one.

---

## D-010 — Paso 1 and Paso 2 merged into one commit
**Date:** 2026-08-06 · **Decided by:** agent (deviation from the requested two commits)

**Evidence:** both steps edit the same five rows of one table in `vendor/NOTICE.md`.
Splitting would require staging partial hunks of a single table.

**Decision:** one commit (`1748670`) covering both, with the message naming both. The
gate fix Paso 1 exposed was committed separately (`e5aff74`) because it is code, not ledger.

**Overturned by:** nothing; recorded so the deviation from the requested commit plan is
visible rather than silent.

---

## D-013 — State repair runs before planning, never after
**Date:** 2026-08-06 · **Decided by:** agent (bug found by its own test)

**Evidence:** `V-INST-06` — install onto a project holding an interrupted transaction —
failed with `ENOENT ... copyfile`. The first A3b draft computed the plan, then recovered
the interrupted transaction, then applied. The plan is a **snapshot of the target's
bytes**: it records the prior sha256 of every path so it can back them up and put them
back. Recovery changes exactly those bytes. So the plan described a file that recovery had
just deleted, and the failure surfaced at the backup step — pointing at the copy, not at
the stale premise that caused it.

**Decision:** in `install()`, recovery precedes `planInstall()`. A second guard was added
at the backup step: the on-disk sha is re-read and compared to the planned `prior_sha`, and
a mismatch aborts with *"changed between planning and applying"* rather than with whatever
downstream error the staleness happens to produce. Ordering is the fix; the guard is what
makes the residual race legible instead of mysterious.

**Why this generalises:** the plan is a *reference derived from a pre-state*, and a repair
step that mutates that state invalidates every reference taken before it. This is
`feedback_reference_derived_from_post_state` seen from the other side — there a reference
was taken too late, here it was taken too early. The invariant is the same: pin the
reference at the boundary where the state stops moving. Sealed as
`T-PLAN-COMPUTED-BEFORE-STATE-REPAIR-001`.

**Overturned by:** nothing foreseeable.

**Dry-run note:** a dry run writes nothing, so it cannot recover, so its plan is read off
whatever tree is actually there. It therefore reports `dirty: true` rather than presenting
those actions as a forecast of what an install would do.

---

## Open questions (not yet decisions)

| # | Question | Blocks | State |
|---|---|---|---|
| Q1 | Tailark's copyright holder | Its NOTICE attribution row | **RESOLVED 2026-08-06** — MIT, © 2025 Irung, read from `LICENCE.md` |
| Q2 | Is `nilbuild/driver.js` canonical or a rename-redirect? | Its NOTICE provenance row | **RESOLVED 2026-08-06** — rename redirect. Both API paths return one identical object (`fork: false`, no parent, same 2018-03-11 creation, 26,544 stars) |
| Q3 | Does the React Bits boundary warrant human legal review before a public registry ships? | Public release only | OPEN |
| Q4 | Should `reachability.py` discover non-Python subjects? | The Liveness gate's honesty about JS/TS modules | OPEN (see D-009) |
