# D11 step 3 -- this-flow probe: controller objects into Tennis (zero-model, 2026-10-09)

Work dir: `C:\Users\User\Apps\recon_work\wst_tennis\step3\` (`probe_step3.py`, `step3_report.json`). Run by one bounded
Sonnet subagent: 10 tool calls, 138,532 subagent tokens, 2 script iterations. The probe itself is a script. The
subagent's FINDINGS.md write was refused by the harness, so this file is the record.

## Allocator (fn_800B7BFC, loop at .L_800B7D88, 4 channels)
- Each controller is a 0xFC0-byte `new` (fn_800B4508) with vtable lbl_803EABA8 at +0. If the SDA global lbl_805133BC is
  non-zero, it is a factory callback and that callback creates the controller instead.
- Controller pointers live at `(*(mgr+0x1C))[ch*4]` (4 entries). mgr+0x18 is the count, mgr+0x14 an embedded container
  (vtable lbl_803EAB7C), and mgr+0x24/0x28/0x2C an array of per-channel ints, not controllers.

## Getters (read by hand)
- fn_800B7AD4(mgr, idx): bounds-checks against +0x18, returns array[idx].
- fn_801DDEC8(mgr, id): scans the array, returns the controller whose +0x4 == id.
- 16 other short `array[idx]` functions are other instantiations of the same container and were excluded. Inline
  global -> +0x1C -> lwzx loads: 0 in the whole game, so consumers go through the two getters.

## Counts (Tennis units 1,797 functions; game 18,820)
| measure | Tennis | game |
|---|---|---|
| (c) `bl` callers of the two getters | 50 | 114 |
| (d) of those, a load at 0x8..0xFB4 through r3 or an `mr` copy | 20 | 58 |
| (d') of those, at a step-2 named offset | 5 | 19 |

Offsets read in Tennis (offset:functions): 0x1C:17, 0x18:8, 0x74:6, 0x76:3, 0x3C:3, 0x38:3, 0xF18:1. Only 7 distinct
offsets. 0x18 is the raw KPAD buffer. The derived state 0xF18 is read by 1 Tennis function (6 in the game).
0xF6C..0xFB4 are not read in Tennis by this tracker.

## Controls
- Positive: fn_800B772C with r3 = controller shows 27 stores and 33 loads in range (0x8, 0xC, 0x10, 0xF18, 0xF6C..0xF9C,
  0xFA4). Two getters were found, so the step is not UNRESOLVED. A synthetic body is detected and a near-miss global is not.
- Negative: 50 random non-Tennis functions (seed 20261009, >0x10000 from the manager, pool 9,112): (c) 0/50, (d) 0/50.
  That discriminates, but it cannot exclude a true rate below ~6%.

## Caveats (all counts are floors)
- The tracker is linear: no branches, volatile registers cleared at calls. It follows `mr` and the getter returns only.
  A controller passed in an argument register or used through a virtual call is invisible.
- fn_800B772C (reached via its vtable) is not counted as a Tennis consumer.
- The Tennis units include shared engine code, and the Resort-shape overlap was not subtracted.

## Reading
Tennis's direct motion-consumer surface is small: 20 functions read controller fields at least, mostly the raw buffer
and low offsets, and almost none read the derived state. Step 4, if wanted, would add one level of argument
propagation into the callees of the 50 getter callers and subtract the Resort-shape overlap.
