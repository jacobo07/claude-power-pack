# WU-C5 -- Proof locality: affected proof closure + green path without reviewer

Common brief: `vault/programs/cdc/PROGRAMME.md`. Plan section: 3 (C5).

Goal: a local change proves locally.
1. `tools/change_impact.py` (exists, 09-28): read it; expose `affected_tests(paths) -> list[cmd]`.
2. `land_worktree.py`: new `--affected` mode: declared tests = union(explicit `--test`, affected_tests(changed paths));
   a changed path with no mapped test -> refuse with reason (never silently skip). Receipt lists the closure.
3. `tier_routing.py` policy: deterministic unit + all affected tests green -> no reviewer escalation; red or
   ambiguous -> escalate (existing behaviour).
4. Proof: on 3 real past landings, affected closure vs full suite agree (same verdict); record times + test counts.
5. From here every CDC landing uses `--affected`. Land via land_worktree.
