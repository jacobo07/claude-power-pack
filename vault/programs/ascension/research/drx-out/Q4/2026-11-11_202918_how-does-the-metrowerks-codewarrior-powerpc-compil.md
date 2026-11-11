# mwcc (GameCube/Wii) register allocation: state of the evidence

## 1. Bottom line

**The research behind this report did not answer your question.** It produced two learnings, both about process and compiler versioning. None covers:
- the allocator's internals,
- which source edits change allocation,
- decomp-permuter documentation,
- a graph-coloring order model.

I have no sourced, falsifiable claim of the form "with X, mwcc emits Y" for any of the factors you listed. Section 4 gives hypotheses I can offer from background knowledge. They carry no source from this research, so treat them as test candidates, not findings.

## 2. What the research did establish

| # | Claim | Tags | Source / ledger |
|---|---|---|---|
| C2 | The only quantified practice found is a cap of **25 builds per function**, cited as the Retrobench standard, with the diff output fed back each round. Agents without a cap thrash. | [DERIVED][MEDIUM] | S2 (specific figure) |
| C3 | Codegen is version-specific. Compiler versions across titles range **1.0 through 1.7**, and a flag mismatch makes every function unmatchable. | [DERIVED][MEDIUM] | S2 |

Implications, all [DERIVED][MEDIUM]:
- **Edit effects are found empirically per function.** The 25-build cap suggests no rulebook is reliable enough to skip trial-and-compare. This is an inference from the cap. S2 does not say it outright.
- **Version and flags are preconditions.** Any register-level result holds only for the same compiler version and flag set. Results from projects that differ in either shouldn't be compared. That includes `-O4,p` vs `-O4,s`, which are different flag sets.
- **S2 gives no per-edit data.** It reports no measurement for declaration order, temporaries, scope blocks, inlines, casts, or struct copies.

## 3. Coverage gaps

Nothing was found, so nothing can be tagged, on any of these:

| Question | Status |
|---|---|
| Allocator structure (priority, coloring order, spill heuristics) | **No evidence** |
| Effect of declaration order, first-use order, temporaries, scope blocks, inlining, casts, struct copies | **No evidence** |
| `-O4,p` vs `-O4,s` effect on allocation | **No evidence** |
| Decomp project guidance on regswaps (repo files, issues, PRs) | **No evidence** |
| decomp-permuter docs: which randomizations work for mwcc | **No evidence** |
| Any documented graph-coloring model of mwcc | **No evidence.** I can't say one doesn't exist, only that none was found. |
| Compiler manual statements on register use | **No evidence** |

## 4. Candidate hypotheses (not from research)

These come from my general background on mwcc and decomp practice. I did not verify them in this session and have no primary source for any. **None should be cited as established.** Each is written as a falsifiable pair, to be run on a pinned compiler build.

Tags: [HYPOTHESIS][UNVERIFIED].

