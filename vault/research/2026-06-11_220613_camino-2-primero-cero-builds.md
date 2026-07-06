# Camino 2 Primero — Cero Builds: Reverse-Engineering the H&S → SCENE_TITLE Black-Screen Transition

**Project:** KobiiSports Resort (Wii homebrew, Kamek C++ overlay on Wii Sports Resort PAL)
**Directive:** *Camino 2 primero. Cero builds.* — pursue the static reverse-engineering path to the title-scene handoff **first**, and produce **zero compiled artifacts** this cycle.
**Date:** 2026-06-11

---

## 1. Directive Interpretation

The instruction is two constraints, not a feature request:

| Token | Meaning in this context | Operational consequence |
|---|---|---|
| **Camino 2 primero** | Of the two open attack vectors, prioritize **Path 2: the H&S→SCENE_TITLE transition reverse-engineering / STRAP scene-exit probe** ahead of Path 1 (the WiFi-UDP networking continuation). | All effort this cycle targets *why SCENE_TITLE is never reached*, not what to do once it is. |
| **Cero builds** | No `make.py`, no Caddie `.bin`, no WBFS injection, no hardware boot. | The deliverable is **knowledge** — static disassembly, ABI maps, documented hypotheses — not a binary. Every conclusion must be reachable from RE of the golden DOL and public sources, never from a new boot. |

The "zero builds" rule is forced by the current evidence state, not an arbitrary austerity measure. The v104 falsification (2026-06-11) established that the black screen is **upstream** of SCENE_TITLE: `KSR_AUTO_HUB` at `main.cpp:8351` never executes, and the WiFi-UDP probe's intended entry point ("first SCENE_TITLE frame / OnCalculate") is therefore **unreachable on silicon**. Building another overlay variant cannot diagnose a fault that occurs before any overlay code runs. The only productive moves are static.

This report synthesizes the research learnings into (a) what we now know about the transition, (b) the competing root-cause hypotheses, (c) the zero-build forensic levers available, and (d) the preserved networking substrate that Camino 1 will resume against once Camino 2 lands SCENE_TITLE.

---

## 2. The Failure Surface — What "Black After H&S" Actually Is

### 2.1 Observed behavior

The console reaches the Health & Safety (epilepsy/seizure) warning screen, then **freezes BLACK** before the WSR title compositor renders. The auto-hub branch (decoder branch 2) confirmed SCENE_TITLE is **not** reached — the black is in the H&S→title handoff itself, not in any subsequent title-overlay draw.

### 2.2 This is NOT a publicly-documented homebrew topic

A critical negative result from research: the search surface returned **only general consumer-troubleshooting content** — HDMI/AV cables, cache reset, firmware updates, power-supply faults, overheating. There is **no public homebrew-development material** on:

- `RPSysScene` scene management internals
- STRAP scene-exit hooks
- PAL DOL transition internals
- The H&S→title scene handoff specifically

**Implication for Camino 2:** there is no shortcut, no forum thread, no prior art to copy. The transition must be reconstructed **from the WSR DOL itself** via disassembly. This is exactly why "cero builds" is the right posture — the work product is an RE map, and the map can only come from the binary.

### 2.3 Two phenomenologically-similar but distinct community symptoms

Research surfaced two consumer-level black-screen patterns that **resemble** our failure and inform the hypothesis space — but neither is our exact case, and conflating them is a trap:

| Community symptom | Trigger | Attributed cause | Documented "fix" | Relevance to us |
|---|---|---|---|---|
| Black screen right after H&S, "Press A" never appears, Wiimotes won't sync | Boot of any disc on certain consoles | **Corrupted system update / firmware** | Boot *New Super Mario Bros Wii* (bundles the 4.2 update) to repair | Matches our *location* (post-H&S) but attributes to firmware, not our Kamek hook |
| Intermittent black after pressing **Start**, in Homebrew Channel | Start press | **Non-deterministic boot-state dependency** | Hard power-off (hold power button) + reboot | Matches the v85 "title→Start→black" ceiling; suggests state-drift, not deterministic code fault |

The second symptom is the more dangerous one for our diagnosis: it asserts that an *identical binary* can pass or fail depending on **boot-state**, recoverable only by a full power-cycle. This directly corroborates the project's own `v97-v100` finding that "env/Wii state drift, NOT code" is a live alternative explanation, and the v102 finding that a latent boot bug was being **masked** by FZDIAG breadcrumbs. If our black screen is in this class, **no source change will fix it deterministically** — which is another reason builds are premature until the RE proves a code-resident fault.

---

