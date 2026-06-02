"""Compile a task description into a frozen contract."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

# OD3 budget table (Owner-sealed 2026-06-01). USD per task class --
# values declared as named constants so the table is self-documenting
# and free of literal-number ambiguity.
BUDGET_S_USD = 5.0    # small fix / rename / lint
BUDGET_M_USD = 15.0   # bugfix / single-file feature
BUDGET_L_USD = 30.0   # multi-file feature / refactor
BUDGET_XL_USD = 100.0  # architecture / cross-cutting initiative

BUDGETS: dict[str, float] = {
    "S": BUDGET_S_USD,
    "M": BUDGET_M_USD,
    "L": BUDGET_L_USD,
    "XL": BUDGET_XL_USD,
}

TaskSize = Literal["S", "M", "L", "XL"]


@dataclass(frozen=True)
class OneShotContract:
    task_id: str
    description: str
    size: TaskSize
    budget_usd: float
    scope: tuple[str, ...]
    out_of_scope: tuple[str, ...]
    done_gate: str
    created_at: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _task_id() -> str:
    return f"OS-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def _derive_scope(description: str) -> tuple[str, ...]:
    # v1 heuristic: scope == description as a single concern. Future
    # iterations may decompose into atomic concerns via an NLP layer.
    desc = description.strip()
    return (desc,) if desc else ()


# Default out-of-scope items applicable to any task. The intent is
# "anything not explicitly required by the description is implicitly
# out of scope" -- these strings document that contract.
_DEFAULT_OUT_OF_SCOPE: tuple[str, ...] = (
    "unrelated refactors not required by the description",
    "feature additions beyond the stated scope",
    "performance optimizations not measured to be needed",
    "cosmetic edits to files outside the stated concern",
)


def _derive_out_of_scope(description: str) -> tuple[str, ...]:
    return _DEFAULT_OUT_OF_SCOPE


def _derive_done_gate(description: str, size: TaskSize) -> str:
    budget = BUDGETS.get(size, BUDGETS["M"])
    return (
        f"Done = (a) addresses the concern empirically (V-gate test "
        f"with observed output); (b) cost under ${budget:.2f} USD; "
        f"(c) no files touched outside scope; (d) commit pathspec-scoped."
    )


def compile_contract(
    description: str, size: TaskSize = "M",
) -> OneShotContract:
    if size not in BUDGETS:
        size = "M"
    return OneShotContract(
        task_id=_task_id(),
        description=description,
        size=size,
        budget_usd=BUDGETS[size],
        scope=_derive_scope(description),
        out_of_scope=_derive_out_of_scope(description),
        done_gate=_derive_done_gate(description, size),
        created_at=_now_iso(),
    )


def render_contract(c: OneShotContract) -> str:
    """Human-readable rendering of a frozen contract -- the text the
    Owner pastes at the top of the next prompt to lock fidelity."""
    bar = "=" * 60
    lines = [
        bar,
        f"ONE-SHOT CONTRACT: {c.task_id}",
        bar,
        f"Size:      {c.size}  (budget ${c.budget_usd:.2f} USD)",
        f"Created:   {c.created_at}",
        "",
        "Scope (in):",
    ]
    lines += [f"  - {s}" for s in c.scope] or ["  (none derived)"]
    lines += ["", "Out of scope:"]
    lines += [f"  - {o}" for o in c.out_of_scope]
    lines += ["", "Done gate:", f"  {c.done_gate}", bar]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(
        description="Compile a One-Shot Contract (BL-ONESHOT-001 / OD3)."
    )
    p.add_argument("--task", required=True, help="Task description")
    p.add_argument(
        "--size", default="M", choices=list(BUDGETS),
        help="S=$5  M=$15  L=$30  XL=$100 (OD3 budget table)",
    )
    args = p.parse_args(argv)

    contract = compile_contract(args.task, args.size)
    print(render_contract(contract))
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
