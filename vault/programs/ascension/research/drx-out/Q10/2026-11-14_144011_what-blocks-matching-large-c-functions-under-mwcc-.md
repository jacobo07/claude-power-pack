# Blockers to Byte-Exact Matching of Large C++ Functions under mwcc (Wii, NW4R/EGG-style)

## 0. Bottom line

**The research gathered does not answer the question.** All eight learnings concern adjacent topics: decomp tooling, match-percentage semantics, linker folding, and general compiler behaviour. None cites an mwcc flag, pragma, manual page, repo file, issue or PR for the topics you asked about:

- `-inline auto/deferred` and inline depth
- constructors/destructors
- vtables and RTTI
- extab/extabindex
- templates
- member pointers
- copy constructors

I cannot give you the requested "with X, mwcc emits Y; with X', mwcc emits Y'" claims backed by a primary source, because none was retrieved. Section 3 lists predictions from my own background knowledge, tagged `[HYPOTHESIS][NONE]` and not verified in this session. Section 4 gives falsification procedures so you can promote or kill each one.

**Tag legend:** `[EPISTEMIC][SOURCE-QUALITY]`, carried verbatim from the research. `[HYPOTHESIS][NONE]` means my own recollection with no source retrieved.

---

## 1. What the research does support

### 1.1 Tooling is where inlining evidence comes from
- [DERIVED][MEDIUM] The toolchain has a diff tool that finds the most obvious cause of a mismatch in a linked ELF. It also has a map command that surfaces deduplicated weak functions, a known signature of inlining and template instantiation.
- [DERIVED][MEDIUM] A per-project inlining-failure count would therefore have to be assembled from these outputs, not read from documentation. The README describes the purposes of both tools, but neither source reports aggregate inlining statistics.
- **Falsifiable prediction (derived from the above, so also weak):** running the map command on a linked NW4R/EGG-style build should list weak symbols for template and inline instantiations. If it lists none for a TU known to use inline accessors, the claim fails.

### 1.2 Optimizer behaviour is context-dependent
- [DERIVED][LOW] Compilers apply only low-level, semantics-preserving transformations, and each is conditional on context. A repeated array read is reused only if no write can occur on any path in between.
- [DERIVED][LOW] Optimizations chain, so one pass exposes or removes work for the next. This makes output sensitive to surrounding code.
- **Weakness:** the source is a general compiler textbook example (quicksort). The extension to "mwcc output differs across functions and builds" is my inference, not a measured mwcc result.
- **Implication for large functions:** a small source change early in a function can change register allocation and scheduling much later in it. This is consistent with the observation, but not proof, that large functions are the hardest to match.

### 1.3 Linker folding can make "mismatches" or phantom identities
- [DERIVED][LOW] The linker can merge functions with byte-identical machine code. One piece of code then has two names, and a debugger shows the wrong one arbitrarily. Whether two functions fold depends on compiler version and optimization settings, and is very frequent with templates.
- [DERIVED][LOW] A developer can be sent to a function that was never called, with no source change. The effect can be switched off with a linker setting and should be ruled out before chasing a phantom bug. The triage consequence is my inference.
- **Caveat:** the source is a Windows/MSVC-era post demonstrating a single example. It gives no frequency and says nothing about the Metrowerks linker.
- [DERIVED][LOW] A comparable factor on the matching side: the MW2 rebuild developer attributes the unmatched ~17% of functions to nondeterminism and an inability to reproduce identical COMDAT folding in the linker. This is self-reported and unpublished. He also thinks stronger agents might still raise the figure, so the ceiling is not proven.
- **Prediction (weak):** when a function matches in isolation but fails in a linked build, first check COMDAT/weak-function folding and ordering.

### 1.4 How to read "match %" numbers
- [DERIVED][HIGH] Match figures use different units:
  - decomp.dev's code match rate counts matched code bytes.
  - The 83% figure for Modern Warfare 2 counts matched functions out of all functions.
  - The 99% figure counts functions with any reconstructed source.
- [DERIVED][HIGH] A Halo fork's README claims 99.5% byte matching, while the original repo on decomp.dev shows 23.25% (2,511 of 11,047 functions), with no definition given for the README figure.
- **Practical rule:** before citing any "matches byte for byte" claim for an NW4R/EGG project, find the denominator (bytes, functions, or functions with source) and who measured it.

