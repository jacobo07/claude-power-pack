# Function identification by content in GameCube/Wii DOL/REL binaries: report

## 0. Read this first: coverage

**The research behind this report did not answer your question.** None of the learnings supplied covers:

- dtk signatures
- Ghidra BSim or Function ID
- IDA FLIRT or Lumina
- Dolphin `.map`/`.dsy` files
- relocation-aware hashing
- mwcc output
- repo URLs or licences

They cover the *limits* of matching, signatures and name transfer, mostly from non-GameCube sources.

As a result:

- Section 2 carries every learning with its original tag.
- Section 3 is a list of unverified pointers from my own memory, not from research. These are **not** tagged as findings.
- Per-tool relocation masking, false-match reporting, licences by file, and the "with X, mwcc emits Y; with X', Y'" predictions are **not delivered**. I won't invent primary sources for them.

Section 4 gives a verification plan that produces those predictions.

## 1. Tag legend

| Tag | Meaning |
|---|---|
| `[DERIVED]` | Inferred from sources, not stated by them |
| `[LOW]` / `[MEDIUM]` | Source quality, as supplied |
| `[UNVERIFIED-MEMORY]` | My recollection, no research behind it. Check before use |

No `[OBSERVED]` learnings were supplied. Everything below the research line is inference.

## 2. Findings from research

### 2.1 What a match proves, and what it doesn't

| # | Claim | Tags | Basis (source ledger) |
|---|---|---|---|
| C4 | A matching decompilation proves only that one compiler turns the C into the original bytes. It does not prove the C means the same thing under another compiler or ABI. In the V-Rally port, byte-matched functions misbehaved on another target: cars started backwards, textures loaded at 0×0 pixels, and sign errors turned 255 into -1. Super Mario 64 has similar cases kept under `AVOID_UB`. Any imported name or semantics should be treated as unverified until run under a different build. | [DERIVED][LOW] | S6 lists about ten V-Rally bugs, each in functions that matched with KMC GCC 2.7.2. |
| C5 | Cheap behavioral checks catch what a match hides: a second modern compiler, a port build, or comparing memory against the running original. SM64 runs a host-GCC syntax check next to the IDO build. Match percentage is not a correctness measure. | [DERIVED][LOW] | S6: every bug came from building a port. S4: decomp.me scores single functions and never sees other bytes. |
| C6 | No supplied source quantifies how often names imported by matching across games are wrong. The nearest evidence is anecdotal bug lists plus the Decomperson figure of 300 perfect decompilations from 35,000 submissions. That measures human matching success, not name accuracy. **Evidence is thin here: any error rate you plan around is an assumption.** | [DERIVED][LOW] | S4, S6, S7, S8, S9 contain no figure on incorrect imported names. |

### 2.2 Byte-exact verification at the object level

| # | Claim | Tags | Basis |
|---|---|---|---|
| C16 | mwcc-rs defines parity as emitting the same relocatable object as the real Metrowerks compiler, byte for byte. An exact `.text` section alone is useful evidence but not parity. It also keys on section order, symbol order, alignment, and relocations such as `R_PPC_EMB_SDA21`. Comparing at the object stage, before addresses are assigned, avoids layout-dependent changes made at link time. | [DERIVED][MEDIUM] | S18 states the goal and lists relocation types and section details, with 4,523 commits behind it. |

This is the only supplied item touching GameCube-era compiler output (mwcc, SDA21 relocations). It is also the only [MEDIUM] item.

### 2.3 Why a signature may not hit, even when the library is present

**SDK and library versioning**

- **C19.** [DERIVED][LOW] Library behavior can differ by the SDK version the caller was built against. One program can mix modules and static libraries built against different SDK versions. A name or version match therefore does not guarantee the same body, and it raises the risk of a confident but wrong identification. Basis: S23, applied to signatures by inference.
- **C20.** [DERIVED][LOW] Shared libraries keep several versioned implementations of one function. S24's example is `memcpy@GLIBC_2.2.5` alongside `memcpy@@GLIBC_2.14`. A database holding only the newest variant will miss or mislabel older builds. This is a glibc example. The signature-database consequence is inferred.

**Inlining**

- **C21.** [DERIVED][LOW] If every call is inlined and the address is never taken, no standalone copy is emitted, so a signature of the standalone function has nothing to match. "Not found" can mean the code is dissolved into callers, not that the library is absent. Basis: GCC documentation and Wikipedia's inline-function article.
- **C22.** [DERIVED][LOW] Each inlined copy is optimized in its caller's context. Constant propagation, dead-code elimination and branch folding mean copies need not look alike. Ten call sites give ten different copies. A signature may match some, none, or fire inconsistently. Basis: S25, which does not discuss signatures. The signature consequence is inferred.
- **C23.** [DERIVED][LOW] Inlining is mostly an optimizing-build behavior. GCC inlines nothing without optimization unless forced. Debug-style builds keep standalone functions that signatures can find. Compilers also differ in what they can inline. Judge any "library present/absent" result by build settings. Basis: S27, the GCC manual and Wikipedia.

