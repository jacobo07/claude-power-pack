# SCS C53 -- TCO Visibility by Default

**Sealed:** 2026-06-23. Domain: token cost / observability.
**Lineage:** complements the TIS/budget_monitor stack (2026-05-26) by adding the
missing aggregated real-usage view. UKDL: `T-TCO-TRACKING-GAP-001`,
`T-CACHE-RATIO-HEALTHY-001`.

## Standard

The real token TCO is read from Claude Code's own transcripts
(`~/.claude/projects/<enc-cwd>/<sid>.jsonl`, `message.usage`), never inferred
from a hook-cadence logger or a programmatic-credit monitor.

1. **Ground truth = transcripts.** `tools/token_ground_truth.py::analyze`
   aggregates real per-turn `input/output/cache_read/cache_creation` across all
   non-subagent transcripts, bucketed today / month / lifetime.
2. **Cache ratio is the Max-relevant health metric.** On a flat-rate Max plan
   the economic TCO is $0 marginal/token; efficiency = `cache_read /
   (cache_read + input + cache_creation)`. Healthy >= 50%; measured 96.6%.
3. **High-consumer = avg fresh input/turn > 100k**, with /compact or /kclear as
   the action. Whole-session size pressure stays gated by `context_monitor`
   (16/24 MB, 6000/12000 turns), independent of the cache ratio.
4. **Three systems, three buckets, never conflated:** transcripts = real
   session usage; TIS = JIT-injection overhead; budget_monitor = programmatic
   metered credit. An audit that expects them to "match" is mis-framed.
5. **On-demand by design.** The audit report
   (`vault/audits/token_usage_<ISO>.md`) is regenerated from disk; no new
   always-on hook is added (token austerity; the data already exists on disk).

## Done evidence (2026-06-23)

- `tools/token_ground_truth.py` -- new aggregated real-usage analyzer
  (importable `analyze(proj_base=, now=)`, fail-safe per-file parse).
- `vault/audits/token_usage_2026-06-23.md` -- real numbers: today 9.6M in /
  49.5M out / 6.27B cache-read / 96.5%; lifetime cache 96.6%; 0 high consumers.
- `tools/test_tco_tracking.py` -- 6/6 x3 hermetic (V-TRANSCRIPTS-HAVE-TOKENS,
  V-AGG-CORRECT, V-CACHE-RATIO-CALCULATED, V-HIGH-CONSUMERS-IDENTIFIED,
  V-SUBAGENT-EXCLUDED, V-REPORT-RENDERS).
- `modules/token-optimizer/token_autopsy.py:409` -- fixed latent `NameError`
  (`mass_ops` -> `mass_greps or mass_bash`) that crashed on a clean session.

## What this did NOT change

- No new always-on hook (the transcripts are the source; reading is on-demand).
- `pane_map.md` left unchanged (Owner chose standalone report over wiring a
  tokens column into the disk-regenerated `build_pane_map.ps1`).
- budget_monitor / TIS untouched -- documented, not "fixed", because they
  measure different (valid) buckets.
