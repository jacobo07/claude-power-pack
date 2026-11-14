# CodeWarrior version mixing in commercial Wii games: evidence, tooling, and the "true match" test

## 0. Read this first: what the evidence does and doesn't cover

The research returned **one on-topic primary source**, the Petari wiki for Super Mario Galaxy 1 (ledger S1, cited in C1, C2, C9 and C10), plus one on-topic project README on frame and stack mismatches (S9, decomp-triage on Super Mario Sunshine, a GameCube game). Everything else is generic and only loosely related.

| Part of your question | Research coverage |
|---|---|
| Do Wii games mix CodeWarrior versions? | **One game (SMG1) documented.** Nothing on other titles. |
| How is each object's version detected? | **Partial.** Three heuristics are listed by one wiki, with no tooling detail. |
| How is `mw_version` set per unit in `configure.py`? | **No learning covers it.** Section 3 is background knowledge, unverified. |
| Compiler wrappers | **No learning covers it.** Unverified. |
| What separates a true match from a coincidence? | **Only fragments.** Section 5 is mostly my own reasoning and is flagged as such. |

Two further limits:
- The ledger labels (S1, S9, S14, and so on) are the only provenance I have. I could not resolve them to URLs, repo paths or commit hashes. Every "primary source" below is therefore a ledger ID, not a verified link.
- I have no compiler manual citation for any claim. None of the predictions below has been run against `mwcceppc.exe` in this session.

Tag legend: `[EPISTEMIC][QUALITY]` is carried from the research. `[HYPOTHESIS][UNSOURCED]` is my own background knowledge or reasoning, not backed by any returned learning. Verify it before relying on it.

---

## 1. Do commercial Wii games link objects from different CodeWarrior versions?

### 1.1 The one documented case: Super Mario Galaxy 1

| Component | Compiler matched | Source |
|---|---|---|
| Game code | GC 3.0a3 | S1 (Petari wiki) |
| RVL_SDK, NW4R, JSystem, MSL | GC 3.0 | S1 |
| MetroTRK | GC 2.5 | S1 |

- [DERIVED][MEDIUM] The Petari wiki table gives a per-library split. A single-compiler assumption would make some library code unmatchable, so setup and effort estimates must be per component (C1).
- [HYPOTHESIS][MEDIUM] The same table appears again with the added statement that "a lot of testing went into finding the correct compiler per library" (C9). It is tagged "no verified citation", but it is the same claim as C1. I treat the two as one observation with one source, not as independent confirmation.
- **Thin evidence:** this is one game. "Commercial Wii games link mixed versions" is established for SMG1 only. Generalising to other titles is an inference, and I have no learning that supports it.
- **Thin evidence:** the table says what matched. It does not say what failed under the alternatives. See section 5.

### 1.2 Falsifiable predictions (SMG1)

All of these are derived from S1. S1 does not state the cross-tests explicitly, so the negative halves are inferred.

1. With GC 3.0a3, an SMG1 game-code translation unit (TU) reproduces the original bytes. With GC 3.0, the same TU does not. `[DERIVED][MEDIUM]`
2. With GC 3.0, an MSL, NW4R, JSystem or RVL_SDK TU reproduces the original bytes. With GC 3.0a3, it does not. `[DERIVED][MEDIUM]`
3. With GC 2.5, MetroTRK TUs match. With 3.0 or 3.0a3, they do not. `[DERIVED][MEDIUM]`

**Falsifier:** if a single version (for example 3.0a3) matches every component, the per-library split is only a convention and not a necessity.

---

## 2. How projects detect an object's compiler version

### 2.1 What the research supports

- [DERIVED][MEDIUM] The SMG community pinned versions with three signals (C2, C10, S1):
  1. The shipped game's build date. Pick the most recent compiler build near that date.
  2. Codegen differences that rule compilers in or out by trial and error.
  3. SDK libraries such as NW4R whose initialization functions print the compiler build.
- [DERIVED][MEDIUM] The cheap signals (date, self-reported string) shorten the candidate list before the expensive one (trial and error) is applied (C10). The source gives **no measurements** of how much each signal narrows the search, so any cost claim is inferred.
- [DERIVED][MEDIUM] A verification recipe: compile one already-matched function with candidate flags and see which reproduces its bytes. Cross-check against a sibling project on the same platform. This catches a wrong version or flag early (C31, S36). The source reports no actual per-file version error caught this way.

### 2.2 Prediction for the build-string signal

`[DERIVED][MEDIUM]`, source S1:
- If a library prints its compiler build in an init function, then `strings` on the DOL or REL shows that build identifier. The matching compiler is the one whose own build ID is consistent with it.
- **Falsifier:** the printed build string disagrees with the version that byte-matches the library's functions. That would mean the string is stale, copied or unrelated to the compile.

### 2.3 Unverified background (not from research)

- [HYPOTHESIS][UNSOURCED] CodeWarrior-linked ELF objects carry a `.comment` section recording compiler-version info, and decomp-toolkit splits can carry per-file comment-version metadata. If so, the original per-object toolchain version might be partly recoverable from retail artefacts. I have no learning confirming this, and retail DOLs are typically stripped, so treat it as a lead to check, not a fact.

---

## 3. Setting the version per object: `configure.py` and wrappers

