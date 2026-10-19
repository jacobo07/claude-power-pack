# Two Builders: PC feasibility spike (decide Wii-first versus PC-first)

Date 2026-10-19. Origin: the Owner shared a third-party proposal to make TCS on PC the main target and answered two questions:
how they will play in January ("Ambos": same sofa first, Remote Play as backup) and whether the physical Wii is part of the gift
("Solo importa jugarlo juntos"). PC becomes the target only if this spike passes; that is a decision for the Owner, not a default.

## What was verified (2026-10-19, primary pages read)
- BrickBench: map editor for TCS, Windows and Linux x64, OpenGL 4.5, 67 stars, 25 open issues, last commit date not shown.
- BactaTank Classic: loads only `*_PC.GHG`, says it does not work with console versions; some TCS models fail to load; mesh edits need the
  Blender add-on (Blender 4.0+); extraction needs QuickBMS plus a TT Games BMS script; Windows Defender may block the exe.
- Traveller: early (30 commits, no releases, scripting layer being rewritten); platform not stated on its page.
- TCS is on Steam with 2-player local co-op; forum reports say Remote Play Together works with one copy, with a second-controller
  detection problem and a community workaround. NOT verified: whether TCS keeps one shared camera when players separate.

## What carries over from the Wii work, and what does not
Carries: references, `fidelity/contracts`, the audit tracker, level and narrative design, art sources (PNG/DDS), the decision pack.
Does not: the CHG geometry writer, the Wii disc build, the Dolphin capture infrastructure. The baseline family `game_mod_fidelity`
says a PC result is not Wii proof; moving the target needs a new generation with a reason and an authority from the Owner.

## Spike: three tests, each judged by a continuous video, not stills (budget: 3-5 days, no new mission)
- **S1 two players.** Two controllers (DualShock/DualSense through Steam Input) drive two characters in one session.
  PASS = a video where both move independently for 2 minutes with no controller reassignment. Then a Remote Play Together session
  with Madzia: PASS = her controller drives player 2 from her machine; a dropped session leaves no ghost player.
- **S2 model and face.** One character gets a changed face texture and one mesh change, loaded in game.
  PASS = front and 3/4 views in play showing both changes, no crash, original character still intact after rollback.
- **S3 level.** One level edited with BrickBench, loaded and played in co-op.
  PASS = a video of both players completing a changed objective. Include the camera test: separate the players and record whether
  the camera is shared (decides the alley-and-bridge scene).

## Rules
- Every artefact is copied from its source into a new empty directory; nothing downloaded is run from inside it (unvetted exes).
- Originals of the game files are never overwritten; every test ships a rollback.
- Evidence level for each result is "WORKS IN PC NATIVE"; none of it is Wii proof, and none is Owner-approved until a decision file says so.
- Stop and report on the first test that fails twice for a structural reason, with the measured cause.

## Decision after the spike
All three PASS: ask the Owner to promote PC to the main target and write the new baseline generation (reason + authority).
Any FAIL: keep Wii as the target, and say which test failed and why.
