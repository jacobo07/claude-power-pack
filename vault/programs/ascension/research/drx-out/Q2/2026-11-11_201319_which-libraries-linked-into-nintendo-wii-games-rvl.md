# Byte-matching reconstructions of Wii-era libraries: what the research supports, and what it does not

## 0. Evidence status

**The research ledger does not answer the core question.** None of the nine learnings is an `[OBSERVED]` claim. All are `[DERIVED][LOW]`, and none comes from a repo file, issue, PR, or CodeWarrior manual. The only compiler manual consulted was GCC's, which is not the toolchain in question. The ledger therefore contains no per-library match status, no exact SDK build dates, no license text for any decomp repo, and no confirmed mechanism for identifying a library version inside a DOL.

The report has four parts:
1. what the ledger supports, with tags carried over (§1–2);
2. the explicit gaps (§3);
3. background leads from my own memory, tagged `[HYPOTHESIS][UNSOURCED]` and not to be treated as research findings (§4–5);
4. a verification protocol that turns those leads into falsifiable checks (§6).

## 1. What the ledger supports

### 1.1 Compiler behavior (indirect evidence, GCC manual only)

| ID | Claim | Tag | Relevance to the question |
|---|---|---|---|
| C1 | The optimization level changes which passes run, so the same source yields different instructions at different levels. The level must be pinned before any byte comparison. | [DERIVED][LOW] | A "match" is only meaningful relative to a flag set. An SDK built at a different level looks like a different library version. |
| C2 | Enabled optimizations depend on target and configuration, and the inlining size unit may change between releases. Different compiler builds can therefore emit different bytes for the same source. | [DERIVED][LOW] | The compiler build is part of the fingerprint. The link to library-version identification is my inference, not stated in the source. |
| C3 | Whole-program compilation can inline callers and drop the standalone copy, or merge constants across units. | [DERIVED][LOW] | A function may be absent from the DOL, so "function not found" does not mean "library version differs." |

**Caveat on all three:** the source is the GCC manual, not the Metrowerks (mwcc) manual. The principle, that flags and compiler build change the bytes, is generic and very likely true for mwcc. Any specific mwcc claim is unverified (§5).

### 1.2 Reuse across projects and legal and policy constraints

| ID | Claim | Tag |
|---|---|---|
| C4 | GameCube and Wii games share the Dolphin SDK. Matching it once lets later projects reuse it (cited repos: `doldecomp/dolsdk2001`, `doldecomp/dolsdk2004`; Melee accelerated this way). CodeWarrior cannot be legally distributed, and each project documents its own toolchain setup. The community is also decompiling the compiler (mweppc). | [DERIVED][LOW] |
| C5 | An open-source license can only license rights the contributor holds. "Bring your own disc" does not automatically clear a package of translated game code. AI generation adds no exception. Settlements (re3/reVC, Yuzu) are not rulings. | [DERIVED][LOW] |
| C6 | AI-contribution policy varies by project (N64Recomp prohibits it, RPCS3 permits it with disclosure). The Wii decomp list labels projects human-led versus AI-assisted, and some projects ban AI contributions. Provenance risk is therefore separate from license text. | [DERIVED][LOW] |
| C7 | In the 2021 Take-Two action over re3/ReVC, the project contained no Rockstar assets, yet Take-Two targeted the reconstructed code. A February DMCA takedown escalated to a California suit naming 14 programmers, partly after three filed counter-notifications. | [DERIVED][LOW] |
| C8 | On 17 Aug 2026 Nintendo filed seven DMCA notices on GitHub and removed over 400 repositories, 311 of them in the Suyu fork network (GitHub acts on a whole network past 100 repos). The theory was anti-circumvention, not code copyright. Eden, Citron and Ryujinx escaped by self-hosting. | [DERIVED][LOW] |
| C9 | Nintendo's February 2026 notices gave Switch emulator repos one day to comply, and affected only GitHub copies. A commentary source (TBPN, unverified detail) claims decomp-based mods are removed within hours and that decompilation itself is argued to be fair use. | [DERIVED][LOW] |

