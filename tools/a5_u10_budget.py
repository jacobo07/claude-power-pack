#!/usr/bin/env python3
"""ce-a5 U10: READ-ONLY DWS recompilation. Builds A/dws-claims-semantic.json and A/DWS-BUDGET-FINAL.md.

No model calls, no DWS product work. Pricing engine = tools/cost_to_completion.compile_cost (semantic stage).
Never applies a percentage to the historical 6.5B: new numbers are calls x ctx per obligation, ctx measured by the
U2 replay of policy f (slim floor + rotate@20 + read-once + STATE projection + poll->event).
"""
from __future__ import annotations

import datetime
import json
import math
import re
import subprocess
import sys
from pathlib import Path

W = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(W / "tools"))
import cost_to_completion as ctc  # noqa: E402
import a5_counterfactual as cf  # noqa: E402
import route_admission as ra  # noqa: E402

A = W / "vault/programs/cognitive-economy/a5"
D = Path("/home/kobii/ce5-env/data")
DWS = D / "orca-dws"
HEAD_EXPECT = "466b62d82"
HIST_BASE = 6_501_959_646
PRICING = W / "vault/pricing/anthropic_2026-09.json"
SECTIONS = [
    "Compilation time", "DWS HEAD and worktree", "Scope", "Counts", "Old-architecture baseline",
    "New irreducible lower bound", "New execution profile", "Token budget", "Model routing shares", "USD",
    "Quota reality", "Confidence", "Assumptions", "Top uncertainties", "Savings vs old",
    "Extinguished", "OLD vs NEW", "Meta-analysis", "Universal iteration pass",
]
DECISION = ["DECISION REQUIRED", "APPROVE DWS EXECUTION", "or", "OPTIMIZE FURTHER"]
ROUTE = {"known_transform": "claude-sonnet-5", "family": "claude-sonnet-5", "novel": "claude-opus-5",
         "visual": "claude-opus-5", "proof": "claude-sonnet-5", "reality": "claude-sonnet-5",
         "closeout": "claude-sonnet-5", "recovery": "claude-sonnet-5"}
CATS = ["known_transform", "family", "novel", "visual", "proof", "reality", "closeout", "recovery"]
RECOVERY_SHARE = {"lower": 0.0, "expected": 0.098, "p90": 0.196, "ceiling": 0.294}


def refuse_percentage_of_historical(forecast: float, hist: float = HIST_BASE) -> None:
    """Mutant guard: a forecast that is hist x k (k a 1%-grid factor, 0 < k) is a percentage, not a compile."""
    r = forecast / hist * 100.0
    if abs(r - round(r)) < 1e-4 or abs(forecast - hist) / hist < 1e-6:
        raise ctc.Refused("PERCENTAGE_OF_HISTORICAL", f"forecast {forecast:,.0f} = {hist:,.0f} x {r / 100:.4f}")


def load_matrix() -> list[dict]:
    t = (DWS / "config/dws-completion-matrix.jsonc").read_text(encoding="utf-8")
    t = re.sub(r"^\s*//.*$", "", t, flags=re.M)
    return json.loads(t)["rows"]


def dws_head() -> tuple[str, str]:
    h = subprocess.run(["git", "-C", str(DWS), "log", "-1", "--format=%H"], capture_output=True, text=True).stdout.strip()
    s = subprocess.run(["git", "-C", str(DWS), "status", "--short"], capture_output=True, text=True).stdout.strip()
    return h, s


