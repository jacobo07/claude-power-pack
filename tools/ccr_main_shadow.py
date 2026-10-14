"""CCR v4 A7: offline shadow of the Work Unit closure over interactive main sessions, and the main-lean alternative.

For every session whose start receipt says interactive with no Work Unit, the main-loop attach receipts give the
bytes unit closure would drop per attachment type (skill_listing, agent_listing_delta, mcp_instructions_delta) and
the bytes it would replace (instructions -> kernel + index, at most KERNEL_CHARS). The session's usage projection then
says which dropped capability the main loop used AFTER the first dropped listing: a Skill, Agent or mcp__ tool_use
there is a regression risk under drop. Under main-lean (name-only listings) the names stay, so the same use is a
discoverability risk only.

    python tools/ccr_main_shadow.py <pack-dir> [--json]

Receipts and projections are content-free; name-only bytes are bytes x the ratio measured on real listing text
(LEAN_RATIO). Tokens are chars x TOK_PER_CHAR, an assumption (chars/4), not a fit.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

DROPPED = ("skill_listing", "agent_listing_delta", "mcp_instructions_delta")
REPLACED = "instructions"
KERNEL_CHARS = 8000  # mods/cpp-cognitive-runtime/hooks/policy.ts
# decideMainLeanAttachment output / input, run 2026-10-14 on real listing text of the GEX44 estate (transcript d5e49ddf,
# 2.1.296), page hint included: skills 7,778/29,998 (314/314 names kept), agents 1,521/26,065 (70/70), mcp 197/1,893.
LEAN_RATIO = {"skill_listing": 0.259, "agent_listing_delta": 0.058, "mcp_instructions_delta": 0.104}
TOK_PER_CHAR = 0.25  # assumption: chars/4
CAP = {"skill_listing": "skill", "agent_listing_delta": "agent", "mcp_instructions_delta": "mcp"}


def _rows(path: Path) -> list[dict]:
    out = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                out.append(json.loads(line))
            except ValueError:
                continue  # a torn last line of a live receipt
    return out


def capability_uses(projection: Path) -> dict:
    """Main-loop calls, processed tokens, and Skill/Agent/MCP tool_use names after the first dropped listing."""
    seen = False
    calls: set = set()
    processed = 0
    uses: dict[str, Counter] = {"skill": Counter(), "agent": Counter(), "mcp": Counter()}
    for r in _rows(projection):
        if r.get("sidechain"):
            continue  # subagent rows: the subagent policy governs them
        if r.get("t") == "attachment" and r.get("att") in DROPPED:
            seen = True
        if r.get("t") != "assistant":
            continue
        key = r.get("mid") or r.get("rid")
        if key and key not in calls:
            calls.add(key)  # one API call can span several assistant rows; its usage is counted once
            u = r.get("usage") or {}
            processed += sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
        if not seen:
            continue
        for b in r.get("blocks") or []:
            if b.get("k") != "tool_use":
                continue
            n = b.get("name") or ""
            if n == "Skill":
                uses["skill"][b.get("skill") or "?"] += 1
            elif n in ("Agent", "Task"):
                uses["agent"][b.get("subagent_type") or "?"] += 1
            elif n.startswith("mcp__"):
                uses["mcp"][n] += 1
    return {"listing_seen": seen, "calls": len(calls), "processed": processed, "uses": {k: dict(v) for k, v in uses.items()}}


def shadow(pack: Path) -> dict:
    sessions = []
    for f in sorted(pack.glob("receipts/*/*.jsonl")):
        rows = _rows(f)
        st = next((r for r in rows if r.get("ev") == "start"), None)
        if not st or not st.get("interactive") or st.get("unit"):
            continue
        att: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for r in rows:
            if r.get("ev") == "attach" and r.get("agent") is None and r.get("type") in DROPPED + (REPLACED,):
                att[r["type"]][0] += 1
                att[r["type"]][1] += int(r.get("bytes") or 0)
        proj = pack / "sessions" / f"{f.stem}.jsonl"
        sessions.append({"sid": f.stem, "repoKey": f.parent.name, "attach": dict(att),
                         "cap": capability_uses(proj) if proj.exists() else None})
    return {"sessions": sessions, "table": table(sessions)}


def table(sessions: list[dict]) -> dict:
    t: dict[str, dict] = {}
    for typ in DROPPED + (REPLACED,):
        n = b = s = 0
        rides = 0.0  # lean-saved chars x main-loop calls they ride (mean event size; sessions with a projection)
        for x in sessions:
            c, by = x["attach"].get(typ, (0, 0))
            n += c
            b += by
            s += 1 if c else 0
            if c and x["cap"] and typ in LEAN_RATIO:
                rides += by / c * (1 - LEAN_RATIO[typ]) * x["cap"]["calls"]
        t[typ] = {"sessions": s, "events": n, "bytes": b,
                  "drop_saves": b if typ != REPLACED else None,
                  "replace_saves_min": max(0, b - n * KERNEL_CHARS) if typ == REPLACED else None,
                  "lean_saves": round(b * (1 - LEAN_RATIO[typ])) if typ in LEAN_RATIO else None,
                  "lean_processed_tok": round(rides * TOK_PER_CHAR) if typ in LEAN_RATIO else None}
    with_proj = [x for x in sessions if x["cap"]]
    risk = {k: Counter() for k in ("skill", "agent", "mcp")}
    risk_sessions = {k: 0 for k in risk}
    for x in with_proj:
        for k in risk:
            u = x["cap"]["uses"][k]
            risk[k].update(u)
            risk_sessions[k] += 1 if u else 0
    return {"sessions": len(sessions), "with_projection": len(with_proj), "types": t,
            "listed_with_projection": sum(1 for x in with_proj if any(x["attach"].get(k) for k in DROPPED)),
            "risk_sessions_any": sum(1 for x in with_proj if any(x["cap"]["uses"][k] for k in risk)),
            "processed": sum(x["cap"]["processed"] for x in with_proj),
            "risk_uses": {k: sum(v.values()) for k, v in risk.items()}, "risk_sessions": risk_sessions,
            "risk_top": {k: v.most_common(8) for k, v in risk.items()}}


def render(t: dict) -> str:
    lines = [f"interactive main sessions: {t['sessions']} ({t['with_projection']} with a usage projection, "
             f"{t['listed_with_projection']} of those with listing receipts); main-loop processed {t['processed']:,}", "",
             "| attachment | sessions | events | bytes | unit closure | main-lean saves (bytes) | main-lean est. processed tok | later uses (sessions) |",
             "|---|---:|---:|---:|---|---:|---:|---|"]
    for typ, v in t["types"].items():
        uc = f"drop {v['drop_saves']:,}" if v["drop_saves"] is not None else f"replace, saves >= {v['replace_saves_min']:,}"
        lean = f"{v['lean_saves']:,}" if v["lean_saves"] is not None else "kept"
        tok = f"{v['lean_processed_tok']:,}" if v["lean_processed_tok"] is not None else "-"
        k = CAP.get(typ)
        used = f"{t['risk_uses'][k]} ({t['risk_sessions'][k]})" if k else "n/a"
        lines.append(f"| {typ} | {v['sessions']} | {v['events']} | {v['bytes']:,} | {uc} | {lean} | {tok} | {used} |")
    lines.append(f"\nsessions with any later Skill/Agent/MCP use (regression risk under drop): {t['risk_sessions_any']}")
    return "\n".join(lines)


def _first_ctx(rows: list[dict]) -> int | None:
    return next((int(r["ctx"]) for r in rows if r.get("ev") == "call" and r.get("agent") is None and r.get("call") == 1), None)


def canary_report(receipts: Path) -> dict:
    """Main-lean canary sessions (start receipt canary != off) against the interactive sessions without it, same root.

    Predicted first-call saving = chars the canary withheld at the first call x TOK_PER_CHAR. Measured = the median
    first-call ctx of the baseline minus the canary session's (different prompts and estates move it too: n is small).
    Receipts are content-free: a capability failure shows here only as a page fault or a spawn; the Owner's account is
    the other half of the read.
    """
    canary, base = [], []
    for f in sorted(receipts.glob("*/*.jsonl")):
        rows = _rows(f)
        st = next((r for r in rows if r.get("ev") == "start"), None)
        if not st or not st.get("interactive") or st.get("unit"):
            continue
        if st.get("canary") in ("enforce", "shadow"):
            att = [r for r in rows if r.get("ev") == "attach" and r.get("canary")]
            canary.append({
                "sid": f.stem, "canary": st["canary"], "releaseId": st.get("releaseId"), "policyGen": st.get("policyGen"),
                "applied": sum(1 for r in att if r.get("applied")),
                "withheld": sum(int(r.get("bytes") or 0) - int(r.get("out") or 0) for r in att if r.get("applied")),
                "lean_if_enforced": sum(int(r.get("bytes") or 0) - int(r.get("lean") or 0) for r in att),
                "by_type": dict(Counter(r.get("type") for r in att)),
                "faults": dict(Counter(r.get("kind") for r in rows if r.get("ev") == "fault")),
                "spawns": dict(Counter(r.get("agentType") for r in rows if r.get("ev") == "spawn")),
                "errors": sum(1 for r in rows if str(r.get("ev", "")).endswith(".error")),
                "calls": sum(1 for r in rows if r.get("ev") == "call" and r.get("agent") is None),
                "first_ctx": _first_ctx(rows)})
        elif st.get("compatible") and _first_ctx(rows) is not None:
            base.append(_first_ctx(rows))
    base.sort()
    med = base[len(base) // 2] if base else None
    for c in canary:
        c["predicted_first_call_tok"] = round(c["withheld"] * TOK_PER_CHAR)
        c["measured_first_call_tok"] = (med - c["first_ctx"]) if med is not None and c["first_ctx"] is not None else None
    state = "CANARY_PENDING" if not canary else "CANARY_RAN"
    return {"state": state, "baseline_n": len(base), "baseline_first_ctx_median": med, "canary": canary}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pack", type=Path, help="pack dir (shadow), or with --canary a receipts root (<repoKey>/<sid>.jsonl)")
    ap.add_argument("--canary", action="store_true", help="read main-lean canary sessions instead of the shadow")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.canary:
        json.dump(canary_report(a.pack), sys.stdout, indent=1)
        print()
        return 0
    res = shadow(a.pack)
    if a.json:
        json.dump(res, sys.stdout, indent=1)
    else:
        print(render(res["table"]))
        print("top later uses:", json.dumps(res["table"]["risk_top"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
