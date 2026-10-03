# Phase 3: KME corpus measurements - Context

**Gathered:** 2026-10-03 (GEX44, orchestrator pre-research; discuss skipped via workflow.skip_discuss)
**Status:** Ready for planning
**Mode:** Auto-generated from ROADMAP + the frozen ledger rules. Pillars D, E, F, G, H, I.

<domain>
## Phase Boundary

Goal: each measured pillar gets a terminal by its frozen rule on KME-L / KME-G.
Success criteria: per pillar one measurement file naming its denominator and `command:`; materiality applied
exactly; a second workload sampled for any pillar that clears 3 %.

**Run-plane constraint (binding, ROADMAP "Run plane: GEX44"):** KME-L is the laptop's transcript corpus and is
NOT on GEX44. D, E, F, G, I (and H's KME check) name KME-L. On GEX44 this phase therefore:
1. BUILDS each measuring instrument (one CLI under `wiki/tools/`, program-owned `wiki/tools/kme_*.py`) with tests
   on synthetic transcript fixtures that drive BOTH poles (a fixture where the effect is present and one where
   it is absent; a positive control that the detector fires);
2. SMOKE-RUNS each instrument on GEX44's own KME-G corpus and labels the output `plane: gex44, denominator:
   KME-G (not the frozen denominator)` -- never substitutes it for KME-L;
3. records one `[<P>]` owner-bundle line per pillar with the exact laptop command that produces the frozen
   measurement file;
4. leaves `state.<P>` OPEN (no terminal) -- a terminal needs the KME-L measurement file.
Exception: H "consume CE P and G verdicts" -- if the CE ledger at a commit reachable from HEAD shows P and G
terminals, record that (R2 owner_ledger form) in evidence; H still needs its KME-specific check on KME-L.
</domain>

<frozen_rules>
## Frozen pillar rules (ledger `vault/programs/incremental-cognition/ledger.json`, immutable)

- **D** silent-success hooks: measure `hook_additional_context` chars per tool call on KME-L and CPP-D-W7
  sessions; a slice only at >= 3 % weighted; broken hook delivery is fixed under B regardless. Predicted
  FALSIFIED_OR_REJECTED_BY_EVIDENCE.
- **E** large-source read virtualization: replay rereads of identical file versions on KME-L (same path,
  unchanged content between reads); build a query path in an existing owner only at >= 3 % weighted on KME-L AND
  confirmed on a second workload; never split source for size alone. Predicted RESEARCH_INSUFFICIENT_EVIDENCE.
- **F** GSD operational projection: measure GSD workflow-doc residency (char x turns) on KME-L; if gsd-tools init
  already returns the compact state, hand the residency finding to the GSD owner; never fork GSD. Predicted
  MERGED_INTO_EXISTING_OWNER.
- **G** derived cognition / decision + negative-result reuse: count re-tested falsified hypotheses and
  re-litigated sealed decisions in the corpus (positive control: listing hiding C6 -> K4); one falsifiable slice on
  the existing owner only if the count clears materiality or a correctness exception. Predicted
  RESEARCH_INSUFFICIENT_EVIDENCE.
- **H** proof reuse / singleflight / CCSE: consume CE P and G verdicts; one KME-specific check that verification
  share is below materiality. Predicted FALSIFIED_OR_REJECTED_BY_EVIDENCE.
- **I** startup floor + subagent bootstrap: add the measured subagent first-call context on KME-L to CE B / SC A-C;
  no move of a rule or skill here. Predicted MERGED_INTO_EXISTING_OWNER.

Materiality (frozen): a dedicated slice needs >= 3 % of a named weighted denominator (KME-L weighted =
`weighted_input_equivalent` 1,764,247,687 = input 1 + cache_read 0.1 + cache_write 2 + output 5). A saving is
realized only when displaced work is measured on the same denominator; otherwise interval or UNKNOWN.
</frozen_rules>

<code_context>
## Existing instruments (P0, frozen denominators produced by these)

- `wiki/tools/kme_token_audit.py` (263 lines): `scan_file(path, sess)` walks a transcript jsonl. Already collects
  per session: `attach[type:hookName] = [count, chars]` (attachments incl. `hook_additional_context`),
  `reads[file_path]` (Read calls), `residency` = (tool_key, name, chars, calls_resident, chars*calls) per tool
  result until next compaction, `first_ctx` (main-thread first call context), subagent files
  (`/subagents/` in path), per-call usage (inp, cw, cw1h, cw5m, cr, out) deduped by (message id, requestId),
  `tool_result_chars`, `compactions`. CLI: `--host NAME --out out.json [--expand] ROOT...`.
- `wiki/tools/kme_report.py` (163 lines): aggregates audit JSON per host (KME classification, cost split,
  dead sessions). `wiki/tools/kme_denominators.py` (40 lines): writes the frozen denominator JSON.
- Frozen denominator file: `vault/programs/incremental-cognition/denominators/kme_audit_2026-10-03.json`
  (KME-L 34,871 calls; KME-G 1,322 calls, 13 active / 151 dead sessions).
- GEX44 KME-G corpus: `~/a5-env/home/.claude/projects/*` and `~/a7-env/home/.claude/projects/*` (READ ONLY; live
  sweeps write there -- never write). Main GEX44 projects: `~/.claude/projects/*` (not KME).
- CE verifier evidence kinds: `measurement` file must name a frozen denominator (`KME-L` / `KME-G` / `CPP-D-W7`)
  and record `command:`; see `tools/test_cognitive_economy_program.py` (L4 measurement clause ~line 296).
- No tests exist yet for kme_* tools. Python 3 only, stdlib only.

## Measurement definitions to implement (the instrument must name its numerator and denominator)
- D: sum of `hook_additional_context` attachment chars (and their token estimate) / calls; share of weighted
  denominator = the cache_write + cache_read cost those chars ride along (state the estimate model).
- E: per session, Read results of the same path whose CONTENT hash equals the previous read's hash with no
  intervening Edit/Write to that path; chars and residency-weighted chars; share of weighted denominator.
- F: residency (chars x calls) of tool results / attachments whose content is a GSD workflow doc
  (`gsd-core/workflows/*.md`, `skills/gsd-*/SKILL.md`, command bodies containing `<objective>` from gsd) ;
  compare to the size of `gsd-tools query init.*` JSON for the same step (the compact state that exists).
- G: count of hypotheses marked falsified / decisions marked sealed in the corpus that are re-tested /
  re-opened later (heuristic text markers; MUST carry a positive control fixture: the C6 -> K4 listing-hiding case,
  and report precision caveats). Output an interval, not a point, when the classifier is heuristic.
- H: share of calls/tokens spent in verification (test runs, gate runs, verifier subagents) on KME.
- I: subagent first-call context (`first_ctx` of each `/subagents/` file), distribution + total; compare to
  main-thread `first_ctx`.
</code_context>

<decisions>
## Implementation Decisions

- One module per concern is fine, but prefer ONE new CLI `wiki/tools/kme_pillars.py` with subcommands
  `d e f g h i` reusing `kme_token_audit.scan_file`-style parsing (import, do not fork; extend
  kme_token_audit only additively if a field is missing, and re-verify the frozen denominator is reproduced
  byte-identically on a fixture -- the frozen numbers must not move).
- Each subcommand writes a measurement markdown under
  `vault/programs/incremental-cognition/measurements/<P>-<denominator>-<date>.md` with front matter:
  `pillar`, `denominator` (KME-L | KME-G | CPP-D-W7), `plane`, `command:` (exact argv), numerator, share,
  materiality verdict (>= 3 % / < 3 % / UNMEASURED), and caveats. UNMEASURED is never "below materiality".
- Tests: `tools/test_kme_pillars.py` (V-KMEP-* gates, `KMEP_PASS=n/m threshold=n/m` line), synthetic jsonl
  fixtures generated in a tmp dir by the test itself; each detector driven from both poles + a positive control.
- Smoke on KME-G (GEX44): run each subcommand on the a5/a7 KME projects, write measurement files labelled
  `denominator: KME-G` and `plane: gex44`; they are EVIDENCE about the instrument, not pillar terminals.
- Owner bundle: one `[D]`..`[I]` line each with the exact laptop command. P0 scanned KME-L as
  `python wiki/tools/kme_token_audit.py --host local --out local.json <KobiiCraft/KME project dirs>` and KME-G as
  `python3 wiki/tools/kme_token_audit.py --host gex44 --expand --out gex44.json <a5/a7/b001/main projects roots>`
  (`kme_denominators.py` docstring); the new instrument must accept the same roots and the same KME
  classification, so its session population equals the frozen one (assert the session count).
- Never write ledger `state.D..I` terminals in this phase. Evidence summary in
  `vault/programs/incremental-cognition/evidence/phase3.md` (Product Delta + Intelligence Delta).
- Commits: explicit pathspec only, `git commit -F <msgfile>`, plain single git commands (the worktree harness
  refuses compound git), verify `git log -1 --format=%s`. Never push.

### Claude's Discretion
Subcommand internals, fixture shapes, token-estimate model (state it), output layout.
</decisions>

<deferred>
## Deferred Ideas
- Any build (query path, hook silencing, GSD projection) -- only after a KME-L measurement clears 3 %, which
  cannot happen on GEX44.
</deferred>
