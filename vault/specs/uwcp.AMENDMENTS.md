---
status: APPROVED 2026-09-25 by Owner ("y", all six recommendations) -- binding on the UWCP execution pane
source: vault/specs/uwcp-assimilation.md (r2, P4 audit applied)
reader: the pane executing vault/specs/uwcp.md slices (Lane L)
---

# UWCP amendments -- read at every slice boundary

Each amendment names its HOST slice. When you reach that slice, its acceptance criteria include the
amendment and its falsification test. An amendment whose host slice is already sealed becomes a
delta slice with the id shown. Lane R (the assimilation pane) writes only new files outside
modules/gsd_x/goal and provides libraries you import; it never edits your files.

## URGENT for S2 (workspace.py is in progress)
A6 -- the capsule object model. The approved §10 premise "`git bundle verify` checks integrity" is
FALSE, measured 2026-09-25: a bundle with one byte flipped mid-pack -> `git bundle verify` prints
"is okay", exit 0; `git -c transfer.fsckObjects=true fetch <bundle>` -> "inflate: data stream error",
exit 1. Required:
1. every part and the manifest named {sha256, size}; size checked first; digest_function and
   git_object_format recorded; capsule_id = sha256 of canonical manifest bytes (UTF-8, sorted keys,
   no floats, LF, entry arrays sorted by UTF-8 path bytes).
2. identity = index_tree + worktree_tree, git tree ids of a synthetic index SEEDED from the base tree
   (`GIT_INDEX_FILE=tmp git read-tree <base>` then add dirty in-scope paths) -- never an empty index
   (drops 100755, 120000, gitlinks, skip-worktree on NTFS). Diffs are transport only.
3. restore by objects + node-local `checkout-index`, never `git apply` across hosts (autocrlf).
4. content verify = part digests + fetch with transfer.fsckObjects; bundle verify = structural only.
5. conversion_env {autocrlf, eol, safecrlf, filters in scope + installed, lfs + git version} is a
   correctness baseline field (feeds S3-19). Relation to S1-9 blob_oid: equal exactly when
   conversion_env is equal; otherwise verify = COMPATIBLE_WITH_DECLARED_DRIFT. git_state stays owner.
6. node "have" asked at dispatch; missing prerequisite -> full bundle, never partial apply.
7. retention keeps parts referenced by last N receipts UNION queued/running manifests; deletes only
   after age > max epoch budget + transfer margin AND unreferenced on two passes; RETIRED is an
   outcome distinct from NON_EQUIVALENT.
8. refuse: unmerged index, case-colliding paths onto a case-insensitive host, required filter/LFS absent.
Falsification tests: byte-flip part -> NON_EQUIVALENT before git is asked; symlink/exec-bit seeded
from base survive a Windows capture; retention N=0 during capture -> parts survive.
Library: Lane R ships modules/cas/ (digest, canonical manifest, verify tiers, retention planner);
import it rather than re-deriving.

## Delta slices on sealed work
A1 -> S1-8b: receipt echoes {goal_id, epoch_id, run_token, fence, revision}; ingest compares all;
   refusal codes stale_fence | epoch_ended | epoch_mismatch | revision_mismatch | duplicate; receipt
   fence greater than the projection -> reload once then judge; begin() refused while ANY epoch open.
A2 -> S1-8c "UNKNOWN never licenses anything": observe returns UNKNOWN (not LOST) for "no child
   handle in this process" (claude.py, codex.py) and unreadable state; probe returns a closed
   tri-state FOUND|ABSENT|UNKNOWN, any other return = UNKNOWN, pid=None after Popen = UNKNOWN;
   enumerate implementers structurally (5 + test fakes); decide() evaluates operator cancel/pause
   BEFORE any UNKNOWN wait; WAIT on UNKNOWN past its deadline -> BLOCKED_ENVIRONMENT whose only
   exits are a positive observation or operator cancel that bumps the fence; no successor after
   UNKNOWN until A3 node fencing is live. Red tests: Lane R's TLA+ counterexamples replayed in Python.
X0 -> S1-8d codex account lock: take a stale lock by os.rename(lock -> lock.stale.<run_token>) (one
   winner), verify tombstone bytes == bytes judged stale, create with O_EXCL; unparseable lock older
   than the bound goes through the same path; barrier race test for both races.

## Future host slices
A3 -> S5-33/S5-30 (PLAN checkpoint): fence held WITH the effect -- node flock on the resource
   lockfile across each side effect; dispatcher bumps the fence under the same flock; stopped holder
   killed, never bypassed; stale fence -> stop all effects, exit non-retryable lease_fenced; git to
   refs/uwcp/<goal>/<fence>, promoted by update-ref with expected old value after the receipt append,
   idempotent. Pause drill = REMOTE_REALITY via a dispatcher signal verb with an allow-list.
A4 -> S5-30/S6-40: four clocks (queue-wait, epoch budget, stall, max_hours) as absolute deadlines
   owned and judged by the writing host (node: monotonic durations), never restarted by owner
   restart; QUEUE_WAIT_EXCEEDED releases the lease and bumps the fence atomically; graded
   suggest<warn<error for brief bytes, capsule bytes, goal-log events (suggest_handoff); cancel
   exempt from all size bounds; operator event ids deduped goal-scoped.
A5 -> S4-25 (PLAN checkpoint): Lane R ships modules/lease/ (the etcd-derived primitive: min TTL >=
   3 x renew + RTT; expiry bumps fence in the critical section; all-or-nothing multi-class; refuse
   nfs/fuse/overlay; ack after fsync; reserve/takeover atomic); S4-25 deploys and wires it.
A7 -> S6-37/38/39: Lane R ships modules/provider_routing/ (decision record, bounded non-revisiting
   chain, error-class retry default 0, positive semantic outcome list, same-window TRUNCATED skip,
   falsy-zero refusal, reserve/commit/release ledger with `leaked`); route.py consumes it. Measure the
   real claude/codex exit codes on quota text before trusting the list.
A8 -> §16 wherever status/control lands: Lane R ships modules/trace_context/ (W3C traceparent);
   trace-id minted at declare into the goal log; TRACEPARENT in child env and in uwcp.control/1
   verbs + job records; JSONL spans beside the log; telemetry removed -> byte-identical decisions.
X3 -> history adapter: goal/history.py maps the goal log to ops for Lane R's modules/history_check/
   (Jepsen-derived checkers); X4 -> extend tools/test_gsd_x_goal_chaos.py with §14 rows as faults.
