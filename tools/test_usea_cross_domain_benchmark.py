#!/usr/bin/env python3
"""Cross-domain benchmark for the USEA completeness baseline (Phase III, section 18-23).

The question this answers is not "does more process happen". It is:

    Do the universal obligations arrive in EVERY domain, while the conditional
    machinery stays off in the domains it does not serve?

Both halves are needed. A stack that activates everything everywhere scores
perfectly on recall and is worthless; a stack that activates nothing scores
perfectly on negative capability and is equally worthless. So this measures
both against one portfolio and reports the confusion matrix rather than a
single number.

SUBJECT. The real engine: modules.capability_runtime.applicability.compile_stack
over the ten contracts in vault/capability_runtime/contracts. No mock. A mock of
a router measures the mock's opinion of the router.

FIXTURES. Nine materially different classes of software -- embedded flash,
a one-line CLI text change, an HTTP persistence endpoint, credential handling,
a lost-update concurrency defect, cross-platform artifact determinism, an
unfamiliar frontend framework migration, monorepo architecture, and a
destructive deploy script. The missions are written as a working engineer would
state them. They are deliberately NOT written by reading the contracts' trigger
lists: a fixture reverse-engineered from the matcher tests only whether words
can be copied.

THE VACUITY GUARD (section 35, test-the-test). A "must not activate" assertion
is worthless if the capability never activates anywhere. Before any negative
result is counted as evidence, this suite requires the capability to have been
observed ACTIVE on at least one other fixture in the portfolio. A negative
claim about a capability that is dormant everywhere is reported UNPROVEN, never
as a pass -- that is the difference between demonstrating restraint and
demonstrating a broken engine.

WITHHELD IS NOT BLOCKED. The engine has four ways to not activate something,
and only one of them is restraint: it can judge the capability irrelevant
(NOT_APPLICABLE), rank it below the bar (AVAILABLE_ON_TRIGGER), or refuse to
judge it at all because a gate input is absent (the BLOCKED_* verdicts). The
first run of this benchmark scored zero activations across all nine fixtures
and reported flawless restraint and perfect context economy; every capability
had in fact been BLOCKED_BY_MISSING_EVIDENCE because the fixtures declared no
evidence at all. A gate that could not judge its subject must never read as a
gate that declined it, so a blocked capability is counted as UNDETERMINED here
and can satisfy no assertion in either direction.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from modules.capability_runtime.applicability import (  # noqa: E402
    MissionContext,
    compile_stack,
)

PASSES = 0
FAILS = 0


def check(gate: str, cond: bool, evidence: str) -> None:
    global PASSES, FAILS
    if cond:
        PASSES += 1
        print(f"  OK   {gate}  {evidence}")
    else:
        FAILS += 1
        print(f"  FAIL {gate}  {evidence}")


@dataclass
class Fixture:
    key: str
    domain: str
    mission: str
    runtime: str = ""
    evidence: list = field(default_factory=list)
    prereqs: list = field(default_factory=list)
    must_activate: tuple = ()
    must_not_activate: tuple = ()
    # Ceremony expectation: the absolute ceiling on how many capabilities a
    # change of this risk class may legitimately pull in. A ratio would be
    # satisfied by shrinking the contract set, so this is an absolute.
    max_activated: int = 99

    def context(self) -> MissionContext:
        return MissionContext(
            description=self.mission,
            runtime=self.runtime,
            available_evidence=self.evidence or REPO_EVIDENCE,
            satisfied_prerequisites=self.prereqs,
        )


# What a caller sitting in a real repository actually has in hand. Nine of the
# ten contracts require "source" and one also requires "tests"; a fixture that
# declares neither is not a restrained mission, it is a caller who never opened
# the project -- which is why the first run blocked all ten and read as calm.
REPO_EVIDENCE = ["source", "tests"]


# The portfolio. Diversity is the point: if these were five variants of one web
# task, universality would be asserted rather than tested.
FIXTURES = (
    Fixture(
        key="embedded",
        domain="firmware / embedded C",
        mission=(
            "Write the flash erase-program-verify routine for the STM32 bootloader. "
            "The sector must be read back and compared against the image before the "
            "slot is marked valid, because a write call returning ok is not a "
            "completed erase-program cycle."
        ),
        runtime="c",
        must_not_activate=("cdicf-installer",),
        max_activated=6,
    ),
    Fixture(
        key="trivial_cli",
        domain="CLI text change (trivial, reversible)",
        mission="Fix the spelling mistake in the --help epilog of the argument parser.",
        runtime="python",
        must_not_activate=(
            "architecture_reconstruction",
            "cdicf-installer",
            "duplicate_detection",
        ),
        max_activated=3,
    ),
    Fixture(
        key="http_persistence",
        domain="HTTP endpoint with durable side effect",
        mission=(
            "Add a POST /orders endpoint that writes the order row to the database "
            "and returns the created id. A 200 response is not proof the row "
            "committed, so the handler needs a durability check."
        ),
        runtime="python",
        max_activated=8,
    ),
    Fixture(
        key="credentials",
        domain="security-sensitive credential handling",
        mission=(
            "The deploy script has an api key and a password hardcoded in the "
            "committed config. Rotate the secret, move it to an environment "
            "variable, and make sure the credential is never written to a log."
        ),
        runtime="bash",
        must_activate=("secret_containment",),
        max_activated=8,
    ),
    Fixture(
        key="concurrency",
        domain="concurrency / lost update",
        mission=(
            "Two worker processes append entries to the same run log and one "
            "silently overwrites the other's lines. Fix the lost update so a "
            "concurrent writer cannot absorb another writer's records."
        ),
        runtime="python",
        must_not_activate=("cdicf-installer",),
        max_activated=8,
    ),
    Fixture(
        key="determinism",
        domain="cross-platform deterministic artifact",
        mission=(
            "The generated lockfile has a different checksum on the Windows CI "
            "runner than on Linux, so every build reports the file as modified. "
            "Make the generator emit identical bytes on both platforms."
        ),
        runtime="node",
        must_not_activate=("cdicf-installer",),
        max_activated=8,
    ),
    Fixture(
        key="unfamiliar_fw",
        domain="unfamiliar framework migration",
        mission=(
            "Migrate the Svelte 4 store subscriptions in the dashboard to Svelte 5 "
            "runes. Check the current release before assuming any api still exists."
        ),
        runtime="node",
        must_activate=("premise_verification",),
        max_activated=8,
    ),
    Fixture(
        key="architecture",
        domain="monorepo architecture / dependency graph",
        mission=(
            "Design the architecture reconstruction pass that extracts the "
            "dependency mapping for the monorepo, so a change can be traced to the "
            "packages it affects."
        ),
        runtime="python",
        must_activate=("architecture_reconstruction",),
        max_activated=9,
    ),
    Fixture(
        key="component_adoption",
        domain="transactional component adoption into a target project",
        mission=(
            "Install the approved design-registry component into the target project "
            "as a journalled transaction, and give me a way to revert it if the "
            "adoption goes wrong."
        ),
        runtime="node",
        # This caller really does hold these: the emitter produced them.
        evidence=["source", "tests", "install_manifest", "registry_item"],
        prereqs=["emitter_output", "target_directory"],
        must_activate=("cdicf-installer",),
        max_activated=8,
    ),
    Fixture(
        key="destructive_deploy",
        domain="destructive deploy script",
        mission=(
            "The release script runs rm -rf on the build directory and then does a "
            "deploy to production with no backup. Make the dangerous command safe."
        ),
        runtime="bash",
        must_activate=("cascade_prevention",),
        max_activated=8,
    ),
)


def main() -> int:
    stacks = {fx.key: compile_stack(fx.context()) for fx in FIXTURES}

    print("\n--- activation matrix (real engine, ten contracts) ---")
    for fx in FIXTURES:
        s = stacks[fx.key]
        print(f"  {fx.key:<19} activate={sorted(s['activate']) or '(none)'}")
        if s["dormant"]:
            print(f"  {'':<19} dormant ={sorted(s['dormant'])}")
        if s["blocked"]:
            print(f"  {'':<19} BLOCKED ={dict(sorted(s['blocked'].items()))}")

    # --- POSITIVE CONTROL --------------------------------------------------
    # An engine that returns an empty stack for every mission would satisfy
    # every negative assertion below and report flawless restraint. Prove the
    # instrument can fire at all before reading anything else it says.
    ever_active = set()
    for s in stacks.values():
        ever_active.update(s["activate"])
    check(
        "V-BENCH-POSITIVE-CONTROL",
        len(ever_active) >= 3,
        f"engine activated {len(ever_active)} distinct capabilities across the portfolio: {sorted(ever_active)}",
    )

    # --- NOTHING MAY BE JUDGED THROUGH A GATE THAT COULD NOT RUN -----------
    # A BLOCKED_* verdict says the engine declined to evaluate, not that it
    # evaluated and said no. Counting one as the other is how the first run of
    # this benchmark reported perfect restraint over an engine that had judged
    # nothing at all.
    blocked_any = {cap for s in stacks.values() for cap in s["blocked"]}
    check(
        "V-BENCH-NO-UNDETERMINED-GATES",
        not blocked_any,
        f"every contract was actually evaluated on every fixture"
        if not blocked_any
        else f"UNDETERMINED, not restraint: {sorted(blocked_any)} never reached scoring",
    )

    # The portfolio must actually span domains, or 'cross-domain' is a label.
    check(
        "V-BENCH-DIVERSITY",
        len({fx.runtime for fx in FIXTURES}) >= 4 and len(FIXTURES) >= 8,
        f"{len(FIXTURES)} fixtures across {len({fx.runtime for fx in FIXTURES})} runtimes",
    )

    # --- RECALL: required expertise reaches the domain that needs it -------
    recall_hits = recall_total = 0
    for fx in FIXTURES:
        active = set(stacks[fx.key]["activate"])
        for cap in fx.must_activate:
            recall_total += 1
            got = cap in active
            recall_hits += int(got)
            check(
                f"V-BENCH-RECALL-{fx.key.upper()}-{cap.upper().replace('_', '-')}",
                got,
                f"{fx.domain}: {cap} {'activated' if got else 'MISSING from ' + str(sorted(active))}",
            )

    # --- NEGATIVE CAPABILITY, guarded against vacuity ----------------------
    neg_proven = neg_vacuous = 0
    for fx in FIXTURES:
        active = set(stacks[fx.key]["activate"])
        for cap in fx.must_not_activate:
            if cap not in ever_active:
                # The capability never activated anywhere. Its absence here is
                # not restraint -- it is an unexercised matcher. Reporting this
                # as a pass is exactly the vacuous green section 35 forbids.
                neg_vacuous += 1
                check(
                    f"V-BENCH-NEGATIVE-{fx.key.upper()}-{cap.upper().replace('_', '-')}",
                    False,
                    f"UNPROVEN: {cap} is dormant on all {len(FIXTURES)} fixtures, so its "
                    f"absence on {fx.key} is not evidence of restraint",
                )
                continue
            neg_proven += 1
            check(
                f"V-BENCH-NEGATIVE-{fx.key.upper()}-{cap.upper().replace('_', '-')}",
                cap not in active,
                f"{fx.domain}: {cap} correctly withheld (it DOES activate elsewhere, so this is restraint)",
            )

    # --- CEREMONY SCALES WITH RISK, NOT WITH NOVELTY (section 39) ----------
    for fx in FIXTURES:
        n = len(stacks[fx.key]["activate"])
        check(
            f"V-BENCH-CEREMONY-{fx.key.upper()}",
            n <= fx.max_activated,
            f"{fx.domain}: {n} capabilities activated (ceiling {fx.max_activated})",
        )

    # The load-bearing comparison: a trivial reversible edit must not pull in
    # more machinery than a destructive production deploy.
    trivial = len(stacks["trivial_cli"]["activate"])
    risky = len(stacks["destructive_deploy"]["activate"])
    check(
        "V-BENCH-RISK-ORDERING",
        trivial <= risky,
        f"trivial CLI typo activates {trivial}, destructive deploy activates {risky}",
    )

    # --- CONTEXT ECONOMY (section 49), as an absolute not a ratio ----------
    check(
        "V-BENCH-CONTEXT-TRIVIAL",
        trivial <= 3,
        f"a one-line text change carries {trivial} capabilities of conditional context",
    )

    # --- UNIVERSALITY IS NOT DOMAIN-CONDITIONAL ----------------------------
    # The universal laws live in the always-read layer, so they are the same
    # bytes for every fixture above. Asserted here as a domain-invariance
    # claim; the inheritance chain itself is pinned by
    # tools/test_baseline_inheritance.py and is not re-litigated.
    core = _ROOT / "parts" / "core.md"
    core_text = core.read_text(encoding="utf-8") if core.exists() else ""
    check(
        "V-BENCH-UNIVERSAL-INVARIANT",
        "LAW II" in core_text and "LAW IX" in core_text,
        "LAW II and LAW IX sit in the always-read layer, identical for all "
        f"{len(FIXTURES)} domains (no per-domain copy to drift)",
    )

    print("\n--- benchmark result ---")
    print(f"  recall            : {recall_hits}/{recall_total} required activations")
    print(f"  negative capability: {neg_proven} proven, {neg_vacuous} unproven (dormant-everywhere)")
    print(f"  distinct capabilities exercised: {len(ever_active)}")
    print(f"BENCH_PASS={PASSES}/{PASSES + FAILS}  threshold={PASSES + FAILS}/{PASSES + FAILS}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
