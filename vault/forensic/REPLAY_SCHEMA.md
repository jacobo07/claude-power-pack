# Adversarial Replay Schema (CGAR-replay extension) — MC-OVO-106

**File location (per project):** `vault/audits/replay_log/*.jsonl`
**Consumer:** `tools/replay_harness.py` and `tools/forensic_probes.py cgar_check()`
**Goal:** prove the post-delta build behaves identically to the pre-delta build on real production inputs. Diff != 0 = caught regression *before* it shipped.

## Why this exists (and why it's separate from the cascade graph)

CGAR's blast-radius probe says "this delta touches a node with 200 transitive callers". Replay says "and here are 100 real production inputs that exercise that path; the post-delta output diffs from baseline on input #47". The first is structural risk; the second is empirical regression evidence. They're complementary; replay is the stronger evidence when both are configured.

## Format — JSONL, one event per line

Each event captures a single deterministic input the post-delta sandbox should be able to reproduce:

```json
{"iso_ts":"2026-04-26T14:00:00Z","event_id":"evt-001","input_kind":"http.request","input":{"method":"POST","path":"/api/v1/score","body":{"player":"x","score":1234}},"observed_output":{"status":200,"body":{"accepted":true,"new_rank":42}}}
{"iso_ts":"2026-04-26T14:00:01Z","event_id":"evt-002","input_kind":"command","input":{"argv":["score","calculate","--player","x","--bonus","100"]},"observed_output":{"exit":0,"stdout":"final=1334\n","stderr":""}}
```

## Required fields

| Field | Type | Meaning |
|-------|------|---------|
| `iso_ts` | string | ISO-8601 timestamp of when the event was observed in production |
| `event_id` | string | stable identifier; the harness uses this to correlate replay verdicts back to specific events |
| `input_kind` | string | type tag the project's shim dispatches on (`http.request`, `command`, `event.bus`, `db.query`, etc.) |
| `input` | object | opaque-to-the-harness input payload; the project's shim knows how to apply it |
| `observed_output` | object | what production actually produced when given `input`. The harness diffs the post-delta output against this. |

## Optional fields

- `tags` (object) — `{"endpoint": "/api/v1/score", "player_count": 47}` — used to filter event sets
- `severity_hint` — `low`/`medium`/`critical` — replay verdict is amplified for `critical` events (any diff = REJECT, not B)
- `replay_skip_reason` — if non-empty, the harness skips this event with the reason logged (use for non-deterministic events that shouldn't be replayed)

## How replay verdicts are produced

For each event:

1. Harness loads the event line.
2. Project's shim receives `input` + `input_kind` and returns `replayed_output`.
3. Harness diffs `observed_output` vs `replayed_output` using the project's diff strategy (default: deep-equal JSON).
4. Result one of:
   - `MATCH` — post-delta output matches observed
   - `DIFF` — post-delta output differs (capture the diff string)
   - `SHIM_ERROR` — shim raised; record the error
   - `SKIPPED` — `replay_skip_reason` non-empty

Aggregate verdict over all events:
- All `MATCH` (or all `MATCH`+`SKIPPED`) → `replay_verdict=clean` → CGAR blast-radius cap is relaxed by one tier (B → none, REJECT → B)
- Any `DIFF` → `replay_verdict=regressed` → verdict cap is **B** (REJECT for events with `severity_hint=critical`)
- Any `SHIM_ERROR` (>10% of events) → `replay_verdict=shim_unreliable` → cap **B** + advisory to fix the shim

## How a project opts in

1. **Capture events.** Write a small log producer that appends to `vault/audits/replay_log/<date>.jsonl` from production. Frequency is the project's choice — the harness uses the most recent N (default 100) per cycle.

2. **Provide a shim.** Create `tools/replay_shim.py` (or `.js`/`.go`/etc.) that exposes a single function:

   ```python
   # tools/replay_shim.py
   def apply(input_kind: str, input: dict) -> dict:
       """Run `input` against the post-delta build and return the output dict."""
       ...
   ```

   The shim is the project-specific bridge between an opaque event and the actual code path. For an HTTP server, it might use `requests.request()` against a local instance. For a CLI, it might `subprocess.run`. For an event bus, it might `bus.publish_and_collect`.

3. **Configure the harness.** Optional: `_audit_cache/replay_config.json`:

   ```json
   {
     "max_events": 100,
     "shim_path": "tools/replay_shim.py",
     "diff_strategy": "deep_equal",
     "critical_event_kinds": ["payment", "auth"],
     "skip_kinds": ["analytics.fire_and_forget"]
   }
   ```

   Defaults are sensible if file missing.

4. **Run it.** From OVO Phase B+ at FORENSIC tier:

   ```bash
   python tools/replay_harness.py --project . --json
   ```

## States — CONFIGURED / NOT_CONFIGURED

Same three-state contract as RLP/AFHL/CGAR:

| State | When | Effect |
|-------|------|--------|
| `CONFIGURED` + `replay_verdict=clean` | shim exists, log non-empty, all events match | relaxes blast-radius cap by one tier |
| `CONFIGURED` + `replay_verdict=regressed` | shim exists, log non-empty, ≥1 DIFF | cap **B** (REJECT for critical-tagged DIFFs) |
| `CONFIGURED` + `replay_verdict=shim_unreliable` | shim exists, log non-empty, >10% SHIM_ERROR | cap **B**; advisory to fix shim |
| `NOT_CONFIGURED` | log dir absent OR empty OR shim absent | advisory; **no cap, no PASS claim** |

The harness runs in `NOT_CONFIGURED` mode for the power-pack itself — it has no daemon, no event log, no shim. That's correct, not a defect.

## Self-test (no project dep)

The harness ships with a built-in self-test mode (`--self-test`) that:
- generates 3 synthetic events in a tmpdir
- uses an identity shim that returns the input as the output (so events deliberately MATCH)
- and one event with a corrupted observed_output (so it deliberately DIFFs)
- asserts the aggregate verdict is `regressed` with exactly 1 DIFF found

This proves the engine works end-to-end without requiring any consuming project to have set up a shim. Run after install to verify the harness is wired correctly.

## Non-goals (this MC)

- Adversarial mutation (fuzz the input, see if shim crashes) — separate MC after this lands. Out of scope here.
- Stateful replay (events that depend on each other in sequence) — first version replays each event independently; ordered replay is a config opt-in for v2.
- Network event capture (auto-record from production) — out of scope; project provides events however it likes.

## Why this stays out of CGAR_SCHEMA.md

CGAR_SCHEMA.md describes the cascade graph (static blast radius). Replay is the *behavioral* check that complements it. Keeping the schemas separate lets a project opt into one without the other.