| ID | Factor | With X, mwcc emits Y | With X', mwcc emits Y' |
|---|---|---|---|
| H1 | Declaration order | Locals declared A then B get nonvolatile registers in one order | Declared B then A, the assignment swaps (or doesn't, which falsifies the "order matters" claim) |
| H2 | First-use order | Variable first assigned early gets the higher-numbered nonvolatile (r31 side) | Reordering the first assignments swaps the pair |
| H3 | Temporaries | Introducing `T t = expr;` changes live ranges and can flip a swap | Inlined expression form gives the original allocation |
| H4 | Scope blocks | Wrapping a variable in `{ }` shortens its range and can free its register for reuse | Function-scope declaration keeps it live and distinct |
| H5 | Inline functions | Inlining adds temporaries, so allocation differs from a manual expansion | Manual expansion gives different assignment |
| H6 | Casts | A redundant cast alters the emitted instruction (e.g. extsb/extsh) and so the live-range shape | No cast gives the base allocation |
| H7 | Struct copies | Struct assignment vs member-wise copy yields different register choice for the temporaries | The alternate form flips it |
| H8 | `-O4,p` vs `-O4,s` | The two settings produce different allocation for the same source (my understanding: `p` favors speed, `s` favors size) | Same source under the other flag gives a different register assignment |

For each, the decisive test is to compile the pair with the identical pinned compiler and flags, then diff the assembly. A result that contradicts the stated Y or Y' falsifies the hypothesis. Because of C3, a result from one version says nothing about another.

## 5. Recommended protocol

1. **Pin the version and flags first.** Without that, no result is comparable [DERIVED][MEDIUM, per C3].
2. **Cap trial builds per function**, using 25 as a starting budget, and feed the diff back each round [DERIVED][MEDIUM, per C2].
3. **Run H1–H8 as a controlled micro-benchmark** on small functions. This would generate the missing evidence directly.
4. **Record results per version** so they accumulate into a rulebook.

## 6. Where to look for the missing primary sources

I have not opened any of these, so I don't know their contents.

- **decomp-permuter** (simonlindholm): README and its randomization/macro documentation, plus any mwcc-specific issues.
- **GameCube/Wii decomp project repos** (e.g. doldecomp, and projects such as Melee or Metroid Prime): contributor guides, "regswap" or "register allocation" notes, and closed PRs that cite a fix.
- **decomp.me**: scratches and discussion for mwcc register swaps.
- **Metrowerks CodeWarrior PowerPC manuals**: optimizer and `-opt` flag documentation.
- **Retrobench**: the source of the 25-build figure, to confirm the claim in S2.

Searching those for "regswap", "register allocation", "declaration order", and "mwcc" would be the most direct way to fill the gaps in Section 3.

## 7. Confidence summary

| Item | Confidence |
|---|---|
| 25-build cap and thrashing without it | Medium, from one source |
| Version range 1.0–1.7 and flag-mismatch unmatchability | Medium, from one source |
| Everything in Section 4 | Unverified, no source |
| Allocator model, permuter randomizations, per-edit effects | Not covered by research |

## Contradicciones detectadas

Ninguna. Las fuentes procesadas no se contradicen entre sí en los puntos extraídos. Esto no significa consenso del campo: significa que las fuentes que este run alcanzó coinciden.

## Sources

- <https://github.com/encounter/decomp-toolkit>
- <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/>

## Run metadata

- **Prompt:** How does the Metrowerks CodeWarrior PowerPC compiler (mwcceppc, GameCube/Wii versions) allocate registers, and what source changes deterministically change the allocation (variable declaration order, first-use order, temporaries, scope blocks, inline functions, casts, struct copies, -O4,p vs -O4,s)? What do decompilation projects and decomp-permuter documentation say about fixing register swaps (regswaps) on mwcc, which permuter randomizations work for mwcc, and is there any documented model of its graph-coloring order? For every claim give the primary source (repo file, issue, PR, compiler manual) and state it as a falsifiable prediction: 'with X, mwcc emits Y; with X', it emits Y''. Mark anything unverified.
- **Depth / breadth:** 2 / 4
- **Queries used:** 10 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 528.0 s
- **Errors during run:** 22
- **Started at:** 2026-11-11T19:29:18Z
- **Module version:** deep_research 0.4.1
- **Quality gates:** 0 query/queries rejected as keyword soup · 0 learning(s) dropped for containing code · 19 dropped as not operator-actionable (relevance: rated)
- **E1 decomposition:** 5/5 axes searched (BOUNDARY, COUNTEREXAMPLE, EVIDENCE, MECHANISM, TRANSFERABILITY)  — SHORTFALL: only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY; only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY; only 2 axis/axes covered (COUNTEREXAMPLE, MECHANISM) — minimum 3; missing: EVIDENCE, BOUNDARY, TRANSFERABILITY
- **E2 landscape:** B_ACADEMIC×12, C_PRACTITIONER×2, UNKNOWN×21 · 0 question(s) refused as vendor-only · 1 learning(s) killed by the coverage gate
- **E3 reality:** DERIVED 2 · 7 label(s) demoted by the evidence gates
- **E4 contradictions:** 0 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `THIN` / MEDIUM [EVIDENCE] — 2 source(s), families C_PRACTITIONER, UNKNOWN — _What measured evidence do decompilation projects for GameCube and Wii games give about whi_
- `THIN` / MEDIUM [MECHANISM] — 3 source(s), families B_ACADEMIC, UNKNOWN — _Why does the order in which a compiler assigns registers to local variables change when th_
- `THIN` / HIGH [BOUNDARY] — 5 source(s), families B_ACADEMIC, UNKNOWN — _What happens when a contributor fixes register allocation in one function with a source ed_
- `THIN` / HIGH [BOUNDARY] — 4 source(s), families B_ACADEMIC, UNKNOWN — _Why does a register swap that looks fixable by reordering declarations sometimes refuse to_
- `THIN` / MEDIUM [MECHANISM] — 2 source(s), families B_ACADEMIC, UNKNOWN — _Why does changing the order in which local variables are declared or used sometimes shift _
- `THIN` / MEDIUM [BOUNDARY] — 5 source(s), families B_ACADEMIC, UNKNOWN — _What happens to a function's register assignment when the function is large, holds many si_
- `THIN` / HIGH [TRANSFERABILITY] — 4 source(s), families B_ACADEMIC, UNKNOWN — _Does register allocation behavior and the set of effective fixes stay the same across diff_
- `THIN` / MEDIUM [MECHANISM] — 5 source(s), families B_ACADEMIC, UNKNOWN — _Why does the same source edit produce different register assignments when the compiler's i_
- `THIN` / MEDIUM [COUNTEREXAMPLE] — 5 source(s), families C_PRACTITIONER, UNKNOWN — _Which register-mismatch fixes that worked in one game's decompilation were reported to fai_

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `fetch_page 'https://deepwiki.com/encounter/decomp-toolkit/6-binary-analy...': page-fetch: https://deepwiki.com/encounter/decomp-toolkit/6-binary-analysis: HTTP Error 429: Too Many Requests`
- `fetch_page 'https://deepwiki.com/command-tab/awesome-gamecube-developmen...': page-fetch: https://deepwiki.com/command-tab/awesome-gamecube-development/2.3-reverse-engineering-and-decompilation-projects: HTTP Error 429: Too Many Requests`
- `fetch_page 'https://github.com/sh1ftmaker/decomp-research-ai...': page-fetch: https://github.com/sh1ftmaker/decomp-research-ai: HTTP Error 404: Not Found`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `decomposition narrow: only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY`
- `fetch_page 'https://www.sciencedirect.com/topics/computer-science/regist...': page-fetch: https://www.sciencedirect.com/topics/computer-science/register-allocation: HTTP Error 403: Forbidden`
- `fetch_page 'https://web.stanford.edu/class/archive/cs/cs143/cs143.1128/l...': page-fetch: https://web.stanford.edu/class/archive/cs/cs143/cs143.1128/lectures/17/Slides17.pdf: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1010)>`
- `epistemic demoted DERIVED -> HYPOTHESIS: ledger: no quote verified in any snapshot`
- `fetch_page 'https://www.csl.cornell.edu/courses/ece4750fa22/handouts/ece...': page-fetch: https://www.csl.cornell.edu/courses/ece4750fa22/handouts/ece4750-T08-ap-regrename-problems.pdf: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1010)>`
- `decomposition narrow: only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY`
- `fetch_page 'https://stackoverflow.com/questions/1102049/order-of-local-v...': page-fetch: https://stackoverflow.com/questions/1102049/order-of-local-variable-allocation-on-the-stack: HTTP Error 403: Forbidden`
- `fetch_page 'https://stackoverflow.com/questions/36298567/why-does-gcc-re...': page-fetch: https://stackoverflow.com/questions/36298567/why-does-gcc-reorder-the-local-variable-in-function: HTTP Error 403: Forbidden`
- `fetch_page 'https://web.stanford.edu/class/archive/cs/cs143/cs143.1128/l...': page-fetch: https://web.stanford.edu/class/archive/cs/cs143/cs143.1128/lectures/17/Slides17.pdf: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1010)>`
- `epistemic demoted OBSERVED -> HYPOTHESIS: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED; ledger: no quote verified in any snapshot`
- `epistemic demoted VERIFIED -> DERIVED: ledger: VERIFIED needs 2 independent lineages, verified spans cover 1`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `web_search 'Which commonly repeated rules of thumb a...': ddg: fetch failed: <urlopen error [WinError 10054] Se ha forzado la interrupción de una conexión existente por el host remoto>; brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`
- `fetch_page 'https://www.sciencedirect.com/topics/computer-science/regist...': page-fetch: https://www.sciencedirect.com/topics/computer-science/register-allocation: HTTP Error 403: Forbidden`
- `decomposition narrow: only 2 axis/axes covered (COUNTEREXAMPLE, MECHANISM) — minimum 3; missing: EVIDENCE, BOUNDARY, TRANSFERABILITY`

</details>


## Evidence ledger

- **Claims:** 21 · with a verified quote: 19 (rate 0.905)
- **Quotes:** 41 offered, 8 rejected (not verbatim / unknown source / length)
- **Sources:** 24 snapshots in 24 independent lineage(s); 0 URL(s) were byte-identical copies
- **Labels lowered by the ledger:** 3
- **Sources with instruction-like text (treated as data):** 0

**C1** [DERIVED] Neither source contains before-and-after measurements linking particular source edits to Metrowerks register choices, and neither names anyone who recorded such results. They describe the workflow (write code, compile, compare, repeat) and say the compiler's optimization decisions are 'less predictable', but offer no measured edit-to-register effects.
  - S2 <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/> chars 4676-4793: "Matching C for CodeWarrior is harder than for GCC because the compiler's optimization decisions are less predictable."

**C2** [DERIVED] The only quantified practice is a cap of 25 builds per function, cited as the Retrobench standard, with the diff output fed back each round. This implies that edit-to-register effects are discovered empirically per function, not applied from a known rulebook, and that uncapped agents thrash.
  - S2 <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/> chars 20921-20942: "Cap the build budget."
  - S2 <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/> chars 15802-15860: "Iterate until score 100 or until you have tried 25 builds."

**C3** [DERIVED] Codegen is version-specific, and a flag mismatch makes every function unmatchable. Compiler versions across titles range from 1.0 through 1.7, so any claim that an edit reliably changes register choice only holds within the same version and flag set.
  - S2 <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/> chars 15927-16019: "CodeWarrior's codegen is version-specific. A flag mismatch makes every function unmatchable."
  - S2 <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/> chars 3965-4054: "The versions used across titles range from 1.0 through 1.7, per decomp.wtf documentation."

**C4** [DERIVED] Allocators such as linear scan operate on a linear ordering of the program, and different orderings of the same control flow produce different live intervals with more or less overlap. Textual order versus depth-first order of the flow graph can therefore yield different register assignments for logically identical code, which is why reshuffled but equivalent source can change which registers locals receive.
  - S3 <https://pages.cs.wisc.edu/~horwitz/CS701-NOTES/5.REGISTER-ALLOCATION.html> chars 11464-11624: "Note also that for non-straight-line code, different linear representations can lead to different live ranges (some of which may have more overlap than others)."

**C5** [DERIVED] Usage-weighted allocators rank variables by estimated savings, scaled by loop nesting depth, and give registers to the highest scorers. Moving a use or definition in or out of a loop, or adding a use, changes the ranking and so changes which variables get registers and in what order. Chaitin-style graph coloring also picks spill candidates by a cost function that includes loop nesting and neighbor counts.
  - S3 <https://pages.cs.wisc.edu/~horwitz/CS701-NOTES/5.REGISTER-ALLOCATION.html> chars 9424-9469: "Choose the R values with the highest savings."
  - S4 <https://en.wikipedia.org/wiki/Register_allocation> chars 7659-7804: "Spill cost : compute the spill cost of each variable. This assesses the impact of mapping a variable to memory on the speed of the final program."

**C6** [DERIVED] Graph coloring is NP-hard, so allocators use heuristics that remove easy nodes onto a stack and then pop and color them in reverse order. Which node is pushed first, and which is chosen when none are easy, determines the final color assignment, and in the worked example one live range is left with no register at all. Anything that changes the graph, such as live-range structure, changes this order and the resulting assignment.
  - S3 <https://pages.cs.wisc.edu/~horwitz/CS701-NOTES/5.REGISTER-ALLOCATION.html> chars 19515-19547: "Note: This is an NP hard problem"
  - S4 <https://en.wikipedia.org/wiki/Register_allocation> chars 8337-8494: "When none remain, a variable is chosen to be removed (making it a spill candidate) and hopefully increasing the number of variables with degree less than r ."

**C7** [DERIVED] Allocation is computed per function (or per loop within it): liveness, interference graphs and coloring are built function by function, so a source edit that changes one function's allocation should not directly alter a neighbor's register assignment. Spillover to neighbors or the whole file must therefore come from shared factors such as calling conventions, stack layout or inlining, not from the allocator itself.
  - S7 <https://course.ccs.neu.edu/cs4410sp24/lec_register-alloc_notes.html> chars 10567-10792: "Iterate over every function in the now-annotated program.  For each function, iterate over every expression within it and build an interference graph whose nodes are variable names and whose edges are each pair of variables ("
  - S4 <https://en.wikipedia.org/wiki/Register_allocation> chars 538-653: "When done per function/procedure the calling convention may require insertion of save/restore around each call-site"

**C8** [DERIVED] Register assignment depends on heuristics (spill-cost choices, node ordering during coloring, linear ordering of blocks), so a minor edit can change which live range is spilled or which color each receives. Because the exact outcome is heuristic and the problem is NP-hard, a fix that makes one function match can plausibly alter results elsewhere, which means contributors should re-verify the whole file after each such edit.
  - S3 <https://pages.cs.wisc.edu/~horwitz/CS701-NOTES/5.REGISTER-ALLOCATION.html> chars 19515-19547: "Note: This is an NP hard problem"
  - S3 <https://pages.cs.wisc.edu/~horwitz/CS701-NOTES/5.REGISTER-ALLOCATION.html> chars 11464-11624: "Note also that for non-straight-line code, different linear representations can lead to different live ranges (some of which may have more overlap than others)."

**C9** [HYPOTHESIS] None of the retrieved material measures or reports how frequently an allocation fix in one function breaks a neighbor or the whole file; it covers compiler theory only (liveness, interference graphs, linear scan, graph coloring). The frequency question is unanswered here and needs project-level data.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C10** [DERIVED] Allocators decide register sharing by liveness (whether a value is still needed later), not by scope or declaration position. Reordering declarations or uses changes which variables are live at the same time, so a variable can lose its register, share one with another, or be spilled to memory where before it had a register.
  - S7 <https://course.ccs.neu.edu/cs4410sp24/lec_register-alloc_notes.html> chars 1067-1199: "if two variables are never needed simultaneously, then they can share the same location (whether that’s a stack slot or a register)."
  - S4 <https://en.wikipedia.org/wiki/Register_allocation> chars 1739-1866: "However, two variables in use at the same time cannot be assigned to the same register without corrupting one of the variables."

**C11** [HYPOTHESIS] When there are more simultaneously live variables than registers, the allocator spills some to RAM, which is slower. Register pressure is the count of simultaneously live variables at an instruction. A reorder that lengthens one variable's lifetime across others can push the count past the available registers, and x86 has only 8 general registers in 32-bit mode.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C12** [DERIVED] Optimal register allocation is NP-complete, so real allocators use heuristics such as graph-coloring with simplify ordering, or greedy linear scan that visits intervals in order of start point. Their outcomes depend on the order in which candidates are processed and on which one is chosen to spill, so small input changes can produce different assignments. Fixed-register constraints (such as parameters in R3-R10 on PowerPC) and aliasing on x86 add further sensitivity.
  - S4 <https://en.wikipedia.org/wiki/Register_allocation> chars 5291-5372: "Chaitin et al. showed that optimal register allocation is an NP-complete problem."

**C13** [DERIVED] Allocators can only share a register between values that are never needed at the same time, and when more values are live together than there are registers, some are pushed to memory (spilled). In a large function with many simultaneous values or inlined code, this shows up as extra stores and loads and shifted register choices that differ from the target, even when the logic is identical.
  - S7 <https://course.ccs.neu.edu/cs4410sp24/lec_register-alloc_notes.html> chars 9833-9993: "The key idea behind register allocation is to preserve the invariant that no two variables that are live at the same time can be allocated to the same location."
  - _ledger: VERIFIED needs 2 independent lineages, verified spans cover 1_

**C14** [DERIVED] Which value gets spilled is chosen by heuristics based on how constrained each value is and the estimated cost of spilling it, and the choice is global to the function. A small change in the number or lifetime of live values can therefore change which values are evicted and which registers everything else gets, producing widespread diffs from one root cause.
  - S15 <https://www.brainkart.com/article/Register-Allocation-and-Assignment_8105/> chars 1137-1204: "Cost of spilling will depend on frequencies and locations of uses."
  - S14 <https://www.brainkart.com/article/Register-Allocation-and-Assignment_8186/> chars 11196-11264: "A general rule is to avoid introducing spill code into inner loops."

**C15** [DERIVED] The same code can receive different register assignments depending on the allocation approach: graph coloring gives better code at higher compile cost, while linear scan is faster but greedy, and it ignores gaps in a value's lifetime and keeps spilled values spilled throughout. A mismatch on a large function may therefore reflect the allocator's design differences, not source-level differences.
  - S4 <https://en.wikipedia.org/wiki/Register_allocation> chars 22581-22651: "Besides, a spilled variable will stay spilled for its entire lifetime."
  - S4 <https://en.wikipedia.org/wiki/Register_allocation> chars 21182-21252: "The Hotspot server compiler uses graph coloring for its superior code."

**C16** [DERIVED] Register allocation outcomes depend on the allocation strategy and the architecture's constraints. PowerPC fixes ordinary values into pre-colored registers (parameters in R3-R10, return value in R3), and allocators differ in how they spill, coalesce and pick colors. This gives a reason to expect behavior to shift between compiler versions and settings, but nothing here covers GameCube/Wii compilers specifically, so the sameness question remains unanswered by these sources.
  - S4 <https://en.wikipedia.org/wiki/Register_allocation> chars 17038-17167: "The heuristics used for ordering of RN reduction, and modification of cost have a significant effect on the resulting allocation."

**C17** [DERIVED] Allocators decide using heuristic orderings: graph-coloring simplify removes nodes in some order and then picks a spill candidate when stuck, and the greedy allocator processes intervals in a priority queue by spill weight, evicting lower-weight occupants. Because outcomes depend on processing order and on eviction, a change in order or weights can flip which values get registers or spill, so identical source can yield different assignments across versions.
  - S19 <https://www.codermusings.com/register-allocation-compiler-guide/> chars 9029-9191: "If the current interval has a higher spill weight than the occupant of a desired register, the allocator kicks out the lower-priority interval and re-enqueues it."
  - S13 <https://www.geeksforgeeks.org/computer-organization-architecture/register-allocations-in-code-generation/> chars 7485-7615: "Top-Down uses priority ranking to order all the constrained nodes. (However, it colors the unconstrained nodes in arbitrary order)"

**C18** [DERIVED] Heuristic choices in the allocator are not local optimizations: the cost and ordering heuristics have a significant effect on the resulting allocation, and coalescing can both help and hurt colorability of the interference graph. A tweak that relieves pressure for one function can therefore worsen another, which explains fixes that break neighbors.
  - S4 <https://en.wikipedia.org/wiki/Register_allocation> chars 17038-17167: "The heuristics used for ordering of RN reduction, and modification of cost have a significant effect on the resulting allocation."
  - S4 <https://en.wikipedia.org/wiki/Register_allocation> chars 24464-24573: "Doing coalescing might have both positive and negative impacts on the colorability of the interference graph."

**C19** [DERIVED] Allocation is NP-complete in general and solved by approximation, and the guidance in the contents is to profile for spilling in hot loops rather than manually restructure code. Manual tuning targets an outcome that heuristic changes can undo.
  - S19 <https://www.codermusings.com/register-allocation-compiler-guide/> chars 16054-16191: "Unless profiling reveals spilling in hot loops, the allocator is almost certainly making better decisions than manual intervention would."
  - S13 <https://www.geeksforgeeks.org/computer-organization-architecture/register-allocations-in-code-generation/> chars 627-724: "Therefore a good register allocator computes an effective approximate solution to a hard problem."

**C20** [DERIVED] The SotN decomp wiki documents mismatch tricks that are explicitly platform-specific: a hidden no-op move that appears in PSP output but is compiled out on PSX, and a modulo pattern that is hard to recognise because PSX and PSP compile it differently. A fix that works on one target therefore cannot be assumed to work on another, so teams should expect to rediscover fixes for each compiler/platform combination rather than reuse a playbook wholesale.
  - S21 <https://mathisto.github.io/sotn-wiki/decomp/register-mismatch-tricks/> chars 1894-2017: "This gets compiled out of the code on PSX, so you won't see it there, but it can cause a lot of register mismatches in PSP."
  - S21 <https://mathisto.github.io/sotn-wiki/decomp/register-mismatch-tricks/> chars 711-754: "This is a harder one to find in PSX vs PSP."

**C21** [DERIVED] On the PSP build of SotN, a stray instruction (a value loaded into a register and never used) signalled that the original code was a modulo, and a redundant self-move was reproduced by adding and then subtracting a non-zero constant. Mismatches can therefore be caused by invisible compiler artifacts rather than by variable choice, and recognising them can resolve many a0/v0 mismatches at once.
  - S21 <https://mathisto.github.io/sotn-wiki/decomp/register-mismatch-tricks/> chars 1465-1569: "The "tell" on this situation is that we are loading 0x80 into v0 on PSP, but not doing anything with it."
  - S21 <https://mathisto.github.io/sotn-wiki/decomp/register-mismatch-tricks/> chars 2813-2885: "In a lot of cases, this also resolves a lot of a0/v0 mismatches as well."