### 1.5 Process findings on "impossible" functions
- [DERIVED][LOW] Snowboard Kids 2 stalled twice (≈25%→58%, then ≈75%) and still reached 100% on 2026-05-17, 596 days after the first commit. The last 10 hard functions were largely closed by community members. The stalls track the ordering strategy (easiest first, give up after 10 failed attempts), not true impossibility.
- [DERIVED][LOW] About 4.8% of matching commits (~41) involved experts on SGI's IDO compiler. The maintainer's own estimate, not a measurement, is that the match rate would otherwise have plateaued around 89–90%.
- **Transfer to mwcc:** weak. These are different compilers (IDO/MIPS), but the process lesson is that scarce knowledge of the exact toolchain matters most late in a project.

---

## 2. Coverage matrix: your question vs. evidence obtained

| Topic you asked about | Evidence retrieved | Status |
|---|---|---|
| `-inline auto/deferred`, inline depth | None | **Gap** |
| Constructors/destructors | None | **Gap** |
| Vtables and RTTI | None | **Gap** |
| extab/extabindex | None | **Gap** |
| Templates | Only indirect: weak-function dedup and folding (§1.1, §1.3) | **Thin** |
| Member pointers | None | **Gap** |
| Copy constructors | None | **Gap** |
| Source patterns that reproduce byte-exact output | None | **Gap** |
| Primary sources (compiler manual, repo file, issue, PR) | None cited for any mwcc claim | **Gap** |

---

## 3. Unverified hypotheses from background knowledge

None of these has a retrieved primary source. Treat each as a lead to test, not a finding.

| # | Topic | Prediction (X → Y; X' → Y') | Tag | Where to verify |
|---|---|---|---|---|
| H1 | Inline mode | With `-inline auto`, a small inline function defined *after* its caller in the TU is not inlined into it. With `-inline deferred`, it can be, because inlining runs after the whole TU is parsed. | [HYPOTHESIS][NONE] | Metrowerks compiler manual (`-inline`); compile a 2-function test |
| H2 | Inline mode | Switching `auto`→`deferred` changes the emission order of weak inline functions in `.text`. | [HYPOTHESIS][NONE] | objdump/map of a test TU |
| H3 | Inline depth | `#pragma inline_depth(n)` with a lower `n` leaves a nested inline call as a `bl`. A higher `n` flattens it. | [HYPOTHESIS][NONE] | Manual (pragma reference); test |
| H4 | Inline control | `#pragma dont_inline on` around a definition forces an out-of-line call at every call site. Without it, the same function is inlined when small. | [HYPOTHESIS][NONE] | Manual; test |
| H5 | Destructors | An empty virtual destructor emits a `__dt(this, flags)` function containing a null check on `this`, a `flags & 1` test, and a conditional `operator delete`. | [HYPOTHESIS][NONE] | Disassembly of any NW4R/EGG-style class; decomp project repos |
| H6 | Vtable placement | The vtable is emitted in the TU that defines the first non-inline, non-pure virtual function (the "key function"). If every virtual is inline, it is emitted weakly in each TU that uses it. | [HYPOTHESIS][NONE] | Test across two TUs; check weak vs. strong symbol |
| H7 | RTTI | With RTTI on, each polymorphic class gets a `__RTTI__` record referenced from the vtable. With `-RTTI off`, the record is absent and the vtable layout shifts. | [HYPOTHESIS][NONE] | Manual (`-RTTI`); compare `.rodata`/`.data` layout |
| H8 | Exceptions | With C++ exceptions enabled, any function owning a destructible local gets `extab`/`extabindex` entries. With `-Cpp_exceptions off`, none are emitted. | [HYPOTHESIS][NONE] | Manual (`-Cpp_exceptions`); section sizes in a test build |
| H9 | Extab dependency | Extab contents depend on object lifetimes and cleanup regions. Reordering local declarations or scoping can change extab bytes even when `.text` is identical. | [HYPOTHESIS][NONE] | Diff `.text` vs. extab for a scoping-only change |
| H10 | Templates | Template instantiations are emitted weakly. Identical instantiations in different TUs are folded by the linker. A mismatch can then be an ordering or folding artifact, not a code error (consistent with §1.3). | [HYPOTHESIS][NONE] | Linked map; weak-symbol listing |
| H11 | Copy-ctor / by-value | Passing a class by value with a non-trivial copy constructor generates a temporary with a copy-ctor call and (with exceptions on) an extab entry. A trivial copy constructor lets mwcc copy by registers or `lwz/stw`. | [HYPOTHESIS][NONE] | Test with a trivial vs. non-trivial copy-ctor struct |
| H12 | Member pointers | A pointer-to-member-function is a multi-word aggregate (this-adjust, vtable index or function pointer). A call through it compiles to a branch on the virtual flag. | [HYPOTHESIS][NONE] | Test with a virtual and a non-virtual method |

