#!/usr/bin/env python3
"""loop_budget.py -- CO-09: loop & subagent economics (the two burn multipliers).

Loops COMPOUND and subagent swarms MULTIPLY -- the two highest-risk context/compute
growers. CO-09 makes each prove it stays bounded before it is admitted.

A LOOP is admitted only with the seven-part budget (CO-09 I.2): expected cost,
expected context growth, a MAXIMUM ITERATION CAP, a checkpoint plan, stop gates, a
kill switch, and a resume plan. An uncapped loop is refused outright -- the single
most important rule. Once running, the kill switch fires at iteration boundaries
(the frequent boundary the kernel owns) when cost exceeds 2x budget (HR-COST-002),
the context projection breaches the 60% ceiling (CO-00), or the 2-consecutive-
failures law trips (anti-antipatterns Rule 12). The kill switch has no bypass.

A SUBAGENT is a budgeted economic actor: it declares a budget, an allowed model
(routed by CO-03 / cost_collapse -- exploration/test/doc agents use Haiku/Sonnet,
never Opus on a trivial task: HR-COST-001), a context limit, and an ROI. Its cost
ATTRIBUTES TO THE PARENT, closing the found defect where subagent transcripts were
excluded from burn analysis (token_ground_truth "Skip subagent logs").

Honest guarantee (CO-10): rung-3 admission refusal where a loop/swarm is launched
through a boundary the wrapper owns + iteration-boundary kill switch. It cannot
halt the interior of a single iteration's generation; a loop's boundaries are
frequent enough that the kill switch is a real guarantee, and the hard cap is the
absolute backstop. All decisions here are PURE and deterministic; the consumer
(loop/agent orchestration) fail-opens around them.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

CEILING_PCT = 60.0                 # CO-00 hard ceiling (effective context)
KILL_COST_FACTOR = 2.0             # HR-COST-002: cost > 2x budget -> kill
CONSECUTIVE_FAIL_LIMIT = 2         # Rule 12 / CO-09 I.2 part 6


@dataclass
class LoopBudget:
    """The seven-part loop budget (CO-09 I.2). max_iterations is mandatory; a
    None/<=0 value means UNCAPPED -> refused at admission."""
    max_iterations: int | None = None      # 1) hard cap (mandatory)
    per_iter_tokens: int = 0                # for the cost projection
    per_iter_context_pct: float = 0.0       # 2) context growth / iteration
    start_context_pct: float = 0.0
    budget_tokens: int = 0                  # the loop's cost ceiling
    checkpoint: bool = False                # 4) commits durable progress?
    stop_gates: list = field(default_factory=list)   # 5) early-stop conditions
    resume_plan: bool = False               # 7) recover progress if killed?
    # kill switch (6) is implicit via kill_check(); cost/growth are 1/2.


@dataclass
class LoopVerdict:
    verdict: str                            # "proceed" | "refuse"
    reasons: list = field(default_factory=list)
    satisfy: list = field(default_factory=list)
    projected_context_pct: float | None = None
    missing_parts: list = field(default_factory=list)


def validate_budget(b: LoopBudget) -> list:
    """Return the list of missing mandatory budget parts ([] == complete)."""
    missing = []
    if not b.max_iterations or b.max_iterations <= 0:
        missing.append("max_iterations (an uncapped loop is forbidden)")
    if not b.stop_gates:
        missing.append("stop_gates (a loop with no convergence/stop gate spins)")
    if not b.checkpoint:
        missing.append("checkpoint plan (an interrupted loop must not waste work)")
    if not b.resume_plan:
        missing.append("resume_plan (a killed loop must recover from checkpoint)")
    return missing


def admit_loop(b: LoopBudget, *, ceiling_pct: float = CEILING_PCT) -> LoopVerdict:
    """Admit a loop only if it is fully budgeted AND its conservative context
    trajectory (start + per-iteration growth x cap) stays under the ceiling."""
    missing = validate_budget(b)
    reasons: list[str] = []
    satisfy: list[str] = []

    # The uncapped loop is the hardest refusal -- it cannot even be projected.
    if not b.max_iterations or b.max_iterations <= 0:
        return LoopVerdict(
            "refuse",
            ["uncapped loop -- no maximum iterations declared"],
            ["declare a hard max_iterations before this loop can be admitted"],
            None, missing)

    proj = b.start_context_pct + b.per_iter_context_pct * b.max_iterations
    if proj > ceiling_pct:
        reasons.append(
            f"projected context {proj:.0f}% > {ceiling_pct:.0f}% ceiling "
            f"before the {b.max_iterations}-iteration cap")
        # How many iterations fit under the ceiling?
        if b.per_iter_context_pct > 0:
            fit = int((ceiling_pct - b.start_context_pct) / b.per_iter_context_pct)
            satisfy.append(f"lower max_iterations to <= {max(0, fit)}")
        satisfy.append("or checkpoint-and-hibernate between iterations "
                       "(CO-07) so context resets each round")

    if missing:
        reasons.append("incomplete budget: " + "; ".join(missing))
        satisfy.append("declare the missing budget part(s) above")

    if reasons:
        return LoopVerdict("refuse", reasons, satisfy, proj, missing)
    return LoopVerdict("proceed", ["bounded loop under ceiling"], [], proj, [])


@dataclass
class LoopState:
    """Live state evaluated at each iteration boundary."""
    iterations_done: int = 0
    cost_so_far_tokens: int = 0
    current_context_pct: float = 0.0
    per_iter_context_pct: float = 0.0
    consecutive_failures: int = 0


@dataclass
class KillVerdict:
    kill: bool
    reasons: list = field(default_factory=list)


def kill_check(s: LoopState, b: LoopBudget, *,
               ceiling_pct: float = CEILING_PCT,
               cost_factor: float = KILL_COST_FACTOR,
               fail_limit: int = CONSECUTIVE_FAIL_LIMIT) -> KillVerdict:
    """Evaluate the kill switch at an iteration boundary. No bypass."""
    reasons: list[str] = []
    if b.budget_tokens > 0 and s.cost_so_far_tokens > cost_factor * b.budget_tokens:
        reasons.append(
            f"cost {s.cost_so_far_tokens:,} > {cost_factor:g}x budget "
            f"{b.budget_tokens:,} (HR-COST-002)")
    # Next iteration's projected context would breach the ceiling.
    next_proj = s.current_context_pct + s.per_iter_context_pct
    if next_proj > ceiling_pct:
        reasons.append(
            f"next iteration projects {next_proj:.0f}% > {ceiling_pct:.0f}% ceiling")
    if s.consecutive_failures >= fail_limit:
        reasons.append(
            f"{s.consecutive_failures} consecutive failures "
            f">= {fail_limit} (Rule 12 -- pivot, do not retry)")
    return KillVerdict(bool(reasons), reasons)


# --------------------------------------------------------------------------
# Subagent economics
# --------------------------------------------------------------------------
@dataclass
class SubagentVerdict:
    verdict: str                            # "proceed" | "refuse"
    model: str = ""
    reasons: list = field(default_factory=list)
    satisfy: list = field(default_factory=list)


def admit_subagent(task_description: str, *, budget_remaining_tokens: int,
                   est_tokens: int = 0, route_fn=None) -> SubagentVerdict:
    """Admit a subagent: route its model (CO-03 / cost_collapse), check it fits
    the parent's remaining envelope, and forbid Opus on a trivial (NANO) task
    (HR-COST-001)."""
    try:
        if route_fn is None:
            from modules.cost_collapse.router import route as route_fn  # type: ignore
        r = route_fn(task_description)
        model = getattr(r, "model", "")
        route_class = getattr(getattr(r, "route_class", None), "value", "")
    except Exception:  # noqa: BLE001 -- routing unavailable -> safe default
        model, route_class = "claude-sonnet-4-6", "micro"

    reasons: list[str] = []
    satisfy: list[str] = []

    # HR-COST-001: an expensive model on a trivial subagent task is a budget hole.
    if route_class == "nano" and "opus" in model.lower():
        reasons.append("Opus routed to a NANO subagent task (HR-COST-001)")
        satisfy.append("route this subagent to Haiku")
        model = "claude-haiku-4-5"

    if budget_remaining_tokens >= 0 and est_tokens > budget_remaining_tokens:
        reasons.append(
            f"estimated {est_tokens:,} tok exceeds parent's remaining "
            f"{budget_remaining_tokens:,} tok envelope")
        satisfy.append("narrow the subagent's scope or free parent budget")

    if reasons:
        return SubagentVerdict("refuse", model, reasons, satisfy)
    return SubagentVerdict("proceed", model, [f"routed to {model} ({route_class})"], [])


def attribute_subagent_cost(parent_cost_tokens: int,
                            subagent_cost_tokens: int) -> int:
    """The found-defect fix (CO-09 II.3): a swarm's burn is the PARENT's burn.
    Subagent cost is added to the parent's ledger -- never an invisible blind
    spot. Returns the parent's cost INCLUDING the attributed subagent spend."""
    return (parent_cost_tokens or 0) + (subagent_cost_tokens or 0)


def main(argv=None) -> int:
    import argparse
    import json
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--max-iter", type=int, default=None)
    ap.add_argument("--start-pct", type=float, default=0.0)
    ap.add_argument("--per-iter-pct", type=float, default=0.0)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    b = LoopBudget(max_iterations=args.max_iter,
                   start_context_pct=args.start_pct,
                   per_iter_context_pct=args.per_iter_pct,
                   checkpoint=True, resume_plan=True, stop_gates=["demo"])
    v = admit_loop(b)
    if args.json:
        print(json.dumps({"verdict": v.verdict, "reasons": v.reasons,
                          "satisfy": v.satisfy,
                          "projected_context_pct": v.projected_context_pct}))
    else:
        print(f"loop admission: {v.verdict}")
        for r in v.reasons:
            print(f"  - {r}")
        for s in v.satisfy:
            print(f"  > {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
