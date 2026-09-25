# A2 — TLA+ / TLC and Jepsen research for UWCP (2026-09-25)

Read-only research. Every upstream claim cites repo + path + tag/SHA + date where obtained.
Classification tags: INVARIANT / ALGORITHM / DATA MODEL / PROTOCOL PATTERN / FAILURE PATTERN /
TEST PATTERN / FAULT-INJECTION PATTERN / ANTI-PATTERN.

## 0. Local context (read from disk, this session)

- `vault/specs/uwcp.md` §5-§14 read. Concurrency core: append-only goal log (VPS), epochs
  DISPATCHING -> RUNNING -> ENDED (+RECEIPT), lease store (flock, TTL from dispatch, holder-only renew,
  consume, monotonic fence generation), run_token = queue job id, cancel dominates pause (CAS).
- `modules/gsd_x/goal/epoch.py` (local tree, branch feature/knowledge-acquisition):
  states `epoch.dispatching|running|ended|receipt` (L43-46); outcomes completed/failed/lost/expired/
  cancelled/stale_revision (L51-53); observation states running/ended/lost/unknown (L61).
- FINDING (local, INVARIANT gap, measured by grep): `grep fence|lease modules/gsd_x/goal` finds **no fence
  and no lease code** in the goal package (only a docstring mention epoch.py:8 and a codex provider lock).
  The planned fence is PLANNED, not LIVE.
- FINDING (local, INVARIANT gap): `ingest_receipt` (epoch.py:256-273) refuses unknown epoch, duplicate
  receipt id, and revision mismatch — it does **not** refuse a receipt for an epoch whose state is
  `ended`. The only caller today (sweep.py:206-211) ingests before `end`, so the property holds by call
  order, not by the function. A late-receipt path (e.g. a second harvest after a crash between
  ingest-equivalent and end) is not refused by the authority. §14's "ended-epoch refusal" must be
  enforced inside `ingest_receipt` itself (guard at the choke point). This is exactly the kind of gap a
  TLA+ model with a `LateReceipt` action would expose as a counterexample.
- Local JVM (probe, this session): `C:\Users\User\Apps\jdk-17\bin\java.exe -version` ->
  `openjdk 17.0.19 2026-04-21 Temurin-17.0.19+10`. Satisfies TLC's Java 11+ floor. VPS JVM not probed.
- Tooling note: the GitHub MCP returned `401 Bad credentials`; all upstream reads below used the public
  GitHub REST API / raw.githubusercontent.com via WebFetch.

## 1a. TLA+ tools (tla2tools.jar / TLC)

Source: github.com/tlaplus/tlaplus, master HEAD `5d5360599f3df7d919c44647af65d5bfa57562fb`
(committer date 2026-09-25).

- Releases (REST `/releases`, 2026-09-25): latest **stable** = `v1.7.4` "Xenophanes" (2024-08-05), asset
  `tla2tools.jar`. `v1.8.0` "Clarke" is a **rolling prerelease** rebuilt on every master commit (README:
  "every commit to the master branch is built & uploaded to the 1.8.0 Clarke pre-release"), so its
  bytes are not a fixed version -> for a gate, pin v1.7.4 or pin a v1.8.0 jar **by sha256**, never by tag.
  (PROTOCOL PATTERN: pin the instrument by content hash — cf. develop-here-prove-there.)
- License: README "Licensed under the MIT License" (copyright HP, Microsoft 2003, Linux Foundation 2023).
- Java: README "The TLA+ tools require Java 11+ to run."
- Invocation: `java -jar tla2tools.jar` aliases `tlc2.TLC`; alternatively
  `java -cp tla2tools.jar tlc2.TLC ...` (also `tla2sany.SANY` for parse-only, `pcal.trans` for PlusCal).
  Headless: `java -XX:+UseParallelGC -jar tla2tools.jar -workers auto -config UWCP.cfg -deadlock
  -dumpTrace json cex.json -noGenerateSpecTE -metadir <tmp> -cleanup UWCP.tla`.
- Flags (tlc2/TLC.java usage text @ 5d53605):
  - `-workers N|auto` (default 1); `-config` (default SPEC.cfg);
  - `-deadlock` **DISABLES** deadlock checking ("if specified DO NOT CHECK FOR DEADLOCK") — a trap:
    the flag name reads as "check deadlock". For UWCP, terminal states (goal CONVERGED/CANCELLED) are
    legitimate stuttering; either pass `-deadlock` or add an explicit `Done == ... /\ UNCHANGED vars`
    step. Prefer the explicit step: `-deadlock` also hides genuine stuck states (ANTI-PATTERN).
  - `-dump [dot,...] file` dumps all states; `-dumpTrace json|tla|tlc file` writes the error trace in
    that format (json is the machine-readable counterexample a Python gate should parse);
  - `-coverage N` (minutes between coverage reports; without it none) — use it: an action with zero
    coverage means the model never exercised that branch (TEST PATTERN: vacuity check);
  - `-tool` wraps output in message codes (`@!@!@STARTMSG <code>:<class> @!@!@`) for machine parsing;
  - `-continue` keeps going past the first violation; `-simulate num=X` / `-depth` random simulation;
    `-noGenerateSpecTE` suppresses the SpecTE trace-exploration module; `-metadir`, `-cleanup`,
    `-checkpoint`, `-fp`, `-maxSetSize`, `-terse`.
