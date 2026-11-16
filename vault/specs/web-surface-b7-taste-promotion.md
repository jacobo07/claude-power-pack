---
covers: [web-surface-b7, taste-hard-bans, taste-promotion, asc-inherit-run]
tier: T2
owner_decision: "campaign 1 obligation 4; Owner 'both ... on GEX44' and 'y' 2026-11-16"
---
# web_surface B7: promote the Taste hard bans (campaign 1, obligation 4)

## Problem
The Taste Skill (`design-taste-frontend`) is absorbed (bb4db9f4): `modules/cdio/taste.py` lints the critical half of
its bans and `taste:<page>` is a static check kind. No baseline entry uses it, so a fresh builder is never told, and
the family done-gate never judges a page against it. The entry `web_surface-taste-hard-bans` was only named (NOTICE.md,
`taste-absorption.json` row 14 "B7 pending"). B6 is the re-citation generation, so this promotion is B7.

## Design
- Delta as data: `vault/programs/ascension/bcap-1/b7/deltas.json`, one entry, check `taste:index.html`, origin the
  TASTE-EMDASH row of `modules/cdio/taste.py` (quote verified verbatim), `applies_to_all_members: true`, `floor:
  false` -> ARCHETYPE_ENHANCING. Surfaces outside the archetype (dashboards, editors) declare `NO APLICA` with a reason,
  which the Stop done-gate already honours.
- Pair run: `tools/asc_inherit_run.py` takes `--deltas/--out/--task` (defaults = phase 5, unchanged) and
  `CPP_CLAUDE_EXE`; `--dry-run` prints the candidate block without a model call; it refuses (rc 3) a pair whose
  candidate equals the live baseline. B7 uses task `saas`: a SaaS landing with hero, testimonials, pricing, which
  invites the slop defaults without naming any ban.
- Evidence: `tools/asc_b7_evidence.py` (static, any plane): improvement = `taste:index.html` FAIL -> PASS on a fixture;
  negative controls = fixture + treated surface with a planted em-dash + with a planted scroll listener, each must be
  judged VIOLATED (rc 1; a broken judge is rc 4 and never counts); positive = treated surface; the control agent is
  reported apart with `discriminated` (a quiet control that passes is a reported fact, not a broken instrument).
- Promotion: only through `python -m modules.backlog_autopilot.promotion web_surface --deltas ... --evidence ...`
  (tower ratchet, evidence re-checked), after the Owner reads the evidence.

## Acceptance
- `tools/test_asc_b7.py` (V-ASC-B7-*, no model call): delta promotable, origin real, candidate block carries the
  entry at B(n+1), task names no ban, empty pair refused, evidence over synthetic pairs accepted by the ratchet,
  sloppy treated refused, broken judge not a control, quiet control reported; V-ASC-B7-RECORDED once the pair exists.
- `tools/test_asc_baseline.py` stays 32/32 (phase 5 untouched).
- Plane: the pair runs on GEX44 (laptop RAM). It loads `--setting-sources project`, so live user-hook delivery is NOT
  exercised by the pair; that plane is the laptop's live dispatcher (item 5) and stays a named residual.

## Evidence (laptop, worktree Apps\pp-bcap-verify)
- V-ASC-B7 13/13 rc 0 (RECORDED pending); V-ASC-BASE 32/32 rc 0. Dry run: candidate web_surface/B7, block 3551 chars,
  first taste line `[web_surface-taste-hard-bans]`.

## Rollback
Nothing is promoted by this tooling. If B7 is written and must go, the ratchet's own retirement path applies; the
pair's artifacts live only under `vault/programs/ascension/bcap-1/b7/`.
