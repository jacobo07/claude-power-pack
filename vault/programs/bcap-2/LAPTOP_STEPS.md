# BCAP-2 laptop-plane steps

## BLOCKED-ON-LAPTOP
- Phase 5 (Synsation): the four source videos are not on GEX44. Re-inspect them with audio/transcript to confirm wording-dependent claims (UX-07..20 stay INFERRED until then).
- Phases 4/5: real-browser verification (real hitboxes, focus/scroll to first invalid field, CLS of skeletons, optimistic rollback, reduced-motion exercised, timeline cancel/unmount cleanup).
- Phase 9 (Ruflo): activation is refused. To go READY_FOR_CANARY, on an isolated plane: `python3 vault/programs/bcap-2/ruflo/install_sandbox.py 3.78.0 <fresh dir>`, then drive each GHSA/#3294 fixture against the real MCP transport through `modules/ruflo_gate` and record `npm audit --json` + `npm audit signatures`. Owner approval needed before anything leaves the sandbox.
