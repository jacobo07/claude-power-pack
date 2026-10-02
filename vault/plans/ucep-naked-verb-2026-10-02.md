# UCEP — "No feature ships as a naked verb" — plan state

Status: PHASE 5 done — 18 audit gaps (`ucep-naked-verb-2026-10-02.audit.md`) injected into the executable roadmap
`.planning/workstreams/ucep/ROADMAP.md` (phase order changed: admission before archetype seeding). The roadmap
SUPERSEDES the task list below where they differ. Awaiting Owner approval to arm /cpp-gsd-long.
Live false-activation evidence (2026-10-02): the subagent hand-back message, which builds nothing, was injected
`persistent_state/B0` because it contained the word "schema" — D7 observed on the real prompt path.
Mission prompt: Owner, 2026-10-02 (/ultra plan, pasted constitution). Owner answers: same day (below).
Base: `feature/knowledge-acquisition` @ `a9c603f`. Tree is dirty with another live pane's files
(sdd_os, hooks, tools/rollover*, .planning/STATE.md). This mission prefers NEW files; any edit to a
shared file is committed within minutes, pathspec-scoped, hunk headers checked.

## Owner answers (2026-10-02)

1. Merge goal-spine/v1 only if clean AND still canonical. Leave ucr-cif/construction out.
2. Write to KobiiCraft Core Files and InfinityOps only via isolated branch/worktree, scoped commits.
   KSR read-only.
3. Auto-approve family/archetype-level promotions that fully meet the evidence bar with bounded
   blast radius. Cross-family / universal / constitutional need explicit Owner approval.
4. REPORT-ONLY first, kill switch. Blocking only after positive/negative controls, mutation +
   severing drills, N/A-gaming tests and one real run with zero false activations.
5. B0/B1 untouchable; C/D -> LEGACY_UNSPECIFIED by projection; next generations use explicit
   instance/product/archetype/constitutive (or a better canonical representation if found).
6. Floor = 3 materially distinct archetypes + 1 real admitted promotion + automatic inheritance in a
   later feature + red severing drill. The 9 red citations are IN scope. Budget: /cpp-gsd-long after
   one approved ULTRA-PLAN; downshift clear slices to EXECUTION.

## Decision on answer 1 (resolved from evidence, no Owner question needed)

goal-spine/v1 is NOT merged. `git merge-tree HEAD goal-spine/v1` conflicts in
`modules/gsd_x/mission/store.py`, and the conflict is two competing designs, not text: HEAD carries a
newer goal owner (`modules/gsd_x/goal`, commits `bc2ea73` 09-25, `fe2be9c`/`8ee41c6` 09-28; store
uses a goal BINDING that makes the per-root store read-only) while the branch (last commit 09-22)
namespaces the store. Both of the Owner's conditions fail. Mission completion owner on HEAD =
`gsd_x/mission` (obligation + closure) + `gsd_x/goal`. Branch left untouched.

## Verified reality (2026-10-02)

| fact | grade | evidence |
|---|---|---|
| "UBC" = `modules/capability_runtime/applicability.py` (gates, then score; anti-trigger veto) | PROVEN | `modules/tower/families.py:7-13` |
| 13 capability contracts; schema has `dependencies`, `risk_class`, `maturity` | PROVEN | `contract.py:78-118` |
| Derived-obligation engine: facts -> 4 OPERATORS -> Obligation (consequence, closure_condition, owner, revisit_when) -> CANDIDATE/ACCEPTED/NOT_APPLICABLE/REJECTED/DEFERRED/SATISFIED/STALE | PROVEN | `gsd_x/mission/obligation.py:31-62,392` |
| Closure: only a gate verdict moves to SATISFIED; ALLOWED/REFUSED/UNJUDGEABLE | PROVEN | `gsd_x/mission/closure.py` |
| Tower: 4 families x B0(15); web_surface B1 (+2, class letters "by analogy") | PROVEN | `09b1172` |
| Injected prompt promises a done-gate; `donegate.judge` has no production caller | PROVEN | `gsd_x/cli.py:143-145` |
| `test_baseline_generations` RED 15/16 — 9 QUOTE_MISSING (8 persistent_state, 1 wii_homebrew) | PROVEN (run) | today |
| promote() admits any well-formed entry; N/A gaming; test:DELEGATED never runs; why/origin/class outside diff | OBSERVED | `wiki/syntheses/cbr-gap-analysis.md` D3-D5 |
| Families classified by prompt words only | OBSERVED | D7 |
| ucr-cif/construction unmerged, BLOCKED, touches contracts | PROVEN | out of scope (answer 1) |
| Maturity ladder L1-L5/LG, traits per plane, portable form; KC->KSR pilot | OBSERVED | `wiki/concepts/maturity-transfer.md` |
| `gsd_mission.py arm` supports `--workstream`, `--add-dir` | PROVEN | `tools/gsd_mission.py:1912-1925` |
| Proving grounds: KC `C:\Users\User\Desktop\Cursor Projects\Minecraft Projects\KobiiCraft Workspace\KobiiCraft Core Files`; InfinityOps `C:\Users\User\Desktop\Cursor Projects\InfinityOps` | PROVEN (paths) | `wiki/raw/2026-10-01-kobiicraft-capability-harvest.md:3` |

