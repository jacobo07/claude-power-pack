# Agent Registry — AI SaaS Product Development

## Identity

| Field | Value |
|---|---|
| Document ID | AGENT-REG-AISAAS-001 |
| Version | 1.0.0 |
| Skill ID | SKILL-AISAAS-001 |
| Dataset IDs | DS-SAAS-001, DS-AI-001, DS-GSD-001 |
| Total Candidate Agents | 10 |
| Compilation Date | 2026-02-28 |

## Agent Definitions

### Agent 1: Product Validator

| Field | Value |
|---|---|
| Agent ID | AGENT-AISAAS-001 |
| Role | Validates product ideas against market pain points |
| Input | Product concept description, target market, competitor landscape |
| Output | Validation report with pain-point score, demand signals, go/no-go recommendation |
| Knowledge Files | aisaas_product_strategy.json |
| Constraints | Cannot approve without evidence of "will you pay?" validation |
| Risk | Low — advisory only, no code generation |

### Agent 2: Architecture Selector

| Field | Value |
|---|---|
| Agent ID | AGENT-AISAAS-002 |
| Role | Recommends and configures technical stack based on product requirements |
| Input | Product requirements, team size, budget, timeline |
| Output | Stack recommendation with rationale, dependency list, scaffold command |
| Knowledge Files | aisaas_technical_architecture.json |
| Constraints | Must recommend scrappy-first for unvalidated products |
| Risk | Medium — generates configuration files and project structure |

### Agent 3: Context Engineer

| Field | Value |
|---|---|
| Agent ID | AGENT-AISAAS-003 |
| Role | Optimizes AI context management across sessions |
| Input | Current claude.md, skill inventory, MCP configuration, context usage metrics |
| Output | Optimized claude.md, skill curation report, context budget analysis |
| Knowledge Files | aisaas_ai_llm_integration.json |
| Constraints | Must not exceed 50% context window; must use progressive disclosure |
| Risk | Medium — modifies configuration files |

### Agent 4: UI Vibe-Coder

| Field | Value |
|---|---|
| Agent ID | AGENT-AISAAS-004 |
| Role | Rapid frontend implementation using vibe-coding methodology |
| Input | Feature spec, API endpoints (verified working), design reference |
| Output | Functional UI components with tested API connections |
| Knowledge Files | aisaas_frontend_ux_vibe_coding.json |
| Constraints | API must be verified working before UI generation; plan mode for multi-table features |
| Risk | Medium — generates code; requires Git review after every edit |

### Agent 5: Pricing Architect

| Field | Value |
|---|---|
| Agent ID | AGENT-AISAAS-005 |
| Role | Designs monetization models and pricing strategies |
| Input | Product type, target market, value proposition, competitor pricing |
| Output | Pricing model with ROI projections, tier structure, "investment" framing |
| Knowledge Files | aisaas_monetization_pricing.json |
| Constraints | Must calculate ROI using lead-value or time-saved formula; must use "investment" framing |
| Risk | Low — advisory only, generates pricing documents |

### Agent 6: Launch Commander

| Field | Value |
|---|---|
| Agent ID | AGENT-AISAAS-006 |
| Role | Executes launch strategy with manual-first onboarding |
| Input | Product (built), target user list, team structure |
| Output | Launch playbook, onboarding scripts, adoption milestones, champion identification |
| Knowledge Files | aisaas_launch_growth_distribution.json |
| Constraints | Must complete 10 manual onboards before broad launch; must address team fears |
| Risk | Medium — may send outbound communications (requires human-in-loop) |

### Agent 7: GSD Orchestrator (Extension)

| Field | Value |
|---|---|
| Agent ID | AGENT-AISAAS-007 |
| Role | Coordinates GSD lifecycle across all project phases |
| Input | Project state (STATE.md), current phase, roadmap |
| Output | Phase coordination, subagent delegation, wave execution plans |
| Knowledge Files | aisaas_prompt_engineering_agent_design.json |
| Constraints | Thin orchestrator (~10-15% context); must delegate to specialized subagents |
| Risk | High — orchestrates multiple agents; requires checkpoint protocol |

### Agent 8: Anti-Pattern Auditor

| Field | Value |
|---|---|
| Agent ID | AGENT-AISAAS-008 |
| Role | Scans project for documented failure modes and anti-patterns |
| Input | Codebase, configuration files, deployment setup, team practices |
| Output | Audit report with severity-ranked findings and mitigation plans |
| Knowledge Files | aisaas_anti_patterns_failure_prevention.json |
| Constraints | CRITICAL findings = BLOCK; must scan all 93 documented patterns |
| Risk | Low — read-only analysis, no code modification |

### Agent 9: Memory System Architect

| Field | Value |
|---|---|
| Agent ID | AGENT-AISAAS-009 |
| Role | Designs and configures hybrid memory systems for AI applications |
| Input | Application type, data volume, privacy requirements, budget |
| Output | Memory architecture (vector + keyword), sanitization pipeline, hooks configuration |
| Knowledge Files | aisaas_technical_architecture.json, aisaas_ai_llm_integration.json |
| Constraints | Must include PII/API key sanitization; must use temporal decay; must implement deduplication |
| Risk | High — handles sensitive data; requires automatic scrubbing |

### Agent 10: Skill Compiler

| Field | Value |
|---|---|
| Agent ID | AGENT-AISAAS-010 |
| Role | Compiles new skills from datasets following governance protocol |
| Input | Raw dataset files, target domain, governance chain |
| Output | Complete skill directory (SKILL.md, knowledge/, governance/, intelligence/) |
| Knowledge Files | All knowledge files |
| Constraints | Must follow DIF 8-step protocol; must generate all mandatory artifacts; must validate against governance |
| Risk | High — creates governance-binding files; requires full validation pipeline |

## Agent Interaction Matrix

| Agent | Can Delegate To | Must Not Delegate To |
|---|---|---|
| GSD Orchestrator | All agents | — |
| Product Validator | Pricing Architect | UI Vibe-Coder |
| Architecture Selector | Memory System Architect | Launch Commander |
| Context Engineer | Anti-Pattern Auditor | Pricing Architect |
| UI Vibe-Coder | Anti-Pattern Auditor | Product Validator |
| Pricing Architect | — | All (advisory only) |
| Launch Commander | — | Architecture Selector |
| Anti-Pattern Auditor | — | All (read-only) |
| Memory System Architect | Context Engineer | Product Validator |
| Skill Compiler | Anti-Pattern Auditor | Launch Commander |

## Anti-Drift Declaration
- Version: 1.0.0
- Created: 2026-02-28
- Frozen: YES (after deployment)
- Modification requires: version increment + changelog + re-validation
- Parent governance: MEGA_GOVERNANZA_AISAAS.md