*Caveat on C19–C23:* the sources are GCC, glibc and general inlining material, not mwcc. Whether the same holds for mwcc, which has its own `-inline` modes and `auto` behavior, is an extrapolation.

### 2.4 What signature databases actually cover

| # | Claim | Tags | Basis |
|---|---|---|---|
| C25 | Signature databases auto-name only statically linked standard libraries (zlib, Lua, the C runtime). Game-specific naming came from strings, imports and accidental debug leftovers. Devilution used a symbols file left on the Japanese PlayStation disc plus a debug build hidden in the PC data archives. Silent Hill's team reverse-engineered an undocumented internal Konami vibration library by hand. Fingerprinting does not reach proprietary engine code. The sources do not compare results against a no-signature approach, so this is inferred. | [DERIVED][LOW] | S9, S30 |
| C24 | The documented trade-off is matching decompilation (years per game, human-readable, byte-exact proof) against static recompilation (weeks to months, machine-translated C, fast native port). N64Recomp (May 2024) translates MIPS straight to C. Recompilation gives speed but not understanding, and teams return to decompilation when behavior must change. **No supplied content describes a shared-name database or any cross-game name-sharing mechanism.** | [DERIVED][LOW] | S9 comparison table |
| C26 | The AI-assisted Silent Hill port used generative models to guess missing logic and produced frequent crashes and inconsistent flashlight behavior. The 45-contributor human team spent over two years reaching a readable, accurate decompilation. The byte-for-byte compile-and-diff check separates proven equivalence from code that merely looks right. | [DERIVED][LOW] | S30, S9 |

## 3. Unverified pointers from memory

These are **not research findings** and carry no source quality. Confirm each against the repo before relying on it. I give no file paths or line numbers, since I can't confirm them.

| Tool | Where to look | Memory-based note | Status |
|---|---|---|---|
| decomp-toolkit (dtk) | `github.com/encounter/decomp-toolkit` | Rust CLI for DOL/REL/RSO analysis, splitting and linking. I recall a built-in signature set for CRT/runtime functions. I'm not sure whether it supports user-extensible content signatures or how it masks relocations. | [UNVERIFIED-MEMORY] |
| objdiff | `github.com/encounter/objdiff` | Object-level diff that compares relocation targets symbolically, not by raw bytes. This is relevant to C16. | [UNVERIFIED-MEMORY] |
| Ghidra BSim / Function ID | `github.com/NationalSecurityAgency/ghidra` | Apache-2.0. BSim uses decompiler-derived features with similarity scores. Function ID uses hashes with masking. I'm unsure how well either handles PowerPC 750CL, paired singles, or SDA relocations. | [UNVERIFIED-MEMORY] |
| IDA FLIRT / Lumina | Hex-Rays documentation | Proprietary. FLIRT masks relocation-affected bytes in `.pat` and `.sig` files. I don't know whether public GameCube/CodeWarrior signature sets exist. | [UNVERIFIED-MEMORY] |
| Dolphin symbol maps | `github.com/dolphin-emu/dolphin` | GPL-2.0-or-later. Supports `.map` loading and a `.dsy` signature database, with menu entries to generate and apply them. Matching details and false-match reporting are unknown to me. | [UNVERIFIED-MEMORY] |

## 4. Verification plan: producing the falsifiable predictions you asked for

Each prediction below is a **hypothesis [HYPOTHESIS]**, not a finding, and each states what would falsify it.

| # | Prediction | Falsified if |
|---|---|---|
| P1 | Compile one function containing a call to an external symbol with mwcc, then relink it at two different addresses. The `.text` bytes of the **object** are identical, with the call emitted as `R_PPC_REL24` and the immediate field zero. After linking, the bytes differ. (Grounded in C16, but not in mwcc output I have seen.) | Object bytes differ between compiles, or the relocation type differs. |
| P2 | With `-sdata`/`-sdata2` thresholds changed, a global access switches between `R_PPC_EMB_SDA21` (r13/r2-relative) and `lis`+`addi`/`lwz` (`HA`/`L` pair). A hash masking only `REL24` will then split one function into two. (Extends C16; the threshold behavior is from memory.) | The relocation set is unchanged across thresholds. |
| P3 | With mwcc `-inline off` (or `-inline auto` with a small `-inline` limit), a small static helper called once appears as a standalone symbol. With aggressive inlining it vanishes and a standalone-function signature misses. (Analogous to C21 and C23, which are GCC-sourced.) | The standalone symbol persists under aggressive inlining. |
| P4 | Two SDK versions of the same library function (for example a `memcpy` or `OSReport` variant) produce different masked hashes. A single-variant database labels one build as a miss or a wrong match. (From C19 and C20.) | Masked hashes match across versions. |
| P5 | Any match-then-name pipeline will mislabel a nonzero share of functions. Measure it by building matched code under a second compiler or port and diffing behavior (C5, C6). | Zero mismatches over a large enough sample. State the sample size in advance. |

**Experiment design:**

