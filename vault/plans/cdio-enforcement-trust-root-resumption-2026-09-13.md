---
title: CDIO enforcement trust root — the hook boundary is now proven, the registration is double, and score composition changed
date: 2026-09-13
tier: T2
status: FOUR COMMITS LANDED, VERIFIED. One Owner-side action is owed. Nothing blocking.
covers: [cdio, design_gate, review_gate, hook_boundary, trust_root, registration,
         abstain, revise_reachability, score_composition, liveness, subprocess,
         double_invocation, settings_json]
---

# Resumption — CDIO enforcement trust root

Successor to `cdio-callable-liveness-resumption-2026-09-13.md`. Read that one for
the reachability findings; they are settled and must not be re-derived.

Not `RESUMPTION_FILE.md`: that file is an ACTIVE-TASK ROUTER for other builds,
carries an explicit "do not delete", and is dirty with another session's work.

## Identity

Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch
`feature/knowledge-acquisition`. Session start HEAD `dd37380`; end `<see git log>`.
At start the branch was 51 ahead / 0 behind origin, and MOST of those commits
belong to other sessions. **Do not push.**

## The thesis, in one line

Last session proved a rule whose function nothing calls is fiction. This one asked
the next question — can you prove the thing that calls it actually runs — and the
answer was: the enforcement had TWO triggers and no artifact asserted either.

## Exact state — SEALED

| commit | what |
|---|---|
| `1d604ce` | D3 ABSTAIN + D2 one-verdict-per-contradiction + exit-table unknown-is-not-ALLOW |
| `05b6c75` | the hook subprocess boundary suite + `registration_sites` (EXTEND of liveness) |
| `e02eeed` | adversarial-pass repairs, including a FALSE GREEN in my own boundary suite |
| (this) | docs truth, knowledge writeback, ratchet absorb |

**Coherence anchor.** All six suites green, plus the ratchet:

```
python tools/test_cdio.py                  # 8/8
python tools/test_design_gate.py           # 15/15
python tools/test_experience_contract.py   # 19/19
python tools/test_cdicf_scope.py           # 10/10
python tools/test_callable_reach.py        # 6/6
python tools/test_hook_boundary.py         # 7/7
python -m modules.liveness.callable_reach  # exit 0, 1370 frozen
```

`python modules/liveness/reachability.py` exits 1 — that is PRE-EXISTING debt
(another session's `knowledge_acquisition` / `session_resilience` modules), it was
exit 1 before this session, and its full output is byte-identical. Do not "fix" it.

## Owner action owed (the only one)

**Remove the duplicate CDIO hook registration** in `~/.claude/settings.json`. The
hook is registered BOTH directly (the `Write|Edit|MultiEdit|NotebookEdit` entry
whose command names `cdio_visual_advisory.js`, timeout 5) AND inside the dispatcher
chain (`--event=PreToolUse-Edit-chain`, which contains it with `block: true` and a
10s budget). `design_gate.py` therefore spawns TWICE per visual write.

Delete the standalone entry; keep the dispatcher one. HR-001 makes this Owner-side,
which is why `V-HOOK-TRIGGER-REGISTERED` reports rather than fails. After the fix
that gate's message changes from DOUBLE INVOCATION to "no matcher reaches it twice"
and stays green either way — the SYNTHETIC control is what proves the detector
still works, so removing the real duplicate does not blind it.

## Active decisions (Owner-approved this session)

1. **D3 → ABSTAIN.** Zero assessed criteria: verdict ABSTAIN, score None, not done.
2. **D2 → one verdict per contradiction.** REVISE reachable; BLOCK also becomes
   reachable without a critical (see below).
3. **Trust-root gate is report-only** on duplicates, hard-fail on absence.

## Open — none blocking, each named so it cannot be lost

1. **Score composition WIDENED refusal.** Six majors and zero criticals now score 52
   = BLOCK, where the same document scored 84/APPROVE before the split. A repo that
   passed yesterday can be denied today. Intended, pinned by
   `V-DESIGN-SPLIT-WIDENS-REFUSAL`. If that is judged too strict the lever is
   `SEVERITY_DEDUCTION["major"]` or `APPROVE_MIN`, and it is a product decision.
2. **The harness hop is unproven.** The suite proves the hook EMITS
   `permissionDecision: deny`; that the harness HONOURS it is exercised by nothing.
3. **No upward-walk fixture.** Every boundary fixture puts DESIGN.md beside the
   surface. Nothing drives a successful walk to an ancestor, and nothing proves the
   walk stops at a `.git` boundary — both are real aperture gaps.
4. **UKDL router pointer, STILL OWED** (second session running). Distillations are
   `vault/knowledge_base/callable-liveness-and-gate-honesty.md` and
   `enforcement-trust-root-and-boundary-honesty.md`. `ukdl-universal.md` is still
   dirty with another session's work.
5. **`hooks/cdio_visual_advisory.js` still says a SKIP'd document "clears the
   anti-slop floor"**, and its comment now also omits ABSTAIN from the
   "APPROVE / REVISE / SKIP" branch. Still dirty with another session's 68 lines.
6. **Nothing runs the callable ratchet or the boundary suite automatically.** Both
   are CLI gates, so both remain subject to the defect they detect, one level up.
   This is the next frontier and it needs a finite trust root of its own.
7. **No rendered surface is ever observed automatically** — the reduced-motion floor
   stays reachable only from the agent path. Unchanged from last session.
8. `registration_sites` was absorbed into the callable inventory by explicit
   `--absorb-new`: its only production caller is in its own module, which the
   detector cannot attribute. Accusing blind spot, recorded not hidden.

## Next three concrete actions

1. Owner removes the duplicate registration; re-run `tools/test_hook_boundary.py`
   and confirm the message flips to "no matcher reaches it twice".
2. Decide whether the widened refusal (open item 1) is wanted at its current
   severity. This is the only product question outstanding.
3. Close item 6: give the ratchet and the boundary suite an automatic trigger with
   an externally observable root, then prove THAT root runs.

## Start instruction

Run the seven commands under **Coherence anchor**. If green, the sealed work is
intact. Do not re-derive the reachability or trust-root findings — both are
measured, fixed and drilled (9/9 across two red-branch drills, with an aperture
control proving the in-process suite is blind to a serialisation break). Do not
push: most commits on this branch are not this pane's.
