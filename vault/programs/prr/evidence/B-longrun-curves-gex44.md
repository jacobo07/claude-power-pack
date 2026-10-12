# B -- Long-run memory curves, GEX44 plane (2026-10-12)

**Plane: GEX44 (Linux 64 GB), Claude Code 2.1.296 (Bun 1.4.3 / JSC), isolated `CLAUDE_CONFIG_DIR`, no PP hooks,
no MCP.** Not a Windows result. Fixture: `modules/prr/bench/stub_api.py` (scripted Messages API, zero provider
tokens) + `modules/prr/bench/longrun.py`. Every turn = one Bash tool call printing 20,000 chars + a final text reply.
500 turns per curve; checkpoints 1/10/25/50/100/150/200/250/300/400/500; memory = main process RssAnon (closest to
private bytes with no swap), VmRSS, VmHWM from `/proc/<pid>/status`. Fit = least-squares RssAnon slope, turns >= 25.
Raw rows: GEX44 `~/prr-bench/runs/{plain,compact,recycle,compact_recycle}.jsonl` (+ `.req.jsonl` request sizes).

| mode | anon t1 | anon t500 | HWM t500 | slope MB/100 turns | last request | epochs | resume s |
|---|---|---|---|---|---|---|---|
| plain | 107 | 212 | 562 | +10.08 | 10.5 MB / 1,999 msgs | 1 | - |
| compact /50 | 107 | 257 | 557 | +11.86 | 1.2 MB / 201 msgs | 1 | - |
| recycle /50 (`--resume`) | 107 | 248 | 521 | +10.70 | 10.7 MB / 2,035 msgs | 10 | 0.67-0.95 |
| **compact + recycle /50** | 107 | **166** | **362** | **+0.27** | 1.2 MB / 205 msgs | 10 | **0.29-0.31** |

compact_recycle: anon right after each resume = 133, 126, 126, 126, 126, 127, 127, 127, 128 MB (epochs 2-10) while the
durable transcript grew to **26.7 MB on disk**. Session id identical across all 10 epochs.

## Findings
1. **Hard resident floor (Linux, bare host): ~107 MB anon / ~224 MB RSS** after one turn; ~126 MB anon for a resumed
   epoch carrying a post-compact live set.
2. **RAM grows with history in one process**: ~0.2 MB anon per turn for 20 KB of tool text, about 10x the transcript bytes.
   HWM grows faster (562 MB) -- request serialisation peaks scale with the context sent.
3. **Compaction is a token lever, not a RAM lever.** It cut the request from 10.5 to 1.2 MB, but in-process anon kept
   growing at the same slope. Allocator page retention would plateau at the HWM; continued growth after compaction
   points to pre-boundary state still being live in the process. (PARTIAL for Root Q3: no heap stats reachable.)
4. **Recycling alone is not bounded**: `--resume` rehydrates the whole transcript (2,035 messages), so each successor
   starts higher (146 -> 225 MB).
5. **Compaction followed by recycling is bounded**: the successor loads only the post-boundary set. Slope 0.27 MB/100
   turns is inside the residual noise (max |resid| 10.3 MB). Terminal-law candidate holds on this plane.

## Consequences for the architecture
- Physical epoch recycling must happen **after** a compaction boundary, never instead of one.
- The compaction (semantic step, token cost) and the recycle (physical step, ~0.3 s, zero tokens) are separate
  decisions. A recycle right after a compaction costs no extra tokens and is the cheapest moment to release RAM.

## Open (not proven here)
- Windows plane: private bytes per main process average 854 MB on the laptop (vs ~107-250 MB anon here); the share
  from hooks, MCP, real tool output and images, and Windows commit semantics, is unmeasured. Laptop canary blocked:
  Available 490 MB < 4 GB floor.
- `/clear` (ASER's lever) retention: measured next.
- Real-model token cost of the compaction call (CCR: cache prefix rewrite ~80K cache-write).
