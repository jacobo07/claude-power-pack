# Phase 3: Opportunity and delivery measurement - Context

**Gathered:** 2026-10-03
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss), enriched with the orchestrator's evidence read
**Host:** gex44 (no claim here is a laptop live reading)
**Governing spec:** vault/plans/skill-capability-program-2026-10-03.md

<domain>
## Phase Boundary

Pillar C of `vault/programs/skill-capability/ledger.json`: opportunity / delivery / recall / precision.
Frozen rule (immutable): "opportunity, delivery, recall and precision are computed by one gate from transcripts
over a named window; recall and precision report n and are never extrapolated from n < 5".
Frozen owners: `tools/skill_invocations.py`, `.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/p3_delivery.py`.
Predicted terminal: IMPLEMENTED_AND_VERIFIED (needs `gate` argv + `prg` evidence, like pillar A).

</domain>

<decisions>
## Implementation Decisions

### D-01 One gate, extend the owner, never a second invocation counter
- Delivery by invocation comes from `tools/skill_invocations.py` (model `Skill` tool_use + typed `<command-name>`;
  it already refuses mentions, listings and hook bodies). Reuse its functions by import; do not re-implement the
  transcript parse. Delivery by card comes from the doctrine-card ledger (`deny-card` = delivered, per
  `tools/skill_opportunity_signals.py` docstring: a ledger-only row is a measurement, never delivery).
- Opportunity = a commit judgement where the card saw foreign hunks (`opportunity`, `deny-card`) — the only
  capability with a machine opportunity detector today is `concurrent-writers-shared-tree` (CWST). Every other
  skill has NO detector: the gate reports it as `opportunity: UNMEASURED`, never 0 (absent is not zero).
- Definitions the gate prints verbatim: recall = delivered opportunities / opportunities; precision = delivered
  AND needed / delivered, where "needed" = the frozen D-CARD ground truth (D-CARD: 5 live denies, 0 true
  positives) or a per-row label carried in the window fixture. Each rate prints its n; n < 5 prints
  `n=<k> (< 5, not estimated)` and no ratio.

### D-02 Named windows, each labelled with its plane and its selection rule
- Window L (laptop, shipped content-free): `/home/kobii/missions/skill-capability-data/card_evidence_pack.json`,
  copied into `vault/programs/skill-capability/` as a fixture and cited with sha256 (the pack already has a copy
  there: `vault/programs/skill-capability/card_evidence_pack.json`, sha in ledger state.A). CAUTION measured by the
  orchestrator: the pack holds 20 of `source_ledger_rows`=140 ledger rows, selected (deny-card 6, pass-after-card
  8, unknown 6); it is NOT the population. A recall computed over it is a recall over that selection and must be
  labelled so; the population recall over all 140 rows is UNMEASURED on this host (Owner bundle `[C]` line: run
  the gate on the laptop's live ledger + transcripts).
- Window G (gex44, live here): this host's own `~/.claude/projects/**/*.jsonl` (173 files modified in the last
  7 days at plan time) for invocation delivery. This host has NO doctrine-card ledger
  (`~/.claude/state/doctrine-cards/` absent), so window G has invocation delivery and no card opportunity:
  opportunity UNMEASURED there, never 0. Name the window by `--root` + `--days` + an end timestamp so a re-run is
  the same window.
- The gate never mixes planes in one figure.

### D-03 Driven red, positive control
- A fixture window with a known answer (e.g. 6 opportunities, 4 delivered, 1 needed) must produce exact figures;
  a mutant that counts mentions as invocations, or treats UNMEASURED as 0, must go red; a positive control proves
  the detector found something in a real window (population floor > 0 on window L).

### D-04 Closure
- `state.C` = IMPLEMENTED_AND_VERIFIED with `gate` argv (the new gate) + `prg` evidence file
  `vault/programs/skill-capability/evidence/C-delivery.md` (sha256 LF) carrying the figures with `command:` lines
  and naming the window(s); savings none or `unknown` (this pillar measures, it saves nothing).
- One `[C]` owner-bundle line: laptop live-ledger population run.
- `python3 tools/test_skill_capability_program.py --pillar C` PASS; `--pillar A` and `--pillar B` stay PASS.

### Claude's Discretion
Gate file name (e.g. `tools/test_skill_delivery.py` or a subcommand of skill_invocations.py), fixture layout.

</decisions>

<code_context>
## Existing Code Insights
- `tools/skill_invocations.py`: `installed_names`, `typed_name`, `session_of`, `count_file`, `scan(root, days, installed, now)`, `main`.
- `tools/skill_opportunity_signals.py`: card ledger -> CO-12 signals (imports `modules.cognitive_os.co_12_telemetry`; read only, never edit modules/cognitive_os).
- `card_evidence_pack.json`: keys `source_ledger_rows`, `rows` (ledger rows: ts, decision, session, basis, foreign[{file, hunk_headers}]), `sessions` (per-session `tool_calls` with tool/start/end/command or file_path).
- Phase 1 closure pattern: `.planning/workstreams/skill-capability/phases/01-card-precision/01-03-PLAN.md`.
</code_context>

<specifics>
## Specific Ideas
- Report shape per window: `{window, plane, selection, opportunities{n}, delivered{card,invocation,n}, recall{value|null,n}, precision{value|null,n}, unmeasured[...]}`.
</specifics>

<deferred>
## Deferred Ideas
- Laptop population run over all 140+ ledger rows and laptop transcripts -> owner bundle `[C]`.
- Opportunity detectors for skills other than CWST -> pillar D (coverage class) and J (creation governance).
</deferred>
