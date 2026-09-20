# Phase 7 — shipping a native Wii port

`wii-dev-best-practices` owns the Wii toolchain, GX pipeline, libogc, memory
model and donor-disc injection. This file covers only the packaging question a
from-scratch port faces, and it marks what has and has not been proven.

## The two models, and which one you are in

**Homebrew application — `boot.dol`.** A from-scratch port built with devkitPPC
produces a DOL. It ships as:

    apps/<name>/boot.dol
    apps/<name>/meta.xml
    apps/<name>/icon.png

on an SD card or USB device, launched from the Homebrew Channel or from a USB
loader's homebrew list. **This is the proven path.**

**Donor-disc injection.** Replacing content inside a retail game, which then
ships as a modified disc image. This is a different discipline — Kamek, BRRES,
`wszst`, disc IDs — and it belongs to `wii-dev-best-practices`. A from-scratch
port is not in this model.

**Disc image for a homebrew title.** Wrapping a homebrew DOL into an ISO, then
converting to WBFS with `wit`, so the port appears as a disc entry rather than a
homebrew entry. Real, optional, cosmetic in effect. **UNPROVEN here** — see
below.

## Status of the WBFS path

**Nothing in the source programme has produced an ISO or a WBFS.** The claim
"ships for Wii USB Loader" in that repository refers to the `boot.dol` layout
above, and the only verified artifact is `boot.dol` booting in Dolphin.

Treat the disc-image path as a documented option, not a capability, until:

1. `wit` is confirmed present and runs;
2. an ISO is produced from the DOL and its structure verified;
3. the WBFS converts and *boots* — in Dolphin first, then on hardware.

Each of those is a separate gate. None has run. Reporting the path as working
because the commands are written down is the exact failure
`documented-capability-must-be-executable` describes.

`wii-dev-best-practices` records `wit` at `C:/Users/User/tools/wit/wit.exe` on
this host, and its error database carries a real disc-ID incident: a WBFS built
with the wrong disc ID loaded but silently failed to load a module. Verify the
tool exists before planning around it.

## The build traps that cost real time

**devkitPPC cannot build from a path containing spaces.** The failure does not
mention spaces — it reports a missing target that is the first half of your path.

**A directory junction does not fix it.** Windows resolves the junction when it
sets a process's working directory, so `make` still receives the real spaced
path. What works is a `subst` virtual drive, which is not a reparse point:

```powershell
subst W: "C:\path with spaces\YourProject"
# build from W:\ , then release it
subst W: /D
```

**`make` is not where you would look for it.** On a devkitPro install it lives
in msys2, not in `devkitPro\tools\bin`, and `DEVKITPRO` / `DEVKITPPC` may not be
set by the installer at all.

**Pin the output name in the Makefile.** The devkitPPC template derives it from
the directory name. Under `subst` that becomes the drive letter, and both the
Homebrew Channel and USB loaders want `boot.dol` specifically.

## Build identity, and why it is a shipping concern

Bake `git describe --always --dirty --abbrev=8` into the binary and print it on
screen.

A screenshot of a Wii showing your title proves *something* ran. It does not
prove *which build* ran, and every fidelity gate is a comparison against one
specific artifact. A dirty-tree suffix means the tree had uncommitted changes:
treat that evidence as unreproducible rather than as a result.

## Dolphin is not hardware

Dolphin is the development loop. It is the right place to iterate and the wrong
place to claim a hardware gate.

When capturing evidence from it, capture late rather than at the first frame — a
program that draws one frame and hangs is indistinguishable from one that works,
if you only look at frame one. The source programme's boot evidence was captured
at frame 960, about sixteen seconds in, which is what makes it evidence of a
program that keeps running.

Record what the capture actually establishes: resolution, free MEM1 and MEM2,
controller connected, pointer resolved. Those are facts. "It boots" is a summary
of them and should not travel without them.
