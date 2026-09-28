---
phase: 04-prefix-cache-miss-a-b
verified: 2026-09-28T14:50:58Z
status: passed
score: 6/6 must-haves verified
covered_files:
  - .planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/04-01-PLAN.md
  - .planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/04-01-SUMMARY.md
  - .planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/EVIDENCE.md
  - .planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/ab_runner.py
  - .planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/raw/ab-live.json
  - .planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/raw/claude-help.txt
  - .planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/raw/static-excerpts.txt
  - .planning/workstreams/cognitive-resource-os/REQUIREMENTS.md
covered_digest: "v1:sha256:3d35faa6c930b54649616cf20103d90c85827e0ff5a187339441adbfa8b79794"
behavior_unverified: 0
overrides_applied: 0
---

# Phase 04: Prefix cache-miss A/B Verification Report

**Phase Goal:** Test the unmeasured hypothesis that a new session misses the previous session's cached prefix because the tool list varies with MCP.
**Verified:** 2026-09-28T14:50:58Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | EVIDENCE section 0 records the pre-check before any run (no API key, claudeAiOauth, credential file stat-only) | VERIFIED | `EVIDENCE.md` §0: `ANTHROPIC_API_KEY: UNSET`, `anthropic_env_names: none`, `blocking_env_names: none`, `auth_method: claude.ai`, `auth_api_key_source: ABSENT`, `auth_subscription_type: max`, `credentials_type: claudeAiOauth`, `credentials_file: stat only ... never opened`. `precheck: PASS`. `credentials_evidence` cites `auth status --json` under the runs' own scrubbed env, grounded by byte-verified excerpts X01/X02 |
| 2 | Pre-registration committed in EVIDENCE §1 before the live invocation; runner refuses unless its own sha256/fingerprint match | VERIFIED | Independently confirmed: pre-registration commit `740b41b` committer time `2026-09-28T16:40:50+02:00` = `14:40:50Z`, which is **before** `live_window_utc` start `14:41:42Z`. `git merge-base --is-ancestor 740b41b HEAD` → rc=0. `git diff --stat 740b41b..HEAD -- ab_runner.py` is empty (no post-registration change). Current `--fingerprint` output (`runner_sha256=9414fd25...`, `rules_fingerprint=ab6454cd...`) matches EVIDENCE §1 byte-for-byte. Guard G6 (`REFUSED: G6 runner_sha256 or rules_fingerprint mismatch`) is present in `ab_runner.py` and exercised by selftest cases S12/G6 |
| 3 | Exactly 4 `claude -p` launches in order A1 A2 B1 B2, Arm B via `--strict-mcp-config --mcp-config` on an empty MCP config file, each identified by pre-assigned `--session-id` | VERIFIED | `raw/ab-live.json`: `launches: 4`, runs array in order A1,A2,B1,B2. `/tmp/claude-1000/cro-p04-ab/work/live.log`: exactly 4 `LAUNCH` lines + 1 `LIVE_DONE`. B1/B2 `argv_display` carries `--strict-mcp-config --mcp-config /tmp/claude-1000/cro-p04-ab/empty-mcp.json`; file content is literally `{"mcpServers": {}}`. Each of the 4 session ids resolves to **exactly one** `<id>.jsonl` under `~/.claude/projects/*/` (independently globbed — see Requirements Coverage below); the two project dirs (`...-armA`, `...-armB`) contain exactly 2 transcripts each, no extras |
| 4 | Per-run first-call cache figures read from that run's transcript via `tools/tis_observed.py`, never CLI stdout; `--readout` re-derives to MATCH; `tis_observed`'s own CLI reproduces the same figures | VERIFIED | `ab_runner.py --readout raw/ab-live.json` → `READOUT: MATCH` (re-run independently in this verification). `tools/tis_observed.py --project-dir .../armA --project-dir .../armB --sessions` independently reproduces, per session id: A1 context=29205/cache_read=13689, A2 context=29205/cache_read=29195, B1 context=27627/cache_read=13689, B2 context=27627/cache_read=27617 — all four match `EVIDENCE.md` §2 and `raw/ab-live.json` exactly |
| 5 | Run-2 vs run-1 reuse compared across arms (s_A1/A2/B1/B2, deltas, gap_run2, delta_gap), plus TTL/M1/M2/vA | VERIFIED | Independently recomputed s_A1=0.468721, s_A2=0.999658, s_B1=0.495494, s_B2=0.999638 from the raw token counts above; delta_A=0.530937, delta_B=0.504144, gap_run2=-2e-05, delta_gap=-0.026793 (rounding shares to 6dp before differencing, per the recorded metric definition) — all match `EVIDENCE.md` §3 and `raw/ab-live.json.metrics` exactly. M1=PASS, M2=PASS, vA=NO all cross-checked against the recorded init tool lists (A1/A2 identical `tools_sha256` and `mcp_servers`; B1/B2 empty `mcp_servers`, 0 `mcp__` tools) |
| 6 | Verdict line exactly SUPPORTED/REFUTED(sub-case)/UNJUDGED(why), recomputable from the pre-registered rule (committed before the live window per git log); n=2 stated as limit; every per-run figure labeled (GEX44) | VERIFIED | Independently re-derived the verdict from the pre-registered R1-R8 rule text (copied from EVIDENCE §1, itself an ancestor commit of the live-window commit) against the recomputed gap_run2/s_B2/vA: falls through R2-R7 (all pass their gates: 4 valid runs, M1/M2 PASS) to R8's first matching case `abs(gap_run2) < GAP_NULL` → **similar-reuse-variance-not-observed** — matches `EVIDENCE.md` `verdict: UNJUDGED (similar-reuse-variance-not-observed)` / `rule_fired: R8` exactly. `n_limit:` present verbatim. All A1-B2 per-run lines in EVIDENCE.md end `(GEX44)` |

