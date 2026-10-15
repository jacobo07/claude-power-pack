"""C12: read-only QuickLease recompile. Reads QL (stat/size only), calls tools/cost_to_completion.compile_cost
in-process (no subprocess, nothing to await), writes vault/programs/cdc/QL-RECOMPILE.{json,md}.
Run: python -I ql_recompile.py"""
from __future__ import annotations
import json, math, sys
from pathlib import Path

PP = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PP / "tools"))
import cost_to_completion as ctc  # noqa: E402
import route_admission as ra  # noqa: E402
import usage_index as ui  # noqa: E402

QL = Path(r"C:\Users\User\Apps\io-ql-organic")
UI = QL / "13_UI_Product_Layer" / "infinity_ui"
OUT = PP / "vault" / "programs" / "cdc"
M = 1_000_000

# (id, family, CDC class, tool class, est_calls, note)
C = [
 # F1 truth / legal closure
 ("p1-verify-work", "F1", "PROOF_ONLY", "known_transform", 3, "Phase-1 verifier over sealed 01-01..01-05"),
 ("p1-push-pr524", "F1", "NO_WORK", "satisfied", 0, "origin/feat == HEAD 0d88a1ae; PR #524 OPEN draft"),
 ("p1-cendoj-620-human-search", "F1", "OWNER_ONLY", "owner_reality", 0, "CENDOJ 403 to automation; human browser search (P-001-19)"),
 ("p1-lawyer-reply-ingest", "F1", "EXTERNAL_WAIT", "owner_reality", 0, "reply in Gmail thread 1a11d58817cf06fa; untrusted until attributable per-item reading"),
 ("p1-lawyer-reply-record", "F1", "CERTIFIED_TRANSFORM", "known_transform", 3, "record readings into registry once a reply exists"),
 ("p6-valencian-decree-identify", "F1", "EXTERNAL_WAIT", "owner_reality", 0, "DOGV TLS failure not bypassed; UNKNOWN_UNREACHABLE"),
 # F2 technical surface (one locality packet: layout, sitemap, metadata, ql_case)
 ("p2-merge-origin-main", "F2", "REUSE_EXISTING", "known_transform", 3, "branch is 42 commits behind origin/main"),
 ("p2-lang-en", "F2", "DERIVED", "bounded_coding", 2, "layout reads locale; QL-host value unproven at HEAD; crawl decides"),
 ("p2-entity-graph-reverify-d3", "F2", "SUPERSEDED", "satisfied", 0, "#517 MERGED 2026-10-08; checked by the deterministic crawl, not a claim"),
 ("p2-og-image", "F2", "BOUNDED_CODING", "bounded_coding", 3, "HEAD og image is InfinityOps cortex-compass.png"),
 ("p2-real-lastmod", "F2", "REUSE_EXISTING", "known_transform", 2, "PR #466 (open) already drops fabricated lastmod; HEAD sitemap still lastModified: now"),
 ("p2-reviewer-person-byline", "F2", "BOUNDED_CODING", "bounded_coding", 4, "schema must equal visible byline; no invented credentials"),
 ("p2-attribution-landing-to-ql-case", "F2", "BOUNDED_CODING", "bounded_coding", 6, "migration + capture + prod DB observation"),
 ("p2-gsc-read-router", "F2", "BOUNDED_CODING", "bounded_coding", 4, "google-account-router read-only"),
 ("p2-pr-merge-cd-prod-smoke", "F2", "DETERMINISTIC", "deterministic", 0, "one parameterised ship+smoke script, reused by every family"),
 # F3 commercial core
 ("p3-services-home-check-intent", "F3", "BOUNDED_CODING", "bounded_coding", 5, ""),
 ("p3-methodology", "F3", "BOUNDED_CODING", "bounded_coding", 4, "rendered from claims registry"),
 ("p3-what-we-cannot-guarantee", "F3", "CERTIFIED_TRANSFORM", "known_transform", 2, "derived from registry not-checked list"),
 ("p3-cta-audit", "F3", "DETERMINISTIC", "deterministic", 0, "crawl script; fixes below"),
 ("p3-cta-fixes", "F3", "BOUNDED_CODING", "bounded_coding", 2, "only what the crawl flags (count UNKNOWN)"),
 ("p3-pr-merge-cd-prod-smoke", "F3", "DETERMINISTIC", "deterministic", 0, ""),
 # F4 guides cluster (legal gated, READY_FOR_LEGAL_REVIEW does not block)
 ("p4-research-plan-check", "F4", "DERIVED", "novel", 6, "OWNERSHIP_MAP (49 families) already decides ownership; only SERP differentiation is new"),
 ("p4-guides-collection", "F4", "BOUNDED_CODING", "bounded_coding", 5, "route + template + first asset"),
 ("p4-asset-registry-after-ruling", "F4", "BOUNDED_CODING", "bounded_coding", 3, "first asset on the template"),
 ("p4-asset-community-ban-17-12", "F4", "CERTIFIED_TRANSFORM", "known_transform", 3, "LC-006/LC-008 sealed"),
 ("p4-asset-licence-transfer", "F4", "CERTIFIED_TRANSFORM", "known_transform", 3, ""),
 ("p4-asset-licence-check-andalucia", "F4", "CERTIFIED_TRANSFORM", "known_transform", 3, "Decreto 28/2016 stored"),
 ("p4-asset-buyer-laws-2026", "F4", "CERTIFIED_TRANSFORM", "known_transform", 3, ""),
 ("p4-asset-6", "F4", "UNKNOWN", "sleeping", 0, "cap is <=6; demand UNKNOWN (15/17 seeds null); decided by scale/improve/pause"),
 ("p4-lawyer-review-recorded", "F4", "EXTERNAL_WAIT", "owner_reality", 0, "legal wording publishes only after recorded review"),
 ("p4-links-sitemap-schema", "F4", "CERTIFIED_TRANSFORM", "known_transform", 2, ""),
 ("p4-pr-merge-cd-prod-smoke", "F4", "DETERMINISTIC", "deterministic", 0, ""),
 # F5 GEO observability (extends GEO-audit geo-seo-os / FARO, never a second runner)
 ("p5-faro-panel-30-prompts", "F5", "DERIVED", "known_transform", 3, "prompts derive from ownership map families"),
 ("p5-ql-ledger", "F5", "CERTIFIED_TRANSFORM", "known_transform", 2, "separate ledger dir, cap $10/mo"),
 ("p5-gex44-run-provenance", "F5", "BOUNDED_CODING", "bounded_coding", 4, "deploy on existing FARO install"),
 ("p5-serp-baseline-dataforseo", "F5", "BOUNDED_CODING", "bounded_coding", 3, "inside the $10 cap"),
 ("p5-mention-citation-recommendation-wilson", "F5", "REUSE_EXISTING", "known_transform", 2, "reuse FARO Wilson if present; UNKNOWN until read"),
 ("p5-report", "F5", "CERTIFIED_TRANSFORM", "known_transform", 2, ""),
 # F6 regions by evidence
 ("p6-andalucia-by-evidence", "F6", "NOVEL_COGNITION", "novel", 8, "real local sources only"),
 ("p6-cvalenciana-by-evidence", "F6", "EXTERNAL_WAIT", "sleeping", 0, "blocked by the unidentified decree"),
 # F7 distribution
 ("p7-buyer-screener", "F7", "NOVEL_COGNITION", "novel", 10, "no legal verdicts"),
 ("p7-costaluz-backup", "F7", "DETERMINISTIC", "deterministic", 0, "REST GET to disk before any write"),
 ("p7-costaluz-corrections-lc001-lc002", "F7", "BOUNDED_CODING", "bounded_coding", 3, "verbatim BOE restore needs no review; other wording waits"),
 ("p7-costaluz-tracked-links", "F7", "BOUNDED_CODING", "bounded_coding", 3, ""),
 ("p7-earned-distribution-queue", "F7", "CERTIFIED_TRANSFORM", "known_transform", 3, "drafts only; no outreach beyond spec s0"),
 ("p7-pr-merge-cd-prod-smoke", "F7", "DETERMINISTIC", "deterministic", 0, ""),
 # F8 compounding
 ("p8-ql-organic-gate-script", "F8", "BOUNDED_CODING", "novel", 6, "reuses the F2/F3 crawl; only claim/attribution/GEO checks are new"),
 ("p8-gate-run-prod", "F8", "DETERMINISTIC", "deterministic", 0, ""),
 ("p8-scale-improve-pause", "F8", "BOUNDED_CODING", "bounded_coding", 4, ""),
 ("p8-freshness-by-source", "F8", "BOUNDED_CODING", "bounded_coding", 3, ""),
 ("p8-kv-ukdl-ratchet", "F8", "CERTIFIED_TRANSFORM", "known_transform", 2, ""),
 ("p8-fresh-agent-test", "F8", "BOUNDED_CODING", "bounded_coding", 6, "cold agent; counts as one extra worker"),
 ("p8-two-layer-handoff", "F8", "CERTIFIED_TRANSFORM", "known_transform", 2, ""),
]
FAM = {
 "F1": ("truth + legal closure", ["vault/specs/ql-organic-acquisition.md", "vault/quicklease/organic/RESUMPTION.md",
        "vault/quicklease/organic/lawyer/P-001/PACKET.json", "13_UI_Product_Layer/infinity_ui/lib/quicklease/legal-claims*.ts"]),
 "F2": ("technical surface", ["13_UI_Product_Layer/infinity_ui/app/layout.tsx", "13_UI_Product_Layer/infinity_ui/app/sitemap.ts",
        "13_UI_Product_Layer/infinity_ui/app/quicklease/layout.tsx", "13_UI_Product_Layer/infinity_ui/lib/quicklease/funnel-events.ts"]),
 "F3": ("commercial core", ["13_UI_Product_Layer/infinity_ui/app/quicklease/services/*.tsx", "13_UI_Product_Layer/infinity_ui/app/quicklease/page.tsx",
        "13_UI_Product_Layer/infinity_ui/lib/quicklease/faq.ts"]),
 "F4": ("guides cluster", ["13_UI_Product_Layer/infinity_ui/lib/quicklease/legal-claims*.ts", "vault/quicklease/organic/OWNERSHIP_MAP.md"]),
 "F5": ("GEO observability", ["vault/specs/ql-organic-acquisition.md"]),
 "F6": ("regions", ["vault/quicklease/organic/OWNERSHIP_MAP.md"]),
 "F7": ("distribution", ["vault/quicklease/organic/OWNERSHIP_MAP.md"]),
 "F8": ("compounding", ["vault/quicklease/organic/RESUMPTION.md", "vault/specs/ql-organic-acquisition.md"]),
}
# measured per-call processed tokens (C1/C10): Live QA packet workers 43k; QL Phase 1 155k (807 calls, 126.26M)
LIVEQA_CTX, P1_CTX = 43_000, 155_000
HOLD = {"liveqa": 0.071, "clockA": 0.151, "intent": 0.170, "dws": 0.202}


