---
status: PROPOSED 2026-11-05 (awaiting Owner phrase "y go ICC"); the inline chat copy is authoritative, this file is recovery support
covers: [icc, state-centric, gpf, ccr, capability-virtualization, deferred-tools, floor-attribution, zero-model, context-policy-regret, model-call-accounting]
continues: vault/programs/global-prefix-floor/RESUMPTION_FILE.md (GPF items 1-7 DONE), vault/programs/cognitive-economy/ (CLOSED 2026-10-03)
novelty: no new system. Every wave extends an existing owner (HR-NOVELTY-001 not triggered: nothing new is admitted).
---

# ICC -- state-centric cognitive runtime, continuation of GPF / Cognitive Economy / CCR

## Reality scan (2026-11-05, measured unless marked)
- HEAD 037b9316, branch feature/knowledge-acquisition, 1,270 foreign dirty paths, nothing pushed, CCR 0.1.0-b4aede4f, host 2.1.318.
- Floor (floor_regression_gate --check --session bcf0a0bc): call-1 71,883 tokens (API usage), 182,303 chars recorded in
  the transcript. Largest recorded layers (chars): deferred_tools_delta 45,603; skill_listing 29,988; agent_listing 27,068;
  memory_project 28,817 (repo CLAUDE.md 22,861, blocked by a foreign uncommitted edit); mcp_instructions 8,975;
  SessionStart hook 8,229; system_prompt 7,937; rules 8,239; memory_global 7,871. Tool schemas are not in the chars rows.
- Deferred tool names by server (first delta, names only, 20,281 chars): vercel 241 names / 8,237; rea 207 / 6,355;
  github 41 / 1,222; artifacts 32 / 1,144; Gmail 30 / 1,108; gex44-browser 25 / 956 (server failed to connect); rest < 500 each.
- OPEN TRUTH DEFECT (A1): the transcript records skill/agent listings WITH descriptions, while CCR's names-only canary
  rewrites what the model sees. The chars rows are the recorded plane, not the request plane. Per-layer tokens are
  therefore UNMEASURED; only the 71,883 total is request-plane truth.
- Owners (subagent scan, read-only): Cognitive Economy CLOSED 2026-10-03 with proof reuse FALSIFIED (0.50% of spend),
  reread 1.88%, tool-output admission falsified. TOK-18 = backlog id (cep_gen2, mission_spend, wu3_packets), not a compiler.
  ContextImage = mission_recovery.render_packet (markdown, not typed). CCR = policy.ts + register.ts (canary names-only for
  skills/agents/mcp_instructions; projection; page tool; frontier). capability_runtime = applicability live, invocation
  unwired, retirement propose-only. agent_bundle (proof-bundle-v1) BUILT, wiring UNVERIFIED. cognitive_admission is token-
  based; no per-obligation model-call receipt exists. Waiting = 5-min sweep (0 model calls), no wake-on-event.
  UCWSM, Universal Construction Ratchet, Compounding Intelligence Fabric, Context-First Prompting Standard: ABSENT.
  UWCP = Universal Workstream Continuity Plane (remote execution/leases), not applicable to context.
- Overlaps found: 5 capsule shapes, 6 typed-knowledge stores, 5 admission owners, 4 ratchets, 5 cost meters.

## Ranking (Theory of Constraints, by measured share of call-1)
1. Deferred tool names (largest recorded layer; ~72% vercel+rea) -> Phase B via CCR canary extension.
2. Floor truth on the request plane (A1) -- every later number depends on it.
3. memory_project (repo CLAUDE.md activation blocks = partial-evaluation candidate) -- blocked by foreign writer.
4. Model-call accounting + Zero-Model Fraction (no receipt exists).
5. Context Policy Regret from ctx_rent's existing offline Belady bound.
Deferred by measured NPV: proof reuse / semantic objects at scale (P falsified 0.50%), singleflight, distributed cache,
time-travel, TLB, physical KV.

## Waves (ceilings in processed tokens, this pane + workers)
- W0 truth (6M): A1 request-plane attribution by single-variable probes (CCR_MAIN_CANARY=0/1, --strict-mcp-config empty vs
  default, n=3/arm haiku); wake_check pinned by session id; COMPAT-miss surfaced at SessionStart from the CCR start receipt;
  GEX44 budget file + dangling pointers + attribution (ssh, read first).