## 3. The RPSysScene Scene-Management Layer — The Camino 2 Target

The transition we must reverse-engineer is governed by `RPSysScene`, the WSR scene-management class. Research confirmed concrete, named entry points inside the PAL DOL:

| Symbol / artifact | What it tells us |
|---|---|
| `RPSysScene::GetDbgNWC24Error()` | The scene layer carries a **NWC24/WiiConnect24 error path**. A failed NWC24 startup during scene init is a candidate freeze site — and NWC24 lives on `/dev/net/kd/request`, the same device Camino 1's net stack opens. |
| `RPSysScene::GetDbgNANDError()` | The scene layer carries a **NAND error path**. A NAND access during the H&S→title handoff that returns an unhandled error is a candidate freeze site — consistent with the project's prior NAND-persist investigations (v101/v102). |
| `RPSysDbgScenePatroler` | A debug scene-watchdog class exists in the DOL. Its presence implies the retail build retains scene-transition instrumentation that can be **read statically** and potentially **observed** without rebuilding our overlay. |

**Camino 2 thesis (high confidence):** the black screen is a state inside `RPSysScene`'s transition out of the STRAP/H&S scene and into the title scene, and the two `GetDbg*Error()` accessors name the two most likely fault domains — **NWC24 networking init** and **NAND access** — both of which the project has independently flagged as silicon-RED hazards. The zero-build task is to disassemble the `RPSysScene` transition path in the golden `main_PAL.dol` and locate where these error accessors are populated, and whether the transition blocks/loops on either.

This is the "Option A RE / STRAP scene-exit probe, plan-first" lead the memory already named as the next move — Camino 2 is its formal execution.

---

## 4. Zero-Build Forensic Levers Inside the WSR DOL

The decisive advantage for a "cero builds" cycle: **Wii Sports Resort ships with its own built-in diagnostics**, retained in the retail PAL binary. These can be exercised or read **without compiling anything of ours**.

### 4.1 The NintendoWare exception handler (post-crash fault display)

WSR (Nintendo EAD, released 2009-06-25) embeds the NintendoWare exception handler. After a crash it can be summoned with a specific input sequence on the **vertical 1st Wii Remote**:

> **HOME, A, B, 1, 2, −, +** (in order), with **D-Pad to scroll**.

**Camino 2 use:** if the black-after-H&S state is a *trapped exception* (DSI/ISI) rather than a silent livelock, this combo may surface the fault register dump (SRR0/DSISR/DAR) **on the existing hardware with the existing binary** — no rebuild. That dump feeds directly into the project's Forensic Reflex Arc (`addr2line -e externals/golden/main_PAL.dol <hex>` + `objdump` disasm). This is the single highest-value zero-build experiment: it can convert "black screen" into a faulting address, collapsing the entire RPSysScene search.

*Caveat (flagged speculation):* the exception handler only displays if the CPU actually traps and the handler's own render path still runs. If the freeze is a pre-handler livelock or a GX/video-output death, the combo will produce nothing — which is itself diagnostic (rules out trapped-exception class, pushes toward the state-drift/livelock hypothesis from §2.3).

### 4.2 The title-screen build-display debug trigger

WSR exposes a title-screen build/debug display via the combo:

> **A, B, Down, 1, 2, Up, −, +, −, +**

**Camino 2 use:** this is a *gating oracle*. If we can ever reach a state where this combo responds, the title scene's input loop is alive. In the current failure it presumably will not respond (title never reached) — but it provides a crisp, build-free **pass/fail boundary** for any future hardware check: "does the retail debug combo answer?" is a cheaper liveness probe than any custom overlay.

### 4.3 The sport scene-code-name map (for downstream Camino 1 and overlay routing)

WSR's internal scene/game-mode code names (from unused Japanese executable comments) decode to:

| Code | Sport | Code | Sport |
|---|---|---|---|
| Swf | Swordplay | Wkb | Wakeboarding |
| Jsk | Power Cruising (JetSki) | Pln | Air Sports (Plane) |
| Arc | Archery | Glf | Golf |
| Fld | Frisbee (Flying Disc) | Dgl | (Disc Golf / Frisbee Golf) |
| Bsk | Basketball | Bic | (Cycling) |
| Bwl | Bowling | Omk | (Omake / bonus) |
| Can | Canoeing | Png | Table Tennis (Ping-pong) |

This map is not directly part of the transition fault, but it is the **scene-routing vocabulary** the Camino 2 disassembly will encounter when walking the `RPSysScene` table, and it is the substrate Camino 1's hub will route into once SCENE_TITLE is recovered. Preserved here so the RE pass can label scene-table entries without re-deriving them.

