# PRD (Tier 1 -- Standard Task) -- `tools/ccn_census.py`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

> CCN census: does running sessions concurrently cost more than running them in turn?

**Files:** 1  ·  **LOC:** 601  ·  **Public symbols:** 34

### Public interface
- `default_roots()` (function, `tools/ccn_census.py`)
- `parse_ts(ts)` (function, `tools/ccn_census.py`)
- `main_transcripts(roots, cut)` (function, `tools/ccn_census.py`)
- `records(path)` (function, `tools/ccn_census.py`)
- `tool_key(name, inp)` (function, `tools/ccn_census.py`)
- `collect_tool_events(roots, hours, now)` (function, `tools/ccn_census.py`)
- `dup_scan(roots, hours=168.0, now=None, window_s=WINDOW_S)` (function, `tools/ccn_census.py`)
- `first_call_rows(roots, days, now)` (function, `tools/ccn_census.py`)
- `stampede_scan(roots, days=7.0, now=None, concurrent_s=CONCURRENT_S)` (function, `tools/ccn_census.py`)
- `encode_cwd(cwd)` (function, `tools/ccn_census.py`)
- `argv_session_id(argv)` (function, `tools/ccn_census.py`)
- `is_claude_argv(argv)` (function, `tools/ccn_census.py`)
- `classify_role(argv)` (function, `tools/ccn_census.py`)
- `proc_record(pid, ppid, argv, cwd, rss_mb)` (function, `tools/ccn_census.py`)
- `procs_linux(proc_root='/proc')` (function, `tools/ccn_census.py`)
- `split_windows_cmdline(cmdline)` (function, `tools/ccn_census.py`)
- `procs_from_cim_json(text)` (function, `tools/ccn_census.py`)
- `procs_windows()` (function, `tools/ccn_census.py`)
- `list_claude_procs()` (function, `tools/ccn_census.py`)
- `free_ram_mb()` (function, `tools/ccn_census.py`)
- `last_activity(path)` (function, `tools/ccn_census.py`)
- `find_by_id(roots, sid)` (function, `tools/ccn_census.py`)
- `newest_in_cwd(roots, cwd)` (function, `tools/ccn_census.py`)
- `hot_idle_scan(roots, now=None, procs=None, free_mb=_AUTO)` (function, `tools/ccn_census.py`)
- `release_path(row)` (function, `tools/ccn_census.py`)
- `advise(scan, min_idle=ADVISE_IDLE_MIN)` (function, `tools/ccn_census.py`)
- `write_advisory(adv, path=ADVISORY_PATH)` (function, `tools/ccn_census.py`)
- `fmt_advice(adv)` (function, `tools/ccn_census.py`)
- `check_thresholds(dup, stamp)` (function, `tools/ccn_census.py`)
- `fmt_dup(r)` (function, `tools/ccn_census.py`)
- `fmt_stampede(r)` (function, `tools/ccn_census.py`)
- `fmt_hot_idle(r)` (function, `tools/ccn_census.py`)
- `build_parser()` (function, `tools/ccn_census.py`)
- `main(argv=None)` (function, `tools/ccn_census.py`)

### Dependencies
`argparse`, `bisect`, `calendar`, `collections`, `glob`, `json`, `os`, `platform`, `re`, `statistics`, `subprocess`, `sys`, `time`
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Brief: _(Owner-defined; fill in during planning.)_
- Acceptance criteria: _(Owner-defined; fill in during planning.)_
- Impact map: _(Owner-defined; fill in during planning.)_
- Test plan: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
