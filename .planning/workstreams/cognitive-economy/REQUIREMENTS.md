# Requirements: Cognitive Economy Program (cognitive-economy workstream)

Each requirement is satisfied when its pillar's ledger entry reaches a terminal that
`python tools/test_cognitive_economy_program.py --pillar <P>` prints PASS for. The pillar's frozen rule
(ledger `frozen.pillars`) decides WHICH terminal; this file does not.

A checked box means "terminal reached and gate PASS", not "built here". The Status column carries the
ledger terminal; read it before treating a pillar as implemented.

## v1 Requirements

- [x] **CE-A**: Baseline cognitive economics -- re-runnable baseline gate; before/after snapshots on the same command.
- [x] **CE-B**: Resident context floor -- remaining rules->skills moves batched for the Owner (CCP / R2 / P3 own the moves).
- [x] **CE-C**: Capability virtualization -- skills/agents handed to their owners; tool-schema residency measured.
- [x] **CE-D**: Context lifetime -- realized savings of the live economic rollover trigger measured with displacement.
- [x] **CE-E**: Fresh-epoch economics -- continuation vs rotation measured from the epoch census.
- [x] **CE-F**: Reread / materialized cognition -- sibling identical-dependency re-reads measured.
- [x] **CE-G**: Common cognitive subexpression elimination -- decided from F's identity evidence.
- [x] **CE-H**: Turns per verified advancement -- reproducible turn taxonomy with a gate.
- [x] **CE-I**: Work packet -- existing owner verified and handed off.
- [x] **CE-J**: Non-convergence -- decided from H.
- [x] **CE-K**: Tool output admission -- KSR instrument replicated on the CPP corpus.
- [x] **CE-L**: Capability compile-out -- compound steps 7+8 module proven on a temp state copy.
- [x] **CE-M**: Model allocation -- handed to CCP C4 / Owner (quota).
- [x] **CE-N**: Event-driven cognition -- existing sweeps verified and handed off.
- [x] **CE-O**: Cognitive IR -- Goal spine verified; shared-checkout tree-pin finding handed to its owner.
- [x] **CE-P**: Proof reuse -- verification share measured.
- [x] **CE-Q**: Technical capital accounting -- CAPEX/OPEX per pillar in the ledger.
- [x] **CE-R**: Institutionalization -- UKDL 3-level + CBR review in the campaign candidates file.
- [x] **CE-S**: Universal baseline compiler -- trait -> obligation derivation audited.
- [x] **CE-T**: Institutional GC -- liveness sweep; retirements batched for the Owner.

## Out of Scope

- Editing any peer-owned surface listed in ROADMAP "Operating constraints".
- Reopening falsified slices (KSR generated view, tool-I/O firewall, 5-min TTL) without new evidence.
- Paid API spend, new credentials, GEX44, pushing, external publication.

## Traceability

Synced 2026-10-04 from `ledger.json` `state` after `--pillar <P>` printed PASS for all 20 pillars and
`--status` reported open=[] violations=[]; `--final` CEP_VERDICT=PASS failures=0 (after acbaabcf).

| Requirement | Phase | Status |
|-------------|-------|--------|
| CE-A | Phase 1 | Complete -- IMPLEMENTED_AND_VERIFIED |
| CE-I | Phase 1 | Complete -- MERGED_INTO_EXISTING_OWNER |
| CE-N | Phase 1 | Complete -- MERGED_INTO_EXISTING_OWNER |
| CE-O | Phase 1 | Complete -- MERGED_INTO_EXISTING_OWNER |
| CE-Q | Phase 1 | Complete -- MERGED_INTO_EXISTING_OWNER |
| CE-D | Phase 2 | Complete -- MERGED_INTO_EXISTING_OWNER |
| CE-E | Phase 2 | Complete -- MERGED_INTO_EXISTING_OWNER |
| CE-H | Phase 3 | Complete -- IMPLEMENTED_AND_VERIFIED |
| CE-J | Phase 3 | Complete -- DEFERRED_STRONGER_OWNER |
| CE-F | Phase 4 | Complete -- FALSIFIED_OR_REJECTED_BY_EVIDENCE |
| CE-G | Phase 4 | Complete -- FALSIFIED_OR_REJECTED_BY_EVIDENCE |
| CE-K | Phase 4 | Complete (closed early, epoch 2) -- FALSIFIED_OR_REJECTED_BY_EVIDENCE |
| CE-P | Phase 4 | Complete -- FALSIFIED_OR_REJECTED_BY_EVIDENCE |
| CE-C | Phase 4 / 7 | Complete -- DEFERRED_STRONGER_OWNER |
| CE-L | Phase 5 | Complete -- IMPLEMENTED_AND_VERIFIED |
| CE-S | Phase 6 | Complete -- MERGED_INTO_EXISTING_OWNER |
| CE-T | Phase 6 | Complete -- AUTHORIZATION_BOUND (retirements in owner-bundle) |
| CE-B | Phase 7 | Complete -- AUTHORIZATION_BOUND (moves in owner-bundle) |
| CE-M | Phase 7 | Complete -- DEFERRED_STRONGER_OWNER |
| CE-R | Phase 7 | Complete -- IMPLEMENTED_AND_VERIFIED |
