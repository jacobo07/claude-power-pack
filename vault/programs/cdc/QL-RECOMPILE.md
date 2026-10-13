# QuickLease SEO + GEO recompile (CDC C12, 2026-10-13) -- READ-ONLY

Machine file: `QL-RECOMPILE.json`. Reproduce: `python -I vault/programs/cdc/evidence/ql_recompile.py` (in-process `cost_to_completion.compile_cost`, QL read by file size only). Nothing was armed, edited, pushed or sent in QL.

## 1. Reality (HEAD delta, not the old list)
- Branch `feat/ql-organic-acquisition` @ `0d88a1ae` (2026-10-08 23:10), origin == local, **42 commits behind origin/main**. Mission m-23568bbcd2f9 HALTED, owner dead; nothing burning.
- PR #524 OPEN draft, UNSTABLE; last CI (2026-10-08): `UI typecheck + palette_guard + build` FAILURE, the rest green/skipped. #517 (D3 entity-graph leak) MERGED. #466 (lastmod/sitemap) and #435 (canonical) still OPEN, other sessions'.
- Sealed: W1 plans 01-01..01-05 (ownership checker 39/39 mutants, sources 43/43, registry + validator with 16 debt claims, lawyer packet P-001). Not run: Phase 1 verify/close. Phases 2-8: not started. Workstream STATE.md is stale (stopped_at 01-02); RESUMPTION.md is the truth.
- Lawyer: P-001 SENT 2026-10-08 21:08Z (Gmail `1a11d58817cf06fa`); no reply is recorded in the repo, so a reply is UNKNOWN, not absent. Never resend.
- Blockers: CENDOJ "620/2026" UNKNOWN (CENDOJ 403 to automation; human search, packet item P-001-19; BOE-A-2026-13893 gives num. 629/2026 for the 21 May sentencia). Valencian tourism decree UNKNOWN_UNREACHABLE (DOGV TLS, not bypassed).
- HEAD defects seen by grep: sitemap `lastModified: now`; og image is the InfinityOps `cortex-compass.png`; `lang={locale}` (QL-host value unproven -> the crawl decides).
- The old 50-claim list was only used as the old-shape baseline (`ql_old_claims.json`).