## Mode

ULTRA-PLAN once (this document). Execution under /cpp-gsd-long in GSD workstream `ucep`; every slice
below except S4 and S7 is EXECUTION MODE. Return to PLAN only on new architectural evidence.

## Ownership (no parallel authority)

| question | owner | change |
|---|---|---|
| what is this capability, its traits, archetypes | `capability_runtime` | new `archetypes.py` + trait facts; reuse `_hits`; repo reality first, prompt second |
| what maturity applies to the archetype | `tower` | second axis `vault/tower/baselines/archetype/<ID>/B<n>.json`, same generation/ratchet code |
| which surfaces apply, why, with what consequence | `gsd_x/mission` obligation engine | new operator family (new file) emitting `Obligation`s — one per surface |
| may it close | `gsd_x/mission/closure` + `tower/donegate` | wired on the real Stop path, report-only |
| may a lesson become constitutive | `tower` | new `admission.py`; `ratchet.promote` refuses without an admission record |
| what did construction teach | fable_distillation deposits + capsule; UKDL | candidate emission only |
| composition | `CapabilityContract.dependencies` (+ typed relation) | extend, no new graph |
| metrics | tower consumption ledger | new rung rows, test rows segregated |

## Invariants

- UNKNOWN != PASS; UNJUDGED != VERIFIED; DELEGATED != VERIFIED; DEFERRED needs owner + revisit_when.
- Applicability disposition (REQUIRED/CONDITIONAL/NOT_APPLICABLE/EXPLICITLY_DEFERRED) is separate from
  evidence verdict (VERIFIED/VIOLATED/DELEGATED/UNJUDGED).
- Consequence strengthens an envelope; complexity alone does not.
- No archetype from vocabulary alone: an archetype needs a structural repo/intent fact.
- B0/B1 bytes never change. History is projected, never rewritten.
- Kill switch `CPP_CAPABILITY_GATE=off` disables injection AND judging; default report-only.

## Tasks (revised, numbered)

S0 — Integrity repair (EXECUTION)
1. `vault/tower/baselines/persistent_state/B1.json`, `wii_homebrew/B1.json` — create via
   `ratchet.revert` + `promote` (re-anchor 9 QUOTE_MISSING origins to where the rules now live, or
   revert with reason if gone). Verify: `test_baseline_generations` 16/16, `verify_chain` ok.
2. `modules/tower/ratchet.py` — diff `why`/`origin`/`class`/`propagation_scope`; unanchored child =
   not ok; authority from allowlist. Verify: probe H1/H2/H3b now red-on-attack, controls green.
3. `modules/tower/donegate.py`/`checks.py` — N/A requires a reason from a closed vocabulary +
   cap on N/A share; `test:` checks run (bounded) or stay UNJUDGED, never DELEGATED-green.
   Verify: probe H5/H6 now block.
4. `modules/gsd_x/cli.py` — the delivered sentence matches what runs (true after S5).

