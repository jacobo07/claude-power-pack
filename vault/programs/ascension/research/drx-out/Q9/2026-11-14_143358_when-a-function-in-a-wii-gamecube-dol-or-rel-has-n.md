# Obtaining target bytes, attributing units, and proving byte-identical matches for functions with no reference object (Wii/GameCube DOL/REL)

## 0. Read this first: what the research supports

The research learnings cover **general matching-decompilation methodology**: acceptance tests, data checks, boundary hypotheses and re-verification. They contain **nothing specific** to dtk, mwcc/mwld, REL relocations, symbols.txt/splits.txt, `.ctors`/`.dtors` or extab. They also contain no primary source for any Wii/GameCube claim. Several learnings come from other domains (IDO/SM64, TH08, a chardet licensing dispute) and apply here only by analogy.

- **Section 1** carries the research findings with their original tags and ledger IDs.
- **Section 2** is a Wii/GameCube-specific model from my background knowledge. It is **[UNVERIFIED][NO-SOURCE-IN-RESEARCH]**: no repo file, issue, PR or compiler manual was retrieved, so none of it meets your "primary source for every claim" requirement. Treat it as a checklist of things to verify, not as findings.
- **Section 3** gives falsifiable predictions, all unverified.

## 1. Findings supported by the research

| # | Claim | Tags | Ledger | Applies to the prompt |
|---|---|---|---|---|
| 1 | The acceptance test is a byte-identical rebuild with the original toolchain, not behavioural equivalence or a similarity score. A match shows the logic and range belong together. | [DERIVED][LOW] | C1 (S3, S4) | Directly. The cited source is IDO/SM64, not mwcc. |
| 2 | A function-level match does not prove correct literal pools, section placement or data ownership. Checkers should be tested with deliberately wrong candidates, then the full image compared. | [DERIVED][LOW] | C2 (S1) | Directly. Single source. |
| 3 | The same point restated: a 100% function score can hide latent mismatches. Mutation-test the checker, compare the linked image. | [DERIVED][MEDIUM] | C23 (S1) | Directly. Rated higher than C2, but the evidence is the same single source. The link to "preventing late surprises" is inference. |
| 4 | Shared constants, strings and entry points only suggest file boundaries. A split is accepted only if, after reassigning data and rebuilding, existing matches and the final image stay intact. For overlay games, loader and relocation records decide which bytes belong to which function. | [DERIVED][LOW] | C3 (S1) | This is the closest research support for "attribute the function to a unit" and "REL relocation handling". The cited cases are Doubutsu no Mori and Ghidra overlays, not REL specifically. |
| 5 | A rebuild can match on 46 code bytes and have an identical relocation record, yet differ in the table it points to (1,2,3,4,3 vs 1,2,3,4,4). Byte comparison reports no change. TH08 had the same failure (0.0 vs 128.0), and a 1,548-reference audit corrected twelve more. | [DERIVED][HIGH] | C16 (S27) | Directly. A matching relocation record does not prove the pointed-to data matches. This is the strongest-rated finding here, but it comes from a teaching lesson and TH08, not from a GC/Wii project. |
| 6 | Matches are valid only under the compiler, flags and source context checked. Re-verify after shared type, prototype or build-setting changes. Record compiler, flags and diff with each result. The cost of discovering the wrong compiler late is **not** stated in the sources, so that extension is inference. | [DERIVED][MEDIUM] | C22 (S1) | Relevant to inline, weak and template functions, whose emission depends on flags and header context. |
| 7 | A near-zero similarity score (JPlag under 1.3% in the chardet case) can coexist with a derivative relationship. Ask for process evidence. | [DERIVED][LOW] | C26 (S36) | Only by analogy. It cautions against using fuzzy matching (instruction-similarity scores) to attribute a function to a unit. |
| 8 | LLM statements about provenance or licence are fluent but unsubstantiated. Check them against the repository, LICENSE or SPDX before recording. | [DERIVED][LOW] | C27 (S36) | By analogy. It applies to my own Section 2: check it against dtk's repo before relying on it. |

**Consequences for the prompt (derived from the table, tags inherited, lowest tag is LOW):**
- A per-function diff against a reference object is unavailable for your target class of functions. Findings 2, 3 and 5 therefore imply the proof must move to the **linked image**: section bytes, relocations and referenced data, all compared against the original DOL/REL. [DERIVED][LOW]
- Attribution of an unreferenced function is a **hypothesis tested by rebuild** (finding 4), not a lookup. [DERIVED][LOW]
- Every fix to a unit boundary or compiler flag set triggers re-verification (finding 6). [DERIVED][MEDIUM]

## 2. Domain model from background knowledge [UNVERIFIED][NO-SOURCE-IN-RESEARCH]

None of the following was confirmed in this research. Primary sources to check are listed per item.

