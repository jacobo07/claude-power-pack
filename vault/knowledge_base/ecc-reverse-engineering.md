# ECC -- Everything Claude Code: Reverse-Engineering Analysis

*Sealed 2026-05-27 as part of the ECC Total Absorption cycle. This
document records the technical analysis behind the absorption; the
absorbed code lives in `modules/uqf/`, `modules/code_review/`,
`rules/`, and CEPS extensions.*

## Repo of record

- **Source:** github.com/affaan-m/ecc
- **License:** MIT (c) 2026 Affaan Mustafa
- **Version analyzed:** 2.0.0-rc.1
- **Clone date:** 2026-05-27
- **Stars / forks (at clone time):** 182K+ / 28K+
- **Anthropic Hackathon Winner:** yes

## What ECC is (technical, no marketing)

ECC is a multi-harness operator system for agentic software work.
It does NOT have a single algorithmic core; it is a collection of:

- 61 specialized agents (`.md` with YAML frontmatter)
- 246 skills (each a `skills/<name>/SKILL.md`)
- 76 slash commands (`commands/<name>.md`)
- ~150K LOC of JavaScript / TypeScript / Python / Rust / Shell
- A unified hook system (`hooks/hooks.json`) consolidated through a
  Node bootstrap that resolves the plugin root across 6+ install
  layouts
- A continuous-learning subsystem ("instinct-based v2.1") observing
  PreToolUse / PostToolUse events and emitting confidence-scored
  atomic behaviors
- A per-language rule taxonomy (`rules/<lang>/{coding-style, hooks,
  patterns, security, testing}.md`) across 17 languages

The Power Pack (PP) is in the same conceptual niche but historically
emphasized different axes (TIS, TCO, CEPS closed-loop, Reality
Contract, monitoring). The two are complementary, not duplicative.

## Architecture (module-by-module summary)

| Surface | What it does | PP analog |
|---|---|---|
| `agents/` | 61 .md prompts for delegable agents | partial (~6) |
| `skills/` | 246 .md skills, each its own dir | partial (~10) |
| `commands/` | 76 slash commands; ECC notes commands/ is legacy, skills/ is canonical | partial (mixed) |
| `hooks/hooks.json` | Single consolidated hook config | distributed across many JS files |
| `rules/common/` + `rules/<lang>/` | per-language quality rules | NONE before this absorption |
| `scripts/` | Node cross-platform utilities | tools/ (Python) |
| `mcp-configs/` | MCP server configs | partial |
| `.claude/`, `.cursor/`, `.codex/`, ... | per-harness skill subsets | PP serves only Claude Code |
| `tests/` | ~700KB JS test corpus | 43 pytest + 8 V-* suites |
| `ecc2/` (alpha) | Rust control-plane binary | NONE |
| `ecc_dashboard.py` | TkInter GUI | NONE |
| `skills/continuous-learning-v2/` | Confidence-scored "instincts" with project-scoped + global promotion | CEPS (different shape) |

## Algorithms and structures (substantive)

ECC's core surface is doctrinal more than algorithmic. The genuine
algorithms found:

- **Confidence scoring** (continuous-learning-v2): 0.3-0.9 scale,
  promotion from project-scope to global at >=2 distinct projects.
  Adapted to Python in `tools/ceps.py::compute_confidence` and
  `promote_to_global`.
- **Plugin-root resolution** (hooks.json bootstrap): probes 6+ paths
  before falling back to `~/.claude`. Solves multi-installer
  layouts. NOT adopted in PP (we install only as a skill).
- **Multi-matcher hook dispatcher**: one Node script that handles
  PreToolUse Bash / Write / Edit / "*" through a single dispatcher
  with shared utility loading. Conceptually similar to PP's
  planned hook-dispatcher (BL future).

## Patterns of quality (the absorbed catalog)

These 12 patterns are the substantive contribution of ECC absorbed
into PP. They are documented in detail in
`vault/knowledge_base/ecc-universal-baseline.md` (companion doc).
Brief summary:

| # | Pattern | Classification | PP Implementation |
|---|---|---|---|
| P01 | Pre-Report Gate (4 questions) | DIRECT | `modules/uqf/principles/pre_report_gate.py` |
| P02 | Common False Positives Catalog | DIRECT | `modules/uqf/principles/false_positives_catalog.py` |
| P03 | Zero Findings Is Valid | DIRECT | `modules/uqf/principles/zero_findings_valid.py` |
| P04 | HIGH/CRITICAL Proof Triad | DIRECT | `modules/uqf/principles/proof_triad.py` |
| P05 | Severity Table Output | DIRECT | `modules/uqf/principles/severity_table.py` |
| P06 | Error Never Silent | DIRECT | `modules/uqf/principles/error_never_silent.py` + AST detectors |
| P07 | TDD Workflow (RED-GREEN-REFACTOR) | DIRECT | `modules/uqf/principles/tdd_workflow.py` |
| P08 | AAA Test Pattern | DIRECT | `modules/uqf/principles/aaa_test_pattern.py` |
| P09 | Prompt Defense Baseline (6 rules) | DIRECT | `modules/uqf/principles/prompt_defense_baseline.py` + CLAUDE.md |
| P10 | rules/common + rules/<lang>/ taxonomy | DIRECT | `rules/common/` (7 files) + `rules/python/` (5) + `rules/elixir/` (5) |
| P13 | Confidence-scored instincts | ADAPTED (JS->Python) | `tools/ceps.py::compute_confidence`, `promote_to_global` |
| P14 | Skills-first migration (commands/ legacy) | INSPIRATIONAL | spec only |

