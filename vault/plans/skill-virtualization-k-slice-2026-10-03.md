---
id: PLAN-SKILL-VIRT-K
title: Card aperture fix, CWST representation verdict (C8), first listing-floor experiment
status: PHASE-3 REVISED (Owner Q&A answered 2026-10-03); phase-4 audit pending
parent: vault/plans/skill-residency-program-2026-10-03.md (PLAN-SKILL-RESIDENCY; this is its C8 + post-C8 slice)
covers: [card-aperture, cwst-representation-verdict, listing-floor, capability-directory-gateway]
date: 2026-10-03
---

# K-slice (2026-10-03)

## Reality (scan, read-only)
- HEAD 3b2e7881 feature/knowledge-acquisition, 5 ahead / 0 behind origin (mine: 91cdc85e, d9072185;
  3 foreign: 61698b13 KSR plan, 74c344e2 governance FP, 26e5cdf0+3b2e7881 KSR audit/plan), 806 dirty, 14 worktrees.
- UKDL ukdl-universal.md dirty from a foreign pane -> never written by this slice.
- Settings: 134 name-only overrides + CLAUDE_DOCTRINE_CARDS=deny; backup sha 0890684D4C60.
- Card live ledger (11:33-14:30): 35 judgements / 12 sessions; unknown 15 (43%), all "pathspec / add pathspec
  is an unresolved variable"; deny-card 1 (300ac3a1, .planning/workstreams/ucep/{ROADMAP,STATE}.md) then pass-after-card.
- Replay of 54 real commit commands (sessions behind the unknown rows) through plan(): unknown 37, judged 17.
  Shapes: A `-- file 2>$null` (redirect token resolved as a pathspec); B `$p=@('a','b')` / `$paths='a','b'`
  (psVars reads single-string assignments only); C dynamic (`Get-ChildItem`, `"$d/x"`; literal $d expandable).
- Listing (fresh a5df8940): 30,002 chars = kept descriptions 20,734 + header/continuations 6,386 + hidden names
  2,444 + kept name-only 198; 11 kept truncated need ~3.5k more (+5 commands unresolved). Demand ~35k vs cap ~30k.
- Docs (tier A, 2026-10-02): listing budget = 1% of context window; all names always listed; descriptions dropped
  least-used first; 1,536 chars/skill; skillOverrides on|name-only|user-invocable-only|off; disable-model-invocation.
- Startup input (a5df8940 -p json): input 2 + cache_creation 97,591 + cache_read 15,665 = 113,258 tokens.
- Owners: capability_runtime/{applicability,invocation,retirement}.py (ACV); CBR = modules/tower +
  vault/tower/families; Context Compiler: no module found (ABSENT); CO-12 via C5 offline adapter.

## Owner decisions (Q&A 2026-10-03)
1. Card to LEDGER during the fix; replay + regression + drill pass first; flip back to deny as a separate verified transition.
2. C8 = split representation (deterministic card + paged skill + 914 B pointer) at EXPERIMENTAL; pointer retained;
   removing it is a separate arm with its own fresh-session evidence.
3. <= 12 fresh sessions (~$10-15 list); ceiling not target; stop early on decisive falsification.
4. Protection = any authority-, security-, recovery-critical, uniquely covering or production-dependent capability,
   plus the moved-rule / claude-power-pack / kresume / kclear / 7-day-activity rules. No blanket KobiiCraft class.
5. Global settings window only if R2 proves --settings cannot carry the experiment AND isolation from other panes
   (no session start/restart during the window) can be guaranteed; otherwise do NOT run the global window.
6. Push after K5 only: fetch, reconcile ancestry, verify the 5-ahead history is intentional, one normal push, no
   force; if a foreign commit is not ready to publish, stay local and report.

## Micro-commit DAG
K0 settings: CLAUDE_DOCTRINE_CARDS deny -> ledger (snapshot first; not a repo commit; recorded in K1 message).
K1 hooks/doctrine_cards.js: drop redirect tokens before pathspec parsing; parse PowerShell list assignments
   (`@(...)`, comma lists) of literals; expand "$v/x" when $v is a literal; everything else stays unknown.
   + test-doctrine-cards.js regression cases cut from the real shapes (A, B, C-literal, C-dynamic stays unknown)
   + replay fixture (the 54 commands, here-strings elided) as a gate: unknown only for dynamic shapes.
   Gates: suite green; replay before (37 unknown, red) / after; isolated mutation drill (tools/mutation_drill.py,
   never the live file); destructive card 17/17 e2e; matcher-liveness.
