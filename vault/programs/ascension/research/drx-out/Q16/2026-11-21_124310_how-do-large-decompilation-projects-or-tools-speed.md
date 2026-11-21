# Speeding up mass compile-and-diff loops for mwcc: what the research supports, and what it does not

## 0. Bottom line

**The research did not answer most of your question.** The learnings contain no repo URLs, licences, measured invocation costs, throughput figures, or primary sources (repo file, issue, PR, compiler manual) for mwcc, wibo, objdiff, decomp-permuter, compile caches or ninja. The usable material is two indirect findings about where cost sits (filesystem boundaries and Wine startup) and several project-management findings about match-rate plateaus and verification. Everything specific to mwcc tooling in section 4 comes from my background knowledge, not from the research, and is unverified.

Tag legend: `[EPISTEMIC][SOURCE-QUALITY]` as delivered. Items marked **[UNVERIFIED-BACKGROUND]** are mine, carry no research backing, and should not be treated as findings.

---

## 1. Per-invocation cost: where it plausibly comes from

### 1.1 Filesystem boundary (WSL2 and similar)

- **[DERIVED][LOW]** File-heavy tools that cross a translation boundary (Linux tools reading Windows drives via WSL2) slow down because of the boundary, not the tool. The range is roughly 2x to 10x or worse. Moving the project to the native filesystem matters more than configuration tuning. (Ledger C4, source S8.)
- **[DERIVED][LOW]** Applying this to compiler and permuter loops is my inference, not something S8 states. A compile-heavy loop would plausibly gain more from file placement than from faster machines.
- **Relevance to your environment:** you are on Windows 11 with PowerShell and Bash. If mwcc runs under WSL, or Linux-side tooling reads `C:\...` through `/mnt/c`, this is the first thing to check.

**Falsifiable prediction (hypothesis, untested):**
- With the source tree and temp dir on the WSL2 ext4 filesystem, mwcc (under wibo or wine) emits a `.o` byte-identical to the one emitted with the tree on `/mnt/c`, and wall time per invocation is lower.
- With a second compiler build or hardware change but the tree still on `/mnt/c`, the byte output is unchanged and the wall time stays dominated by boundary cost.
- Byte-identity is the safe part (same inputs, deterministic compiler). The speedup magnitude is the unverified part.

### 1.2 Wine startup cost

- **[DERIVED][LOW]** Wine startup passes through the host dynamic loader, a Unix-side ntdll, creation of Windows process structures, connection to a separate server process, and mapping of a Windows-side ntdll. S7 traces these stages but gives no timings. (Ledger C5, source S7.)
- **[DERIVED][LOW]** Each compile launched by an automated loop pays this setup. Per-invocation overhead, not just compile speed, plausibly explains the gap versus native Windows. This link is inferred, not measured.

**Falsifiable prediction (hypothesis, untested):**
- With a persistent Wine server and prefix already running, per-launch wall time of a trivial mwcc invocation is lower than with a cold server. Output bytes are identical.
- With a lighter loader (the wibo approach below), the same holds, with the caveat that compatibility gaps could make it fail rather than just run differently.

**Gap:** there are no measured milliseconds per invocation for native Windows, wine, or wibo anywhere in the research. Any "wibo is N times faster" number would be unsourced.

---

## 2. Verification as the real accelerator

These findings concern AI-driven decompilation projects, not mwcc specifically. Several do not even use the same compiler (the Snowboard Kids project uses SGI IDO). They bear on loop design, not on invocation cost.

### 2.1 Byte-exact checking replaces review machinery

- **[DERIVED][MEDIUM]** The Modern Warfare 2 rebuild went from an error-ridden ~80% (fabricated or deleted logic, needing a reviewer agent) to 83% byte-exact once correctness was judged by byte-for-byte comparison with the original compiler's output. That removed the need for the review agent, let cheap models (Haiku, Luna) carry the work, and cut cost substantially. (Ledger C18, source S32.)
- **Figures:** 83% of all functions byte-matched, 99% with source, 600-700 billion tokens (about 300 billion on the cheap Luna model). All self-reported by the developer.
- **Takeaway:** a mechanical pass/fail oracle beat elaborate parallel tooling. This argues for investing in the compile-and-diff step itself (fast, deterministic, cacheable) rather than in more agents.

**Falsifiable prediction:** with a byte-compare oracle in the loop, a candidate C function that compiles to bytes equal to the target is accepted; with the oracle replaced by LLM review, accepted candidates include some whose bytes differ. This is stated by the developer for MW2, not independently reproduced.