---

## 4. Falsification protocol

1. **Pin the compiler.** Build with the exact mwcc version and flags the target game used. Without this, every prediction above is untestable.
2. **Build minimal TUs** (2 functions, 1 class) for each hypothesis. Compile with variant flags, and compare with the project's diff tool and `.text`/extab/`.rodata` section dumps. This uses the tooling in §1.1.
3. **Compare at link level too**, using the map command, so that folding effects (§1.3) are separated from codegen effects.
4. **Promote or kill.** A hypothesis becomes `[OBSERVED]` only when the test output and the manual's text or a repo file agree. Record the source file and line.
5. **Consult primary sources**, as candidates rather than verified content:
   - the Metrowerks CodeWarrior compiler manual (for flag and pragma semantics)
   - the decomp toolkit and diff tool repos' issues
   - the Wii decomp projects' docs on compiler quirks

---

## 5. Suggested next steps (things you may not have considered)

- **Bisect large functions.** Because optimization effects chain (§1.2), split a large function's source into regions and match the first diverging region, not the whole function. [HYPOTHESIS][NONE] This is a working method, not a documented result.
- **Treat "unmatchable" as a toolchain-versus-code question** (§1.3, §1.5). Check linker flags and folding before spending effort on source rewrites.
- **Fix the denominator before comparing projects** (§1.4).
- **Use a second research pass** targeted at primary sources: the compiler manual's `-inline` and `-Cpp_exceptions` sections, and the decomp projects' compiler-quirk docs. That pass could convert H1–H12 from hypotheses to observed or refuted.

**Overall confidence:** the retrieved evidence is adequate only for the meta-level claims in §1 (tooling, match-percent semantics, folding as a confound). For the mwcc-specific questions you asked, it is absent.

## Contradicciones detectadas

Ninguna. Las fuentes procesadas no se contradicen entre sí en los puntos extraídos. Esto no significa consenso del campo: significa que las fuentes que este run alcanzó coinciden.

## Sources

- <https://github.com/encounter/decomp-toolkit>
- <https://github.com/doldecomp>
- <https://recompsoftware.com/platforms/wii/>
- <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/>
- <https://nsmbw-community.github.io/NSMBW-Decomp/docs/>
- <https://www.martincid.com/technology-sv/decomp-dev-ai-game-decompilation-shuts-index/>
- <https://xenospectrum.com/en/decompilation-match-rate-melee/>
- <https://www.tomshardware.com/tech-industry/artificial-intelligence/dev-used-ai-agents-and-more-than-500-billion-tokens-to-rebuild-call-of-duty-modern-warfare-2s-source-code-83-percent-of-the-2009-shooters-functions-now-match-the-original-byte-for-byte>
- <https://www.youtube.com/watch?v=Pl7ThC4PiVA>
- <https://arxiv.org/abs/2306.06884>
- <https://github.com/Dryxio/samp-source>
- <https://www.tomshardware.com/software/operating-systems/45-years-later-earliest-dos-source-code-transcribed-from-a-stack-of-old-printouts-found-in-a-garage-code-was-open-sourced-to-mark-86-dos-1-00s-anniversary>
- <https://devblogs.microsoft.com/oldnewthing/20050322-00/?p=36113/>
- <https://www.brainkart.com/article/The-Principal-Sources-of-Optimization_8191/>
- <https://en.wikipedia.org/wiki/Code_generation_%28compiler%29>
- <https://www.reddit.com/r/Compilers/comments/1b9flo/why_do_compilers_compile_the_same_code_in/>

## Run metadata

