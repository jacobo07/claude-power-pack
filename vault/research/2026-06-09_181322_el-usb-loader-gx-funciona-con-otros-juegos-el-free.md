# USB Loader GX: Diagnosing a Single-Game Freeze When Other Games Work

## Executive Summary

The diagnostic premise — *"USB Loader GX works with other games; only this one freezes"* — is the single most valuable piece of information in this class of problem. It is a natural bisection. A working loader running a library of other titles **proves** that the entire shared substrate is sound: the cIOS install, the storage format and partitioning, the USB port selection, the loader binary, and the launch method are all functional. That eliminates roughly two-thirds of the documented black-screen/freeze causes in one stroke and forces the investigation onto **game-specific** factors.

This report consolidates the research learnings into (1) a triage model that uses the "other games work" fact to prune the cause tree, (2) the game-specific freeze mechanisms that survive that pruning — chiefly multi-DOL games and unblocked IOS reloads — and (3) the concrete loader settings and patch-subsystem behaviors that resolve them. It closes with the residual hardware-revision class of failures that no software patch can fix.

---

## 1. The Bisection: What "Other Games Work" Rules Out

USB Loader GX black-screen / freeze causes fall into two families: **shared-substrate causes** (affect *every* game) and **game-specific causes** (affect only certain titles). The reported symptom isolates the problem to the second family.

| Cause class | Affects all games? | Status given "other games work" |
|---|---|---|
| Incorrect / missing cIOS install | Yes | **RULED OUT** |
| Wrong USB port (must be edge port USB0) | Yes | **RULED OUT** |
| Storage not FAT32 MBR / formatting fault | Yes (mostly) | **RULED OUT** (see caveat) |
| Launched via forwarder instead of Homebrew Channel | Yes | **RULED OUT** |
| SD card write-protect lock enabled | Yes (config writes) | **LIKELY RULED OUT** |
| Drive > 2TB / flash-drive incompatibility | Yes (mostly) | **LIKELY RULED OUT** |
| Bad / corrupt / NKIT image | **Per-game** | **SUSPECT** |
| Multi-DOL game + unblocked IOS reload | **Per-game** | **PRIME SUSPECT** |
| Wrong per-game IOS base (249 vs 250/224) | **Per-game** | **PRIME SUSPECT** |
| Video patch conflict (deflicker / width / 480p) | **Per-game** | **SUSPECT** |
| Title needs a private-server / accessory IOS setting | **Per-game** | **SUSPECT** |

### Caveats that survive the bisection

Two "shared" causes are not fully eliminated by the fact that other games boot:

- **The 4 GB FAT32 split boundary.** FAT32 cannot store a single file > 4 GB; large images must be split. If the failing title is your *only* image above 4 GB and it was copied without splitting, every *other* (smaller) game would still load fine. This is a per-game-sized manifestation of a storage rule.
- **Image integrity is inherently per-game.** A corrupt or NKIT-format image affects only that title. Wii games **must** be ISO or WBFS — NKIT is GameCube-only. The canonical first test is to load the failing image in **Dolphin Emulator** (PC or Android). If it fails there too, the image is the fault: re-acquire it.

---

## 2. The Prime Suspect: Multi-DOL Games and IOS Reload

The dominant documented cause of a freeze that hits *specific* titles while the rest of the library runs is the **multi-DOL game** interacting with an **unblocked IOS reload**.

### 2.1 The mechanism

Some Wii games ship **multiple DOL executables** and/or trigger an **IOS reload at runtime** — typically at a scene/state transition (calibration finishing, a cutscene boundary, entering gameplay). When a game running from USB asks the system to reload IOS, the running USB context can be torn out from under it. If the cIOS does not **block or redirect** that reload, the game hangs — a black screen or hard freeze precisely at the transition point.

This is why these freezes are characteristically **late** — the title boots, shows logos, even reaches a menu or a calibration step, *then* dies. A freeze at a deterministic point (rather than at first boot) is the signature of an IOS-reload / alternate-DOL boot event rather than a bad image.

### 2.2 The empirically reported victims

