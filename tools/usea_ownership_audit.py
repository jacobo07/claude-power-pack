#!/usr/bin/env python3
"""USEA constitutional-law ownership audit.

LAW IV requires every important responsibility to have one legitimate
architectural owner, and section 9 requires that a new component earn its
existence against the owners that already exist.

This audit answers, for each of the fifteen constitutional laws: does Claude
Power Pack already own this, and where. It is executable rather than prose
because a hand-written ownership table is a snapshot of somebody's memory --
it cannot notice when an owner is deleted, renamed, or was never there. This
one fails.

Verdicts follow the constitution's own vocabulary (section 3):
    REUSE       an existing owner satisfies the law as-is
    EXTEND      an owner exists and needs additional reach
    CONNECT     owners exist but nothing composes them
    NEW         no legitimate owner can satisfy the responsibility

A NEW verdict requires evidence, and this tool's job is to make that evidence
hard to fake: a law is only claimed as owned if the cited artifact is on disk.

Exit codes mirror the corpus gate's discipline -- a run that broke has not
judged anything:
    0  audit ran, every cited owner resolves
    1  audit ran, one or more cited owners are MISSING (the claim is false)
    4  the audit itself failed
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Law:
    numeral: str
    name: str
    verdict: str
    owners: list[str]
    gap: str = ""
    resolved: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)


# The mapping is a CLAIM. Every path below is checked against the filesystem;
# an unresolvable path is reported as a false claim rather than quietly dropped.
LAWS: list[Law] = [
    Law("I", "REALITY FIRST", "REUSE",
        ["modules/sdd_os", "modules/error_prevention/premise_verifier.py",
         "modules/repo_identity/identity.py"],
        gap="Reality Scan is doctrine in CLAUDE.md, not a callable obligation."),
    Law("II", "ARCHITECTURAL TRUTH", "EXTEND",
        ["modules/arch-decision", "modules/architecture_horizon",
         "modules/contract_fabric"],
        gap="Nothing distinguishes 'target reached' from 'reached through a "
            "valid architectural state'. This is the thinnest coverage found."),
    Law("III", "EMPIRICAL AUTHORITY", "REUSE",
        ["modules/oracle/ovo-protocol.md", "modules/intent_verified"]),
    Law("IV", "OWNERSHIP", "REUSE",
        ["modules/duplicate_to_advantage/d2a_engine.py", "modules/spec_gate/gate.py"]),
    Law("V", "MINIMUM SUFFICIENT CHANGE", "REUSE",
        ["modules/one_shot/compiler.py", "modules/one_shot/lock.py"]),
    Law("VI", "DETERMINISTIC SUPREMACY", "REUSE",
        ["modules/oracle/ovo-protocol.md", "modules/uqf"]),
    Law("VII", "VERSION TRUTH", "REUSE",
        ["modules/dependency_sovereignty/sovereignty.py"]),
    Law("VIII", "FAILURE AS EVIDENCE", "REUSE",
        ["modules/cascade_prevention/engine.py", "modules/drift_registry"]),
    Law("IX", "NO VAPOR DONE", "EXTEND",
        ["modules/done_gate/artifact_done_gate.py", "modules/output_contracts"],
        gap="Completion is binary (done / not done). The constitution's "
            "section 26 defines THIRTEEN graded states and forbids claiming a "
            "stronger one than evidence supports. No owner grades a claim."),
    Law("X", "PRODUCTION REALITY", "REUSE",
        ["modules/sleepless_qa", "modules/deployment"]),
    Law("XI", "NEGATIVE CAPABILITY", "REUSE",
        ["modules/duplicate_to_advantage", "modules/hard_rules/residual.py"]),
    Law("XII", "SCOPE-AWARE LEARNING", "REUSE",
        ["modules/recall_roi", "modules/fable_distillation"]),
    Law("XIII", "NO SILENT REGRESSION", "REUSE",
        ["modules/sqi", "modules/liveness/reachability.py"]),
    Law("XIV", "CAUSAL REPAIR", "REUSE",
        ["modules/cascade_prevention", "modules/error_prevention"]),
    Law("XV", "INFORMATION EFFICIENCY", "REUSE",
        ["modules/token-optimizer", "modules/cognitive_load", "modules/recall_roi"]),
]

# The incumbent for the completeness half of the constitution. Named separately
# because it is a global skill, not a Power Pack module, and an audit scoped to
# modules/ would not see it -- which is how a duplicate gets built.
INCUMBENT = Path.home() / ".claude" / "skills" / "software-best-practices" / "instructions.md"

# --- the ROLE axis ---------------------------------------------------------
#
# The constitution also describes eight conceptual SPECIALIST ROLES. That is a
# different question from the fifteen laws above: a law asks "who owns this
# responsibility", a role asks "must this be a standing agent, and can anything
# reach it".
#
# The expensive mistake this table exists to refuse is creating eight agents to
# match eight headings. A conceptual role is not a required persistent agent,
# and the verdict ladder is ordered by cost:
#     REUSE_AGENT   a dispatchable agent already owns it
#     REUSE_SYSTEM  a non-agent system owns it better than an agent would
#     DYNAMIC       a competence composed per task, with no standing identity
#     EXTEND        an owner exists and needs more reach
#     CONNECT       owners exist and nothing composes them
#     NEW_AGENT     the most expensive verdict; needs evidence, not symmetry
LIVE_AGENT_DIR = Path.home() / ".claude" / "agents"
REPO_AGENT_DIR = REPO_ROOT / "agents"

# Provided by the harness rather than by a file. Judging these by filesystem
# presence would report the estate's most-used specialists as missing.
BUILTIN_AGENTS = frozenset({"Explore", "Plan", "general-purpose", "claude"})

# An agent that is in the repo and NOT dispatchable is dormant. That is a legal
# state -- HR-001 forbids this repo from installing into ~/.claude, so the
# activation step is the Owner's -- but it is only legal if the file SAYS so.
# Silence is not an exemption (Liveness Standard), and the difference between
# "deliberately parked" and "nobody noticed" is exactly what this string carries.
DORMANCY_MARK = "activate globally by copying into"


@dataclass
class Role:
    letter: str
    name: str
    verdict: str
    owners: list[str]
    rationale: str = ""
    resolved: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    dormant: list[str] = field(default_factory=list)


ROLES: list[Role] = [
    Role("A", "PRINCIPAL ARCHITECT", "DYNAMIC",
         ["modules/arch-decision", "modules/contract_fabric", "parts/core.md"],
         "One canonical architectural authority already exists and it is the "
         "main thread. A standing orchestrator agent would be a SECOND writer "
         "of architectural truth, which LAW IV forbids -- the role is real and "
         "an agent for it would be a duplicate."),
    Role("B", "REALITY & FORENSICS", "REUSE_AGENT",
         ["agent:Explore", "agent:gsd-codebase-mapper",
          "modules/repo_identity/identity.py",
          "modules/error_prevention/premise_verifier.py"],
         "Repository archaeology is the single best-owned role in the estate."),
    Role("C", "IMPLEMENTATION", "DYNAMIC",
         ["agent:gsd-executor", "modules/one_shot/compiler.py"],
         "The implementer is whoever holds the write authority for the change; "
         "delegating it to a standing agent separates the decision from the "
         "hand, which is where architectural drift starts."),
    Role("D", "VERIFICATION / ADVERSARIAL", "REUSE_SYSTEM",
         ["tools/verify_spp.py", "vault/governance/mutation_ratchet.json",
          "agent:pp-code-reviewer", "agent:woz"],
         "Deterministic verification belongs to a system, not an agent: an "
         "oracle that can be argued with is not an oracle. The agents here are "
         "for the adversarial half, where judgement is the point."),
    Role("E", "CAUSAL FAILURE", "REUSE_AGENT",
         ["agent:pp-ceps-analyst", "agent:pp-cascade-guard",
          "agent:gsd-debugger", "modules/cascade_prevention/engine.py"],
         "Competing-hypothesis work benefits from a separate context, because "
         "the session that built the defect is the worst judge of it."),
    Role("F", "KNOWLEDGE / RESEARCH", "REUSE_AGENT",
         ["agent:graphify-librarian", "agent:pp-never-again",
          "modules/graphify/indexer.py"],
         "Already a cheap-model locator by contract."),
    Role("G", "SECURITY / TRUST", "REUSE_SYSTEM",
         ["modules/secret_firewall", "hooks/secret_firewall_gate.js",
          "modules/hard_rules"],
         "Enforced by hooks that cannot be talked out of a verdict. The "
         "REVIEW half is thinner than the ENFORCEMENT half."),
    Role("H", "PERFORMANCE / PRODUCTION", "REUSE_SYSTEM",
         ["modules/sqi/environment_qualifier.py", "modules/sleepless_qa",
          "agent:pp-monitor"],
         "SQI-03 was orphaned until Phase V gave it a caller; the lesson is "
         "that this role's owner needs a consumer more than it needs an agent."),
]


def _agent_state(name: str, agent_dir: Path | None = None,
                 live_dir: Path | None = None) -> str:
    """LIVE / DORMANT / UNDECLARED / MISSING for one agent name.

    The two directories are injectable so the red branch can be driven against
    a SYNTHETIC population. A drill pinned to a real agent has an interest in
    that agent staying broken, and decays the day someone fixes it; a drill
    that had to create a deliberately-malformed agent inside the real
    directory would be damaging the estate to measure it.

    Dispatchability is decided by the LIVE directory, because that is what the
    Agent tool reads. A definition in this repo is a definition; it is not a
    thing anything can invoke, and the estate's liveness sweep cannot see the
    difference -- it globs agents/*.md as a SEED, so an agent is a source of
    reachability there and never a subject of it. An instrument that can only
    return one answer about a class carries no information about that class.
    """
    if name in BUILTIN_AGENTS:
        return "LIVE"
    if ((live_dir or LIVE_AGENT_DIR) / f"{name}.md").exists():
        return "LIVE"
    repo_copy = (agent_dir or REPO_AGENT_DIR) / f"{name}.md"
    if not repo_copy.exists():
        return "MISSING"
    try:
        text = repo_copy.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return "UNDECLARED"
    return "DORMANT" if DORMANCY_MARK in text else "UNDECLARED"


def audit_roles() -> list[Role]:
    for role in ROLES:
        for owner in role.owners:
            if owner.startswith("agent:"):
                state = _agent_state(owner.split(":", 1)[1])
                if state == "LIVE":
                    role.resolved.append(f"{owner}  [dispatchable]")
                elif state == "DORMANT":
                    role.dormant.append(f"{owner}  [declared dormant]")
                else:
                    role.missing.append(f"{owner}  [{state}]")
            elif (REPO_ROOT / owner).exists():
                role.resolved.append(owner)
            else:
                role.missing.append(owner)
    return ROLES


def audit_agent_population(agent_dir: Path | None = None,
                           live_dir: Path | None = None,
                           ) -> tuple[list[str], list[str], list[str]]:
    """Every agent definition in this repo, classified as a SUBJECT.

    Enumerated structurally from the directory, never from a hand list: an
    audit whose subjects are enrolled by hand measures memory, and an agent
    nobody remembered is exactly the one that needs classifying.
    """
    agent_dir = agent_dir or REPO_AGENT_DIR
    live, dormant, undeclared = [], [], []
    for path in sorted(agent_dir.glob("*.md")):
        state = _agent_state(path.stem, agent_dir=agent_dir, live_dir=live_dir)
        {"LIVE": live, "DORMANT": dormant}.get(state, undeclared).append(path.stem)
    return live, dormant, undeclared


def audit() -> tuple[list[Law], list[str]]:
    notes: list[str] = []
    for law in LAWS:
        for rel in law.owners:
            (law.resolved if (REPO_ROOT / rel).exists() else law.missing).append(rel)
    if INCUMBENT.exists():
        notes.append(f"INCUMBENT present: {INCUMBENT}")
    else:
        notes.append(f"INCUMBENT ABSENT (expected): {INCUMBENT}")
    return LAWS, notes


def main() -> int:
    try:
        laws, notes = audit()
    except Exception as exc:  # noqa: BLE001 - the audit's own failure branch
        print(f"USEA OWNERSHIP AUDIT: GATE_FAILED  {type(exc).__name__}: {exc}")
        print("  NOTE: the audit failed; ownership was NOT judged.")
        return 4

    by_verdict: dict[str, int] = {}
    total_missing = 0

    print("USEA CONSTITUTIONAL OWNERSHIP AUDIT")
    print("=" * 72)
    for law in laws:
        by_verdict[law.verdict] = by_verdict.get(law.verdict, 0) + 1
        flag = "  " if not law.missing else "!!"
        print(f"{flag} LAW {law.numeral:<5} {law.name:<28} {law.verdict}")
        for r in law.resolved:
            print(f"      ok      {r}")
        for m in law.missing:
            total_missing += 1
            print(f"      MISSING {m}   <-- ownership claim is FALSE")
        if law.gap:
            print(f"      gap:    {law.gap}")
    print("=" * 72)
    for n in notes:
        print(n)

    owned = sum(1 for lw in laws if lw.verdict == "REUSE")
    print(f"\nverdicts: {by_verdict}")
    print(f"laws already owned outright (REUSE): {owned}/{len(laws)}")
    print(f"unresolvable ownership claims: {total_missing}")
    print(f"OWNERSHIP_AUDIT_PASS={len(laws) - total_missing}/{len(laws)}")

    # --- roles ------------------------------------------------------------
    try:
        roles = audit_roles()
        live, dormant, undeclared = audit_agent_population()
    except Exception as exc:  # noqa: BLE001
        print(f"\nROLE AUDIT: GATE_FAILED  {type(exc).__name__}: {exc}")
        print("  NOTE: the role audit failed; roles were NOT judged.")
        return 4

    print("\nUSEA SPECIALIST ROLE AUDIT")
    print("=" * 72)
    role_missing = 0
    role_verdicts: dict[str, int] = {}
    for role in roles:
        role_verdicts[role.verdict] = role_verdicts.get(role.verdict, 0) + 1
        flag = "!!" if role.missing else "  "
        print(f"{flag} ROLE {role.letter}  {role.name:<28} {role.verdict}")
        for r in role.resolved:
            print(f"      ok      {r}")
        for d in role.dormant:
            print(f"      dormant {d}")
        for m in role.missing:
            role_missing += 1
            print(f"      MISSING {m}   <-- ownership claim is FALSE")
        if role.rationale:
            print(f"      why:    {role.rationale}")

    print("=" * 72)
    print("AGENT POPULATION (this repo's definitions, judged as SUBJECTS)")
    print(f"  dispatchable      : {len(live)}  {live}")
    print(f"  declared dormant  : {len(dormant)}")
    print(f"  UNDECLARED        : {len(undeclared)}  {undeclared}")

    new_agents = role_verdicts.get("NEW_AGENT", 0)
    print(f"\nrole verdicts: {role_verdicts}")
    print(f"new persistent agents required by this audit: {new_agents}")
    print(f"ROLE_AUDIT_PASS={len(roles) - role_missing}/{len(roles)}")

    # A floor, so a sweep that silently matched nothing cannot report a clean
    # bill. An empty population satisfies "zero undeclared" perfectly.
    if not (live or dormant or undeclared):
        print("\nFLOOR BREACHED: the agent sweep found no definitions at all. "
              "That is an instrument failure, not a clean estate.")
        return 4

    if undeclared:
        print("\nAn UNDECLARED agent is defined here, is not dispatchable, and "
              "says nothing about why. Either it is reachable and the claim is "
              "wrong, or it is parked and must say so -- silence is not an "
              "exemption (Liveness Standard).")

    if total_missing or role_missing or undeclared:
        print("\nAn unresolvable claim means this audit asserted an owner that is "
              "not on disk. Fix the claim, not the number.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
