# WU-E2 -- Obligation model, owner classifier, evaluation->obligation compiler (M1, M3, M4)

Common brief: `PROGRAMME.md`. Read `WU-E1-receipt.md` and `PREMISES.md` first; they override this packet where they
disagree. Route M (20 calls). cwd `C:\Users\User\Apps\wt_ewc`.

Steps:
1. M1 Goal Spine obligation fields (EXTEND convergence.py / mission/obligation.py per PREMISES): add `source`,
   `severity` (RED/AMBER/INFO), `actionability` (NOW / AFTER_DEP / HUMAN_PREF / APPROVAL / RESOURCE / INFO / WAIVED),
   `owner_class`, `next_action`. Old events without them must still project (test it on a real existing goal log copy).
   Add the SESSION scope for sessions with no goal bound, in the SAME event format, at the path PREMISES names, written
   atomically, readable by a Node hook with one JSON/JSONL read. RED tests first, both poles.
2. M3 `modules/autonomy_gate`: `classify_obligation(ob)` -> {owner AGENT|OWNER, category, why} reusing `classify()` on
   the obligation's next_action (do not fork the regexes). Rules: RED with an internal next action -> AGENT/NOW;
   "another iteration", "takes effort", "uncertain but researchable" are NEVER owner categories; subjective-only ->
   OWNER/preference, and only when no NOW obligation remains in the set (`human_gate_ready(obs)`). Fail closed as the
   gate already does. Tests: every category both poles + the 3 phrases above as near-misses.
3. M4 compiler: a function in `modules/daif/obligation_extractor.py` (or a thin sibling, decide by PREMISES) that takes
   the last assistant turn's TEXT and returns obligations: table rows with FAIL/RED/WARN/AMBER, "not written/missing
   evidence", "uncommitted/not committed", "next iteration/next step/recommend ... next". Wish/description sentences
   are refused exactly as the extractor already refuses them. Put the trigger patterns in ONE JSON (e.g.
   `modules/autonomy_gate/obligation_patterns.json` -- decide the home) that E3's Node hook will read too.
4. CLI the agent uses to record/close explicitly: `python -m <owner> obligations add|close|list --session <sid>`
   (or extend an existing CLI if PREMISES finds one). Closing requires a verdict string naming the gate that ran.
5. Run `tools/test_ewc.py`: the fixture's incident turn must now COMPILE to >= 5 NOW obligations + 1 HUMAN_PREF, the
   complete control to 0, the human-only control to 1 APPROVAL. (The Stop-level assertions stay red until E3.)
6. Liveness: new module/CLI wired or declared in `vault/liveness/reachability_registry.json`; reachability exit 0.
Receipt: per-step PROVEN/NOT_PROVEN with test output counts, the patterns-JSON path, the session-ledger path + format.
