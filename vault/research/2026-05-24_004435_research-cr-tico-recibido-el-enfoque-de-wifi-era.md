# Critical Research Report — WiFi Approach for KobiiSports Resort

**Date:** 2026-05-24
**Scope:** Reconciliation of the v90/v91 IOS-IPC bypass strategy against libogc 3.1.0 ground truth, Hollywood IPC hardware reality, and the WiiConnect24/replacement-server landscape.
**Verdict (lede):** The original "direct MMIO bypass of libogc at 0xCD000000" framing is **technically legal on AHBPROT-disabled stacks but strategically wrong for KSR**. The evidence overwhelmingly favors the libogc IOS dispatch path (the same one v61–v66 already proved). The single remaining justification for raw MMIO — libogc unavailability — does not apply: the v85 baseline already links libogc and reaches `IOS_Open("/dev/net/ip/top")`. Pivoting to MMIO forfeits 4+ years of correctness patches for a problem that does not exist.

---

## 1. Executive Summary

The "WiFi enabling" problem for KSR was framed during Phase 1 as a binary choice between two candidates:

| Candidate | Description | Strategic cost |
|---|---|---|
| **A (shipped v91)** | Call `__ipc_queuerequest = 0x8003ae90` directly | Bypasses libogc state machine, retains hardware contract |
| **S (eliminated by Owner)** | Direct MMIO write to `HW_IPC_PPCMSG @ 0xCD000000` | Bypasses libogc AND Starlet contract; forfeits all future fixes |

The research below confirms the Owner's bilateral-evidence rule correctly eliminated Candidate S. More importantly, **a third path (Candidate L — full libogc `net_init` chain) was not on the table and is the real shortest line to a network-enabled overlay** — because libogc has shipped active correctness patches to the exact code path KSR needs as recently as 2026 (3.0.2 `h_addrtype/h_length` size fix, `SOCK_NONBLOCK`, `inet_pton` footprint reduction, `network_wii` `STACK_ALIGN` fix in 2.13.0).

The KSR injection environment (Kamek module, no libogc relink) makes Candidate A correct **only if libogc symbols at the v85 WSR PAL DOL addresses are silicon-real**. The Phase 1 GREEN triangulation already proved they are — `__IPCReadReg=0x8003a8c0`, `__IPCWriteReg=0x8003a8d0`, `DCFlushRange=0x800460e0`, `DCInvalidateRange=0x800460b0`, `__ipc_queuerequest=0x8003ae90`. We are not bypassing libogc — we are **statically linking against the WSR-embedded libogc-equivalent IPC core** through the cast-iron PPC ABI.

The deeper finding: **Phase 1's "WiFi RE" rename of the problem space was itself a misdirection**. There is no WiFi configuration code on the Broadway PPC. All WiFi hardware (BCM4318 + abstracted radio) is mediated by the Starlet ARM through IOS. The PPC's job is to (1) talk IPC to IOS, (2) request a socket, (3) chunk data. The "WiFi enable" boils down to `IOCTL_SO_STARTUP=0x1F` on `/dev/net/ip/top` after the NCD link is up — which is a five-line call sequence, not a stack rewrite.

---

## 2. The Hollywood IPC Mailbox — Hardware Ground Truth

### 2.1 Register Map

The PPC-visible IPC surface is exactly three registers at base `0xCD000000` (PPC alias of the Starlet view `0x0D800000`):

| Offset | Register | Direction | Width | Purpose |
|---|---|---|---|---|
| +0x000 | `HW_IPC_PPCMSG` | Broadway → Starlet | 32-bit | Pointer to a 0x40-byte ipcreq struct in MEM1 |
| +0x004 | `HW_IPC_PPCCTRL` | Broadway R/W (X1,X2), R+W1C (Y1,Y2) | 32-bit | Control/flags (low 6 bits) |
| +0x008 | `HW_IPC_ARMMSG` | Starlet → Broadway | 32-bit | Pointer to response (read-only from PPC) |
| +0x00C | `HW_IPC_ARMCTRL` | **Starlet-only** | 32-bit | Hardware-masked from PPC by AHB_TRUSTED_OFFSET (addr bit 23) |

