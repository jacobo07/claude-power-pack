# C -- Agents, images and history elasticity, GEX44 plane (2026-10-12)

Same fixture and plane as `B-longrun-curves-gex44.md` (Linux, 2.1.296 Bun/JSC, isolated config, zero provider tokens).
Raw rows: GEX44 `~/prr-bench/runs/{agent_plain,agent_cr,image_plain,image_cr,hist_big,hist0,hist1,hist4,hist10}.jsonl`.

## Agents (each turn spawns one general-purpose subagent that runs one 20 KB Bash call), 200 turns
| mode | anon t1 -> t200 | slope MB/100 turns | epoch-start anon | process tree |
|---|---|---|---|---|
| plain | 135 -> 333 | **+64.0** | - | n=1 (subagents run in-process) |
| compact+recycle /50 | 130 -> 220 | -0.17 | 149, 160, 162 | n=1 |
Completed subagents stay resident in the parent process: about 1 MB per completed agent with no live consumer
(COMPLETED_AGENT_RESIDENCY, CONFIRMED on this plane). Mods cannot stop an agent (A1); the recycle releases it.

## Images (each turn Reads a 3.0 MB noise PNG, 1000x1000), 200 turns
| mode | anon t200 | HWM | largest request | epoch-start anon |
|---|---|---|---|---|
| plain | 298 (345 at t100) | **1,202 MB** | **67.5 MB** | - |
| compact+recycle /50 | 250 | 715-840 | 34.5 MB | 152, 152, 154 |
Image history drives the PEAK, not only the steady state: every request re-serialises every live image.
Recycling bounds the epoch start; the in-epoch peak follows the live image set (50 images per epoch here).
Epoch length is the lever on the peak (same lever CCR arm B names for tokens).

## Tool output size
200 KB per Bash result: the host spills large output to a per-session directory and keeps the transcript small
(22.8 MB after 500 turns, largest request 337 KB). Large tool results are not a resident-memory driver.

## History elasticity (resume after a compact boundary, pre-boundary history padded k times)
| k | transcript on disk | anon after resume | HWM | first-turn latency |
|---|---|---|---|---|
| 0 | 26.9 MB | 119 MB | 266 MB | 0.33 s |
| 1 | 50.9 MB | 120 MB | 269 MB | 0.39 s |
| 4 | 123.0 MB | 121 MB | 274 MB | 0.37 s |
| 10 | 267.1 MB | 119 MB | 288 MB | 0.42 s |
Elasticity of resident anon to durable history: ~0 over a 10x range. Peak +22 MB for +240 MB of history (file
streamed once). The successor's resident set depends on the post-boundary live set only.
**Total recall does not require total residency**: all 267 MB stay on disk under the same session id.

## Epoch-start drift (generation over generation)
bash compact+recycle, epochs 3-10: +0.27 MB/epoch (residual 0.5 MB). The 10x history test shows it is not
transcript size. Unattributed; watch it in the Windows canary before calling it zero.
