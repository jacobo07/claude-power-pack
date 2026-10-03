---
id: PLAN-INCREMENTAL-COGNITION-PROGRAM
date: 2026-10-03
status: APPROVED 2026-10-03 (Owner "y" to the inline plan; this file mirrors it)
covers: [incremental-cognition, context-rent, institutional-memoization, invalidation, cognitive-compiler, baseline-ratchet, incremental-cognition-program]
parents: [vault/plans/cognitive-economy-program-2026-10-03.md, vault/plans/skill-capability-program-2026-10-03.md]
mode: one ULTRA reconciliation; EXECUTION MODE from P0 onward
done_gate: python tools/test_incremental_cognition_program.py --final
workstream: .planning/workstreams/incremental-cognition
---

# Incremental Cognition -- delta program over cognitive-economy (CE) and skill-capability (SC)

## Reality at drafting (HEAD bd5a5a5c, 2026-10-03 ~17:50 local), measured
- Branch feature/knowledge-acquisition, origin +26/-0, ~40+ dirty paths owned by peers. 15 worktrees.
- CE program (pillars A-T, approved 15:50 today) is the owner of most of this prompt. Mission
  m-fdefb0fca0c0 record says RUNNING but its owner is DEAD and every relay is HELD:
  "cwd not aligned with work_dir (diverged)" (tools/gsd_mission.py:1583 align_cwd). The worker entered
  .claude/worktrees/cognitive-economy (branch cognitive-economy/autonomous-run, 12 commits, phases 1-2 done,
  last 17:19) while peers committed 4 times to main. ucep m-876f8b5a904a: same hold, 149 behind.
- SC program (pillars A-N) approved 17:38, P0 not started, arming gated on >= 4 GB free RAM.
- RAM 3.1 GB free / 31.3, 31 claude.exe. Sweep healthy (heartbeat 17:46, rc 0).
- CE ledger on its branch: A IMPLEMENTED; D, E, I, N, O, Q MERGED (measured); K measured "no class >= 3 %" (wip).

## Thesis
Not a third mega-program. A DELTA program: only pillars no CE/SC pillar owns, plus the repair that makes
every mission in a shared checkout survive (repair clause). Everything else is consumed from CE/SC ledgers.

## Pillars (ledger ids A..N; prompt letters in brackets)
A [repair] /cpp-gsd-long relay in a shared checkout when the worker's worktree diverges from main.
B [V] GEX44 remote environment integrity: preflight (auth, rules version, hook health, interpreters, repo id).
C [W] persistent-failure retry classification (auth-expired relaunch loop; local Ralph + GEX44 sweep).
D [X] silent-success hooks: measure per-call additionalContext rent, then act through the hook dispatcher owner.
E [G,H,AA] large-source read virtualization: KME corpus replay of the CE-F/K instrument; build only if material.
F [U] GSD operational projection: measure workflow-doc residency; prefer existing gsd-tools init JSON.
G [J,K,L,M,AE] derived cognition + invalidation + decision/negative reuse: one falsifiable slice on an existing owner.
H [O,AD,N] proof reuse / singleflight / CCSE: consume CE P and G verdicts; KME-specific re-check only.
I [T,B,C,D,E,AB] startup floor + subagent bootstrap: consume CE B and SC A-C; add subagent-floor measurement.
J [R,P,Q,AC,S] context lifetime / rollover / zero-transcript / context images: consume CE D, E, I.
K [AK] cognitive cost regression: connect the existing floor probe to a ratchet, scoped by layer.
L [AL,AM,AN,AO] held-out gym + lower bound + regret: KME champion/challenger + one independent workload.
M [AP,AQ,AR,AS,AF,AG,AH,AI,AJ,Y,Z] optimizer/experiments/negative capital/routing/events/reality model: dispositions only.
N closeout: UKDL 3 levels, CBR, baseline, Vault, product/intelligence deltas, institutional GC (with CE T).

## Done-gate (fixed now, file created in P0)
python tools/test_incremental_cognition_program.py --final
= thin wrapper over tools/test_cognitive_economy_program.py (SC precedent): rebind LEDGER_REL, FROZEN_AT_REL,
HANDOFF_DIR, PILLARS=A..N, SELF_REL; never edit the CE file. --selftest must kill every ledger mutant.

## Owner boundaries
GEX44 /login (interactive OAuth); quota spend for KME champion/challenger sessions; global settings/rules edits
(HR-001); arming only at >= 4 GB free RAM (SC boundary); no push while peer commits interleave.