**Score:** 6/6 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `ab_runner.py` | Read-only evidence runner, `def rules_fingerprint` | VERIFIED | Exists, 14/14 selftest passes on re-run in this verification; `--fingerprint` output matches committed EVIDENCE §1; G1-G8 guards present and behaviorally tested (S12) |
| `EVIDENCE.md` | Sections 0-4, `## 1. Pre-registration` present | VERIFIED | All 5 sections present with the exact content cross-checked above |
| `raw/ab-live.json` | `"schema": "cro-p04-ab/1"`, no reply text | VERIFIED | Present, schema matches; `complete: true`; no `result`/`text`/`content`/`message`/`stdout`/`email`/`orgId`/`orgName` key found via independent JSON-key walk |
| `raw/static-excerpts.txt` | X01-X05 headers | VERIFIED | Present, 5 headers X01-X05, each a byte-verified substring of the sha-pinned binary (checked by the plan's own third automated check, re-run clean) |
| `raw/claude-help.txt` | `--strict-mcp-config` present | VERIFIED | Present; all 8 required flags found; `--max-turns` absent (0 matches), consistent with EVIDENCE's `max_turns_flag: ABSENT` claim |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `ab_runner.py` | `tools/tis_observed.py` | lazy import `_ensure_tools_importable()` | WIRED | `read_run()`/`assemble()` call `T.read_session`/`T.iter_calls`; independently re-running `tools/tis_observed.py --sessions` on the two project dirs reproduces identical first-call figures |
| `ab_runner.py live()` | installed claude (sha256-pinned) | subprocess argv, scrubbed env | WIRED | `raw/ab-live.json.claude` records the exact resolved path/sha/version; matches `EVIDENCE.md` §0 `claude_resolved`/`binary_sha256` |
| EVIDENCE §1 (sha, fingerprint) | `live()` guard G6 | `--expect-runner-sha256`/`--expect-rules-fingerprint` | WIRED | Guard code present (`REFUSED: G6 ...`) and exercised in selftest; live values in `raw/ab-live.json` (`runner_sha256_at_run`, `rules_fingerprint_at_run`) equal the pre-registration commit's values |
| run session id | transcript file | `locate_transcript()` exact glob, 1 match required | WIRED | Independently globbed `~/.claude/projects/*/<id>.jsonl` for all 4 ids — exactly one match each, matching the recorded `path_rel`/`matches: 1` |
| `raw/ab-live.json` | EVIDENCE §2-4 | `--evidence-lines` verbatim paste | WIRED | Every per-run numeric line in EVIDENCE §2/3 matches the corresponding `raw/ab-live.json` field exactly (spot-checked all 4 runs' first-call fields, reuse_share, metrics, verdict) |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `EVIDENCE.md` §2/§3 numeric lines | first-call token counts, reuse shares | `tis_observed.read_session`/`iter_calls` over real `.jsonl` transcripts written by 4 real `claude -p` subprocess launches | Yes — independently re-read from the transcripts on disk, not from any static fallback | FLOWING |
| `raw/ab-live.json.verdict` | verdict label/reason/rule_fired | `verdict()` function applied to the real `metrics`/`manipulation`/`validity` computed from the 4 real runs | Yes — recomputed the same label from raw numbers independently | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Selftest re-runs green at current HEAD | `ab_runner.py --selftest` | `ABRUN_SELFTEST_PASS=14/14 threshold=14/14` | PASS |
| Readout re-derives from real transcripts | `ab_runner.py --readout raw/ab-live.json` | `READOUT: MATCH` | PASS |
| Fingerprint stable since pre-registration | `ab_runner.py --fingerprint` | matches EVIDENCE §1 verbatim | PASS |
| `tis_observed` CLI cross-check | `tools/tis_observed.py --project-dir ... --sessions` | reproduces all 4 runs' `first_call_context`/`first_call_cache_read` exactly | PASS |
| 4 model calls, no more, no fewer | glob `~/.claude/projects/*/<sid>.jsonl` for all 4 ids + directory listing | 1 match per id; 2 transcripts per project dir, no extras | PASS |

### Probe Execution

Not applicable — this phase's verification IS the probe (`ab_runner.py --readout`/`--selftest`/`--fingerprint`), executed above under Behavioral Spot-Checks rather than a separate `scripts/*/tests/probe-*.sh`.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CRO-04 | 04-01-PLAN.md | The cross-session prefix cache-miss hypothesis (MCP tool-list variance) is tested on subscription quota and judged | SATISFIED | 4 real runs launched and judged; `cro04: SATISFIED` in EVIDENCE §4, independently confirmed launches=4, complete=true, verdict correctly re-derivable (R8, UNJUDGED). `REQUIREMENTS.md` marks CRO-04 `[x]` Complete, mapped to Phase 4 only — no orphaned requirement IDs for this phase |

### ROADMAP Success Criteria (Phase 4)

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Pre-check recorded: no ANTHROPIC_API_KEY; credentials claudeAiOauth; otherwise BLOCKED | VERIFIED | EVIDENCE §0, cross-checked above |
| 2 | Arm A: 2 back-to-back runs, one scratch dir, identical short prompt; Arm B: same + `--strict-mcp-config` + empty MCP config; exactly 4 runs; cheapest model; output discarded | VERIFIED | 4 launches confirmed via live.log + raw/ab-live.json; argv_A/argv_B differ only by the 3 trailing MCP elements; model=haiku (cheapest, X05); no reply text stored anywhere (JSON-key scan clean) |
| 3 | Per-run `cache_read_input_tokens`/`cache_creation_input_tokens` read from transcript via tis_observed (not CLI stdout); run-2 vs run-1 compared across arms | VERIFIED | Independently re-read via `tis_observed.py --sessions`; matches EVIDENCE exactly; §3 comparison present |
| 4 | Verdict SUPPORTED/REFUTED/UNJUDGED with why; n=2 per arm stated as limit, not hidden | VERIFIED | `verdict: UNJUDGED (similar-reuse-variance-not-observed)`, `rule_fired: R8`, `n_limit:` full canonical statement present in EVIDENCE §4 |

### Anti-Patterns Found

None. Grep for `TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER` across `ab_runner.py` and `EVIDENCE.md` returned no matches. Leak scan (credential shapes, email pattern, `-home-kobii` path fragment, `.credentials.json` reference in the runner) returned clean across all 8 committed phase files.

### Honesty / Overclaiming Review (adversarial, per task instructions)

- **UNJUDGED wording**: honest. `vA: NO` (Arm A's MCP tool list and server-status map were byte-identical between A1 and A2 — independently confirmed by comparing `tools_sha256` and `mcp_servers` in `raw/ab-live.json` for both A runs), so the hypothesis's precondition (MCP surface actually varying) was never exercised in this single observation. R8's `similar-reuse-variance-not-observed` case is the pre-registered, correct label for exactly this outcome — not a SUPPORTED/REFUTED result reached by loosening the rule.
- **The notable observation** (both arms ~99.96-99.97% run-2 reuse) is stated only as a GEX44-scoped, single-observation fact (`comparison:` line, `host_scope:`, `n_limit_statement:`). It is **not** used to draw any conclusion about the laptop's much lower first-call shared share (1.9% sdk-cli / 16.4% cli, from Phase 2's `02-01-SUMMARY.md`). EVIDENCE.md never mentions those laptop figures in this file at all — the scope is kept strictly to "GEX44 transcripts, not the laptop's; the at-run claude version and this MCP configuration," which is the correct, non-overclaiming posture given n=2 and a different host/environment entirely.
- `cro04: SATISFIED` is not conflated with a positive/negative hypothesis result — the SUMMARY and EVIDENCE both correctly distinguish "CRO-04 is judged" (procedurally satisfied — the requirement was to test-and-judge, not to prove a direction) from "the hypothesis was SUPPORTED/REFUTED" (which did not happen this run). This matches ROADMAP criterion 4's own wording ("Verdict: hypothesis SUPPORTED / REFUTED / UNJUDGED (with why)").

### Human Verification Required

None. Every must-have was independently recomputed or re-derived from raw artifacts (transcripts on disk, git commit history, live.log, selftest re-run) rather than accepted from SUMMARY.md or EVIDENCE.md claims alone.

### Gaps Summary

No gaps found. All 6 derived must-have truths, all 5 required artifacts, all 5 key links, and all 4 ROADMAP Phase 4 success criteria are independently verified against the codebase and the transcripts on disk, not merely against SUMMARY.md's narrative. The phase goal — testing the MCP tool-list-variance cache-miss hypothesis on subscription quota — was executed correctly and judged honestly as UNJUDGED for a documented, pre-registered, legitimate reason (Arm A's MCP surface did not vary in this single observation), which is itself a valid and honestly-reported phase outcome, not a defect.

---

_Verified: 2026-09-28T14:50:58Z_
_Verifier: Claude (gsd-verifier)_