### 2.2 Plateaus and the limits of automation

- **[DERIVED][MEDIUM]** Snowboard Kids (2,145 functions, 100% in about 83 days): roughly 4.8% of matching commits (about 41) involved expert intervention. The developer estimates matching would have stalled around 89-90% without IDO experts. Snowboard Kids 2 stalled twice (25% to 58%, then about 75%) and needed community members for its last 10 functions, taking 596 days. (Ledger C19, S32.)
- **[DERIVED][LOW]** The same figures are repeated in S40 (Ledger C25): 4.8% (about 41 commits), the 89-90% plateau and the 25%/58%/75% stall pattern. This is the same claim from a second source, but the 4.8% and the plateau are the developer's rough estimates, not measured values.
- **[DERIVED][LOW]** In the MW2 rebuild, leftover functions would not match however often they were revised. The developer attributes this to nondeterministic compiler behavior and an inability to reproduce the linker step that merges identical functions. They stopped at 83% after an estimated 600-700 billion tokens. The code is unpublished and unverifiable by third parties, and the source is single and self-reported. (Ledger C24, S32.)

**Implication for permuter farms:** these plateaus are what large permuter or compute farms would hit. The evidence suggests the last functions are limited by expertise, linker behavior and compiler determinism, not by compile throughput. This is an interpretation. No source in the research tested farm scaling.

**Falsifiable prediction (low confidence):**
- With easiest-first automated processing, match rate rises quickly and then stalls (the SK2 pattern at about 75%).
- With added specialist intervention on the remaining functions, the stall breaks. Doubling compute alone is predicted not to break it. Nothing in the research tests the compute-only arm.

### 2.3 Completion percentages are not comparable

- **[DERIVED][LOW]** Three units circulate: matched bytes of total code (Melee, 100%), matched functions of all functions (MW2, 83%), and functions with any source regardless of match (MW2, 99%). Halo shows 99.5% in one README versus 23.25% on a public tracker. (Ledger C26, S32.)
- **[DERIVED][LOW]** S38 independently explains that Halo's 99.5% is an optional verification build, not completion (the tracker shows 7.17%). The two sources do not agree on the tracker figure (23.25% vs 7.17%). I cannot resolve which is correct or current.
- **Practical rule:** do not quote or compare a match percentage without its denominator and verifier.

---

## 3. Coverage of your specific questions

| Topic you asked about | Research finding | Status |
|---|---|---|
| mwcceppc native vs wibo vs wine, per-invocation cost | Wine startup stages (S7), no timings; filesystem boundary effect (S8) | Thin; no measurements |
| Compile result caches | None | **Gap** |
| objdiff CLI batch / library | None | **Gap** |
| Parallel / distributed permuter farms | Only indirect: plateaus suggest compute is not the binding limit | **Gap**; inference only |
| Incremental ninja builds | None | **Gap** |
| Repo URLs, licences | None | **Gap** |
| Measured throughput | None | **Gap** |
| Primary sources (file/issue/PR/manual) | None for tooling claims | **Gap** |

---

## 4. [UNVERIFIED-BACKGROUND] Leads to check

These are from my memory, not from the research. I have not verified URLs, licences or behavior, and I could have details wrong. Treat them as a checklist for primary-source verification.

| Component | Likely repo | Licence (from memory, verify) |
|---|---|---|
| decomp-permuter | github.com/simonlindholm/decomp-permuter | Believed permissive; verify `LICENSE` |
| objdiff | github.com/encounter/objdiff | Believed MIT/Apache-2.0; verify |
| wibo | github.com/decompals/wibo | Verify |
| ninja | github.com/ninja-build/ninja | Apache-2.0 |
| ccache | github.com/ccache/ccache | GPL-3.0-or-later (verify) |
| decomp.me | github.com/decompme/decomp.me | Verify |

Ideas worth testing, each with a falsifiable form (all untested hypotheses):