**Thinness flags:**
- C7 to C9 are news and commentary. They concern Rockstar and Switch emulators, not Wii SDK decomps.
- No source found any Nintendo action against a GameCube/Wii decomp repo specifically. This is an absence in the research, not evidence that no action exists.
- C4's "legally unresolved toolchain dependency" is my inference, not a stated holding.

## 2. Practical consequences

- **Pin flags and compiler before trusting a match** (from C1–C3). Record `mwcc` version, `-O` level, `-inline` mode, `-sdata/-sdata2` thresholds and `-fp` mode alongside any claimed match. `[DERIVED][LOW]`
- **Treat reuse as two separate layers** (from C4–C6). The matched SDK source is a shared artifact. The compiler and the contributor policies are per-project gates. `[DERIVED][LOW]`
- **Distribution is the exposure point** (from C5, C7–C9). Enforcement targets published artifacts and hosting platforms. Keep a local mirror, and consider self-hosting if you publish. `[DERIVED][LOW]`

## 3. What the research did not establish

| Requested item | Status |
|---|---|
| Per-library match status for OS, GX, VI, PAD, WPAD, KPAD, DVD, NAND, AX, SC | **Not researched.** No repo file, issue or PR was retrieved. |
| NW4R (g3d, lyt, snd, ut, math, ef) and EGG status | **Not researched.** |
| MSL_C, Runtime.PPCEABI.H, MetroTRK, HomeButtonMenu status | **Not researched.** |
| Exact library versions and build dates | **Not researched.** |
| License of each decomp repo | **Not researched.** The only licensing content is the generic analysis in C5. |
| Version identification inside a DOL (strings, signatures, dtk signature files) | **Not researched.** No dtk documentation was retrieved. |
| mwcc-specific falsifiable predictions | **Not researched.** The only manual consulted was GCC's. |

## 4. Unsourced background leads (from model memory, not from research)

All items are `[HYPOTHESIS][UNSOURCED]`. I have not verified them against repos or manuals in this session, so check each one before relying on it.

### 4.1 Where matched SDK code probably lives
- `doldecomp/dolsdk2001` and `doldecomp/dolsdk2004` appear in C4. These are GameCube-era Dolphin SDK reconstructions. They are not RVL SDK.
- RVL SDK code is, as I recall, mostly carried inside individual Wii game decomps rather than in a standalone shared repo. I am not certain which games, and I won't name repos I can't confirm.
- Whether NW4R, EGG and HomeButtonMenu have byte-matching coverage, and at which revisions, is unknown to me with confidence. These libraries were revised across Wii titles, so one title's match should not be assumed to hold for another.

### 4.2 Version identification in a DOL (leads)
1. **SDK banner strings.** Nintendo SDK libraries usually embed strings of the form `<< RVL_SDK - <LIB> release build: <Mon DD YYYY> <HH:MM:SS> (0x<ver>) >>`. The Dolphin-era equivalents embed "Dolphin SDK". Search `.rodata`/`.data` for `RVL_SDK`. If present, the string gives the library and its build date and time.
2. **Per-library granularity.** Each library normally carries its own banner, so OS, GX, PAD and others may be dated differently within one DOL. A game can thus mix SDK builds.
3. **decomp-toolkit (`dtk`).** It splits DOLs using `splits.txt` and `symbols.txt` and has a signature-based function-recognition feature. I believe `dtk` ships built-in signatures for a few common runtime/OS functions, but I am unsure of the exact subcommand names and of the signature file format.
4. **Compiler version.** The `mwcc` version is not reliably recoverable from a stripped DOL. It is typically inferred by trial: build candidate versions until the objects match byte for byte. This is the closest practical equivalent of "reuse only when bytes are identical."

