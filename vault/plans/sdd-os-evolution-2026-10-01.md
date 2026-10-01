---
title: SDD-OS evolution — from spec-existence check to ready-spec, risk-tiered, enforced, traced
date: 2026-10-01
status: PROPOSED (ultra phase 1; awaiting Owner answers to phase-2 questions)
base: feature/knowledge-acquisition @ a3513d0
evidence: wiki/syntheses/sdd-os-gap-analysis.md, wiki/tools/sdd_probe.py, scratchpad research/owners_*.md
---

# Plan — SDD-OS evolution (ultra phase 1)

## Mode decision

ULTRA-PLAN for this turn only. Two decisions span owners: the enforcement boundary, and which
existing state owner carries a change through to closure. Everything after Owner answers runs in
EXECUTION mode in micro-batches of 5 files or fewer. Evidence: every capability the mission needs
already has an owner (table below); the remaining work is wiring plus about four small semantic
extensions, not new architecture.

## Reality scan — verified at a3513d0

- Defects D1–D6 (`wiki/syntheses/sdd-os-gap-analysis.md`) all reproduce at HEAD
  (`wiki/tools/sdd_probe.py`, with a no-spec control).
- Injections: 4,218 fires across 4,097 distinct prompt keys. Records hold only
  `last_fire / last_advisory / fire_count`, so delivery is observable and compliance is not.
- No hook references sdd_os, spec_gate or pre_exec_gate. Enforcement edge: none.
- Live install drift: `~/.claude/hooks/zero-issue-gate.js` is 18.5 KB live vs 32.2 KB in the repo;
  `hook-dispatcher.js` also differs. Commands: 29 live vs 90 in the repo. `install-global.ps1` has
  never been applied (agent dry run: would install 73, update 3).
- Concurrency: another writer commits every few minutes. 657 dirty paths, 13 worktrees.
  `hooks/hook-dispatcher.js` carries foreign uncommitted changes.
- Unmerged owners: `ucr-cif/construction` (77 commits), goal-spine (11 + 2).
- Evidence re-graded:
  - Gloaguen 2602.11988: context files; success deltas not significant (p=.87/.37); cost
    +20–23% (p<.001); Python, Sonnet 4.5 / GPT-5.x / Qwen. About repo context files, not specs.
  - TDAD 2603.17973: Qwen3 open-weight models only.
  - Neither tests spec workflows.
- A historical ON/OFF comparison is not supportable: ~300 transcripts predate SDD-OS vs ~3,100 after,
  with different work and models. Measurement must be prospective, or a replay of fixed cases.

## Owner dispositions

| capability | owner | disposition |
|---|---|---|
| task→spec binding, readiness | `modules/sdd_os/spec_binding.py` | EXTEND (readiness predicate, binding strength, tier reconciliation) |
| tier / risk | `modules/spec_gate/gate.py::classify_tier` (+ contract `spec_depth_selection.json`) | EXTEND (risk dimensions, stemming, visible UNASSESSED) |
| directive + decision | `modules/sdd_os/pre_exec_gate.py`, `activation.py` | EXTEND (decision taxonomy, five-field contract, UNJUDGEABLE) |
| binding-strength vocabulary | `modules/rule_compiler/schema.py` Binding | REUSE (ADVISORY / WARN / REQUIRE_EVIDENCE / BLOCK_BUILD / REQUIRE_HUMAN_AUTHORIZATION) |
| write boundary | PreToolUse Edit/Write chain (`hook-dispatcher.js`; `zero-fiction-gate.js:146` is the "ask" precedent) | CONNECT (one new chain member, shadow first) |
| change identity, obligations, tree-bound closure, independent judge, anti-thrash | `modules/gsd_x/goal/*` (CAS log, `revision_of`, `goal_closure(tree_hash)`, judge, `info_key`) | CONNECT (spec → goal obligations adapter); no new state store |
| requirement → evidence join | `modules/intent_verified` | EXTEND (AC ids with runnable `verify`; evidence stamped with a tree hash) |
| affected suites | `tools/change_impact.py` | CONNECT (suggest the must-still-pass set) |
| ratchet | `vault/governance/mutation_ratchet.json` + `tools/mutation_drill.py`; named-set pattern | REUSE (kill floors for the new guards) |
| liveness | `modules/liveness`, reachability registry | REUSE (declare and wire every new module) |
| UKDL / CEPS | `vault/knowledge_base/ukdl-universal.md`, `tools/ceps.py` | REUSE (one trap per defect class, deduped) |
| old any-file gate | `spec_gate.check_spec_gate` (callers: one_shot, sdd_tier, dataset_first, …) | RETIRE from SDD decisions; leave other callers untouched (out of scope) |
| Graphify requirement edges, CIR, baseline DB, attestations, MVCC, OTel, spec IR compiler, /loops | — | NOT BUILT (no residue this slice needs; recorded as follow-ups) |

## Residue that is genuinely missing (small)