- Use one mwcc build, one pair of flag sets, and one pair of SDK versions.
- Record the object-level hash with relocations masked.
- Record the hash without masking.
- Record the decomp.me or objdiff score.
- Call a false match any case where the hash agrees and the behavior or semantics disagree.

## 5. Gaps

- No repo URLs, licences, masking schemes or false-match reporting were established for any tool in the question. Section 3 is memory only.
- No source confirms that any cross-game name-transfer database exists for GameCube/Wii (C24). Its absence in these sources isn't evidence that none exists. Search the Decomp Toolkit Discord, the `encounter` org, and per-game decomp repos for symbol-sharing conventions.
- No mwcc-specific inlining or relocation evidence was supplied beyond S18. C19–C23 are drawn from GCC, glibc and general material.
- All but one learning is [LOW] quality and none is [OBSERVED]. Treat the whole report as a map of what to test, not a reference.

**Suggested next step:** I can run a targeted pass on the five repos in section 3, reading their signature and relocation-masking code directly. That would turn those pointers into sourced claims with file paths and replace P1–P4 with observed results. Say if you want that.

## Contradicciones detectadas (2)

Los conflictos siguientes se reportan SIN resolver, a propósito. Elegir un ganador en silencio sería inventar una certeza que las fuentes no dan.

**CONTRADICCIÓN** — Fuente [0] afirma: A byte-for-byte match proves only that one specific compiler turns the C into the original bytes, not that the C behaves correctly elsewhere, so matched code needs separate behavioral checks. · Fuente [11] afirma: The community's byte-for-byte compile-and-diff check is what separates proven equivalence from code that merely looks right, so it should be insisted on before trusting a port.
El conflicto NO está resuelto. Explicación probable: distinta metodología de medición (METHODOLOGY).
Para el operador: A byte match proves equivalence only for the original compiler and target, as [11] uses it. [0] shows that proof does not carry over to other compilers or ABIs, so require both a byte match and a behavioral check for any port or new target.

**CONTRADICCIÓN** — Fuente [0] afirma: Matched functions in the V-Rally port behaved wrongly on another target, so a byte match is not evidence that the code means the same thing under a different compiler or ABI. · Fuente [9] afirma: Matching decompilation provides byte-exact proof of equivalence, and that proof is the reason to choose it over faster routes such as static recompilation.
El conflicto NO está resuelto. Explicación probable: distinto contexto (CONTEXT).
Para el operador: Treat [9]'s 'proof' as holding only for the original toolchain and target. It does not hold for porting or for semantics inferred from a match, so the sources do not resolve how strong the guarantee is for portable code.

## Sources

- <https://www.retroreversing.com/byte-matching-decompilation-accuracy>
- <https://www.recompiled.games/guides/decompilation>
- <https://www.retroreversing.com/decompilers>
- <https://www.denis-iakimenko.com/blog/reverse-engineering-decompilation-ports>
- <https://grokipedia.com/page/Matching_Decompilation>
- <https://github.com/zcanann/mwcc-rs>
- <https://maskray.me/blog/long-branches-in-compilers-assemblers-and-linkers>
- <https://link.springer.com/chapter/10.1007/979-8-8688-2154-7_6>
- <https://en.wikipedia.org/wiki/Relocation_%28computing%29>
- <https://www.philipzucker.com/notes/Programming/linkers/>
- <https://runebook.dev/en/docs/gcc/compatibility>
- <https://devblogs.microsoft.com/oldnewthing/20260506-00/?p=112303/>
- <https://howtech.substack.com/p/mastering-symbol-versioning-for-backward>
- <https://en.wikipedia.org/wiki/Inline_expansion>
- <https://gcc.gnu.org/onlinedocs/gcc-4.1.2/gcc/Inline.html>
- <https://en.wikipedia.org/wiki/Inline_(C_and_C%2B%2B)>
- <https://ethz.ch/content/dam/ethz/special-interest/infk/ast-dam/documents/Theodoridis-ASPLOS22-Inlining-Paper.pdf>
- <https://www.theverge.com/games/1004869/reverse-engineered-games-all-the-news-on-video-game-decomps-recomps-vr-and-web-and-3d-ports>
- <https://www.thegamer.com/original-silent-hills-lost-code-recomp/>
- <https://www.ign.com/articles/a-massive-decompilation-community-is-shutting-down-thanks-to-the-deluge-of-ai-decomps-and-ports>
- <https://wal.sh/research/code-decomp/>

## Run metadata

