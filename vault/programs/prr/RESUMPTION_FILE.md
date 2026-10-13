# RESUMPTION_FILE: prr (Physical Runtime Working Set)

**Identity.** Claude Power Pack. PRR now lives on **main** (fast-forward `b8a98796..5a48019a`, 2026-10-13: the 16
PRR-owned commits ported with `-x` onto clean main; `prr/main` is history only, never merge it). Work worktree:
`C:\Users\User\Apps\pp-prr-int`, branch `prr/integrate-2026-10-13` (tracks origin). The goal-bound root is still
`Apps/pp-prr`: never `Set-Location` into it (see memory feedback-coordinator-set-location-binds-goal). Goal `prr`:
programme 88,000,000 (OCA packet `prr-l3-successor-50m-2026-10-13`, sha 9c14194a...), lease **L3** `prr:D:r3`, cap
46,000,000 productive + 2,000,000 closeout + 2,000,000 recovery (protected: not for productive work). Plans:
`vault/plans/prr-physical-working-set-2026-10-12.md` and `vault/plans/prr-same-pid-continuation-2026-10-13.md`.
GEX44: clones `~/missions/prr-int/{prr-int,prr-int-base}`, bench data `~/prr-bench/runs/`.

**Owner direction 2026-10-13 (binding).** Scope is NOT narrowed. A: CPP-owned processes/state/inputs, directly.
B: what CPP feeds the host, indirectly. C: host frontier - claude.exe same-PID reclaim is HOST_LIMITATION /
CURRENTLY UNREACHABLE (evidence A1), never "impossible"; keep falsifiable invalidators. Restart is fallback only.
Priority order: 1 integration, 2 economic truth/successor/reserve, 3 Windows-vs-Linux attribution, 4 orphan census,
5 floor decomposition, 6 CPP-owned same-PID reclaim, 7 tool/artifact/image/agent residency, 8 MCP deflation,
9 PGO+forecast, 10 pressure/admission, 11 same-PID marathons (CPP-owned), 12 host frontier + restart fallback,
13 UKDL/FIOS/Vault/CBR. Do not return to the Owner for lease/session/pane mechanics.

**State (coherence anchor: main @ 5a48019a).** SEALED: A0 census, A1 matrix, B/C/D/E GEX44 evidence, recycle policy,
PGO ledger, UKDL block, D28 backlog. SEALED 2026-10-13: priority 1. Gates: PRR suites 37/37 (laptop); 11 shared-file
consumer tests identical failing-gate sets on main vs integration (GEX44); reachability 70 offenders on both, none PRR.
Pre-existing reds on main (not PRR): V-BASELINE-INTACT, V-RESTART-FLOW-COMPLETE, V-D2A-BASELINE,
V-CEPS-ADMIT-HERMETIC, V-CEPS-BRIDGE-SUBSYSTEM-IS-THE-TOOL; V-UKDL-NO-COLLISION reads the GLOBAL vault UKDL.

**Active decisions.** Laptop = light control plane while Available < 4 GB (2026-10-13: free 2.5-3.5 GB, census
"available" 388 MB - the two instruments disagree, resolve in priority 3). Heavy runs only on GEX44, one at a time.
No kill without ownership + liveness proof.

**Next 3 actions.**
1. Priority 3: per-process region attribution of one live claude.exe (private commit vs private working set vs image
   vs mapped, read-only) and the same split on a GEX44 claude (smaps_rollup). Test the hypothesis that ~887 MB
   "private" (commit) is not comparable with Linux anon RSS 107-160 MB.
2. Priority 4: classify the census's orphan candidates by ownership/liveness proof (read-only).
3. Priority 2: wire lease exhaustion -> settlement + successor inside programme authority (goal-succession).

**Start.** `python tools/mission_spend.py goal-status --goal prr` from the PP repo, then action 1.
