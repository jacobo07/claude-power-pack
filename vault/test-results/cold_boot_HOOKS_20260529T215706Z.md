# Cold Boot Evidence -- BL-HOOKS-REG-001 (PP Hooks Registration)

Timestamp: 20260529T215706Z

## 1. test_hooks_registration (13 V-gates)
```
Already registered (5):
  [PreToolUse   ] uqf_pre_edit_gate
  [PostToolUse  ] osa_deploy_detector
  [PostToolUse  ] bug-hunter-ceps-bridge
  [SessionStart ] session-start-check
  [Stop         ] jobs_woz_gate

[OK] All 5 PP hooks already registered. Nothing to do.
PASS  V-HOOKS-SCRIPT-IDEMPOTENT          2x runs -> identical counts {'PreToolUse': 1, 'PostToolUse': 2, 'SessionStart': 1, 'Stop': 1}
PASS  V-HOOKS-CHECK-STATUS               rc=1 from cwd=C:\Users\User\AppData\Local\Temp\ppcheck_s26rb7hz
PASS  V-HOOKS-MARKER-PRE                 'uqf_pre_edit_gate' present in script
PASS  V-HOOKS-MARKER-POST-OSA            'osa_deploy_detector' present in script
PASS  V-HOOKS-MARKER-POST-CEPS           'bug-hunter-ceps-bridge' present in script
PASS  V-HOOKS-MARKER-SESSION             'session-start-check' present in script
PASS  V-HOOKS-MARKER-STOP                'jobs_woz_gate' present in script
PASS  V-HOOKS-FILES-EXIST                4/4 JS hooks present
PASS  V-HOOKS-DOCS-EXIST                 5000 bytes
PASS  V-BASELINE-INTACT                  rc=0 last='[32m[32m[1m43 passed[0m[32m in 1.11s[0m[0m'

HOOKS_REG_PASS=13/13  threshold=13/13
```

## 2. test_proactive_agents (16 V-gates, BL-PROACTIVE-001)
```
=== test_proactive_agents (BL-PROACTIVE-001) ===
  pp root     : C:\Users\User\.claude\skills\claude-power-pack
  throttle dir: C:\Users\User\.claude\skills\claude-power-pack\vault\pp_agents\throttle

PASS  V-PROACTIVE-CORE-FIRE            advisory len=38
PASS  V-PROACTIVE-CORE-THROTTLE        second call throttled within 15min cooldown
PASS  V-PROACTIVE-CORE-WEAK            weak signal (0.3) below threshold (0.9) -> None
PASS  V-SIGNAL-COST-LOW                pct=25 below 60 threshold -> silent
PASS  V-SIGNAL-COST-HIGH               pct=80 -> value=0.80
PASS  V-SIGNAL-CODE-CLEAN              clean code -> silent (implicit Jobs approval)
PASS  V-SIGNAL-CODE-DIRTY              value=0.50 advisory='2 instance(s) of 'missing type hints' in...'
PASS  V-SIGNAL-HEALTH-UP               status=UP -> silent (production healthy)
PASS  V-SIGNAL-HEALTH-DOWN             status=DOWN -> value=1.00
PASS  V-SIGNAL-ERRORS-NEW              novel error -> silent (learning opportunity)
PASS  V-SIGNAL-ERRORS-RECURRING        recurrence=3 -> value=0.60
PASS  V-DISPATCHER-CLEAN               clean context -> 0 advisories (silence is approval)
PASS  V-DISPATCHER-MAXTHREE            emitted 3 (cap=3)
PASS  V-JOBSWOZ-MEDIOCRE               advisory fired with 2 hit class(es)
PASS  V-JOBSWOZ-CLEAN                  clean output -> silent (no additionalContext)
PASS  V-BASELINE-INTACT                rc=0 last='[32m[32m[1m43 passed[0m[32m in 1.18s[0m[0m'

PROACTIVE_PASS=16/16  threshold=16/16
```

## 3. _hook_smoke (7 scenarios, empirical)
```
=== M5 hook smoke harness ===
  pp root      : C:\Users\User\.claude\skills\claude-power-pack
  hooks        : C:\Users\User\.claude\skills\claude-power-pack\hooks

PASS  H1-dirty       expected=advisory expected                rc=0
PASS  H1-clean       expected=silent expected                  rc=0
PASS  H2-deploy      expected=advisory expected                rc=0
PASS  H3-error       expected=advisory expected                rc=0
PASS  H4-session     expected=silent (pct < 70%)               rc=0
PASS  H5-slop        expected=advisory expected                rc=0
PASS  H5-clean       expected=silent expected                  rc=0

Evidence: C:\Users\User\.claude\skills\claude-power-pack\vault\test-results\hook_smoke_20260529T195716Z.md
SMOKE_PASS=7/7
```