- **Prompt:** What public tools or databases identify functions in a PowerPC GameCube/Wii DOL/REL by content and map them to known names or sources across games: dtk signatures, Ghidra BSim or Function ID databases, IDA FLIRT/Lumina-style PowerPC signatures, Dolphin symbol maps (.map/.dsy) and signature generators, masked-byte or relocation-aware hashing used to transfer matched functions between decomps? Give repo URLs, licences, how they mask relocations and how they report false matches. For every claim give the primary source (repo file, issue, PR, compiler manual) and state it as a falsifiable prediction: 'with X, mwcc emits Y; with X', it emits Y''. Mark anything unverified.
- **Depth / breadth:** 2 / 4
- **Queries used:** 12 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip, empty-input
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 417.0 s
- **Errors during run:** 55
- **Started at:** 2026-11-21T11:36:28Z
- **Module version:** deep_research 0.4.1
- **Quality gates:** 0 query/queries rejected as keyword soup · 2 learning(s) dropped for containing code · 15 dropped as not operator-actionable (relevance: UNRATED)
- **E1 decomposition:** 4/5 axes searched (BOUNDARY, COUNTEREXAMPLE, EVIDENCE, MECHANISM)  — SHORTFALL: only 2 axis/axes covered (EVIDENCE, MECHANISM) — minimum 3; missing: BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY; only 2 axis/axes covered (EVIDENCE, MECHANISM) — minimum 3; missing: BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY; only 2 axis/axes covered (COUNTEREXAMPLE, MECHANISM) — minimum 3; missing: EVIDENCE, BOUNDARY, TRANSFERABILITY; only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY
- **E2 landscape:** B_ACADEMIC×5, C_PRACTITIONER×2, D_VENDOR×2, UNKNOWN×30 · 0 question(s) refused as vendor-only · 0 learning(s) killed by the coverage gate
- **E3 reality:** DERIVED 12 · 12 label(s) demoted by the evidence gates
- **E4 contradictions:** 2 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `THIN` / MEDIUM [EVIDENCE] — 5 source(s), families C_PRACTITIONER, UNKNOWN — _What measured results exist on how often content-based function matching between GameCube _
- `UNCLASSIFIED` / LOW [EVIDENCE] — 5 source(s), families UNKNOWN — _When a decompilation project imports function names from another game's finished work by m_
- `UNCLASSIFIED` / LOW [MECHANISM] — 3 source(s), families D_VENDOR, UNKNOWN — _Why do two different functions, or two copies of the same library function, end up with id_
- `THIN` / MEDIUM [MECHANISM] — 2 source(s), families B_ACADEMIC, UNKNOWN — _Why do two copies of the same function compiled by the Metrowerks compiler end up with dif_
- `THIN` / HIGH [EVIDENCE] — 4 source(s), families B_ACADEMIC, UNKNOWN — _What measured data exists on how often the same C source compiled with different Metrowerk_
- `THIN` / MEDIUM [MECHANISM] — 5 source(s), families C_PRACTITIONER, UNKNOWN — _Why does the Metrowerks linker sometimes insert branch stubs or veneers or rewrite relocat_
- `UNCLASSIFIED` / LOW [BOUNDARY] — 3 source(s), families D_VENDOR, UNKNOWN — _What happens to function matching when the same library code was built with a different SD_
- `UNCLASSIFIED` / LOW [MECHANISM] — 4 source(s), families UNKNOWN — _Why does a compiler that inlines a small function, or merges and reorders code, leave a bi_
- `VENDOR_ONLY` / LOW [COUNTEREXAMPLE] — 0 source(s), families none — _Which reverse engineering teams or researchers have reported that automatic function match_
- `UNCLASSIFIED` / LOW [COUNTEREXAMPLE] — 5 source(s), families UNKNOWN — _Are there decompilation projects that skipped signature databases and shared function name_
- `UNCLASSIFIED` / LOW [BOUNDARY] — 1 source(s), families UNKNOWN — _How often do two games from the same studio and console generation, built with different c_
- `THIN` / MEDIUM [MECHANISM] — 2 source(s), families B_ACADEMIC, UNKNOWN — _Why do automated function-matching tools that compare control-flow structure, constants an_

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `source https://grokipedia.com/page/Matching_Decompilation carries instruction-like text ['tool-or-exfil-request']; treated as data`
- `decomposition narrow: only 2 axis/axes covered (EVIDENCE, MECHANISM) — minimum 3; missing: BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY`
- `source https://www.retroreversing.com/byte-matching-decompilation-a carries instruction-like text ['tool-or-exfil-request']; treated as data`
- `source https://grokipedia.com/page/Matching_Decompilation carries instruction-like text ['tool-or-exfil-request']; treated as data`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `relevance filter unavailable: llm-parse: no valid JSON in 1628 chars; head: '{"ratings":[{"index":0,"relevance":"LOW","reason":"Fails Q3 and mostly Q2: it is a true caution that a byte match does not prove behavior or names, bu'; anthropic-sdk: ANTHROPIC_API_KEY not set`
- `fetch_page 'https://stackoverflow.com/questions/678254/what-should-i-do-...': page-fetch: https://stackoverflow.com/questions/678254/what-should-i-do-if-two-libraries-provide-a-function-with-the-same-name-generati: HTTP Error 403: Forbidden`
- `fetch_page 'https://stackoverflow.com/questions/15497220/two-lib-contain...': page-fetch: https://stackoverflow.com/questions/15497220/two-lib-containing-different-functions-with-the-same-name-how-to-choose-the-ri: HTTP Error 403: Forbidden`
- `fetch_page 'https://github.com/mohitmishra786/underTheHoodOfExecutables/...': page-fetch: https://github.com/mohitmishra786/underTheHoodOfExecutables/blob/main/src/Ch-6-Relocations-Patching-The-Code/The%20Linker's%20Patchwork.md: HTTP Error 429: Too Many Requests`
- `fetch_page 'https://people.cs.pitt.edu/~xianeizhang/notes/Linking.html...': page-fetch: https://people.cs.pitt.edu/~xianeizhang/notes/Linking.html: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1010)>`
- `fetch_page 'https://stackoverflow.com/questions/55110545/why-is-there-a-...': page-fetch: https://stackoverflow.com/questions/55110545/why-is-there-a-relocation-needed-if-calling-function-in-same-translation-unit: HTTP Error 403: Forbidden`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `decomposition narrow: only 2 axis/axes covered (EVIDENCE, MECHANISM) — minimum 3; missing: BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY`
- `fetch_page 'https://www.nxp.com/design/design-center/software/developmen...': page-fetch: https://www.nxp.com/design/design-center/software/development-software/codewarrior-development-tools:CW_HOME: HTTP Error 404: Not Found`
- `learning dropped (code gate): schema field names (3 identifiers): optimization_level, optimize_for_size, register_coloring`
- `epistemic demoted DERIVED -> HYPOTHESIS: ledger: no quote verified in any snapshot`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `fetch_page 'https://stackoverflow.com/questions/67500470/are-there-hidde...': page-fetch: https://stackoverflow.com/questions/67500470/are-there-hidden-dangers-to-link-libraries-compiled-with-different-c-standard: HTTP Error 403: Forbidden`
- `fetch_page 'https://stackoverflow.com/questions/41641751/using-shared-li...': page-fetch: https://stackoverflow.com/questions/41641751/using-shared-libraries-and-mismatched-compilers: HTTP Error 403: Forbidden`
- `source https://runebook.dev/en/docs/gcc/compatibility carries instruction-like text ['tool-or-exfil-request']; treated as data`

