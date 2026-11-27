# Phase 6 evidence: ratchet, UKDL and hand-back (PERF-06)

Plane: GEX44 (kobicraft-gex44, Linux, Python 3.12, stdlib only) for everything observed here. The laptop is observed by nothing in this phase: zero laptop-judged items. PH below means `.planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back`. Every path is repo-relative.

## a. Decisions D6-01 to D6-10 and what carries each

| Decision | Carried by | Record or file |
|----------|------------|----------------|
| D6-01 phase-local code only, stdlib, registered nowhere | `PH/inherit_check.py`, `PH/ratchet_connect.py`, `PH/ukdl_candidate_check.py`, `PH/handoff_check.py` | `PH/records/06-03-T3.tree.txt` (tools, modules, hooks, vault/config show no change); only two tracked files outside the workstream exist, the two candidate files |
| D6-02 inheritance measured, not asserted | manifest and mutant matrix | `PH/records/06-01-T2.manifest.txt`, `PH/records/06-01-T3.matrix.txt`, map `PH/06-INHERITANCE.md`; re-run in `PH/records/06-03-T3.final-gates.txt` |
| D6-03 no standing-gate wiring | decision (11) | `PH/06-INHERITANCE.md` section 5, STATE.md Phase 6 block, `PH/HANDOFF.md` decision list |
| D6-04 ratchet CONNECTED_SCRATCH, live BLOCKED | the real owner `modules/tower/ratchet.py` driven on a scratch root | `PH/records/06-02-T2.connect.txt`, `PH/records/06-02-T2.classify.txt`, `PH/records/06-02-T1.selftest.txt` |
| D6-05 Tower candidate note | five entries, four promotable under an Owner authority, one NOT_PROMOTABLE with the missing parts named | `vault/tower/candidates/perf_construction.md` |
| D6-06 UKDL candidates, append-only file | five blocks (one NEW, four pointers to existing owners), none promoted | `vault/knowledge_base/candidates/perf-construction-20261123.md`, `PH/records/06-02-T3.ukdl.txt` |
| D6-07 HANDOFF facts generated | INVENTORY line recomputed by the checker; selftest with a mutant control | `PH/handoff_check.py`, `PH/records/06-03-T1.selftest.txt`, `PH/records/06-03-T1.tracer.txt`, `PH/records/06-03-T2.check.txt`, `PH/HANDOFF.md` |
| D6-08 bookkeeping by addition only | a Phase 6 hand-back block appended to STATE.md; no position field, ROADMAP.md, REQUIREMENTS.md or ROOT milestone edited | `PH/records/06-03-T3.tree.txt` |
| D6-09 s9 red-team stays UNJUDGED | row SKIPPED_BY_POLICY in the manifest, repeated in the final record | `PH/records/06-01-T2.manifest.txt`, `PH/records/06-03-T3.final-gates.txt` |
| D6-10 plane discipline | the owner summary's first line, the closed forbidden-claim list, laptop slots fixed to UNJUDGED | `PH/handoff_check.py` gates V-HO-FIRSTLINE, V-HO-CLAIM, V-HO-LP |

## b. The three ROADMAP success criteria

| Criterion | Status | Evidence |
|-----------|--------|----------|
| 1. UKDL candidates appended to a candidate file, no shared aggregate edited, each with evidence and scope | MET for the code path: candidates appended and checker-validated (`UKDL_CHECK=5/5`); the aggregates, `vault/hard_rules`, `governance` and `wiki` show no change. The checker validates shape and that cited paths exist, not that a cited line says what the block claims (lines were re-read by hand once). | `vault/knowledge_base/candidates/perf-construction-20261123.md`, `PH/ukdl_candidate_check.py`, `PH/records/06-02-T3.ukdl.txt` |
| 2. Ratchet entry connected to the real owner from Phase 1, or BLOCKED with reason | CONNECTED_SCRATCH, live BLOCKED, with three ordered reasons: no family reaches this work (`CLASSIFY_NO_FAMILY=4/4`), a live promotion needs an Owner authority an unattended run does not have, and one mission is not a second independent domain. Nothing live was written. | `PH/records/06-02-T2.connect.txt`, `PH/records/06-02-T2.classify.txt` |
| 3. HANDOFF.md with owner summary, engineering handoff, laptop-only checklist, known unknowns, exact next task | HANDOFF checked: five sections in order, first line `Creation speed on the laptop: UNKNOWN`, every count equal to the checker inventory, the LP set equal to the phase files, one next task. | `PH/HANDOFF.md`, `PH/records/06-03-T2.check.txt` |

