# Phase-4 audit -- PLAN-SKILL-VIRT-K (skill-virtualization-k-slice-2026-10-03)

Auditor: oneshot phase-4 (read-only except this file). Date 2026-10-03.
Scope read: hooks/doctrine_cards.js, hooks/tests/test-doctrine-cards.js, tools/mutation_drill.py,
wiki/tools/skill_listing_visibility.py, p3_delivery.py (arm_cmd), capability_runtime/applicability.py, memory dir.

## Gaps (appended as confirmed)

G1. Comma-list assignment is today a WRONG judgement, not an unknown.
- Gap: plan Reality says shape B (`$paths='a','b'`) yields unknown. It does not: psVars regex
  `\$(\w+)\s*=\s*(?:'([^']*)'|"([^"$]*)")` has no end anchor, so `$paths='a','b'` binds paths='a'
  and `git commit -- $paths` is planned as `diff HEAD -- a` (file b silently unchecked). Same for
  `$p='a' + 'b'`, `$p='a'.Replace(..)`, `$p='a' -f ..`: the first literal is taken.
- Evidence: hooks/doctrine_cards.js:101-103 (regex), :146 (resolve), :156 (only-paths plan).
- Fix: K1 regression must include a RED case asserting the comma list currently resolves to one
  path (proves the defect), and the new parser must require the literal/list to be followed by
  `;`, newline, `)`/`}` or end; any trailing operator => variable is UNRESOLVED (unknown).
- Severity: HIGH (false "no_opportunity" possible in deny mode; the 54-command replay counted
  only unknowns, so it cannot see this class).

G2. psVars ignores position and control flow -> fix can turn unknown into WRONG.
- Gap: psVars scans the WHOLE command (last assignment wins), including text AFTER the commit,
  inside if/else branches, loops, and `+=` (not matched at all: `\s*=` needs `=` right after
  spaces, so `$p += 'c'` is silently dropped -> under-approximation). Once lists are parsed,
  `$p=@('a'); $p += 'b'; git commit -- $p` is judged on 'a' only.
- Evidence: hooks/doctrine_cards.js:99-105, :117 (psVars(command) on the full string).
- Fix: (a) only assignments in `before` (cmd.slice(0, cm.index)); (b) a variable assigned more
  than once, or touched by `+=`, `-=`, `[..]=`, `.Add(`, `.Remove(`, `foreach ($v in`, or assigned
  inside `{...}` => unresolved; (c) regression cases for each, all asserting unknown.
- Severity: HIGH.

G3. psVars reads the UN-elided command, so here-string bodies can define variables.
- Gap: plan() elides here-strings for `cmd` but calls psVars(command) on the raw text; a commit
  message here-string containing `$p = 'x'` (code quoted in a message) rebinds $p.
- Evidence: hooks/doctrine_cards.js:116-117.
- Fix: psVars(cmd) on the elided text; regression case with an assignment inside `@'..'@`.
- Severity: MEDIUM.

G4. Same blind spot in the add-path, -C and Set-Location; fix belongs in resolve() + a shared
    redirect filter.
- Gap: (a) ADD_RE capture `([^;\n|&]*)` stops at `&` (cuts `2>&1`) but keeps `2>$null`, `*>$null`,
  `> f`, so `git add -- f 2>$null; git commit` -> 'add pathspec is an unresolved variable'.
  (b) ADD_RE.exec(before) reads the FIRST add only: `git add a; git add b; git commit` plans from
  `a` alone -> under-approximation (WRONG, not unknown). (c) `-C "$d/x"` and `cd "$d/sub"` use the
  same resolve() -> unknown today. (d) A redirect without `$` (`2>&1` in the commit segment,
  `>out.txt`, or `2>` with a separate target token) is passed to `git diff --` as a literal
  pathspec (matches nothing, silently).
- Evidence: hooks/doctrine_cards.js:46, :107-112, :124-129, :148-154.
- Fix: one redirect filter for commit tokens AND add tokens (forms `N>`, `N>>`, `*>`, `>`, `>>`,
  `N>&M`, target attached or next token); matchAll adds before the commit and union them (unknown
  if any unresolved); list and "$v/x" expansion inside resolve() so repo/-C/cd/add all benefit;
  regression cases for each surface.
- Severity: HIGH for (b), MEDIUM for the rest.

G5. K1 drill gate names an instrument that cannot run this suite.
- Gap: tools/mutation_drill.py executes `sys.executable <test>` (python only). The JS card already
  has its isolated drill, hooks/tests/drill-doctrine-cards.py (copy + control + live-sha check),
  but its fresh() copies only doctrine_cards.js and test-doctrine-cards.js, so a separate replay
  fixture file would be missing in the copy -> CONTROL_INVALID. Docstring says 15/15 (suite has 16).
- Evidence: tools/mutation_drill.py:150; hooks/tests/drill-doctrine-cards.py:3, :14-27, :36-41.
- Fix: K1 gate = `python hooks/tests/drill-doctrine-cards.py` with new mutants per K1 invariant
  (redirect drop, list parse, "$v/x" expansion, G1 end anchor, G2 position/single-assignment,
  G4b all-adds); inline the replay fixture in the test or extend fresh() to copy it.
- Severity: MEDIUM.

G6. The replay gate can pass while the guarantee is absent.
- Gap: "replay unknown set == dynamic shapes only" counts unknowns. A fix that resolves shapes
  WRONGLY (G1, G2, G4b) shrinks unknowns and passes. plan() is pure (command + cwd, no I/O), so the
  fixture CAN be frozen with no live transcript read at test time.