</details>


## Evidence ledger

- **Claims:** 29 · with a verified quote: 28 (rate 0.966)
- **Quotes:** 43 offered, 5 rejected (not verbatim / unknown source / length)
- **Sources:** 34 snapshots in 34 independent lineage(s); 2 URL(s) were byte-identical copies
- **Labels lowered by the ledger:** 4
- **Sources with instruction-like text (treated as data):** 7

**C1** [OBSERVED] Reported progress numbers measure different things: one AI-assisted Super Mario 64 DS project reports 99.9% of functions matched while its readable-source conversion counter sits at 30.5%. Likewise, decomp.dev separates a 'decompiled' percentage from a 'fully linked' one, so a single completion figure can overstate real, shippable status.
  - S3 <https://kingy.ai/blog/ai-video-game-decompilation-legality/> chars 204-358: "An AI-assisted Super Mario 64 DS reconstruction reports 99.9% of its functions matched. Its counter for source converted into readable form sits at 30.5%."

**C2** [DERIVED] None of the retrieved material reports a measured rate of wrong-name or wrong-source-file results from content-based matching between GameCube and Wii decomp projects, nor who reported such mismatches. The nearest evidence is that matching is judged per function by byte comparison, that the shared Dolphin SDK is reused across games, and that a function-level match does not certify unique historical source. The question is therefore unanswered by public evidence here.
  - S4 <https://grokipedia.com/page/Matching_Decompilation> chars 3502-3567: "A match certifies generated code, not a unique historical source."

**C3** [DERIVED] Matching is scored per function and the site never sees the other bytes, while a project-level hash is a stricter claim. A function can match while the surrounding image does not, so a name or file attribution inferred from a matching function carries uncertainty that the match score itself does not remove.
  - S4 <https://grokipedia.com/page/Matching_Decompilation> chars 16532-16674: "A hash of the whole image is a stricter claim than a match of one function. decomp.me scores a single function and never sees the other bytes."

**C4** [DERIVED] A matching decompilation only proves one specific compiler turns the C into the original bytes, not that the C means the same thing to another compiler or ABI. In the V-Rally port, a set of matched functions each behaved wrongly once built for another target, including cars starting backwards, textures loading at 0 by 0 pixels and sign errors turning 255 into -1. Any name or semantics inferred from a match should be treated as unverified until run under a different build.
  - S6 <https://www.retroreversing.com/byte-matching-decompilation-accuracy> chars 668-713: "Identical bytes prove less than they seem to."
  - S6 <https://www.retroreversing.com/byte-matching-decompilation-accuracy> chars 7645-7787: "Each function involved matched byte for byte with KMC GCC 2.7.2, and each one behaved differently once compiled with clang for another target:"

**C5** [DERIVED] The sources point to cheap behavior checks that surface errors a match hides: building under a second modern compiler, building a port, and comparing memory against the running original. Super Mario 64 already runs a host GCC syntax check alongside the IDO build, and every bug on the V-Rally page was found by building a port. A progress percentage from a match checker is not a correctness measure.
  - S6 <https://www.retroreversing.com/byte-matching-decompilation-accuracy> chars 13532-13576: "Every bug on this page came from doing that."

