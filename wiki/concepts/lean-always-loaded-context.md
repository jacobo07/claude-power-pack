---
type: concept
created: 2026-09-30
updated: 2026-09-30
sources: [2026-09-30-yt-9uojngzcjo]
---

# Lean always-loaded context

Everything loaded into every session costs tokens on every call and competes for attention. Keep the
always-loaded layer to pointers and truly universal rules; load depth on demand
([[2026-09-30-yt-9uojngzcjo]]: "fresh and condensed", "the right context at the right time, and
nothing more").

## Mechanisms in PP

- Rule → skill moves with short stubs (2026-09-29/30), status LIVE: the stubs exist under
  `~/.claude/rules/`. Whether sessions then invoke the skills when needed is unmeasured — the stubs
  themselves note "moved rules were not auto-invoked (0/8)".
- Sleepy / latent-card skills (PP CLAUDE.md "Future skills MUST be latent-card + JIT-full-depth").

## Tension

Moving a rule out of context trades a constant cost for a recall risk: the rule applies only if
something triggers the skill. PP's answer for destructive commands is a hook that shows a card
(`destructive_doctrine_card.js`, per the rule stub).

Tracked in [[always-loaded-prefix-audit]].
