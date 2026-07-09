# SCS C82 — Fable-Advantage-Distillation-Active

**Sealed 2026-07-09.** The Fable Advantage Distillation Reinforcement Suite (FD-00…FD-07) is built:
**8 architectural datasets** in `vault/knowledge_base/fable_distillation/`, **5 NEW + 3 EXTEND**, out
of **26 named candidates** (5 NEW · 9 EXTEND · 2 MERGE · 10 DO_NOT_BUILD ⇒ **~81 % already covered or
thin-extension**, reported before building per the anti-bloat gate). Zero code — architecture only,
per the Owner mandate. Depth: **>2500 real words/Part, Owner-ruled** (all 24 Parts 2502–3976 words).

## The thesis, operative

> Convert every interaction with a frontier model into permanent, portable, model-independent
> infrastructure. The dependence on the model decreases; the cognitive capital grows. **If a
> capability only works with the frontier model, it has not yet been distilled.** Success is measured
> by how much future dependence on frontier models is reduced — not by the number of datasets.

Operationalized: the family's success metric is **CO-12's model-demotion / Opus-avoided count +
cognitive-compression ratio** (adopting-cohort WU/MTok ÷ non-adopting), **reused, never re-invented**
(SCS C41 + CO-12 parallel-reader anti-pattern). The root law `PR-FABLE-DELTA-ONLY-001` — *spend
frontier tokens only on the delta; deposit a classified delta before every session closes* — is the
routing rule FD-01/FD-05 feed into CO-03.

## The family

| ID | Dataset | Verdict | Parent(s) |
|---|---|---|---|
| FD-00 | Fable Advantage Doctrine & Session Operating Protocol | NEW (doctrine) | sibling CO-00; metric = CO-12 |
| FD-01 | Fable Delta Extraction Engine (S-DELTA) | NEW (spine) | PM-03 (transport → differential) |
| FD-02 | High-Leverage Question Compiler (S-QUESTION) | NEW | one_shot Q&A + CO-03 |
| FD-03 | Insight Triage & Transmutation (S-TRIAGE ⊕ S-TRANSMUTE) | EXTEND | compound-learnings tree + UKDL |
| FD-04 | Intelligence Decay & Transfer-Proof (S-DECAY) | NEW (HIGH-RISK) | CO-12 + CDIO-05 |
| FD-05 | Anti-Dependence Arbitrage | EXTEND | CO-03 + CO-05 + CO-12 |
| FD-06 | Permanent Advantage Writeback | EXTEND | GK-08 + UKDL |
| FD-07 | Fable Learning Flywheel (S-FLYWHEEL) | NEW (loop) | GK-08 Stop-hook + learning-sentinel |

The loop: FD-02 compiles the high-leverage question → FD-00 admits the frontier call → FD-01 extracts
and classifies the delta against the CO-05 baseline → FD-03 routes it to its exact home and transmutes
its form → FD-06 writes it back permanently with cross-system reinforcement → FD-04 proves it survives
a model downgrade → FD-05 converts the convertible ones into CO-03 routing rules and CO-05 assets →
CO-12's dependence metric moves → the risen floor sharpens the next session's questions. Each turn
raises the floor, so the next delta is smaller and more precisely targeted — the compounding dynamic.
**The loop is the moat** (CWOPS): the durable advantage is not the answer (commoditized) but the
valid·closed·<30-day flywheel the suite's own execution deposits.

## Done-gate (CLEARED)

- **FASE 0 Reality Scan** — blocking; STOP #1 approved by Owner in two rounds (scope: FD-00..07 as mapped).
- **V-gates ×3 hermetic** — `DATASET_FAMILY_VERDICT=PASS` (3/3). All 24 Parts ≥2500 words;
  0 code fences across all 8; every dataset carries an explicit "does NOT duplicate" section;
  thesis-term density 88–219/dataset (differential, not generic).
- **V-FD-DECAY anti-test-theater** — FD-04 grades against human-curated gold standards, never
  auto-generated tests (SCS C41), enforced as a founding law + failure mode (97 refs).
- **Cross-reference integrity** — every dataset declares its CO/PM/GK/CDIO/UKDL parent and its
  downstream consumers; the FD_INDEX dependency graph and integration map are consistent.
