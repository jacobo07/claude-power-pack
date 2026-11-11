# mwcceppc residual-asm idioms: status report

## 1. Bottom line

**The research returned no source↔asm pairs.** The four learnings I received cover matching *process* (flags, budgets, partial matching). None covers a specific mwcceppc idiom, and none gives a repo file, issue, PR, decomp.me scratch or compiler-manual citation for any of your ten topics.

I will not invent citations. Section 2 reports what the research established, with its tags. Section 3 lists candidate predictions from my own recall. They carry a different tag, `[UNVERIFIED][MODEL-RECALL]`, because they have no retrieved primary source and must not be read as research findings. Section 4 is a plan to close the gap.

## 2. What the research established

| # | Claim | Tags | Source ref |
|---|---|---|---|
| C2 | A public PS2 CodeWarrior repository stores its rewrite knowledge as a ledger of 24 public source revisions, with technical contrasts, caveats, allocation worksheets and evidence templates. It states that current project instructions and actual per-unit compiler settings take precedence, and that no historical experiment was rerun. | [DERIVED][MEDIUM] | S3 |
| C3 | A flag mismatch makes every function unmatchable and looks like a source problem. Confirm the compiler and flags on a known-matched function before blaming a rewrite. A low rewrite success rate may therefore reflect configuration, not the rewrite. The confound for rewrite-effect statistics is the researchers' own inference. | [DERIVED][MEDIUM] | S2 |
| C10 | Agent-driven workflows cap attempts per function (Retrobench uses 25 builds). Humans hit diminishing returns on hard functions. The stop decision is a pre-set budget, keeping the best partial result and reporting the first remaining mismatch. | [DERIVED][MEDIUM] | S2 |
| C11 | Unmatched functions commonly stay as included assembly so the program still links. Function-level progress is tracked separately from linked-ROM progress. A project can sit at about 90% function coverage and still fail to link because of one stubborn function. | [VERIFIED][MEDIUM] | S2, S15 |

**What these mean for your question**

- C2 matters most. The PS2 repo is not mwcceppc (PS2 uses a different CodeWarrior target), so its recipes are not evidence for GameCube/Wii behavior. It does show the right storage format: each idiom claim should carry compiler version and per-unit flags.
- C3 means every prediction below is conditional on a fixed build (compiler build, `-O4,p` or `-O4,s`, `-inline`, `-fp`, `-sched`, and so on). A "failed" prediction under the wrong flags falsifies nothing.
- Evidence quality is MEDIUM throughout, and the only [VERIFIED] item is about project workflow, not compiler behavior.

## 3. Candidate predictions (not research findings)

**Tag meaning:** `[UNVERIFIED][MODEL-RECALL]` means I recall the behavior from general knowledge of mwcc output. No primary source was retrieved, and I cite none. Confidence is my own estimate. Treat each row as a hypothesis to test, not a fact.

Format: *with X, mwcc emits Y; with X′, it emits Y′.*

| Topic | Prediction | Confidence (my estimate) |
|---|---|---|
| char/short/bool casts | With `(unsigned char)x`, mwcc emits `clrlwi rA,rB,24`. With `(signed char)x`, it emits `extsb`. With `(unsigned short)x`, it emits `clrlwi rA,rB,16`. With `(short)x`, it emits `extsh`. A `bool` store or return normalizes like `unsigned char` (mask 24). | High |
| int→float | With signed `(float)i`, it emits `lis rT,0x4330; xoris rI,rI,0x8000; stw` of both words to the stack; `lfd` of that double; `lfd` of the magic constant 0x4330000080000000 from a literal pool; then `fsub`/`fsubs`. With `(float)u` (unsigned), the `xoris` is absent and the subtracted constant is 0x4330000000000000. | High on shape, medium on exact register/slot order |
| float→int | With `(int)f`, it emits `fctiwz fT,fS; stfd fT,off(r1); lwz rD,off+4(r1)`. | High |
| `frsp` | With a double-typed intermediate assigned to a float (or an explicit `(float)` cast on a double expression), it emits `frsp`. With all-float operands and single-precision ops (`fadds`/`fmuls`), there is no `frsp`. Unsuffixed float literals promote to double, which forces `frsp` and double-width ops. | Medium-high |
| fmadds | With `a*b + c` in float and contraction enabled, it emits `fmadds`. With `#pragma fp_contract off` (or a flag disabling it), it emits `fmuls` then `fadds`. Parenthesization or splitting into two statements may change whether it fuses. | Medium |
| Operand order | With `a + b` versus `b + a`, commutative ops may swap source registers. Swapping source operand order is the first thing to try. | Medium (hypothesis) |
| Extra/missing `mr` | A temporary variable, a parameter reassigned, or a different declaration order can add or remove an `mr` because register assignment follows variable and live-range order. | Low-medium (hypothesis) |
| Loops | With a counted loop with a known/invariant trip count at `-O4,p`, it may emit `mtctr`/`bdnz`, and may unroll small constant counts. With a loop whose counter is used in the body or has a non-trivial exit, it may emit a compare/branch form. Loop rotation (test at the bottom) is the default shape at higher optimization. | Medium |
| Switch | With dense case values, it emits a jump table (`lis/addi` base, `slwi`, `lwzx`, `mtctr`, `bctr`). With sparse or few cases, it emits a compare chain or binary search. I do not have reliable thresholds. | Medium on shape, low on thresholds |
| if/else, ternary | Branch layout (which side falls through) follows source order. A ternary may compile differently from an equivalent if/else, but I recall no firm rule. | Low |
| Early return vs single exit | Early returns may duplicate `blr` or the epilogue where a single-exit form shares it. The effect is likely sensitive to optimization level. | Low (hypothesis) |
| `volatile` | With `volatile` accesses, each read or write is emitted and not merged or reordered across the access. | High on principle |
| Inline asm | An `asm` function body is emitted as written, with no optimization of its contents. | High on principle |

