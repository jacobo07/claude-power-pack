---
id: PLAN-CEP-GEN3
date: 2026-10-07
status: APPROVED 2026-10-07 (Owner "y" to inline master plan, pane c77978f6); T1-T3 funded, stages 4-10 NOT funded
covers: [cep-gen3-t1-mandatory-envelope, cep-gen3-t2-floor-and-packet, cep-gen3-t3-recon-canary, cep-gen3-reforecast]
parents: [vault/programs/cognitive-economy/gen2/ledger.json, vault/specs/edd-compiled-execution-canary.md, vault/specs/goal-governed-mission-control.md]
mode: PLAN (frame) / EXECUTION per tranche. Run as a bounded /cpp-gsd-long mission: fresh workers, no coordinating Opus pane.
---

# Cognitive Economy gen3: enforce the envelope, attribute the floor, prove compiled execution on recon

Workers read THIS card and their own tranche section only. Not the source prompt, not any transcript.

## Verified at approval (2026-10-07)
- Recon-factory lineage: 1,179,796,538 processed / 4,274 calls, 15 mission records, token_estimate None on all
  (laptop transcripts, deduped by message id). Last measured rate: 33.2M for plans 04-01+04-02 (~16.6M/plan).
- Laptop non-terminal missions with no token_estimate: RUNNING m-42c68efbb4b4, m-5128a41e0398, m-6f7451aefe40;
  BLOCKED m-608c8d8d761f, m-a128e03c7419, m-b65977d380b3, m-ce41dd79ddd7. Owner did NOT decide on them: never touch.
- Admission gap: gsd_mission admission runs only `if rec.get("wu_packet")` (tools/gsd_mission.py ~887/931); a
  mission armed without a packet skips session-declare feasibility entirely.
- Reuse (never duplicate): gsd_mission envelope/hold/release/wu_packet; mission_spend session-declare + session-floors.jsonl;
  tranche_driver.py; cep_gen2 --tranche; gsd_dossier.py; source_packet.py / wu3_packets.py; floor_regression_gate --admit-cwd;
  wake_check.py; GGMC C1-C5; FIOS / usage_index; UKDL; CBR.
- Proven: EDD compiled 3.31M vs 32.06M+ champion (quality 6/8, 28 UNKNOWN); fresh workers ~96k floor, 0 transcript;
  WU2 dependency packet 3/3 critical whole vs current 0/3.
- Falsified (closed): F 1.88, K 2.67, P 0.50, C-tools 0.002, D 0.19, E 2.78 %.
- Known bugs: packet builder flags floor_regression_gate.py as credential-content (false positive, forces DEOPT);
  PP-Vault-Summarize missed its 2026-10-07 02:00 run (LastRun still 10-06 02:00); coordinating pane = top cost (5x).

## Tranches (hard cap 31M total; central ~22M; no borrowing between tranches)
T1 mandatory envelope (EXECUTION, 3M): a mission with no token_estimate AND no wu_packet is refused at launch
unless an explicit Owner waiver is recorded. Shadow first (log would-refuse rows), then enforce. Flip
CPP_MISSION_BOUNDED_RENEWAL shadow -> enforce if its shadow rows support it. Tests drive refuse and admit poles.
Real evidence: one real refused launch row in the ledger. Never edit or stop another pane's mission.
T2 floor + packet (EXECUTION, 3M): decompose the ~96k fresh-worker floor into host-forced vs CPP soft floor with
on/off probes; rank top controllable renters; fix the credential-content false positive (record in
governance/KNOWN_FALSE_POSITIVES.md); diagnose the missed 02:00 run; observe one real nightly run whose WAKE_FLAG
is consumed, else WAITING.
T3 recon canary (25M): finish recon-factory plan 04-03 (worktree C:\Users\User\Apps\recon_work\wt_keosdtk_home,
workstream recon-factory) under compiled grammar: gsd_dossier -> dependency packet -> one bounded worker -> gate.
Champion = measured 16.6M/plan. The hold on m-a128e03c7419 is the Owner's: T3 starts only via a NEW attempt that
supersedes it per GGMC (`arm --supersedes`), carrying token_estimate and the packet.
Reforecast: from T1-T3 receipts, cost stages 4-10. Not funded by this approval.

## Done-gates
Per tranche: `python tools/cep_gen2.py --tranche cep-gen3-t1|t2|t3` -- receipts + no violations + both-pole tests +
metered spend <= cap + Production Reality or explicit WAITING. Program: `python tools/test_cognitive_economy_program.py
--generation 3 --final` (cannot pass on this approval; not claimed).

## Rules
Pathspec commits, re-read HEAD first, never push. Calls per worker = cap / measured floor. Two equivalent failures =
change method. UKDL into ukdl-universal.md only when no foreign uncommitted hunks; else BLOCKED_BY_OWNERSHIP.

## Spend
| tranche | processed | calls | gate |
|---|---|---|---|
