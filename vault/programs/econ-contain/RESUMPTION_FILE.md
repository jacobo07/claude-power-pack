# RESUMPTION_FILE — econ-contain-2 (workstreams F-L)

**Identity.** Claude Power Pack, `C:\Users\User\.claude\skills\claude-power-pack`, branch
`feature/knowledge-acquisition`. Goal `econ-contain-2` (cap 23,000,000, Owner-approved successor of
econ-contain, which was spent at 13,790,935 of 14M). Plan: `vault/plans/econ-containment-2026-10-10.md`
(workstream table, Architecture, Done-gates). Thesis: zero model tokens after a goal is known spent; one
Owner decision, never mechanical escape.

**State (coherence anchor: HEAD contains 833eb3fd).**
- SEALED: WS-B..E (9c88ebad): tombstone/exhausted ledger ops, binding generations, quarantine, fence,
  econ_admission.js + econ_plane.py. Admission is its OWN UserPromptSubmit hook, 30 s (d3170d43); proven
  live (headless `claude -p` on a tombstoned sid: blocked, num_turns 0, cost 0; 833eb3fd).
  Gates: ECON 29/29, GOAL 59/59. SBG 21/22: V-SBG-LATENCY red from host RAM (HEAD equally slow), not code.
- PENDING: F (accounting roles: recovery / refused-billed), G (recovery ContextImage via capsule-v2 +
  /clear epoch), H (successor + Owner-capital wake), I (canaries), J (real ctx-same-pane recovery),
  K (cross-domain validation on one unrelated goal), L (vault/FIOS/UKDL/CBR). WS-A status unverified:
  check before assuming.
- Spend: econ-contain-2 had 12,430,329 settled + 1,239,905 reserved by the previous pane (a9647f12),
  whose per-call cost had grown to ~248K. ~9.3M remain. Run `mission_spend.py goal-status --goal econ-contain-2`.

**Active decisions.**
- Fresh pane per workstream; never iterate in a pane whose per-call is >150K (coordinator overrun).
- H: build on 5a's capital authority `modules/provider_routing/capital_authority.py`
  (`ca.apply(packet, transcript, goal, ledger_factory)`); do not fork it. 5a owns that module, the
  `mission_spend.py capital-*` subcommands, gsdx_chain.py, test_capital_authority.py and
  owner_capital_capture.js. Do not edit them; message claude-power-pack-5a.
- J: `goal-settle` books pre-bind history as goal spend (5a: +7.1M on ukai; vault/programs/oca/FINDINGS.md F2).
- Hook / settings.json edits are denied in auto mode: write an Owner-run apply script (pattern:
  `scratchpad/apply_econ_admission_standalone.py`: plan-first, backups, CRLF-preserving, runs the gate).
- Drill goal `econ-drill` (sid f7e8f485 tombstoned) stays as a fixture; it has no roots.

**Next 3 actions.**
1. Bind this session: write `~/.claude/state/goal-binding/<your sid>.json` =
   `{"goal":"econ-contain-2","since_ts":"<your first transcript ts, UTC>","source":"explicit","pid":0}`
   (must be done BEFORE any mutating call; a bound session cannot write it).
2. Run `goal-status`, then confirm which of F-L remain by grepping for each workstream's anchor (e.g. a
   `recovery` role in ledger.py for F, capsule-v2 ContextImage for G). Pick ONE workstream.
3. Implement it with V-ECON-* gates in `tools/test_econ_containment.py` (red first, a control per refusal),
   commit with a scoped pathspec, update this file.

**Start.** Read this file and the plan's Architecture + Done-gates sections, then do action 1.
