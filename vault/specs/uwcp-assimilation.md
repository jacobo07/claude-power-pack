---
status: APPROVED 2026-09-25 by Owner ("y", Q1-Q6 as recommended) + Owner addition: "reconstruct everything we can't include in claude power pack" -> §14 Reconstruction track
opened: 2026-09-25
branch: feature/knowledge-acquisition
baseline_head: 4366543
covers: [uwcp-assimilation, external-architecture-assimilation, distributed-verification, tla-plus, history-checker, fencing, lease-fencing, workspace-capsule-object-model, provider-routing-decision-record, observability-correlation, external-failure-corpus, evidence-class, unknown-never-licenses]
extends: [uwcp.md (APPROVED 2026-09-25)]
research: vault/knowledge_base/uwcp_assimilation/research/ (A1 Temporal+etcd, A2 TLA+Jepsen, B1 CAS/workspace, B2 routing/obs/thresholds, L0 local, P4 audit)
---

# UWCP External Architecture Assimilation -- plan r2

Amends the approved UWCP plan. Adds no platform and no runtime dependency. Two delivery lanes:
- LANE L (the live UWCP pane, which owns modules/gsd_x/goal and its tests) executes every A-nn
  amendment, X0, X3 and X4, reading them from `vault/specs/uwcp.AMENDMENTS.md`, each inside the
  host slice named there.
- LANE R (this pane) writes only NEW files outside modules/gsd_x/goal: X1, X2, X5, X6, UKDL, X8.

## 1. Mode
ULTRA for this plan. Afterwards: X1, X5, X6 EXECUTION; X2 PLAN checkpoint (model semantics);
A3, A5 keep PLAN checkpoints (live infra); X3/X4 EXECUTION inside Lane L once ownership is fixed by
this plan. Nothing re-ULTRA'd unless a new authority question appears.

## 2. Reality delta (HEAD 4366543)
Landed since uwcp.md: 5e79e61 plan, e6b6411 characterization, 9c7a3c6 portable_repo_id, 13c9f16
dir fsync, c58e00f evidence.hypothesis, bd0d831 S1-6 bounded brief, 53f75ec S1-7 operator events,
cf4d71b S1-8 fence (receipt refused when epoch ended or fence stale), 99f587c S1-9 eol-invariant
pins, plus gsd-mission fixes. Live pane contract at S1-10/11. Goal engine is ORPHAN per
reachability (known, owned by the UWCP program). GitHub MCP 401 this session; upstream reads via
public REST/raw.

