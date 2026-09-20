---
name: mobile-game-wii-port
description: Reverse engineer a commercial mobile game (APK/XAPK/IPA asset corpus) down to a verified, portable content model, then reimplement it as a native Nintendo Wii game and ship it as boot.dol or a disc image. Covers engine fingerprinting from stripped native binaries, structural cipher characterisation without a key, container and payload decoding, data-versus-behaviour measurement, the port-versus-extract decision, and Wii packaging. Use when the user wants to port a mobile game to the Wii, decrypt or read a game's packed asset corpus, identify which engine a game binary runs, or decide whether to port a scripting runtime or extract its data.
trigger: port to wii|apk to wii|apk to wbfs|wbfs|mobile game port|port a game|native wii port|decrypt game assets|game asset corpus|which engine does this game use|lua bytecode|extract game data|absw2|angry birds star wars|rovio fusion|homebrew channel|boot.dol|devkitPPC port
---

# Mobile Game -> Native Wii Port

## What this is, stated exactly

**There is no APK-to-WBFS conversion, and nothing here pretends otherwise.** A
Wii cannot run an Android game, and no tool turns one into the other. The
programme is:

    APK corpus  ->  verified portable content model  ->  NEW native runtime  ->  Wii artifact

The first arrow is archaeology, the second is writing a game, the third is
packaging. Reading it as a conversion is the same error as the source
programme's R-01 ("the scripts are JavaScript", inferred from a folder name) and
it costs the same way: it makes the real work invisible until it is hit.

Phases 0-4 are target-agnostic — they would serve a port to any console. Phases
5-7 are Wii-specific.

## Phases

| # | Phase | Run | Answers |
|---|---|---|---|
| 0 | Fingerprint | `core/fingerprint_game.py <file-or-dir>` | Which engine, and is Java decompilation worth anything? |
| 1 | Reproducible inventory | project-local | What is in the corpus, hashed, twice, byte-identical? |
| 2 | Access | `core/cipher_probe.py <dir>` | Encrypted? What holds without the key? |
| 3 | Envelope + payload | `core/envelope_probe.py <file>` | What container, what payload, valid to the last byte? |
| 4 | Content model | project-local | How much is data, how much is behaviour? |
| 5 | Port decision | `references/port-decision.md` | Extract-and-drive, or port the runtime? |
| 6 | Native runtime | `references/` + `wii-dev-best-practices` | Does it build and run? |
| 7 | Shipping | `references/wii-shipping.md` | boot.dol, or disc image? |

Phases 1 and 4 have no executable here on purpose: an inventory walks one
Owner's corpus and a content model is one game's schema. What generalises is the
rule each must satisfy, stated below.

---

## Phase 0 — Fingerprint. Run this first, always.

```
python core/fingerprint_game.py <apk|zip|directory>
```

It reads **runtime literals out of native binaries**, never symbol names, and
reports an engine with the evidence that produced it.

**Why literals and never symbols.** Symbol names do not survive stripping, so a
symbol scan returning nothing cannot distinguish *absent* from *invisible* — it
carries no information. Runtime literals are compiled into C source and do
survive. This is the source programme's R-03, and it cost a retracted claim
about both Lua and Box2D.

**Why this phase gates everything.** For a native-engine game, Java
decompilation yields a launcher activity and nothing else: the game is in the
`.so` and its script corpus. Phase 0 says so in seconds rather than after an
afternoon in a decompiler. It is the same divert
`android-reverse-engineering` applies to Flutter, for the same reason — and when
Phase 0 reports a Java/Kotlin game, **that skill owns the work, not this one.**

Outcomes are `CONFIRMED`, `ABSENT`, `INCONCLUSIVE` and `UNKNOWN`. An engine is
never promoted for tidiness, and `INCONCLUSIVE` is what a build compiled with
assertions disabled earns — its absence of assert strings is invisibility, not
absence.

## Phase 1 — Reproducible inventory

Walk every entry, record path, size and hash, and **run it twice**. Two runs
byte-identical is the gate; anything else means the walk has an ordering or a
timestamp in it and no later measurement built on it is reproducible.

Raise the corpus-completeness question here and leave it `UNKNOWN` until it can
be answered against the game's own manifest. A store download frequently omits
hot-update content, and a corpus that is 90% present looks exactly like one that
is complete until something references what is missing.

## Phase 2 — Access, before any key hunting

```
python core/cipher_probe.py <directory-of-encrypted-assets>
```

**Establish structure before you hunt a key.** These hold with no key at all,
and they survive being wrong about the algorithm:

| Property | Instrument | What separates it from the alternative |
|---|---|---|
| block vs stream | every file size a multiple of 8 or 16 | a stream cipher needs no padding, so its output length equals its plaintext length |
| not ECB | no repeated block within a file | ECB maps a repeated plaintext block to the same ciphertext block anywhere |
| fixed key + fixed IV | identical leading ciphertext blocks across files | a per-file IV, nonce or salt decorrelates the heads |
| ciphertext at all | entropy near 8 bits/byte, no signature prefix | compressed data scores the same, so this is corroboration and never a verdict |

**Two traps this phase exists to avoid**, both paid for in the source programme:

- **A primitive in the process does not identify the component that uses it.** A
  Rijndael S-box proves AES exists somewhere in the address space. If a TLS
  stack is linked in, that alone accounts for it and says nothing about the
  scripts. Check for `/crypto/`, `X509`, `libcurl`, `ssl/s3_` before reading a
  crypto table as a finding. (R-04)
