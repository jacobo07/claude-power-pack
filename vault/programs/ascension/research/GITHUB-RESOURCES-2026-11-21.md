# GitHub resources for bulk function matching (from DRX Q14/Q15/Q16, 2026-11-21)

Status: ALL ROWS ARE HYPOTHESES (E2-E3 web claims). Each of the three reports opens by saying it did NOT answer the question (no repo URLs, licences, throughput numbers or primary sources for the GC/Wii projects). "cited" below means only that the report lists the URL in its Sources or names it in a claim; it does not mean the report read the repo's licence or code. Licence "not stated" = no report gives one. Items marked (memory) come from the report author's own recollection, labelled UNVERIFIED by the report itself.

## 1. Table

| repo/tool | URL as cited | licence | what it gives us | action | gap | report | evidence |
|---|---|---|---|---|---|---|---|
| decomp-toolkit (dtk) | https://github.com/encounter/decomp-toolkit | not stated (Q15 memory: DOL/REL split+link, built-in CRT signature set, unsure if user-extensible) | Already our target-object producer; signature/masking behaviour unconfirmed | USE (already in pipeline); read its signature code before any ADAPT | signatures/naming | Q14 (Sources), Q15 (memory) | cited (URL only) |
| objdiff | https://github.com/encounter/objdiff | not stated (Q16 memory: "believed MIT/Apache-2.0; verify") | Object-level diff, symbolic reloc compare (memory). Q16 idea: use as library not CLI subprocess to cut spawn cost; unmeasured | USE (already); test library mode | throughput | Q15, Q16 (memory only) | unverified |
| Ketbome/decomp-skills | https://github.com/Ketbome/decomp-skills | not stated | Contains a "twins" command: "copies matched functions onto functions with identical assembly: one match yields many" (Q14 C20, quote verified). Guide warns re-verify every call, constant, offset, branch. This is the only endorsed reuse mechanism in the 3 reports | ADAPT (compare with our F6 phase-1 design; steal its identical-assembly criterion and gating) | F6 phase-1 twins | Q14 | cited |
| puiji/decompilation-eval | https://github.com/puiji/decompilation-eval | not stated | Audit rebuilding every matched function of 16 public decomps on stock compiler: 10 of 14 agent-assisted at 99-100%, 4 below 99% (patched compilers/per-file settings), Pokemon Colosseum 71.4%. Does NOT name the 16 | ADAPT the method as a donor-trust filter (rebuild donor on stock flags before using as donor) | F6 phase-2 donors (quality filter) | Q14 | cited |
| zcanann/mwcc-rs | https://github.com/zcanann/mwcc-rs | not stated | Parity = same relocatable object as real Metrowerks compiler byte for byte; keys on section order, symbol order, alignment, R_PPC_EMB_SDA21 (4,523 commits per Q15). Possible faster/native mwcc stand-in, but report says nothing about speed or completeness | SKIP for now (research-only); revisit as throughput lever if it reaches parity on our units | throughput | Q15 | cited |
| Yokimitsuro/khdays-decomp (NDS, not Wii) | https://github.com/Yokimitsuro/khdays-decomp | not stated | Pattern only: per-file compiler override for middleware units; NitroSDK identification harness compiles SDK sources from another game's decomp (Pokemon Diamond) to check matches. Same shape as F6 phase-2 | SKIP code; ADAPT pattern (per-TU flag override table) | F6 phase-2 | Q14 | cited |
| Wind Waker decomp (via awesomerea write-up) | https://awesomerea.org/resources/wind-waker-decomp-case/ (repo URL not given) | CC0-1.0 per write-up; "does not cover Nintendo's game, disc content or the downloaded compilers" | Template for per-version build.sha1 (415-417 entries) and linking only complete units. 79.58% GZLE01 (32,968 of 39,324 functions) | SKIP (not a donor proof; repo URL absent) | F6 phase-2 (candidate only) | Q14 | cited (write-up, not repo) |
| AlfredoDore/Gamecube-and-Wii | https://github.com/AlfredoDore/Gamecube-and-Wii | not stated | Listed in Sources only; no claim attached | SKIP until read | none | Q14 | cited (URL only, no content) |
| decomp.wiki GC/Wii; REWiki GC/Wii | https://decomp.wiki/platforms/gamecube-wii ; https://initialrise.github.io/REWiki/04-recomp/gamecube-wii/ | not stated | Say 2001 vs 2004 SDK split projects exist; mwcc 1.0-1.7 span; codegen version-specific. Not a repo | USE as reading to pick donors by SDK/compiler | F6 phase-2 donor selection | Q14 | cited |
| fnvdecomp.com / f3decomp.com/how | https://fnvdecomp.com/ ; https://f3decomp.com/how | not stated | Lesson, not code: 34% of 320 failed builds were missing shared class declarations ("blueprints"); only ~3 in 100 attempts succeed; fix systemic blockers first | ADAPT idea: cluster our failed twin builds by missing declaration | throughput, F6 | Q14 | cited |
| decomp.dev | no repo URL given; named in Q14 steps and claims | not stated | Progress tracker. Q14 Sources include headlines saying decomp.dev closed its public leaderboard (timeextension, IGN URLs); Q14 step 5 still says "use decomp.dev". Reports do not reconcile this | SKIP | none | Q14 | unverified (status conflicting) |
| decomp-permuter | https://github.com/simonlindholm/decomp-permuter | (memory) "believed permissive; verify LICENSE" | Our permuter at 111/702 MATCH. Q16 hypotheses: dedupe candidates by post-preprocess hash; test mwcc determinism first | USE; ADAPT with dedup layer | near-miss/permuter | Q16 (memory) | unverified |
| wibo | https://github.com/decompals/wibo | (memory) "verify" | Our mwcc runner. Q16: no timings anywhere; hypothesis that batch/long-lived worker amortizes startup | USE; benchmark ourselves | throughput | Q16 (memory) | unverified |
| ninja | https://github.com/ninja-build/ninja | (memory) Apache-2.0 | Incremental builds; stale objects if depfiles missing | USE (check depfile emission) | throughput | Q16 (memory) | unverified |
| ccache | https://github.com/ccache/ccache | (memory) GPL-3.0-or-later, "verify" | Compile cache; only safe if mwcc output deterministic | ADAPT idea (own content-addressed cache) rather than GPL tool in pipeline | throughput | Q16 (memory) | unverified |
| decomp.me | https://github.com/decompme/decomp.me | (memory) "verify" | Per-function scoring only, never sees other bytes (Q15 C3 via grokipedia) | SKIP | none | Q16 (memory) | unverified |
| Ghidra (BSim, Function ID) | https://github.com/NationalSecurityAgency/ghidra | (memory) Apache-2.0 | BSim fuzzy similarity; FID exact-hash with masking. Q15 C15 (pentestpartners, ESP32 example): FID needs a new DB per compiler/flag change; BSim tolerates but lower confidence. PowerPC 750CL/paired-singles/SDA handling unknown | ADAPT BSim as candidate-twin generator only (near-miss class), gate by objdiff | F6 near-twins, signatures | Q15 (memory), Q14 (C15 pointer) | unverified for repo; cited for behaviour via pentestpartners URL in Q14 Sources? NO: URL only in claim text, treat unverified |
| Dolphin (.map/.dsy) | https://github.com/dolphin-emu/dolphin | (memory) GPL-2.0-or-later | Signature DB generation/apply; matching and false-match reporting unknown | SKIP (GPL, unknown value) | signatures/naming | Q15 (memory) | unverified |
| IDA FLIRT/Lumina | none given | proprietary (memory) | Not usable in our 0-token Ghidra factory | SKIP | none | Q15 | unverified |
| Donor-project guesses: doldecomp (melee, sms, ogws), zeldaret (tww, tp), projectpiki (pikmin2), shibbo/petari, SeekyCt/spm-decomp, bfbbdecomp/bfbb, PrimeDecomp | orgs/users only, no repo URLs | not stated (Q14 memory: "many ship without a standard licence") | Candidate multi-function-TU donors for F6 phase-2 (SDK, NW4R, EGG, MSL_C etc.). Q14 gives NO evidence which libraries/versions are matched | FORK-not-yet: verify each repo manually (licence file, library list) before any use | F6 phase-2 | Q14 (memory) | unverified |
| mkst/mwccgap ; ttkb-oss/metrowrap | seen only as failed deepwiki fetches in Q16 error log (deepwiki.com/mkst/mwccgap, deepwiki.com/ttkb-oss/metrowrap) | not stated | Names suggest mwcc wrappers; reports say nothing about them | SKIP until read | throughput | Q16 (error log) | unverified |