def ctx_stats(by, capsule: int) -> dict:
    """Per-call ctx under policy f (replay of a5_counterfactual.replay with the ctx recorded)."""
    vals = []
    for calls in by.values():
        if not calls:
            continue
        g = cf.caused(calls)
        cur, seg = cf.SLIM, 0
        for c, gr in zip(calls, g):
            if c["label"] in ("REDISCOVERY", "CONTROL_LOOP"):
                continue
            if seg >= 20:
                cur, seg = cf.SLIM + capsule, 0
            if c["label"] == "STATE_READ":
                gr = min(gr, cf.STATE_CAP)
            vals.append(cur)
            seg += 1
            cur += gr
    vals.sort()
    n = len(vals)
    return {"n": n, "total": sum(vals), "mean": sum(vals) // n, "p50": vals[n // 2], "p90": vals[int(n * 0.9)]}


# ---------------------------------------------------------------- claims
def build_claims(budget: dict, obsdoc: dict, rows: list[dict]):
    """Return (claims, judgments). Deterministic: class -> obligations by fixed rules."""
    byid_obs = {c["id"]: [o if isinstance(o, str) else o["obs_id"] for o in c.get("observations", [])]
                for c in obsdoc["claims"]}
    row_state = {f"row-{r['id']}": r["state"] for r in rows}
    claims, J = [], []
    inv = [{"id": "matrix-row-state-change", "kind": "matrix row state differs from compile time"},
           {"id": "dws-head-moved", "kind": f"DWS HEAD != {HEAD_EXPECT}"}]
    seen_inv = {}
    for c in budget["claims"]:
        cid, cls = c["id"], c["class"]
        out = {"id": cid, "class": cls, "status": c["status"], "why": c["why"], "phases": c.get("phases", []),
               "matrix_state": row_state.get(cid)}
        if cls in ("sleeping", "deterministic"):
            claims.append(out)
            continue
        ph = (c.get("phases") or [None])[0]
        sc = cid.startswith(("p", "vis")) and not cid.startswith("row")
        proof = cid if sc else (f"gate-p{ph}" if ph else f"gate-{cid}")
        obl = []
        obs_ids = byid_obs.get(cid, [])
        for oid in obs_ids:
            obl.append({"id": f"obs-{oid}", "satisfier": "OBSERVATION", "observation": oid, "cat": "reality",
                        "invalidators": inv + [{"id": "reality-epoch", "kind": "epoch != E0"}]})
        if cls == "owner_reality":
            obl.append({"id": "owner-physical", "satisfier": "OWNER", "cat": "owner", "invalidators": inv})
        elif cls == "known_transform":
            obl.append({"id": "exec", "satisfier": "MODEL", "model_class": "known_transform", "cat": "known_transform",
                        "alternatives": ["TRANSFORM"], "invalidators": inv})
        elif cls == "bounded_coding":
            fam = f"phase-{ph}" if ph else f"claim-{cid}"
            obl.append({"id": "family-code", "satisfier": "TRANSFORM", "family": fam, "proof": proof, "cat": "family",
                        "invalidators": inv})
        elif cls == "novel":
            vis = cid.startswith("vis-")
            obl.append({"id": "decision", "satisfier": "MODEL", "model_class": "novel",
                        "cat": "visual" if vis else "novel", "invalidators": inv})
        if cls != "owner_reality":
            obl.append({"id": "proof", "satisfier": "PROOF", "proof": proof, "cat": "proof", "invalidators": inv})
            obl.append({"id": "evidence-stamp", "satisfier": "TOOL", "cat": "tool", "invalidators": inv})
            if ph is None and cls in ("bounded_coding",):
                J.append(f"{cid}: matrix row lists no phase; family and proof are claim-own (no sharing assumed).")
            if len(c.get("phases") or []) > 1:
                J.append(f"{cid}: phases {c['phases']}; proof/family keyed to the first phase {ph} only (second not priced separately).")
        out["obligations"] = obl
        claims.append(out)
    J += [
        "Class->obligation mapping is fixed by rule: known_transform=MODEL(known_transform)+PROOF+TOOL; bounded_coding=TRANSFORM family(by phase)+PROOF+TOOL; "
        "novel=MODEL(novel)+PROOF+TOOL; owner_reality=OWNER+OBSERVATION. The budget's class labels are inherited, not re-judged.",
        "Family key = phase (code surface shared inside a phase); success-criterion claims (p*/vis*) carry their own proof id, matrix rows share one proof per phase.",
        "known_transform is modelled as a MODEL obligation (one transform pass per claim): the budget JSON gives no transform family for these rows; "
        "each could collapse into a family if the Owner confirms (UNKNOWN, not assumed).",
        "Observations come from inputs/dws-reality-obs.json (U4, hand-derived from ROADMAP phase 25); no other claim has an observation obligation (UNKNOWN whether rows 17..76 need Owner-visible evidence).",
        "owner_reality claims are zero-token in cost_to_completion; their automated captures are priced separately as 'uncovered observations' (see budget).",
        "TOOL obligation 'evidence-stamp' (matrix/evidence record by script) is assumed NO_COMPUTE for every open claim; no tool exists yet for it in DWS (UNKNOWN).",
        "No obligation is reused as NO_WORK: no proof in the DWS tree is valid with a measured invalidator at compile time, so NO_WORK = 0.",
        "46 sleeping claims (parked by the budget compile, phases not unblocked) carry no obligations and are NOT priced (UNKNOWN cost).",
    ]
    return claims, J


def strip_cat(claims, cats=None):
    out = []
    for c in claims:
        c = dict(c)
        if "obligations" in c:
            ob = [{k: v for k, v in o.items() if k != "cat"} for o in c["obligations"] if cats is None or o["cat"] in cats]
            if not ob:
                continue
            c["obligations"] = ob
        out.append(c)
    return out


def compile_doc(claims, *, calls, ctx, floor, cats=None, label="new architecture", hist_calls=None):
    doc = {"claims": strip_cat(claims, cats), "worker_floor": floor, "label": label,
           "profiles": {k: {"calls": calls[k], "ctx_tokens": ctx} for k in ctx_classes()}}
    if hist_calls:
        doc["historical_calls"] = hist_calls
    return ctc.compile_cost(doc, ra.load_floors(None))


def ctx_classes():
    return ctc.MODEL_CLASSES


# ---------------------------------------------------------------- compile
def compile_all(now_iso: str | None = None) -> dict:
    budget = json.loads((A / "inputs/dws-budget-compiled.json").read_text())
    obsdoc = json.loads((A / "inputs/dws-reality-obs.json").read_text())
    rows = load_matrix()
    head, dws_status = dws_head()
    claims, J = build_claims(budget, obsdoc, rows)

    # (a) historical profile: reproduces the old runnable number
    hist_doc = {"label": "historical", "worker_floor": 110835,
                "claims": [{k: c[k] for k in ("id", "class", "status", "est_calls") if k in c}
                           for c in budget["claims"] if c["class"] != "deterministic"],
                "actuals": {k: {"calls": 1, "ctx_tokens": budget["measured"]["ctx_per_call"]} for k in ctc.MODEL_CLASSES}}
    hist = ctc.compile_cost(hist_doc, ra.load_floors(None))
    hist["HISTORICAL_PROFILE_FLAG"] = "HISTORICAL_PROFILE"

    by = cf.load(A / "data/calls.jsonl.gz")
    s_hi = {"2500": ctx_stats(by, 2500), "10000": ctx_stats(by, 10000)}
    rep = {n: (t, c) for n, t, c, _ in json.loads((A / "data/counterfactual.json").read_text())["rows"]}
    f_tokens, f_calls = rep["f a+b20+c+d+e"]
    a_tokens, a_calls = rep["actual"]
    call_ratio = f_calls / a_calls
    open_c = [c for c in budget["claims"] if c["class"] in ("known_transform", "bounded_coding", "novel")]
    H = {}
    for k in ctc.MODEL_CLASSES:
        xs = [c["est_calls"] for c in open_c if c["class"] == k]
        H[k] = max(1, round(sum(xs) / len(xs) * call_ratio))
    L = {k: ctc.PRIORS[k]["calls"] for k in ctc.MODEL_CLASSES}
    E = {k: max(L[k], round(math.sqrt(L[k] * H[k]))) for k in ctc.MODEL_CLASSES}
    floor = cf.SLIM
    scen_def = {
        "lower": (L, s_hi["2500"]["p50"]), "expected": (E, s_hi["2500"]["mean"]),
        "p90": (H, s_hi["2500"]["p90"]), "ceiling": (H, s_hi["10000"]["p90"]),
    }
    price_known = lambda calls, ctx: calls["known_transform"] * max(ctx, floor)  # noqa: E731
    phases = sorted({c["phases"][0] for c in claims if c.get("phases") and c.get("obligations")})
    priced_obs = {o["observation"] for c in claims for o in c.get("obligations", [])
                  if o["satisfier"] == "OBSERVATION" and c["class"] != "owner_reality"}
    zero_obs = {o["observation"] for c in claims for o in c.get("obligations", [])
                if o["satisfier"] == "OBSERVATION" and c["class"] == "owner_reality"} - priced_obs
    lbdoc = None
    scen = {}
    for name, (calls, ctx) in scen_def.items():
        cat_tok = {}
        full = compile_doc(claims, calls=calls, ctx=ctx, floor=floor, hist_calls=hist["candidate"]["calls"])
        key = "ceiling" if name == "ceiling" else "candidate"
        tot = full["ceiling"]["tokens"] if name == "ceiling" else full["candidate"]["tokens"]
        for cat in ("known_transform", "family", "novel", "visual", "proof", "reality"):
            r = compile_doc(claims, calls=calls, ctx=ctx, floor=floor, cats={cat})
            cat_tok[cat] = r["ceiling"]["tokens"] if name == "ceiling" else r["candidate"]["tokens"]
        assert sum(cat_tok.values()) == tot, (name, cat_tok, tot)
        unc = len(zero_obs) * price_known(calls, ctx)
        cat_tok["reality"] += unc
        cat_tok["closeout"] = len(phases) * price_known(calls, ctx)
        sub = sum(cat_tok.values())
        if name in ("p90", "ceiling"):
            for k in cat_tok:
                cat_tok[k] = math.ceil(cat_tok[k] * (1 + ra.DEFAULT_GROWTH_MARGIN))
            sub = sum(cat_tok.values())
        cat_tok["recovery"] = math.ceil(sub * RECOVERY_SHARE[name])
        scen[name] = {"calls": calls, "ctx": ctx, "cats": cat_tok, "total": sum(cat_tok.values()),
                      "tool_total": tot, "HISTORICAL_PROFILE": full.get("HISTORICAL_PROFILE"),
                      "profile_source": full["profile_source"], "tool_calls": full["candidate"]["calls"]}
        if name == "expected":
            lbdoc = full["semantic"]
    keys = ["lower", "expected", "p90", "ceiling"]
    for a, b in zip(keys, keys[1:]):
        assert scen[a]["total"] <= scen[b]["total"], (a, b)
    for k in keys:
        refuse_percentage_of_historical(scen[k]["total"])
    sem = lbdoc
    return {"now": now_iso or datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "head": head, "dws_status": dws_status, "rows": rows, "budget": budget, "claims": claims, "J": J,
            "hist": hist, "ctx": s_hi, "H": H, "L": L, "E": E, "scen": scen, "sem": sem, "phases": phases,
            "zero_obs": sorted(zero_obs), "priced_obs": sorted(priced_obs), "f": (f_tokens, f_calls), "a": (a_tokens, a_calls),
            "obsdoc": obsdoc}


# ---------------------------------------------------------------- render
def n(x):
    return f"{int(x):,}"


def usd(model_tokens: dict, pricing: dict, rate: float | None):
    tot = 0.0
    for m, t in model_tokens.items():
        tot += t / 1e6 * (rate if rate is not None else pricing["models"][m]["cache_read"])
    return tot


def render(R: dict, goal_status: dict, ledger_counts: dict) -> str:
    import collections
    b, hist, sc, sem = R["budget"], R["hist"], R["scen"], R["sem"]
    rows = R["rows"]
    st = collections.Counter(r["state"] for r in rows)
    cc = collections.Counter(c["class"] for c in b["claims"])
    oc = sem["obligation_counts"]
    lb = sem["irreducible_lower_bound"]
    pr = json.loads(PRICING.read_text())
    rate = b["measured"]["usd_per_mtok_processed"]
    L = []
    S = lambda t: L.extend(["", f"## {t}", ""])  # noqa: E731
    src_budget = "src: inputs/dws-budget-compiled.json"
    src_ctc = "src: tools/cost_to_completion.compile_cost on A/dws-claims-semantic.json"
    L += ["# DWS-BUDGET-FINAL (ce-a5 U10)", "", "READ-ONLY recompilation: no DWS product work executed. Every figure carries a `[src: ...]` tag; UNKNOWN is never 0."]
    S("Compilation time")
    L.append(f"- Compiled at {R['now']} [src: system clock at tools/a5_u10_budget.py run]")
    L.append(f"- Work tree branch ce/a5, goal ce-a5 cap {n(goal_status['cap'])} tokens [src: mission_spend goal-status]")
    S("DWS HEAD and worktree")
    L.append(f"- HEAD {R['head'][:9]} (expected {HEAD_EXPECT}): {'MATCH' if R['head'].startswith(HEAD_EXPECT) else 'MISMATCH'} [src: git -C D/orca-dws log -1]")
    L.append(f"- Worktree status: `{R['dws_status'] or 'clean'}` (untracked .planning/ is git-excluded by design) [src: git -C D/orca-dws status --short]")
    S("Scope")
    L.append(f"- Priced: {len([c for c in R['claims'] if c.get('obligations')])} open claims with obligations; parked and not priced: {cc['sleeping']} sleeping claims (UNKNOWN cost) [{src_budget}]")
    L.append(f"- Owner-only (zero model tokens): {cc['owner_reality']} claims; deterministic: {cc['deterministic']} [{src_budget}]")
    L.append("- Not in scope: executing any DWS claim, the sleeping claims' own pricing, quota measurement [src: packet U10]")
    S("Counts")
    L.append(f"- Matrix rows {len(rows)}: PASS {st['PASS']}, PARTIAL {st['PARTIAL']}, ABSENT {st['ABSENT']}, UNKNOWN {st['UNKNOWN']} [src: D/orca-dws/config/dws-completion-matrix.jsonc]")
    L.append(f"- DONE {st['PASS']} (matrix PASS rows, not in claim list) [src: matrix state field]")
    L.append(f"- NO_WORK {oc.get('NO_WORK', 0)} obligations (no valid reusable proof with a measured invalidator) [{src_ctc}]")
    L.append(f"- NO_COMPUTE {oc.get('NO_COMPUTE', 0)} obligations (script-only evidence stamp) [{src_ctc}]")
    L.append(f"- DETERMINISTIC {cc['deterministic']} claim (vis-pixel-gate) [{src_budget}]")
    L.append(f"- KNOWN_TRANSFORM {cc['known_transform']} claims [{src_budget}]")
    L.append(f"- BOUNDED_FAMILY {cc['bounded_coding']} claims -> {oc.get('FAMILY', 0)} family obligations [{src_ctc}]")
    L.append(f"- NOVEL {cc['novel']} claims (of which visual {sum(1 for c in R['claims'] if c['id'].startswith('vis-') and c['class']=='novel')}) [{src_budget}]")
    L.append(f"- REALITY {len(R['priced_obs']) + len(R['zero_obs'])} distinct observations over {len(R['obsdoc']['claims'])} claims [src: inputs/dws-reality-obs.json]")
    L.append(f"- OWNER_ONLY {cc['owner_reality']} claims (row-46, p25-sc4-physical-pcs) [{src_budget}]")
    L.append(f"- SLEEPING/BLOCKED {cc['sleeping']} claims [{src_budget}]")
    S("Old-architecture baseline")
    L.append(f"- Runnable candidate {n(b['runnable']['candidate']['tokens'])} tokens over {n(b['runnable']['candidate']['calls'])} calls; with margin {n(b['runnable']['candidate']['with_margin'])}; ceiling {n(b['runnable']['ceiling']['tokens'])} [{src_budget}]")
    L.append(f"- Reproduced by the extended cost_to_completion: {n(hist['candidate']['tokens'])} tokens, flag HISTORICAL_PROFILE [{src_ctc}; historical doc in tools/a5_u10_budget.py]")
    L.append(f"- Unblocked (all {cc['sleeping']} sleeping included) {n(b['unblocked']['candidate']['tokens'])} tokens [{src_budget}]")
    L.append(f"- Measured history: {n(b['measured']['productive_calls'])} calls, {n(b['measured']['processed_tokens'])} processed tokens for {b['measured']['steps_gained']} steps = {b['measured']['calls_per_step']} calls/step, ctx {n(b['measured']['ctx_per_call'])}/call [{src_budget}]")
    S("New irreducible lower bound")
    L.append(f"- {lb['total']} irreducible items = {lb['novel_decisions']} decisions + {lb['observations']} distinct observations + {lb['assurance_judgments']} assurance judgments + {lb['owner_decisions']} owner decisions (kind: {lb['kind']}) [{src_ctc}]")
    L.append(f"- Token floor if each item cost one call at the slim floor: {n(lb['total'] * cf.SLIM)} tokens ESTIMATE ({lb['total']} x {n(cf.SLIM)}) [src: lb above x tools/a5_counterfactual.SLIM]")
    L.append(f"- Overhead multiplier input: {sem['overhead_multiplier_input']:.1f} (historical {n(hist['candidate']['calls'])} calls / {lb['total']} items) [{src_ctc}]")
    L.append("- This closes the U0 ledger UNKNOWN rows P1-63 / P1-64 (DWS lower-bound number), as an estimate [src: A/U0-receipt.md]")
    S("New execution profile")
    L.append(f"- Floor per call {n(cf.SLIM)} (slim), rotation every 20 calls with a {n(cf.CAPSULE)}-token capsule, STATE card, read-once, poll->event, stall K=14 [src: A/COUNTERFACTUAL.md, A/STALL.md, A/PROJECTION.md]")
    L.append(f"- Replay of policy f: {n(R['f'][0])} processed tokens, {n(R['f'][1])} calls vs actual {n(R['a'][0])}, {n(R['a'][1])} [src: A/COUNTERFACTUAL.md]")
    for k, s in R["ctx"].items():
        L.append(f"- ctx per call under f, capsule {k}: n {n(s['n'])}, mean {n(s['mean'])}, p50 {n(s['p50'])}, p90 {n(s['p90'])} [src: replay of A/data/calls.jsonl.gz by tools/a5_u10_budget.ctx_stats]")
    L.append(f"- Calls per obligation (lower / expected / p90-ceiling): known_transform {R['L']['known_transform']}/{R['E']['known_transform']}/{R['H']['known_transform']}, bounded_coding {R['L']['bounded_coding']}/{R['E']['bounded_coding']}/{R['H']['bounded_coding']}, novel {R['L']['novel']}/{R['E']['novel']}/{R['H']['novel']} [src: lower = cost_to_completion PRIORS (chosen, not measured); p90 = mean budget est_calls per class x f call ratio {R['f'][1]}/{R['a'][1]}; expected = geometric mean]")
    L.append(f"- New-grammar flag HISTORICAL_PROFILE = {sc['expected']['HISTORICAL_PROFILE']} (all three model classes priced from `profiles`) [{src_ctc}]")
    S("Token budget")
    L.append("Processed tokens (ctx-sum currency of the trace corpus; output tokens excluded), by component.")
    L.append("")
    L.append("| component | lower | expected | P90 | hard ceiling | source [src: Token budget] |")
    L.append("|---|---|---|---|---|---|")
    names = {"known_transform": "known-transform", "family": "family", "novel": "novel", "visual": "visual", "proof": "proof",
             "reality": "reality", "closeout": "closeout", "recovery": "recovery"}
    for c in CATS:
        L.append(f"| {names[c]} | " + " | ".join(n(sc[k]["cats"][c]) for k in ("lower", "expected", "p90", "ceiling")) + f" | [src: compile_cost subset by obligation category] |")
    L.append("| **TOTAL** | " + " | ".join(n(sc[k]["total"]) for k in ("lower", "expected", "p90", "ceiling")) + " | [src: sum of components] |")
    L.append("")
    L.append(f"- Scenarios: lower = prior calls x p50 ctx; expected = geometric-mean calls x mean ctx; P90 = historical-per-class calls x p90 ctx x {1 + ra.DEFAULT_GROWTH_MARGIN:.1f} margin; ceiling = P90 calls x p90 ctx at capsule 10,000 x same margin with novel deopt x{ctc.DEFAULT_DEOPT_FACTOR:.0f} [src: tools/a5_u10_budget.compile_all]")
    L.append(f"- Closeout = {len(R['phases'])} phases touched x one known_transform pass; recovery = {RECOVERY_SHARE['expected']:.3f} / {RECOVERY_SHARE['p90']:.3f} / {RECOVERY_SHARE['ceiling']:.3f} of the subtotal (expected/P90/ceiling), 0 in lower; {RECOVERY_SHARE['expected']:.3f} = historical RECOVERY label share [src: A/TRACE-REPORT.md section 1; multiples are chosen]")
    L.append(f"- Uncovered observations priced as one known_transform pass each: {', '.join(R['zero_obs']) or 'none'} ({len(R['zero_obs'])}) [src: tools/a5_u10_budget; reachable only via owner_reality claims]")
    S("Model routing shares")
    routed = {}
    for k in ("expected",):
        for c in CATS:
            routed[ROUTE[c]] = routed.get(ROUTE[c], 0) + sc[k]["cats"][c]
    tot = sc["expected"]["total"]
    for m, t in sorted(routed.items()):
        L.append(f"- {m}: {n(t)} expected tokens = {t / tot * 100:.1f}% [src: routing assumption by category (judgment) x A/dws-claims-semantic.json]")
    L.append("- Routing is an assumption: sonnet for transforms/proof/reality/closeout/recovery, opus for novel and visual decisions [src: judgment, no measured routing outcome]")
    S("USD")
    floor_usd = {k: usd({ROUTE[c]: sc[k]["cats"][c] for c in CATS} if False else _route_tokens(sc[k]), pr, None) for k in sc}
    blend_usd = {k: sc[k]["total"] / 1e6 * rate for k in sc}
    L.append("| scenario | cache-read floor USD | measured blended USD | source |")
    L.append("|---|---|---|---|")
    for k in ("lower", "expected", "p90", "ceiling"):
        L.append(f"| {k} | {floor_usd[k]:,.0f} | {blend_usd[k]:,.0f} | [src: {PRICING.name} cache_read by routed model; blended = tokens x {rate} USD/Mtok from inputs/dws-budget-compiled.json] |")
    L.append(f"- Old runnable candidate USD {n(b['usd']['runnable']['candidate'])}, with margin {n(b['usd']['runnable']['with_margin'])}, ceiling {n(b['usd']['runnable']['ceiling'])} [{src_budget}]")
    L.append("- Cache-read floor excludes cache writes (rotation re-writes the capsule each segment) and output tokens, so it understates; blended rate comes from the historical mix and may not transfer [src: pricing file notes; judgment]")
    S("Quota reality")
    L.append("- Subscription quota consumed by this budget: UNKNOWN (never measured in this mission) [src: no measurement exists]")
    L.append(f"- Goal ledger so far: used {n(goal_status['used'])}, settled {n(goal_status['settled'])}, open hold {n(goal_status['open'])}, remaining {n(goal_status['remaining'])} of cap {n(goal_status['cap'])} [src: mission_spend goal-status --goal ce-a5]")
    S("Confidence")
    L.append("- LOW overall. Token ctx per call is a replay of measured traces (LOW-MED); calls per obligation are NOT measured (priors vs historical bracket); the 46 sleeping claims are unpriced [src: A/COUNTERFACTUAL.md confidence column; this document]")
    L.append(f"- Spread expected->P90 {sc['p90']['total'] / sc['expected']['total']:.1f}x and P90->ceiling {sc['ceiling']['total'] / sc['p90']['total']:.1f}x [src: Token budget table]")
    S("Assumptions")
    for a in ["A1-A11 of the counterfactual replay hold (ctx-only currency, growth independent of policy, capsule 2,500, no event wake cost) [src: A/COUNTERFACTUAL.md]",
              "Calls per obligation lie between cost_to_completion PRIORS and the historical per-class calls scaled by the f call ratio [src: tools/a5_u10_budget.compile_all]",
              "Claim classes (known/bounded/novel) are inherited from the old compile and not re-judged [src: inputs/dws-budget-compiled.json]",
              "Observation set and Owner minutes from U4 are hand-derived estimates [src: A/REALITY-PLAN.md]",
              "Stall trip K=14 and resource admission are guards, not savings: K=15 cuts 1.79% of corpus tokens and is not counted [src: A/STALL.md]",
              "Judgment calls on obligations are listed in A/dws-claims-semantic.json under `judgments` [src: A/dws-claims-semantic.json]"]:
        L.append(f"- {a}")
    S("Top uncertainties")
    for a in ["Rotation capsule fidelity and re-derivation after rotation are not modelled; this alone moves the replay from -46% to -39% on rotate N=40 vs 12 [src: A/COUNTERFACTUAL.md rows b1-b3]",
              "Calls per obligation: expected vs P90 differ by the call bracket above; no worker has run the new grammar [src: Token budget table]",
              "46 sleeping claims unpriced; the old unblocked scope was " + n(b['unblocked']['candidate']['tokens']) + " tokens [src: inputs/dws-budget-compiled.json]",
              "Real worker replay on the STATE card never run (static fault check only: 0 FAULT of 119 reads) [src: A/PROJECTION.md]",
              "Owner session minutes (55 single-sitting) assume all PCs and phone available together [src: A/REALITY-PLAN.md]",
              "Two live-dispatcher guard tests fail outside scope (V-SBG-WIRED, V-SBG-E2E) [src: A/U7-receipt.md]"]:
        L.append(f"- {a}")
    S("Savings vs old")
    old_c, new_e = b["runnable"]["candidate"]["tokens"], sc["expected"]["total"]
    L.append(f"- Old runnable candidate {n(old_c)} vs new expected {n(new_e)}, new P90 {n(sc['p90']['total'])}, new ceiling {n(sc['ceiling']['total'])} tokens: two independent compiles, not a percentage of the old [src: Old-architecture baseline; Token budget table]")
    L.append(f"- Even the new hard ceiling is {'below' if sc['ceiling']['total'] < old_c else 'ABOVE'} the old runnable candidate [src: comparison of the two figures above]")
    L.append(f"- Difference old - new expected = {n(old_c - new_e)} tokens [src: arithmetic on the two compiled figures]")
    S("Extinguished")
    L.append(f"- Work: {oc.get('NO_COMPUTE', 0)} evidence stamps become scripts; {cc['deterministic']} pixel gate is a script; read-once and poll->event remove calls ({n(R['a'][1])} -> {n(R['f'][1])} replay calls) [src: A/COUNTERFACTUAL.md; {src_ctc}]")
    L.append(f"- Boundaries: reality acquisitions 35 -> {len(R['priced_obs']) + len(R['zero_obs'])} distinct observations; sessions 11 -> 1 [src: A/REALITY-PLAN.md totals]")
    L.append(f"- Context: floor {n(b['runnable']['worker_floor'])} -> {n(cf.SLIM)} per call; mean ctx per call {n(b['measured']['ctx_per_call'])} -> {n(R['ctx']['2500']['mean'])} [src: {src_budget}; replay ctx_stats]")
    L.append(f"- Proof: {oc.get('SHARED_PROOF', 0)} proof obligations share {len({o['proof'] for c in R['claims'] for o in c.get('obligations', []) if o['satisfier'] == 'PROOF'})} distinct proofs [{src_ctc}]")
    L.append("- Owner work: 220 min per-claim -> 55 min one session (165 saved, ESTIMATE) [src: A/REALITY-PLAN.md]")
    S("OLD vs NEW")
    L.append("| dimension | OLD | NEW | source |")
    L.append("|---|---|---|---|")
    L.append(f"| runnable tokens | {n(old_c)} | expected {n(new_e)} (ceiling {n(sc['ceiling']['total'])}) | [src: budget JSON; this file] |")
    L.append(f"| calls | {n(b['runnable']['candidate']['calls'])} | expected {n(sc['expected']['tool_calls'])} priced obligation calls | [src: budget JSON; compile_cost] |")
    L.append(f"| ctx per call | {n(b['measured']['ctx_per_call'])} | {n(R['ctx']['2500']['mean'])} | [src: budget JSON; replay] |")
    L.append(f"| first-call floor | {n(b['runnable']['worker_floor'])} | {n(cf.SLIM)} | [src: budget JSON; counterfactual SLIM] |")
    L.append(f"| unit of cost | claim x phase-sized est_calls | obligation x class calls | [src: tools/cost_to_completion.py] |")
    L.append(f"| runnable USD (blended) | {n(b['usd']['runnable']['candidate'])} | {blend_usd['expected']:,.0f} | [src: budget JSON; USD table] |")
    L.append(f"| Owner minutes | 220 | 55 | [src: A/REALITY-PLAN.md] |")
    L.append(f"| stall trip K | 25 | 14 | [src: A/STALL.md] |")
    S("Meta-analysis")
    L.append("**What caused 424 calls/step?** [src: A/U1-receipt.md]")
    L.append(f"- The figure is {n(b['measured']['productive_calls'])} calls / {b['measured']['steps_gained']} steps = {b['measured']['calls_per_step']} [{src_budget}]; the mission's own step definition (rows whose state changed) gives 269.7 calls/change [src: A/U1-receipt.md]. Context share by label: NOVELTY 38.4%, MUTATION 22.3%, PROOF 10.5%, RECOVERY 9.8%, CONTROL_LOOP 7.1%, REDISCOVERY 5.4%, STATE_READ 5.2% (proxy labels) [src: A/U1-receipt.md]. The first-call floor alone is 36.2% of processed tokens and subagents carry 87.1% [src: A/U1-receipt.md]. Call count per step is not reduced much by any policy (10,985 -> 9,780 calls); the saving is per-call context [src: A/COUNTERFACTUAL.md].")
    L.append("**Global vs DWS-local?**")
    L.append("- Global (PROMOTABLE): slim floor, rotation, combined f (gains 42.4/36.6/75.7% on the CE holdout and 30.5/57.1/85.8% on ql-quickie). DWS-local: read-once, STATE projection, poll->event [src: A/HOLDOUT.md].")
    L.append("**Rejected as negative ROI?**")
    L.append(f"- {ledger_counts.get('NEGATIVE_ROI', 0)} ledger rows dispositioned NEGATIVE_ROI (e.g. P1-19 tool schemas as memory, P2-11 cross-project computation market, P2-13 shadow price of uncertainty) [src: A/LEDGER.json]; no replay policy fell below 3% so none was dropped by the counterfactual [src: A/U2-receipt.md]. Tool-schema share of the floor is UNKNOWN [src: A/COUNTERFACTUAL.md].")
    L.append("**Largest remaining debt?**")
    L.append(f"- Unmeasured calls per obligation (the P90/expected spread is {sc['p90']['total'] / sc['expected']['total']:.1f}x), then rotation capsule fidelity, then the {cc['sleeping']} unpriced sleeping claims, then the Owner reality session (55 min) [src: Token budget table; A/COUNTERFACTUAL.md; A/REALITY-PLAN.md].")
    L.append("**Could another bounded pass have positive NPV?**")
    spread = sc['p90']['total'] - sc['expected']['total']
    L.append(f"- A pass costs at most the unit cap of 1,000,000 tokens [src: packet U10]; the expected-to-P90 gap is {n(spread)} tokens [src: Token budget table]. A single instrumented DWS obligation run (real calls per obligation, capsule fidelity) would shrink that gap, so a bounded measurement pass is plausibly positive NPV; a further paper compile is not (no new information) [src: judgment]. This is the OPTIMIZE FURTHER case; approving execution without it spends against LOW confidence.")
    S("Universal iteration pass")
    L.append("Applied once (inputs/iteracion-avanzada-universal.txt).")
    L.append("- REALITY CHECK. Source read: packet U10 lines 1-31, A/U*-receipt.md, inputs/dws-budget-compiled.json, D/orca-dws matrix. Exact error: the Owner's mission text 'FINAL DWS TOKEN BUDGET OUTPUT' is not in the work tree (grep over vault/ and tools/ finds only the packet). Premise false: yes - the section order is taken from the packet's list [src: grep of W].")
    L.append("- CLASE 2: the plan assumed a mission text on disk; it was not. Fix: use the packet's enumerated order, record the deviation in the receipt [src: grep of W].")
    L.append("- CLASE 5 guard: DONE is claimed only with the test output pasted in the receipt (A5_U10_PASS). No placeholder remains; UNKNOWN is stated where unmeasured [src: tools/test_a5_u10.py].")
    L.append("- UKDL seed: PR-CE-A5-001 'budget text is only as good as its unmeasured call count: price calls per obligation before approving' [src: this pass].")
    L += ["", *DECISION]
    return "\n".join(L) + "\n"


def _route_tokens(s):
    t = {}
    for c in CATS:
        t[ROUTE[c]] = t.get(ROUTE[c], 0) + s["cats"][c]
    return t


def missing_sources(md: str) -> list[str]:
    """Lines with a digit but no `[src:` tag (headings, the fixed decision lines and table rules excluded)."""
    bad = []
    for ln in md.splitlines():
        if not ln.strip() or ln.startswith("#") or ln.strip() in DECISION or set(ln.strip()) <= set("|-: "):
            continue
        if re.search(r"\d", ln) and "[src:" not in ln and "src:" not in ln:
            bad.append(ln)
    return bad


def sections_ok(md: str) -> list[str]:
    heads = re.findall(r"^## (.+)$", md, flags=re.M)
    idx, miss = -1, []
    for s in SECTIONS:
        try:
            i = heads.index(s)
        except ValueError:
            miss.append(s)
            continue
        if i < idx:
            miss.append(f"order:{s}")
        idx = i
    return miss


def goal_status() -> dict:
    import os
    env = dict(os.environ, GSD_LONG_RUN_STATE_DIR="/home/kobii/ce5-env/state")
    r = subprocess.run(["python3", "/home/kobii/ce5-env/pp/tools/mission_spend.py", "goal-status", "--goal", "ce-a5"],
                       capture_output=True, text=True, env=env)
    return json.loads(r.stdout)


def main(outdir: str | None = None) -> int:
    out = Path(outdir) if outdir else A
    R = compile_all()
    led = json.loads((A / "LEDGER.json").read_text())["counts"]
    gs = goal_status()
    claims_doc = {"schema": "dws-claims-semantic/1", "dws_head": R["head"], "compiled_at": R["now"],
                  "worker_floor": cf.SLIM, "label": "new architecture", "claims": R["claims"], "judgments": R["J"],
                  "profiles": {"lower": {k: {"calls": R["L"][k]} for k in R["L"]},
                               "expected": {k: {"calls": R["E"][k]} for k in R["E"]},
                               "p90": {k: {"calls": R["H"][k]} for k in R["H"]}}}
    (out / "dws-claims-semantic.json").write_text(json.dumps(claims_doc, indent=1, ensure_ascii=False) + "\n")
    md = render(R, gs, led)
    (out / "DWS-BUDGET-FINAL.md").write_text(md)
    print(json.dumps({k: R["scen"][k]["total"] for k in R["scen"]}), "hist", R["hist"]["candidate"]["tokens"])
    print("missing_sections", sections_ok(md), "missing_src", len(missing_sources(md)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
