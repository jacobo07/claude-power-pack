---
status: APPROVED 2026-09-25 by Owner ("y": plan + dedicated `uwcp` VPS user) -- Owner answered Q1-Q6 on 2026-09-25
opened: 2026-09-24
branch: feature/knowledge-acquisition
covers: [uwcp, workstream, workstream-continuity, remote-execution, gex44, authority-home, lease, workspace-capsule, baseline-fingerprint, model-routing, cpp-gsd-long-remote, placement-rule, broker-law]
extends: [mission-continuity.md, gsd_x goal spine (KSEIP kseip-goal-spine-v1)]
audit: oneshot-architect-auditor 2026-09-25, 22 gaps + 5 advisories, disposition in §P4
---

# Universal Workstream Continuity Plane (UWCP) -- final plan (Phase 5)

This file is the durable backup of the inline approval plan. The inline text in chat and this
file carry the same content; if they ever diverge, this file is re-synced from the approved chat text.

## 1. Mode
Phases 2-5: ULTRA (authority home, broker law, lease authority, three-track ownership, security of a
shared production VPS). After approval every slice runs in EXECUTION. Two slices carry PLAN checkpoints
because they touch live infrastructure owned by other tracks: S5a (dispatcher under VCS + patch = a
live-server deploy, HR router trigger 2) and S4c (KSR lease cutover). Nothing is re-ULTRA'd unless a
new authority question appears.

## 2. Delta since Phase 1 (W0, read-only, via Windows->VPS, the sanctioned route)
D1 goal/mission code unchanged since 850eda3.
D2 live dispatcher sha256 34c33763 (1814 lines) = recorded; edited in place with .bak_* files; the only
   source copy (KobiiCraft vps-bootstrap) is April-stale -> the broker for all GEX44 access has NO VCS.
D3 staging/install primitive exists (JOB_DEFAULT_STAGE, _stage_assets md5 handshake, JOB_DEFAULT_COLLECT,
   install-type jobs). D4 start proof exists (job_started flag + honest status taxonomy).
D5 ksr-keos-wave ends ack_but_no_verdict BY CONSTRUCTION (writes receipt.txt; dispatcher reads only
   verdict.json/failed.flag). No per-job wall clock; only job budget + MAX_UPTIME_HRS.
D6 dispatcher heartbeat-miss + hetzner->runpod failover exist.
D7 VPS: py3.12, claude 2.1.81, node, git; no gsd-core; disk 77 %; RAM 7.7 GB (~3.6 avail); a NON-git
   CPP tree; dispatcher invocation path unknown; GitHub Actions runner + Hermes KEOS board + ~10 services
   all as user kobicraft.
D8 second KEOS on the VPS (Hermes gateway, kanban claims, 6-hourly deterministic heartbeat) -- ownership
   vs UWCP unclassified.
D9 GEX44: disk 93 %, ~3.5 GB free VRAM, Qwen3-Coder-30B-A3B loopback :8081 ctx 32768, claude 2.1.113 headless.
D10 routing owners exist (cost_collapse router, model-routing.json, keos_qwen outcome vocabulary, codex.py
   shared-account budget, claude.py 4/day ledger, KSR on-node ladder).
D11 loop owner exists: reconciler info key + closed hypothesis vocabulary = persist-on-goal/pivot-on-method.
D12 direct GEX44 lanes: L1 keos_qwen ssh/-L + /tmp writes; L2 goal suites run on GEX44 (route unrecorded);
   L3 09-20 reachability `ssh gex44`; L4 KSR ksr_deploy.sh; L5 CPP deployment skill vault/deploy/kobiicraft.json
   (scp-systemd via alias gex44, key kobicraft_gex44). ~/.ssh/config defines aliases gex44 and gex44-root.

Iteration protocol (iteracion-avanzada-universal) applied to Phase 1 premises -- REALITY CHECK:
- CLASE 2 (false repo state): "sweep refuses spending without authority record" -> FALSE, it refuses all
  spending (sweep.py:253-257). "brief bounded" -> PARTIAL (list caps only). "the VPS CPP tree is a runtime"
  -> FALSE (non-git, unknown version). "12 goal suites" -> 14. `gsd_x_goal.py certify` -> does not exist.
- CLASE 1 (API assumed): repo_identity has no portable id; log.repo_id is the only one (log.py:79-91).
- Each fix below lands at the core owner, not the surface; each non-trivial fix seeds UKDL (§23).