| Game | Reported freeze symptom |
|---|---|
| The Legend of Zelda: Skyward Sword | Freeze immediately **after WiiMotionPlus calibration** |
| Super Mario Galaxy | Black screen on load |
| Metroid Prime Trilogy | Boot hang (alternate-DOL booting) |
| Kirby's Dream Collection | Black screen |
| Call of Duty 3 | Black screen |
| Sam & Max, CSI | Alternate-DOL boot hang |

The Skyward Sword "after calibration" signature is the textbook case: the calibration step completes and the game attempts its next-stage load, which involves the reload that the loader failed to block.

### 2.3 The fix: "Block IOS Reload"

The resolution is the **`Block IOS Reload`** function in the loader (Settings → per-game or global). This is a documented **d2x cIOS feature** (the "IOS reload block from USB," credited to **WiiPower**) and requires **d2x v6 or newer**. Enabling it prevents the game from following its alternate-DOL / reload path, keeping it pinned to the USB-running context. It is the specific recommended fix for **Metroid Prime Trilogy, Sam & Max, and CSI**, and the multi-DOL family generally.

> Note: these multi-DOL freezes persist identically across **WiiFlow** and **CFG Loader**, confirming the cause is the cIOS/IOS-reload layer, not a USB Loader GX GUI bug. They are *especially* unresolved on the **Wii Mini**, whose cIOS is non-standard (d2x explicitly must **not** be used on the Wii Mini).

---

## 3. Second Suspect: Wrong Per-Game IOS Base

Some titles simply do not behave on the default cIOS slot (IOS249, base 57) and must be pointed at a different base via **Settings → Game Load → Game IOS** on a per-game basis.

| Game | Symptom on default IOS249 | Working IOS |
|---|---|---|
| Call of Duty: Black Ops | Stuck on loading screen | IOS 224 or 250 |
| Call of Duty: Modern Warfare 3 | Stuck on loading screen | IOS 224 or 250 |
| Just Dance 2014 / 2015 / 2016 | Black screen | IOS 224 or 250 |

The general remedy for a multi-DOL freeze is also expressible at the IOS-base level: **force a cIOS base of IOS56 (the IOS250 slot) instead of IOS57**. So the two prime suspects converge on the same two knobs:

1. **Block IOS Reload = ON** (per-game)
2. **Game IOS = 250 (base 56)** or **224**, instead of 249 (base 57)

Try them independently and in combination.

---

## 4. Verifying the Shared Substrate (Confirmation, Not Re-build)

Even though "other games work" rules out the substrate, it is worth **confirming** the cIOS is the canonical d2x layout before spending time on per-game tuning — a marginal install can produce intermittent per-game behavior.

### 4.1 The SysCheck signature of a correct d2x install

Run **SysCheck** and confirm exactly these three slots:

| Slot | Base | Revision | Modules |
|---|---|---|---|
| **IOS249** | 57 | rev 65535 | Trucha Bug, NAND Access, USB 2.0 |
| **IOS250** | 56 | rev 65535 | Trucha Bug, NAND Access, USB 2.0 |
| **IOS251** | 38 | rev 65535 | + ES Identify |

All three must report **d2x-v10beta52**. Install via the **d2x cIOS Installer** per `wii.guide/cios`.

For **vWii** (Wii U), the d2x **v11** layout differs: 249/base56, 250/base57, 251/base38, optionally adding **248/base38 + 251/base58**. The slot/base mapping is version- and platform-specific — do not assume the Wii layout on vWii.

### 4.2 Storage and launch hygiene (the "minimize variables" doctrine)

From the rWiiHacks *Ultimate Guide to ALL Loader Issues* (u/BloodyThorn, 2022-08-18), the canonical variable-minimization checklist — confirm even if other games work, since a marginal setup can be title-sensitive:

- Storage = **FAT32, MBR-partitioned**. (NTFS/ExFAT only if you have **no** GameCube games. Split images > 4 GB on FAT32.)
- USB device on **port 0** (edge/back port) — unless using the less-compatible **d2x beta53-alt** cIOS.
- Launch the loader **directly from the Homebrew Channel**, never a forwarder (forwarders cause black screen + white-text errors).
- **Avoid USB flash drives** and SD-to-USB adapters (Nintendont devs advise against flash drives); prefer a powered HDD.
- **Avoid backup managers** (WBFS Manager / Wii Backup Manager) for writing the image — they can corrupt.
- Keep drives **under 2 TB**.
- Disable the **SD card write-protect** slider.
- Cross-reference the **GBATemp USB Game Compatibility Table** — some accessory-dependent games need specific IOS settings.

