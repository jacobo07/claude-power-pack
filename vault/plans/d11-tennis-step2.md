# D11 step 2 -- data-flow probe: where controller state lands, who reads it (zero-model, 2026-10-09)

Work dir: `C:\Users\User\Apps\recon_work\wst_tennis\step2\` (`probe_step2.py`, `step2_report.json`, `FINDINGS.md`).
Run by one bounded Sonnet subagent (22 tool calls, 156,686 subagent tokens); the probe itself is a script.

## Step 1 premise corrected
- The 3 game-side callers of the KPAD window call setters only (fn_800DC0E0/C190/C1B0/C1D0); none stores a read result.
- Step 1's window starts at KPADInit, so it misses KPADRead. Inferred KPADRead = fn_800DB250 (per-channel stride
  0x688), reached by fn_801D2744 -> fn_800B772C -> fn_800DB240 -> fn_800DB250. Identified by stride and call shape only.

## Store targets
- Read side: an OBJECT, no global. fn_800B772C is a virtual method of a per-channel controller object (~0xFB8 bytes):
  raw KPAD at this+0x18; derived state at 0x8..0xFB4 (0xF18, 0xF6C..0xF9C, 0xFA4, 0xFB4).
- Publish side: fn_801DDF90 builds the manager via fn_800B7BFC and stores it in SDA globals lbl_805133B8 and
  lbl_80513DF0. The only stores to them are from fn_801DDF90 and fn_800B7A68.

## Consumer counts (Tennis units = 1,797 functions; game = 18,820)
| measure | Tennis | game |
|---|---|---|
| (a) direct load of a manager global | 51 | 122 |
| (b) global -> manager pointer -> load at 0x8..0xFA4 | 0 | 3 |
| inline reads of the per-channel object via `this` | UNRESOLVED | UNRESOLVED |

Tennis passes the manager as `this` into calls rather than reading controller fields inline. (a) is a floor: register
tracking is linear and does not follow pointers passed in argument registers.

## Controls
- Positive: a synthetic body is detected and a near-miss symbol is not. fn_801DDF90 is detected storing the global.
  The spec's "3 callers touch the target" is met only 1/3, because two use `this`, not the globals.
- Negative: 50 random non-Tennis functions give 0/0/0. A looser offset-only proxy hit 29/50 and was discarded.

## Next zero-model probe (step 3)
Find the allocator of the ~0xFB8-byte controller object (the loop at 800B7D88 in fn_800B7BFC), then track `this`
through argument registers into the Tennis units. The inline consumer count is open until then.
