# RESUMPTION_FILE: ccr (CPP Cognitive Runtime as a Claude Code mod)

**Identity.** Claude Power Pack, `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`
(shared tree, 1000+ foreign dirty files: pathspec-scoped commits only). Goal `ccr`, cap 36,880,000. Owner: session
**e10a9f08** (Owner-approved handoff 2026-10-12; c13cda65 and 8f164910 STANDBY). Plan of record:
`vault/plans/ccr-v4-boundary-cost-2026-10-12.md` (Stage 1 approved). Evidence: `vault/programs/ccr/evidence-v4-stage1.md`.

**State (coherence anchor: HEAD contains merge 54d35b33 "merge(ccr v4 Stage 1)").**
- SEALED earlier: S1-S4, M1 226fcc12, M2 53b4941d, M3 11444399, M4 evidence 164ae73f.
- SEALED v4 Stage 1 (branch ccr/v4, merged 54d35b33):
  - B5 94d7b49a: shell tool-output projection. Provider canary: carry -77 % at answer parity.
  - B3 e9c7f071: the "invisible 0.73M" was carried thinking blocks (a3: 1.20M, 40.8 % of carry; ablation-proven).
  - B4/B6 bb179e73: Work-Class model, contract receipt, per-call anomaly. Live canary reproduces M4 as costIfRides 334,773.
  - D1 d37bc362: Lobby unchanged re-reads 2.4 % + 2.2 %, so One-Read is NO_GO.
  - B2/U3 8789f534: elasticity 2.4K-3.3K across 100x estate. The T5 breaker already halts zero-progress lineages; docs-reset hypothesis rejected.
  - B1: the runs-tree dump was already gone from a6 onward (driver change upstream).
- NOT released: the live runtime is still 0.1.0-feaae8b0. The mod changes act only under `--plugin-dir` (dev).
- SPEND: this pane measured 27.9M processed over 144 calls (avg ctx ~194K) and was settled to goal ccr. The interactive
  coordinator pane runs CCR main=shadow, so it got none of the savings it built: self-hosting failed for the coordinator.

**Active decisions.** No Stage 2 spend without a re-forecast and capital: remaining authority after the settle is ~3-4M.
Stage 2 must not run in an interactive pane; run it as a declared Work Unit (projection enforce, lean floor).

**Next 3 actions.**
1. Owner decides capital for Stage 2 (E1 epoch economics with cw, M1 tiny continuation, V1 canary, X1 certify).
2. Release (`tools/ccr_release.py`) M1-M3 + v4 B5/B6 at a Madzia driver boundary, not mid-attempt. Units get
   projection enforce by default, so check whether the Madzia worker declares `CCR_WORK_UNIT` first.
3. Wire the pre-launch contract (`tools/ccr_pgo.py contract`) into `gsd_mission` launch admission (Economic bridge).

**Start.** `python tools/mission_spend.py goal-status --goal ccr`; then action 1.
