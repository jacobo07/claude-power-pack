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

**Action 1 partly answered without timing (2026-09-19, `3c49f86`).** The host sat at 4% free
memory, where this estate has measured 17x drift, so nothing was timed. Two load-independent
instruments were used instead and both hold on any host:
- Static profile of `CHAIN_MAP['Stop-chain']`: 25 members, 0 missing, 327 s of serial budget;
  **6** are both unconditional and transcript-scaling (`lazarus-snapshot`, `mark-live-session`,
  `research-intent-detector`, `session_snapshot_stop`, `output_contract_stop`,
  `ceps_promote_stop`). That is a LOWER BOUND: "a gate exists" is not "the gate fires", and
  `closer-guard` is marked gated while measuring 644-1245 ms.
- `logs/context-watchdog.log`, which real Stops write themselves — 256 real rows / 106 sessions
  after excluding 663 synthetic `gsdac-`/`gsdlr-` rows and the dark window. **`pass` median
  1,555 ms vs `block` 233 ms** (p90 4,930 / max 15,007 on a pass at 45% usage). 92 of 256 are
  multi-second passes with no crossing. The comment at `hook-dispatcher.js:173` claiming 844 ms
  for an ordinary Stop is wrong against real sessions.

**Fixed:** `_orchestrator_overlay` imported `auto_reset_orchestrator` ABOVE its throttle and
no-nag flag, so every Stop paid the import chain forever. Guards hoisted; pinned by
`tools/test_context_watchdog_overlay_guard.py` 4/4 (counts imports, never a clock — valid on a
starved host), mutation 2/4, `test_gsd_autocompact.py` 26/26.

# POST-INCIDENT STATE (2026-09-19 evening) — THE LONG-RUN CAUSAL MODEL CHANGED

**The 7-hour KobiiCraft stall was NOT a hung Stop hook, and not a hung job.** Session
`de7f3c91` (KobiiCraft Core Files, Phase 13). Measured, not inferred:

- 12:38:58 the mission backgrounds a STATE.md blocker read at the harness 120 s timeout.
- **12:41:58 the job COMPLETES** — `tasks/b4haxctvm.output`, 3,095 bytes, exit 0. Its content:
  all four blocker sections **absent**, i.e. "nothing is blocking you, proceed."
- 12:41:58 and 12:44:45 two `<task-notification>` rows are **enqueued**.
- The turn ends. Nothing re-invokes the model. **The queue does not pump itself.**
- 19:50:02 (7 h 08 m later) the notifications are delivered, when the Owner returns and types.
- 20:06:59 the reply is `No response requested.` — a relapse of CLAUDE.md rule (L).

Stop `4/5` is `gsd-context-monitor.js` (timeout 10 s, and it carries its OWN 10 s stdin guard),
so it is a poor 7-hour suspect; `4/5` was the last-rendered frame of a turn that had already
ended. **Do not go looking for a wedged hook without new process evidence.**

**H1 IS REFUTED AS EVIDENCED — and this corrects a claim made in chat on 2026-09-19.**
It was reported that KME "survived 11 compactions unattended, AUTO=11 / HUMAN=0". That was an
instrument failure: the classifier listed `<command-name>` as *synthetic*, so every `/compact`
the Owner typed scored as AUTO. Measured properly across the whole store:

    439 compact boundaries in 131 transcripts -> 419 confirmed MANUAL /compact, 20 window
    artifacts. 3 of 3 hand-checked candidates (including one inside KME's own bb4e529f,
    whose /compact row sits at +9 rows) were MANUAL.

**Zero native auto-compactions have ever been observed in this estate.** But note the selection
effect before concluding the host cannot do it: the watchdog fires at 60/70% and a human
compacts first, so **nothing has ever been allowed to reach the native wall.** H1 is therefore
UNTESTED as a host capability, not disproven. The experiment is cheap and decisive and is the
next big unknown — a disposable session with the watchdog off, run to the real wall.

