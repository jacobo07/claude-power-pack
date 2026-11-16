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
2. DONE 2026-11-16 (campaign 1, obligation 5): the `name-only` override for this skill was removed from
   `~/.claude/settings.json`, so its description reaches the model.
3. DONE 2026-11-16: web_surface **B7** carries `web_surface-taste-hard-bans` (check `taste:index.html`), promoted
   through the tower ratchet with the evidence in `vault/programs/ascension/bcap-1/b7/evidence.json`. The Stop hook
   `tools/family_donegate_stop.py` (Stop-chain in the dispatcher) runs the family done-gate at turn end in a session
   that received a family block and stands in a member repo, and blocks a page with a non-waived critical Taste
   finding. Residual, recorded in the entry itself: the GEX44 pair (106ea304) had `discriminated: false`, since the
   control agent also passed the lint, so whether the block CHANGES what a fresh builder writes is not measured (N=1).
