# PP_AUDIT_REPORT — Global PARTIALLY_FUNCTIONAL Audit

Date: 2026-07-20 | Scope: FASE 0 (read-only) | Branch: main @ 4ae6e8a

## Method note (read this first)

Three of my own intermediate numbers were **false positives**, each caught by
re-verification. They are recorded here because the correction *is* the finding:

| Intermediate claim | Why it was wrong | Corrected |
|---|---|---|
| "74 orphan hooks" | Only checked `settings.json`; missed `hook-dispatcher.js` chains | 34 |
| "46 broken references" | I resolved the PP *mirror* dispatcher's relative paths against its mirror location; those paths are only valid when deployed to `~/.claude/hooks/` | 0 |
| "34 orphan hooks" | Missed `session_start_hub.js`, a **second** registered dispatcher, plus shared libraries required by other hooks | ~6 |

Lesson: PP has **three** registration surfaces, not one — `settings.json`,
`hook-dispatcher.js` chains, and `session_start_hub.js` fan-out. Any audit that
checks fewer than all three manufactures orphans.

## E. settings.json integrity — CLEAN

- 6 event groups, 32 command entries, 50 live-dispatcher chain refs.
- 67 distinct registered script paths. **Broken references: 0.**
- No entry points at a missing, moved, or renamed file.

## A. HOOKS — 99 on disk

- **REGISTERED (~93)** via one of the three surfaces above.
- **LIBRARY (not orphans)**: `_shared/hook-runtime.js`, `session-title-lib.js`,
  `async_wrapper.js` — required by other hooks, correctly never registered.
- **REACHABLE via second-order spawn**: `auto-compact-sendkeys-daemon.ps1`
  (spawned by the registered `auto-compact-stop-launcher.ps1`),
  `token-optimizer-bootstrap.js` + `memory-rotation.js` (invoked by
  `session-init.js`, itself in the dispatcher chain).

### PARTIALLY_FUNCTIONAL — built, has a registrar, never wired (the real finding)

These PP-side hooks exist, and `tools/register_global_hooks.py` **knows their
names**, but they appear in neither live `settings.json` nor either dispatcher:

| Hook | Registrar knows it | In live config |
|---|---|---|
| `hooks/cascade_check_bash.js` | yes (`register_global_hooks.py:30`) | **no** |
| `hooks/output_contract_stop.js` | yes (`:35`) | **no** |
| `hooks/ram-guard-stop.js` | no | **no** |
| `hooks/pm03_publish_stop.js` | no | **no** |
| `hooks/session_end_graceful_beacon.js` | no | **no** |
| `hooks/_oneshot_solitary_empty_shell_cleanup.js` | no | **no** (and drifted vs live copy) |

> **FASE 1 correction.** Reading each header before wiring demoted two of the
> six. `ram-guard-stop.js` declares itself *"SUPERSEDED / UNREGISTERED BY
> DESIGN"* (superseded by `modules/zero-crash/hooks/ram-watchdog.js`) — wiring
> it would be wrong. `_oneshot_solitary_empty_shell_cleanup.js` is a one-shot
> deployed via `install-global.ps1`, never a chain entry; its drift is a stale
> deployment, not an unwired hook. **Genuine candidates: 3, not 6.** Both
> demotions came from reading, not from any gate.
>
> Status after FASE 1: `output_contract_stop.js` **wired + proven** (5/5).
> `session_end_graceful_beacon.js` **proven, registration queued** (needs a
> `settings.json` SessionEnd entry — HR-001 forbids agent self-registration).
> `pm03_publish_stop.js` and `cascade_check_bash.js` deliberately **not wired**:
> unproven, and the latter is a *blocking* gate. See `vault/OWNER_QUEUE.md`.

`output_contract_stop.js` is the one that matters most. **Correction to my
first statement of this finding**: I wrote that wiring it restores
HR-OUTPUT-001/002/003. That was overstated. The hook is *advisory only* and
implements a marker scan for **HR-OUTPUT-001** alone. HR-OUTPUT-002
(`tests_passed=False`) and HR-OUTPUT-003 (`OQS < 70`) have **no runtime
enforcement surface at all** — they exist only as prose in CLAUDE.md. That is a
larger gap than the one I reported, and it is not closed by this fix.

**Second defect, found only by testing it before wiring** (2026-07-20): the hook
scanned `JSON.stringify(payload)`. The Stop payload carries `transcript_path` —
a *path*, never the turn's prose — so the scan matched nothing the harness ever
sends. Wiring it as-shipped would have installed a permanently-silent gate that
reports success forever. Proven empirically: realistic payload → silent;
synthetic payload with the marker inline → fires. This is the "zero cannot fall"
pattern: a gate bounded by an input it never receives.