- Exit codes (tlc2/output/EC.java `ExitStatus` @ 5d53605): `0 SUCCESS`; `10 VIOLATION_ASSUMPTION`;
  `11 VIOLATION_DEADLOCK`; `12 VIOLATION_SAFETY`; `13 VIOLATION_LIVENESS`; `14 VIOLATION_ASSERT`;
  `75 FAILURE_SPEC_EVAL`; `76 FAILURE_SAFETY_EVAL`; `77 FAILURE_LIVENESS_EVAL`; `150 ERROR_SPEC_PARSE`;
  `151 ERROR_CONFIG_PARSE`; `152 ERROR_STATESPACE_TOO_LARGE`; `153 ERROR_SYSTEM`; `255 ERROR`.
  -> (TEST PATTERN) the exit code already separates **subject invalid** (10-14) from **verifier failed /
  unreadable input** (75-77, 150-153, 255). The Python wrapper must map these to four outcomes and never
  collapse 150/151/255 into "spec violated" (instrument-before-claim, "verifier failed").

## 1b. Closest specs in tlaplus/Examples (repo master, listing fetched 2026-09-25)

Directory listing of `specifications/` has no spec named Lease/LeaseLock/Fencing/DistributedReplicatedLog.
Closest, in order of fit:

1. **`specifications/CheckpointCoordination/`** (`CheckpointCoordination.tla`, `MCCheckpointCoordination.tla`,
   `MCCheckpointCoordination.cfg`, `MCCheckpointCoordinationFailure.cfg`). Azure DNS RingMaster: primary
   grants a **checkpoint lease** to one secondary through a replicated log (RSL). Variables include
   `CurrentLease`, `TimeoutCounter`, `CanTakeCheckpoint`, `IsTakingCheckpoint`, `Leader`, `ReplicatedLog`,
   `IsNodeUp`, `NetworkPath`. Lease = `[node : Node, counter : LogIndex]`; expiry is **logical**:
   `currentLease.counter < TimeoutCounter` (ShouldReplaceLease), advanced by action `TriggerTimeout`.
   `SafetyInvariant`: leader never checkpoints; no two nodes checkpoint concurrently; replicated logs never
   conflict. `TemporalInvariant`: eventually a checkpoint is taken/completed. Actions: NodeFailure/Recovery,
   NetworkFailure/Recovery, ElectLeader, Send/Propagate/ProcessReplicatedRequest, Start/FinishCheckpoint,
   TriggerTimeout. Separate failure config = TEST PATTERN (same spec, fault-enabled cfg).
   -> **PROTOCOL PATTERN** directly reusable for UWCP: model lease TTL as a logical counter that a
   `Tick`/`ExpireLease` action advances, never as wall time; fence = lease counter. This is the right
   abstraction for "TTL counted from dispatch".
2. **`specifications/transaction_commit/`**: `TCommit.tla` (abstract commit; invariant `TCConsistent`:
   no RM committed while another aborted), `TwoPhase.tla` (2PC with TM; refines TCommit),
   `PaxosCommit.tla`, `2PCwithBTM.tla`, `APTCommit.tla`, `*_proof.tla`. -> **PROTOCOL PATTERN**
   refinement: write `UWCPAbstract` (one owner, atomic epoch) then `UWCPImpl` (lease store + queue +
   runner) and check `Impl => Abstract`. Invariant names from well-known file contents; bodies not
   re-fetched this session.
3. **`specifications/ewd998/`** — not a lease spec but the **reference trace-validation example**
   (`EWD998ChanTrace.tla/.cfg/.ndjson/.md`, `impl/`). See §1c.
4. **`specifications/lamport_mutex/`** (distributed mutual exclusion; INVARIANT mutual exclusion), and
   `specifications/raft/`, `specifications/MultiPaxos-SMR/`, `specifications/CCF/` for epoch/term
   monotonicity (term = UWCP fence generation analogue). `specifications/Disruptor/` (SPMC/MPMC ring
   buffer, goal "no data races between producers and consumers"; exact invariant names NOT verified).
   `specifications/allocator/` (resource allocator — reservation semantics, not fetched).

## 1c. Trace validation (the bridge TLA+ <-> implementation history)

`specifications/ewd998/EWD998ChanTrace.tla` @ tlaplus/Examples master (2026-09-25):
- The implementation logs one NDJSON object per event. The spec loads it:
  `JsonLog == ndJsonDeserialize(IF "JSON" \in DOMAIN IOEnv THEN IOEnv.JSON ELSE "...ndjson")`
  (modules `IOUtils`/`IOEnv` from CommunityModules — ships inside tla2tools in recent builds; verify on
  the pinned jar).
- `l == TraceLog[TLCGet("level")]` — the current log line is indexed by the behaviour depth.
- Per event kind a predicate `IsX` requires the log line's fields AND `<<X(args)>>_vars` — i.e. the line
  must be explained by a spec action from the current state. `TraceNext` = disjunction of `IsX`.