### 2.1 Obtaining target bytes
- **DOL**: decomp-toolkit (dtk) reads the DOL's text/data sections and the address map. Function bytes come directly from the original image at the virtual address, so no reference object is needed. To check: dtk repo, `dtk dol info` / `dtk dol split`.
- **REL**: the REL header, section table and relocation (imp) records give each module's section contents plus every cross-module and intra-module relocation target. Relocation records tell you which words are pointers rather than constants, which matters for diffing. To check: dtk `rel` subcommands and the REL format documentation.
- **Config files**: dtk uses `config.yml`, `symbols.txt` and `splits.txt`, and `objdiff` compares compiled output against the target. To check: a project's `config/<version>/`, and the dtk README.
- **Shipped maps**: some games shipped CodeWarrior linker maps or debug symbols, which give names, sizes and unit order. To check: per-project docs and `dtk map` (if it exists).

### 2.2 Attribution without a reference object
- Splits are address ranges per source file (`splits.txt`) and symbols carry type, size and scope attributes (`symbols.txt`). My recollection is that flags such as `scope:weak`, `force_active` and `stripped` exist. I am **not certain** of the exact names or semantics in current dtk. To check: dtk docs.
- Evidence for unit ownership includes link order (mwld lays objects in command-line order), shared `@`-numbered literal symbols, string pool adjacency, `.sdata2` constants and `__sinit_<file>_cpp` names. Per finding 4, each is only a hypothesis until a rebuild passes.

### 2.3 Cases in the prompt
| Case | Expected mechanism | Status |
|---|---|---|
| Dead-stripped | Function absent from the image, so there is no target bytes and nothing to match. Only a symbol hint (e.g. `stripped`) or a map shows it existed. | [UNVERIFIED] |
| Inline/weak copies | Emitted as weak in each TU that needs them, with the linker keeping one copy. The surviving copy's address attributes it to whichever unit's weak copy won. Other units' copies can appear as "missing". | [UNVERIFIED] |
| Template instantiations | Same as weak. Emission and order depend on first use and on flags such as `-inline` mode. | [UNVERIFIED] |
| Linker-merged | Identical-code merging is something I am **not sure** mwld does by default. Check before assuming it. | [UNVERIFIED], likely gap |
| Missing from split | Assign the range to a new unit, rebuild, diff. Finding 4 governs. | [DERIVED][LOW] |

### 2.4 ctor/dtor and extab
- Static initialisers: mwcc emits a `__sinit_<file>_cpp` function per TU, and `.ctors` entries point to it. `.dtors` and `__destroy_global_chain` handle destruction. [UNVERIFIED]
- Exceptions: `.extab` holds per-function unwind data and `.extabindex` holds (function address, size, extab address) entries. The linker is believed to drop entries for stripped functions. dtk generates extab symbols and attributes them to units. [UNVERIFIED]
- Proof value: `.ctors`, `.dtors`, `.extab` and `.extabindex` contents are **extra equality constraints** on a unit. A wrong function-to-unit assignment will usually misalign these tables. This is my inference, consistent with finding 4. [HYPOTHESIS]

## 3. Falsifiable predictions (all [UNVERIFIED]; none tested)

| ID | Prediction | How it fails | Source to check |
|---|---|---|---|
| P1 | A TU with a non-trivial static object compiled with mwcc emits a `__sinit_<file>_cpp` function and one `.ctors` entry. A TU without one emits neither. | No `__sinit_*` symbol in the object (`dtk elf` / `objdump`). | mwcc docs, any dtk project |
| P2 | A function with try/catch or objects with destructors gets an `.extab` entry and an `.extabindex` row. The same function compiled with exceptions disabled (`-Cpp_exceptions off`) gets none. | Rows present or absent contrary to this. | mwcc manual, flag reference |
| P3 | An unused header inline function is not emitted with `-inline auto` but is with `-inline noauto` or force-active. | The weak symbol's presence is unaffected by the flag. | mwcc manual, `-inline` section |
| P4 | If the same weak function is defined in two TUs, the final DOL contains one copy, and its address matches the earlier object in link order. | Two copies, or the later object's copy. | A project's `.map`, `splits.txt` ordering |
| P5 | Moving a range between units in `splits.txt` changes `.ctors`/`.extabindex` order, and the rebuild only matches the original when the order is right. | Order unchanged by the move. | dtk, objdiff |
| P6 | A rebuilt function can match on code bytes and relocation records, yet differ in `.rodata`/`.sdata2` pool data. This is the GC analogue of finding 5. | Pools always differ whenever code differs. | Section-level diff of the linked DOL |

## 4. Gaps and recommendations

