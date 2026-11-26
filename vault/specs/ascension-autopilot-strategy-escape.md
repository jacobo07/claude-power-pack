---
covers: [strategy_escape, escape_problems, SYNTH_MAX, wsr_pool_exhaustion, ascension_autopilot]
tier: T2
owner_turn: "2026-11-26 pane a90ef78f, OWNER RULING — WSR SCIENTIFIC ESCAPE AND STRATEGY EVOLUTION"
---
# Ascension autopilot: Strategy Escape (round 5)

## PRD
A lane whose designed levers stop converting parks today (`evolve.SYNTH_MAX=3`) and waits for the Owner to
invent the next route. Measured case: WSR S371R, eligible pool 0 < 20. Its funnel was 34,148 text fns ->
1,295 named -> 1,020 unlinked -> 636 donor-defined -> 626 one-definition -> 0 after the "never named in prior
evidence" exclusion. The named donor population is exhausted; the 32,853 unnamed fns were never a source.
Owner: a stalled generation must be able to open a strategic investigation by itself when an informative,
authorised experiment exists. Reusable for every lane.

## Behaviour
- Where a lane would park on SYNTH_MAX (or a designed lever is refused and the lane would park), and the lane
  still has research room, evolve arms ONE fixed-template lever of family STRATEGY_EXPANSION (not model-designed).
- Its directive requires the checkpoint to carry machine lines:
  - `FUNNEL: <stage> <count>` (>= 2 lines): where the candidates disappear.
  - `STRATEGY: <id> family <F>` (>= 2 lines), each F absent from the lane's lever families so far.
  - Either `DISCOVERY_POOL: <name> count <N> floor <F>` with `HELD_OUT: untouched`, or `LIMITS: <text>` and
    `REOPEN: <condition>`.
- `escape_problems(text, known_families)` admits that checkpoint deterministically. Then:
  - Pool count >= floor goes to the normal judge and evaluation.
  - LIMITS parks with `park_kind=limits` and an owner_queue notice of the REOPEN conditions.
  - Anything else counts as one failed escape.
- Bounded: ESCAPE_MAX=2 escapes in a row without a verified CAPABILITY/CERT; a conversion resets it. After
  that the lane parks as today.

## Never
- No budget raise: the research cap, envelope and day cap bind exactly as before.
- No certifier, breaker or held-out change.
- No new scheduler or autopilot.
- A diagnostic pilot below the floor is exploration, never a decision.

## Acceptance (V-AP-ESCAPE-*)
1. A SYNTH_MAX stall with research room arms STRATEGY_EXPANSION, not park.
2. ESCAPE_MAX reached means park (bounded).
3. No research room means park (no spend past the cap).
4. escape_problems: FUNNEL<2, STRATEGY<2, or a repeated family are each refused; a pool below the floor is not
   eligible; LIMITS without REOPEN is refused.
5. LIMITS+REOPEN gives park_kind=limits plus a notice.
6. A conversion resets escape_streak.
Mutants: escape ignores ESCAPE_MAX; escape ignores the research cap; family-novelty check removed.

## Rollback
Restore `*.bak-a90e-escape-<ts>` of evolve.py, autopilot.py, test_autopilot.py on GEX44
(`~/agora/ascension-autopilot`, not a git repo). planner_prompt.md is unchanged: the escape lever's `what` carries
the whole contract through the existing RESEARCH directive. Kill switch: `AP_STRATEGY_ESCAPE=0` in the cron env.

## Gate (staging `/tmp/ap-r5-stage-a90e`, 2026-11-26)
test_autopilot.py 444/444, mutants 201/201 killed (4 new: escape_unbounded, escape_ignores_room,
escape_no_novelty, escape_limits_ignored; the same 2 pre-existing crash-kills). The 14 legacy park checks now run on a
lane whose escape is spent (evo_fresh `escape_streak: ESCAPE_MAX`): reality changed, no assertion deleted.
V-EVO-ESCAPE-LIVE-PATH drives judge DISAGREE -> design none -> escape -> plan -> arm end to end.

## Round 7: admission reads the evidence where the generation wrote it (Owner 2026-11-26 "go ahead" + "a", pane 31498a3e)
The first real escape (WSR S395R, judged AGREE) wrote `STRATEGY: S1 SIGNATURE_IDENTIFICATION: ...`, put its funnel
in `funnel.json` beside the residual, and wrote its reopen condition as `Next route (...): ...` inside LIMITS. The
round-5 checker refused it three times (0 new families, < 2 FUNNEL lines, LIMITS without REOPEN).
- `escape_family(line)`: an explicit `family <F>` or `FAMILY: <F>` wins; otherwise an UPPER_SNAKE token after the id
  and before a colon. `FAMILY` itself is never a family. Novelty is unchanged: >= 2 families this lane has not tried.
- `escape_funnel_stages(product, residual)`: the integer stages of `funnel.json` beside the residual, counted only if
  there are >= 2 of them (absent, unreadable or a non-map = 0). They are added to the FUNNEL line count.
- `escape_reopen(lines)`: the REOPEN lines; when there are none, a `Next route:` / `reopen ...:` clause inside a
  LIMITS line. LIMITS with neither is still refused. The limits park's `why` carries the derived clause.
- The directive text is unchanged (it still asks for the machine lines).
- Real S395R checkpoint: 3 refusals -> 0. It parks `limits` with the "Next route" text.
- Gate (staging `/tmp/ap-r7-stage-3149`): AUTOPILOT_GATE_PASS, mutants 209/209 killed, 6 of them new
  (family_lead_off, family_colon_off, funnel_file_ignored, funnel_file_any, reopen_clause_off, reopen_anything).
  New checks: V-AP-ESCAPE-FAMILY-FORMS, V-AP-ESCAPE-EVIDENCE-WHERE-WRITTEN.
- Deployed 2026-11-26T17:00:18Z, after the gate and under both locks: evolve 7e89fa2f, test 3860d148. Rollback:
  `*.bak-3149-famforms-20261126T170018Z`.
