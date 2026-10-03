---
covers: [agent-resolver, resolver-negative-cache, typed-misses]
date: 2026-10-03
status: EXECUTED -- Owner approved 2026-10-03 ("y", all three decisions); commits b34dbeec, 016a5b6a, 7faf70be, 16976909 + docs. Resolver 29/29, 8/8 C4 drills KILLED.
parent: vault/specs/agent-capability-virtualization.md (D5, C4)
head_at_scan: 20d0e662
---

# ACV C4 -- typed resolver misses (ULTRA reconciliation, phase 1+5)

## Reality (measured 2026-10-03, read-only)

- HEAD 20d0e662 on feature/knowledge-acquisition; ee4461ac (C3) is an ancestor and is on origin.
  9 local commits ahead of origin, all other panes (rollover / ccp / r2), none on a C4 surface.
  C4 surfaces clean: modules/capability_runtime/, tools/test_agent_resolver.py,
  tools/test_capability_runtime.py, tools/mutation_drill.py, the ACV spec.
- Resolver contract today (`agent_resolver.resolve` -> dict): `status` in
  {RESOLVED, NO_CERTIFIED_SPECIALIST, CATALOG_UNREADABLE}; lists `near_misses` (shortlisted, gate
  verdict not activating) and `excluded` (shortlisted, class above grant, code CLASS_EXCEEDS_GRANT).
  CATALOG_UNREADABLE only when ZERO specs load; it returns before the cache write.
- Callers: tools/test_agent_resolver.py, tools/test_agent_s4.py, the module CLI. No production
  caller, no fallback router, no Foundry recorder (D7: resolver is PLANNED+OWNER_QUEUE).
- Measured on the real catalog (11 specs, 0 broken), no cache:
  - "write a haiku about the ocean" -> near_miss comment-analyzer, verdict NOT_APPLICABLE
    "no trigger matched" (lexical overlap only).
  - "review this code for bugs" @investigator -> 7 reviewers in `excluded`, none gate-evaluated.
  - "audit this migration plan..." @investigator -> oneshot-architect-auditor excluded, and it IS
    the selected specialist @verifier (V-RES-ORDER-FREE-TRIGGER) -- the real CLASS_EXCLUDED case.
  So "near_misses non-empty" / "excluded non-empty" are lexical noise, not causal facts.

## Defects found (classified)

1. CLASE 2 -- partial catalog laundered into a true negative. `catalog()` returns the specs that
   load plus `broken`; with >=1 spec loaded and none matching, status is NO_CERTIFIED_SPECIALIST
   AND it is cached, although the broken spec may be the one that matches.
2. CLASE 4 -- unreadable spec crashes instead of typing. `load()` catches only JSONDecodeError;
   a non-UTF-8 spec.json (UnicodeDecodeError) or an OSError propagates out of `catalog()` and
   `resolve()` -- no typed outcome at all. `root.iterdir()` OSError likewise.
3. Enum-only trap avoided: deriving BELOW_GATE / CLASS_EXCLUDED from the current lists would make
   NO_MATCH almost unreachable (noise above), starving any future gap signal.

## Outcome model (decision 1)

`status` keeps its three values (compat). New machine field `miss` (None on RESOLVED):

| miss | proves | does NOT prove |
|---|---|---|
| CATALOG_UNREADABLE | the search did not cover the estate (no catalog, or >=1 spec failed to load) | anything about capability existence |
| CLASS_EXCLUDED | a spec ABOVE the grant would be selected by the same gate (verdict activating) | that the grant should be raised |
| BELOW_GATE | an in-grant spec whose trigger matched was BLOCKED by a capability gate (applicability.BLOCKING: evidence, owner, scope, runtime, prerequisites) | absence; the capability exists |
| NO_MATCH | no spec in the certified envelope reached its gate: catalog complete, BM25 top-20 with score>0, no trigger hit | that no capability could ever exist; specs ranked past 20 are not judged |

CATALOG_UNREADABLE stays a resolver outcome (status CATALOG_UNREADABLE), not an exception: it is
already a status today and callers read `status`. Partial catalog with a selected candidate stays
RESOLVED (a found specialist is real evidence) and keeps `broken` visible.

