# Constitution -- `tools/ccn_census.py`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

The following public surface is the module's behavioural contract. Removing or breaking any of it is a breaking change.

- `default_roots()`
- `parse_ts(ts)`
- `main_transcripts(roots, cut)`
- `records(path)`
- `tool_key(name, inp)`
- `collect_tool_events(roots, hours, now)`
- `dup_scan(roots, hours=168.0, now=None, window_s=WINDOW_S)`
- `first_call_rows(roots, days, now)`
- `stampede_scan(roots, days=7.0, now=None, concurrent_s=CONCURRENT_S)`
- `encode_cwd(cwd)`
- `argv_session_id(argv)`
- `is_claude_argv(argv)`
- `classify_role(argv)`
- `proc_record(pid, ppid, argv, cwd, rss_mb)`
- `procs_linux(proc_root='/proc')`
- `split_windows_cmdline(cmdline)`
- `procs_from_cim_json(text)`
- `procs_windows()`
- `list_claude_procs()`
- `free_ram_mb()`
- `last_activity(path)`
- `find_by_id(roots, sid)`
- `newest_in_cwd(roots, cwd)`
- `hot_idle_scan(roots, now=None, procs=None, free_mb=_AUTO)`
- `release_path(row)`
- `advise(scan, min_idle=ADVISE_IDLE_MIN)`
- `write_advisory(adv, path=ADVISORY_PATH)`
- `fmt_advice(adv)`
- `check_thresholds(dup, stamp)`
- `fmt_dup(r)`
- `fmt_stampede(r)`
- `fmt_hot_idle(r)`
- `build_parser()`
- `main(argv=None)`
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Invariants that must never change: _(Owner-defined; fill in during planning.)_
- Hard rules specific to this module: _(Owner-defined; fill in during planning.)_
- What breaks downstream if violated: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
