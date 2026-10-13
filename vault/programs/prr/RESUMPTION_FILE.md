# RESUMPTION_FILE: prr (Physical Runtime Working Set)

**Identity.** Claude Power Pack. PRR lives on **main** (16 PRR-owned commits ported with `-x` onto clean main,
2026-10-13; `prr/main` is history only, never merge it). Work tree = the goal-bound root `C:\Users\User\Apps\pp-prr`,
branch `prr/integrate-2026-10-13` (tracks origin; fast-forward main from it after green gates). Never `Set-Location`
into it from a coordinator pane (memory feedback-coordinator-set-location-binds-goal); workers launched IN it bind to
`prr`. Goal `prr`: programme 88,000,000 (OCA `prr-l3-successor-50m-2026-10-13`), lease **L3** `prr:D:r3` cap
46,000,000 + closeout 2,000,000 + recovery 2,000,000 (protected, never productive). A coordinator outside the root is
NOT billed: settle it with `goal-settle --goal prr --session <sid> --measured <session-status tokens>`.
GEX44: `~/missions/prr-int/{prr-int,prr-int-base}`, bench data `~/prr-bench/runs/`.

**Owner direction 2026-10-13 (binding).** Scope NOT narrowed. A: CPP-owned processes/state/inputs. B: what CPP feeds
the host. C: host frontier; claude.exe same-PID reclaim = HOST_LIMITATION / CURRENTLY UNREACHABLE (evidence A1), never
"impossible". Restart = fallback only. Priorities: 1 integration, 2 economic truth/successor/reserve, 3 Win-vs-Linux
attribution, 4 orphan census, 5 floor decomposition, 6 CPP-owned same-PID reclaim, 7 tool/artifact/image/agent
residency, 8 MCP deflation, 9 PGO+forecast, 10 pressure/admission, 11 same-PID marathons (CPP-owned), 12 host
frontier + restart fallback, 13 UKDL/FIOS/Vault/CBR. Never return to the Owner for lease/session/pane mechanics.
Done criteria: the Owner's 2026-10-13 list (causal gap explanation, measured opaque floor, CPP same-PID reclaim
proven, bounded drift, deep-idle deflation, aggregate Goal RAM, peak admission, PGO, orphan governance, retirement as
evidence-backed fallback, host limits + frontier, Vault/FIOS/UKDL/CBR, Production Reality Gate).

**State (coherence anchor: main @ c1513b35).**
SEALED 1: integration (gates: PRR suites green; 11 consumer tests identical on main vs branch on GEX44; reachability
70 offenders both, none PRR).
SEALED 3 (first cut): evidence F + `modules/prr/regions.py`. The 887-vs-107 gap is commit vs anon RSS: Windows median
commit 897 MB = 253 resident private + 608 committed-not-resident (allocator commit-ahead + trimming); image 273 MB
shared; reserve 9.9 GB virtual. Linux anon 64-227 MB. OPEN: matched-workload run; untouched vs paged-out split.
SEALED 4 (first cut): 92 orphan candidates = 322 MB only. 66 were suspended-at-birth `node -e` probes from
gsd-session-state.sh / gsd-phase-boundary.sh, missed by the reaper's ownership test; fixed c1513b35 and deployed live
(self-test 21/21, mutant red, dry run +66). The reaper (SessionEnd) reaps them; no manual kill.
PARTIAL 2: this coordinator's 12,609,706 settled by hand; bound root restored. OPEN: automatic successor via
`goal-succession` needs a tranche structure in the next capital packet (executable after L3 is ~0.35M).

**Active decisions.** Laptop = light control plane while Available < 4 GB. Heavy runs on GEX44, one at a time.
No kill without ownership + liveness proof; route kills through the reaper authority.

**Next 3 actions.**
1. Priority 5/3: matched-workload floor on Windows vs Linux (B stub bench) when the laptop has >= 4 GB, else
   per-region QueryWorkingSetEx sampling of one idle claude.exe over 30 min (read-only).
2. Priority 6/8: census of CPP-owned long-lived processes (MCP servers 19 x ~40 MB, js_other) with drift slope.
3. Upstream GSD hook defect: bash killed mid-spawn leaves suspended children; propose a timeout-safe probe.

**Start.** `python tools/mission_spend.py goal-status --goal prr` from the PP repo, then action 1.