## 2. Phase-1 autopsy (C1 roles, 807 calls, 126.26 M processed, 156 k/call)
| role | share | | role | share |
|---|---|---|---|---|
| READ | 31.8 % | | CONTEXT_FAULT | 4.3 % |
| unattributed | 30.1 % | | RECOVERY | 2.6 % |
| IMPLEMENT | 11.1 % | | PLAN | 2.6 % |
| NOVELTY | 9.5 % | | REREAD | 2.4 % |
| CONTROL | 5.0 % | | PROOF / STATUS / REPAIR | 0 % (PROOF 0 NOT_PROVEN) |
- Topology amplification: 7 subagents carry ~118.7 M of 126.3 M (~94 %); the main thread 9.2 M. Subagent READ is 39.3 M of 40.1 M. Topology, not work, is the cost.
- Transitions: 12 commits, 77 new files, 8 claims, 0 red->green = 97, i.e. **1.30 M tokens per transition**.
- Avoidable under CDC rules: CONTEXT_FAULT + RECOVERY + REREAD = 9.3 % by role (lower bound; breaker-trip tokens not computed on this trace). Survival of the 807 calls under C3/C4: UNKNOWN (not replayed). C10 families show 7-20 % avoidable, a replay estimate, NOT_PROVEN as saving.
- Necessary: IMPLEMENT + NOVELTY (the legal-text pipeline's real new files) and the READ that feeds them. Capital created: the four W1 tools above and a sent packet; prod unchanged.

## 3. Residual compile (53 claims; 38 need the model)
DONE/NO_WORK 1 (push: origin == HEAD) · SUPERSEDED 1 (entity graph, #517; verified inside the crawl) · DETERMINISTIC 7 (ship+smoke script, CTA crawl, CostaLuz backup, gate run) · REUSE_EXISTING 3 (merge main, #466 lastmod, FARO Wilson if present) · DERIVED 3 (lang by crawl, guide plan from OWNERSHIP_MAP, panel prompts from families) · CERTIFIED_TRANSFORM 12 (4 assets after the first, guarantees list, ledger, report, handoff, KV/UKDL, links/schema, queue, lawyer-reply recording) · BOUNDED_CODING 17 · NOVEL_COGNITION 2 (screener, Andalucia evidence) · PROOF_ONLY 1 · OWNER_ONLY 1 (CENDOJ) · EXTERNAL_WAIT 4 (lawyer reply, Valencian decree, publish gate, region) · UNKNOWN/sleeping 1 (asset 6: demand UNKNOWN, cap <= 6) · RESEARCH 0 · SUPERSEDED/UNKNOWN as listed.

## 4. Semantic families and topology (8 workers, each dies at its family proof)
| fam | name | model claims | est calls | CWS of locality set (tok, est bytes/4) | shared closure | proof |
|---|---|---|---|---|---|---|
| F1 | truth + legal | 2 | 6 | 29 k | invariant: claim has source + recorded review | validator + packet items |
| F2 | technical surface | 7 | 24 | 6.5 k | locality layout/sitemap/metadata | prod crawl + attribution DB row |
| F3 | commercial core | 4 | 13 | 3.3 k | registry ids | crawl + search->CTA->new-case |
| F4 | guides (<= 6) | 8 | 28 | 20.7 k | decision map + template | validator + link graph + schema |
| F5 | GEO observability | 6 | 16 | 2.3 k | extend FARO, never a 2nd runner | provenance + ledger <= cap |
| F6 | regions | 1 | 8 | 4.9 k | real local sources | per-city source check |
| F7 | distribution | 4 | 19 | 4.9 k | backup before write | hash + link smoke |
| F8 | compounding | 6 | 23 | 3.9 k | gate reuses F2/F3 crawl | `ql_organic_gate.py` on prod |
CWS is the declared file set only (spec + resumption + code files named), not the 110 k worker floor; the floor dominates every boundary. Packets: declared set + registry ids, no spec re-read; proofs go through `proof_digest.py`. Ship (merge, CD, Std 106 smoke) is one parameterised script reused by F2/F3/F4/F7; merges serialise. F2/F3/F5 are independent localities.

## 5. Budget (processed tokens, not cash)
| | tokens | basis |
|---|---|---|
| semantic LOWER | 5.1 M | 1 call per open model claim + 1 per family, at the 110 k floor |
| P50 | **20.5 M** | tool candidate 15.2 M (slim ctx, clamped to the floor) + reserves 4.0 M (control 16 calls, proof 8, fresh agent 12) + 7.1 % repair |
| P80 | **36.4 M** | max(tool 20 % margin + reserves + 17 %, 66 events x Clock A 551 k) |
| P95 | **85.9 M** | max(tool ceiling novel x3, 66 events x QL Phase-1 rate 1.30 M) |
| HARD AUTHORITY | **96 M** | P95 x 1.10 + 650 k, rounded up (guard overrun lesson: stop + ~650 k) |
Confidence PROVISIONAL-LOW. Call counts per claim are my estimates (tool priors are not measured); the context per call is measured (Live QA 43 k, clamped by the tool to the 110 k floor). 66 events = 38 model claims x 1.75 (ASSUMPTION). The wide P50-P95 band is the honest part: P50 only holds if workers behave like Live QA packet workers (222 k/event); P95 is "no improvement over Phase 1".
Reserves: boundaries/control (2 calls x 8 families), proof (1 digest call x 8), fresh-agent test (12-call extra worker), repair/recovery (7.1 / 17.0 / 20.2 % from C10), Owner-only and external waits **0 tokens but unbounded wall time**. Wall clock: model time P50 ~1.2 h, P95 ~5.4 h (25 s/call from Phase 1) + ~1.3 h CI/deploy (5 ship events x ~15 min).

## 6. Old vs new (old is HISTORICAL)
| | central | high | max |
|---|---|---|---|
| Old (dataset lines 1-1160, historical, not reproduced) | 354 M | 424.8 M | 548.3 M |
| New | P50 20.5 M | P80 36.4 M | P95 85.9 M (HARD 96 M) |
Attribution (one engine, cumulative, so disjoint). Engine W0 for the old 50 claims at Phase-1 context = 42.3 M; **the 354 M -> 42.3 M gap is NOT attributed** (the old x8 factor and Phase-1 topology cannot be reproduced; label it unexplained). From W0: drop claims now DONE/NO_WORK/DETERMINISTIC/EXTERNAL/OWNER/sleeping -8.2 M · family structure, DERIVED, REUSE_EXISTING, CERTIFIED_TRANSFORM call counts -12.9 M · slim locality context -6.1 M = 15.2 M · explicit reserves +4.0 M and repair +1.3 M (costs) = 20.5 M. Note the P80/P95 lift is the reverse of savings: it is the uncertainty premium.
Hypothesis in the master plan (avoided ~230-310 M) is **not confirmed**: the measured claim is "P50 20.5 M / P95 85.9 M vs historical 354 M", payback conditional on workers matching Live QA behaviour.

## 7. Cash (usage_index table, ESTIMATE)
Mix from the only measured source (C10 canary 2): 88.9 % cache read, 11.0 % cache write 5m, 0.2 % output.
| | Sonnet 5 | Opus 5.5 |
|---|---|---|
| LOWER | 2.4 USD | 3.9 |
| P50 | 9.7 | 15.8 |
| P80 | 17.3 | 28.0 |
| P95 | 40.8 | 66.2 |
| HARD | 45.5 | 74.0 |
Cross-check: Phase 1 actually cost 42.3 USD for 126.3 M (0.335 USD/M), below the table mix (0.47-0.77 USD/M), so cash is an upper-ish estimate, not an invoice. Cash is not the gate; tokens are.

## 8. CAPEX vs OPEX
- **CAPEX** = everything above (build + ship + gate + handoff): 20.5 / 36.4 / 85.9 M tokens.
- **OPEX (GEO monitoring after build)**: DataForSEO inside the QL ledger, cap 10 USD/month (spec s0), SerpApi 0; the FARO panel runs on GEX44 without Claude; model use ~ 2-4 calls/month (about 0.2-0.6 M tokens, ESTIMATE); freshness cron deterministic. Real per-run cost UNKNOWN until F5 measures it.

## 9. Owner-only, waits, risks
CENDOJ search (Owner); lawyer reply (external; gates F4 publishing and any non-verbatim CostaLuz correction; content is built as READY_FOR_LEGAL_REVIEW and does not block other work); Valencian decree; #466/#435 belong to other sessions (coordinate, never edit the same files). Spec s0 authorizations (merge+CD, GEX44+DataForSEO, WordPress CostaLuz) exist from 2026-10-08 but this programme's approval does not renew them: the decision below does. A 42-commit rebase and the failing UI build on #524 are first-hour risks inside F2.

Receipt Status: DONE.

DECISION REQUIRED: APPROVE QUICKLEASE SEO + GEO EXECUTION or OPTIMIZE FURTHER
