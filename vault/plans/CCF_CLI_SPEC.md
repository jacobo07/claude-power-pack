# CCF CLI Specification — Phase 3

> `cpp creative <subcommand>`. Subcommands derive from the real pipeline evidenced in Phase 0
> (`REVERSE_ENGINEERING_REPORT.md`) and the 8-component architecture in `CCF_ARCHITECTURE.md`.
> Reduced from the original 15-verb CCF spec to the 8 verbs that map onto an actual pipeline
> stage or gate — no verb exists without a component behind it.

## `cpp creative init <project>`
- **Purpose:** create a new CCF project directory with an empty Creative Specification shell and
  a `config.json` scaffold (Component #2 shape).
- **Inputs:** `<project>` name; `--brief <file|-->` optional (if given, feeds straight into
  `compile` below rather than leaving the spec empty).
- **Outputs:** `<project>/config.json` (schema-versioned, empty concept list), `<project>/spec.json`
  (empty Creative Specification shell), `<project>/.ccf/` state dir.
- **Exit codes:** `0` success; `1` project dir already exists (refuses to overwrite); `2` invalid
  `--brief` path.
- **Failure modes:** none beyond the above — this is a pure filesystem scaffold, no network, no
  model call.

## `cpp creative compile <project> --brief <file|->`
- **Purpose:** run the Creative Contract Engine (#1) — brief → Creative Specification, with
  mandatory ambiguity resolution.
- **Inputs:** brief text (file or stdin); `--refs <url,...>` optional reference assets routed
  through CrawlOS ingestion.
- **Outputs:** populated `spec.json`; if ambiguity is detected, a `questions.json` block printed
  to stdout and exit code `3` (blocking — not an error, a required human turn).
- **Exit codes:** `0` spec compiled clean; `3` blocked on ambiguity (re-run with `--answers
  <file>` to resume); `1` brief unreadable/empty.
- **Failure modes:** an unresolvable brief (contradictory constraints) surfaces as `verdict:
  UNRESOLVABLE` in `questions.json` rather than a silent best-guess spec.

## `cpp creative generate <project>`
- **Purpose:** run the full Phase-1 pipeline — Config-Driven Pipeline (#2) fan-out → Prompt
  Compiler (#3) → Model Adapter Layer (#4) → Trademark Collision Scanner (#7) → Artifact Compiler
  (#5) showcase mode.
- **Inputs:** requires a compiled `spec.json` (from `compile`) and a populated `config.json`
  (concept list — either hand-edited or produced by `compile`); `--only <concept_id>` to run a
  single concept (mirrors the reference repo's `--only=spotify`); `--dry-run` to print assembled
  prompts and estimated cost without calling the Model Adapter (mirrors the reference repo's
  `--dry-run`).
- **Outputs:** `<project>/artifacts/<concept_id>/image.png` per concept; per-concept Trademark
  Scanner verdict recorded in `<project>/.ccf/scan_report.json`; `<project>/showcase.pdf`.
- **Exit codes:** `0` all concepts PASS or WARN-with-no-block; `4` at least one concept BLOCKed
  by the Trademark Scanner (showcase still built, excluding BLOCKed concepts, with the exclusion
  noted on the page — never silently dropped); `5` a Model Adapter `ProviderError` aborted one or
  more concepts (partial showcase built from what succeeded, failures listed in
  `scan_report.json`).
- **Failure modes:** CCF-F03 (no fallback provider) means a provider outage surfaces as exit `5`
  per concept, not a whole-run abort — concepts that already succeeded are preserved.

## `cpp creative select <project> --concept <id>`
- **Purpose:** the human-irreducible gate (Institutional Extraction §F) — record which concept
  was chosen, by whom, when. Not automatable; the CLI's job here is only to *record* a human
  decision, never to pick one.
- **Inputs:** `--concept <id>` (must exist in `scan_report.json` with a non-BLOCK verdict); `--by
  <name>` identifies the approver.
- **Outputs:** `<project>/.ccf/selection.json` `{concept_id, by, timestamp}`; unlocks
  `cpp creative package`.
- **Exit codes:** `0` recorded; `6` referenced concept does not exist or is BLOCKed (refuses to
  select a blocked concept without first re-running `generate` with an explicit override brief).

## `cpp creative package <project>`
- **Purpose:** run Phase-2 Artifact Compiler (brandkit mode) over the selected concept, then the
  Creative Evaluation Engine (#6) objective checks, producing the deliverable brand package.
- **Inputs:** requires `selection.json` to exist (refuses otherwise — enforces the human gate).
- **Outputs:** `<project>/brandkit.pdf` (multi-page, SVG-symbol recolor variants per Phase 0
  evidence); `<project>/evaluation_report.json` (objective PASS/FAIL per check from
  Institutional Extraction §D).
- **Exit codes:** `0` package built, all objective checks PASS; `7` package built but one or more
  objective checks FAILED (package is written for inspection but is NOT release-eligible — see
  `cpp creative release` gate below, not implemented as a separate verb; release is folded into
  `package`'s successful-exit path per the architecture's single Release Manager component,
  avoiding a redundant verb for a check `package` already performs).
- **Failure modes:** CCF-F02 fix applies here directly — if the selected concept's image artifact
  is missing (should not happen post-`select`, but checked anyway), `package` refuses to emit a
  near-empty PDF and exits `2` instead.

## `cpp creative audit <project>`
- **Purpose:** stand-alone invocation of the Trademark Collision Scanner (#7) against an
  already-generated artifact set, without re-running generation — for re-scanning after the
  reference-mark corpus is updated, or auditing a package before external release.
- **Inputs:** `<project>` with existing artifacts; `--corpus-version <id>` optional, to audit
  against a specific reference-corpus snapshot (supports re-auditing older packages against a
  newer corpus).
- **Outputs:** updated `scan_report.json`; a diff against the previous scan if one exists
  (`{concept_id, previous_verdict, new_verdict}` — surfaces cases where a corpus update flips a
  prior PASS to WARN/BLOCK).
- **Exit codes:** `0` no BLOCKs; `4` at least one BLOCK found (same code as `generate`'s
  collision-block path, for scripting consistency).

## `cpp creative diff <project> <v1> <v2>`
- **Purpose:** compare two sealed runs of the same project (reuses `replay_harness.py`'s
  diff-based regression pattern per the architecture's Release Manager reuse verdict — not a new
  diff engine).
- **Inputs:** two version identifiers (git-style refs into the project's `.ccf/` history, or two
  release-manifest hashes).
- **Outputs:** structured diff — which concepts changed, which prompts changed, which scanner
  verdicts changed, cost delta.
- **Exit codes:** `0` diff computed (regardless of whether differences were found — an empty
  diff is a valid, successful result, not an error).

## `cpp creative rollback <project> <version>`
- **Purpose:** restore a project's artifacts/spec/config to a previously sealed version (composes
  with `session_resilience` checkpoint/rollback per the architecture, not a new versioning
  subsystem).
- **Inputs:** `<version>` must reference a Release-Manager-sealed package.
- **Outputs:** working directory restored; a rollback event recorded in the provenance chain
  (never a silent overwrite — the DAIF-21 record shows the rollback as an explicit event, not a
  gap in history).
- **Exit codes:** `0` restored; `8` referenced version not found or not sealed (refuses to roll
  back to an incomplete/unreleased state).

## Deliberately omitted verbs (vs. the original 15-verb spec)

`vectorize`, `validate`, `eval`, `learn`, `export`, `history` are dropped as *separate* verbs:
`validate`/`eval` are folded into `package`'s objective-check exit path (a standalone verb would
duplicate the same check with no new behavior); `vectorize` is out of CCF v1 scope entirely
(Institutional Extraction §E — the manual PNG→SVG/Vectorpea step is deliberately not automated
yet); `learn`/`export` belong to the Knowledge Systems phase (`CCF_KNOWLEDGE_SYSTEMS.md`) as
automatic writeback, not a manually-invoked verb; `history` is `diff` with no second argument
(same underlying data, not a separate command surface).