---

## 5. The Video-Patch Family: A Quieter Per-Game Freeze Source

USB Loader GX rewrites the loaded DOL at runtime through a patch subsystem before execution. A misapplied or conflicting video patch is a documented per-game freeze cause.

### 5.1 The patch pipeline

In the wiidev fork (`source/patches/gamepatches.c`), the central `gamepatches()` orchestrator (lines ~102–215) applies a chain of DOL modifications before hand-off:

| Patch | Purpose |
|---|---|
| `VideoModePatcher()` | Force/normalize video mode |
| `deflicker_patch()` | Toggle the deflicker filter |
| `patch_vfilters()` | Vertical filters |
| `patch_width()` | Video width (decoupled to avoid conflicts) |
| `PatchFix480p()` (lines 418–517) | Fix the Nintendo Revolution SDK 480p bug on early Wii consoles |

Game-specific entries also exist: `patch_nsmb` (New Super Mario Bros), `patch_pop` (Prince of Persia), `patch_kirby`, `patch_re4` (Resident Evil 4).

### 5.2 Known freeze-and-fix history

- **v3.0-r1281** specifically **fixed games freezing when the deflicker filter was turned off**, and **decoupled the video-width patch** so it no longer conflicts with other patches.
- **v4.0-r1283 / r1282** (maintained by **blackb0x**, GUI on Tantric's libwiigui over Waninkoko's loader) **improved the 480p fix and width patches so all games boot**, and added automatic per-game cIOS / language selection (needs `wiitdb.xml`) and Disc-Default video mode via improved country-string patching.

### 5.3 Practical implication

