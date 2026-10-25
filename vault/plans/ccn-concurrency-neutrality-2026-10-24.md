---
covers: [ccn, ccn-0, ccn-1, ccn-2, ccn-3, ccn-4, concurrency-neutrality]
status: AWAITING OWNER APPROVAL (2026-10-24). Nothing armed, nothing released.
mode: EXECUTION for CCN-0/1/2, PLAN-then-EXECUTION for CCN-3/4. No ULTRA-PLAN.
depends_on: vault/plans/ccr-next-master-plan-2026-10-24.md (CCR-NEXT, also awaiting approval; same lease L30)
---

# CCN: Cognitive Concurrency Neutrality. Master Plan (Reality Delta 2026-10-24)

## 0. Verdict
The brief's central premise ("running many sessions at once multiplies cognitive cost") is **mostly
falsified by measurement** on this estate. Over 7 days:
- duplicate tool work across concurrent sessions = **0.5% of calls, 0.4% of result bytes**;
- concurrent cold starts write the **same** first-call cache as isolated starts (no stampede penalty).

What the audit attributes to "concurrency" is the cost of **session count x per-session floor x context
length**. That cost is identical whether the sessions run in sequence or in parallel (Physical Limit Law).
It belongs to CCR-NEXT (floor diet, epoch controller), not to a concurrency system.
So the honest Concurrency Amplification Factor today is about **1.01**, and the 25-stage CCN programme fails
the brief's own Anti-Abstraction Gate: coordination would cost more than the duplication it removes.

What survives the measurement is 4 small stages:
- prove CAF with a matched benchmark (P <= 4);
- an advisory hot-idle census (RAM, not tokens);
- an account-level governor for laptop + GEX44 (availability, not tokens);
- a probe of first-call cache-key determinism. This is the one possible token lever: a 76K unique write per session, about 4.9% of the week.

## A. Measured reality (all commands in section F)
1. Kresume concurrency: 61 successors = 56% of the week (audit 10-24). 42 main transcripts touched <12h:
   14 active <5 min, 12 idle 5-60 min, 16 idle >60 min.
2. Goal/session model: missions (`gsd-mission-*.json`) are durable; successors are NEW conversations rehydrated
   from a capsule/card (8 KB) plus a fresh ~107K floor. Successor boot = ~112K, of which ~5K is the capsule.
   Durable-goal / disposable-session already exists for missions (Ralph v3); for `/kresume` chains it is
   capsule-based, the same shape.
3. Hot contexts: 29 `claude.exe` (28 distinct parents), 10.4 GB working set, **1.6 GB free RAM**.
4. Waiting hot: 5 processes bound to `--resume/--session-id` have transcripts idle **21-70 h**; by transcript
   activity ~15 of ~29 live sessions are idle (estimate, the process-to-transcript join only resolved 5 ids).
   Token cost of an idle process while idle = 0. Cost appears on wake: cache rebuild after >60 min idle = 5.4%.
5. Successor boot: median 112K (CCR-NEXT A13).
6. Bootstrap duplication factor: the ~34K host prefix is already shared across sessions at the provider (it
   is read, not written, on first call); ~76K is written per session. Sequential successors pay the same 76K,
   so the **concurrency-attributable** BDF is about 1.0. The per-session unique write is a determinism problem,
   not a concurrency problem.
7. Context duplication factor: same reasoning as 6. Floor duplication exists per session, not per concurrency.
8. Model-boundary duplication: no evidence of identical concurrent model questions; the only measurable signal
   is that Agent dispatch was duplicated **once** in 7 days.
9. Proof duplication: identical test/status commands across concurrent sessions: **4 calls in 7 days**.
10. Tool query duplication: 94 / 20,038 tool calls (0.5%), 1.64 of 412 MB result bytes (0.4%). 81 of the 94
    are the same reference PNGs (TTB refs) opened by several panes. `RESUMPTION_FILE.md` (TTB) was read 28x by
    14 sessions. That is a SEQUENTIAL chain re-read, not concurrent duplication.
