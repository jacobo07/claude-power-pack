# Automated source-variant search for Metrowerks mwcc (GameCube/Wii): evidence report

## 1. Scope and honesty statement

The research returned **two learnings**. Neither is about mwcc, decomp-permuter internals, PERM macros, scoring, or distributed runs. Most of your question is therefore **unanswered by the evidence I hold**.

| Question component | Evidence status |
|---|---|
| decomp-permuter mwcc support and known limits | **No evidence retrieved** |
| PERM macros | **No evidence retrieved** |
| Randomization passes that change mwcc output | **No evidence retrieved** |
| Scoring function; why score 0 can differ from byte identity | **No evidence retrieved** |
| Parallel/distributed runs | **No evidence retrieved** |
| decomp.me scratch automation | **No evidence retrieved** |
| AI-assisted search with published success rates | **Partial**: one benchmark (non-mwcc), see §3 |
| Symbolic rewriting | **No evidence retrieved** |
| Regression gating of matched functions | **Partial**: one README-level claim, see §2 |

I will not fill these gaps with confident prose. Anything beyond the two learnings is labeled as a verification target, not a finding.

## 2. Finding A: matched-list regression ratchet

**Claim** [DERIVED][MEDIUM]: The tool keeps a list of matched functions. In check mode it fails the build when a listed function stops matching, or when library code is wrongly counted as decompiled. This turns matching progress into a ratchet that can run in CI.

- **Source**: README (ledger C11, S10). It describes the matched-list workflow, the `REGRESSION` status, and exit code 1 on regression.
- **Gaps**:
  - The learning does not name the tool, and I will not guess.
  - It is not stated whether the tool is mwcc-specific.
  - No data exists on how often regressions occur.
  - "[DERIVED]" means the ratchet framing is an inference from the README, not a quote.
- **Practical capability**: gate every build on a committed matched-list, so regressions surface immediately rather than at final link.

