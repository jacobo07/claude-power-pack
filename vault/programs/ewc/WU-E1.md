# WU-E1 -- Premises, seed incident, RED regression fixture (micro-commits M0, M2)

Common brief: `vault/programs/ewc/PROGRAMME.md` (read it first). Route S (12 calls). cwd `C:\Users\User\Apps\wt_ewc`.

Steps:
1. PREMISES (write `vault/programs/ewc/PREMISES.md` in the live checkout, <= 60 lines, each line `fact | file:line |
   VERIFIED/FALSE`):
   a. Goal Spine durable log: where a goal's events live on disk, their format, how `obligation.accepted` is appended
      (`modules/gsd_x/goal/log.py` append ~l.180, `contract.py`), and whether a SESSION-scoped stream (no goal bound)
      can reuse the same model without a second store. Name the read path a Node hook could use without python.
   b. `modules/gsd_x/mission/obligation.py` states/fields; whether `GoalObligation` can gain source / severity /
      actionability / owner_class without breaking existing events (old events must still project).
   c. The canonical PLAN TEMPLATE(s) that plans are written from (grep commands/ultra.md, gsd-planner, writing-plans);
      which ONE is canonical for "every CPP plan" (needed by E5 for the TOKEN BUDGET section).
   d. Stop-chain order and lanes in BOTH `hooks/hook-dispatcher.js` (canonical) and `~/.claude/hooks/hook-dispatcher.js`
      (live); diff closer-guard canonical vs live (hash). Record drift.
   e. Existing test naming for hooks (`hooks/tests/*.js`, `tools/test_*.py`) and how `tools/test_hook_boundary.py`
      drives node->dispatcher->JSON.
   f. Where `/kclear` capsules and the mission successor card are rendered (tools/gsd_mission.py card, rollover
      capsule), so E4 can add open obligations to both.
   Any FALSE premise in PROGRAMME.md -> fix the brief in the same commit and log it in KNOWLEDGE.md.
2. SEED INCIDENT: search transcripts under `~/.claude/projects/*/` for a recent assistant closer that lists FAIL/WARN
   rows and recommends a next iteration (bounded: Grep with head_limit, newest projects first, <= 3 searches). If
   found, add session id + path to KNOWLEDGE.md K0 (no customer content quoted, ids only). If not, say NOT_FOUND.
3. RED FIXTURE (in the worktree): `tools/fixtures/ewc/` holding a synthetic transcript JSONL whose last assistant turn
   is the generic incident shape: 2 RED/FAIL rows, 3 actionable WARN rows, "evidence file not written", "changes not
   committed", "next iteration: X -- recommend doing it next", and ONE subjective line ("final visual approval is the
   Owner's"). Plus a GENUINELY COMPLETE control transcript and a HUMAN-ONLY control (only an outward-facing approval
   left). Generic content, no project names.
4. `tools/test_ewc.py` (V-EWC-* gate style, see an existing tools/test_*.py): drive the REAL
   `hooks/gsd_stop_continuation.js` and `hooks/closer-guard.js` (node subprocess, stdin JSON, temp HOME/state dirs so
   nothing touches ~/.claude/state) against the three fixtures, interactive (no marker). Assert the TARGET behaviour:
   incident -> block/continue (or shadow receipt CONTINUE_*); complete control -> allow + STOP_COMPLETE; human-only
   control -> allow + STOP_HUMAN_GATE. Run it: the incident case MUST be RED today (that is the proof of the root
   cause); controls may be red only because the receipt does not exist yet -- record exactly which assertion fails.
5. Commit (worktree, pathspec): fixture + test. Commit (live): PREMISES.md, KNOWLEDGE.md, receipt.
Receipt must include: the RED output lines, the premise table verdict counts, the plan-template path for E5.
