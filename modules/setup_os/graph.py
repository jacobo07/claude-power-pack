#!/usr/bin/env python3
"""graph.py -- Project Intelligence graph emitters (CPP-APIR DS02).

`scanner.py` answers *what is in this repo*, one flat field at a time, each
carrying its detection Source. That flat profile is the right shape for a
readiness score and the wrong shape for a capability decision: applicability
asks what evidence EXISTS, what runtime this IS, and which scopes are ALREADY
HELD -- three questions no single scanner field answers.

This module is the projection between them. It is an extension of the Setup-OS
owner, not a second scanner: it reads a ProjectProfile and never walks the disk.

Four emitters, then one bridge:

  architecture_graph      layers present + the edges between them
  capability_demand_graph what this project will need done, and why
  human_dependency_map    where a human is currently the router (HR-APA-007's
                          failure class: work with no owner but a person)
  risk_topology           what an automated write here could break

  to_mission_context()    the bridge that feeds capability_runtime

Provenance is preserved end to end. A graph node derived from an INFERRED field
is itself INFERRED -- a projection may never launder an inference into a fact.

Stdlib-only. Read-only. Fail-open at the boundary: an absent field never raises.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field as dc_field
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.setup_os.scanner import (  # noqa: E402
    Field, ProjectProfile, Source, scan,
)

# Runtime identity, most specific first. The first framework that matches wins,
# then the primary language. Order matters: "Next.js" is a more useful runtime
# answer than "TypeScript" when both are true.
_FRAMEWORK_RUNTIME = {
    "Next.js": "node", "Nuxt": "node", "Svelte": "node", "Vue": "node",
    "React": "node", "Express": "node",
    "FastAPI": "python", "Flask": "python", "Django": "python",
    "Phoenix": "beam",
}
_LANGUAGE_RUNTIME = {
    "Python": "python", "TypeScript": "node", "JavaScript": "node",
    "Elixir": "beam", "Go": "go", "Rust": "rust", "Java": "jvm",
    "Kotlin": "jvm", "C": "native", "C++": "native", "Ruby": "ruby",
    "PHP": "php", "C#": "dotnet", "Swift": "native",
}


@dataclass
class Node:
    """A graph node that remembers where its truth came from."""
    id: str
    kind: str
    source: str
    detail: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Edge:
    src: str
    dst: str
    relation: str
    source: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Graph:
    name: str
    nodes: list = dc_field(default_factory=list)
    edges: list = dc_field(default_factory=list)

    def to_dict(self) -> dict:
        return {"name": self.name,
                "nodes": [n.to_dict() for n in self.nodes],
                "edges": [e.to_dict() for e in self.edges]}


def _f(profile: ProjectProfile, name: str) -> Field:
    """A profile field, or an explicit MISSING result when the profile does not
    carry that name. Never raises on a schema change -- an emitter must not
    break because a field was renamed upstream."""
    got = getattr(profile, name, None)
    if isinstance(got, Field):
        return got
    if isinstance(got, dict) and "value" in got:      # already to_dict()'d
        src = got.get("source", Source.UNKNOWN)
        return Field(got["value"],
                     src if isinstance(src, Source) else Source(str(src)))
    return Field(None, Source.MISSING)


def _on(profile: ProjectProfile, name: str) -> bool:
    return bool(_f(profile, name).value)


def _src(profile: ProjectProfile, name: str) -> str:
    s = _f(profile, name).source
    return s.value if isinstance(s, Source) else str(s)


# --- emitter 1 -------------------------------------------------------------

def architecture_graph(profile: ProjectProfile) -> Graph:
    """Which architectural layers exist, and how they connect.

    Edges are asserted only between layers this profile actually observed. A
    frontend->backend edge on a repo with no backend would be an invention.
    """
    g = Graph("architecture")
    layers = (
        ("frontend", "frontend_presence"), ("backend", "backend_presence"),
        ("database", "database_presence"), ("cli", "cli_presence"),
        ("ci", "ci_cd"), ("container", "docker_presence"),
        ("auth", "auth_presence"), ("payment", "payment_presence"),
        ("external_api", "external_api_presence"),
    )
    present = set()
    for node_id, fname in layers:
        if _on(profile, fname):
            present.add(node_id)
            g.nodes.append(Node(node_id, "layer", _src(profile, fname)))

    # Edges, each justified by both endpoints being observed.
    for src, dst, rel in (
        ("frontend", "backend", "calls"),
        ("backend", "database", "persists_to"),
        ("backend", "external_api", "depends_on"),
        ("frontend", "auth", "authenticates_via"),
        ("backend", "auth", "authenticates_via"),
        ("backend", "payment", "charges_via"),
        ("ci", "container", "builds"),
        ("cli", "backend", "invokes"),
    ):
        if src in present and dst in present:
            g.edges.append(Edge(src, dst, rel, Source.INFERRED.value))

    lang = _f(profile, "language_primary")
    if lang.value:
        g.nodes.append(Node(str(lang.value), "language",
                            lang.source.value if isinstance(lang.source, Source)
                            else str(lang.source)))
    fw = _f(profile, "framework_primary")
    if fw.value:
        g.nodes.append(Node(str(fw.value), "framework",
                            fw.source.value if isinstance(fw.source, Source)
                            else str(fw.source)))
    return g


# --- emitter 2 -------------------------------------------------------------

# (demand token, profile field that implies it, why it is implied)
_DEMAND_RULES = (
    ("schema_migration_safety", "database_presence",
     "a database is present, so schema change is a recurring risky operation"),
    ("credential_governance", "auth_presence",
     "authentication code paths handle credentials"),
    ("financial_correctness", "payment_presence",
     "payment integration makes monetary correctness a quality property"),
    ("third_party_contract_drift", "external_api_presence",
     "external APIs change under the project without notice"),
    ("visual_fidelity", "frontend_presence",
     "a user-facing surface has quality properties no unit test observes"),
    ("deployment_reality", "docker_presence",
     "a container spec means built != deployed"),
    ("release_gating", "ci_cd", "CI exists, so gates have somewhere to run"),
    ("secret_containment", "secret_sensitive_files_presence",
     "secret-shaped files are present in the tree"),
    ("multi_package_coordination", "monorepo_presence",
     "a monorepo makes cross-package change a distinct operation"),
)

# Demand that arises from ABSENCE. These are the loudest signals in the graph:
# a missing test runner does not reduce verification demand, it relocates the
# work onto a human.
_ABSENCE_RULES = (
    ("verification_capability", "test_coverage_signal",
     "no test signal -- correctness is currently asserted, not observed"),
    ("release_gating", "ci_cd",
     "no CI -- every gate depends on someone remembering to run it"),
    ("project_documentation", "docs_signal",
     "no docs signal -- onboarding cost is paid per person, repeatedly"),
    ("secret_containment", "env_example_presence",
     "no .env.example -- required configuration is tribal knowledge"),
)


def capability_demand_graph(profile: ProjectProfile) -> Graph:
    """What this project will repeatedly need done.

    Demand is emitted from presence AND from absence, tagged so a consumer can
    tell them apart: `demand` is work the project's shape creates, `gap` is work
    the project's shape creates AND has no mechanism for.
    """
    g = Graph("capability_demand")
    seen: set = set()
    for token, fname, why in _DEMAND_RULES:
        if _on(profile, fname) and token not in seen:
            seen.add(token)
            g.nodes.append(Node(token, "demand", _src(profile, fname), why))
            g.edges.append(Edge(fname, token, "creates_demand",
                                _src(profile, fname)))
    for token, fname, why in _ABSENCE_RULES:
        if not _on(profile, fname):
            node_id = token if token not in seen else f"{token}:unmet"
            g.nodes.append(Node(node_id, "gap", Source.INFERRED.value, why))
            g.edges.append(Edge(fname, node_id, "absence_creates_gap",
                                Source.MISSING.value))
    return g


# --- emitter 3 -------------------------------------------------------------

# (bottleneck id, field that must be ABSENT, what the human does instead)
_HUMAN_ROUTER_RULES = (
    ("manual_verification", "test_coverage_signal",
     "a person decides whether the change works"),
    ("manual_release", "ci_cd",
     "a person runs the build and remembers the order"),
    ("manual_environment_setup", "env_example_presence",
     "a person tells the next person which variables to set"),
    ("manual_context_reconstruction", "existing_claude_md",
     "a person re-explains the project at the start of every session"),
    ("manual_convention_enforcement", "lint_system",
     "a person enforces style in review"),
    ("manual_onboarding", "docs_signal",
     "a person answers the same questions repeatedly"),
)


def human_dependency_map(profile: ProjectProfile) -> Graph:
    """Where a human is currently the routing mechanism.

    This is the graph CPP-APIR exists for. The source document names the class
    directly -- *"un humano actua constantemente como router"* -- and the
    estate's own record of it is the KADOS fork session. Each node is a place
    the project spends a person on work a mechanism could hold.
    """
    g = Graph("human_dependency")
    for node_id, fname, what in _HUMAN_ROUTER_RULES:
        if not _on(profile, fname):
            g.nodes.append(Node(node_id, "human_router",
                                Source.INFERRED.value, what))
            g.edges.append(Edge("human", node_id, "performs",
                                Source.INFERRED.value))
    if _on(profile, "secret_sensitive_files_presence") and not _on(
            profile, "env_example_presence"):
        g.nodes.append(Node("manual_secret_provisioning", "human_router",
                            Source.FILE.value,
                            "secrets exist with no documented shape -- "
                            "provisioning is person-shaped"))
        g.edges.append(Edge("human", "manual_secret_provisioning", "performs",
                            Source.FILE.value))
    return g


# --- emitter 4 -------------------------------------------------------------

_RISK_RULES = (
    ("safety_critical", "payment_presence", "monetary side effects"),
    ("production_changing", "ci_cd", "a merge can reach a deployed surface"),
    ("cross_cutting", "monorepo_presence", "one change spans packages"),
    ("credential_exposure", "secret_sensitive_files_presence",
     "secret-shaped files are in the tree"),
    ("data_loss", "database_presence", "persisted state can be destroyed"),
    ("user_facing", "frontend_presence", "a defect is visible to a user"),
)


def risk_topology(profile: ProjectProfile) -> Graph:
    """What an automated write in this repo could break.

    Consumed by HR-APA-010: a capability whose risk class escalates must not be
    activated automatically in a project whose topology confirms the stake.
    """
    g = Graph("risk_topology")
    for node_id, fname, why in _RISK_RULES:
        if _on(profile, fname):
            g.nodes.append(Node(node_id, "risk", _src(profile, fname), why))
    return g


# --- the bridge ------------------------------------------------------------

def detect_runtime(profile: ProjectProfile) -> str:
    """The runtime identity `MissionContext.runtime` gates on (applicability
    gate 5). Framework beats language: it is the more specific answer."""
    fw = _f(profile, "framework_primary").value
    if fw and str(fw) in _FRAMEWORK_RUNTIME:
        return _FRAMEWORK_RUNTIME[str(fw)]
    lang = _f(profile, "language_primary").value
    return _LANGUAGE_RUNTIME.get(str(lang), "")


# (evidence token, field whose presence proves it)
_EVIDENCE_RULES = (
    ("source", "language_primary"), ("tests", "test_coverage_signal"),
    ("ci_history", "ci_cd"), ("docs", "docs_signal"),
    ("container_spec", "docker_presence"), ("database_schema", "database_presence"),
    ("dependency_manifest", "package_manager"), ("build_spec", "build_system"),
    ("project_doctrine", "existing_claude_md"),
    ("agent_config", "existing_claude_config"),
)

# (scope token, field whose presence means a live owner already holds it)
_HELD_SCOPE_RULES = (
    ("verification", "test_coverage_signal"),
    ("continuous_integration", "ci_cd"),
    ("style_enforcement", "lint_system"),
    ("formatting", "formatter"),
    ("containerization", "docker_presence"),
    ("event_activation", "existing_hooks"),
    ("command_surface", "existing_commands"),
    ("agent_surface", "existing_agents"),
    ("project_doctrine", "existing_claude_md"),
)


def available_evidence(profile: ProjectProfile) -> list:
    return [tok for tok, fname in _EVIDENCE_RULES if _on(profile, fname)]


def held_scopes(profile: ProjectProfile) -> list:
    """Scopes an incumbent already holds in THIS project.

    Feeds applicability gate 4 (REJECTED_AS_DUPLICATE). This is the executable
    form of the constitutional key: no new owner where one already holds the
    territory.
    """
    return [tok for tok, fname in _HELD_SCOPE_RULES if _on(profile, fname)]


def to_mission_context(profile: ProjectProfile, description: str = "",
                       budget_pressure: bool = False):
    """ProjectProfile -> MissionContext. The producer applicability lacked.

    Imported lazily so Setup-OS keeps working if `capability_runtime` is absent
    -- a projection must not make its consumer a hard dependency.
    """
    from modules.capability_runtime.applicability import MissionContext
    return MissionContext(
        description=description,
        available_evidence=available_evidence(profile),
        runtime=detect_runtime(profile),
        held_scopes=held_scopes(profile),
        budget_pressure=budget_pressure,
    )


def emit_all(profile: ProjectProfile) -> dict:
    """Every graph plus the mission-context projection, as plain dicts."""
    return {
        "project": _f(profile, "project_name").value,
        "runtime": detect_runtime(profile),
        "available_evidence": available_evidence(profile),
        "held_scopes": held_scopes(profile),
        "graphs": {g.name: g.to_dict() for g in (
            architecture_graph(profile), capability_demand_graph(profile),
            human_dependency_map(profile), risk_topology(profile))},
    }


def summarize(emitted: dict) -> str:
    graphs = emitted.get("graphs", {})
    gaps = [n for n in graphs.get("capability_demand", {}).get("nodes", [])
            if n.get("kind") == "gap"]
    humans = graphs.get("human_dependency", {}).get("nodes", [])
    risks = graphs.get("risk_topology", {}).get("nodes", [])
    return (f"{emitted.get('project')}: runtime={emitted.get('runtime') or 'unknown'}, "
            f"evidence={len(emitted.get('available_evidence', []))}, "
            f"held_scopes={len(emitted.get('held_scopes', []))}, "
            f"demand_gaps={len(gaps)}, human_routers={len(humans)}, "
            f"risk_nodes={len(risks)}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Project Intelligence graph emitters (CPP-APIR DS02)")
    ap.add_argument("--path", default=".")
    ap.add_argument("--graph", default="all",
                    choices=["all", "architecture", "capability_demand",
                             "human_dependency", "risk_topology"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--mission", default="",
                    help="emit the MissionContext this project projects to")
    args = ap.parse_args(argv)

    profile = scan(args.path)
    emitted = emit_all(profile)

    if args.mission:
        ctx = to_mission_context(profile, args.mission)
        print(json.dumps({"description": ctx.description,
                          "runtime": ctx.runtime,
                          "available_evidence": ctx.available_evidence,
                          "held_scopes": ctx.held_scopes}, indent=2))
        return 0
    if args.json:
        out = emitted if args.graph == "all" else emitted["graphs"][args.graph]
        print(json.dumps(out, indent=2))
        return 0

    print(summarize(emitted))
    for name, g in emitted["graphs"].items():
        if args.graph not in ("all", name):
            continue
        print(f"\n[{name}] {len(g['nodes'])} nodes / {len(g['edges'])} edges")
        for n in g["nodes"]:
            detail = f" -- {n['detail']}" if n.get("detail") else ""
            print(f"  {n['id']} ({n['kind']}, {n['source']}){detail}")
    return 0


__all__ = [
    "Node", "Edge", "Graph", "architecture_graph", "capability_demand_graph",
    "human_dependency_map", "risk_topology", "detect_runtime",
    "available_evidence", "held_scopes", "to_mission_context", "emit_all",
    "summarize",
]

if __name__ == "__main__":
    raise SystemExit(main())