- **Gap:** the research did not retrieve any dtk, mwcc/mwld, REL or extab source. Section 2 is background knowledge and is not independently verified. I regard names such as `stripped`, `force_active` and the exact `__sinit_` convention as likely but unconfirmed. Linker merging in particular is uncertain.
- **Gap:** no learning states how projects handle a function that is truly absent from the image. My guess is that they cannot match it and record it as known-missing. [HYPOTHESIS]
- **Not covered:** the lack of a per-function reference object affects the diff tool, not the final proof. Per findings 2, 3 and 5 the final proof is a bit-exact relink of the DOL/REL.

**Suggested next steps**
1. Clone decomp-toolkit and one mature GC/Wii project, then check P1–P6 against `config/` files and `.map` output, citing `file:line` for each.
2. Add a mutation test of your checker (swap a `.sdata2` constant, a `.ctors` order, an extab row) and confirm it fails the full-image comparison, as in finding 2.
3. Record compiler build, flags and `-inline` mode per unit (finding 6) before accepting an inline or weak attribution.

## Contradicciones detectadas

Ninguna. Las fuentes procesadas no se contradicen entre sí en los puntos extraídos. Esto no significa consenso del campo: significa que las fuentes que este run alcanzó coinciden.

## Sources

- <https://www.retroreversing.com/decompilers>
- <https://en.wikipedia.org/wiki/Decompiler>
- <https://wal.sh/research/code-decomp/>
- <https://www.denis-iakimenko.com/blog/reverse-engineering-decompilation-ports>
- <https://kenji.blog/en/p/decompilation-reverse-engineering-control-flow-recovery-type-inference/>
- <https://aiengineeringfromscratch.com/learn/tools-and-protocols/rebuild-and-prove-equal>
- <https://github.com/morluto/rea/issues/8556>
- <https://www.javacodegeeks.com/2026/09/the-bytecode-verifiers-hidden-contract.html>
- <https://aiengineeringfromscratch.com/learn/tools-and-protocols/binary-diffing-and-symbolic-execution>
- <https://github.com/zeldaret/tww/blob/main/docs/decompiling.md>
- <https://www.reddit.com/r/learnprogramming/comments/fhaykb/does_decompiling_files_restore_the_original_code/>
- <https://heios.github.io/research/2026-07-08/ai-commit-attribution/>
- <https://aitechmodel.com/source-attribution-for-ai-generated-code-what-changed-and-why-it-matters-now/>
- <https://www.taylorwessing.com/en/insights-and-events/insights/2026/06/ai-and-assisted-programming-in-open-source>
- <https://aclanthology.org/2025.ijcnlp-tutorials.1.pdf>

## Run metadata

