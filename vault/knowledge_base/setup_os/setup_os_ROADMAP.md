# CPP Setup OS -- Pillar Roadmap

The dataset defines 10 pillars (Dataset CPP Setup 1.txt, secs. 1-10).
Sprint 3 built the 3 highest-ROI net-new pillars. Several others already
exist in the PP and are composed, not rebuilt (SCS C28: compose existing
primitives).

| # | Pillar | Status |
|---|---|---|
| 1 | Project Intelligence Scanner | **BUILT** -- `modules/setup_os/scanner.py` (`/scan-repo`) |
| 2 | Automation ROI Ranker | **BUILT** -- `modules/setup_os/roi_analyzer.py` (`/analyze-roi`) |
| 3 | Secret Firewall first | **COMPOSED** -- existing `modules/secret_firewall` (M1); the installer runs it before any plan is deemed safe |
| 4 | Dry-run Installer | **BUILT** -- `modules/setup_os/secure_installer.py` (`/setup-repo`) |
| 5 | One-Shot Setup Compiler | **COMPOSE-LATER** -- existing `modules/one_shot/compiler.py` already compiles task contracts; a setup-specific wrapper is the next step |
| 6 | Output Contract Registry | **EXISTS** -- `modules/output_contracts` (code/docs/deploy/test + per-tier OQS from Sprint 2) |
| 7 | Work Queue / What-Now | **EXISTS** -- `modules/backlog_autopilot` (`/what-now`); a setup->backlog bridge is the next step |
| 8 | MCP Recommender w/ governance | **DEFERRED** -- needs an MCP catalog + per-rec permission boundaries (dataset secs. 16, 145) |
| 9 | Subagents w/ operating contract | **DEFERRED** -- agent registry + work-order contract (dataset Part II secs. 44-46) |
| 10 | Self-Safe Evolution OS | **DEFERRED** -- feature flags / shadow / canary / kill-switch (dataset Part XV, ingested as `pp_dataset_15_self_safe_evolution_os.md`) |

## Next-best-actions (when resumed)
1. Pillar 5: wrap `one_shot.compiler` so `/setup-repo` emits a One-Shot
   contract per recommendation (scope + done-gate + budget).
2. Pillar 7: bridge `roi_analyzer` recommendations into
   `backlog_autopilot` BacklogItems so `/what-now` schedules them.
3. Pillar 8: MCP recommender reading the dataset's governance model.

No silent caps: pillars 8-10 are explicitly NOT built this sprint; the
scanner/ROI/installer triad is the executable core the official plugin
lacks.
