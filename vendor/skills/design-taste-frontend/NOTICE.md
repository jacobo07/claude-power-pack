# design-taste-frontend (Taste Skill), vendored

- Upstream: https://github.com/Leonxlnx/taste-skill, MIT License, Copyright (c) 2026 Leonxlnx (LICENSE beside this file,
  fetched from the upstream `main` branch on 2026-11-16).
- `SKILL.md` is a byte copy of the laptop install `~/.claude/skills/design-taste-frontend/SKILL.md`, sha256
  `2e064e92aca020b2e0bad69326fe7ea55d59005ed53d1a8cbce1bd135d44b8b3` (1207 lines). Byte identity with upstream HEAD was
  NOT verified; the install is the version this estate actually ran.
- Do not edit `SKILL.md`. CPP's own decisions about each rule live in
  `vault/knowledge_base/cdio/taste-absorption.json` (every section and Pre-Flight item -> ENFORCED / COVERED_BY /
  RENDER_REVIEW / GUIDANCE / CONFLICT / OUT_OF_SCOPE), and the executable checks live in `modules/cdio/taste.py`.
  `tools/test_taste_absorption.py` (V-TASTE-*) re-parses this file, so an upstream update that adds a rule fails the
  gate until the new rule has a destination.

## How it is consumed (autonomously)
1. A prompt that builds a `web_surface` gets the family block, which names this skill and asks for its Design Read
   (`vault/tower/families/web_surface.json` `skills`, rendered by `modules/gsd_x/cli.py::family_block`).
2. `~/.claude/settings.json` no longer lists the skill as `name-only`, so its description (the trigger) reaches the
   model in every session.
3. The family done-gate runs `taste:index.html` (web_surface B6). The Stop hook `hooks/family_donegate_stop.js` runs
   that gate at turn end in any session that received a family block, and blocks a turn whose page has a non-waived
   critical Taste finding.
