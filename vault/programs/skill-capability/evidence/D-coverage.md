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
- plane gex44: 185 skills, recorded live; node kobicraft-gex44, measured_at 2026-10-03T18:28:57Z, command: python3 tools/skill_coverage.py --measure-live --host gex44
  counts: commands_excluded 86, dangling_symlinks 1, dirs_without_skill_md 24, entries 186, skill_dirs 185

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

## Plane gex44

Coverage: opportunity_detector 1, card 1, none 183. Criticality: high 11, medium 5, low 169.

| criticality \ coverage | opportunity_detector | card | none |
|---|---|---|---|
| high | 1 | 1 | 9 |
| medium | 0 | 0 | 5 |
| low | 0 | 0 | 169 |

High criticality, coverage none (9): claude-power-pack, develop-here-prove-there, evaluation-corpus-governance, guard-event-reachability, instrument-before-claim, monetary-quantity-integrity, presence-is-not-residency, real-context-reachability, recurring-work-cardinality

| skill | coverage | coverage evidence | criticality | criticality evidence | heat_map |
|---|---|---|---|---|---|
| ads | none |  | low |  | no |
| adversarial-longevity | none |  | low |  | yes |
| agent-reach | none |  | low |  | no |
| algorithmic-art | none |  | low |  | no |
| android-reverse-engineering | none |  | medium | activation@repo CLAUDE.md:41; activation@repo CLAUDE.md:46; activation@repo CLAUDE.md:47; activation@repo CLAUDE.md:58 | no |
| anydesign | none |  | low |  | no |
| artifacts-builder | none |  | low |  | yes |
| autofix | none |  | low |  | no |
| autoresearch | none |  | low |  | yes |
| bmad | none |  | low |  | no |
| brand-guidelines | none |  | low |  | yes |
| building-ai-saas-products | none |  | low |  | yes |
| canvas-design | none |  | low |  | yes |
| carl-help | none |  | low |  | no |
| carl-manager | none |  | low |  | yes |
| claude-power-pack | none |  | high | hard_rule@gex44 ~/.claude/CLAUDE.md:15; activation@gex44 ~/.claude/CLAUDE.md:101 | yes |
| claude-power-pack.pre-clone-2026-09-27 | none |  | low |  | no |
| code-auditor | none |  | low |  | yes |
| code-review | none |  | low |  | no |
| code-reviewer | none |  | low |  | yes |
| competitive-ads-extractor | none |  | low |  | no |
| composition-patterns | none |  | low |  | no |
| compound-learnings | none |  | low |  | no |
| concurrent-writers-shared-tree | opportunity_detector | hooks/doctrine_cards.js:428 (PreToolUse-Bash-chain @ hooks/hook-dispatcher.js:433); tools/skill_opportunity_signals.py:29 | high | rule_stub@gex44 ~/.claude/rules/concurrent-writers-shared-tree.md:3 | no |
| content-research-writer | none |  | low |  | no |
| copywriting | none |  | low |  | no |
| cpp-pro | none |  | low |  | yes |
| custom skills | none |  | low |  | no |
| debugging-wizard | none |  | low |  | yes |
| design-taste-frontend | none |  | low |  | no |
| destructive-state-authorization | card | hooks/destructive_doctrine_card.js:61 (PreToolUse-Bash-chain @ hooks/hook-dispatcher.js:427) | high | rule_stub@gex44 ~/.claude/rules/destructive-state-authorization.md:3 | no |
| develop-here-prove-there | none |  | high | rule_stub@gex44 ~/.claude/rules/develop-here-prove-there.md:3 | no |
| dios-segun-buda | none |  | low |  | no |
| doc-coauthoring | none |  | low |  | no |
| elevenlabs-music-generation | none |  | low |  | no |
| elixir-phoenix-patterns | none |  | low |  | no |
| embedded-systems | none |  | low |  | yes |
| evaluation-corpus-governance | none |  | high | rule_stub@gex44 ~/.claude/rules/evaluation-corpus-governance.md:3 | no |
| fix | none |  | low |  | yes |
| frontend-design | none |  | low |  | yes |
| game-feel-codex | none |  | low |  | yes |
| generating-hook-matrix | none |  | low |  | no |
| github-actions-templates | none |  | low |  | no |
| governance-overlay | none |  | low |  | yes |
| gsd-add-tests | none |  | low |  | no |
| gsd-ai-integration-phase | none |  | low |  | no |
| gsd-audit-fix | none |  | low |  | no |
| gsd-audit-milestone | none |  | low |  | no |
| gsd-audit-uat | none |  | low |  | no |
| gsd-autonomous | none |  | low |  | no |
| gsd-capture | none |  | low |  | no |
| gsd-cleanup | none |  | low |  | no |
| gsd-code-review | none |  | low |  | no |
| gsd-complete-milestone | none |  | low |  | no |
| gsd-config | none |  | low |  | no |
| gsd-debug | none |  | low |  | no |
| gsd-discuss-phase | none |  | low |  | no |
| gsd-docs-update | none |  | low |  | no |
| gsd-eval-review | none |  | low |  | no |
| gsd-execute-phase | none |  | low |  | no |
| gsd-explore | none |  | low |  | no |
| gsd-extract-learnings | none |  | low |  | no |
| gsd-fast | none |  | low |  | no |
| gsd-forensics | none |  | low |  | no |
| gsd-graphify | none |  | low |  | no |
| gsd-health | none |  | low |  | no |
| gsd-help | none |  | low |  | no |
| gsd-import | none |  | low |  | no |
| gsd-inbox | none |  | low |  | no |
| gsd-ingest-docs | none |  | low |  | no |
| gsd-manager | none |  | low |  | no |
| gsd-map-codebase | none |  | low |  | no |
| gsd-mempalace-capture | none |  | low |  | no |
| gsd-mempalace-recall | none |  | low |  | no |
| gsd-milestone-summary | none |  | low |  | no |
| gsd-mvp-phase | none |  | low |  | no |
| gsd-new-milestone | none |  | low |  | no |
| gsd-new-project | none |  | low |  | no |
| gsd-next | none |  | low |  | no |
| gsd-ns-context | none |  | low |  | no |
| gsd-ns-ideate | none |  | low |  | no |
| gsd-ns-manage | none |  | low |  | no |
| gsd-ns-project | none |  | low |  | no |
| gsd-ns-review | none |  | low |  | no |
| gsd-ns-workflow | none |  | low |  | no |
| gsd-onboard | none |  | low |  | no |
| gsd-pause-work | none |  | low |  | no |
| gsd-phase | none |  | low |  | no |
| gsd-plan-phase | none |  | low |  | no |
| gsd-plan-review-convergence | none |  | low |  | no |
| gsd-pr-branch | none |  | low |  | no |
| gsd-profile-user | none |  | low |  | no |
| gsd-progress | none |  | low |  | no |
| gsd-quick | none |  | low |  | no |
| gsd-quick-batch | none |  | low |  | no |
| gsd-resume-work | none |  | low |  | no |
| gsd-review | none |  | low |  | no |
| gsd-review-backlog | none |  | low |  | no |
| gsd-secure-phase | none |  | low |  | no |
| gsd-settings | none |  | low |  | no |
| gsd-ship | none |  | low |  | no |
| gsd-sketch | none |  | low |  | no |
| gsd-spec-phase | none |  | low |  | no |
| gsd-spike | none |  | low |  | no |
| gsd-stats | none |  | low |  | no |
| gsd-surface | none |  | low |  | no |
| gsd-thread | none |  | low |  | no |
| gsd-ui-phase | none |  | low |  | no |
| gsd-ui-review | none |  | low |  | no |
| gsd-ultraplan-phase | none |  | low |  | no |
| gsd-undo | none |  | low |  | no |
| gsd-update | none |  | low |  | no |
| gsd-validate-phase | none |  | low |  | no |
| gsd-verify-work | none |  | low |  | no |
| gsd-workspace | none |  | low |  | no |
| gsd-workstreams | none |  | low |  | no |
| guard-event-reachability | none |  | high | rule_stub@gex44 ~/.claude/rules/guard-event-reachability.md:3 | no |
| humanizer | none |  | low |  | no |
| image-calco | none |  | low |  | no |
| image-to-video | none |  | low |  | no |
| instrument-before-claim | none |  | high | rule_stub@gex44 ~/.claude/rules/instrument-before-claim.md:3 | no |
| internal-comms | none |  | low |  | no |
| java-architect | none |  | low |  | yes |
| kobiicraft-debug | none |  | low |  | yes |
| kobiicraft-dev | none |  | low |  | yes |
| kobiicraft-execution | none |  | low |  | yes |
| kobiicraft-ops | none |  | low |  | yes |
| kobiicraft-prd | none |  | low |  | yes |
| kobiicraft-product | none |  | low |  | yes |
| kobiicraft-review | none |  | low |  | yes |
| kobiicraft-testing | none |  | low |  | yes |
| lateral-thinking | none |  | low |  | no |
| leverage-research | none |  | low |  | no |
| ll-revenue-reinforcing | none |  | low |  | no |
| managing-sleepy-skills | none |  | low |  | yes |
| marketing-psychology | none |  | low |  | no |
| mcp-builder | none |  | low |  | yes |
| meeting-insights-analyzer | none |  | low |  | no |
| minecraft-android-renderer-stack | none |  | low |  | no |
| minecraft-mod-jar-patcher | none |  | low |  | no |
| mobile-app-ui-design | none |  | medium | activation@repo CLAUDE.md:36 | no |
| mobile-game-wii-port | none |  | medium | activation@repo CLAUDE.md:52; activation@repo CLAUDE.md:58; activation@repo CLAUDE.md:59 | no |
| monetary-quantity-integrity | none |  | high | rule_stub@gex44 ~/.claude/rules/monetary-quantity-integrity.md:3 | no |
| motion-promo | none |  | medium | activation@repo CLAUDE.md:18; activation@repo CLAUDE.md:25 | no |
| on-device-verification-loop | none |  | low |  | no |
| pojavlauncher-headless-driver | none |  | low |  | no |
| presence-is-not-residency | none |  | high | rule_stub@gex44 ~/.claude/rules/presence-is-not-residency.md:3 | no |
| project-bootstrapper | none |  | low |  | yes |
| project-pulse | none |  | low |  | yes |
| prompt-engineering-patterns | none |  | low |  | no |
| python-best-practices | none |  | low |  | yes |
| python-pro | none |  | low |  | yes |
| react-best-practices | none |  | low |  | no |
| real-context-reachability | none |  | high | rule_stub@gex44 ~/.claude/rules/real-context-reachability.md:3 | no |
| recurring-work-cardinality | none |  | high | rule_stub@gex44 ~/.claude/rules/recurring-work-cardinality.md:3 | no |
| remotion-best-practices | none |  | low |  | no |
| remotion-discovery-trap | none |  | low |  | no |
| remotion-foundation | none |  | low |  | no |
| remotion-kobii-templates | none |  | low |  | no |
| secrets-management | none |  | low |  | no |
| seo | none |  | low |  | no |
| session-handoff-protocol | none |  | low |  | no |
| skill-creator | none |  | low |  | yes |
| skill-prompt-efficiency-001 | none |  | low |  | yes |
| skill-share | none |  | low |  | no |
| slack-gif-creator | none |  | low |  | no |
| sleepy-skills | none |  | low |  | no |
| social-content | none |  | low |  | no |
| social-media | none |  | low |  | no |
| software-best-practices | none |  | low |  | yes |
| spanish-mc-menus | none |  | low |  | no |
| stripe-best-practices | none |  | low |  | no |
| synced | none |  | low |  | no |
| test-master | none |  | low |  | yes |
| theme-factory | none |  | low |  | no |
| vault | none |  | low |  | no |
| video-analyzer | none |  | low |  | yes |
| vision-video | none |  | low |  | no |
| voice-spec-lock | none |  | low |  | yes |
| web-design-guidelines | none |  | low |  | no |
| webapp-testing | none |  | low |  | no |
| wii-dev-best-practices | none |  | medium | activation@repo CLAUDE.md:59 | yes |
| wii-dev-skills | none |  | low |  | no |
| wii-disc-reconstruction | none |  | low |  | no |
| wii-power-pack | none |  | low |  | no |

## Commands

command: python3 tools/test_skill_coverage.py   (check; `python` on the laptop)
command: python3 tools/test_skill_coverage.py --write-evidence   (render this file)
command: python3 tools/skill_coverage.py --measure-live --host <label>   (record a live plane; reads that host's home directory)
