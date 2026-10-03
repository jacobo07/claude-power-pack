---
covers: [agent-telemetry, co12-signal-writer, resolver-negative-cache]
date: 2026-10-03
status: EXECUTED 2026-10-03 (commits 163f0b2f..361aea29 + this docs commit); CBR EXPERIMENTAL
parent: vault/specs/agent-capability-virtualization.md (D3, C5)
head_at_scan: 097613b1
---

# ACV C5 -- resolution telemetry into CO-12 (ULTRA reconciliation)

## Reality (measured 2026-10-03, read-only)

- HEAD 097613b1 = origin/feature/knowledge-acquisition (0/0). C5 surfaces clean.
  `modules/capability_runtime/agent_telemetry.py` does not exist; no C5 work elsewhere.
- C4 plan status line already reads EXECUTED (committed in 097613b1): no correction needed.
- Foreign UKDL append (+1,830 lines) still in the working tree, untouched.
- CO-12 (`modules/cognitive_os/co_12_telemetry.py`):
  - `record_signal(kind, payload, *, state_dir=None, now=None) -> bool`; row = {"kind","ts"}
    then `rec.update(payload)` -- a payload key `kind` or `ts` silently overwrites them.
  - fail-open ABSOLUTE: any error -> False, never raises. Telemetry is best-effort by contract.
  - no schema/version convention: producers put their own fields in the payload.
  - `state_dir` already targets an isolated directory with the REAL writer; test_co12_telemetry
    uses exactly that (tempdir). Reader: `load_signals` (skips unparseable lines silently).
  - writer = `open("a")` + one `write` -- the primitive T-TORN-APPEND-CONCURRENT-JSONL-001
    (amended 2026-10-03) measured OVERWRITING rows under concurrent writers on Windows; only an
    exclusive lock lost 0. Live file ~/.claude/state/co12_readiness/signals.jsonl: 5,368,398 B,
    22,002 rows, 7 UNPARSEABLE, written concurrently by fios_token_irr (7,875), fd_flywheel_turn
    (7,824), fd_delta_deposited (4,607), akos_injection (1,558), cdio, sqi. Each fragment marks
    >= 1 lost row; the count is a lower bound.
- Producers already on CO-12: cdio telemetry, FD-00/04/07, FIOS token_irr/corpus_roi, run_sqi,
  jit_skill_loader. Lock idiom already proven: `tools/rollover.py` ledger() (38fc418c, sidecar
  lock, bounded wait, drop-and-report) -- in tools/, so not importable from modules/.
