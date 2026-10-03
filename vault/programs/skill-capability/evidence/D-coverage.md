# [D] coverage + criticality -- evidence

Frozen rule (ledger pillar D): every installed skill gets a coverage class (opportunity detector / card / none) and a criticality class from a discovered sweep, never a hand list

## Rules

- Coverage rule: `card` = a PreToolUse hook registered in a `*-chain` of `hooks/hook-dispatcher.js` CHAIN_MAP whose source emits a deny (`permissionDecision` and `deny`) and names the skill as a backticked token followed by the word skill. `opportunity_detector` = card AND a `tools/*.py` adapter declaring `KIND = "capability_opportunity"` and `CAPABILITY = "<skill>"`. `none` otherwise. No class is typed per skill.
- Criticality rule: high = a moved-out global rule stub (a top-level rules/*.md that says "moved to a skill" and names the skill, live recording only) or a HARD RULES source (a `## ... HARD RULES ...` section of a CLAUDE.md, or anywhere in vault/hard_rules/HARD_RULES.md) names it; medium = a `## ... Activation Criteria ...` section of a CLAUDE.md names it and nothing high does; low = neither. A token is the skill name in backticks, or skills/<name> followed by a non-name character. The repo plane uses repo evidence only; a live plane uses repo evidence plus its own recorded evidence.
- Precedence: coverage and criticality are independent columns; a skill carries exactly one of each.
- heat_map: membership of the skill in `vault/skills_heat_map.json` (keyword suggestion by the skill-heat-map advisor). It is reported as a column and is never a coverage class: a keyword suggestion is neither a need-time opportunity judgement nor a deny card. `UNMEASURED` = the file could not be read.
- The coverage class is a property of this checkout's dispatcher. Whether a host runs that dispatcher is the pillar A live-sync item, not measured here.

## Planes

Planes are reported separately; no figure sums across planes.

- plane repo: 24 skills, discovered from `skills/*/SKILL.md`

## Plane repo

Coverage: opportunity_detector 1, card 1, none 22. Criticality: high 0, medium 4, low 20.

| criticality \ coverage | opportunity_detector | card | none |
|---|---|---|---|
| high | 0 | 0 | 0 |
| medium | 0 | 0 | 4 |
| low | 1 | 1 | 18 |

High criticality, coverage none (0): (none)

| skill | coverage | coverage evidence | criticality | criticality evidence | heat_map |
|---|---|---|---|---|---|
| agent-architecture-audit | none |  | low |  | no |
| agent-eval | none |  | low |  | no |
| agent-harness-construction | none |  | low |  | no |
| agent-introspection-debugging | none |  | low |  | no |
| agentic-os | none |  | low |  | no |
| android-reverse-engineering | none |  | medium | activation@repo CLAUDE.md:41; activation@repo CLAUDE.md:46; activation@repo CLAUDE.md:47; activation@repo CLAUDE.md:58 | no |
| autonomous-loops | none |  | low |  | no |
| concurrent-writers-shared-tree | opportunity_detector | hooks/doctrine_cards.js:428 (PreToolUse-Bash-chain @ hooks/hook-dispatcher.js:433); tools/skill_opportunity_signals.py:29 | low |  | no |
| destructive-state-authorization | card | hooks/destructive_doctrine_card.js:61 (PreToolUse-Bash-chain @ hooks/hook-dispatcher.js:427) | low |  | no |
| develop-here-prove-there | none |  | low |  | no |
| eval-harness | none |  | low |  | no |
| evaluation-corpus-governance | none |  | low |  | no |
| guard-event-reachability | none |  | low |  | no |
| instrument-before-claim | none |  | low |  | no |
| intent-driven-development | none |  | low |  | no |
| mobile-app-ui-design | none |  | medium | activation@repo CLAUDE.md:36 | no |
| mobile-game-wii-port | none |  | medium | activation@repo CLAUDE.md:52; activation@repo CLAUDE.md:58; activation@repo CLAUDE.md:59 | no |
| monetary-quantity-integrity | none |  | low |  | no |
| motion-promo | none |  | medium | activation@repo CLAUDE.md:18; activation@repo CLAUDE.md:25 | no |
| presence-is-not-residency | none |  | low |  | no |
| real-context-reachability | none |  | low |  | no |
| recurring-work-cardinality | none |  | low |  | no |
| recursive-decision-ledger | none |  | low |  | no |
| verification-loop | none |  | low |  | no |

## Commands

command: python3 tools/test_skill_coverage.py   (check; `python` on the laptop)
command: python3 tools/test_skill_coverage.py --write-evidence   (render this file)
command: python3 tools/skill_coverage.py --measure-live --host <label>   (record a live plane; reads that host's home directory)