The PPC alias `0x0Dxxxxxx` forces address bit 23 to zero internally — this is **why Broadway can never reach `+0x00C`**: it is a hardware mask, not a convention. The frequent misreading (cited gbatemp thread by Nintendo Maniac) that conflates `PPCMSG` and `PPCCTRL` into a single word is wrong; the pointer is a full 32-bit value because the registers are physically separate.

### 2.2 PPC-Side Flag Protocol

Four shared flags route the handshake:

| Flag | PPC role | Starlet role | Hollywood IRQ |
|---|---|---|---|
| X1 | Set on send | Cleared on read | IRQ #31 (Starlet) via IX1 |
| X2 | Set on ack | Cleared on relaunch | IRQ #31 (Starlet) via IX2 |
| Y1 | Read+W1C (reply ready) | Set on reply | IRQ #30 (PPC, vector `IRQ_PI_ACR`) via IY1 |
| Y2 | Read+W1C (ack of prior) | Set on receive | IRQ #30 (PPC) via IY2 |

PPC bit constants:

```
HW_IPC_PPC_SEND      = 0x01   (X1: "new pointer in PPCMSG")
HW_IPC_PPC_MSG_ACK   = 0x02   (Y2: ack prior Starlet message)
HW_IPC_PPC_CTRL_ACK  = 0x04   (Y1: reply ready, W1C to clear)
```

A canonical send is `PPCCTRL = X1 | Y2 = 0x03`. The reply handler clears via `PPCCTRL = Y1 | X2 = 0x05`.

### 2.3 The ipcreq Struct

libogc's `ipc.c` enforces a 0x40-byte request with first field = command:

| Code | Command |
|---|---|
| 0x01 | IOS_OPEN |
| 0x02 | IOS_CLOSE |
| 0x03 | IOS_READ |
| 0x04 | IOS_WRITE |
| 0x05 | IOS_SEEK |
| 0x06 | IOS_IOCTL |
| 0x07 | IOS_IOCTLV |

Every embedded pointer **must be translated** with `MEM_VIRTUAL_TO_PHYSICAL` (subtract `0x80000000`), the entire request + every input buffer must be flushed with `DCFlushRange`, and every output buffer must be invalidated with `DCInvalidateRange`. Buffers must reside in **MEM1 (first 24 MB)**; queue depth is 16 (`IPC_EQUEUEFULL = -8`).

### 2.4 Error Code Range

| Code | Symbol | Meaning |
|---|---|---|
| 0 | IPC_OK | success |
| -4 | IPC_EINVAL | invalid argument |
| -5 | IPC_ENOHEAP | IOS heap exhausted |
| -6 | IPC_ENOENT | path not found |
| -8 | IPC_EQUEUEFULL | 16-deep queue saturated |
| -22 | IPC_ENOMEM | OOM on copy |

IOS version is stored at `0x80003140`. `IOS_ReloadIOS` triggers `IOS_IoctlvReboot`; post-reload state is reset by `__IPC_Reinitialize()` without full teardown.

---

## 3. AHBPROT — When Direct MMIO Becomes Legal

`AHBPROT` lives at `0x0D800064`. Each bit gates PPC access to a specific Hollywood engine (AES, SHA, NAND, SD, OH0, OH1, EHCI…). TMD access-rights bits and IOS `syscall_54` OR/AND the register with `0x80000DFE` to grant or revoke PPC engine access. This is the exact mechanism **BootMii** and **HBC-with-AHBPROT-disabled** exploit to let the PPC drive engines directly.

Implication for KSR: **AHBPROT is locked from disc-launched titles**. KSR runs from a WBFS-injected boot via the standard disc channel — Sysmenu hands control to the title with AHBPROT in default-locked state. Any direct MMIO write to engines beyond the IPC mailbox three-register window will silently no-op or trap. Even the IPC mailbox itself, while readable, **cannot deliver a request without IOS cooperation on the Starlet side** — the Starlet validates the ipcreq, and an out-of-band ipcreq with a malformed cmd field, an unflushed cache, or a non-MEM1 pointer will be rejected (best case) or hang the queue (worst case, observed in v49 with `c514`).

This is the structural reason Candidate S is wrong: it would have worked on a BootMii-launched homebrew but is silently disarmed in the KSR distribution model.

