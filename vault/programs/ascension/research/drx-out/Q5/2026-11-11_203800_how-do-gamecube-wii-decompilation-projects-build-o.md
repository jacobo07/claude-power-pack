# Shared whole-program type models in GameCube/Wii decompilation (m2c, ctx.h, dtk, Ghidra/IDA)

## 0. Evidence status

**The research behind this report did not reach the primary sources your question requires.** None of the collected learnings cover `m2c --context`, `tools/m2ctx.py`, dtk's `symbols.txt` or `dwarf dump`, Ghidra/IDA type export, or mwcc diagnostics. The relevant learnings are only about:

- the SDK being shared across games
- toolchain pinning
- the "linked" completion milestone

The rest are organizational-governance claims that are tangential here.

Everything in §3 onward is therefore my background recall, not research findings. It is tagged `[HYPOTHESIS][UNVERIFIED]`. I cite repository locations only as places to check, not as confirmed citations. Treat every file path, flag name and error string there as a lead to verify, not a quote.

## 1. What the research established

| # | Claim | Tags | Source ledger |
|---|---|---|---|
| C1 | The Dolphin SDK is statically linked into every GC/Wii game. Once its functions match, remaining work is mostly game-specific. Separate SDK decompilations exist for the 2001 and 2004 versions (`dolsdk2001`, `dolsdk2004`), so version-specific shared code is a recognised reuse unit. No savings figure is given. | [DERIVED][MEDIUM] | S2, S3 |
| C2 | Matching depends on the exact CodeWarrior version and flags (versions span 1.0–1.7). A flag mismatch makes every function unmatchable. Such failures can look like wrong type guesses but are toolchain errors. The attribution to toolchain rather than types is my inference. | [DERIVED][MEDIUM] | S3 |
| C31 | Same C with different flags yields different bytes, so a stalled project may have a configuration problem, not a talent problem. The cheap diagnostic is to check the build against one already-matched function. The source does not address auto-exported type headers specifically. | [DERIVED][MEDIUM] | S39 |
| C32 | 90% function coverage can coexist with a failed ROM rebuild (data layout, literal pools, one stubborn function). Metrowerks C++ codegen is less predictable than N64 output, so "linked" is the honest completion measure. | [OBSERVED][MEDIUM] | S39 |

**Implication for your question [DERIVED][LOW, my synthesis]:** the SDK headers (`dolsdk2001`/`dolsdk2004`) are the natural bottom layer of any shared type model. Before attributing a mismatch to a wrong struct guess, rule out the toolchain: take one matched function and confirm the pinned compiler and flags reproduce it.

### Tangential governance learnings (included for completeness, low relevance)

- **C7 [DERIVED][LOW] (S8, S10):** centralize decisions whose consequences cross team boundaries and leave local what stays within one team. By analogy, a shared `ctx.h` is the cross-team artifact, and per-TU scratch types are local.
- **C8 [DERIVED][LOW] (S8, S10):** three symptoms map to three fixes. Repeated waits mean streamline review. Repeated identical exceptions mean formalize a local option. Inconsistent local changes causing handoff problems mean tighten the shared boundary. Queue length for shared teams is proposed as a health metric, with no threshold given.
- **C9 [HYPOTHESIS][LOW] (S10):** a central team doing all work becomes a bottleneck. The alternative is to have it maintain reusable patterns and coach, with autonomy measured as the share of work delivered without its direct help. This is a single practitioner's model with no measured outcomes.

Mapping these to decompilation (one maintainer owning all headers versus contributors adding structs locally) is analogy only. No source here tests it.

## 2. Gaps (stated plainly)

- No primary source was retrieved for m2c's context handling, flags, or output-type behavior.
- No source on dtk's symbol/split format, `dwarf dump`, or how `symbols.txt` types map to prototypes.
- No source on Ghidra or IDA type export, or on round-tripping to C headers.
- No source on mwcc diagnostic wording for the three errors you named.
- No measurement of which errors disappear with a shared context.

## 3. Recalled architecture of a shared type model

All items in this section are [HYPOTHESIS][UNVERIFIED].

1. **Single header tree.** Projects keep one `include/` tree (SDK headers, game headers) that every TU includes. Layout facts live in exactly one definition per struct. Check the project's `include/` and `configure.py` for the include paths and flags.
2. **Context file generation.** m2c needs a single self-contained C file, so projects ship a script (typically `tools/m2ctx.py`) that runs the C preprocessor over a chosen source file and writes `ctx.c`/`ctx.h`. Check `tools/` in the project.
3. **Inference loop.** Types are inferred by reading the binary:
   - Load/store width and signedness give the field type. `lbz`=u8, `lha`=s16, `lfs`=f32, `lfd`=f64.
   - Base-register offset gives the field offset.
   - Call-site argument registers give prototype arity and rough types.
   - `r3`/`r4` flowing into `lwz` at offsets means pointer.
   - A vtable pointer load followed by an indirect `bctrl` gives a virtual call.
   - Constant array strides (`mulli`, `slwi`+`add`) give `sizeof`.
4. **Feedback.** Rerun m2c with the updated context. Previously `unkN` or `s32` values become named, typed expressions.

## 4. m2c: `--context` behavior (recalled)

