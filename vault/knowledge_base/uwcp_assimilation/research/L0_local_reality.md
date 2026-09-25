# L0 -- local reality scan (2026-09-25, main thread)

HEAD c58e00f on feature/knowledge-acquisition. Live UWCP executor pane: brief.py (S1-6 bounded
brief, uncommitted, mtime 13:00), intervention.py untracked (S1-7), both uwcp test files dirty.
-> assimilation plan must NOT touch goal/brief.py, goal/intervention.py, tools/test_uwcp_*.py
until that pane commits. 8 worktrees; ~490 foreign dirty paths.

Landed since the UWCP plan (all today): 5e79e61 plan, e6b6411 characterization, 9c7a3c6
portable_repo_id, 13c9f16 dir fsync, c58e00f evidence.hypothesis.

## Confirmed primitives (keep; external systems confirm them)
- goal/log.py: optimistic CAS on expected_seq (LostRace), exclusive os.link publish, fsync file +
  dir, prev_digest hash chain, gap detection on read. == etcd Txn-on-revision / Temporal event ids.
- epoch.begin: identity (run_token) minted BEFORE the effect; info_key refuses a retry without new
  information (persist-on-goal / pivot-on-method already structural).
- epoch.recover: intent-before-effect adoption by probe.

## Confirmed gaps (file:line)
- G-L1 PROBE BISTATE. epoch.py:115 `probe(...) -> dict | None`; recover() (276-287) maps None -> LOST.
  providers/claude.py:190-196 returns None on OSError/JSONDecodeError. "could not ask" == "absent".
  UWCP §14 says unreachable -> UNKNOWN -> never replace, but the TYPE does not carry it; the future
  providers/queue.py (remote, S5-34) is where "could not ask" is common. Jepsen :info vs :fail.
- G-L2 LOCK TAKEOVER RACE. providers/codex.py:175-197. (a) torn-read window: open('x') creates the
  file before write(); a contender reading in between gets JSONDecodeError -> held={} -> pid 0 ->
  stale -> overwrite -> two holders. (b) two contenders on a genuinely stale lock both write_text
  and both return. (c) no fence: a paused holder past 2*wall keeps spending after takeover.
  Redlock / etcd-mutex stale-owner class, live. Plan S6-38 migrates this ledger to the VPS -- the
  VPS store must be written so this class is unrepresentable, and a regression pins it.
- G-L3 ingest_receipt (256-273) refuses unknown epoch / duplicate / wrong revision but NOT an ended
  epoch and NOT a stale fence -- known, is S1-8 in the live pane's queue.
- G-L4 no typed evidence-class vocabulary in code (grep REMOTE_REALITY|MODEL_CHECKED -> 1 string in
  a test). Evidence tiers are prose only.
- G-L5 model-routing.json names claude-opus-4-7 / sonnet-4-6 (two generations stale).
- G-L6 CONFIRMED. reconcile.decide:141-144 running + observation UNKNOWN -> WAIT, unbounded. No
  age/deadline anywhere in reconcile. Liveness "no epoch indefinitely ambiguous" is violated by
  construction; §14's BLOCKED_ENVIRONMENT-after-bound is not in the core.
  Combined with G-L1 these are the two counterexamples a TLA+ model of the CURRENT code is predicted
  to produce: (safety) probe-unknown -> LOST -> successor while original runs = two executors;
  (liveness) UNKNOWN forever -> WAIT forever. Predict BEFORE running TLC; a model that fails to find
  them is itself suspect (positive control).
- reconcile.py now carries S1-7 code from the live pane (2b blocking_reason) -> do-not-touch list
  also includes goal/reconcile.py until that pane commits.

## Owners found for the assimilation itself
- provenance/license: vendor/NOTICE.md format + lib/license_gate.js (fingerprint, gate verdict).
- "principles only, never code" disposition precedent: vault/knowledge_base/product_demo/recordly-disposition.md.
- upstream snapshot + divergence map precedent: vendor/apollo/{MANIFEST.json,SOURCE.txt,upstream/divergence-map.md}.
- knowledge_acquisition = question/lens routing, NOT the right owner. evaluate-repository = security triage only.
- routing vocabulary owner: modules/keos_qwen/outcome.py (OK/UNAVAILABLE/TRUNCATED/HARNESS_FAILED, precedence).
