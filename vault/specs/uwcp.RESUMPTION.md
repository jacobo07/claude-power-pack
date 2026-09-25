# UWCP -- resumption contract (in flight)

**Read this first; it is self-contained.** Spec + approved plan: `vault/specs/uwcp.md`
(APPROVED 2026-09-25 by Owner "y": plan + dedicated `uwcp` unix user on the VPS).

## Identity
Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`,
worktree = repo root. ~490 foreign dirty paths and live panes (product-demo, KSEIP gsd-x,
keos-qwen): re-read HEAD before every commit, commit by pathspec, check `diff -U0` hunk headers.
Thesis: the Workstream (gsd_x goal log) is durable; sessions, models, clients and nodes are not.

## Sealed (pathspec commits)
`5e79e61` approved plan · `e6b6411` characterization 13/13 (six defects pinned) ·
`9c7a3c6` S1-3 portable_repo_id (shallow/multi-root refused; log.repo_id delegates) ·
S1-4 goal-log directory fsync (POSIX; Windows explicit no-op) -- see git log.
Gates: `tools/test_uwcp_characterization.py`, `tools/test_uwcp_foundation.py`; regression
GSDX_GOAL 26/26, CHAOS 15/15, EPOCH 19/19. Mutation drills via scratchpad `mutate.py`
(snippet swap, named gates must go red, SHA-256 restore).

## Active decisions (do not re-litigate)
VPS = remote authority home (user `uwcp`, 0700, ssh forced-command verbs). Broker law global: no
ssh/scp/rsync to GEX44 (5.9.23.174, aliases gex44 / gex44-root) from CPP; dispatcher only.
Lease + slot consume + provider account ledgers on the VPS; KSR slot_ledger becomes a client.
claude -p: one account ledger, 4/day. One bounded queue job = one epoch. FP-028 only for S1-S3.
Placement rule (Owner request): /cpp-gsd-long -> GEX44 when this host can't/shouldn't; lands S6c.

## Next 3 actions
1. S1-5 `evidence.hypothesis` event (established/rejected/superseded + refs) and projection.
2. S1-6 brief: render rejected hypotheses; byte + token bound that REFUSES (invert CHAR-BRIEF-UNBOUNDED).
3. S1-7 operator.* events, then S1-8 fence (invert CHAR-LATE-RECEIPT-INGESTED).

## Start instruction
Run both uwcp test files; if green, continue at the first unsealed slice in plan §17-18.
