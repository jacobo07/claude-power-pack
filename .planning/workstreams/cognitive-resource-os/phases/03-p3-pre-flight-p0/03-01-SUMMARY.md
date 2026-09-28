---
phase: 03-p3-pre-flight-p0
plan: 01
subsystem: testing
tags: [claude-cli, static-analysis, settings-schema, rules-loading, ablation-protocol]

# Dependency graph
requires:
  - phase: 01-gate-verdict-on-the-big-host
    provides: "Gate verdict pattern (redact-before-write, dirty-set bracket) reused for the global-file bracket here"
provides:
  - "EVIDENCE.md sections 0-4: pre-checks, host facts (~/.claude/rules ABSENT on GEX44), global-file bracket
    B0=B1=B2 (UNCHANGED), invocation log (inv01-inv08, all --help/--version, model_calls: 0), discovered
    candidate surface (40 names: 15 help flags + 22 env vars + 3 settings keys) with full triage, twelve
    candidate blocks (C01-C12) each with byte-verified evidence and a rule-consistent judgement, and the
    P0 verdict: PASS (--settings claudeMdExcludes naming the three R1 files)"
affects: ["05-seal-and-hand-back"]

# Actuals (#2632)
actuals:
  tokens: 15452
  tasks: 3
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Coverage-by-construction candidate discovery: three fixed regex scans (help-flag keyword match,
      env-var name pattern, settings-schema describe() text) over the installed binary's own captured
      output, every discovered name triaged CANDIDATE or NOT_P0 with a reason grounded in its own text"
    - "Byte-verified static excerpts (Xnn): every code-trace claim backed by a grep -a -o -E capture from
      the resolved binary, checked post-hoc to be a byte-for-byte substring of the pinned sha256"
    - "Identifier-hop honesty: minified identifiers with multiple definitions in the bundle (k8, pZe, FEn,
      R, ar, Je, ye) are called out by count in the evidence line rather than treated as globally unique;
      the decisive C02 chain (excludeMatcher:ye for type:\"User\") is established by same-scope local
      variable flow, not by a cross-module name hop, and is spelled out as such"

key-files:
  created:
    - .planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/EVIDENCE.md
    - .planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/raw/claude-version.txt
    - .planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/raw/claude-version-end.txt
    - .planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/raw/claude-help.txt
    - .planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/raw/claude-subcommand-help.txt
    - .planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/raw/discovered-surface.txt
    - .planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/raw/static-excerpts.txt
  modified: []

key-decisions:
  - "P0 verdict is PASS (--settings {\"claudeMdExcludes\":[the three R1 absolute paths]}), C02, the
    lowest-numbered ACCEPTABLE block. claudeMdExcludes' own describe text names a .claude/rules/**
    glob example despite the key's CLAUDE.md-suggesting name, and X08-X10 trace the matcher through to
    excludeMatcher:ye on the type:\"User\" rulesDir walk -- confirming it filters rule files, not only
    CLAUDE.md, and scoped to exactly the named files (EXCLUDES_R1_ONLY)."
  - "C01 (--setting-sources), the protocol's own first-listed candidate, is REJECTED (rules_effect):
    excluding the 'user' source drops the ENTIRE user rules directory, user CLAUDE.md, and user-sourced
    skills/agents/commands together -- EXCLUDES_MORE_THAN_R1, not R1 alone."
  - "C04/C05 (CLAUDE_CONFIG_DIR / alternate HOME), the protocol's own second-listed candidate family, are
    REJECTED (credential): the binary reads .credentials.json from the same relocated config directory
    (X12), so neither reuses auth without copying the credential file -- exactly the protocol's own stated
    test for this candidate family, and it fails."
  - "Host applicability is recorded, not glossed over: ~/.claude/rules does not exist on GEX44 (0 of 3 R1
    files present, prefix_inventory reports 0 rule/rule_scoped rows), so arm A on GEX44 itself carries no
    R1 -- this host cannot run the ablation as defined regardless of the PASS. The mechanism is for
    whichever host (the laptop, per RESUMPTION.md) actually has R1 loaded."
  - "Identifier-hop counts >1 (k8: 4, pZe: 2 byte-identical, FEn: 2 NOT identical, R: dozens) are recorded
    honestly in the evidence rather than silently trusted; the C02 PASS instead rests on a direct,
    same-scope excerpt (excludeMatcher:ye at the type:\"User\" rulesDir call site, X10) that does not
    require resolving those ambiguous global names."

requirements-completed: [CRO-03]

coverage:
  - id: D1
    description: "Candidate mechanisms enumerated from claude --help / documented flags and the installed
      binary's own settings-schema and env-var surface, found by construction (three fixed scans); every
      discovered name triaged, every floor candidate C01-C12 given a full 12-property evidence block"
    requirement: "CRO-03"
    verification:
      - kind: other
        ref: "Task 2 automated verify: coverage-by-construction recompute (untriaged/bad-triage/floor-missing/candidate-without-block all empty) and block/judgement/xid/overclaim consistency checks, exit 0"
        status: pass
    human_judgment: false
  - id: D2
    description: "Every candidate judged against the verbatim P0 clause by one mechanical rule (first
      failing property in a fixed order); a mechanism needing a copied credential or an edited global
      file is REJECTED with that property named first"
    requirement: "CRO-03"
    verification:
      - kind: other
        ref: "Task 1/2 automated verify: p0-clause-exact (whitespace-normalised equality with the protocol paragraph) and per-block judgement recompute, exit 0"
        status: pass
    human_judgment: false
  - id: D3
    description: "p0_verdict is exactly PASS (named mechanism) or STOP, recomputed from the blocks by the
      stated rule; zero model calls made (inv01-inv08 all --help/--version); global config and credentials
      provably untouched (B0=B1=B2, credential stat-only)"
    requirement: "CRO-03"
    verification:
      - kind: other
        ref: "Task 3 automated verify: p0_verdict/global_bracket/cro03/phase_status/version-end-file/keys-once recompute against the live binary and files, exit 0"
        status: pass
    human_judgment: false

