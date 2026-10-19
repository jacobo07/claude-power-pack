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

## Status 2026-10-19
- S1 DEFERRED by the Owner (no gamepads on the laptop; needs 2 DualShock/DualSense). S2 does not need a second pad.
- BactaTank wiki read (Editing, Creating A Character): TCS PC editable via `*_PC.GHG` only (`*_LR_PC.GHG` not loadable).
  Texture: Export (Ctrl+E) -> edit externally (DDS) -> Replace (Ctrl+R). Mesh: Export/Replace the same way, then Ctrl+S overwrites the
  GHG, so work on a COPY in a new CHARS folder (rollback = delete the copy). New character = copy a base's `.GHG` + `.TXT`, rename, edit
  `.TXT` tags, add a `name_id` (<1000, quoted) in `STUFF/TEXT/<LANG>.TXT`, append entries to `CHARS/CHARS.TXT` and `CHARS/COLLECTION.TXT`
  (exact syntax is in screenshots only), delete `CHARSTXT.FPK` if the slot shows "?". Bones/Layers not editable; attributes cannot be added
  or removed. Caveat: Paint.NET suggested for DDS export.
- S2 texture half PASS (2026-10-19, WORKS IN PC NATIVE, screenshot not video): QuiGonJinn face atlas (tex #7, 512x512 DXT5) patched in place
  (same byte size; the GHG stores textures as plain DDS blobs, so no pointer rebuild) shows teal brows/moustache in the Cantina demo.
  Evidence: `C:/Users/User/TB-PC-spike/s2/shot_state.png`, `face_crop.png`. Mesh half and the continuous video are still open.
- Loose files: the engine ignores loose files while the `.DAT` archives are present (the loose GHG's access time never moved). It reads them
  from a DAT-free copy (`TB-PC-spike/game_loose`: extracted tree + non-DAT install files + `steam_appid.txt` = 32440). The Steam install is
  untouched except one new `CHARS/QUIGONJINN` folder (rollback `s2/ROLLBACK.ps1`). Loading without DATs is slower per the community guides.
- Iteration loop here (no GEX44 needed): `s2/shot.ps1` captures the 1024x768 window, `s2/key.ps1` sends keys (synthetic input works).
  The title idle-demo shows Qui-Gon in the Cantina. The in-game prompt "Pulsa F2 o cualquier boton para empezar" is the player 2 join: relevant to S1.

## Decision after the spike
All three PASS: ask the Owner to promote PC to the main target and write the new baseline generation (reason + authority).
Any FAIL: keep Wii as the target, and say which test failed and why.