**C6** [DERIVED] None of the supplied sources quantify how often names imported by matching code across games turn out wrong, or name anyone who has counted. The nearest evidence is anecdotal bug lists in one port and the Decomperson study's 300 successful perfect decompilations out of 35,000 submissions, which measures human matching success, not name accuracy. Any decision relying on a rate would rest on an assumption.
  - S4 <https://grokipedia.com/page/Matching_Decompilation> chars 1104-1270: "Their Decomperson study recorded more than 35,000 submissions from over 150 participants, including more than 300 successful perfect decompilations of small programs."

**C7** [DERIVED] When several static libraries bundled into one product carry duplicated code, the application gets materially larger, and the same duplication is what produces naming collisions and unpredictable crashes. Duplicate copies of the same library are therefore a recurring, avoidable cost, not just a technical curiosity.
  - S10 <https://trtc.io/learning/navigating-library-conflicts-in-software-development> chars 2008-2117: "Using multiple static libraries with duplicated code can significantly increase the size of your application."

**C8** [HYPOTHESIS] The source lists different versions of the same library referenced within one project as a distinct conflict type, producing inconsistent definitions of the same file or function. This implies that identical-looking or near-identical code from different versions can be mislabeled, so any name-based identification of the code should be treated as provisional until versions are reconciled.
  - S10 <https://trtc.io/learning/navigating-library-conflicts-in-software-development> chars 1790-1861: "Different versions of the same file leading to inconsistent definitions"

**C9** [DERIVED] In an unlinked object file, references to other functions and to global data are left as unresolved placeholders listed in a relocation table, and the linker computes the real addresses only afterward. So two identical functions can differ in bytes at exactly those reference sites depending on where the linker places things, which means a comparison must account for relocation entries rather than raw bytes alone.
  - S13 <https://pld.cs.luc.edu/courses/264/spr19/notes/linking.html> chars 2088-2194: ".rel.text:   list of unresolved addresses in the .text         section (data and jumps to other sections)."
  - S13 <https://pld.cs.luc.edu/courses/264/spr19/notes/linking.html> chars 901-998: "calls to other procedures: address has to be worked out, entered into         code before running"

**C10** [DERIVED] A call to a function in another module is compiled as a call to a small jump stub, which loads the real target through a table that is resolved lazily. The stub and table are generated at link time, so the code inside the function looks ordinary while the stub it lands on differs by link layout.
  - S13 <https://pld.cs.luc.edu/courses/264/spr19/notes/linking.html> chars 12935-13067: "This looks like a normal function call. But let's look at the ode for       ml_util_func@plt (which is different from ml_util_func):"

**C11** [DERIVED] The retrieved material covers only generic linking and relocation on GCC and x86-64 ELF. It says nothing about Metrowerks, register allocation, or inlining, and the second source failed to load, so those parts of the query remain unanswered and need targeted sources on that compiler.
  - S12 <https://link.springer.com/content/pdf/10.1007/978-1-4302-6668-6_9.pdf> chars 17-60: "A required part of this site couldn’t load."

**C12** [HYPOTHESIS] None of the retrieved contents contain any measured rate of PowerPC instruction differences across CodeWarrior versions or flag settings, nor any decompilation project that recorded such differences. They cover only the product's history, a profiler manual, and an MPW-to-CodeWarrior porting guide, so the research question remains unanswered by this batch.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C13** [DERIVED] CodeWarrior exposes many code-generation controls: the pragma list in the reference includes scheduling, peephole, register_coloring, optimization_level, optimize_for_size, and PPC loop-unrolling limits. The profiler option additionally inserts compiler-generated code at the entry and exit of every profiled routine. Each of these can alter emitted instructions independently of the compiler version, so any comparison needs to fix them.
  - S14 <https://web.mit.edu/macdev/Development/Documentation/www/devdoc/MW_profiler.html> chars 5502-5715: "Since profiler code is generated by the compiler and inserted at the entry- and exit-point of every profiled routine, you will have to step through some additional assembly code when you are tracing your porgrams."

**C14** [HYPOTHESIS] CodeWarrior shipped about eleven numbered releases from December 1993 to December 1996, plus later Pro releases, so many compiler builds exist to match against. Its PPC code generator was written from scratch around Chaitin-style register allocation, and the later pragma list shows additional PPC unrolling controls. This suggests version-to-version differences in register allocation and scheduling are plausible, though no content measures them.
  - S17 <https://en.wikipedia.org/wiki/CodeWarrior> chars 10612-10758: "During its heyday, the product was known for its rapid release cycle, with multiple revisions every year, and for its quirky advertising campaign."