## 1b. Primary-source check (pane 3581ade8, 2026-11-21, `gh api`; the GitHub MCP token returned 401)
- **Ketbome/decomp-skills: VERIFIED, licence MIT** (`gh api repos/...`: MIT, pushed 2026-10-24, 5 stars).
  `skills/matching-decomp/scripts/dk.py` (982 lines), `cmd_twins` at l.769:
  - `asm_signature` (l.662) normalises the instructions (labels relative, symbol operands -> SYM) and keeps the
    symbols in order of appearance.
  - Twins = same normalised key (>= 4 insns). Rename map = zip(donor syms, target syms), refused if one donor symbol
    maps two ways.
  - Body extracted from a multi-function TU (`function_text`). Declarations of the renamed symbols are copied from the
    donor file (`twin_declaration`), and type definitions are copied transitively (`type_definition` / `visit`).
  - Signature rebound to an existing prototype by casts (`adapt_signature`); a conflicting declaration gets an alias
    via `__asm__("<sym>")`.
  - Written in place, checked (`run_check`), REVERTED on no match.
  - It is MIPS/splat-specific (`jal`, `%hi/%lo/gp_rel`, `INCLUDE_ASM`) and works within one project. That makes it
    ADAPT, not USE.
  - It is exactly F6 step 3 (rename from ordered relocation pairs = our relocation-pair walk) PLUS the phase-2 machinery
    (TU donors: body + declarations + types). Port to PPC: `bl` targets and `@ha/@l/@sda21` relocations from dtk
    objects, in place of jal/%hi/%lo. Attribution: MIT notice in the ported file.
