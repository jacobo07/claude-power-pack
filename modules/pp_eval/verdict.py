"""Layer verdicts (spec §3.3, §3.7). Pure functions over ledger rows; no I/O.

A row is VALID only if its run passed its per-run controls (runner.void_reasons). Here the
remaining judgement happens: pairing, the ceiling defence and the pairwise context control.
"""
from __future__ import annotations

from collections import defaultdict

MIN_TASKS = 4
MIN_DISCRIMINATING = 4
CONTEXT_DROP_MIN = 1000


def discriminating(rows: list[dict]) -> set[str]:
    """Tasks whose VALID history holds at least one pass and one fail (any layer, any arm)."""
    seen = defaultdict(set)
    for r in rows:
        if r.get("status") == "VALID":
            seen[r["task"]].add(bool(r.get("task_pass")))
    return {t for t, outcomes in seen.items() if outcomes == {True, False}}


def pairs(rows: list[dict], layer: str, fp: str) -> dict[str, list[tuple[dict, dict]]]:
    """task -> [(A row, B row)] per replicate, VALID rows of this layer+fingerprint only."""
    by = {}
    for r in rows:
        if r.get("status") != "VALID" or r.get("layer") != layer or r.get("fingerprint") != fp:
            continue
        by[(r["task"], r["rep"], r["arm"])] = r
    out = defaultdict(list)
    for (task, rep, arm), a in by.items():
        if arm == "A" and (task, rep, "B") in by:
            out[task].append((a, by[(task, rep, "B")]))
    return out


def judge(rows: list[dict], layer: str, fp: str) -> dict:
    p = pairs(rows, layer, fp)
    disc = discriminating(rows)
    loss = [t for t, ps in p.items() if len(ps) >= 2 and all(a["task_pass"] and not b["task_pass"] for a, b in ps[:2])]
    harm = [t for t, ps in p.items() if len(ps) >= 2 and all(not a["task_pass"] and b["task_pass"] for a, b in ps[:2])]
    full = {t: ps[:2] for t, ps in p.items() if len(ps) >= 2}
    base = {"layer": layer, "fingerprint": fp, "tasks_paired": len(full),
            "discriminating": sorted(disc & set(full)), "secondary": secondary(p)}
    if loss:
        return {**base, "verdict": "LOSS", "tasks": loss}
    if harm:
        return {**base, "verdict": "HARM", "tasks": harm}
    if len(full) < MIN_TASKS:
        return {**base, "verdict": "INSUFFICIENT", "reason": f"{len(full)} tasks with 2 pairs, need {MIN_TASKS}"}
    if len(disc & set(full)) < MIN_DISCRIMINATING:
        return {**base, "verdict": "INSUFFICIENT",
                "reason": f"ceiling: {len(disc & set(full))} discriminating tasks, need {MIN_DISCRIMINATING}"}
    regress = [t for t, ps in full.items() if any(a["task_pass"] and not b["task_pass"] for a, b in ps)]
    if regress:
        return {**base, "verdict": "INSUFFICIENT", "reason": f"B failed where A passed once (not 2/2): {regress}"}
    if layer == "context":
        weak = [t for t, ps in full.items() for a, b in ps
                if (a["evidence"].get("first_call_context") or 0) - (b["evidence"].get("first_call_context") or 0)
                < CONTEXT_DROP_MIN]
        if weak:
            return {**base, "verdict": "INSUFFICIENT", "reason": f"context control: arm B not lighter in {sorted(set(weak))}"}
    return {**base, "verdict": "NO_LOSS"}


def secondary(p: dict) -> dict:
    """Aggregate cost per arm over every pair (never a tie-breaker)."""
    agg = {"A": [0, 0, 0.0], "B": [0, 0, 0.0]}   # runs, total_context, wall
    for ps in p.values():
        for a, b in ps:
            for arm, r in (("A", a), ("B", b)):
                agg[arm][0] += 1
                agg[arm][1] += r["evidence"].get("total_context") or 0
                agg[arm][2] += r.get("wall_s") or 0.0
    return {arm: {"runs": n, "mean_context": round(c / n) if n else None, "mean_wall_s": round(w / n, 1) if n else None}
            for arm, (n, c, w) in agg.items()}
