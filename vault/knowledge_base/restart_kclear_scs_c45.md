# SCS C45 -- /restart + /kclear audited recursively to two-consecutive-zero

Sealed 2026-06-22. ULTRA 7-phase recursive deep audit ("ni las motas de polvo"):
forensic inventory -> Q&A -> revised plan -> oneshot-architect-auditor -> fix
injection -> 4 audit rounds (loop until two consecutive zero-finding rounds).

## Result

- **Round 1:** 7 findings (PF-1..PF-7). **Round 2:** 2 findings (R2-1, R2-2).
  **Round 3:** 0 in-scope. **Round 4:** 0 in-scope -> two consecutive zeros -> SEALED.
- Flow maps: `vault/audits/restart_flow_map.md` + `vault/audits/kclear_flow_map.md`.
- Permanent gate: `tools/test_restart_kclear.py` -> **RESTART_KCLEAR=14/14**, hermetic,
  stable x3. Baseline intact: `test_restart_and_lag.py` 15/15, `test_auto_reset.py` 8/8,
  `test_ram_optimization.py` 11/11.

## Findings + fixes

| ID | Finding | Fix |
|---|---|---|
| PF-1 | `restart-target.json` self-heal is dead (producer `Write-RestartTarget` removed 2026-05-24; consumer still registered) | Documented OBSOLETE-BY-DESIGN (UKDL T-RESTART-SELFHEAL-OBSOLETE-001). **Audit rejected reviving the producer** -- session_id is not preserved across resume (hub matches by cwd), so a revived producer would false-mismatch and spawn a spurious `lazarus-revive` on EVERY successful restart. Owner-side deregistration step documented (HR-001). |
| PF-2 | `restart-command-pane-eviction.md` prescribes the external-window design that was reverted 2026-05-31 | SUPERSEDED banner -> in-pane CONIN$ design + T-RESTART-001 |
| PF-3 | `ram-watchdog.js` fired at 1.5 GB (alert fatigue); the 20/28 GB recalibration reached only the orphan `ram_guard` | Raised `RSS_THRESHOLD_MB` 1500 -> 20480; documented metric caveat (tasklist private-WS summed != WorkingSet64) + context_monitor authoritative (UKDL T-RAM-DEDUP-001) |
| PF-4 | `ram-guard-stop.js` orphan (richer advisory never fires) | Header-deprecated as superseded-by `ram-watchdog.js`; documented stays-unregistered-by-design |
| PF-5 | `cpc_os/restart.py` (`restart_intent`) has no live caller | Documented intent-validation-library, inert-by-design (UKDL T-RESTART-INTENT-ORPHAN-001) |
| PF-6 | `/kclear` does not free RAM (it checkpoints; native `/clear` frees RAM) | Honest gate: checkpoint integrity + `/clear` suggestion; RAM-free attributed to `/clear` (UKDL T-KCLEAR-RAM-SEMANTICS-001). `V-KCLEAR-RAM-DROPS` rejected as theater. |
| PF-7 | UKDL/docstring describe `restart_resume.js` as standalone; it is folded into `session_start_hub.js` | Fold notes in UKDL T-RESTART-001 + the file docstring |
| R2-1 | `lazarus-janitor.js` is a THIRD dead reference to `restart-target.json` (round-1 undercount) | UKDL trap amended to map all three references |
| R2-2 | `compact_rescue.ps1` is a SECOND producer of `restart_pending.json` and wrote it with `Set-Content -Encoding UTF8` (BOM), violating the no-BOM contract | Switched to `[System.IO.File]::WriteAllText(..., UTF8Encoding($false))`; AST-parse clean; `V-MARKER-NOBOM-CONTRACT` gate |

## Empirical evidence

- `/restart` dry-run (`PP_RESTART_DRY_RUN=1`) on this host: located parent claude.exe
  (PID 32636, proving the shared-console CONIN$ architecture), wrote SID+flag+marker,
  and the dry-run guard correctly SKIPPED both `/exit` injection and the `Stop-Process`
  fallback -- this session survived. Artifacts cleaned; no live residue.
- `/kclear` checkpoint exercised hermetically (tmp root w/ `.claude` marker): handoff +
  insights written under tmp, real repo tree untouched.

## Deferred (out of scope, documented not fixed)

- `test_ram_optimization.py::V-RAM-PP-OVERHEAD` is a pre-existing NON-HERMETIC gate
  (measures live node+python working-set <= 300 MB); it flaked once (10/11) under
  concurrent subprocess load during the sweep, then returned to a stable 11/11 x3. It is
  in the adjacent RAM-optimization suite, NOT the /restart-/kclear surface, and was not
  introduced by this audit. Owner may de-flake (settle/retry or measure PP-only hooks).

## Owner-side activation steps (HR-001 -- documented, not auto-applied)

- Optional: deregister `restart-target-consumer.js` from `~/.claude/settings.json`
  SessionStart (the dead self-heal). Harmless ~3 ms no-op if left; `lazarus-janitor.js`
  Step-9 pruner can stay (would serve a future producer).