Mini's `hollywood.h` (fail0verflow / Bushing / Sven Peter / Hector Martin / John Kelley, 2008–2009, GPLv2) remains the canonical register name source. It uses `HW_REG_BASE = 0x0D800000` (Starlet view) vs `HW_PPC_REG_BASE = 0x0D000000` (PPC alias).

---

## 4. libogc Wii Network Stack — Authoritative Map

### 4.1 Initialization State Machine (`net_init_chain`)

| State | Action | Device | Notes |
|---|---|---|---|
| 0–2 | NCD link bring-up | `/dev/net/ncd/manage` | `IOCTL_NCD_GETLINKSTATUS=0x07`, `IOCTLV_NCD_GETMACADDRESS=0x08` |
| 3 | Open IP top | `/dev/net/ip/top` | fd stored in global `net_ip_top_fd` |
| 4–7 | KD init | `/dev/net/kd/request` | `IOCTL_NWC24_STARTUP=0x06` |
| 8 | Final activation | `/dev/net/ip/top` | `IOCTL_SO_STARTUP=0x1F` |

Constants: `MAX_IP_RETRIES=100`, `MAX_INIT_RETRIES=32`, `NET_HEAP_SIZE=64KB` from `SYS_GetArena2Hi()` (Arena 2). WiFi link failure returns `-ENETDOWN`. **WiFi config is not exposed to PPC** — there is no API to scan SSIDs or set WPA keys from Broadway. All radio control is Starlet-side; the PPC inherits whichever AP the user selected in System Settings.

### 4.2 `/dev/net/ip/top` IOCTL Map — Verified

This table reconciles v20000.61–62 KSR empirical findings with libogc 3.1.0 source:

| Opcode | Symbol | Type | KSR status |
|---|---|---|---|
| 0x01 | `IOCTL_SO_ACCEPT` | IOCTL | unverified |
| 0x02 | `IOCTL_SO_BIND` | IOCTL | **v66 GREEN** |
| 0x03 | `IOCTL_SO_CLOSE` | IOCTL | implied |
| 0x04 | `IOCTL_SO_CONNECT` | IOCTL | unverified |
| 0x05 | `IOCTL_SO_FCNTL` | IOCTL | **v66 GREEN** |
| 0x09 | `IOCTL_SO_SETSOCKOPT` | IOCTL | unverified |
| 0x0A | `IOCTL_SO_LISTEN` | IOCTL | unverified |
| 0x0B | `IOCTLV_SO_RECVFROM` / `IOCTL_SO_POLL` | dual-use | **v66 GREEN** (RECVFROM) |
| 0x0C | `IOCTLV_SO_SENDTO` | IOCTLV | **v62 GREEN** (21 B off-host) |
| 0x0E | `IOCTL_SO_SHUTDOWN` | IOCTL | unverified |
| 0x0F | `IOCTL_SO_SOCKET` | IOCTL | **v61 GREEN** (sock=0) |
| 0x10 | `IOCTL_SO_GETHOSTID` | IOCTL | unverified |
| 0x11 | `IOCTL_SO_GETHOSTBYNAME` | IOCTL | unverified |
| 0x1C | `IOCTLV_SO_GETINTERFACEOPT` | IOCTLV | unverified |
| 0x1F | `IOCTL_SO_STARTUP` | IOCTL | unverified — **KSR_SO_STARTUP counter still 26 (was 31)** |

**Critical insight:** v66's RECVFROM/BIND/FCNTL green proves the libogc-equivalent path at `0x8003bbc0` (`IOS_Ioctl`) and `0x8003bf20` (`IOS_Ioctlv`) is end-to-end live. There is **no remaining unknown in the IPC layer**. The only gap is `IOCTL_SO_STARTUP` — and skipping it appears to work (sock=0 was returned without it), which means either Starlet auto-startup occurred or the libogc state machine progressed past state 7 implicitly when Sysmenu launched KSR.

### 4.3 Parameter Struct Sizes — FIXED

| Struct | Size | Notes |
|---|---|---|
| `bind_params` | 36 B | socket + sockaddr + len |
| `connect_params` | 36 B | identical to bind |
| `sendto_params` | 40 B | adds flags + destaddr presence |
| `setsockopt_params` | 32 B | level + optname + optlen + buffer |
| `getinterfaceopt_params` | 8 B | id + value |