**C15** [DERIVED] When a branch target is out of range, the instruction encoding is already fixed at link time, so the linker cannot change it. Instead it generates a thunk (also called a veneer, branch stub, or trampoline) and redirects the original branch to it. The linked binary therefore contains extra linker-made code that never existed in the compiler's output, and the call site now points at the thunk rather than the real callee. A matching tool comparing linked bytes against compiled objects will see mismatches that are not compiler differences.
  - S19 <https://maskray.me/blog/long-branches-in-compilers-assemblers-and-linkers> chars 15249-15350: "At this point, the instruction encoding is fixed, so the linker cannot simply change the instruction."
  - S19 <https://maskray.me/blog/long-branches-in-compilers-assemblers-and-linkers> chars 15573-15662: "The original branch is redirected to the thunk, which then jumps to the real destination."

**C16** [DERIVED] The mwcc-rs project defines parity as emitting the same relocatable object as the real Metrowerks compiler, byte for byte, and treats an exact .text section alone as useful evidence but not parity. It also keys on section ordering, symbol order, alignment, and relocations such as R_PPC_EMB_SDA21. Comparing at the object stage, before addresses are assigned, avoids layout-dependent changes made at link time.
  - S18 <https://github.com/zcanann/mwcc-rs> chars 980-1126: "for every configured translation unit in reference_projects/* , mwcc-rs must emit the same relocatable object as the real compiler, byte for byte."

**C17** [DERIVED] A relocation table lists addresses in the object code that must be changed once final locations are assigned, and the linker modifies symbol references in code and data to point at the assigned run-time addresses. Bytes at those positions differ between the object and the linked image by design. A comparison tool therefore has to treat these fields as relocations, not as literal bytes.
  - S20 <https://en.wikipedia.org/wiki/Relocation_%28computing%29> chars 4495-4634: "Referring to the relocation table to modify symbol references in data and object code so that they point to the assigned run-time addresses"

**C18** [DERIVED] Compiler version changes can alter struct layout, calling conventions and virtual table layout, and the standard library's own layout (e.g. std::string after C++11) differs between versions. Code compiled by different toolchain versions therefore has different machine-level shape, so a signature database built from one toolchain will see the same source function as different bytes and may miss it or misattribute it.
  - S22 <https://runebook.dev/en/docs/gcc/compatibility> chars 443-556: "GCC updates can sometimes introduce changes to the ABI. When this happens, a new compiler might arrange data in a"
  - S22 <https://runebook.dev/en/docs/gcc/compatibility> chars 849-1008: "If the vtable (virtual function table) layout changes between GCC versions, code that expects the old layout will crash when trying to call a virtual function."

**C19** [DERIVED] Behavior of a library function can legitimately differ depending on which SDK version the calling code was built against, and a single program can mix modules built against different SDK versions, including static libraries. A matched function name therefore does not guarantee the same behavior or body as the reference, which raises the risk of a confident but wrong identification.
  - S23 <https://devblogs.microsoft.com/oldnewthing/20260506-00/?p=112303/> chars 2250-2382: "Also, what if a program is linked with one version of the SDK, but a DLL that it uses is linked with a different version of the SDK?"
  - S23 <https://devblogs.microsoft.com/oldnewthing/20260506-00/?p=112303/> chars 5811-5904: "Changing behavior based on the SDK version you link to works only if programs are monolithic."

**C20** [DERIVED] Shared libraries such as glibc keep multiple versioned implementations of the same function, for example memcpy@GLIBC_2.2.5 alongside memcpy@@GLIBC_2.14, and binaries built years apart bind to different ones. Matching must therefore cover every retained variant, and a database that stores only the newest will miss or mislabel older builds.
  - S24 <https://howtech.substack.com/p/mastering-symbol-versioning-for-backward> chars 700-830: "When glibc ships a faster memcpy implementation, old binaries keep using memcpy@GLIBC_2.2.5 while new ones get memcpy@@GLIBC_2.14."

**C21** [DERIVED] When every call to a function is inlined and its address is never taken, the compiler emits no standalone copy of that function at all, so a signature built from the standalone version has nothing to match. A 'not found' result can therefore mean the code is present but dissolved into its callers, not that the library was never used.
  - S25 <https://en.wikipedia.org/wiki/Inline_expansion> chars 1307-1431: "Inline expansion is similar to macro expansion as the compiler places a new copy of the function in each place it is called."

**C22** [DERIVED] Inlining puts a separate copy of the function body at each call site, and then optimizes each copy in its caller's context. Constants passed in can fold away branches, so no two copies need look alike or look like the standalone function. A signature may match some copies, none, or fire inconsistently, and an inlined function called 10 times yields 10 differing copies instead of one.
  - S25 <https://en.wikipedia.org/wiki/Inline_expansion> chars 1573-1671: "If a function is inlined 10 times, there will be 10 copies of the function inserted into the code."

**C23** [DERIVED] Inlining is largely an optimizing-build behavior: GCC inlines nothing without optimization unless forced, so debug-style builds keep standalone functions that signatures can find, while optimized release builds may erase them. Compilers also differ in what they can inline, so results vary across toolchains.
  - S27 <https://en.wikipedia.org/wiki/Inline_(C_and_C%2B%2B)> chars 2345-2422: "Different compilers vary in how complex a function they can manage to inline."