### 4.3 Likely flag conventions (unverified)
- Wii-era SDK and game code is commonly built with `-O4,p` and inlining enabled, with `-sdata`/`-sdata2` thresholds (small-data via r13/r2). Exact per-library flags, and exact compiler build numbers such as the `Wii/1.x` series, are not confirmed.
- Library code built at one level may sit beside game code built at another. The same compiler can therefore produce non-uniform flags within a single DOL.

## 5. Falsifiable predictions (all unverified, and no primary source retrieved)

Each follows your requested form. Each is a hypothesis about `mwcc`, derived from the generic principle in C1–C3. Verify by compiling the same snippet with both settings and diffing the object files.

| # | Prediction | Tag |
|---|---|---|
| P1 | With `-O0`, a trivial leaf function emits a full frame (`stwu r1,-N(r1)`, `mflr`/`mtlr`, `stw`/`lwz` of LR). With `-O4,p`, the same leaf function omits the frame. | [HYPOTHESIS][UNSOURCED] |
| P2 | With `-inline auto`, a small `static` helper is inlined at its call sites. With `-inline off` (or `-inline none`), the call sites emit `bl` and the helper body is retained. | [HYPOTHESIS][UNSOURCED] |
| P3 | With `-sdata 8`, a small global is accessed with `lwz rX, sym@sda21(r13)`. With `-sdata 0`, the same access emits a `lis`/`lwz` pair via `@ha`/`@l`. | [HYPOTHESIS][UNSOURCED] |
| P4 | With compiler build A, a given library source produces object X. With a different build A′, at least one function differs in instruction scheduling, register allocation or inlining. A bytewise diff is therefore a valid test that the compiler build was identified correctly. | [HYPOTHESIS][UNSOURCED] (supported in principle by C2, which is only about GCC) |
| P5 | If a DOL contains `RVL_SDK - GX release build: <date>`, then compiling that library's reconstructed source with the right compiler and flags reproduces the original GX object bytes. With a different banner date (the same source at a different SDK revision), at least one function is expected to differ. | [HYPOTHESIS][UNSOURCED] |

**Falsification criterion:** if P1–P3 fail on the actual toolchain, the flag-fingerprinting method in §6 needs revising. If P5 fails (same banner, same source, bytes differ), the banner is not a sufficient version key.

## 6. Verification protocol (proactive suggestions)

1. **Scan for banners.** Run a strings pass over each target DOL for `RVL_SDK`, `Dolphin SDK`, `NW4R` and `EGG`. Tabulate library, date, and the number inside the parentheses.
2. **Gate reuse on bytes, not labels.** Reuse matched source only if (a) the banner/date agrees and (b) the per-object hash after linking is identical. Banner agreement alone is insufficient, per P5's falsifier.
3. **Pin the toolchain per object.** Record compiler build and flag set in the project config. A flags change must invalidate cached "matched" status.
4. **Use function-level fingerprints as a second key.** Hash relocation-masked instruction sequences. This survives address changes but not inlining differences (C3).
5. **Build the missing table.** For each library in your list, fill in repo, commit, banner date, compiler build, flags, license, and AI-policy status (C6). This table is the real deliverable, and none of its cells are currently verified.
6. **Read the primary sources.** These are the target repos' READMEs and `config`/`splits` files, `dtk` docs, and the Metrowerks CodeWarrior compiler manual for `-O`, `-inline` and `-sdata` semantics.
7. **Contrarian option.** Because compiler builds change bytes (C2), a *failed* match against one SDK revision may be more informative than a success. A systematic mismatch pattern can date a library between two known builds. This is speculative and untested.

## 7. Legal and operational risk (applies to any reuse plan)