11. Planning/research duplication: no measured instance. Prior art `derivation_store` + `hooks/research_reuse.js`
    already singleflights research by key (subscribe-deny, 30-min stale lock), and its tests are green in the repo.
12. Cache stampede: first call, start <=5 min after another session: write median 75,958 / read 33,831 (n=99);
    isolated start: write 76,831 / read 33,526 (n=191). **No stampede signature.** First-call writes total
    21.7M tokens/week.
13. Account: laptop and GEX44 are both on jacobo@costaluzlawyers.es (checked in `.claude.json` 2026-10-24).
    VPS kobicraft is on a separate account.
14. Cross-host state: missions, ledgers and goal spend are per-host; GEX44's plane lags (memory: 45 files behind).
    The coordinator settles and fetches back. There is **no live account-level admission**.
15. Semantic cache: `derivation_store` (research) is PRODUCTION. A general semantic cache: MISSING, and no
    measurement justifies one.
16. Singleflight prior art: `tools/derivation_store.py` (begin/complete/abandon, O_EXCL lock, dependency
    fingerprint by content sha, TTL, stale-lock recovery) = the canonical owner. Extend it; do not build a second one.
17. Event fabric: the mission sweep is a 5-min **poll** (scheduled task). No typed event bus was verified in this
    delta (UNVERIFIED, not missing).
18. Account governor: `mission_spend.py` goal leases + `mission_topup.py` = per-goal and per-host. There is
    no per-account weekly view.
19. Claude Mod interposition: 104 API names exist; CCR is in **shadow on 78% of starts** (compat drift 2.1.310)
    and main is shadow by design; `turn.step`/`agent.spawn` are observe-only and deny is unproven (CCR-NEXT A2-A11).
    Any CCN enforcement through the mod is therefore blocked behind CCR-NEXT A0.

## B. Architecture decisions (items 20-61)
20. Sequential benchmark contract: W = 4 read-only audit tasks on a pinned commit, each a fixed prompt, run headless
    (`claude -p`, Sonnet, same flags) one after another. Measured from their transcripts: processed tokens by
    class (fresh/read/write/output), API-eq, calls, tool calls, wall-clock, task verdict vs a fixed rubric.
21. Parallel contract: the same W at P=2 and P=4, 2 repeats each. **P=8/16 are refused**: 1.6 GB free RAM and
    the estate's BSOD-on-RAM-starvation history make them unsafe, and P<=4 settles the question.
22. CAF = cost(P) / cost(sequential) for the same W and rubric. Current estimate ~1.01 (from 10 + 12).
23. Elasticity = d ln cost / d ln P. Estimate ~0.
24. Durable goals / disposable sessions: already true for missions (v3) and capsule chains. No new primitive.
    The real gap is **when** a chain rotates (CCR-NEXT B1, >300K = 43% of kresume cost).
25. Shared semantic address space: DEFERRED. The vault + derivation_store + capsules already cover the shared objects
    that are measurably reused.
26. Canonical semantic projection: the only re-derived shared object found is RESUMPTION_FILE re-reads (sequential).
    The capsule card already is the canonical projection. No build.
27. Delta-only continuation: already used by the capsule card (HEAD, dirty paths, note). No build.
28. Minimum successor boot: owned by CCR-NEXT A4 (floor diet on successors). Not duplicated here.
29-30. Semantic COW / layered ContextImage: DEFERRED. The host materializes text per boundary, and the shared part
    (34K) is already provider-shared.
31-34. Local singleflight, key, crash recovery, invalidation: EXISTS (`derivation_store`: key = normalized question +
    scope + dependency content shas; stale-lock recovery; dependency change = key change). No new build. Extending
    it to tests is DEFERRED (4 duplicate test calls/week).
