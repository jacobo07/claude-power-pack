# Agent Governance — Verification Commands

> Loaded during verification phase. Run these before claiming agent system is complete.

## Pre-Flight Checks

| Check | Command | Expected |
|-------|---------|----------|
| AGT installed | `pip show agent-governance-toolkit` | Version displayed |
| Policy valid | `agt policy validate <policy-file>` | 0 errors |
| Trust scores | `agt mesh trust-score <agent-id>` | Score 0-1000 |
| SLO dashboard | `agt sre dashboard --project <name>` | SLOs defined |
| OWASP ASI scan | `agt audit owasp-asi <project-dir>` | 0 CRITICAL |
| Kill switch test | `agt runtime kill-switch test <agent-id>` | Agent terminates |
| Ring audit | `agt runtime ring-audit <project-dir>` | No privilege escalation paths |
| Plugin verify | `agt marketplace verify <plugin>` | Signature valid |

## Fallback (AGT Not Installed)

If AGT SDK is not available, verify manually:

1. **Kill switches:** `grep -rn "max_iterations\|circuit_breaker\|cost_limit" <agent-dir>` — at least 1 per agent loop
2. **Tool scope:** `grep -rn "allowed_tools\|blocked_tools\|tool_whitelist" <agent-dir>` — explicit lists defined
3. **Trust/auth:** `grep -rn "verify\|authenticate\|trust_score\|Ed25519" <agent-dir>` — present in multi-agent code
4. **Timeouts:** `grep -rn "timeout\|max_time\|deadline" <agent-dir>` — no `:infinity` or missing timeouts
5. **Rollback:** `grep -rn "rollback\|compensate\|saga\|undo" <agent-dir>` — present in multi-step workflows
6. **Logging:** `grep -rn "log\.\|logger\.\|telemetry\|instrument" <agent-dir>` — agent actions logged

## Quality Gate Integration

Add to pre-output quality gates when building agent systems:

```
| Agent Systems | agt audit owasp-asi <dir> | 0 CRITICAL |
| Agent Policy  | agt policy validate <file> | Valid      |
| Kill Switches | grep max_iterations in agent loops | Present |
```