K1b settings: ledger -> deny after K1 gates; PRG = a real commit in this session using `$p=@(...)` judged (not
   unknown) with mode=deny in the live ledger.
K2 vault/audits/cwst-representation-verdict-2026-10-03.md: arm C rows, N0/R/P/old-C, post-K1 live ledger,
   300ac3a1 deny true/false positive, cost (pointer 914 B resident; skill 7,891 B paged, never loaded in arm C;
   card 0 tokens unless it fires), verdict SPLIT REPRESENTATION, EXPERIMENTAL, rollback (rule backup 0c86aa17,
   CLAUDE_DOCTRINE_CARDS=off), what arm C cannot prove.
K3 wiki/tools listing instrument: composition + startup model-visible input tokens from -p json usage;
   champion x2 fresh sessions (variance).
K4 research gates then challenger (shadow, per-run --settings only):
   R1 user-invocable-only removes the name from the model listing? R2 --settings carries skillOverrides?
   R3 Skill tool on a user-invocable-only name: refused or served?
   Challenger: hidden 133 + a low-use kept cohort (sized from measured demand so total < cap - margin; protection
   rule applied) -> user-invocable-only; one `capability-directory` skill (short description; body = index
   generated from SKILL.md frontmatter by a tool, never hand-curated); page by Skill if R3 serves, else Read.
   Measure: listing chars + startup input tokens vs champion; positive control (natural task needing a cohort
   skill, not naming it); negative control (unrelated task; gateway not loaded); page cost; fallback.
   Stop early on decisive falsification (e.g. R1 false, or floor not below cap).
K5 results into both plans; lessons file (vault/lessons/, UKDL is foreign-dirty); CBR note (EXPERIMENTAL only);
   then the push procedure of decision 6.

## Done-gates
- K1: replay unknown set == dynamic shapes only; suite + drill + e2e green; live judged commit.
- K2: every verdict field filled or UNKNOWN; no claim beyond n=2 + live ledger.
- K4: floor below champion in model-visible input tokens, positive found, negative not loaded, no client patch,
  rollback verified; else the falsification is the result.
- Token claims only from -p usage, never from chars alone.

## Phase 5 -- audit fixes injected (vault/audits/skill-virt-k-slice-audit.md, EXECUTE-WITH-FIXES)
- G1 (live wrong judgement, not unknown): a literal value/list must END at `;`, newline or end of command;
  `'a','b'`, `'a' + 'b'`, `'a'.Replace()` today bind only `'a'`. Test pins today's wrong behaviour red first.
- G2: only assignments BEFORE the commit, at top level (brace depth 0), exactly once, no `+=`; else unknown.
- G3: assignments read from the here-string-elided command.
- G4: every `git add` before the commit (not the first); redirects stripped from commit AND add segments
  (`2>$null`, `2>&1`, `>f`, `*>f`); `-C` / Set-Location resolve to exactly one literal or stay unknown.
- G5: drill with hooks/tests/drill-doctrine-cards.py (isolated copy), not tools/mutation_drill.py; its fresh()
  must copy the replay fixture.
- G6: replay fixture rows carry the EXPECTED plan; gate = exact equality (unknown-count alone hides wrong
  resolutions). Expectations reviewed row by row, plus hand-written oracle tests for G1/G2/G3 shapes.
- G7: the card is loaded from the working tree: develop on a scratch copy, gate it, then one atomic copy-in.
- G8: K4 order R2 -> R1 -> R3; R2 also measures merge-vs-replace of the skillOverrides map; champion runs
  through the same harness.
- G9: gateway index generator extends modules/skill_router/skill_index.py; population = measured listing.
- G10: the protection rule also filters the 133 hidden set.
- G11: K1b PRG must be a JUDGED shape (only-paths / add-then-commit basis), not no_opportunity alone; K4
  rollback is the per-run settings disappearing, stated as such, not claimed as a verified restore.
- Finding for K2 (not K1): 300ac3a1 deny-card = probable FALSE POSITIVE -- ROADMAP/STATE written by the
  session's own `node gsd-tools.cjs`, invisible to write attribution; one extra turn, then pass-after-card.

## Reject
More blind hiding; never-invoked cleaner; new skill ledger; client patching; automatic deletion; migrating
TFPS/SSEA (rule residency, separate program).
