# Agent Governance — Policy Templates

> Reference document. Loaded at FORENSIC tier or on explicit request.

## Basic Agent Policy (AGT PolicyEngine)

```python
from agent_governance_toolkit import PolicyEngine, CapabilityModel

engine = PolicyEngine(capabilities=CapabilityModel(
    allowed_tools=["web_search", "read_file", "write_file"],
    blocked_tools=["shell_exec", "delete_file", "network_raw"],
    max_iterations=50,
    total_cost_limit_usd=5.00,
    timeout_seconds=300
))

# Evaluate before every tool call
decision = engine.evaluate(agent_id="worker-1", action="tool_call", tool="web_search")
if not decision.allowed:
    log.warning(f"BLOCKED: {decision.denial_reason}")
```

## Multi-Agent Mesh Policy (AGT AgentMesh)

```python
from agent_governance_toolkit import AgentMesh, TrustPolicy

mesh = AgentMesh(trust_policy=TrustPolicy(
    min_trust_for_delegation=700,      # Only trusted+ agents can delegate
    require_mutual_auth=True,           # Ed25519 challenge-response
    max_delegation_depth=3,             # Prevent infinite delegation chains
    privilege_narrowing_only=True       # Delegatee gets fewer permissions, never more
))
```

## Production Agent Policy

```python
from agent_governance_toolkit import AgentRuntime, SREConfig

runtime = AgentRuntime(
    privilege_ring=2,                    # Ring 2 = standard operations
    sre=SREConfig(
        latency_slo_p99_ms=2000,        # 2s p99 latency target
        error_budget_percent=0.1,        # 99.9% success rate
        circuit_breaker_threshold=5,     # Open after 5 consecutive failures
        circuit_breaker_reset_seconds=60
    ),
    kill_switch=True,                    # Always enable
    saga_rollback=True                   # Auto-rollback on partial failure
)
```

## OWASP ASI Verification Checklist

| # | Risk | Verification | Command |
|---|------|-------------|---------|
| ASI-01 | Unrestricted Agency | Tool scope explicitly defined | `agt audit asi-01` |
| ASI-02 | Data Poisoning | Input validation on agent memory/context | `agt audit asi-02` |
| ASI-03 | Insecure Agent-Agent Comms | Mutual auth between agents | `agt audit asi-03` |
| ASI-04 | Supply Chain Vulnerabilities | Plugin signatures verified | `agt audit asi-04` |
| ASI-05 | Improper Output Handling | Output sanitization + saga rollback | `agt audit asi-05` |
| ASI-06 | Excessive Functionality | Minimal tool set assigned | `agt audit asi-06` |
| ASI-07 | Prompt Injection | Input filtering + trust scoring | `agt audit asi-07` |
| ASI-08 | Cascading Failures | Circuit breakers + error budgets | `agt audit asi-08` |
| ASI-09 | Insufficient Oversight | Human-in-the-loop for critical actions | `agt audit asi-09` |
| ASI-10 | Inadequate Logging | All agent actions logged with telemetry | `agt audit asi-10` |

## OPA/Rego Example

```rego
package agent.policy

default allow = false

allow {
    input.action == "tool_call"
    input.tool == data.allowed_tools[_]
    not input.tool == data.blocked_tools[_]
    input.trust_score >= 400
}

deny[msg] {
    input.action == "tool_call"
    input.tool == data.blocked_tools[_]
    msg := sprintf("Tool %v is blocked by policy", [input.tool])
}
```

## Cedar Example

```cedar
permit(
    principal in AgentGroup::"workers",
    action in [Action::"tool_call"],
    resource in ToolSet::"safe_tools"
) when {
    principal.trust_score >= 400 &&
    context.iteration_count < 50
};

forbid(
    principal,
    action in [Action::"tool_call"],
    resource in ToolSet::"dangerous_tools"
);
```