## 4. Gaps and next steps

- **Gap 1: no primary sources.** For every row in section 3, no repo file, issue, PR, scratch URL or manual page was retrieved. Do not cite section 3 as documented.
- **Gap 2: version scope.** mwcceppc builds differ (GC 1.x vs Wii 1.x builds). No retrieved evidence says which row holds on which build (relates to C2).
- **Gap 3: thresholds.** Switch jump-table cutoffs, unroll limits and branch-layout rules are unquantified.
- **Gap 4: negative results.** Nothing retrieved records rewrites that did *not* work. Ledgers like the PS2 one (C2) are the model to copy.

**Suggested verification protocol (my proposal)**

1. Pin the compiler build and flags using a known-matched function first (C3).
2. For each row, write a minimal C file for X and X′, compile with mwcceppc, and diff the objdump output. This is the cheapest falsification test for the "with X … with X′" predictions.
3. Record each result as: compiler build, flags, source pair, asm pair, pass/fail.
4. Search the doldecomp-style project repos for the matching asm pattern. Cite the file and commit only after reading it.
5. Cap time per unresolved idiom (C10) and leave stubborn functions as included assembly (C11).

If you want, I can build the minimal test harness from step 2 once you tell me which mwcceppc build and flags you use.

## Contradicciones detectadas

Ninguna. Las fuentes procesadas no se contradicen entre sí en los puntos extraídos. Esto no significa consenso del campo: significa que las fuentes que este run alcanzó coinciden.

## Sources

- <https://initialrise.github.io/REWiki/04-recomp/matching-decomp/>
- <https://github.com/Raikaru/MWCCPS2-Matching-Techniques>
- <https://decomp-academy.dev/courses/gba/lesson/gba-foundations-what-is-matching>
- <https://decomp-academy.dev/courses/n64-c/lesson/foundations-what-is-matching>
- <https://www.charles.systems/teaching/Decompilation_Shmecompilation.pdf>
- <https://grokipedia.com/page/Matching_Decompilation>

## Run metadata

