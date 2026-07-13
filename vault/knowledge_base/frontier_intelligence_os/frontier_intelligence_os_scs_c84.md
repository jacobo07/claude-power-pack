# SCS C84 — Frontier Intelligence Operating System (FIOS) — execution layer

**Sealed:** 2026-07-10 · **State:** Sealed (execution-first; live-path hooks Owner-gated)

## One line

The **execution layer** over the FD knowledge: FD-00…07 say *what* a frontier
distillation is; FIOS is the live code that **compiles** the session plan, **prices**
the tokens as R&D capital, and **evolves** the knowledge base — composing FD/CO/PM/GK,
forking none.

## What sealed

Reality scan of the Owner's 17-system, 5-layer proposal against all five parent
families (FD-00…07, CO-00…12, PM-01…05, GK-00…12, CDIO-00…05) found **3 genuinely-new ·
7 thin-extend · 5 covered**. STOP #1 approved **execution-first** (the genuine deltas
are code, not prose) → **3 engines + 1 doctrine index, zero new prose datasets.**

| Artifact | Carries |
|---|---|
| `modules/frontier_intelligence/session_compiler.py` | I-1⊕V-1⊕V-2 — declaration → 9-component `SESSION_ZERO_<iso>.md`; composes FD-00 gate + FD-07 floor + FD-02 axes |
| `modules/frontier_intelligence/token_irr.py` | III-2⊕III-3 — numeric IRR (immediate/reuse/compound/payback) + Frontier Dependence Index + balance sheet; feeds CO-12 |
| `modules/frontier_intelligence/evolution_engine.py` | IV-1 — whole-KB mutation proposals; Owner-gated, never auto-applies |
| `vault/knowledge_base/frontier_intelligence_os/FIOS_INDEX.md` | the doctrine index (5-layer overlap map + integration + scorecard) |
| `vault/knowledge_base/frontier_intelligence_os/pending_mutations.md` | live Owner-review queue (68 proposals from the real KB scan) |
| `tools/test_frontier_intelligence_os.py` | 13 V-gates, hermetic ×3 |

## UKDL sealed

- **`PR-FRONTIER-AS-RD-001`** — a frontier session is an R&D operation, not a query;
  compile first, writeback at close; Token IRR measures the return.
- **`T-FIOS-EVOLUTION-LOCK-001`** — the Dataset Evolution Engine proposes, never applies;
  every mutation to a sealed dataset is Owner-promoted by hand.

## Done-gate (observed evidence)

- `tools/test_frontier_intelligence_os.py` = **13/13, hermetic ×3** (identical each run).
- Baseline `tools/test_fable_distillation.py` = **12/12** (no regression).
- Live run: evolution engine produced **68 real proposals** on the actual KB; session
  compiler wrote a real `SESSION_ZERO`; token_irr reports honest 0 (empty per-repo
  ledger — no fake number).

## Honest residuals (CO-10)

- ~~Engines are advisory + fail-open (rung-1/2). Live-path wiring (kclaude preflight for
  the compiler, Stop-chain IRR emission) is the Owner-authorized EXECUTION-mode
  follow-up — same staging as PM-02's scheduler and FD-00's v2 hook.~~
  **CLOSED 2026-07-10** by the Addendum below. Engines are wired and live. This bullet is
  struck rather than deleted so the record shows the residual existed and was discharged.
- The evolution engine's `deprecate` signal reads a top-of-file banner window (600
  chars) to avoid prose false positives; `abstract`/`specialize` kinds are defined but
  not yet emitted (they need cross-family pattern detection — a v2 pass).
- The 7 thin-extends ship as sections/fields in the doctrine + compiler output, not
  standalone systems.

## Addendum -- live-path wiring (2026-07-10)

The engines are no longer advisory-only: both are wired to their live surface with the
FD-00/FD-07 pattern (no new plumbing).

| Surface | Wiring |
|---|---|
| kclaude preflight | `Invoke-FiosPreflight` (`tools/kclaude.ps1`) runs `session_compiler.py --preflight` when a session is FRONTIER (`PP_FRONTIER_SESSION=1`) AND an objective is declared (env `PP_SESSION_OBJECTIVE` or repo `.pp_frontier.json`) -> writes a `SESSION_ZERO` + prints a 3-line summary. No objective -> silent, no python spawn. |
| Stop-chain | `token_irr.py` gained `stop_entry()` + an argv-dispatch; added as a `PY_EXE` entry to `hooks/hook-dispatcher.js` Stop-chain, frontier-gated exactly like `fd_07_flywheel.py`. Emits `FIOS IRR: ...` via `systemMessage` + feeds CO-12. |

