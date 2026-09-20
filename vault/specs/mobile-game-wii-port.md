---
covers: [mobile-game-wii-port, apk-to-wii, game-port-archaeology, wbfs, absw2]
tier: 2
sealed: 2026-09-20
---

# Spec — `mobile-game-wii-port` skill

## Why this exists

The ABSW2-Wii programme (Angry Birds Star Wars II 1.9.25 -> native Wii) has
produced a method that works and a body of negative knowledge that was expensive:
six retractions, each with a named root cause, in
`docs/ARCHITECTURE_TRUTH.md` §3. None of it is reusable today — it lives in one
private repository and reaches a new session only through `/absw2-continue`,
which is bound to that one programme.

This skill generalises the method and carries the negative knowledge with it.

## The premise correction this spec exists to pin

There is no APK-to-WBFS conversion, and the skill must never imply one. The
pipeline is:

    APK corpus  ->  verified portable content model  ->  NEW native runtime  ->  Wii artifact

Framing it as a conversion is the same class of error as R-01 ("the scripts are
JavaScript", inferred from a directory listing). It is recorded here so the
framing cannot drift back.

Second correction, measured 2026-09-20: **ABSW2 ships `apps/absw2/boot.dol` for
the Homebrew Channel and USB Loader, not a WBFS.** WBFS is a disc-image
container for retail discs and donor-disc mods. Wrapping a homebrew DOL into a
disc image is a real optional step; nothing in ABSW2 has run it, so the skill
carries it with an explicit unproven status.

## Ownership — what this skill must NOT duplicate

| Owner | Owns | Boundary |
|---|---|---|
| `android-reverse-engineering` | APK/XAPK entry, Java/Kotlin decompilation, R8 name recovery, HTTP endpoint extraction | Hands off the moment Phase 0 says the game is native-engine. Its Phase 0 already diverts Flutter for the same reason. |
| `wii-dev-best-practices` | GX pipeline, libogc, memory/build, donor-disc injection (Kamek/BRRES), `wit`, Dolphin loop | Owns everything downstream of a built DOL. This skill references it and restates none of it. |
| `/absw2-continue` | Continuation of that one programme from its durable state | Stays project-bound. This skill is the method; the command is the instance. |
| `claude-power-pack` | Gates, done-gates, Reality Contract, evidence doctrine | Supplies the gate convention (`V-*`), not the domain. |

The uncovered middle, and the reason this skill is admitted: **asset-corpus
archaeology** — establishing access to a packed/encrypted content corpus,
validating the payload structurally, extracting a data model, and deciding
port-vs-extract on a measurement rather than a preference.

## Phases

Phases 0-4 are target-agnostic (they would serve a port to any console).
Phases 5-7 are Wii-specific.

| # | Phase | Executable | Question it answers |
|---|---|---|---|
| 0 | Fingerprint | `core/fingerprint_game.py` | Which engine runs this, and is Java decompilation worth anything? |
| 1 | Reproducible inventory | (project-local) | What is in the corpus, hashed, twice, byte-identical? |
| 2 | Access | `core/cipher_probe.py` | Are the assets encrypted, and what can be established without the key? |
| 3 | Envelope + payload | `core/envelope_probe.py` | What container, what payload format, valid to the last byte? |
| 4 | Content model | (project-local) | How much of the corpus is data and how much is behaviour? |
| 5 | Port decision | reference | Extract-and-drive, or port the runtime? |
| 6 | Native runtime | reference + `wii-dev-best-practices` | Does it build and run? |
| 7 | Shipping | reference | boot.dol, or disc image? |

Phases 1 and 4 stay project-local by decision: an inventory is a walk over one
Owner's corpus and a content model is that game's schema. What generalises is
the *rule* each must satisfy, which the skill states and the gate cannot check.

## Acceptance

`python tools/test_mobile_game_wii_port.py` exits 0.

- Every executable is driven from BOTH poles on real byte shapes: a real LZMA
  stream from the standard library, a real Lua 5.1 header in both the stock
  double and the float32 build, ZIP corpora carrying real engine literals.
- Every detector ships a negative control sized to its search, per the
  programme's standing constraint that a false-positive rate sit below 1/N.
- `UNKNOWN` is asserted as a reachable outcome, not only as a default.
- A mutation drill removes each load-bearing clause and requires a named gate
  to go red, with restores verified by SHA-256.

## Asset firewall (inherited, non-negotiable)

Facts about a corpus may be committed: hashes, sizes, counts, offsets, names
shared across three or more files. Bytes derived from it may not, decrypted or
converted, regardless of repository visibility. The skill's tools emit facts;
payload bytes go only to a gitignored build tree. No test fixture in this
repository is drawn from a real corpus.