35. Proof singleflight: DEFERRED, same evidence.
36. Research/planning singleflight: EXISTS (research_reuse.js). Planning: no measured duplication.
37. Cache-warmup singleflight: REJECTED. There is no stampede (12).
38. Coalescer decision tree: adopted as **doctrine** (UKDL process rule candidate) and not as a runtime. There is no
    interposition point until CCR leaves shadow.
39-40. Microbatching / batch economics: DEFERRED. No Work Class with homogeneous concurrent items was measured.
41-43. Semantic CPU scheduler / novelty detection / backpressure: DEFERRED. A slot cap without measured novelty
    is the "lower concurrency" cheat the brief forbids, and waiting already costs ~0 tokens.
44-45. WAIT_SEMANTIC_CPU / zero-hot waiting: missions already wait cold (BLOCKED/HALTED, no process). For panes, see
    **CCN-2** (advisory census; HR-STALLED-SESSION-ADVISORY-001 forbids auto-kill).
46. Locality quantum: owned by CCR-NEXT B1/B2 (`rotate_advice` break-even).
47. Fair scheduler: DEFERRED (no scheduler).
48. Account governor: **CCN-3**.
49-51. Cross-machine cache / distributed singleflight / ROI gate: REJECTED by the ROI gate. Local duplication is
    0.4%, so cross-host duplication cannot be larger than the cross-host fraction of that.
52-53. Cache-stampede prevention / cache-key determinism: stampede is rejected; determinism = **CCN-4**.
54. Shared deterministic services: the resource monitor is already per-host (omniram-sentinel). The repo index is
    already shared (`_audit_cache`, graphify). No move.
55-56. Single writer / delta merge: missions already have one writer by construction (AMCR binding, worker fence).
    No change.
57. Semantic conflict resolver: DEFERRED.
58-59. Parent elimination / agent dedupe: DEFERRED. Subagents = 12.7% of spend, fork vs clean unmeasured (CCR-NEXT 18).
60. Intentional redundancy: preserved by default, because no dedupe is built.
61. Concurrency CI: the deterministic census (`tools/ccn_census.py`) runs weekly and fails if cross-session
    duplication exceeds 3% of calls or the concurrent-start write exceeds the isolated write by >10%. The model
    benchmark is NOT in CI (it costs tokens); it reruns only when CCR/ASER change the floor.

## C. Execution
62. Canary ladder: CCN-0 census tool -> CCN-1 benchmark P1 -> P2 -> P4 -> CCN-2 -> CCN-3 -> CCN-4 (CCN-4 runs only
    after CCR-NEXT A0, because it needs compat).
63. Modes: CCN-0/1/2 EXECUTION; CCN-3 PLAN (1 page) then EXECUTION; CCN-4 probe only. ULTRA-PLAN: none (no
    ownership conflict: K = PP Python ledgers, H = mod).
64. Micro-commits (pathspec-scoped, worktree `.claude/worktrees/ccn` from main HEAD, gate before each):
    `tool(ccn): census -- cross-session dup + first-call stampede + hot-idle`; `test(ccn): V-CCN census gates`;
    `bench(ccn): matched seq/P2/P4 harness`; `bench(ccn): results + CAF receipt`; `feat(ccn): hot-idle advisory in
    status`; `feat(ccn): account weekly ledger (laptop+GEX44)`; `feat(ccn): mission arm admission vs account
    ledger`; `probe(ccn): first-call prefix divergence`; `kb(ccn): UKDL/FIOS entries`.
65. Staged token budget (processed tokens, goal `ccr` lease L30, 55.2M remaining, shared with CCR-NEXT):