- **REMOTE_DELTA = 0 0** on push.

## Honest residuals (CO-10, never hidden)

The suite is **architecture (datasets), not live code** — the same staging discipline as CO/PM/GK,
whose datasets preceded their modules. Enforcement is rung-1/2 advisory today except where it rides an
existing hook (FD-00 preflight on kclaude; FD-07 close-boundary on the GK-08 Stop hook). The
EXECUTION-mode follow-ups each dataset specifies (admission-gate hook, consultation-rate instrumenting,
FD-04 transfer-test harness, FD-05 conversion emitter into CO-03/CO-05) are the Owner-authorized next
build — the datasets are the contract; the code is the next step. Per CO-12 Telemetry-Before-Claims,
no dependence-reduction figure is claimed here — the metric is wired to CO-12 and reads *unknown* until
the loop runs live and the cohort data accrues.

Cross-ref: FD_INDEX.md · [[ukdl-universal]] `PR-FABLE-DELTA-ONLY-001` · CO-12 (metric) · SCS C41
(do-not-build-what-exists + anti-test-theater) · SCS C61/C65/C71 (the CO/PM/GK families this extends).

## EXECUTION-mode addendum (SCS C82, 2026-07-09) -- FD-00 gate + FD-07 flywheel LIVE

The two hooks the datasets documented as their next build are now code on the real session
path, not architecture:

- **FD-00 admission gate** -- `modules/fable_distillation/fd_00_gate.py`.
  `check_admission(task) -> {ADMIT, DECLINE, ROUTE_CHEAPER, ANSWER_FROM_ASSET, DEFER}`
  (`.action` = admit|reject|defer). It CONSULTS the real CO-03 `route()` and CO-05
  `vault/asset_resolver` and the knowledge_base floor; it never re-implements routing.
  Advisory, fail-open ABSOLUTE -> ADMIT (never blocks the Owner). Verified: a mechanical
  transform and a dataset-covered task REJECT; a floor-silent above-floor discovery ADMITs;
  a non-str input fails open to ADMIT without raising.
- **FD-07 close-boundary flywheel** -- `modules/fable_distillation/fd_07_flywheel.py`,
  registered in the dispatcher Stop-chain after GK-08 `session_writeback.py`. At a frontier
  session's Stop it reads this session's PM-03 findings, classifies each (NEW/STRONGER/DUP/
  DISCARD), triages a destination (hard_rule/benchmark/prompt_fragment/asset/dataset_part),
  and writes each back idempotently (SHA-256) to the deposits ledger (+ Owner-promotable UKDL
  candidate for rule/trap; gated CO-05 `store_asset` for asset). Reports THROUGH CO-12, never
  a parallel metric. Gated on `PP_FRONTIER_SESSION` (T-FRONTIER-SESSION-DETECTION-001).
- **CO-12 fd_metrics** -- `co_12_telemetry.fd_metrics()` + folded into `readiness_report()`:
  fd_sessions_count / fd_frontier_calls_admitted / fd_admissions_declined / fd_rejection_rate
  / fd_deltas_extracted / fd_assets_written / fd_portability_slope_proxy, reading the same
  `signals.jsonl`. instrument-pending until the loop accrues on live frontier sessions.

**Done-gate cleared.** `tools/test_fable_distillation.py` = `DATASET_FAMILY_VERDICT=PASS`
(12/12) x3 hermetic. Live proof of Reality-Contract #2: on first frontier Stop the flywheel
distilled **7 real PM-03 findings** into classified deposits at
`~/.claude/state/fable_distillation/` (destinations asset/benchmark/dataset_part). Reality
#1: the gate REJECTS a Sonnet-sufficient / dataset-covered / mechanical task.

**Honest residual (CO-10):** activation is rung-2 advisory + rung-3 at the Stop boundary,
but LIVE requires the Owner Copy-Item of the canonical dispatcher + kclaude to their
`~/.claude/` mirrors (T-HOOK-DISPATCHER-DRIFT-001) -- the PP-internal half ships this turn;
the mirror step is the documented Owner registration (HR-001). No dependence-reduction figure
is claimed: CO-12 reads the fd_* metrics as instrument-pending until the loop runs across
many live sessions (Telemetry-Before-Claims).
