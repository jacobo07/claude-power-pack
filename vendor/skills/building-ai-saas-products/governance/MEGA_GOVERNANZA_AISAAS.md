# MEGA GOVERNANZA — AI SaaS Product Development

## 1. Governance Identity

| Field | Value |
|---|---|
| Skill ID | SKILL-AISAAS-001 |
| Domain | AI SaaS Product Development |
| Dataset IDs | DS-SAAS-001, DS-AI-001, DS-GSD-001 |
| Version | 1.0.0 |
| Status | ACTIVE |
| Governance Date | 2026-02-28 |
| Framework Extension | GSD (Get Shit Done) |

## 2. Domain Boundaries

### In Scope

- AI-powered SaaS product design, validation, and development
- Technical architecture selection and composition (Next.js, Supabase, N8N, Stripe)
- AI/LLM integration patterns (context management, memory, skills, hooks)
- Frontend/UX rapid prototyping with vibe-coding methodology
- Monetization model design (subscription, retainer, service-to-SaaS, agent commerce)
- Launch and growth strategy (manual onboarding, team adoption, community)
- Prompt engineering and multi-agent architecture (GSD lifecycle, wave execution)
- Anti-pattern detection and failure prevention (93 documented patterns)
- GSD framework lifecycle orchestration (discuss → plan → execute → verify)
- Scaffold generation for new AI SaaS projects

### Out of Scope

| Prohibited Domain | Boundary Rule |
|---|---|
| Hardware design | R-AISAAS-BOUNDARY-001 |
| Non-AI traditional software | R-AISAAS-BOUNDARY-002 |
| Physical product manufacturing | R-AISAAS-BOUNDARY-003 |
| Academic research papers | R-AISAAS-BOUNDARY-004 |
| Cryptocurrency trading advice | R-AISAAS-BOUNDARY-005 |
| Medical/legal professional advice | R-AISAAS-BOUNDARY-006 |
| Military/weapons applications | R-AISAAS-BOUNDARY-007 |

## 3. Kill Switches (16 Total)

| ID | Condition | Action |
|---|---|---|
| KS-AISAAS-001 | Budget overrun detected (API costs exceed projected by >200%) | BLOCK — halt all API-consuming operations, present cost analysis |
| KS-AISAAS-002 | Scope creep detected (feature count exceeds v1 spec by >50%) | BLOCK — enforce requirements freeze, present scope delta |
| KS-AISAAS-003 | Security vulnerability detected (OWASP Top 10) | BLOCK — halt deployment, require security review |
| KS-AISAAS-004 | Data leak risk (PII/API keys in output or storage) | BLOCK — purge sensitive data, enforce sanitization pipeline |
| KS-AISAAS-005 | API abuse detected (rate limits exceeded or TOS violation) | BLOCK — halt API calls, review integration pattern |
| KS-AISAAS-006 | Context overflow (>80% context window consumed) | WARN — recommend compaction or new session |
| KS-AISAAS-007 | Hallucination propagation (unverified data in production output) | BLOCK — halt pipeline, require source verification |
| KS-AISAAS-008 | Untested deployment (code pushed without testing gates) | BLOCK — revert, enforce phased testing protocol |
| KS-AISAAS-009 | Backward compatibility break (API contract violated) | BLOCK — require version increment and migration plan |
| KS-AISAAS-010 | Unauthorized data access (accessing data outside scope) | BLOCK — audit trail, revoke access |
| KS-AISAAS-011 | Unvalidated pricing (revenue model launched without demand validation) | WARN — require "will you pay?" test results |
| KS-AISAAS-012 | Premature launch (fewer than 10 manual onboard users) | WARN — recommend completing manual onboarding first |
| KS-AISAAS-013 | Agent autonomy violation (agent acts outside permitted scope) | BLOCK — enforce adversarial trust model |
| KS-AISAAS-014 | Checkpoint skip (verification level not met before delivery) | BLOCK — require 4-level verification (exists → substantive → wired → functional) |
| KS-AISAAS-015 | Stub in production (placeholder code detected in deployment) | BLOCK — run stub detection, require real implementation |
| KS-AISAAS-016 | Governance bypass (rule softened from MUST to SHOULD) | BLOCK — restore original enforcement level |

## 4. Memory Locks (9 Total)

| ID | Lock | Description |
|---|---|---|
| ML-AISAAS-001 | Domain Boundary Lock | Skill cannot operate outside defined domain boundaries |
| ML-AISAAS-002 | Dataset Isolation Lock | Each dataset (SaaS, AI, GSD) maintains namespace isolation |
| ML-AISAAS-003 | Rule Immutability Lock | No rule may be weakened without version increment + changelog |
| ML-AISAAS-004 | Version Pinning Lock | All artifacts must reference specific version numbers |
| ML-AISAAS-005 | Namespace Protection Lock | ID prefixes (R-AISAAS, DH-AISAAS, etc.) cannot be reassigned |
| ML-AISAAS-006 | Checkpoint Protocol Lock | GSD checkpoint types (90/9/1) cannot be modified |
| ML-AISAAS-007 | Atomic Commit Lock | Every GSD task must produce its own atomic commit |
| ML-AISAAS-008 | Verification Level Lock | Minimum 4-level verification required for all deliverables |
| ML-AISAAS-009 | Anti-Drift Lock | Version match between SKILL.md and MEGA_GOVERNANZA required |

## 5. Recompilation Triggers

1. Any source dataset file is added, modified, or removed
2. GSD framework version is updated
3. New vertical namespace is requested
4. Kill switch threshold values change
5. Memory lock scope changes
6. Governance hierarchy changes

**On recompilation:**
- All knowledge JSON files regenerated from updated sources
- dataset-manifest.json updated with new counts and fingerprints
- SKILL.md version incremented
- MEGA_GOVERNANZA version incremented to match
- Changelog entry added

## 6. Vertical Namespaces

| Vertical | Namespace | Additive Rules |
|---|---|---|
| Legal Tech SaaS | R-AISAAS-LEGAL-XXX | Compliance automation, document processing, client intake |
| Marketing SaaS | R-AISAAS-MKTG-XXX | Content generation, campaign optimization, lead scoring |
| Developer Tools | R-AISAAS-DEVTOOL-XXX | Code generation, CI/CD, testing automation |
| E-commerce | R-AISAAS-ECOM-XXX | Product catalog AI, recommendation engines, checkout |
| Healthcare SaaS | R-AISAAS-HEALTH-XXX | HIPAA compliance, patient data, clinical workflows |
| Education Tech | R-AISAAS-EDTECH-XXX | Learning paths, content adaptation, assessment |
| FinTech | R-AISAAS-FINTECH-XXX | Risk scoring, fraud detection, agent commerce |
| Creator Economy | R-AISAAS-CREATOR-XXX | Content monetization, audience tools, UGC automation |

## 7. Audit Trail

| Event | Timestamp | Actor | Details |
|---|---|---|---|
| Initial compilation | 2026-02-28T00:00:00Z | Claude Code | 681 extractions compiled from 3 datasets (SaaS: 411, AI: 222, GSD: 48) |
| Governance created | 2026-02-28T00:00:00Z | Claude Code | 16 kill switches, 9 memory locks, 8 vertical namespaces |
| Skill registered | 2026-02-28T00:00:00Z | Claude Code | SKILL-AISAAS-001 v1.0.0 registered |

## Anti-Drift Declaration

- Version: 1.0.0
- Created: 2026-02-28
- Frozen: NO (active governance, evolves with skill)
- Modification requires: version increment + changelog + re-validation
- Parent governance: CONSTITUTION.md