- **Prompt:** Which C source idioms make mwcceppc (CodeWarrior for PowerPC, GameCube/Wii) emit specific residual assembly patterns that block matching: swapped operand order, an extra or missing mr, clrlwi/rlwinm masks from char/short/bool casts, extsh/extsb, branch layout of if/else and ternaries, loop rotation and unrolling, switch jump tables vs compare chains, int<->float conversion sequences (0x43300000 magic, frsp, fctiwz), fmadds contraction, inline asm and volatile effects, and early-return vs single-exit? Collect documented source<->asm pairs from decomp projects, decomp.me scratches and the decomp community wiki. For every claim give the primary source (repo file, issue, PR, compiler manual) and state it as a falsifiable prediction: 'with X, mwcc emits Y; with X', it emits Y''. Mark anything unverified.
- **Depth / breadth:** 2 / 4
- **Queries used:** 8 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 428.9 s
- **Errors during run:** 26
- **Started at:** 2026-11-11T19:20:29Z
- **Module version:** deep_research 0.4.1
- **Quality gates:** 0 query/queries rejected as keyword soup · 0 learning(s) dropped for containing code · 8 dropped as not operator-actionable (relevance: rated)
- **E1 decomposition:** 4/5 axes searched (BOUNDARY, COUNTEREXAMPLE, EVIDENCE, MECHANISM)  — SHORTFALL: only 2 axis/axes covered (EVIDENCE, MECHANISM) — minimum 3; missing: BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY; only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY
- **E2 landscape:** B_ACADEMIC×2, C_PRACTITIONER×4, UNKNOWN×10 · 0 question(s) refused as vendor-only · 0 learning(s) killed by the coverage gate
- **E3 reality:** VERIFIED 1, DERIVED 3 · 6 label(s) demoted by the evidence gates
- **E4 contradictions:** 0 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `UNCLASSIFIED` / LOW [MECHANISM] — 1 source(s), families UNKNOWN — _Why does the CodeWarrior PowerPC compiler lay out if/else and ternary branches, rotate or _
- `THIN` / MEDIUM [EVIDENCE] — 2 source(s), families C_PRACTITIONER — _What measured evidence do matching-decompilation teams have on how often a given source re_
- `THIN` / HIGH [MECHANISM] — 4 source(s), families B_ACADEMIC, UNKNOWN — _Why does the order in which a compiler assigns registers and schedules instructions make a_
- `UNCLASSIFIED` / LOW [BOUNDARY] — 1 source(s), families UNKNOWN — _When do known source-level tricks for coaxing the CodeWarrior compiler into the target ass_
- `THIN` / MEDIUM [MECHANISM] — 3 source(s), families C_PRACTITIONER, UNKNOWN — _Why does changing a single line of C source, like reordering a local variable declaration _
- `THIN` / MEDIUM [BOUNDARY] — 5 source(s), families C_PRACTITIONER, UNKNOWN — _What happens to a matching decompilation effort when a function stays a few instructions o_

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `web_search 'What documented pairs of original-lookin...': ddg: 0 hits parsed (possible block or empty SERP); brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`
- `fetch_page 'https://github.com/MarkMcCaskey/decomp-scripts/blob/main/mwc...': page-fetch: https://github.com/MarkMcCaskey/decomp-scripts/blob/main/mwcc-compiler-notes.md: HTTP Error 429: Too Many Requests`
- `fetch_page 'https://www.nxp.com/docs/en/reference-manual/CWMCUPABTR.pdf...': page-fetch: https://www.nxp.com/docs/en/reference-manual/CWMCUPABTR.pdf: HTTP Error 404: Not Found`
- `fetch_page 'https://www.nxp.com/docs/en/user-guide/CWPADBGUG.pdf...': page-fetch: https://www.nxp.com/docs/en/user-guide/CWPADBGUG.pdf: HTTP Error 404: Not Found`
- `fetch_page 'https://manualzz.com/doc/o/1ewl4v/metrowerks-3.2-c-compilers...': page-fetch: https://manualzz.com/doc/o/1ewl4v/metrowerks-3.2-c-compilers-reference-manual-powerpc-pragmas: HTTP Error 403: Forbidden`
- `decomposition narrow: only 2 axis/axes covered (EVIDENCE, MECHANISM) — minimum 3; missing: BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY`
- `fetch_page 'https://dl.acm.org/doi/full/10.1145/3708821.3733877...': page-fetch: https://dl.acm.org/doi/full/10.1145/3708821.3733877: HTTP Error 403: Forbidden`
- `fetch_page 'https://deepwiki.com/simdecomp/sims1_mac_decomp/2.3-compilat...': page-fetch: https://deepwiki.com/simdecomp/sims1_mac_decomp/2.3-compilation-and-matching-verification: HTTP Error 429: Too Many Requests`
- `fetch_page 'https://www.researchgate.net/publication/392359955_Binary-So...': page-fetch: https://www.researchgate.net/publication/392359955_Binary-Source_Code_Matching_Based_on_Decompilation_Techniques_and_Graph_Analysis: HTTP Error 403: Forbidden`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `fetch_page 'https://engineeringhulk.com/cs-it/compiler-design/code-gener...': page-fetch: https://engineeringhulk.com/cs-it/compiler-design/code-generation/: HTTP Error 403: Forbidden`
- `epistemic demoted DERIVED -> HYPOTHESIS: ledger: no quote verified in any snapshot`
- `fetch_page 'https://www.nxp.com/docs/en/user-guide/CWAPPTM.pdf...': page-fetch: https://www.nxp.com/docs/en/user-guide/CWAPPTM.pdf: HTTP Error 404: Not Found`
- `fetch_page 'https://support.arm.com/documentation/dui0065/d/configuring-...': page-fetch: https://support.arm.com/documentation/dui0065/d/configuring-a-build-target/configuring-assembler-and-compiler-language-settings/configuring-the-compilers: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1010)>`
- `fetch_page 'https://www.nxp.com.cn/docs/en/application-note/AN4094.pdf...': page-fetch: https://www.nxp.com.cn/docs/en/application-note/AN4094.pdf: HTTP Error 404: Not Found`
- `fetch_page 'https://retrocomputing.stackexchange.com/questions/14927/whe...': page-fetch: https://retrocomputing.stackexchange.com/questions/14927/when-and-why-did-high-level-language-compilers-start-targeting-assembly-language: HTTP Error 403: Forbidden`
- `source https://support.novell.com/techcenter/articles/dnd19990101.h carries instruction-like text ['tool-or-exfil-request']; treated as data`
- `decomposition narrow: only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY`
- `fetch_page 'https://stackoverflow.com/questions/36298567/why-does-gcc-re...': page-fetch: https://stackoverflow.com/questions/36298567/why-does-gcc-reorder-the-local-variable-in-function: HTTP Error 403: Forbidden`

