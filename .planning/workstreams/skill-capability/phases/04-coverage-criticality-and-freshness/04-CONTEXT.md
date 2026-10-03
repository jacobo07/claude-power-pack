# Phase 4: Coverage, criticality and freshness - Context

**Gathered:** 2026-10-03
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss), enriched with the orchestrator's evidence read
**Host:** gex44 (every figure below is a gex44 reading; the laptop's live tree is a different plane)
**Governing spec:** vault/plans/skill-capability-program-2026-10-03.md

<domain>
## Phase Boundary

Two pillars of `vault/programs/skill-capability/ledger.json`, both predicted IMPLEMENTED_AND_VERIFIED:
- **D coverage + criticality.** Frozen rule: "every installed skill gets a coverage class (opportunity detector /
  card / none) and a criticality class from a discovered sweep, never a hand list". Owners:
  `tools/skill_invocations.py`, `modules/zero-crash/hooks/skill-heat-map-advisor.js`.
- **H freshness / drift / recert.** Frozen rule: "drift between a skill's live copy and its repo mirror, and
  between a card and its source, is detected by a gate driven from both poles". Owner: `tools/router_freshness_gate.py`.

</domain>

<decisions>
## Implementation Decisions

### D-01 (pillar D) Population discovered, never listed
- Sweep the installed skill population off disk: repo `skills/*/SKILL.md` (24 dirs at plan time) and the host's
  live `~/.claude/skills/*` (186 entries on gex44), plus `installed_names()` from `tools/skill_invocations.py`
  (reuse, do not re-implement). Report each plane separately; never merge gex44 live with the laptop.
- Coverage class per skill, one of: `opportunity_detector` (a machine detector exists: today only
  `concurrent-writers-shared-tree` via `hooks/doctrine_cards.js` + `tools/skill_opportunity_signals.py`), `card`
  (a doctrine/PreToolUse card delivers it: e.g. `destructive-state-authorization` via
  `destructive_doctrine_card.js`), `none`. The class is DERIVED from code (grep the hook/tool sources for the
  skill name in a registration position), never typed per skill.
- Criticality class: derived from evidence present in the repo (e.g. the skill is a moved-out global rule under
  `~/.claude/rules/*.md` "moved to a skill", or is named by a Hard Rule / project CLAUDE.md activation criteria)
  -> `high`; activation-criteria only -> `medium`; else `low`. Planner may refine the rule but it must be a rule.
- Gate: population floor (> 0 and >= the measured repo count), a positive control (CWST must classify as
  `opportunity_detector`), and a drill: removing the detector registration from a copy must flip CWST to `none`.
- Output: a committed report `vault/programs/skill-capability/evidence/D-coverage.md` (prg) with `command:` lines.

### D-02 (pillar H) Extend the existing comparator, do not build a second
- Measured gap: `modules/mirror_discovery/discovery.py:189` classifies the whole `skills` domain as
  `OTHER_OWNER` ("PP itself lives here; the git repo IS the source"), so repo-mirrored skills
  (`skills/<name>` mirrored live at `~/.claude/skills/<name>`, per CLAUDE.md activation sections) are outside
  every existing parity check (`tools/verify_global_mirrors.py`, `tools/test_mirror_parity.py`).
- Measured on gex44 at plan time (SKILL.md only, `cmp`): of 24 repo skills, 4 identical to the live copy,
  10 differ, 10 have no live copy. That is a real red pole on this plane; the gate must report it per skill
  (DRIFT / ABSENT_LIVE / IDENTICAL), compare whole directories by sha256, and read the repo side from the
  committed blob (as verify_global_mirrors does), never the working tree.
- Both poles: identical pair -> pass; a mutated temp live copy -> DRIFT. Card-vs-source drift: a card that quotes
  or compiles a skill (destructive card <- destructive-state-authorization SKILL.md) records the source digest;
  changing the source without re-deriving fails. (Lineage proper is pillar G, phase 6: keep H to detection.)
- Do NOT "fix" gex44 live copies (never edit ~/.claude on this host). Drift found is reported, and a `[H]` owner
  bundle line asks the Owner to run the gate on the laptop plane.
- `tools/router_freshness_gate.py` is the frozen owner: wire the new check so that gate (or a sibling it invokes)
  reaches it; read its `canonical_repo_root` worktree handling first (this run IS a linked worktree).

### D-03 Closure
- `state.D`, `state.H` = IMPLEMENTED_AND_VERIFIED, each with `gate` argv + `prg` file
  (`evidence/D-coverage.md`, `evidence/H-drift.md`, sha256 LF), savings `unknown` or none.
- `--pillar D` and `--pillar H` PASS; A, B (and C if closed) stay PASS.

### Claude's Discretion
File names, whether D and H are one plan each or split further, criticality rule details.

</decisions>

<code_context>
## Existing Code Insights
- `modules/mirror_discovery/discovery.py` `discover(repo_root, live_root)`; domain table near line 189; `EXTRA_REPO_ROOTS` line 198.
- `tools/verify_global_mirrors.py`: committed-blob reads via one `git cat-file --batch`; resolution chain for repo path.
- `modules/zero-crash/hooks/skill-heat-map-advisor.js` reads `vault/skills_heat_map.json` (built by `tools/skill_heat_map_indexer.py`).
- Phase 1 closure pattern: `.planning/workstreams/skill-capability/phases/01-card-precision/01-03-PLAN.md`.
- Liveness Standard (CLAUDE.md): new modules under `modules/` must be reachable or declared; tools/ follow phase 1's precedent.
</code_context>

<specifics>
## Specific Ideas
- If editing `modules/mirror_discovery` is needed, prefer a skills-specific pass in a new tool over changing the
  OTHER_OWNER classification (other estates depend on it); justify in the plan either way.
</specifics>

<deferred>
## Deferred Ideas
- Laptop-plane drift run -> owner bundle `[H]`. Card lineage fields -> phase 6 (G).
</deferred>
