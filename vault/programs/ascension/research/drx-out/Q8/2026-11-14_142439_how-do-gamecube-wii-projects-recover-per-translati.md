# Recovering per-translation-unit compiler flags and #pragmas in GameCube/Wii decompilation

## 0. Read this first: what the research supports and what it does not

The ledger holds 8 learnings. **None addresses mwcc (Metrowerks CodeWarrior), GameCube/Wii, `-O4,p` vs `-O4,s`, `-inline`, `-sdata` thresholds, `optimize_for_size`, `scheduling off`, `.sdata2` duplication, or any decomp repo file, issue or PR.** The sources behind them (S3, S5, S6, S10, S26-S28) are a GCC manual, a Retro Reversing guide, decomp.wtf-style verification material and generic compiler-behavior statements.

- **Gap, stated plainly:** no ledger entry supports any specific mwcc flag-to-binary-signal mapping. You asked for a primary source for every claim, and I cannot supply one for the core question. I have not invented repo paths, issue numbers or manual page numbers.
- **Section 2** gives the ledger-backed methodology, with tags carried over.
- **Section 3** gives mwcc-specific falsifiable predictions from my own background knowledge. All are tagged **[HYPOTHESIS][UNSOURCED]** and need verification before you rely on them.

## 1. Evidence-quality summary

| Ledger ref | Epistemic | Source quality | Relevance to the query |
|---|---|---|---|
| C20 | VERIFIED | HIGH | Generic: compiler version/config changes output |
| C7 | DERIVED | HIGH | Direct: function match ≠ correct data/link |
| C8 | DERIVED | HIGH | Direct: negative tests for the match checker |
| C13 | DERIVED | LOW | Partial: data layout can hide wrong settings (its x86 vs PowerPC link is inferred) |
| C14 | DERIVED | LOW | Partial: record compiler, flags and diff per candidate |
| C5 | DERIVED | LOW | Partial: stop-after-stage artifacts (GCC-flavored, not mwcc) |
| C6 | DERIVED | LOW | Marginal: reproducible-build path remapping (GCC) |
| C3 | DERIVED | MEDIUM | Marginal: coverage % overstates progress |

## 2. Ledger-backed methodology

### 2.1 Pin the toolchain before tuning flags
- **[VERIFIED][HIGH]** Option behavior and default optimization sets depend on compiler version and configuration, so identical flags can yield different binaries on a different release (C20; S26-S28).
- **Falsifiable form:** with mwcc build A and flags F, the output is O. With build B and the same F, the output may be O′ ≠ O, so flag search on the wrong build cannot converge.
- **Implication [DERIVED]:** treat the compiler build as a separate suspect from the flags. In practice, bisect the build before the flags whenever a previously matching unit stops matching.
- **Caveat:** the sources are general compiler manuals. They do not name mwcc build numbers.

### 2.2 A function match is not a flag-hypothesis validation
- **[DERIVED][HIGH]** Matching all functions does not show the rebuilt file supplies correct data or links correctly. Check literal pools, section placement and data ownership, and run a full binary comparison (C7; Retro Reversing guide).
- **[DERIVED][LOW]** Function order and literal use change constant-pool layout. Read-only vs writable and file-scope vs function-local placement matter, so wrong settings can pass on instructions and fail on data (C13).
- **My inference, not stated by the source:** a flag hypothesis (for example `-sdata` threshold or `-str` pooling) is only confirmed when it also reproduces section sizes, symbol placement and relocation targets. Instruction equality alone is insufficient.

### 2.3 Audit the checker with deliberately wrong candidates
- **[DERIVED][HIGH]** The decomp.wtf-style data tests change a string, a float constant or a pointer-table entry and expect rejection. If the checker still reports a complete match, it may cover only instructions, mask relocations, omit referenced data or use a stale build (C8).
- **Report scope explicitly:** isolated function, referenced data, linked object, or complete image.
- **Gap:** no measured false-match rate is given.
- **Proposed adaptation [HYPOTHESIS]:** to validate a flag-detection heuristic, apply it to units whose boundaries and flags are already known. Mutate each unit's flags (`-O4,p` → `-O4,s`, toggle `scheduling`, change the sdata threshold) and confirm the heuristic and the checker both flag the change. A heuristic that cannot detect injected flag changes on known units should not be trusted on unknown units.

### 2.4 Isolate compile-time from link-time layout changes
- **[DERIVED][LOW]** Stopping after a given stage and diffing the intermediate artifact for the single changed file separates compile-time ordering effects from link-time ones (C5; the GCC manual describes the stop-after-stage options, the strategy is inferred).
- **mwcc applicability [UNVERIFIED]:** whether and how mwcc emits comparable intermediates is not covered by the sources. The usual practice is to compare the `.o` against the split object from the original binary.

