> **STALE (2026-10-25).** S2/S3 (af7ec647) and S4 (44396331) landed after this file's anchor 4e9953a7, so the "do S1" line below is
> stale. The anchor check passes only because 4e9953a7 is an ancestor of HEAD. NEXT is its owner's decision; nothing else here was changed.

# RESUMPTION_FILE: econ-succession

**Identity.** Claude Power Pack, `C:\Users\User\.claude\skills\claude-power-pack`, branch
`feature/knowledge-acquisition`. Goal `econ-succession`. Plan: `vault/plans/econ-succession-2026-10-11.md`
(sections 4-7: architecture, security, workstreams S0-S10, canaries). Thesis: after a tombstone, one
Owner approval becomes a durable receipt before the model, and a journalled transaction opens the
successor lease and launches the next work unit. No Owner plumbing.

**State (coherence anchor: HEAD contains commit 4e9953a7 "plan(econ-succession)").**
- Owner typed `approve p80` on 2026-10-11T07:44:25.111Z, transcript of session 28a5bd61, entry uuid
  25a5410c-54d3-4e9b-a944-3d8089f069fe, for packet
  `~/.claude/state/capital-authority/packets/econ-succession-2026-10-11.json`
  (sha256 86ba1888c7bda34779eae9e21ba749ba638eb1b8dab132febf9bc59add83ca4d). Verified with
  `capital_authority.find_owner_decisions`.
- SEALED S0: goal econ-succession declared (L1 cap 20,000,000, no root); capital APPLIED for
  econ-succession (programme 20,000,000, P80) in capsules.jsonl; session 28a5bd61 bound since the
  approval. The 5a capital files are clean (last commit 2026-10-10); `tools/gsd_mission.py` is dirty
  by another writer: call it, never edit it.
- NOT APPLIED on purpose: the econ-contain-2 half of the same packet (P80 ceiling 49,000,000). It is
  the real canary (S9) for succession.py. Its authority is the transcript entry above; S3 must turn
  it into a durable receipt. Packet expiry 2026-10-14T00:00:00Z (approval came before it).
- econ-contain-2 untouched: L1 used 22,756,864, reserved 1,379,100 (a9647f12 1,239,905 real, measured
  +1,263,445; b1876f55 139,195, measured +138,594, 601 stale). fd25efd1 still to be recorded INVALIDATED.
- The packet's 150K per-call stop-loss fired in the planning pane (~227K context per call; the fresh
  floor here is 139K, so it can never hold). Spend on econ-succession then: about 1.6M. The scan
  before approval cost 4.9M, unbound.
- OWNER RULE 2026-10-11 ("continue but with context rent"): CONTINUE. The per-call stop-loss is
  replaced by context rent: rotate in place (/kclear -> /clear -> /kresume) when the saving per call
  reaches 150K, or at any sealed workstream boundary. Stop-loss is now: a workstream exceeds 3x its
  P50 row, or the 20M ceiling would be crossed.

**Active decisions.**
- Keep going in this pane lineage; rotate through /kclear at each sealed workstream.
- No settings.json edits: the approval verb goes into `hooks/econ_admission.js` (already registered).
- S1 decides whether hook-attested provenance ships; if no field separates interactive from headless,
  it does not ship.

**Next 3 actions.**
1. Bind your session first: write `~/.claude/state/goal-binding/<your sid>.json` =
   `{"goal":"econ-succession","since_ts":"<your first transcript ts, UTC>","source":"explicit","pid":0}`.
2. Run `python tools/mission_spend.py goal-status --goal econ-succession`, then do S1 (bounded: 6 calls).
3. Then S3 + S2, red tests first in `tools/test_econ_succession.py`; commit per workstream; update this file.

**Start.** Read this file and plan sections 4-7, then do action 1.
