# Incremental Cognition -- candidate learnings (pillar N closeout)

Frozen rule N (verbatim from `ledger.json`, `frozen.pillars` id N):

> candidates go to vault/programs/incremental-cognition/ukdl-candidates.md; promotion into ukdl-universal.md and CBR is reviewed, never silent

These are the candidate learnings of THIS run (mission `incremental-cognition`, GEX44 plane, branch
`mission/incremental-cognition-run`). Nothing in this file is promoted: promotion into `vault/knowledge_base/ukdl-universal.md`
or into a CBR family generation is the Owner's (`[N]` in `owner-bundle.md`), and the closeout gate
(`python3 tools/test_ic_closeout.py`) turns red if a candidate id ever shows up in the UKDL or under `vault/tower/` without a
recorded promotion. Each verdict (PROMOTE-PROPOSED / HOLD / REJECT) and its reason live in
`reviews/ukdl.md` and `reviews/cbr.md`, never here.

Three levels, each with its own target:

| level | what it is | target |
|---|---|---|
| universal | true of any project that does this kind of work | `vault/knowledge_base/ukdl-universal.md` |
| domain | true of this kind of work (measuring and supervising agent sessions) | an existing file under `vault/knowledge_base/`, here `ukdl-cognitive-resource-os.md` (mission-scoped entries, kept out of the universal file because its tail has an automated writer) |
| project | true of this program only | this file |

Block grammar, discovered by the gate and never listed in it: `### IC-<U|D|P>-<NN> -- <title>`, then `level:`, `kind:`
(`hard-rule` | `process-rule` | `trap` | `performance`), `proposed_id:` (UKDL id grammar), `target:`, `statement:`,
`evidence:` (refs separated by ` ; `: a tracked path, an optional `:line` or `:from-to`, or `commit:<sha>` reachable from HEAD)
and, for a performance guarantee, `second_workload:`. Every ref was re-read at its path / line / commit when it was written.

## Universal

### IC-U-01 -- classify an authorization refusal by who wrote the reply, never by its words
level: universal
kind: process-rule
proposed_id: PR-CLASSIFY-A-REFUSAL-BY-ITS-WRITER-NOT-ITS-WORDS-001
target: vault/knowledge_base/ukdl-universal.md
statement: A supervisor that decides "the worker was refused, stop relaunching" from the last reply must judge the AUTHOR of the reply (a host-written row: model `<synthetic>`, zero usage), not the phrase. A model that merely quotes "Please run /login" is not a refusal (the breaker-less fallback in tools/gsd_mission.py needs the host author AND an auth phrase, and the quoted case is pinned by V-PFP-FALLBACK-QUOTED-NOT-PARKED). Matching words alone would park a healthy mission; ignoring the refusal relaunches a locked-out one (the a7 loop: 137 dead relaunches in the replayed transcript shape).
evidence: tools/gsd_mission.py:1957-1972 ; vault/programs/incremental-cognition/evidence/C.md:21-22 ; vault/programs/incremental-cognition/evidence/C.md:93-95 ; vault/programs/incremental-cognition/evidence/C.md:105-107 ; commit:5962571c840943ae0a3aa901efb08e69a04434da

## Domain

### IC-D-01 -- a frozen denominator over a live corpus reproduces only inside its frozen window
level: domain
kind: trap
proposed_id: T-FROZEN-DENOMINATOR-OVER-A-LIVE-CORPUS-REPRODUCES-ONLY-IN-ITS-WINDOW-001
target: vault/knowledge_base/ukdl-cognitive-resource-os.md
statement: A population frozen at an instant is reproduced by a rescan only if the rescan is cut back to that instant: the live corpus keeps growing, so an unwindowed scan reads a different population (14 active sessions / 1,679 calls against the frozen 13 / 1,322). The instrument must default to the freeze instant, locate it with a bounded search, and treat a population that does not match as UNMEASURED, never as "below the threshold".
evidence: .planning/workstreams/incremental-cognition/STATE.md:66 ; vault/programs/incremental-cognition/evidence/phase3.md:10-11 ; vault/programs/incremental-cognition/evidence/phase3.md:83-85 ; vault/programs/incremental-cognition/evidence/phase3.md:169-172 ; vault/programs/incremental-cognition/evidence/phase3.md:212-214

## Project

### IC-P-01 -- a smoke measurement taken on another plane is instrument evidence, never terminal
level: project
kind: process-rule
proposed_id: PR-SMOKE-ON-ANOTHER-PLANE-IS-NEVER-TERMINAL-001
target: vault/programs/incremental-cognition/ukdl-candidates.md
statement: Every measurement committed from GEX44 is about the instrument, not the pillar: the denominator it ran on (KME-G, or the named GEX44-B001 workload) is outside each pillar's frozen rule (KME-L, laptop-plane), so the file carries evidence_role smoke and terminal_evidence false and the program done-gate (R3) refuses it as terminal. A KME-G figure is never stated as a KME-L result, never generalised to it, and an upper bound is never presented as a saving.
evidence: vault/programs/incremental-cognition/evidence/phase3.md:10-13 ; vault/programs/incremental-cognition/evidence/phase3.md:14-20 ; vault/programs/incremental-cognition/evidence/L.md:91-93 ; vault/programs/incremental-cognition/evidence/L.md:109-110 ; tools/test_incremental_cognition_program.py:419