## 3. Owner decisions integrated
Q1 broker law global -> §8 guard (destination-position patterns, nested hops, static sweep) + retire L1-L5
   after replacements are proven. Q2 -> REUSE JOB_DEFAULT_STAGE; add uwcp-install / uwcp-epoch / uwcp-probe.
Q3 VPS authority home -> §5/§6, with a dedicated unix user (see §28). Q4 -> one VPS lease+consume store;
   KSR slot_ledger becomes a client. Q5 -> §7 capability-aware routing, ONE account ledger for claude -p on
   the VPS (4/day total, all spenders reserve from it). Q6 -> additive extension of gsd_x/goal; canary first;
   FP-028 for S1-S3 only; foreign dirty paths excluded + reported.
Owner mid-turn request (2026-09-25): "run /cpp-gsd-long on GEX44 if the host can't or shouldn't" ->
   §12b placement rule, landed in S6c with the certified remote path (not before: a rule that routes to an
   unproven path would be a documented capability nobody can execute).

## 4. Final ownership map
| responsibility | owner | action |
|---|---|---|
| Workstream identity | goal/log.py | REUSE; + dir fsync (POSIX) |
| portable repo id | log.repo_id (root commit) | MERGE: repo_identity.portable_repo_id() delegates to one impl; + origin-URL collision check; refuse shallow/multi-root |
| mission / revision / budget / authority | goal/contract.py | REUSE; + mandatory max_epochs/max_hours for remote homes |
| execution / epoch | goal/epoch.py | EXTEND: node, provider, fence generation, authority_home, baseline_fp, capsule_ref; ingest refuses stale fence / ended epoch |
| hash/pin identity | git_state + epoch.scope_hash | EXTEND: git blob ids of tracked in-scope files (eol-invariant) |
| negative knowledge | none | EXTEND: evidence.hypothesis event |
| resume capsule | goal/brief.py | EXTEND: hypotheses + node/provider + byte AND token bound (refuse, never truncate); gsd_mission card rendered from it (MERGE) |
| workspace capsule | none | NEW goal/workspace.py |
| baseline fingerprint | none (tower/capsule is applicability) | NEW goal/baseline.py; tower/capsule.py untouched |
| node manifest | KSR capabilities.json | EXTEND via goal/node.py adapter (measured_at, known heads, max age) |
| placement | none | NEW pure function goal/placement.py |
| provider routing | reconcile._work_provider + cost_collapse + codex.py budget | MERGE: goal/route.py REPLACES _work_provider, consumes reconcile's gate-first step |
| provider budgets | claude.py / codex.py per-host ledgers | MIGRATE: one VPS account ledger (flock), hosts reserve from it |
| lease + slot consume | KSR slot_ledger (Windows) | MIGRATE to VPS store; KSR = client; AUTHORIZED/CONSUMED projected from VPS |
| broker | VPS gex44_dispatcher | REUSE + bring under VCS + uwcp job types + lease gate + failover:never for uwcp-* |
| executor adapter | provider protocol | NEW goal/providers/queue.py (run_token = dispatcher job id, idempotent add) |
| on-node runner | none | NEW uwcp-epoch runner (CPP-owned), writes verdict.json/failed.flag + fence echo |
| installer | install-type jobs | REUSE pattern: uwcp-install (atomic, hashed, N-1 rollback, free-space precondition, hook drills) |
| remote relay | gsd_mission (local) | CONNECT: reconciler owns remote chain; shared note-parse + GSD completion probe extracted; mission records name goal id; supervise refuses home != self |
| supervisor | goal sweep | EXTEND: authority record permits spending (per-provider budget); VPS cron+flock; heartbeat of each run (missed != quiet) |
| operator events | goal log | EXTEND operator.* |
| judge | goal/judge.py | REUSE as queue gate epoch on node against final capsule |
| control contract | gsd_x_goal.py | EXTEND: uwcp.control/1 JSON verbs via ssh forced command; `certify` verb added in the commit that names it |
| broker-law guard | cascade_prevention/dangerous_cmds + cascade_check_bash.js | EXTEND with own pattern class + static sweep (AST + .sh) |
| VPS KEOS board | /home/kobicraft/keos | CLASSIFY in S4 (read-only); no UWCP dependency; its codex spend joins the account ledger |
| loop | reconciler info key + /ultra 4-5 | REUSE; failure signature = normalized gate stderr hash; forced provider_change after 2 on (obligation, provider) |
| writeback | UKDL, vault, convergence learning plane | REUSE |

