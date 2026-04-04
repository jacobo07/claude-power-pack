# Overlay: Agent Governance

- **Policy-First:** Define `allowed_tools` and `blocked_tools` BEFORE writing agent logic. Default = deny all.
- **Trust Boundaries:** Every agent-to-agent call must declare trust level. Use AGT AgentMesh for Ed25519 identity.
- **Privilege Rings:** Map agent capabilities to Ring 0-3 (Ring 3 = least privilege). Delegation chains must narrow, never widen.
- **Kill Switches:** Every agent loop MUST have `max_iterations`, `total_cost_limit`, and a circuit breaker. No unbounded loops.
- **Identity:** Production agents require cryptographic credentials (Ed25519 or SPIFFE/SVID). No anonymous agents in production.
- **SLOs:** Define latency, error-rate, and cost SLOs BEFORE deploying any agent system. Use AGT AgentSRE for monitoring.
- **Adversarial Testing:** Test with prompt injection, tool abuse, and privilege escalation attempts before deployment.
- **OWASP ASI:** Run the 10-risk checklist (`agt audit owasp-asi`) before any agent goes to production.
- **Framework Detection:** Detect framework from imports; apply AGT adapter for LangChain, CrewAI, AutoGen, Claude Agent SDK, etc.
- **Observability:** Instrument every agent action with structured telemetry: agent_id, action, tool, latency_ms, outcome, trust_score.
- **Saga Pattern:** Multi-step agent workflows MUST have rollback/compensation on partial failure. Use AGT saga orchestration.
- **Plugin Security:** Third-party agent tools require cryptographic signature verification before installation.