## 4. pytest tests/ -q
```
[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m                              [100%][0m
[32m[32m[1m43 passed[0m[32m in 1.14s[0m[0m
```

## 5. verify_hooks_registration probe
```
============================================================
PP HOOKS REGISTRATION  --  ONE-TIME OWNER SETUP
============================================================
Repo  : C:\Users\User\.claude\skills\claude-power-pack
Target: C:\Users\User\AppData\Local\Temp\prob_reg_8a_qi8m5\settings.json
Mode  : DRY RUN (no changes)

To register (5):
  [PreToolUse   ] matcher=Write|Edit|MultiEdit
    -> node "C:\Users\User\.claude\skills\claude-power-pack/hooks/uqf_pre_edit_gate.js"
       (pp-code-reviewer + pp-uqf-auditor on .py writes)
  [PostToolUse  ] matcher=Bash
    -> node "C:\Users\User\.claude\skills\claude-power-pack/hooks/osa_deploy_detector.js"
       (OSA audit recommendation on deploy commands)
  [PostToolUse  ] matcher=Bash
    -> node "C:\Users\User\.claude\skills\claude-power-pack/hooks/bug-hunter-ceps-bridge.js"
       (pp-ceps-analyst auto-capture on Bash errors)
  [SessionStart ] matcher=*
    -> python "C:\Users\User\.claude\skills\claude-power-pack/tools/tco_compact_gate.py" --session-start-check
       (pp-tco-advisor warning when context_pct >= 70)
  [Stop         ] matcher=*
    -> node "C:\Users\User\.claude\skills\claude-power-pack/hooks/jobs_woz_gate.js"
       (Jobs/Woz advisory on assistant turn slop)

============================================================
DRY RUN COMPLETE -- settings.json untouched.
Re-run without --dry-run to commit.
PASS  reg-script         --dry-run rc=0 (8151B)
PASS  status-script      5 markers
PASS  hooks-on-disk      4/4 present
PASS  docs-present       5000 bytes
PASS  sscheck-flag       flag and handler both present
PASS  smoke-harness      9045 bytes
PASS  idempotency-mod    5 markers exact-match

HOOKS_REG_PROBE=7/7
```

## 6. check_hook_status (Owner view -- ACTION REQUIRED until Owner runs register)
```
============================================================
PP AGENT STATUS
============================================================
Settings: C:\Users\User\.claude\settings.json
PP root : C:\Users\User\.claude\skills\claude-power-pack

HOOKS (auto-fire when their event matches):
  [GAP] [PreToolUse   ] uqf_pre_edit_gate              -> pp-code-reviewer + pp-uqf-auditor on .py writes
  [GAP] [PostToolUse  ] osa_deploy_detector            -> omni-singularity on deploy command
  [GAP] [PostToolUse  ] bug-hunter-ceps-bridge         -> pp-ceps-analyst on Bash error
  [GAP] [SessionStart ] session-start-check            -> pp-tco-advisor at session start
  [GAP] [Stop         ] jobs_woz_gate                  -> Jobs/Woz judge on assistant turn

USER PROMPT SUBMIT (already active via jit_skill_loader):
  [OK] jit_skill_loader -> proactive dispatcher (every PP agent)

GLOBAL AGENTS (~/.claude/agents/):
  [OK] omni-singularity
  [OK] pp-ceps-analyst
  [OK] pp-code-reviewer
  [OK] pp-monitor
  [OK] pp-never-again
  [OK] pp-tco-advisor
  [OK] pp-uqf-auditor

LAST ADVISORIES FIRED (vault/pp_agents/throttle/):
  [2026-05-29T19:57:15] pp-ceps-analyst_bash-error           fired=  1  [Woz] [pp-ceps-analyst] Bash error captured to CEPS. Snippet: Traceback (most re
  [2026-05-29T19:57:14] omni-singularity_deploy              fired=  1  [Jobs] [omni-singularity] Deploy command detected: vercel deploy --prod. OSA rec
  [2026-05-29T13:49:06] smoke-test_smoke                     fired=  1  [Jobs] [smoke-test] Test advisory body -> Do X now

============================================================
[ACTION REQUIRED]
  -> cd ~/.claude/skills/claude-power-pack
  -> python tools/register_global_hooks.py
  -> close + reopen Claude Code, then re-run this script.
```