## c. Meta-analysis

Per phase, the headline claim, the plane and instrument it rests on, and what it does not say. Sample sizes are those the phase recorded; none is re-typed from memory.

| Phase | Headline claim | Instrument and plane | Not said |
|-------|----------------|----------------------|----------|
| 1 reality and ownership | Four roadmap criteria verified at code level; the owner of each mechanism named (extend `modules/capability_runtime`); most reference ids stay UNKNOWN because the origin audit is absent | reading of this clone, GEX44 | any laptop reading (LP-01, LP-02) |
| 2 benchmark integrity | A failed sample cannot be hidden and regression compares only host-matched history, for the code paths of four reference ids | `tools/test_bench_integrity.py` and `tools/test_bench_gate.py` on temp ledgers, GEX44 | live regression verdicts (matched history too short), Windows host state (LP-03) |
| 3 construction metrology | A timing contract with censoring and an instrument-fail state, exercised on a capped real sample | `tools/test_construction_metrology.py`, one capped GEX44 sample of the local transcripts, below the minimum sample for percentiles | the Owner's own definitions (PROPOSED), any laptop distribution (LP-04 to LP-06) |
| 4 host pressure admission | A reader and classifier separate a slow host from a slow component; the count refusal exists but no launch path passes it | `tools/test_resource_pressure.py`, GEX44 probes taken one at a time | the ceiling value (uncalibrated), the Windows and macOS parsers on real hosts (LP-07, LP-08) |
| 5 critical path audit | The registry is inventoried and a guard rejects each planted mutant; the live registry moved zero entries | `tools/test_hook_critical_path.py`, the repo dispatcher registry, GEX44 | any wall time of a real hook chain, the laptop registry (LP-09 to LP-12) |

Laptop-judged items, computed from the inventory as LP ids whose status is not UNJUDGED: 0 of 12. Every LP row of the hand-back carries the literal status LAPTOP-ONLY / UNJUDGED and an empty laptop value slot.

Matrix verdict counts (plan 06-01, five mutants, one per owner): ENFORCED 3, OWN_SUITE_ONLY 2, SURVIVED_ALL 0, NOT_DISCRIMINATING 0. Phases 2 and 4 are inherited by the `bench-gate` row; Phases 3 and 5 only by a command nobody runs on a schedule that anyone found.

Owner's complaint terms (creation slowness, as the three PROPOSED metrics time to first material change, time to first user-visible response and time to verified deliverable, expansions proposed in `vault/specs/construction-metrology-contract.md`): none has any laptop evidence, and none has an Owner-admitted definition. The GEX44 distribution of Phase 3 is a capped sample of this host and says nothing about the laptop.

The single largest unknown: how long creation takes on the laptop, and whether any of the changes in this campaign moved it. The first step is LP-05.

## d. Carried debt, by name

- 56 reachability offenders, unchanged by name (the metrology unit is among them as ORPHAN with class DORMANT; Phase 5 imports two constants from it by code, which the reachability tool does not count).
- `tools/test_git_invocation.py` at 6 of 7.
- `tools/test_s9_redteam.py` at 111 of 114, UNJUDGED, not run unattended, no clean control run.
- The Phase 3 and Phase 5 suites are wired into no standing gate (Owner decision (11)).
- `PH/ukdl_candidate_check.py` verifies that a cited path exists, not what a cited line says.
- Whether anything schedules the `bench-gate` row of `tools/verify_spp.py` is UNKNOWN.
- Suite timings are one run per session and disagree between sessions by a factor of about three.
- The other manifest suites (a5_u6, arm_preflight, gsd_mission resources and baseline, hook_boundary) have no mutant: whether a standing gate defends them was not measured.
