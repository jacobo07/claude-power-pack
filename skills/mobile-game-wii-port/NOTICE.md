# NOTICE — `mobile-game-wii-port`

## Provenance

This skill is **not** an absorption of a third-party project. It is distilled
from the Owner's own **ABSW2-Wii** programme — a native Wii reimplementation of
Angry Birds Star Wars II 1.9.25 — at
`C:\Users\User\Desktop\Cursor Projects\Wii Projects\ABSW2-Wii`
(private remote `github.com/jacobo07/ABSW2-Wii`).

Read as of **2026-09-20**, at the state sealed by waves W0-W4, W3b-1 and W3b-2:

- `.planning/STATE.md` — waves closed, facts the next wave must not re-derive
- `docs/ARCHITECTURE_TRUTH.md` — findings A-01..A-11, retractions R-01..R-06,
  §7 script decryption, §8 instruction decode, §9 data extraction
- `docs/BUILDING.md` — devkitPPC environment and the `subst` requirement

No source file was copied. What travels is the **method** and the **negative
knowledge**: which instruments returned no information and why.

## What is carried, and what it is worth

| Carried | From | Why it generalises |
|---|---|---|
| Engine identification from runtime literals, never from symbol names | R-03 | Symbol names do not survive stripping, so that scan cannot distinguish absence from invisibility. True of any stripped native binary. |
| A primitive present in the process does not identify the component that uses it | R-04 | A linked TLS stack supplies AES for its own reasons. True wherever a third-party library shares a primitive. |
| Structural cipher characterisation before key hunting | §5, A-08a/b | Block size, ECB, fixed-IV are all establishable with no key at all, and they survive being wrong about the algorithm. |
| A positive control must be drawn from the space of plausible plaintexts | R-06 | An oracle built for the expected format certified a sweep blind to the format that existed. 22.9M candidates, zero information. |
| An observation consistent with two mechanisms attributes to neither | R-05 | A shared ciphertext prefix is produced by CBC with a fixed IV *and* by a reused stream keystream. |
| Payload header fields are a build choice, not a constant | §7 | `lua_Number = float32` makes every stock-header tool reject the corpus. |
| Data-vs-behaviour split decides port-vs-extract | §9 | 91.6% / 8.4% by instruction count is what turned a preference into an evidenced decision. |
| A verdict that contradicts the evidence printed beside it indicts the parser | §9 | The first physics check reported `NONE` next to a listing containing the vocabulary it was looking for. |

## Adjacent owners

- `android-reverse-engineering` — owns APK entry and Java/Kotlin work. This
  skill takes over when Phase 0 reports a native-engine game.
- `wii-dev-best-practices` — owns the Wii toolchain, GX, donor-disc injection
  and `wit`. This skill references it and restates none of it.
- `/absw2-continue` — the project-bound continuation of the source programme.

## Asset firewall

Facts about an Owner's corpus may be committed: hashes, sizes, counts, offsets,
and names shared across three or more files. Bytes derived from it may not be
committed, whether decrypted or converted, regardless of repository visibility.

**No fixture in this skill or its gate is drawn from a real corpus.** Every
test input is synthesised in-process from the byte shapes the parsers consume —
real LZMA streams from the standard library, real Lua 5.1 headers assembled
field by field, ZIP containers built at test time. Nothing copyrighted is
vendored, and the gate runs on a machine that has never seen the game.

## Status of the shipping leg

ABSW2 ships `apps/absw2/boot.dol` and that path is proven in Dolphin
(`evidence/W4_boot_dolphin.png`). The DOL-to-disc-image path is documented in
`references/wii-shipping.md` and is marked **UNPROVEN**: no ISO or WBFS has been
produced by this programme, and no artifact of either kind has run on real
hardware. Dolphin is the development loop, not hardware truth.