**Generalized risk**: the other five unwired hooks have *also* never run in
production. Wiring them without first proving each one fires would propagate
this same class of silent-gate defect. Wire-then-verify is not optional here.

### DRIFT — canonical vs live (7 basenames, same name, different bytes)

`jobs-woz-gatekeeper.js`, `lazarus-livesnap.js`, `lazarus-stub-recover.js`,
`learning-sentinel.js`, `research-intent-detector.js`, `session-file-guard.js`
(all **registered** — so the live copy is what actually runs, and the PP
committed copy is not what is executing), plus
`_oneshot_solitary_empty_shell_cleanup.js` (unregistered).

## The structural finding (added FASE 1) — the gate cannot see hooks

`modules/liveness/reachability.py` enumerates `modules/**/*.py` as its
denominator. `hooks/*.js` appear only in `_SEED_GLOBS` / `_LIVE_SEED_GLOBS` —
as **sources** of reachability, never as **subjects** of it.

So an unregistered hook is not scored ORPHAN. It is **absent from the
denominator, and absence reads as health**. All six hooks above sat undetected
in the same run where the gate confidently reported 155 named orphan modules —
it looked maximally honest exactly where it was blind.

This is PR-COVERAGE-BY-CONSTRUCTION-001 turned on the auditor itself: the tool
built to catch unwired things had an unwired *class* outside its own
denominator. That blind spot is invisible by construction, because the
instrument is what you would use to find it.

**This, not the individual hooks, is the highest-value output of the audit.**
Sealed as `T-LIVENESS-DENOMINATOR-EXCLUDES-HOOKS-001`.

## B. MODULES — pre-measured, not a new finding

`modules/liveness/reachability.py` already scores this and exits 1:

```
modules: 284 | REACHABLE: 129 | ORPHAN: 155 | UNKNOWN: 0 | gate offenders: 7
```

This matches the standing debt already named in CLAUDE.md. **No new audit tool
should be built** — the instrument exists and is authoritative. The correct
FASE 1 action is to reduce the named set, not to re-measure it.

## C. TOOLS — test posture (RESOLVED in FASE 1, commit df5bb93)

`pytest tools/` died with `INTERNALERROR` (exit 3): four V-gate scripts called
`sys.exit()` at module level, killing the collector. Fixed by guarding those
exits under `__main__` **and** exposing a `test_gate()` assertion — without the
assertion pytest would have executed each gate as an import side effect and
reported green regardless of outcome, the same silent-success defect as the
hook above. Six further tests errored at setup on fixtures (`tmp`, `sample`)
that were never defined, so they had **never executed under pytest**; fixtures
added, guarded so standalone `main()` still works.

**38 → 156 tests collected, 156 passing.** PP now has one command that runs its
tool suite. Original finding retained below.

### Original finding (superseded)

- 89 `tools/test_*.py` + 22 `tools/verify_*.py`.
- **`pytest tools/` does not work**: collection dies with `INTERNALERROR`,
  exit 3, at `tools/test_compact_rescue.py:251` — the V-gate scripts call
  `sys.exit()` at import time, which kills pytest's collector.
- Only 38 of 89 `test_*.py` are pytest-collectable. The rest are standalone
  V-gate scripts (valid by PP doctrine, but invisible to any suite-wide run).
- Consequence: there is **no single command that runs PP's tests**. A green
  `pytest tests/ -q` (7 files) says nothing about the other 264 tools.

## D / F — not completed this pass

Skills wrapper-depth (D) and Liveness Ledger probe-verifiability (F) were not
audited; the hook/settings surface consumed the budget. Flagged honestly rather
than filled in with assumption.

## Most common failure pattern

Not "registration forgotten" in general — PP registers most things. The pattern is:

> **A registrar exists as a separate manual step.** `register_global_hooks.py`
> and `settings_merger.py` are tools someone must *choose to run*. Code that
> ships with "run the registrar later" is complete-looking and inert. The hook
> is written, committed, documented in CLAUDE.md as active — and never wired.

`mistake-ingest.js`, the exemplar in the original premise, is **already wired**
(PostToolUse `Write|Edit`). The live instance of the pattern today is
`output_contract_stop.js`.

## Proposed FASE 1 order (ROI-ranked, pending approval)

1. Wire `output_contract_stop.js` — restores HR-OUTPUT-001/002/003. 1 line + gate test.
2. Resolve the 6 drifted basenames — decide live-or-canonical per file, sync one way.
3. Wire or declare `cascade_check_bash.js`, `ram-guard-stop.js`, `pm03_publish_stop.js`,
   `session_end_graceful_beacon.js`.
4. Fix `pytest tools/` collection (guard the `sys.exit` under `__main__`).
5. Then, and only then, attack the 155-module named orphan set.
