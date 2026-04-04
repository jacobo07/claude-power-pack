# OmniCapture Engine — Core

> SLEEPY module. ~200 tokens. Zero cost when dormant.

## Activation Triggers

Keywords: "runtime telemetry", "check runtime", "omnicapture", "show errors", "what crashed", "show me runtime", "runtime check"

Auto-activated at DEEP+ tier when claiming completion AND project has OmniCapture configured.

## What It Does

Bridges the gap between "it compiles" and "it actually works" (Mistake #6 at application scale). Queries VPS-resident OmniCapture Receiver for real-time errors, crashes, performance metrics, and state dumps from running applications.

## Commands

| Action | Command |
|--------|---------|
| Query errors | `python modules/omnicapture/query_telemetry.py --project <name> --since 5m --severity ERROR` |
| Summary | `python modules/omnicapture/query_telemetry.py --project <name> --summary` |
| All crashes | `python modules/omnicapture/query_telemetry.py --project <name> --category crash` |
| Network failures | `python modules/omnicapture/query_telemetry.py --project <name> --category network` |
| Install adapter | `python modules/omnicapture/install_adapter.py --type python|minecraft|wii_cpp|react_native --project <name>` |

## Governance Integration

| Tier | Behavior |
|------|----------|
| LIGHT / STANDARD | Not consulted |
| DEEP | Consulted if configured. WARNING logged, does NOT block. |
| FORENSIC | Required if configured. ERROR+ BLOCKS completion claim. |

## Pre-Completion Gate (DEEP+)

Before claiming "done", "fixed", "ready", or "complete":
1. If OmniCapture configured for project: run `--summary`
2. If CRITICAL or FATAL events in last 5 min: **DO NOT** claim completion. Report errors first.
3. If no OmniCapture configured: note "Runtime telemetry not configured — static verification only" and proceed.

## Config

See `modules/omnicapture/config.json` for VPS endpoint, API keys, and project mapping.