- [HYPOTHESIS][UNVERIFIED] `m2c --target ppc-mwcc-c --context ctx.c file.s` parses the context with pycparser. Struct definitions, global declarations, and function prototypes are then used to type arguments, returns, and member accesses.
- [HYPOTHESIS][UNVERIFIED] Without a context, unknown functions appear as `? func(?)` and values default to `s32`. Offsets appear as `unkN` fields.
- [HYPOTHESIS][UNVERIFIED] The context must be preprocessed because m2c does not resolve `#include`. This is why generation scripts exist.
- [HYPOTHESIS][UNVERIFIED] decomp.me scratches take a "context" field, and projects feed the same generated context into both m2c and the compile step, so m2c and mwcc see identical declarations.

## 5. dtk (decomp-toolkit) role (recalled)

All [HYPOTHESIS][UNVERIFIED]:

- `symbols.txt` records name, address, and attributes (`type:function`, `size:`, `scope:`). It carries **no struct layouts or prototypes**, only symbol metadata. It makes the symbol layer consistent across TUs, not the type layer.
- `splits.txt` assigns address ranges to TUs, fixing the TU boundaries that the shared headers must serve.
- `dtk dwarf dump` can reconstruct C-like declarations when a game shipped DWARF debug info. This is rare, and where present it is the best ground truth for struct layouts. Verify availability per game.

## 6. Ghidra / IDA export (recalled)

All [HYPOTHESIS][UNVERIFIED]:

- Both tools can export types as C headers (Ghidra's header export, IDA's Local Types). Output is usually not directly compilable by mwcc: it uses tool-specific typedefs (`undefined4`, `__int32`) and has no mwcc-specific conventions.
- Round-tripping therefore requires a normalization step (rename to `s32`/`u32`/`f32`, drop pragmas). This is where a hand-maintained header tree beats raw export.

## 7. Which errors should disappear with a shared context

Exact mwcc wording is unverified. Categories are inferred.

| Symptom | Likely cause | Shared context fixes it? |
|---|---|---|
| "pointer expected" / dereferencing an integer | Parameter typed `s32` instead of a pointer | Yes, if the prototype is in context [HYPOTHESIS][UNVERIFIED] |
| "not a struct/union" on `->` | Value typed as integer or `void*` | Yes, once the struct and typed parameter exist [HYPOTHESIS][UNVERIFIED] |
| "illegal operands" for `void* + int` | Pointer arithmetic on `void*` | Yes if a concrete pointee type is known; otherwise needs a cast [HYPOTHESIS][UNVERIFIED] |
| Wrong offsets or strides | Duplicated, divergent struct definitions | Yes, via a single definition [HYPOTHESIS][UNVERIFIED] |
| Whole-function mismatch with correct types | Wrong compiler or flags | **No.** Fix the toolchain (C2, C31) [DERIVED][MEDIUM] |

## 8. Falsifiable predictions

Each is `with X, mwcc emits Y; with X′, emits Y′`. **All are [HYPOTHESIS][UNVERIFIED]**: I have not run any of them. Fix compiler version and flags per C2 before testing.

| ID | X → Y | X′ → Y′ | How to falsify |
|---|---|---|---|
| P1 | Field `u8 a` at 0x0: load is `lbz` | Field `s8 a`: `lbz` + `extsb` | Compile both, diff the `.s` output |
| P2 | `u16` field: `lhz` | `s16` field: `lha` | Same |
| P3 | `f32` field: `lfs` | `f64` field: `lfd` | Same |
| P4 | `sizeof(T)==0x14`, indexing `arr[i]`: `mulli rN,rM,20` | `sizeof(T)==0x18`: `mulli rN,rM,24` | Change one pad field, recompile |
| P5 | Prototype `void f(Obj*)`, call passes pointer in `r3` | Prototype `void f(s32)` with a cast: same registers but different surrounding casts/extension | Compare surrounding instructions |
| P6 | C++ TU with the correct prototype: mangled name matches the original symbol in `symbols.txt` | Wrong parameter type: different mangled name, so unresolved or duplicate symbol at link | Run the link, inspect the map |
| P7 | C (not C++) TU with a wrong prototype: links fine, mismatch only at the instruction level | Same wrong prototype in C++: link failure | Compare the two builds |
| P8 | Same C, flags A: matches | Same C, flags B (e.g. inline/opt level changed): bytes differ (C31) | Build one matched function under both |
| P9 | m2c with `--context` containing the struct: output uses `obj->field` | m2c without context: `unkN` offsets or `s32` arithmetic | Run m2c twice on one `.s` |
| P10 | `void *p; p + 4` in strict C mode: diagnostic | Cast to `u8*` first: compiles | Compile both |

P6/P7 rest on a general C++ name-mangling property that I have not confirmed for this mwcc version.

## 9. Recommended next steps

1. **Verify toolchain first (C2, C31).** Compile one known-matched function and confirm identical bytes.
2. **Collect primary sources:**
   - m2c README and `--help`
   - A project's `tools/m2ctx.py`
   - dtk docs on `symbols.txt`
   - The Ghidra export documentation
   - The CodeWarrior manual's error-message appendix
3. **Run P1–P10** on a scratch (decomp.me or a local mwcc) and replace the tags with `[OBSERVED]` or drop the claim.
4. **Fuzzy tie-in [HYPOTHESIS][LOW]:** treat the SDK header tree (`dolsdk2001`/`dolsdk2004`) as the frozen shared base and add game-specific headers on top. Version-pin which SDK a game uses, since the two SDK versions are separate repos (C1).

I did not run any tools or builds for this report.

## Contradicciones detectadas