- **A shared ciphertext prefix does not prove CBC.** A reused stream keystream
  produces the identical observation. What discriminates is padding: block
  ciphers pad, stream ciphers do not. (R-05)

When a key sweep is written, its **positive control must be drawn from the space
of plausible plaintexts, not the one in mind**. The source programme swept
22,892,378 candidates with an oracle that accepted only printable source or
deflate, against a corpus whose real plaintext was an LZMA stream carrying
compiled bytecode. The oracle could not have accepted the correct key. Its
controls were green throughout and proved only that it rejects random keys.
(R-06)

## Phase 3 — Envelope and payload

```
python core/envelope_probe.py <plaintext-file>
```

Plaintext is rarely the thing you want. Expect layers: a magic, a compression
envelope, then a payload that is itself a compiled format.

Validate the payload **structurally to the last byte** — a full walk that
consumes every byte and ends exactly where the declared length says. A parser
that stops early and reports success has measured the prefix it understood.

**Header fields are a build choice.** The source corpus is Lua 5.1 bytecode
compiled with `lua_Number` as float32 rather than the stock double, and with all
debug information stripped. Every stock-header tool rejects it, and a decompiler
that relies on local names emits generated `L0_1`-style names throughout. Read
the header before choosing a downstream tool; the probe reports these fields for
exactly that reason.

## Phase 4 — Content model, and the measurement that decides Phase 5

Extract the data with an interpreter that models only what it can establish and
marks everything else `UNKNOWN` **with a count**. A partial recovery that cannot
report its own gaps reads as a complete one.

Then measure the split that decides the port: **what fraction of the corpus is
data construction, and what fraction is behaviour?** Count by instruction, not
by file, and interpret nested function bodies separately from top-level
constructors — that is where behaviour lives, and a file-level sweep attributes
it to data.

In the source corpus the answer was **91.6% data / 8.4% behaviour** across
2,371,105 instructions. That number is what converted a preference into an
evidenced decision.

## Phase 5 — The port decision

`references/port-decision.md`. Extract-and-drive versus port-the-runtime,
decided on the Phase 4 measurement, with the conditions under which each answer
is right and what each costs.

## Phase 6 — Native runtime

`wii-dev-best-practices` owns the Wii toolchain, GX pipeline, libogc and memory
model. This skill adds only what the port-from-a-mobile-original context needs:

- **Reproduce the original's numeric semantics.** If the original computed in
  single precision, matching it is a fidelity requirement, not a detail.
- **Reproduce the original's physics vocabulary.** If the content is authored in
  a known physics library's terms — fixture density/friction/restitution, joint
  motor and limit fields, a pixels-per-metre ratio — the port must reproduce
  those semantics or the levels do not play the same. This is a requirement
  whether or not the original binary links that library, and it is established
  from the content, not from the binary.
- **Bake a build identity into the artifact and show it on screen.** A
  screenshot proves something ran, not which build ran, and every fidelity gate
  is a comparison against one specific artifact. A dirty-tree suffix means the
  evidence is unreproducible.

## Phase 7 — Shipping

`references/wii-shipping.md`. Two models, one proven and one not:

- **`boot.dol` + `meta.xml` + `icon.png` in `apps/<name>/`** — Homebrew Channel
  and USB Loader. This is what the source programme ships and it is proven in
  Dolphin.
- **Disc image (ISO, then WBFS via `wit`)** — real, optional, and **UNPROVEN**
  by this programme. No ISO or WBFS has been produced and none has run on
  hardware.

Donor-disc injection — replacing content inside a retail game — is a different
model entirely and belongs to `wii-dev-best-practices`.

---

## Standing constraints

**Asset firewall.** Facts about the Owner's corpus may be committed: hashes,
sizes, counts, offsets, and names shared across three or more files. A name used
in a single file is that file's own content, not shared vocabulary. Bytes
derived from the corpus may not be committed, decrypted or converted, regardless
of the repository being private. Derived payloads go to a gitignored build tree.

**Controls before conclusions.** Every sweep and detector ships a positive
control proving it can find a known answer, and a negative control sized to the
search: a false-positive rate must sit below 1/N. A detector tight at one scale
is routinely useless at the next.

**`UNKNOWN`, `INCONCLUSIVE` and `BLOCKED` are results.** They are never promoted
to `PASS` for tidiness. A clean miss with green controls is worth committing.

**A verdict that contradicts the evidence beside it indicts the parser, not the
world.** Print what a check matched against, so its own bugs are visible.

**Measure host memory before launching anything heavy.** A disassembler JVM
wants 2-4 GB. A load generator is part of the system under test, and this host
has reaped a background task for memory pressure.

**Dolphin is the development loop, not hardware truth.** Never claim a hardware
gate that has not run on a real Wii.

## Traps, with the root cause of each

`references/retractions.md` — six retracted claims from the source programme,
generalised into detection rules. Read it before asserting an absence, before
reading a crypto table as a finding, and before trusting any third-party
analysis report.

## Done-gate

```
python tools/test_mobile_game_wii_port.py
```

from the Power Pack repository root. Exit 0. Every executable is driven from
both poles on real byte shapes; `UNKNOWN` is asserted as reachable rather than
only as a default.
