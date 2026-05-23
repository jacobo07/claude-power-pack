# Plan: Architecture Decision Skill (Arch-Check)

Sealed: 2026-05-23. Sister to `vault/plans/auto-testing-skill-2026-05-23.md`.
Spec: `vault/specs/arch-decision-skill.md`.

## Scope

5 components / 14 micro-commits / 6 V-tests / approximately 700 LOC.

## Sequencing graph

```
P1 spec  ----------+
                   v
P2 plan  --------> P3 build_index.py --> P4 first build --> P5 arch_check.py
                                                                  |
                              +---- V-COLLISION (P6) <------------+
                              +---- V-WARNING  (P7) <-------------+
                              +---- V-CLEAR + V-TIMING (P8) <-----+
                                                                  |
P9 commands/arch-decision.md  -- DEEP mode --> P10 V-ADR <--------+
                                                                  |
P11 jit_skill_loader.py piggyback --> P12 V-CLOSED-LOOP + UKDL    |
                                                                  |
P13 apex section + session_lessons + push (P14 verifies + push)
```

## Plan (clickable, micro-commit per paso)

- [x] **P1** -- Write spec `vault/specs/arch-decision-skill.md`.
      Done-gate: file exists, 15 sections present, contract for STDIN + verdict shapes documented.
      Micro-commit: `feat(arch-check): spec for Architecture Decision Skill axis`

- [ ] **P2** -- Write this plan file.
      Done-gate: file exists with full P1-P14 step list + done-gates + micro-commits.
      Micro-commit: `feat(arch-check): plan + sequencing graph`

- [ ] **P3** -- `modules/arch-decision/build_index.py` (approximately 250 LOC).
      Scans 8 vault paths with weights; emits `vault/.arch-index/index.json` + `arch_check_vocab.json`. Derives concepts from apex section-titles + antipattern filenames + feedback memory first-lines.
      Done-gate: file written; module imports clean (`python -c "import modules.arch_decision.build_index"` exit 0).
      Micro-commit: `feat(arch-check): build_index.py (vault scanner + TF-IDF)`

- [ ] **P4** -- First run of `build_index.py`.
      Done-gate: `vault/.arch-index/index.json` exists, `len(sources) >= 50`. `arch_check_vocab.json` has `len(verbs) >= 18 AND len(concepts) >= 25`. Confirm 8 source classes appear (apex, feedback, gex44_antipatterns, antipatterns, session_lessons, governance, errors, ukdl).
      Micro-commit: `chore(arch-check): build initial index (sources=N concepts=M)`

- [ ] **P5** -- `modules/arch-decision/arch_check.py` (approximately 300 LOC).
      STDIN reader (Windows argv vaccine); entity + concept extractor; relevance scorer (Jaccard 0.3 floor + exact-entity boost); JSON output with verdict + cited context.
      Done-gate: `echo "test" | python arch_check.py --fast` returns valid JSON with `verdict: CLEAR`.
      Micro-commit: `feat(arch-check): arch_check.py fast-mode engine`

- [ ] **P6** -- V-COLLISION + V-COLLISION-2.
      V-COLLISION: STDIN = `"Vamos a montar un workflow con n8n para automatizar X"` returns `COLLISION` with `feedback_no_n8n_ever.md` cited.
      V-COLLISION-2: STDIN = `"quiero que un hook auto-fire un slash command para X"` returns `COLLISION` citing BL-0003 + Zero-Command Standard.
      Done-gate: both prompts return verdict COLLISION + at least one literal source path.
      Micro-commit: `test(arch-check): V-COLLISION verifies veto surfacing`

- [ ] **P7** -- V-WARNING + V-WARNING-2.
      V-WARNING: STDIN = `"voy a escribir 5 archivos en paralelo en un Write batch"` returns `WARNING` citing `feedback_parallel_write_batch_limit`.
      V-WARNING-2: STDIN = `"llevamos meses sin mergear feat a main, ahora lo merge-amos"` returns `WARNING` citing Production Branch Standard.
      Done-gate: both prompts return WARNING + cite the related lesson at Jaccard >= 0.3.
      Micro-commit: `test(arch-check): V-WARNING verifies lesson similarity matching`

- [ ] **P8** -- V-CLEAR + V-TIMING.
      V-CLEAR: STDIN = `"explica este snippet de Rust:\nfn add(a: i32, b: i32) -> i32 { a + b }"` returns CLEAR (no design verbs).
      V-TIMING: 10 runs of V-COLLISION-1 (with index warm). p95 < 3.0 s, p05 < 0.5 s. Output timings to `vault/.arch-index/timings.json`.
      Done-gate: V-CLEAR exits 0 with empty context. V-TIMING p95 < 3.0 s.
      Micro-commit: `test(arch-check): V-CLEAR + V-TIMING (p95=Xs p05=Ys)`