Ninguna. Las fuentes procesadas no se contradicen entre sí en los puntos extraídos. Esto no significa consenso del campo: significa que las fuentes que este run alcanzó coinciden.

## Sources

- <https://github.com/doldecomp>
- <https://github.com/orgs/doldecomp/repositories>
- <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/>
- <https://ones.com/blog/which-model-works-best-centralized-vs-team-owned-process-maintenance-after-a-standardized-project-process-rollout/>
- <https://www.geeksforgeeks.org/git/version-control-systems/>
- <https://vsra-community.org/2025/12/08/the-organizational-pendulum-why-software-teams-swing-between-centralization-and-decentralization/>
- <https://www.atlassian.com/git/tutorials/source-code-management>
- <https://initialrise.github.io/REWiki/04-recomp/matching-decomp/>
- <https://tanepiper.github.io/game-frame/consoles/matching-decomp>

## Run metadata

- **Prompt:** How do GameCube/Wii decompilation projects build one whole-program type model (struct layouts, field types, pointer vs integer, function prototypes) shared across translation units, inferred from how the binary uses each value (load/store widths and offsets, call arguments, vtables), and how do they keep m2c output (which types unknown values as s32/long or ?) consistent across TUs: m2c --context, ctx.h generation, Ghidra/IDA type export, dtk symbols, and which errors (pointer expected, not a struct/union, illegal operands void*+int) disappear with a shared context? For every claim give the primary source (repo file, issue, PR, compiler manual) and state it as a falsifiable prediction: 'with X, mwcc emits Y; with X', it emits Y''. Mark anything unverified.
- **Depth / breadth:** 2 / 4
- **Queries used:** 12 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip, empty-input
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 521.8 s
- **Errors during run:** 36
- **Started at:** 2026-11-11T19:38:00Z
- **Module version:** deep_research 0.4.1
- **Quality gates:** 0 query/queries rejected as keyword soup · 0 learning(s) dropped for containing code · 29 dropped as not operator-actionable (relevance: rated)
- **E1 decomposition:** 5/5 axes searched (BOUNDARY, COUNTEREXAMPLE, EVIDENCE, MECHANISM, TRANSFERABILITY)  — SHORTFALL: only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY; only 2 axis/axes covered (BOUNDARY, EVIDENCE) — minimum 3; missing: MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY; only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY; only 2 axis/axes covered (BOUNDARY, COUNTEREXAMPLE) — minimum 3; missing: EVIDENCE, MECHANISM, TRANSFERABILITY
- **E2 landscape:** B_ACADEMIC×4, C_PRACTITIONER×10, UNKNOWN×31 · 0 question(s) refused as vendor-only · 0 learning(s) killed by the coverage gate
- **E3 reality:** OBSERVED 1, DERIVED 5, HYPOTHESIS 1 · 12 label(s) demoted by the evidence gates
- **E4 contradictions:** 0 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `THIN` / MEDIUM [EVIDENCE] — 3 source(s), families C_PRACTITIONER, UNKNOWN — _What do GameCube and Wii decompilation repositories actually contain in their shared heade_
- `THIN` / MEDIUM [MECHANISM] — 4 source(s), families C_PRACTITIONER, UNKNOWN — _Why do some functions in a decompilation project stay unmatched even after the struct layo_
- `UNCLASSIFIED` / LOW [BOUNDARY] — 4 source(s), families UNKNOWN — _At what point does a shared, centrally maintained type model start slowing contributors do_
- `THIN` / MEDIUM [MECHANISM] — 5 source(s), families C_PRACTITIONER, UNKNOWN — _Why does the decompiler's output keep guessing plain integers for values that are really p_
- `THIN` / HIGH [EVIDENCE] — 3 source(s), families B_ACADEMIC, UNKNOWN — _What measured error rates do decompilation projects and published studies report for point_
- `THIN` / MEDIUM [BOUNDARY] — 5 source(s), families B_ACADEMIC, UNKNOWN — _At what point does supplying more type information, such as struct definitions, function p_
- `THIN` / MEDIUM [BOUNDARY] — 3 source(s), families C_PRACTITIONER, UNKNOWN — _What happens to compile errors and to byte-for-byte matching when the shared type definiti_
- `UNCLASSIFIED` / LOW [MECHANISM] — 3 source(s), families UNKNOWN — _What happens to a reconstructed program when one shared struct definition has the wrong fi_
- `THIN` / MEDIUM [BOUNDARY] — 3 source(s), families C_PRACTITIONER, UNKNOWN — _At what point does sharing one type definition across all files in a reconstructed codebas_
- `THIN` / MEDIUM [TRANSFERABILITY] — 5 source(s), families C_PRACTITIONER, UNKNOWN — _Do decompilation projects for other consoles or other compilers, such as those for the N64_
- `THIN` / MEDIUM [BOUNDARY] — 2 source(s), families C_PRACTITIONER, UNKNOWN — _What happens to a matching decompilation project when types exported automatically from a _
- `THIN` / MEDIUM [COUNTEREXAMPLE] — 5 source(s), families B_ACADEMIC, UNKNOWN — _Why do some decompilation projects that share type definitions across several game version_

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `fetch_page 'https://deepwiki.com/xbret/xenoblade/2.3-global-include-head...': page-fetch: https://deepwiki.com/xbret/xenoblade/2.3-global-include-headers-and-decompilation-macros: HTTP Error 429: Too Many Requests`
- `fetch_page 'https://deepwiki.com/encounter/decomp-toolkit...': page-fetch: https://deepwiki.com/encounter/decomp-toolkit: HTTP Error 429: Too Many Requests`
- `decomposition narrow: only 2 axis/axes covered (BOUNDARY, MECHANISM) — minimum 3; missing: EVIDENCE, COUNTEREXAMPLE, TRANSFERABILITY`
- `fetch_page 'https://deepwiki.com/alam0rt/breaking-the-mold/2.2-decompila...': page-fetch: https://deepwiki.com/alam0rt/breaking-the-mold/2.2-decompilation-workflow: HTTP Error 429: Too Many Requests`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 1082, 2047, 66.6%, 78.9%`
- `fetch_page 'https://blogs.embarcadero.com/maintainable-code-a-practical-...': page-fetch: https://blogs.embarcadero.com/maintainable-code-a-practical-guide-to-scaling-quality-in-large-teams/: HTTP Error 403: Forbidden`
- `epistemic demoted VERIFIED -> DERIVED: VERIFIED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `learning 0 unrated by relevance filter — kept, flagged UNRATED`
- `learning 1 unrated by relevance filter — kept, flagged UNRATED`
- `learning 2 unrated by relevance filter — kept, flagged UNRATED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `decomposition narrow: only 2 axis/axes covered (BOUNDARY, EVIDENCE) — minimum 3; missing: MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY`
- `fetch_page 'https://dl.acm.org/doi/10.1145/3708821.3733877...': page-fetch: https://dl.acm.org/doi/10.1145/3708821.3733877: HTTP Error 403: Forbidden`
- `fetch_page 'https://dl.acm.org/doi/10.1145/3733822.3764675...': page-fetch: https://dl.acm.org/doi/10.1145/3733822.3764675: HTTP Error 403: Forbidden`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 0.418, 130, 23400`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 0.361, 0.513, 0.523, 0.706`
- `source https://www.geeksforgeeks.org/compiler-design/type-checking- carries instruction-like text ['tool-or-exfil-request']; treated as data`
- `source https://learn.microsoft.com/en-us/cpp/c-language/function-pr carries instruction-like text ['tool-or-exfil-request']; treated as data`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted VERIFIED -> DERIVED: ledger: VERIFIED needs 2 independent lineages, verified spans cover 1`

</details>


## Evidence ledger

- **Claims:** 36 · with a verified quote: 36 (rate 1.0)
- **Quotes:** 62 offered, 2 rejected (not verbatim / unknown source / length)
- **Sources:** 41 snapshots in 41 independent lineage(s); 1 URL(s) were byte-identical copies
- **Labels lowered by the ledger:** 5
- **Sources with instruction-like text (treated as data):** 3

**C1** [DERIVED] The Dolphin SDK is statically linked into every GameCube and Wii game, so once its functions are matched the remaining unmatched work in a new game is mostly game-specific code. The community already runs separate SDK decompilations for the 2001 and 2004 versions, which implies version-specific shared code is a recognised unit of reuse, though the sources give no measure of how much time it saves.
  - S3 <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/> chars 5533-5653: "Once the SDK library is decompiled and matched, every new game's non-matched functions become mostly game-specific code."
  - S2 <https://github.com/orgs/doldecomp/repositories> chars 5424-5494: "A decompilation of the 4-20-2004 version of the Dolphin SDK Libraries."

**C2** [DERIVED] Matching depends on reproducing the exact CodeWarrior compiler version and flags used originally, and a flag mismatch makes every function unmatchable. Compiler versions across titles range from 1.0 to 1.7, so a project that has not pinned its toolchain will produce failures that look like wrong type guesses but are really toolchain errors.
  - S3 <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/> chars 15861-16019: "The key is giving the agent the exact compiler version and flags. CodeWarrior's codegen is version-specific. A flag mismatch makes every function unmatchable."

**C3** [HYPOTHESIS] None of the retrieved material describes the contents of the shared headers or context files, nor how often wrongly guessed types break a match. The sources show only repository listings and an AI-oriented overview, with a 25-build cap per function as a working convention, so the central question is unanswered. Open issue counts are small (melee 17, mkdd 2, sms 1), which suggests type problems are handled in pull requests and commits rather than tracked as issues.
  - S3 <https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/> chars 20943-21023: "25 builds per function is the Retrobench standard. Without a cap, agents thrash."

**C4** [DERIVED] Remaining byte differences fall into distinct categories that point to different causes: missing or extra instructions suggest branch or loop shape, wrong offsets suggest field layout or element size, and the same operations with different registers suggest declaration order or how long temporaries stay live. Different stack offsets or frame size point to local types, temporary structures or inlined helpers, so correct struct layouts do not rule out a mismatch. The guidance is to resolve instruction structure before operands, then register allocation, and not to rely on a percentage score alone.
  - S6 <https://www.retroreversing.com/decompilers> chars 17178-17295: "The matching workflow guide recommends resolving instruction structure before operands, then register allocation 12 ."
  - S6 <https://www.retroreversing.com/decompilers> chars 17391-17448: "These symptoms suggest experiments, not unique diagnoses:"

**C5** [DERIVED] A function can still differ from the original because of things outside its own body: inline helpers, per-file pragmas, compiler version and flags, literal pools, string and constant layout, and section placement. Function-level similarity does not establish that the rebuilt file or final image matches, so full-binary comparison is the real completion test. Instruction-only checkers can also miss data differences.
  - S6 <https://www.retroreversing.com/decompilers> chars 19812-19877: "Do not infer a complete rebuild from a function similarity score."
  - S6 <https://www.retroreversing.com/decompilers> chars 18343-18421: "A function is compiled in the context of its source file and included headers."

**C6** [DERIVED] The project's issue tracker lists sibling functions with similarity percentages, such as 78.9% and 66.6% between two large functions of 1082 and 2047 bytes, and tells workers that a conclusion reached on one usually holds for the rest. It adds the caveat to check which local owns the stack slot before copying a sibling's shape. This shows that unmatched leftovers are often tackled in families, and that retries of earlier failed attempts are queued with notes on what still differs.
  - S4 <https://github.com/HectorBailey/byte-tactics/issues/4863> chars 1040-1174: "a conclusion reached on one usually holds for the rest, though check which local owns the stack slot before copying a sibling's shape."
  - _ledger: OBSERVED number(s) absent from verified spans: 1082, 2047, 66.6%, 78.9%_

**C7** [DERIVED] The contents converge on one dividing line: centralize decisions that affect multiple teams (shared handoffs, controls, reporting, completion definitions) and leave local what stays within one team's work. A shared baseline with bounded local additions avoids both a central bottleneck and silent erosion of standards, which is the same risk as one fix breaking pieces others already rely on.
  - S8 <https://ones.com/blog/which-model-works-best-centralized-vs-team-owned-process-maintenance-after-a-standardized-project-process-rollout/> chars 5280-5399: "Centralize decisions that affect multiple teams; keep decisions local when their effects remain within one team’s work."
  - S10 <https://vsra-community.org/2025/12/08/the-organizational-pendulum-why-software-teams-swing-between-centralization-and-decentralization/> chars 6998-7090: "Consistency is critical (brand, accessibility, security, compliance) and variation is costly"

**C8** [DERIVED] Three distinct symptoms point to three different fixes: repeated waits for routine approval means streamline review; the same exception requested again and again means formalize a permitted local option; and handoff problems from inconsistent local changes mean tighten the shared boundary. Tracking queue length for shared teams is proposed as a standing health measure.
  - S8 <https://ones.com/blog/which-model-works-best-centralized-vs-team-owned-process-maintenance-after-a-standardized-project-process-rollout/> chars 15680-15832: "Look for repeated delays awaiting routine approval, recurring requests for the same exception, or handoff problems caused by inconsistent local changes."
  - S10 <https://vsra-community.org/2025/12/08/the-organizational-pendulum-why-software-teams-swing-between-centralization-and-decentralization/> chars 7983-8032: "Dependency health (queue length for shared teams)"

**C9** [HYPOTHESIS] When a central specialist team (the example is UX) does all work for every feature team, queues grow and it becomes a bottleneck. The proposed alternative is for the central team to maintain reusable patterns, coach other teams, and join temporarily only on novel work, with autonomy measured as the share of work delivered without its direct help.
  - S10 <https://vsra-community.org/2025/12/08/the-organizational-pendulum-why-software-teams-swing-between-centralization-and-decentralization/> chars 5030-5202: "If the UX team tries to do all the design work for every feature team, work will pile up, queues will grow, and the UX team will become a bottleneck under extreme pressure."
  - S10 <https://vsra-community.org/2025/12/08/the-organizational-pendulum-why-software-teams-swing-between-centralization-and-decentralization/> chars 7849-7911: "Autonomy signals (% features delivered without direct UX help)"

**C10** [VERIFIED] Decompilers label values by width only until told otherwise, so a pointer, an int and a float all appear as the same raw integer. Analysts who read these as real behavior end up describing bugs that are only the missing type. The decompiler's own signals (a pointer used as an integer for no reason) should trigger a check against the assembly, not a conclusion.
  - S16 <https://hackblue.org/learn/ghidra-data-types> chars 109-164: "Until you say otherwise, Ghidra labels values by width."
  - S15 <https://lazyhackers.com/article/asm-decompiler-output-mastery> chars 13754-13826: "The assembly is ground truth. The pseudocode is a guess layered over it."

**C11** [DERIVED] An angr bug report found many functions across two stripped binaries (Redis 7.4.2 and Lua 5.4.7) where pointer parameters came out as 64-bit integers, even when the body passed them to memset or strlen. Recovery was inconsistent even within one signature: in anetResolve, two char pointers were recovered correctly while an identically declared third was not. Results also changed depending on what else had been decompiled earlier in the session.
  - S12 <https://github.com/angr/angr/issues/6687> chars 3809-3911: "anetResolve shows that the pointer type is sometimes recovered and sometimes not within one signature:"
  - S12 <https://github.com/angr/angr/issues/6687> chars 4598-4703: "Decompiling several functions in one session changes what is recovered for the functions decompiled later"

**C12** [DERIVED] Fixing a type in one place propagates outward: correcting a recognized library call's signature fixes parameter types in every caller, and retyping a wrapper's return as a struct pointer lets callers be retyped from it. Loading shipped type archives is described as the single step that changes output the most. What must be known per value is the evidence from the instructions that touch it (how it is passed, which offsets and widths are accessed), so consistency comes from recording that decision once, not per file.
  - S15 <https://lazyhackers.com/article/asm-decompiler-output-mastery> chars 3496-3573: "Loading type information is the single step that changes the output the most."
  - S16 <https://hackblue.org/learn/ghidra-data-types> chars 1037-1071: "Let the instruction pick the type."

**C13** [DERIVED] On DecompileBench (23,400 functions from 130 OSS-Fuzz programs), each function was extracted and compiled in isolation, then decompiled. Hex-Rays led with an average recompile success of 0.583 and coverage equivalence of 0.418. LLM-refined outputs trailed it, with coverage equivalence lower by 17.2-52.2%, because the LLMs favour readability over strict compiler compatibility. This is an aggregate correctness measure and does not break out pointer-versus-integer or struct-versus-scalar type errors.
  - S18 <https://arxiv.org/html/2505.11340v1> chars 23648-23854: "Hex-Rays is recognized as the leading traditional decompiler, achieving the highest single optimization-level RSR of 0.706 at -O0 , and excelling in averaged metrics with an RSR of 0.583 and a CER of 0.417."
  - S18 <https://arxiv.org/html/2505.11340v1> chars 24269-24409: "However, these LLM-enhanced results still fall short of Hex-Rays’ original metrics, with RSR lower by 0.2-45.3% and CER lower by 17.2-52.2%."
  - _ledger: OBSERVED number(s) absent from verified spans: 0.418, 130, 23400_

**C14** [DERIVED] Every decompiler's correctness fell as compiler optimization rose. Hex-Rays' coverage equivalence went from 0.523 at -O0 to 0.361 at -O3, and its recompile success from 0.706 to 0.513. The authors highlight a 36.11% functionality correctness drop for Hex-Rays under -O3.
  - S18 <https://arxiv.org/html/2505.11340v1> chars 8166-8353: "Our key findings contain Hex-Rays’ 36.11% functionality correctness drop under -O3 optimizations, LLM’s significant readability improvement over Hexrays despite lower recompilation rates."
  - _ledger: OBSERVED number(s) absent from verified spans: 0.361, 0.513, 0.523, 0.706_

**C15** [DERIVED] The only substantive source retrieved, DecompileBench from Tsinghua (Zeyu Gao, Chao Zhang et al., 2025), scores type problems only qualitatively. It uses an LLM judge with 'Typecast Correctness' and 'Memory Layout' (failed type inference) criteria, validated against human raters at kappa 0.778. It reports no error rates for these specific type decisions. The other retrieved sources were unreadable (a raw PDF stream and a bot-check page).
  - S18 <https://arxiv.org/html/2505.11340v1> chars 7201-7443: "This automated approach, validated against expert ratings with κ \kappa =0.778 agreement, not only ranks decompilers but predicts their effectiveness for specific aspects in aiding the real-world reverse engineering tasks for reverse experts."

**C16** [DERIVED] Without complete prototypes, the compiler applies default conversions and makes no attempt to check argument types or counts. A mismatch can cause arguments on the stack to be misread, corrupting not only the mismatched parameter but all subsequent ones. So partial type information does not just leave errors unreported; it lets wrong code compile and misbehave at runtime.
  - S23 <https://learn.microsoft.com/en-us/cpp/c-language/function-prototypes?view=msvc-170> chars 1848-2002: "Without complete prototypes, standard conversions are made, but no attempt is made to check the type or number of arguments with the number of parameters."
  - S23 <https://learn.microsoft.com/en-us/cpp/c-language/function-prototypes?view=msvc-170> chars 2344-2454: "A type mismatch between an argument and a parameter may cause the arguments on the stack to be misinterpreted."

**C17** [DERIVED] Declaring a struct inside a function prototype makes the compiler scope it locally under strict ANSI mode, so the function can never be called without a type mismatch error. The fix is to declare the struct at global scope before the prototype. More type information therefore creates new mismatches when it is supplied in the wrong place or order, not only when it is wrong.
  - S23 <https://learn.microsoft.com/en-us/cpp/c-language/function-prototypes?view=msvc-170> chars 3982-4100: "If you declare a struct or union tag within a prototype, the tag is entered at that scope rather than at global scope."
  - S23 <https://learn.microsoft.com/en-us/cpp/c-language/function-prototypes?view=msvc-170> chars 4258-4364: "To correct your code, define or declare the struct or union at global scope before the function prototype:"

**C18** [DERIVED] A sound and decidable static checker must be incomplete, meaning it will reject some correct programs. Conversely, a program can pass the type checker and still fail at runtime, for example through division by zero. Reaching zero compiler errors is therefore a weak completion signal for reconstructed code, and the remaining defects must be found by testing or other analysis.
  - S22 <https://en.wikipedia.org/wiki/Type_system> chars 10668-10785: "In a type system with automated type checking, a program may prove to run incorrectly yet produce no compiler errors."
  - S22 <https://en.wikipedia.org/wiki/Type_system> chars 12597-12675: "Static type checking for Turing-complete languages is inherently conservative."
  - _ledger: VERIFIED needs 2 independent lineages, verified spans cover 1_

**C19** [DERIVED] GCC's feedback-profile mismatch check shows the tradeoff: when source files change between profiling and the final build, the compiler cannot use the profile. By default this is an error, but it can be downgraded, which risks poorly optimized code. The maintainers say this is acceptable only for very minor changes such as bug fixes, and that disabling the warning completely is not recommended, so stale shared data is tolerable only in a narrow band.
  - S27 <https://gcc.gnu.org/onlinedocs/gcc-9.2.0/gcc/Warning-Options.html> chars 9811-9980: "Disabling the error for this warning can result in poorly optimized code and is useful only in the case of very minor changes such as bug fixes to an existing code-base."

**C20** [DERIVED] Compilers detect errors, report them, and then try to recover so they can keep processing, and an undeclared identifier shows up as a missing symbol-table entry. A single missing shared definition therefore becomes an error in every file that uses it, and later errors may be recovery artifacts. GCC offers a limit on error count and an abort-on-first-error mode, which reflects that cascades are common enough to need controls.
  - S26 <https://www.geeksforgeeks.org/compiler-design/error-handling-compiler-design/> chars 1001-1095: "For example, using an undeclared identifier can result in a missing entry in the symbol table."
  - S27 <https://gcc.gnu.org/onlinedocs/gcc-9.2.0/gcc/Warning-Options.html> chars 1772-1922: "This option causes the compiler to abort compilation on the first error occurred rather than trying to keep going and printing further error messages."

**C21** [DERIVED] GCC separates warnings, which flag constructions that are not inherently erroneous but risky, from errors, and a warning does not stop the build unless it is promoted. Shared type definitions that are incomplete or contradictory may therefore compile cleanly while producing different behavior, so exact-match goals need a stricter bar than passing the build.
  - S27 <https://gcc.gnu.org/onlinedocs/gcc-9.2.0/gcc/Warning-Options.html> chars 216-368: "Warnings are diagnostic messages that report constructions that are not inherently erroneous but that are risky or suggest there may have been an error."
  - S27 <https://gcc.gnu.org/onlinedocs/gcc-9.2.0/gcc/Warning-Options.html> chars 960-990: "Make all warnings into errors."

**C22** [DERIVED] Padding is inserted automatically to satisfy alignment, so the total size of a structure is not the sum of its members. For the same members, reordering changes size from 24 bytes to 16 bytes, and turning padding off changes sizes from 4/8/24/16 to 3/7/13/13. A wrong width or padding assumption therefore compiles cleanly but yields a differently sized and shifted structure, which shows up as output or size differences rather than errors.
  - S30 <https://www.geeksforgeeks.org/c/structure-member-alignment-padding-and-data-packing/> chars 4740-4849: "Structure D is a good example, where reordering members reduces the structure size from 24 bytes to 16 bytes."
  - S30 <https://www.geeksforgeeks.org/c/structure-member-alignment-padding-and-data-packing/> chars 6132-6229: "Since padding is disabled, the structure size becomes the direct sum of the sizes of its members."

**C23** [DERIVED] Layout depends on the compiler's packing setting, which defaults to 8-byte packing in Microsoft's compiler and can be overridden per structure by directives. GCC also offers a Microsoft-compatible layout mode, and mixing its packing directive with its packed attribute may cause spurious warnings or unexpected behavior. Identical source can therefore produce different binaries depending on settings, so differences may come from build configuration rather than a reconstruction error.
  - S28 <https://learn.microsoft.com/en-us/cpp/c-language/storage-and-alignment-of-structures?view=msvc-170> chars 1731-1764: "The default packing size is /Zp8."

**C24** [DERIVED] Structures that must match external layouts need padding disabled to match exactly, so a reconstruction that leaves default padding in place will misread or misplace fields. Elsewhere a padding error mostly changes size and performance; here it corrupts data interpretation.
  - S30 <https://www.geeksforgeeks.org/c/structure-member-alignment-padding-and-data-packing/> chars 4868-5019: "Sometimes, structures must exactly match the layout of external data, such as file headers or network packets. In such cases, padding must be disabled."

**C25** [DERIVED] In a real codebase cleanup, a 'duplicate' Task type turned out to be two distinct types with different identifiers (text versus numeric), different extra fields, and different jobs: one for the external data contract and one for internal live state. The team deliberately kept both, deleted only the unused legacy third copy, and documented the split, with 1096 of 1096 tests passing. Forcing a merge would have created mismatches between what the outside world sends and what the internal system tracks.
  - S31 <https://github.com/frankbria/codeframe/issues/53> chars 15362-15403: "Two distinct Task types remain by design:"
  - S31 <https://github.com/frankbria/codeframe/issues/53> chars 15595-15665: "These serve different architectural purposes and should not be merged."

**C26** [DERIVED] The failure that prompted the Task cleanup was not the duplicate definitions themselves but one file pulling the Task type from the legacy location even though it defined its own, which created confusion about which version was authoritative. Consolidation effort is best aimed at finding such wrong-source usage rather than at collapsing every similar-looking definition.
  - S31 <https://github.com/frankbria/codeframe/issues/53> chars 2570-2641: "These are not true duplicates but distinct types for different domains."

**C27** [DERIVED] One engineer lost nearly three days trying to make a single shared build work for both the browser frontend and the Node backend, producing errors that looked random: runtime export-syntax failures, missing modules, and builds that passed but broke at runtime. The fix was one source of truth with separate builds per environment, so sharing works when the shared source is single but its delivery is split.
  - S32 <https://dev.to/aoda-zhang/making-a-typescript-shared-package-work-across-frontend-and-backend-in-a-monorepo-1k23/> chars 1407-1467: "After nearly three days of trial and error, it became clear:"
  - S32 <https://dev.to/aoda-zhang/making-a-typescript-shared-package-work-across-frontend-and-backend-in-a-monorepo-1k23/> chars 5023-5096: "Trying to fit all environments into a single artifact leads to conflicts."

**C28** [DERIVED] The general-purpose binary splitter used for N64, PS1, PS2 and PSP projects explicitly does not cover GameCube/Wii and redirects those projects to a separate dedicated toolkit. A GameCube/Wii effort therefore cannot reuse the N64/PS2 splitting workflow and its type and symbol configuration directly; it needs the GameCube/Wii-specific toolkit and its project template.
  - S34 <https://github.com/ethteck/splat> chars 1048-1109: "Currently, only N64, PSX, PS2 and PSP binaries are supported."
  - S34 <https://github.com/ethteck/splat> chars 1852-1884: "For Gamecube / Wii projects, see"
  - _ledger: VERIFIED needs 2 independent lineages, verified spans cover 1_

**C29** [DERIVED] The matching-decompilation process is the same across consoles; what changes per platform is the compiler to reproduce, with Metrowerks CodeWarrior versions named for GameCube versus SGI IDO for many N64 titles and GCC from PsyQ for PlayStation. Type and structure naming happens after matching begins, so the shared type model grows incrementally from generic names rather than being imported up front, and the compiler's sensitivity to statement order and register use is what makes it slow.
  - S36 <https://tanepiper.github.io/game-frame/consoles/matching-decomp> chars 670-901: "Find the exact compiler and version the game was built with: SGI IDO 5.3 or 7.1 for many N64 games, GCC 2.x versions from the PsyQ SDK for the PlayStation, Metrowerks CodeWarrior versions for the GameCube, Microsoft's for the Xbox."
  - S36 <https://tanepiper.github.io/game-frame/consoles/matching-decomp> chars 1694-1825: "Matching code starts with generic names. The project then names variables, structures and functions, as in any reverse engineering."

**C30** [DERIVED] The first-draft C generator used in matching projects targets MIPS and PowerPC (plus ARM and SuperH), so N64/PS2 and GameCube/Wii efforts can share that stage even though their splitters differ. The shared layer is therefore the draft decompiler, diffing and browser-matching tools, not the splitter or type configuration.
  - S37 <https://decomps.net/tools> chars 1018-1072: "A decompiler targeting MIPS, PowerPC, ARM, and SuperH."
  - S36 <https://tanepiper.github.io/game-frame/consoles/matching-decomp> chars 1331-1453: "Tools give a first draft (m2c), and decomp.me lets many people try candidate C against the original compiler in a browser."

**C31** [DERIVED] A flag mismatch makes every function unmatchable and looks like a source-code problem, so a stalled project may be a configuration problem rather than a talent or effort problem. Checking the build against one already-matched function is the cheap diagnostic before blaming the people or the code.
  - S39 <https://initialrise.github.io/REWiki/04-recomp/matching-decomp/> chars 7601-7710: "Do not guess flags blindly. A flag mismatch makes every function unmatchable and looks like a source problem."

**C32** [OBSERVED] A project can reach 90 percent function coverage and still fail to rebuild the final ROM because of data layout, literal pools, or one stubborn function. For GameCube and Wii work with Metrowerks CodeWarrior, matching is harder than on N64 because C++ code generation is less predictable, so the 'linked' milestone is the honest completion measure.
  - S39 <https://initialrise.github.io/REWiki/04-recomp/matching-decomp/> chars 3264-3415: "A project can sit at 90 percent function coverage and still fail to link the final ROM because of data layout, literal pools, or one stubborn function."
  - S39 <https://initialrise.github.io/REWiki/04-recomp/matching-decomp/> chars 20345-20413: "Matching is harder than N64 because C++ codegen is less predictable."

**C33** [DERIVED] Compilers of that era are sensitive to statement order, temporary variable types and register use, and some functions take days to match. Automated type exports are therefore a first draft that still needs manual tuning, not a finished input. Neither source describes the specific header constructs that break matching, so the question as posed remains unanswered here.
  - S36 <https://tanepiper.github.io/game-frame/consoles/matching-decomp> chars 2181-2338: "Compilers of the time are sensitive to the order of statements, the types of temporary variables and the use of registers. Some functions take days to match."

**C34** [DERIVED] In matching decompilation, a header change ripples into every function compiled against it, so a edit that fixes one function can silently break previously matched code. This coupling is the concrete mechanism that makes one shared header costly to keep across several versions or titles, and it pushes contributors toward private copies where changes cannot break others.
  - S6 <https://www.retroreversing.com/decompilers> chars 21620-21728: "After changing shared types or prototypes, rebuild affected code and verify previously matched functions too"

**C35** [DERIVED] Matching results depend on the compiler, flags, per-file pragmas and inline helpers, so the same type definition can need different treatment in different builds. A shared header that must satisfy several toolchains and versions accumulates conflicts, which is a plausible reason projects copy headers instead of sharing them.
  - S6 <https://www.retroreversing.com/decompilers> chars 18907-18961: "These are compiler- and version-dependent experiments."
  - S6 <https://www.retroreversing.com/decompilers> chars 18422-18532: "The CodeWarrior guide highlights inline helpers, local declarations and per-file pragmas as matching variables"

**C36** [DERIVED] Types are lost in compilation and recovered by heuristics, so struct layouts in a project's headers are educated guesses that get revised as work continues. A shared header encoding guesses made for one title can be wrong for another, so each project tends to correct its own copy.
  - S6 <https://www.retroreversing.com/decompilers> chars 8879-8906: "Type recovery is heuristic."
  - S6 <https://www.retroreversing.com/decompilers> chars 15289-15339: "Treat decompiler output as an editable hypothesis."
