---
title: Durable execution substrate pass (cpp-gsd-long v3) -- incident records
date: 2026-09-27/28
session: 958a5394 (pane claude-power-pack, branch feature/knowledge-acquisition)
commits: 12bee64 859be49 d730a23 26f14bd 676370b dfe968f 07f1e71
peer: claude-power-pack-c2 (03dcad48) -- sweep starvation root cause 9f750fa, live-mutant catch
---

# Incident records

Each record: symptom / impact / trigger / root cause / why defenses failed / fix / proof /
regression protection / pattern / epistemic status. ASCII only (this corpus has mojibake from
a wrong-encoding write elsewhere).

## I-1 Completion unreachable when convergence lands on the last budgeted turn
- Symptom: 43 mission records, 0 COMPLETED, 38 HALTED, 25 of them "turn ended and budget".
- Impact: a finished mission reads as budget-exhausted; renewal then refuses on ALL_COMPLETE, so
  the Owner cannot tell a finished run from a starved one.
- Trigger: the worker that finishes the milestone is often the last one the budget allows.
- Root cause: plan_next halts "turn ended and budget" BEFORE GSD is asked; GSD was asked only on
  relay/replace. Ordering defect -- the budget check outranked convergence.
- Why defenses failed: the W8/M6 live proofs ended HALTED-on-budget by design; "COMPLETED observed
  live" was already recorded as NOT observed, and nothing asked why 0 of 41 ever were.
- Fix: 12bee64 -- ask GSD before any budget halt; ALL_COMPLETE -> COMPLETED; renewal reuses the answer.
- Proof: V-MC-CONVERGE-* red on HEAD then green; mutation killed.
- Regression protection: V-MC-CONVERGE-AT-BUDGET-COMPLETES + controls.
- Pattern: a terminal classification must consult the convergence authority before the resource
  authority. See UKDL candidate T-BUDGET-OUTRANKS-CONVERGENCE.
- Status: LOCALLY ADVERSARIALLY TESTED; latent in production (ALL_COMPLETE never seen in the sweep log).

## I-2 An unreadable mission record left supervision silently
- Symptom: all_missions() `continue`d past unparseable records.
- Impact: a torn record removes a LIVE mission from supervise and status while its worker runs
  unsupervised -- a silent dead state reachable by one bad write.
- Trigger: torn write (power loss / BSOD on this host), hand edit, a newer build's schema.
- Root cause: enumerator returning only what parses; contradicted load()'s own docstring.
- Why defenses failed: load() was tested for "malformed raises"; the enumerator had no test.
- Fix: 859be49 fsync + _scan (readable, unreadable) surfaced by supervise/status; 07f1e71 adds
  newer-schema refusal into the same channel.
- Proof: V-MC-UNREADABLE-*, V-MC-KILL-* (real os._exit at the rename boundary), mutations killed.
- Status: ADVERSARIALLY TESTED for process kill; fsync durability across power loss UNVERIFIED.

## I-3 O_EXCL lock reclaimed by age: both failure directions reproduced
- Symptom: a hard-killed holder blocked every writer 60 s ("lock busy"); a live holder whose lock
  file looked old was unlinked under it (two holders). Recorded debt L1 since 2026-09-24.
- Root cause: liveness inferred from mtime; the file itself was the lock.
- Fix: d730a23 kernel byte-range lock (msvcrt.locking / flock) on a persistent file.
- Proof: V-MC-LOCK-* with real separate processes; mutation killed by 2 gates.
- Residual: one sweep pass of mixed-version overlap with a process still on the O_EXCL code.
- Status: ADVERSARIALLY TESTED.

## I-4 Ledger failures were silent and undetectable
- Root cause: ledger_append swallowed every exception; record written before its row.
- Fix: 26f14bd -- monotonic seq on record + rows, LEDGER_WRITE_FAILED on stderr, history_gaps.
- Status: ADVERSARIALLY TESTED (forced failure named as gap [4]).

## I-5 Renewal relaunched lineages that had stopped progressing
- Symptom: all 18 renewed missions of the 6 renewal-capped lineages made 0 commits (first
  missions 3-137). Peer: 444/499 launches were relays of "turn ended without completion".
- RETRACTED 2026-09-28 (kept, not deleted): "1 of 499 launches was wall-triggered", repeated in
  commit 676370b's message. It counted only `handoff_asked` rows; the mid-turn wall leaves a
  `mission-wall-<sid>-e<N>.flag` plus `handoff_already_asked`, and `tools/gsd_epoch.py census`
  finds 10 wall-witnessed production rotations (peer c2, corroborated in worker cb70bd86's
  transcript). Instrument lesson: a count keyed on ONE event name is blind to a sibling event
  that records the same fact. Rotations are now certified by `launch_cause` cause=CONTEXT_ROTATION.
- Root cause: relay/renew decided on liveness + GSD "work remains", never on progress evidence.
  At least one lineage was weekly-quota refusals (30ccdeb holds those going forward).
- Fix: 676370b -- progress fingerprint (HEAD + porcelain + shortstat), stall counter only on a
  MEASURED unchanged tree, HALTED no_progress at 3, no renewal from an unchanged origin.
- Instrument note: commits are a lower bound on progress, not semantic progress; a zero is
  decisive, a non-zero is not proof. Unmeasured never stalls.
- Status: ADVERSARIALLY TESTED; not yet EXERCISED by a live mission.

## I-6 The sweep had no pass contract
- Symptom (peer c2): 7 overlapping passes; supervise starved behind the v2 stage; log silent.
- Root cause: task time limit kills wscript, not the python grandchild; no lease; stage order.
- Fix: 9f750fa (peer, the v2 marker walk at its cause) + dfe968f (lease, mission first, bounded
  stages with tree kill, heartbeat every pass).
- Found by the test: Start-Process -PassThru ExitCode is null unless the handle is touched first.
- Status: HOST_VERIFIED (live heartbeat: mission rc 0 193.7 s, v2 rc 0 35.8 s).

## I-7 Instrument failures of my own (kept: they are the transferable part)
- A hunk check taken minutes before `git commit` let another pane's feature ride in (12bee64).
  Fix: a guarded commit that snapshots the diff and refuses if it moved.
- Mutation drills wrote mutants into the LIVE file the 5-minute sweep loads (caught by the peer).
  All mutants equalled pre-change behaviour, but the method was wrong. Fix: drills run on an
  isolated copy and assert the live file's SHA-256 is untouched.
- A drill scored SURVIVED when the suite crashed (no summary line). Fix: UNJUDGED.
- A drill that removed only the lock crashed on unlock -- scored UNJUDGED, not KILLED.
- A new supervise test reached the REAL gsd-tools (no gsd_status injected).
- A timing probe hit a path reconstructed from a truncated display string (fp=None was correct).
- A timing loop captured every start time before the first call: cumulative, not per-call.
- PS 5.1 stripped quotes from native argv (mutation anchors -> JSON spec) and the `>` redirect
  added a BOM (json.load failed until utf-8-sig).

## Retraction preserved
F2 ("compaction happened but the host boundary was missing") stays FALSIFIED: the expected
compaction did not occur. v2 compact items (EBUSY, compaction witness, continuation jobs) target
machinery retired for live runs on 2026-09-25 and were not reopened.
