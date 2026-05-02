# AI + SaaS + Vibe-Coding Mega Skill

## Capabilities

1. **Product Strategy & Validation** — Validate SaaS ideas via pain-point discovery, demand validation, service-to-SaaS progression
2. **Technical Architecture Design** — Compose production stacks (Next.js/Supabase/N8N/Stripe) with phased gates and API-first integration
3. **AI/LLM Integration** — Context management, skill architecture, hybrid memory systems, progressive disclosure
4. **Frontend/UX Vibe-Coding** — Rapid UI prototyping with plan-mode-first workflows and iterative refinement
5. **Monetization & Pricing** — Subscription tiers, retainer models, ROI frameworks, irresistible offers
6. **Launch & Growth** — Manual-first onboarding (first 10 users), team AI adoption, community-driven growth
7. **Prompt Engineering & Agent Design** — Multi-agent architectures with wave-based execution and checkpoint verification
8. **Anti-Pattern Detection** — Identify and prevent 93 documented failure modes with severity-based triage
9. **GSD Lifecycle Orchestration** — Discuss, plan, execute, verify lifecycle with atomic commits and subagent delegation
10. **Scaffold Generation** — Complete project structures with governance, state management, and CI/CD configs

## Governance Awareness

- **Kill Switches (16):** Budget overrun, scope creep, security violation, data leak, API abuse, context overflow, hallucination propagation, untested deployment, broken backward compat, unauthorized data access, unvalidated pricing, premature launch, agent autonomy violation, checkpoint skip, stub in production, governance bypass
- **Memory Locks (9):** Domain boundary, dataset isolation, rule immutability, version pinning, namespace protection, checkpoint protocol, atomic commit requirement, verification level minimum, anti-drift enforcement
- **Violation = BLOCK** — no exceptions without explicit override

## Workflows

### Flow 1: Idea Validation & Product Strategy

- Run pain-point discovery, validate demand with "will you pay?" test
- Classify product type (SaaS / Service / Hybrid) using service-to-SaaS progression
- Define v1 scope using avoid-loss principle
- Produce validated product brief with market positioning

### Flow 2: Technical Architecture & Stack Selection

- Select stack based on requirements and scrappy-first principle
- Design database schema with field-name matching enforcement
- Plan API integrations with early isolation testing and phased development gates
- Produce architecture document with dependency graph

### Flow 3: AI/LLM Integration Design

- Design context management strategy (budget, compaction, handoff)
- Select skill architecture pattern (Targeted Tool / Router Hub / Progressive Disclosure)
- Configure hybrid memory (vector + keyword with temporal decay) and hooks architecture (pre-tool guardrails, post-tool validation, stop-hook memory)

### Flow 4: Frontend/UX Rapid Build

- Use plan mode for feature scoping (mandatory for multi-table features)
- Implement backend-first, verify APIs before building UI
- Apply phased development with testing gates; review every Git change after agent edits

### Flow 5: Monetization & Pricing Design

- Calculate lead-value ROI (leads/month x lead value) and time-saved ROI (cost/task x frequency)
- Design pricing tiers using "investment" framing
- Structure irresistible first offer (free/low for validation), plan service-to-SaaS timeline

### Flow 6: Launch & Growth Execution

- Manual onboarding for first 10 users
- Recruit tech-savvy champions, address team AI adoption fears directly
- Build community with shared solutions and weekly touchpoints

### Flow 7: Agent Architecture & Prompt Engineering

- Define agent hierarchy: thin-orchestrator + specialized-subagent pattern
- Configure wave-based parallel execution with dependency analysis
- Implement 4-level verification (exists, substantive, wired, functional) with goal-backward checks
- Checkpoint types: 90% human-verify, 9% decision, 1% human-action

### Flow 8: Anti-Pattern Audit

- Scan project against 93 documented failure modes
- Classify by severity (CRITICAL / HIGH / MEDIUM), generate mitigation plans
- Cross-reference kill switches — any CRITICAL = BLOCK

### Flow 9: GSD Full Lifecycle

- **Discuss** — Identify gray areas, scout codebase, capture decisions in CONTEXT.md
- **Plan** — Spawn researcher + planner subagents, create atomic task plans
- **Execute** — Wave-based parallel execution with fresh context per plan
- **Verify** — Goal-backward verification, stub detection, UAT walkthrough
- Atomic commits: `{type}({phase}-{plan}): {description}`, state via STATE.md (~100 lines max)

### Flow 10: Project Scaffold

- Generate Next.js + Supabase + Stripe skeleton
- Create CLAUDE.md with project context, skills reference, governance binding
- Set up GSD state files and .planning/ directory for research and plans