### 2.5 Record everything per candidate
- **[DERIVED][LOW]** Record the exact compiler, flags and resulting diff with each candidate, and do not generalize across targets (C14).
- **[DERIVED][LOW]** Path-remapping options exist to make builds location-independent (C6; GCC). The mwcc analogue is not established. In mwcc objects, embedded source-path strings may affect string-pool offsets [HYPOTHESIS][UNSOURCED].

### 2.6 Progress accounting
- **[DERIVED][MEDIUM]** Track data layout and final linking separately from function-match percentage. A project can be at ~90% function coverage and still fail to link (C3). The 90% figure is an illustration, not a measurement.

## 3. mwcc-specific predictions (background knowledge, not from the research)

**Status of this whole section: [HYPOTHESIS][UNSOURCED].** These come from my general familiarity with mwcc and GC/Wii decomp practice. None is backed by a ledger source, so I cite none. Each should be tested on a known-boundary unit before use. Items I am less sure of are marked **(low confidence)**.

| # | Signal | Prediction (with X → Y; with X′ → Y′) | Boundary or flag implication | Confidence |
|---|---|---|---|---|
| P1 | `.sdata2` float pool | With the default small-data2 threshold (commonly 8 bytes), float/double literals go to `.sdata2` (r2-relative). With the threshold at 0, they go to `.rodata` and are addressed via `lis/addi`. | Consistent use of r2-relative vs absolute float loads across a contiguous range suggests a threshold change at a unit boundary. | Medium |
| P2 | `.sdata` / `.sbss` split | With threshold ≥ object size, small globals land in `.sdata`/`.sbss` (r13-relative). With threshold 0, they land in `.data`/`.bss`. | A discontinuity in where same-sized objects live marks a flag change. | Medium |
| P3 | `-O4,p` vs `-O4,s` | `,s` favors size and `,p` favors speed. Expect differences in loop and inline decisions, and in `lmw/stmw` vs unrolled load/store prologue usage. | Per-function differences inside one unit suggest `#pragma optimize_for_size` rather than a unit-level flag. | Low |
| P4 | `#pragma scheduling off` | With scheduling on, instruction order is interleaved for latency. With it off, instructions follow source order with unscheduled load-use sequences. | If a single function is unscheduled while its neighbors are scheduled, expect a pragma, not a boundary. | Medium |
| P5 | `-inline` mode | With `-inline deferred`, inline functions are emitted after callers and in reversed order. With `-inline auto`, they follow normal order. | The weak/inline-function ordering in `.text` flips at a boundary. | Medium-low |
| P6 | String pool layout | With string pooling/reuse on, duplicate literals within a unit are merged in one `@stringBase0` region. With it off, each literal is a separate symbol. | Pool restarts mark unit boundaries. Merging across what you believed was a boundary means your split is wrong. | Medium |
| P7 | Float constant duplication | Each unit carries its own `.sdata2` copy of a constant, so the same value appearing twice in `.sdata2` implies two units. A unique copy implies one unit or deduplication. | Duplicate constants at distant offsets predict a boundary between them. | Medium |
| P8 | Alignment padding | Section start alignment per object follows the largest member alignment, so padding gaps at known section boundaries predict unit starts. | Unexpected padding inside a supposed unit suggests a missed split. | Medium |
| P9 | Function ordering | Functions emit in source order, with exceptions for inlines and weak/COMDAT-like symbols. | A reversal of expected order points to a deferred-inline flag or a header-defined function. | Low |
| P10 | `.comment` section | mwcc objects can record the compiler version and some flag state, which is useful for per-unit version attribution. | Present only if preserved in the original build. | Low (unverified) |

**Why these are not validated here:** the ledger gives no mwcc manual, no decomp repo files and no case studies. Candidate primary sources to check (names only, not verified): the CodeWarrior MWCPPC/Targeting manuals, the `decomp-toolkit` splits and config format, `objdiff`, and the per-project `configure.py` flag tables. I have not read them in this session.

## 4. Proposed validation protocol on known-boundary units

1. **Pin the compiler build** (§2.1) against a unit that matches trivially.
2. **Build a labelled corpus** of units with known boundaries and known flags (those already matching).
3. **Extract the signals P1-P9** per unit: `.sdata2` contents, string-pool base resets, section alignment, function order.
4. **Mutate flags** (§2.3) and record which signals move. This gives an empirical signal-to-flag table that replaces the unsourced predictions in §3.
5. **Predict on held-out units**, then verify by a full data and relocation comparison, not instruction diff alone (§2.2).
6. **Label the scope** of every result: function, data, object or image.
7. **Log** compiler, flags and diff per candidate (§2.5).

