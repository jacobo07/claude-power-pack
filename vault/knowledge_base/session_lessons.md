# Session Lessons — Atomic Learning

Append-only log of concrete, non-derivable learnings per session.
One entry per `/kclear` with a `lesson` field. Keep each entry short and
self-contained — if a future reader can't grok it without the conversation,
rewrite it.

---

## 2026-04-22 — Shipped 5 MC-OVO cycles on claude-power-pack: sleepless_qa atomic landing (34 fi

**Session:** `kpp-supremacy-v7000-marathon`

Before promoting any inline-one-liner failure to an audit recommendation, run the canonical tool (--help / official CLI). Mistake #52: my ad-hoc script's bug got misattributed to the audited file.

---

## 2026-05-14 — Stop-hook PATH: bare `python` resolves to Store stub on Win11

**Session:** `kobiidistilleros-genesis-v82000`

Stop-chain hooks were emitting "command not found" because `hook-utils.js#getPythonCommand` returned bare `python` on win32. Windows 11's PATH includes a Microsoft Store stub `python.exe` that exits non-zero (it opens the Store), not the real interpreter under `%LOCALAPPDATA%\Programs\Python\Python3*\python.exe`. Inline copies of the same pattern existed in `kobiiclaw-autoresearch.js`, `baseline-translator.js`, `dna-flywheel.js`, `session-init.js`.

Fix: `getPythonCommand()` now probes in priority — `$CLAUDE_PYTHON` → `%LOCALAPPDATA%\Programs\Python\Python3*\python.exe` → `py -3` → bare `python`. Memoized after first resolution. Added matching `getNodeCommand()` returning `process.execPath` to neutralize the same risk for bare-`node` shell-outs. `kobiiclaw-autoresearch.js` (the Stop-chain offender) migrated to call the helper.

**Vaccine:** never write `const x = process.platform === 'win32' ? 'python' : 'python3'` inline; always import the helper. Reviewers reject bare-interpreter execSync templates outright.

---

## 2026-05-14 — Stop-hook schema: no `hookSpecificOutput`, top-level fields only

**Session:** `kobiidistilleros-22-section-singularity-v210000`

Earlier RAM Shield + voice-gate cycles emitted `hookSpecificOutput: {hookEventName: "Stop", additionalContext: "..."}` on Stop events. The harness rejects every such payload with "Hook JSON output validation failed", drops the advisory, and floods the validation log. The schema constraint is: Stop hooks accept ONLY `{continue, suppressOutput, stopReason, decision, reason, systemMessage}` at top level. `hookSpecificOutput` is valid for PreToolUse / UserPromptSubmit / PostToolUse / PostToolBatch — NOT Stop. The canonical re-engagement pattern when a Stop hook needs the model to keep working is `decision: "block" + reason` (see `modules/zero-crash/hooks/context-watchdog.py:209-216`). `systemMessage` is the correct field for UI-visible advisories on Stop (see `modules/zero-crash/hooks/ram-watchdog.js:135-142` and the post-patch `ram-shield.js:213-223`).

**Audit pass:** Glob'd `~/.claude/hooks/*.{js,py}` + `~/.claude/skills/**/hooks/*.{js,py}` and enumerated the 10-entry Stop chain in `settings.json:206-303` by name. Every Stop hook either never used `hookSpecificOutput` or already cited the schema constraint in a header comment. Zero patches needed beyond ram-shield.js (Owner-patched today). Earlier memory entry `BL-0040` incorrectly generalized "additionalContext IS supported on Stop" — that claim was true for PreToolUse, not Stop. Correction landed in this entry.

**Vaccine:** When emitting JSON from a Stop hook, treat any field outside the top-level six as schema-poison. Cite `context-watchdog.py:207-209` in the hook header so future contributors don't re-introduce the bug. `BL-0040` superseded.

---

## 2026-05-14 — Voice gate enforcement: global scope, exit 5, anchor-OR-blacklist

**Session:** `kobiidistilleros-22-section-singularity-v210000`