- W1 capability virtualization (10M): CCR canary collapses deferred_tools_delta to per-server counts + ToolSearch hint
  (shadow -> enforce, kill switch CCR_DEFERRED_NAMES=0); quality task = model must find and call a named deferred tool;
  n=10/arm smoke; elasticity bench (synthetic +10x / +100x skills/agents/tools: call-1 delta).
- W2 instruction elimination (5M, conditional on the foreign CLAUDE.md edit landing): activation blocks -> skill-routed pages.
- W3 model-call accounting (8M): per-obligation call receipt from transcripts + mission ledgers; Zero-Model Fraction and
  calls-per-obligation by Work Class; one zero-model closeout path (done_gate verdict closes a mission without a model turn).
- W4 agent delta return (8M): wire agent_bundle into one real reviewer path; measure parent-context growth vs prose return.
- W5 regret + CI (7M): Context Policy Regret from ctx_rent Belady bound per Work Class; resident_budget.json gains the
  listing layers on the request plane; floor CI gate.
- Closeout reserve 4M.

## Budget
Planning ceiling 2M. Lower bound 25M, P50 45M, P80 60M, P95 80M, hard authority 90M (60M + 3 x 10M top-ups).
Max cycles 12, max hours 24. First evidence commit within 3M of approval. Early-value checkpoint at 10M: A1 table + W1
shadow receipts. Breaker: two consecutive 5M intervals without a causal commit -> METHOD_PIVOT_REQUIRED.

## Kill switches / rollback
CCR_DEFERRED_NAMES=0 (new), CCR_MAIN_CANARY=0, CCR_MAIN_PROJECT=0, tools/ccr_release.py rollback; every wave = revertable commits.
HR-2: no green smoke -> rollback. HR-001: no write under ~/.claude outside the repo without a separate Owner go.

## Master done-gate mapping (Phase 7, 2026-11-05)
Each wave: gate that proves it, status, and the NPV of what was deferred. Planes labelled; chars are recorded-plane, tokens request-plane.

| Wave | Gate (command) | Status |
|---|---|---|
| W0 request-plane floor | `vault/programs/icc/floor-request-plane.{md,json}`; `python tools/test_floor_regression_gate.py` 70/70 | DONE; MCP names+instr marginal 3.56k tokens (-p) |
| W1 CCR deferred-name collapse | `claude plugin test mods/cpp-cognitive-runtime` 39/39; HR-2 smoke `phase2-release-hr2-smoke.json` 2/2 | RELEASED IN SHADOW 0.1.0-05998d9a; enforce NOT enabled (M2 format check pending) |
| W2 CLAUDE.md chain diet | gate `git status -- CLAUDE.md` clean | DEFERRED-FOREIGN-WRITER (main checkout ` M CLAUDE.md`); NPV unmeasured until the foreign edit lands |
| W3 model-call accounting | `python tools/test_done_gate_close.py` 5/5, mutation red; `python tools/mission_spend.py model-calls --mission m-1f1ba12950ec` | DONE; not Work-Class-aware (all unclassified) |
| W4 handback bundle | `vault/programs/icc/phase5-bundle-vs-prose.json` | MEASURED, REJECTED for savings (+23% chars, no parent-growth win) |
| W5 regret + floor CI | `python tools/test_ctx_regret.py`; `V-FLOOR-BUDGET-REAL-PINNED` (skill_listing, agent_listing ceilings, growth fails) | DONE; regret is an upper bound (chars/4) |
| Closeout | UKDL 5 entries; errors.md 4 rows; fresh-agent recovery test (STATE Notes) | DONE |

Deferred, with NPV: enforce deferred-name collapse (positive only if shadow receipts show the assumed one-name-per-line format; potential up to the 8-14k-char deferred layer, request-tokens UNMEASURED in interactive); Work-Class grouping in model_call_report (low: reporting only); pp-code-reviewer on Phase 4/5 diffs (risk-reduction, not savings); proof reuse / singleflight / distributed cache stay deferred as in the Waves section (P falsified 0.50%).
Baseline Ratchet: floor ceilings tightened for two listing layers only; request-plane call-1 has no committed ceiling (plane differs per host/mode), so no ratchet claim is made on it.