| Stage | Lower bound | Lower | P50 | P80 | P95 | Calls | Avg CWS | Hot ctx | Deterministic | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| CCN-0 census tool | 0.5M | 1.5M | 2.5M | 4M | 6M | ~30 | <120K | 1 | 95% | high |
| CCN-1 benchmark (W=4: seq, P2, P4, x2) | 4M | 6M | 9M | 13M | 18M | ~24 runs | <130K | <=4 | 10% | medium |
| CCN-2 hot-idle advisory | 0.5M | 1M | 2M | 3M | 5M | ~20 | <120K | 1 | 95% | high |
| CCN-3 account governor | 2M | 3.5M | 6M | 9M | 13M | ~60 | <150K | 1 | 85% | medium |
| CCN-4 determinism probe | 0.5M | 1M | 2M | 3.5M | 5M | ~20 | <120K | 2 | 70% | low |
| **Total** | **7.5M** | **13M** | **21.5M** | **32.5M** | **47M** | | | | | |

    Expected singleflight hits: 0 (none built). Duplicate work eliminated: ~0 (there is none to eliminate).
    Hard authority: **25M for CCN**. Above that the breaker parks. If CCR-NEXT Tranche A is also approved, the two
    together must fit L30's 55.2M: CCN first (it settles which CCR-NEXT premises hold), then Tranche A.
66. Expected token saving: CCN-0..3 ~0% (measurement, RAM and availability). CCN-4: if the 76K first write can be
    made prefix-stable across sessions in one cwd, up to ~4% of the week; P50 ~1%, low confidence, and it depends
    on host prompt composition we may not control.
67. Wall-clock: no change by design. CCN-1 reports it per P.
68. Payback: the benchmark has no payback; it prevents spending ~200M+ on a 25-stage build for a ~1% problem.
    CCN-4 at P50 1% of ~6.5B/week = ~65M/week vs 2M -> payback < 1 week if realized.
69. Owner authority: Q1-Q3 below. No new capital.
70. Hashes: PP HEAD `7ea946df` (branch feature/knowledge-acquisition, dirty files belong to other panes, untouched);
    CCR-NEXT plan sha256 printed with the approval; this plan sha256 printed with the approval; lease L30 remaining
    55,182,168 (as of CCR-NEXT delta, not re-read).
71. Approval surface: chat.
72. Returns to Owner: >25M spend; the benchmark shows CAF > 1.10 (the premise was right, so re-plan the deferred
    stages with real data); the account-governor threshold; any kill/release of a live pane; any hook or settings
    registration (HR-001); irreversible acts.

## D. Owner questions
- Q1: Approve CCN-0..CCN-3 (+ CCN-4 after CCR-NEXT A0) within hard authority 25M of lease L30?
- Q2: Account-governor policy: (advisory) a status line plus a refusal message, or (enforce) `gsd_mission.py arm` and
  auto-topup refuse above X% of the weekly estimate unless the Owner overrides? Which X (suggested 85%)?
- Q3: Start after the weekly reset (~02:00 25/10) or now?

## E. Deferred / rejected (named, so the set can only shrink)
Rejected by the ROI gate: cache-warmup singleflight, distributed singleflight, cross-machine semantic cache.
Deferred until a measurement justifies them: semantic CPU scheduler, microbatching, COW, layered ContextImage,
proof singleflight, parent relay elimination, agent COW, semantic conflict resolver, fair scheduler.

## F. Evidence commands (2026-10-24)
- dup: `python -I <scratch>/dup.py 168` -> sessions_with_tools=220 tool_events=20038, dup calls=94 (0.5%), bytes 1,644,533/412,184,468 (0.4%).
- stampede: `python -I <scratch>/stampede.py` -> concurrent n=99 write med 75,958 read 33,831; isolated n=191 write 76,831 read 33,526; first-call writes 21,736,561.
- processes: `Get-CimInstance Win32_Process -Filter "Name='claude.exe'"` -> 29 procs, 10,416 MB WS, 1,598 MB free.
- missions: state census of `gsd-mission-*.json` -> RUNNING 16, BLOCKED 6, PREPARED 7, ORPHANED 7, HALTED 392, COMPLETED 146 (liveness not verified).
Scratch: C:\Users\User\AppData\Local\Temp\claude\C--Users-User--claude-skills-claude-power-pack\f315f5d3-0c40-4638-9bfa-620cbd3d449b\scratchpad\ (CCN-0 promotes both scripts to tools/ccn_census.py).
