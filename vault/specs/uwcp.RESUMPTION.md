# UWCP -- resumption contract (in flight)

**Read this first; it is self-contained.** Spec + approved plan: `vault/specs/uwcp.md`
(APPROVED 2026-09-25 by Owner "y": plan + dedicated `uwcp` unix user on the VPS).

## Identity
Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`,
worktree = repo root. ~490 foreign dirty paths and live panes (product-demo, KSEIP gsd-x,
keos-qwen): re-read HEAD before every commit, commit by pathspec, check `diff -U0` hunk headers.
Thesis: the Workstream (gsd_x goal log) is durable; sessions, models, clients and nodes are not.

## Sealed (pathspec commits, all EXECUTION mode)
`5e79e61` plan · `e6b6411` characterization · `9c7a3c6` S1-3 portable_repo_id ·
`13c9f16` S1-4 dir fsync · `c58e00f` S1-5 evidence.hypothesis · `bd0d831` S1-6 bounded brief +
negative knowledge · `53f75ec` S1-7 operator intervention (intervention.py, reconcile step 2b) ·
`cf4d71b` S1-8 epoch fence · `99f587c` S1-9 eol-invariant pins (blob: scheme, versioned digests) ·
`4366543` mutation-harness fix (timeout = INVALID, tree kill, restore retry) · `0ff7cf7` S1-10
runtime_identity (non-git runtime refuses autonomy; RUNTIME_ID `uwcp-runtime:<sha>`) · `bc2ea73`
S1-11 LongRunProvider arms v3 missions (mission id = m-<run_token[:12]>) · S1-12 real Workstream
`ksr-p2w25-fp028` (repo 8f11bb03899e) via `tools/uwcp_golden08_fp028.py` 7/7 LOCAL_REALITY.
S1 SEALED. S2 Workspace Capsule SEALED on the A6 object model (two seeded trees, restore by
objects, {sha256,size} parts, conversion_env, retention): `tools/test_uwcp_workspace.py` 37/37
LOCAL_REALITY (see git log for the hash; drills in the follow-up commit).
**Read `vault/specs/uwcp.AMENDMENTS.md` at every slice boundary** (Owner-approved, binding; Lane R
= the assimilation pane, writes only new files outside modules/gsd_x/goal). Queued delta slices on
sealed work: A1 -> S1-8b (receipt echoes goal/epoch/run_token/fence/revision, refusal codes,
begin() refused while any epoch open); A2 -> S1-8c (UNKNOWN never licenses: tri-state probe,
BLOCKED_ENVIRONMENT); X0 -> S1-8d (codex account lock stale-takeover by rename).
OWED: full 54-mutant run of tools/test_gsd_x_goal_mutation.py on an unstarved node (this host
timed out; harness now reports INVALID instead of crashing). Card-from-brief merge in
gsd_mission.render_card deferred (another pane committing there hourly).
Gates: `tools/test_uwcp_characterization.py` 24/24, `tools/test_uwcp_foundation.py` 22/22;
goal regressions green (GOAL 26, CHAOS 15, EPOCH 19, RECONCILE 22, SWEEP 14, JUDGE 11, CONV 29,
GATE 18, CLAUDE_PROVIDERS 20, CLI 25). Mutation drills: scratchpad `mutate.py` (snippet swap,
named gates must go red, SHA-256 restore; refuses ambiguous snippets as HARNESS-FAILED).

## Traps learned this run (for the vault at S10)
- Editing a module while a background suite exercises it produced a false 22/25 (NameError
  window). Never edit gsd_x/goal while tools/test_gsd_x_goal_mutation.py runs -- it mutates
  those files on disk and refuses a dirty tree (exit 2).
- mutate.py restores in `finally`, which does NOT run when the harness is killed from outside
  (Claude Code reaped the drill batch at low memory, 2026-09-25): mutant M8 stayed on disk in
  workspace.py. After ANY killed drill, diff the target against HEAD before anything else;
  restore with `git checkout -- <file>` and compare hash-object to HEAD's blob.
- anti-thrash: a PARTIAL Read (offset/limit) did not reset the counter; a full Read did.
- A one-line mutation snippet can occur twice (end() and ingest_receipt share a guard line).
- V-CHAOS-7-REPLAY passed only via the duplicate check; fixed for real by the S1-8 fence.
- The whole gsd_x goal engine is ORPHAN for /liveness (only tools/gsd_x_goal.py reaches it);
  evidence + intervention declared PLANNED until S6 wires it.

## Active decisions (do not re-litigate)
VPS = remote authority home (user `uwcp`, 0700, ssh forced-command verbs). Broker law global: no
ssh/scp/rsync to GEX44 (5.9.23.174, aliases gex44 / gex44-root) from CPP; dispatcher only.
Lease + slot consume + provider account ledgers on the VPS; KSR slot_ledger becomes a client.
claude -p: one account ledger, 4/day. One bounded queue job = one epoch. FP-028 only for S1-S3.
Placement rule (Owner request): /cpp-gsd-long -> GEX44 when this host can't/shouldn't; lands S6c.

## Next 3 actions
1. S1-8b (A1) SEALED: Receipt echoes goal_id/run_token/fence via epoch.echo(spec); ingest
   compares all, ReceiptRefused codes; begin() refused while any epoch open. NEXT: S1-8c (A2) --
   claude.py:144 and codex.py:262 return OBS_LOST for "no child handle in this process": make it
   UNKNOWN; probe tri-state FOUND|ABSENT|UNKNOWN; decide() checks operator cancel/pause BEFORE any
   UNKNOWN wait; UNKNOWN past deadline -> BLOCKED_ENVIRONMENT. Then S1-8d (X0 codex lock).
   Workspace drills: M1/M3/M4 caught; M2 (fsck flags removed) SURVIVED -- a byte flip is refused
   by index-pack inflate regardless, so fsck's value for malformed-but-inflatable objects is
   undrilled (gate renamed to FETCH-REFUSES); M5-M8 re-run alone (first run starved by my own
   concurrent suites -> INVALID, not verdicts).
2. S3: goal/baseline.py fingerprint (runtime-manifest hash, hook-set hash, claude CLI version,
   model/GGUF/llama build, HR digest, permission mode) + the capsule's conversion_env as a
   correctness field (A6.5) + epoch pin + drift policy.
3. S4: node adapter over KSR capabilities.json, placement.py, VPS lease store wiring Lane R's
   modules/lease/ (A5, PLAN checkpoint; read the VPS dispatcher first; DEPLOY hard rules before
   any VPS write).
Host note: this laptop runs at ~0.9 GB free of 32 GB; the workspace suite takes ~10 min here.

## Start instruction
Run both uwcp test files; if green, continue at the first unsealed slice in plan §17-18.