- **Prompt:** What blocks matching large C++ functions under mwcc for Wii (NW4R/EGG-style code): inlining decisions (-inline auto/deferred, inline depth), constructors/destructors, virtual tables and RTTI, exception tables (extab/extabindex), templates, member-pointer and copy-constructor code, and which documented source patterns make mwcc reproduce them byte for byte? For every claim give the primary source (repo file, issue, PR, compiler manual) and state it as a falsifiable prediction: 'with X, mwcc emits Y; with X', it emits Y''. Mark anything unverified.
- **Depth / breadth:** 2 / 4
- **Queries used:** 10 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 372.7 s
- **Errors during run:** 37
- **Started at:** 2026-11-14T13:40:11Z
- **Module version:** deep_research 0.4.1
- **Quality gates:** 0 query/queries rejected as keyword soup · 0 learning(s) dropped for containing code · 15 dropped as not operator-actionable (relevance: rated)
- **E1 decomposition:** 5/5 axes searched (BOUNDARY, COUNTEREXAMPLE, EVIDENCE, MECHANISM, TRANSFERABILITY)  — SHORTFALL: only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY; only 2 axis/axes covered (COUNTEREXAMPLE, MECHANISM) — minimum 3; missing: EVIDENCE, BOUNDARY, TRANSFERABILITY; only 2 axis/axes covered (MECHANISM, TRANSFERABILITY) — minimum 3; missing: EVIDENCE, BOUNDARY, COUNTEREXAMPLE
- **E2 landscape:** B_ACADEMIC×4, C_PRACTITIONER×9, D_VENDOR×1, UNKNOWN×25 · 0 question(s) refused as vendor-only · 0 learning(s) killed by the coverage gate
- **E3 reality:** DERIVED 8 · 12 label(s) demoted by the evidence gates
- **E4 contradictions:** 0 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `THIN` / MEDIUM [EVIDENCE] — 5 source(s), families C_PRACTITIONER, D_VENDOR, UNKNOWN — _What measurements have decompilation projects for Wii games actually recorded on how often_
- `UNCLASSIFIED` / LOW [MECHANISM] — 4 source(s), families UNKNOWN — _Why does the compiler produce different code for a large function when a small helper is i_
- `COVERED` / HIGH [BOUNDARY] — 5 source(s), families B_ACADEMIC, C_PRACTITIONER, UNKNOWN — _At what function size or complexity do attempts to reproduce the original compiled bytes s_
- `COVERED` / HIGH [BOUNDARY] — 4 source(s), families B_ACADEMIC, C_PRACTITIONER, UNKNOWN — _What happens when a large function with templates, member-pointer calls, copy constructors_
- `UNCLASSIFIED` / LOW [COUNTEREXAMPLE] — 4 source(s), families UNKNOWN — _Which functions in matching-decompilation projects were declared impossible to match and l_
- `THIN` / MEDIUM [MECHANISM] — 4 source(s), families C_PRACTITIONER, UNKNOWN — _Why does the same source code produce different register assignments, stack frame sizes an_
- `COVERED` / HIGH [COUNTEREXAMPLE] — 4 source(s), families B_ACADEMIC, C_PRACTITIONER, UNKNOWN — _Which documented source patterns that are said to reproduce original compiler output byte _
- `UNCLASSIFIED` / LOW [MECHANISM] — 4 source(s), families UNKNOWN — _Why does a piece of source code that produces identical machine code on one function under_
- `COVERED` / HIGH [TRANSFERABILITY] — 5 source(s), families B_ACADEMIC, C_PRACTITIONER, UNKNOWN — _What happens when a reverse-engineering team applies a matching technique that worked in o_

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 1.73%, 10.77%, 100%`
- `decomposition narrow: only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY`
- `fetch_page 'https://www.sciencedirect.com/topics/computer-science/inline...': page-fetch: https://www.sciencedirect.com/topics/computer-science/inline-function: HTTP Error 403: Forbidden`
- `source https://en.wikipedia.org/wiki/Inline_(C_and_C%2B%2B) carries instruction-like text ['tool-or-exfil-request']; treated as data`
- `source https://en.wikipedia.org/wiki/Inline_expansion carries instruction-like text ['tool-or-exfil-request']; treated as data`
- `source https://learn.microsoft.com/en-us/cpp/cpp/inline-functions-c carries instruction-like text ['tool-or-exfil-request']; treated as data`
- `source https://learn.microsoft.com/en-us/cpp/c-language/inline-func carries instruction-like text ['tool-or-exfil-request']; treated as data`
- `epistemic demoted VERIFIED -> DERIVED: VERIFIED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `web_search 'Why does the CodeWarrior compiler for Wi...': ddg: 0 hits parsed (possible block or empty SERP); brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`
- `fetch_page 'https://medium.com/@xersendo/optimizing-c-templates-from-inl...': page-fetch: https://medium.com/@xersendo/optimizing-c-templates-from-inlining-to-modules-62851191fd00: HTTP Error 403: Forbidden`
- `source https://0xghost.dev/blog/template-parameter-deduction/ carries instruction-like text ['tool-or-exfil-request']; treated as data`
- `source https://learn.microsoft.com/en-us/cpp/cpp/overload-resolutio carries instruction-like text ['tool-or-exfil-request']; treated as data`
- `decomposition narrow: only 2 axis/axes covered (COUNTEREXAMPLE, MECHANISM) — minimum 3; missing: EVIDENCE, BOUNDARY, TRANSFERABILITY`
- `fetch_page 'https://windowsforum.com/news/decomp-dev-shuts-its-public-le...': page-fetch: https://windowsforum.com/news/decomp-dev-shuts-its-public-leaderboard-as-ai-slop-disrupts-matching-decompilation.448883/: HTTP Error 403: Forbidden`
- `source https://www.tomshardware.com/tech-industry/artificial-intell carries instruction-like text ['role-reassignment']; treated as data`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `learning 0 unrated by relevance filter — kept, flagged UNRATED`

