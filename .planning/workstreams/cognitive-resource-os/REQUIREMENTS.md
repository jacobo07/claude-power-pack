# Requirements: Cognitive Resource OS (GEX44 workstream)

## v1 Requirements

- [ ] **CRO-01**: The workstream's gates and the full pytest suite have a recorded verdict on an unstarved host, with a dirty-set bracket.
- [x] **CRO-02**: GEX44's own transcripts yield an observed usage baseline split by entrypoint, compared with the laptop's.
- [x] **CRO-03**: The P3 ablation's pre-flight P0 has a PASS (named mechanism) or STOP verdict, reached without model calls.
- [x] **CRO-04**: The cross-session prefix cache-miss hypothesis (MCP tool-list variance) is tested on subscription quota and judged.
- [x] **CRO-05**: RESUMPTION and UKDL carry every verdict; every result is committed on the mission branch for the laptop to fetch.

## Out of Scope

- Running the P3 ablation itself or relocating any rule (needs P0 PASS and an Owner-visible result first).
- Editing tools/gsd_mission.py, gsd-x closure, or consolidating transcript parsers (peer-owned).
- Any paid (API-key) model spend.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CRO-01 | Phase 1 | Pending |
| CRO-02 | Phase 2 | Complete |
| CRO-03 | Phase 3 | Complete |
| CRO-04 | Phase 4 | Complete |
| CRO-05 | Phase 5 | Complete |
