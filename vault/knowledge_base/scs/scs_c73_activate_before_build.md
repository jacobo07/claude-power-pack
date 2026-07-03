# SCS C73 — Activate-Before-Build-by-default

**Sealed:** 2026-07-03
**Type:** process doctrine + empirical activation proof (no new architecture)
**Slot check:** C70 = Cognitive-Leak-Taxonomy, C71 = Graphify Navigation Kernel (arch),
C72 = Graphify live activation → this is **C73**. Verified free (no `scs_c73*` file; the six
grep hits for "c73" are telemetry-hash substrings, not seals).
**Siblings:** `[[scs_c70_cognitive_leak_taxonomy]]`, `[[scs_c69_conversation_quality]]`,
`[[scs_c68_token_corpus_doctrine]]`.

---

## Doctrine

Before proposing new cognitive-kernel datasets or systems, **verify whether the existing ones are
live**. The 2026-07-03 Reality Scan (Cognitive Kernel family) confirmed CO-00..10 + PM-01..05 +
GK-00..12 + G1..G6 already answer *"how does Claude think less?"*. The remaining reasoning-tax was
not missing architecture — it was **built architecture sitting inert or unverified**. The correct
policy is *activate-and-prove* before *design-and-build*: the highest-ROI move on a mature stack is
to make what exists actually run, measured with real data.

## What this sprint verified (Scope A, EXECUTION)

Two of the three "inert" systems were **already activated by the same-day C70 sprint**; the
sprint's own premise was outdated. Empirical PASO -1 replaced the assumption:

| System | Real state | Proof |
|---|---|---|
| **PM-03 Findings Bus** | consume wired (hub Hook 13); bus seeded by C70 | 4th real finding published this session; digest round-trips |
| **GK-12 dispatcher** | live, **0 drift** (repo==live `4C5336E4`) | Graph-First advisory observed in the model's tool context this session |
| **CO-08 scheduler** | scope-gate **built + tested** (PM-02, 26/26); inert only at `prelaunch.py::_gate` | 4-scenario scope-gate proof; wrapper seam documented Owner-side |

CO-08 recalibration's true activation surface is the **declare-intent habit** (a pane declares its
scope via `pm_02_intent`), not the launch wrapper — at prelaunch no intent exists yet. The wrapper
edit only lets an incumbent's declared scope soften the warning; the full relaxation is realized by
panes calling `scope_gated_admit(declared_scope=[…])` when contending for a repo.

## Reality-contract highlights

- **Measure-before-build paid off again:** the plan would have re-wired PM-03's consume side that
  C70 had already shipped — pure duplication avoided by reading the live hub first.
- **Pre-existing FAIL fixed, not swept:** baseline surfaced `V-SCS-NO-COLLISION` (8/9), a
  pre-existing FP where the gate flagged a graphify file that merely *documents* "SCS C69→C71".
  RCA-hardened the gate (a line seals C69 only if it names C69 without C71) → 9/9. No classified
  FAIL carried into the seal.
- **No live-state contamination:** the committed regression test is hermetic (temp bus dir); only
  the one deliberate activation publish touched the live bus.

## Verification

`tools/test_scope_a_activation.py` — 7 V-gates (V-PM03-FIRST-FINDING, V-PM03-DEDUP,
V-PM03-FAILOPEN, V-CO08-INTENT-ALLOWED, V-CO08-NOINTENT-CAPPED, V-CO08-COLLISION-REFUSED,
V-CO08-GATE-FAILSAFE), **7/7 ×3 hermetic**. Baseline no-regression: `test_parallel_mesh` 26/26,
`test_cognitive_os_build` 68/68, `test_cognitive_leak_taxonomy` **9/9** (was 8/9 pre-fix).

## Cross-references

- Execution report + Owner-side seam: `vault/plans/activate-inert-2026-07-03.md`
- Reality Scan verdict: `vault/plans/cognitive-kernel-datasets-2026-07-03.md`
- UKDL: `ukdl-universal.md` — T-INERT-ARCHITECTURE-TAX-001, T-SCS-COLLISION-GATE-FP-001
- Siblings: `[[scs_c70_cognitive_leak_taxonomy]]`, `[[scs_c72]]` (graphify live)