</details>


## Evidence ledger

- **Claims:** 12 · with a verified quote: 10 (rate 0.833)
- **Quotes:** 19 offered, 4 rejected (not verbatim / unknown source / length)
- **Sources:** 15 snapshots in 15 independent lineage(s); 0 URL(s) were byte-identical copies
- **Labels lowered by the ledger:** 2
- **Sources with instruction-like text (treated as data):** 2

**C1** [DERIVED] The only stated measurement tied to attempts is a budget: the Retrobench benchmark allows 25 builds per function, and human decompilers allow more for hard functions but see diminishing returns. No source publishes how often a given rewrite changes the emitted PowerPC instructions, so the per-rewrite effect rate is effectively unmeasured in this material and the real control lever is the attempt cap.
  - S2 <https://initialrise.github.io/REWiki/04-recomp/matching-decomp/> chars 10898-11052: "Cap the attempts. Retrobench uses 25 builds per function as a budget. Human decompers often allow more for hard functions, but diminishing returns set in."

**C2** [DERIVED] One public repository for the PS2 CodeWarrior compiler records its rewrite knowledge as a ledger of 24 public source revisions with technical contrasts and caveats, plus allocation worksheets and evidence templates. It explicitly says current project instructions and actual per-unit compiler settings take precedence over the recipes, and that no historical experiment was rerun, so the recipes are not guaranteed to transfer across compiler versions.
  - S3 <https://github.com/Raikaru/MWCCPS2-Matching-Techniques> chars 3432-3515: "Current project instructions and actual per-unit compiler settings take precedence."
  - S3 <https://github.com/Raikaru/MWCCPS2-Matching-Techniques> chars 3246-3356: "No historical compiler experiment, C consumer, retail-image build or PS2 execution was rerun for this edition."

**C3** [DERIVED] The community guidance is that a flag mismatch makes every function unmatchable and looks like a source problem, so the compiler and flags must be confirmed on a known-matched function before attributing a failure to a rewrite. This means a low success rate for rewrites can reflect configuration, not the rewrites themselves.
  - S2 <https://initialrise.github.io/REWiki/04-recomp/matching-decomp/> chars 7601-7710: "Do not guess flags blindly. A flag mismatch makes every function unmatchable and looks like a source problem."

**C4** [DERIVED] Register reuse creates artificial ordering constraints (write-after-read and write-after-write) that disappear if different registers are chosen, so whichever allocation the compiler lands on directly limits how instructions can be reordered. A change that shifts register assignment in one place therefore changes what the scheduler is allowed to move in another, and the reverse also holds.
  - S6 <https://www.cosmiclearn.com/compilerdesign/instruction-scheduling.php> chars 8894-9008: "Unlike RAW dependencies, WAR dependencies are not fundamental to the math. They are an artifact of register reuse."