def cws(globs):
    tot, files = 0, 0
    for g in globs:
        for p in QL.glob(g):
            if p.is_file():
                tot += p.stat().st_size // 4
                files += 1
    return {"files": files, "tokens_est": tot}


def run(profile_ctx, claims, margin=0.2, calls_override=None, deopt=3.0):
    floors = ra.load_floors(None)
    rows = []
    for (i, f, cdc, tc, n, note) in claims:
        status = "sleeping" if tc == "sleeping" else None
        cls = "novel" if tc == "novel" else tc
        if tc == "sleeping":
            cls = "known_transform"
        d = {"id": i, "class": cls, "est_calls": n if n else None}
        if status:
            d["status"] = status
        if tc == "satisfied":
            d["class"], d["status"] = "known_transform", "satisfied"
        if tc in ("deterministic", "owner_reality"):
            d.pop("est_calls")
        rows.append(d)
    doc = {"claims": rows, "deopt_factor": deopt,
           "actuals": {k: {"ctx_tokens": profile_ctx} for k in ctc.MODEL_CLASSES}}
    return ctc.compile_cost(doc, floors, margin=margin)


def main():
    floors = ra.load_floors(None)
    wfloor = int(floors["profiles"][ra.TOP_LEVEL]["floor"])
    new = run(LIVEQA_CTX, C)            # ctx clamped up to the worker floor by the tool
    # "old shape": the 50 original claims all open at the measured P1 per-call context (no CDC classes)
    old = json.loads((OUT / "evidence" / "ql_old_claims.json").read_text(encoding="utf-8-sig"))
    old_doc = {"claims": [{"id": c["id"], "class": c["class"], "status": "open"} for c in old["claims"]],
               "actuals": {k: {"ctx_tokens": P1_CTX} for k in ctc.MODEL_CLASSES}}
    old_eng = ctc.compile_cost(old_doc, floors)
    # waterfall: each step recomputed by the same engine, applied cumulatively (no double count)
    s1 = old_eng["candidate"]["tokens"]
    # step 2: remove NO_WORK/SUPERSEDED/zero-token classes and sleeping, keep old calls & ctx
    keep = {c[0] for c in C if c[3] in ("known_transform", "bounded_coding", "novel")}
    oldcalls = {c["id"]: c for c in old["claims"]}
    # work in terms of the engine for ctx change only
    new_calls_P1ctx = run(P1_CTX, C)["candidate"]["tokens"]
    new_calls_slim = new["candidate"]["tokens"]
    # families: packet opens + proof + control reserves (explicit lines)
    nfam = len([f for f in FAM if any(c[1] == f and c[3] in ctc.MODEL_CLASSES for c in C)])
    ctx = max(LIVEQA_CTX, wfloor)
    open_calls = new["candidate"]["calls"]
    reserves = {
        "packet_open_control": nfam * 2 * ctx,           # 2 calls per family boundary (open + hand-off)
        "proof_digest": nfam * 1 * ctx,                  # 1 digest call per family (proof_digest.py absorbs the rest)
        "fresh_agent_extra_worker": 1 * 12 * ctx,        # cold agent test = separate worker
    }
    base = new["candidate"]["tokens"]
    res_sum = sum(reserves.values())
    # repair/recovery reserve scenarios from C10 replay
    rep = {"P50": HOLD["liveqa"], "P80": HOLD["intent"], "P95": HOLD["dws"]}
    p50 = int((base + res_sum) * (1 + rep["P50"]))
    p80 = int((new["percentiles"]["P80"] + res_sum) * (1 + rep["P80"]))
    p95 = int((new["percentiles"]["P95"] + res_sum) * (1 + rep["P95"]))
    # cross-check against OBSERVED tokens per progress event (C10 holdouts / C1): the claim-level call estimates are mine,
    # the per-event rates are measured. Events per model claim (1.75) is an ASSUMPTION (edit + commit/proof, some claims 1).
    n_claims = len([c for c in C if c[3] in ctc.MODEL_CLASSES])
    events = int(round(n_claims * 1.75))
    rates = {"liveqa_222k": 222_000, "clockA_551k": 551_000, "intent_595k": 595_000, "dws_1.21M": 1_210_000, "ql_phase1_1.30M": 1_301_606}
    xc = {k: events * v for k, v in rates.items()}
    p50_tool, p80_tool, p95_tool = p50, p80, p95
    p80 = max(p80, xc["clockA_551k"])
    p95 = max(p95, xc["ql_phase1_1.30M"])
    hard = int(math.ceil((p95 * 1.10 + 650_000) / M) * M)
    lower_calls = len([c for c in C if c[3] in ctc.MODEL_CLASSES]) + nfam
    lower = lower_calls * ctx
    hard = int(math.ceil((p95 * 1.10 + 650_000) / M) * M)
    # waterfall (cumulative, same engine): A old shape @P1 ctx -> B drop zero-token/done/sleeping -> C family call counts -> D slim ctx
    old_open_model = [c for c in old["claims"] if c["class"] in ctc.MODEL_CLASSES]
    wf = [("W0 old claim list (50 claims, all open, P1 per-call context 155k, tool priors for calls)", s1)]
    # B: claims that the recompile proves DONE/NO_WORK/SUPERSEDED/DETERMINISTIC/OWNER/SLEEPING drop to 0 tokens; their prior cost leaves
    new_ids_zero = {c[0] for c in C if c[3] in ctc.ZERO_CLASSES + ("sleeping",)}
    cut = [c for c in old["claims"] if c["id"] in new_ids_zero or c["class"] in ctc.ZERO_CLASSES]
    b_doc = {"claims": [{"id": c["id"], "class": c["class"], "status": "open"} for c in old["claims"] if c not in cut]
                       + [{"id": "_pad", "class": "deterministic"}],
             "actuals": old_doc["actuals"]}
    s2 = ctc.compile_cost(b_doc, floors)["candidate"]["tokens"]
    wf.append(("W1 minus claims now DONE/NO_WORK/SUPERSEDED/DETERMINISTIC/EXTERNAL/OWNER/SLEEPING (same engine, same ctx)", s2))
    # C: new claim set & est_calls at P1 context (family/derived/reuse structure)
    s3 = new_calls_P1ctx
    wf.append(("W2 recompiled claim set with CDC est_calls (families, DERIVED, REUSE, CERTIFIED_TRANSFORM) at P1 context", s3))
    wf.append(("W3 slim locality-packet context (Live QA measured 43k, clamped to worker floor)", new_calls_slim))
    wf.append(("W4 explicit reserves (control, proof, fresh agent) -- ADDED, not saved", new_calls_slim + res_sum))
    wf.append(("W5 repair/recovery reserve at the C10 liveqa share (7.1%)", p50))
    price = ui.load_prices()
    mix = {"cache_read": 289_730 / 326_000, "cache_write_5m": 35_770 / 326_000, "output": 727 / 326_000}
    def usd(tokens, model):
        p = price[model]
        return tokens / M * sum(mix[k] * p[k] for k in mix)
    cash = {}
    for name, v in (("LOWER", lower), ("P50", p50), ("P80", p80), ("P95", p95), ("HARD", hard)):
        cash[name] = {m: round(usd(v, m), 2) for m in ("claude-sonnet-5", "claude-opus-5-5")}
    hist = {"central_tokens": 354_000_000, "p_hi_tokens": 424_800_000, "p_max_tokens": 548_300_000,
            "phase1_tokens": 126_255_827, "phase1_usd": 42.3, "label": "HISTORICAL (dataset lines 1-1160); not reproduced by this engine"}
    out = {
        "unit": "C12", "generated_for": "2026-10-13", "read_only": True,
        "reality": {
            "branch": "feat/ql-organic-acquisition", "head": "0d88a1ae (2026-10-08 23:10), origin == local",
            "behind_origin_main": 42, "dirty_paths": ["_audit_cache/source_map.json", "vault/handoffs/ESCALATED.md", "vault/handoffs/escalations.json", "vault/handoffs/mirror-drift-*.md"],
            "pr_524": "OPEN draft, mergeState UNSTABLE; last CI run 2026-10-08: UI typecheck+build FAILURE, rest SUCCESS/SKIPPED",
            "pr_466": "OPEN", "pr_435": "OPEN (conflicts main on faq/page.tsx per RESUMPTION)", "pr_517": "MERGED 2026-10-08",
            "mission": "m-23568bbcd2f9 HALTED, owner DEAD (master plan 2026-10-10); nothing burning",
            "phases_sealed": "W1 plans 01-01..01-05 sealed; Phase 1 verify/close not run; Phases 2-8 not started; workstream STATE stale (stopped_at 01-02)",
            "lawyer": "P-001 SENT 2026-10-08 21:08Z, Gmail 1a11d58817cf06fa; no reply recorded in repo (UNKNOWN whether one exists); never resend",
            "cendoj_620_2026": "UNKNOWN (METHOD_BLIND, CENDOJ 403); BOE-A-2026-13893 gives num. 629/2026 for 21 May sentencia",
            "valencian_decree": "UNKNOWN_UNREACHABLE (DOGV TLS)",
            "head_defects_seen_by_grep": "sitemap lastModified: now (L45-L113); og image = InfinityOps cortex-compass.png; lang={locale} (QL-host value unproven)",
        },
        "autopsy_P1": {"tokens": 126_255_827, "calls": 807, "tokens_per_call": 156_449,
            "roles_share": {"READ": .318, "unattributed": .301, "IMPLEMENT": .111, "NOVELTY": .095, "CONTROL": .050, "CONTEXT_FAULT": .043, "RECOVERY": .026, "PLAN": .026, "REREAD": .024, "RESEARCH": .006, "PROOF": 0, "STATUS": 0, "REPAIR": 0},
            "avoidable_under_cdc_rules_share_lower_bound": round(.043 + .026 + .024, 3),
            "avoidable_note": "CONTEXT_FAULT+RECOVERY+REREAD = 9.3% by role only; breaker-trip tokens not computed on this trace; NOT_PROVEN as saving",
            "necessary": "IMPLEMENT 11.1% + NOVELTY 9.5% (legal-text pipeline new files) + READ that feeds them; 'READ 31.8%' mostly subagent re-priming (39.3M of 40.1M in subagents)",
            "topology_amplification": "7 subagents carry 118.7M of 126.3M tokens (~94%); main thread only 9.2M; topology, not work, is the cost",
            "transitions": {"commit": 12, "new_file": 77, "claim": 8, "red_green": 0, "tokens_per_transition": 1_301_606},
            "capital_created": "W1 sealed: ownership checker (39/39 mutants red), sources tool (43/43), registry+validator (16 debt claims), lawyer packet P-001 sent; prod unchanged",
            "survival_under_cdc_rules": "UNKNOWN as replay of the 807 calls was not re-run under C3/C4; C10 families show 7-20% avoidable (replay estimate)"},
        "taxonomy_counts": {}, "claims": [], "families": {}, "budget": {}, "old_vs_new": {}, "cash": {}, "opex": {}, "wall_clock": {}, "owner_only_and_waits": []}
    cnt = {}
    for (i, f, cdc, tc, n, note) in C:
        cnt[cdc] = cnt.get(cdc, 0) + 1
        out["claims"].append({"id": i, "family": f, "cdc_class": cdc, "tool_class": tc, "est_calls": n, "note": note})
    out["taxonomy_counts"] = cnt
    for f, (name, globs) in FAM.items():
        mc = [c for c in C if c[1] == f and c[3] in ctc.MODEL_CLASSES]
        out["families"][f] = {"name": name, "model_claims": len(mc), "calls": sum(c[4] for c in mc), "cws_locality_set": cws(globs),
            "worker_lifetime": "one worker per family, dies at the family proof; locality packet = declared set + registry ids, no spec re-read",
            "shared": {"F1": "invariant: claim has primary source + recorded review", "F2": "locality: layout/sitemap/metadata; one crawl proves lang, graph, canonical, lastmod, og",
                       "F3": "evidence: registry ids; one CTA/crawl proof", "F4": "decision: ownership map; invariant: validator; template", "F5": "locality: GEO-audit FARO; ledger",
                       "F6": "evidence: real local sources", "F7": "decision: screener rules; invariant: backup before write", "F8": "proof closure: gate reuses F2/F3 crawl"}[f],
            "proof_closure": {"F1": "claims validator + packet items", "F2": "prod crawl + attribution DB row", "F3": "prod crawl + search->CTA->new-case smoke",
                "F4": "validator + link graph + sitemap/schema", "F5": "GEO run with provenance + ledger <= cap", "F6": "source check per city", "F7": "backup hash + link smoke", "F8": "ql_organic_gate.py on prod"}[f]}
    out["budget"] = {
        "worker_floor": wfloor, "slim_ctx_used": ctx, "model_claims_open": len([c for c in C if c[3] in ctc.MODEL_CLASSES]),
        "open_model_calls": open_calls, "families_with_model_work": nfam, "reserves_tokens": reserves,
        "LOWER": lower, "P50": p50, "P80": p80, "P95": p95, "HARD_AUTHORITY": hard,
        "tool_output": {"confidence": new["confidence"], "percentiles": new["percentiles"], "floor": new["floor"], "profile_source": new["profile_source"]},
        "tool_based": {"P50": p50_tool, "P80": p80_tool, "P95": p95_tool},
        "cross_check_tokens_per_progress_event": {"model_claims": n_claims, "events_assumed": events, "events_per_claim_ASSUMPTION": 1.75, "rates": rates, "totals": xc,
            "reading": "tool-based P50 sits at the Live QA rate (best measured, slim packet workers). P80 is lifted to the Clock A rate and P95 to the QL Phase-1 rate (no improvement) because the tool's call counts are uncalibrated estimates. Reserves are inside the per-event rates, not added again."},
        "how": "LOWER = 1 call per open model claim + 1 per family at the floor; P50 = tool candidate + reserves, +7.1% (Live QA replay) repair; P80 = max(tool 20% margin + reserves +17.0%, events x Clock A 551k); P95 = max(tool ceiling novel x3 + reserves +20.2%, events x QL Phase-1 1.30M); HARD = P95 x1.10 + 650k (guard overrun lesson: stop + ~650k), rounded up to 1M",
        "confidence": "PROVISIONAL-LOW: per-class calls are my estimates (PRIOR-like), ctx is measured (Live QA 43k) but clamped to the floor; profile calls are not calibrated on QL",
        "per_class_priors": ctc.PRIORS}
    out["old_vs_new"] = {"historical": hist, "waterfall_engine_reproduced": [{"step": s, "tokens": t} for s, t in wf],
        "savings_attribution_note": "steps W0->W3 are cumulative on one engine, so each delta is disjoint; reserves in W4/W5 are costs, not savings. The gap between HISTORICAL 354M and engine W0 is NOT attributed (the old x8 factor / Phase-1 topology cannot be reproduced here).",
        "deltas": {"claims_removed_done_det_owner": s1 - s2, "family_structure_and_derivation": s2 - s3, "slim_context": s3 - new_calls_slim,
                   "total_engine_vs_P50": s1 - p50}}
    out["cash"] = {"table": "tools/usage_index.load_prices() at run time", "mix": {k: round(v, 4) for k, v in mix.items()},
        "mix_source": "only measured mix on hand: C10 canary run 2; ESTIMATE", "usd": cash,
        "historical_cross_check": "Phase 1 actual 42.3 USD / 126.26M = 0.335 USD/M; table-mix cost is higher, so cash is a ceiling-ish ESTIMATE, not an invoice"}
    out["opex"] = {"separation": "CAPEX = everything in budget above (build + ship). OPEX = GEO monitoring after build.",
        "geo_monitoring_per_month": {"dataforseo_cap_usd": 10, "serpapi_usd": 0, "note": "spec s0 cap; actual per-run cost UNKNOWN until F5 measures it",
            "model_tokens_est": "report/ingest ~ 2-4 calls/month -> about 0.2-0.6M tokens/month (ESTIMATE); the panel runs on GEX44 without Claude"},
        "freshness_cron_tokens": "deterministic; 0 model tokens unless a source changed"}
    ext = [("p1-cendoj-620-human-search", "Owner browser search of recurso 1/143/2025 at CENDOJ"),
           ("lawyer reply (P-001)", "Maria Luisa answers in thread 1a11d58817cf06fa; untrusted until per-item reading; gates F4 publish and F7 non-verbatim corrections"),
           ("p6-valencian-decree-identify", "DOGV TLS failure; Owner/human or later fix"),
           ("PR #466 / #435", "other sessions' PRs; coordinate, never edit same files")]
    out["owner_only_and_waits"] = [{"id": a, "what": b} for a, b in ext]
    calls_total = open_calls + nfam * 3 + 12
    out["wall_clock"] = {"model_hours": round(calls_total * 25 / 3600, 1), "basis": "Phase 1: 5.7 h / 807 calls = 25 s per call",
        "ci_and_deploy": "5 ship events x ~15 min CI (observed 2026-10-08 12-16 min) = ~1.3 h", "external_waits": "lawyer reply, CENDOJ, Valencian decree: UNBOUNDED (not in any token figure)",
        "note": "families F2/F3/F5 are independent localities and could overlap, but each ship merges to main: serialise merges"}
    (OUT / "QL-RECOMPILE.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: out["budget"][k] for k in ("LOWER", "P50", "P80", "P95", "HARD_AUTHORITY", "open_model_calls", "families_with_model_work")}))
    print(json.dumps(out["old_vs_new"]["waterfall_engine_reproduced"], indent=1))
    print(json.dumps(out["cash"]["usd"]))
    print(out["wall_clock"]["model_hours"], {f: v["cws_locality_set"] for f, v in out["families"].items()})


if __name__ == "__main__":
    main()
