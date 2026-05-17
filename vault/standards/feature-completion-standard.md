# Feature Completion Standard

Sealed 2026-05-17 (RTK/JIT/apex/intent-lock publish cycle). Prerequisite of any
OVO submission from this session forward.

## Hooks & Harnesses Gate (mandatory for any feature shipping new hooks)

A feature that introduces new hooks or verification harnesses is **not
complete** — and MUST NOT be OVO-submitted as A/A+ — until every item below
holds with executed, real-input evidence (no mocks, no dry-runs that never
touch the system):

1. **Hook registration is real.** Every new hook is either (a) registered in
   `~/.claude/settings.json` under its correct event (`PreToolUse` /
   `PostToolUse` / `UserPromptSubmit`) with a post-write
   `node -e "JSON.parse(fs.readFileSync('settings.json','utf8'))"` parse
   assertion, OR (b) bundled by an already-live dispatcher
   (`hook-dispatcher.js` `EVENT_MAP`) — in which case "0 settings.json refs"
   is by-design and the dispatcher wiring MUST be proven by reading the
   `EVENT_MAP` entry, not assumed.

2. **Live verification, honest about restart.** A hook registered directly in
   `settings.json` is inert until `/restart` — and `/restart` is an
   Owner-only action (an agent cannot self-restart; classifier hard-denies
   `settings.json` hook self-registration under autonomy). If a hook's
   activation is sealed doctrine as an explicit Owner step, its DONE-gate is
   the **doctrine-defined verifier** (e.g. `verify_rtk_fusion.py` exit 0),
   NOT "live in the authoring session." Applying a "live-in-my-runtime" bar
   to an Owner-gated hook is the wrong gate.

3. **Every harness runs green against real input.** Each new harness is
   executed against real targets (not empty fixtures) and exits 0 with
   semantically-correct output. A harness that passes against empty fixtures
   is a failure.

4. **OVO audit → A before push.** A re-audit consumes the executed-evidence
   ledger. A is honest **only** when every B objection has been empirically
   falsified by an executed run. Stamping A with any objection
   unaddressed/unrun is inflation and is forbidden. A genuine B is a task
   list (run the verifiers, re-audit), never a license to inflate.

This section is a prerequisite of any OVO submission from this session
forward. Governance walls (auto-mode `settings.json` self-registration deny,
Owner-only `/restart`) are never worked around to satisfy it — an
Owner-gated step left as the Owner's step is correct, not incomplete.
