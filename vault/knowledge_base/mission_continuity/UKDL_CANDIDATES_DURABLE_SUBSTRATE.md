---
title: UKDL candidates + baseline-ratchet extension -- durable substrate pass (cpp-gsd-long v3)
date: 2026-09-28
status: CANDIDATES -- drafted for merge, NOT merged into ukdl-universal.md
merge_target: vault/knowledge_base/ukdl-universal.md
evidence: vault/lessons/durable-substrate-2026-09-27.md (I-1..I-7); commits 12bee64..07f1e71
---

# 0. Why these are candidates, not rules
Each was observed ONCE, in one repository, on one host. Governance: a single occurrence does
not promote. ukdl-universal.md also takes automatic CEPS appends at its tail, so merging from a
live pane risks the file-granular pathspec collision (rules/concurrent-writers-shared-tree.md
section 1). Merge when the file is quiet and a second occurrence (or the Owner) promotes.

# 1. Ownership sweep (done before drafting)
Searched ukdl-universal.md for synonyms, by regex AND by plain word (a narrow regex is blind to
paraphrase): mutant/live, hunk/expired/commit, O_EXCL/stale lock, budget/convergence,
unreadable/skip, PassThru/ExitCode, byte-range, flock, renewal, taskkill, fsync, torn -> 0 owners.
"progress": 15 hits, none about gating a relay on evidence; nearest neighbour is
T-PARALLEL-PANES-BURN-001 (burn without progress) -- cited, not duplicated.
"self-certif": PR-NO-SELF-CERTIFICATION-001 already owns the self-hosting law -- NOT re-drafted.

# 2. Hard-rule candidates

## HR-CAND-MUTATE-A-COPY-WHEN-THE-SUBJECT-IS-LIVE-LOADED
A mutation drill that edits a file a running system loads (a scheduler, a hook, a sweep) puts the
mutant in production for the drill's duration. Drill on an isolated copy, and assert the live
file's hash is unchanged at the end. Evidence: I-7 (this pass wrote two mutants into the live
tools/gsd_mission.py; a peer pane caught it). Damage potential is irreversible when the mutated
guard protects a destructive effect -> HR tier. #CROSS-PROJECT

## HR-CAND-NEVER-INFER-LOCK-LIVENESS-FROM-AGE
Reclaiming a lock because its file looks old fails both ways: a killed holder blocks writers for
the whole stale window, and a slow live holder is dispossessed. Use a primitive the OS releases
when the holder dies (byte-range lock / flock / exclusive handle). Evidence: I-3, both directions
reproduced before the fix. #CROSS-PROJECT

# 3. Process-rule candidates

## PR-CAND-TERMINAL-STATE-ASKS-CONVERGENCE-BEFORE-RESOURCES
Before classifying a run as budget/quota-exhausted, ask the authority that knows whether the
work is DONE. The last affordable step is disproportionately the finishing one. Evidence: I-1.

## PR-CAND-RELAY-AND-RENEWAL-REQUIRE-MEASURED-PROGRESS
An unattended loop that restarts workers must compare a progress fingerprint across restarts and
stop after N unchanged ones; a fresh budget is never granted to a run whose tree has not moved.
Unmeasured is never "unchanged". Evidence: I-5 (18 renewals, 0 commits). Sibling of
T-PARALLEL-PANES-BURN-001.

## PR-CAND-A-SCHEDULED-JOB-OWNS-ITS-PASS-CONTRACT
A recurring job needs: a single-instance lease the OS releases on death, a deadline per stage
that kills the stage's whole TREE, the live stage before the legacy one, and a heartbeat on every
pass -- not only on passes that acted. Evidence: I-6. Scheduler time limits kill the wrapper,
not the grandchild.

## PR-CAND-GUARDED-COMMIT-IN-A-SHARED-TREE
Snapshot the diff (content hash) at the end of the edit; commit only if the pathspec diff is
byte-identical at commit time. Mechanizes rules/concurrent-writers-shared-tree.md section 1,
whose "read the hunk headers" check expired between reading and committing (I-7, 12bee64).
Candidate destination: an amendment to that rule, not a new UKDL entry.

# 4. Trap candidates
- T-CAND-AN-ENUMERATOR-THAT-SKIPS-WHAT-IT-CANNOT-PARSE: the subject vanishes from every consumer
  while still running (I-2). Return (readable, unreadable) from one enumeration.
- T-CAND-PASSTHRU-EXITCODE-IS-NULL: PowerShell Start-Process -PassThru reports a null ExitCode
  unless the handle was touched before exit; success and crash read alike (I-6). #CROSS-PROJECT
- T-CAND-A-CRASHED-MUTATION-RUN-SCORED-AS-SURVIVAL: no summary line means UNJUDGED (I-7).
- T-CAND-RENEWALS-READ-AS-PROGRESS: relays and renewals are activity; commits per epoch are the
  cheapest counter-instrument (I-5).

# 5. Constitutive Baseline Ratchet -- extension proposal (NOT promoted)
Recommendation: MERGE into vault/knowledge_base/uwcp_assimilation/RATCHET_PROPOSAL.md
(`distributed_correctness`, PROPOSED 2026-09-25) rather than open a second baseline. Its
requirements 1 (authority + fence), 2 (UNKNOWN kept), 6 (mutation drill per guard) already cover
this pass's CAS/epoch and UNKNOWN-never-replaces. Proposed additions, each with its local proof:

| # | requirement | local proof | ladder rung reached |
|---|---|---|---|
| 8 | a lock/lease whose release does not depend on its holder's cleanup | V-MC-LOCK-*, V-SWEEP-KILLED-PASS-RELEASES-LEASE | adversarial (local) |
| 9 | every record enumeration returns its unreadable members | V-MC-UNREADABLE-* | adversarial (local) |
| 10 | a restart loop gated on measured progress | V-MC-PROGRESS-* | adversarial (local) |
| 11 | convergence consulted before resource exhaustion | V-MC-CONVERGE-* | adversarial (local) |
| 12 | decisions name their build; newer schema refused | V-MC-CODE-ID-*, V-MC-SCHEMA-* | adversarial (local) |
| 13 | recurring jobs carry the pass contract of PR-CAND-A-SCHEDULED-JOB | V-SWEEP-* + live heartbeat | host-verified |
| 14 | mutation drills on an isolated copy with a live-hash check | harness (scratchpad mutate.py) | observed |

Status per the UCR-CIF ladder: observed -> local success -> adversarial (local). NOT reached:
repeated success, cross-context, cross-project, transfer proof. Promotion owed to the Owner after
a second project adopts at least items 8-11 and a transfer proof exists. Nothing here binds any
project yet.
