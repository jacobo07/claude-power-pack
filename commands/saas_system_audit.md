# SaaS System Audit — Universal Commercial Readiness Assessment

You are operating in **SYSTEM AUDIT + COMMERCIAL READINESS ASSESSMENT MODE**.

Your task is NOT to build anything new.
Your task is to inspect the real local project state, determine exactly what has been built, what is missing, how far the system is from being genuinely sellable, and what the shortest path is to reach a product that can be sold.

You must work from the real filesystem only.

---

## PHASE 0 — AUTOMATIC CONTEXT DISCOVERY

Before auditing, you MUST discover the project's identity automatically. Run these discovery steps silently and use the results to adapt the entire audit:

### 0.1 Project Identity
- Read `README.md`, `CLAUDE.md`, `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, or any manifest at root
- Identify: project name, description, stated purpose, tech stack
- If a PRD, SPEC, or architecture doc exists anywhere, read it

### 0.2 Tech Stack Detection
- Detect primary language(s) from file extensions and manifests
- Detect framework (Next.js, FastAPI, Django, Rails, Spring, etc.)
- Detect database (check for migrations, ORMs, connection strings, docker-compose)
- Detect auth system (check for auth modules, JWT, OAuth configs)
- Detect deployment config (Dockerfile, docker-compose, vercel.json, railway.toml, fly.toml, Procfile)
- Detect CI/CD (`.github/workflows/`, `.gitlab-ci.yml`, etc.)
- Detect testing setup (pytest, jest, vitest, etc.)

### 0.3 Architecture Shape
- List all top-level directories and classify them (src, tests, docs, config, scripts, governance, etc.)
- Count Python/JS/TS/Go/Rust files to gauge codebase size
- Identify: monolith vs microservices, frontend vs backend vs fullstack
- Check for any UI (templates, components, pages, routes)
- Check for any API layer (routes, endpoints, controllers)

### 0.4 State of Reality
- Check git status (committed? dirty? branches?)
- Check if dependencies are installed (node_modules, venv, etc.)
- Check if the app can be imported/started (try a dry import or health check)
- Run tests if a test suite exists (collect, don't run if >60s expected)
- Check for seed data, sample data, or populated databases

### 0.5 Adjacent Projects
- Check sibling directories under the parent folder for related repos
- Only inspect those that appear directly related (shared name patterns, cross-references)

### 0.6 Commercial Doctrine Reference
Reference the SaaS Launch Doctrine principles when assessing readiness. Key laws to evaluate against:

**Planning completeness:**
- Does a PRD or spec exist? (LAW-PLAN-001, LAW-PLAN-002)
- Is the build phased or monolithic? (LAW-PLAN-003)

**Stack soundness:**
- Does the stack match production requirements? (LAW-STACK-001, LAW-STACK-004)
- Is there provider abstraction for external services? (LAW-STACK-002)

**Foundation:**
- Is there a CLAUDE.md / project constitution? (LAW-SETUP-002)
- Is git initialized with meaningful history? (LAW-SETUP-003)

**Feature completeness for MVP:**
- Auth implemented? (LAW-AUTH-001)
- Core features working? (LAW-FEAT-001)
- Admin panel? (LAW-FEAT-003)

**Deployment readiness:**
- Can it be deployed today? (Playbook Phase 3: deploy empty shell early)
- Is there a production URL? (Playbook Gate: production URL returns 200)

**Monetization:**
- Is there a payments/billing system? (Playbook Phase 10)
- Is there a pricing model defined? (Pre-Flight Checklist)

---

## HARD RULES

1. **Grounding only** — If something is not present on disk, say it is not verified. Separate VERIFIED from INFERRED from MISSING.

2. **No scope creep** — Identify the frozen core / MVP and audit against that. Do not silently include later expansions as required unless they genuinely block saleability.

3. **Commercial realism** — Judge sellability by whether this can be shown to a real buyer without looking fragile, fake, incomplete, or confusing. Distinguish:
   - sellable as internal operator tool
   - sellable as managed service enablement layer
   - sellable as standalone software product
   - sellable as SaaS with self-serve onboarding

4. **No fake percentages** — If you estimate completion, justify it with real module/file evidence.

5. **Shortest-path lens** — The goal is: get to something genuinely vendible, start practicing sales, not overbuild before market conversations.

6. **Anti-fantasy** — Do NOT invent progress. Do NOT give motivational fluff. Do NOT give generic startup advice. Do NOT brainstorm random features.

---

## WHAT YOU MUST DETERMINE

**A. CURRENT BUILD REALITY** — What is actually implemented, scaffold only, spec/plan only, or missing entirely.

**B. SYSTEM MATURITY** — For each major area rate: not started / scaffolded / partially implemented / working but fragile / working and demoable / commercially credible.

**C. COMMERCIAL READINESS** — Assess separately with justification:
1. Can it be sold right now as an internal tool used by the operator?
2. Can it be sold right now as part of a managed service offer?
3. Can it be sold right now as a software product?
4. Can it be demoed right now without damaging trust?

**D. MINIMUM SELLABLE PRODUCT THRESHOLD** — Exact minimum system state required to start outreach, do real demos, have credible sales conversations.

**E. WORK REMAINING** — Grouped by core gaps, demo gaps, reliability gaps. Tied to actual modules/files.

**F. OFFER SHAPE** — Best first thing to sell based on current reality: managed service / pilot / internal-tool-backed service / software with setup / SaaS / not ready.

---

## REQUIRED OUTPUT — 14 SECTIONS

Output exactly these sections:

### 1. SYSTEM SNAPSHOT
One paragraph. What the project currently is in reality. What stage it is actually in.

### 2. VERIFIED BUILD INVENTORY
Table of actual discovered folders/files/modules/components that matter. Each marked VERIFIED with why it matters.

### 3. MODULE-BY-MODULE STATUS
For each core module discovered during context detection:
- Status (not started / scaffolded / partial / working-fragile / working-demoable / commercially-credible)
- Evidence (specific files/lines)
- Quality judgment
- Whether it is sell-critical

Include: auth, database, API, UI/frontend, core business logic, payments, admin, deployment, tests, monitoring — but only those that exist or are expected for this specific project.

### 4. WHAT IS REAL VS WHAT IS ONLY PLANNED
Four buckets:
- **VERIFIED IMPLEMENTED** — code exists, imports, runs
- **VERIFIED SCAFFOLDED ONLY** — files exist but stubs/empty/placeholder
- **SPEC / DOC ONLY** — described in docs but no code
- **MISSING** — not even planned or documented

### 5. COMMERCIAL READINESS ASSESSMENT
Score each with plain-language justification (not vanity scores):
- Internal operator usefulness
- Managed-service usefulness
- Demo credibility
- Software-product readiness
- SaaS readiness (if applicable)

### 6. WHAT CAN BE SOLD RIGHT NOW
Be concrete. Only say something can be sold if justified by the audit. Examples: nothing yet / pilot with manual support / managed service / limited founder-led implementation.

### 7. WHAT CANNOT BE SOLD YET
Exact reasons. What would break trust. What is too fragile/incomplete.

### 8. MINIMUM SELLABLE PRODUCT GAP
Exact missing pieces required before first credible sale. Prioritize only what is truly necessary. Include effort estimates per gap.

### 9. HOW MUCH IS LEFT
Brutally honest estimate grouped by:
- Core gaps (must-have for the product to function)
- Demo gaps (must-have to show without embarrassment)
- Reliability gaps (must-have for real client use)
- NOT required for first sale (explicitly list what to skip)

### 10. SHORTEST PATH TO VENDIBLE
Exact shortest path. No fluff. No extra features. Sequence only the highest-leverage moves.

### 11. BEST FIRST OFFER TO PRACTICE SALES
Choose one and justify: managed service / pilot / internal-tool-backed service / software with setup / SaaS subscription / not ready. Include why this is the best first commercial move based on current reality.

### 12. DEMO READINESS
- What can already be demoed
- What must not be demoed yet
- What must be polished first

### 13. BLOCKERS
- Exact blockers to first sale
- Exact blockers to first demo
- Exact blockers to real delivery

### 14. NEXT 7 EXECUTION MOVES
7 concrete actions. Each must:
- Be directly tied to becoming vendible faster
- Avoid scope creep
- Improve commercial readiness
- Be phrased as an action with estimated effort

---

## QUALITY BAR

Your audit must be: brutally honest, repo-grounded, commercially realistic, anti-overengineering, anti-fantasy, anti-fake-progress.

Explicitly distinguish: build progress vs product readiness vs offer readiness vs sales-readiness.

A product can be NOT fully built and still be sellable as a managed service.
A product can be technically impressive and still NOT be sellable.

### CRITICAL: BUYER-CALIBRATED STANDARDS

NEVER judge readiness against an abstract "minimum viable" standard. ALWAYS judge against the actual target buyer.

Before claiming anything is "demoable," "sellable," or "commercially credible," apply this test:

**"Would the target buyer — the person who writes the check — take a second meeting after seeing this?"**

If the target buyer is a business spending $90k/month on marketing, they have seen Agency Analytics, SEMrush, Ahrefs, polished agency dashboards, and premium consulting decks. A basic CRUD app with domain-specific labels is not a product — it is a prototype. Say so.

If the target buyer is a solo founder, the bar is different. Calibrate accordingly.

Do NOT:
- Present basic task trackers as "commercially credible"
- Confuse "technically works" with "commands respect from the buyer"
- Optimize for "shortest path" at the expense of the buyer's minimum threshold of seriousness
- Dress up scaffolding as product readiness

DO:
- Name the gap honestly: "This is a functioning internal tool. It is not at the quality level that would command respect from [target buyer profile]."
- Quantify how far below the buyer's bar the system currently sits
- Identify the specific capabilities that the target buyer considers table-stakes vs differentiating

Return the audit only. No commentary outside the 14 sections.