---

## 5. The Preserved Networking Substrate (Camino 1 — Parked, Not Lost)

Camino 1 (the WiFi-UDP probe) is **halted at its Phase-1 gate** because its entry point — the first SCENE_TITLE frame / `OnCalculate` — is unreachable while the black-screen fault stands. Per the directive, it waits behind Camino 2. But the research has already mapped its entire ABI, and that map must be preserved intact so Camino 1 resumes at full speed the moment Camino 2 lands SCENE_TITLE. The complete substrate:

### 5.1 Architectural ground truth

- The Wii WiFi chip is **not memory-mapped** and **not accessible from PowerPC code**. All TCP/IP, WiFi, and packet handling is delegated to **IOS firmware** via IPC IOCTL calls to **`/dev/net/ip/top`** (descriptor stored in `net_ip_top_fd`).
- WiFi must be **pre-configured via the Wii System Menu** — there are **no APIs** for scanning, password entry, or connection management. Link-status failure returns **`-ENETDOWN`**.
- Source of record: libogc `network_wii.c` (devkitPro/libogc commit **c76d61d8**, original author *bushing*, 2008).

### 5.2 Socket → IOCTL command map (the binary ABI)

All socket ops route through the **single** `net_ip_top_fd` descriptor:

| Operation | Command value | Transport |
|---|---|---|
| `SO_SOCKET` | **0x0F** | `IOS_Ioctl` |
| `SO_BIND` | **0x02** | `IOS_Ioctl` |
| `SO_FCNTL` | **0x05** | `IOS_Ioctl` |
| `SO_STARTUP` | **0x1F** | `IOS_Ioctl` |
| `SO_POLL` | **0x0B** | `IOS_Ioctl` |
| `SO_SENDTO` | **0x0C** | `IOS_Ioctlv` (vectored) |
| `SO_RECVFROM` | **0x0B** | `IOS_Ioctlv` (vectored) |

> **ABI hazard (preserved):** `SO_RECVFROM` and `SO_POLL` both surface as **0x0B** in the research notes — `0x0B` is vectored RECVFROM via `IOS_Ioctlv`, while POLL appears as `0x0B` via `IOS_Ioctl`. The transport (Ioctl vs Ioctlv) disambiguates; do not collapse them on command value alone. Reconcile against the DOL before any Camino 1 build.

This reconciles with the project's own silicon-verified seals: `IOS_Ioctl_libogc=0x8003bbc0` (SO_SOCKET round-trip CONFIRMED, sock=0), `IOS_Ioctlv_libogc=0x8003bf20` (SO_SENDTO=21 bytes physically off-host, dual-proof), `IOS_Open_libogc=0x8003b1f0` (ip_fd=8). The libogc command map is the *generic* ABI; the project's `0x8003bxxx` addresses are the *WSR-bundled* instances of it.

### 5.3 Error-code mapping

IOS returns **negative error codes**, mapped by `_net_error_code_map[]` to POSIX errno:

| IOS code | POSIX | Meaning |
|---|---|---|
| −4 | EADDRNOTAVAIL | address not available |
| −6 | EAGAIN / EWOULDBLOCK | non-blocking would-block |
| −26 | EINPROGRESS | async op in progress |
| −76 | ETIMEDOUT | timed out |
| unknown | `NET_UNKNOWN_ERROR_OFFSET(−10000) + ios_retval` | unmapped |

A **sane negative error** (−4/−6 etc.) proves the dispatch reached IOS — this is the project's established "callable" oracle.

### 5.4 The non-blocking 60 Hz path (and its historic bug)

- Per-frame non-blocking recvfrom requires **`FCNTL O_NONBLOCK = 04000`** + **`MSG_DONTWAIT = 0x40`** on the socket via `SO_FCNTL` (0x05).
- **`IOS_O_NONBLOCK` is `0x04`**, not `(O_NONBLOCK >> 16)`. The original libogc code shifted an *octal* constant to **0**, so non-blocking sockets **silently did not work** until corrected to `0x04`. This is a known-good landmine: any Camino 1 non-blocking path must pass `0x04`, not a shifted value.
- `net_poll` / `net_select` exist but **`FD_SETSIZE` is capped at only 16** — adequate for our single-socket use, fatal if a design assumes many descriptors.

### 5.5 Buffers, heaps, and chunking

- `net_recvfrom()` / `net_sendto()` chunk at **`maxblocksize = NET_HEAP_SIZE/2 = 32 KB`** (NET_HEAP_SIZE = 64 KB, from **Arena 2** via `SYS_GetArena2Hi`).
- **All IOS buffers must be 32-byte aligned** (`net_malloc` from the 64 KB Arena-2 heap). Misalignment is a silent corruption source.

