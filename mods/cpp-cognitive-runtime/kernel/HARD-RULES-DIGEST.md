# HARD-RULES DIGEST (compiled -- do not hand-edit)

149 binding rules | 13 rejected at the schema gate and INERT | regenerate: `~/.claude/skills/claude-power-pack/tools/hardrule_compile.py --compile`

**Read this at the trigger point.** Find the class your next action matches, then fetch those rules IN FULL:

    python ~/.claude/skills/claude-power-pack/tools/hardrule_compile.py --class DEPLOY

A class that matches is BINDING: fetch it and comply before acting. No rule is summarised here -- a summarised kill switch is how one quietly stops meaning anything.

| class | rules | fires on |
|---|---:|---|
| **PROD-WRITE** | 22 | writing to a live substrate: prod config, server.properties, plugins data, prod DB rows, prod env |
| **DEPLOY** | 6 | deploying: power restart/start, JAR upload, schematic paste, kubectl, helm, fly, vercel, release |
| **DONE-CLAIM** | 36 | declaring done/ready/shipped, or any human-facing completion claim |
| **SECRETS** | 14 | credentials, keys, tokens, .env, cookies, rotation, redaction |
| **DESTRUCTIVE** | 4 | rm -rf, Remove-Item -Recurse, DROP/TRUNCATE, force-push, delete |
| **VAULT-WRITE** | 19 | writes to vault/knowledge/memory files (atomicity, heredoc race) |
| **COMMIT** | 7 | git commit / staging / pathspec discipline |
| **COST-CONTEXT** | 22 | model routing, token budget, context threshold, /compact |
| **DATA-HONESTY** | 36 | writing a factual claim: PII, attribution, benchmarks, any number or biographical datum about a real person or operator |
| **BILLING-REVENUE** | 45 | money surfaces: billing, invoicing, FX, profit, capital, usage metering, entitlement, subscription |
| **CONTENT-PUBLISH** | 57 | public surface: blog, landing, marketing copy, SEO/GEO/AEO, schema markup, indexing |
| **AGENT-AUTONOMY** | 35 | agent behaviour: autonomy tiers, sub-agent dispatch, shadow runs, kill/expiry switches, self-prompting |
| **QA-TEST** | 27 | tests, QA harnesses, stress runs, determinism gates |
| **UNCLASSIFIED** | 10 | matched no trigger keyword -- read on any high-stakes action |

## RETIRED TRIGGERS (withdrawn from the router -- an empty result here is the governed answer, not a gap)
- **PLUGIN-INSTALL** -- retired 2026-07-27 by Owner decision -- no corpus. Zero rules ever classified here, so the trigger enforced nothing, and a contracted trigger with no corpus is governance theater. REOPEN when a real plugin-install incident yields at least one schema-valid rule: move the name back into ROUTER_CONTRACTED and restore the router's fourth trigger in ~/.claude/CLAUDE.md.

## BINDING POINT NOT DECLARED (149 of 149 binding rules) -- these do not say whether they advise, block a build, block a deploy or stop the runtime. Treat every one as blocking until it declares: an undeclared consequence is not a mild one.
    ~/.claude/skills/claude-power-pack/tools/hardrule_compile.py --binding

Rejected rules cannot fire: `~/.claude/skills/claude-power-pack/tools/hardrule_compile.py --rejects`.