- `TraceAccepted` postcondition: violated if the behaviour TLC finds is shorter than the log (a line no
  action explains). `TraceView` includes `TLCGet("level")` so repeated states are not pruned.
- Invocation: `JSON=impl/trace-01.ndjson tlc EWD998ChanTrace`. Multi-process logs merged via vector
  clocks (`CausalOrder`) because they are "compiled out of several logs ... unordered".
- Classification: **TEST PATTERN** (trace validation) + **DATA MODEL** (NDJSON event log).

Fit for UWCP: very high, because UWCP *already* has the NDJSON-shaped artifact: the append-only goal log
is a totally-ordered event sequence written by one authority (no vector clocks needed for the log
itself). The dispatcher/queue history and node progress files are separate logs and need an ordering
rule (e.g. VPS receive time + per-source seq) — or trace-validate the goal log alone first.
Caveat (instrument-before-claim): trace validation proves the *logged* events are a legal behaviour.
It cannot see an effect that was not logged (e.g. a side effect taken by a runner with a stale fence
that never wrote a receipt). So the runner must log each side-effect attempt with its fence, or the
validator is blind by construction.

Paper: Cirstea, Kuppe, Loillier, Merz, "Validating Traces of Distributed Programs Against TLA+
Specifications", arXiv 2404.16075 (v1 2024-04-24, v2 2024-09-17), published in SEFM 2024 (Springer LNCS,
doi 10.1007/978-3-031-77382-2_8). Reduces trace checking to **constrained model checking with TLC**; traces
may carry only *updates* to spec variables and only a subset of variables (TLC fills the rest
nondeterministically). Java instrumentation API + TLA+ operators + run scripts. Found discrepancies in
every program they applied it to. (ALGORITHM + TEST PATTERN.) Artifact repo not named on the abstract
page; not chased.

Production uses (the pattern at industrial scale):
- **etcd-io/raft** `tla/` (last tla commit `96b36c48655634a04fd9dcd73d71886839f132a5`, 2025-12-21):
  `etcdraft.tla`, `MCetcdraft.tla/.cfg`, `Traceetcdraft.tla/.cfg`, `example.ndjson`, `validate.sh`,
  `validate-model.sh`. Go emits traces behind build tag `-tags=with_tla` through a
  `TraceLogger { TraceEvent(*TracingEvent) }` interface, NDJSON, **sampling disabled**; multi-node runs
  write to one file on one machine "to preserve the causality of events". Run:
  `./validate.sh -s ./Traceetcdraft.tla -c ./Traceetcdraft.cfg /path/to/traces/*.ndjson` (`-p` parallelism,
  `MAX_TRACE` env). Failure = "a state or transition the state machine can't accommodate".
- **microsoft/CCF** `tla/consensus/` (Traceccfraft.tla last commit `07384376697fdff058f1fdbc7d7a302508102abc`,
  2026-08-11): `ccfraft.tla`, `abs.tla`, `MCccfraft.*`, `SIMccfraft.*`, `SIMCoverageccfraft.tla`,
  `Traceccfraft.tla/.cfg`, `Network.tla`. -> **TEST PATTERN**: one spec, three drivers — exhaustive MC
  (small constants), random simulation (larger), trace validation (real runs).

UWCP fit: **good, second priority.** The goal log is already NDJSON-shaped, single-writer, totally ordered —
the hardest part (causal merge) disappears. Python needs no TLA+ library; it only emits the goal log
(exists) plus lease-store and dispatcher events. Cost ~80-120 lines of `TraceUWCP.tla` over the model.
Risk: long logs with many unlogged variables make TLC slow; validate per goal, short traces.

## 1d. Apalache (one paragraph)

apalache-mc/apalache: latest `v0.62.2` (2026-08-26); `v0.62.0` (2026-08-18) **raised the minimum Java to
21** — local JDK is 17, so Apalache needs a second JVM. License Apache-2.0 (prior knowledge, not
re-verified this session). Symbolic SMT (Z3) bounded checker; wants type annotations; strong for large
integer domains and checking inductive invariants, weaker than TLC for liveness, and the trace-validation
workflow is TLC-specific (`TLCGet("level")`, IOUtils). UWCP's state space is tiny and finite: TLC suffices.
Apalache is only worth it later to prove an inductive invariant over unbounded fence generations. Not now.

## 1e. DRAFT — smallest TLA+ model of UWCP's concurrency core (text only, not a repo file)

Scope: one goal, one exclusive resource class (one lease), the queue, the runner, harvest, operator
events. Everything else (capsules, routing, baseline) is abstracted to nondeterministic success/failure.

