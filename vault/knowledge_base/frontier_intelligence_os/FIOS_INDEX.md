# Frontier Intelligence Operating System — Master Index (FIOS)

> Where the **Fable Advantage Distillation Suite** (FD-00…FD-07) is the *knowledge*
> — the doctrine that a frontier session must distill the delta and write it back —
> **FIOS is the live execution layer that runs that doctrine.** FD-00 tells a session
> *what a distillation event is*; FIOS is the executable that *walks the session
> across it*: it compiles the plan, prices the tokens as R&D capital, and evolves the
> knowledge base the sessions feed.
>
> **Central law (`PR-FRONTIER-AS-RD-001`):** *a frontier session is an R&D operation,
> not a query. Every token must produce a permanent asset that lowers the need for
> future frontier tokens. The Token IRR measures this; a session without a compiled
> plan and without a writeback is capital wasted.* Sealed in `ukdl-universal.md`.
>
> **Honesty rule (inherited from CO-10 / CO-12):** every engine reports through the
> **CO-12** instrument and computes **no** parallel dependence number; every metric is
> numeric with a data source, never an adjective. No advantage is *claimed* without its
> `(metric, source, value)` triple — else it is a hypothesis.
>
> **Scope approved by Owner 2026-07-10 (STOP #1, execution-first):** of **17 named
> systems across 5 layers**, evidence showed **3 genuinely-new · 7 thin-extend · 5
> covered** by FD/CO/PM/GK. The genuine deltas are **executable, not prose** — so FIOS
> ships as live engines + this one doctrine index, *zero* new prose datasets
> (writing prose that *describes* an execution layer would re-narrate FD/CO doctrine —
> the bloat GK-00 / SCS C41 / `PR-FABLE-DELTA-ONLY-001` forbid). Sealed as **SCS C84**.
>
> **Update (2026-07-21, CPCSC Tier-B B1):** **II-1 Unknown-Unknown Hunter** is promoted
> from thin-extend (🟡 "not built") to a **built engine** — `unknown_unknown_generator.py`.
> The NEW-engine count is now **4** (was 3); thin-extends **6** (was 7). It is the
> unmapped-space complement the harvester could not reach: `question_harvester` mines
> the gaps the estate ALREADY RECORDED, this generates the ones no record contains, as a
> structural asymmetry against a DISCOVERED peer cohort.

---

## The reality-scan verdict (why execution-first, not a dataset family)

The five parent families were read in full at STOP #1. **FD-00…07 already ARE the
Frontier Token Economics architecture** (sealed SCS C82), and its EXECUTION-mode code
(`fd_00_gate.py`, `fd_07_flywheel.py`) is live. The proposed FIOS layers therefore
mostly resolve to *"the executable that runs a doctrine FD already states."* The one
honest build is code where the delta is code, and a thin doctrine here — never 17
prose datasets narrating engines that do not execute (Scaffold Illusion, Mistake #16).

## The 5-layer overlap map (17 systems, evidence-based)

| Layer / system | Verdict | Parent (evidence) · genuine delta |
|---|---|---|
| **I-1 Session Orchestrator** ⊕ **V-1 Conversation Compiler** ⊕ **V-2 State Machine** | 🟢 **NEW (code)** | FD-00 is the *doctrine*; no executable ran it → `session_compiler.py`. State machine + declaration→plan folded in. |
| I-2 Budget Manager | ❌ COVERED | PM-04 Budget Auction + CO-09 loop_budget + CO-02 governor. 5-category split = a *field* in the plan. |
| I-3 Frontier Queue | ❌ COVERED | FD-02 *is* the ROI-ranked, dedup'd, dynamic question queue (III.13 ledger). |
| I-4 Session Replay Engine | 🟡 EXTEND | FD-07 momentum + C69 behavior audit. Post-session improvement report → §Thin-extends. |
| **II-1 Unknown-Unknown Hunter** | 🟢 **NEW (code)** | FD-02 targets *known* weak spots; the unmapped-space complement is now built → `unknown_unknown_generator.py` (structural absence vs a discovered peer cohort; composes the harvester's question shape + the FD-00 gate, forks neither). |
| II-2 Research Planner (multi-session) | 🟡 EXTEND | FD-07 cross-session; explicit campaign arc → plan's *escalation* field. |
| II-3 Critique Director | 🟡 EXTEND | FD-02 critique archetype + CDIO-05 six-lens; pre-question critique on cheap rungs → §Thin-extends. |
| **III-1 Cognitive Asset Ledger** | ❌ COVERED | `fd_07_flywheel.py` deposits ledger already catalogs assets by destination + FD-04 decay. |
| **III-2 Token IRR Calculator** ⊕ **III-3 Balance Sheet** | 🟢 **NEW (code)** | IRR/payback/reuse-multiplier + Frontier Dependence Index — numeric, over CO-12's adoption framing → `token_irr.py`. |
| **IV-1 Dataset Evolution Engine** | 🟢 **NEW (code)** | Whole-KB mutation proposals; FD-06 mutates *assets*, GK-07 *graph*, cdio-librarian *CDIO-only* — none does whole-KB → `evolution_engine.py`. |
| IV-2 Knowledge Emergence Detector | 🟡 EXTEND | GK-03/04 graph synthesis → §Thin-extends. |
| IV-3 Frontier Theory Compiler | 🟡 EXTEND | FD-03 transmutation; N→patterns→law cross-deposit abstraction → §Thin-extends. |
| IV-4 Meta-Learning Engine | 🟡 EXTEND | CO-12 + FD-02 III.4; which archetypes/domains yield most assets → §Thin-extends. |
| V-2 Session State Machine | ❌ COVERED | FD-00 8 stages + FD-07 9 stages; folded into I-1's rendered plan. |
| V-3 Conversation Graph | 🟡 EXTEND | GK-03/04 graph machinery, session-scoped → §Thin-extends. |

**Tally:** 4 NEW (built as code) · 6 thin-EXTEND (sections/fields, below) · 5 COVERED.

## Family tree (what actually ships)

```
FD-00..07 (knowledge) + CO-00..12 + PM-01..05 + GK-00..12   ← PARENT SUBSTRATE (composed, never rebuilt)
│
└── FIOS — Frontier Intelligence OS (execution layer)        ← this build
    ├── modules/frontier_intelligence/session_compiler.py           (I-1⊕V-1⊕V-2)  declaration → SESSION_ZERO plan
    ├── modules/frontier_intelligence/unknown_unknown_generator.py  (II-1)         structural-absence questions → the plan
    ├── modules/frontier_intelligence/token_irr.py                  (III-2⊕III-3)  frontier tokens as R&D capital → CO-12
    ├── modules/frontier_intelligence/evolution_engine.py           (IV-1)         KB mutation proposals, Owner-gated
    └── vault/knowledge_base/frontier_intelligence_os/              this index + pending_mutations.md (Owner review queue)
```

## The 4 engines — contracts and integration

**`session_compiler.py`** — inputs: a `SessionDeclaration` (objective, constraints,
unknowns, candidate questions, repo, token budget). Composes: FD-00 `check_admission`
(question worthiness) + FD-07 `_load_deposits` (the repo floor) + the FD-02 leverage
axes (order only). Output: a 9-component `SESSION_ZERO_<iso>.md` — minimal context
(<2000 tok), ROI-ranked questions, optimal order, 5-category budget, next-session
escalation, early-stop/saturation criteria, writeback plan, distillation plan,
Opus/Claude-Code transfer plan — plus the binary state machine. **Fail-open.**

**`unknown_unknown_generator.py`** (II-1) — inputs: a DISCOVERED peer cohort (file paths
found by the caller's own glob, never a curated list) + a feature detector. Composes:
the harvester's `HarvestedQuestion` shape (so its output flows into the same
`SessionDeclaration.candidate_questions`) + the FD-00 admission gate (a proposed
unknown-unknown the floor already covers is DECLINE'd there, correctly). Output:
`UnknownUnknown` questions from majority-absence asymmetries — a feature ≥75 % of a
cohort's peers carry that one peer lacks, the gap no record names because absence leaves
none. **Distinct from `question_harvester` (I-4 intake):** the harvester reads gaps the
estate WROTE DOWN; this finds gaps its own structure IMPLIES. Silent on a uniform cohort
(0 findings — never manufactures one), loud on the odd sibling out. Deterministic,
zero-model, **fail-open ABSOLUTE**. It only PROPOSES; it also seeds A2 (Theory Generator)
as a build dependency (CPCSC Tier-B B1).

**`token_irr.py`** — reads the FD-07 deposits ledger + CO-12 `fd_metrics`. Emits
numeric `immediate_roi`, `reuse_multiplier`, `compound_roi`, `payback_tokens`, and the
**Frontier Dependence Index** (frontier-only ÷ total), plus the III-3 balance sheet
(assets by type vs frontier-dependence + DUP liabilities). **Feeds CO-12** via
`record_signal("fios_token_irr", …)` — one more producer into the single instrument,
never a parallel accountant (FD-07 Invariant 1).

**`evolution_engine.py`** — scans every KB dataset for cheap deterministic health
signals and proposes typed mutations (compress / split / merge / reinforce / deprecate
/ abstract / specialize) to `pending_mutations.md`. **Never applies one**
(`T-FIOS-EVOLUTION-LOCK-001`) — the Owner promotes by hand, mirroring the
cdio-standards-librarian and graphify agents.

## Thin-extends — shipped as fields/sections, not standalone systems

- **Session Replay (I-4)** → the plan's early-stop criteria + a future `token_irr`
  session-delta comparison; rides FD-07 momentum + C69.
- **Research Planner (II-2)** → the plan's *next-session escalation* field.
- **Critique Director (II-3)** → the plan's *critique* budget category + FD-02's
  critique archetype run on a cheap rung before the frontier question.
- **Emergence (IV-2) / Theory Compiler (IV-3) / Meta-Learning (IV-4) / Conversation
  Graph (V-3)** → documented as the evolution engine's and GK graph's future analytic
  passes; each is a thin analytic delta over existing graph/telemetry, not a new system.

*(II-1 Unknown-Unknown Hunter left this list on 2026-07-21 — it is now a built engine, above.)*

## V-gates (done-gate) — honest scorecard

`tools/test_frontier_intelligence_os.py` = the 3-engine core suite, hermetic ×3.
`tools/test_unknown_unknown_generator.py` = **8/8, hermetic ×3** (II-1):

| Gate | Status | Evidence |
|---|---|---|
| V-FIOS-NO-DUPLICATE-FD | ✅ | each engine imports/composes its FD/CO parent; IRR stands up no parallel router/metric |
| V-FIOS-SESSION-COMPILE / -UNDER-2K / -BUDGET | ✅ | 9 components render; frontier-worthy question ranks #1; context <2000 tok; budget sums |
| V-FIOS-TOKEN-IRR-NUMERIC / -BALANCE-SHEET / -FEEDS-CO12 | ✅ | numeric IRR; FDI ∈ [0,1]; `fios_token_irr` accrues in CO-12 (feed, not fork) |
| V-FIOS-EVOLUTION-PROPOSES / -LOCK | ✅ | typed mutations surfaced; **0** source datasets mutated |
| V-UUG-MAJORITY-ABSENCE | ✅ | a feature in 4/5 peers, absent in 1 → exactly that peer flagged |
| V-UUG-UNANIMOUS-SILENT / -MINORITY-NOT-FLAGGED | ✅ | universal feature → 0 findings; a minority feature's absence is NOT a gap |
| V-UUG-DISCOVERED-COHORT | ✅ | the odd-one-out file surfaced from a real, filesystem-discovered cohort |
| V-UUG-FAIL-OPEN / -QUESTION-SHAPE / -DETERMINISTIC | ✅ | raises → []; pipeline-shaped (`uu:` fp, asdict); identical on re-run |
| *-FAILOPEN / V-BASELINE | ✅ | pathological input → no raise; `test_fable_distillation.py` 12/12 unaffected |

**No V-DEPTH gate:** execution-first ships code, not prose datasets — depth is proven
by behavior, not word count. This index is a doctrine index, not a 2500-word/Part
dataset.

## Honest residuals (CO-10, never hidden)

- The engines are **advisory + fail-open** (rung-1/2): `session_compiler` is invoked by
  hand or a future kclaude preflight hook; `unknown_unknown_generator` is CLI-invokable
  and produces pipeline-shaped questions — its **auto-wiring into the harvest/compile
  flow** (a `generate()` call alongside `harvest()` at the compiler's intake) is the
  natural next integration, deferred here to avoid touching the compiler flow in the B1
  commit; `token_irr` feeds CO-12 when a caller wires it; `evolution_engine` proposes on
  demand. Live-path hook wiring is the Owner-authorized EXECUTION-mode follow-up.
- The 6 thin-extends are **fields/sections**, not full engines; each is a genuine but
  small delta and is recorded here rather than inflated into a dataset.

## The fundamental property

> **Run the doctrine; do not re-narrate it.** FD knows *what* a distillation is; FIOS
> *executes* the session, *prices* the tokens as R&D capital, *hunts the gaps no record
> holds*, and *evolves* the knowledge base — composing FD/CO/PM/GK, forking none. Every
> metric is numeric with a source; every mutation is Owner-gated; every engine fails
> open. It is code on disk that runs, plus one doctrine — no prose engine that only
> describes, no magic promised.