### 5.6 The async init state machine

Network init is a **multi-stage asynchronous state machine** (`net_init_chain`) across **three devices**, opened sequentially:

1. **`/dev/net/ncd/manage`** — link status, MAC address
2. **`/dev/net/ip/top`** — sockets
3. **`/dev/net/kd/request`** — NWC24 / WiiConnect24 startup

Constants: **`MAX_IP_RETRIES = 100`**, **`MAX_INIT_RETRIES = 32`**. `net_init()` is synchronous/blocking; `net_init_async()` drives the chain.

> **Camino 2 ↔ Camino 1 crossover (important):** the third init device, **`/dev/net/kd/request` (NWC24)**, is the **same subsystem** named by `RPSysScene::GetDbgNWC24Error()` in §3. If WSR's own scene transition attempts an NWC24 startup during the H&S→title handoff and that startup hangs or errors unhandled, it would manifest exactly as our **black-after-H&S** freeze. **This is the strongest cross-path hypothesis:** the thing blocking Camino 2 (scene transition) may be a **failed NWC24 init** — the very subsystem Camino 1 needs. Verifying this is a pure-RE task: trace whether the retail RPSysScene transition path calls into the kd/request init chain and whether it can block there.

---

## 6. Root-Cause Hypothesis Matrix (Pre-RE)

| # | Hypothesis | Evidence for | Evidence against | Zero-build test |
|---|---|---|---|---|
| H1 | **Trapped CPU exception** (DSI/ISI) in the scene transition | Project's Reflex Arc is built for this; v104 freeze is hard | If handler combo yields nothing, weakens it | Press the **HOME,A,B,1,2,−,+** exception combo on the frozen console |
| H2 | **Unhandled NWC24 error** during RPSysScene transition (kd/request hang) | `GetDbgNWC24Error()` exists; kd/request is in the init chain; networking is silicon-fragile here | Retail WSR boots fine for normal users → would need our overlay to perturb it | RE the RPSysScene transition for kd/request calls; check for blocking retry loops (`MAX_INIT_RETRIES=32`) |
| H3 | **Unhandled NAND error** during transition | `GetDbgNANDError()` exists; project has live NAND-RED history (v101/v102) | Same retail-boots-fine objection | RE the transition for NAND access + error population of the Dbg accessor |
| H4 | **Non-deterministic boot-state drift**, not code | Community Homebrew "black after Start, fixed by power-cycle" symptom; project's own v97-v100 / v102-FZDIAG-masking findings | A deterministic RE fault would contradict it | Cannot be settled by RE alone; requires controlled power-cycle A/B (a *future* hardware step, still zero-*build*) |
| H5 | **Our overlay perturbs an otherwise-healthy transition** (Kamek hook timing) | v104 proved our auto-hub code never even runs → if the hook *install* itself destabilizes IOS/scene state, fault precedes our code | If a **bit-perfect v85 re-inject** also blacks, our delta is exonerated | Compare current binary's hook-install footprint vs v85 statically; no rebuild needed to *read* the diff |

**Prioritization under "Camino 2 primero":** H2 and H3 are the two RE-resolvable, code-resident hypotheses that the named `RPSysScene::GetDbg*Error()` symbols directly point at — they are the spine of Camino 2. H1 is the cheapest single experiment (one button combo, no build) and should be fired first as a triage gate. H4/H5 are the "it's not our code" branches that RE can *narrow* but only a controlled hardware A/B can *settle* — and notably **neither requires a build**, only a boot of an *existing* binary, keeping the cycle compliant with "cero builds."

---

## 7. Recommended Camino 2 Execution Plan (Zero Builds)

All steps are static RE or exercise the **existing** retail/last-shipped binary. No `make.py`, no injection.