**C24** [DERIVED] None of the contents describe a project that shared function names across games through a shared-name database or comparable mechanism; the real trade-off documented is between matching decompilation (years per game, human-readable, byte-exact proof of equivalence) and static recompilation (weeks to months, unreadable machine-translated C, but a fast native port). Recompilation gives speed but not understanding, so teams return to a decompilation when behavior must be changed.
  - S9 <https://www.denis-iakimenko.com/blog/reverse-engineering-decompilation-ports> chars 19218-19335: "Static recompilation trades understanding for speed. You get a native port, and nobody knows what func_80024A10 does."

**C25** [DERIVED] Signature databases only auto-name statically linked standard libraries such as zlib, Lua, or the C runtime. Game-specific naming came from strings, imports, and accidental debug leftovers: Devilution used a symbols file left on the Japanese PlayStation disc plus a debug build hidden in the PC data archives, and Silent Hill's team had to reverse-engineer an undocumented internal Konami vibration library by hand. Signature fingerprinting therefore does not reach proprietary engine code.
  - S9 <https://www.denis-iakimenko.com/blog/reverse-engineering-decompilation-ports> chars 5576-5728: "Known libraries. Statically linked zlib, Lua, or a C runtime can be fingerprinted and auto-named. Ghidra and IDA both ship signature databases for this."
  - S9 <https://www.denis-iakimenko.com/blog/reverse-engineering-decompilation-ports> chars 16824-17003: "Diablo was rebuilt in 2018 as Devilution, using a symbols file accidentally left on the Japanese PlayStation disc plus a debug build hidden inside the PC game’s own data archives."
  - S30 <https://www.thegamer.com/original-silent-hills-lost-code-recomp/> chars 2670-2766: "One of the toughest obstacles was a vibration function buried inside an internal Konami library."

**C26** [DERIVED] The AI-assisted Silent Hill port relied on generative models to guess missing logic and produced frequent crashes and inconsistent flashlight behavior, while the 45-contributor human team spent over two years reaching a readable, accurate decompilation. AI has also sharply cut timelines elsewhere, but the community's byte-for-byte compile-and-diff check is what separates proven equivalence from code that merely looks right.
  - S30 <https://www.thegamer.com/original-silent-hills-lost-code-recomp/> chars 1767-2017: "That version relied heavily on generative models to guess at missing logic, which led to frequent crashes, inconsistent flashlight behavior, and a cycle where players reported bugs and the developer fed those issues into AI to generate quick patches."
  - S9 <https://www.denis-iakimenko.com/blog/reverse-engineering-decompilation-ports> chars 23928-24030: "Matching decompilation exists to prove equivalence, and code that merely “looks right” proves nothing."

**C27** [DERIVED] In SBridge's evaluation, optimization level was the largest single driver of match reliability: top-1 recall was 84.96% at -O0 versus 65.31% at -O2, while architecture (about 71-78%) and compiler (GCC 75.4% vs Clang 74.9%) barely moved it. Binaries built with heavy optimization should therefore be treated as lower-confidence matches regardless of platform or compiler.
  - S34 <https://www.emergentmind.com/topics/sbridge> chars 12411-12444: "Optimization has a larger effect:"
  - S34 <https://www.emergentmind.com/topics/sbridge> chars 12326-12410: "Across compilers, results are 0.7537 / 0.8097 for GCC and 0.7490 / 0.8099 for Clang."
  - _extractor cited S33; quote found verbatim in S34 (citation corrected)_
  - _ledger: OBSERVED number(s) absent from verified spans: 65.31%, 71, 74.9%, 75.4%, 78%, 84.96%_

**C28** [DERIVED] Function inlining collapses several source functions into one binary function, which breaks matchers that compare whole-function structure. About 40% of binary functions in the test set were inlined; the prior tool BinaryAI scored under 0.01 Recall@1 on inlined functions, while the inlining-aware block approach reached 75.13% overall.
  - S34 <https://www.emergentmind.com/topics/sbridge> chars 14059-14166: "In the adapted inlined-function setting, the paper reports that BinaryAI achieved less than 0.01 Recall@1 ("
  - _ledger: OBSERVED number(s) absent from verified spans: 40%, 75.13%_

**C29** [DERIVED] Stripping symbols lowers top-1 recall from 79.09% to 71.19%, and the authors concede that decompiler quality, very long decompiled functions and the lack of data-flow analysis cause wrong mappings. In the vulnerability-detection use, the tool had only 59.49% precision and 42.18% recall, so a flagged match still needs human verification.
  - S34 <https://www.emergentmind.com/topics/sbridge> chars 15343-15391: "Decompilation quality directly affects accuracy."
  - S34 <https://www.emergentmind.com/topics/sbridge> chars 15514-15612: "Exceptionally long decompiled functions can produce incorrect mappings even with length filtering."
  - _ledger: OBSERVED number(s) absent from verified spans: 42.18%, 59.49%, 71.19%, 79.09%_
