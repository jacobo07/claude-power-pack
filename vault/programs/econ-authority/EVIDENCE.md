# Mission-authority programme — evidence (2026-10-15, session 51030f62)

Plan: `vault/plans/mission-authority-econ-programme-2026-10-15.md` (Owner "approve", 30M slice, goal
`econ-authority-a`, this pane bound to it from 13:27:22Z).

## Landed
- `8279e4c7` (PP main, from branch `econ/mission-authority` 02976b60): `mission_spend.judge` trips at
  `authority_tokens - closeout_reserve` whatever the estimate; supervise judges authority-only missions;
  `set_owner_hold(kind="cost")` writes an economic-incident receipt (`tools/econ_incident.py`) + ledger row;
  `gsd_mission.py status` prints open incidents.
- Gates: `tools/test_mission_authority.py` V-MA 23/23 (worktree and live tree); mutation (authority branch
  disabled) turns 9 gates red for the right reason. Regression: test_gsd_mission 230/230, accounting 10/10,
  phase lease 15/15, mission_gate 31/31, AMR 63/63, AMCR 37/38 (V-AMCR-ONE-RESOLVER-INVENTORY fails
  identically on unmodified main: pre-existing).
- Live: first sweep pass on the new code 13:51:08Z, mission stage rc 0 (74.6 s). The prior pass (rc 3) ran
  old code and failed on m-33f7242bd363 `route-P6.json` FileNotFoundError (gsdx-pcc, not this programme).
- Retroactive receipt `~/.claude/state/economic-incidents/m-ce2bacd4cbb0-1792072192.json` (overshoot
  38,778,584); `status` shows it.

## Not built here, on purpose (owned by CCR v5, Owner-approved, landed 4752ce43 or planned kernel-u1/u2)
In-turn cost-hold denial + subagent caps (mission_gate.js, LIVE), phase lease + phase breaker (LIVE),
stopped-worker tree settlement (LIVE), next-call exposure in the gate, sweep breaker priority, floor
decomposition, context admission, call ledger / work-class profiles, physical forecast gate (kernel-u1/u2,
not landed; kernel-u1 m-589fabb143de halted 15:26 with 307K spent and no commit). Building a second
version would have been the duplicate the plan forbids.

## Measured (autopsy of transcripts incl. subagents)
| | m-ce2bacd4cbb0 dataset | m-28ab89fff085 SurvivalSMP |
|---|---|---|
| calls | 551 | 890 |
| processed | 84.1M | 134.8M (at 15:00) |
| floor main / subagent | 115,870 / ~75,000 | 116,891 / ~77,000 |
| mean ctx, cache-read | ~150K, 0.95 | ~150K, 0.95 |
| biggest | gsd-planner OPUS 165 calls 23.3M; executors 266 calls 42.2M | executor plans 9.6-47M (P50 ~25M) |
Plan-file `estimate.tokens` (e.g. 02-05: 75,000) is ~300x below measured plan cost: not a forecast.
Dataset hold at 82,289,960; final 83,778,584: +1,488,624 after the hold (owner hold kind=null is not a cost hold,
so mission_gate did not deny; the session-budget stop file did, main-transcript-only).

## Bugs / failed assumptions (KV)
1. MISSION_AUTHORITY_NOT_RUNTIME_ENFORCED — authority_tokens read only at launch admission and AMR lease.
   Fixed 8279e4c7.
2. BREAKER_RATIO_ABOVE_AUTHORITY — trip at 2 x estimate; estimate set = authority -> trip at 2 x authority.
   Fixed (authority binds first).
3. OWNER_USED_AS_OVERSPEND_MONITOR — overrun found by a manual status check. Fixed: receipt + status line.
   Residual: no push notification (debt).
4. MANUAL_HOLD_NOT_IN_TURN — an owner hold without kind=cost is not denied in-turn by mission_gate.js.
   Open (CCR v5 owns the gate).
5. PROGRESS_CREDITED_FROM_FOREIGN_COMMITS — a mission bound to a shared root tree (SurvivalSMP gen 0) moves
   its fingerprint on other panes' commits. Open (B3, not in this slice).
6. FORECAST_FROM_ROADMAP_LENGTH — dataset forecast 25-45M for 8 phases vs 84M for phase 1 (calls 15x).
7. VALUE_CRITICAL_DEPENDENCY_NOT_GATED — 8 phases planned over 2 rights-UNKNOWN samples in 1 lineage group.
   Dataset roadmap now parks behind `rights` + `population` gates (Core Files 16cd017c). Generic gate: B4 debt.
8. CLIPBOARD_FALLBACK_IN_COMMIT_MESSAGE (this session) — a PowerShell `Set-Content -Encoding utf8NoBOM` failed on
   PS 5.1 and a `Get-Clipboard` fallback wrote the Owner's clipboard into commit 1609e2ad's message; amended
   to 02976b60 before any push. Never read the clipboard as a fallback for content; write files with
   `[IO.File]::WriteAllText(path, text, UTF8Encoding($false))`.

## UKDL candidates (not promoted: no live trip of the new breaker observed yet)
- HR: an economic limit not checked by the runtime is not an authority limit.
- HR: a breaker threshold may never exceed the Owner's authority, whatever the estimate.
- PR: arm -> record authority -> breaker binds at authority minus closeout -> incident receipt on trip.
- Trap: storing a budget in STATE/record and assuming it is enforced; reading plan `estimate.tokens` as a forecast.
Promote after the first real authority trip produces a receipt with no Owner involvement.