"Reached its gate" = the shared matcher finds a trigger hit (the gate-1.5 predicate) on the same
mission text evaluate() sees; computed with applicability's own `_hits`, evaluate() unchanged.
Excluded specs get the same evaluate() call to decide CLASS_EXCLUDED; `excluded` rows gain a
boolean `would_activate`. No new score/threshold fields: near_misses already carry verdict,
gate_score, reason.

## Precedence (decision 2 -- DEVIATES from D5's list, needs Owner approval)

Proposed: CATALOG_UNREADABLE > CLASS_EXCLUDED > BELOW_GATE > NO_MATCH.
D5 listed BELOW_GATE above CLASS_EXCLUDED. With D5's order, a request that HAS an applicable
specialist withheld only by the grant reports BELOW_GATE whenever any in-grant spec also reached
its gate -- the authority fact is hidden behind a weaker one. Under the new definitions
CLASS_EXCLUDED is a counterfactual hit (raise the grant and you get a specialist), the most
decisive cause short of a blind search. Precedence is a fixed table lookup over the set of facts
found, never iteration order; overlap tests drive both orders of the catalog.

## Empty / unsearchable query (decision 3 -- touches C3)

A task with text but no searchable tokens ("!!! ???") never reaches BM25, so any miss label would
be false evidence. Proposed: raise the EXISTING AgentSpecError("EMPTY_TASK") (the CLI already maps
it to exit 2). Consequence: `use_cache = use_cache and bool(q)` becomes unreachable, so C3 drill
c3-5 would read SURVIVED/HARNESS. It is superseded (dated note in the JSON, file kept) by a C4
drill that removes the raise. Alternative if the Owner prefers C3 untouched: keep the return path
with miss=None and status NO_CERTIFIED_SPECIALIST -- weaker (a None miss on a non-RESOLVED status).

## Cache matrix (decision 4) -- existing cache, no new layer, key unchanged

| outcome | cached | answer depends on | invalidated by (existing key parts) |
|---|---|---|---|
| RESOLVED | yes (as today) | tokens, grant, k, spec.json set, code | fingerprint, policy hash |
| NO_MATCH | yes | same | same |
| BELOW_GATE | yes | same (gate code in policy hash, contract in spec.json) | same |
| CLASS_EXCLUDED | yes | grant (in key) | same |
| CATALOG_UNREADABLE (total or partial) | NO | -- | recomputed every call |
| EMPTY_TASK | never reaches cache | -- | -- |

`miss` lives in the cached VALUE, so a HIT reproduces it; `cache: HIT|MISS` already distinguishes
fresh from cached. Old entries become unreachable automatically (agent_resolver.py edit changes the
policy hash). Known limit kept: a spec breaking without a spec.json change (primitive deleted) can
still serve a pre-break hit; it can only have been computed on a complete catalog, so it is not a
partial-catalog lie.

## Callers (decision 5)

- module CLI: print `miss`; exit code unchanged (0 RESOLVED, 1 otherwise, 2 AgentSpecError).
- test_agent_s4: re-run, no change expected (must_still_pass).
- Foundry recorder / creation gate / C5 telemetry: future consumers. C4 guarantees only that a gap
  signal can be keyed on miss == NO_MATCH and that the other three are distinguishable.

## mutation_drill detail debt (decision 6): FIX NOW, separate micro-commit

tools/mutation_drill.py:176 lists `startswith("FAIL")` lines; both resolver suites indent. C4 adds
drills on those suites. One-line change to strip before matching, plus a case in
tools/test_mutation_drill.py. Verdict logic (gate_line) untouched. Unowned, clean.

## Commits

1. fix(agent-spec): unreadable spec.json / catalog dir is typed, not a crash (+ red-first test).
2. feat(agent-resolver): typed `miss` + precedence + partial catalog not cached + EMPTY_TASK.
3. test(agent-resolver): V-RES-MISS-* on real resolver paths (temp catalogs + real catalog).
4. fix(mutation-drill): detail lists indented FAIL lines.
5. test: C4 mutation drills under vault/audits/agent_estate/mutation_drills/ (c3-5 superseded note).
6. docs: spec D5/status + RESUMPTION + this plan sealed; S5d typed-negative-cache marked subsumed.
7. docs(ukdl): only lessons with evidence (partial-catalog trap; lexical-noise-as-cause trap).

