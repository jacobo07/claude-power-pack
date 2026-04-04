# PARTS O + P + S + V + X — INFRASTRUCTURE

## O: Cross-Repo Dispatcher
`claude-dispatch <repo> <prompt-file>` — dispatches to any repo on disk.

## P: Dynamic Daemon
`claude-daemon` — crash recovery loop, auto RAM allocation (25% system, 2-8GB).

## S: OmniCapture Engine
Runtime telemetry bridge. `python modules/omnicapture/query_telemetry.py --project <name> --summary`

## V: Agent Lightning
Trace collection + APO. `python modules/agent-lightning/query_lightning.py --suggestions`

## X: Kobii Infrastructure
VPS health queries. `python modules/infrastructure/query_infra.py --status`
