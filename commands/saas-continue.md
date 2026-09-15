---
description: Continue an existing SaaS project using the internalized doctrine
---

# SaaS Continue Protocol

You are resuming work on an existing SaaS project using the **SaaS Launch Doctrine**.

## STEP 1: Assess Current State

1. Read CLAUDE.md to understand the project
2. Check git log for recent commits
3. Identify which of the 14 launch phases the project is currently in:
   - Phase 1: Planning | Phase 2: Bootstrap | Phase 3: Deploy | Phase 4: Database
   - Phase 5: UI Shell | Phase 6: Auth | Phase 7: Feature #1 | Phase 8: Feature #2
   - Phase 9: AI Integration | Phase 10: Payments | Phase 11: Landing Page | Phase 12: Polish
   - Phase 13: Go-to-Market Readiness | Phase 14: Launch & Sell

4. Report: "This project is in Phase [N]. Last completed: [description]. Next action: [description]."

## STEP 2: Apply Operating Laws

- **One phase per session** — complete the current phase, verify, commit, then clear
- **Plan-first rule** — outline approach before writing code
- **Verification-led** — build passes + browser verification before commit
- **Sub-agent review** — after completing a feature, review with fresh context
- **Context discipline** — keep sessions focused, use /compact when heavy

## STEP 3: Execute Next Phase

Follow the phase checklist from the SaaS Launch Playbook. Mark items complete as you go.

## STEP 4: Phase Gate

Before moving to next phase:
- [ ] Build passes clean
- [ ] All features verified in browser
- [ ] Previous features still work (regression check)
- [ ] Git commit with phase label
- [ ] CLAUDE.md updated with new current phase

Report completion and recommend next action.