**None of the returned learnings documents this.** What follows is background recall, with no repo file or PR confirmed. Verify each item against the actual repo (for example the decomp-toolkit template's `configure.py`) before use.

- [HYPOTHESIS][UNSOURCED] Template-style projects keep a `config.linker_version` for the link step. Each compile unit is an `Object(...)` entry inside a library dict, and a per-library or per-object `mw_version` string selects a compiler directory such as `GC/3.0a3` or `Wii/1.x`. Libraries inherit a default and override it where the original build did.
  - **Prediction:** changing only `mw_version` on one `Object` changes only that object's `.o`, and `ninja` rebuilds only that unit. **Falsifier:** other units rebuild, meaning the setting is global.
- [HYPOTHESIS][UNSOURCED] Compiler wrappers commonly handle Shift-JIS source encoding and running the Windows `mwcceppc.exe` under Linux or macOS via a wine replacement. A dependency-file transform step is also typical.
- **Mapping to the SMG1 table (inferred, not observed):** game objects would get `GC/3.0a3`. SDK, NW4R, JSystem and MSL would get `GC/3.0`. MetroTRK would get `GC/2.5`.

**Gap:** I have no issue, PR or repo file showing how any project handles per-object override rules, nor evidence of a wrapper that auto-detects versions. I believe none does, but that is unverified.

---

## 4. Compiler-version-dependent symptoms (what a wrong version looks like)

### 4.1 Evidence from Super Mario Sunshine (GameCube, S9)

- [DERIVED][MEDIUM] In a 10,115-function decompilation, 8,072 functions matched. About 600 were frame-only (every instruction right, stack frame wrong), about 1,150 had both frame and code wrong, and about 350 were structural (C6).
  - Frame-only functions are the hardest, not the cheapest. The diff shows no progress and the automated permuter has nothing to optimise toward.
  - **Relevance:** a wrong compiler version could masquerade as a frame-only bucket. The source does not say that any frame-only function turned out to be a version problem. That link is my inference.
- [DERIVED][MEDIUM] Compiler lessons don't transfer between siblings (C8, S9):
  - GC/1.x never reclaims dead stack slots, while the ARM variant (mwccarm) does.
  - One lever for by-value class parameters, proven on the DS project, failed against every frame-only function.
  - **Prediction:** a function with sequential scoped locals under GC/1.x has a frame sized for all slots. Under mwccarm the frame shrinks. **Falsifier:** both compilers produce the same frame size for that function.
- [DERIVED][MEDIUM] Hidden mismatch from dead-stripping (C7, S9):
  - 204 symbols across 185 sections (5.1% of "target lacks this" reports) were misclassified because the original linker dead-stripped symbols that are absent from extracted objects but listed in the link map.
  - Acting on that output cost 4,416 bytes of matched data in one commit, which was reverted.
  - 40 unexplained bytes at the start of `.data` turned out to be a precompiled-header footprint, which looked like a wrong struct but was a flags mismatch.
  - **Implication:** before concluding "wrong compiler version", check the original link map and the PCH or flag setup.

### 4.2 Generic guidance (lower confidence)

- [DERIVED][LOW] Register, ordering and stack-frame differences suggest experiments but are not unique diagnoses. Fixes depend on compiler and version, so log the compiler, flags and diff for each attempt (C11, S14). The source never describes a wrong compiler release being found.
- [DERIVED][LOW] If the same register or frame pattern recurs across many unmatched functions in one library while neighbours match, a systematic cause such as the compiler build is plausible (C12, S14). This is my extension, not the guide's statement.
- [DERIVED][LOW] The linker can fold identical functions, so a debugger shows a different name at the same address. Whether folding occurs depends heavily on compiler version and flags, and is common with templates (C27, S21). Raymond Chen's example is the Microsoft linker's identical COMDAT folding (`Class1::GetQ` and `Class2::GetValue` at `010010d6`).
  - **Caveat:** that example is the MSVC linker, not the CodeWarrior linker. It shows the general phenomenon, not that CodeWarrior behaves the same way. Whether the Wii-era linker folds is not established here.

---

## 5. What makes a non-baseline match a true match

**No learning directly answers this.** What follows combines the generic fragments with my own reasoning, flagged where applicable.

### 5.1 From the research

- [DERIVED][LOW] A similarity score doesn't explain why a function differs. A function-level match doesn't show the whole image is correct. Test the checker by feeding it deliberately wrong candidates to confirm it rejects them (C13, S14).
- [DERIVED][MEDIUM] Reproducing the bytes of an already-matched function under candidate flags is the cheap sanity check (C31).
- [DERIVED][LOW] Headline match percentages can hide unfinished work (C14, S18). SM64DS reports 99.9% matched but only 30.5% converted to readable source. Counted units must be disclosed.
- [DERIVED][LOW] Version and flag choice is a human-prepared precondition, not something an agent removes (C15, S18).

### 5.2 Proposed decision criteria (my reasoning, speculative)

`[HYPOTHESIS][UNSOURCED]`: none of these thresholds comes from a project's documented policy.

| # | Criterion | Why it separates true from coincidental |
|---|---|---|
| 1 | **Unit-level, not function-level.** Most or all functions in the TU match under X', and the baseline X fails on several of them. | One function matching under X' is weak. Small leaf functions often compile identically across many versions. |
| 2 | **Weight by codegen decisions.** Count the independent decisions in the function that differ between X and X' (scheduling, register allocation, inlining, constant pooling, stack layout). | Few decisions mean low evidential weight. Many decisions all agreeing mean high weight. |
| 3 | **Data-side agreement.** `.rodata`, `.sdata`, `.sdata2`, string pooling, symbol and section order and relocations also match under X'. | Coincidental instruction matches rarely reproduce data layout. |
| 4 | **Negative control.** Known-good functions in the same library match under X' and fail under X, or at least the pattern is consistent across the library. | Distinguishes "this library is X'" from "this function is lucky". |
| 5 | **Independent provenance.** Build date, library self-reported build string, or a sibling project on the same platform agrees (C2, C10, C31). | Prior probability from non-codegen evidence. |
| 6 | **Checker soundness.** Reject known-wrong candidates (C13). | A lenient checker makes everything "match". |
| 7 | **Link-map check.** Compare against the original map for stripped or folded symbols before concluding anything (C7, C27). | Removes artefacts that mimic a version difference. |

**Predictions for the decision rule:**
- If a function is a true X' match, then every other non-trivial function in that library built with X' also matches, and the same functions fail under X. **Falsifier:** X' matches only isolated functions and fails the rest of the library.
- If a match is coincidental, then compiling a large sibling function in the same TU under X' fails even when under X it nearly matches.

### 5.3 Thin spots

- I found no recorded case of a Wii function matching only under a non-baseline compiler and being accepted or rejected. The criteria above are therefore **untested here**.
- The SMG1 split is itself the best example of the principle (whole libraries differ), but the wiki doesn't describe individual borderline functions.

---

## 6. Off-topic learnings (retained for completeness, low relevance)

These do not address Wii or CodeWarrior and are tagged accordingly:
- [DERIVED][LOW] An up-front dependency and toolchain audit prevents overruns (C4, S7). It does not mention a Wii compiler mismatch.
- [DERIVED][LOW] Engine and toolchain upgrades change which compiler builds what, and should be costed with regression tests (C5, S5/S7). The Unity chain to a Wii studio is inferred.

I would not cite either as evidence for the research question.

---

## 7. Recommended next steps (to close the gaps)

1. **Pull the primary sources.** Get the Petari SMG1 compiler page and the decomp-toolkit template `configure.py`. Record file paths, commit hashes, and the exact `mw_version` strings.
2. **Run the three SMG1 predictions** (section 1.2) against the real compilers. This is the only way to turn the `[DERIVED]` claims into `[OBSERVED]`.
3. **Check `.comment` section recoverability** (section 2.3) on a retail DOL or REL, and on a debug build if one exists.
4. **Look for borderline cases** in other Wii decomp repos' issues or PRs, where a function matched only under a non-baseline version, and see what evidence the maintainers required.
5. **Treat SM Sunshine frame-only results as a hint, not proof.** Test a version hypothesis on a whole library before blaming the compiler for a handful of functions.

## Contradicciones detectadas

Ninguna. Las fuentes procesadas no se contradicen entre sí en los puntos extraídos. Esto no significa consenso del campo: significa que las fuentes que este run alcanzó coinciden.

## Sources

- <https://github.com/SMGCommunity/Petari/wiki/CodeWarrior>
- <https://github.com/encounter/decomp-toolkit>
- <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/>
- <https://celestialamber.github.io/GC-Wii-Decomp-Splitting-Guide/>
- <https://docs.unity3d.com/540/Documentation/Manual/PlatformDependentCompilation.html>
- <https://docs.unity3d.com/420/Documentation/Manual/PlatformDependentCompilation.html>
- <https://www.cubix.co/blog/game-porting/>
- <https://github.com/FuturesLab/Bin2Wrong>
- <https://github.com/KakarottoCake/decomp-triage>
- <https://en.wikipedia.org/wiki/Decompiler>
- <https://docs.hex-rays.com/ida-9.2/user-guide/decompiler/failures>
- <https://www.reddit.com/r/learnprogramming/comments/vff0n5/why_different_machine_code_is_generated_by/>
- <https://docs.nxp.com/bundle/GUID-9FAC1C79-3809-474F-B8DF-82BEB5B88419/page/GUID-25B710D5-3B80-45E6-8BC0-30EF5FCE89F9.html>
- <https://www.retroreversing.com/decompilers>
- <https://www.bohrium.com/en/sciencepedia/feynman/compiler_principles_undergraduate-decompilation_techniques>
- <https://www.reddit.com/r/learnprogramming/comments/fhaykb/does_decompiling_files_restore_the_original_code/>
- <https://devblogs.microsoft.com/visualstudio/disassembly-improvements-for-optimized-debugging/>
- <https://hex-rays.com/blog/igors-tip-of-the-week-40-decompiler-basics>
- <https://kingy.ai/blog/ai-video-game-decompilation-legality/>
- <https://learn.microsoft.com/en-us/cpp/error-messages/compiler-errors-1/fatal-error-c1047?view=msvc-170>
- <https://learn.microsoft.com/en-us/cpp/build/working-with-project-properties?view=msvc-170>
- <https://devblogs.microsoft.com/oldnewthing/20050322-00/?p=36113/>
- <https://initialrise.github.io/REWiki/04-recomp/matching-decomp/>
- <https://grokipedia.com/page/Matching_Decompilation>
- <https://tanepiper.github.io/game-frame/consoles/matching-decomp>
- <https://www.youtube.com/watch?v=Pl7ThC4PiVA>

## Run metadata

- **Prompt:** Do commercial Wii games link libraries built with different CodeWarrior versions (SDK, NW4R, MSL, game code), how do projects detect each object's compiler version and set it per object (configure.py mw_version per unit, compiler wrappers), and what evidence decides that a function matching only under a non-baseline compiler is a true match rather than a coincidence? For every claim give the primary source (repo file, issue, PR, compiler manual) and state it as a falsifiable prediction: 'with X, mwcc emits Y; with X', it emits Y''. Mark anything unverified.
- **Depth / breadth:** 2 / 4
- **Queries used:** 12 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 514.8 s
- **Errors during run:** 45
- **Started at:** 2026-11-14T13:57:21Z
- **Module version:** deep_research 0.4.1
- **Quality gates:** 0 query/queries rejected as keyword soup · 0 learning(s) dropped for containing code · 16 dropped as not operator-actionable (relevance: rated)
- **E1 decomposition:** 4/5 axes searched (BOUNDARY, COUNTEREXAMPLE, EVIDENCE, MECHANISM)  — SHORTFALL: only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY; only 2 axis/axes covered (BOUNDARY, COUNTEREXAMPLE) — minimum 3; missing: EVIDENCE, MECHANISM, TRANSFERABILITY; only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY; only 2 axis/axes covered (COUNTEREXAMPLE, MECHANISM) — minimum 3; missing: EVIDENCE, BOUNDARY, TRANSFERABILITY
- **E2 landscape:** A_MEASURED×1, B_ACADEMIC×3, C_PRACTITIONER×10, D_VENDOR×3, UNKNOWN×28 · 0 question(s) refused as vendor-only · 0 learning(s) killed by the coverage gate
- **E3 reality:** DERIVED 15, HYPOTHESIS 1 · 13 label(s) demoted by the evidence gates
- **E4 contradictions:** 0 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `THIN` / MEDIUM [EVIDENCE] — 4 source(s), families C_PRACTITIONER, UNKNOWN — _What do the build configurations and commit histories of Wii decompilation projects show a_
- `UNCLASSIFIED` / LOW [MECHANISM] — 3 source(s), families D_VENDOR, UNKNOWN — _Why would a studio shipping one Wii game end up compiling its own code, the platform SDK a_
- `THIN` / MEDIUM [BOUNDARY] — 4 source(s), families C_PRACTITIONER, UNKNOWN — _What happens when a decompilation team picks the wrong compiler version or flags for a lib_
- `THIN` / MEDIUM [MECHANISM] — 3 source(s), families C_PRACTITIONER, UNKNOWN — _Why would two builds of the same C or C++ source from different CodeWarrior releases produ_
- `UNCLASSIFIED` / LOW [BOUNDARY] — 3 source(s), families UNKNOWN — _What happens to a decompilation team's progress when a compiler release they believed was _
- `UNCLASSIFIED` / LOW [COUNTEREXAMPLE] — 5 source(s), families UNKNOWN — _Which functions or objects in published console decompilation projects matched only after _
- `THIN` / MEDIUM [BOUNDARY] — 3 source(s), families C_PRACTITIONER, UNKNOWN — _When a function matches byte for byte only under a non-baseline compiler version, what hap_
- `COVERED` / HIGH [BOUNDARY] — 4 source(s), families A_MEASURED, B_ACADEMIC, UNKNOWN — _What happens to a decompilation project when a function matches byte for byte under the wr_
- `THIN` / MEDIUM [MECHANISM] — 5 source(s), families B_ACADEMIC, UNKNOWN — _Why do different builds of the same compiler family produce different instruction ordering_
- `THIN` / MEDIUM [COUNTEREXAMPLE] — 4 source(s), families C_PRACTITIONER, D_VENDOR, UNKNOWN — _Are there Wii or GameCube projects where every object matched under one single compiler ve_
- `UNCLASSIFIED` / LOW [MECHANISM] — 3 source(s), families UNKNOWN — _Why does a function that looks like it was built with a different compiler release sometim_
- `THIN` / MEDIUM [COUNTEREXAMPLE] — 4 source(s), families C_PRACTITIONER, UNKNOWN — _Which reverse-engineering or matching-decompilation projects first assigned a different co_

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `fetch_page 'https://deepwiki.com/doldecomp/mkw/2-build-configuration-and...': page-fetch: https://deepwiki.com/doldecomp/mkw/2-build-configuration-and-toolchain: HTTP Error 429: Too Many Requests`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `axis-widening re-ask failed: llm-parse: no valid JSON in 1850 chars; head: '{"questions":[{"query":"What measurements have decompilation teams published on how many functions stayed unmatched or needed workarounds because the '; anthropic-sdk: ANTHROPIC_API_KEY not set`
- `decomposition narrow: only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY`
- `fetch_page 'https://stackoverflow.com/questions/3000221/how-do-game-comp...': page-fetch: https://stackoverflow.com/questions/3000221/how-do-game-companies-handle-programming-for-multiple-platforms: HTTP Error 403: Forbidden`
- `fetch_page 'https://stackoverflow.com/questions/29466/writing-a-game-for...': page-fetch: https://stackoverflow.com/questions/29466/writing-a-game-for-the-nintendo-wii: HTTP Error 403: Forbidden`
- `learning 0 unrated by relevance filter — kept, flagged UNRATED`
- `learning 1 unrated by relevance filter — kept, flagged UNRATED`
- `fetch_page 'https://dl.acm.org/doi/10.1145/3395363.3397370...': page-fetch: https://dl.acm.org/doi/10.1145/3395363.3397370: HTTP Error 403: Forbidden`
- `source https://docs.hex-rays.com/ida-9.2/user-guide/decompiler/fail carries instruction-like text ['tool-or-exfil-request']; treated as data`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 4416`
- `fetch_page 'https://community.nxp.com/t5/CodeWarrior-Development-Tools/H...': page-fetch: https://community.nxp.com/t5/CodeWarrior-Development-Tools/How-to-build-mixed-C-and-C-project-in-CodeWarror/m-p/1033066: HTTP Error 403: Forbidden`
- `fetch_page 'https://community.nxp.com/t5/CodeWarrior-Development-Tools/L...': page-fetch: https://community.nxp.com/t5/CodeWarrior-Development-Tools/Linking-and-compiling-with-CodeWarrior/ta-p/1118848: HTTP Error 403: Forbidden`
- `epistemic demoted OBSERVED -> HYPOTHESIS: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED; ledger: no quote verified in any snapshot`
- `decomposition narrow: only 2 axis/axes covered (BOUNDARY, COUNTEREXAMPLE) — minimum 3; missing: EVIDENCE, MECHANISM, TRANSFERABILITY`
- `fetch_page 'https://stackoverflow.com/questions/10311189/how-does-decomp...': page-fetch: https://stackoverflow.com/questions/10311189/how-does-decompiling-work: HTTP Error 403: Forbidden`
- `fetch_page 'https://dl.acm.org/doi/full/10.1145/3708821.3733877...': page-fetch: https://dl.acm.org/doi/full/10.1145/3708821.3733877: HTTP Error 403: Forbidden`
- `learning 0 unrated by relevance filter — kept, flagged UNRATED`
- `learning 1 unrated by relevance filter — kept, flagged UNRATED`

</details>


## Evidence ledger

- **Claims:** 32 · with a verified quote: 30 (rate 0.938)
- **Quotes:** 47 offered, 4 rejected (not verbatim / unknown source / length)
- **Sources:** 39 snapshots in 39 independent lineage(s); 2 URL(s) were byte-identical copies
- **Labels lowered by the ledger:** 3
- **Sources with instruction-like text (treated as data):** 3

**C1** [DERIVED] Super Mario Galaxy 1's Petari wiki documents a per-library split: game code matched with GC 3.0a3, while RVL_SDK, NW4R, JSystem and MSL matched with GC 3.0, and MetroTRK with GC 2.5. A single-compiler assumption would make some library code unmatchable, so effort estimates and tooling setup must be per-component.
  - S1 <https://github.com/SMGCommunity/Petari/wiki/CodeWarrior> chars 1170-1346: "For Super Mario Galaxy 1 , a lot of testing has gone into finding the correct compiler for every library and also having the correct compiler arguments to match code perfectly."

**C2** [DERIVED] The SMG community pinned versions using three signals: the game's build date, codegen differences that rule compilers in or out through trial and error, and SDK libraries like NW4R whose initialization functions print the compiler build. That means the answer is recoverable from the shipped binary, but it takes experimentation time per library.
  - S1 <https://github.com/SMGCommunity/Petari/wiki/CodeWarrior> chars 1044-1169: "For the SDK libraries such as NW4R and RLV_SDK, the initialization functions for some libraries print out the compiler build."
  - S1 <https://github.com/SMGCommunity/Petari/wiki/CodeWarrior> chars 961-1043: "Trial and error shows what compilers could work and what compilers could not work."

**C3** [DERIVED] A general wiki gives CodeWarrior versions 1.0 through 1.7 across titles and suggests a single version per project in its prompt template, while the SMG documentation shows GC 3.0-series and 2.5 builds mixed within one game. Generic guidance therefore understates version variation, and an automated or outsourced workflow told only one version will fail on libraries built differently.
  - S3 <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/> chars 3965-4054: "The versions used across titles range from 1.0 through 1.7, per decomp.wtf documentation."

**C4** [DERIVED] The porting guidance says unsupported middleware, third-party plugins, outdated dependencies and undocumented build steps are what cause schedule and budget overruns, and that they should be found in an up-front audit. A studio whose game, platform SDK and middleware are built with different compiler versions is showing exactly this unaudited-dependency risk, so the audit is where the mismatch should surface before a release date is promised.
  - S7 <https://www.cubix.co/blog/game-porting/> chars 5179-5270: "The audit helps uncover compatibility issues before they cause schedule or budget overruns."
  - S7 <https://www.cubix.co/blog/game-porting/> chars 4924-4991: "Third-party plugins and middleware that may not support the target."

**C5** [DERIVED] Engine and tool versions change over time (Unity's documentation lists version-specific build flags from 2.6 through 5.x, and compiler-specific response files tied to each compiler it invokes). Each upgrade can change which compiler builds which part of the code. The porting guidance says updated dependencies and patches cause regressions, and recommends automated builds and regression tests to catch them before release.
  - S7 <https://www.cubix.co/blog/game-porting/> chars 12075-12276: "After launch, track platform-specific bugs, test new content and patches, and update dependencies when necessary. Automated builds and regression tests can catch update-related failures before release."
  - S5 <https://docs.unity3d.com/540/Documentation/Manual/PlatformDependentCompilation.html> chars 8135-8289: "If you choose the .rsp files instead, you need to provide one file for every compiler Unity uses, and you won’t know when one or another compiler is used."

**C6** [DERIVED] In a 10,115-function Super Mario Sunshine decompilation, roughly 600 failures were frame-only (every instruction right, only the stack frame wrong) and about 1,150 had both frame and code wrong, so four in five remaining failures involve a wrong frame. Frame-only functions are the hardest, not the cheapest, because the diff tool shows no progress and the automated permuter has nothing to optimise toward; the structural bucket (~350 functions) is where matches actually come from. A scan that cancels the frame delta separates functions one fix away from those needing real work, saving days of manual discovery.
  - S9 <https://github.com/KakarottoCake/decomp-triage> chars 2895-2951: "Frame-only functions are the hardest , not the cheapest."
  - S9 <https://github.com/KakarottoCake/decomp-triage> chars 5331-5409: "A function whose leftovers are entirely regperm and slot has no code work left"

**C7** [DERIVED] A compiler/library-version mismatch can be hidden because the original build dead-stripped symbols that are absent from extracted objects yet listed in the link map. On the Sunshine project 204 symbols across 185 sections were misclassified (5.1% of 'target lacks this' reports), and acting on that output cost 4,416 bytes of matched data in one commit that had to be reverted. Similarly, 40 bytes of unexplained constants at the start of .data turned out to be the footprint of a precompiled header the original build used, which looked like a wrong struct but was a flag/setup mismatch.
  - S9 <https://github.com/KakarottoCake/decomp-triage> chars 8677-8847: "On the project it was built against, 204 symbols across 185 sections were on the wrong side of that line — 5.1% of every "the target does not have this" it used to print."
  - S9 <https://github.com/KakarottoCake/decomp-triage> chars 7612-7798: "Retail's .data simply began with 40 bytes of constants the compiler generated and then optimised the uses of — the footprint of a precompiled header the original build used and we don't."
  - _ledger: OBSERVED number(s) absent from verified spans: 4416_

**C8** [DERIVED] Catalogues of compiler behaviours are only 'proven' when a byte-match was reproduced, and a lever proven on one compiler is only a hypothesis on another. Metrowerks GC/1.x never reclaims dead stack slots while the ARM variant does, so opposite mechanisms produce similar symptoms, and a lever for by-value class parameters from the DS project failed when tested against every frame-only function here. Teams that import folklore across versions will chase functions that can never match.
  - S9 <https://github.com/KakarottoCake/decomp-triage> chars 15909-15974: "A lever proven on one compiler is only a hypothesis on the other."
  - S9 <https://github.com/KakarottoCake/decomp-triage> chars 16109-16197: "mwccarm reclaims dead slots and needs volatile to pin one; GC/1.x never reclaims at all."

**C9** [HYPOTHESIS] In the Super Mario Galaxy 1 decompilation effort, different components required different CodeWarrior releases to reproduce the original instruction sequences: the game itself matched GC 3.0a3, the SDK, NW4R, JSystem and MSL matched GC 3.0, and MetroTRK matched GC 2.5. A one-compiler-fits-all approach would therefore produce mismatches, and version identification is a per-component effort that consumed substantial testing.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C10** [DERIVED] Practitioners narrow compiler candidates by the build date of the shipped game, picking the most recent compiler build near that date, and by reading the compiler build that some SDK libraries print in their initialization functions. Trial and error on code generation then eliminates the remaining candidates, so the expensive step is applied to a short list rather than every release.
  - S1 <https://github.com/SMGCommunity/Petari/wiki/CodeWarrior> chars 1044-1169: "For the SDK libraries such as NW4R and RLV_SDK, the initialization functions for some libraries print out the compiler build."
  - S1 <https://github.com/SMGCommunity/Petari/wiki/CodeWarrior> chars 961-1043: "Trial and error shows what compilers could work and what compilers could not work."

**C11** [DERIVED] The source treats register, ordering and stack-frame differences as symptoms that suggest experiments, not unique diagnoses, and says these experiments depend on the compiler and its version. Without a record of compiler, flags and resulting diff for every attempt, a wrong compiler release looks identical to a wrong rewrite, and engineers can burn weeks rewriting correct code.
  - S14 <https://www.retroreversing.com/decompilers> chars 18907-19081: "These are compiler- and version-dependent experiments. Record the compiler, flags and resulting diff rather than treating a register-allocation heuristic as a universal rule."
  - S14 <https://www.retroreversing.com/decompilers> chars 17391-17448: "These symptoms suggest experiments, not unique diagnoses:"

**C12** [DERIVED] The source tells teams to check the project's known configuration and neighbouring matched functions before changing compiler settings, and to re-verify earlier matches after shared changes. If the same register or stack-frame pattern recurs across many unmatched functions while others match, that points to a systematic cause such as the compiler build. This is a reasoned extension of the guide, not something it states.
  - S14 <https://www.retroreversing.com/decompilers> chars 18104-18214: "Before changing compiler settings, check the project’s known configuration and neighbouring matched functions."

**C13** [DERIVED] A similarity score does not explain why a function differs, and a function-level match does not show the whole rebuilt image is correct. The source advises deliberately feeding the checker wrong candidates to confirm it rejects them, so a progress figure built on a mismatched toolchain or a lenient checker doesn't mislead management.
  - S14 <https://www.retroreversing.com/decompilers> chars 17296-17390: "Use the actual disassembly alongside the score; a percentage alone does not explain the cause."
  - S14 <https://www.retroreversing.com/decompilers> chars 19812-19877: "Do not infer a complete rebuild from a function similarity score."

**C14** [DERIVED] The Super Mario 64 DS reconstruction reports 99.9% of functions matched yet only 30.5% converted into readable source, in the same README, and its matching figure includes a disclosed set of assembly primitives. A single progress number can therefore hide large amounts of unreadable or unrecovered work.
  - S18 <https://kingy.ai/blog/ai-video-game-decompilation-legality/> chars 204-358: "An AI-assisted Super Mario 64 DS reconstruction reports 99.9% of its functions matched. Its counter for source converted into readable form sits at 30.5%."

**C15** [DERIVED] The article says matching workflows depend on choosing the right executable revision, compiler, build options and comparison rules, and that an agent inherits those decisions rather than eliminating their cost. This implies compiler settings are a human-prepared precondition for matching, though the contents name no specific function that matched only after a flag or pragma change.
  - S18 <https://kingy.ai/blog/ai-video-game-decompilation-legality/> chars 4046-4184: "Preparing that loop requires expertise: the right executable revision, compiler, build options, function boundaries, and comparison rules."

**C16** [HYPOTHESIS] None of the supplied contents list a specific function or object that matched only after an optimisation flag or pragma change, nor maintainer explanations of why. The material is general (decompiler overviews, a debugger blog, an AI-decompilation survey), so the question needs primary sources such as project issue trackers and Discord or commit logs.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C17** [DERIVED] The Total Annihilation matching decompilation shows what a true non-baseline compiler match looks like: the compiler was pinned to Visual C++ 5.0 SP3 (not the RTM release) because the runtime library matched SP3, with 568 LIBCMT code sections found byte-for-byte and linker 5.10. All 3,267 functions (850,853 bytes) match and the full exe rebuilds to the shipped MD5, which a coincidental single-function match could never achieve.
  - S20 <https://github.com/HectorBailey/byte-tactics> chars 8869-8920: "Linker 5.10; runtime library matches SP3, not RTM ("

**C18** [DERIVED] In the TA project, the linker kept each subsystem roughly together, so each 64 KB of the executable is mostly one subsystem. Neighbouring functions therefore cluster by area, and leftover FPO debug records and source-path strings in the binary give exact function starts, sizes and argument counts. A candidate match that sits in the wrong region or contradicts those records is likely accidental.
  - S20 <https://github.com/HectorBailey/byte-tactics> chars 2512-2626: "The linker kept each part of the engine roughly together, so each 64 KB of the executable is mostly one subsystem."

**C19** [DERIVED] The Microsoft linker's identical COMDAT folding merges functions that compile to identical code, so two unrelated functions (a getter in one class and a virtual getter in another) end up at one address under two names. Short accessor-like functions and template instantiations collide often, so a byte match on them is weak evidence, and symbol names at that address are ambiguous.
  - S21 <https://devblogs.microsoft.com/oldnewthing/20050322-00/?p=36113/> chars 1424-1535: "What happened is that the Microsoft linker combined functions that are identical at the code generation level ."

**C20** [DERIVED] The Decompile-Bench team found that real projects often ignore standard build settings, so they had to fork the compiler to force consistent optimization levels and debug information. The consequence is that the toolchain has to be controlled and recorded deliberately, because a match alone does not reveal how the code was built. The contents do not say how often tiny functions match under several compiler versions, so that part of the question stays unanswered.
  - S22 <https://www.emergentmind.com/papers/2505.12668> chars 4400-4595: "They forked the Clang compiler to enforce consistent optimization levels (-O0 to -O3) and include DWARF debug information (-g), addressing issues where projects ignore standard environment flags."

**C21** [DERIVED] Decompile-Bench condensed 100 million raw binary-source function pairs into two million usable ones, and training on the unfiltered data made results worse. A large pile of matches therefore overstates real, trustworthy progress, and a project's quality gate matters more than its headline count.
  - S22 <https://www.emergentmind.com/papers/2505.12668> chars 5820-5936: "This filtering process is shown to be critical, reducing the raw 100 million pairs to two million high-quality ones."

**C22** [DERIVED] The fnvdecomp project reports 70,611 functions totaling 11,537,067 bytes, an average of roughly 163 bytes per function, and defines success as machine code identical to the shipped executable. With functions that small, some matches are plausibly ambiguous across compiler versions, but the page gives no breakdown of function sizes or of toolchain verification. Treat the 100% figure as proof of matching, not of a correct toolchain.
  - S25 <https://fnvdecomp.com/> chars 258-300: "★ 100% · byte for byte · source released ★"

**C23** [DERIVED] Stack-frame growth and register spills are driven largely by optimization level and by the CPU's register file and calling convention, not only by the compiler's identity. At -O0 every variable gets a stack slot and frames balloon past 60 bytes for a simple 8-parameter function, while at -O2 the same source uses registers with zero spills. x86-64 has 16 general-purpose registers against ARM64's 31, so the same source spills less on ARM64. Attributing a frame layout to a specific compiler build without controlling for flags and target will therefore mislead.
  - S29 <https://www.codermusings.com/register-allocation-compiler-guide/> chars 13462-13574: "Every operation involves a round-trip to memory. The stack frame for this simple function balloons to 60+ bytes."
  - S29 <https://www.codermusings.com/register-allocation-compiler-guide/> chars 2993-3091: "ARM64’s nearly double-sized register file gives the compiler significantly more room to work with."

**C24** [DERIVED] Register choice is made by the backend allocator after the source has been reduced to an IR with unlimited virtual registers, so it reflects allocator strategy and not source structure. LLVM uses a fast allocator for debug builds and a greedy allocator with priority queues, spill weights, live-range splitting and eviction for optimized builds. Different allocators or versions will therefore assign different registers and place spills differently for identical source.
  - S29 <https://www.codermusings.com/register-allocation-compiler-guide/> chars 9409-9513: "The -regalloc=fast allocator is used for -O0 debug builds — it is extremely fast but produces poor code."
  - S28 <https://browncs1260.github.io/notes/22> chars 4163-4227: "A basic block program is agnostic about where values get stored."

**C25** [DERIVED] Manually reusing variables does not help the allocator and can hurt, because optimizers work best on SSA-style code with one definition per variable. Since the source-level form is normalized away in the IR, low-level layout differences between builds are weak evidence about how the code was written and stronger evidence about the toolchain and flags.
  - S29 <https://www.codermusings.com/register-allocation-compiler-guide/> chars 15818-15913: "The compiler works best with SSA-style code where each variable has a single, clear definition."
  - S28 <https://browncs1260.github.io/notes/22> chars 2036-2079: "each temporary is assigned to exactly once."

**C26** [DERIVED] The only relevant guidance in these sources is that a match depends on the compiler's floating-point settings and operand order, and that one instruction pattern does not prove a particular source construct. Single-rounding versus separate multiply and add, or a rounding instruction, can look like a version difference when it is really a settings difference. The sources do not name any project that was matched under one compiler version, or any per-object override that was later reverted, so treat the settings-first explanation as a lead, not a finding.
  - S33 <https://www.retroreversing.com/gamecube> chars 8749-8835: "Preserve operand order and check the compiler’s floating-point settings when matching."

**C27** [DERIVED] The linker can fold functions with identical generated code into one copy, so the debugger shows a different function name at the same address. Whether two functions end up identical depends heavily on compiler version and optimization flags, and happens very often with templates. An apparent function mismatch can therefore be a linker artifact rather than evidence of a different toolchain.
  - S21 <https://devblogs.microsoft.com/oldnewthing/20050322-00/?p=36113/> chars 1424-1535: "What happened is that the Microsoft linker combined functions that are identical at the code generation level ."
  - S21 <https://devblogs.microsoft.com/oldnewthing/20050322-00/?p=36113/> chars 2193-2299: "Identical code generation for different functions occurs with very high frequency when you use templates.)"

**C28** [DERIVED] When whole-program optimization or link-time code generation is used, the toolchain refuses to link objects from different compiler versions, and requires both major and minor update numbers to match exactly. So in such builds a mixed-compiler binary cannot silently exist, and a version difference shows up as a hard build error that the fix (rebuild everything with one toolset) resolves.
  - S34 <https://learn.microsoft.com/en-us/cpp/error-messages/compiler-errors-1/fatal-error-c1047?view=msvc-170> chars 867-1132: "For example, you can't link a /LTCG library built by using Visual Studio 2019 version 16.7 to an app built by using Visual Studio 2019 version 16.8. Both the major and minor update numbers of the toolset used to compile the objects and libraries must match exactly."

**C29** [DERIVED] Most compiler settings are configuration- and platform-dependent, so the same compiler produces very different code depending on which configuration was active. Optimization defaults to Maximize Speed in Release and is disabled in Debug, meaning the same compiler can yield visibly different functions across builds.
  - S35 <https://learn.microsoft.com/en-us/cpp/build/working-with-project-properties?view=msvc-170> chars 2052-2206: "For example, the Optimization property, by default, is set to Maximize Speed (/O2) in a Release configuration, but is disabled in the Debug configuration."

**C30** [DERIVED] The contents say a flag mismatch makes every function unmatchable and looks like a source problem, and that old compilers such as IDO and CodeWarrior change output for casts, inline, const and even whitespace. So a different compiler version can appear necessary when corrected flags or rewritten source would have produced the same bytes, and the cheap checks should come before a toolchain change.
  - S36 <https://initialrise.github.io/REWiki/04-recomp/matching-decomp/> chars 7601-7710: "Do not guess flags blindly. A flag mismatch makes every function unmatchable and looks like a source problem."

**C31** [DERIVED] The recommended way to verify flags is to compile one already-matched function with candidate flags and see which reproduces its bytes, and to cross-check against a sibling project on the same platform. This catches a wrong version or flag assignment early, before many functions are attempted under it.
  - S36 <https://initialrise.github.io/REWiki/04-recomp/matching-decomp/> chars 7497-7600: "Experiment: compile one known-matched function with candidate flags and see which reproduces its bytes."

**C32** [DERIVED] Decompedia, as summarized, says one game can mix compilers and that the right version is often recovered from old install discs. Per-file version assignment is therefore normal practice, but the contents give no case of a project reversing one or a maintainer admitting a mistake.
  - S37 <https://grokipedia.com/page/Matching_Decompilation> chars 12847-12989: "Decompedia notes that one game can mix compilers and that, before the late 2000s, the right version is often recovered from old install discs."
