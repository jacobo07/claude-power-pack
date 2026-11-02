# S9 proposal: Exactness Bridge (Lane B) + Mission Control failure-immunity (Lane A)

Status: PROPOSED 2026-11-01, awaiting Owner approval. Supersedes the "bounded S9 pilot" choice and absorbs its kill rule.
Inline copy presented in chat; this file is the backup. On approval, copy it into gen3-pp ASCENSION-PLAN.md as "Wave S9".

## Reality Scan (2026-11-01, GEX44)
- Anchors: t1 `62e108c6` (t1/campaign), gen3 `ddd4d95a` (mission/gen3), GEX44 PP clone `ac18e7a9`. No mission worker is alive (spare daemons only).
- PP divergence: `ac18e7a9` (not_before) is absent on the laptop, and laptop `05407d94` (mission-policy) is absent on GEX44.
- Lane A facts:
  - `WAIT_RESOURCE` is an `owner_hold` of kind `resource` (gsd_mission.py:2544-2575, 2878), so hold-as-pause is structural.
  - The breaker judges one `mission_binding.execution_root`, so a sibling repo is invisible to it.
  - `no_progress` is terminal (gsd_mission.py:5859-5862).
  - `arm_chain` returns the authoritative mission_id (6318-6345), but helper tools still glob the newest `gsd-mission-*.json` (exp_successor_packet.py:93, flow_replay.py:120).
  - The t1 `llm_fix --budget-usd` is checked only at dispatch: S8d r1 spent $35.45 against a $30 run budget.
- Lane B facts:
  - sweep-b: 1613 fns, fanout ptr-args 13 and sp-locals 31 compile gains, plus v5t.
  - s8b-diagnosis covers 69 of the 73.
  - s8a search controls exist per fn.
  - S8d r1: 27 judged, 0 SOLVED, 26 IMPROVED (a subset of the 73).
  - sweep-h: +5 held-out compiles.
  - Owners already present: `causal_diff.py`, `build_twin.py`, `atoms.py`/`g3_atoms.py`, `g4_ops.py`, `search_ops.py`, `certify.py`, `compiler_causality.py`, `maturity.py`, `g4_ab.py`.
  - relations.json is thin: 10 causes, 33 pairs, 1-3 lineages each, `suff_lb` 0.0 on most pairs.
- Maturity 2/10:
  - D01, D02 and D09 are capped by wiring and evidence names (no `s1/types.json`, `regime_router` does not import `g4_solv`), not by capability.
  - D04, D05, D07 and D11 reach 10 only through the S6 literal SUCCESS, which its own caveat calls within noise.

## Ownership / duplicate audit
No new OS and no new lifecycle. Lane A extends PP `gsd_mission.py`, `mission_binding.py`, `mission_spend.py`, `mission_topup.py` and the ledger. Lane B extends t1 `modules/recon_fabric/*` (the owners listed above). Duplicate to resolve: `atoms.py` vs `g3_atoms.py` (pick one owner in B2).

## Lanes, mode, gates
A0 EXECUTION: reconcile the PP copies (git bundle both ways, merge on GEX44, laptop fast-forward). Lane A edits only after A0.
A1 PLAN: durable WAIT_TIME/WAIT_RESOURCE/PAUSED as non-owner, nonterminal states that release the worker lease: checkpoint, exit, rehydrate on the unblock event, zero epochs while waiting. Owner hold stays Owner-only.
A2 EXECUTION: Mission Workset (repos, roles, custody, HEADs). The breaker fingerprints every workset root; the gen3 workaround status writes are retired.
A3 EXECUTION: terminal precision (CHECKPOINT_COMPLETE / NEXT_PLAN_REQUIRED / METHOD_PIVOT_REQUIRED distinct from no_progress stall). Owner Decision Compiler: method exhaustion inside authority becomes a bounded method plan, not an Owner question.
A4 EXECUTION: economic lease. Reserve worst-case before dispatch (t1 llm_fix + mission_spend), reconcile after, settled+reserved <= envelope; concurrency shrinks to fit.
A5 EXECUTION: decision delivery semantics (record / wake / wake-when-ready / next-epoch); mission-id only from the operation result (globbing helpers fixed, regression test).
A6: Production Reality canaries MC-PR1..7 on GEX44 with real throwaway missions, plus a replay of the overnight 2 h idle incident (target ~0 avoidable idle).
B0 EXECUTION: verify spend accounting; Build Twin check (build_twin.verdict) over the TUs of the 73+5; shared twin uncertainty with fan-out outranks source tweaks.
B1 EXECUTION: Transition Corpus `evidence/ascension/s9/transition.jsonl` (pre/post state, unlocking rule, diagnostics, objdiff residual, search/model history, best candidate, H flag). Also diagnose the 4 fns missing from s8b-diagnosis.
B2 EXECUTION: WHY_NOT_EXACT census via causal_diff normal form; UNKNOWN_DIAGNOSIS becomes a work unit. Cluster into causal classes, report 73 -> k honestly, rank dominators.
B3 PLAN: bridge canary on the top class. Induce an operator from minimal deltas (S8d r1 IMPROVED diffs + s8a controls), then run regional CEGIS search via g4_ops/search_ops with a dead-compile stop, then certify. Synthetic tomography only if the class is ambiguous.
B4: held-out application to the clean H members of that class (5 compile gains; record contamination).
B5 EXECUTION: evidence-graded Capability Delta Gate (replication, independence, cost, attribution), D11 regrade, D01/D02 layered (structural unlock / certified propagation / held-out / policy), Factory Contribution attribution in certify (PRODUCT_HARVEST / CAPABILITY_DELTA / ASSURANCE), and a D09 auto-learning hook on every exact closure.
B6: Motion applicability check, Construction Return, KV incidents (17 seeds), UKDL candidates, CBR, handoff.

## Stop rule (absorbs the bounded-pilot kill criterion)
Bridge success = >=2 exact from one mechanism in a class with >=3 members, plus >=1 independent/held-out application, 0 lapses.
If B3 and B4 give <=1 exact and no new evidence delta remains: METHOD_PIVOT_REQUIRED with the exact residual, and the programme closes (Owner's pilot rule).

## Execution topology
- Phase 1, attended in the laptop pane, <=2 subagents: A0, A1-A5 on the GEX44 PP clone, and in parallel B0-B2 (deterministic, $0).
- Phase 2: when MC-PR1..7 are green, arm ONE gen3 mission with a Workset of gen3 + t1 + PP. Use arm-chain `--no-launch`, then `mission_topup budget`, then the sweep launches it. It runs B3-B6 on the corrected runtime, which doubles as the fresh-inheritance canary.
- No unattended model spend before A4 is green.

## Budget
Tokens, Owner authority 120M:
- Lane A: 45M;
- Lane B: 50M;
- assurance: 10M;
- contingency: 15M;
- top-ups: 2 x 20M.

Model:
- settled ~$331 of $471.10 (verify in B0), in-flight $0, remaining ~$140;
- generic Harvest $0;
- capability canary reserve $25, used only after B0-B2 plus fixed point are exhausted, through the A4 lease;
- held-out $15;
- contingency $10;
- hard cap $50 (low $0 / central $25 / high $50), leaving >= ~$90 unspent.

Deterministic compute: GEX44 CPU, no cap beyond the cycle and hour limits (14 cycles, 36 h). No push.