- **Prompt:** When a function in a Wii/GameCube DOL or REL has no reference object to diff against (dead-stripped, inline or weak copies, template instantiations, functions merged by the linker, objects missing from the split), how do decompilation projects obtain the target bytes, attribute the function to a unit, and still prove a byte-identical match (dtk extraction, REL relocation handling, symbol maps, ctor/dtor and extab tables)? For every claim give the primary source (repo file, issue, PR, compiler manual) and state it as a falsifiable prediction: 'with X, mwcc emits Y; with X', it emits Y''. Mark anything unverified.
- **Depth / breadth:** 2 / 4
- **Queries used:** 10 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 557.8 s
- **Errors during run:** 34
- **Started at:** 2026-11-14T13:33:58Z
- **Module version:** deep_research 0.4.1
- **Quality gates:** 0 query/queries rejected as keyword soup · 1 learning(s) dropped for containing code · 18 dropped as not operator-actionable (relevance: rated)
- **E1 decomposition:** 4/5 axes searched (BOUNDARY, COUNTEREXAMPLE, EVIDENCE, MECHANISM)  — SHORTFALL: only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY; only 2 axis/axes covered (BOUNDARY, EVIDENCE) — minimum 3; missing: MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY; only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY
- **E2 landscape:** A_MEASURED×2, B_ACADEMIC×4, C_PRACTITIONER×5, D_VENDOR×1, UNKNOWN×27 · 0 question(s) refused as vendor-only · 0 learning(s) killed by the coverage gate
- **E3 reality:** DERIVED 8 · 11 label(s) demoted by the evidence gates
- **E4 contradictions:** 0 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `UNCLASSIFIED` / LOW [EVIDENCE] — 5 source(s), families UNKNOWN — _How do decompilation projects recover the exact original bytes and boundaries of a functio_
- `THIN` / HIGH [MECHANISM] — 4 source(s), families B_ACADEMIC, D_VENDOR, UNKNOWN — _Why does a recovered function that matches the original bytes sometimes still turn out to _
- `THIN` / MEDIUM [BOUNDARY] — 5 source(s), families C_PRACTITIONER, UNKNOWN — _What happens to the recovery of function boundaries when the original linker or compiler i_
- `UNCLASSIFIED` / LOW [MECHANISM] — 1 source(s), families UNKNOWN — _Why does the CodeWarrior compiler and linker produce code that cannot be traced back to a _
- `COVERED` / HIGH [EVIDENCE] — 5 source(s), families A_MEASURED, B_ACADEMIC, C_PRACTITIONER, UNKNOWN — _What measured counts exist from decompilation projects on how many functions in a CodeWarr_
- `UNCLASSIFIED` / LOW [BOUNDARY] — 3 source(s), families UNKNOWN — _When a CodeWarrior-linked binary contains duplicate inline or template function copies, wh_
- `COVERED` / HIGH [BOUNDARY] — 4 source(s), families A_MEASURED, C_PRACTITIONER, UNKNOWN — _When does the usual approach of proving a function matches byte for byte fail or become mi_
- `THIN` / MEDIUM [COUNTEREXAMPLE] — 4 source(s), families C_PRACTITIONER, UNKNOWN — _Which decompilation projects have decided that a function without a reference object canno_
- `THIN` / MEDIUM [BOUNDARY] — 4 source(s), families C_PRACTITIONER, UNKNOWN — _What happens when a decompilation project discovers, months after declaring a function mat_
- `UNCLASSIFIED` / LOW [MECHANISM] — 4 source(s), families UNKNOWN — _Why do automated or assisted attribution methods (symbol-matching, signature matching, sim_

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `epistemic demoted VERIFIED -> DERIVED: VERIFIED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `learning 0 unrated by relevance filter — kept, flagged UNRATED`
- `learning 1 unrated by relevance filter — kept, flagged UNRATED`
- `learning 2 unrated by relevance filter — kept, flagged UNRATED`
- `decomposition narrow: only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY`
- `fetch_page 'https://www.researchgate.net/publication/356457442_When_Func...': page-fetch: https://www.researchgate.net/publication/356457442_When_Function_Signature_Recovery_Meets_Compiler_Optimization: HTTP Error 403: Forbidden`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `fetch_page 'https://community.nxp.com/t5/CodeWarrior-Development-Tools/L...': page-fetch: https://community.nxp.com/t5/CodeWarrior-Development-Tools/Linking-and-compiling-with-CodeWarrior/ta-p/1118848: HTTP Error 403: Forbidden`
- `fetch_page 'https://stackoverflow.com/questions/6264249/how-does-the-com...': page-fetch: https://stackoverflow.com/questions/6264249/how-does-the-compilation-linking-process-work: HTTP Error 403: Forbidden`
- `fetch_page 'https://unix.stackexchange.com/questions/715899/do-c-compile...': page-fetch: https://unix.stackexchange.com/questions/715899/do-c-compilers-discard-unused-functions-when-statically-linking-to-a-file: HTTP Error 403: Forbidden`
- `fetch_page 'https://stackoverflow.com/questions/2395158/linker-error-lin...': page-fetch: https://stackoverflow.com/questions/2395158/linker-error-linker-input-file-unused-because-linking-not-done-undefined-ref: HTTP Error 403: Forbidden`
- `decomposition narrow: only 2 axis/axes covered (BOUNDARY, EVIDENCE) — minimum 3; missing: MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 100, 85000`
- `fetch_page 'https://stackoverflow.com/questions/44335046/how-does-the-li...': page-fetch: https://stackoverflow.com/questions/44335046/how-does-the-linker-handle-identical-template-instantiations-across-translation: HTTP Error 403: Forbidden`
- `fetch_page 'https://stackoverflow.com/questions/31824018/does-the-c-link...': page-fetch: https://stackoverflow.com/questions/31824018/does-the-c-linker-remove-code-duplication-from-templates-and-inline-functions: HTTP Error 403: Forbidden`
- `source https://blog.trailofbits.com/2019/09/02/rewriting-functions- carries instruction-like text ['tool-or-exfil-request']; treated as data`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `fetch_page 'https://www.sciencedirect.com/science/article/pii/S016740482...': page-fetch: https://www.sciencedirect.com/science/article/pii/S0167404826002531: HTTP Error 403: Forbidden`

</details>


## Evidence ledger

- **Claims:** 27 · with a verified quote: 27 (rate 1.0)
- **Quotes:** 44 offered, 1 rejected (not verbatim / unknown source / length)
- **Sources:** 37 snapshots in 37 independent lineage(s); 0 URL(s) were byte-identical copies
- **Labels lowered by the ledger:** 3
- **Sources with instruction-like text (treated as data):** 1

**C1** [DERIVED] Matching projects treat a function as done only when compiling candidate C with the original toolchain (e.g., SGI IDO 5.3 for Mario 64) reproduces the original bytes instruction for instruction. This is stronger than behavioural equivalence: it rules out off-by-one errors, changed float precision or silently removed undefined behaviour, so a matching function is evidence the range and logic really belong together.
  - S3 <https://wal.sh/research/code-decomp/> chars 3119-3166: "The byte-identical target is the gold standard."
  - S4 <https://www.denis-iakimenko.com/blog/reverse-engineering-decompilation-ports> chars 15591-15791: "It’s obsessive, and in return you get proof: a matching function has the same logic as the original, so nobody slipped in an off-by-one, changed float precision, or quietly removed undefined behavior."

**C2** [DERIVED] A function-level match does not establish that the rebuilt file has the right literal pools, section placement or data ownership, and a checker can be fooled if it ignores referenced data or reads a stale build. Projects test their checkers with deliberately wrong candidates (changed strings, float constants, swapped pointer-table entries) and then run the full binary comparison before claiming a recovered range is correct.
  - S1 <https://www.retroreversing.com/decompilers> chars 19812-19877: "Do not infer a complete rebuild from a function similarity score."
  - S1 <https://www.retroreversing.com/decompilers> chars 21795-21884: "A useful checker must reject incorrect reconstructions as well as recognise correct ones."

**C3** [DERIVED] Clues such as shared constants or strings, related class methods and module entry points only suggest original file boundaries. A split is accepted only if, after assigning data and rebuilding, existing matches and the final image stay intact. For overlay-based games, loader and relocation records decide which bytes belong to which function, because a plausible decompilation at the wrong address is still the wrong function.
  - S1 <https://www.retroreversing.com/decompilers> chars 20065-20208: "Treat a proposed split as a hypothesis: assign the associated data, rebuild, and check that existing matches and the final image remain intact."
  - S1 <https://www.retroreversing.com/decompilers> chars 12594-12763: "The game’s loader and relocation records establish which bytes and addresses belong together. A plausible decompilation at the wrong address is still the wrong function."

**C4** [OBSERVED] In a study of eight LLM decompilation systems, candidates that passed every shipped test still diverged from the original on a broader fuzzed input set 4.9% of the time overall and up to 13% for a single system. The shipped test suites missed 3% to 45% of the divergence, because their inputs sat in a narrow range and never reached edge paths like a final-band branch or integer overflow.
  - S7 <https://arxiv.org/html/2609.05370v1> chars 1406-1638: "Across eight systems in nine configurations on established LLM decompilation corpora, candidates that pass every shipped test still diverge from the original on our input corpus: 4.9% overall, and as many as 13% for a single system."
  - S7 <https://arxiv.org/html/2609.05370v1> chars 16145-16331: "The same pattern recurs elsewhere: replaying every candidate shows that the shipped suites released by the three corpora fail to capture 3% to 45% of the divergence in function behavior."

**C5** [OBSERVED] Cleaner-looking output can be less faithful: the strongest refinement LLM raised Ghidra's build rate from 75% to 90% while its behavioral Matched rate fell from 74% to 62%. The study attributes this to the model inventing fields, types, callees and guards where traditional tools leave visible unknowns, so errors become silent instead of obvious.
  - S7 <https://arxiv.org/html/2609.05370v1> chars 1765-1965: "the strongest refinement LLM lifts Ghidra’s build rate from 75% to 90%, while its Matched rate falls from 74% to 62%; on disclosed vulnerabilities, up to one tenth exhibit Crash Absence in its output."

**C6** [DERIVED] The distinguishing evidence is the original's actual behavior on many generated inputs, compared on return values, written bytes and global state, with divergences counted only if they reproduce across repeated runs. A separate source stresses that syntax checks only show the code parses, not that calculations or decisions are right, so project-specific tests are needed. Note the sources do not address identical library routines or overlays directly; applying this to those cases is an inference.
  - S7 <https://arxiv.org/html/2609.05370v1> chars 18617-18722: "The reference execution thus supplies the expected behavior without hand-written input/output assertions."
  - S8 <https://phpdecompile.com/blog/ioncube-decoded-code-quality> chars 2335-2459: "Passing syntax does not establish correct calculations, authorization decisions, callback behavior, or transaction handling."

**C7** [DERIVED] In a documented F# compiler case (dotnet/fsharp issue #9283), a function in one library that asked 'which assembly am I running in' returned the library's own name in Debug builds but the calling application's name in Release builds, because the compiler silently copied the function's body into the caller across the library boundary. The original function boundary effectively ceased to exist in the shipped binary, and the maintainers closed the issue in 2023 without changing the behavior, so this class of silent divergence persists.
  - S10 <https://github.com/dotnet/fsharp/issues/9283> chars 1183-1252: "Run the projects in Debug: name of the first project will be returned"
  - S10 <https://github.com/dotnet/fsharp/issues/9283> chars 1253-1358: "Run the projects in Release: the call will be inlined, so the name of the second project will be returned"

**C8** [DERIVED] The F# case shows boundary loss happened even though the called framework method was explicitly marked as not-inlinable, because the compiler did not honor that marking and the relevant security attribute was absent from the reference assemblies it compiled against. The maintainers' stated position was that there is no reliable attribute to detect such cases and that a maintained list of special APIs is hard to keep correct, so the only protection is the developer manually marking their own functions.
  - S10 <https://github.com/dotnet/fsharp/issues/9283> chars 15618-15900: "To address this a developer can add [<MethodImpl(MethodImplOptions.NoInlining)>], there's no reliable attribute for us to detect, and lists of well-known APIs are always difficult to reason about and maintain, and the developer can also suppress cross-assembly inlining when ne..."

**C9** [DERIVED] Zephyr's relocation feature lets a project move code and data for whole files or libraries into different memory regions without touching the source, and it keeps relocated items from being discarded even if unused unless told otherwise. The documentation warns that relocating kernel or architecture files can break because some contain early initialization that runs before relocation takes place, so placement changes can silently alter behavior of boundary-sensitive code.
  - S11 <https://docs.zephyrproject.org/latest/kernel/code-relocation.html> chars 487-596: "This script provides a robust way to re-order the memory contents without actually having to modify the code."
  - S11 <https://docs.zephyrproject.org/latest/kernel/code-relocation.html> chars 5849-5980: "Take care if relocating kernel/arch files, some contain early initialization code that executes before code relocation takes place."

**C10** [OBSERVED] A decompilation percentage is only meaningful with its unit (functions, bytes, files, symbols, assets), its scope (whole executable, one library, a region) and the build version measured. A project with 900 of 1,000 functions matched is 90% by function count but not 90% by bytes if the remaining functions hold half the code, so the same bar can hide very different amounts of remaining work.
  - S20 <https://decomphub.com/guides/understanding-decompilation-progress> chars 1490-1682: "Consider a hypothetical project with 900 of 1,000 functions matched. That is 90% by function count. If the remaining functions contain half of the program’s code bytes, it is not 90% by bytes."

**C11** [DERIVED] An unknown progress value can mean no compatible report exists, a source was unavailable, or scope could not be established, so it does not show that no work was done. Values above 100%, shifting denominators, or conflicting badges point to a report error or differing scopes and should not be silently clamped. Code-matching and asset-identification bars should not be averaged into one completion score.
  - S20 <https://decomphub.com/guides/understanding-decompilation-progress> chars 3754-3981: "Unknown can mean the project has no compatible report, a source was unavailable, the parser could not establish the scope, or collection has not reached a usable source yet. It does not establish that upstream has done no work."

**C12** [DERIVED] In the Decompile-Bench pipeline, roughly 100 million raw binary functions from about 85,000 binaries were reduced to 2 million matched pairs, about 2% retained. Losses came from discarding code not defined in the project repo (system and dependency headers, trivial getters/setters), keeping only one binary function per source function (such as template instantiations), and removing near-duplicates across binaries. This is a GCC/Clang DWARF-based pipeline, not a CodeWarrior one, so it indicates the order of magnitude and the categories of unmatched code rather than a CodeWarrior count.
  - S16 <https://www.emergentmind.com/topics/decompile-bench-dataset> chars 3858-4005: "This yields a final dataset of 2 million high-quality, project-rooted function pairs—retaining only approximately 2% of the initial function pool ("
  - _ledger: OBSERVED number(s) absent from verified spans: 100, 85000_

**C13** [DERIVED] Stripping removes the symbol table but leaves other structures that still enumerate functions. On the Mach-O build, a stripped file listed only one name yet a function-start list still held all five function starts in nine bytes. On Windows 64-bit images, exception-unwind entries still mark the start and end of every function that uses stack or calls another, though leaf functions are missing. A reviewer who trusts the name count will undercount badly, and the recovery methods can be scored against an unstripped twin build.
  - S21 <https://aiengineeringfromscratch.com/learn/tools-and-protocols/linking-loading-and-stripped-binaries> chars 2467-2515: "The stripped file lost its symbol table and kept"

**C14** [DERIVED] In the worked example, an agent read a pointer slot's raw bytes and reported a call into kernel space. The word was a placeholder that the loader replaces with the real library function address before the program starts. Reading a file as if it were the running process produces confident but wrong answers, and each format (ELF, PE, Mach-O) has its own placeholder mechanism.
  - S21 <https://aiengineeringfromscratch.com/learn/tools-and-protocols/linking-loading-and-stripped-binaries> chars 2192-2253: "Both answers read the file as if it were the running process."

**C15** [DERIVED] Recycled routines such as initialization, encoding and networking wrappers make a binary look larger and more complex than its unique logic. Collapsing familiar code and comparing the remaining delta across samples makes the distinctive part visible. This is general guidance, and the sources do not address what happens when a rebuilt copy of a CodeWarrior inline or template function differs from the original.
  - S23 <https://nhimg.org/faq/what-are-the-signs-that-a-binary-contains-more-reused-code-than-unique-malicious/> chars 3060-3152: "The goal is to collapse the familiar parts quickly so attention stays on the novel behavior."

**C16** [DERIVED] A rebuilt function can have 46 code bytes identical to the original and an identical relocation record, yet differ in the lookup table it points at (1,2,3,4,3 versus 1,2,3,4,4). A byte comparison alone reports no change; only reading the pointed-to data catches it. This is the same failure the TH08 project documented, where source 0.0 looked exact against target 128.0 and the fix audited 1,548 literal references and corrected twelve more.
  - S27 <https://aiengineeringfromscratch.com/learn/tools-and-protocols/binary-diffing-and-symbolic-execution> chars 18665-18724: "A function differ that stops at bytes says nothing changed."

**C17** [VERIFIED] Two builds of the same function (46 bytes, identical in the object files) were flagged different because the loaded images place the data section 0x70 bytes apart, changing one displacement byte (0x7a versus 0xea). Ghidra's byte correlator missed that function while its instruction correlator caught it, and rea's compare tool states it cannot normalize relocations. Teams chasing such a 'change' waste effort explaining something that does not exist.
  - S27 <https://aiengineeringfromscratch.com/learn/tools-and-protocols/binary-diffing-and-symbolic-execution> chars 10570-10658: "One byte of 46 differs, the Levenshtein ratio is 0.978, and the exact-bytes stage fails."
  - S24 <https://aiengineeringfromscratch.com/learn/tools-and-protocols/rebuild-and-prove-equal> chars 11296-11370: "Assembly is opaque provider text; relocation normalization is unavailable."

**C18** [DERIVED] In rea's matching tool, two functions whose file bytes differed in the relocation slot (48b80000... versus 48b8ab00...) were still reported as an identical-bytes match, because the loader rewrote both to the same value. The warning about loader fixups lived only in the source records and did not appear in the match report. Separately, a structural-shape match paired the wrong functions (percent_change with grade_label) until name matching contradicted it.
  - S25 <https://github.com/morluto/rea/issues/8556> chars 9963-10083: "It shows that identical loaded bytes do not imply identical file bytes and makes the missing source basis consequential."
  - S27 <https://aiengineeringfromscratch.com/learn/tools-and-protocols/binary-diffing-and-symbolic-execution> chars 8769-8889: "The false match also consumes grade_label on the right, so the real percent_change and grade_label pairs stay unmatched."

**C19** [DERIVED] The SSBU decomp reports 35.72% of functions compiled but only 7.00% of .text bytes compiled and 1.78% byte-matched, because matched functions average 46 bytes versus 986 for the undecompiled ones. Function counts therefore overstate real progress by a large factor, and the project itself calls byte-weighted progress the more accurate measure.
  - S28 <https://github.com/sbergeron42/ssbu-decomp> chars 2589-2691: "Progress skews toward small functions: avg matched function is 46 bytes vs avg undecompiled 986 bytes."
  - _ledger: OBSERVED number(s) absent from verified spans: 1.78%, 35.72%, 7.00%_

**C20** [DERIVED] SSBU decomp found that compiling zstd v1.3.7, confirmed as the same version in the binary, with upstream Clang 8.0.0 gave identical function sizes but 0% instruction match, since Nintendo's NX Clang fork differs in its backend. Roughly 6-15MB of library code (jemalloc, zstd, Lua, curl, SDK) was therefore classed as identifiable but non-matching, and some game logic is expected never to match. The reference compiler, not the source, is what decides whether a unit can be attributed with confidence.
  - S28 <https://github.com/sbergeron42/ssbu-decomp> chars 5815-6038: "Compiling zstd v1.3.7 (confirmed same version as in-binary) with upstream Clang 8.0.0 produces functions with identical sizes but 0% instruction match — different register allocation, instruction selection, and code layout."
  - S28 <https://github.com/sbergeron42/ssbu-decomp> chars 6671-6733: "Some will never match due to irreducible compiler differences."
  - _ledger: OBSERVED number(s) absent from verified spans: 15_

**C21** [DERIVED] SSBU decomp splits its naming into ground truth (4,888 exported symbols) versus about 10,191 community labels with no formal provenance, and tags guesses as inferred and flags them as 'verify before building on'. It also admits function boundaries from Ghidra may be over-sized or wrongly split. The practical consequence is that confidence in an attribution tracks its evidence tier, and a large share of labels sit in the weakest tier. Source material does not describe any specific reversal, so this is inferred from the project's own caveats.
  - S28 <https://github.com/sbergeron42/ssbu-decomp> chars 5394-5483: "Fields tagged [inferred: ...] are usage-pattern guesses — verify before building on them."
  - S28 <https://github.com/sbergeron42/ssbu-decomp> chars 3193-3339: "Function boundaries are Ghidra's best estimate — some may be over-sized (trailing alignment padding) or split (one function misidentified as two)."

**C22** [DERIVED] Matching decompilation depends on the exact compiler, flags and source context, so a match is only valid under the configuration it was checked against. The guidance is to rebuild affected code and re-verify previously matched functions after shared types or prototypes change, and to record compiler, flags and resulting diff with each result. A late discovery that the compiler or flags were wrong therefore invalidates matches, not just the functions still open.
  - S1 <https://www.retroreversing.com/decompilers> chars 18907-18961: "These are compiler- and version-dependent experiments."
  - S1 <https://www.retroreversing.com/decompilers> chars 21620-21728: "After changing shared types or prototypes, rebuild affected code and verify previously matched functions too"

**C23** [DERIVED] A function can show 100% while the rebuilt file still has wrong literal pools, section placement or data ownership, so completion claims based on per-function scores can hide latent mismatches. Teams should test their checker with deliberately wrong candidates (changed strings, constants, pointer-table entries) to confirm it rejects them, and run the full binary comparison. This reduces the chance that a hidden wrong assumption surfaces months later.
  - S1 <https://www.retroreversing.com/decompilers> chars 19812-19877: "Do not infer a complete rebuild from a function similarity score."
  - S1 <https://www.retroreversing.com/decompilers> chars 21795-21884: "A useful checker must reject incorrect reconstructions as well as recognise correct ones."

**C24** [DERIVED] In the Zelda: Wind Waker decomp, small residual diffs such as register swaps, out-of-order instructions or duplicated instructions can come from missing the original developers' inline functions, and debug maps from a prerelease kiosk demo are used to recover those inlines. Since inline usage changes generated code in non-obvious ways, a function forced to match with the wrong structure may be fragile, and the guide itself notes the maps only partly show inline use. This is a place where assumptions that later need revisiting accumulate.
  - S32 <https://github.com/zeldaret/tww/blob/main/docs/decompiling.md> chars 12278-12369: "Some examples of small issues in the assembly that may be caused by incorrect inline usage:"
  - S32 <https://github.com/zeldaret/tww/blob/main/docs/decompiling.md> chars 16532-16638: "However, there's an important caveat to keep in mind when reading the debug maps: Each inline only appears"

**C25** [DERIVED] GitHub's Copilot matcher compares a suggestion plus roughly 150 surrounding characters against an index of public GitHub repositories only, skips edited suggestions and user-written code, and flags fewer than 1% of suggestions. The index is refreshed only every few months, so it misses new code and can point to moved or deleted files. A wrong or empty answer therefore looks clean while the real source sits outside the index or was altered after the match.
  - S35 <https://aitechmodel.com/source-attribution-for-ai-generated-code-what-changed-and-why-it-matters-now/> chars 2230-2397: "The reference system has important gaps. It does not check altered Copilot suggestions or code written by the user, and matches appear in fewer than 1% of suggestions."
  - S35 <https://aitechmodel.com/source-attribution-for-ai-generated-code-what-changed-and-why-it-matters-now/> chars 2570-2704: "The index is refreshed every few months. It can therefore miss newly published code or point to files that have moved or been deleted."

**C26** [DERIVED] In the March 2026 chardet case, JPlag measured structural similarity to the prior LGPL version at under 1.3%, yet the original author disputes that the rewrite is independent because the maintainer had years of access to the LGPL code and the LLM reportedly accessed metadata from that version. A near-zero similarity score can coexist with a derivative relationship, so scoring-based attribution can make a wrong 'unrelated' call look rigorous.
  - S36 <https://www.taylorwessing.com/en/insights-and-events/insights/2026/06/ai-and-assisted-programming-in-open-source> chars 1602-1700: "According to JPlag analysis, the structural similarity to the previous version was less than 1.3%."
  - S36 <https://www.taylorwessing.com/en/insights-and-events/insights/2026/06/ai-and-assisted-programming-in-open-source> chars 1701-1895: "The original author disagrees: This is not a “clean room” implementation, as the maintainer had years of access to the LGPL code and the LLM demonstrably accessed metadata from the LGPL version."

**C27** [DERIVED] Language-model tools produce confident provenance and license statements ('this is MIT', 'no copyleft') that are unsubstantiated. They are fluent enough to pass a casual review, so a wrong source or license attribution reads as plausible. The law-firm source recommends treating every non-trivial AI snippet as external third-party content to be scanned and checked.
  - S36 <https://www.taylorwessing.com/en/insights-and-events/insights/2026/06/ai-and-assisted-programming-in-open-source> chars 3650-3947: "AI tools produce not only code but also “legal” accompanying statements (e.g., “this is MIT,” “this is freely usable,” “no copyleft”). This leads to false compliance: developers rely on unsubstantiated statements rather than verifiable license information (repository, LICENSE ..."
