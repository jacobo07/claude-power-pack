# Software-engineering capability gaps — Claude Power Pack (2026-09-30)

## Method

Three independent sources, then a verification pass:

1. **Inventory** of what PP provides, per area, discovered from the filesystem
   (modules, commands, skills, agents, hooks, tools). 21 areas.
2. **External benchmark**: SWEBOK v4, what Claude Code / Codex / Cursor / Copilot /
   Devin / OpenHands / Aider / Amp / Jules / Factory ship, and the evidence on
   what actually moves agent outcomes. 56-item checklist with evidence tiers:
   **A** = controlled or measured, **B** = vendor/practitioner claim, **C** = none found.
3. **Host tooling probe**: which analysers are installed here (decides cost to close).
4. **Verification**: every absence below was re-checked by an independent sweep
   of 1,388 executable files (.py/.js/.ps1, excluding vault and worktrees), using
   code-shaped patterns (imports, invocations), with two positive controls
   (`secret_firewall` 24 files, mutation 15 files) so a zero means absent, not blind.
   Non-zero hits were read before being counted as capability.

Working files: scratchpad `research/` (inventory.md, benchmark.md, host_tooling.md,
gap_sweep.py/.out).

## The one-paragraph answer

PP is strong where most agent toolkits are weak: governance, session continuity,
failure learning (CEPS, hard rules), deploy/backup/rollback, design review, cost
telemetry, and mutation-testing **of its own gates**. It is thin exactly where the
external evidence says outcomes are decided: it never measures whether its own
rules help, it does not feed compiler/linter/type diagnostics back after an edit,
it has no symbol-level code intelligence, security stops at secrets, and its
testing machinery points at itself rather than at the user's code. And half of
what it has built is not wired: 73 of 145 registry entries are PLANNED
(built, nothing calls them), mostly meta-governance.

## Ranked gaps

Rank = evidence of impact × how directly it affects everyday coding × cost to close.

| # | Gap | Evidence | PP today (verified) | Cost to close |
|---|---|---|---|---|
| 1 | **No standing eval of PP itself** — no private task set measuring whether rules/hooks/gates improve outcomes or cost | A (contaminated public benchmarks; harness matters as much as model; context files measured neutral-to-negative, +20–23% cost) | One-off P3 ablation (found no quality loss with rules removed). No harness in repo; `daif/two_arm_trial` is PLANNED | Medium: build a ~30-task private suite from real past sessions, run with/without each layer |
| 2 | **No post-edit diagnostics loop** (type/lint errors fed back in the same turn) | B (plausible, cheap signal) | `quality-gate.js` only *prints a reminder* to run `tsc --noEmit`; no PostToolUse-Edit chain runs anything | Low: PostToolUse-Edit hook running ruff (installed) / project tsc on the edited file |
| 3 | **Testing aimed at PP, not at the user's code** — no property-based testing, fuzzing, coverage-guided or impacted-test selection, flaky-test handling; mutation-guided test generation absent | A for mutation-guided test gen (Meta: 73% accepted) and execution feedback | Mutation drills/ratchet exist but target PP's own gates; auto-testing generators only py/node/java; 0 files use hypothesis, fuzzing, or coverage for user code | Low–medium: hypothesis and coverage are installed; point existing mutation machinery at user projects |
| 4 | **Security beyond secrets** — no SAST, dependency CVE scanning (SCA), SBOM, license scan, threat model | A/B (Veracode: 45% of AI code failed security tests) | `secret_firewall` is the only real capability; SAST/SCA sweep = 1–2 incidental hits | Medium: install semgrep + osv-scanner/pip-audit; wire into done-gate |
| 5 | **No symbol-level code intelligence** (LSP, tree-sitter, SCIP; defs/refs/call graph) | B | graphify is file-level; `ast` used in 19 tools for file-level analysis; 0 tree-sitter/ctags/SCIP; the 10 "LSP" hits are incidental | Low if adopted: Claude Code ships LSP code-intelligence plugins; needs pyright/typescript-language-server installed (both absent) |
| 6 | **Delivery pipeline for PP itself** — no CI, no release/changelog/semver automation, no PR creation | B (DORA links delivery to outcomes) | No `.github/workflows`; 600+ test gates run only when someone runs them; 0 PR-creation code (gh installed) | Low: one CI workflow running the gate suite; release notes from commits |
| 7 | **No hybrid verification / best-of-N** | A in research (R2E-Gym 51% hybrid vs ~43% either alone), unproven on frontier models | 0 hits | High (tokens); only for high-stakes tasks |
| 8 | **No sandboxed execution** | B | Worktrees for missions exist; no container/VM isolation; Docker not installed | Medium–high on this Windows host |
| 9 | **Data & API safety** — no migration safety checks (locks, backward compat), no API contract/schema diffing | C (classic outage causes, no agent evidence) | backup/rollback via pg_dump only; 2 incidental hits each | Medium, per stack |
| 10 | **Performance** — no profiling or perf-regression detection for user code | C | Benchmarks cover PP's own hooks and LLM endpoints only; 0 profiler hits | Medium |
| 11 | **Accessibility & i18n measured, not declared** | C | WCAG is a *declared* level in DESIGN.md (design_gate.py), not measured on the render; 1 incidental i18n hit | Low for a11y: playwright is installed, axe-core runs inside it |
| 12 | **Collaboration metadata** — CODEOWNERS/review routing, feature flags/progressive rollout | C | 0 hits each | Low / out of scope for a solo estate |

## Structural gaps (not in the checklist, found on the way)

- **Built-not-wired**: 73/145 registry entries PLANNED + 9 known orphans. The
  cheapest SE wins are already written: `refcheck` (reference-integrity linter,
  136+ findings by its own docstring, no caller), `done_gate` (artifact done-gate,
  no caller), `monitoring/alert` (its consumer never imports it),
  `cascade_prevention/pre_mortem` (not exported).
- **Language support is mostly prose.** 18 overlays, but test generators exist
  only for Python/Node/Java and static checks (uqf) are Python-only.
- **Context load vs evidence.** The external study most relevant to PP found that
  instruction files it did not need cost 20–23% more with no gain; PP's own P3
  ablation found no quality loss when rules left the always-loaded prefix. Both
  point the same way: measure (gap 1) and then keep moving rules out of the
  always-on context.

## What is already covered (checked against the benchmark)

Cost/step tracking per task (A: TIS, tco gate, cost_collapse) · lifecycle hooks as
deterministic gates · subagents and missions with worktree isolation · secret
blocking · code review with severity filtering (pp-code-reviewer) · plan-before-edit
(SDD-OS, /ultra, spec gate) · permission/destructive-action guards · headless
runtime verification (sleepless_qa) · deploy/backup/rollback · design review (CDIO).

## Confidence and limits

- Benchmark claims rest mostly on search snippets, not full reads; Devin, Jules,
  Amp and Factory are secondary sources. Evidence on hooks, repo maps, subagents
  and multi-agent review is thin *everywhere*, not just here.
- Hook registration in settings.json was not verified per hook.
- The inventory agent listed a `process-sandbox.js` that does not exist; it was
  dropped. Other inventory entries marked LIVE were not individually re-verified,
  only the absences above.
- Host tooling absence is PATH + the main Python only.

## Suggested order

1 (measure) → 2 (post-edit diagnostics) → 3 (hypothesis/coverage/mutation on user
code) → 4 (semgrep + osv-scanner) → 5 (adopt LSP plugins) → 6 (CI). Wiring
`refcheck` and `done_gate` can happen alongside at almost no cost.