S1 — Capability subject + archetypes (EXECUTION)
5. `modules/capability_runtime/archetypes.py` (new) — traits (persistent, multi_actor, bulk,
   destructive, distributed, external_effect, scheduled, money, policy_layers, ui) from repo
   structure + intent; archetypes = trait conjunctions; anti-triggers demote, not veto; family and
   archetype orthogonal. Verify: `tools/test_capability_archetypes.py` — negative control
   (vocabulary overlap without structure -> no archetype), trait-transition recompiles.

S2 — Archetype maturity generations (EXECUTION, seeds through S4 admission)
6. `vault/tower/archetypes/*.json` + `archetype/<ID>/B0.json` for 3 archetypes:
   WORLD_MUTATION/persistent-state (donor KC world_persistence_gate), EXTERNAL_EFFECT (donor
   InfinityOps web_surface B1 effect-keeps-status, generalized), BACKGROUND_JOB (donor PP gsd sweep
   lease/heartbeat/bounded stages + KC stale-lock). Each entry: surface, consequence, origin+quote
   (verify_origin VERIFIED), check or MANUAL do-confirm, negative applicability, propagation_scope.

S3 — Envelope compiler (EXECUTION)
7. `modules/gsd_x/mission/envelope.py` (new) — subject -> archetypes -> archetype+family entries ->
   UKDL traps that causally apply -> contract dependencies -> `Obligation`s with dispositions and
   reasons; explicit NOT_APPLICABLE list for considered surfaces. Verify: naked-verb, irrelevant-
   surface, consequence-escalation, silent-omission tests.

S4 — Promotion admission + C/D contract (PLAN MODE: one design check, then build)
8. `modules/tower/admission.py` (new) — evidence bar proportional to scope: origin VERIFIED, check or
   MANUAL, evidence ref (commit/incident), production evidence ref, negative applicability,
   counterfactual verdict, provisional status; family/archetype auto-admit; cross-family/universal/
   constitutive -> PENDING_OWNER. `ratchet.promote` requires an admission record.
9. `modules/tower/baselines.py` — `propagation_scope(entry, gen)` projection: gen<=1 ->
   LEGACY_UNSPECIFIED. Verify: B0/B1 sha unchanged; admission refuses bad origin / `glob:**`.

S5 — Delivery + closure on the live path (EXECUTION)
10. `modules/gsd_x/cli.py` — bounded envelope block beside family_block (respect 8/1,400 cap).
11. Stop path — report-only judge of envelope + family entries; rows to consumption ledger with
    rungs compiled/required/closed/NA/deferred/unjudged. Verify: real session in a real repo leaves
    a row (Production Reality), kill switch silences both.

S6 — Proving grounds + transfer (EXECUTION, isolated worktrees)
12. KC (worktree): a real persistence/world-mutation feature compiles an envelope and closes it.
13. InfinityOps (worktree): a real external-effect feature inherits EXTERNAL_EFFECT surfaces.
14. KSR (read-only): naked "add coin save" intent against KSR reality -> envelope requires save
    integrity; current code judged VIOLATED (main.cpp:1443-1565) — cross-context transfer, no mutation.

S7 — Falsification + live promotion (PLAN check, then EXECUTION)
15. `tools/test_capability_envelope_adversarial.py` — 12 challenges incl. N/A gaming, deferred-forever.
16. Severing drill via `tools/mutation_drill.py` (isolated copy): sever archetype inheritance ->
    S6 mission goes red. Register in mutation ratchet.
17. One real admitted promotion (archetype B1) from S6 evidence; a later feature inherits it
    unprompted; closure flags its absence.
18. Report-only -> blocking decision gate (answer 4 criteria) — only if all met.

S8 — Knowledge + handoff
19. Incidents + UKDL HR/PR/Trap candidates; liveness `--baseline`; wiki component pages; metrics
    (closure rate, naked-verb escape, inheritance rate, false activation) with real denominators;
    RESUMPTION + handoff.

## Risks / kill switches

- Live pane in same tree -> new files, minute-scale commits, narrow oracles bracketed by dirty-path SET.
- Envelope bloat / false activation -> anti-bloat metric + irrelevant-surface test; report-only.
- Prompt-path cost -> envelope compiled from cached repo traits; hook budget measured.
- Admission too strict -> nothing promotes -> floor item explicitly gated (task 17).
- `CPP_CAPABILITY_GATE=off`; archetype axis removable by deleting `vault/tower/archetypes/`.
