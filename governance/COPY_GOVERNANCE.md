# COPY_GOVERNANCE.md — Public copy is a done-gate

> Normative. Any project using Claude Power Pack obeys this from its first commit.
> Domain: any project with an end-user-facing interface (portfolios, landing pages,
> products aimed at non-technical people). Origin: Jacobo portfolio, 2026-07-11.

## The rule (imperative)
Humanizing public copy before production is NOT optional. It is a done-gate, exactly like
a passing build. A project MAY deploy with warnings in its logs. A project MUST NOT deploy
with technical vocabulary in copy visible to the end user.

## Gate V-COPY-01 — run before any deploy that changes copy
1. Build the project and fetch the SERVED HTML of every principal route from the
   production/preview URL (the rendered output, not the source files).
2. Grep that HTML for the banned-term list below.
3. If any term appears in VISIBLE text (element content, not an `href`/`src` URL): BLOCK
   the deploy. Rewrite, rebuild, re-grep. Zero visible hits is the pass condition.
4. A functional URL inside an `href`/`src` attribute is exempt — it is a technical
   necessity like a variable name, not copy — but its visible label must be clean (strip
   any hosting-platform suffix so a visitor reads a name, not where it is hosted).

## Banned-term list (seed — extend per project, never shrink)
stack, framework, Next.js, React, TypeScript, PostgreSQL, Elixir, Phoenix, Tailwind, API,
backend, frontend, deploy, runtime, SDK, repo, codebase, database, schema, endpoint,
CI/CD, pipeline, microservices, monorepo, LLM, token, prompt, vector, embedding, Vercel,
pnpm, npm, git, commit, branch, PR, merge, SaaS, B2B, B2C, MVP, KPI, ROI, MRR, ARR, churn,
CAC, LTV — and any term a restaurant owner or a non-technical investor would not use in
conversation. For a concept the reader needs (e.g. an AI model), translate it: "the
intelligence that understands what you describe", never the technical name.

## Tone benchmark
The KobiiCraft manifesto (Jacobo portfolio, `app/kobiicraft/manifesto/page.tsx`) is the
standing reference. Copy passes tone when it: leads with a human feeling, not a category;
uses concrete, sensory images; describes technology only by what it does for a person,
never by name; communicates ambition through values, not metrics; uses short, warm,
declarative sentences; names a real problem anyone recognizes. Translate the technology
into plain language — change the language, never the facts.

## Applies to
Any pull request or deploy that touches strings visible to the end user.