1. **Readiness predicate.** Machine-readable front matter is the minimal "IR"; no compiler.
   - `status: ready`;
   - `open_questions` items each RESOLVED | ASSUMED(evidence) | OWNER_DECISION | RESEARCH | BLOCKING;
     any OWNER_DECISION, RESEARCH or BLOCKING item means not ready;
   - `scope` paths;
   - `acceptance` items each with a runnable `verify` command (the falsifier);
   - `must_still_pass` (commands, or "none: reason");
   - `checkpoints` (required at T3).

   Empty, blank and missing fields are distinct states, never "ok".
2. **Binding strength:** STRONG / WEAK (single generic token) / AMBIGUOUS (more than one candidate)
   / STALE (scope paths changed since the spec was verified) / UNBOUND. Never silent newest-wins
   for an ambiguous match.
3. **Risk escalators** (conjunctive and hard, not a score):
   - destructive data (drop, delete, truncate, migrate, purge);
   - public contract (public, SDK, API, breaking, schema, signature);
   - auth/permissions/secrets;
   - production/deploy;
   - irreversible external side effects.

   Plus stemming. No signal gives T1 with `risk=UNASSESSED` recorded, which is never T0.
4. **Decision ledger** (append-only, telemetry not authority). Records prompt key, tier, risk,
   binding, readiness and decision; PreToolUse adds the first-write outcome. This is the producer
   for "injected vs followed vs ignored vs UNJUDGEABLE" and the measurement denominator.
5. **Spec → goal adapter.** A ready spec's acceptance items become GSD X goal obligations with
   pinned verify gates; closure goes through `goal_closure(tree_hash)` and the judge (the closer is
   not the implementer).

## Waves and expected micro-commits

| wave | content | commit(s) |
|---|---|---|
| W0 | research record: `wiki/` + my `CLAUDE.md` hunk (provenance verified, single-author); this plan | `docs(wiki): …`, `docs(plans): …` |
| W1 | replay corpus (~40 labelled prompts + binding/readiness cases, incl. D1–D6) as V-gates; baseline run records current failures by name | `test(sdd-os): replay corpus …` |
| W2 | risk classifier (gate.py) — report false-downgrade AND false-escalation on the corpus | `feat(spec-gate): risk escalators …` |
| W3 | readiness predicate + binding strength + tier reconciliation + legacy migration lint | 2 commits (readiness; binding) |
| W4 | decision taxonomy + 5-field directive + decision ledger (producer) + report (consumer) | 1–2 commits |
| W5 | PreToolUse write gate in SHADOW (would-block logged; UNJUDGEABLE ≠ ALLOW for high risk); kill switch; mutation drills | 1 commit + live install step |
| W6 | spec → GSD goal adapter; intent_verified AC ids + tree stamp; vertical slice = this mission's own ready spec driven to judged closure | 2 commits |
| W7 | UKDL traps, mutation-ratchet floors, liveness declarations, wiki + handoff, final git audit | 2–3 commits |

## Validation (Production Reality)

- Replay corpus: D1–D6 flip for the right reason; legitimate cases stay PROCEED.
- Classifier error is reported both ways.
- Mutation drills on: the ready predicate, tier reconciliation, the UNJUDGEABLE guard, ambiguous
  binding, and the empty-denominator guard. Each must be KILLED; floors go to the mutation ratchet.
- Live proof: the hook copy in `~/.claude` fires in a real session (ledger line with a session id),
  not just the repo copy under test.
- `python modules/liveness/reachability.py` exits 0 with no new orphans; `test_sdd_os*` green.
- The vertical slice reaches a judge verdict on the current tree.

## Rollback

Every wave is its own commit. The write gate is shadow by default, with kill switch
`CLAUDE_SDD_WRITE_GATE=off` and a mode variable. Activation stays fail-open for low risk. Legacy
specs keep binding (warned) during the migration window.

## Deliberately not built

A second graph, a CIR owner, a baseline database, cryptographic attestations, MVCC/leases, OTel
export, a spec IR compiler or DSL, /loops, a Golden Path system, UCR-CIF promotion (its owner sits on
an unmerged branch).

## Phase 2 — Owner answers (2026-10-01: "rec, y")

1. Enforcement: shadow first, then ask (REQUIRE_HUMAN_AUTHORIZATION) for T3 and for high-risk T2
   (destructive data / public contract) once the corpus shows a low false-positive rate. Ordinary
   T2 gets WARN.
2. Live install: option (b), a separate `settings.json` entry. No edit to the foreign-dirty
   `hook-dispatcher.js`. The entry points at the **repo file directly**, so live == repo by
   construction. `install-global.ps1` is NOT run (Owner follow-up).