1. **Content-addressed compile cache keyed on (preprocessed source, flags, compiler binary hash).**
   - With the cache, mwcc emits `.o` bytes B for a given key, and a second request with an identical key returns the same B without invoking mwcc.
   - Caveat from section 2.2: if mwcc output is nondeterministic for some inputs (as MW2's developer claims for their compiler, which I cannot confirm is mwcc), the cache would pin one outcome. Test determinism first by compiling the same input many times and comparing hashes.
2. **Cache at the permuter level.** Permuters generate many candidate sources that preprocess identically after normalization. Hashing the post-preprocessing text should skip redundant compiles. Prediction: with a hash-dedup layer, the number of mwcc invocations drops while the set of distinct output bytes is unchanged.
3. **objdiff as a library versus a CLI subprocess.** Prediction: in-process diffing avoids per-candidate process-spawn cost, and the diff result (score) is identical to the CLI's for the same pair of objects. Spawn cost matters more under Windows or Wine-adjacent setups. Unmeasured.
4. **Batch compiles in one Wine session** (a long-lived worker that receives file lists). Prediction: output bytes are identical to one-shot invocation, and amortized startup falls. Risk: mwcc may keep no cross-invocation state, so verify there is no leakage between compiles.
5. **ninja incremental builds** only help when dependency tracking is accurate. Prediction: with correct depfiles, editing one header rebuilds only dependents; with missing depfiles, stale objects pass the diff incorrectly. Check how the project's `configure.py` emits deps.
6. **Native-filesystem build directory and tmpfs for scratch output.** This follows from the 2x-10x boundary finding in section 1.1.

---

## 5. Recommended next research steps

1. Benchmark yourself on your machine: hyperfine over 200 invocations of a trivial mwcc compile under (a) native Windows, (b) wibo, (c) wine with warm server, (d) WSL2 on ext4 vs `/mnt/c`. Record median and p95. This closes the biggest gap and produces the measured numbers the research lacks.
2. Run a determinism test: compile one input 100 times per configuration and compare SHA-256 of the outputs. This tells you whether caching and farm dedup are safe.
3. Read primary sources: the permuter's README and its scorer and compile code, objdiff's CLI and library docs, and the wibo README for known gaps, then record the file and line for each claim.
4. Treat any throughput figure you encounter without a stated machine, compiler version and flags as unusable, in line with the denominator rule in section 2.3.

---

## 6. Confidence summary

- **Highest confidence:** a mechanical byte-exact oracle simplifies the loop (MEDIUM, self-reported).
- **Medium-low:** plateau patterns and the role of expertise (estimates, single-developer sources).
- **Low:** the cost model for Wine and the filesystem boundary (qualitative, no timings, inferred to apply).
- **No evidence:** caches, objdiff batching, permuter farm scaling, ninja behavior, licences, URLs.

## Contradicciones detectadas

Ninguna. Las fuentes procesadas no se contradicen entre sí en los puntos extraídos. Esto no significa consenso del campo: significa que las fuentes que este run alcanzó coinciden.

## Sources

- <https://arcanenibble.com/notes-on-wine-architecture-and-process-startup.html>
- <https://www.howtogeek.com/your-wsl2-projects-are-running-much-slower-because-you-put-them-on-the-windows-filesystem/>
- <https://khimananda.com/blog/incremental-and-parallel-builds-explained>
- <https://xenospectrum.com/en/decompilation-match-rate-melee/>
- <https://devblogs.microsoft.com/cppblog/faster-c-iterative-builds-with-github-copilot/>
- <https://heldgames.com/guides/games-100-percent-decompiled-what-next>
- <https://f4decomp.com/>
- <https://aisignal.day/en/ai-game-decompile-howto-2026/>
- <https://heldgames.com/guides/retro-decompilation-recompilation-explained>

## Run metadata

- **Prompt:** How do large decompilation projects or tools speed up mass compile-and-diff loops for mwcc: running mwcceppc natively or under wibo/wine with lower per-invocation cost, compile result caches, objdiff CLI in batch or as a library, parallel/distributed permuter farms, incremental ninja builds? Give repo URLs, licences and any measured invocation cost or throughput. For every claim give the primary source (repo file, issue, PR, compiler manual) and state it as a falsifiable prediction: 'with X, mwcc emits Y; with X', it emits Y''. Mark anything unverified.
- **Depth / breadth:** 2 / 4
- **Queries used:** 12 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 401.3 s
- **Errors during run:** 45
- **Started at:** 2026-11-21T11:43:10Z
- **Module version:** deep_research 0.4.1
- **Quality gates:** 0 query/queries rejected as keyword soup · 0 learning(s) dropped for containing code · 19 dropped as not operator-actionable (relevance: rated)
- **E1 decomposition:** 4/5 axes searched (BOUNDARY, COUNTEREXAMPLE, EVIDENCE, MECHANISM)  — SHORTFALL: only 2 axis/axes covered (EVIDENCE, MECHANISM) — minimum 3; missing: BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY; only 2 axis/axes covered (BOUNDARY, EVIDENCE) — minimum 3; missing: MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY; only 2 axis/axes covered (EVIDENCE, MECHANISM) — minimum 3; missing: BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY; only 2 axis/axes covered (BOUNDARY, EVIDENCE) — minimum 3; missing: MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY
- **E2 landscape:** B_ACADEMIC×5, C_PRACTITIONER×4, D_VENDOR×1, UNKNOWN×32 · 0 question(s) refused as vendor-only · 0 learning(s) killed by the coverage gate
- **E3 reality:** DERIVED 7 · 16 label(s) demoted by the evidence gates
- **E4 contradictions:** 0 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `THIN` / HIGH [EVIDENCE] — 3 source(s), families B_ACADEMIC — _What per-invocation time and throughput do decompilation projects actually measure when th_
- `THIN` / MEDIUM [EVIDENCE] — 3 source(s), families C_PRACTITIONER, UNKNOWN — _How long does a single Metrowerks compiler invocation actually take on native Windows, und_
- `UNCLASSIFIED` / LOW [MECHANISM] — 2 source(s), families UNKNOWN — _Why does process startup and filesystem translation make the same Windows compiler binary _
- `UNCLASSIFIED` / LOW [MECHANISM] — 5 source(s), families UNKNOWN — _Why does launching a 32-bit Windows compiler under a compatibility layer cost so much per _
- `UNCLASSIFIED` / LOW [EVIDENCE] — 3 source(s), families UNKNOWN — _What measured timings have people published for launching an old 32-bit Windows compiler t_
- `UNCLASSIFIED` / LOW [BOUNDARY] — 4 source(s), families UNKNOWN — _When a compiler is kept alive and reused across many compilations instead of being restart_
- `THIN` / MEDIUM [BOUNDARY] — 4 source(s), families C_PRACTITIONER, D_VENDOR, UNKNOWN — _What happens to the correctness of cached or incrementally rebuilt compile results when co_
- `UNCLASSIFIED` / LOW [EVIDENCE] — 5 source(s), families UNKNOWN — _What measured evidence exists on how often a build that reuses cached or previously compil_
- `UNCLASSIFIED` / LOW [MECHANISM] — 1 source(s), families UNKNOWN — _Why does a compile that looks identical to a previous one sometimes get treated as the sam_
- `THIN` / MEDIUM [COUNTEREXAMPLE] — 3 source(s), families C_PRACTITIONER, UNKNOWN — _Which projects ignored the elaborate speedup machinery and still reached high match rates _
- `THIN` / HIGH [EVIDENCE] — 4 source(s), families B_ACADEMIC, UNKNOWN — _What do decompilation contributors report about how much time and compute they actually sp_
- `UNCLASSIFIED` / LOW [BOUNDARY] — 5 source(s), families UNKNOWN — _What happens to the final few percent of a game rebuild when the original compiler's outpu_

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `fetch_page 'https://dl.acm.org/doi/full/10.1145/3708821.3733877...': page-fetch: https://dl.acm.org/doi/full/10.1145/3708821.3733877: HTTP Error 403: Forbidden`
- `fetch_page 'https://windowsforum.com/news/decomp-dev-shuts-its-public-le...': page-fetch: https://windowsforum.com/news/decomp-dev-shuts-its-public-leaderboard-as-ai-slop-disrupts-matching-decompilation.448883/: HTTP Error 403: Forbidden`
- `epistemic demoted DERIVED -> HYPOTHESIS: ledger: no quote verified in any snapshot`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `decomposition narrow: only 2 axis/axes covered (EVIDENCE, MECHANISM) — minimum 3; missing: BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY`
- `fetch_page 'https://deepwiki.com/mkst/mwccgap/2.3-compiler-and-assembler...': page-fetch: https://deepwiki.com/mkst/mwccgap/2.3-compiler-and-assembler-wrappers: HTTP Error 429: Too Many Requests`
- `fetch_page 'https://deepwiki.com/ttkb-oss/metrowrap/3.2-compiler-wrapper...': page-fetch: https://deepwiki.com/ttkb-oss/metrowrap/3.2-compiler-wrapper-(srccompiler.rs): HTTP Error 429: Too Many Requests`
- `extract_learnings: llm-parse: no valid JSON in 2627 chars; head: '{"learnings":[{"capability":"You can stop assuming that the choice of Windows, Wine, or wibo to run the old compiler only affects speed, and treat it '; anthropic-sdk: ANTHROPIC_API_KEY not set`
- `fetch_page 'https://deepwiki.com/wine-mirror/wine/1.2-windows-api-implem...': page-fetch: https://deepwiki.com/wine-mirror/wine/1.2-windows-api-implementation-layer: HTTP Error 429: Too Many Requests`
- `fetch_page 'https://deepwiki.com/wine-mirror/wine/1.3-wine-loader-and-pr...': page-fetch: https://deepwiki.com/wine-mirror/wine/1.3-wine-loader-and-preloader: HTTP Error 429: Too Many Requests`
- `fetch_page 'https://stackoverflow.com/questions/8081919/executable-runs-...': page-fetch: https://stackoverflow.com/questions/8081919/executable-runs-faster-on-wine-than-windows-why: HTTP Error 403: Forbidden`
- `epistemic demoted DERIVED -> HYPOTHESIS: ledger: no quote verified in any snapshot`
- `learning 0 unrated by relevance filter — kept, flagged UNRATED`
- `learning 1 unrated by relevance filter — kept, flagged UNRATED`
- `source https://baike.baidu.com/en/item/Wine/1460278 carries instruction-like text ['tool-or-exfil-request']; treated as data`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `decomposition narrow: only 2 axis/axes covered (BOUNDARY, EVIDENCE) — minimum 3; missing: MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY`
- `fetch_page 'https://stackoverflow.com/questions/226377/operating-system-...': page-fetch: https://stackoverflow.com/questions/226377/operating-system-compile-time: HTTP Error 403: Forbidden`
- `fetch_page 'https://stackoverflow.com/questions/1180984/programmatically...': page-fetch: https://stackoverflow.com/questions/1180984/programmatically-compute-the-start-time-of-a-process-on-windows: HTTP Error 403: Forbidden`

</details>


## Evidence ledger

- **Claims:** 26 · with a verified quote: 22 (rate 0.846)
- **Quotes:** 33 offered, 6 rejected (not verbatim / unknown source / length)
- **Sources:** 41 snapshots in 41 independent lineage(s); 0 URL(s) were byte-identical copies
- **Labels lowered by the ledger:** 8
- **Sources with instruction-like text (treated as data):** 1

**C1** [HYPOTHESIS] The retrieved sources are decompiler-evaluation work and a community wiki. None report how long a Metrowerks compiler run takes, or how many runs per hour a matching-decompilation project achieves. Anyone budgeting build-farm time or compute for brute-force compiler-matching work therefore has no benchmark here and should plan to measure it directly or find project-level reports elsewhere.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C2** [DERIVED] DecompileBench scores 12 decompilers on three things: recompile success, runtime coverage equivalence, and LLM-judged readability. It reports no per-function time or throughput. Hex-Rays leads on average with 0.583 recompile success and 0.418 coverage equivalence across 23,400 functions. A cost or speed comparison between approaches would need separate measurement.
  - S1 <https://arxiv.org/html/2505.11340v1> chars 23648-23773: "Hex-Rays is recognized as the leading traditional decompiler, achieving the highest single optimization-level RSR of 0.706 at"

**C3** [DERIVED] A 2026 literature review states that the field lacks reliable ground truth and standardized benchmarks, which hinders rigorous comparison. Any timing or throughput numbers a decompilation project does publish are likely measured differently from other projects' numbers, so they cannot safely be compared directly.
  - S3 <https://arxiv.org/abs/2608.24955> chars 1146-1300: "Our review reveals key challenges, such as the lack of reliable ground truth and the absence of standardized benchmarks, which hinder rigorous comparison."

**C4** [DERIVED] When file-heavy tools run across a translation boundary (Linux tools reading Windows drives through WSL2), the slowdown comes from the boundary, not the tool, and ranges from roughly 2x to 10x or worse. Moving the project onto the native filesystem changes performance more than configuration tuning, so a compile-heavy loop like a permuter's would likely gain more from file placement than from faster machines.
  - S8 <https://www.howtogeek.com/your-wsl2-projects-are-running-much-slower-because-you-put-them-on-the-windows-filesystem/> chars 2625-2715: "Sometimes it is 2x slower, sometimes it is 10x slower, and in some cases, it can be worse."
  - S8 <https://www.howtogeek.com/your-wsl2-projects-are-running-much-slower-because-you-put-them-on-the-windows-filesystem/> chars 7533-7619: "A change in location alters performance more than most configuration tuning ever will."

**C5** [DERIVED] Wine startup passes through the host dynamic loader, a Unix-side ntdll, creation of Windows process structures, connection to a separate server process, and mapping of a Windows-side ntdll before the program runs. Each compile launched by an automated search loop pays this setup, so per-invocation overhead, not just compile speed, plausibly explains Wine's gap versus native Windows.
  - S7 <https://arcanenibble.com/notes-on-wine-architecture-and-process-startup.html> chars 4789-5035: "The start_main_thread function starts setting up data structures that would be found in a Windows process such as the Process Environment Block (PEB) and the Thread Environment Block (TEB). It also launches and connects to the wineserver process."

**C6** [HYPOTHESIS] Neither source gives timings for compiling versus scoring objects against a target, nor any head-to-head figures for Wine, a lightweight loader and native Windows. The split must be measured directly before spending on faster compilation or a different runtime.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C7** [DERIVED] On ordinary 64-bit Intel/AMD Windows, the 32-bit compatibility subsystem switches the processor between modes rather than emulating instructions, which is computationally cheap, and Microsoft says performance is similar to native 32-bit Windows. So the per-call cost of a 32-bit compiler there is mostly not instruction translation, and the large overhead appears when software emulation is involved (non-x64 hosts) or comes from the surrounding work each launch does.
  - S11 <https://en.wikipedia.org/wiki/WoW64> chars 2541-2638: "This is computationally cheap, as x86-64 machines have a native mode for running 32-bit x86 code."
  - S11 <https://en.wikipedia.org/wiki/WoW64> chars 8225-8382: "According to Microsoft, 32-bit software running under WOW64 (x64) has similar performance to executing under 32-bit Windows, but with fewer threads possible."

**C8** [HYPOTHESIS] Compatibility layers add work on every launch beyond code execution: redirecting system-folder and registry access for 32-bit programs, loading Wine-style DLL sets, and for Wine the choice between built-in and native DLLs. These costs sit in the loader and file/registry paths, so they can in principle be reduced by caching, keeping the process resident or trimming what loads, without touching the machine code the compiler emits. The sources describe these mechanisms but give no per-call timings, so how much each contributes is unknown.
  - S12 <https://baike.baidu.com/en/item/Wine/1460278> chars 3712-3826: "Users can also use the configuration tool to choose between using Wine's built-in DLLs or local Windows DLL files."

**C9** [DERIVED] None of the retrieved sources quantify startup, licence-check or temporary-file cost for a compiler under a compatibility layer, and they only offer generic overhead figures, such as 0-20% frame-rate loss for Wine graphics workloads and 1.5-5x degradation for translation methods. Those numbers describe long-running programs, not the fixed cost of launching a short process thousands of times, so they should not be used to estimate build-time savings.
  - S13 <https://grokipedia.com/page/Compatibility_layer> chars 24299-24572: "For instance, benchmarks of Windows applications running under Wine on Linux can reveal frame rate reductions of 0-20% for graphics-intensive tasks compared to native execution, depending on the application, hardware, and optimizations like those in recent Proton versions."

**C10** [DERIVED] Incremental compilers reuse earlier output and recompile only changed pieces, which limits how much optimization they can apply because they see only a narrow slice of the program. The common practice is therefore to use incremental builds during development and a standard full batch compiler for release, so what you ship is not shaped by leftover state from earlier compilations.
  - S17 <https://en.wikipedia.org/wiki/Incremental_compiler> chars 2069-2237: "One downside to this type of incremental compiler is that it cannot easily optimize the code that it compiles, due to locality and the limited scope of what is changed."

**C11** [DERIVED] A long-lived Java runtime compiles code on the fly based on what it observes the program doing, and keeps the results in memory so later calls skip the slow path. As a result, what gets compiled and how fast it runs depends on the workload history so far, and thousands of methods compiled at startup measurably affect startup time. Measurements taken early or on a differently exercised process will not match steady-state behavior.
  - S18 <https://alexanderobregon.substack.com/p/how-jit-compilation-uses-code-caching> chars 1294-1410: "Instead of recompiling that native code over and over again, it holds onto it using something called the code cache."
  - S19 <https://www.geeksforgeeks.org/java/just-in-time-compiler/> chars 3350-3561: "When the java virtual machine first starts up, thousands of methods are invoked. Compiling all these methods can significantly affect startup time, even if the end result is a very good performance optimization."

**C12** [DERIVED] Gradle's documentation states that if a task setting affects the output but is not registered as an input, the task will be treated as up to date when it is not, so stale results are served silently. Conversely, registering irrelevant settings causes needless rebuilds. The speedup therefore does not guarantee correctness; it depends on someone having declared every relevant input.
  - S24 <https://docs.gradle.org/current/userguide/incremental_build.html> chars 3299-3437: "If a task property affects the output, be sure to register it as an input, otherwise the task will be considered up to date when it’s not."

**C13** [HYPOTHESIS] One source lists what quietly breaks identical output even with the compiler version locked: embedded build timestamps, locale and timezone, file ordering, parallel builds changing archive order, absolute paths in debug info, minor linker/assembler/C-library differences, and compiler internals that depend on memory layout. Any of these can make a cached result differ from a fresh build, so a cache hit and a rebuild may not be interchangeable. The source is a vendor blog with no incident data, so treat it as a checklist, not evidence of frequency.
  - S22 <https://ubos.tech/news/understanding-compiler-determinism-key-insights-and-practices/> chars 3418-3561: "Even minor differences in the C library, linker, or assembler version can alter register allocation, instruction scheduling, or section layout."

**C14** [DERIVED] Gradle's guidance warns that tasks that can produce different output for exactly the same inputs should not be configured for incremental builds, because the up-to-date checks will not work for them. Tasks with validation problems are also run with all optimizations disabled: never up-to-date, never cached, never parallel. That means a trustworthy build system deliberately gives up speed when it cannot vouch for correctness.
  - S24 <https://docs.gradle.org/current/userguide/incremental_build.html> chars 3588-3784: "Also be careful of non-deterministic tasks that may generate different output for exactly the same inputs: these should not be configured for incremental build as the up-to-date checks won’t work."

**C15** [DERIVED] In Docker's own worked example, a one-line code edit reran the dependency install for about 41 seconds total (37.4s for the install step) because source and dependency list were copied together. After reordering so dependencies are copied first, the same edit rebuilt in 0.1 seconds with the install served from cache. This measures speed gained from cache reuse, not whether the result differs from a clean build.
  - S25 <https://docs.docker.com/learn/content/how-image-layers-and-the-build-cache-work/> chars 19236-19315: "The same edit that cost 41 seconds before now builds in a fraction of a second."

**C16** [DERIVED] Cached build steps compare the command text, not what the command would fetch, so a step that pulls 'latest' packages keeps returning old results until something earlier changes or the cache is forced clean. A cached build can therefore ship a different package state than a from-scratch build would. None of the sources measure how often this happens.
  - S25 <https://docs.docker.com/learn/content/how-image-layers-and-the-build-cache-work/> chars 20183-20253: "Docker compares the command text, not what the command would download."

**C17** [DERIVED] Across these sources, none measures the rate at which a cached build yields a different artifact than a clean one. The one that explicitly addresses benchmarking disclaims it, saying it has no timings from real projects and makes no quantitative speedup claims. The only hard speed numbers are from one small demo app.
  - S28 <https://www.k4nul.com/en/devops/docker-build-cache-and-invalidation/> chars 5609-5767: "This is not a benchmark post with measured timings from repeated builds across real projects. It does not claim that one structure is always “N times faster.”"

**C18** [DERIVED] The Modern Warfare 2 rebuild jumped from an error-ridden ~80% (fabricated or deleted logic, needing a dedicated reviewer agent) to 83% byte-exact once correctness was judged by byte-for-byte comparison with the original compiler. That made the review agent unnecessary and let cheap models (Haiku, Luna) carry the work, cutting cost substantially. What made a simple setup sufficient was the codebase having a checkable answer key, not extra machinery.
  - S32 <https://xenospectrum.com/en/decompilation-match-rate-melee/> chars 7003-7105: "The turning point was switching the judgment of correctness from AI review to byte-by-byte comparison."
  - S32 <https://xenospectrum.com/en/decompilation-match-rate-melee/> chars 7379-7587: "With clear pass/fail judgments, even low-cost models such as Haiku and Luna, which had not produced enough results before, could now carry the work forward, and he explained that this cut costs substantially."
  - _ledger: OBSERVED number(s) absent from verified spans: 80%, 83%_

**C19** [DERIVED] On Snowboard Kids (2,145 functions, 100% in about 83 days), roughly 4.8% of matching commits (about 41) involved expert intervention. The developer estimates that without experts on the IDO compiler, matching would have stalled around 89-90%. Snowboard Kids 2 stalled twice (25% to 58%, then ~75%) and needed community members for its last 10 functions, taking 596 days overall.
  - S32 <https://xenospectrum.com/en/decompilation-match-rate-melee/> chars 15637-15785: "Lewis stresses that not only model performance but also human cooperation was important, stating, "the community was more important than any model.""
  - _ledger: OBSERVED number(s) absent from verified spans: 10, 100%, 2145, 25%, 4.8%, 41, 58%, 596, 75%, 83, 89, 90%_

**C20** [HYPOTHESIS] The same word 'match rate' meant different things across projects: Melee's 100% is matched bytes of total code, MW2's 83% is functions matched of all functions, and a Halo fork's README claims 99.5% while the public tracker shows 23.25% (2,511 of 11,047 functions). Only three projects (Melee, Snowboard Kids, Snowboard Kids 2) had 100% confirmable externally, so self-reported headline numbers can't be compared or trusted without definitions.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C21** [DERIVED] A benchmark of 23,400 functions from 130 real-world programs found LLM-based decompilers beat commercial tools on code understandability but had 52.2% lower functionality correctness. Buying LLM decompilation for work that needs behavior-accurate output (not just human-readable output) carries a large correctness penalty.
  - S35 <https://aclanthology.org/2025.findings-acl.1194/> chars 1245-1495: "Through a systematic comparison between six industrial-strength decompilers and six recent LLM-powered approaches, we demonstrate that LLM-based methods surpass commercial tools in code understandability despite 52.2% lower functionality correctness."
  - _ledger: OBSERVED number(s) absent from verified spans: 130, 23400_

**C22** [DERIVED] Decompile-Bench's builders argue that earlier benchmarks relied on contest-style or synthetic binary-source mappings that diverge from the real world, so they built a set of two million function pairs (condensed from 100 million) plus an evaluation set of repositories released after 2025 to limit data leakage. Fine-tuning on it improved re-executability by 20% over previous benchmarks, which suggests earlier headline numbers may not transfer to real projects.
  - S34 <https://arxiv.org/abs/2505.12668> chars 1587-1828: "we introduce Decompile-Bench, the first open-source dataset comprising two million binary-source function pairs condensed from 100 million collected function pairs, i.e., 450GB of binaries compiled from permissively licensed GitHub projects."
  - _ledger: OBSERVED number(s) absent from verified spans: 20%, 2025_

**C23** [HYPOTHESIS] None of the retrieved sources report time or compute spent on automated permutation before a manual rewrite achieved a match, nor who measured it. They cover LLM decompilation benchmarks and correctness metrics, not match-decompilation workflow costs, so the question remains unanswered here.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C24** [DERIVED] In the Modern Warfare 2 rebuild, the leftover functions would not match byte for byte however often they were revised, because of nondeterministic compiler behavior and an inability to reproduce the linker step that merges identical functions into one. The developer stopped at 83% of all functions matched, with source existing for 99%, judging that further matching would only consume tokens without real improvement, after spending an estimated 600 to 700 billion tokens.
  - S32 <https://xenospectrum.com/en/decompilation-match-rate-melee/> chars 8718-9012: "The remaining functions would not match byte for byte no matter how many times they were revised. Heumann cites nondeterministic behavior and an inability to reproduce a linker process called "identical COMDAT folding," which merges functions with identical content into one, a..."

**C25** [DERIVED] On Snowboard Kids, roughly 4.8% of matching commits (about 41) involved experts familiar with the original SGI IDO compiler, and the lead estimates the match rate might have plateaued around 89 to 90% without them. Easiest-first automated processing stalls, as seen when Snowboard Kids 2 jumped from about 25% to 58%, rose to about 75%, then stalled again and needed community help on its last 10 functions.
  - S40 <https://aisignal.day/en/ai-game-decompile-howto-2026/> chars 10296-10444: "About 4.8% of matching commits involved expert intervention, and Lewis says the project would have stalled around 89–90% without that IDO expertise."

**C26** [DERIVED] Three different units circulate: matched bytes of total code (Melee, 100%), matched functions of all functions (MW2, 83%), and functions with any source regardless of match (MW2, 99%). The Halo project shows 99.5% in one README versus 23.25% on a public tracker, so a headline number can mean a verification mode, a different metric, or a stale fork rather than progress.
  - S32 <https://xenospectrum.com/en/decompilation-match-rate-melee/> chars 5563-5740: "decomp.dev's code match rate is the share of the total code bytes that is matched. The 83% Heumann reported, by contrast, is the share of all functions that match byte for byte."
  - S38 <https://heldgames.com/guides/games-100-percent-decompiled-what-next> chars 9538-9757: "That is not a completion percentage. It refers to an optional build that compiles with the original Xbox SDK compiler and compares the output against the retail binary, which is a verification mode rather than progress."
