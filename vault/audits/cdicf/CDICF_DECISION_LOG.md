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

## Open questions (not yet decisions)

| # | Question | Blocks |
|---|---|---|
| Q1 | Tailark's copyright holder — unresolved | Its NOTICE attribution row |
| Q2 | Is `nilbuild/driver.js` canonical or a rename-redirect? | Its NOTICE provenance row |
| Q3 | Does the React Bits boundary warrant human legal review before a public registry ships? | Public release only |
