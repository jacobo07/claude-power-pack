---
phase: 02-e1-runner-with-the-stopping-contract-as-tested-code
plan: 03
requirements: [E1-RUNNER]
status: complete (uncommitted; the orchestrator commits after review)
files_modified:
  - vault/programs/cognitive-economy/e1/e1_runner.py
  - vault/programs/cognitive-economy/e1/test_e1_runner.py
---

# 02-03 Summary: preflight, per-run checks and the `preflight` subcommand

## What was built

- `e1_runner.py` additions:
  - `git(*args, cwd, check)`: the runner's own git helper.
  - `e1_rules(packet)`: the 11 E1 rules.
  - `ordered_tasks(bank, packet)`: `bank.tasks()` plus the packet's `rule_bytes`, passed through `e1_contract.contract_order`.
  - `check_pins(packet, home)`: opens each rule file `"rb"` only, normalises CRLF to LF, compares sha256 against the packet, and returns `(ok, mismatches)`.
  - `cli_version(path)`: runs `--version` only; raises on a non-zero rc or empty output.
  - `check_cli(path, version_fn)`: refuses any path other than CLAUDE, a non-executable file, an unreadable version, and any first token other than 2.1.289. Returns `(problems, version)`.
  - `bank_drift(repo, bank_rel, frozen_file, info=None)`: compares the frozen commit's blobs with the working-tree bytes (`git hash-object`). Reports missing, edited and added files. It skips `__pycache__` and never follows symlinks.
  - `read_records(path)`.
  - `preflight(...)`: nine checks in fixed order. Every check is evaluated, and an exception or SystemExit becomes REFUSED, never an escape. When no bank is loaded, the four bank-dependent checks are REFUSED "bank not loaded".
  - `per_run_checks(...)`: the CLI + pins + drift subset.
  - `cmd_preflight(argv, version_fn)`.
  - `main(argv)` and `__main__` dispatch. The module docstring now carries the usage lines.
- `test_e1_runner.py`: 9 new gates, inserted before V-E1-NO-MODEL-END:
  - Task 1: PINS, CLI, BANK-DRIFT, RECORDS-READ.
  - Task 2: PREFLIGHT-OK, PREFLIGHT-REFUSALS, PREFLIGHT-NOBANK, PER-RUN-CHECKS, CLI-PREFLIGHT.
  - Helpers: `pin_world`, `drift_repo` (temp git repos, `core.hooksPath=/dev/null`), and the `fake_world(tmp, **faults)` fixture builder.

## Verify output

Task 1: `test_e1_runner.py V-E1-PINS V-E1-CLI V-E1-BANK-DRIFT V-E1-RECORDS-READ` printed `E1_PASS=6/6` (exit 0).

The full suite (exit 0, 0 FAIL lines) ends `E1_PASS=49/49  threshold=49/49`. New lines (abridged at 300 chars by the harness):
```
PASS V-E1-PINS clean=13/[] edited=(12, ['rules/python/testing.md: sha256 1bb840a98c91 != pinned 5f08f3abc04e']) deleted=(12, ['rules/python/testing.md: unreadable (FileNotFoundError)']) crlf=(13, [])
PASS V-E1-CLI good=([], '2.1.289 (Claude Code)') local=(['CLI path /usr/local/bin/claude is not ...']) bare=(['CLI path claude is not ...']) old=(['CLI version 2.1.113 != 2.1.289 (ADDENDUM-E1 Design)'], ...) unread=(['version unreadable: OSError'], None)
PASS V-E1-BANK-DRIFT clean=[] pycache_only=[] edited=[edited since freeze: bank/task_a.py] edited_committed=[same] added=[added since freeze: bank/task_zz.py] deleted=[missing since freeze: bank/_e1_common.py] frozen_absent=[BANK_FROZEN_AT missing] not_a_hash=[malformed] zeros=[not in this repository] bankless=[holds no bank]
PASS V-E1-RECORDS-READ absent=[] blanks=[{'kind': 'run'}, {'kind': 'stop'}] bad='results line 2 malformed'
PASS V-E1-PREFLIGHT-OK cli:OK pins:OK:13/13 excludes:OK:13 paths bank:OK bank_drift:OK freeze_check:OK base:OK:78ba9e7414 index:OK:11 tasks results:OK:absent
PASS V-E1-PREFLIGHT-REFUSALS freeze_bad>freeze_check no_freeze>freeze_check base_raise>base index_absent>index index_swap>index index_missing>index index_ten>index pin_edit>pins version_old>cli results_malformed>results results_attempt3>results drift>bank_drift
PASS V-E1-PREFLIGHT-NOBANK escaped=None ... bank:REFUSED:no validate_bank.py ... freeze_check/base/index/results:REFUSED:bank not loaded
PASS V-E1-PER-RUN-CHECKS good=[] pin_edit=[1 problem] drift=[1 problem] version_old=[1 problem]
PASS V-E1-CLI-PREFLIGHT rc=1 last='PREFLIGHT REFUSED 6' bank=['CHECK bank REFUSED no validate_bank.py in /tmp/...', ...] bogus_rc=2
PASS V-E1-NO-MODEL-END blocked=1 with -p=0 version-probes=1 other=[]
```

