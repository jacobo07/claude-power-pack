# S23 PLAN — GSDX-UNIVERSAL-WII: reconcile S22, compositional search, context identity, cross-title transfer

Status: PROPOSED, not armed. Brief: Owner /cpp-gsd-long paste "GSD X RECONSTRUCTION ASCENSION PRINCIPAL ARCHITECT"
(laptop session 978a21cc, 2026-11-09). Approval surface: the inline plan in that session; this file is the backup.

## Reality scan (measured 2026-11-09 16:07Z)
- Laptop PP: branch feature/knowledge-acquisition, HEAD eb4fbb40 (local, unpushed backlog commit); origin/main d5825825.
  `modules/reconstruction_factory/` (29 modules incl. operators, permute, method_graph, genome, heldout, judge, certify)
  lives on origin/main, not on this branch. GEX44 copy: /home/kobii/missions/recon-general 429b0126.
- GEX44 live PP d23f6d8c (13 dirty, not mine). t1/campaign 2ca2530f (1090 dirty paths, pre-existing); gen3 671a2c86.
- S22 m-4a5a719551ae: state RUNNING, owner_hold kind=cost (breaker 7,810,901 >= 8M - 0.4M reserve at 14:01:38Z),
  worker f271b7bd dead. Roadmap W0, W1 ticked; W2..W5 open.
- Other gen3 mission m-e0cb2c1792f9: PREPARED, held "superseded ... never launch" since 2026-11-03. Not a live writer.
- Iteration file: laptop and gen3 copies identical (sha256 f7c579b1168e, 6862 B).

## Premises in the brief that the scan falsified or sharpened
1. "W2 is next" is FALSE. W2 and W3 RAN (13:51-14:00Z) before the breaker; their evidence is on disk UNTRACKED
   (t1 evidence/ascension/s22/w2/, w3/, tools/s22_w2.py, tools/s22_w3.py):
   - W2 search on the 6: fn_8024E024 EXHAUSTED at 99.412%; fn_80251618 EXHAUSTED 64.41%; fn_80250D58 BUDGET_EVALS
     60.7 -> 63.7%; 0 exact. The existing operator vocabulary exhausts on the best near-miss.
   - W3 candidate C1_slot_unk2C_unk4C: fn_8024E284 NO_COMPILE -> COMPILES (29.2%), 0 exact, 0/1058 regressions,
     controls 12/0/5, ctx 6b9e5f71 (isolated).
   - Canonical moves over W1-W3: 0. Isolated moves: 7 to COMPILES, 0 exact.
2. "568 unreproduced_pre" is most likely an instrument-scope artefact, not 568 failed reproductions:
   pre_reproduces_recorded 490 == by_kind.cert1 490 exactly, and 568 == llm 492 + toolchain 76 exactly.
   Hypothesis: only cert1 rows carry a comparable recorded object hash. To verify in E02 (cheap).
3. MANIFEST_CTX fired at check 1 (manifest identity), before any compile: the C++ refusal is silent on the
   assembly. `not_replayed.other = -2` is a real accounting defect (to fix with a regression test).