**H2 IS SUPPORTED.** `closer-guard` measured 867 runs / 385 blocks, live. Stop `decision:block`
re-invokes the model in the same session. That primitive is proven in production here.

**H3 is supported but did NOT cause this stall.** Three `auto-compact-refused-*.flag` files,
zero deliveries; `8915b3d5` (KobiiCraft, 71%) went dead 23 h after its refusal. (That session id
is real — it had been flagged in chat as possibly invented. It is not.)

**LANDED (`4d45b7a`).** `hooks/gsd_stop_continuation.js` — bounded autonomous TURN continuation.
Second on Stop-chain, critical lane, after `closer-guard`. 17/17 both poles, 2 mutations caught
on their own assertions, SHA-256 restore verified, and driven END-TO-END through the real
dispatcher (`runnable=20/26`, reason survives the merge, negative control clean).
**It is OPT-IN and currently inert:** it does nothing unless the autorun marker carries
`continuation: "stop-block"`. 11 markers existed when it landed; none opt in. Kill switch
`CPP_GSD_STOP_CONTINUATION=off`. Anti-loop = A SECOND BLOCK REQUIRES A CAUSAL DELTA.

**LANDED (`1df113f5`, KobiiCraft repo).** `agents_installed:false` with all 35 agents present was
Orca exporting `CODEX_HOME` into Claude Code panes, so GSD's host-detection rung reported
`codex` and checked a directory that does not exist. Fixed at `config.runtime`, never in
`gsd-core` (MANAGED tree — edits are re-staged away). Same file finished the long-run threshold
restore (12/8 -> defaults) that `_pp_long_run_backup` proved was owed.

Next actions for the long-run track, highest value first:
1. **The native-wall experiment.** Disposable session, watchdog off, run to the real context
   wall. This single measurement decides whether the whole compact-delivery apparatus lives or
   dies. Until it runs, do not retire the legacy path and do not flip the default.
2. **A/B**, then flip `continuation: "stop-block"` on by default only if it wins.
3. `Stop-chain` still has **no `CHAIN_DEADLINE_MS` entry**. Adding one needs its own wall-clock
   measurement AND an argument about what failing open costs — the dispatcher states that bar
   itself. Note the Stop-chain blockers are `closer-guard` and `zero-issue-gate`, i.e.
   ACCOUNTING and dead-screen, not the HR-SECRET-001 boundary, so the argument differs from
   PreToolUse. Blocked on host headroom (6.4% free at time of writing).
4. Four GSD projects still lack `runtime` in `.planning/config.json` and misreport agents the
   same way: `gsd-long-smoke`, `Orca X`, `ABSW2-Wii`, `KobiiSports Resort`. Deliberately NOT
   patched — the Owner does run Codex sessions, so a blind `claude` would create the mirror bug.
   Apply per project when next active.

Older actions from the watchdog hot-path slice (still open):
1. **Explain the pass/block asymmetry — still open.** The overlay runs FIRST for both outcomes
   (`context-watchdog.py:963`), so the import defect does not by itself explain why the cheap
   path costs 6.7x the expensive one. Do not assume the fix closed it. Suspect next: what
   `block` short-circuits that `pass` does not.
2. **Time it once the host has headroom** (>8 GB free, medians not single readings, bracket the
   headroom on BOTH sides of the sweep — a pre-flight reading cannot see contention the sweep
   creates). Quantify what the hoisted import actually cost; no timing claim exists yet. Then
   take the 6 suspects above in order.
3. Make the synthetic drivers stop writing the production watchdog log (override HOME and
   USERPROFILE, see `tools/test_hook_replay_isolation.py`) — `tools/test_gsd_autocompact*.py`
   has been quiet since 09-18 17:57, so that pane is done and this is now unblocked. Note the
   synthetic rows already outnumber real ones 2.6:1 in the log.

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
