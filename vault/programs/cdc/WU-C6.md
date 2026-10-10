# WU-C6 -- Derivation store, singleflight, research reuse, negative knowledge

Common brief: `vault/programs/cdc/PROGRAMME.md`. Plan section: 3 (C6).

Goal: equivalent demand reuses a completed or in-flight derivation.
1. `tools/derivation_store.py`: key = sha256(normalized question + scope + sorted dependency fingerprints (path sha /
   URL / evidence id)). Record: answer pointer (file), provenance, created, freshness TTL, invalidators. API: get
   (fresh + deps unchanged), begin (in-flight lock file, O_EXCL), complete, abandon (lock stale after 30 min).
2. `hooks/research_reuse.js` PreToolUse `WebSearch|WebFetch` (kill `CPP_RESEARCH_GATE=off`): normalized query/URL
   hit -> additionalContext with the stored evidence path + deny the duplicate when the session is bound; in-flight
   by another sid -> deny with "subscribe: <lock>". PostToolUse stores the result. Negative knowledge: query UKDL
   traps + FIOS for the same key; a match -> advisory with the reopen condition.
3. Tests: hit, miss, stale (dep changed) -> miss, in-flight subscriber, abandoned lock recovery, kill switch.
4. Proof: two sessions ask the same research question; second served from store (record both jsonl rows).
Land via land_worktree.