## Work units (DAG; each is EXECUTION mode unless marked)
- WU0 Close S22 honestly (authority: S22's own 0.4M closeout reserve + an Owner close). Land the W2/W3 evidence by
  the producing mission, write W5 closeout with the stop-rule verdict (canonical 0 moved -> BUDGET_EXHAUSTED per its
  rule; isolated 7 COMPILES recorded separately), then `gsd_mission.py close`.
- WU1 E01 context-identity discriminator (deterministic, isolated): compile the 6 C++ units under the patched ctx in a
  copy, objdiff vs their certified objects. Identical bytes -> the refusal is integrity-only, and landing needs an
  Owner-authorised new certificate identity (old certificates preserved). Different -> R2 changes C++ output; not landable.
- WU2 E02 replay attribution: confirm or refute the cert1-only hypothesis; fix `not_replayed` arithmetic with a test.
- WU3 Ownership map (no code): CPP reconstruction_factory (operators, permute, method_graph, genome, heldout, judge)
  vs t1 recon_fabric (search_ops, g4_ops, search_plan, compiler_causality, causal_diff, microscope, llm_fix).
  Verdict per responsibility: REUSE / EXTEND / CONNECT / MERGE / RETIRE / NEW. NEW needs evidence.
- WU4 E03+E07 compositional search pilot (the main bet). Measure exhaustion first (done for 3 fns in W2). Extend the
  existing search with (a) multi-hunk macros mined from the S17 natural successes (S20 autopsy: 19/42 need 4-12 hunks)
  and (b) a non-monotone k-best frontier instead of strict-rise best.c. Train on S17 trajectories only; dev cohort =
  COMPILES_NO_MATCH residue minus H2, family-disjoint from train, frozen by commit before any run; a separate heldout.
  First value = one exact certificate via certify.py on a function not used to build the mechanism.
  External priors for the WU4 operator vocabulary (research_notes/Herramientas decomp Wii en GitHub/
  mwcc_near_miss_causes.md, community sources, hypotheses until measured here): register colouring moves with value
  lifetimes (temp vs local, inline helpers, `&x` lifetime split), not with declaration order; function-scoped pragmas
  (scheduling, opt_propagation, opt_common_subs) are fakematch-risk operators and must be labelled as such;
  `-inline deferred` emits a file's functions in reverse source order. decomp-permuter (PPC) added if/else reversal
  and variable merge in 2026 -- candidate operators. Triage the 158 by diff kind, not by percentage.
- WU4b E05 for the NO_COMPILE residue: per-file generated context (dtk-template decompctx pattern) plus m2c
  `--valid-syntax` (M2C_FIELD) to move NO_COMPILE into the near-miss queue; measured as COMPILES moves, never certs.
- WU5 E04+E05 versioned context variants: immutable ctx variants with provenance (R2, C1 first), evaluated beside the
  canonical ctx, never replacing it; production use is an Owner gate (new certificate contract).
- WU6 E08/E12 cross-title transfer: apply the WU4 mechanism to the KSR (WSR) frontier (t1 evidence/ksr-frontier:
  8,687 CERTIFIED / 9,941 COMPILES_NO_MATCH / 5,453 NO_COMPILE) and certify under the KSR certifier.
- WU7 Institutionalise: UKDL (vault/knowledge_base/ukdl-universal.md is canonical), KV, CEPS, baseline ratchet with
  consumer + fresh-agent test, handoff, meta-analysis.
Order: WU0 || WU1 || WU2 -> WU3 -> WU4 -> (WU5 if WU1 says integrity-only) -> WU6 -> WU7.

## Budget (proposal; mission authority is metered in PROCESSED tokens, llm_fix children in FRESH)
Measured: S22 spent 7.8M processed on W0-W3 with zero model calls; S21 56.2M processed for a full generation.
- Checkpoint A (WU0-WU3): 15M processed worker, 0 fresh children.
- Checkpoint B (WU4): +25M processed, <= 3M fresh children.
- Checkpoint C (WU5): +10M processed, <= 0.5M fresh.
- Checkpoint D (WU6): +25M processed, <= 3M fresh.
- Checkpoint E (WU7): +10M processed, <= 0.5M fresh.
Ceiling 85M processed / 7M fresh, 12 cycles / 24 h, paid USD 0. Each checkpoint opens only on a typed Owner turn.

## Invariants
certify.py and cert_cxx semantics and PIN_SHA unchanged; H2 sealed (922f214e); SDA NO; canonical ctx a9761086
unchanged; no push from GEX44; worker never edits a PP checkout (CPP changes go through the laptop coordinator);
waits on pid/sentinel; two causally equivalent failures -> pivot; COMPILES is never counted as certified.

## Done-gates
A repo reality · B S22 context diagnosed (WU1) · C instrument reconciled (WU2) · D DAG respected · E S17-S20 corpus
structured · F compositional mechanism on an unseen cohort · G any new cert via canonical certify + FRONTIER_CHECK OK
· H economics vs S17-S22 baseline · I transfer on KSR under its certifier · J judge independence · K-L production and
regression · M-O KV/UKDL/ratchet with consumers · P micro-commits · Q fresh-agent test · R meta-analysis.
