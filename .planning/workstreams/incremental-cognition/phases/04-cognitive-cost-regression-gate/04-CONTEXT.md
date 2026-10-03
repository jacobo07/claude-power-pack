# Phase 4: Cognitive cost regression gate - Context

**Gathered:** 2026-10-03 (GEX44, orchestrator pre-research; discuss skipped via workflow.skip_discuss)
**Status:** Ready for planning
**Mode:** Auto-generated from ROADMAP + frozen ledger rule K. Pillar K.

<domain>
## Phase Boundary

Goal: a material rise in startup floor by layer is visible in review.
Success criteria: gate green on today's floor, red on a seeded rise (positive control), layer and scope reported.

Frozen rule K (ledger, immutable; owners `wiki/tools/listing_floor_probe.py`, `tools/baseline_ledger.py`):
"a gate that measures the current startup floor by layer and fails on a material unexplained rise versus a
committed reference; a 1K universal addition reported distinctly from project-local". Predicted
IMPLEMENTED_AND_VERIFIED.

Run plane (ROADMAP): "K's reference floor is laptop-plane. Build and test the gate here (positive control on a
seeded rise); the committed reference must come from the laptop install -> `[K]` owner-bundle line." K stays
open until the laptop reference lands.
</domain>

<evidence>
## Measured on GEX44, 2026-10-03

- `wiki/tools/listing_floor_probe.py` runs ONE fresh headless `claude -p` session (costs quota, Windows paths:
  `CLAUDE = C:\Users\User\.local\bin\claude.exe`, `REPO = ~/.claude/skills/claude-power-pack`) and `analyse(path,
  watch)` reads the transcript: `startup_tokens` = input + cache_creation + cache_read of the FIRST model call;
  `listing` = chars / entries / described of the initial `skill_listing` attachment. Results file
  `wiki/tools/listing_floor_probe.results.jsonl` (4 rows, laptop: champion 87,739 startup tokens, listing 30,000
  chars / 216 entries).
- Existing transcripts already carry the per-layer startup payload WITHOUT spending a session: the first rows of a
  session hold `attachment` rows -- `hook_success` / `hook_additional_context` (per hookName, e.g.
  `SessionStart:startup`), `hook_system_message`, `skill_listing` (isInitial), `prompt_snapshot` (systemPrompt
  parts), file attachments (CLAUDE.md memory) -- and the first assistant row's usage gives the model-visible
  total. Example: `~/a7-env/home/.claude/projects/-home-kobii-kobii-a7/71e107ea-...jsonl` rows 8-11 (a 39-row
  transcript). So the gate can measure layers from a transcript (`analyse`-style), and use a probe session only
  when a fresh measurement is wanted.
- Static layer sizes on GEX44 main install (chars): `~/.claude/CLAUDE.md` 25,206; project `CLAUDE.md` 35,875;
  `~/.claude/state/inherited-global-rules.md` 58,247 (rules delivered by file); 23 files in `~/.claude/rules`;
  186 entries in `~/.claude/skills`. These are `plane: gex44` facts, not the laptop reference.
- `tools/baseline_ledger.py` (451 lines) is a version-axis ledger (k_qa, k_router, engineering_baseline,
  highest_dna) at `~/.claude/vault/global_baseline_ledger.json`; it has no floor axis. Writing that ledger is a
  `~/.claude` write (HR-001) -> never from this phase.
</evidence>

<decisions>
## Implementation Decisions

- **Scope / layer model (report both):** each startup component is classified by LAYER (system_prompt,
  memory_global = ~/.claude/CLAUDE.md, memory_project = repo CLAUDE.md, rules, skill_listing, hook_context per
  hook event+name, hook_system_message, other) and SCOPE (universal = comes from ~/.claude/** and applies to every
  repo; project = comes from the repo). "A 1K universal addition reported distinctly from project-local": a rise
  is attributed to its scope and the report prints universal and project deltas separately.
- **Measurement source:** a transcript (`--transcript <jsonl>`) or the newest session of a project dir; chars per
  layer plus the first-call model-visible token total. Optional `--probe` reuses `listing_floor_probe.py` (do not
  fork it; extend it only additively, e.g. a path-portable CLAUDE exe from env `CPP_CLAUDE_EXE`). Never spawn a
  session from tests.
- **Reference:** a committed JSON `vault/programs/incremental-cognition/floor/reference.json` with per-layer chars,
  total tokens, provenance (`plane`, transcript id, install commit). On GEX44 commit a `plane: gex44` reference used
  only by the tests/smoke; the frozen-rule reference must be the laptop's -> `[K]` owner-bundle line with the exact
  command. Materiality: a rise >= 3 % of the reference total OR >= 1,000 chars in any universal layer, unless an
  `explanations` entry (layer, delta bound, reason, commit) covers it; an explanation with an empty reason is refused.
- **Gate CLI:** new `tools/floor_regression_gate.py` (`--check`, `--reference`, `--transcript`, `--write-reference
  <out>` to a path argument only, `--json`); exit 0 within bound, 1 material unexplained rise, 2 UNMEASURABLE
  (no transcript / no skill_listing / unreadable) -- never 0 on unmeasurable.
- **Tests:** `tools/test_floor_regression_gate.py` (V-FLOOR-* gates, `FLOOR_PASS=n/m threshold=n/m`): green on a
  fixture equal to the reference; red on a seeded +1 KB universal rise (positive control) with layer + scope named;
  a project-local rise reported as project; explained rise green; empty-reason explanation refused; unmeasurable ->
  exit 2; a real GEX44 transcript parses (smoke, plane gex44). Mutation drill: drop the scope split -> the
  universal/project test goes red; restore proven by sha256.
- Liveness: the gate must be reachable (a test or a declared registry entry in
  `vault/liveness/reachability_registry.json` as LIBRARY/SCHEDULED with reason) -- check `modules/liveness`.
- Evidence `vault/programs/incremental-cognition/evidence/K.md` (Product Delta + Intelligence Delta). Ledger
  `state.K` stays OPEN (laptop reference pending). Never write `~/.claude/**`.
- Commits: explicit pathspec, `git commit -F <msgfile>`, plain single git commands, verify `git log -1`. Never push.

### Claude's Discretion
Layer-classification heuristics (state them), output format, where the explanation list lives (inside reference.json is fine).
</decisions>
