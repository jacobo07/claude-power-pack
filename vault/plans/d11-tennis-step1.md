# D11 step 1 -- call-graph walk: Tennis closure and the KPAD read path (zero-model, 2026-10-09)

Work dir: `C:\Users\User\Apps\recon_work\wst_tennis\step1\` (`probe_step1.py`, `step1_report.json`). It reuses step 0's
`probe_tennis.py` scan. No model tokens were spent; everything below is a tool reading.

## Graph
- 18,820 functions (every one has a VA), 30,718 call edges (`bl`/`b`), 908 address-taken edges, 1,312 data objects that
  hold function pointers (vtables, callback tables). Indirect calls (`bctrl`) are approximated by address-taken edges,
  which over-include.
- Control: the walk re-derives step 0's seeds, 13/13.

## SDK library bounds (a DTK unit is not a library)
- DTK places the whole SDK in one auto object, `auto_03_800C3098_text.s`, with 3,900 functions holding both KPAD and
  WPAD. A first run took that object as "the KPAD library". Every count then came out identical for KPAD and WPAD
  (943 = 943), so that instrument could not tell them apart, and its motion figure (4,466) is discarded.
- The replacement uses address windows between RVL_SDK version-string anchors (the Init function that reads each
  library's version string). Anchor order: KPAD 800DBA70, WPAD 800E1BE0, VI 8011F110, AI, AX, HBM, NWC24, RFL.
- KPAD window: (800DBA70, 800E1BE0), 109 functions, 5,954 instructions, 86 of them shape-shared with Resort. KPAD is
  the first anchor, so the window starts at KPADInit, misses any KPAD code before it, and may hold the head of WPAD.
  It is a bound, not an identification.

## Tennis closure (forward from the 13 seeds)
| closure | functions | in the 6 Tennis units | shape-shared with Resort | novel | instructions |
|---|---|---|---|---|---|
| reach (call + addr edges) | 11,766 | 1,775 | 5,460 | 6,306 | 724,728 |
| novel (stop at Resort-shape functions) | 5,434 | 1,323 | 0 | 5,434 | 434,250 |

The forward walk escapes the Tennis code through vtables and callback tables into the rest of the game. It is an upper
bound and does not size Tennis. The useful number is the novel closure inside the 6 Tennis units, 1,323 functions,
which agrees with step 0's estimate of about 1,200 to 1,400.

## Motion read path
- No function in the Tennis reach is within 4 caller hops of the KPAD window (motion = 0, and 0 of 13 seeds reach it).
- Exactly 3 game-side functions call into the KPAD window directly: `fn_800B7BFC` (`auto_03_800B38E4_text.s`),
  `fn_801D2744` (`auto_03_801D2150_text.s`) and `fn_801DDF90` (`auto_03_801D74F8_text.s`). None of them is in the Tennis
  reach, and none has a Resort-shape match.
- Reading: the framework reads the Wiimote once per frame through those 3 functions and stores the result. Tennis
  consumes the stored state by DATA (an object or offsets), not by calls. Resort works the same way: KSR's
  RZTP01_CORECONTROLLER_CONTRACT reads accel from fixed CoreController offsets. A call graph cannot size the motion
  closure.

## Consequence
- The motion closure has two ends. The read end is 3 functions plus whatever KPAD and WPAD code they need, which can be
  relinked from retail. The consumer end is Tennis code that loads the stored controller state.
- Next zero-model probe: a data-flow probe. Find the store target of those 3 callers (the controller-state object
  or global), then count the Tennis-unit functions that load from it (by symbol, or by `lwz`/`lfs` from a pointer
  loaded from it). That count, not a call walk, sizes the motion consumer side.
