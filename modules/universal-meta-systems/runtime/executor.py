"""Meta-System Executor (R-CORE) -- interpret one meta-system for one repo.

Given a meta-system id + a repo's noun-map, parse the corpus dataset and emit a
concrete, noun-substituted, gate-checked execution plan. It NEVER reimplements
the meta-system: every ACTION, INVARIANT, and PIPELINE is the corpus's own
doctrine with the repo's nouns substituted in. The specificity is exactly as
rich as the noun-map -- no richer, and honestly so.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import corpus_parser as cp
from .noun_map import NounMap, apply_noun_map


@dataclass(frozen=True)
class PlanOp:
    signature: str
    guarantee: str
    never: str


@dataclass
class ExecutionPlan:
    ms_id: str
    title: str
    noun_map_source: str
    source_path: str
    ops: list[PlanOp] = field(default_factory=list)
    pipelines: list[tuple[str, tuple[str, ...]]] = field(default_factory=list)
    lifecycle: tuple[str, ...] = ()
    gates: list[tuple[str, str]] = field(default_factory=list)
    frozen_semantics: str = ""
    warnings: list[str] = field(default_factory=list)


def build_plan(ms_id: str, nm: NounMap, corpus_root: str | Path) -> ExecutionPlan:
    """Interpret MS-N for a repo via its noun-map. Read-only w.r.t. the corpus."""
    spec = cp.load_spec(ms_id, Path(corpus_root))

    def s(text: str) -> str:
        return apply_noun_map(text, nm)

    plan = ExecutionPlan(
        ms_id=spec.ms_id,
        title=s(spec.title),
        noun_map_source=nm.source,
        source_path=spec.source_path,
        lifecycle=tuple(s(x) for x in spec.lifecycle),
        frozen_semantics=s(spec.frozen_semantics),
        warnings=list(nm.warnings),
    )
    plan.ops = [PlanOp(signature=s(op.signature),
                       guarantee=s(op.guarantee),
                       never=s(op.never)) for op in spec.ops]
    plan.pipelines = [(s(p.name), tuple(s(step) for step in p.steps))
                      for p in spec.pipelines]
    plan.gates = [(g.gid, s(g.text)) for g in spec.gates]
    if nm.is_generic:
        plan.warnings.append(
            "GENERIC noun-map: plan shows the corpus doctrine unsubstituted "
            "(universal, not yet domain-specific). Declare a noun-map to specialize.")
    return plan


def render_plan(plan: ExecutionPlan) -> str:
    """Human-readable execution plan for a repo."""
    out: list[str] = []
    tag = "domain-specific" if plan.noun_map_source == "file" else "GENERIC (universal)"
    out.append(f"# {plan.ms_id} -- {plan.title}")
    out.append(f"noun-map: {tag}  |  source: {plan.source_path}")
    if plan.warnings:
        out.append("")
        for w in plan.warnings:
            out.append(f"  [!] {w}")
    if plan.frozen_semantics:
        out.append("")
        out.append(f"Frozen semantics (must not drift): {plan.frozen_semantics}")

    out.append("")
    out.append("## ACTIONS (each operation this meta-system requires of your system)")
    for i, op in enumerate(plan.ops, 1):
        out.append(f"{i}. {op.signature}")
        if op.guarantee:
            out.append(f"     guarantee: {op.guarantee}")
        if op.never:
            out.append(f"     must never: {op.never}")

    if plan.pipelines:
        out.append("")
        out.append("## PIPELINES (the order operations chain)")
        for name, steps in plan.pipelines:
            out.append(f"- {name}: " + "  ->  ".join(steps))

    if plan.lifecycle:
        out.append("")
        out.append("## LIFECYCLE: " + "  ->  ".join(plan.lifecycle))

    if plan.gates:
        out.append("")
        out.append("## INVARIANTS (hard gates that must hold)")
        for gid, text in plan.gates:
            out.append(f"- {gid}: {text}")

    return "\n".join(out)


def plan_to_dict(plan: ExecutionPlan) -> dict:
    """Serializable form (for JSON output and PM-03 findings)."""
    return {
        "ms_id": plan.ms_id,
        "title": plan.title,
        "noun_map_source": plan.noun_map_source,
        "source_path": plan.source_path,
        "ops": [{"signature": o.signature, "guarantee": o.guarantee, "never": o.never}
                for o in plan.ops],
        "pipelines": [{"name": n, "steps": list(s)} for n, s in plan.pipelines],
        "lifecycle": list(plan.lifecycle),
        "gates": [{"id": g, "text": t} for g, t in plan.gates],
        "frozen_semantics": plan.frozen_semantics,
        "warnings": list(plan.warnings),
    }