**Falsifiable predictions** (all from the README description, [MEDIUM]):
1. With function F in the matched list and F's compiled output changed so it no longer matches, check mode reports `REGRESSION` for F and exits 1. With F's output unchanged (F'), it exits 0.
2. With library code wrongly counted as decompiled, check mode fails. With it correctly excluded, it passes.

**Unverified**: the exact status strings and exit codes in a current release. Run the tool on a fixture to confirm.

## 3. Finding B: AI-assisted matching benchmark (non-mwcc)

**Claim** [DERIVED][MEDIUM]: In the benchmark, nearly half of AI-phase matches came on the first attempt. A function unmatched by attempt 3 had only about a 25% chance of eventually matching.

**Claim** [DERIVED][MEDIUM]: The permuter mattered most on the IDO-compiled N64 game (Animal Forest), matching 3–4 functions per run. It matched **none** on the ARM/GBA game (Sonic Advance 3). Permutation value therefore depends on how well the tool supports the compiler.

- **Source**: benchmark figures (ledger C15, S18).
- **Critical gap**: **Metrowerks/mwcc support was not measured in these sources.** Nothing here transfers directly to GameCube/Wii. Treat it as an analogy only.
- **Other gaps**: there is no sample size, no per-function difficulty stratification, and no definition of "attempt" in the learning. The 25% figure is conditional and may not survive a different corpus.

**Implication** [DERIVED][MEDIUM]: Fund attempt budget front-loaded. Stop spending on functions unmatched after about 3 attempts, or switch strategy for them, since the marginal return is low.

**Falsifiable predictions** (benchmark-bound, so they apply to mwcc only if replicated):
1. With the same benchmark protocol on a mwcc game, about half of AI-phase matches occur on attempt 1. With a different protocol, this may fail.
2. With functions unmatched after attempt 3, the eventual match rate is about 25% (the benchmark's figure, not a mwcc one).
3. With the permuter run on IDO-compiled code, expect 3–4 matches per run. With ARM/GBA, expect about 0. **For mwcc the value is unknown and should be measured before being budgeted.**

## 4. What I cannot assert about decomp-permuter and mwcc

I have no retrieved evidence for the following. Each is **unverified** and listed only as a check target.

| Topic | What to verify | Where to look (unverified pointers) |
|---|---|---|
| mwcc support | Whether the compiler is driven via a user-supplied compile script, and which flags are assumed | permuter repo README and `compile.sh`/`settings.toml` conventions in a decomp project |
| PERM macros | The macro set and semantics (e.g., choice, expression, ordering variants) | permuter README section on PERM macros |
| Randomization passes | Which AST rewrites change mwcc codegen (statement order, temp introduction, operand swap, type casts) | `src/randomizer.py` and related passes |
| Scoring | How the score is computed from assembly diffs, and whether score 0 implies byte identity | `src/scorer.py`; issue tracker |
| Score 0 ≠ byte identity | Candidates: relocations, symbol or section differences, data/rodata ordering, and scorer normalization that ignores some instruction details | Needs a concrete case |
| Parallel/distributed | Local multi-process flags; no distributed claim retrieved | README flags |
| decomp.me automation | API availability and scratch automation | decomp.me repo and API docs |
| Symbolic rewriting | Any published tool | Not located |

## 5. Anticipated needs and suggested approaches

These are my suggestions, **[HYPOTHESIS]**, not research findings.

1. **Measure before budgeting.** Reproduce the §3 benchmark on a corpus of already-compiling but non-matching mwcc functions. Record per-attempt cumulative match rate, so you get your own first-attempt share and attempt-3 conditional rate for mwcc.
2. **Audit score 0 explicitly.** For every permuter score-0 result, run a byte-level comparison of the final object or linked output against the target. Log the cause of any residual difference. This builds the empirical taxonomy your question implies and no source I hold provides.
3. **Combine with the ratchet.** Feed only byte-verified matches into the matched-list (§2), so a scorer false positive cannot enter the regression baseline.
4. **Mutation-oracle testing for falsifiability.** For each randomization pass, take a function that already matches, apply the pass in isolation, and diff mwcc output. A pass that never changes output on a corpus is dead weight for mwcc. Counting passes by output-changing frequency would produce the "passes that actually change mwcc output" table you want.
5. **Contrarian idea**: a many-small-compile search guided by instruction-level diff features (register allocation versus scheduling versus ordering) could prune randomization choices. This is speculative and untested here.

## 6. Bottom line

- **Supported** [DERIVED][MEDIUM]: matched-list regression gating exists as a CI-usable ratchet, and an AI benchmark shows front-loaded returns, with permuter value depending on compiler support.
- **Not supported by retrieved evidence**: every mwcc-specific claim, including limits, PERM macros, passes, scoring versus byte identity, parallelism, decomp.me automation, and symbolic rewriting. A second research pass targeting the permuter repo files and issue tracker is required before any of these can be stated as findings.

## Contradicciones detectadas

Ninguna. Las fuentes procesadas no se contradicen entre sí en los puntos extraídos. Esto no significa consenso del campo: significa que las fuentes que este run alcanzó coinciden.

## Sources

- <https://github.com/dmadevice/verifier>
- <https://docs.oracle.com/cd/E26505_01/html/E26506/chapter2-90421.html>
- <https://link.springer.com/chapter/10.1007/979-8-8688-2154-7_6>
- <https://gambiconf.substack.com/p/can-llms-really-do-matching-decompilation>
- <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/>
- <https://capitalandcompute.net/blog/which-games-has-ai-decompiled/>
- <https://reversedwithai.com/ai-game-decompilation>
- <https://recompsoftware.com/progress/>

## Run metadata

- **Prompt:** How do decompilation projects run automated source-variant search at scale for Metrowerks mwcc (GameCube/Wii): decomp-permuter's mwcc support and its known limits, PERM macros, randomization passes that actually change mwcc output, scoring functions and why a permuter score of 0 can still differ from byte identity, parallel/distributed runs, and any other tool (decomp.me scratch automation, AI-assisted search, symbolic rewriting) with published success rates on functions that already compile but do not match? For every claim give the primary source (repo file, issue, PR, compiler manual) and state it as a falsifiable prediction: 'with X, mwcc emits Y; with X', it emits Y''. Mark anything unverified.
- **Depth / breadth:** 2 / 4
- **Queries used:** 8 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 995.4 s
- **Errors during run:** 25
- **Started at:** 2026-11-14T13:13:58Z
- **Module version:** deep_research 0.4.1
- **Quality gates:** 0 query/queries rejected as keyword soup · 0 learning(s) dropped for containing code · 16 dropped as not operator-actionable (relevance: rated)
- **E1 decomposition:** 5/5 axes searched (BOUNDARY, COUNTEREXAMPLE, EVIDENCE, MECHANISM, TRANSFERABILITY)  — SHORTFALL: only 2 axis/axes covered (COUNTEREXAMPLE, MECHANISM) — minimum 3; missing: EVIDENCE, BOUNDARY, TRANSFERABILITY; only 2 axis/axes covered (EVIDENCE, MECHANISM) — minimum 3; missing: BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY
- **E2 landscape:** B_ACADEMIC×6, C_PRACTITIONER×3, D_VENDOR×1, UNKNOWN×14 · 0 question(s) refused as vendor-only · 0 learning(s) killed by the coverage gate
- **E3 reality:** DERIVED 2 · 7 label(s) demoted by the evidence gates
- **E4 contradictions:** 0 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `THIN` / MEDIUM [EVIDENCE] — 4 source(s), families C_PRACTITIONER, UNKNOWN — _What measured match rates do decompilation projects report when they run automated source-_
- `THIN` / HIGH [MECHANISM] — 4 source(s), families B_ACADEMIC, UNKNOWN — _Why does a source-level random mutation change the machine code that the Metrowerks compil_
- `UNCLASSIFIED` / LOW [MECHANISM] — 1 source(s), families UNKNOWN — _Why does a small change in how a C function is written cause the Metrowerks PowerPC compil_
- `THIN` / MEDIUM [COUNTEREXAMPLE] — 3 source(s), families C_PRACTITIONER, UNKNOWN — _What happens when a decompiled function scores as a perfect match by instruction, relocati_
- `THIN` / HIGH [TRANSFERABILITY] — 5 source(s), families B_ACADEMIC, D_VENDOR, UNKNOWN — _Do approaches that rewrite code symbolically or use language models to search for matching_
- `THIN` / MEDIUM [EVIDENCE] — 5 source(s), families C_PRACTITIONER, UNKNOWN — _What match rates have GameCube and Wii decompilation projects actually reported when they _
- `THIN` / MEDIUM [MECHANISM] — 2 source(s), families B_ACADEMIC, UNKNOWN — _Why do register allocation, instruction scheduling and inlining decisions in the Metrowerk_

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `fetch_page 'https://windowsforum.com/news/decomp-dev-shuts-its-public-le...': page-fetch: https://windowsforum.com/news/decomp-dev-shuts-its-public-leaderboard-as-ai-slop-disrupts-matching-decompilation.448883/: HTTP Error 403: Forbidden`
- `source https://www.tomshardware.com/video-games/retro-gaming/game-d carries instruction-like text ['role-reassignment']; treated as data`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 10, 16`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `generate_serp_queries: claude.exe: subprocess failed: Command '['C:\\Users\\User\\.local\\bin\\claude.exe', '--model', 'claude-sonnet-5-5', '-p', '--disable-slash-commands', '--disallowed-tools', '*', '--setting-sources', 'local', '--strict-mcp-config', '--append-system-prompt', "You are an expert researcher. Today is 2026-11-14. Follow these instructions when responding:\n - You may be asked to research subjects that is after your knowledge cutoff, assume the user is right when presented with news.\n - The user is a highly experienced analyst, no need to simplify it, be as detailed as possible and make sure your response is correct.\n - Be highly organized.\n - Suggest solutions that I didn't think about.\n - Be proactive and anticipate my needs.\n - Treat me as an expert in all subject matter.\n - Mistakes erode my trust, so be accurate and thorough.\n - Provide detailed explanations, I'm comfortable with lots of detail.\n - Value good arguments over authorities, the source is irrelevant.\n - Consider new technologies and contrarian ideas, not just the conventional wisdom.\n - You may use high levels of speculation or prediction, just flag it for me."]' timed out after 120 seconds; anthropic-sdk: ANTHROPIC_API_KEY not set`
- `no SERP queries generated`
- `fetch_page 'https://web.stanford.edu/class/cs143/lectures/lecture16.pdf...': page-fetch: https://web.stanford.edu/class/cs143/lectures/lecture16.pdf: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1010)>`
- `decomposition narrow: only 2 axis/axes covered (COUNTEREXAMPLE, MECHANISM) — minimum 3; missing: EVIDENCE, BOUNDARY, TRANSFERABILITY`
- `fetch_page 'https://www.ibm.com/docs/en/aix/7.2.0?topic=overview-registe...': page-fetch: https://www.ibm.com/docs/en/aix/7.2.0?topic=overview-register-usage-conventions: HTTP Error 403: Forbidden`
- `fetch_page 'https://stackoverflow.com/questions/78647291/what-syntax-do-...': page-fetch: https://stackoverflow.com/questions/78647291/what-syntax-do-i-need-to-make-the-compiler-put-this-variable-on-the-stack: HTTP Error 403: Forbidden`
- `fetch_page 'https://stackoverflow.com/questions/10630649/function-callin...': page-fetch: https://stackoverflow.com/questions/10630649/function-calling-convention-powerpc-vs-intel: HTTP Error 403: Forbidden`
- `fetch_page 'https://users.ece.utexas.edu/~valvano/embed/chap12/chap12.ht...': page-fetch: https://users.ece.utexas.edu/~valvano/embed/chap12/chap12.htm: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1010)>`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `fetch_page 'https://medium.com/@0xzoowa/the-linker-relocation-part-2-35d...': page-fetch: https://medium.com/@0xzoowa/the-linker-relocation-part-2-35db96844514: HTTP Error 403: Forbidden`
- `fetch_page 'https://deepwiki.com/tangOS-decomps/pictochat-decomp/5.2-mat...': page-fetch: https://deepwiki.com/tangOS-decomps/pictochat-decomp/5.2-matching-and-verification-tools: HTTP Error 429: Too Many Requests`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `web_search 'At what point does automated permutation...': ddg: 0 hits parsed (possible block or empty SERP); brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 2024`
- `decomposition narrow: only 2 axis/axes covered (EVIDENCE, MECHANISM) — minimum 3; missing: BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY`
- `source https://gambiconf.substack.com/p/can-llms-really-do-matching carries instruction-like text ['system-prompt-reference', 'tool-or-exfil-request']; treated as data`

</details>


## Evidence ledger

- **Claims:** 18 · with a verified quote: 18 (rate 1.0)
- **Quotes:** 30 offered, 1 rejected (not verbatim / unknown source / length)
- **Sources:** 23 snapshots in 23 independent lineage(s); 0 URL(s) were byte-identical copies
- **Labels lowered by the ledger:** 4
- **Sources with instruction-like text (treated as data):** 2

**C1** [DERIVED] A rebuild of every matched function in 16 public decompilations on the released compiler with default settings found 10 of 14 agent-assisted projects hold at 99–100%, while four fall below 99% because they rely on patched compilers or per-file settings. Pokémon Colosseum, a GameCube title, is the worst at 71.4% stock matches, and both human-built references (Melee, The Wind Waker) hit 100%. Headline match numbers therefore overstate genuine source recovery in a minority of agent projects.
  - S1 <https://github.com/puiji/decompilation-eval> chars 1573-1791: "Ten of the 14 agent-assisted projects match at 99–100% on stock tools. Four fall below 99%, using patched compilers or per-file settings for part of their code; Pokémon Colosseum has the most, with 71.4% stock matches."
  - S1 <https://github.com/puiji/decompilation-eval> chars 1792-1909: "Both human-built projects (Melee, The Wind Waker) match at 100%, counting community-shared compiler patches as stock."
  - _ledger: OBSERVED number(s) absent from verified spans: 10, 16_

**C2** [DERIVED] The evaluator reports that functions depending on patched compilers or per-file settings cannot be distinguished by reading the source: neither a static scanner nor an LLM classifier could find them. Only rebuilding on the stock compiler exposes them, so verification cost is a compute-and-build cost, not a reviewer-time cost.
  - S1 <https://github.com/puiji/decompilation-eval> chars 1910-2055: "You can't tell these functions apart by reading the source; neither a static scanner nor an LLM classifier could. The rebuild is what finds them."

**C3** [DERIVED] The decomp.dev leaderboard, the main central tracker of matching progress, is closing to new projects, with its maintainer saying AI made percentages easy to inflate. Existing projects such as Melee keep reporting, but new AI-assisted projects will have no shared independent number, which makes the single-author stock-compiler audit more significant. The searched question (match rates from automated source-variant search on near-miss functions) is not answered by any of these sources.
  - S4 <https://www.tomshardware.com/video-games/retro-gaming/game-decompilation-tracker-decomp-dev-shuts-its-public-leaderboard-saying-ai-has-broken-the-community-its-creator-blames-forks-that-use-ai-to-finish-other-teams-projects-and-races-to-ship-rough-pc-ports> chars 8357-8438: "However, no new projects may join, and nobody may rebuild the site from its code."
  - S4 <https://www.tomshardware.com/video-games/retro-gaming/game-decompilation-tracker-decomp-dev-shuts-its-public-leaderboard-saying-ai-has-broken-the-community-its-creator-blames-forks-that-use-ai-to-finish-other-teams-projects-and-races-to-ship-rough-pc-ports> chars 4641-4710: "AI has made the progress percentages on decomp.dev easier to push up."

**C4** [DERIVED] Final code generation takes optimized intermediate code and assigns variables to a small, fixed set of registers, with each intermediate line expanding into one or more machine instructions. Because register assignment and instruction expansion happen at this last stage, a source tweak that leaves the intermediate form unchanged will leave the output unchanged, while one that alters it can reshuffle registers and instruction order.
  - S7 <https://www.geeksforgeeks.org/compiler-design/target-code-generation-in-compiler-design/> chars 831-972: "Each line in optimized code may map to one  or more lines in machine (or) assembly code, hence there is a  1:N mapping associated with them ."
  - S7 <https://www.geeksforgeeks.org/compiler-design/target-code-generation-in-compiler-design/> chars 1584-1726: "Register allocation is the process of assigning program variables to  registers and  reducing the number of swaps in and out of the registers."

**C5** [DERIVED] Mutation research defines equivalent mutants as variants with identical outputs on all inputs, and notes full equivalence is undecidable and in practice only checked on a finite test suite. Equivalence in behavior says nothing about identical instruction bytes, and that gap is one reason a zero-difference score can still fall short of a byte-exact match.
  - S6 <https://www.emergentmind.com/topics/source-code-mutation> chars 2050-2095: "Full equivalence is undecidable; in practice,"

**C6** [HYPOTHESIS] Classical mutation operators were designed to mimic programmer faults, and research notes fixed operator sets are insufficient even for real bugs. Operators like replacing a loop with a single iteration change behavior, so they do not target the output-preserving rewrites needed to nudge compiler output, which means random edits need guidance toward constructs the compiler is sensitive to.
  - S6 <https://www.emergentmind.com/topics/source-code-mutation> chars 3634-3943: "Recent research stresses the insufficiency of fixed operator sets: deletion of arbitrary method calls and identifier renaming are among the most frequent real-bug transformations, while classical increment/decrement, removal of conditionals, or constructor mutations are rarely..."

**C7** [DERIVED] The documented PowerPC/EABI allocation policy favors caller-save registers and only falls back to callee-save registers when no caller-save is free. So a small source change that adds one more live value, or a call that forces values to survive across it, can push a variable from a caller-save register into a callee-save one, and the compiler then also has to save and restore that register in the prologue and epilogue. This is a general allocator rule, not a Metrowerks-specific finding, so how it applies to Metrowerks is an inference.
  - S9 <https://compcert.org/doc/html/compcert.powerpc.Conventions1.html> chars 3139-3252: "We favor the use of caller-save registers, using callee-save registers     only when no caller-save is available."

**C8** [DERIVED] Under the PowerPC EABI, where each argument lives depends on its type and its position in the list: the first 8 integer arguments go in R3 to R10, the first 8 float arguments in F1 to F8, and long integers take aligned register pairs. Extra arguments spill to consecutive stack slots, with floats taking 2 words and aligned. Changing one parameter's type or order can therefore shift every later argument into a different register or stack slot.
  - S9 <https://compcert.org/doc/html/compcert.powerpc.Conventions1.html> chars 7062-7127: "The first 8 integer arguments are passed in registers R3 to R10 ."

**C9** [DERIVED] The verifier project defines a match as requiring four things at once: identical code bytes apart from address fields, references that resolve to the same original targets, matching table contents, and identical unwind and exception-handling metadata. A function that looks identical instruction by instruction can still be reported as different because a referenced constant, vtable, or exception table differs, so 'perfect instruction match' is not the same as 'done'.
  - S10 <https://github.com/dmadevice/verifier> chars 1667-1711: "A function matches only when all of it does."
  - S10 <https://github.com/dmadevice/verifier> chars 1517-1666: "The data and metadata the code depends on (constants, string literals, tables, vtables, RTTI, unwind and exception-handling tables) are compared too."

**C10** [DERIVED] The verifier tolerates certain gaps: without an exported data-item list, a data object is compared only up to the rebuilt object's last nonzero byte, so a table with trailing zero entries or a truncated string still matches. Functions using the newer compressed exception-handling format cannot be verified and are reported as differences, and 32-bit or non-MSVC builds are unsupported. A reported match count can therefore be either overstated or understated depending on setup.
  - S10 <https://github.com/dmadevice/verifier> chars 7365-7546: "Without it, a data object is compared only up to the rebuilt object's last nonzero byte, so a table whose last entries the rebuild leaves zero, or a string cut short, still matches."
  - S10 <https://github.com/dmadevice/verifier> chars 21629-21712: "A function that uses it is reported as a DIFF whose handler data is not verifiable."

**C11** [DERIVED] The tool keeps a regression list of matched functions and, in check mode, fails the build when any listed function stops matching or when library code is wrongly counted as decompiled. This turns matching progress into a ratchet that can run in continuous integration, rather than a number someone re-measures by hand.
  - S10 <https://github.com/dmadevice/verifier> chars 2371-2551: "Once functions match, keep them matching with a regression list: add --matched matched.txt --update to record the current matches, and run with --matched matched.txt --check in CI."

**C12** [DERIVED] The ReCo paper (ACL 2024) reports that having an LLM rewrite the codebase itself to normalize style, in addition to generating example code for the query, boosts retrieval accuracy by up to 35.7% for sparse retrieval, 27.6% for zero-shot dense and 23.6% for fine-tuned dense. The gain comes from closing the stylistic gap between generated and real code. Nothing in the material tests this on mwcc or on older console toolchains, so whether it transfers to compiler-specific matching is unproven.
  - S13 <https://arxiv.org/abs/2401.04514> chars 1533-1758: "Experimental results demonstrate that ReCo significantly boosts retrieval accuracy across sparse (up to 35.7%), zero-shot dense (up to 27.6%), and fine-tuned dense (up to 23.6%) retrieval settings in diverse search scenarios."
  - S13 <https://arxiv.org/abs/2401.04514> chars 1137-1346: "This limitation could potentially be ascribed to the fact that the generated codes, albeit functionally accurate, frequently display a pronounced stylistic deviation from the ground truth code in the codebase."
  - _ledger: OBSERVED number(s) absent from verified spans: 2024_

**C13** [DERIVED] The Code2Code tool indexes 1,100,000+ snippets across 2,400+ repositories but supports only Python, C++, C, PHP, JavaScript, TypeScript, Lua, Go, Java and Rust. It finds code similar in meaning regardless of style, which differs from the exact byte or instruction matching that compiler-specific work needs. It says nothing about mwcc output or optimizer quirks, so it should not be counted on for that use.
  - S16 <https://diff.wikimedia.org/2026/04/14/introducing-mediawiki-code2code-search-semantic-search-to-find-code-by-under-the-surface-similarity/> chars 6174-6277: "Currently supported languages are Python, C++, C, PHP, JavaScript, TypeScript, Lua, Go, Java, and Rust."
  - S16 <https://diff.wikimedia.org/2026/04/14/introducing-mediawiki-code2code-search-semantic-search-to-find-code-by-under-the-surface-similarity/> chars 741-968: "You paste a piece of code that captures some behaviour, and the tool attempts to find similar code across MediaWiki extensions and the core, even if the programming language, coding style, variable names or exact syntax differ."

**C14** [DERIVED] Macabeus's benchmark of 60 functions from two real projects (Sonic Advance 3 on GBA and Animal Forest on N64, both non-Metrowerks) matched 74% on average across 6 runs using m2c, decomp-permuter and Claude Sonnet 4.6, with 88% of functions giving the same outcome every run. 12 functions always failed, so the ceiling is a stable set of hard functions, not luck. No GameCube/Wii Metrowerks-specific rate was reported in these sources, so applying 74% to Metrowerks code is an extrapolation.
  - S18 <https://gambiconf.substack.com/p/can-llms-really-do-matching-decompilation> chars 2806-2945: "Across 60 functions from two real decomp projects, the pipeline matches 74% functions, and 88% of them produce the same outcome every time!"
  - S18 <https://gambiconf.substack.com/p/can-llms-really-do-matching-decompilation> chars 16804-16878: "53 of the 60 functions (88%) had identical outcomes across all three runs."
  - _ledger: OBSERVED number(s) absent from verified spans: 12, 4.6_

**C15** [DERIVED] In the benchmark, nearly half of AI-phase matches came on the first attempt, and a function unmatched by attempt 3 had only about a one-quarter chance of eventually matching. The permuter mattered most on the IDO-compiled N64 game (matching 3-4 functions per run) and matched none on the ARM/GBA game, so permutation value depends on how well the tool supports the compiler. Metrowerks support was not measured in these sources.
  - S18 <https://gambiconf.substack.com/p/can-llms-really-do-matching-decompilation> chars 13788-13893: "Permuter likely worked better on AF because it was initially designed for IDO (the compiler used for AF)."
  - _ledger: OBSERVED number(s) absent from verified spans: spans carry no figure_

**C16** [DERIVED] None of the sources report a function-level match rate for Metrowerks-compiled code. They give project outcomes instead: Melee at 100% of 19,828 functions with 116 of 900 sampled commits carrying AI co-author lines, and Lewis estimating that without expert intervention (about 4.8% of commits) his Snowboard Kids project would have stalled around 89-90%. The wiki page that discusses CodeWarrior sets a 25-build cap as a standard but cites no measured rate. Judge any GameCube/Wii AI claim by who measured it and whether it counts functions or commits.
  - S19 <https://capitalandcompute.net/blog/which-games-has-ai-decompiled/> chars 4477-4626: "In a sample of 900 commits from June to October 2026, 116 carry AI co-author lines, most often Claude Fable 5, followed by Codex and Claude Opus 5.5."
  - S19 <https://capitalandcompute.net/blog/which-games-has-ai-decompiled/> chars 5635-5719: "Without that expertise, he estimates the project “would have stalled around 89–90%.”"

**C17** [DERIVED] Register allocation is an NP-complete problem that compilers solve only approximately, typically via graph coloring with heuristics for spilling and splitting. Because the result depends on heuristic ordering and priority rankings, tiny source changes can flip which values get which registers, so the match is a search over heuristic behavior rather than a deterministic translation.
  - S23 <https://www.geeksforgeeks.org/computer-organization-architecture/register-allocations-in-code-generation/> chars 627-724: "Therefore a good register allocator computes an effective approximate solution to a hard problem."
  - S23 <https://www.geeksforgeeks.org/computer-organization-architecture/register-allocations-in-code-generation/> chars 7485-7551: "Top-Down uses priority ranking to order all the constrained nodes."

**C18** [DERIVED] Values with long live ranges and many interfering neighbors (constrained nodes) are the hard cases, forcing spill or split decisions that depend on estimated execution frequency and spill cost. Functions heavy in such values are where small differences in the allocator's cost estimates produce visibly different register assignments and spill code.
  - S23 <https://www.geeksforgeeks.org/computer-organization-architecture/register-allocations-in-code-generation/> chars 6142-6238: "Live ranges having k or more neighbors are called constrained nodes and are difficult to handle."
  - S23 <https://www.geeksforgeeks.org/computer-organization-architecture/register-allocations-in-code-generation/> chars 4695-4828: "Essential for taking a spill decision which includes - address computation, memory operation cost, and estimated execution frequency."
