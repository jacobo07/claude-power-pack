# PART W — AGENT GOVERNANCE TOOLKIT BRIDGE

Microsoft AGT integration for AI agent systems. Maps programmatic enforcement to reasoning-time governance.

| AGT Layer | CPP Integration |
|-----------|----------------|
| PolicyEngine | Pre-task: scaffold policy file |
| AgentMesh (trust 0-1000) | During-task: verify trust per call |
| AgentRuntime (Ring 0-3) | Route: map Ring to tier |
| AgentSRE (SLOs) | Pre-output: verify SLO compliance |
| OWASP ASI (10 risks) | Pre-output: 10-risk scan |

Install: `pip install agent-governance-toolkit[full]`