# Metrics
duration: 28min
completed: 2026-09-28
status: complete
---

# Phase 03 Plan 01: P3 pre-flight P0 Summary

**P0 verdict PASS (--settings claudeMdExcludes naming the three R1 rule files), reached from twelve byte-verified candidate blocks and zero model calls; CRO-03 SATISFIED.**

## Performance

- **Duration:** 28 min
- **Started:** 2026-09-28T13:36:41Z
- **Completed:** 2026-09-28T14:04:48Z
- **Tasks:** 3 completed
- **Files modified:** 7 (EVIDENCE.md plus 6 raw/ captures)

## Accomplishments
- Pre-checks recorded: ANTHROPIC_API_KEY UNSET, installed claude 2.1.283 resolved and sha256-pinned
  (1859583ce3292059...), global-file bracket B0=B1=B2 for settings.json/CLAUDE.md/rules-dir-presence/
  credentials-stat (UNCHANGED across the whole phase, credential only ever stat-ed).
- Host facts re-measured (not copied from planning notes): ~/.claude/rules is ABSENT on GEX44 (0 of 3 R1
  files present), and `prefix_inventory.py --json` reports 0 rule/rule_scoped rows with ~26.1k unconditional
  tokens (ESTIMATE) -- matching the planning-time facts.
- Eight allowlisted claude invocations (inv01-inv08): --version (start and end), --help, and five
  subcommand --help forms (auth, auth login, auth status, setup-token, doctor). `model_calls: 0`.
- Candidate set built by construction: three fixed scans of the installed binary's own help text, env-var
  names, and settings-schema describe() text discovered 40 names (15 help flags, 22 env vars, 3 settings
  keys). Every name triaged CANDIDATE (mapped to a floor block C01-C12) or NOT_P0 with a reason grounded in
  its own text -- no name from memory, no new C13+ block needed.
