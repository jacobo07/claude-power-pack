# UKDL -- UWCP External Architecture Assimilation (2026-09-25)

Every entry was paid for by a measurement in this program; the evidence column names it.
Levels: HARD RULE (irreversible harm possible) · PROCESS RULE (costly, recoverable) · TRAP.

## Hard Rules

### HR-FENCE-AT-RESOURCE-001 -- a lease protects a resource only where the resource checks the fence
TRIGGER: designing or reviewing any lease, lock, slot or reservation that guards a side effect.
ACTION: name every resource the lease guards; each one must refuse a stale fence itself (or be
reached only through a verb that does). A holder-side self-check is Redlock.
EVIDENCE: Jepsen etcd-3.4.3; Kleppmann 2016; reproduced here -- `V-HIST-E2E-NAIVE-RESOURCE`
(a resource trusting the lease accepted the stale write while the lease journal looked healthy)
vs `V-HIST-E2E-FENCED-RESOURCE`; TLC `UWCP_mutant_nofence.cfg` (a486bf8). Extends
PR-LEASE-NEEDS-AN-OPERATOR-OVERRIDE-001 and T-CONT-19.

### HR-UNKNOWN-NEVER-LICENSES-001 -- "could not ask" never licenses a replacement
TRIGGER: any code that turns a failed observation or probe into an ending (LOST, ABSENT, ended).
ACTION: keep UNKNOWN as its own answer; a successor needs POSITIVE evidence the previous executor
stopped (observed exit or confirmed kill), never the home's own "ended".
EVIDENCE: `providers/claude.py` observe "no child handle in this process" -> LOST (HEAD 4366543);
TLC reaches two live executors through it (`V-TLA-UWCP-CURRENT-MECHANISM`) and through wall-bound
expiry without stop evidence (`V-TLA-UWCP-NOSTOPEVIDENCE-MECHANISM`). Jepsen `:info` != `:fail`.

### HR-CLOCK-OWNER-RESTART-001 -- a clock restarted by its owner's restart is an immortal lease
TRIGGER: any TTL, budget or deadline held by a process that can restart.
ACTION: persist the ABSOLUTE deadline with the authority; a reload never extends it; the persist
must be checked, never swallowed.
EVIDENCE: etcd #9888, #21372; `V-LEASE-RESTART-NO-EXTEND` (acea1f6).

## Process Rules

### PR-FENCE-WITH-EFFECT-001 -- check the fence with the effect, not before it
Temporal checks range_id inside the write transaction; etcd embeds IsOwner() in the guarded Txn.
Node effects are provisional until the home ingests them; a check followed by a wait or a spawn is
check-then-act. Evidence: etcd #11456; P4 audit gap 3 (the drafted A3 was check-then-act).

### PR-PREDICT-THEN-MODEL-001 -- predict the counterexamples before running the model, then replay them as code tests
Write down which defects the current code must exhibit; a model that finds none is refused. Then
check the MECHANISM, not only the property: TLC's first "current" counterexample went through
Expire, not the predicted FalseLost -- one flag had merged two mechanisms (a486bf8). Each
counterexample is handed to the code owner as a failing Python test (the model proves the model).

### PR-INDEPENDENT-HISTORY-001 -- judge a distributed primitive from independent histories
Checkers read the lease journal, dispatcher history and the resources' own accept/refuse logs --
never only the subject's final status. UNKNOWN is reported beside FAIL, never hidden by it; a
checker that crashed or judged nothing is UNKNOWN (141df71).

### PR-LOCK-PROOF-DETERMINISTIC-001 -- prove a lock by holding it, not by racing it
A six-process barrier race passed with the lock deleted (interpreter start-up serialised the
contenders). Prove exclusivity by having a child hold the section and requiring the parent to
wait. Evidence: lease drill 14/14 and ledger drill 17/17 only after `V-LEASE-LOCK-BLOCKS` /
`V-LEDGER-LOCK-BLOCKS` (acea1f6, 13c66b0).

### PR-GRADED-BOUNDS-001 -- bounds are suggest < warn < error, and the kill switch is exempt
Temporal: suggest Continue-As-New at 4 MiB / 4k events, warn 10 MiB, error 50 MiB; #6638 shows a
kill switch sharing a bounded write path. Owed in A4.

### PR-CAPSULE-BY-SEEDED-INDEX-001 -- workspace identity = git trees of a synthetic index seeded from base; restore by objects
An empty-index build drops exec bits, symlinks, gitlinks and skip-worktree on NTFS; `git apply`
across hosts fails under autocrlf. Owed in A6 (workspace.py).

### PR-TIMING-CHECKS-SELF-CONSISTENT-001 -- a timing gate uses floors and self-consistency, not wall windows
Fixed windows flaked at 2.7 GB free of 32 GB; a +/-0.02 s TPOT window was wider than the 17 %
error it had to catch. Compare TPOT with the same run's mean ITL; server sleeps are floors (7b25803).

## Traps

- **T-BUNDLE-VERIFY-STRUCTURAL-001** `git bundle verify` passes a bundle with one byte flipped
  mid-pack ("is okay", exit 0); `fetch` with transfer.fsckObjects rejects it. MEASURED 2026-09-25.
- **T-TLC-DEADLOCK-FLAG-001** TLC's `-deadlock` DISABLES deadlock checking. Use an explicit
  terminal stutter instead.
- **T-TLC-MASTER-FLAGS-001** flags documented on tlaplus master (`-noGenerateSpecTE`,
  `-dumpTrace json`) do not exist in the pinned v1.7.4 jar; a gate must use the pinned tool's
  flags and map an argument error (exit 1) to VERIFIER_FAILED.
- **T-TLC-LIVENESS-UNNAMED-001** TLC 2.19 does not name the violated temporal property; a liveness
  cfg must list exactly one property to be attributable.
- **T-EXIT0-QUOTA-001** a CLI harness can print a limit or auth message and exit 0; classify by a
  positive semantic list before the exit code (LiteLLM #38535).
- **T-GC-VS-UNPUBLISHED-001** retention against published references deletes in-flight writes
  (restic #2715, Kopia #5371).
- **T-UNPARSEABLE-LOCK-STALE-001** a lock file read between create and write parses as empty and
  gets taken as stale (providers/codex.py acquire_lock).
- **T-VLLM-TOTAL-VRAM-001** vLLM reserves a fraction of TOTAL VRAM and checks it against FREE; it
  refuses to start on a shared card.
- **T-BUDGET-CHECK-THEN-APPEND-001** a budget counted then appended per host is a race; reserve
  atomically at one authority, fix the window at reservation (LiteLLM #36926/#39150).
- **T-NOT-MY-CHILD-IS-LOST-001** "no child handle in this process" read as LOST.
- **T-SCAN-SEES-ITSELF-001** a gate that enumerates gate ids from tools/test_*.py reads its own
  synthetic ids as real gates -- exclude the scanner from its own scan (a8b61c6).
- **T-RESEARCH-AGAINST-MASTER-001** upstream research read on master describes a different tool
  than the release you pin; re-verify every flag and default against the pinned artifact.