Host preflight (`python3 vault/programs/cognitive-economy/e1/e1_runner.py preflight`, exit 0):
```
CHECK cli OK 2.1.289 (Claude Code)
CHECK pins OK 13/13
CHECK excludes OK 13 paths
CHECK bank OK vault/programs/cognitive-economy/e1/bank
CHECK bank_drift OK 17 files match d68871742a
CHECK freeze_check OK d68871742a
CHECK base OK 78ba9e7414
CHECK index OK 11 tasks
CHECK results OK absent
PREFLIGHT OK
```

The plan's full `<verify>` chain printed rc 0. Other checks:
- `validate_bank.py freeze-check` printed `FREEZE-CHECK OK d68871742a`, and `pins` printed `PINS 13/13`.
- `/home/kobii/e1-runs` holds 0 entries, and `git worktree list | grep -c e1test` printed 0.
- The only real `claude` exec was the host preflight's `--version`.

## Red drills (throwaway in-process monkeypatches, nothing written)

Each one turned its gate red:
- pins hashing without LF normalisation turned V-E1-PINS red (the CRLF case).
- bank_drift with the working-tree walk removed turned V-E1-BANK-DRIFT red (added file).
- `hash-object` returning nothing crashed V-E1-BANK-DRIFT, which counts as a FAIL.
- CLI_VERSION swapped turned V-E1-CLI red.
- `ordered_tasks` reversed turned V-E1-PREFLIGHT-OK red (index order).
- `replay` as a no-op turned V-E1-PREFLIGHT-REFUSALS red (results_attempt3).

## Deviations from Plan

1. **[Count] The suite ends 49/49, not 45/45.** The plan counted 36 gates before it. Four more were added by the 02-01/02-02 review fixes: CLI-ERROR, BANK-ACCESS, BANK-ACCESS-RECORDED and ARM-EXCLUDES. 40 + 9 = 49.
2. **[Discretion] The index check does not compare `base` when the base check refused.** The plan's base fault (jbase raises) must leave index OK. With no BASE value to compare against, index stays OK and its detail says "(base unchecked: the base check refused)". The preflight is still refused by the base line, so this does not weaken the overall verdict.
3. **[Discretion] `bank_drift` takes an optional `info` dict** (files count and frozen hash) for the OK detail `17 files match d68871742a`. preflight passes `info=`, so an injected drift_fn must accept `**k`. per_run_checks does not pass it.
4. **[Discretion] check_cli calls `version_fn()` with no argument.** The path is already pinned to CLAUDE before the version is read, and the injected fakes stay trivial. check_cli also refuses a non-executable CLAUDE before it reads the version.
5. **[Discretion] cli_version raises on a non-zero rc or empty stdout.** Either case then reads as "version unreadable" instead of an empty version string.

Not touched: the bank, BANK_FROZEN_AT, the packet, STATE/ROADMAP and ~/.claude. `vault/progress.md` (modified) and `.gsd/` (untracked) were already in that state before this executor ran.

## Review fixes (02-03 review)

These were applied after 02-04 landed. The source is review-02-03.md (verdict APPROVE, with MEDIUM F1-F3 and LOW F4-F5). The binding decision is STATE.md 2026-10-05 PINNED IDENTITIES. Every fix is a refusal; no fix adds a pass path. The only files touched were e1_runner.py, e1_contract.py and test_e1_runner.py.

**F1: the packet is pinned.**
- `PACKET_SHA256` is the sha256 of the committed packet bytes: `git show HEAD:vault/programs/cognitive-economy/post-reset-packet.json | sha256sum` printed `b6b104bb523d147377d13f752fe7d13b31cc66728164eb6bdf5b6e2c1c5522ba`, which matches the file on disk.
- `check_packet` refuses any other packet bytes.
- `rule_set_problems` refuses a packet that is not 13 distinct rule paths. Both `check_pins` and `excludes()` use it.
- Preflight gained a `CHECK packet` line, so it now runs 10 checks. `per_run_checks` runs the same packet and pin checks.