If the freezing title is video-patch-sensitive, two moves help: **(a) update USB Loader GX to the latest r-revision** (the freeze you're hitting may already be a fixed regression), and **(b) experiment with the per-game video-mode setting** (Disc Default vs Force NTSC/PAL) and toggling deflicker/patches.

---

## 6. The Residual Class: Hardware-Revision Faults No Patch Fixes

One category cannot be resolved by any loader setting. The **480p SDK fix** targets early Wii consoles, but community reports confirm that **later board revisions (e.g., RVL-CPU-40)** still exhibit a 480p video-output defect (slight pixel blurring, visible under OSSC upscaling), and the software 480p fix **does not correct it** on those boards. This implies the root cause for those revisions is in the **hardware video-output chain**, not software-patchable.

This matters for triage: if a freeze/black-output correlates with a specific console board revision and a specific video mode, and survives every per-game software setting, you may be in hardware territory. Switch the console out of 480p as a test.

---

## 7. Infrastructure Context (for IOS-Level Debugging)

For deeper IOS-module behavior analysis during scene/state transitions — the exact regime where multi-DOL freezes occur — the relevant homebrew building blocks are:

- **neimod's Custom IOS Module Toolkit** (wiibrew.org)
- **Crediar's Sneek** (IOS emulation)
- **WiiGator's DIP plugin**
- **kwiirk / Hermes EHCI modules**
- **ChaN's FatFs**

The **d2x cIOS** itself derives from **Waninkoko's cIOSX rev21**, maintained by **davebaol / wiidev** on GitHub. A pivotal fix in its lineage was replacing cIOSX rev21's buggy **EHCI module** with the working one from **rev19** (XFlak's idea) — directly relevant to USB-transition stability.

---

## 8. Recommended Diagnostic Sequence

Ordered by expected value, using the "other games work" bisection:

1. **Test the failing image in Dolphin** (PC/Android). Fails there → re-acquire the image; confirm it is **ISO/WBFS, not NKIT**. Stop here if reproduced.
2. **Confirm SysCheck** shows IOS249[57] / IOS250[56] / IOS251[38], rev 65535, d2x-v10beta52. Marginal → reinstall via d2x cIOS Installer.
3. **Enable `Block IOS Reload`** for the failing game (per-game). Re-test. *(Highest yield for late/transition freezes — the Skyward-Sword-after-calibration signature.)*
4. **Set Game IOS = 250 (base 56)** or **224** for the failing game. Re-test, alone and combined with step 3.
5. **Update USB Loader GX** to the latest r-revision (latest official sources only) to pick up video-patch and freeze regression fixes.
6. **Tune per-game video mode** (Disc Default vs forced; toggle deflicker). 
7. **Check the FAT32 4 GB split** if this is your only >4 GB image.
8. **Consult the GBATemp compatibility table** for game-specific IOS requirements.
9. If correlated to board revision + 480p and nothing helps → **suspect hardware video chain**; change video mode out of 480p.

---

## 9. Note on Relevance to a Custom Homebrew Build

If the "game" that freezes while others work is a **custom Kamek/homebrew title** (rather than a retail disc image), the bisection still holds but the interpretation shifts: the loader, cIOS, and storage are confirmed good, so the freeze is **inside the custom module's own runtime path** at the transition point — not a USB Loader GX or cIOS configuration issue. In that case the loader-side knobs above (`Block IOS Reload`, Game IOS base) are worth a single confirmatory pass, but a freeze that reproduces identically across loaders **and** is deterministic at a specific in-game event (e.g., a Start-press scene transition) points to the title's own code, where loader settings will not be the fix. The substrate confirmation in Sections 1–4 remains the correct first step to *prove* the problem is the title, not the platform.

## Sources

- <https://gbatemp.net/threads/usb-loader-gx-black-screen-when-launching-some-wii-games-and-then-back-to-menu.656797/>
- <https://www.reddit.com/r/WiiHacks/comments/dnfb81/usb_loader_gx_troubleshooting_guide/>
- <https://www.rwiihacks.com/tutorials/loadersupport/index.html>
- <https://www.youtube.com/watch?v=0jBwREk6b1Y>
- <https://www.reddit.com/r/WiiHacks/comments/dxf4nt/black_screen_when_loading_games_in_usb_loader_gx/>
- <https://github.com/Leseratte10/d2xl-cios/issues/7>
- <https://github.com/wiidev/d2x-cios>
- <https://github.com/davebaol/d2x-cios>
- <https://wiibrew.org/wiki/Main_Page>
- <https://deepwiki.com/wiidev/usbloadergx/4.3-game-patching-and-compatibility>
- <https://www.reddit.com/r/WiiHacks/comments/12cvi3x/is_there_an_explanation_of_all_usb_loader_gx/>
- <https://www.gamebrew.org/wiki/Usb_Loader_Gx_Wii>
- <https://www.scribd.com/document/961697265/How-to-change-the-IOS-in-USB-Loader-GX>
- <https://gbatemp.net/threads/480p-bug-fix-for-later-wii-revisions.646029/>
- <https://usbloadergx.org/>
- <https://github.com/wiidev/usbloadergx>

## Run metadata

- **Prompt:** El USB Loader GX funciona con otros juegos. El freeze
- **Depth / breadth:** 2 / 3
- **Queries used:** 6 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 416.2 s
- **Errors during run:** 6
- **Started at:** 2026-06-09T16:13:22Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `fetch_page 'https://sourceforge.net/p/usbloadergx/issues/...': page-fetch: https://sourceforge.net/p/usbloadergx/issues/: HTTP Error 403: Forbidden`
- `fetch_page 'https://forum.wii-homebrew.com/index.php/Thread/60399-USB-Lo...': page-fetch: https://forum.wii-homebrew.com/index.php/Thread/60399-USB-Loader-GX-Blackscreen-when-loading-game/: HTTP Error 403: Forbidden`
- `fetch_page 'https://forum.wii-homebrew.com/index.php/Thread/61069-Ninten...': page-fetch: https://forum.wii-homebrew.com/index.php/Thread/61069-Nintendo-Wii-freeze-after-launching-any-game/: HTTP Error 403: Forbidden`
- `fetch_page 'https://forum.wii-homebrew.com/...': page-fetch: https://forum.wii-homebrew.com/: HTTP Error 403: Forbidden`
- `web_search 'Wii game IOS reload at scene transition ...': ddg: 0 hits parsed (possible block or empty SERP); brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`
- `fetch_page 'https://shmups.system11.org/viewtopic.php?t=70398...': page-fetch: https://shmups.system11.org/viewtopic.php?t=70398: HTTP Error 403: Forbidden`

</details>