**Honest refinements over the literal wiring plan** (documented, not silently dropped):

- Preflight fires on frontier AND a declared objective, not every launch -- kclaude sets
  `PP_FRONTIER_SESSION=1` unconditionally, so per-launch firing would spam empty
  `SESSION_ZERO`s (the exact bloat `evolution_engine` flags, `PR-FABLE-DELTA-ONLY-001`).
- The IRR Stop is frontier-gated (like FD-07), not "every session" -- avoids a CO-12 signal
  per turn on bare sessions; a kclaude session IS frontier, so `/kclear` emits.
- `tokens_spent` at Stop = optional `PP_SESSION_TOKENS`, else unmeasured (0). The
  model-independence metrics (assets / FDI / reuse / balance sheet) need no token count.

**New V-gates:** `V-FIOS-PREFLIGHT-FIRES` / `-SILENT` / `-FAILOPEN`, `V-FIOS-IRR-ON-STOP`,
`V-FIOS-STOP-FRONTIER-GATE`, `V-FIOS-LIVE-PATH-WIRED` (`test_frontier_intelligence_os.py`,
19/19 hermetic ×3). UKDL: `T-FIOS-FRONTIER-SESSION-DETECT-001`.

**Owner-side residual (HR-001 / `T-HOOK-DISPATCHER-DRIFT-001`) -- DISCHARGED 2026-07-13.**
The canonical `hooks/hook-dispatcher.js` had to be `Copy-Item`-ed to
`~/.claude/hooks/hook-dispatcher.js` + /restart before the Stop entry could fire live. The
Owner did so: canonical and live are byte-identical (sha256
`1E08BB34616B2CE00F80DA27E1B5610DE771EA2E75714C8FB6F4EAAB84277212`), and the live file
carries the `token_irr` / `fd_07_flywheel` / `session_writeback` Stop entries. Verified by
hash, not by assumption.

## Liveness proof (2026-07-13 re-verification)

FIOS is not "wired on paper" -- it has run in production. Re-verified with an independent
check because the residuals above had gone stale and re-triggered an already-completed
wiring mission (see the trap below):

| Claim | Instrument | Result |
|---|---|---|
| Preflight is wired | `tools/kclaude.ps1` `Invoke-FiosPreflight` (line ~251) | present, frontier+objective gated, fail-open |
| Stop IRR is wired | `hooks/hook-dispatcher.js` Stop-chain `PY_EXE` entry | present (`token_irr.py`, 8000 ms) |
| Live path == canonical | sha256 of both dispatcher copies | identical -- no drift |
| Preflight really fires | `vault/sessions/SESSION_ZERO_*.md` | 6 real files from kclaude launches on 07-10 / 07-11 (test artifacts are hermetic and land in a temp dir, so these are production, not fixtures) |
| Gates hold | `tools/test_frontier_intelligence_os.py` | `FIOS_ACTIVATION_PASS=48/48`, exit 0 |
| Sealed upstream | `git rev-list --left-right --count origin/main...HEAD` | `0 0` |

**T-STALE-RESIDUAL-REGENERATES-MISSION-001.** A "Honest residuals" section that is not
updated when its addendum discharges it becomes a false NEXT. Here the residuals block still
read "live-path wiring is the follow-up" ten lines above an addendum stating the wiring had
shipped -- a self-contradicting document. A later session trusted the residual, not the
addendum, and re-planned a completed mission. **Rule:** when an addendum closes a residual,
strike the residual in the SAME commit; a document may not hold a residual and its discharge
simultaneously. The generalization is the estate's own law -- a handoff's NEXT is a
hypothesis about state, and state is verified on disk (`PR-LIVENESS-CHECK-BEFORE-SHIP-001`).

## Cross-ref

`FIOS_INDEX.md` · `ukdl-universal.md` (PR-FRONTIER-AS-RD-001, T-FIOS-EVOLUTION-LOCK-001,
T-FIOS-FRONTIER-SESSION-DETECT-001) · parents: `fable_distillation_scs_c82.md`,
`cognitive_os/COGNITIVE_OS_INDEX.md`.
