# Cold Boot Evidence -- BL-PROACTIVE-001 (PP Agents Proactive Mode)

Timestamp: 20260529T160139Z

## 1. test_proactive_agents (16 V-gates)

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
PASS  V-BASELINE-INTACT                rc=0 last='[32m[32m[1m43 passed[0m[32m in 1.22s[0m[0m'

PROACTIVE_PASS=16/16  threshold=16/16
```

## 2. test_globalization (15 V-gates, BL-GLOB-001)

```
=== test_globalization (BL-GLOB-001) ===
  agents dir : C:\Users\User\.claude\agents
  rules dir  : C:\Users\User\.claude\rules
  pp root    : C:\Users\User\.claude\skills\claude-power-pack

PASS  V-GLOB-AGENT-COUNT                   7 PP agents present
PASS  V-GLOB-AGENT-SCHEMA                  all 7 agents have name/description/tools, no forbidden YAML keys
PASS  V-GLOB-AGENT-CODEREV                 pp-code-reviewer.md doctrine present
PASS  V-GLOB-AGENT-MONITOR                 pp-monitor.md observability protocol present
PASS  V-GLOB-AGENT-UQF                     pp-uqf-auditor.md scan + principles present
PASS  V-GLOB-AGENT-TCO                     pp-tco-advisor.md cost-projection + /compact present
PASS  V-GLOB-AGENT-CEPS                    pp-ceps-analyst.md NEVER_AGAIN + taxonomy present
PASS  V-GLOB-AGENT-NEVER                   pp-never-again.md inject + top_recurring present
PASS  V-GLOB-RULES-COMMON                  ~/.claude/rules/common/code-review.md (1772 bytes)
PASS  V-GLOB-RULES-PYTHON                  ~/.claude/rules/python/testing.md (2516 bytes)
PASS  V-GLOB-UQF-IMPORTABLE                UQFAuditor score=100.0%
PASS  V-GLOB-OSA-DISPATCHER                project='claude-power-pack' reason=T4_SESSION_TIMER
PASS  V-GLOB-TCO-PROXY                     MAX-of-recent proxy = 10000 for 3x10k input (not 30k)
PASS  V-GLOB-NEVER-AGAIN-INJECTABLE        top_recurring=3 query=BL-GLOB-001 matches=1
PASS  V-BASELINE-INTACT                    rc=0 last='[32m[32m[1m43 passed[0m[32m in 0.98s[0m[0m'

GLOB_PASS=15/15  threshold=14/14

Documented out-of-scope (classifier-blocked, Owner-side):
  - ~/.claude/commands/uqf-audit.md
  - ~/.claude/commands/code-review.md
  - ~/.claude/settings.json hook registration (uqf_pre_edit_gate, osa_deploy_detector, ceps-bridge)
  - ~/.claude/CLAUDE.md PP-tools section (QW-A)
```

## 3. pytest tests/ -q

```
[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m                              [100%][0m
[32m[32m[1m43 passed[0m[32m in 0.94s[0m[0m
```

## 4. verify_proactive_agents probe

```
PASS  core-import        cap=3
PASS  dispatch-clean     0 advisor(ies) (0 expected)
PASS  hook-present       4345 bytes
PASS  throttle-dir       C:\Users\User\.claude\skills\claude-power-pack\vault\pp_agents\throttle
PASS  agents-proactive   7/7 carry PROACTIVE MODE section
PASS  decorator-wired    def + @stack both present

PROACTIVE_PROBE=6/6
```