- **License limits (C5):** a repo's open-source label does not clear rights the contributor never held. Reconstructed SDK code derives from Nintendo's proprietary code, so a permissive label gives limited assurance. `[DERIVED][LOW]`
- **Counter-notices can escalate (C7)**, per the IGN-reported re3 case. `[DERIVED][LOW]`
- **Network-wide takedowns (C8):** a notice against one fork can reach a whole network of over 100 repos. Cited cases involved anti-circumvention claims against emulators, not decomp repos, so applicability to Wii decomps is unconfirmed. `[DERIVED][LOW]`
- **Policy gates (C6):** check each upstream's AI-contribution rules before merging work between projects. `[DERIVED][LOW]`
- **Self-hosting (C8):** it avoided the platform takedown for the named emulators. Whether it reduces substantive legal risk is untested. `[DERIVED][LOW]`

## 8. Bottom line

- The research establishes only generic principles: compiler flags and builds change bytes (C1–C3), and reuse is bounded by legal and policy gates (C4–C9). All of it is `[DERIVED][LOW]`.
- It does **not** establish which Wii libraries are already matched, at which versions or dates, under which licenses, or how dtk identifies versions. Those cells are empty, not "no."
- §4–5 are leads from memory, flagged `[HYPOTHESIS][UNSOURCED]`. They are cheap to test, and §6 gives the order in which to test them.

If you want, I can start on step 1 of §6 by scanning DOLs you have for SDK banners. I would need those files placed in a fresh, empty directory.

## Contradicciones detectadas

Ninguna. Las fuentes procesadas no se contradicen entre sí en los puntos extraídos. Esto no significa consenso del campo: significa que las fuentes que este run alcanzó coinciden.

## Sources

- <https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html>
- <https://recompsoftware.com/platforms/wii/>
- <https://www.nme.com/news/gaming-news/github-connecting-devs-with-legal-resources-as-nintendo-takes-down-8535-projects-3753299>
- <https://decomp.wiki/platforms/gamecube-wii>
- <https://kingy.ai/blog/ai-video-game-decompilation-legality/>
- <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/>
- <https://www.tbpndigest.com/story/2026-10-06/ai-powered-game-decompilation-is-going-viral-and-heading-straight-into-copyright-litigation>
- <https://gamerant.com/nintendo-switch-emulators-dmca-takedown-notices/>
- <https://heldgames.com/guides/emulation-legal-status-2026>
- <https://www.ign.com/articles/take-two-reverse-engineered-gta-three-vice-city-fan-project-lawsuit>
- <https://shattered.io/claude-game-clone-rule-legit-developers-troubleshooting-false-positives-2026/>

## Run metadata

