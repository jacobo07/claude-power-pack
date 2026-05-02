#!/usr/bin/env node

/**
 * scaffold-saas-project.js
 *
 * Generates a complete AI SaaS project structure with GSD framework integration,
 * governance binding, and Claude Code skill configuration.
 *
 * Usage: node scaffold-saas-project.js <project-name> [--stack next-supabase|next-prisma|n8n-sheets]
 *
 * Skill: SKILL-AISAAS-001 v1.0.0
 * Framework: GSD (Get Shit Done) Extension
 */

const fs = require('fs');
const path = require('path');

const STACKS = {
  'next-supabase': {
    name: 'Next.js + Supabase + Stripe',
    dirs: ['src/app', 'src/components', 'src/lib', 'src/hooks', 'src/types', 'supabase/migrations'],
    description: 'Production SaaS stack with auth, database, and payments'
  },
  'next-prisma': {
    name: 'Next.js + Prisma + Stripe',
    dirs: ['src/app', 'src/components', 'src/lib', 'src/hooks', 'src/types', 'prisma'],
    description: 'Production SaaS stack with Prisma ORM and payments'
  },
  'n8n-sheets': {
    name: 'N8N + Google Sheets (Scrappy MVP)',
    dirs: ['workflows', 'scripts', 'docs'],
    description: 'Scrappy-first validation stack — unscalable but fast to validate'
  }
};

function parseArgs() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.error('Usage: node scaffold-saas-project.js <project-name> [--stack next-supabase|next-prisma|n8n-sheets]');
    console.error('\nStacks:');
    Object.entries(STACKS).forEach(([key, val]) => {
      console.error(`  ${key}: ${val.description}`);
    });
    process.exit(1);
  }

  const projectName = args[0];
  let stack = 'next-supabase';

  const stackIndex = args.indexOf('--stack');
  if (stackIndex !== -1 && args[stackIndex + 1]) {
    stack = args[stackIndex + 1];
    if (!STACKS[stack]) {
      console.error(`Unknown stack: ${stack}. Available: ${Object.keys(STACKS).join(', ')}`);
      process.exit(1);
    }
  }

  return { projectName, stack };
}

function createDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
    console.log(`  Created: ${dirPath}`);
  }
}

function writeFile(filePath, content) {
  fs.writeFileSync(filePath, content, 'utf-8');
  console.log(`  Written: ${filePath}`);
}

function generateClaudeMd(projectName, stackInfo) {
  return `# ${projectName}

## Project Overview
- **Type:** AI-powered SaaS application
- **Stack:** ${stackInfo.name}
- **Skill:** SKILL-AISAAS-001 (building-ai-saas-products)
- **Framework:** GSD (Get Shit Done) — discuss → plan → execute → verify

## Key Processes
1. Feature development follows GSD lifecycle (discuss → plan → execute → verify)
2. Every phase uses wave-based parallel execution where possible
3. Atomic commits per task: \`{type}({phase}-{plan}): {description}\`
4. 4-level verification required: exists → substantive → wired → functional

## Development Rules
- Test API integrations early and in isolation before building UI
- Use plan mode before building any multi-table feature
- Always review Git changes after agent edits
- Be specific about data formats (JSON structure, field names)
- Mark phases done and get approval before proceeding
- Context budget: compact or start new session above 50% usage

## Anti-Pattern Watchlist
- Do NOT build UI before verifying backend API connections
- Do NOT build complex features without plan mode first
- Do NOT package for distribution before full IDE testing
- Do NOT skip the scrappy prototype validation stage
- Do NOT store PII/API keys without automatic sanitization

## Governance
- Governance: MEGA_GOVERNANZA_AISAAS.md
- Kill switches: 16 active (budget, scope, security, data, API, context, hallucination, testing, compatibility, access, pricing, launch, agent, checkpoint, stub, governance)
- Violation = BLOCK
`;
}

function generateProjectMd(projectName) {
  return `# ${projectName}

## Core Value
[Define the single most important value proposition]

## Target User
[Define the primary user persona and their pain point]

## Success Criteria
- [ ] Pain point validated ("will you pay?" test passed)
- [ ] First 10 users manually onboarded
- [ ] Core feature functional end-to-end
- [ ] Payment integration working

## Technical Decisions
[Captured during discuss phases]

## Learnings
[Updated after each milestone]
`;
}

function generateRequirementsMd() {
  return `# Requirements

## v1 (MVP)
- [ ] [Core feature 1]
- [ ] [Core feature 2]
- [ ] [Core feature 3]
- [ ] User authentication
- [ ] Payment integration (Stripe)

## v2 (Post-Validation)
- [ ] [Enhancement 1]
- [ ] [Enhancement 2]

## Out of Scope
- [Feature explicitly excluded]
`;
}

