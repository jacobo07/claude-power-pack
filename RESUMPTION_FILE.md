# POST-INCIDENT STATE (2026-09-18, read before the router below)

**Hook substrate restored.** All six dispatcher chains were dark 2026-09-16 20:02 → 2026-09-18
13:55 (an agent's exec-form rewrite of `~/.claude/settings.json` dropped every `--event=`).
Full report: `vault/incidents/2026-09-16-hook-registration-identity-loss.md`. Commits
`9b536df` `e58b6af` `5dfbda4` `098f564` `f939aef` `a8b5f0a`, pushed.

- Canonical settings generation: sha16 `49402DC084DCC5F7` (repaired 13:55:50). Pre-repair
  evidence kept: `settings.json.bak-20260918-135550-pre-incident-repair`.
- Check it any time: `python tools/test_hook_registration_integrity.py --live` (must be 15/15);
  the launcher also checks at every start and logs `state/session-config-generations.jsonl`.
- `state/dispatcher-no-event.jsonl` non-empty = a registration lost its identity again.
- Hooks reload LIVE in running sessions on this build; no stale-session restart program needed.

Do NOT re-litigate without new evidence: the writer (session `2174d82b`, ad-hoc script; not
fix_conhost, not settings_merger, not Orca); exec form stays; launcher check is detect-only
by decision (GSDX-I05) — no auto-restore.

**GSD X resumes at the Context Watchdog hot-path slice.** Baseline is GSDX-I11 (real
sessions only: median 3,132 ms / p90 4,974 ms per Stop). Never use synthetic rows
(`gsdac-*`, `gsdlr-*`) or the dark window (GSDX-I09).

Next 3 actions:
1. Read the Stop-chain `CHAIN_MAP['Stop-chain']` members and time each one on a real
   transcript payload (the watchdog's cost scales with the transcript) to find the
   unconditional multi-second overlay.
2. Build the cheap eligibility fast path, keeping the 20 s safety headroom and heartbeat
   honesty; prove auto-compact semantics are unchanged by a red/green drill.
3. Make the synthetic drivers stop writing the production watchdog log (override HOME and
   USERPROFILE, see `tools/test_hook_replay_isolation.py`) — only once the pane editing
   `tools/test_gsd_autocompact*.py` has committed.

# ACTIVE-TASK ROUTER (read first)

**GSD X — Invocation Independence is LIVE (2026-09-16). Do not re-litigate this without new evidence.**
GSD X computes the ExecutionOS Lite tier from a prompt's measured evidence, ambiently, on the real
`UserPromptSubmit-chain`. Live-served branch `feature/knowledge-acquisition` @ `ee54540` (pushed).
Integration branch `integrate/gsd-x-landing` @ `42dd006` (pushed).

Settled by measurement — do NOT rebuild these conclusions:
- There is **no installer** from repo to live. `~/.claude/skills/claude-power-pack` IS the main git
  worktree, and the live dispatcher resolves `path.join(__dirname, '../skills/claude-power-pack/...')`.
  A committed file is live-served. 31 other repo-owned hooks already arrive this way.
- `~/.claude/hooks` is **not under git** (79 hooks; only 15 also exist in the repo). It is the executing
  authority. `hooks/hook-dispatcher.js` in the repo is a **snapshot**, not an authority; its only
  consumer is `tools/test_dispatcher_drift.js`. Do not try to make the repo copy execute — the
  dispatcher's relative paths are resolved from `~/.claude/hooks`, so running it from the repo would
  break all 31 registrations plus the 64 live-only hooks.

Proven at the production invocation (`node hook-dispatcher.js --event=UserPromptSubmit-chain`):
heavy prompt → FORENSIC (secret_containment, cascade_prevention), 9000 ms of a 15 s timeout ·
trivial prompt → silent, heartbeat still advanced (judgements 43→45, LIGHT 10→11) so VALID_SILENCE is
distinguishable from a dead hook · `CLAUDE_GSDX=off` → 0 emissions, judgements unchanged, chain
unharmed. Drift gate `DISPATCHER_DRIFT=3/3` byte-identical. `test_gsd_x.py` 14/14,
`test_gsd_x_timeout_visibility.js` 9/9.

**OPEN, in ROI order:** (1) U05 is only half-measured — per-hook timings inside the chain were not
broken out, only chain wall time; (2) F06 contract-corpus coverage never started; (3) U01 not
re-evaluated against the now-live architecture; (4) informative rate is recorded by the heartbeat
(29/45) but was not analysed for false escalations; (5) concurrency 4 on this chain is still
**inherited, not proven** — shared stdout/heartbeat surfaces unvalidated.

**ACTIVE line (2026-09-13): USEA — Universal Software Engineering Architect.** Phases I–VI
are sealed and green; the one thing the programme still has no evidence for is whether the
constitution changes engineering OUTCOMES. Resume it from
`vault/knowledge_base/usea/USEA_RESUMPTION.md`. Read its §1 before acting on any brief that
asks you to reconcile `UASE` with `USEA` — they are two different systems and one of them
was rejected.

**ACTIVE build (2026-07-12): DAIF — Duplicate-to-Advantage Institutional Fabric.**
Resume it from `vault/knowledge_base/d2a_fabric/DAIF_RESUMPTION.md` → then `DAIF_INDEX.md` →
`DAIF_CANONICAL_MAP.md`. Owner re-spec approved; 22 candidates → 8 sovereign datasets; building DAIF-00.

**PARALLEL build (2026-07-19): Crawl OS.** Separately tracked, not a replacement for the DAIF
ACTIVE line above. Resume it from `vault/knowledge_base/crawl_os/CRAWLOS_RESUMPTION.md` →
`CONSUMER_DECLARATIONS.md`. STOP #1 and Fase 0 (invocation model, consumer declarations) are
Owner-approved; dataset 01 (Constitutional Architecture) is in progress.

**PRIOR task below — SQI — is SEALED (SCS C90/C91/C94) and pushed.** Its content is preserved verbatim;
its backlog (threshold inventory §15.7, pointing `run_sqi` at the estate, surfacing the 4 PP findings) is
unstarted but lower priority than the active DAIF build. Do not delete the SQI section.

---

# RESUMPTION — SQI / UQIOS

You are continuing work on the **Sovereign Quality Intelligence (SQI)** axis in
`C:\Users\User\.claude\skills\claude-power-pack`. Read this file, then the index, then execute
Block 4. Do not re-plan. The architecture is approved and sealed.

---

## 1. What this is

SQI is the **Verification axis** of Claude Power Pack: it governs whether the executable reality
is actually verified, and what evidence licenses that claim. It is the ex-post counterpart to DRK
(decisions, ex-ante) and ACIS (epistemic status of claims).

It is now **two layers**: a corpus (doctrine) and engines (enforcement).

- Corpus: `vault/knowledge_base/sqi/` — 4 datasets, 80 Parts, 108,598 words.
- Engines: `modules/sqi/` — scanner, qualifier, reconciler. `tools/run_sqi.py` runs all three.
- Architecture: `vault/plans/sqi-uqios-architecture-2026-07-12.md`
- Engine contract: `vault/plans/sqi-reconciliation-engine-2026-07-12.md`
- **Binding ontology — read before authoring any Part:** `vault/knowledge_base/sqi/CANONICAL_ONTOLOGY.md`
- Honest gaps: `vault/knowledge_base/sqi/SQI_COMPLETION_REPORT.md`
- Latest seal: `vault/knowledge_base/sqi/sqi_scs_c91.md`

---

## 2. Exact state

**SPEARHEAD CORPUS (SCS C90) AND EXECUTABLE LAYER (SCS C91) ARE BOTH COMPLETE AND PUSHED.**
Do not rewrite either.

- `sqi_00_constitution_v1.txt` · `sqi_01_repository_reality_v1.txt` ·
  `sqi_02_test_reach_v1.txt` ★ · `sqi_03_environment_qualification_v1.txt` — 20/20 Parts each.
- `modules/sqi/repo_reality_scanner.py` · `environment_qualifier.py` · `reconcile.py` ·
  `baseline_guardian.py` · `weakening_detectors.py` · `weakening_baseline.py` ·
  `discovery_rules.json` (**governed artifact** — widening its `exclusions` is the census trap;
  **narrowing its `assertion_vocabulary` is the inverse trap**, and blinds the weakening gate).
- `vault/audits/sqi_weakening_baseline.json` — per-file `{assertions, mocks, cases, sha256}`,
  NOT environment-keyed (the counts are static; keying them would let a host change erase them).
  Currently: **101 files, 2,158 assertions, 23 exit-code-gate (UNKNOWN), 9 verifying nothing.**
- `tools/run_sqi.py` → `vault/audits/sqi_report_<date>.md` + JSON sidecar + the guardian verdict.
  **It exits non-zero on an unexplained decrease.** `--accept-baseline --reason … --author …`
  is the only path that may LOWER a baseline.
- `vault/audits/sqi_baseline.json` — per-root, env-keyed, identity-carrying. Currently: **76**
  executed in root `pytest tests/`, 101 authored, reach 3.0%, env `b5ec3ed51c2f23b1`.
- `tests/test_sqi_engine.py` — 33 tests, **inside** `tests/` so the engine and the guardian are
  reached. It is there because the engine reported SELF-REACH ZERO about itself.
- `sqi-runner` in the D1 Liveness Ledger. CO-12 signal kind `sqi_reconcile`.
- UKDL: `T-SQI-PARALLEL-SYSTEM-001`, `PR-SQI-COMPOUND-INTELLIGENCE-001`,
  `T-SQI-SELF-EVOLUTION-UNCONTROLLED-001`, `PR-SQI-EXECUTABLE-GOVERNANCE-001`,
  `T-SQI-FINDING-FABRICATION-001`, `T-SQI-DIRECTORY-NOT-MANIFEST-001`,
  `PR-SQI-SIGNAL-MUST-GATE-001`, `T-SQI-RATIO-GATE-REWARDS-DELETION-001`,
  `T-SQI-SCOPE-LAUNDERING-001`.

**Coherence anchor — these must agree or something has drifted:**
`python tools/test_sqi.py` reports `SQI_PASS=53/53` and `datasets=4` · `pytest tests/` reports
**86 passed** · `SQI_INDEX.md` marks 4 datasets `COMPLETE` ·
`vault/knowledge_base/sqi/sqi_*_v1.txt` is exactly 4 files · `modules/sqi/*.py` is exactly 7 files
(6 engines + `__init__`).

**What the engine measures about this repository right now** (do not re-derive; re-run it):
Test File Reach **3.0%** (3 of 100) · Orphaned **97** · Executed Protection Ratio **1.6%** ·
authoritative invocation **BROKEN** (`pytest` exits 3, collects nothing) · reach under it
**UNKNOWN, not zero** · verdict `PARTIAL_GREEN`.

**NOT BUILT (backlog, verdicts already fixed in `SQI_INDEX.md` — do not re-litigate):**
SQI-04…SQI-13. Ten datasets.

---

## 3. Active decisions (binding — do not revisit)

1. **14 datasets, not 17.** Every overlapping capability is a cross-reference to the system that
   already owns it (`T-SQI-PARALLEL-SYSTEM-001`). **Never fork:** the evidence ladder (ACIS), the
   knowledge graph (graphify), the insight router (**FD-03 — DO NOT BUILD; it already *is* the
   "Failure-to-Data Compiler"**), decision verdicts/blast radius (DRK), bug→invariant
   (`modules/hard_rules`), the premise verifier (`modules/error_prevention`), done-gate scoring
   (`output_contracts`), telemetry (CO-12 `record_signal` — extend the kind, never fork the bus),
   liveness (D1 `default_registry` — add an entry, never a second ledger).
2. **Fabrication contract.** One `.txt` per dataset. `PART I`…`PART XX`, each closed by
   `PART N FINAL LAW`. Dense prose, numbered subsections, arrow flows. **No** markdown headings,
   bullets, tables, or code fences. **≥1,200 words per Part.**
3. **Vocabulary.** Use *transmutation* / *institutionalization*. The quarantined literals live
   fragment-assembled in `tools/test_sqi.py` `_BANNED` and are **never spelled out in any vault
   prose — including prose that is describing the rule.** A document about forbidden words cannot
   contain the forbidden words.
4. **Never move a criterion to fit a draft.** If a Part lands under the floor, raise the Part.
   The only gate ever loosened here was loosened because the *detector* was broken, never because
   a real finding was inconvenient — that is Part XIII's Gate Mutation Firewall.
5. **The producer never certifies its own claim.** Delegated work is verified by running the gate
   yourself, not by trusting the agent's self-report.
6. **Never adjust the engine so the number confirms the hypothesis** (`T-SQI-FINDING-FABRICATION-001`).
   Every number the engine produced disagreed with the plan's prediction, and every disagreement
   was a real fact about the repository. Report what the instrument says.
7. **The engine surfaces; the Owner remediates.** Widening the canonical invocation is a
   governance event (SQI-02 §9.10). Do not silently fix `testpaths` or the `_logs/` crash.

---

## 4. Next actions (imperative — highest value first)

1. ~~Build SQI-02 Part XV weakening detection.~~ **DONE — SCS C94.** `weakening_detectors.py` +
   `weakening_baseline.py`; four gates (assertions fell → FAIL; mocks rose ∧ assertions did not →
   FAIL; hash moved ∧ arithmetic held → REVIEW; broad handlers rose → REVIEW) + the §15.8 mutation
   probe (`--mutation-probe`, opt-in). **Do NOT gate the mocks/assertions ratio** — a ratio falls
   when its denominator rises, and the cheapest way to raise an assertion count is a tautological
   assertion, which IS weakening §15.8. The assertion vocabulary is a governed artifact:
   **narrowing it hides removals, because zero cannot fall.**
2. **Build the threshold inventory (§15.7)** — the one weakening still undetected. Every numeric
   threshold in the repository, versioned, each change a governance event with a reason. Each
   individual relaxation is defensible; the sum, over a year, is a set of gates that constrain
   nothing. It is invisible without a ledger and lethal with one.
3. **Point `run_sqi.py` at the rest of the estate.** It takes a path argument and has never been
   run outside PP. TUA-X's 390 orphaned tests are one `testpaths` line; CostaLuz's scanner is
   declared and never invoked; the two Elixir repos cannot compile. The engine detects all three
   classes already. Nothing has pointed it at them.
3. **Surface the four PP findings to the Owner** (governance decisions, not agent work): the
   broken zero-argument default, the absent root pytest config, the canonical invocation, and the
   63 unprotected module packages including `secret_firewall` and `cascade_prevention`.
4. **Only then** consider SQI-04…13 from the backlog.

---

## 5. Start instruction

Read this file, then `SQI_INDEX.md`, then `SQI_COMPLETION_REPORT.md` §4 (honest gaps), then
execute Block 4 action 1. Do not ask for approval. Do not explain the plan. Build.

**Update this file after every sealed unit of work — never only at the end.**

---

## Parallel workstream: exact-target continuation (2026-09-18)

The false "COMPACTION LANDED" and the foreground `/d1-continue` injection are fixed in
`5d17c1e`, `01211b5`, `fd87e39`. Its own resumption contract, with what is and is not
proven, lives in `vault/specs/exact-target-continuation.RESUMPTION.md`; read that file
before touching the watchdog resume path, the SendKeys daemon or `continuation_transport`.