1. **Exception-handler triage (cheapest, do first).** On the frozen v104 console, fire **HOME,A,B,1,2,−,+** on the vertical Wiimote, D-Pad to scroll. If a fault dump appears → capture SRR0/DSISR/DAR → run the Reflex Arc (`addr2line`/`objdump`) → H1 confirmed, search collapses to one address. If nothing → H1 weakened, proceed to static RE.
2. **Disassemble the RPSysScene STRAP/H&S→title transition** in `externals/golden/main_PAL.dol`. Locate the scene-exit path out of the H&S/STRAP scene and the entry into the title scene. Label scene-table entries using the §4.3 code-name map.
3. **Trace the two Dbg error accessors.** Find where `GetDbgNWC24Error()` and `GetDbgNANDError()` storage is **written**. Any write site inside the transition path is a candidate freeze locus (H2/H3). Check for blocking retry loops bounded by `MAX_INIT_RETRIES=32` / `MAX_IP_RETRIES=100`.
4. **Check for a kd/request (NWC24) init call in the transition** (the §5.6 crossover). If the retail transition opens `/dev/net/kd/request` and can block, H2 is structurally confirmed and Camino 1's parked work becomes the actual blocker.
5. **Static delta vs v85.** Read (do not rebuild) the hook-install footprint of the current binary against the v85 baseline to test H5 — is our Kamek install touching scene/IOS state before the retail transition runs?
6. **Document, do not build.** Output = an RE map: faulting address (if H1), or annotated transition disassembly with the candidate block site (H2/H3), or an exoneration of our delta (H5). The map is the deliverable that unblocks the *next* (build-bearing) cycle.

---

## 8. Open Questions Carried Forward

- **Did the title ever render, or was it black-immediately-post-H&S?** (Memory's explicit OPEN item.) The exception-combo triage in step 1 partially answers this: a handler that renders proves the GPU/video path survived H&S.
- **Is the fault deterministic or state-drift (H4)?** RE cannot settle this; a controlled power-cycle A/B on the existing binary is required — permissible under "cero builds," but it is a *hardware* step, not an RE step. Flag for the Owner as the one experiment Camino 2's RE cannot replace.
- **Does WSR's own transition depend on NWC24 success?** If retail WSR tolerates NWC24 failure but our hooked binary does not, the regression is in how our install changes IOS/scene state, not in WSR's logic.

---

## 9. Summary

**Camino 2 primero, cero builds** is the correct posture because v104 proved the black screen is upstream of all our overlay code — no build can diagnose it. The research gives Camino 2 a concrete spine: the `RPSysScene` scene layer carries two named, statically-traceable error domains — **NWC24** (`GetDbgNWC24Error`) and **NAND** (`GetDbgNANDError`) — that are the two most probable freeze loci, and WSR ships a **built-in exception handler** (HOME,A,B,1,2,−,+) that can convert the freeze into a faulting address with **zero builds**. The entire libogc/IOS networking ABI (devices, IOCTL command map 0x02–0x1F, error codes, the `IOS_O_NONBLOCK=0x04` landmine, 32-byte alignment, the 3-device async init chain) is preserved intact for Camino 1, which resumes the instant Camino 2 recovers SCENE_TITLE — with the strong, RE-testable suspicion that the same **kd/request / NWC24** subsystem blocking Camino 2 is exactly what Camino 1 was reaching for.

The next action is non-destructive and build-free: **fire the exception-handler combo on the frozen console, then disassemble the RPSysScene transition.**

## Sources

- <https://deepwiki.com/devkitPro/libogc/7.1-wii-network-stack>
- <https://github.com/devkitPro/libogc>
- <https://wiibrew.org/wiki/Libogc>
- <https://devkitpro.org/viewforum.php?f=40>
- <https://bot.libretro.com/doxygen/a06278_source.html>
- <https://deepwiki.com/devkitPro/libogc/3.3-ipc-and-ios-services>
- <https://github.com/Poligraf/retroarch-retrofwunofficial/blob/main/wii/libogc/libogc/network_wii.c>
- <https://www.reddit.com/r/WiiHacks/comments/gus16t/wii_freezes_after_health_and_safety_screen/>
- <https://gbatemp.net/threads/black-screen-on-the-homebrew-channel.221001/>
- <https://www.ifixit.com/Answers/View/33250/Freezing+up+at+Black+Health+Screen>
- <https://www.wiichat.com/threads/help-black-screen-after-health-screen-idk-where-to-put.83909/>
- <https://stealthygaming.com/fix-wii-black-screen/>
- <https://gamebanana.com/games/6332>
- <https://gamebanana.com/games/6532>
- <https://www.reddit.com/r/wii/comments/mkc6zb/every_time_i_try_to_load_wii_sports_resort_it/>
- <https://tcrf.net/Wii_Sports_Resort>
- <https://www.reddit.com/r/WiiHacks/comments/h8y8ss/wii_sports_resort_dead_black_screen_wiiflow/>

## Run metadata

- **Prompt:** Camino 2 primero. Cero builds.
- **Depth / breadth:** 2 / 3
- **Queries used:** 4 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 457.4 s
- **Errors during run:** 0
- **Started at:** 2026-06-11T20:06:13Z
- **Module version:** deep_research 0.1.0
