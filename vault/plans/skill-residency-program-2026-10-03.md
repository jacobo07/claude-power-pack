---
id: PLAN-SKILL-RESIDENCY
title: Skill residency program -- availability without residency, proven by need-time delivery
status: APPROVED (Owner "y" 2026-10-03, six defaults) + phase-4 EXECUTE-WITH-FIXES (vault/audits/skill-residency-audit.md)
defaults: C3 runs now (<=40 sessions); card LEDGER-ONLY first; Owner applies wiki/tools/skill_overrides.final.json (134, kobiicraft-* kept); this pane executes PLAN-R2-RESIDENCY; telemetry via CO-12 record_signal, converge with ACV C5 later; no push, no CLAUDE.md
harness: .planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/p3_delivery.py (C2, 755e857a)
fixes_injected: |
  G'1 opportunity = LINE-level ownership (Edit old/new_string, Write content, structuredPatch); shell write -> basis unknown.
  G'2 commit-plan parser + fixture table per commit form; unparsed = UNKNOWN, never "no opportunity".
  G'3 ledger-only card is never delivery; delivered_by=card only for deny-card before a later commit; Skill window = since previous commit, else session start.
  G'4 hook is pure node + one bounded git spawn; C5 = OFFLINE adapter card-ledger -> record_signal (CO-12 file is under a live peer edit: never a second writer).
  G'5 C4b = live dispatcher registration (Owner-visible, HR-001) + mirror sync + G9 procedure; liveness = own-session ledger row.
  G'6 card honours CLAUDE_DOCTRINE_CARDS / DOCTRINE_CARDS_STATE_DIR; runner sets both; rows carry source; C4 frozen until C3 ends.
  G'7 kind capability_opportunity; C8 report is its named consumer (positive control); foreign_custody reference dropped.
  G'8/G'9 C1 fixtures: order-agnostic command regex, installed-set filter, isMeta expansions count 0, dedupe, subagent dir joined by file sessionId.
  G'11 card returns before any I/O unless the commit regex matches; non-commit median measured.
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

## Results (2026-10-03, session bfe97833)
- C3 arm C on fixed card (123c96cc): 2/2 PASS, 1 commit each; ledger deny-card before the first commit
  in both; Skill never invoked. Prior: N0 0/2, R 0/2, P 0/2 (P-r1 stored PASS = amended shape, regrades
  FAIL-SWALLOW-REPAIRED), C-old 0/2. 10/40 sessions used. n=2 per arm.
- Card aperture (open): repo path or pathspec held in a shell variable -> `unknown`, allowed (r2's 2nd
  commit; live pane 2f6e9166 11:55:09).
- C4b DONE `91cdc85e`: card in PreToolUse-Bash-chain (Bash|PowerShell), live + mirror by edit (live still
  lacks the repo's 09-23 'skipped: <names>' hunk). Owner set CLAUDE_DOCTRINE_CARDS=deny in settings env;
  own-session ledger row mode=deny. Checks: 16/16, destructive 17/17 incl e2e, matcher-liveness 71/71.
- C6 DONE: 134 name-only overrides in ~/.claude/settings.json (backup
  ~/.claude/backups/settings.pre-skillOverrides-20261003.json). `wiki/tools/skill_listing_visibility.py`,
  initial listing before (bfe97833) vs after (fresh a5df8940): 29,991 -> 30,002 chars (still capped);
  overridden-and-described 21 -> 1; kept-but-name-only 19 -> 11. CWST and guard-event-reachability now
  described; presence-is-not-residency still name-only. Recall improved, cap still binds.
