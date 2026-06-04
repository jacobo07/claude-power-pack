# SessionStart Hub Fold -- BL-SESSION-FOLD-001 (2026-06-04)

Extends the hook-hub fold sprint to the SessionStart event. Reduces the
SessionStart spawn count by folding fire-and-forget hooks into
`hooks/session_start_hub.js` (SCS C23 Session-Hub-by-default).

## Inventory (11 entries, all read/grep-classified)

| hook | ms | class | action |
|---|---|---|---|
| token-shield-refresh.js | 44 | stdout-consumed | KEEP standalone |
| terminal-slot-recorder.js | 4567 | Lazarus registry + stdin-coupled | KEEP standalone |
| learning-sentinel.js | 63 | stdout-consumed | KEEP standalone |
| lazarus-livesnap.js | 50 | load-bearing recovery | KEEP standalone |
| restart-target-consumer.js | 84 | stdout-consumed (resume ctx) | KEEP standalone |
| lazarus-stub-recover.js | 854 | load-bearing recovery | KEEP standalone |
| lazarus-index-aggregator.js | 11298 | load-bearing recovery | KEEP standalone |
| **mark-live-session.js** | 263 | **fire-and-forget** | **FOLD** |
| **zero-command-bootstrap.js** | 50 | **fire-and-forget** | **FOLD** |
| **first-time-project.js** | 49 | **fire-and-forget** | **FOLD** |
| session_start_hub.js | 108 | the hub | (target) |

Result: **11 -> 8** SessionStart spawns once migration applied.

## Why only these three

Only fire-and-forget hooks (side-effect only, silence on stdout) are safe to
detach into the hub. The task's own rule: stdout-consumed hooks and
load-bearing recovery hooks (lazarus-*, restart-*) stay standalone. The two
multi-second hooks (lazarus-index-aggregator 11s, terminal-slot-recorder 4.5s)
are the biggest wall-time cost but are off-limits -- they are recovery
substrate. So this fold buys spawn-count (3 fewer cold starts), not the
multi-second wall-time collapse.

## Mechanism: env-payload detached spawn

The folded hooks are stdin-payload-coupled -- they need `cwd`/`session_id` from
the SessionStart event. A detached child gets no stdin, so the hub passes the
payload via env (`PP_EVT_CWD` / `PP_EVT_SID`), the same pattern the hub already
uses for `cpc_register` / `jit_warm`. Each hook reads env as a fallback when
its own stdin is empty:

```js
const cwd = (event && event.cwd) || process.env.PP_EVT_CWD;
```

The standalone settings.json entry still feeds stdin until migration, so the
double-run window is benign (all three hooks are idempotent: append-only or
marker-gated).

## Premise correction (vs the task as written)

`migrate_hub_fold.py` CANNOT do this leg -- it folds Stop / UserPromptSubmit /
PostToolUse into `hook-dispatcher.js` CHAIN_MAP and its docstring explicitly
leaves SessionStart byte-untouched. SessionStart uses the hub mechanism, a
different model. The dedicated migration is `tools/migrate_sessionstart_fold.py`
(idempotent, dry-run default, backup-first, hub-reachability guard). It does not
collide with the sibling pane's `migrate_hub_fold.py`.

## Owner --apply step (HR-001: settings.json write is Owner-side)

```
python tools/migrate_sessionstart_fold.py            # dry-run: 11 -> 8
python tools/migrate_sessionstart_fold.py --apply     # backup + write
/restart                                              # reload settings.json
python tools/measure_hook_event.py --event SessionStart   # confirm AFTER=8
```

Verify idempotency: a second `--apply` reports "Nothing to migrate" (no write).

## Verification done

- Hub spawns all 3 (`SPAWNED mark_live_session/zero_command_bootstrap/
  first_time_project`, hub DONE 81ms, valid `{"continue":true}` stdout).
- Env-payload path does real work: `zero-command-bootstrap` with empty stdin +
  `PP_EVT_CWD` wrote `constitution.md` + `.pp-onboarded`.
- Migration dry-run: 11 -> 8, removes exactly the 3, reachability-proven.
- `test_hook_hubs` 7/7; all 4 edited files PP-only (zero mirror drift).

## SCS C38 -- SessionStart-fold

Fire-and-forget SessionStart hooks fold into `session_start_hub.js` via the
env-payload detached pattern; stdout-consumed and load-bearing-recovery hooks
stay standalone. The settings.json removal is the Owner `--apply` step via
`migrate_sessionstart_fold.py` (HR-001). measured BEFORE=11; AFTER=8 post-apply.