</details>


## Evidence ledger

- **Claims:** 23 · with a verified quote: 22 (rate 0.957)
- **Quotes:** 41 offered, 4 rejected (not verbatim / unknown source / length)
- **Sources:** 38 snapshots in 37 independent lineage(s); 0 URL(s) were byte-identical copies
- **Labels lowered by the ledger:** 4
- **Sources with instruction-like text (treated as data):** 9

**C1** [DERIVED] None of the retrieved material reports a measured frequency of large functions failing to match due to inlining choices, per project or per compiler version. The sources give project lists, completion percentages and general statements that CodeWarrior's optimization decisions are hard to predict, but no failure-rate data. Any estimate for effort on large functions would have to come from sampling a project directly.
  - S4 <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/> chars 4676-4793: "Matching C for CodeWarrior is harder than for GCC because the compiler's optimization decisions are less predictable."

**C2** [DERIVED] The Wii decomp tracker lists projects at very different maturity: Petari (Super Mario Galaxy) and Mario Strikers Charged are complete at 100%, while Wii Sports is at 35.03%, Xenoblade at 10.77% and Brawl at 1.73%. Completed or high-progress projects are the ones where hard, inlining-sensitive large functions have already been resolved or left as known blockers, so they are the best candidates for mining commit history and issue trackers for measurements. The compiler range cited is CodeWarrior 1.0 through 1.7 across titles, but no per-project version mapping is given.
  - S3 <https://recompsoftware.com/platforms/wii/> chars 2231-2298: "Wii Sports decompilation Wii Sports 2006 wip 35.03% Human-led — 187"
  - S4 <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/> chars 3965-4054: "The versions used across titles range from 1.0 through 1.7, per decomp.wtf documentation."
  - _ledger: OBSERVED number(s) absent from verified spans: 1.73%, 10.77%, 100%_

**C3** [DERIVED] The toolchain exposes a diff tool that finds the most obvious cause of a mismatch in a linked ELF, and a map command that surfaces deduplicated weak functions, which are a known signature of inlining and template instantiation. This means a per-project inlining-failure count would have to be assembled from these outputs, not read from documentation.
  - S1 <https://github.com/encounter/decomp-toolkit> chars 7502-7639: "Simple diff tool for issues in a linked ELF. (Yes, not DOL. It's misnamed.) Tries to find the most obvious difference causing a mismatch."

**C4** [DERIVED] Inlining copies a helper's body into every call site, so the large caller no longer contains a call at all. Optimization then runs on the enlarged body, with constants propagated, branches eliminated and registers allocated across the combined code. The instruction order and register choices in the large function therefore depend on whether the helper was inlined, and they differ from the not-inlined case, where arguments are passed and a call is made.
  - S7 <https://en.wikipedia.org/wiki/Inline_expansion> chars 6229-6293: "Register allocation can be done across the larger function body."
  - S7 <https://en.wikipedia.org/wiki/Inline_expansion> chars 4042-4251: "However, the main benefit of inline expansion is to allow further optimizations and improved scheduling, due to increasing the size of the function body, as better optimization is possible on larger functions."

**C5** [DERIVED] The same helper can end up inlined at some call sites while an out-of-line copy still exists, for example when its address is taken or the compiler judges it too large. In C++, an unexpanded helper is emitted as a shared copy that the linker merges across translation units. In C, a static helper instead gets a separate copy per translation unit. So the deduplicated-copy case is a linkage outcome, not just an optimizer choice.
  - S6 <https://en.wikipedia.org/wiki/Inline_(C_and_C%2B%2B)> chars 11055-11246: "In C++, a function defined inline will, if required, emit a function shared among translation units, typically by putting it into the common section of the object file for which it is needed."
  - S8 <https://learn.microsoft.com/en-us/cpp/cpp/inline-functions-cpp?view=msvc-170> chars 6963-7217: "Rather than expand an inline function defined in a header file, the compiler may create it as a callable function in more than one translation unit. The compiler marks the generated function for the linker to prevent one-definition-rule (ODR) violations."
  - S9 <https://learn.microsoft.com/en-us/cpp/c-language/inline-functions?view=msvc-170> chars 580-752: "Inline code substitution occurs only at the compiler's discretion. For example, the compiler won't inline a function if its address is taken or if it's too large to inline."