- [ ] **P9** -- `commands/arch-decision.md` (approximately 80 LOC of skill prompt).
      `/arch-decision "<desc>"` invokes `arch_check.py --deep` (60 s budget). Generates ADR via claude.exe (one LLM call). Saves to `vault/decisions/<ts>_<slug>.md` with 6 sections (Context / Decision / Consequences / Alternatives / Vault-conflicts / Lessons-cited).
      Done-gate: command file present; `/arch-decision --help` (dry-run) reports usage.
      Micro-commit: `feat(arch-check): /arch-decision command for DEEP-mode ADR`

- [ ] **P10** -- V-ADR.
      Real run: `/arch-decision "usar Redis como session store en TUAX"`. Wait for ADR file. Verify `vault/decisions/<ts>_redis-sessions-tuax.md` exists with 6 sections + at least one cited source from the index (Redis is not a veto target; expect WARNING-level mentions if any session-store lesson exists, else CLEAR Vault-conflicts but other sections still populated).
      Done-gate: ADR file present, 6 sections, no fabricated source paths (every cited path must exist).
      Micro-commit: `test(arch-check): V-ADR Redis-sessions case study`

- [ ] **P11** -- Extend `tools/jit_skill_loader.py` (approximately 60 LOC added).
      Add design-verb threshold detector (≥2 verbs from vocab). On match, spawn `arch_check.py --fast` with 3 s subprocess timeout. On verdict COLLISION/WARNING, append the context to the existing `additionalContext` payload. Respect `CLAUDEPP_ARCHCHECK_RUNNING=1` (short-circuit CLEAR if set). Respect `CLAUDEPP_ARCHCHECK_DISABLED=1` (opt-out).
      Done-gate: synthetic UserPromptSubmit payload with design verbs + n8n entity returns `additionalContext` containing `ARCH-CHECK`.
      Micro-commit: `feat(arch-check): jit_skill_loader piggyback integration`

- [ ] **P12** -- V-CLOSED-LOOP + UKDL rows.
      Append UKDL-AC-01..AC-04 to `vault/knowledge_base/ukdl-universal.md` (spec / plan / arch_check.py / build_index.py). Run arch_check twice with same prompt; second run should still cite same sources (deterministic). Verify ADR entity tokens appear in next scan via `build_index.py --update` (re-derive).
      Done-gate: 4 new UKDL rows present; second run byte-identical context to first.
      Micro-commit: `docs(arch-check): UKDL-AC-01..04 + closed-loop verified`

- [ ] **P13** -- Apex section + session_lessons entry.
      Append "Architecture Decision Axis (sealed 2026-05-23)" section to `~/.claude/knowledge_vault/core/apex-completion-standard.md` (PP source + live mirror, sha256 verified identical). Append a 2026-05-23 lesson row to `vault/knowledge_base/session_lessons.md` summarising the iteration findings.
      Done-gate: apex contains the new section; live mirror has byte-identical content; session_lessons.md appended row visible.
      Micro-commit: `docs(apex): Architecture Decision Axis sealed`

- [ ] **P14** -- Final verifiers + push.
      Run `python tools/verify_spp.py` (exit 0 expected, 7/7 STRICT-PASS). Run `python tools/verify_full_install.py` (exit 0 expected). Commit snowball. `git push origin main`. Verify REMOTE_DELTA=0 both directions.
      Done-gate: both verifiers exit 0; push succeeds; `git rev-list --count origin/main..main == 0` AND reverse == 0.
      Micro-commit: `chore(arch-check): seal axis + push to origin/main`

## V-block summary

| V-test | Input | Expected verdict | Latency floor |
|---|---|---|---|
| V-COLLISION | n8n workflow prompt | COLLISION + feedback_no_n8n_ever | < 3 s |
| V-COLLISION-2 | hook auto-fire slash | COLLISION + BL-0003 / Zero-Command | < 3 s |
| V-WARNING | parallel 5-write | WARNING + parallel_write_batch_limit | < 3 s |
| V-WARNING-2 | months-old feat merge | WARNING + Production Branch Standard | < 3 s |
| V-CLEAR | Rust snippet explain | CLEAR (empty context) | < 1 s |
| V-TIMING | 10 V-COLLISION runs | p95 < 3 s, p05 < 0.5 s | per-run |
| V-ADR | /arch-decision Redis | ADR file with 6 sections | < 60 s |
| V-CLOSED-LOOP | same prompt x2 | byte-identical second run | per-run |

## Reality Contract

A V-test that does not fire empirically is a paper claim. Every V-test
above MUST produce an artifact on disk (timings.json, ADR file, sample
arch_check JSON output, or build log) before the corresponding paso is
marked `[x]`. Reading "the spec says it works" is not evidence.

The merge to `main` only happens at P14 after both verifiers exit 0 and
all 8 V-tests have produced empirical artifacts. A "classified FAIL" is
still a FAIL.

## Cross-references

- `vault/specs/arch-decision-skill.md` (parent spec)
- `vault/specs/auto-testing-gate.md` (sister axis spec)
- `vault/plans/auto-testing-skill-2026-05-23.md` (sister axis plan)
- `vault/plans/deep-research-agent-2026-05-23.md` (sister axis plan)
- `knowledge_vault/core/apex-completion-standard.md` (axis seal target)
