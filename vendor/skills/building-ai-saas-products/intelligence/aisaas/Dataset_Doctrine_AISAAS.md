# Dataset Doctrine — AI SaaS Product Development

## Identity

| Field | Value |
|---|---|
| Document ID | DOCTRINE-AISAAS-001 |
| Version | 1.0.0 |
| Domain | AI SaaS Product Development |
| Dataset IDs | DS-SAAS-001, DS-AI-001, DS-GSD-001 |
| Compilation Date | 2026-02-28 |
| Framework Extension | GSD (Get Shit Done) |
| Total Rules | 143 |
| Total Heuristics | 95 |

## Domain

### Bounded Domain
AI-powered SaaS product development using vibe-coding methodology, extending the GSD framework for lifecycle orchestration.

### In Scope
- Product strategy and validation
- Technical architecture (Next.js, Supabase, N8N, Stripe stacks)
- AI/LLM integration (context management, memory, skills, hooks)
- Frontend/UX rapid prototyping
- Monetization model design
- Launch and growth execution
- Prompt engineering and agent architecture
- Anti-pattern detection and failure prevention

### Excluded
- Hardware design, non-AI traditional software, physical products, academic research, cryptocurrency trading, medical/legal advice, military applications

## Rules by Category

### Product Strategy (12 rules)

1. **R-AISAAS-PS-001:** Fix the pain point manually first before automating; understand the process end-to-end
2. **R-AISAAS-PS-002:** Ask people to pay before building fully; "If I build this, will you pay?" validates demand
3. **R-AISAAS-PS-003:** Clients buy business outcomes, not automations; explain money saved/earned
4. **R-AISAAS-PS-004:** Start with an irresistible offer (even free/low cost) to validate and refine
5. **R-AISAAS-PS-005:** The pain point must be painful enough for people to pay
6. **R-AISAAS-PS-006:** Be honest if automation is impossible for a client's problem
7. **R-AISAAS-PS-007:** Do not mention "AI" when selling — focus on the business outcome
8. **R-AISAAS-PS-008:** As a founder, you must market your product — "basically done" means nothing without distribution
9. **R-AISAAS-PS-009:** Manually onboard the first 10 users before opening broadly
10. **R-AISAAS-PS-010:** The moat is specialized industry knowledge, not tool proficiency
11. **R-AISAAS-PS-011:** If something is hard to do, it is usually valuable; value shifts to domain knowledge
12. **R-AISAAS-PS-012:** What cost $50K last year now costs thousands; AI compression makes execution cheap, strategy expensive

### Technical Architecture (11 rules)

1. **R-AISAAS-TA-001:** Match database field names exactly between application code and Supabase tables
2. **R-AISAAS-TA-002:** Always save .env file after inputting variables
3. **R-AISAAS-TA-003:** Test API integrations early and in isolation before building UI
4. **R-AISAAS-TA-004:** Be specific with the agent about data formats or it will improvise
5. **R-AISAAS-TA-005:** Require the agent to mark phases done and get approval before proceeding
6. **R-AISAAS-TA-006:** Disable RLS during development, re-enable before production
7. **R-AISAAS-TA-007:** Never let a system send emails without human in the loop
8. **R-AISAAS-TA-008:** Set appropriate data retention periods
9. **R-AISAAS-TA-009:** Build and test all skills before packaging for distribution
10. **R-AISAAS-TA-010:** Test at two levels: functionality in IDE, front-end after distribution
11. **R-AISAAS-TA-011:** Bake in PII/API key sanitization automatically before storage

### AI/LLM Integration (22 rules)

1. **R-AISAAS-AI-001:** Context is finite; manage your context budget carefully
2. **R-AISAAS-AI-002:** Clear context before starting a new feature
3. **R-AISAAS-AI-003:** Use plan mode before building large features
4. **R-AISAAS-AI-004:** A skill is just a markdown file with a description — do not over-complicate
5. **R-AISAAS-AI-005:** Use progressive disclosure for MCP tools
6. **R-AISAAS-AI-006:** When running out of context, save session log and resume next session
7. **R-AISAAS-AI-007:** claude.md must contain: company overview, key processes, brand voice, data structure, tool connections
8. **R-AISAAS-AI-008:** Commit claude.md to shared repository for team-wide context
9. **R-AISAAS-AI-009:** Skills stack: one skill can trigger another
10. **R-AISAAS-AI-010:** First iteration will not be perfect; iterate until consistent
11. **R-AISAAS-AI-011:** Claude Code is an AI agent on your file system, not just a coding tool
12. **R-AISAAS-AI-012:** Analyze JSON conversation logs to improve agent memory
13. **R-AISAAS-AI-013:** Turn on verbose output to understand context and behavior
14. **R-AISAAS-AI-014:** Always review every Git change after agent edits
15. **R-AISAAS-AI-015:** Context quality determines output quality
16. **R-AISAAS-AI-016:** Hooks are deterministic; cannot be overridden by the agent
17. **R-AISAAS-AI-017:** Pre-tool hooks for guardrails, post-tool for validation, stop hooks for memory
18. **R-AISAAS-AI-018:** Skills are versioned, mountable instruction packages
19. **R-AISAAS-AI-019:** Move stable procedures into versioned modular bundles
20. **R-AISAAS-AI-020:** Update skill version and every agent follows automatically
21. **R-AISAAS-AI-021:** Run /init on a codebase to create claude.md
22. **R-AISAAS-AI-022:** Start small: verbose, Git review, backups, skills, weekly analysis