- **Prompt:** Which libraries linked into Nintendo Wii games (RVL SDK: OS, GX, VI, PAD, WPAD, KPAD, DVD, NAND, AX, SC; NW4R: g3d, lyt, snd, ut, math, ef; EGG; MSL_C; Runtime.PPCEABI.H; MetroTRK; HomeButtonMenu) already have byte-matching clean-room reconstructions in public decompilation projects, at which exact library versions/build dates, under which licenses, and how do projects identify the library version inside a DOL (version strings, signatures, dtk signature files) so that matched sources can be reused only when the bytes are identical? For every claim give the primary source (repo file, issue, PR, compiler manual) and state it as a falsifiable prediction: 'with X, mwcc emits Y; with X', it emits Y''. Mark anything unverified.
- **Depth / breadth:** 2 / 4
- **Queries used:** 8 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 771.9 s
- **Errors during run:** 27
- **Started at:** 2026-11-11T19:13:19Z
- **Module version:** deep_research 0.4.0
- **Quality gates:** 0 query/queries rejected as keyword soup · 0 learning(s) dropped for containing code · 3 dropped as not operator-actionable (relevance: UNRATED)
- **E1 decomposition:** 4/5 axes searched (BOUNDARY, COUNTEREXAMPLE, EVIDENCE, MECHANISM)  — SHORTFALL: only 2 axis/axes covered (BOUNDARY, COUNTEREXAMPLE) — minimum 3; missing: EVIDENCE, MECHANISM, TRANSFERABILITY; only 2 axis/axes covered (BOUNDARY, EVIDENCE) — minimum 3; missing: MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY
- **E2 landscape:** B_ACADEMIC×1, C_PRACTITIONER×1, D_VENDOR×2, UNKNOWN×15 · 0 question(s) refused as vendor-only · 0 learning(s) killed by the coverage gate
- **E3 reality:** DERIVED 9 · 7 label(s) demoted by the evidence gates
- **E4 contradictions:** 0 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `UNCLASSIFIED` / LOW [MECHANISM] — 1 source(s), families UNKNOWN — _Why does the same library source compile to different bytes depending on the compiler buil_
- `THIN` / MEDIUM [BOUNDARY] — 4 source(s), families B_ACADEMIC, UNKNOWN — _At what point does matching library functions by signature or hash stop working when the s_
- `UNCLASSIFIED` / LOW [COUNTEREXAMPLE] — 5 source(s), families D_VENDOR, UNKNOWN — _What do the licensing terms, contributor rules and takedown history of Wii decompilation p_
- `UNCLASSIFIED` / LOW [EVIDENCE] — 5 source(s), families UNKNOWN — _What happened to game decompilation or reverse-engineering projects that received takedown_
- `THIN` / MEDIUM [BOUNDARY] — 4 source(s), families C_PRACTITIONER, D_VENDOR, UNKNOWN — _What happens to a project's own codebase and release history when a matched reconstruction_

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `web_search 'Which Wii-era SDK and middleware librari...': ddg: fetch failed: <urlopen error [WinError 10054] Se ha forzado la interrupción de una conexión existente por el host remoto>; brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`
- `fetch_page 'https://stackoverflow.com/questions/15240427/will-compiling-...': page-fetch: https://stackoverflow.com/questions/15240427/will-compiling-with-the-same-source-compiler-and-library-version-result-in-exac: HTTP Error 403: Forbidden`
- `fetch_page 'https://stackoverflow.com/questions/24151453/how-can-compili...': page-fetch: https://stackoverflow.com/questions/24151453/how-can-compiling-the-same-source-code-generate-different-object-files: HTTP Error 403: Forbidden`
- `fetch_page 'https://blog.sigplan.org/2021/11/11/when-compiler-optimizati...': page-fetch: https://blog.sigplan.org/2021/11/11/when-compiler-optimization-meets-binary-code-difference/: Remote end closed connection without response`
- `fetch_page 'https://www.researchgate.net/publication/356821924_Identifyi...': page-fetch: https://www.researchgate.net/publication/356821924_Identifying_Compiler_and_Optimization_Level_in_Binary_Code_From_Multiple_Architectures/fulltext/61aeff78c11c103836973b98/356821924_Identifying_Compiler_and_Optimization_Level_in_Binary_Code_From_Multiple_Architectures.pdf: HTTP Error 403: Forbidden`
- `source https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html carries instruction-like text ['tool-or-exfil-request']; treated as data`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `relevance filter unavailable: llm-parse: no valid JSON in 1501 chars; head: '{"ratings":[{"index":0,"relevance":"LOW","reason":"Fails Q2 and Q3 (no business/product decision and generic compiler background); only marginally act'; anthropic-sdk: ANTHROPIC_API_KEY not set`
- `decomposition narrow: only 2 axis/axes covered (BOUNDARY, COUNTEREXAMPLE) — minimum 3; missing: EVIDENCE, MECHANISM, TRANSFERABILITY`
- `web_search 'What happens when a decompilation team c...': ddg: 0 hits parsed (possible block or empty SERP); brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`
- `fetch_page 'https://unix.stackexchange.com/questions/765445/making-chang...': page-fetch: https://unix.stackexchange.com/questions/765445/making-changes-to-the-shared-library: HTTP Error 403: Forbidden`
- `source https://binary.ninja/2020/03/11/signature-libraries.html carries instruction-like text ['tool-or-exfil-request']; treated as data`
- `extract_learnings: claude.exe: subprocess failed: Command '['C:\\Users\\User\\.local\\bin\\claude.exe', '--model', 'claude-sonnet-5-5', '-p', '--disable-slash-commands', '--disallowed-tools', '*', '--setting-sources', 'local', '--strict-mcp-config', '--append-system-prompt', "You are an expert researcher. Today is 2026-11-11. Follow these instructions when responding:\n - You may be asked to research subjects that is after your knowledge cutoff, assume the user is right when presented with news.\n - The user is a highly experienced analyst, no need to simplify it, be as detailed as possible and make sure your response is correct.\n - Be highly organized.\n - Suggest solutions that I didn't think about.\n - Be proactive and anticipate my needs.\n - Treat me as an expert in all subject matter.\n - Mistakes erode my trust, so be accurate and thorough.\n - Provide detailed explanations, I'm comfortable with lots of detail.\n - Value good arguments over authorities, the source is irrelevant.\n - Consider new technologies and contrarian ideas, not just the conventional wisdom.\n - You may use high levels of speculation or prediction, just flag it for me."]' timed out after 120 seconds; anthropic-sdk: ANTHROPIC_API_KEY not set`
- `web_search 'What happens when matched library code f...': ddg: 0 hits parsed (possible block or empty SERP); brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`
- `epistemic demoted VERIFIED -> DERIVED: VERIFIED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `epistemic demoted VERIFIED -> DERIVED: VERIFIED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `relevance filter unavailable: llm-parse: no valid JSON in 1474 chars; head: '{"ratings":[{"index":0,"relevance":"LOW","reason":"Fails Q1 and Q2 as it is background on SDK reuse and compiler legal status with no testable mwcc ou'; anthropic-sdk: ANTHROPIC_API_KEY not set`
- `decomposition narrow: only 2 axis/axes covered (BOUNDARY, EVIDENCE) — minimum 3; missing: MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY`
- `source https://shattered.io/claude-game-clone-rule-legit-developers carries instruction-like text ['system-prompt-reference']; treated as data`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`

</details>


## Evidence ledger

- **Claims:** 12 · with a verified quote: 12 (rate 1.0)
- **Quotes:** 24 offered, 0 rejected (not verbatim / unknown source / length)
- **Sources:** 19 snapshots in 19 independent lineage(s); 0 URL(s) were byte-identical copies
- **Labels lowered by the ledger:** 2
- **Sources with instruction-like text (treated as data):** 3

**C1** [DERIVED] The compiler's optimization level changes which transformation passes run, so one source file produces materially different instruction sequences at no optimization, at the first optimization level, and at higher levels. Matching a library inside an executable therefore requires knowing, or searching across, the level it was built with, because a mismatch looks like a different library version.
  - S1 <https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html> chars 1244-1396: "Most optimizations are completely disabled at -O0 or if an -O level is not set on the command line, even if individual optimization flags are specified."
  - S1 <https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html> chars 3344-3398: "-O2 turns on all optimization flags specified by -O1 ."

**C2** [DERIVED] Which optimizations are active at each level depends on the target and how the compiler was configured, and the inlining size limit is measured in an abstract unit whose meaning may change from one release to another. This means that even with identical flags, two compiler releases can inline or lay out code differently, so byte-level differences can separate toolchain generations and thereby narrow down the library revision.
  - S1 <https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html> chars 1450-1599: "Depending on the target and how GCC was configured, a slightly different set of optimizations may be enabled at each -O level than those listed here."

**C3** [DERIVED] When several files are compiled together, the compiler uses information from all of them, and it can inline functions into their callers and then omit the standalone copy entirely, or merge identical constants across compilation units. A library function may thus be absent as a distinct unit in the final executable, so a version check that relies on finding each function intact can miss or misread it.
  - S1 <https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html> chars 13751-13914: "If all calls to a given function are integrated, and the function is declared static , then the function is normally not output as assembler code in its own right."
  - S1 <https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html> chars 16594-16704: "Attempt to merge identical constants (string constants and floating-point constants) across compilation units."

**C4** [DERIVED] Wii and GameCube games share the Dolphin SDK, and matching it once lets every later game reuse those functions, so only game-specific code remains; the Melee project accelerated this way. But CodeWarrior cannot be legally distributed, so projects each document their own toolchain setup and the community is decompiling the compiler itself (mweppc) to escape the dependency. Sharing reconstructed SDK source across projects is technically encouraged, while the build toolchain stays a per-project legal gray zone.
  - S10 <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/> chars 4055-4107: "The community cannot distribute CodeWarrior legally."
  - S10 <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/> chars 17061-17198: "The Dolphin SDK is shared across games. Once you match the SDK library for one game, you can reuse the matched functions for other games."

**C5** [DERIVED] Legal analysis in the contents says an open-source label can only license rights the contributor holds, requiring users to supply their own disc does not automatically clear a package that distributes translated game code, and AI generation adds no exception. Projects nonetheless rely on exactly these defenses, publishing code only and asking users to supply game data. Settlements such as re3/reVC and Yuzu are not rulings, so no court has settled whether reconstructed source is shareable.
  - S9 <https://kingy.ai/blog/ai-video-game-decompilation-legality/> chars 16517-16613: "An open-source label can license contributors’ rights; it cannot supply rights they do not hold."
  - S6 <https://recompsoftware.com/platforms/wii/> chars 6306-6404: "They publish code only, and the ones that need game data ask you to supply it from a copy you own."

**C6** [DERIVED] Projects disagree sharply on AI contributions: N64Recomp prohibits them, RPCS3 permits them with disclosure, and the Wii decomp list shows many projects labeled AI-assisted or AI-generated alongside human-led ones. The GameCube/Wii wiki warns that some projects ban AI contributions, and permitted downstream reuse does not guarantee upstream acceptance. Moving reconstructed code between Wii projects therefore carries a provenance risk that licenses alone do not resolve.
  - S9 <https://kingy.ai/blog/ai-video-game-decompilation-legality/> chars 17994-18125: "Contribution policies and licence permissions are also separate: permitted downstream reuse does not guarantee acceptance upstream."
  - S10 <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/> chars 21406-21466: "Some projects ban AI contributions. Check before submitting."

**C7** [DERIVED] In the 2021 Take-Two case over the GTA 3 and Vice City reverse-engineering project (re3/ReVC), the project contained no Rockstar assets and users needed their own game copy, yet Take-Two went after the reconstructed code as 'derivative GTA source code'. It escalated from a GitHub takedown to a California lawsuit naming 14 programmers, partly after three of them filed counter-notifications. Filing a counter-notice can therefore turn a takedown into litigation.
  - S14 <https://www.ign.com/articles/take-two-reverse-engineered-gta-three-vice-city-fan-project-lawsuit> chars 1164-1396: "This project doesn't contain any Rockstar assets, either, so players that wish to use this reverse-engineered source code will actually need to have their own copy of GTA 3 or Vice City to create a port of the games using this code."
  - S14 <https://www.ign.com/articles/take-two-reverse-engineered-gta-three-vice-city-fan-project-lawsuit> chars 322-450: "Take-Two Interactive is suing the creators of reverse-engineered Grand Theft Auto 3 and Grand Theft Auto Vice City fan projects."

**C8** [DERIVED] On 17 August 2026 Nintendo filed seven DMCA notices at GitHub in one day and removed over 400 repositories. The largest notice covered 311 repositories in the Suyu fork network, because GitHub processes a notice against an entire network once it passes 100 repositories. The theory was anti-circumvention (the emulators cannot work without defeating Nintendo's encryption), not copyright infringement by the code itself. Eden, Citron and Ryujinx escaped because they had moved to self-hosted repositories after February.
  - S13 <https://heldgames.com/guides/emulation-legal-status-2026> chars 2219-2337: "On 17 August 2026, Nintendo filed seven DMCA notices at GitHub in a single day and removed more than 400 repositories."
  - S13 <https://heldgames.com/guides/emulation-legal-status-2026> chars 2646-2831: "Nintendo is not arguing that emulators infringe copyright. It is making a DMCA anti circumvention argument, claiming these emulators cannot work without defeating Nintendo's encryption."
  - S13 <https://heldgames.com/guides/emulation-legal-status-2026> chars 2991-3131: "Eden, Citron and the Ryujinx line do not appear anywhere in the August sweep, because they moved to self hosted repositories after February."

**C9** [DERIVED] Nintendo's February 2026 notices gave Switch emulator repositories on GitHub (Citron, Eden, Kenji-X) one day to comply or be disabled, and affected only GitHub-hosted copies. A commentary source says viral decompilation-based mods of games such as GTA 5 are removed within hours, while the decompilation act itself is argued to be protected as fair use. The legal exposure sits in shipping a derivative product, not in the analysis.
  - S12 <https://gamerant.com/nintendo-switch-emulators-dmca-takedown-notices/> chars 2235-2335: "The emulators that were served a takedown notice had only one day to comply with Nintendo's request."
  - S11 <https://www.tbpndigest.com/story/2026-10-06/ai-powered-game-decompilation-is-going-viral-and-heading-straight-into-copyright-litigation> chars 1936-2023: "That protection evaporates the moment the decompiled code becomes a derivative product."

**C10** [DERIVED] Relicensing is a negotiated, slow process, and projects treat near-complete contributor consent as sufficient rather than unanimous. Mozilla reportedly relied on about 95% author coverage, mpv started with 95%+ consent in 2015, reached roughly 90% of authors by August 2016 and only finalized in October 2017, and PoDoFo's April 2026 change took a multi-year effort. So a license change on something you imported is a multi-year, foreseeable event, not a sudden one, and you can watch it coming.
  - S18 <https://en.wikipedia.org/wiki/Software_relicensing> chars 947-1142: "While in the free and open-source domain achieving 100% coverage of all authors is often impossible due to the many contributors involved, often it is assumed that a great majority is sufficient."
  - S18 <https://en.wikipedia.org/wiki/Software_relicensing> chars 5667-5782: "In August 2016 approx. 90% of the authors could be reached and consented. In October 2017 the switch was finalized."
  - _ledger: OBSERVED number(s) absent from verified spans: 2015, 2026, 95%_

**C11** [DERIVED] License incompatibility has blocked real product distribution: VLC was pulled from the Apple App Store in early 2011 and only returned in July 2013, about 30 months later, after relicensing its library and application. Projects that want to stay shippable relicense proactively, so a release channel can be lost for years while a license fix is negotiated.
  - S18 <https://en.wikipedia.org/wiki/Software_relicensing> chars 2517-2712: "After VLC was removed from Apple App Store at the beginning of 2011, in October 2011 the VLC project re-licensed the VLC library part from the GPLv2 to the LGPLv2 to achieve better compatibility."
  - S18 <https://en.wikipedia.org/wiki/Software_relicensing> chars 11588-11620: "Johnston, Casey (July 18, 2013)."
  - _ledger: OBSERVED number(s) absent from verified spans: 30_

**C12** [DERIVED] The practical guard against losing the ability to see or reproduce old code is a permanent snapshot marker plus a separate untouched archive copy created before deletions, with a written rollback plan. This keeps troubleshooting, audits and rollback possible even after the live code has moved on, which matters when a dependency's source or license later changes underneath you.
  - S19 <https://medium.com/@rahulonrails/how-to-safely-clean-up-a-legacy-github-repository-without-losing-historical-code-b14ab3e1e1e2> chars 913-1021: "Removing code without a proper baseline can make troubleshooting, audits, and rollback activities difficult."
  - S19 <https://medium.com/@rahulonrails/how-to-safely-clean-up-a-legacy-github-repository-without-losing-historical-code-b14ab3e1e1e2> chars 6217-6361: "By establishing these safeguards before refactoring, teams can modernize large repositories without losing access to historical implementations."
