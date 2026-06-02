"""CPC-OS Parallel Backlog -- section 208.5 Acceptance Contract.

Plans a set of backlog items into dependency-ordered *waves* and proves
the section 208.5 invariants hold: each pane runs a distinct task, locks
never overlap within a concurrent wave, dependencies are sequenced
(DAG), collisions are blocked, and a merge plan exists.

An item is a dict:
    {"item_id": str, "pane_id": str, "task": str,
     "locks": [str, ...], "deps": [item_id, ...]}

plan_parallel_backlog() returns {"valid": bool, "reason": str,
"waves": [[item_id, ...], ...], "merge_plan": [...]}. Items with no
unmet dependency share a wave (run in parallel); the planner blocks the
batch if any concurrent pair would collide on a lock, a pane, or a task,
or if the dependency graph has a cycle.
"""
from __future__ import annotations


def plan_parallel_backlog(items: list[dict]) -> dict:
    def fail(reason: str) -> dict:
        return {"valid": False, "reason": reason, "waves": [], "merge_plan": []}

    by_id: dict[str, dict] = {}
    for it in items:
        iid = it.get("item_id")
        if not iid:
            return fail("item missing item_id")
        if iid in by_id:
            return fail(f"duplicate item_id {iid!r}")
        by_id[iid] = it

    for it in items:
        for d in it.get("deps", []):
            if d not in by_id:
                return fail(f"item {it['item_id']!r} depends on unknown {d!r}")

    # Kahn-style wave construction (topological layering).
    remaining = dict(by_id)
    done: set[str] = set()
    waves: list[list[str]] = []
    while remaining:
        wave = [iid for iid, it in remaining.items()
                if all(d in done for d in it.get("deps", []))]
        if not wave:
            return fail(f"dependency cycle among {sorted(remaining)}")

        # Concurrent-wave collision checks (section 208.5).
        seen_locks: dict[str, str] = {}
        seen_panes: dict[str, str] = {}
        seen_tasks: dict[str, str] = {}
        for iid in wave:
            it = by_id[iid]
            for lk in it.get("locks", []):
                if lk in seen_locks:
                    return fail(
                        f"lock collision on {lk!r}: "
                        f"{seen_locks[lk]!r} vs {iid!r}")
                seen_locks[lk] = iid
            pane = it.get("pane_id")
            if pane in seen_panes:
                return fail(
                    f"pane {pane!r} has two concurrent items: "
                    f"{seen_panes[pane]!r} vs {iid!r}")
            seen_panes[pane] = iid
            task = it.get("task")
            if task in seen_tasks:
                return fail(
                    f"duplicate task {task!r} concurrently: "
                    f"{seen_tasks[task]!r} vs {iid!r}")
            seen_tasks[task] = iid

        waves.append(sorted(wave))
        done.update(wave)
        for iid in wave:
            del remaining[iid]

    merge_plan = [{"wave": i, "items": w} for i, w in enumerate(waves)]
    return {
        "valid": True,
        "reason": "section 208.5 contract satisfied",
        "waves": waves,
        "merge_plan": merge_plan,
        "wave_count": len(waves),
        "item_count": len(items),
    }
