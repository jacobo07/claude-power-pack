# Runtime Liveness Probe (RLP) — schema

**File:** `_audit_cache/runtime_probe.jsonl` (per project, opt-in)
**Consumer:** `tools/forensic_probes.py rlp_check()`
**Goal:** distinguish "process running" from "process processing work at expected rate"

## Why this exists

A daemon that has open sockets and responds to TCP heartbeats but no longer drains its work queue is a **zombie**. Static OVO sees the source unchanged and grades A. RLP catches the failure mode that static analysis is structurally blind to: liveness ≠ healthy work-conservation.

## File format — JSONL, append-only

Each line is one probe sample. Most recent N lines (default 10) are read by the gate.

```json
{"iso_ts":"2026-04-25T18:00:00Z","probe_id":"server-tps","metric":"tps","value":19.8,"baseline":20.0,"unit":"ticks/sec","sample_window_s":10}
{"iso_ts":"2026-04-25T18:00:10Z","probe_id":"server-tps","metric":"tps","value":4.2,"baseline":20.0,"unit":"ticks/sec","sample_window_s":10}
{"iso_ts":"2026-04-25T18:00:00Z","probe_id":"queue-drain","metric":"work_conservation","value":0.97,"baseline":1.0,"unit":"ratio","sample_window_s":60}
```

## Required fields

| Field | Type | Meaning |
|-------|------|---------|
| `iso_ts` | string | ISO-8601 timestamp of sample |
| `probe_id` | string | stable identifier for the probe source |
| `metric` | string | what was measured (`tps`, `rps`, `rss_mb`, `p99_ms`, `work_conservation`, etc.) |
| `value` | number | observed value |
| `baseline` | number | expected value at healthy operation |
| `unit` | string | unit of value/baseline |
| `sample_window_s` | number | observation window in seconds |

## Optional fields

- `tags` (object) — free-form key/value for project-specific dimensions (`{"node":"vps-01","region":"eu"}`)
- `severity_hint` (string) — `info`/`warn`/`critical` if the producer knows
- `notes` (string) — short human note (rarely used)

## Health rules (default; configurable per project via `_audit_cache/rlp_thresholds.json`)

For each `(probe_id, metric)` pair:

| Trigger | Verdict cap |
|---------|-------------|
| `value < baseline * 0.10` (90% degradation) | **REJECT** — process is effectively dead |
| `value < baseline * 0.50` (50% degradation) | **B** — significant degradation |
| `value < baseline * 0.80` (20% degradation) | warning, no cap |
| `last 10 samples all degraded ≥20%` | **B** — sustained degradation, not transient |

For ratio metrics like `work_conservation` (processed ÷ enqueued over window), the inverted threshold applies: `value < 0.5` = REJECT, `value < 0.8` = B.

## States

- **CONFIGURED + clean**: file exists, last 10 samples all within healthy thresholds → no cap.
- **CONFIGURED + findings[]**: file exists, samples violate thresholds → findings emitted, cap per the table above.
- **NOT_CONFIGURED**: file does not exist → emitted as advisory in the Council block; no cap, but probe cannot affirm health. *This is the correct state for projects without a running daemon.*

## How a project opts in

1. Choose your liveness signal source (Mineflayer ping, HTTP /metrics endpoint, OmniCapture query, custom script).
2. Append samples to `_audit_cache/runtime_probe.jsonl` on a schedule (cron, systemd timer, or in-process emitter).
3. (Optional) Tune thresholds via `_audit_cache/rlp_thresholds.json` of shape `{"<probe_id>:<metric>": {"reject_below": 0.1, "b_below": 0.5, "warn_below": 0.8}}`.
4. From the next OVO audit forward, RLP is enforced.

## Example: KobiiCraft

```json
{"iso_ts":"2026-04-25T18:00:00Z","probe_id":"paper-tps","metric":"tps","value":19.85,"baseline":20.0,"unit":"ticks/sec","sample_window_s":60,"tags":{"world":"resort_main"}}
{"iso_ts":"2026-04-25T18:00:00Z","probe_id":"paper-mspt","metric":"p99_ms","value":42.1,"baseline":50.0,"unit":"ms","sample_window_s":60}
```

`p99_ms` baseline is the *acceptable ceiling*; for ceiling metrics, the rule inverts: `value > baseline * 1.5` triggers B, `value > baseline * 2.0` triggers REJECT. The probe library handles direction inference from metric naming or explicit `direction: "lower_is_better"` in thresholds.

## Non-goals

- RLP does NOT collect samples — that's the project's responsibility.
- RLP does NOT alert/page — the verdict cap is the only enforcement signal.
- RLP does NOT replace OmniCapture or Grafana — it's the OVO-readable hand-off file.