**C5** [VERIFIED] Optimal register allocation is NP-complete, and optimal basic-block scheduling is also NP-complete, so compilers use greedy heuristics (graph coloring with spill candidates, list scheduling with priority picks). In the scheduling walkthrough, a priority tie between two ready instructions is broken arbitrarily, so a small upstream change can reorder the whole result.
  - S7 <https://en.wikipedia.org/wiki/Register_allocation> chars 5291-5372: "Chaitin et al. showed that optimal register allocation is an NP-complete problem."
  - S6 <https://www.cosmiclearn.com/compilerdesign/instruction-scheduling.php> chars 12943-13040: "Finding the absolute mathematically optimal schedule for a basic block is an NP-Complete problem."

**C6** [HYPOTHESIS] Global schedulers pick a hot trace and treat it as one block, duplicating tails so control never enters mid-trace, and they insert compensation code on exits. Software pipelining restructures a loop into prologue, kernel and epilogue with an initiation interval set by the larger of resource and recurrence bounds. So changing a hot path or one loop dependency can alter block layout and loop shape well away from the edit.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C7** [DERIVED] Compilers are only obliged to preserve single-threaded behavior, so a build change can alter instruction order or cache a value in a register without any source change. In the cited scenario, a team upgraded GCC from 11.4 to 13.2 with no source or CPU change, and code that had run in production for nine months began reading stale data. The right response is to audit for unsynchronized shared state rather than blame the new compiler.
  - S11 <https://wendajiang.github.io/area/blog/memory_ordering_at_compile_time> chars 1079-1143: "Thou shalt not modify the behavior of a single-threaded program."

**C8** [HYPOTHESIS] Code that ran 14 hours without anomalies on x86 servers began corrupting data within 90 seconds on ARM-based Graviton2 production machines, because x86 hides ordering bugs that ARM exposes. A similar contrast was reported for a litmus test: roughly 4.9% anomalies on ARM versus 0.15% on x86. Test results on one processor family say little about another.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C9** [VERIFIED] Compiler barriers and volatile only constrain the compiler, not the processor, so they are insufficient on multicore machines. Atomic types constrain both layers at once, which is why they are the correct construct for cross-thread synchronization. Choosing atomics up front avoids a costly diagnosis later.
  - S11 <https://wendajiang.github.io/area/blog/memory_ordering_at_compile_time> chars 4407-4464: "A compiler barrier is not enough on any CPU architecture."
  - S10 <https://learn.padho.ai/wiki/instruction-reordering-by-cpu-and-compiler> chars 1955-2125: "volatile only stops the compiler half, fences only stop the CPU half, and std::atomic (or equivalent in your language) is the only construct that constrains both at once."

**C10** [DERIVED] Agent-driven matching workflows cap attempts per function (one benchmark uses 25 builds), and the guidance notes that human decompilers allow more for hard functions but hit diminishing returns. The practical consequence is that the stop decision is made by a pre-set budget, with the best-scoring partial result kept, rather than by feel.
  - S2 <https://initialrise.github.io/REWiki/04-recomp/matching-decomp/> chars 10898-11052: "Cap the attempts. Retrobench uses 25 builds per function as a budget. Human decompers often allow more for hard functions, but diminishing returns set in."

**C11** [VERIFIED] Projects leave unmatched functions as included assembly so the rest of the program still links and builds, and they track function-level progress separately from the fully linked result. A project can sit at 90 percent function coverage and still fail to link the final ROM because of one stubborn function, so the unmatched remainder is a visible, bounded debt rather than a stall.
  - S15 <https://grokipedia.com/page/Matching_Decompilation> chars 15869-15965: "Unmatched functions commonly remain as included assembly so the rest of the program still links,"
  - S2 <https://initialrise.github.io/REWiki/04-recomp/matching-decomp/> chars 3264-3415: "A project can sit at 90 percent function coverage and still fail to link the final ROM because of data layout, literal pools, or one stubborn function."

**C12** [DERIVED] Some projects accept relaxed matches (equivalent under a looser comparison) and near-finished projects have included functions that were functionally the same but not byte-identical. Tooling also exists specifically for the plateau after 99 percent, such as classifying the mismatch and injecting outside leads rather than letting the agent random-walk, and permutation search is described as most useful once only register allocation remains. This implies the last few instructions need a different method, not just more iterations.
  - S15 <https://grokipedia.com/page/Matching_Decompilation> chars 4597-4715: "Near-finished projects have included functions that were not byte-for-byte identical yet were "functionally the same.""
  - S2 <https://initialrise.github.io/REWiki/04-recomp/matching-decomp/> chars 2814-2907: "The function matches under a relaxed comparison, for example with different register choices."
