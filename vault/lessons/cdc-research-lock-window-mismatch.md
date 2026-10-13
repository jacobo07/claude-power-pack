# Research in-flight lock window must be shorter than the store's, because PostToolUse never fires on failed calls (CDC C6)
- Symptom: a failed WebSearch would leave the in-flight lock held and make subscribers wait out the store's 30 min abandonment window.
- Trigger: tool call fails -> no Post hook -> lock never released.
- Root cause: hook reused the store's lock TTL.
- Fix: hook lock window 300 s (CPP_RESEARCH_LOCK_S); store keeps 30 min.
- Prevention: any lock released by a Post event needs a TTL tuned to the failure path, not the success path.
- Regression proof: tools/test_derivation_store.py 24/24 (abandoned lock recovery).