### Frontend/UX Vibe-Coding (6 rules)

1. **R-AISAAS-UX-001:** Use plan mode before building large features
2. **R-AISAAS-UX-002:** Test API integrations before building UI
3. **R-AISAAS-UX-003:** Review every Git change after agent edits
4. **R-AISAAS-UX-004:** Be specific about data formats
5. **R-AISAAS-UX-005:** Mark phases done and get approval before proceeding
6. **R-AISAAS-UX-006:** Match database field names exactly in UI components

### Monetization & Pricing (4 rules)

1. **R-AISAAS-MP-001:** Use "investment" not "cost" when describing fees
2. **R-AISAAS-MP-002:** First client free/low cost for validation
3. **R-AISAAS-MP-003:** Frame ROI so client wins more than you
4. **R-AISAAS-MP-004:** Clients care about two variables: money and time

### Launch, Growth & Distribution (6 rules)

1. **R-AISAAS-LG-001:** Manually onboard first 10 users
2. **R-AISAAS-LG-002:** You must market — "basically done" means nothing without distribution
3. **R-AISAAS-LG-003:** Start with one process to automate first
4. **R-AISAAS-LG-004:** Meet strict directory structure for marketplace upload
5. **R-AISAAS-LG-005:** Address team AI replacement fears directly
6. **R-AISAAS-LG-006:** The AI-first transformation window will not last forever

### Prompt Engineering & Agent Design (8 rules)

1. **R-AISAAS-PE-001:** Treat the agent as a potential adversary, not a trusted employee
2. **R-AISAAS-PE-002:** Skills are versioned, mountable instruction packages
3. **R-AISAAS-PE-003:** The web is forking into human web and agent web
4. **R-AISAAS-PE-004:** GSD: thin orchestrator (~10-15% context) + specialized subagents
5. **R-AISAAS-PE-005:** GSD: atomic commits per task
6. **R-AISAAS-PE-006:** GSD: STATE.md under 100 lines
7. **R-AISAAS-PE-007:** GSD: if Claude CAN automate it, Claude MUST automate it
8. **R-AISAAS-PE-008:** GSD: every plan must pass plan-checker before execution

## Heuristics (Key Patterns)

### Context Management
- DH-AISAAS-AI-001: 50 skills, use 5 → remaining 45 are noise
- DH-AISAAS-AI-005: Above 50% context → performance degrades

### Development
- DH-AISAAS-TA-001: AI-created tables match; manual tables mismatch
- DH-AISAAS-TA-005: Many things at once → issues compound

### Product Strategy
- DH-AISAAS-PS-001: Industry experience → specialized knowledge advantage
- DH-AISAAS-PS-004: Repeatable process across clients → signal to automate

### Agent Architecture
- DH-AISAAS-PE-001: Agent with wallet + search + content + payment + execution = economic actor
- DH-AISAAS-PE-005: Human fraud detection ≠ agent fraud detection

## Boundary Statements

1. This doctrine covers AI SaaS product development ONLY
2. Rules from DS-SAAS-001 and DS-AI-001 are SYNTHESIZED, not duplicated
3. GSD framework patterns are EXTENDED, not modified
4. All rules are MUST-level enforcement; violation = BLOCK
5. Namespace R-AISAAS-* is exclusive to this skill

## Memory Locks

| ID | Lock | Description |
|---|---|---|
| ML-AISAAS-001 | Domain Boundary | Cannot operate outside AI SaaS domain |
| ML-AISAAS-002 | Dataset Isolation | SaaS, AI, GSD namespaces stay isolated |
| ML-AISAAS-003 | Rule Immutability | No weakening without version increment |
| ML-AISAAS-004 | Version Pinning | All references include version numbers |
| ML-AISAAS-005 | Namespace Protection | R-AISAAS prefix cannot be reassigned |
| ML-AISAAS-006 | Checkpoint Protocol | 90/9/1 checkpoint ratios locked |
| ML-AISAAS-007 | Atomic Commit | Every task produces its own commit |
| ML-AISAAS-008 | Verification Level | 4-level verification mandatory |
| ML-AISAAS-009 | Anti-Drift | SKILL.md and MEGA_GOVERNANZA versions must match |

## References

- SaaS Dataset: 14 source files from DS-SAAS-001
- AI Dataset: 8 source files from DS-AI-001
- GSD Framework: 140+ files from get-shit-done-main repository
- Knowledge files: 8 domain JSON files in knowledge/ directory
- Governance: MEGA_GOVERNANZA_AISAAS.md

## Anti-Drift Declaration
- Version: 1.0.0
- Created: 2026-02-28
- Frozen: YES (after deployment)
- Modification requires: version increment + changelog + re-validation
- Parent governance: MEGA_GOVERNANZA_AISAAS.md
