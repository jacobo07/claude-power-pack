# J creation gate evidence (skill-capability pillar J)

Rule: a new skill must declare its opportunity detector or why it has none; a gate refuses a skill directory without the declaration.

Rendered by `python3 tools/skill_creation_gate.py --render`; judged by `python3 tools/skill_creation_gate.py`.

skills_tree=6808f63a349b4fa9479dcb8e50db9b9fdce96211
population=24

| skill | declaration | coverage class | coverage evidence files | DECLARED | FORM | TARGET | COVERAGE-AGREES |
|---|---|---|---|---|---|---|---|
| agent-architecture-audit | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| agent-eval | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| agent-harness-construction | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| agent-introspection-debugging | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| agentic-os | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| android-reverse-engineering | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| autonomous-loops | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| concurrent-writers-shared-tree | hooks/doctrine_cards.js | opportunity_detector | hooks/doctrine_cards.js, tools/skill_opportunity_signals.py | PASS | PASS | PASS | PASS |
| destructive-state-authorization | none (reason: coverage class card; deny card hooks/destructive_doctrine_card.js names this skill and no CO-12 adapter declares it, so it is not an opportunity detector) | card | hooks/destructive_doctrine_card.js | PASS | PASS | PASS | PASS |
| develop-here-prove-there | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| eval-harness | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| evaluation-corpus-governance | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| guard-event-reachability | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| instrument-before-claim | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| intent-driven-development | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| mobile-app-ui-design | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| mobile-game-wii-port | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| monetary-quantity-integrity | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| motion-promo | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| presence-is-not-residency | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| real-context-reachability | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| recurring-work-cardinality | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| recursive-decision-ledger | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |
| verification-loop | none (reason: coverage class none; no registered card hook and no CO-12 adapter names this skill) | none | - | PASS | PASS | PASS | PASS |

FLOOR=PASS (population=24)
POSITIVE-CONTROL=PASS (class opportunity_detector seen for concurrent-writers-shared-tree)