Patterns classified NO-TRANSFERIBLE: Rust control-plane binary
(`ecc2/`), GitHub App Pro tier, Manim/Remotion video generation
skills, TkInter dashboard (PP has no GUI surface).

## License and ethics of absorption

ECC is MIT-licensed. The license permits:

- Use, copy, modify, merge, publish, distribute, sublicense, sell

Required: include the copyright notice + permission notice in all
"substantial portions of the Software". PP discharges this by:

1. Every file in `rules/common/`, `rules/python/`, `rules/elixir/`,
   `modules/uqf/principles/` includes the attribution footer:
   `*Portions adapted from ECC (github.com/affaan-m/ecc) under MIT
   License (c) 2026 Affaan Mustafa.*`
2. `modules/uqf/__init__.py` carries the project-level attribution.
3. This document records the full attribution context.
4. Each `Principle` subclass that derives from ECC has
   `source = "ECC/Affaan Mustafa MIT"`, surfaced in `AuditReport`.

The 14 patterns absorbed are paraphrased and reimplemented in Python
from the ECC `agents/code-reviewer.md`, `rules/common/`, and
`skills/continuous-learning-v2/` sources. No direct ECC source code
was copy-pasted; the principles are expressed in Python idioms.

## Gaps that ECC reveals in PP (priority order, post-absorption)

1. **Per-language rule taxonomy** -- now bootstrapped: common (7),
   python (5), elixir (5). Future cycles can add typescript, rust, go.
2. **Pre-Report Gate + False Positives** for code review -- now active
   in `modules/code_review/`.
3. **Confidence-scored CEPS** -- now active in `tools/ceps.py`.
4. **Prompt Defense Baseline** for agents -- now active in CLAUDE.md;
   future cycles can add to individual agent .md files.
5. **Per-language reviewers** (python-reviewer, go-reviewer,
   typescript-reviewer agents) -- still gap. Spec in
   `vault/knowledge_base/ecc-specs/per-language-reviewers-spec.md`
   (future work).
6. **Multi-harness distribution** (.claude/.cursor/.codex/.zed
   subsets) -- still gap. PP serves only Claude Code today.
7. **Industrial test corpus** (ECC has ~700KB JS tests) -- gap;
   PP's 43 pytest + 8 V-* suites are a fraction of that volume.

## What PP has that ECC does NOT (and must not be lost)

- TIS (Token Intelligence System): per-call event log with JSONL
  append, session id tracking, handoff summarizer.
- TCO (Token Cost Optimizer): compact gate at 70% context, model
  router with task_type -> model mapping, --cost-projection with
  honest-zero contract.
- Monitoring / Alert Axis: state-machine debounce on UP/DOWN, no
  auto-rollback, Owner-gated daemon install.
- Reality Contract / scaffold-auditor: forbids completion-pending
  anchors in delivered code.
- CEPS closed-loop with FTS5 sidecar BM25 search.
- SCS C1-C13 sealed clauses + 8-axis Apex Completion Standard.
- Knowledge Vault + UKDL cross-repo lessons.
- LT (Lateral Thinking) skill axis with empirical fixture.
- Backup / Rollback / Heartbeat / Lazarus resurrection axes.

These are **PP-native and not subject to ECC absorption**. The two
codebases occupy complementary niches in the agentic-productivity
space; absorption is one-way: ECC -> PP for review doctrine + rules
taxonomy + confidence-scoring; PP -> ECC for cost telemetry +
monitoring + closed-loop CEPS (if Affaan ever wants it).

## Empirical baseline (post-absorption)

`tools/uqf_audit.py --scan-all` produced this baseline immediately
after the absorption cycle:

| Module | Score | Status |
|---|---|---|
| modules/monitoring/monitor.py | 80% | OK |
| tools/tco_compact_gate.py | 40% | WARN |
| tools/ceps.py | 20% | FAIL (silent passes detected) |
| tools/tis.py | 20% | FAIL (silent passes detected) |
| tools/jit_skill_loader.py | 20% | FAIL (silent passes detected) |

These low scores reflect **honest baseline**: the ECC absorption
revealed PP-native fail-open patterns that the auditor flags as
silent-pass anti-patterns. Each of these has a documented rationale
(telemetry must not break the request path, hook fail-open is
mandatory for stability) but is now visible as deuda in the audit
output. Future cycles raise the threshold; the baseline is captured.

## Cross-references

- `vault/knowledge_base/ecc-universal-baseline.md` -- companion doc
  with the 12 principles in detail.
- `rules/common/` + `rules/python/` + `rules/elixir/` -- absorbed
  rule taxonomy.
- `modules/uqf/` -- active framework: principles, auditor, gates,
  anti-pattern detectors.
- `modules/code_review/` -- ECC doctrine applied as importable
  helpers (pre_report_gate, filter_false_positives,
  validate_high_critical, run_full_review).
- `tools/ceps.py` -- CEPS extended with confidence_score + scope +
  promote_to_global.

---

*Source: ECC v2.0.0-rc.1 (github.com/affaan-m/ecc) under MIT License
(c) 2026 Affaan Mustafa. Absorption performed in claude-power-pack
2026-05-27.*
