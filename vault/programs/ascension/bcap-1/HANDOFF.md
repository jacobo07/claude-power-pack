# HANDOFF: Ascension campaign 1 (Universal Backlog-to-Capability) -- PARTIALLY PROVEN

Branch `mission/ascension-run`, worktree `~/missions/ascension/.claude/worktrees/ascension`. Nothing pushed, no PR, no merge. Base 2f9386f6.
Verdict command: `python3 vault/programs/ascension/bcap-1/done_gate.py --campaign 1` -> all 7 gates PASS, verdict PARTIALLY_PROVEN (never COMPLETE: four items below are unprovable on this host).

## Owner summary
- Inventory: 620 raw records -> 471 obligation identities, discovered not curated (V-ASC-INV).
- Ledger: RECONCILIATION 372/471 = 0.79; OPERATIONAL 3/373 = 0.008 (only three obligations have recorded exit-0 execution evidence). Two metrics, two denominators.
- Web slice: 12 mandatory cases from both poles (V-ASC-WEB); slice passed CDIO, Production Reality and legal gates after a missing terms page was added, not waived.
- CCF: 5 integrity defects reproduced then fixed in the existing owner (bytes kept, manifest, kit embeds logo, BLOCK before provider, evidence before SEALED), V-ASC-CCF RED->GREEN.
- Baseline: `web_surface` B5 promoted with 2 CONSTITUTIVE rules (privacy and terms pages linked); 4 other deltas refused by name. A fresh `claude -p` given the baseline wrote the legal pages unasked; the control and an incomplete variant were rejected (N=1, mechanism not rate).
- Liveness: the four `backlog_autopilot` modules are now reached through `commands/backlog-to-capability.md` (V-ASC-LIVE, both poles). Repo-wide offenders: 61 -> 56, all pre-existing.
- Immunity: UKDL section "Ascension campaign 1" in `vault/knowledge_base/ukdl-universal.md`. One TRAP has 2-subsystem proof; the rest are OBSERVED, none promoted to HR.
- Defect found and fixed in my own gate: V-ASC-BASE passed 3 runs then failed (offer counter in real `~/.claude/state/tower`); now hermetic, 4 consecutive greens.

## UNPROVEN (named residuals)
1. Live hook delivery of B5 (needs merge+sync): LAPTOP_STEPS.md 3.
2. Taste Skill, ASTRYX, Design Index reachability: LAPTOP_STEPS.md 1-2.
3. Inheritance rate (one agent pair). 4. CCF PDF carries a hash, not an embedded image; trademark scanner recall is low (a literal Nike tick scored PASS); no live provider run (no paid calls).
5. Two pre-existing Linux-only failures in family-baseline tests: LAPTOP_STEPS.md 4.
Spend: phase 5 pair measured 568,459 tokens; other phases UNMEASURED per phase (no session id for mission_spend).

## Engineering handoff
- Gates: tools/test_asc_{inventory,ledger,webslice,ccf,baseline,liveness}.py, tools/test_gsd_mission_parked_label.py. Artifacts under vault/programs/ascension/{phase1,phase2,phase3}/ and bcap-1/phase5/.
- Next for the coordinator: review and merge `mission/ascension-run` (Owner-gated), sync live tree, then LAPTOP_STEPS 1-4. Do not edit other files in vault/programs/ascension/ (KSR programme).