## 5. Authority model
Workstream / mission / epochs / hypotheses / receipts / operator events: goal log at the authority home,
owned by unix user `uwcp` (0700), writable only through its forced-command verbs. Capsule store: beside the
log, same user, content-addressed, retention-bounded. Lease + consume + provider account ledgers: `uwcp`-owned
store on the VPS, flock-serialized, exclusive create, monotonic fence generation. Placement + routing: pure
functions evaluated by the reconciler. Queue + transport to GEX44: dispatcher only. Execution: uwcp-epoch
runner. Judgement: independent gate epoch. Writeback: reviewed commits. Control surfaces: read + operator
events only.

## 6. Architecture
CONTROL SURFACE --ssh uwcp@vps forced-command uwcp.control/1--> AUTHORITY HOME (VPS, user uwcp: goal log,
capsules, lease+ledgers, reconciler/sweep via cron+flock, heartbeat per run) --gex44_cli queue add
(job_id = run_token, lease token)--> DISPATCHER (lease re-check at dispatch, stage capsule+runtime, ack,
job-peek, collect; uwcp-* never fail over) --> GEX44 EPOCH (host-identity assert, free-space check, fence
re-check, hydrate+verify, baseline verify, routed provider, progress file, commit, HANDOFF NOTE, capsule',
receipt, verdict.json|failed.flag) --> COLLECT --> harvest (fence + ended-epoch refusal) --> next epoch |
READY_FOR_JUDGE -> judge gate epoch -> CONVERGED -> artifacts pulled by any control surface.

