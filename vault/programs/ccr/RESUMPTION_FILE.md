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

**M4 (a4/a5, 2026-10-12).** Owner ruled phase 2 head-only; driver relaunched ON THE LAPTOP (pid 13924), a4
accepted (2.22M), a5 1.90M, a6 running. Shell results 32-38 %; one call-2 recursive listing of the runs tree is
up to 0.30-0.34M tok per attempt (14-18 %), more than all image carry. Owner says Madzia moves to GEX44: dev mod
staged and proven there (`/home/kobii/ccr-dev/cpp-cognitive-runtime`, smoke d670c760 ctx == usage).

**Next 3 actions.**
1. Driver owner (not this pane while the driver is live): ContextImage lists prior-attempt evidence paths, no
   runs-tree listing. Gate: a7+ call-2 shell result < 2K chars; processed/attempt vs a4/a5 at reviewer parity.
2. On the GEX44 driver: worker gets `--plugin-dir /home/kobii/ccr-dev/cpp-cognitive-runtime`; arm B = driver
   reads `.state-dev/advice/<sid>.json` and rotates with a successor ContextImage. Read live `thinking`/`sealed`
   receipts there to close the 0.73M gap. Linux worker needs `Bash`, not `PowerShell`, in `--tools`.
3. Release M1-M3 (`tools/ccr_release.py`) only after that canary.

**Start.** `python tools/mission_spend.py goal-status --goal ccr`; check where the Madzia driver runs
(laptop `boundary.py` process vs GEX44), then action 1 or 2.