## 3. Contribution per family (detail in research files)
Temporal v1.32.0 MIT: fence inside the write txn, deposed owner self-stops, completion echoes full
attempt identity, stale-token vs stale-view, four clocks, graded suggest/warn/error bounds.
etcd v3.7.2 Apache-2.0: lease = liveness, fence = safety (Jepsen 3.4.3, #11456), clock restart
makes leases immortal (#9888, #21372), revoke clears guarded state atomically, ack-before-durable
(#14370). TLA+ MIT (TLC v1.7.4 on local JDK 17): exit codes separate violation from tool failure;
CheckpointCoordination logical-counter lease; trace validation in etcd-raft and CCF. Jepsen EPL:
:info != :fail, pure checkers over stored history, faults as ops, heal step. REAPI Apache-2.0:
Digest {hash,size}, canonical trees, referenced blobs must exist, FindMissingBlobs. restic BSD-2 /
Kopia Apache-2.0: GC races unpublished writers, structural vs content verify. git: clean-form ids;
`bundle verify` structural only (MEASURED). LiteLLM MIT+ee: error-class retry default 0, bounded
non-revisiting chain, budget-race corpus. vLLM/SGLang: static VRAM fraction of TOTAL vs FREE.
llama.cpp: /health /slots timings. OTel: W3C ids, TRACEPARENT env (RC), gen_ai names (Development).
OpenHands MIT: session != runtime, tools pinned on resume. NATS/Nomad(BUSL-1.1)/Ray: thresholds.
Daytona: no LICENSE at HEAD, unmaintained.

## 4. Assimilation matrix
| family | disposition | destination |
|---|---|---|
| Temporal | ABSORB CONCEPTS + FAILURE CORPUS; REJECT replacement (server+DB+workers vs one home, CLI-harness executors, 3.6 GB free VRAM-less VPS; its update dedup is per-run, weaker than the goal-scoped need) | A1 A4 |
| etcd | ABSORB CONCEPTS + FAILURE CORPUS; REJECT install (single home, flock CAS suffices) | A2 A5 |
| TLA+/TLC | ADOPT DEVELOPMENT DEPENDENCY (jar pinned by sha256, outside git, never on VPS/GEX44) | X2 |
| Apalache | REJECT now (Java 21, no trace validation) | - |
| Jepsen/Elle/Knossos | ABSORB CONCEPTS + TEST PATTERNS; REJECT code | X3 X4 |
| TLA+ trace validation | KEEP AS MIGRATION OPTION (after X2+X3) | X9 |
| REAPI | ADAPT DATA MODEL | A6 |
| Bazel / Dagger | REFERENCE ONLY (corpus / naming) | X5 |
| restic / Kopia | ABSORB CONCEPTS; REJECT CDC and keyed ids | A6 |
| git + LFS | ADOPT as object model (existing dependency) | A6 |
| LiteLLM | REFERENCE ONLY (HTTP-only; 2026-03-24 PyPI compromise) | A7 |
| vLLM / SGLang | REJECT for GEX44 now; reuse bench metric definitions | A7 §10 |
| llama.cpp | KEEP; wire /health /slots timings | A7 |
| OpenTelemetry | ADOPT FORMATS + NAMES only | A8 |
| OpenHands | REFERENCE ONLY | A7 |
| NATS / Ray | MIGRATION OPTION with thresholds | §10 |
| Nomad | CONCEPTS ONLY (BUSL-1.1 blocks adoption) | §10 |
| Daytona | REJECT | - |

## 5. Gap map (symbol@4366543; P4-verified)
- G-L1 "UNKNOWN reads as LOST", two paths: (observe) providers/claude.py Observation `no child handle
  in this process` -> OBS_LOST (claude.py:144, codex.py:262) -> reconcile HARVEST -> successor while
  the original runs; (probe) Provider.probe `-> dict | None`, recover maps None -> LOST; claude.py
  returns None on OSError and on pid=None after Popen-before-rewrite. Five implementers + test fakes.
- G-L2 codex account lock takeover race (codex.acquire_lock): torn read -> stale -> overwrite; two
  stale-takers both win; no fence.
- G-L4 evidence classes exist as prose (uwcp.md:241) and as done_gate/strength_ladder
  (claim <= evidence) and decision_review/epistemic_algebra (weakest-link meet); no class axis there.
- G-L5 model-routing.json ids two generations stale; cost_collapse reason depends on PYTHONHASHSEED.
- G-L6 reconcile.decide: UNKNOWN observation -> WAIT unbounded, and step 2 (wait) precedes step 2b
  (operator intervention) -> an UNKNOWN epoch starves cancel. sweep observes only gate epochs today.
- G-L7 claude/codex budgets = used_today() then append, per host.
- G-T5b begin() refuses only a same-info_key open epoch (holds by reconcile order + CAS).
- CLOSED by cf4d71b: late receipt after end, stale fence at ingest.
Upstream-derived (design): G-T2a fence checked before the effect; G-T2b no deposed-runner self-stop;
G-T3a receipt identity incomplete; G-T3b stale-view vs stale-receipt; G-T4 no queue-wait bound, and
queue-wait expiry must release the lease; G-T5 operator-event dedup goal-scoped; G-T1 only the error
rung; G-E1a min TTL; G-E1b clocks restart with owner; G-E1c expiry bumps fence atomically; G-E3
node-local resources unfenced; G-W5 bundle verify structural; G-W6 remembered heads; G-W7 retention
vs in-flight; G-W12 two content identities (S1-9 blob_oid CRLF-normalizes; git clean honours
.gitattributes); G-R1 exit-0 quota text; G-R2 TRUNCATED same-window rung; G-R3 multi-class lease.

## 6. Amendments (delivered via uwcp.AMENDMENTS.md to Lane L)
A1 -> S1-8b (new delta slice): receipt echoes {goal_id, epoch_id, run_token, fence, revision}, ingest
   compares all; refusal codes stale_fence | epoch_ended | epoch_mismatch | revision_mismatch |
   duplicate; receipt fence greater than the projection -> reload once, then judge; begin() refused
   while ANY epoch is open.
A2 "UNKNOWN NEVER LICENSES ANYTHING" (-> S1-8b + S4-26): (a) observe returns UNKNOWN, not LOST, for
   "not my child"/unreadable; (b) probe returns a closed tri-state FOUND|ABSENT|UNKNOWN, recover
   treats any other return as UNKNOWN, pid=None-after-Popen is UNKNOWN; implementers enumerated
   structurally; (c) decide() evaluates operator cancel/pause BEFORE any UNKNOWN wait; (d) a WAIT on
   UNKNOWN past its deadline -> BLOCKED_ENVIRONMENT, whose only exits are a positive observation or
   an operator cancel that bumps the fence; (e) a successor epoch after UNKNOWN is permitted only
   once node fencing (A3) is live.
A3 (-> S5-33 runner + S5-30 dispatcher; PLAN checkpoint): the fence is HELD WITH the effect: the
   runner holds a node flock on the resource lockfile across each side effect; the dispatcher takes
   the same flock to bump the fence; a stopped holder is killed, never bypassed; on a stale fence the
   runner stops all effects and exits non-retryable `lease_fenced`. Git writes go to
   refs/uwcp/<goal>/<fence>; the home promotes by update-ref with the expected old value, after the
   receipt append, idempotently. dolphin_slot/gpu_vram acquired through the same node lockfile.
A4 (-> S5-30 + S6-40): four clocks (queue-wait, epoch budget, stall, goal max_hours), each an
   absolute deadline owned and judged only by the host that wrote it (node uses monotonic durations);
   never restarted by an owner restart. QUEUE_WAIT_EXCEEDED releases the lease and bumps the fence in
   the same critical section. Graded suggest < warn < error for brief bytes, capsule bytes, goal-log
   events; suggest sets suggest_handoff. operator.cancel exempt from every size bound. Operator event
   ids deduped at goal scope.
A5 (-> S4-25 lease store; PLAN checkpoint): min TTL >= 3 x renew interval + measured RTT, else
   refused; expiry and queue-wait expiry bump the fence inside the flock critical section; multi-class
   acquisition all-or-nothing; refuse nfs/fuse/overlay; ack only after fsync; reserve and takeover are
   single atomic steps.
A6 (-> S2-13..18, S3-19): capsule = canonical manifest named {sha256,size}; index_tree and
   worktree_tree from a synthetic index seeded from base (read-tree); untracked (path, sha256, size,
   mode); gitlinks + LFS oids; conversion_env is a correctness baseline field; restore by objects +
   node checkout-index, never git apply; content verify = part digests + fetch with fsckObjects;
   node "have" asked at dispatch with full-bundle fallback; retention keeps last N receipts UNION
   queued/running manifests, age margin >= epoch budget + transfer, two observations, RETIRED outcome;
   refuse unmerged, case-colliding, required-filter/LFS absent. Identity relation stated: S1-9
   blob_oid (CRLF-normalized pin) and worktree_tree (git clean form) agree exactly when conversion_env
   is equal; otherwise verify says COMPATIBLE_WITH_DECLARED_DRIFT; git_state stays the one owner.
A7 (-> S6-37/38/39): Provider Routing Decision Record in epoch.dispatching (fields per B2), pure and
   replayable; bounded non-revisiting chain; error-class retries default 0; positive semantic list
   (exit 0 + quota/limit/auth text -> UNAVAILABLE/AUTH_FAILED; real-binary behaviour MEASURED in S6
   before the list is trusted); TRUNCATED skips same-window rungs; ctx and availability read live from
   llama-server with measured_at; falsy-zero config refused; reserve/commit/release on the one VPS
   ledger with an explicit `leaked` state; tools/hooks pinned per epoch. Adjacent: routing ids ->
   current catalog; cost_collapse determinism test.
A8 (-> §16): W3C trace-id minted at declare, stored in the goal log; span-id per epoch/provider call;
   TRACEPARENT in child env and as a field of uwcp.control/1 verbs and job records; JSONL spans beside
   the goal log (gen_ai.* pinned + uwcp.*); no SDK/Collector/exporter; emission failure counter;
   authority rule tested: telemetry removed -> byte-identical decisions.

## 7. Slices
Lane R (new files only):
X1 vault/knowledge_base/uwcp_assimilation/{INDEX.md, research/*.md} -- dispositions, rejections,
   thresholds, provenance per claim (repo, SHA/tag, date, license, VERIFIED|OBSERVED|RECALLED); a
   graphify query test proves "why did we reject Temporal" resolves.
X2 vault/specs/tla/UWCP.tla + UWCP.cfg + UWCP_pre_cf4d71b.cfg + 4 mutant cfgs; Bound = BLOCKED
   (not lost), liveness L2 = started epoch ~> ended OR blocked-with-operator-exit; FalseLost action
   (observe says LOST while running). Gate tools/test_uwcp_tla.py: PASS | SUBJECT_VIOLATION |
   VERIFIER_FAILED | UNJUDGED, coverage and state floors, no -deadlock. Conformance link: every
   counterexample is replayed as a failing Python characterization test against the code (handed to
   Lane L as the red test for its A-nn).
X5 vault/datasets/uwcp/external_failure_corpus.jsonl (~25) + tools/test_external_failure_corpus.py:
   every entry has a destination; OWED names a slice; stale-entry clause; license gate refuses
   adoption of any RECALLED-license item.
X6 evidence-class axis inside modules/done_gate/strength_ladder.py (THEORETICAL, MODEL_CHECKED,
   SIMULATED, LOCAL/REMOTE/PRODUCTION/HARDWARE_REALITY; no cross-class promotion; weakest link via
   epistemic_algebra meet) + its test.
X8 ratchet proposal `distributed_correctness` (applicability: a stateful primitive that can race,
   replay or split), proposed only; promotion owed after UWCP Golden 01.
UKDL, meta-analysis, handoff.
Lane L (via AMENDMENTS.md): A1-A8 in host slices; X0 codex lock (rename-to-unique-tombstone, O_EXCL
create, unparseable lock older than the bound stale through the same path; barrier race test);
X3 history checker at modules/gsd_x/goal/history.py (op model invoke|ok|fail|info; checker names ==
TLA+ invariants; any_unknown separate; crash -> UNKNOWN; ops floor; unbridled-optimism negative
control; source today = goal log only, stated; lease journal/dispatcher/fenced-store logs join as
they are built); X4 extend tools/test_gsd_x_goal_chaos.py with the §14 rows as declarative faults.
X9 deferred: trace validation.

## 8. Dependencies
Adopted: tla2tools.jar v1.7.4 (MIT), dev-only, sha256-pinned, NOTICE.md entry. Runtime: NONE.

## 9. Evidence honesty
GEX44 pause drill (SIGSTOP runner past TTL, second epoch, SIGCONT, old fence refused) = REMOTE_REALITY,
not HARDWARE; runs only through a dispatcher signal verb with an allow-list (part of A3, PLAN
checkpoint). MODEL_CHECKED is never promoted to any REALITY class.

## 10. Migration thresholds
llama.cpp -> vLLM/SGLang: dedicated GPU AND >=48 GB (or >=24 GB + validated 4-bit MoE) AND sustained
requests_deferred > 0 AND >=20 GB free disk. ctx 32k -> larger: TRUNCATED >10 % of qwen epochs AND KV
VRAM free. Routing -> gateway: >=3 HTTP providers AND >=5 req/min each. Collector: >=3 emitting
hosts, or a push consumer, or >100 MB/day. Dispatcher -> JetStream: >=2 dispatcher hosts, or flock
waits >0/day with p99 enqueue >1 s, or delivery while the queue host is down. placement.py ->
scheduler: >=4 nodes or >=3 classes with >1 feasible node, or double-placement refusals >0/week, or
gang reservations. Temporal: >=2 replicated authority homes, or >100 concurrent workstreams, or
code-defined workflows replacing CLI harnesses.

## 11. Certified primitive candidates
Monotonic Fencing Token (A3+A5+cf4d71b) · Tri-state Probe/Observe (A2) · Content-Addressed Workspace
Manifest (A6) · Provider Routing Decision Record (A7) · Cross-Node Trace Context (A8) · History
Consistency Checker (X3) · TLC Gate (X2). Not duplicated: goal-log CAS, keos_qwen outcome,
evidence.hypothesis, info_key loop, done_gate ladder, gsd_x chaos suite.

## 12. UKDL candidates
HR lease protects only where the resource checks the fence (cites PR-LEASE-NEEDS-AN-OPERATOR-OVERRIDE-001,
T-CONT-19) · HR UNKNOWN never licenses a replacement · HR a clock restarted by its owner is an immortal
lease. PR fence held with the effect · PR predict counterexamples, then replay them as code tests · PR
histories from independent sources · PR graded bounds, kill switch exempt · PR capsule identity by
seeded synthetic index, restore by objects. T bundle verify passes a corrupt pack (MEASURED) · T TLC
-deadlock disables deadlock checking · T exit 0 with a quota message · T GC vs unpublished writers ·
T unparseable lock read as stale · T vLLM reserves a fraction of TOTAL · T budget as check-then-append
· T "not my child" read as LOST.

## 14. Reconstruction track (Owner addition, 2026-09-25)
Rule: every capability we reject as a dependency but need is rebuilt CLEAN-ROOM as the smallest CPP
primitive carrying the upstream invariant -- concepts only, no copied source, provenance per concept
in the module docstring and X1. Not reconstructed: whole platforms (a Temporal/etcd/NATS server
clone is the framework shopping this plan forbids); a scheduler (below the §10 threshold).
All R modules are pure libraries outside modules/gsd_x/goal, each with a V-* gate, red+green cases,
and a SHA-256-restored mutation drill; Lane L wires them.
R1 modules/cas/        <- REAPI + restic/Kopia: Digest{sha256,size}, canonical JSON manifest, verify
                          tiers (STRUCTURAL | CONTENT | UNKNOWN), GC-safe retention planner
                          (referenced-by-receipt UNION in-flight, age margin, two observations).
R2 modules/lease/      <- etcd lessor + Temporal range_id: flock store, monotonic fence, TTL from
                          dispatch, min-TTL refusal, expiry bumps fence atomically, all-or-nothing,
                          persisted absolute deadlines, fs-type refusal, fsync-before-ack.
R3 modules/history_check/ <- Jepsen/Elle/Porcupine: op model invoke|ok|fail|info, pure checkers
                          (single-valid-owner interval check, fence-monotone-at-store, one-job-per-token,
                          unknown-never-pass, cancel-absorbing, info-is-not-fail), verdict merge with
                          any_unknown separate, check-safe, negative control.
R4 modules/provider_routing/ <- LiteLLM router: decision record, bounded non-revisiting chain,
                          error-class retry policy default 0, cooldown by consecutive-failure count
                          (not per-minute rate), positive semantic outcome list, window-aware skip,
                          reservation lifecycle with explicit `leaked`.
R5 modules/trace_context/ <- W3C Trace Context + OTel env carriers: mint/parse/validate traceparent,
                          child-env injection, span JSONL record with gen_ai.* names, never authoritative.
R6 modules/inference_bench/ <- vLLM/SGLang bench_serving: TTFT, TPOT, ITL, E2E, throughput, goodput
                          against any OpenAI-compatible endpoint (llama-server); feeds routing priors.
X2 (TLA+) is adopted, not reconstructed. Order: R1 (S2 is live now), R2, R3, R5, R4, R6.

## 13. Done-gate
uwcp.md §26 plus: test_uwcp_tla.py (base PASS with floors; pre_cf4d71b cfg finds the late-receipt
violation; FalseLost/replace-on-unknown found against a current-code cfg; 4 mutants red; each
counterexample has a replayed Python test) · Lane L gates for A1-A8, X0, X3, X4 · test_external_failure_corpus.py
· done_gate strength-ladder class-axis tests · pause drill REMOTE_REALITY through the dispatcher ·
reachability clean or declared for every new module.