## PRG (real resolver path for each outcome)

NO_MATCH: real catalog, "write a haiku about the ocean". CLASS_EXCLUDED: real catalog, audit query
@investigator. BELOW_GATE: temp catalog with a real spec whose anti-trigger is hit (anti-trigger
veto after a trigger hit). CATALOG_UNREADABLE: temp catalogs -- missing dir; one non-UTF-8 spec.json
beside valid specs (red today: crash); one malformed JSON beside valid specs (red today: cached
NO_CERTIFIED_SPECIALIST). Precedence: temp catalog with a below-gate in-grant spec AND an
activating above-grant spec, in both name orders.

## Mutation discriminators (smallest set)

partial catalog -> NO_MATCH; CATALOG_UNREADABLE cached; BELOW_GATE without the trigger-reach test
(noise); CLASS_EXCLUDED without would_activate (noise); precedence swapped; EMPTY_TASK raise removed.
Cached-reason loss is already covered by the cache value round-trip gate.

## Audit (phase 4, oneshot-architect-auditor, READY-WITH-FIXES, 6 gaps) -> all accepted

Supersedes the text above wherever they disagree. Gap 1 premise re-checked by the parent: all 11
real specs declare anti_triggers, none declares required_evidence or prerequisites.

| # | sev | gap | fix injected |
|---|---|---|---|
| 1 | MED-HIGH | anti-trigger veto (NOT_APPLICABLE, not in BLOCKING) counted as BELOW_GATE: "review this go code and write the fix" -> BELOW_GATE "capability exists" while no writer specialist exists; starves NO_MATCH | BELOW_GATE = trigger hit AND verdict in BLOCKING. Anti-trigger veto = did not reach the gate -> NO_MATCH with `vetoed_by` detail. PRG for BELOW_GATE uses a temp spec with required_evidence (the resolver context never supplies evidence, so gate 3 blocks on a real path) |
| 2 | HIGH | EMPTY_TASK raise crashes V-RES-CACHE-NO-EMPTY-KEY (test_agent_resolver.py:128-133), suite dies before its _PASS= line -> every drill on it UNJUDGED | replace that gate with V-RES-EMPTY-QUERY-TYPED (code EMPTY_TASK, cache rows unchanged); raise stays AFTER class_rank so V-RES-BAD-GRANT-TYPED ("x", zero tokens) still gets UNKNOWN_CLASS |
| 3 | MED | miss facts read from truncated lists (`near[:k]`) or excluded rows never evaluated -> k-dependent false NO_MATCH; would_activate must use the same order-free hit augmentation | collect reached / blocked-in-grant / activating-above-grant over the WHOLE shortlist before any [:k]; one helper builds the MissionContext for both in-grant and excluded specs; `miss_ids` names the deciding spec(s) |
| 4 | MED | a dir without spec.json is UNKNOWN_SPEC in `broken` -> permanent uncached CATALOG_UNREADABLE, and fingerprint ignores it -> HIT says NO_MATCH, fresh says CATALOG_UNREADABLE | `catalog()` skips dirs without spec.json (consistent with fingerprint). Early return: existing empty dir -> NO_MATCH; NO_CATALOG -> CATALOG_UNREADABLE |
| 5 | MED | wrong-shape JSON (array/string), non-dict contract, non-string permission_class, fingerprint stat OSError still escape untyped | load(): OSError, UnicodeDecodeError, JSONDecodeError, non-dict raw -> UNREADABLE_SPEC; AgentSpec: AttributeError/TypeError/ValueError -> INVALID_CONTRACT; fingerprint OSError -> cache disabled for that call; one red-first case per shape |
| 6 | LOW-MED | partial-catalog RESOLVED is cached -> "known limit" sentence false (restored primitive keeps serving the weaker candidate) | cache only when `broken == []`, whatever the status |

Mutation set gains: anti-trigger veto counted as BELOW_GATE.

## NOW / NEXT / LATER / REJECT

NOW: the above. NEXT: C5 telemetry (`miss` + `cache` are the fields it emits), C6, C7.
LATER: S6 recorder keyed on NO_MATCH only. REJECT: new cache, new ledger, LLM miss classification,
raw miss counts as a gap metric, a fifth miss class for empty queries.