**C6** [DERIVED] Inline markings do not force inlining. Debug builds with MSVC's default setting disable it entirely, and even forced inlining is refused for recursion, varargs, or mismatched exception handling. Rust never inlines in debug mode. The same source therefore compiles to structurally different code per build mode, and the original build flags matter as much as the source.
  - S8 <https://learn.microsoft.com/en-us/cpp/cpp/inline-functions-cpp?view=msvc-170> chars 8205-8292: "The function or its caller is compiled with /Ob0 (the default option for debug builds)."
  - S7 <https://en.wikipedia.org/wiki/Inline_expansion> chars 20399-20445: "In debug mode, the compiler will never inline."
  - S8 <https://learn.microsoft.com/en-us/cpp/cpp/inline-functions-cpp?view=msvc-170> chars 5962-6092: "The compiler treats the inline expansion options and keywords as suggestions. There's no guarantee that functions will be inlined."

**C7** [DERIVED] Heavier inlining makes the compiled program larger, which can cause more instruction-cache misses and slow the program down in workloads under cache pressure. So the most aggressive optimization level is not always the fastest, and the claim has to be checked by profiling both builds.
  - S11 <https://unseel.com/cs/compilation-pipeline> chars 5788-5921: "Aggressive optimization can be slower in cache-pressured workloads (more inlining → larger code → more I-cache misses). Profile both."

**C8** [HYPOTHESIS] The retrieved material is about C++ language mechanics, not matching-decompilation practice, so it cannot say how people prove a difference is unreachable. It does show that compilers insert copy-constructor calls, and extra moves from pass-by-value parameters, that the author never wrote. Output differences can therefore come from compiler-generated behavior that no rewrite of the visible source controls, which suggests setting a stopping rule for repeated rewrites.
  - S15 <https://www.cs.odu.edu/~zeil/cs260/latest/Public/big3/index.html> chars 11877-11980: "The compiler often generates implicit calls to this constructor in places where we might not expect it."

**C9** [DERIVED] Snowboard Kids 2 stalled twice after the first AI-driven jumps (about 25% to 58%, then to about 75%), yet reached 100% on May 17, 2026, 596 days after the first commit. The last 10 especially hard functions were largely closed by community members, and the maintainer says the community mattered more than any model. Stalls reflect the ordering strategy (easiest first, give up after 10 failed attempts) rather than true impossibility.
  - S20 <https://xenospectrum.com/en/decompilation-match-rate-melee/> chars 14972-15059: "Processing functions from easiest to hardest has the problem that it eventually stalls."
  - S20 <https://xenospectrum.com/en/decompilation-match-rate-melee/> chars 15369-15476: "Community members reportedly played a major role in the last 10 functions, which were especially difficult."

**C10** [DERIVED] On Snowboard Kids, about 4.8% of matching commits (roughly 41) involved experts familiar with SGI's IDO compiler. The maintainer estimates that without them the match rate might have plateaued at around 89-90%. The estimate is the maintainer's own and is not a measured value.
  - S20 <https://xenospectrum.com/en/decompilation-match-rate-melee/> chars 16063-16169: "About 4.8% of commits related to matching work (about 41 commits) reportedly involved expert intervention."

**C11** [DERIVED] In the MW2 rebuild, the remaining roughly 17% of functions would not match byte for byte however often they were revised. The developer attributes this to nondeterministic behavior and to the inability to reproduce identical COMDAT folding in the linker, and he stopped there as diminishing returns. He thinks Opus 5.5 agents might still raise the figure, so this ceiling is not proven final.
  - S20 <https://xenospectrum.com/en/decompilation-match-rate-melee/> chars 8718-8815: "The remaining functions would not match byte for byte no matter how many times they were revised."
  - S21 <https://www.tomshardware.com/tech-industry/artificial-intelligence/dev-used-ai-agents-and-more-than-500-billion-tokens-to-rebuild-call-of-duty-modern-warfare-2s-source-code-83-percent-of-the-2009-shooters-functions-now-match-the-original-byte-for-byte> chars 9146-9266: "Heumann believes the 16% lacking a byte match are still semantically correct, but diminishing returns were getting real."