```
CONSTANTS Epochs (e.g. {e1,e2}), Execs ({x1,x2}), MaxTTL (2), MaxGen (3)
None == "none"
VARIABLES
  goal,      \* "active" | "paused" | "cancelled" | "converged"
  ep,        \* [Epochs -> [st: {"idle","dispatching","queued","running","ended"},
             \*             out: {None,"completed","failed","lost","expired","cancelled"},
             \*             obs: {"running","ended","lost","unknown"}, verdict: {None,"pass","fail","unknown"},
             \*             afterCancel: BOOLEAN]]
  jobs,      \* [Epochs -> {None} \cup [fence: 0..MaxGen, st: {"queued","running","done","killed"}]]
             \* keyed by run_token == epoch id  => a second Enqueue of the same token is a no-op
  gen,       \* lease store fence generation (monotonic)
  lease,     \* [holder: Execs \cup {None}, fence: 0..MaxGen, ttl: 0..MaxTTL, st: {"free","held","consumed"}]
  xfence,    \* [Execs -> 0..MaxGen]  fence each runner last saw (may be stale)
  hist       \* history variable: [effects: Seq(fence), dispatchOK: BOOLEAN, receiptOK: BOOLEAN]
             \* store as flags/max-fence, not full sequences, to keep the state space small
```

Actions (each ~3-8 lines):
- `Begin(e)`: goal="active", ep[e].st="idle", no other epoch with obs="unknown" (never replace on UNKNOWN)
  -> st "dispatching" (intent logged before the effect).
- `Enqueue(e)`: st="dispatching" -> jobs[e] := IF jobs[e]=None THEN new job ELSE jobs[e] (idempotent by
  run_token); st "queued". `CrashAfterIntent(e)` = no-op on jobs; `Recover(e)`: probe jobs[e] -> adopt
  ("queued") or end "lost".
- `Acquire(x)`: lease.st="free" -> holder x, gen' = gen+1, fence' = gen+1, ttl' = MaxTTL, xfence[x]' = gen+1.
- `Renew(x)`: lease.holder = x /\ lease.fence = xfence[x] -> ttl' = MaxTTL (holder-only).
- `Tick`: lease.st="held" /\ some job for it is running or dispatched -> ttl' = ttl-1 (TTL counts from DISPATCH:
  Tick disabled while the job is merely queued). `Expire`: ttl=0 -> st "free", holder None.
- `Dispatch(e,x)`: jobs[e].st="queued" /\ lease re-check -> (lease.holder=x /\ lease.fence=gen /\ ttl>0)
  ELSE job status lease_expired_in_queue (ep ends "expired"). Records hist.dispatchOK.
- `SideEffect(e,x)`: runner acts with xfence[x]; the **store** accepts only if xfence[x] = gen
  (fenced write); accepted effects append/raise hist max-fence. A variant `SideEffectUnfenced` exists only
  in the mutant config to prove the invariant can go red.
- `Receipt(e,x)` / `Harvest(e)`: accepted iff ep[e].st # "ended" /\ jobs[e].fence = gen; else refused +
  finding. Then `End(e,o)`.
- `NodeUnreachable(e)`: obs "unknown"; `Bound(e)`: after bound -> end "lost" as BLOCKED_ENVIRONMENT.
- `Judge(e)`: verdict from receipt; verdict "unknown" if obs was unknown.
- `OpPause`, `OpResume`, `OpCancel`: CAS on goal; `OpCancel` from any non-terminal; `OpPause`/`OpResume`
  disabled once goal="cancelled" (cancel dominates). `Converge`: goal := "converged" iff last epoch judged
  pass on the current revision. `Consume`: lease st "consumed" (absorbing).
- `Done == goal \in {"cancelled","converged"} /\ UNCHANGED vars` (explicit terminal stutter; do NOT rely
  on `-deadlock`).

Safety invariants (12; INVARIANT class):
1. `TypeOK`.
2. `AtMostOneValidOwner` == Cardinality({x \in Execs : lease.holder = x /\ xfence[x] = gen /\ lease.ttl > 0}) <= 1.
3. `StaleFenceCannotAdvance` == every accepted side effect carried fence = gen at acceptance
   (hist.maxEffectFence monotone; no accepted effect with fence < a previously accepted fence).
4. `CancelledNeverResumes` == goal = "cancelled" => \A e : ~ep[e].afterCancel /\ goal stays cancelled
   (`[][goal = "cancelled" => goal' = "cancelled"]_goal` as action property).
5. `ReceiptOnlyForOpenEpoch` == hist.receiptOK (no receipt accepted for an ended epoch or stale fence).
   **This is the invariant today's `ingest_receipt` does not enforce by itself** (§0).
