# Apollo Retrofit — Per-Task Context Compression (executed plan)

> /ultra ONESHOT, sealed + Accepted 2026-05-18. Scope (Owner Q1c): root
> skill + `jit_skill_loader.py` trigger matrix only — global
> `~/.claude/skills/*` out of scope (blast radius). Q2: extend
> `apex-completion-standard.md`, no new doc. Q3: ≥30% cl100k reduction,
> existing structure intact. Q4: extend the existing loader, no new
> dispatcher. Q5: COO-Oracle = constraint only, zero vapor. Q6: plan
> file post-Accept.

## Outcome: 5 commits (not 7 — honest consolidation, see Step 1-3)

| Step | Commit | Done-gate (empirical) |
|---|---|---|
| 1-3 jit_skill_loader retrofit | `a011e3f` | G1-G7 PASS: 10/10 profiled, golden-SHA full-tier identical, summary 5041<7423 B, discovery 15≤80 t, e2e telemetry raw-sid |
| 4 ref-correlator Stop hook | `57557d4` | ref_ratio exactly 2/3, sid-absent skip+0, settings.json sha256 unchanged |
| 5 compression gate | `f2c6f55` | apollo-client 33.8%, graphql-operations 36.6%, graphql-schema 33.5%; anchors 3/3,3/3,4/4 verbatim; exit 0 |
| 6 apex checklist | `dc7180c` | repo==global 0 diff; verify_global_mirrors.py EXIT 0 all 4 pairs |
| 7 this plan file | (this commit) | file exists, non-empty, matches executed steps |

## What shipped

**A — Task profiles + tier selector (`tools/jit_skill_loader.py`).**
`TASK_PROFILES`: per-module `include`/`exclude` `##` anchors verified
against real vendored SKILL.md headers. 3-tier selector
(discovery ~80 cl100k / summary / full) with pinned verb regexes,
**default = summary** (full is the regression-risk default).
Section extractor: no-anchor-match → full body (never silent-empty);
full tier bypasses the extractor → byte-identical (golden-SHA proven).
Unprofiled module → full verbatim (13-vs-9 vendored/trigger reconciled,
no KeyError).

**B — Usage telemetry + reference correlation.** Loader appends one
JSONL row per injection to `PP_ROOT/vault/telemetry/jit_usage_<sid>.jsonl`
(absolute path — the hook cwd is the user's arbitrary project; raw
`session_id` written as a field for cross-hook join). Stop hook
`tools/jit_ref_correlate.py` reads the finished transcript, counts
injected `##` anchors actually referenced in assistant output, writes
`jit_refs_<sid>.jsonl`. READ+PROPOSE only, fail-open, **not
self-registered** — Owner applies the one-line patch in the file's
ACTIVATION block (auto-mode classifier denies agent hook self-reg).

**C — Compression measurement (`tools/measure_compression.py`).** Live
cl100k full-vs-summary delta for the 3 highest-priority trigger modules.
Gate = ≥30% reduction AND every `include` anchor verbatim
post-extraction (Apollo guides have no executable done-gate — the
structural-anchor invariant is the sanctioned substitute). Numbers are
computed, never hardcoded.

**D — Doctrine (`knowledge_vault/core/apex-completion-standard.md`).**
"Apollo Retrofit Checklist" section EXTENDS BL-0069 (does not replace):
the 3 mandatory components for any future trigger-matrix skill +
the measured-not-declared 30% gate. Mirror-synced repo→global, verify
exit 0. Baseline for all future skills incl. COO-Oracle.

## Auditor gaps folded (oneshot-architect-auditor, 9 found, all closed)

1 false "executable done-gate" → structural-anchor invariant. 2 heterogeneous
headers → per-module enumerated anchors + `###` support + full-body
fallback. 3 discovery card → deterministic name+1st-sentence, tiktoken
hard-cap. 4 mirror direction → repo-commit→cp-global→verify. 5 parallel
sealed doc → honored explicit Owner Q2 (named-file §2 override),
mechanics made explicit. 6 sid mismatch → raw session_id as a telemetry
field, correlator joins on it. 7 tier verbs → pinned regexes,
default=summary. 8 13-vs-9 → unprofiled→full default. 9 telemetry path →
absolute `PP_ROOT/vault/telemetry`, fail-open.

## Honest deviations

- **5 commits, not the planned 7.** Steps 1-3 all mutate one
  UserPromptSubmit hook file and are interdependent (selector needs
  profiles, telemetry needs the inject path). Three sequential edits to
  one hook file risks an anti-thrash freeze (session_lessons Addendum 9);
  the change is atomic in practice. Consolidated into one commit
  (`a011e3f`), reported transparently rather than fabricating commit
  ceremony.
