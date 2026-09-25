# Synthesis -- concurrency core (drafted before wave 2 lands)

## Convergent invariants (independently repeated across systems)
C1 Fence is safety, lease is liveness. etcd 3.4.3 (Jepsen), Redlock/Kleppmann, Hazelcast, Temporal
   range_id. Four independent systems, same lesson. UWCP: every side-effect TARGET checks the fence;
   runner self-check alone == Redlock.
C2 Check atomically WITH the effect. Temporal readLockShard inside txExecuteShardLocked; etcd IsOwner()
   Cmp inside the guarded Txn. UWCP's only atomic commit point is home ingest under the goal-log CAS ->
   node effects are PROVISIONAL; external effects go to fence-named refs the home promotes.
C3 Indeterminate is its own outcome. Jepsen :info, Temporal ErrStaleState vs ErrActivityTaskNotFound,
   keos_qwen UNAVAILABLE, reconcile OBS_UNKNOWN. UWCP already has the vocabulary at observation level,
   NOT at probe level (G-L1).
C4 Identity two-level + attempt identity on completion. WorkflowID/RunID/request_id/attempt/version ==
   goal_id/epoch_id/run_token/fence/revision. Receipt must echo all; ingest compares all (G-T3a).
C5 Bounded everything with graded rungs. Temporal suggest 4MiB / warn 10 / error 50; brief bound is the
   error rung only (G-T1).
C6 Clocks persisted by the authority, never restarted by owner restart (etcd #9888, #21372).
C7 Ack only after durable (etcd #14370; Temporal #9118 outbox). goal/log.py satisfies it; dispatcher
   queue file is the unverified party.
C8 The checker never trusts the subject's own narrative (Jepsen pure checkers over stored history;
   etcd robustness recording client histories; trace validation).

## Decisions
D-FM  TLA+/TLC = ADOPT DEVELOPMENT DEPENDENCY (MIT, JDK17 present, jar pinned by sha256 outside git;
      absent jar = UNJUDGED). ONE model: vault/specs/tla/UWCP.tla. Gate maps TLC exit codes to four
      outcomes (0 PASS / 10-14 SUBJECT_VIOLATION / 75-77,150-153,255 VERIFIER_FAILED / jar or java
      absent UNJUDGED). Coverage floor (every action fired) + 4 mutant cfgs must go red. Predicted
      counterexamples on a CURRENT-CODE config: late receipt after end, replace-on-unknown probe,
      unbounded WAIT. Predicting them first = positive control on the model.
      Apalache REJECTED now (Java 21, no trace validation).
D-HC  CPP-native Python history checker = ABSORB CONCEPTS (Jepsen/Elle/Porcupine), no Clojure.
      Inputs are INDEPENDENT sources: goal log, VPS lease journal, dispatcher history, fenced-store
      accept/refuse logs, runner attempt log. Checker names == TLA+ invariant names (one vocabulary).
      Merge rule diverges from Jepsen: any_unknown reported separately; UNKNOWN never folded into
      PASS and never hidden under a FAIL from another checker.
      Negative control: unbridled-optimism swap must be detected by the harness.
D-TV  Trace validation (TraceUWCP.tla over goal log NDJSON) = KEEP AS MIGRATION OPTION; add after the
      model and checker exist. Blind to unlogged effects -> runner logs each side-effect attempt with fence.

## Workspace capsule (B1 + local measurement)
MEASURED 2026-09-25 (LOCAL_REALITY, scratchpad/bundletest): one byte flipped mid-pack in a 357-byte
bundle -> `git bundle verify` prints "is okay", exit 0; `git -c transfer.fsckObjects=true fetch` ->
"inflate: data stream error ... index-pack died", exit 1. -> §10's verify premise is FALSE (CLASE 2).
Changes to the approved §10 (EXTEND, not redesign):
W1 every part + manifest named {sha256,size} (REAPI Digest), size checked first; digest_function and
   git_object_format explicit; capsule_id = digest of canonical manifest bytes.
W2 identity = two git trees (index_tree, worktree_tree) from a synthetic index SEEDED from base
   (read-tree), never empty; diffs demoted to optional transport.
W3 restore by objects + node-local checkout-index; never git apply across hosts (F-GIT-1 autocrlf).
W4 conversion_env (autocrlf, eol, filters in scope + installed, LFS version) = correctness baseline field.
W5 content verify = part digests + fetch with fsckObjects; bundle verify = structural only.
W6 node "have" asked at dispatch (FindMissingBlobs analogue); remembered heads are beliefs.
W7 retention = keep parts referenced by last N receipts UNION queued/running manifests; delete only
   older than max epoch budget + transfer margin AND unreferenced on two passes; retention outcome
   RETIRED is distinct from NON_EQUIVALENT (etcd ErrCompacted analogue).
W8 refusals: unmerged index, case-colliding paths onto case-insensitive host, required filter/LFS absent.
Dispositions: remote-apis ADAPT DATA MODEL; bazel REFERENCE (corpus); dagger REFERENCE; restic/kopia
ABSORB CONCEPTS (GC margins, structural vs content verify); CDC + keyed ids REJECTED; git = object model.

## Owner check (EXTEND before NEW)
- No existing formal-verification or history-checker owner in CPP (grep TLA+/jepsen/linearizab: none in
  code). A new capability is justified, but as a NEW MODULE under an existing home, not a new platform:
  modules/distributed_verification/{tlc_gate.py, history.py, checkers.py, nemesis.py}. Consumers:
  UWCP first; KSR slot leasing second (it has the same lease). Promotion to baseline only after UWCP
  demonstrates value (ratchet rule below).