6. `ExpiredLeaseNoNewDispatch` == hist.dispatchOK (no job started with ttl = 0 or fence # gen).
7. `DuplicateEnqueueOneJob` == structural via run_token keying; state it anyway as
   \A e : jobs[e] # None => job count for e = 1 (and a mutant with set-of-jobs must go red).
8. `UnknownNeverPass` == \A e : ep[e].obs = "unknown" => ep[e].verdict # "pass".
9. `NoReplaceOnUnknown` == \A e1,e2 : e1 # e2 /\ ep[e1].obs = "unknown" => ep[e2].st # "dispatching"
   unless e2 began before e1 went unknown (keep as a Begin guard + invariant over a flag).
10. `EndedIsTerminal` (action property) == [][\A e : ep[e].st = "ended" => ep'[e] = ep[e]]_ep.
11. `FenceMonotonic` (action property) == [][gen' >= gen]_gen; `ConsumedAbsorbing` similarly.
12. `ConvergedOnlyFromPass` == goal = "converged" => \E e : ep[e].verdict = "pass" /\ ep[e].out = "completed".

Liveness (with WF on Recover, Expire, Tick, Bound, Harvest; faults bounded by constraint):
- L1 `DispatchingResolves` == \A e : ep[e].st = "dispatching" ~> ep[e].st \in {"queued","running","ended"}
  (no epoch stranded between intent and enqueue).
- L2 `EveryStartedEpochEnds` == \A e : ep[e].st \in {"queued","running"} ~> ep[e].st = "ended"
  (unknown node eventually becomes BLOCKED_ENVIRONMENT, never hangs forever).

Mutation configs (TEST PATTERN, required so a green is earned): `UWCP_mutant_nofence.cfg` enables
`SideEffectUnfenced` -> must exit 12 on inv 3; `..._latereceipt.cfg` drops the ended check -> exit 12 on
inv 5; `..._pauseovercancel.cfg` -> action-property violation; `..._ttlfromqueue.cfg` lets Tick run while
queued -> expect `lease_expired_in_queue` reachable and L2 still holding. Positive control: base cfg exit 0
with `-coverage 1` showing every action fired (non-zero coverage) — an action with zero coverage means the
model never reached that branch and the green is vacuous.

State-space estimate (2 epochs, 2 execs, 2 operators modelled as interleavings of Op* actions, MaxTTL=2,
MaxGen=3, history kept as flags/max): per-epoch record reachable ~20-40 combos -> ~10^3 for two; lease
~3 holders x 4 fence x 3 ttl x 3 st ≈ 10^2; goal 4; xfence 16; flags 8. Upper product ~5x10^7, reachable
(well-guarded) plausibly **10^4 - 10^6 distinct states**. TLC typically explores 10^5-10^6 states/min/worker
on a laptop, so with `-workers auto` and `SYMMETRY Permutations(Execs)` (roughly halves it) expect
**seconds to ~2 minutes**; liveness checking adds a multiple. Estimate, not measured — the first run's
"distinct states found" line is the measurement. If it exceeds ~10 min, the model has a redundant variable
(usually a full-sequence history); replace by a flag.

Note on symmetry: TLC disables/warns about liveness checking under SYMMETRY in some configurations; run
safety with symmetry and liveness in a separate cfg without it (recalled behaviour, verify on first run).

---

# TASK 2 — JEPSEN

Sources: github.com/jepsen-io/jepsen main HEAD `9ea74ea6ef7a11367bcfb66ad103678a19077f0e` (2026-09-22,
"Version 0.3.15-SNAPSHOT"); github.com/jepsen-io/elle (repo page 2026-09-25; raw README path 404'd, the
rendered page was read); jepsen.io/analyses pages as dated below.

## 2a. History model (DATA MODEL)

`jepsen/doc/tutorial/03-client.md` @ 9ea74ea: an operation is a map `{:type :f :value :process :time}`
(plus `:index`). `:invoke` = attempt begins; completion is one of `:ok` (happened), `:fail` (**definitely
did not happen**), `:info` (**indeterminate — may or may not have happened**). An exception in a client
is converted to `:info`. A process whose op ended `:info` is treated as crashed; the generator continues
with a fresh process id, so a process never has two concurrent ops and an `:info` op stays "open
forever" (may take effect at any later time). (Last point: Jepsen's documented semantics; the tutorial
wording was paraphrased by the fetch tool.)

UWCP mapping: `:info` == UNKNOWN. This is exactly §14's "node unreachable -> UNKNOWN -> never replace".
The key consequence Jepsen encodes, and UWCP must too: **an :info op's effect window is unbounded to the
right** — a checker must allow it to take effect any time after invoke, including after the epoch that
issued it "ended". That is why a late receipt must be *refused by the authority*, not merely unexpected.
A UWCP history should record, per epoch attempt: invoke (epoch.dispatching with run_token), and
completion ok/fail/info distinctly; `lost` and `unknown` observations are `:info`, never `:fail`.
ANTI-PATTERN: mapping "worker vanished" to `:fail` — lets a checker assume the work did not happen and
approve a replacement that then races the ghost.

## 2b. Nemesis design (FAULT-INJECTION PATTERN)

`jepsen/src/jepsen/nemesis/combined.clj` @ 9ea74ea: a **nemesis package** is a map
`{:nemesis :generator :final-generator :perf}` — the fault mechanism, the schedule producing fault ops,
the cleanup schedule that returns the system to a known-good state at the end, and plot metadata;
packages compose ("an algebra for composing both simultaneously"). Fault packages: partition (grudge
patterns), packet (delay/loss/corruption), kill, pause (SIGSTOP/SIGCONT), clock (offset/strobe/reset),
file-corruption (bitflip/truncate). Targets: `nil` random, `:one`, `:minority`, `:majority`,
`:minority-third`, `:primaries`, `:all`, or explicit nodes. Schedule: `:interval` (default 10 s) between
fault ops; `:faults` set selects which packages are active. Faults are themselves **ops in the history**
(`:process :nemesis`), so the checker sees when a fault happened relative to client ops.

UWCP translation (no Clojure needed): a Python nemesis table keyed to §14 rows —
`kill_between_intent_and_enqueue`, `pause_runner(SIGSTOP > TTL)` (the etcd/Kleppmann case),
`kill_job`, `kill_worker`, `partition_vps_gex44` (ssh drop), `clock_skew_gex44`, `truncate_capsule`,
`duplicate_enqueue`, `late_receipt_replay`, `operator_pause_cancel_race`, `home_crash_mid_append`.
Each must be written into the same history as client ops, and each needs a final-generator (heal: SIGCONT,
restore link) so the run ends checkable. The pause fault is the single most valuable one for a lease
protocol (see 2e).

## 2c. Checker composition (TEST PATTERN)

`jepsen/src/jepsen/checker.clj` @ 9ea74ea:
- `compose`: map of name -> checker; runs each (possibly in parallel), returns per-name results plus a
  top-level `:valid?` merged over all.
- `merge-valid` priority `{true 0, :unknown 0.5, false 1}` — **false dominates unknown dominates true**.
- `check-safe`: wraps checker exceptions into `{:valid? :unknown :error ...}` — a crashed checker is
  UNKNOWN, never true.
- `unbridled-optimism`: always `{:valid? true}` ("Everything is awesoooommmmme!") — the named null
  checker; `noop` returns nil. `perf` = latency + rate graphs; `stats` success/failure by `:f`;
  `unhandled-exceptions`; `linearizable` (Knossos, `:linear` or `:wgl`).
- Principle: checkers are pure functions of `(test, history, opts)`; they never query the system under
  test. The verdict is recomputable from the stored history alone.

For UWCP: adopt `check-safe` semantics (checker crash -> UNKNOWN) and pure-function checkers over a stored
history. **Deliberate divergence**: Jepsen's merge lets `false` outrank `:unknown`; the estate doctrine
(`instrument-before-claim.md`, "verifier failed outranks subject failures") says a run in which a checker
could not judge is not a verdict about what it skipped. Report both (the merged valid? AND a separate
`any_unknown`), and never let a false-from-one-checker hide an unknown-from-another in the done-gate.
`unbridled-optimism` is useful as UWCP's **negative control**: the gate harness must prove that swapping a
real checker for it turns a known-bad fixture history green -> i.e. the harness detects that it is being
lied to (a mutation of the checker, not of the system).

## 2d. Elle vs Knossos vs a custom checker (ALGORITHM)

- Knossos (`checker/linearizable`): searches for a linearization of a register/queue/set model; the
  problem is NP-complete, runtimes "diverge exponentially with concurrency" (Elle README) — practical for
  hundreds of ops.
- Elle (EPL-2.0 or GPLv2+CPE): infers version orders from **list-append** (unique appended elements make
  every read reveal a prefix of the version order) or weaker **rw-register** workloads; builds a
  dependency graph (ww, wr, rw, plus realtime and process edges) and finds cycles = Adya anomalies
  (G0, G1c, G-single, G2, internal inconsistency); "linear-to-log-linear", handles 10^5+ ops. It checks
  **transactional isolation**, not mutual exclusion.
- UWCP's properties are **not** register linearizability and **not** transaction isolation. They are
  per-resource safety predicates over a sequenced log: single valid owner, fence monotone at the fenced
  store, no receipt after end, no dispatch on expired lease, one job per run_token, unknown never pass,
  cancel absorbing. **Neither Elle nor Knossos is the right tool.** The right tool is a custom invariant
  checker over the event history — essentially the TLA+ invariants of §1e evaluated on the recorded
  history (which is what trace validation does, via TLC). The one Jepsen-standard workload that does
  transfer is a **lock/fence-register test**: every protected write carries its fence; a checker asserts
  accepted writes are strictly fence-monotone and that no two holders' write intervals overlap in real time
  (that last part is an interval check, O(n log n), no search).
  Elle's *technique* worth borrowing: make values **unique and traceable** (every effect carries
  `(epoch_id, run_token, fence, seq)`) so ordering is inferred from data, not from clocks.

## 2e. Analyses with lease/lock/fencing lessons (FAILURE PATTERN)

1. **etcd 3.4.3** (jepsen.io/analyses/etcd-3.4.3, 2020-01-30). Symptom: "multiple clients may hold the
   same etcd lock simultaneously", even without faults; with 2 s lease TTLs and process pauses ~18% of
   acknowledged updates lost. Root cause: (a) lease expiry while the holder was paused; (b) a bug where
   after a blocking wait "the server would not re-check to make sure the lease was still valid before
   informing the client that they now held the lock". Abstraction: **check-then-act across a wait; lease
   validity sampled before the blocking step**. Fix advocated: fencing tokens = the lock key's revision,
   "operations using a lower token x < y must fail"; or transactional guard on the lock key's version.
   UWCP exposure: HIGH — dispatcher lease re-check at dispatch and runner fence re-check "before each side
   effect" are the same shape; any await/spawn between re-check and effect is the window
   (destructive-state-authorization.md "final check to effect"). Falsification test: SIGSTOP the GEX44 runner
   after its fence check for > TTL, let the reconciler acquire a new lease + dispatch epoch 2, SIGCONT;
   assert the fenced store (git push target / receipt ingest) refuses the old fence, and the history
   checker reports zero accepted effects with fence < max accepted fence.
2. **Redlock / Kleppmann** ("How to do distributed locking", martin.kleppmann.com 2016-02-08). Symptom:
   GC pause longer than TTL -> two holders ("it may go ahead and make some unsafe change"; HBase hit this).
   Root cause: lock without a monotonic token and a storage layer that does not check it; safety resting on
   bounded pauses/clock drift. Abstraction: **a lease is a hint unless the resource verifies a fence**.
   UWCP exposure: HIGH — "TTL counted from dispatch" is timing-based; only the fence makes it safe. The
   side-effect targets (VPS goal log ingest, git remote, provider ledger) must each check the fence
   themselves; a runner-side self-check alone is Redlock. Falsification test: same pause drill, plus a
   mutant where the ingest ignores the fence -> checker must go red (proves the test can fail).
3. **Hazelcast 3.8.3** (jepsen.io/analyses/hazelcast-3-8-3, 2017-10-06). Symptom: "two members from
   different clusters can acquire the same lock"; IdGenerator ~10-11% duplicate IDs under partition. Root
   cause: AP split brain; quorum protection applies only after a detection window. Abstraction: **an
   authority that can split grants twice; an ID source without consensus duplicates**. Recommendation:
   "couple them to a sequentially consistent sequence number". UWCP exposure: LOW-MEDIUM — UWCP has one
   authority (VPS, flock), so no split brain *if* nothing else mints fences or run_tokens. Exposure appears if
   the Windows slot_ledger (§9 "becomes a projection") ever grants while the VPS is unreachable. Test: cut
   Windows<->VPS, attempt acquire from Windows -> must be BLOCKED, never a local grant; checker asserts every
   fence in the history was minted by the VPS host id.
4. **ZooKeeper** (jepsen.io/analyses zookeeper, 2013) and **Consul** (2014) — recalled, NOT re-fetched this
   session. ZooKeeper passed linearizability for its primitives; the recurring lesson from ZK/Curator
   recipes is that a client's session can expire while it believes it holds the lock, so the lock znode's
   `czxid`/sequence must be used as a fence downstream. Consul 2014 found stale reads from the leader
   before a consistency mode was added (reads not linearizable by default). Abstraction: **"I hold it"
   is a belief about the past**; reads served by a possibly-deposed leader are stale. UWCP exposure: the
   status/attach control surface reading a projection — must label freshness, never authorize from it.
5. **etcd again (lease + watch) / general**: the analyses repeatedly show that the *client library* adds
   the unsafe step (a wait between validity check and grant). UWCP analogue: the dispatcher wrapper around
   `gex44_cli queue add`. Test: inject a delay (sleep hook) between the dispatcher's lease re-check and job
   launch; expire the lease inside it; expect `lease_expired_in_queue`, not a running job.

---

# TASK 3 — FEASIBILITY FOR CPP

Environment facts: local JDK 17.0.19 present (TLC floor Java 11 OK; Apalache needs 21). Repo is Python
first; Windows dev + Linux VPS. Gates are `tools/test_*.py` with `V-*` lines.

## Option (1) TLA+ spec + TLC, dev-only, wrapped by a Python gate

- Artifacts: `vault/specs/tla/UWCP.tla` (~250-350 lines), `UWCP.cfg` + 4 mutant cfgs (~15 lines each),
  optional `TraceUWCP.tla` (~100). Gate `tools/test_uwcp_tla.py` (~150-200 lines): locate java; locate
  pinned `tla2tools.jar` by **sha256** (outside git or LFS; not downloaded by the gate — absent jar =
  INCONCLUSIVE/UNJUDGED, never PASS); run `java -jar tla2tools.jar -workers auto -config X -dumpTrace json
  cex.json -noGenerateSpecTE -coverage 1 -metadir <tmp> UWCP.tla`; map exit codes: 0 -> PASS; 10-14 ->
  SUBJECT VIOLATION (with parsed counterexample); 75-77/150-153/255 -> VERIFIER FAILED. V-gates: base cfg
  exits 0 AND "distinct states" >= floor AND every action coverage > 0; each mutant cfg exits 12 (or 13)
  naming the expected invariant.
- ROI: high for the design phase — the counterexample for `ReceiptOnlyForOpenEpoch` is likely on the
  first run (§0 gap). Cheap to run (seconds). Limitation: proves the **model**, not the code.
- Theatre version: a spec whose invariants are implied by its own action guards with no mutant cfg
  (every invariant trivially true); a gate that treats "jar missing" or exit 255 as pass; a gate that
  greps stdout for "No error has been found" (present also on some partial runs) instead of the exit
  code; a spec with no failure actions (no crash, no pause, no late receipt) — then nothing can go wrong;
  running with `-deadlock` to "fix" a deadlock the model actually has.

## Option (2) CPP-native Python history checker (Jepsen-style, no Clojure)

- Input: the goal log (`GoalLog` NDJSON, already authoritative), the VPS lease-store journal (acquire,
  renew, expire, consume with fence and host id), the dispatcher history (queue add/dispatch/ack/collect
  with run_token), and the **fenced stores' acceptance/refusal log** (receipt ingest, writeback push).
  Normalize into ops `{type: invoke|ok|fail|info, process, f, value, time, source, seq}`.
- Checkers (pure functions, `check_safe` wrapper): single-valid-owner (interval overlap over lease
  journal), fence-monotone-at-store, no-receipt-after-end, no-dispatch-on-expired, one-job-per-run_token,
  unknown-never-pass, cancel-absorbing, info-is-not-fail. Compose with a verdict that keeps UNKNOWN separate.
- Nemesis: Python drill table on GEX44/VPS (SIGSTOP/SIGCONT runner, kill job, ssh partition via iptables
  or sshd stop, clock offset, capsule truncate, replay receipt) recorded into the same history.
- Size: normalizer ~200, checkers ~300, nemesis drills ~250, gate + synthetic histories (red + green
  fixtures per checker) ~300 -> **~1,000-1,100 lines**. Checkers alone (on synthetic histories) ~500 and
  are useful immediately; the nemesis half needs the real VPS/GEX44 path (validation plane).
- ROI: highest long-term — it judges the **real system**. It is the only one that can catch an
  implementation bug the model does not have.
- Theatre version: a checker that reads only the system's own final status (`goal=CONVERGED`, epoch
  outcomes) — that is the system grading itself; a checker fed only by the goal log (the authority's own
  record) cannot see an effect the authority never logged, i.e. the stale-fence write that is the whole
  point — the fenced stores' logs and the runner's attempt log must be independent inputs; histories
  generated by the same code path under test; a nemesis that never actually paused anything (no
  precondition proof — assert the runner's `/proc/<pid>/stat` state was `T` during the window);
  `:info` folded into `:fail`; a green with zero ops judged (needs a floor on ops and on faults injected).

## Option (3) both — recommended split

TLA+ first (design-time, 1-2 days, finds protocol bugs before the lease store is written), then the Python
history checker as the runtime oracle; share one vocabulary: the invariants' names in §1e are the checker
names, so a TLA+ counterexample and a runtime violation cite the same id. Trace validation (`TraceUWCP.tla`
over the goal log) is the optional bridge later; it is cheaper than it looks because the goal log is
already single-writer ordered.

---

# RECOMMENDATION

1. **Do (3), in this order.** (a) Fix now, independent of tooling: make `ingest_receipt` refuse an epoch in
   state `ended` and (once fences exist) a stale fence — at the function, not by caller order (epoch.py:256).
   (b) Write `UWCP.tla` per §1e with four mutant cfgs; Python gate wraps TLC with exit-code mapping and
   coverage floor; dev-only, jar pinned by sha256, absent jar = UNJUDGED. (c) Build the Python history
   checker (~1k LOC) whose inputs include the fenced stores' own acceptance logs, not just the goal log;
   drive it first with synthetic red/green histories, then with the GEX44 pause drill (etcd/Kleppmann
   scenario) on the validation plane.
2. **Do not adopt Jepsen/Elle/Knossos code.** Clojure + JVM runtime for a Python estate, and the properties
   are not linearizability/isolation. Adopt the data model (`:info` distinct), `check-safe`, pure
   checkers, nemesis-as-ops-in-history, final-generator healing.
3. **Fences must be checked by every side-effect target**, not only by the runner (Kleppmann). If git
   writeback cannot check a fence, it must go through a VPS-side verb that does.
4. Apalache: not now (Java 21, no trace-validation workflow).

# LICENSE + MAINTENANCE

| Component | License | Status (as observed 2026-09-25) | Use in CPP |
|---|---|---|---|
| tlaplus/tlaplus (tla2tools.jar) | MIT | Active; master `5d53605` 2026-09-25; stable v1.7.4 (2024-08-05); v1.8.0 rolling prerelease | dev-only jar, pinned by sha256, not vendored in git |
| tlaplus/Examples | MIT (repo-level; per-spec authors — verify per file before copying) | Active | read/reference; copy patterns not files |
| CommunityModules (IOUtils/ndJsonDeserialize) | MIT | bundled in recent tla2tools (verify on pinned jar) | trace validation only |
| apalache-mc/apalache | Apache-2.0 (not re-verified) | Active; v0.62.2 2026-08-26; Java 21+ | not now |
| jepsen-io/jepsen | EPL-1.0 (recalled; not re-verified) | Active; main `9ea74ea` 2026-09-22, 0.3.15-SNAPSHOT | patterns only, no code |
| jepsen-io/elle | EPL-2.0 or GPLv2 w/ classpath exception | Active | technique only (unique traceable values) |
| jepsen-io/knossos | EPL (recalled) | Maintained, lower activity | not applicable |
| etcd-io/raft tla/ | Apache-2.0 (etcd project) | tla last commit `96b36c4` 2025-12-21 | reference for trace validation harness |
| microsoft/CCF tla/ | Apache-2.0 | Traceccfraft last commit `0738437` 2026-08-11 | reference for MC/SIM/TRACE triad |

Maintenance cost for CPP: the TLA+ spec must change in the same commit as any protocol change (lease verbs,
epoch states) — otherwise it becomes a documented capability that no longer describes the code
(documented-capability-must-be-executable.md). Trace validation is the mechanism that keeps them honest.