All buffers **32-byte aligned** (`net_malloc()` + `STACK_ALIGN()`).

### 4.4 Wii Custom `sockaddr_in` — Endianness Trap

Wii's `sockaddr_in` is **8 bytes, not 16**:

```c
struct sockaddr_in {
  u8  sa_len;        // auto-populated to 8
  u8  sa_family;     // AF_INET = 2
  u16 sin_port;      // network order
  u32 sin_addr;      // network order
  // NO sin_zero[8] padding
};
```

This is the exact landmine v66 hit when re-encoding to `u8[12]`: `sa_family` ended up at offset 1 with `af_byte=0x02`, but the surrounding bytes formed `af=0x02000000` when reinterpreted as a `u32`, returning `-SO_EAFNOSUPPORT` (-5). The fix was to revert to the v61-proven `u32[3]` hand-layout matching libogc's actual struct.

[[PILLAR_49_WII_NET_PROTOCOL_BINARY]] §49.1 codifies this: **"Read Dolphin source first, write last."** Three consecutive first-pulse greens followed from honoring the BE-PPC network-order + verbatim `ToNativeAddrIn` copy semantics in Dolphin's IOS_Net implementation.

---

## 5. IOS Memory Model — Hard Constraints

### 5.1 Heap Sizing

`NET_HEAP_SIZE = 64 KB` from Arena 2. `maxblocksize = NET_HEAP_SIZE / 2 = 32 KB`. **Every transfer over 32 KB must chunk** through repeated `IOS_IoctlvFormat()` calls.

### 5.2 Chunking Semantics

| Function | Loop break condition | Returns on partial |
|---|---|---|
| `net_sendto()` | error code on any chunk failure | error code, **NOT bytes-already-sent** — caller cannot resume |
| `net_recvfrom()` | (a) all received, (b) `received<=0`, (c) `received<blockSize` (TCP boundary) | bytes received |

The `received<blockSize` short-read break is how libogc detects TCP message boundaries without a separate framing layer. KSR's per-frame `KobiiNetLiveTick` (designed in v63–v65 but never observed ticking per [[PILLAR_50]]) must respect this: never send >32 KB in a single call, and treat short receives as message delimiters not partial reads.

### 5.3 TCP Window Forcing

`net_socket()` automatically issues `SO_RCVBUF = 32 KB` setsockopt on every new TCP socket — there is no way to negotiate a larger window from the PPC.

### 5.4 IOS → POSIX Error Map (`_net_error_code_map[]`)

| IOS | POSIX | Meaning |
|---|---|---|
| -1 | E2BIG | argument list too long |
| -2 | EACCES | permission denied |
| -3 | EADDRINUSE | address already in use |
| -4 | EADDRNOTAVAIL | cannot assign requested address |
| -5 | EAFNOSUPPORT | address family not supported |
| -6 | EAGAIN | resource temporarily unavailable |
| -14 | ECONNREFUSED | connection refused |
| -15 | ECONNRESET | connection reset by peer |
| -26 | EINPROGRESS | operation now in progress |
| -30 | EISCONN | already connected |
| -38 | ENETDOWN | network is down — **WiFi link failure** |
| -40 | ENETUNREACH | network unreachable |
| -49 | ENOMEM | OOM |
| -56 | ENOTCONN | not connected |
| -76 | ETIMEDOUT | timed out |

Unknown codes return `NET_UNKNOWN_ERROR_OFFSET (-10000) + ios_retval`. **KSR observation**: v90's MMIO probe got `0xCD000000` returned (= uninitialized poison from reading a dead register), which is **not** in this map — confirming the call never reached IOS dispatch, never reached the error path, just read garbage from a register that was never written by Starlet. This is a positive forensic signature.

---

## 6. libogc 3.x ABI Drift — Active Hazard

libogc reached **3.1.0** (docs generated Sun May 3 2026). Multiple breaking renames and structural changes have accumulated since the era of the v85 WSR DOL libogc-equivalent:

### 6.1 Cache Primitive Renames (2026-01-25, libogc 3.0 "tuxedo")

| Old | New |
|---|---|
| `DCStoreRange` | `PPCDCacheStore` |
| `DCStoreRangeNoSync` | `PPCDCacheStoreAsync` |
| `DCFlushRange` | `PPCDCacheFlush` (in 3.x parallel rename) |
| `DCInvalidateRange` | `PPCDCacheInvalidate` |

