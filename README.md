# Claude Power Pack v1.0

All-in-one skill that makes Claude Code and Claude.ai dramatically better at building software. Project-agnostic — works on any stack, any project.

## What It Does

**Always active (zero trigger needed):**
- Execution depth loop: OBSERVE → PLAN → EXECUTE → VERIFY → HARDEN
- Intent routing: classifies your request complexity and scales effort proportionally
- Quality gates: prevents shipping broken code
- Anti-fabrication: stops Claude from inventing fake classes/endpoints
- Proportional cost: simple requests stay cheap, complex ones get full rigor

**On trigger (token optimization):**
- Context audit: find what's burning your tokens
- Prompt compressor: rewrite instructions shorter
- Dedup finder: eliminate overlapping rules
- Governance digest: compress large docs to actionable rules
- Description trimmer: enforce 15-token budget on descriptions
- Sleepy architecture audit: find always-loaded waste
- Full optimization: run the complete pipeline

## Install

### Claude.ai (Project Knowledge)
1. Open your Project → Add Project Knowledge
2. Upload this zip (or just SKILL.md)
3. Use any trigger phrase in conversation

### Claude Code (Skill)
```bash
mkdir -p ~/.claude/skills/claude-power-pack
cp SKILL.md ~/.claude/skills/claude-power-pack/
```

### ChatGPT (Project Instructions)
1. Open your Project → Settings → Instructions
2. Paste the contents of SKILL.md

## Capabilities

| Code | Capability | Trigger | Always Active? |
|------|-----------|---------|---------------|
| A | Execution Depth | — | Yes |
| B | Intent Routing | — | Yes |
| C1 | Context Audit | "token audit" | On trigger |
| C2 | Prompt Compressor | "compress this" | On trigger |
| C3 | Dedup Finder | "dedup check" | On trigger |
| C4 | Governance Digest | "create digest" | On trigger |
| C5 | Description Trimmer | "trim descriptions" | On trigger |
| C6 | Sleepy Audit | "sleepy audit" | On trigger |
| C7 | Full Optimization | "full optimization" | On trigger |
| D | Delivery Standards | — | Yes |

## Token Budget

SKILL.md: ~1900 words (~2527 tokens). Loaded once per session.

## What You'll Notice

- Fewer "it should work" moments — verification is mandatory
- Simpler requests get fast answers instead of over-engineered responses
- Complex requests get proper planning instead of rushing
- Your instruction files get smaller and sharper over time
- Claude asks one clarifying question instead of guessing wrong and rebuilding

## Origin

Distilled from 180+ governance files, 20+ production projects, and 3 years of iteration. The principles come from real failures, not theory.
