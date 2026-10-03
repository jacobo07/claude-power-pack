---
id: PLAN-SKILL-CAPABILITY-PROGRAM
status: APPROVED (Owner "y" 2026-10-03, incl. owner boundaries 1-3); P0 not started
covers: [skill, capability, residency, discovery, opportunity, delivery, contribution, representation, lifecycle, virtualization, compile-out, skill-capability-program]
parents: [vault/plans/skill-residency-program-2026-10-03.md, vault/plans/skill-virtualization-k-slice-2026-10-03.md]
consumer: cognitive-economy pillar C (DEFERRED_STRONGER_OWNER -> this program); its pillar T overlaps S-I
date: 2026-10-03
---

# Skill / Capability program (master)

## Master done-gate
`python tools/test_skill_capability_program.py --final`
= thin wrapper over tools/test_cognitive_economy_program.py: import it, rebind module globals
LEDGER_REL=vault/programs/skill-capability/ledger.json, FROZEN_AT_REL=vault/programs/skill-capability/FROZEN_AT,
HANDOFF_DIR=vault/programs/skill-capability/handoffs/, PILLARS=A..N, SELF_REL=tools/test_skill_capability_program.py,
then call its main(). NEVER edit the CE file (a live mission, m-fdefb0fca0c0, uses it).
Reuse facts (read 2026-10-03): clauses read globals at call time; selftest mutants use letters A-G and
frozen.pillars indices 3,4,7 (need >= 8 pillars lettered from A); _clean_fixture reads LEDGER_REL;
V-CEP-REAL-HANDOFF is pinned to CE commits 1cabd117/4d1cfb83 (still valid, repo-local); messages say "A-T".
Ledger shape: {frozen:{pillars:[{id,predicted,owner:[paths],rule?}], denominators:{...}}, state:{id:{terminal,
reason, evidence:[{kind,ref,sha256}|{kind:gate,argv}], savings:[{status,displacement,denominator,measurement?}]}},
reviews:{ukdl:{file},cbr:{file}}, deltas:{product:[],intelligence:[]}}. Terminals: IMPLEMENTED_AND_VERIFIED,
MERGED_INTO_EXISTING_OWNER, FALSIFIED_OR_REJECTED_BY_EVIDENCE, DEFERRED_STRONGER_OWNER, AUTHORIZATION_BOUND,
EXTERNAL_BLOCKED, RESEARCH_INSUFFICIENT_EVIDENCE. Wrapper extra (--final only): settings == declared retained state.

## Pillars (ledger ids A..N)
A card precision + C8 maturity | B listing floor + plugin gateway + economics | C opportunity/delivery/recall/precision
| D coverage + criticality | E contribution + result consumption | F disclosure/fission/fusion/inline/dedup
| G compile-out + lineage | H freshness/drift/recert | I lifecycle/retirement/self-pruning/GC (MERGE CE T)
| J creation governance | K capability routing + ACV | L CO-12 + Context Compiler (CC ABSENT -> CE)
| M economics/model/goal relativity | N CBR/UBC/UKDL/settings/push closeout.
DAG: P0 -> A -> B -> C -> (D || H) -> F -> G -> E -> (I,J,K,L,M) -> N.

## Evidence at approval
Listing hiding FALSIFIED x2 (C6, K4: 30,000->29,795 chars, 87,739->89,844 startup tokens; plugin refill 22->50).
R1-R3: per-run --settings merges; user-invocable-only removes name; Skill tool REFUSES it (page by Read only).
Card: arm C 2/2; LIVE precision 0 TP / 5 denies (300ac3a1 gsd-tools; 5b36b02f oxfmt x2; 3a05f288 own script;
4a7ee8bc ledger_write.py) -- all tool-mediated own writes, agent re-issued each time (+1 turn). New unknown class
post-K1: `git exit 128` x6 (root-cause in A). Pillar A design: mtime-window provenance -- a file whose mtime lies
inside one of this session's shell tool-call windows after its last own edit => unknown, not foreign; pre-session
foreign hunks (arm C) stay foreign. C8 target: delivery card (deny-once question), never authority.

## Long run
Mission: gsd_mission.py arm --cwd <repo> --workstream skill-capability --command "/gsd-autonomous"
--max-cycles 12 --max-hours 24 (permission auto). Two missions already RUNNING here (ucep, cognitive-economy).
Terms recorded in workstream REQUIREMENTS (arm CLI has no terms flag; record field has no reader).

## Owner boundaries (approved as written)
1 RAM: arm only at >= 4 GB free (0.8 GB / 34 claude.exe at approval); until then run pillar A in-pane.
2 Sessions: listing family 8 of 12 left; <= 10 new for contribution/delivery benchmarks.
3 Global edits (HR-001): snapshot, shortest window, restore; per-run --settings whenever possible.
4 Push: local while foreign commits interleave (24 ahead at approval).

## Next action (P0)
Write vault/programs/skill-capability/ledger.json (A..N pre-registered, predicted terminals + frozen owners that
exist), tools/test_skill_capability_program.py (wrapper), run --selftest, create
.planning/workstreams/skill-capability/{REQUIREMENTS,ROADMAP,STATE}.md, commit, write FROZEN_AT = that commit,
commit; then RAM check -> arm, else start pillar A in-pane.
