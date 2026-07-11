# DRK Wiring + Proactive Mode — plan (2026-07-11)

Mode: **EXECUTION** (Owner-declared). Composition of sealed systems; no new architecture.
Closes the one honest residual of the DRK build: the kernel composed *injected* provider
verdicts (fixture-tested) and no adapter called the real modules.

## PASO -1 — PROVIDER SIGNATURE MAP (verified, blocking, HR-PREMISE-001)

| Provider | Location | Entrypoint (verified) | Output | Compat |
|---|---|---|---|---|
| precedent | `modules/arch-decision/arch_check.py` | no library fn; compose `load_index` + `load_vocab` + `extract_signals` + `rank_sources` + `decide_verdict` | `COLLISION`/`WARNING`/`CLEAR` + per-source `is_veto` | adapter needed — **hyphenated dir, not importable**; use `importlib.spec_from_file_location` |
| placement | `modules/duplicate_to_advantage/d2a_engine.py` | `run(Proposal(description, name)) -> D2AVerdict` | `.recommended.operation`, `.dupe.coverage_pct` | compatible |
| evidence | `modules/fable_distillation/epistemic_ladder.py` | `epistemic_level(fingerprint, repo, *, state_dir) -> "E0".."E6"` | E-level | adapter + **semantic limit** |
| tier | `modules/spec_gate/gate.py` | `classify_tier(description) -> TierResult` | `tier` 0..3 | compatible (advisory tier-raiser) |
| routing | `modules/cost_collapse/router.py` | `route(description) -> RouteResult` | `route_class`, `max_budget` | compatible (self-cost) |
| queue | `modules/owner_queue/owner_queue.py` | `append(action, command, *, component, source, state_dir) -> id` | row id | compatible, hermetic via `state_dir` |

**Premises the request asserted that are FALSE (caught before writing code):**
1. `DecisionKernel` class does not exist — the entrypoint is `review_decision(obj, *, precedent, placement, registry, ts)`.
2. `modules/acis/` does not exist — the ladder lives in `modules/fable_distillation/`.
3. `epistemic_level` is keyed by **FD deposit fingerprint**, not evidence text. It returns `E0`
   for any unknown fingerprint. It therefore CANNOT level arbitrary evidence. The adapter resolves
   a level ONLY when `Evidence.source` names a real deposit fingerprint; otherwise `None` and the
   caller's `acis_level` is left untouched. Inventing a level here would be exactly the fabrication
   ACIS's No-Autopromotion invariant forbids.

**D1 Liveness:** `default_registry()` holds 5 rows; **DRK has none** — added by W3.

## W1 — Live provider adapters (`modules/decision_review/providers.py`)

One adapter per verified provider. Each: converts the real output to the kernel's contract,
fail-open to `None` (never raises), own wall-clock budget so a slow provider cannot stall a
review. `resolve_all(obj)` returns `{precedent, placement, evidence_levels, tier, route}`.
`review_decision` gains `providers=None` — when `precedent`/`placement` are not injected and
`providers` is truthy, it resolves them live. Injection still wins (tests stay hermetic).

Done-gate: a real proposal produces a verdict from live providers; disabling one provider still
yields a verdict from the rest.

## W2 — Proactive scanner (`modules/decision_review/proactive_scanner.py`)

`scan_repo(repo_root) -> list[ProactiveSuggestion]`. Detectors, each grounded in an EXISTING
system (no new signals invented):
- **orphan** — `liveness.audit()` rows whose verdict is non-LIVE (WIRED-BUT-SILENT/DRIFTED/ORPHANED).
- **dead-knowledge** — `recall_roi.retirement_candidates()` (kb_injection < 1 in the window).
- **owner-residual** — `owner_queue.pending()` rows aged past the grace window.
- **decision_needed** — an architecture decision implicit in the repo with no Decision Record:
  a `modules/<x>/` package with no `DEC-` citation in the registry, cross-checked against the
  registry's recorded statements. Evidence = the real path.
- **debt** — a suggestion whose kernel-computed blast radius is high.

Urgency `high` ONLY when the blast radius is verifiably high (kernel-computed, not guessed).
Every suggestion carries `evidence` naming a real path/row — no evidence, no suggestion
(T-DRK-PROACTIVE-NOISE-001). Fail-open per detector: one failing detector is skipped, the scan
continues. Never blocks.

Activation: **Option B — Scheduled Task** (daily). Rationale over A and C: the SessionStart hub
is already the most contended surface (JIT + AKOS + hub reads) and a scan there taxes every
session start; the Stop chain already carries FD-07 + token_irr and a scan there taxes every turn.
A daily out-of-band task has **zero** interference with the interactive flow — which is the
constraint the request states ("el scanner nunca bloquea el flujo de trabajo").

Output: `vault/audits/drk_proactive_<date>.md`, ordered by urgency. High-urgency findings are
appended to the OWNER_QUEUE via `owner_queue.append()` (the existing API — no new channel).

## W3 — Integration with OWNER_QUEUE + D1 Liveness

- High-urgency → `owner_queue.append(action, command, component=..., source="drk-proactive")`.
- Add two rows to `liveness.default_registry()`: `drk-kernel` (file-mtime on the decision
  registry JSONL — LIVE iff a decision was actually reviewed recently) and `drk-proactive`
  (file-mtime on `vault/audits/drk_proactive_*.md`). If nobody reviews a decision, DRK reports
  WIRED-BUT-SILENT — which is the truth, and exactly what D1 is for.

## W4 — Tests + Seal

Add to `tools/test_decision_review.py`: `V-DRK-PROVIDERS-LIVE`, `V-DRK-FAILOPEN-PROVIDER`,
`V-DRK-SCANNER-RUNS`, `V-DRK-SCANNER-EVIDENCE`, `V-DRK-QUEUE-INTEGRATION`, `V-DRK-LIVENESS-ENTRY`.
All hermetic ×3. UKDL: `T-DRK-PROACTIVE-NOISE-001`. Push → `REMOTE_DELTA = 0 0`.
