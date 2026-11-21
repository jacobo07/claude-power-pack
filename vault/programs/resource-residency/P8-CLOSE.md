# Resource Residency: close (D-2026-11-21 scope: Phases 1, 2, 5-shadow, 8)

Date 2026-11-21. Branch `worktree-rr-phase2`, unpushed. Commits 57e4a1a7, 87a5572c, 53a9d2f5, dbb49a53 (+ this file).

## Master gate, item by item
| Phase | Verdict | Evidence |
|---|---|---|
| P1 census + open P1 gate | DONE | `P0-P1-GATE-EVIDENCE.md`, 22 V-CENSUS |
| P2 lazy MCP shim | DONE, one server in one project | 14 V-LAZY gates + live Gate A/B on GEO-audit/google-ads (STATE.md) |
| P3 server classification/pooling | NO APLICA (deferred by Owner) | not started |
| P4 | NO APLICA (deferred) | not started |
| P5 session liveness | SHADOW ONLY, done to scope | `tools/session_liveness.py`, 15 V-LIVE gates incl. mutation drill; no hibernation, no stop |
| P6 commit governor | NO APLICA (deferred) | not started |
| P7 | NO APLICA (deferred) | not started |

## 2-snapshot census delta (baseline 2026-11-20 23:20 -> close 2026-11-21)
`census-baseline-20261120.json` vs `census-close-20261121.json`: google-ads procs -42 (private -1.10 GB), rea procs -10
(private -1.33 GB), claude sessions 3 in the snapshot, process_count -45. Host: commit_total +2.73 GB, pagefile_total -4.01 GB,
ram_free -1.19 GB.

**What this does NOT show.** It is not evidence the shim freed memory. The shim is live for one server in one project, and the
drop in google-ads/rea processes is explained by sessions ending between snapshots (RR-03). Host commit went UP. No
"freed N GB" claim is made (post-effect-resource-truth). The only measured shim number: idle shim private 10.5 MB; the real
google-ads server's private size was not captured.

## P5 live shadow result (28 claude.exe, 5 s window)
ACTIVE 21, IDLE 0, UNKNOWN 7 (4 protected by a bg-job lease, 3 with no session id on the command line, so no transcript).
Zero IDLE on a memory-starved host most likely means the 0.5 s CPU / 5 s threshold is too sensitive for this host, or
interactive sessions' process-to-session mapping is missing; the threshold was not tuned to produce a number. Reclaimable-by-
hibernation estimate: none supportable yet.

## Owner steps (BLOCKED-ON-OWNER, none automated)
1. Pagefile: system-managed pagefile total shrank 4.01 GB while commit_total rose 2.73 GB between snapshots. Recommend the
   Owner review a fixed pagefile size (Settings > System > About > Advanced > Performance). Not changed by this work.
2. Hibernate -> `--resume` canary (P5): not run. Needs a chosen IDLE session; none classified IDLE yet.
3. Extend lazy to other servers/projects: `python tools/mcp_scope.py lazy <server> --project <path>`; rollback `unlazy`.
4. RR-03 leftover rea/google-ads processes leave with their old sessions.
5. Merge `worktree-rr-phase2` into the feature branch (lineage owner); push is the Owner's.

## Debt
- No V-LAZY gate yet pins the `server/discover` -32601 and cached prompts/resources list paths (found only by the live gate).
- P5: map interactive claude.exe pid -> session id; calibrate the CPU threshold from a longer sample.
