# Roadmap: Perf Construction ("va lento al crear") — GEX44 workstream

Plan of record: the inline plan approved by the Owner ("y", 2026-11-22, laptop pane 8fd6ace9).
Wave 0 evidence so far: `vault/audits/perf_campaign_w0_reality.md` (copied into this clone).

Principle: optimise for less REPEATED work at equal or higher quality, never for less engineering.
Every number names its instrument, its plane (GEX44 or laptop) and its sample size. UNKNOWN is never PASS,
TIMED_OUT/FAILED stay in the denominator, a skipped gate is never a passed gate.

## Operating constraints (every phase)

- This clone lives on GEX44 (`~/missions/perf-construction`, branch `mission/perf-construction`).
  Commit by explicit pathspec on this branch; the commits ARE the hand-back (the laptop fetches the branch).
  Do not push. Never touch `/home/kobii/.claude/skills/claude-power-pack` (live install) or another mission's dir.
- Never edit `~/.claude/settings.json`, `~/.claude/rules/`, `~/.claude/CLAUDE.md` or credentials.
- Model calls only on this host's subscription quota. If `ANTHROPIC_API_KEY` is set, STOP the phase, record BLOCKED.
- Never ask the Owner mid-run: write the blocker into the phase EVIDENCE.md, mark the phase BLOCKED/UNJUDGED, continue.
- PLANE RULE: the Owner's complaint is the LAPTOP. Anything that judges laptop hooks, laptop RAM, laptop
  transcripts or laptop `~/.claude` is LAPTOP-ONLY: write the procedure and the falsifier, mark it
  `LAPTOP-ONLY / UNJUDGED`, never substitute a GEX44 number for it.
- Reuse owners, never build a second one: bench_all, verify_bench_all, measure_hook_event, measure_session_start,
  resource_admission, route_admission, work_class_profile, cost_to_completion, modules/trace_context,
  modules/capability_runtime. BUILD only with a written reason why EXTEND/CONNECT fails.
- Each phase ends with `phases/NN-*/EVIDENCE.md`: commands, exit codes, verdicts, P-ids touched.

## Phases

- [x] **Phase 1: Reality and ownership** - classify P01-P40 by code reading, locate UCR-CIF + Baseline Ratchet owners, decide D1
- [x] **Phase 2: Benchmark integrity** - fix confirmed metrology defects (P01, P03, P04, P06, P07) in their owners, with falsifying tests
- [x] **Phase 3: Construction metrology contract** - TTFMC / TTFUR / TTVD events + p50/p90/p95 with censored samples, in existing owners
- [x] **Phase 4: Host-pressure admission** - resource_admission judges real free RAM / process count and separates slow-component from slow-host
- [x] **Phase 5: Critical-path audit** - which Stop/PostToolUse work is deferrable without moving any blocking control; laptop procedure written
- [x] **Phase 6: Ratchet, UKDL and hand-back** - inheritance proof, HR/PR/Trap entries, meta-analysis, laptop-only checklist

### Phase 1: Reality and ownership

**Goal**: A verified world model so no later phase builds on an assumption.
**Depends on**: Nothing
**Requirements**: PERF-01
**Success Criteria** (what must be TRUE):

  1. `EVIDENCE.md` holds a table P01-P40, each CONFIRMED_ACTIVE / HISTORICAL_FIXED / PARTIALLY_FIXED / SUPERSEDED /
     FALSIFIED / UNKNOWN / NOT_APPLICABLE / LAPTOP-ONLY, each with file:line or command evidence.
  2. The owner (path) of UCR-CIF and of the Constitutive Baseline Ratchet is named, or recorded as NOT FOUND with the searches run.
  3. D1 (does the construction contract extend trace_context or capability_runtime) is decided from their real consumers.
  4. `C:\Users\User\Downloads\Promptsss\...\iteracion-avanzada-universal.txt` is not on this host: record UNAVAILABLE, do not invent it.

**Plans**: 2 plans

Plans:

- [x] 01-01-PLAN.md - tracer (phase-local evidence checker + EVIDENCE.md v0), P-id definition census, judge the defined P-ids by code reading
- [x] 01-02-PLAN.md - locate UCR-CIF and Baseline Ratchet owners, decide D1 from real consumers, record UNAVAILABLE input, close verdict

### Phase 2: Benchmark integrity

**Goal**: bench_all / verify_bench_all cannot report success they did not earn.
**Depends on**: Phase 1
**Requirements**: PERF-02
**Success Criteria** (what must be TRUE):

  1. Four separate verdicts per metric: instrument_ran, met_target, regressed, evidence_sufficient. A FAILED or
     TIMED_OUT sample never counts as a fast sample (P03); exit code is non-zero when a primary metric misses its absolute target (P01).
  2. verify_bench_all keeps `min` as the labelled potential floor and adds p50/p95 (P04); regression compares against a
     host-state-matched window, not only the previous run (P06).
  3. Each fix has a test that FAILS on the pre-fix code (mutation/negative control) and passes after. Recorded verbatim.
  4. Existing gates of the touched owners still pass.

**Plans**: 3/3 plans executed

Plans:

- [x] 02-01-PLAN.md - bench_all: FAILED/TIMED_OUT samples never count as fast at all 15 sample sites (P03), non-zero exit on a missed absolute target and the progress tag fix (P01)
- [x] 02-02-PLAN.md - verify_bench_all: min kept as the labelled potential floor plus p50/p95 (P04), failed retry reported UNCONFIRMED, in-band absolute misses reported (P03 gate side)
- [x] 02-03-PLAN.md - host-state-matched regression window (P06), four verdicts per metric with the exit derived from them, integrity suite wired into the bench-gate row, live smoke, phase evidence (P07 recorded BLOCKED-ON-ORIGIN-AUDIT)

### Phase 3: Construction metrology contract

**Goal**: The time a construction takes is measured, not guessed.
**Depends on**: Phase 2
**Requirements**: PERF-03
**Success Criteria** (what must be TRUE):

  1. Start/end points of TTFMC, TTFUR, TTVD defined in writing; implemented as events in the owner chosen by D1.
  2. Distribution report (p50/p90/p95, N, censored count) runs over real transcripts of THIS host and says GEX44 plane.
  3. States MEASURED / FAILED / TIMED_OUT / INCONCLUSIVE / SKIPPED_BY_POLICY / NOT_APPLICABLE / UNOBSERVED / UNAVAILABLE reachable, each tested.

### Phase 4: Host-pressure admission

**Goal**: Work is admitted against the host's real state; a starved host is reported as such.
**Depends on**: Phase 2
**Requirements**: PERF-04
**Success Criteria** (what must be TRUE):

  1. resource_admission reads free RAM and live claude process count and returns RED below a declared floor, with a test from both poles.
  2. Every benchmark sample carries the host state; samples under RED are INCONCLUSIVE for regression purposes.
  3. Laptop evidence (28 claude.exe, 12 revived in one minute, 275-1563 MB free) is cited as the motivating case, LAPTOP-ONLY.

### Phase 5: Critical-path audit

**Goal**: Name what runs synchronously while the user waits and what could move.
**Depends on**: Phase 3, Phase 4
**Requirements**: PERF-05
**Success Criteria** (what must be TRUE):

  1. Inventory of hooks per event from the repo's hook registry, each classed BLOCKING-SAFETY / DEFERRABLE / UNKNOWN.
  2. Any change moves only DEFERRABLE work and keeps `tools/test_hook_boundary.py` green.
  3. A laptop measurement procedure (before/after, host-state matched) is written and marked LAPTOP-ONLY / UNJUDGED.

### Phase 6: Ratchet, UKDL and hand-back

**Goal**: What was proven is inherited; what was not is said plainly.
**Depends on**: Phase 5
**Requirements**: PERF-06
**Success Criteria** (what must be TRUE):

  1. UKDL candidates (HR/PR/Trap) appended to a candidate file, no shared aggregate edited; each with evidence and scope.
  2. Ratchet entry connected to the real owner from Phase 1, or BLOCKED with reason.
  3. HANDOFF.md: owner summary, engineering handoff, laptop-only checklist, known unknowns, exact next task.
