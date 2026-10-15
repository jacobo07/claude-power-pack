# Requirements: CCR v5 Stage A

Source: `vault/plans/ccr-v5-vehicle-repair-2026-10-15.md`.

- REQ-A1 A phase cannot exceed its hard lease regardless of model prose; ambiguous accounting blocks (Phase 1).
- REQ-A2 Subagents are capped per type; past the cap their tool calls are denied (Phase 1).
- REQ-A3 Every stopped worker session is booked exactly once with mission/epoch identity (Phase 2).
- REQ-A4 Estimates and authority are derived, never chosen; authority above the lease remainder is refused (Phase 2).
- REQ-A5 A unit DONE never closes a mission whose composition contract is unmet (Phase 3).
- REQ-A6 Missions armed in a new worktree do not stall on MCP approval, without crossing repository identity (Phase 3).
- REQ-A7 A real canary stays within cap + one sweep; Stage B gets a measured reforecast (Phase 4).
- REQ-A8 Confirmed and falsified failure classes recorded in UKDL/KV (Phase 5).