## 7. Routing
Decided at the home per epoch, recorded in epoch.dispatching (provider identity per epoch = provenance):
gate-first (reconcile's own step) -> claude-harness@qwen-local -> codex@qwen-local -> codex frontier ->
claude -p frontier. Inputs: obligation class, measured harness prompt tokens vs 32k, brief tokens,
priors from the benchmark, per-(obligation,provider) failure signatures, provider availability with
measured_at (stale = unknown = not selected), budgets. Outcomes use keos_qwen vocabulary + AUTH_FAILED
(non-retryable, alerting) + harness context errors mapped to TRUNCATED. claude -p: one account ledger on
the VPS, 4/day ceiling, every spender (UWCP epochs, local goal engine, KSR wave frontier rungs) reserves
atomically; the goal's authority record carries its own sub-budget. Local-model epochs never touch it.
Escalation: 2 same-signature failures on (obligation, provider) -> provider_change forced.
Benchmark (S6a): 7 frozen tasks (repo understanding, bounded implementation, constraint adherence, test
repair, rejected-hypothesis preservation, resume from brief, one causal task); Qwen on all 7, claude -p on
<=3; metrics: gate pass, repair rate, constraint violations, hallucinated state (claims vs git), tokens,
latency, escalation; persisted as vault/datasets/uwcp/routing_priors.jsonl; tasks held out from prompt tuning.

## 8. Legal deploy + broker law
S5a: commit the live dispatcher bytes into KobiiCraft vps-bootstrap (VCS), then patch by reviewed diff;
deploy = scp to a temp name on the VPS, sha256 verify, atomic mv, .bak kept; DEPLOY hard rules read first
(HR router trigger 2). uwcp-install stages a runtime bundle (CPP runtime manifest + runner + Linux executor
settings/hooks + pinned node user/path), refuses below a free-space floor, verifies sha256, flips `current`
atomically, keeps N-1, runs red-branch drills proving each critical hook fires on the node, receipt via
collect; same sha = reported no-op. Guard: dedicated broker-law pattern class (destination position incl.
-J/ProxyJump and nested ssh; aliases gex44, gex44-root, IP), negative control `gex44_cli.py queue add` must
pass, own reason text, no phrase exception (the Owner's own terminal is the exception); plus a static AST +
.sh sweep over CPP/KSR code as the second instrument. Lanes L1-L5 migrate to uwcp-probe / queue gate epochs /
staging and are retired only after each replacement runs.

## 9. Lease migration
Lease = multi-job semantic reservation of a resource class (dolphin_slot, gpu_vram, ksr_workspace);
queue = per-job serialization. Store on VPS: acquire/renew/release/consume, holder-only, TTL counted from
DISPATCH (queued jobs hold a reservation, not a clock), dispatcher renews while queued/running, fence
generation staged with the job, runner verifies it before each side effect; statuses lease_expired_in_queue
and lease_fenced distinct from failed. queue add requires a token for exclusive classes; dispatcher re-checks
at dispatch. KSR slot_ledger acquire/release/consume keep signatures, call the VPS; AUTHORIZED/CONSUMED
authoritative on the VPS, the Windows ledger becomes a projection; a live local lease at cutover is imported
once; VPS unreachable -> BLOCKED. Golden 13 enumerates every enqueue path structurally.

## 10. Workspace capsule
Manifest: portable repo id + origin URL, base commit/tree, branch, eol config, submodule gitlinks + object
availability, lockfile hashes, per-file git blob ids of tracked in-scope files, capsule sha256, provenance,
ownership table. Parts: git bundle (incremental against node-known heads from the manifest; `git bundle
verify`; fallback full), staged + unstaged binary diffs, allowlisted untracked tar; per-part size cap.
Exclusions: structural (.env*, *.pem, *.key, id_rsa*, secret dirs), secret detector + independent entropy
check -> capture REFUSED on hit. FOREIGN = dirty paths outside declared scope or dirty before the goal and
never touched by its epochs -> excluded + reported. Verify: EQUIVALENT | COMPATIBLE_WITH_DECLARED_DRIFT |
NON_EQUIVALENT | UNKNOWN; missing submodule objects -> NON_EQUIVALENT; UNKNOWN never promoted. Retention:
keep last N receipted capsules per goal; node stage dirs deleted on harvest by the dispatcher job itself.

## 11. Baseline / drift (goal/baseline.py)
Fields, classed: correctness = runtime-manifest content hash, executor hook-set hash, claude CLI version,
model id + GGUF sha + llama.cpp build, HR digest hash, permission mode; compatible = applicable tower
generation ids; irrelevant = everything else. Correctness drift -> refuse unless an operator/policy re-pin
event; compatible -> proceed, recorded; never invisible (status shows pin vs observed).

## 12. Distributed /cpp-gsd-long
Remote goal = chain of bounded epochs (job budget default 45 min, plus the provider's context wall via the
staged mission_wall hook). Epoch prompt = brief + "continue the GSD roadmap; at wall or budget: commit,
HANDOFF NOTE". GSD completion is probed as a gate epoch on the node (gsd-core installed by uwcp-install).
Local v3 Ralph unchanged. Start proof: DISPATCHING -> LAUNCHING (queue accepted) -> RUNNING only on the ack
flag AND a first progress-file record read via job-peek within a deadline; otherwise LOST(not_started).
12b Placement rule (Owner request): /cpp-gsd-long places on GEX44 when any holds -- host free RAM under the
estate floor at arm time; the host is a sleep/power-down client (laptop) and the mission budget exceeds one
session; a required capability exists only on the node; explicit --node gex44. Stays LOCAL with a stated
reason when the remote path is not certified, the lease or node is unavailable, or the mission is local-only
by applicability. Lands in S6c: placement.py + command doc + UKDL process rule, with tests of every branch.

## 13. Client independence
After declare + authority_set the client is optional. Proof: VPS sshd journal shows zero sessions from the
client across >=1 relay; local PP sweep disabled for the window; epoch events written by the home's host id.
Reattach: `status/attach` from a second control surface (Owner-assisted one command from another device; the
VPS-local surface is labelled as such, not as "another device").

## 14. Failure matrix (expected state per injection)
kill between intent and enqueue -> probe by run_token (queue, history, collect dir) -> adopt | LOST, never
duplicate; stale/late receipt -> refused, finding logged; stall -> abort -> LOST(stall); worker kill ->
receipt LOST_WORKER from committed state, uncheckpointed work reported lost; job kill -> LOST, next epoch from
last receipted capsule; lease expired in queue -> lease_expired_in_queue, re-acquire; lease bypass -> refused at
add and at dispatch; home crash -> log intact (link+fsync+dir fsync), cron resumes, missed run visible;
supervisor overlap -> flock; node unreachable -> UNKNOWN -> never replace, BLOCKED_ENVIRONMENT after bound;
failover triggered -> uwcp-* stay queued (failover:never); disk floor -> install/epoch refuse; auth stale ->
AUTH_FAILED, routed away, alert; Qwen down -> UNAVAILABLE, routed away; invalid patch -> gate fail signature,
escalate after 2; quota exhausted -> provider unavailable; baseline drift -> refuse; capsule corrupt/truncated ->
verify NON_EQUIVALENT; foreign/secret file -> excluded/refused + reported; CRLF drift -> blob-id identity holds;
missing branch -> full bundle; operator pause/cancel race -> CAS, cancel dominates; done race -> judge at final
capsule only; writeback failure -> learning plane CANDIDATE, blocks CONVERGED.

## 15. Security
Dedicated `uwcp` user (0700) with ssh forced-command verbs: closes same-user forgery by the GitHub runner,
Hermes tool calls and other kobicraft services (HMAC re-evaluated after, not adopted now). No secrets in
capsules or briefs; credentials node-local, refresh owner per host documented; AUTH_FAILED distinct. Runner
asserts host identity; uwcp-* never fail over to RunPod. Brief is data from the home's log only. Broker-law
guard + static sweep. Artifacts sha256 at both ends. Policy/permission pinned per epoch in the authority
record; the node cannot widen it (Golden 10).

## 16. Observability
One `status` view (uwcp.control/1): goal, epoch, node, home, state, PROCESS_ALIVE and PROGRESSING as separate
fields with ages, mission revision, provider + budget per provider, lease holder/TTL/fence, capsule verdict,
baseline pin vs observed, last receipt + age, continuation/recovery/migration counts, supervisor last-run
heartbeat, done-gate state, blocker. Every field has a producer; absent = UNKNOWN, rendered as such.

## 17-18. Slices and micro-commits (~46, three repos; HEAD re-read + pathspec + staged-diff check before each)
S0 (CPP): 1 spec+plan backup · 2 characterization tests (red today: no fence, home-less sweep, eol pins,
   unbounded brief, non-git autonomy pass, long_run can't start).
S1 foundation (CPP, KSEIP-additive): 3 portable_repo_id merge + collision/shallow refusal · 4 dir fsync ·
   5 evidence.hypothesis · 6 brief hypotheses + byte/token bound · 7 operator.* · 8 fence generation +
   ingest refusal · 9 blob-id pins/scope hash · 10 non-git autonomy refusal (engine = runtime sha) ·
   11 LongRunProvider v3 + card-from-brief · 12 local Golden 02+08 (LOCAL_REALITY, FP-028 read-only goal).
S2 workspace (CPP): 13 capture · 14 exclusions + secret/entropy refusal · 15 foreign-path ownership ·
   16 hydrate · 17 verify (4 outcomes) · 18 Golden 04 local (two worktrees, autocrlf both ways, submodule, missing branch).
S3 baseline (CPP): 19 goal/baseline.py · 20 epoch pin + drift policy · 21 Golden 05 local.
S4 node/placement/lease: 22 node adapter + freshness (CPP) · 23 placement.py (CPP) · 24 VPS KEOS board
   classification note (read-only) · 25 VPS store: lease+consume+account ledgers (CPP code, deployed as
   runtime) · 26 lease fencing tests (two enqueuers, stale, expired-in-queue, worker death, delayed receipt,
   cancel) · 27 KSR slot_ledger client adapter (KSR repo) · 28 KSR cutover import + Golden 06 synthetic.
S5 broker (KobiiCraft repo + CPP): 29 dispatcher live bytes into VCS · 30 uwcp-probe/install/epoch entries +
   lease gate + failover:never + job-peek + idempotent add (reviewed diff) · 31 deploy (temp+sha+mv) ·
   32 runtime bundle builder + uwcp-install (CPP) · 33 runner (verdict.json, fence, host assert, disk floor) ·
   34 providers/queue.py · 35 dedicated uwcp user + forced-command verbs (after §28) · 36 Golden 09 +
   kill-between-intent-and-enqueue (REMOTE_REALITY).
S6 routing + remote run: 37 route.py replaces _work_provider + outcome mapping (AUTH_FAILED, TRUNCATED) ·
   38 account ledger migration (claude.py, codex.py, KSR wave rungs reserve) · 39 benchmark run + priors ·
   40 sweep authority-record spending + VPS cron/flock + run heartbeat · 41 canary Golden 01 part A
   (>=2 relays, Golden 07, 11, 12) · 42 placement rule landed in /cpp-gsd-long (12b).
S7-S8: 43 client independence Golden 03 + session kill Golden 02 remote + Golden 10.
S9: 44 uwcp.control/1 contract doc + contract test (new verbs = new method names; old peers fail closed).
S10: 45 broker-law guard + static sweep + L1-L5 retirement (each after its replacement ran) + Golden 13 ·
   46 certification record, UKDL (HR/PR/T), vault lessons, ratchet candidate, meta-analysis, RESUMPTION, handoff.

## 19-20. Tests, goldens, chaos, reality gates
Every slice: V-UWCP-* unit gates with driven red branches (mutation drills, SHA-256 restores), regression of
touched suites (discovered by glob), evidence class stated: SIMULATED | LOCAL_REALITY | REMOTE_REALITY |
PRODUCTION_REALITY | HARDWARE_REALITY. Goldens 01-13 as specified by the Owner; 04/05/06/08/09 first local
or synthetic then remote; 01/02/03/07/10/11/12/13 remote only. Chaos: every §14 injection asserts the
classified state, never merely an exception. Level target: 4 (host-portable) proven on GEX44; Level 5 is
NOT claimed in this program (RunPod excluded by design, no second eligible node).

## 21-22. Migration / rollback
Opt-in flags (--goal, --node); local v3 unchanged; legacy v2 behind "legacy compact". Remote cutover by
relocation: the laptop log is tombstoned with a format marker old readers refuse. Rollback: pathspec reverts;
dispatcher .bak restore by sha; uwcp-install N-1 `current` flip; cron line removal; lease store falls back to
BLOCKED (never to the Windows file); goal logs append-only, remote goals end via operator cancel.

## 23-25. UKDL, vault, ratchet, meta-analysis
Candidates, each promoted only with its evidence: HR broker-law transport; HR a bounded lock-holding job
must not host an unbounded mission; HR a lease that does not gate the effective enqueuer is not a lease;
PR one home + fenced epochs instead of consensus; PR identity by git blob ids across hosts; T path-derived
repo keys are host-local; T non-git runtime silently disables staleness checks; T receipt-writing jobs read
as ack_but_no_verdict; T a broker with no VCS; T ARMED != RUNNING; T PROCESS_ALIVE != PROGRESSING. Vault
lessons carry the causal evidence. Ratchet: capability contract `workstream_durability` proposed after
Golden 01 is REMOTE_REALITY, applicability = multi-context or remote missions only. Meta-analysis at close
per the Owner's list; CLAUDE.md size: noted, not in scope (evidence: remote executors run with a compiled
executor config, a working example of applicability-compiled doctrine for a later pass).

## 26. Done-gate (live repo)
python tools/test_uwcp_*.py (all) · every tools/test_gsd_x_goal*.py (14) · tools/test_gsd_mission.py ·
tools/test_gsd_mission_freshness.py · tools/test_mission_watchdog.py · node tools/test_hub_mission_start.js
· tools/test_gsd_long_run.py · tools/test_gsd_autocompact.py · tools/test_cpp_gsd_long_routing.py ·
tools/test_keos_qwen_outcome.py · python modules/liveness/reachability.py · tools/gsd_x_goal.py certify
--goal <canary> (added in commit 46) scoring the VPS log + collect receipts + dispatcher history + git +
judge PASS; each Owner-listed Done item mapped to one named observable; any simulated leg labelled.

## 27. Handoff contract
Owner's 16 fields at every handoff, plus RESUMPTION_FILE updated after each sealed slice.

## 28. Owner decisions still required
One: approve creating a dedicated unix user `uwcp` on the production VPS (sudo, privileged change on a host
running ~10 production services) to hold the authority home, lease and account ledgers.

## P4. Audit disposition (22 gaps + 5 advisories)
ACCEPTED: 1,2,3,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,22; advisories D7-atomic-deploy, job-peek vs
audit.lock (verified in S5 before §N depends on it), availability freshness, repo_id shallow/fork, dir fsync.
PARTIALLY ACCEPTED: 4 (dedicated user + forced command adopted; HMAC deferred until perms are proven
insufficient; needs §28), 21 (pattern class + static sweep adopted; Owner-phrase exception dropped rather
than implemented). REJECTED: none.
