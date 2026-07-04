# SCS C74 — CO-NextGen: Cognitive Readiness Telemetry (CO-12)

**Sealed:** 2026-07-04
**Type:** architecture dataset (no code) + adoption-axis doctrine
**Slot check:** C71/C72 = Graphify, C73 = Activate-Before-Build → this is **C74**.
CO family ids CO-09/CO-10 are TAKEN (SCS C61/C62); this dataset is **CO-12** (CO-11 approved,
deferred by Owner choice). **Siblings:** `[[scs_c68_token_corpus_doctrine]]` (volume),
`[[scs_c69_conversation_quality]]` (behavior), `[[scs_c70_cognitive_leak_taxonomy]]` (non-token).

---

## Doctrine

The kernel now has a **fourth audit axis: adoption.** C68 measures volume, C69 behavior, C70
non-token leaks — all retrospective ("what did the session spend?"). None measured whether the
machinery built to save reasoning was **actually consulted and acted on**. A built-but-unused
system produces zero savings while looking shipped — PM-03 proved this by sitting inert a full day
(C70→C73). CO-12 closes that: a **Cognitive Readiness Score** (adoption rate over *eligible*
opportunities, per lever / day / week / cohort) tied to CO-01 WU/MTok as the realized-multiplier
ground truth, plus the **Telemetry-Before-Claims Contract**.

## Scope (Owner-approved at STOP #1, 2026-07-04)

The CO-NextGen Reality Scan found **7/9 proposed systems already COVERED** (Model Router=CO-03,
Context VM=CO-04/GK-06, Asset Factory=CO-05/GK-08, Reasoning-Dedup=PM-03, Repo Brain=PM-01, Budget
Auction=PM-04, **Loop Compression=CO-09**), and **two genuine gaps**: CO-11 Output Budget Governor
and CO-12 Cognitive Readiness Telemetry. Owner chose **CO-12 first** ("measure before more
building"). CO-11 remains approved-but-deferred. No CO-09/CO-10 reuse.

## The two contracts formalized

- **Telemetry-Before-Claims (NEW, cross-cutting):** no dataset/seal/sprint may claim any saving
  without a `(metric, data-source, value)` triple in the same emission; an unmeasured saving is a
  **hypothesis** and must be labelled one. Formalizes the discipline already proven by C68/C69/C70.
- **Extend-Existing-Parent (already doctrine):** SCS C73 (Activate-Before-Build) + HR-PREMISE-001 +
  the V-REALITY-SCAN gate already enforce "verify a compatible parent before building". Cited, not
  re-created.

## Honesty highlights (per CO-10)

- Every CO-12 metric names its **data source** and whether the instrument **exists today** or is
  **instrument-pending**. Pending metrics (dedup-hit, Opus-avoided, loop-boundedness) read *unknown*
  and are excluded from the composite — never faked as 0/100. The pending list is itself a readiness
  signal. The live tool is the EXECUTION-mode follow-up; this seal is architecture only (like PM-02's
  scheduler recalibration and GK's live agents).
- CO-12 is a **rung-2 measurement layer** (CO-01 class): it makes non-adoption visible and enforces
  claim-honesty at the claim boundary; it does not itself pull a lever.
- **~40% synthesis, stated plainly:** CO-12 leans on the C68/C69/C70 readers + CO-01 WU/MTok + the
  GK-09 presentation pattern. Its genuinely-new material is the adoption-rate metric set + the
  Telemetry-Before-Claims contract.

## Addendum — CO-12 instruments wired (EXECUTION, 2026-07-04)

The C74 dataset specified three instrument-pending signals. This addendum records their wiring in
`modules/cognitive_os/co_12_telemetry.py` (the instrument layer; the dataset stays code-free):

- **loop-boundedness — LIVE with real data.** Corpus-derived (reads `~/.claude/projects/*/*.jsonl`,
  the C68/C69/C70 reader pattern; `_SID_RE`-filtered to real session transcripts). First run on the
  live corpus classified **625 sessions → 431 bounded, 194 unbounded** (threshold 800 entries; top
  offenders 20,458 / 19,647 / 18,673 entries — the long/hung-session pattern the signal targets).
  This satisfies the reality contract "≥1 signal wired with real data".
- **opus-avoided — WIRED, honest 0.** `route_and_record()` routes via CO-03 then records the
  opus-avoided classification to a JSONL sink (fail-open). It accrues real data when called
  (proved: `V-OPUS-WIRED`); the live count is 0 because `route()` is not yet on the live
  model-selection path (CO-10 residual) — reported as such, never faked.
- **dedup-hit — PENDING (honest).** PM-03 consume is wired (Hook 13, C73), but the RedundancyTax
  hit-producer is agent-driven, off the live path. `readiness_report()` marks it
  `instrument-pending`; the datum is not invented.

Done-gate: `tools/test_co12_telemetry.py` **8/8 ×3 hermetic** (synthetic corpus + temp sink; router
untouched — `V-NO-REGRESSION` = `test_cognitive_os_build` 68/68). Companion sprint item: CLAUDE.md
safe-trimmed 39,967→39,910; the `<38000` target proved below the ~39,658 operative floor
(see `[[T-CLAUDE-MD-SIZE-001]]`) — reported, not faked.

## Verification

`tools/test_co12_readiness_telemetry.py` — 8 V-gates (V-NO-CODE, V-CORRECT-IDS, V-PARENT-REFS,
V-REALITY-SCAN, V-TELEMETRY-REAL, V-CONTRACT, V-INDEX-REGISTERED, V-NO-REGRESSION), hermetic ×3.
V-NO-REGRESSION runs the C68 + C69 + C70 suites in-subprocess (all exit 0). V-DEPTH inherits the
sealed CO-family Owner ruling (~600–1100 words/Part, architecturally complete, zero-padding);
full 2500/Part expansion would be the low-WU/MTok burn the kernel exists to prevent.

## Cross-references

- Dataset: `vault/knowledge_base/cognitive_os/cognitive_os_12_cognitive_readiness_telemetry.md`
- Reality Scan + scope: `vault/plans/co-nextgen-datasets-2026-07-04.md`
- Index: `COGNITIVE_OS_INDEX.md` § CO-NextGen extension
- Siblings: `[[scs_c68_token_corpus_doctrine]]`, `[[scs_c69_conversation_quality]]`,
  `[[scs_c70_cognitive_leak_taxonomy]]`; predecessor `[[scs_c73_activate_before_build]]`
