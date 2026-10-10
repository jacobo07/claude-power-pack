# S4 receipt
Status: DONE

Commit: see `git log -1 --format=%h -- tools/programme_status.py` on feat/ucda.

- PROVEN (18/18 tools/test_programme_status.py): projection from chain.json + receipts + mission records + programme_spend + git HEAD: state, current unit, worker, last verified transition, spend settled/reserved/UNKNOWN/available, forecast (route target of current unit), blocker, next eligible transition (gsdx_chain.decide), debt, rendered HANDOFF block. Output size identical for 5 vs 5000 fake history missions; free text clipped. Unreadable live state or spend renders UNKNOWN, never armable/zero. Notification only for done / blocked / authority edge (held, arm refused, envelope refusal, telemetry failure), once per (event, unit).
- Live read-only run: state running S4, worker named, but spend = UNKNOWN (goal not readable from the local index in this run) -- reported honestly, not zero.
- NOT_PROVEN: spend values against the real goal ledger; the `--notify` state file in a scheduled task.
- Calls used: ~12.
- Next unit: status now comes from `python tools/programme_status.py [--json|--notify]`; it reuses gsdx_chain.decide, so any new chain action name must be added to BLOCKING/AUTHORITY in programme_status.py.