Downstream impact documented: wii-opengx 0.17.0-1 fails to link against libogc 3.0.3-1 until source-patched.

### 6.2 Header/API Reshuffle

- `gettime` and `diff_msec` dropped/renamed — breaks pre-2026 launcher `main.c`/`shutdown.c`/`update.c`.
- `libfat-ogc` no longer exposes `io/fat.h` and `io/fat-sd.h` in standard include paths.
- libogc 3.x ships its own `inet_ntop` / `inet_pton`, **conflicting with libwiisocket** (multiple-definition link errors on devkitPPC r45 / GCC 15.2.0 / `devkitpro/devkitppc:latest` Docker image and macOS Sonoma 14.x).

### 6.3 Low-Level Restructuring

libogc 3.0.0 introduced the **Tuxedo/Calico** low-level layer replacing LWP, freeing ~1 MB of system RAM previously held by LWP heap. Added BSD socket header shims and default reset/power button handling via `SYS_MainLoop`. devkitPPC r49 added pthread/c11/std::thread support. WiFi control added by contributor **abdelali221** in PR #247.

### 6.4 Active Correctness Patches

| Version | Fix |
|---|---|
| 3.0.2 | `h_addrtype/h_length` size fix |
| 3.x | `SOCK_NONBLOCK` implementation |
| 3.x | `inet_pton` lowered footprint (adopted from libnx) |
| 2.13.0 | `network_wii` `STACK_ALIGN` fix |
| 3.x | SD SDHS support (DacoTaco, PR #232) |
| 3.x | ES `ISALIGNED` operator-precedence fix |

**Implication for KSR Candidate A:** by calling the *v85 WSR PAL DOL* libogc-equivalent at fixed addresses, we **inherit the 2007-era libogc** snapshot — meaning none of these correctness patches apply. For UDP datagram telemetry off-console, this is acceptable; for any production-grade TCP, NWC24 mail, or SSL workload, it is a known hazard surface. The `STACK_ALIGN` fix in 2.13.0 alone is sufficient to crash unaligned buffers — KSR's `KobiiNetLiveTick` must hand-align with `__attribute__((aligned(32)))` to compensate.

### 6.5 Internal IPPROTO Force

Wii socket protocol is internally forced to `IPPROTO_IP` for compatibility — meaning user-requested `IPPROTO_TCP`/`IPPROTO_UDP` distinctions are normalized away by libogc before reaching IOS. The protocol is encoded in the socket *type* (`SOCK_STREAM` vs `SOCK_DGRAM`), not the protocol field.

---

## 7. WiiConnect24 — The Offline Path

### 7.1 What WC24 Actually Is

WC24 is the codename for the `/dev/net/kd` IOS driver. Architecturally it is:

- **~360 KB** of IOS code (the kd module proper).
- **Depends on**: SSL, SO (socket), WL/ETH drivers — together comprising ~75% of total IOS firmware.
- **Lets the Starlet ARM perform network tasks while Broadway is powered off** (this is the headline feature).
- Includes: task scheduler with **thermal duty-cycle limits** ("Too much wakeup executed recently. Need to wait."), mail engine, RTC sync over SSL to `vtp.wapp.wii.com`, and a JavaScript-variant VM for CHANS channel scripts.

### 7.2 NANDBOOTINFO Email-Triggered Boot

WC24 can **boot NAND titles from email attachments** when the system is idle/standby. Mechanism:

1. Wakeup flag in `/shared2/wc24/nwc24msg.cfg` must be non-zero (default 0).
2. Next-wakeup timestamp in `/shared2/wc24/misc.bin`.
3. Mail must have:
   - `X-Wii-Cmd` bit 17 set (`0x20000`)
   - `(value & 0x00ffffff) - 0x20001 <= 1`
   - `X-Wii-AppID` first field = 1 (so sysmenu ignores)
4. Demonstrated by libwc24 SVN's `wc24app` + `wc24testboot` mail — booted HBC via this path.

**Limitations**:
- NAND titles only — **cannot launch discs**, which means KSR (disc-launched) cannot self-bootstrap via this path.
- `X-Wii-MB`/`X-Wii-Cmd`/`X-Wii-AppID` headers are **stripped from direct SMTP mail** — only HTTP-delivered WC24 mail honors them.

### 7.3 WC24 File Structures — Direct Manipulation Vectors

**`/shared2/wc24/nwc24dl.bin`** (63,488 bytes — per WSR-Patcher `nwc24dl.h`, WiiLink24):

| Region | Size | Content |
|---|---|---|
| Header | 128 B | `DLListHeader`: magic `'WcDl'=0x5763446C`, version=1, `max_entries ≤120`, `max_subentries=32` |
| Records | 120 × 16 B | `DLListRecord`: low_title_id, next_dl_timestamp, last_modified_timestamp, flags |
| Entries | 120 × 512 B | `DLListEntry`: full title id, group_id, retry policy, error tracking, 32 subtask timestamps, 236-char dl_url, 64-char filename, root CA flag |

**WSR title constants**:

| Constant | Hex | ASCII |
|---|---|---|
| `WSR_NO_REGION` | `0x525A5400` | `'RZT\0'` |
| `WS_PLUS_WSR_NO_REGION` | `0x53503200` | `'SP2\0'` |

**`/shared2/wc24/nwc24msg.cfg`** (1024 B, wiibrew): magic `'WcCf'=0x57634366`, version=8, holds NWC24 ID @ `0x08`, 5 × 0x80-byte mail engine URLs @ `0x9C` (amw/rcw/mtw `.wc24.wii.com` — Nintendo defunct 2013, RiiConnect24 restored). **IOS SSL client cert required** to reach original servers.

### 7.4 Strategic Read for KSR

WC24 is **not the right surface for KSR live telemetry** (live UDP/TCP via `/dev/net/ip/top` is faster, simpler, and already proven in v62/v66). But it is the **canonical surface for**:

- **Offline content delivery** — schedule overnight downloads of new sport packs, voice-clip refreshes, KobiiMii face updates.
- **Persistent mailbox** — receive Owner-facing notifications even when console is off.
- **Standby telemetry** — push run-result digests to RiiConnect24 mailbox without holding the PPC live.

This is a Phase 3+ feature, not Phase 2.

---

## 8. Replacement Server Landscape (2026)

Nintendo discontinued WC24 + NWFC in 2013–2014. Two homebrew replacement stacks are live as of 2026:

### 8.1 RiiConnect24

- Domain: `rc24.xyz`
- GitHub: `RiiConnect24/RiiConnect24-Patcher`
- **Patcher v1.6.0 deprecated** — reroutes channel patching to WiiLink.
- **Unix v1.2.0** added **native Dolphin WC24 support** (Dolphin ≥ 5.0-17611), eliminating the prior VFF Downloader requirement.

### 8.2 WiiLink

- Domain: `wiilink.ca`
- GitHub: `WiiLink24/WiiLink-Patcher-GUI` (maintainer Harry / hwalker56)
- Most recent issue tracked: **#40 dated 2026-04-30** (active).
- Replaces **both** WiiConnect24 AND Nintendo Wi-Fi Connection — making it the single integration point for KSR's eventual online layer.

### 8.3 Known WC24 Error Codes

| Code | Meaning |
|---|---|
| 32002 | server overload |
| 32030 | maintenance |
| 20110 | NWFC discontinued (→ Wiimmfi-class replacement) |
| 20102–20109 | Cluster: bans, Console Identifier collisions, MAC-based account caps |

**KSR strategic implication**: any production telemetry layer should be tested against **WiiLink first** (single stack, active maintenance), with RiiConnect24 fallback only for users who have already provisioned it. The Patcher v1.6.0 deprecation message confirms this is the upstream-preferred path.

---

## 9. Reconciling Phase 1 RE With This Research

The Phase 1 WiFi RE GREEN findings stated:
> WSR PAL DOL libogc TU @ `0x8003axxx–0x8003cxxx` has silicon-RED wrappers (IOS_Open etc.) BUT silicon-real bare-MMIO helpers (`__IPCReadReg=0x8003a8c0`, `__IPCWriteReg=0x8003a8d0`, `DCFlushRange=0x800460e0`, `DCInvalidateRange=0x800460b0`).

This research **confirms and refines**:

| Phase 1 claim | Research verdict | Refinement |
|---|---|---|
| Hollywood IPC mailbox at `0xCD000000` is silicon-uniform across all IOS versions | **CORRECT** | libogc/ipc.h:33 compile-time literal — the three-register mailbox is hardware, not IOS code. |
| Wrappers (`IOS_Open` etc.) are silicon-RED | **PARTIALLY CORRECT** | The wrappers themselves dispatch through `__ipc_queuerequest=0x8003ae90` which IS silicon-real. The "RED" status is likely a **symbol-resolution** issue (wrapper name doesn't appear in `externals/PAL.txt`) not a runtime issue. |
| Direct-MMIO bypass is ~60 LOC | **CORRECT BUT MISLEADING** | The 60 LOC is the ipcreq builder + cache flush + register write. It does **not** include the reply handler, queue serialization, or the Starlet contract validation. A *robust* MMIO IPC reimplementation is closer to libogc's full `ipc.c` (~800 LOC). |
| Calling `__ipc_queuerequest=0x8003ae90` directly is the cleanest path (Candidate A) | **CORRECT** | This is **functionally equivalent to using the wrapper** — the wrapper is just a thin shim that builds the ipcreq and calls `__ipc_queuerequest`. Skipping the wrapper saves one stack frame and the symbol-resolution risk. |

**Verdict on v91 ship**: structurally sound. The probe directly exercises `__ipc_queuerequest=0x8003ae90` which is the same entry point libogc's `IOS_Open` would have reached anyway. The reduction is the right call — fewer unverified addresses in the call chain means tighter failure-mode discrimination.

---

## 10. Recommendations — Phase 2 Forward

### 10.1 Immediate (next 1 pulse)

1. **Validate v91 boot result**. If GREEN: Candidate A is the production path; seal `__ipc_queuerequest=0x8003ae90` as Tier-S and graduate to step 2.
2. **Add `IOCTL_SO_STARTUP=0x1F` probe** if v91 returns sock fd but RECVFROM hangs. The v66 success may have been the Sysmenu auto-startup leaking through; an isolated KSR overlay may need an explicit startup call.

### 10.2 Short-term (Phase 2 completion)

3. **Rewire `KobiiNetLiveTick` per [[PILLAR_50]]** — the hook is NOT wired until observed ticking. v63/v64 RED_TIMEOUT proved per-frame `OnCalculate` does not fire on scene-0; the fix is to nest the tick INSIDE the OnConfigure path that already proved live in v66 (bounded burst cadence, not 60 Hz).
4. **Adopt the Dual-Proof Standard ([[PILLAR_49]] §49.2)** for every new opcode: device echo (Dolphin `[IOS_NET]` log) + off-host capture (GEX44 listener). Sane-negative-no-echo is a v57-trap — hard-fail.
5. **Codify the 8-byte sockaddr_in layout in a header** — `kobii_net_types.h` with `static_assert`-equivalent negative-array assertions (devkitPPC has no `static_assert` or `__builtin_offsetof`). This prevents the v66 endianness regression.

### 10.3 Medium-term (Phase 3)

6. **Don't bypass libogc — fork it.** The drift hazard documented in §6 is real but containable. Vendor libogc 3.1.0 source into `tools/caddie/vendor/libogc/` and freeze. This gives KSR access to `STACK_ALIGN`, `SOCK_NONBLOCK`, and the SSL fixes without committing to upstream's release cadence.
7. **Defer WC24 integration to a discrete milestone.** It is its own 360 KB problem space with its own server contract (WiiLink/RiiConnect24). Treat it as a separate IOS device (`/dev/net/kd/request`) campaign, not an extension of the current `/dev/net/ip/top` work.

### 10.4 Long-term — Contrarian Suggestion (Speculation flagged)

8. **Skip socket telemetry entirely; use NCD-MAC + USB-Gecko backchannel for the live loop.** Hot take: every UDP packet from KSR has to cross WiFi → Starlet → IPC → MEM1 → PPC, with all the chunking and alignment overhead. A USB-Gecko on EXI port 0 or 1 gives ~1 MB/s deterministic backchannel with **zero IOS involvement** — perfect for the headless GEX44 forensic loop. The cost is one cable per dev console. Worth evaluating before committing to 60 Hz socket cadence as the canonical telemetry surface.

---

## 11. Mistakes Registry Additions (Proposed)

Three new entries crystallized by this research:

| # | Title | Trigger | Reflex |
|---|---|---|---|
| #49 | Direct-MMIO Mirage | Proposal to bypass libogc via raw `0xCD000000` writes | Check AHBPROT state first; if locked, reject. If unlocked, weigh against §10.6 vendoring strategy. |
| #50 | libogc Symbol-Resolution Conflation | Symbol marked "silicon-RED" but functionally works through underlying dispatch | Re-test: call the wrapper AND its dispatch entry; if both succeed, the RED is a naming artifact not a runtime failure. |
| #51 | sockaddr_in BSD Reflex | Hand-writing a `sockaddr_in` and assuming 16 bytes | Use 8 B Wii custom layout; encode with `u32[3]` not `u8[12]`; verify against Dolphin `[IOS_NET]` `IOCTL_SO_BIND` decoded output. |

---

## 12. Closing — The Real Pivot

The phrase "El enfoque de WiFi era…" (the WiFi approach **was**…) implies a past tense. The research validates that pivot. **The WiFi approach WAS to bypass libogc; the WiFi approach IS to ride the IPC ABI we already proved.** v61 through v66 are not preliminary experiments — they are the production network stack, expressed as four cast-iron addresses (`__ipc_queuerequest=0x8003ae90`, `IOS_Open=0x8003b1f0`, `IOS_Ioctl=0x8003bbc0`, `IOS_Ioctlv=0x8003bf20`) and a sockaddr struct. Phase 2 ships on top of that, not around it.

The Hollywood mailbox is hardware. The IOCTL opcodes are a contract. The endianness is BE-PPC network-order. Everything else is overlay logic — which is exactly what Kamek does best.

## Sources

- <https://deepwiki.com/devkitPro/libogc/7.1-wii-network-stack>
- <https://github.com/devkitPro/libogc>
- <https://wiibrew.org/wiki/Libogc>
- <https://libogc.devkitpro.org/>
- <https://bot.libretro.com/doxygen/a06278_source.html>
- <https://github.com/Retro-Rewind-Team/RR-Launcher/issues/79>
- <https://devkitpro.org/viewforum.php?f=40>
- <https://github.com/mkwcat>
- <https://devkitpro.org/viewtopic.php?f=15&t=9871>
- <https://gbatemp.net/threads/customizemii-complex-forwarder-not-working-even-with-devkipppc-and-libogc.536883/>
- <https://wii.hacks.guide/>
- <https://github.com/devkitPro/libogc/releases>
- <https://wiibrew.org/wiki/Hollywood/Registers>
- <https://github.com/bryankeller/wiiMac/blob/main/src/hollywood.h>
- <https://deepwiki.com/devkitPro/libogc/3.4-ipc-and-ios-services>
- <https://wiibrew.org/wiki/Hardware/IPC>
- <https://gbatemp.net/threads/documentation-of-the-ipc-mechanisms.564796/>
- <https://wiibrew.org/wiki/WiiConnect24>
- <https://github.com/WiiLink24/nwc24>
- <https://pokeacer.xyz/wii/pdf/WiiConnect24_ProgrammingManual.pdf>
- <https://www.gamebrew.org/wiki/Riiconnect24_Patcher_Wii>
- <https://wiilink.ca/>
- <https://github.com/WiiLink24/WSR-Patcher/blob/main/nwc24dl.h>
- <https://wiibrew.org/wiki//shared2/wc24/nwc24msg.cfg>
- <https://www.netflix.com/es-en/login>
- <https://library.nwciowa.edu/>

## Run metadata

- **Prompt:** Research crítico recibido. El enfoque de WiFi era
- **Depth / breadth:** 2 / 3
- **Queries used:** 6 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip, readability, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 656.5 s
- **Errors during run:** 1
- **Started at:** 2026-05-23T22:44:35Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `fetch_page 'https://smashboards.com/threads/modify-a-hacked-wii-to-boot-...': page-fetch: https://smashboards.com/threads/modify-a-hacked-wii-to-boot-straight-to-the-homebrew-channel-goodbye-wiimote.358240/page-2: HTTP Error 403: Forbidden`

</details>