- All other rows above stay UNVERIFIED.

## 2. Top 5 actions (expected functions gained per hour of work; all are hypotheses)

1. Read Ketbome/decomp-skills twins command, diff its identical-assembly criterion against our F6 phase-1 (867 one-function-donor twins). Why: only reuse mechanism the reports endorse, and it is the cheapest to compare. Falsified if its criterion is the same as ours or it needs the donor's full image (no new matches over our masked-body rule).
2. Add a full-image/section gate after the per-function objdiff pass for twin transfers (Q14 C18). Why: protects the certified count from .sdata2/string-pool ordering failures; saves rework, not new matches. Falsified if a sample of already transferred twins all pass a section-level diff.
3. Determinism test (200x same input, SHA-256 of .o) then a hash-dedup layer in front of mwcc for permuter and flag arms (Q16 hypotheses 1-2). Why: raises throughput on the 702-function permuter queue with no new source. Falsified if mwcc under wibo is nondeterministic, or candidate preprocess-hash dedup removes under a few percent of compiles.
4. Pick phase-2 donor repos by SDK build and mwcc version first (REWiki/decomp.wiki 2001 vs 2004 SDK; embed-string check from Q14 section 4), then rebuild the donor on stock flags in the puiji/decompilation-eval style before trusting it. Why: avoids spending TU extraction on donors with patched compilers. Falsified if donor functions built on stock flags and ours disagree in under a few percent.
5. Cluster failed twin/lift builds by missing shared declaration (f3decomp/fnvdecomp lesson, 34% of 320 failures). Why: one declaration fix unblocks many functions. Falsified if our failure log shows no repeated missing-declaration cause.

## 3. Not found or thin (identical across all three reports)

- No GC/Wii repo URL, licence, library list or SDK version was verified in any report. Q14 explicitly says its per-project table cannot be filled. All donor-repo names are memory.
- No report describes dtk signatures, Ghidra FID/BSim PowerPC behaviour, or relocation-masking schemes. Q15 P1-P4 (reloc type R_PPC_REL24, SDA21 vs lis/addi under -sdata thresholds, -inline effects, SDK-version hashes) are untested hypotheses.
- No false-match rate for content-based name transfer exists in the sources (Q15 C6); only anecdotes (V-Rally port).
- No measured mwcc invocation cost for native/wine/wibo, no compile-cache data, no objdiff batch data, no permuter farm scaling data (Q16). Only qualitative Wine startup and WSL2 boundary (2x to 10x) notes; the latter applies only if tooling crosses /mnt/c.
- Disagreements: Halo fork tracker figure is 23.25% (2,511 of 11,047) in Q14/Q16 C20 but 7.17% in Q16 S38; unresolved. Q15 reports 2 unresolved conflicts on how far a byte match proves equivalence (matches only the original compiler/target). decomp.dev status conflicts (Q14 recommends it; its Sources include closure headlines).
- Licence for twin-transferred source from public decomps is untested; Q14 notes licence files (e.g. TWW CC0-1.0) do not cover Nintendo SDK content. Our rule (no leaked SDK code) needs manual verification per donor.
- Dolphin/ IDA/ BinaryAI/ SBridge-type fuzzy matchers: only generic accuracy figures (SBridge top-1 recall 84.96% at -O0 vs 65.31% at -O2; inlined functions under 0.01 Recall@1 for BinaryAI) from Q15; not PowerPC or mwcc.
