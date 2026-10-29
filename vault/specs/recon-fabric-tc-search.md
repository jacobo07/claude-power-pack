---
status: APPROVED 2026-10-29 (Owner "go ahead" on the next unit named in D21 step 4d)
covers: [recon-fabric-tc-search, toolchain-search, tc3, toolchain_sd-search]
extends: [d21-step4-motion-closure-vs-frontier-2026-10-29.md]
tier: T2 (certification authority, persisted evidence, gate changes)
---

# TC3: search under the toolchain flags

## Objective
Run the SR1 search engine on the near-misses of the toolchain lane (`toolchain_sd.LANE`, -sdata 8 -sdata2 8), and
certify what it solves. Today search_c and the campaign compile at -sdata 0, so those near-misses are out of reach. The
lane's 3 motion functions at >= 95 % are among them.

## Premises (verified in source, GEX44 t1/campaign @ dc01ea78)
- Every frozen path search_c uses (`fastmatch.measure_fn`, `cache_key`, `fingerprint.real_bracket`) reads cv1.FLAGS at
  call time, so a process switched by `use_sd8()` searches under the lane's flags.
- `search_c.CDomain` takes its root from the module function `root_source` (v5). `searchable()` ties the root to the
  committed fingerprint view key, and the views were built at -sdata 0.
- `search.run` refuses a store path that is not git-ignored (`.local` is ignored), and resumes only under the same
  identity (root, seed, depth).

## Design
1. `toolchain_sd.TCDomain(CDomain)`:
   - The root is the lane transform (v5 + retype) of the m2c source, and `materialize` replays from that root.
   - `searchable` requires the lane sweep row to exist, compile and not match, its key to equal the root ident (the tie
     to committed lane evidence), and pct < 100.
   - Labels come from the views when present, else `UNLABELLED` (summary schema widened for this domain only).
2. `toolchain_sd search --min-pct P --max-evals N --max-depth D`:
   - The cohort is the lane rows with compiles, not match, pct >= P and no CERTIFIED frontier state, sorted by
     (-pct, fn).
   - Store: `.local/search-tc/<lane>-<sl>-d<D>`.
   - Evidence: `evidence/tc-search/<run>/{run.json, results.jsonl, solved.jsonl}`, where solved rows use the campaign's
     format plus `lane`.
3. `toolchain_sd certify-solved <solved.jsonl>`. It applies the search hook's rule under the lane's flags:
   - controls before and after;
   - a fresh-cache replay of the materialized source, which must give the solved object bytes at 100;
   - the extent check;
   - an A2 negative on the rebuilt source.

   Receipts merge by function into `evidence/cert1-sd8/receipts.jsonl` with `kind: "search"`, `root` and `path`.
4. Projection: a toolchain receipt of kind `search` certifies (`certified_by: toolchain`) only while the lane sweep, the
   champion sweep and the champion key hold and `root` equals the lane row key. The lane row need not match. Whole-lane
   receipts keep today's rule.

## Acceptance (each driven red -> green)
- A1 V-RF-TC1-SEARCH-DOMAIN: TCDomain's root ident equals the lane sweep key for a real function. A matching lane row,
  a missing row, or a root key that differs from the lane key is each refused by `searchable`.
- A2 V-RF-TC1-PROJECTION covers kind `search`: a stale root lapses the receipt and a matching root certifies. A search
  receipt does not need the lane row to match; a whole-lane receipt still does.
- A3 a real run certifies >= 0 functions through `certify-solved` with healthy controls. 0 is a valid measured result,
  never assumed.
- A4 every existing suite stays green: TC1, FR1, FP1, CERT1, RR1, CP1 (and --live), NEXT, SR1 --live.

## Out of scope
Changing the campaign's own SL/pins or `next`, the 10499 rule, and pushing.

## Rollback
Revert the commits. Evidence lives in new paths only.
