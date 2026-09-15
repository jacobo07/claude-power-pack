<!-- Source: ECC v2.0.0-rc.1 (github.com/affaan-m/ECC), MIT License (c) 2026 Affaan Mustafa. Mirrored into the claude-power-pack rules taxonomy during the ECC absorption gap pass (2026-06-06). Adapted in place for PP on 2026-09-15; the ECC fleet table and its unconditional-parallelism rule described a different estate and a renamed tool. -->

# Agent Orchestration

## Status of this file

**Not mirrored to `~/.claude/rules/`, so it reaches no session.** Two of this
repo's 108 rule files are live — `common/code-review.md` and
`python/testing.md`, both carrying their ECC attribution — and this is not one
of them. Adapted rather than deleted because it belongs to a coherent absorbed
corpus, and because a file that is wrong today is a trap on the day someone
mirrors the tree wholesale.

## Available agents

**Do not maintain a list here.** PP's fleet is discovered, not declared:
`modules.mirror_discovery` enumerates it across every legitimate source root
(`agents/`, `vault/agents/`, `vendor/rtk/agents/`), and
`tools/test_install_population.py` holds the floor. As of 2026-09-15 that is 27
agents. A table in a rules file is a second denominator maintained by memory,
and this estate has now paid for that four times — a hand-enrolled file list, a
hand-declared domain root, a hand-curated install manifest, and a hand-written
identity map, each of which went quietly stale
(`PR-COVERAGE-BY-CONSTRUCTION-001`; `vault/lessons/installer-population-was-a-memory.md`).

The table this file carried until 2026-09-15 named eleven agents — planner,
architect, tdd-guide, code-reviewer, security-reviewer, build-error-resolver,
e2e-runner, refactor-cleaner, doc-updater, rust-reviewer,
harmonyos-app-resolver. That list was correct **for ECC** and never described
PP: ten have never existed in this estate, and the one whose name matches
(`rust-reviewer`) is a PP agent with a different purpose. The file was not
inventing anything; it was describing a different fleet, which is why nothing
ever flagged it.

To see the current fleet: `python tools/test_install_population.py` names the
roots and the floor, and the agent frontmatter carries each one's own
dispatch criteria.

## Dispatch concurrency

The rule this file carried — *"ALWAYS use parallel Task execution for
independent operations"* — is superseded on two separate grounds, and both
matter.

It names `Task`, which the harness renamed to `Agent`. An instruction that
names a tool which no longer exists degrades silently rather than loudly
(`silent-dead-gate`).

More importantly it inverts the host constitution. On Windows the governing
rules are in `~/.claude/CLAUDE.md`:

- an `Agent` dispatch is **solo in its batch** — even one `Agent` plus one
  `Read` in the same batch produces a dropped tool result roughly half the
  time, and that dropped frame is the documented dead-screen hang;
- parallel `Agent` / `Explore` spawns are **capped at 2**, run as waves rather
  than a single fan-out;
- every long-running dispatch carries a durable-output clause and a bound, so
  a timeout costs the tail rather than the whole.

So the correct rule is: **parallelize only where causal independence and
positive ROI justify it, within the host's caps.** Unconditional parallelism is
not an optimisation here; it is the failure mode.

## Multi-perspective analysis

Retained from ECC, and still sound: for a genuinely contested problem, split
the review across roles — factual reviewer, senior engineer, security expert,
consistency reviewer, redundancy checker — rather than asking one pass to hold
every lens at once. Subject to the concurrency rules above: these are separate
dispatches, not one parallel fan-out.
