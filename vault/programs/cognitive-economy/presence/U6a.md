# ce-presence U6a -- launch-time baseline resolver (EXECUTION)

Card: vault/plans/ce-presence-contract-2026-10-07.md in the MAIN checkout (C:\Users\User\.claude\skills\claude-power-pack);
read ONLY sections 1 and 4. No transcripts, no other plans. Goal ce-presence, cap for this unit 2.0M; plan <= 30 tool calls.
cwd = C:\Users\User\Apps\pp-ce-presence (branch ce/presence). Edit and commit ONLY here, never under ~/.claude.
git = & 'C:\Program Files\Git\cmd\git.exe'; python = & 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'.
Commit with `git commit -F <msgfile> -- <paths>`, verify `git log -1 --format=%s`. Never push, reset, stash, merge.

Root cause (verified): in tools/gsd_mission.py every optimisation field is opt-in, so absent = host maximum:
`create()` comment "None -> the host's own defaults"; `slim_profile()` -> None -> `--bg`; `worker_argv` adds `--model`
only if set (host Opus); `--autocompact` falls back to AUTOCOMPACT_SAFETY_NET "600k"; `continue_max_tokens` unset.
Premise: `slim_argv` passes --disable-slash-commands, so a `/gsd-*` resume can NEVER be routed slim.

Do (find code by symbol name, not line number):
1. Grep every caller of worker_argv / launch_worker; record them in the receipt. All launch paths must pass the resolver.
2. Add `resolve_baseline(rec) -> rec` in gsd_mission.py, called once in launch_worker before argv is built.
   Per field: explicit record value kept (src explicit); absent -> policy value (src policy@<version>); policy file
   unreadable -> built-in values (src builtin). Fields: model, autocompact, continue_max_tokens. Work Class from the
   record only: COMPILED_UNIT (has wu_packet), GSD_RESUME (resume_command starts "/gsd-"), OTHER. Never make
   a GSD_RESUME slim. Policy = new keys in vault/config/mission-budget-defaults.json: `baseline_version`, and per
   class {model, autocompact, continue_max_tokens}. Values: model "sonnet"; autocompact and continue_max_tokens taken
   from MEASURED evidence already in the repo (grep continue_max_tokens / autocompact in vault/programs/cognitive-economy,
   e.g. C23b used 170k-250k); cite the source in the receipt. Built-in fallback must equal the policy, never Opus/600k.
   _budget_defaults must keep reading its two old keys unchanged.
3. Record `rec["baseline"] = {version, tier BASIC|COMPILED, work_class, src:{field:..}, legacy_reason}` via the
   existing transition/ledger pattern, ledger row `baseline_resolved`.
4. Legacy exception: optional record field `legacy_reason` in a closed set {host_limitation, uncertified_work_class,
   quality_requirement, novel_architecture, safe_deopt}. Switch env CPP_CE_BASELINE=shadow|enforce|off, default
   shadow, same parser shape as bounded_renewal_mode. shadow: apply defaults, log `would_refuse_legacy` when the final
   launch is --bg + opus + >=600k with no legacy_reason. enforce: refuse that launch with the fix command. off: no
   change at all (byte-identical argv to today).
5. Tests: new tools/test_gsd_mission_baseline.py, V-BASE-* gates, AAA, pure (no worker launched): absent fields ->
   sonnet + policy ceilings; explicit kept; unreadable policy -> builtin (not opus, not 600k); GSD_RESUME never slim;
   packet -> slim path untouched; off -> argv identical to pre-change; enforce + legacy combo without reason -> refused;
   with reason -> allowed and recorded. Mutation drill: delete the resolver call -> a gate must go red; set builtin
   model to opus -> red. Run: test_gsd_mission_baseline, test_gsd_mission, test_gsd_mission_envelope,
   test_gsd_mission_admission, test_gsd_epoch. Report exit codes. A pre-existing red is recorded vs HEAD, not fixed.
6. Receipt vault/programs/cognitive-economy/presence/U6a-receipt.md (<=30 lines): commits, callers found, tests+exit
   codes, mutants, policy values + their evidence source, deviations, bugs. Commit it.
Two failures of the same shape = stop and write the blocker into the receipt. End with `HANDOFF NOTE: U6a done`
(or the blocker).