**C12** [HYPOTHESIS] Register assignment and spilling are decided by the compiler backend from live-range overlap, spill weights and the target's calling rules, so hand-reusing variables or restructuring code does not help and can hurt. Spilled values are what enlarge the stack frame, so frame size is an allocator outcome, not a source property. The advice is to profile first and trust the allocator unless hot-loop spilling is shown.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C13** [DERIVED] The same source yields different register and stack outcomes across platforms because the calling convention and register file are fixed by the target, not the code. In the one worked example, a function with 8 parameters had its last two passed on the stack on x86-64 System V (first 6 in registers), whereas ARM64 passed all 8 in registers with no stack access. Windows x64 differs again, passing 4 in registers and requiring 32 bytes of caller-allocated shadow space, so no rewrite can equalise these.
  - S25 <https://www.codermusings.com/register-allocation-compiler-guide/> chars 14508-14652: "With 8 function parameters, x86-64’s System V ABI passes the first 6 in registers (RDI through R9) and pushes parameters 7 and 8 onto the stack."
  - S26 <https://en.wikipedia.org/wiki/X86_calling_conventions> chars 22583-22834: "In the Microsoft x64 calling convention, it is the caller's responsibility to allocate 32 bytes of "shadow space" on the stack right before calling the function (regardless of the actual number of parameters used), and to pop the stack after the call."

**C14** [VERIFIED] Compilers and CPUs reorder independent instructions freely, and the result varies with context, hardware and surrounding code. Only data dependencies are preserved, which is safe for single-threaded programs but can break multithreaded code that lacks locks, atomics or barriers. Vendors also implement named conventions like fastcall differently, so mixing compilers can break interoperability.
  - S23 <https://dev.to/sachin_tolay_052a7e539e57/instruction-reordering-your-code-doesnt-always-run-in-the-order-you-wrote-it-bb8> chars 5900-6086: "Because CPUs and compilers apply many different optimizations based on context, hardware, and surrounding code, the specific ordering of operations can vary in ways you might not expect."
  - S26 <https://en.wikipedia.org/wiki/X86_calling_conventions> chars 8236-8375: "Conventions named fastcall or register have not been standardized, and have been implemented differently, depending on the compiler vendor."

**C15** [DERIVED] Reported match figures use different units: decomp.dev's code match rate counts matched code bytes, Heumann's 83% for Modern Warfare 2 counts matched functions out of all functions, and his 99% counts functions with any reconstructed source. A Halo fork's README claims 99.5% byte matching while the original repository on decomp.dev shows 23.25% (2,511 of 11,047 functions), with no definition given for the README figure, so a headline number can mean something very different from what it appears to.
  - S20 <https://xenospectrum.com/en/decompilation-match-rate-melee/> chars 5646-5740: "The 83% Heumann reported, by contrast, is the share of all functions that match byte for byte."
  - S20 <https://xenospectrum.com/en/decompilation-match-rate-melee/> chars 11226-11313: "The problem is that no definition is given for what the 99.5% in the README represents."
  - _ledger: OBSERVED number(s) absent from verified spans: 11047, 23.25%, 2511, 99%_

**C16** [DERIVED] The Modern Warfare 2 83% byte-match figure comes only from the developer's own report, the reconstructed code is unpublished, and third parties cannot verify it. By contrast, Melee, Snowboard Kids and Snowboard Kids 2 reaching 100% can be traced in decomp.dev's public records. None of the contents identifies an independent party reporting a failure of a specific source pattern on other functions, libraries or compiler builds, so the question's premise is not confirmed here.
  - S20 <https://xenospectrum.com/en/decompilation-match-rate-melee/> chars 10251-10356: "However, including the 83% byte-match rate, there is no way for third parties to verify it independently."

**C17** [DERIVED] Some functions stayed unmatched however many times they were revised: Heumann cites nondeterministic behavior and inability to reproduce identical COMDAT folding in the linker, so MW2 stopped at 83%. On Snowboard Kids, Lewis estimates roughly 4.8% of matching commits (about 41) involved experts familiar with SGI's IDO compiler, and without them matching might have plateaued around 89 to 90%, though this is his own estimate.
  - S20 <https://xenospectrum.com/en/decompilation-match-rate-melee/> chars 16063-16169: "About 4.8% of commits related to matching work (about 41 commits) reportedly involved expert intervention."
  - S20 <https://xenospectrum.com/en/decompilation-match-rate-melee/> chars 8718-8815: "The remaining functions would not match byte for byte no matter how many times they were revised."
  - _ledger: OBSERVED number(s) absent from verified spans: 83%, 89, 90%_

