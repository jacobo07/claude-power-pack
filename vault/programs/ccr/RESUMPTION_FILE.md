# RESUMPTION_FILE: ccr (CPP Cognitive Runtime as a Claude Code mod)

**Identity.** Claude Power Pack, `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`
(shared tree, 1000+ foreign dirty files: pathspec-scoped commits only). Goal `ccr`, cap 36,880,000; at 2026-10-12
used 5,171,864, remaining 31,708,136 (`goal-status`; pane c13cda65 is not bound to the goal, so its spend is not in
the ledger). The approved 66.2M raise stays unapplied: not needed.
Plans: `vault/plans/ccr-v2-enforcement-2026-10-11.md` + `ccr-v2-addendum-2026-10-11.md` + **`ccr-v2-addendum-umvm-2026-10-12.md`**.
**Owner: session c13cda65** (took over from 8f164910 on 2026-10-12; do not run both).

**State (coherence anchor: HEAD contains the "feat(ccr M2)" commit after 226fcc12).**
- SEALED: S1-S4; **M1 226fcc12** (carry receipts + rotate advice, observe only); **M2** pixel GC, opt-in
  `CCR_PIXEL_GC=0` + a driver `/compact` turn: full transcript rebuild with no summarizer, image tombstones, image
  map read back from the transcript (a `--resume` turn is a fresh process). Dev-only; release still 0.1.0-feaae8b0.
- Image cost truth: ceil(w*h/750) as sent, no MP cap. Image share of Madzia workers: 16.8 % / 9.3 % / 10.5 %.
  Text transcript carry dominates (a3: 53 calls, 4.0M tok, ctx 20K -> 113K). S4 negative knowledge stands.
- Host limits (2.1.296): `$.session.compact()` refused headless; a mixed handle/rebuilt kept-set is a silent no-op.
- Price caveat: GC and rotation rewrite the cache prefix (~80K cw); ledger-token savings can be price losses.

**Active decisions.** Pixels are a minority rent; do not build more pixel-only machinery. The next lever is
text carry: the same full-rebuild path can project dead tool-result TEXT (v2 §4.1 was demoted on the inflated 55 %
image figure; re-rank it on measured shares). Rotation (B) vs in-place rebuild (D+text) is decided per metric.

**M3 (11444399), text carry measured.** Tool-result text 44.9 % of a3, but superseded Reads reclaim 0 tokens:
in-place text projection has no safe liveness signal (NO_WORK). ~0.73M of a3's text carry is invisible in the
stream (likely carried thinking); row receipts now count `thinking`/`sealed`. The lever is epoch length (arm B).

**Next 3 actions.**
1. Arm B at the next Madzia driver run (after the Owner's phase-2 strategy decision; driver stopped at
   `OWNER_STRATEGY`): driver reads `<ccr state>/advice/<sid>.json` and rotates with a successor ContextImage;
   compare tokens per accepted transition + reviewer verdict vs a2/a3 (A baseline, no re-run).
2. With the dev mod loaded on that run, read the live `thinking`/`sealed` row receipts to close the 0.73M gap.
3. Release M1-M3 (`tools/ccr_release.py`) only after that canary.

**Start.** `python tools/mission_spend.py goal-status --goal ccr`, then action 1.
