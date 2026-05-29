# Cold Boot Evidence -- BL-HARDRULE-001 (PP Bug->HardRule + Cascade Guard)

Timestamp: 20260529T223712Z

## 1. test_hard_rules (14 V-gates)

```
     - CLAUDE.md     : C:\Users\User\AppData\Local\Temp\hr_bak_3s0til8b\CLAUDE.md
     - archive       : C:\Users\User\AppData\Local\Temp\hr_bak_3s0til8b\archive\HARD_RULES.md
     - CLAUDE.md.bak : C:\Users\User\AppData\Local\Temp\hr_bak_3s0til8b\CLAUDE.md.pre-hr-20260529T203712Z.bak
PASS  V-HR-WRITER-BACKUP               backup created: CLAUDE.md.pre-hr-20260529T203712Z.bak
[OK] hard rule HR-001 written
     - CLAUDE.md     : C:\Users\User\AppData\Local\Temp\hr_idem_t23g0vdv\CLAUDE.md
     - archive       : C:\Users\User\AppData\Local\Temp\hr_idem_t23g0vdv\archive\HARD_RULES.md
     - CLAUDE.md.bak : C:\Users\User\AppData\Local\Temp\hr_idem_t23g0vdv\CLAUDE.md.pre-hr-20260529T203712Z.bak
PASS  V-HR-WRITER-IDEMPOTENT           two writes -> same id=HR-001
PASS  V-HR-WRITER-SENTINEL             both sentinels present in CLAUDE.md
PASS  V-HR-LIST                        7 rules installed
PASS  V-HR-CLI-SCAN                    rc=0 with candidates header
PASS  V-HR-CLI-LIST                    rc=0 with list header
PASS  V-HR-CASCADE-MAP                 map has 0 pattern(s)
PASS  V-HR-CASCADE-SIGNAL              clean state -> None
PASS  V-HR-NEVER-AGAIN-AUTO            draft created: auto_2026-05-29T203713Z.md
PASS  V-HR-DISPATCHER                  cascade registered + dispatch -> 0 adv
PASS  V-BASELINE-INTACT                rc=0 last='[32m[32m[1m43 passed[0m[32m in 1.22s[0m[0m'

HARDRULES_PASS=14/14  threshold=14/14
```

## 2. verify_hard_rules probe

```
PASS  extractor          8 candidate(s)
PASS  writer             7 rules listed
PASS  cli                --list rc=0
PASS  cascade-signal     0 pattern(s)
PASS  dispatcher         pp-cascade-guard registered
PASS  agent-file         2943 bytes
PASS  archive-or-claude  sentinel block present

HARDRULES_PROBE=7/7
```

## 3. bug_to_hardrule --list

```
=== INSTALLED HARD RULES (7) ===

HR-001 -- Classifier Blocks Claudesettingsjson Commands In
  TRIGGER : Before writing any file under ~/.claude/ or any agent-owned global config
  STOP    : Ship the PP-internal half (hook script, command body); document the Owner-side registration step in the agent body. Do not advisory-tag the gap; document honestly per L no-classified-FAILs.
  EVIDENCE: [never_again] Classifier blocks ~/.claude/settings.json + commands/ in auto-mode

HR-002 -- Test Critical Bug For Auto-propose Pipeline
  TRIGGER : Test recognizer for pipeline
  STOP    : Run auto_HR-002 proposal drafting
  EVIDENCE: [never_again] TEST CRITICAL bug for auto-propose pipeline ZZZ

HR-003 -- Ukdl S 2026-05-26
  TRIGGER : Before: UKDL S+++ 2026-05-26
  STOP    : write body to file via Write tool, invoke `git commit -F file` (or `gh --body-file`, `mix run -f`, `node script.js`). Transversal across repos. Cross-ref: `vault/lessons/git-commit-heredoc-argv-repars
  EVIDENCE: [ukdl] UKDL S+++ 2026-05-26

HR-004 -- Osa Absorption Tco Context Fix
  TRIGGER : Before: OSA Absorption + TCO Context Fix UKDL (2026-05-28)
  STOP    : UKDL (2026-05-28) | UKDL-OSA-2026-05-28-L1 | Context-percent proxy MUST be MAX of recent calls' `input_tokens`, NOT cumulative SUM. The TIS log records every claude-CLI invocation; summing across them
```

## 4. pytest baseline + test_proactive_agents + test_hooks_registration

```
[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m                              [100%][0m
[32m[32m[1m43 passed[0m[32m in 1.19s[0m[0m

PASS  V-BASELINE-INTACT                rc=0 last='[32m[32m[1m43 passed[0m[32m in 1.16s[0m[0m'

PROACTIVE_PASS=16/16  threshold=16/16

PASS  V-BASELINE-INTACT                  rc=0 last='[32m[32m[1m43 passed[0m[32m in 1.11s[0m[0m'

HOOKS_REG_PASS=13/13  threshold=13/13
```