- Evidence: hooks/doctrine_cards.js:115-159; plan lines 47, 71.
- Fix: freeze the 54 commands with the hand-checked EXPECTED plan per row ({basis, args} or the
  unknown reason); gate = exact equality per row; cwd as a fixed token; keep here-strings elided
  and pass the fixture through the secret redactor before commit (real commands, HR-SECRET-005).
- Severity: HIGH.

G7. Every K1 save is live in every pane: the dispatcher loads the card from the repo working tree.
- Gap: K0 assumes ledger mode protects panes during the fix. (i) The dispatcher runs
  `../skills/claude-power-pack/hooks/doctrine_cards.js` directly, so each intermediate edit is
  production for all panes. (ii) Whether a settings `env` change reaches RUNNING sessions is
  UNMEASURED: memory proves live reload of hook REGISTRATIONS only, not `env`. The card reads MODE
  once per spawned process from inherited env, so pre-K0 panes may stay in deny.
- Evidence: ~/.claude/hooks/hook-dispatcher.js:428; hooks/doctrine_cards.js:40;
  memory/feedback_settings_session_load.md:11-15 (registrations only).
- Fix: develop K1 on a scratch copy (test via CARD path override or the drill copy), land with one
  write after the suite + drill pass; after K0 and after K1b read the live ledger `mode` field per
  session (doctrine_cards.js:80) and report which pre-existing sessions changed mode -- that is the
  measurement of question 3, and K1b's PRG must also show an OLD pane's row, or state UNKNOWN.
- Severity: HIGH.

G8. K4 gate order and the --settings merge semantics.
- Gap: --settings already carries `hooks` and `claudeMdExcludes` per child (p3_delivery.py:201-206),
  so per-run carriage is plausible, but skillOverrides is a MAP and the user settings already hold
  134 name-only entries: whether --settings merges per key or REPLACES the map is unknown. If it
  replaces, the challenger loses the 134 overrides and the comparison is confounded. R1 and R3 can
  only be tested through --settings (decision 5), so R2 must run FIRST.
- Evidence: p3_delivery.py:195-206; plan lines 16, 59-61.
- Fix: order R2 -> R1 -> R3; R2 asserts (a) a --settings override changes the listing and (b) a
  user-level name-only entry absent from --settings stays name-only (merge, not replace); run the
  champion through the same --settings harness (empty/identical map) for parity.
- Severity: MEDIUM.

G9. Gateway index belongs to skill_router, not capability_runtime and not a new tool.
- Gap: applicability.py judges CapabilityContract objects against a MissionContext; it does not
  read SKILL.md. modules/skill_router/skill_index.py already parses SKILL.md frontmatter
  name+description (build_index, _read_frontmatter). It walks ~/.claude/skills only: plugin skills
  and commands in the listing would be missing from the gateway (silent capability loss).
- Evidence: modules/capability_runtime/applicability.py:140-142, :246-258;
  modules/skill_router/skill_index.py:4-10, :138-166.
- Fix: add a render-directory function to skill_index; population = the actual names in the
  measured initial skill_listing (wiki/tools/skill_listing_visibility.py:9-24), and the gate
  asserts every cohort name appears in the generated index (count equality, by name).
- Severity: MEDIUM.

G10. Protection rule must filter the 133, not only the new low-use cohort.
- Gap: the challenger moves "hidden 133 + low-use cohort" to user-invocable-only with "protection
  rule applied", ambiguous for the 133. Moved-rule skills (destructive-state-authorization,
  instrument-before-claim, ...) are reached by model invocation per their router stubs; if R3
  refuses, the experiment's positive result would recommend removing that path.
- Evidence: plan lines 36, 61-63; ~/.claude/rules/*.md stubs ("Load the skill when").
- Fix: apply decision 4 to the whole moved set, list excluded names in K4 output.
- Severity: MEDIUM.

G11. Vacuous K4 gate clause.
- Gap: "rollback verified" has nothing to roll back in a per-run --settings experiment, so it passes
  with no observation. Same for K1 "live judged commit": `no_opportunity` counts as judged.
- Evidence: plan lines 71-74.
- Fix: K4 rollback = a fresh session after the run shows the champion listing byte-equal
  (chars) to the pre-run champion; K1b PRG states its decision value and basis.
- Severity: LOW.

## Answers
1. K1 fix direction is right but not minimal-safe: G1, G2, G3, G4. Yes, same blind spot in add-path
   (:148-154), -C (:126) and Set-Location (:124). Wrong-judgement shapes: reassignment after the
   commit, `+=`, branch/loop assignment, trailing operators after a literal, multiple adds.
2. Fixture can be frozen (plan() pure, :115-159). tools/mutation_drill.py cannot drill JS (:150);
   use hooks/tests/drill-doctrine-cards.py (isolated, live-sha check) - G5.
3. Only evidence: hook REGISTRATIONS reload live (memory feedback_settings_session_load.md:11-15).
   For `env`: UNKNOWN; measure via ledger `mode` per session (doctrine_cards.js:80) - G7.
4. Order R2->R1->R3 (G8). --settings carries per-run keys in principle (p3_delivery.py:203-206);
   skillOverrides merge semantics UNKNOWN. Generator in skill_router (G9), not capability_runtime.
5. Gates passable without guarantee: G6, G11. No Owner-decision violation found; G10 is a risk to
   decision 4.

VERDICT: EXECUTE-WITH-FIXES