## 5. Open gaps (no evidence in this research)

- Primary-source mapping of mwcc flags to section/pool behavior, including exact default thresholds.
- Whether `.comment` or similar metadata reliably reveals per-unit flags.
- Real decomp-project precedents: repo files, issues and PRs where unit boundaries were inferred from `.sdata2` duplication or string-pool resets.
- Empirical false-positive rates for any boundary heuristic.
- Differences across mwcc builds (GC 1.x vs Wii 4.x) in the behaviors above.

**Recommendation:** rerun the research with targeted retrieval of the mwcc manuals and one or two mature GC/Wii decomp repos before treating §3 as more than a hypothesis list.

## Contradicciones detectadas

Ninguna. Las fuentes procesadas no se contradicen entre sí en los puntos extraídos. Esto no significa consenso del campo: significa que las fuentes que este run alcanzó coinciden.

## Sources

- <https://github.com/doldecomp>
- <https://github.com/encounter/decomp-toolkit>
- <https://initialrise.github.io/REWiki/04-recomp/matching-decomp/>
- <https://decomp.wiki/platforms/gamecube-wii>
- <https://gcc.gnu.org/onlinedocs/gcc-14.2.0/gcc/Overall-Options.html>
- <https://gcc.gnu.org/onlinedocs/gcc-4.1.2/gcc/Overall-Options.html>
- <https://arxiv.org/abs/2505.12668>
- <https://www.usenix.org/system/files/sec22-burk.pdf>
- <https://en.wikipedia.org/wiki/Decompiler>
- <https://www.retroreversing.com/decompilers>
- <https://arxiv.org/pdf/2312.13463>
- <https://blog.hpc.qmul.ac.uk/debugging-with-compiler-flags/>
- <https://laptopjudge.com/gcc-documentation/>
- <https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html>

## Run metadata