KobiiDistillerOS v1.2 ships `voice_gate.mode: "enforcing"` in `schema.json`. Validator implementation (`validate.py#_check_voice_gate`) aggregates every materialized section body, strips code fences (so contract docs enumerating the blacklist by name don't trip the gate), and counts hits across two lists:

- `blacklist_candidates` — corporate vocabulary (KPI, synergy, leverage, stakeholder, roadmap, paradigm shift, holistic, …).
- `anchors_candidates` — nostalgic / Refugio-voice tokens (Refugio, MCPE, 2014, cabaña, linterna, Helsinki, KobiiCraft, Andorra, …).

Exit 5 fires **iff** ≥1 blacklist hit AND 0 anchor hits across the **entire** output (global scope per `voice_gate.scope: "global"`). The OR semantic was chosen over AND because:

- A document with anchors + blacklist may be a deliberate translation of corporate-vocabulary readers into Refugio voice (legitimate use case).
- A document with no blacklist + no anchors is "neutral" and shouldn't be punished.
- A document with blacklist + zero anchors is the exact failure mode the gate exists to catch: corporate vocabulary winning, Refugio losing.

**Vaccine:** Voice gates that scan per-section are too strict (most sections legitimately don't reference 2014 / Refugio). Global scope is the right granularity. When wiring the next voice-shaped contract, default to aggregation across the unit-of-distribution (here: the 22-section dataset; for other systems: the PR diff, the commit body, the released chapter).

---

## 2026-05-14 — 22-section schema expansion + Tandas & Partes structural contract

**Session:** `kobiidistilleros-22-section-singularity-v210000`

Schema v1.2.1 expanded the canonical Mother Prompt from 19 to **22 sections** by adding the Sovereignty layer (§14-16: Cognitive Mirror, Decision Traceability, Antifragilidad) and the Cashflow/Telemetría/Outside-the-Box trio (§20-22). §22 was fused at Owner direction: "Inferencia Decisional Exógena & Conocimiento Negativo (Outside-the-Box Time-Saver)" — outside-the-box inference IS the harvest mechanism for inheriting other people's negative knowledge.

A new top-level block `tandas_partes_spec` declares the structural contract every materialized section MUST honor:

- 3 **depth-tandas** (`### Tanda T1` Baseline / `### Tanda T2` Chase-Gain / `### Tanda T3` Síntesis & Ventaja Estructural).
- 3 **orthogonal partes** per tanda (`#### Parte I` Narrativa / `#### Parte II` Estructura / `#### Parte III` ROI).
- Validator enforces both marker regexes (`tanda_heading_regex`, `parte_heading_regex`) per section file. Missing any tanda or parte → exit 1.

The §2 native "POR TANDAS" semantic (quick-wins / structural / arquitectura) collapses cleanly onto the depth-tanda axis: T1 = quick wins, T2 = structural, T3 = arquitectura. No duplication, no conflict.

**Vaccine:** When a schema names a structural concept twice (the §2 title "POR TANDAS" pre-existed; the structural layer reuses "Tandas"), explicitly map the older concept onto the newer abstraction in BOTH the schema description block AND the Mother Prompt instructions. Future readers will hit the collision and need the bridge documented inline. Done here in `parts/sleepy/distiller.md` §2 body and `schema.json#description`.

---

## 2026-05-14 — RAM Shield (BL-0033 RAM channel)

**Session:** `kobiidistilleros-consolidation-v82001`

Two-stage RAM management for 30+h unattended sessions. `ram-watchdog.js` already advised at 1500 MB ("consider /kclear"). New `ram-shield.js` adds an *active* 2 GB trip: append a timestamped snapshot block to `<cwd>/vault/progress.md` (or `.claude/progress.md` fallback, or `~/.claude/state/progress.md` global), emit a `systemMessage` carrying the exact `/compact focus on …` line (task summary auto-derived from `git log -1 --pretty=%s`), and emit `hookSpecificOutput.additionalContext` with the literal `CONTEXT THRESHOLD CROSSED` phrase so BL-0033 fires Claude's next-turn `/compact` emission. Live empirical: 20 claude.exe procs at 7 GB tripped cleanly on smoke (synthetic session ID kept the real session's debounce flag clean).

**Schema-field uncertainty:** `ram-watchdog.js` header claims `additionalContext` is rejected on Stop; memory `BL-0040` claims it IS supported. `ram-shield.js` emits BOTH `systemMessage` (reliable) and `additionalContext` (BL-0033 channel) — if the harness drops the latter, the former still surfaces the human-readable instruction. **Vaccine:** when two governance artifacts disagree on a harness schema, ship both and let the harness pick.

**Process-name resolution:** `tasklist /FI "IMAGENAME eq claude.exe"` matches Claude Code on Windows (verified, not inferred — `ram-watchdog.js` already uses it). `process_name_candidates` config array `["claude.exe","claude","claude-code"]` covers Posix + future renames.

**CWD-relative snapshot path:** Stop hook stdin carries `cwd`; resolve project-local first (`vault/progress.md` then `.claude/progress.md`), global fallback last (`~/.claude/state/progress.md`). Never assume `process.cwd()` is the project root inside a hook.

---

## 2026-05-15 — Verdict-B root cause: stale doctrine oversold the engine; the fix was one function

**Session:** `kobiidistilleros-v1.2-sync-artifact-regeneration`

`/ovo-audit` stamped **Verdict B** (delta_id=66c04ee7): the 22 files in Power Pack `vault/distilled/Dataset_KobiiDistillerOS_1.txt/` failed 43 Tandas/Partes marker checks. The first plan (and the `oneshot-architect-auditor`) trusted the sealed doctrine `docs/KOBII_PHILOSOPHY/KOBIIDISTILLER_OS_v1.md` (v220000), which claimed the canonical engine was a 19-section gap-marked stand-in needing a full synthesizer rewrite. **Empirical probe contradicted the doctrine on three points:** (1) `prompt_madre.py` was already v1.2 — 22 sections, 7/6/9 tiers, titles verbatim, `is_gap_section()` False for all; (2) `_bodies_per_section()` already held real warm-tone content for all 22; (3) the engine already emitted 22 artifacts at exit 0. The ONLY defect: `orchestrator._build_section_body` dumped `payload["decision"]` as flat prose and never emitted the `### Tanda T1/T2/T3` × `#### Parte I/II/III` skeleton the validator requires. The stale e2e test (`test_distill_emits_19_artifacts`) and the doctrine were both written against a pre-v1.2 engine and never re-baselined — they became the misleading "source of truth."

Fix: rewrote one ~45-line function into a deterministic 3-tanda × 3-parte composer wrapping the existing distilled content (zero tokens, zero fabrication, ad-hoc-heading sanitize for Gap-1 collision, §16 kill-switch injected per contract). Re-baselined the e2e suite (9/9 green). Validator: exit 0, "22 sections validated against schema v1.2.1". Wired `tools/distiller/run.py distill` → subprocesses the canonical engine with explicit `cwd`+`PYTHONPATH`, DRY_RUN default, `$KOBII_DISTILLER_ENGINE_ROOT` cross-repo contract (Mistake #36), loud exit-3 if unset (no silent LLM fallback — Mistake #37).

**Vaccine:** A doctrine/README/sealed-claim about a component's capability is a HYPOTHESIS, not evidence (Mistake #51). Before scoping work off a capability claim — especially one that says "X is a stub / gap-marked / needs a rewrite" — run the component's own test suite AND its canonical validator against real input. The audit found the doctrine wrong only because Phase A ran the engine before believing the doctrine. When a test asserts an old shape (19) and the code produces a new shape (22), the test is stale debt that actively misleads the next reader — re-baseline it in the same commit, never leave it red-or-lying. `BL`-style capability claims in sealed docs must carry the date + commit of the last empirical verification, else they are presumed stale.

---

## 2026-05-15 — Jobs & Woz global guardians: a memory said "won't work this session"; the runtime said it just did

**Session:** `jobs-woz-global-quality-guardians` (/ultra ONESHOT)

Built two global subagents (`steve-jobs` design/UX, `woz` engineering) + an enforced PreToolUse gate: `tools/quality_audit.py` (domain-routes UI→JOBS / code→WOZ, exit 5 on slop, appends a permanent prohibition to `~/.claude/knowledge_vault/global_vetoes.md`) wired through `~/.claude/hooks/jobs-woz-gatekeeper.js` as the 11th PreToolUse block in `settings.json`.

**The headline lesson — empirical reality beat a stored memory, again.** Memory `feedback_settings_session_load.md` / `feedback_agent_files_cold_load.md` asserts hooks+agents cold-load at session start and a mid-session settings edit "does not activate until /restart". Phase-7 was scoped (Owner answer #3) as a runnable-checker fallback *because* of that memory. Then the very next `Write` of a `Coming Soon` fixture was **blocked live, this session**, by the just-wired gatekeeper — `permissionDecision: deny`, JOBS veto emitted, ledger auto-appended. The cold-load memory did not hold for a newly-appended PreToolUse block on this harness build. This is the same failure mode as the KobiiDistiller verdict above: a stored capability claim is a HYPOTHESIS; the runtime is the only source of truth. Phase-7 verification was upgraded on the spot from "runnable checker" to "observed live enforcement" — strictly stronger evidence (Ley 25).

**Three engineering bugs caught by verify-before-claim (none shipped):**
1. `_skip()` auto-skipped anything under `%TEMP%` → the hook's temp-staged copy made the gate a silent no-op (passed ALL slop). Fixed by giving `scan()` a `logical` arg: read the temp copy, classify/skip by the *real* target path. Smoke test caught it before the settings wire.
2. Edit tool has **no `content` field** (audit gap #1) — `tool_input.new_string` for Edit, `edits[].new_string` for MultiEdit. A naive `tool_input.content` reader would no-op on every Edit.
3. Self-veto risk: the detector's own token list + the manifesto's sample audit contain literal slop strings → basename skip-set (`quality_audit.py`, `JOBS_MANIFESTO.md`, `session_lessons.md`, `scaffold-auditor.js`, …) + dir-fragment skips for `/.claude/agents|hooks/` and `/knowledge_vault/`.

**Secondary:** a linter re-added a UTF-8 BOM to `settings.json` after my Edit. Raw `JSON.parse` chokes on BOM; the harness + `utf-8-sig` do not (proven — the hook fired). Correct response was NOT to re-edit the harness file to fight the linter (anti-thrash + don't-fight-tooling), but to validate the BOM-aware way and record the interaction.

**Vaccine:** When a memory says "X won't take effect until /restart", treat it as a hypothesis and design a cheap live probe into the same session — do not pre-emptively downgrade the verification plan around an unverified constraint. A self-enforcing gate must be smoke-tested on a temp fixture **before** it is wired into the harness, because once live it will (correctly) block you from creating the very slop fixtures you'd test it with — and it will also block any delivered file containing the literal tokens, so meta/governance files MUST be on an explicit skip-set or the gate eats itself. Cross-tool BOM on harness JSON is tolerated by the harness; validate with `utf-8-sig`, never thrash the file to strip it.

---

## 2026-05-15 — Total Recall: classifier-gated config, partial-SQLite recovery, the 11→434 bug

**Session:** `total-recall-sqlite-kernel-stabilization` (/ultra ONESHOT v3)

Three durable lessons:

**1. The auto-mode classifier hard-gates `settings.json` self-modification regardless of tool — explicit Owner authorization is the unlock, and a Python rewrite ≠ the Edit tool.** The `.DISABLED` Stop-hook purge was denied twice via the Edit tool ("self-modification of agent startup config", reproduction not classifier-visible). I correctly STOPPED (2-fail pivot) and deferred to the Owner. Once the Owner *explicitly* authorized "rewrite settings.json via Python/Bash" in a classifier-visible turn, a `python -c` json-filter rewrite (read `utf-8-sig`, drop blocks whose command contains `.DISABLED`, write plain utf-8, assert `bytes[0:3]` unchanged, backup first, validate with python AND node, then re-exec every Stop+SessionStart hook → 0 MODULE_NOT_FOUND) succeeded. The audit also caught a **third** orphaned ref (`SessionStart → lazarus_revive.py.DISABLED`) the 2-block scope missed — always enumerate ALL events, not just the reported one.

**2. SQLite "malformed image" is rarely all-or-nothing — `count(*)` and `LIMIT 5` can succeed while a deeper fetch throws mid-stream.** First build recovered **11** turns; probing one DB showed `cursorDiskKV` had **175** rows but the connection raised `DatabaseError: database disk image is malformed` on the 3rd query. The original except fell back to `ItemTable` (metadata only) and discarded the file. Fix that took 11→**434** turns across 116 DBs: (a) fetch row-batches in a loop so a mid-stream malformed page keeps prior rows; (b) **always byte-scrape every copied DB as a recovery FLOOR** (regex over raw bytes survives malformed pages), dedup on `(composerId,bubbleId)` so the clean parse wins and scrape only fills refused pages; (c) flag DEGRADED only when the clean parse failed (honest manifest: 2 truly-degraded, not 116). Cursor chat lives in `cursorDiskKV` (`bubbleId:%`→`.text`,`.type` 1=user/2=asst), **not** `ItemTable` `composer%` (that's headers) — verify table/key against a real DB before trusting a query.

**3. WAL is not optional and temp connections must close in `finally`.** A locked live `state.vscdb` had a `-wal` (4.3 MB) **larger than the main DB**; `immutable=1` ignores the WAL → silent data loss. Copy the `.vscdb`+`-wal`+`-shm` trio and open RO *without* immutable so SQLite replays the WAL (immutable only as the corrupt-file fallback). A shared `TemporaryDirectory()` raised `WinError 32` on cleanup because a sqlite connection leaked on an exception path — close in `finally`, `mkdtemp` + `rmtree(ignore_errors=True)`.

**Bonus pitfall:** a single-quoted bash heredoc carrying a Windows path in a Python triple-quoted string died on `\U` (`unicodeescape`). For data files with embedded `C:\Users\...`, write via the Write tool (raw content) or raw-string/forward-slash — never paste Windows paths into a heredoc'd non-raw Python literal.

**Vaccine:** Partial SQLite corruption demands a recovery FLOOR (unconditional byte-scrape + dedup), not a try/except that trusts a clean parse — `count(*)` succeeding is not proof the rows are readable. And a config-mutation denial is a STOP-and-ask boundary, not a try-three-tools puzzle; the unlock is explicit classifier-visible authorization, after which the *non-Edit* path (scripted rewrite) is legitimate, not a bypass.

---


## 2026-05-15 (addendum) — Kernel re-verification: a throwing probe cannot return CLEAN

**Session:** `sovereign-miner-v2` (/ultra ONESHOT, resumed post-compaction)

**Finding:** Re-ran the hook kernel scan over all 30 referenced hooks. settings.json had **zero** `.DISABLED` refs and parsed valid — consistent with the prior Total Recall turn's scripted rewrite already having sealed it (no broken entry to "fix"; honoring "no alteres la lista salvo los rotos" meant *no settings.json edit at all*). Only real action: purge the 3 dead disk orphans (`lazarus_revive.py/.heartbeat.js/.janitor.js.DISABLED`, all 1-line `exit(0)` stubs).

**Vaccine:** A subprocess-probe that decodes child stderr with the Windows default `cp1252` will raise `UnicodeDecodeError` mid-scan on the first hook emitting non-cp1252 bytes — and a "BROKEN 0 / CLEAN" verdict printed *after* that throw is untrustworthy because the throwing child's stderr was never inspected. Always decode probed output as `utf-8, errors="replace"` and assert `probed == total` before trusting a CLEAN verdict. "The loop finished" ≠ "every unit was actually checked" (Mistake #17 class).
