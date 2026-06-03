# Spec-Driven Department -- Stand-Down Audit (2nd collision)

- **Date:** 2026-06-03
- **HEAD at PASO -1:** `781d4e2`
- **Reason for audit:** the prompt asked Pane 1 to BUILD the
  Spec-Driven Department (M1-M8). PASO -1 inventory found every M
  already shipped by sibling panes. This audit records the stand-
  down decision with empirical evidence so a future agent does not
  repeat the build.
- **Memory cross-ref:**
  `~/.claude/projects/<pp>/memory/feedback_edit_modified_since_read_is_live_concurrent_pane.md`
  (2nd occurrence section appended this turn).

## Sibling commits (already in HEAD, in build order)

| Commit | Subject | Maps to prompt M |
|---|---|---|
| `23f5957` | feat(spec-gate): gate.py + optional spec-gate advisory in one_shot compiler | M1 backing API |
| `78167ca` | feat(error-prevention): premise_verifier + HR-PREMISE/HR-SPEC/HR-CONTEXT | M2 backing API |
| `b7775a6` | feat(spec-driven): 11 V-gates + verify_spp rows + SCS C31 + root-cause taxonomy | taxonomy + tests |
| `6066744` | feat(agents): pp-spec-guardian + pp-premise-guardian + pp-error-analyst | M1 + M2 + M3 |
| `9dc061e` | feat(signals): spec_compliance + premise_risk + error_recurrence | M4 + M5 + M6 |
| `7a16715` | feat(dispatcher): register spec department + feed prompt/cwd into ctx_in | M7 |
| `9c67ba3` | test(spec-dept): 13 V-gates + verify_spp row + SCS C32 seal | M8 |

## File inventory (each M empirically present)

| M | Deliverable | Path | Status |
|---|---|---|---|
| M1 | pp-spec-guardian.md | `vault/agents/pp-spec-guardian.md` | EXISTS |
| M2 | pp-premise-guardian.md | `vault/agents/pp-premise-guardian.md` | EXISTS |
| M3 | pp-error-analyst.md | `vault/agents/pp-error-analyst.md` | EXISTS |
| M4 | signals/spec_compliance.py | `modules/pp_agents/signals/spec_compliance.py` | EXISTS |
| M5 | signals/premise_risk.py | `modules/pp_agents/signals/premise_risk.py` | EXISTS |
| M6 | signals/error_recurrence.py | `modules/pp_agents/signals/error_recurrence.py` | EXISTS |
| M7 | dispatcher registration | `modules/pp_agents/proactive_dispatcher.py` lines 26-32 (imports) + 137-144 (lambdas) | WIRED |
| M8 | test_spec_department.py | `tools/test_spec_department.py` | EXISTS, 13/13 PASS |

## Empirical done-gates (vs the prompt's 6 stated gates)

| # | Gate (prompt wording) | Method | Result |
|---|---|---|---|
| 1 | dispatch("build complete auth from scratch") -> advisory observable | `dispatch(ctx with prompt=...)` returns the pp-spec-guardian advisory | PASS (1 advisory, body matches) |
| 2 | dispatch("fix typo") -> silence | same call, prompt="fix typo in readme" | PASS (0 advisories) |
| 3 | test_spec_department.py -> 8/8 in 3 runs consecutive | run the test 3x | PASS (13/13 each run; exceeds 8/8 target; hermetic) |
| 4 | test_spec_driven.py -> 11/11 no regression | run the test | PASS (11/11) |
| 5 | pytest baseline no regression | `pytest tests/ -q --tb=no --no-header` | PASS (43 passed in 1.38s) |
| 6 | REMOTE_DELTA = 0 0 | git status -sb after potential commit | PASS (this audit is the only file written) |

## Stand-down decision

The Spec-Driven Department is **complete and operational on HEAD**.
Building any duplicate files (under different module names) would
re-trigger the §39.8 naming-drift cascade documented in the BL-SPEC-
DEPT collision memory (sibling pane on 2026-06-02 already lost a
round to this exact trap). The correct outcome of this prompt is
**zero code commits + this audit documenting the empirical state**.

## Recognizer (sealed for cross-repo)

When the prompt says "BUILD M1-M8 spec-department" (or any large
multi-deliverable plan):

1. **PASO -1 is non-negotiable.** `git log --oneline -8` covering
   the last week MUST run BEFORE the first edit.
2. **Inventory each Mx by Glob + Grep.** If every M is found and
   linked to a sibling commit, run the prompt's done-gates AGAINST
   the existing artifacts.
3. **If done-gates pass:** stand down. This audit is the
   deliverable, not the duplicate code.
4. **If done-gates fail in a way that surfaces a real gap:** build
   the SMALLEST patch that closes the gap, not the whole M.

This is the cheap-path version of the BL-SPEC-DEPT collision
recovery (no temp files to delete, no race to reconcile). The
expensive-path version is the original 2026-06-02 recovery
documented in the memory file.

## Cross-link

`SCS C28` (plan code is a hypothesis -- read source first) +
`SCS C29` (smallest real gap, never seal "ALL N CLOSED" on
unanchored count) -- both apply directly. This audit is the
empirical instance.