- All twelve floor candidates given a full 12-property block with byte-verified excerpts (X01-X14 in
  raw/static-excerpts.txt, each checked to be a real substring of the pinned binary):
  - **C02 --settings claudeMdExcludes: ACCEPTABLE.** The schema's own describe text names a
    `.claude/rules/**` glob example; the code trace shows the resulting matcher wired as
    `excludeMatcher:ye` directly into the `type:"User"` rulesDir walk -- it filters rule files (not only
    CLAUDE.md, despite the key's name), scoped to exactly the named files.
  - C01 (--setting-sources, the protocol's first-listed candidate): REJECTED (rules_effect) -- drops the
    whole ~22-file user rules dir plus user CLAUDE.md and user-sourced skills/agents/commands, not R1 alone.
  - C03 (same key via a worktree settings file): REJECTED (other_prefix_changes) -- the new file changes
    the arm's own worktree git status.
  - C04/C05 (CLAUDE_CONFIG_DIR / alternate HOME, the protocol's second-listed candidate): REJECTED
    (credential) -- `.credentials.json` is read from the same relocated directory (X12), so neither reuses
    auth without a copy.
  - C06 (--bare): REJECTED (credential) -- its own help text states auth is "strictly ANTHROPIC_API_KEY or
    apiKeyHelper" once bare.
  - C07 (--safe-mode), C08 (--restricted), C09 (--system-prompt), C10 (--append-system-prompt), C11
    (CLAUDE_CODE_DISABLE_CLAUDE_MDS): each REJECTED (rules_effect) -- too broad, no effect on rules at all,
    undecidable without a model call, additive-only, or (X14) empties the whole user rules dir together
    with Managed/project CLAUDE.md.
  - C12 (editing/relocating the R1 files directly): REJECTED (global_edit) -- recorded per the plan, never
    performed.
- Section 4 verdict: `p0_verdict: PASS (--settings {"claudeMdExcludes":[the three R1 absolute paths]})`,
  `cro03: SATISFIED`, `global_bracket: UNCHANGED`, with `version_scope` pinning the result to claude
  2.1.283 on GEX44 and `host_applicability` stating plainly that GEX44 itself has no R1 to exclude (the
  mechanism is for whichever host -- the laptop, per RESUMPTION.md -- actually carries R1).

## Task Commits

Each task was committed atomically:

1. **Task 1: Tracer -- pre-checks, host facts, global bracket, every help/version capture, and C01 judged end-to-end** - `6d2c6e1` (docs)
2. **Task 2: Candidate set by construction -- discovery scans, floor blocks C02-C12, judgements** - `c632771` (docs)
3. **Task 3: End-of-phase version/bracket checks, the P0 verdict by rule, CRO-03 status** - `d08644d` (docs)

_No TDD tasks in this plan; each task is a single evidence-recording commit, per the plan's own commit protocol._

## Files Created/Modified
- `.planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/EVIDENCE.md` - Sections 0-4: pre-checks, host facts, global bracket, invocation log, discovery (2a), candidate blocks (2b, C01-C12), P0 judgement (3), and the verdict (4)
- `.planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/raw/claude-version.txt` - inv01 output
- `.planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/raw/claude-version-end.txt` - inv08 output
- `.planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/raw/claude-help.txt` - inv02 output (full --help, 66 options)
- `.planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/raw/claude-subcommand-help.txt` - inv03-inv07 output (auth/auth login/auth status/setup-token/doctor --help)
- `.planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/raw/discovered-surface.txt` - the three fixed discovery scans (H/E/S)
- `.planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/raw/static-excerpts.txt` - X01-X14, byte-verified against the pinned binary

## Decisions Made
See key-decisions in frontmatter above.

## Deviations from Plan

None - plan executed exactly as written. One self-correction during execution: several `- key: value`
lines inside candidate blocks (rules_effect, other_prefix_changes, global_edit on C02/C03/C06/C07/C08/C10/
C12) were initially drafted with a trailing parenthetical explanation on the same line, which the plan's
own automated enum/exact-match checks correctly rejected (`enum:rules_effect`, `:global_edit`,
`:judgement` failures on the first re-run of Task 2's checks). Fixed before committing by moving those
values to bare enum tokens (the reasoning is still carried in each block's `changes`/`touches_on_disk`
prose); both automated checks then passed cleanly. No fabricated evidence was committed at any point.

## Issues Encountered
None beyond the self-correction above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 5 (Seal and hand back) can carry `p0_verdict`, `version_scope`, and `host_applicability` from this
  EVIDENCE.md into RESUMPTION.md and the UKDL, per section 4's own `next:` line.
- This PASS does not itself authorize running the ablation: P1 (A/A noise floor) and every counted run
  still wait on subscription quota and the Owner, and arm B-prime (R1 on demand) remains a separate,
  unjudged arm per the protocol.
- No blockers. No candidate mechanism was exercised; global config and credentials are provably untouched.

## Self-Check: PASSED
- FOUND: .planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/EVIDENCE.md
- FOUND: .planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/raw/claude-version.txt
- FOUND: .planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/raw/claude-version-end.txt
- FOUND: .planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/raw/claude-help.txt
- FOUND: .planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/raw/claude-subcommand-help.txt
- FOUND: .planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/raw/discovered-surface.txt
- FOUND: .planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/raw/static-excerpts.txt
- FOUND: commit 6d2c6e1 (Task 1)
- FOUND: commit c632771 (Task 2)
- FOUND: commit d08644d (Task 3)

---
*Phase: 03-p3-pre-flight-p0*
*Completed: 2026-09-28*
