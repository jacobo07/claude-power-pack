#!/usr/bin/env python3
"""specialization.py -- the 6-component specialization map (CPP-APIR DS06).

`executor.py` specializes a meta-system by substituting nouns, and says so
honestly: *"The specificity is exactly as rich as the noun-map -- no richer."*
For rendering doctrine that is correct and sufficient. For specializing a
CAPABILITY it is precisely the shape `HR-APA-016` refuses:

    Renaming a capability is not specializing it.

This module supplies the depth that rule demands. It compiles six declared
components into the `overrides` dict that
`capability_runtime.derivatives.derive()` already consumes, so ownership stays
clean: this module decides HOW DEEP a specialization goes, and
`capability_runtime` remains the one registry that records genealogy.

    Universal Capability Kernel   (the parent contract -- not ours)
      + Domain Pack               vocabulary, triggers, anti-triggers, scope
      + Runtime Adapter           which runtimes this can actually serve
      + Evidence Adapter          what counts as evidence in THIS project
      + Quality Policy            the properties that make output acceptable
      + Activation Policy         cost, risk, when it must not fire
      + Project Contracts         prerequisites, consumers, write surfaces
      = Specialized Project Capability

Two things this module refuses to do. It never invents a domain noun (the
noun-map contract: PROPOSE, never guess), and it never lets a domain term reach
the kernel -- `contaminates_kernel()` is the enforcement surface `HR-APA-017`
lacked outside the derivative path.

Stdlib-only. Compiling is fail-closed; auditing is fail-open.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[3]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

# Components that carry real specialization. A delta confined to the naming
# component alone is what HR-APA-016 rejects.
SUBSTANTIVE_COMPONENTS = (
    "domain_pack", "runtime_adapter", "evidence_adapter",
    "quality_policy", "activation_policy", "project_contracts",
)
# Minimum distinct components that must carry content for a specialization to
# be more than a rename. Two, not one: a single populated component is usually
# just a runtime pin, which is configuration rather than specialization.
MIN_COMPONENTS = 2


class SpecializationError(ValueError):
    """A specialization that would be invalid if compiled."""


@dataclass
class DomainPack:
    """The project's own vocabulary and boundary. The only domain-bearing
    component -- everything domain-specific must live here so the kernel
    stays domain-blind."""
    domain: str = ""
    triggers: list = field(default_factory=list)
    anti_triggers: list = field(default_factory=list)
    scope: list = field(default_factory=list)
    non_scope: list = field(default_factory=list)
    vocabulary: dict = field(default_factory=dict)   # universal noun -> local noun


@dataclass
class RuntimeAdapter:
    """Which runtimes the specialized capability can actually serve.
    Consumed by applicability gate 5 (CAPABILITY_INSUFFICIENT)."""
    compatible_runtimes: list = field(default_factory=list)
    dependencies: list = field(default_factory=list)


@dataclass
class EvidenceAdapter:
    """What counts as evidence HERE. A capability that requires hardware proof
    in one project may require a passing suite in another; the kernel must not
    encode either."""
    required_evidence: list = field(default_factory=list)
    inputs: list = field(default_factory=list)


@dataclass
class QualityPolicy:
    """The properties that make this capability's output acceptable in this
    project, and what it costs to be wrong."""
    outputs: list = field(default_factory=list)
    failure_risk_if_omitted: str = ""
    maturity: str = ""


@dataclass
class ActivationPolicy:
    """When it may fire, what that costs, and what it may never do
    unilaterally."""
    activation_cost: str = ""
    context_cost: str = ""
    operational_cost: str = ""
    expected_leverage: str = ""
    risk_class: str = ""
    rollback: str = ""
    kill_switch: str = ""
    retirement_condition: str = ""


@dataclass
class ProjectContracts:
    """Who consumes it here, what it may write, what must be true first."""
    prerequisites: list = field(default_factory=list)
    consumers: list = field(default_factory=list)
    write_surfaces: list = field(default_factory=list)
    permissions: list = field(default_factory=list)


@dataclass
class SpecializationSpec:
    """A declared specialization. `project` and `naming` are identity;
    everything else is depth."""
    project: str
    naming: dict = field(default_factory=dict)      # id / name / owner overrides
    domain_pack: DomainPack = field(default_factory=DomainPack)
    runtime_adapter: RuntimeAdapter = field(default_factory=RuntimeAdapter)
    evidence_adapter: EvidenceAdapter = field(default_factory=EvidenceAdapter)
    quality_policy: QualityPolicy = field(default_factory=QualityPolicy)
    activation_policy: ActivationPolicy = field(default_factory=ActivationPolicy)
    project_contracts: ProjectContracts = field(default_factory=ProjectContracts)
    benchmarks: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _nonempty(component) -> dict:
    """Fields of a component that actually carry a value."""
    return {k: v for k, v in asdict(component).items() if v not in (None, "", [], {})}


def populated_components(spec: SpecializationSpec) -> list:
    """Which substantive components carry content. This is the measurement
    HR-APA-016 is enforced against -- depth is counted, not asserted."""
    return [name for name in SUBSTANTIVE_COMPONENTS
            if _nonempty(getattr(spec, name))]


def depth(spec: SpecializationSpec) -> int:
    """Number of substantive components populated. 0 means a rename."""
    return len(populated_components(spec))


def contaminates_kernel(spec: SpecializationSpec, kernel_fields: dict) -> list:
    """HR-APA-017 outside the derivative path: a domain term must never appear
    in a field the universal kernel owns.

    Returns the offending (field, term) pairs. Empty means clean. Read-only and
    fail-open -- an unusable kernel dict reports no contamination rather than
    raising, because this is an audit, not a gate on construction.
    """
    terms = {str(t).strip().lower()
             for t in list(spec.domain_pack.vocabulary.values())
                     + ([spec.domain_pack.domain] if spec.domain_pack.domain else [])
             if str(t).strip()}
    if not terms or not isinstance(kernel_fields, dict):
        return []
    hits = []
    for fname, val in kernel_fields.items():
        blob = " ".join(map(str, val)) if isinstance(val, list) else str(val)
        low = blob.lower()
        for t in terms:
            if t in low:
                hits.append((fname, t))
    return sorted(set(hits))


def compile_overrides(spec: SpecializationSpec) -> dict:
    """Compile the six components into contract-field overrides.

    Fail-closed: a specialization that is naming-only is refused HERE, before
    `derive()` sees it, so the caller gets the rule violation at the point the
    spec was authored rather than one layer later.
    """
    if not str(spec.project).strip():
        raise SpecializationError("a specialization requires a project")

    populated = populated_components(spec)
    if len(populated) < MIN_COMPONENTS:
        raise SpecializationError(
            f"HR-APA-016 {spec.project}: specialization populates "
            f"{populated or 'no'} substantive component(s); at least "
            f"{MIN_COMPONENTS} required -- naming and a single pin are not "
            "specialization")

    out: dict = {}
    # Naming is applied, but never counts toward depth.
    for k in ("id", "name", "owner", "sovereign_question"):
        if spec.naming.get(k):
            out[k] = spec.naming[k]

    for component in SUBSTANTIVE_COMPONENTS:
        got = _nonempty(getattr(spec, component))
        # `domain` and `vocabulary` describe the pack; they are not contract
        # fields, so they inform the compile without being written through.
        got.pop("domain", None)
        got.pop("vocabulary", None)
        out.update(got)
    return out


def specialize(parent, spec: SpecializationSpec, *, approved_override: str = "",
               upgrade_path: str = "") -> tuple:
    """Compile, then cut the derivative. Returns (child, derivative_record).

    Imported lazily so this module is usable for auditing a spec even where
    `capability_runtime` is not on the path.
    """
    from modules.capability_runtime.derivatives import derive
    overrides = compile_overrides(spec)
    return derive(parent, spec.project, overrides,
                  approved_override=approved_override,
                  upgrade_path=upgrade_path
                  or f"recompile specialization for {spec.project}")


# --- PROPOSE-only derivation from a project's own graphs -------------------

def propose_from_graphs(emitted: dict, project: str = "") -> SpecializationSpec:
    """Draft a specialization from the DS02 graph emitters.

    PROPOSE-only, per the noun-map contract this module inherits: every value
    below is READ from the project's observed graphs. Nothing is invented, and
    the draft is deliberately shallow -- an Owner completes the domain pack.
    """
    graphs = (emitted or {}).get("graphs", {}) or {}

    def nodes(name, kind=None):
        return [n for n in graphs.get(name, {}).get("nodes", [])
                if kind is None or n.get("kind") == kind]

    demand = [n["id"] for n in nodes("capability_demand", "demand")]
    gaps = [n["id"] for n in nodes("capability_demand", "gap")]
    risks = [n["id"] for n in nodes("risk_topology", "risk")]

    # A scope the project already holds becomes an ANTI-trigger: the capability
    # must not fire where an incumbent owns the territory.
    held = list((emitted or {}).get("held_scopes", []))

    spec = SpecializationSpec(project=project or str(emitted.get("project") or ""))
    spec.domain_pack = DomainPack(triggers=sorted(set(demand + gaps)),
                                  anti_triggers=sorted(set(held)))
    rt = (emitted or {}).get("runtime")
    spec.runtime_adapter = RuntimeAdapter(compatible_runtimes=[rt] if rt else [])
    spec.evidence_adapter = EvidenceAdapter(
        required_evidence=sorted(set((emitted or {}).get("available_evidence", []))))
    # Risk topology sets the activation policy's floor, never its ceiling.
    if "safety_critical" in risks:
        spec.activation_policy = ActivationPolicy(risk_class="safety_critical")
    elif "production_changing" in risks:
        spec.activation_policy = ActivationPolicy(risk_class="production_changing")
    elif "cross_cutting" in risks:
        spec.activation_policy = ActivationPolicy(risk_class="cross_cutting")
    return spec


def audit(spec: SpecializationSpec, kernel_fields: dict | None = None) -> dict:
    """Non-raising report on a spec: depth, which components carry it, whether
    it would compile, and any kernel contamination."""
    populated = populated_components(spec)
    try:
        compile_overrides(spec)
        compiles, why = True, ""
    except SpecializationError as exc:
        compiles, why = False, str(exc)
    return {
        "project": spec.project,
        "depth": len(populated),
        "populated_components": populated,
        "name_level_only": len(populated) == 0,
        "compiles": compiles,
        "reason": why,
        "kernel_contamination": contaminates_kernel(spec, kernel_fields or {}),
        "benchmarks": len(spec.benchmarks),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="6-component specialization map (CPP-APIR DS06)")
    ap.add_argument("--propose-from", metavar="PATH", default=None,
                    help="a repo path: emit a PROPOSED spec from its graphs")
    ap.add_argument("--audit", metavar="SPEC_JSON", default=None,
                    help="audit a spec file for depth and HR-APA-016")
    ap.add_argument("--project", default="")
    args = ap.parse_args(argv)

    if args.propose_from:
        from modules.setup_os.graph import emit_all
        from modules.setup_os.scanner import scan
        spec = propose_from_graphs(emit_all(scan(args.propose_from)), args.project)
        print(json.dumps(spec.to_dict(), indent=2))
        return 0

    if args.audit:
        try:
            raw = json.loads(Path(args.audit).read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"unreadable spec: {type(exc).__name__}: {exc}")
            return 1
        spec = SpecializationSpec(
            project=raw.get("project", ""),
            naming=raw.get("naming", {}),
            domain_pack=DomainPack(**raw.get("domain_pack", {})),
            runtime_adapter=RuntimeAdapter(**raw.get("runtime_adapter", {})),
            evidence_adapter=EvidenceAdapter(**raw.get("evidence_adapter", {})),
            quality_policy=QualityPolicy(**raw.get("quality_policy", {})),
            activation_policy=ActivationPolicy(**raw.get("activation_policy", {})),
            project_contracts=ProjectContracts(**raw.get("project_contracts", {})),
            benchmarks=raw.get("benchmarks", []))
        print(json.dumps(audit(spec), indent=2))
        return 0

    ap.print_help()
    return 0


__all__ = [
    "DomainPack", "RuntimeAdapter", "EvidenceAdapter", "QualityPolicy",
    "ActivationPolicy", "ProjectContracts", "SpecializationSpec",
    "SpecializationError", "SUBSTANTIVE_COMPONENTS", "MIN_COMPONENTS",
    "populated_components", "depth", "contaminates_kernel", "compile_overrides",
    "specialize", "propose_from_graphs", "audit",
]

if __name__ == "__main__":
    raise SystemExit(main())