3. Holdout: built, default **0%** (no recommendation was given; withholding governance is the
   Owner's switch).
4. Legacy specs keep binding with a NOT-READY warning (action stays `proceed`, readiness=`LEGACY`).
5. UCR-CIF promotion, CIR, Graphify requirement edges and Spec Kit stay out of scope (follow-ups).
6. Pathspec-scoped commits per wave; `knowledge/PORTFOLIO_LEARNINGS.md` excluded (mixed
   provenance); one push at the end (the branch carries another writer's commits; the push grant
   in memory covers `main`).

## Phase 3 — Revised plan (numbered tasks)

| # | file | action | purpose | verification |
|---|---|---|---|---|
| 0a | `wiki/**`, `CLAUDE.md` (my hunk only) | commit | record the research | `git show --stat` contains only these paths; CLAUDE.md diff is one hunk |
| 0b | `vault/plans/sdd-os-evolution-2026-10-01.md` | commit | the plan | same |
| 1 | `fixtures/sdd_os/replay_corpus.json` | create | ~40 labelled prompts (expected tier floor and ceiling, risk dims) + binding/readiness cases incl. D1–D6 | loads; every case has an expected value |
| 2 | `tools/test_sdd_os_evolution.py` | create | V-SDDEVO-* gates over the corpus: tier accuracy (false-downgrade AND false-escalation counts, empty-denominator guard), binding, readiness, decision, write gate | baseline run at HEAD names the failing cases (expected red before W2–W5) |
| 3 | `modules/spec_gate/gate.py` | edit | `classify_tier`: plural/stem match; risk escalators (destructive data, public contract, auth/secrets, production, irreversible external) floor T2; destructive+production → T3; doc-only typo/wording with no escalator → T0; `TierResult` gains `risk_dims`, `risk_assessed` (backward-compatible defaults) | corpus: 0 false downgrades on the labelled high-risk set; false escalations reported |
| 4 | `modules/sdd_os/readiness.py` | create | `assess(spec_path, task_tier)` → Readiness(state READY / NOT_READY / LEGACY, missing, blocking, spec_tier); fields `status`, `open_questions` (RESOLVED/ASSUMED/NONE vs BLOCKING/OWNER/RESEARCH), `scope`, `verify`, `must_still_pass`, `checkpoints` (T3); `tier` accepts `2` or `T2`; missing ≠ none | unit gates incl. D1 empty-draft → NOT_READY |
| 5 | `modules/sdd_os/spec_binding.py` | edit | `strength` STRONG / WEAK / AMBIGUOUS / REFERENCED; explicit path reference wins; equal-strength ties across specs → AMBIGUOUS (no newest-wins) | D2 → WEAK, not proceed |
| 6 | `modules/sdd_os/pre_exec_gate.py` | edit | decision: proceed only when STRONG/REFERENCED + READY (or LEGACY with warning); new actions `spec_not_ready`, `binding_weak`, `binding_ambiguous`; five-field directive; tier reconciliation | corpus decision gates; existing `test_sdd_os*.py` stay green |
| 7 | `modules/sdd_os/activation.py` | edit | write the per-session decision state (`~/.claude/state/sdd-os/session/<sid>.json`) and append to the decision ledger (`~/.claude/state/sdd-os/decisions.jsonl`) on every task prompt, even when throttled; holdout flag (env/config, default 0); docstring law narrowed to "never writes specs" | ledger line for a real prompt |
| 8 | `tools/jit_skill_loader.py` | edit (1 line) | pass `session_id` to `build_directive` | activation test |
| 9 | `hooks/sdd_write_gate.py` | create | PreToolUse Write/Edit: read the session state; spec paths exempt; requirement + not ready → re-evaluate → shadow logs `would_block`; enforce mode → `ask` for T3/high-risk; internal error on a high-risk record → `ask` (UNJUDGEABLE ≠ ALLOW); no state → `unjudgeable_no_state` logged, allow; kill switch `CLAUDE_SDD_WRITE_GATE=off`, mode `CLAUDE_SDD_WRITE_GATE_MODE=shadow` | hook-level gates feed real JSON on stdin |
| 10 | `~/.claude/settings.json` | edit (Owner-side if the classifier blocks) | add a `Write\|Edit\|MultiEdit` entry → python.exe repo `hooks/sdd_write_gate.py` | live session ledger line from the hook |
| 11 | `tools/sdd_os_cli.py` | edit | `report` (ledger consumer: injected / reached-write / followed / would_block / unjudgeable counts) and `readiness <spec>` (migration lint) | report on the live ledger |
| 12 | `modules/sdd_os/goal_adapter.py` + `sdd_os_cli.py close` | create/edit | ready spec → `gsd_x_goal declare` + `oblige` per `V-ID @ file` verify item; uncompilable verify items reported, never dropped; closure via `gsd_x_goal judge` | vertical slice: this mission's spec → judge verdict on the current tree |
| 13 | `vault/specs/sdd-os-evolution.md` | create | this mission's own READY spec (dogfood) | `readiness` → READY; binds STRONG |
| 14 | mutation drills (`tools/mutation_drill.py`) on readiness / tier reconciliation / UNJUDGEABLE / ambiguity / empty-denominator guards | run | prove each guard has a red branch | all KILLED; floors recorded in `mutation_ratchet.json` |
| 15 | `vault/liveness/reachability_registry.json` (if needed), `ukdl-universal.md`, wiki | edit | declare new modules; UKDL traps per defect class (dedupe first); wiki update + handoff | `reachability.py` exit 0; grep dedupe |

`intent_verified` is NOT extended in this mission: the GSD goal obligations already provide
tree-bound requirement→gate evidence. Recorded as a follow-up (join on AC ids), not dropped
silently.
