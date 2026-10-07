done_gate: python3 tools/test_grammar_default.py && python3 tools/test_grammar_compile.py

# WU-G2 -- close G1's review findings, compile by default, orchestration below the model

Spec (binding): `vault/specs/compiled-grammar-default.md` (laws 4-6). G1 is merged (laws 1-4, 7; V-GRAMMAR 41/41).
Fresh worker, no parent transcript. This file is your scope, budget and done-gate. Do NOT run GSD commands, do NOT
spawn agents, do NOT create or enter git worktrees (the stall breaker cannot see a worktree): work directly in
`/home/kobii/missions/grammar` on branch `grammar/default`. Pathspec commits. Never push. Never touch the live install
`/home/kobii/.claude/skills/claude-power-pack` or another mission's directory.

## 1. Fix the two findings of the independent review of G1 (first, each with a test that fails before the fix)
- F1 self-certification: `packet_gate_passed` reads `done_gate:` from the packet at run time; the worker can edit the
  packet. When the packet's current sha256 differs from the one recorded at `envelope --wu-packet` time, the gate is
  NOT judged (return None) and a ledger row `packet_gate_drift` is written. Test: edit a fixture packet's gate to
  `true` after setting it -> not COMPLETED; unedited control -> COMPLETED.
- F2 gate cwd: the gate must run in the tree the packet's work happens in. Find how the supervisor already follows a
  worker into a worktree (`git grep -n "WORK TREE\|work_tree\|worktree" tools/gsd_mission.py tools/gsd_epoch.py`) and
  reuse it; additionally honour an optional packet line `work_tree: <abs path>` (must be inside the record's repo,
  else not judged). Test both poles.

## 2. Law 5 -- `tools/gsd_compile.py`
`gsd_compile.py compile --repo R --workstream W --phase N [--gate CMD] [--out DIR]`:
- reads `.planning/workstreams/W/ROADMAP.md`, extracts phase N's Goal, Requirements and Success Criteria (refuse if
  the phase is absent or already `[x]`);
- runs `tools/gsd_dossier.py` with the phase section as the contract (concepts = its success criteria) and the repo's
  module roots named in the phase text, output under `.planning/workstreams/W/packets/phase-N/`;
- writes `WU-PN.md`: `done_gate:` (from `--gate`, or a `Gate:` line in the phase; NO gate -> refuse to compile: a
  packet without a deterministic gate is not admissible), `work_tree:`, inputs (dossier first, page rules), outputs
  (the success criteria verbatim), budget derived from `vault/config/route-floors.json` via route_admission
  (floor x calls x (1+margin)), boundary-reason rules, and "Do not run GSD / spawn agents / enter worktrees";
- `--arm` performs arm(--no-launch) -> hold -> set_envelope(token_estimate derived, model sonnet, autocompact =
  floor + packet + margin rounded up to 10k) -> release, through gsd_mission's functions (no subprocess to itself),
  and prints the mission id. `--dry-run` prints everything and arms nothing.
- `commands/cpp-gsd-long.md`: the default section becomes "compile the next phase with gsd_compile --arm"; the old
  `/gsd-autonomous` arming is under a "Legacy (CPP_MISSION_GRAMMAR=legacy)" heading. Keep its done-gate list valid.

## 3. Law 6 -- `tools/mission_wait.py`
`mission_wait.py --mission M [--timeout S] [--guard-renewals]`: zero model; polls the record every 20 s; exits on
COMPLETED / HALTED / BLOCKED / owner hold / worker gone with the packet gate passing; with `--guard-renewals` holds
and `claude stop`s any record `renewed_from` M; prints measured spend (mission_spend.processed_tokens), state and
the last ledger rows. Runnable detached (`nohup`), writes its result to a JSON file next to the record.

## 4. Tests -- `tools/test_grammar_compile.py` (V-GRAMMAR-COMPILE-*, V-WAIT-*, V-GRAMMAR-F1/F2-*)
Both poles for every rule (refusal AND admitted control); compile against a fixture ROADMAP (tmp dir), and once
against this repo's real `.planning/workstreams/` if any workstream has an open phase (dry-run only). One mutation
check per law-5/6 rule (copy, remove the check, import the copy, assert red). Use the harness style of
tools/test_grammar_default.py.

## Budget
At most 60 model calls. Token estimate 10M; the breaker parks you at 20M; commit after each section (a stall of 5M
without a tree change parks you). Redirect test output to logs; read only summary + failing lines.

## Done
`python3 tools/test_grammar_default.py && python3 tools/test_grammar_compile.py` exits 0;
`python3 tools/test_gsd_mission.py` shows no new red (baseline 224/225, the red is V-MC-PLAN-FACTS-REFUSES-OVERLAP);
`python3 tools/test_gsd_mission_envelope.py` 39/39. Write `vault/specs/compiled-grammar-default.RECEIPT-G2.json`
(commits, test pass lines, changed functions). Commit, end with `HANDOFF NOTE:` and one line. Do not wait.
