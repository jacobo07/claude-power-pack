---
id: PLAN-SKILL-RESIDENCY
title: Skill residency program -- availability without residency, proven by need-time delivery
status: PROPOSED (awaiting one Owner approval; /ultra phase 1 + phase 2 questions inline)
covers: [skill-residency, skill-opportunity, skill-delivery, skill-invocation-telemetry, skill-listing-rent, never-invoked-triage, r2-residency]
children: [vault/plans/r2-instruction-residency-2026-10-03.md]   # adopted as slice 1, not duplicated
date: 2026-10-03
---

# Skill residency program (2026-10-03)

## Reality (scan, read-only except one measurement tool)
- HEAD `097613b1` feature/knowledge-acquisition, 0/0 vs origin, 778 dirty paths, 13 worktrees.
  Live peers: ACV (C4 sealed 32 min before scan), CCP/rollover. Auto mode OFF.
- R2 plan `PLAN-R2-RESIDENCY` APPROVED + audited (EXECUTE-WITH-FIXES G1-G12,
  `vault/audits/r2-residency-audit.md`) but UNEXECUTED: no `p3_delivery.py`, no `hooks/doctrine_cards.js`,
  last run 09:29; no session in the last 3 h references it. => adopted here as slice 1.
- Move 4 intact: repo == live SKILL.md `b1eda762` (7,891 B); backup `0c86aa17` (7,094 B); pointer
  `e311ddff` 914 B. Maturity: NEGATIVE ABLATION ONLY. Natural counter-evidence (R2 log 10:27): a session
  holding the FULL resident rule still committed a peer's hunk => residency did not deliver behaviour.
- Remaining resident candidates: TFPS 6,932 B, SSEA 6,602 B (both unchanged since 09-28).

## Measured this scan
- Invocation channels (`wiki/tools/skill_invocation_channels.py`, 7 d, 1,969 transcripts, JSON-parsed):
  model `Skill` tool_use 463 (41 names); Owner/automation-typed `/command` 550 (7 names). Positive
  control: this session's typed `/kresume` left NO Skill tool_use, only a `<command-name>` row.
  Names a tool_use-only counter reports as ZERO: `/cpp-compound` 33, `/restart` 4.
  A substring search over the same transcript also matched the probe's own command text (trap).
- Not observable as invocation at all: bodies injected by hooks (SessionStart `using-superpowers`, JIT
  spec injection, doctrine cards). These DELIVER capability without any invocation event.
- Estate: 352 distinct listed (30 d), 50 invoked via tool_use (`skill_keep_list.2026-10-03.out`);
  ACV scan: 237 SKILL.md / 197 unique names / 69,358 description bytes.
- Listing rent: one session's listing = 30,000 chars (harness cap), 269 entries; ~6.5k tok neutral cwd,
  ~9.4k in a 276-skill session, of a ~114k first call (~6-8 %). The cap TRUNCATES descriptions: CWST,
  guard-event-reachability, presence-is-not-residency appear name-only (audit G5). Rent is capped; the
  cost is now RECALL, not tokens.
- Event vs judgement delivery (R2 scan): 9 moved rule-skills invoked 14x since 09-29, 5 never;
  destructive card (event) denied-with-card 86x in 17,177 shell judgements.
- Existing candidate-suggester: `modules/zero-crash/hooks/skill-heat-map-advisor.js` (BL-0018,
  lexical, 82-skill heat map, PreToolUse Bash/Edit/Write, advisory). This session: 3 advisories,
  0 relevant, 2 named skills not installed here (stale map). n=3: anecdote, not a rate.

## Decisions
1. Opportunity v1 (CWST only): at a `git commit` tool_use, the index or the commit's pathspec carries
   a hunk this session did not write (session write set = `rollover.session_writes`, foreign check =
   `rollover.foreign_custody` pattern + `git diff --cached -U0`). External, deterministic, no CoT.
2. Delivery: Skill tool_use `input.skill == concurrent-writers-shared-tree` OR a card ledger row with
   this session_id, timestamped BEFORE the commit tool_use. Resident pointer text = floor, never counted.
   Missed = opportunity true and neither before the commit. Stronger alternative = card deny/ask that
   lists per-file hunks.
3. Contribution now: behavioural grade only (G7 table). Contribution claims: LATER.
4. Representation CWST: PAGED SKILL + COMMIT-TIME EVENT CARD (compile-out of the hard part), card
   starts LEDGER-ONLY = the shadow opportunity detector; deny mode only after P-arm evidence.
   Revert path kept (backup).
5. Never-invoked: label "no observed invocation (2 channels)"; triage report only, no deletion.
6. Listing: tokens NOT the bottleneck (capped); recall IS. NOW: `skillOverrides` name-only for the 142
   (Owner step, HR-001), re-measure whether CWST/TFPS/SSEA descriptions become visible. Listing
   virtualization architecture: LATER.
7. Telemetry: CO-12 `record_signal`, kind `capability.opportunity`, one row per opportunity (not per
   skill): {capability, session, basis, delivered_by: skill|card|none, before_action, outcome?}.
   Converge with ACV C5 `agent_telemetry.py` adapter if it lands first; never a new ledger.
8. R2 future: TFPS/SSEA wait for the CWST positive result; then N0 screen under SPLIT (SSEA authority
   core stays resident).

## Micro-commit DAG
C0 this plan + invocation-channel instrument and output.
C1 `tools/skill_invocations.py` + `tools/test_skill_invocations.py` (V-SKINV-*): two channels; listing,
   pointer, hook text, tool input mentioning a name -> 0; fixtures cut from real transcripts.
C2 `p3_delivery.py` + CWST natural positive task (unlabeled foreign hunk) + G7 grader (R2 G1/G7/G8).
C3 N0 x2 screen; if discriminating, R x2 + P x2; G5 listing check; report.
C4 `hooks/doctrine_cards.js` commit card, LEDGER-ONLY, + test; destructive card 15/15 unchanged (G9).
C5 card emits `capability.opportunity` via record_signal (isolated state in tests).
C6 Owner applies skillOverrides; re-measure listing + description visibility.
C7 zero-observed triage report (classes, no action).
C8 CWST verdict; then TFPS / SSEA N0 screens under SPLIT.
C9 KV + UKDL (only earned entries) + resumption.