- Resolver output today: status, miss, miss_ids, vetoed_by, candidates, near_misses, excluded,
  broken, catalog_size, fingerprint (= CATALOG identity: name|size|mtime of every spec.json),
  policy (= sha over capability_runtime/*.py), cache (HIT|MISS), ms. No request identity is
  exposed; the token normalisation lives only inside resolve().
- No test drives the resolver CLI; the CLI is the only production entry point (D7).

## Correction to the handoff's premise

The handoff's "fingerprint" is the resolver's CATALOG fingerprint, not a request fingerprint.
Both are needed: catalog_fp says which estate was searched; a request identity is what lets a
later reader count one fresh NO_MATCH plus N cache reuses as ONE observation. Request identity
must come from the resolver (its own `_tokens` normalisation), never re-derived in telemetry.

## Decisions

1. Owner: CONNECT to CO-12 `record_signal` (no new ledger). NEW thin adapter
   `modules/capability_runtime/agent_telemetry.py` (D3, approved) mapping a resolver result to one
   payload; mirrors CO-12's own `route_and_record` pattern (I/O kept out of the decider).
2. Writer integrity is a PREREQUISITE (commit 1, canonical owner co_12_telemetry): record_signal
   appends under a sidecar exclusive lock (rollover idiom), bounded wait, returns False on
   timeout/OSError -- same bool contract, still never raises. Red first: a multi-process race test
   on a temp state_dir must lose rows with the old writer and none with the new.
3. Event: kind `agent_resolution`, payload `schema: "agent-telemetry/1"`. One signal per resolve
   call, emitted after resolve() returns (final outcome only). Fields and producers:

   | field | producer | meaning |
   |---|---|---|
   | miss | resolver | exact C4 value; null on RESOLVED |
   | candidate_ids | resolver `candidates[].id` | certified specialists returned (hit only) |
   | miss_ids, miss_ids_total | resolver `miss_ids` | causal ids (below); list capped at 20, total kept |
   | vetoed_by | resolver | NO_MATCH only: specs whose anti-trigger vetoed after a trigger hit |
   | cache | resolver | HIT = reuse of an earlier computation, MISS = computed now |
   | policy | resolver `policy_hash()` | code version that produced the answer |
   | catalog_fp | resolver `fingerprint` | catalog state searched (null if unstat-able) |
   | query_fp | resolver (NEW additive output field) | sha over the normalised token sequence |
   | grant | caller's max_class | needed to read CLASS_EXCLUDED |
   | dispatch_id, goal_id | caller, only if supplied | future join keys; never invented |

   Never stored: raw task, spec bodies, near_misses, excluded rows, broken details, scores.
   `ts` comes from CO-12. The adapter refuses payload keys `kind`/`ts` (they would overwrite).
4. miss_ids (C4 already makes them causal; telemetry copies, never recomputes):
   CATALOG_UNREADABLE = directory names of specs that failed to load (the contract id is unknown
   because the spec did not load; for NO_CATALOG the list is EMPTY -- resolver fix: today it
   carries the catalog PATH, which is not a capability identity) · CLASS_EXCLUDED = contract ids of
   above-grant specs that would_activate · BELOW_GATE = contract ids blocked in grant ·
   NO_MATCH = always empty (valid). Ranker residue (near_misses, lexical exclusions) never enters.
5. query_fp: sha256 over the resolver's normalised tokens (canonical_text, lowercase, stopwords
   out). Equal fingerprints = same token sequence ("Review C++ code" == "review cpp code").
   Normalisation lives in agent_resolver.py, which policy_hash covers, so (query_fp, policy) is
   unambiguous across normalisation changes -- no separate version. Not a goal identity.
6. Sink: `resolve_and_record(task, ..., sink=None, dispatch_id=None, goal_id=None)` returns
   (result, recorded). sink None -> CO-12 record_signal looked up at CALL time (so a test spy can
   intercept). The result is never modified; a False write is surfaced, never turned into a miss.
   The CLI calls resolve_and_record and prints one stderr line when recorded is False.
   EMPTY_TASK / UNKNOWN_CLASS raise before any resolution: no agent_resolution signal.
7. Reader: read-only `agent_metrics(state_dir)` in the adapter + one lazy-import line in CO-12
   readiness_report (cdio pattern, D3). It reports fresh vs cached separately per miss, so cached
   reuse is never counted as new evidence.
8. S5b alignment: C5 completes the agent_resolution kind of D3. agent_run (one row per dispatch,
   tokens, repairs) and agent_outcome stay in C6 with run accounting. S5c/S5e untouched.

## Test matrix (tools/test_agent_telemetry.py, AC-3)

contract (schema, field set, refused kind/ts) · each miss type through the REAL resolver into a
capturing sink (temp catalogs from C4) · RESOLVED hit carries candidate_ids and null miss ·
miss_ids causal: residue case (haiku near-miss, 7 lexical exclusions) emits empty ids ·
NO_CATALOG emits empty miss_ids, not a path · cache: first call MISS, second HIT, same query_fp
and miss · query_fp equality/inequality · failing sink -> result identical, recorded False ·
exactly one signal per call · PRG: real record_signal with state_dir=tmp, read back via
load_signals · live isolation: spy on co_12.record_signal proves no default-sink call during the
suite, with a positive control that the spy does catch one; plus live `agent_resolution` row count
unchanged before/after (other producers write that file concurrently, so its size is no evidence).
co12: V-CO12 race test (multi-process, temp dir) red before commit 1, green after.

## Mutation drills (smallest set)

miss omitted from payload · cache always reported MISS · policy omitted · miss_ids filled from
near_misses · NO_CATALOG path back into miss_ids · default sink used despite injected sink ·
two signals per call · writer lock removed (race gate).

## Audit (phase 4, oneshot-architect-auditor, READY-WITH-FIXES, 5 gaps) -> all accepted

Supersedes the text above wherever they disagree. Gap 1 re-checked by the parent against
agent_resolver.policy_hash (glob "*.py" over the package dir).

| # | sev | gap | fix injected |
|---|---|---|---|
| 1 | MED | policy_hash hashes every *.py in capability_runtime, so an adapter-only edit would read as a resolver version change and flush every cache entry | policy_hash excludes agent_telemetry.py by name; V-gate: adapter-only edit leaves policy unchanged, resolver edit changes it |
| 2 | MED | the no-specs early return (NO_CATALOG / all broken / empty catalog) builds its own dict; query_fp only on `out` would be null there | compute query_fp once after `_tokens`, put it on both returns; assert equal across NO_CATALOG, empty catalog, MISS and HIT for one task |
| 3 | MED | "live agent_resolution count unchanged" goes falsely red once C5 is live (another pane may resolve during the suite); CLI test path unspecified | every test task carries a unique nonce token; gate = no live agent_resolution row has any of the suite's query_fp values. CLI driven in-process with `--no-cache` under the record_signal spy: exactly one agent_resolution call, stderr line when the spy returns False |
| 4 | MED | dispatch_id/goal_id cannot be set from the only production entry point, so live rows until C6 have no join key and cannot be backfilled | adapter mints `resolution_id` (uuid4 -- an identity, not a fact) per signal and returns it; CLI prints it (and --json carries it). C6's agent_run joins on resolution_id. goal_id stays an optional parameter, never invented |
| 5 | LOW-MED | MISS rows over-count fresh observations (cache bypassed on null fingerprint, partial catalog, eviction, concurrent cold writers, --no-cache) | agent_metrics counts distinct fresh observations by (query_fp, grant, catalog_fp, policy); raw MISS/HIT kept separately; test: two use_cache=False calls = one observation |

Also from the audit (clean items applied): reuse tools/test_rollover_ledger_race.py's template for
the race (start event, rows identified, variable padding); no stderr print inside record_signal
(hooks may parse it); the payload mapping sits inside the adapter's fail-open boundary too
(test: mapping raises -> result identical, recorded False). Every signals.jsonl writer goes through
record_signal (9 call sites), so the lock covers all producers.

## Commits

1. fix(co12): record_signal appends under a lock (+ race test, red first).
2. feat(agent-resolver): query_fp output; NO_CATALOG not in miss_ids.
3. feat(agent-telemetry): adapter + resolve_and_record + agent_metrics + CLI wiring + CO-12 lazy
   line + tests (one atomic behaviour).
4. test: C5 mutation drills.
5. docs: spec D3/status, RESUMPTION, this plan; UKDL only if a new lesson is earned.

GEX44: not needed (local adapter). CBR: stays EXPERIMENTAL; no promotion.

## Revision R2 -- ULTRA reconciliation of commits 3-5 (2026-10-03, Owner answers 1A 2A 3 4A 5A 6A)

State: commit 1 = 163f0b2f (locked record_signal, 214/900 -> 0), commit 2 = 965fb859 (query_fp on
every return, NO_CATALOG out of miss_ids, NOT_POLICY + policy_hash(root)), 32/32. HEAD 713b02a7,
8 ahead / 0 behind origin. Supersedes "Commits" above where they disagree.

Premises found false at scan:
- P1 the CLI lives in agent_resolver.py, which policy_hash covers: wiring it would flush every cache
  entry with no answer changed (the exact defect commit 2 closed for the adapter).
- P2 load_signals returns [] on OSError: a reader on it reports "0 observations" for UNREADABLE.
- P3 no host-load standard exists for wall-clock gates; V-RES-LATENCY is one warm sample vs 2000 ms
  (first run 2,884 ms at 100% CPU / ~30 claude procs, rerun 932 ms, no old/new A/B).
- P4 liveness: agent_resolver is already ORPHAN (pre-existing gate debt); new modules reached only
  through it would land ORPHAN too.

| # | commit | files | action | verification |
|---|---|---|---|---|
| 3a | refactor(agent-resolver): CLI out of policy | capability_runtime/agent_resolver_cli.py (new, main moved verbatim); agent_resolver.py (main -> lazy delegating stub; NOT_POLICY += agent_resolver_cli.py); test_agent_resolver.py | pure move | V-RES-CLI-DELEGATES (in-process main == old exit codes/output shape on the real catalog, and `python -m ...agent_resolver resolve` subprocess still works); V-RES-POLICY-NOT-POLICY extended: CLI-copy edit leaves policy unchanged; suite green |
| L | test(agent-resolver): latency median of 3 | test_agent_resolver.py | gate = median of 3 warm uncached runs <= 2000 ms (bar unchanged); CPU time recorded; wall/cpu > 2 printed as CONTENDED next to the verdict, never turning FAIL into PASS | suite green; evidence line shows samples + cpu |
| 3 | feat(agent-telemetry) | co_12_telemetry.py (load_signals strict=False param: strict raises OSError; readiness_report lazy `agent_resolution` line); capability_runtime/agent_telemetry.py (new); agent_resolver_cli.py (resolve_and_record, prints resolution_id, stderr line when not recorded, --json adds resolution_id/recorded to a COPY); test_agent_telemetry.py (new); liveness registry (declare agent_resolver/_cli/_telemetry with owner + reopen) | one behaviour | test matrix above + strict reader (absent file = measured True, 0 rows; unreadable = measured False, no numbers); CLI in-process under record_signal spy forwarding to the REAL writer on a temp state_dir; live isolation by nonce query_fp; test_co12_telemetry + race + resolver suites green |
| 4 | test: C5 mutation drills | tools/mutation_drill.py specs | 8 drills from the list above + "CLI back in policy" + "metrics count HIT as fresh" | each killed by its named gate; clean control green; live source hash unchanged |
| 5 | docs | spec D3/status, RESUMPTION, this plan (committed), KB note; UKDL only if earned | -- | router freshness; fetch, linear-history check, push, no force |

Field owners (adapter copies, never recomputes): miss / miss_ids / vetoed_by / cache / policy /
catalog_fp (=fingerprint) / query_fp = resolver result; grant = caller max_class; resolution_id =
adapter uuid4 (identity, not fact); ts = CO-12; schema = adapter constant "agent-telemetry/1".
agent_metrics (read-only, derived from signals of kind agent_resolution): rows, fresh (cache MISS),
cached (HIT), by_miss {miss: {fresh, cached}}, distinct_fresh_observations by (query_fp, grant,
catalog_fp, policy), distinct_query_fp, schemas_seen, measured. Rejected names: demand, needed,
gap value. Unknown schema rows counted under schemas_seen, not in miss tallies.

### R2 audit (oneshot-architect-auditor, 5 gaps, 0 blocking) -> all accepted

| # | sev | gap | fix |
|---|---|---|---|
| 1 | MED | after commit 3 the resolver suite's CLI tests (in-process + `python -m` subprocess) write LIVE agent_resolution rows (and the live cache), outside the telemetry suite's nonce gate; every drill rerun repeats it | all CLI tests `--no-cache`; subprocess env HOME/USERPROFILE=tmp (Path.home drives both CACHE and CO-12 state; SPECS_DIR is repo-relative); from commit 3 assert exactly one agent_resolution row in tmp signals.jsonl |
| 2 | MED | a cdio-style fallback in readiness_report would report 0 resolutions on error (P2 again) | except -> {"measured": False, "status": "error", "reason"} with no counts; test monkeypatches agent_metrics to raise |
| 3 | MED-LOW | LIBRARY means "never an entrypoint"; the CLI is one and no command/agent names it | agent_resolver_cli = PLANNED + OWNER_QUEUE row (reopen: C6 names it in a command/agent body); agent_resolver + agent_telemetry = LIBRARY; drop agent_resolver from known_orphans; `--baseline` same commit |
| 4 | LOW | a nonce _tokens drops would collide with real requests | nonce letters-only suffix, asserted present in `_tokens(task)` |
| 5 | LOW | strict still drops unparseable lines silently | `stats=` dict out-param receives `unparseable`; agent_metrics reports it; return type unchanged |

Clean: 3a stub has no import cycle (lazy import; `python -m` loads a second resolver module copy,
harmless); CLI holds no answer-producing logic; strict kw leaves all 8 callers unchanged; median
of 3 keeps the bar (report max beside median, cold run excluded); telemetry cannot alter an answer
or double-emit. 3a changes agent_resolver.py bytes, so the policy id changes ONCE (one cache flush)
-- expected, stated in the commit.

## Execution record (2026-10-03)

| commit | hash | gates |
|---|---|---|
| 1 record_signal lock | 163f0b2f | race 5/5 (214/900 lost -> 0) |
| 2 query_fp, NO_CATALOG ids, NOT_POLICY | 965fb859 | resolver 32/32 |
| 3a CLI out of policy | 050c3484 | resolver 33/33, s4 44/44; liveness offenders 69 -> 69 (agent_resolver off, agent_telemetry on-disk-undeclared until 3) |
| L latency median of 3 | d1f2d541 | same 2000 ms bar; median 934 ms [918, 934, 1015], cpu 609 ms |
| 3 adapter + resolve_and_record + metrics + CLI | 383fa916 | telemetry 20/20, resolver 33/33, co12 8/8, race 5/5, s4 44/44; pre-commit review APPROVE (LOW + INFO applied); offenders 69 -> 68 |
| 4 mutation drills | 361aea29 | 13/13 KILLED (c5-1..13). First pass 12/13: the sink-bypass mutant crashed the suite (IndexError) -> UNJUDGED; the same block let V-TEL-POLICY pass vacuously (all() over []). Fixed, 4 affected drills re-run from committed specs -> KILLED |

Live PRG (read-only, real surface): `python -m modules.cognitive_os.co_12_telemetry --report` ->
`agent-resolution: 0 resolutions (no observations) ... 7 unparseable signal lines not counted`.
The 7 are the torn fragments measured before commit 1, previously dropped with no count.

Not done on purpose: `reachability.py --baseline` (it freezes EVERY undeclared orphan into
standing debt, including other panes' new ones; agent_resolver was never in known_orphans, so the
3a declaration removed it by name). ADS auto-docs under docs/arch|prd for the new tests stay
untracked like the rest of that tree. UKDL not edited: it carries another pane's uncommitted
hunk and commit isolation is file-granular.

### Meta-analysis
- Durable facts per resolution: typed miss, causal miss_ids, vetoed_by, cache provenance, policy
  id, catalog fingerprint, request identity (query_fp), grant, resolution_id. All COPIED from the
  resolver; the adapter owns only schema, grant and resolution_id. Nothing recomputed.
- Fresh vs reused stays separable (cache field; distinct fresh observations by (query_fp, grant,
  catalog_fp, policy)). NO_MATCH is reported as a count of answers, never as demand.
- Observability left the policy id twice in this program: the adapter (commit 2) and the CLI
  (3a). The general shape: a hash over "the package" silently includes presentation.
- Latency red at 2,884 ms: environment (one sample, 100% CPU, ~30 claude procs); a third of a
  resolve is I/O, so the gate stays host-sensitive. Bar unchanged; median of 3 now.
- Answerable now: how often each typed miss occurs, fresh vs reused, recurrence by query_fp.
  NOT answerable until C6: whether a miss cost anything (no agent_run / outcome join yet).

### UKDL candidates (not promoted: one occurrence each, and UKDL is foreign-dirty)
- Trap: a policy/cache identity hashed over a whole package also hashes presentation and
  telemetry; an edit that cannot change an answer then flushes every cached answer.
- Trap: a "freeze today's debt" baseline command run to clear ONE module absorbs every other
  writer's new debt into the standing set -- declare by name instead.
- Trap: a lenient reader (OSError -> []) under a metric turns UNREADABLE into a measured zero;
  give the owner a strict mode, keep the lenient default for existing callers.
- Trap (from drill 7): a gate that indexes what a collaborator received crashes when the
  collaborator is bypassed, so the mutant reads UNJUDGED instead of KILLED; and `all()` over the
  received items passes vacuously on zero. Assert the count, then read with defaults.

CBR: agent_systems stays EXPERIMENTAL (B0). Nothing here is mature enough to ratchet: no live
agent_resolution rows yet, no outcome join, no remote PRG.
