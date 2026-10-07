# Phase 1 -- API coverage

No external API integration: Phase 1 changes one line of the in-repo gate supervisor (`modules/gsd_x/goal/providers/gate.py`), adds two local stdlib-only measurement tools under `tools/`, freezes the liveness registry and writes phase evidence; no network service, SDK, provider account or third-party API is called, and the claude/codex/long_run provider suites are run only after their fakes/sandboxes are confirmed by reading (else recorded UNKNOWN, never run against a real account).
