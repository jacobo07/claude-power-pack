# rocket.new Pattern Extraction (MC-SYS-68)

**Audit date:** 2026-05-03
**Method:** WebFetch on `rocket.new`, `docs.rocket.new`, `docs.rocket.new/getting-started/workspace/connectors`.
**Verdict:** **NO design DNA to extract.** The user-supplied premise that rocket.new exposes a design system / pattern library / token spec is incorrect.

---

## What rocket.new actually IS

A vibe-coding / no-code-but-AI app generator. Direct competitor to Cursor / Lovable / v0 / Claude itself. Tagline: "the world's first Vibe Solutioning platform" combining:
- **Solve** — research/decision support
- **Build** — app generation
- **Intelligence** — competitive tracking

**Output stack:**
- **Web:** Next.js
- **Mobile:** Flutter

That's the entire technical specification their docs expose at the introduction tier. No design tokens, no color system, no component templates, no styling framework named, no accessibility ruleset.

---

## What rocket.new actually exposes

### 14 OAuth workspace connectors

| Connector | Purpose (their copy, verbatim where useful) |
|---|---|
| Notion | "Share pages, databases, wikis, and meeting notes across all projects" |
| Google Workspace | "Share Docs, Sheets, and Calendar data across all projects" |
| GitHub | "Sync your codebase for backups, collaboration, and version control" |
| Supabase | "Add a PostgreSQL database, auth, file storage, and edge functions" |
| Figma | "Import Figma designs and convert them into production-ready code" |
| Netlify | "Deploy your app to the web with one click" |
| Airtable | "Manage leads, content, inventory, and internal workflows" |
| Linear | "Build from tickets and write follow-up issues back to your board" |
| Mailchimp | Email campaigns + automation |
| Typeform | Forms / surveys |
| Calendly | Scheduling |
| Razorpay | Payments |
| Webflow | CMS collections as data source |
| Confluence | Team docs as context for codegen |

### 4+ task-level API-key connectors
OpenAI, Anthropic, Stripe, "and others." Details not in the public intro docs.

---

## What this means for claude-power-pack

**Not actionable for the frontend lieutenant.** rocket.new is a competitor product, not a pattern library. There is no "rocket.new DNA" to fold into our `parts/sleepy/frontend.md`. The lieutenant already covers Next.js (one of rocket's defaults) via the `frontend-design` + `ui-ux-pro-max` skills.

**Actionable for autoresearch / competitive intel:**
- They normalize **Next.js + Flutter** as the cross-platform default. Confirms our lieutenant's Next.js bias.
- The Figma → production code path is real (per their connector). Worth noting for future Figma-MCP work if user goes there.
- Supabase is their default backend-in-a-box. Worth mentioning in `building-ai-saas-products` lieutenant routing.
- They expose payments via **Razorpay**, not Stripe at the workspace tier (Stripe is task-level only). Quirky regional default.

**NOT actionable per "design-gate":** the user's "Design-Gate must validate against rocket.new patterns" is impossible — rocket.new exposes no public patterns to validate against. Per Reality Contract, that piece of the original spec is fiction. The advisable design gate already exists via `frontend-design` (anti-AI-slop discipline) + `ui-ux-pro-max` (priority-ordered ruleset).

---

## Verdict

**Phase VI MC-SYS-68:** WebFetch completed honestly. No patterns to integrate. Lieutenant unchanged. This file (`vault/research/rocket_new_extraction.md`) IS the deliverable — a forensic record so future audits don't re-litigate.

**Cited URLs:** all 200 OK as of 2026-05-03.
- `https://rocket.new`
- `https://docs.rocket.new`
- `https://docs.rocket.new/getting-started/workspace/connectors`
