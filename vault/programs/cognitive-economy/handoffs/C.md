# Handoff [C] -- skill / agent / tool capability virtualization -> residency owners

Pillar: [C] skill/agent/tool capability virtualization. Terminal: DEFERRED_STRONGER_OWNER.

Owners (frozen): `vault/plans/skill-residency-program-2026-10-03.md`,
`vault/plans/skill-virtualization-k-slice-2026-10-03.md`, `vault/specs/agent-capability-virtualization.md`.

Frozen rule: "skills/agents consumed from their owners; tool schemas: build lazy loading only if MCP/tool schema
residency >= 3 % of D-W7 weighted".

## Tool half -- measured, no build (`vault/programs/cognitive-economy/evidence/F-G-P-C-carriage.md`)

- Lazy loading of MCP/tool schemas already exists in the harness: deferred tools are listed by name and loaded on
  demand through ToolSearch. What ToolSearch loads costs **0.0020 %** of D-W7 weighted (read + write carriage of
  its results, KSR construction, all 75,969 D-W7 calls). Far below 3 %: nothing to build.
- Always-on built-in schemas sit in the system prompt, which no transcript records: UNMEASURED by this campaign.
  They are part of the startup floor the K-slice / skill-residency programs measure.

## Skill / agent half -- consumed from the owners, with one fact for them

- `vault/programs/cognitive-economy/measure/t_sweep.py` (pillar T) counted D-W7 invocations of every skill installed
  under `~/.claude/skills`: 165 installed, 23 invoked at least once in the week (Skill tool_use or slash command),
  142 not invoked. The full per-skill table is in `measure/t_sweep_out.json`. Of the invocations, `gsd-autonomous`
  alone is 159. One week is a thin window: "not invoked in D-W7" is a fact about the week, not a retirement verdict.
- What a non-invoked skill costs is its listing line in the skill catalogue, not its body; sizing that line set is
  the K-slice's measurement, so no number is claimed here.

## What the owners keep

Skill residency, the K-slice listing budget, agent capability virtualization, and the decision whether the 142
non-invoked skills change any listing. Nothing edited by the campaign.