**F2: per_run_checks no longer discards the pin count.** A pin count other than 13, or any pin problem, now becomes one problem `pins N/13: ...`.

**F3: the freeze hash is pinned.**
- `BANK_FROZEN_HASH = d68871742adefe392728370d82b69991a4437f79`, and `BANK_COMMIT_PREFIX` is derived from it.
- `check_frozen_pin` refuses any other BANK_FROZEN_AT value. Both preflight's bank_drift line and per_run_checks use it.
- A re-freeze (edit, commit, write the new hash into BANK_FROZEN_AT) still passes `bank_drift` on its own. It is now refused.

**F4: the gap between the check and the use is closed.**
- `child_env` sets `DISABLE_AUTOUPDATER=1` for both arms.
- `one_run` records `cli_versions_observed`, the distinct `version` values found in the transcript. `reconcile` records it too.
- `one_run` takes `drift_fn` and re-runs it after the post-session grade, storing the result as `bank_drift_after`.
- `e1_contract.run_valid` has new clauses for a run that was launched (or whose launch is not recorded):
  - a version list other than `[CLI_VERSION]` makes the run invalid as `cli version drift: ...`.
  - a non-empty drift list gives `bank drift during run`.
  - a missing re-check gives `bank not re-checked after grade`.
- `CLI_VERSION` now lives in e1_contract, and the runner reads it from there.
- `drive()` appends a refusal record `{"kind": "refusal", "after": <run_id>, "problems": ["bank drift during run", ...]}` after a run that drifted, commits it and halts with REFUSED.
- `cmd_run` passes the production re-check, `check_frozen_pin + bank_drift`.

**F5: bank_drift's walk fails loudly.** `os.walk` now runs with `onerror` raising, so a directory it cannot list becomes the problem `bank unreadable: <path>`.

**Drive and per-run exceptions.**
- `drive()` already called `check_fn` before every `run_fn`, attempt 2 included (02-04). V-E1-LOOP-CHECK-EVERY-RUN now pins that with an attempt-2 retry.
- A `check_fn` that raises, or returns something other than a dict, now becomes the refusal record `per-run check raised: ...` with no run. Before this fix the exception escaped drive.
- Inside `per_run_checks`, a step that raises (for example an unreadable packet) becomes the problem `<step> unreadable: ...`.

**Gates.** There are 7 new gates: PACKET-PIN, PACKET-SET, FROZEN-PIN, CLI-DRIFT, LOOP-DRIFT-HALT, LOOP-CHECK-EVERY-RUN and DRIFT-UNREADABLE. V-E1-VALID gained 5 faults (versions and drift) and V-E1-ENV gained DISABLE_AUTOUPDATER. The fixtures changed too:
- `good_run` and the fake transcript carry the version and drift fields.
- `fake_world` passes its own packet and freeze pins.
- The tracer passes the real post-grade drift check.
The suite went from `E1_PASS=64/64` to `E1_PASS=71/71` (exit 0).

**Red drills.** The driver is jobs/68d51544/tmp/fix0203/drills.py. Each drill mutated the source on disk, ran the named gates, and restored the files byte-identical (sha256 checked). All 12 went red:
- F1, packet pin ignored: PACKET-PIN went red.
- F1, rule-set check off: PACKET-SET went red.
- F2, the original shape (count clause off and per-run ignoring n): PACKET-SET went red.
- F3, frozen pin ignored: FROZEN-PIN went red.
- F4, run_valid ignoring the version: VALID and CLI-DRIFT went red.
- F4, no post-grade re-check: CLI-DRIFT went red.
- F4, drive not halting on drift: LOOP-DRIFT-HALT went red.
- F4, auto-updater left on: ENV went red.
- F5, onerror dropped: DRIFT-UNREADABLE went red.
- drive, raising check escapes: LOOP-CHECK-EVERY-RUN went red.
- drive, check skipped on attempt 2: LOOP-CHECK-EVERY-RUN went red.
- per_run, a raising step escapes: PACKET-PIN went red.

The F2 count is enforced twice: by the count clause in `rule_set_problems` and by the `n == 13` test in per-run. So removing only one of them stays green by design, and the F2 drill removes both.

**Host.**
- `preflight` printed 10 lines of `CHECK ... OK`, including `CHECK packet OK sha256 b6b104bb523d` and `CHECK bank_drift OK 17 files match d68871742a`, then `PREFLIGHT OK` (rc 0).
- `plan` ended with `NEXT RUN J-gceg_product_page A 1` (rc 0).
- `validate_bank.py freeze-check` printed `FREEZE-CHECK OK d68871742a`.
- No results.jsonl was written. The bank, BANK_FROZEN_AT and the packet are untouched.
