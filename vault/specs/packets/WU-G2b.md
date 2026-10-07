done_gate: python3 tools/test_grammar_default.py && python3 tools/test_grammar_compile.py
work_tree: /home/kobii/missions/grammar/.claude/worktrees/wu-g2

# WU-G2b -- close G1's review findings, compile by default, orchestration below the model

Re-issue of WU-G2 (mission m-da6e925b5092 halted: its packet forbade worktrees, which contradicts the harness
EnterWorktree rule). Spec (binding): `vault/specs/compiled-grammar-default.md` (laws 4-6). G1 is merged (laws 1-4, 7;
V-GRAMMAR 41/41). Fresh worker, no parent transcript. This file is your scope, budget and done-gate.

## 0. Where you work
- FIRST action: EnterWorktree with name `wu-g2`. All edits, tests and commits happen in
  `/home/kobii/missions/grammar/.claude/worktrees/wu-g2` (the `work_tree:` line above). Never edit the main clone
  `/home/kobii/missions/grammar` itself, never touch branch `grammar/default`.
- The worktree starts from `grammar/g2-partial`. Check `git merge-base --is-ancestor 1a4192fe HEAD` exits 0; if not,
  `git merge --ff-only grammar/g2-partial` before anything else.
- Do NOT run GSD commands, do NOT spawn agents. Pathspec commits on the worktree branch. Never push. Never touch the
  live install `/home/kobii/.claude/skills/claude-power-pack` or another mission's directory.

## 1. Finish and prove the two findings of the independent review of G1 (first)
Commit 1a4192fe already carries an UNVERIFIED implementation of both in `tools/gsd_mission.py`
(`_packet_text`, `_tree_inside_repo`, `packet_gate_dir`, the drift check in `packet_gate_passed`). Treat it as a
hypothesis: write the tests, prove each one red against the pre-fix behaviour (mutation: copy the module, revert the
hunk, import the copy, assert red), then fix whatever the tests expose.
- F1 self-certification: when the packet's current sha256 differs from the one recorded at `envelope --wu-packet`,
  the gate is NOT judged (return None) and a ledger row `packet_gate_drift` is written. Test: edit a fixture packet's
  gate to `true` after setting it -> not COMPLETED; unedited control -> COMPLETED. Also: a record whose wu_packet has
  no sha256 -> not judged.
- F2 gate cwd: the gate runs in the tree the work happens in. A packet `work_tree: <abs path>` inside the record's
  repo wins; outside the repo (or relative, or missing dir) -> not judged + `packet_gate_unanswered`; no line -> the
  owner worker's tree via `effective_workdir`, else work_dir, else cwd. Test every pole, including a worktree of the
  same repo (admitted) and a sibling clone of a different repo (refused).

## 2. Law 5 -- `tools/gsd_compile.py`
`gsd_compile.py compile --repo R --workstream W --phase N [--gate CMD] [--out DIR]`:
- reads `.planning/workstreams/W/ROADMAP.md`, extracts phase N's Goal, Requirements and Success Criteria (refuse if
  the phase is absent or already `[x]`);
- runs `tools/gsd_dossier.py` with the phase section as the contract (concepts = its success criteria) and the repo's
  module roots named in the phase text, output under `.planning/workstreams/W/packets/phase-N/`;
- writes `WU-PN.md`: `done_gate:` (from `--gate`, or a `Gate:` line in the phase; NO gate -> refuse to compile: a
  packet without a deterministic gate is not admissible), `work_tree:`, inputs (dossier first, page rules), outputs
  (the success criteria verbatim), budget derived from `vault/config/route-floors.json` via route_admission
  (floor x calls x (1+margin)), boundary-reason rules, and the worktree rule: the worker enters ONE worktree named
  in the packet and works only there (never "do not enter worktrees": that contradicts the harness);
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
check per law-5/6 rule and per F1/F2 rule (copy, remove the check, import the copy, assert red). Use the harness
style of tools/test_grammar_default.py.

## Budget
At most 60 model calls. Token estimate 10M; the breaker parks you at 20M. The stall breaker fingerprints the main
clone root and cannot see your worktree, so its stall budget is set to 20M (equal to the trip): it will not park you
for working in the worktree, and nothing else will either -- the 20M total is the only ceiling, so stay lean.
Commit after each section. Redirect test output to logs; read only summary + failing lines.

## Done
In the worktree: `python3 tools/test_grammar_default.py && python3 tools/test_grammar_compile.py` exits 0;
`python3 tools/test_gsd_mission.py` shows no new red (baseline 224/225, the red is V-MC-PLAN-FACTS-REFUSES-OVERLAP);
`python3 tools/test_gsd_mission_envelope.py` 39/39. Write `vault/specs/compiled-grammar-default.RECEIPT-G2.json`
(worktree branch, commits, test pass lines, changed functions). Commit, end with `HANDOFF NOTE:` and one line. Do not
wait.
