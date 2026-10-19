---
covers: [ttb-wii-sdk, h4-level-collapse, two-builders, wii-breakthrough]
tier: T2
status: DRAFT packet for the tb-m2 mission worker (Owner "y" 2026-10-19 released T2; slot spend still the Owner's call)
date: 2026-10-19
---

# H4 packet: collapse the largest Negotiations_a draws (one Dolphin run)

Author pane writes NOTHING to the tb-m2 clone. The worker copies the probe and PREREG below, lints, admits, then runs one slot.
Evidence level of any result: Dolphin on GEX44 = candidate, never Wii hardware.

## Question
Does the engine load an edited level scene (`NEGOTIATIONS_A.CSC`) and draw the edit? Collapse needs no vertex-format knowledge.

## Probe (add to `tools/build_two_builders.py` after the dict, like the other post-dict probes)
```python
# H4 (TTB Wii SDK): the 12 largest draws of the Negotiations_a scene collapsed (any-format hide). Header offsets measured in the
# unmodified CSC (5,555,680 bytes, sha256 873ac9238a56e96d...) by TB-wii-sdk/h4_targets.py; translations (0,0,0) = large static shell.
PROBES["level-geom-negotiations"] = [
    ("collapse", "files/Levels/Episode_I/Negotiations/Negotiations_a/NEGOTIATIONS_A.CSC", h)
    for h in (0x4647C4, 0x429EE4, 0x427E64, 0x450E24, 0x42DBC4, 0x468264,
              0x47EFE4, 0x492F44, 0x42BF64, 0x42F084, 0x491B64, 0x46BBA4)
] + PROBES["newgame-negotiations"]
```
Offline proof (this pane): applying those 12 collapses to a copy changes 50,040 bytes, all inside the 12 display lists, file length
unchanged, every chosen draw reads back collapsed, and the unmodified file reads not-collapsed (red branch). Script `TB-wii-sdk/h4_targets.py`,
ranking in `TB-wii-sdk/h4_negotiations_a_targets.csv`. Assumption to verify first: the `collapse` step handler accepts a `.CSC` path
(it is used on `.CHG` only so far) and the build's disc layout puts the file at that path.

## PREREG (ADMIT fields)
- Owner/premise: collapse edits only display-list vertex bytes (Dolphin-proven on Madzia, P16/P17). UNPROVEN: that Negotiations_a is read from this CSC. Run with `TB_DOLPHIN_LOG=1` so FileMon shows the open (a no-change result is then attributable).
- Instrument qualification: same Dolphin config and same Negotiations_a camera as the stock baseline run; the baseline screenshot of that frame is the positive/negative control.
- Control: stock disc, same level, same frame (already captured in earlier TB runs; use the same capture time).
- Observable the baseline cannot produce: large static shell geometry missing at the known frame (floor or walls absent, background visible).
- Outcomes -> next action:
  - A. Shell parts visibly missing, game runs: edited CSC is loaded and drawn. Next: bisect to name the visible draw, then H3c on strides, then move geometry.
  - B. No visible change and FileMon shows the CSC opened: the 12 draws are not what the camera sees. Next: collapse the next ranked 30, or pick draws by node translation near spawn.
  - C. No visible change and FileMon shows no CSC open: wrong file. Next: find the loaded level container (cf. the Cantina `Levels/Map/map` lesson).
  - D. Crash/black screen: the edit breaks load. Next: halve the set (6/6) to find the breaking draw. Instrument failure = no capture or no pre-read gate.
- Budget: one slot, about 4M processed, inside T2 (8M). Not spent yet.