- **Prompt:** How do GameCube/Wii projects recover per-translation-unit compiler flags and #pragmas when one game mixes objects built with different flags (e.g. -O4,p vs -O4,s, -inline, -sdata thresholds, optimize_for_size, scheduling off): which binary signals (literal pools, .sdata2 float constant duplication, string pool layout, alignment padding, sbss/sdata split, function ordering) predict a unit boundary or a flag change, and how is a flag hypothesis validated on units whose boundaries are already known? For every claim give the primary source (repo file, issue, PR, compiler manual) and state it as a falsifiable prediction: 'with X, mwcc emits Y; with X', it emits Y''. Mark anything unverified.
- **Depth / breadth:** 2 / 4
- **Queries used:** 12 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 639.7 s
- **Errors during run:** 34
- **Started at:** 2026-11-14T13:24:39Z
- **Module version:** deep_research 0.4.1
- **Quality gates:** 0 query/queries rejected as keyword soup · 0 learning(s) dropped for containing code · 18 dropped as not operator-actionable (relevance: rated)
- **E1 decomposition:** 5/5 axes searched (BOUNDARY, COUNTEREXAMPLE, EVIDENCE, MECHANISM, TRANSFERABILITY)  — SHORTFALL: only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY; only 2 axis/axes covered (BOUNDARY, TRANSFERABILITY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE; only 2 axis/axes covered (BOUNDARY, EVIDENCE) — minimum 3; missing: MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY; only 2 axis/axes covered (COUNTEREXAMPLE, MECHANISM) — minimum 3; missing: EVIDENCE, BOUNDARY, TRANSFERABILITY
- **E2 landscape:** B_ACADEMIC×5, C_PRACTITIONER×7, UNKNOWN×30 · 0 question(s) refused as vendor-only · 0 learning(s) killed by the coverage gate
- **E3 reality:** VERIFIED 1, DERIVED 7 · 6 label(s) demoted by the evidence gates
- **E4 contradictions:** 0 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `THIN` / MEDIUM [EVIDENCE] — 4 source(s), families C_PRACTITIONER, UNKNOWN — _What measurements have decomp projects actually published showing which compiler flag diff_
- `UNCLASSIFIED` / LOW [MECHANISM] — 2 source(s), families UNKNOWN — _Why does changing a single compiler option for one source file shift the order of data, co_
- `COVERED` / HIGH [BOUNDARY] — 4 source(s), families B_ACADEMIC, C_PRACTITIONER, UNKNOWN — _What happens when a decompilation team guesses per-file compiler flags and gets a function_
- `THIN` / MEDIUM [MECHANISM] — 2 source(s), families C_PRACTITIONER, UNKNOWN — _Why does the Metrowerks compiler place float constants, string literals and small data in _
- `UNCLASSIFIED` / LOW [TRANSFERABILITY] — 2 source(s), families UNKNOWN — _Why does a decompilation project that guesses compiler settings from the output of an x86 _
- `UNCLASSIFIED` / LOW [BOUNDARY] — 5 source(s), families UNKNOWN — _What happens when a file is rebuilt with the wrong small-data size limit or the wrong opti_
- `THIN` / MEDIUM [BOUNDARY] — 4 source(s), families B_ACADEMIC, UNKNOWN — _When do the binary signals used to guess a unit boundary or a flag change become ambiguous_
- `UNCLASSIFIED` / LOW [EVIDENCE] — 3 source(s), families UNKNOWN — _What measured false-positive and false-negative rates do studies report when tools try to _
- `THIN` / HIGH [BOUNDARY] — 4 source(s), families B_ACADEMIC, UNKNOWN — _At what point does tuning compiler flags to match a target binary stop converging, and wha_
- `UNCLASSIFIED` / LOW [COUNTEREXAMPLE] — 4 source(s), families UNKNOWN — _Which GameCube or Wii games have units whose original build flags contradict the common as_
- `THIN` / MEDIUM [COUNTEREXAMPLE] — 5 source(s), families C_PRACTITIONER, UNKNOWN — _Which decompilation projects for GameCube or Wii games found that a few files, such as SDK_
- `THIN` / MEDIUM [MECHANISM] — 3 source(s), families B_ACADEMIC, UNKNOWN — _Why does a different release of the same compiler produce different instruction ordering, _

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `fetch_page 'https://deepwiki.com/encounter/decomp-toolkit/6-binary-analy...': page-fetch: https://deepwiki.com/encounter/decomp-toolkit/6-binary-analysis: HTTP Error 429: Too Many Requests`
- `decomposition narrow: only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY`
- `fetch_page 'https://linux.die.net/man/1/gcc...': page-fetch: https://linux.die.net/man/1/gcc: HTTP Error 403: Forbidden`
- `fetch_page 'https://stackoverflow.com/questions/18388710/what-is-the-pro...': page-fetch: https://stackoverflow.com/questions/18388710/what-is-the-proper-sequence-of-options-for-gcc-the-importance-of-that-sequence: HTTP Error 403: Forbidden`
- `fetch_page 'https://home.cs.colorado.edu/~main/cs1300/doc/gnu/gcc_2.html...': page-fetch: https://home.cs.colorado.edu/~main/cs1300/doc/gnu/gcc_2.html: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1010)>`
- `epistemic demoted VERIFIED -> DERIVED: VERIFIED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `learning 1 unrated by relevance filter — kept, flagged UNRATED`
- `learning 2 unrated by relevance filter — kept, flagged UNRATED`
- `fetch_page 'https://stackoverflow.com/questions/10311189/how-does-decomp...': page-fetch: https://stackoverflow.com/questions/10311189/how-does-decompiling-work: HTTP Error 403: Forbidden`
- `fetch_page 'https://manualzz.com/doc/o/1ewkwu/metrowerks-3.2-c-compilers...': page-fetch: https://manualzz.com/doc/o/1ewkwu/metrowerks-3.2-c-compilers-reference-manual-c-compiler: HTTP Error 403: Forbidden`
- `fetch_page 'https://stackoverflow.com/questions/14254889/what-is-the-dif...': page-fetch: https://stackoverflow.com/questions/14254889/what-is-the-difference-between-rodata-and-rodata-str1-4-section-in-compiled-ou: HTTP Error 403: Forbidden`
- `fetch_page 'https://www.cosmiclearn.com/embeddedc/memory-sections.php...': page-fetch: https://www.cosmiclearn.com/embeddedc/memory-sections.php: <urlopen error [WinError 10054] Se ha forzado la interrupción de una conexión existente por el host remoto>`
- `source https://github.com/PrimeDecomp/mwcc-tools/blob/main/gc2/docs carries instruction-like text ['tool-or-exfil-request']; treated as data`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `decomposition narrow: only 2 axis/axes covered (BOUNDARY, TRANSFERABILITY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE`
- `fetch_page 'https://stackoverflow.com/questions/618491/can-you-find-out-...': page-fetch: https://stackoverflow.com/questions/618491/can-you-find-out-which-compiler-was-used-to-compile-a-program: HTTP Error 403: Forbidden`
- `fetch_page 'https://reverseengineering.stackexchange.com/questions/170/i...': page-fetch: https://reverseengineering.stackexchange.com/questions/170/is-it-possible-to-hide-the-details-of-which-compiler-was-used: HTTP Error 403: Forbidden`
- `fetch_page 'https://stackoverflow.com/questions/10311189/how-does-decomp...': page-fetch: https://stackoverflow.com/questions/10311189/how-does-decompiling-work: HTTP Error 403: Forbidden`
- `learning 0 unrated by relevance filter — kept, flagged UNRATED`

</details>


## Evidence ledger

- **Claims:** 26 · with a verified quote: 26 (rate 1.0)
- **Quotes:** 51 offered, 2 rejected (not verbatim / unknown source / length)
- **Sources:** 38 snapshots in 37 independent lineage(s); 0 URL(s) were byte-identical copies
- **Labels lowered by the ledger:** 0
- **Sources with instruction-like text (treated as data):** 2

**C1** [DERIVED] The contents state that a flag mismatch makes every function unmatchable and looks like a source problem, and that large projects sometimes override flags for specific translation units. The practical consequence is that teams should test candidate flags against one known-matched function before spending effort rewriting code. Note that none of the sources publish per-translation-unit measurements of which flag differences changed instructions, data layout or section placement, so this is general guidance only.
  - S3 <https://initialrise.github.io/REWiki/04-recomp/matching-decomp/> chars 7601-7710: "Do not guess flags blindly. A flag mismatch makes every function unmatchable and looks like a source problem."
  - S3 <https://initialrise.github.io/REWiki/04-recomp/matching-decomp/> chars 7021-7117: "Sometimes per-file flag overrides. Large projects override flags for specific translation units."

**C2** [DERIVED] GameCube/Wii projects split the original binary into per-file objects, swap in decompiled versions one at a time, and relink with the original linker. If the output is still byte-for-byte identical, that confirms not just the instructions but the data layout and section placement for that file. This is the confirmation method the field uses, though the contents give no worked example of a specific flag difference caught this way.
  - S2 <https://github.com/encounter/decomp-toolkit> chars 2905-3023: "Then, each object can be replaced by a decompiled version as matching code is written. If the linker still generates a"
  - S3 <https://initialrise.github.io/REWiki/04-recomp/matching-decomp/> chars 3047-3144: "Every function and every piece of data in a file match, and the whole ROM rebuilds byte for byte."

**C3** [DERIVED] A project can sit at 90 percent function coverage and still fail to link the final binary because of data layout, literal pools, or one stubborn function. So function-level progress figures overstate how close a decomp is to a verified result, and data and section placement need their own tracking.
  - S3 <https://initialrise.github.io/REWiki/04-recomp/matching-decomp/> chars 3264-3415: "A project can sit at 90 percent function coverage and still fail to link the final ROM because of data layout, literal pools, or one stubborn function."

**C4** [DERIVED] The compiler toolchain runs four distinct stages in fixed order: preprocessing, compilation proper, assembly, and linking. Each source file is compiled to its own object file, and only the final linking step combines all object files into the executable, so a per-file option change takes effect in that file's object output before the linker merges everything.
  - S5 <https://gcc.gnu.org/onlinedocs/gcc-14.2.0/gcc/Overall-Options.html> chars 207-328: "Compilation can involve up to four stages: preprocessing, compilation proper, assembly and linking, always in that order."
  - S6 <https://gcc.gnu.org/onlinedocs/gcc-4.1.2/gcc/Overall-Options.html> chars 166-287: "Compilation can involve up to four stages: preprocessing, compilation proper, assembly and linking, always in that order."

**C5** [DERIVED] The compiler can be told to stop after any stage and hand back that stage's output: preprocessed source, assembler code, or an unlinked object file per source file. Comparing these for the single changed file, before and after the option change, isolates whether the data, constants and string literal ordering shifted at compile time or only later at link time.
  - S5 <https://gcc.gnu.org/onlinedocs/gcc-14.2.0/gcc/Overall-Options.html> chars 4719-4877: "Stop after the stage of compilation proper; do not assemble.  The output is in the form of an assembler code file for each non-assembler input file specified."
  - S5 <https://gcc.gnu.org/onlinedocs/gcc-14.2.0/gcc/Overall-Options.html> chars 4340-4509: "Compile or assemble the source files, but do not link.  The linking stage simply is not done.  The ultimate output is in the form of an object file for each source file."

**C6** [DERIVED] The compiler offers path-remapping options so that references to the build directory recorded in output are rewritten as if the files lived elsewhere, and the manual explicitly names this as the way to make location-independent reproducible builds. Build location is therefore one input that can change what gets embedded in the binary, and it can be neutralized.
  - S5 <https://gcc.gnu.org/onlinedocs/gcc-14.2.0/gcc/Overall-Options.html> chars 22921-22996: "This can be used to make reproducible builds that are location independent."

**C7** [DERIVED] Matching every function in a file does not show the rebuilt file supplies the right data or links into the final image correctly. The guidance is to check literal pools, section placement and data ownership after functions match, and to run a full binary comparison rather than inferring a complete rebuild from a function similarity score. This is where a coincidental function match under wrong per-file settings can hide until data or layout is compared.
  - S10 <https://www.retroreversing.com/decompilers> chars 19129-19259: "Matching each function does not establish that the rebuilt file supplies the correct data or links into the final image correctly."
  - S10 <https://www.retroreversing.com/decompilers> chars 19812-19877: "Do not infer a complete rebuild from a function similarity score."

**C8** [DERIVED] The decomp.wtf data tests change a string, a floating-point constant or a pointer-table entry and expect the checker to reject each; if it still reports a complete match, the check may cover only instructions, mask relocations, omit referenced data or use a stale build. Results should also be labelled by scope: isolated function, referenced data, linked object or complete image.
  - S10 <https://www.retroreversing.com/decompilers> chars 21795-21884: "A useful checker must reject incorrect reconstructions as well as recognise correct ones."
  - S10 <https://www.retroreversing.com/decompilers> chars 22664-22816: "If it still reports a complete match, inspect whether the check covers only instructions, masks relocations, omits referenced data or used an old build."

**C9** [DERIVED] Proposed source-file splits, grouped by shared constants or strings and related methods, are only hypotheses. They should be validated by assigning the associated data, rebuilding, and confirming existing matches and the final image survive, and settings should be checked against the project's known configuration and neighbouring matched functions before being changed.
  - S10 <https://www.retroreversing.com/decompilers> chars 20065-20208: "Treat a proposed split as a hypothesis: assign the associated data, rebuild, and check that existing matches and the final image remain intact."
  - S10 <https://www.retroreversing.com/decompilers> chars 18104-18214: "Before changing compiler settings, check the project’s known configuration and neighbouring matched functions."

**C10** [DERIVED] The compiler places each literal where it is first used and merges identical ones within a single unit. Functions the linker later discards still leave their literals behind, in the order the functions were defined. Literal order and duplication in the data therefore reveal unit boundaries and the ghosts of dead code. This was observed on the x86 host compiler; the PPC output probably follows the same front-end logic, but that is unconfirmed.
  - S11 <https://github.com/PrimeDecomp/mwcc-tools/blob/main/gc2/docs/matching-guide.md> chars 15116-15193: "MWCC emits a literal at its first use and pools equal literals within a unit."

**C11** [DERIVED] Statics are laid out in reverse declaration order, so their addresses run backward through the source. When function order does not explain the layout, the original declared those statics at file scope. This gives a cheap, objective check on a reconstruction before anyone spends time on instruction-level matching. It was observed on one compiler version and host.
  - S11 <https://github.com/PrimeDecomp/mwcc-tools/blob/main/gc2/docs/matching-guide.md> chars 13306-13357: "Statics are allocated in reverse declaration order."
  - S11 <https://github.com/PrimeDecomp/mwcc-tools/blob/main/gc2/docs/matching-guide.md> chars 13410-13466: "Use the .bss addresses to recover the declaration order."

**C12** [DERIVED] With automatic inlining, a function not marked inline is absorbed into its callers only if it stays under a counted-statement limit, not a size limit. The limit tightens with nesting: the guide gives 10 at nesting level 1 and 7 at level 2. One extra statement can flip a function between inlined and standalone, which changes both code order and which data stays in the unit. The 15-statement top-level figure is for the reference compiler, and the guide says the 2.6 compiler's own limit differs.
  - S11 <https://github.com/PrimeDecomp/mwcc-tools/blob/main/gc2/docs/matching-guide.md> chars 7938-7988: "The auto-inline limit counts statements, not size."
  - S11 <https://github.com/PrimeDecomp/mwcc-tools/blob/main/gc2/docs/matching-guide.md> chars 8175-8234: "At nesting level 1 the limit is 10, and at level 2 it is 7."

**C13** [DERIVED] Matching each function does not prove the rebuilt file has the right constants, strings or storage placement, because function order and literal use change how constant pools are laid out, and read-only versus writable and file-scope versus function-local placement matter. A compiler-settings guess validated only on instructions can therefore look right while the data layout is wrong, which is the kind of gap that separates an x86-derived guess from the PowerPC result.
  - S10 <https://www.retroreversing.com/decompilers> chars 19129-19259: "Matching each function does not establish that the rebuilt file supplies the correct data or links into the final image correctly."
  - S10 <https://www.retroreversing.com/decompilers> chars 19453-19508: "Function order and literal use can affect their layout."

**C14** [DERIVED] The source stresses that matching experiments are compiler- and version-dependent and that the exact compiler, flags and resulting diff should be recorded with each candidate rather than generalized. Settings inferred from a different target's output are therefore only a hypothesis until confirmed against the real target's own toolchain and known project configuration.
  - S10 <https://www.retroreversing.com/decompilers> chars 18962-19081: "Record the compiler, flags and resulting diff rather than treating a register-allocation heuristic as a universal rule."
  - S10 <https://www.retroreversing.com/decompilers> chars 18104-18214: "Before changing compiler settings, check the project’s known configuration and neighbouring matched functions."

**C15** [DERIVED] A target file size is only a best-effort guideline: after a run with a 100MB target, a table still held files of 5KB to 3MB because small partitions, recent or streaming files, and partition-filtered runs are skipped. A leftover cluster of tiny files therefore does not prove the setting was wrong, and a clean result does not prove it was right.
  - S16 <https://community.databricks.com/t5/data-engineering/small-files-persist-after-optimize-with-target-file-size-set-to/td-p/123975> chars 5006-5133: "That setting is only a guideline, not a hard rule. Delta makes a best effort but won’t force all files to match the exact size."
  - S13 <https://docs.databricks.com/aws/en/tables/tune-file-size> chars 7040-7167: "When set, all data layout optimization operations make a best-effort attempt to generate files of the specified size, including"

**C16** [DERIVED] Databricks autotunes target size by table size: 256 MB below 2.56 TB, rising linearly to 1 GB at 10 TB, with roughly 4,096 files expected at 1 TB and about 24,437 at 10 TB. A table with a manually pinned size stops being autotuned, and a wrong value leaves a measurable mismatch in file counts and sizes. Fabric also records the size distribution (minimum, median, maximum) after each compaction in table history, so a bad setting can be seen without reading the data.
  - S13 <https://docs.databricks.com/aws/en/tables/tune-file-size> chars 8570-8806: "For tables smaller than 2.56 TB, the autotuned target file size is 256 MB. For tables with a size between 2.56 TB and 10 TB, the target size grows linearly from 256 MB to 1 GB. For tables larger than 10 TB, the target file size is 1 GB."
  - S14 <https://learn.microsoft.com/en-us/fabric/data-engineering/table-compaction> chars 14584-14620: "Smallest file size after compaction."

**C17** [DERIVED] Raising a table's target size does not re-optimize files already written, so a large table keeps some undersized files, and changing clustering keys leaves old files in their previous layout unless a full table-wide recluster is run. That full pass can rewrite most or all of a large table and is substantially more expensive than routine maintenance, so a wrong setting is cheap to make and costly to undo.
  - S13 <https://docs.databricks.com/aws/en/tables/tune-file-size> chars 8812-8917: "When the target file size for a table grows, existing files are not re-optimized into larger files by the"

**C18** [DERIVED] The retrieved material contains no study of compilation-unit boundary recovery in stripped binaries, so nothing here supplies the measured rates or the effect of identical-function merging or shared string data. What it does establish is that false-positive and false-negative rates trade off against each other via the detection threshold, and that 'false positive rate' is defined inconsistently across fields, so any quoted figure must be read with its definition and threshold in hand.
  - S22 <https://en.wikipedia.org/wiki/False_positives_and_false_negatives> chars 6911-6993: "The higher this threshold, the more false negatives and the fewer false positives."
  - S22 <https://en.wikipedia.org/wiki/False_positives_and_false_negatives> chars 5209-5318: "Because of the ambiguity of notation in this field, it is essential to look at the definition in every paper."

**C19** [DERIVED] When a program behaves differently at different optimization levels, the manual-style guidance is to investigate undefined behavior in the source rather than keep hunting for a faster or safer flag. One reported case was a 'hardware-sensitive' project that crashed only in release builds; the real cause was an uninitialized value exposed by optimization, found with warning flags and a debug baseline, not by flag tuning.
  - S27 <https://laptopjudge.com/gcc-documentation/> chars 8462-8624: "If behavior changes, investigate undefined behavior before selecting a faster flag. Optimization often reveals an existing source defect rather than creating one."
  - S27 <https://laptopjudge.com/gcc-documentation/> chars 8748-8816: "The actual issue was an uninitialized value exposed by optimization."

**C20** [VERIFIED] Compiler behavior, available options, and default optimization sets vary by release, target and how the compiler was configured, so the same flags can yield different binaries or new diagnostics on a different version. The practical consequence is that matching a target binary requires first pinning the exact compiler version and full command, because flag tuning on the wrong version cannot converge.
  - S28 <https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html> chars 1450-1599: "Depending on the target and how GCC was configured, a slightly different set of optimizations may be enabled at each -O level than those listed here."
  - S27 <https://laptopjudge.com/gcc-documentation/> chars 5375-5477: "This approach separates actual source defects from new warnings introduced by a different GCC release."
  - S26 <https://blog.hpc.qmul.ac.uk/debugging-with-compiler-flags/> chars 11327-11404: "We also see that as compilers develop their diagnostic abilities may improve."

**C21** [DERIVED] The recommended safe practice is to record the compiler version, operating system and target architecture, exact compile and link commands, and the source commit or archive being tested before experimenting. Without that record, a mismatch cannot be attributed to flags, source, or compiler, and one-flag-at-a-time experiments have no fixed baseline to converge against.
  - S27 <https://laptopjudge.com/gcc-documentation/> chars 1541-1592: "The commit, archive, or source version being tested"
  - S27 <https://laptopjudge.com/gcc-documentation/> chars 167-284: "Check the compiler version, inspect available options, change one flag at a time, and test on the real target system."

**C22** [DERIVED] The contents state that CodeWarrior codegen is version-specific and that versions across titles range from 1.0 through 1.7, so a wrong version or flag set makes functions unmatchable. This implies that a small set of files (SDK or middleware) built with a different version can look like unmatchable code. The contents do not report any specific project, reporter, or discovery story.
  - S34 <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/> chars 15861-15969: "The key is giving the agent the exact compiler version and flags. CodeWarrior's codegen is version-specific."
  - S34 <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/> chars 5398-5532: "The SDK is a static library linked into every game. Different games may use different SDK versions, but the core functions are stable."

**C23** [DERIVED] Separate decompilations exist for specific SDK builds (the 5-23-2001 and 4-20-2004 Dolphin SDK libraries), which shows that SDK code differs by version and is tracked as its own project. Reusing matched SDK functions speeds up new games, but the existence of version-pinned SDK projects suggests the match may not carry over between builds.
  - S33 <https://github.com/orgs/doldecomp/repositories> chars 3567-3637: "A decompilation of the 5-23-2001 version of the Dolphin SDK Libraries."
  - S33 <https://github.com/orgs/doldecomp/repositories> chars 4634-4704: "A decompilation of the 4-20-2004 version of the Dolphin SDK Libraries."

**C24** [DERIVED] Register allocation is an NP-complete problem in general, so compilers rely on heuristics (spill-cost ordering, coalescing criteria, tie-breaking among candidates), and the sources note that the heuristics used for ordering and cost modification have a significant effect on the resulting allocation. A new release that tunes any of these will legitimately assign different registers or spill different variables for identical source and options.
  - S37 <https://en.wikipedia.org/wiki/Register_allocation> chars 17038-17167: "The heuristics used for ordering of RN reduction, and modification of cost have a significant effect on the resulting allocation."
  - S37 <https://en.wikipedia.org/wiki/Register_allocation> chars 5291-5372: "Chaitin et al. showed that optimal register allocation is an NP-complete problem."

**C25** [DERIVED] Compilers pick among allocation strategies that trade code quality against compile time: linear scan is greedy and fast (used in V8, the Android Runtime and the HotSpot client compiler), while graph coloring gives better code at quadratic cost (used by the HotSpot server compiler). Changing which strategy, or which refinement of it, a release uses changes the output for the same input.
  - S37 <https://en.wikipedia.org/wiki/Register_allocation> chars 21182-21252: "The Hotspot server compiler uses graph coloring for its superior code."
  - S37 <https://en.wikipedia.org/wiki/Register_allocation> chars 20664-20807: "The motivation for this approach is speed; not in terms of execution time of the generated code, but in terms of time spent in code generation."

**C26** [DERIVED] Allocation runs on an intermediate representation, not the source: the representation itself is agnostic about where values are stored, and the allocator decides locations, spilling to the stack when registers run out. Because this layer is internal to each compiler, a release that changes it or its passes can change placement without any source or option change.
  - S38 <https://browncs1260.github.io/notes/22> chars 4163-4227: "A basic block program is agnostic about where values get stored."
  - S38 <https://browncs1260.github.io/notes/22> chars 6055-6152: "We won't always be able to do this with registers alone, forcing us to spill over into the stack."
