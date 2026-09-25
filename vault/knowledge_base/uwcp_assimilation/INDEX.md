# UWCP External Architecture Assimilation -- index

Research done 2026-09-25 for the Universal Workstream Continuity Plane. Plan:
`vault/specs/uwcp-assimilation.md`. Amendments delivered to the UWCP pane:
`vault/specs/uwcp.AMENDMENTS.md`. Raw evidence: `research/` (every upstream claim carries repo, path,
SHA or tag, date). Confidence per claim: VERIFIED (raw file read), OBSERVED (fetch-tool summary),
RECALLED (prior knowledge, not re-fetched) -- the research files mark each.

UKDL from this program (3 hard rules, 8 process rules, 12 traps): `UKDL.md`. Failure corpus:
`vault/datasets/uwcp/external_failure_corpus.jsonl` (gate `tools/test_external_failure_corpus.py`).
Mutation drill specs per module: `mutations/` (runner `tools/lane_r_mutate.py`).

Reports: `A1_temporal_etcd.md` · `A2_tla_jepsen.md` · `B1_cas_workspace.md` ·
`B2_routing_obs_thresholds.md` · `L0_local_reality.md` (our own code) · `S_synthesis_core.md`.
Phase-4 audit (oneshot-architect-auditor, REVISE, 21 gaps, all accepted) is summarised in §P4 below.

## Upstream revisions read
| project | revision | license |
|---|---|---|
| temporalio/temporal | v1.32.0 d94e34a1 (2026-09-11) | MIT |
| etcd-io/etcd | v3.7.2 68c065e5 (2026-09-22) | Apache-2.0 |
| tlaplus/tlaplus | master 5d53605 (2026-09-25); stable v1.7.4 (2024-08-05) | MIT |
| jepsen-io/jepsen | main 9ea74ea (2026-09-22) | EPL (RECALLED) |
| bazelbuild/remote-apis | main adbf4a2 (2026-09-22), v2.12.0 | Apache-2.0 |
| restic/restic | v0.19.1 (2026-07-05) | BSD-2-Clause |
| kopia/kopia | v0.23.1, master 1d4d45a (2026-09-25) | Apache-2.0 |
| dagger/dagger | v0.21.9 (2026-08-26) | Apache-2.0 |
| BerriAI/litellm | v1.102.1, main c19ce71 | MIT + enterprise/ |
| vllm-project/vllm | main 25b0add | Apache-2.0 (RECALLED) |
| sgl-project/sglang | main 2f5c9ac | Apache-2.0 (RECALLED) |
| OpenHands software-agent-sdk | main (2026-09-25) | MIT |
| hashicorp/nomad | - | BUSL-1.1 (RECALLED) |
| daytonaio/daytona | HEAD, no LICENSE file | none |

## Questions this record answers
**What did Temporal teach us about long execution histories?** Bound every run and roll over
voluntarily: suggest 4 MiB / 4k events, warn 10 MiB, error 50 MiB / 51,200 (dynamicconfig). A
completion echoes the full attempt identity (task token: run, scheduled event, attempt, version)
and a superseded attempt is dropped. Ownership is fenced by range_id INSIDE the write transaction,
and a deposed owner stops itself. -> A1, A3, A4.

**What did etcd teach us about stale leases?** A lock is a liveness hint; only a fence the resource
checks gives safety (Jepsen etcd 3.4.3: two holders, ~18 % acked updates lost; #11456 lock returned
without re-checking the lease). A clock restarted when its owner changes makes leases immortal
(#9888; #21372 swallowed checkpoint errors). Revoke deletes guarded state atomically. -> A3, A5, R2.

**Why did we reject adopting Temporal directly?** UWCP needs ONE authority home, CLI-harness
executors (`claude -p`, codex, Qwen harness) and runs on a VPS with ~3.6 GB free RAM; Temporal is a
server + database + worker fleet whose value is multi-home replication we do not need, and its update
dedup is per run (lost across Continue-As-New) where UWCP needs goal-scoped dedup. Revisit: >=2
replicated homes, >100 concurrent workstreams, or code-defined workflows replacing CLI harnesses.

**Why not etcd?** One home + flock CAS on a local ext4 file gives the lease semantics we need; etcd
adds a consensus cluster for a problem we do not have. Its invariants are reconstructed in R2.

**What invariants does UWCP formally guarantee?** Planned in X2 (`vault/specs/tla/UWCP.tla`): 12 safety
(at most one valid owner, stale fence cannot advance, cancelled never resumes, receipt only for open
epoch, expired lease no new dispatch, one job per run_token, UNKNOWN never PASS, no replacement on
UNKNOWN, ended terminal, fence monotonic, converged only from pass, type) + 2 liveness. Status: see
the gate `tools/test_uwcp_tla.py` once landed; until then THEORETICAL.

**Which Jepsen-style histories have we tested?** R3 `modules/history_check/` + the goal-log adapter;
see its gate. None on real remote histories yet.

**What REAPI ideas does the Workspace Capsule use?** Digest {sha256,size}, canonical sorted manifest,
referenced parts must exist, ask the node what it is missing at dispatch. Not used: action cache,
CDC, keyed ids.

**When would NATS become justified?** >=2 dispatcher hosts on one queue, or flock waits >0/day with
p99 enqueue >1 s, or delivery required while the queue host is down.

**When would Nomad (or Ray) become justified?** >=4 nodes or >=3 resource classes with >1 feasible
node, or double-placement refusals >0/week, or multi-host gang reservations. Nomad is BUSL-1.1:
concepts only regardless.

**Which local provider beats Claude for which task class?** Not measured yet -- owed by UWCP S6a
(7 frozen tasks, `vault/datasets/uwcp/routing_priors.jsonl`) using R6 metrics. Serving stays llama.cpp
on GEX44 (vLLM/SGLang reserve a fraction of TOTAL VRAM against FREE on a shared 20 GB card).

**Which external bugs already have CPP regressions?** `vault/datasets/uwcp/external_failure_corpus.jsonl`
(X5) -- each entry carries `regression` (test id) or `OWED` with the slice that closes it.

**Which concepts became Certified Primitives / stayed research-only?** Candidates: plan §11.
Research-only: Dagger, Bazel, OpenHands, Daytona (rejected), trace validation (deferred, X9).

## Measured here (not only read)
- `git bundle verify` passed a bundle with one flipped byte mid-pack ("is okay", exit 0); `git fetch`
  with transfer.fsckObjects rejected it (inflate error, exit 1). LOCAL_REALITY, 2026-09-25, git on this
  Windows host. -> A6 item 4.

## §P4 audit (summary)
Critical: stale baseline (S1-6..S1-9 had landed; cf4d71b already refuses late/mis-fenced receipts);
the observe path turns "no child handle in this process" into LOST (claude.py, codex.py), the
dominant form of UNKNOWN-read-as-LOST; A3 as drafted was check-then-act. High: UNKNOWN wait starved
operator cancel; model Bound semantics contradicted A2; the "current code" counterexample prediction
was stale; X6/X4/X3 duplicated done_gate/strength_ladder, the gsd_x chaos suite and belonged near
gsd_x/goal; X0 os.replace not single-winner; no delivery path to the live pane; five probe
implementers, not four; queue-wait expiry left the lease immortal; two content identities.
All accepted; plan r2.