**C18** [DERIVED] The linker can merge functions whose generated machine code is byte-identical, so one piece of code ends up with two names and a debugger arbitrarily shows the wrong one. Whether two different functions end up identical depends on the compiler version and optimization settings, and is very frequent with templates, so the same pattern can be merged in one build and not in another.
  - S30 <https://devblogs.microsoft.com/oldnewthing/20050322-00/?p=36113/> chars 2018-2192: "(Note that whether two functions are identical at the object code level is highly dependent on which version of what compiler you’re using, and with which optimization flags."

**C19** [DERIVED] Because merging happens at link time and depends on the build, a developer or support team can be sent to a function that was never actually called, with no change in the source. This is a tooling artifact that can be switched off with a linker setting, so it should be ruled out before spending engineering time chasing a phantom bug.
  - S30 <https://devblogs.microsoft.com/oldnewthing/20050322-00/?p=36113/> chars 2805-2944: "Therefore, when the debugger sees that you’ve jumped to 0x010010d6 , it doesn’t know which of the names it should use, so it just picks on."

**C20** [DERIVED] Compilers apply only low-level, semantics-preserving transformations, and each one is conditional on context. For example, a repeated array read is reused only if no write to the array can occur on any path in between, so the same expression is optimized in one block and left alone in another. Optimizations also chain, so one pass exposes or removes work for the next, which makes the outcome sensitive to what surrounds the code.
  - S31 <https://www.brainkart.com/article/The-Principal-Sources-of-Optimization_8191/> chars 8081-8223: "Hence, a[tl] may not have the same value on reaching B6 as  it did on leaving B1, and it is not safe to treat a[tl] as a common subexpression."
  - S32 <https://en.wikipedia.org/wiki/Code_generation_%28compiler%29> chars 873-1097: "This multi-stage process is used because many algorithms for code optimization are easier to apply one at a time, or because the input to one optimization relies on the completed processing performed by another optimization."

**C21** [DERIVED] AI coding agents have compressed decompile-and-rebuild work for new hardware from months to hours or days, and the technique has carried across very different targets: a 2003 PC RTS to iOS, Halo and GTA V into web browsers, PS4's Bloodborne to native PC, and even a Switch 2 jailbreak. The reported limit is that classic games have relatively low code complexity, so the compression is best demonstrated on older titles, not modern large codebases.
  - S36 <https://www.gamemeca.com/en/view.php?gid=1781785> chars 2012-2195: "With a bit of help from AI, the process of rebuilding this code to suit other operating systems or current-gen hardware can be compressed from months down to a mere few hours or days."

**C22** [DERIVED] The decompilation progress index decomp.dev is shutting down because AI use turned its percentage leaderboard into a hollow numbers game, and indie studio Digital Sun kept its ReVamp playtest private for fear of reverse-engineered clones appearing before launch. The matching metric that motivated humans stopped meaning real understanding once tokens could be burned to raise it.
  - S37 <https://www.theverge.com/games/1004869/reverse-engineered-games-all-the-news-on-video-game-decomps-recomps-vr-and-web-and-3d-ports> chars 7793-7980: "Today, that same idea has warped decompilation into a hollow numbers game, exacerbated by folks who just want to burn tokens to make number go up or “port game to PC”, all else be damned."
  - S37 <https://www.theverge.com/games/1004869/reverse-engineered-games-all-the-news-on-video-game-decomps-recomps-vr-and-web-and-3d-ports> chars 7077-7194: "With launch still months away, sharing a build with tens of thousands of players felt like too big a risk for ReVamp."

**C23** [VERIFIED] Technical ports have succeeded broadly, but the browser GTA V port was shut down almost immediately by DMCA notices from Rockstar and Take-Two, and analysts expect Nintendo and Sony to stay strict. Microsoft is taking the opposite stance by creating Xbox Labs to experiment openly, so response varies sharply by rights holder. Anthropic has also altered Claude Code to steer away from direct game clones.
  - S36 <https://www.gamemeca.com/en/view.php?gid=1781785> chars 8023-8204: "The aforementioned web browser-based GTA 5 port was summarily shut down almost immediately after launch following DMCA takedown notices from Rockstar Games and Take-Two Interactive."
  - S37 <https://www.theverge.com/games/1004869/reverse-engineered-games-all-the-news-on-video-game-decomps-recomps-vr-and-web-and-3d-ports> chars 8728-8915: "Microsoft is putting together a new Xbox Labs group to explore the rapid emergence of these mods, many of which use AI models to help modders remix games in ways we’ve rarely seen before."