function generateRoadmapMd() {
  return `# Roadmap

## Milestone 1: Foundation

### Phase 1: Project Setup
- **Goal:** Development environment, database schema, auth
- **Dependencies:** None
- **Requirements:** Authentication, database
- **Success Criteria:** User can sign up and log in

### Phase 2: Core Feature
- **Goal:** Primary value proposition implemented
- **Dependencies:** Phase 1
- **Requirements:** Core feature 1, 2
- **Success Criteria:** End-to-end workflow functional

### Phase 3: Payments
- **Goal:** Stripe integration, subscription management
- **Dependencies:** Phase 2
- **Requirements:** Payment integration
- **Success Criteria:** User can subscribe and access paid features

## Progress

| Phase | Status | Started | Completed |
|-------|--------|---------|-----------|
| 1 | pending | - | - |
| 2 | pending | - | - |
| 3 | pending | - | - |
`;
}

function generateStateMd(projectName) {
  return `# State

## Project Reference
- **Project:** ${projectName} (see PROJECT.md)
- **Core Value:** [TBD after discuss phase]
- **Current Focus:** Project initialization

## Current Position
- **Phase:** 0 of 3
- **Plan:** N/A
- **Status:** not_started
- **Progress:** [..........] 0%

## Performance Metrics
| Phase | Plans | Duration | Notes |
|-------|-------|----------|-------|
| - | - | - | - |

## Accumulated Context
- **Recent Decisions:** None yet
- **Pending TODOs:** Run /gsd:discuss-phase 1
- **Blockers:** None

## Session Continuity
- **Last Session:** ${new Date().toISOString()}
- **Stopped At:** Project scaffold generated
- **Resume:** Start with /gsd:discuss-phase 1
`;
}

function generateEnvExample(stack) {
  if (stack === 'n8n-sheets') {
    return `# N8N Configuration
N8N_HOST=localhost
N8N_PORT=5678

# Google Sheets
GOOGLE_SERVICE_ACCOUNT_EMAIL=
GOOGLE_PRIVATE_KEY=
SPREADSHEET_ID=
`;
  }

  return `# Database
${stack === 'next-supabase' ? 'NEXT_PUBLIC_SUPABASE_URL=\nNEXT_PUBLIC_SUPABASE_ANON_KEY=\nSUPABASE_SERVICE_ROLE_KEY=' : 'DATABASE_URL='}

# Authentication
${stack === 'next-supabase' ? '# Supabase handles auth' : 'NEXTAUTH_SECRET=\nNEXTAUTH_URL=http://localhost:3000'}

# Stripe
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=

# AI
ANTHROPIC_API_KEY=
`;
}

function main() {
  const { projectName, stack } = parseArgs();
  const stackInfo = STACKS[stack];
  const projectDir = path.resolve(projectName);

  console.log(`\nScaffolding AI SaaS project: ${projectName}`);
  console.log(`Stack: ${stackInfo.name}`);
  console.log(`Framework: GSD (Get Shit Done)\n`);

  // Create project root
  createDir(projectDir);

  // Create stack-specific directories
  stackInfo.dirs.forEach(dir => createDir(path.join(projectDir, dir)));

  // Create GSD directories
  createDir(path.join(projectDir, '.planning', 'research'));
  createDir(path.join(projectDir, '.planning', 'phases'));

  // Create hooks directory
  createDir(path.join(projectDir, 'hooks'));

  // Write CLAUDE.md
  writeFile(path.join(projectDir, 'CLAUDE.md'), generateClaudeMd(projectName, stackInfo));

  // Write GSD state files
  writeFile(path.join(projectDir, 'PROJECT.md'), generateProjectMd(projectName));
  writeFile(path.join(projectDir, 'REQUIREMENTS.md'), generateRequirementsMd());
  writeFile(path.join(projectDir, 'ROADMAP.md'), generateRoadmapMd());
  writeFile(path.join(projectDir, 'STATE.md'), generateStateMd(projectName));

  // Write .env.example
  writeFile(path.join(projectDir, '.env.example'), generateEnvExample(stack));

  // Write .gitignore
  writeFile(path.join(projectDir, '.gitignore'), `node_modules/
.env
.env.local
.next/
dist/
.planning/research/
*.log
`);

  console.log(`\nProject scaffolded successfully!`);
  console.log(`\nNext steps:`);
  console.log(`  1. cd ${projectName}`);
  console.log(`  2. Copy .env.example to .env and fill in values`);
  console.log(`  3. Run: /gsd:discuss-phase 1`);
  console.log(`  4. Follow GSD lifecycle: discuss → plan → execute → verify`);
}

main();
