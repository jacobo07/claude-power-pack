# Founder OS v0 — Universal Repo-Scoped Business Round

Status: **MVP PROPOSED FOR REVIEW** (command + deterministic local journal; **not** a persistent autonomous business operator).

## Intent and ownership

Founder OS is a business-level orchestration layer for Claude Power Pack. The shared command `/cpp-founder-round` selects the **current repository**, discovers its actual business model, prioritizes a measurable constraint, carries out only reversible/authorized work, and closes with an evidence-qualified result. It must support any model or lifecycle stage. A repo can represent KobiCraft, InfinityOps, CommonWealth Ops, QuickLease, CostaLuz or an unknown future company; business names do not select hard-coded strategies.

| Concern | Existing CPP owner | New Founder OS responsibility |
|---|---|---|
| Stable repository root | `modules/repo_identity` | Compose; never create second identity algorithm |
| Generic actionable backlog | `modules/backlog_autopilot` | Add **business** hypotheses, causal evidence, ROI uncertainty and stop gates |
| Owner decisions | `modules/autonomy_gate`, `decision_review` | Apply stricter commercial/legal/privacy controls; no new permission engine |
| Long execution | `/cpp-gsd-long` | Use only when a bounded round needs multiple contexts |
| Universal validated learning | Knowledge Vault, UKDL and ratchets | Propose de-identified domain-qualified promotion, never bulk-copy company data |
| Installer | `tools/install_global_core.py` + mirror discovery | The new file in `commands/` is discovered for global installation |

## v0 protocol (implemented / not implemented)

**Implemented surface:** a global Claude Code slash command and a stdlib Python CLI with `init`, `start`, `event`, `close`, and `status`. Stored journal includes source-asserted evidence classes, round-specific proof links, an integrity hash chain, exclusive write lock, Secret Firewall redaction of metadata strings, rejection of nested payloads, and a repo-scoped private state path. It makes **zero network, API, billing, customer, production or cross-repo calls**. It does **not** execute the AI round without Claude Code invocation. No scheduler is installed.

**Deliberately deferred:** live CRM/ads/analytics adapters, sector metric plugins, verified financial calculators, real-world experiment orchestrators, automatic causal inference, persistent worker, cross-repo portfolio synthesis and Founder Skill's existing 11-skills adapter. These require proof of current interfaces, legal/privacy boundaries and testable source contracts; no adapters are to be fabricated from the earlier conceptual proposal.

## Contracts

1. **Namespace:** local state rooted at `~/.claude/state/founder-os/sha256(canonical_repo)[:32]/`. Same repo subdirectory or worktree -> same key. Distinct roots -> distinct stores. No automatic sync, no remote reads, no cross-business sharing. Cross-host sync is NOT solved by this host-local key; defer portable IDs until needed with `repo_identity.portable_repo_id`.
2. **World model:** core fields remain `UNKNOWN` unless dated source evidence exists. Each business is a separate domain model with sector-specific economics defined by a later adapter. Simulated buyers or projections cannot validate demand.
3. **Round states:** one active round per namespace. `start` refuses overlap; `close` is explicit and terminal. `BLOCKED` and `INCONCLUSIVE` are valid honest outcomes.
4. **Evidence:** journal entries are metadata with source references, NOT embedded raw customer records. Chain SHA-256 proves internal event consistency, not truth or authenticity of source claims. The agent/owner must independently inspect the source and source freshness. The shared Secret Firewall strips detected secrets from event metadata, but this does not guarantee removal of all personal data; source material must still be minimized. No external action permission is conferred by a `authorization_ref` string.
5. **Authorization:** outer policy and actual permission gates remain authoritative. A journaling command only writes local files. All external mutations require specific owner permission and are independently logged.
6. **Budget and loop:** at most 3–5 live opportunities per round, principal bottleneck first, no uncontrolled backlog growth, no unbounded inference/retries. Prefer a low-cost observation to a false confidence conclusion.
7. **Learning:** business-local observations remain business-local. Only validated, domain-qualified, privacy-safe generalizations may be proposed for existing CPP ratchets; promotion is a distinct reviewed process.
8. **Completion:** result claims must cite events from the current round, and impact needs a measurement. The journal enforces linkage and admissible evidence classes, but *not causal identification*, monetary reality, independence or outside-data authenticity. Outcome `IMPACT_VERIFIED` is an agent+owner evidence judgment, not a certificate issued by code.

## v1 progression (not silently shipped)

- Add an explicit `BusinessProfile` schema and user-confirmed mapping for monorepos and multi-repo companies; validate identity and control company/portfolio permissions.
- Adapt Founder Skill's 11 skills **after** verifying its repository and licenses; expose specialist capabilities on demand, not perpetual departments.
- Add metric ontology: funnel, acquisition, margin, cash runway, activation, churn, operational capacity, risk. Distinguish forecasts from real transactions and keep money/currency/period typed.
- Add connector contracts with least privilege, source lineage, freshness, redaction, timezone, sampling and reconciled transaction trust, never guessed availability.
- Add experiment compiler: preregistration, control/comparison where feasible, impact range, lag window, reversible execution and guardrail thresholds.
- Add portfolio layer only behind explicit business-owner grants. Patterns must be proven transferable; raw data never crosses namespaces as a default.
- Add a persistent runtime only when scheduler, liveness, checkpoint, recovery, spend policy, idempotent writes and human oversight pass independent gates. A slash command is not a daemon.

## Minimum gates

Run `python tools/test_founder_os.py` in the CPP repository (must exit 0), then perform a fresh isolated-repo dry run: initialize -> start -> record source-backed observation -> close as uncertainty reduction -> status. Repeat from a nested directory and independent second business repo. Also prove outward actions without authorization receipt are not recorded as normal internal work, spoofed/tampered journal is rejected, second simultaneous round is refused, and simulated evidence cannot justify verified outcomes.

**Reality caveat:** deterministic tests prove the *journal's behavior*, not the efficacy of the autonomous business improvements. An actual connected-company cycle with tracked before/after metrics and valid approvals is the separate Production Reality Gate.
