# Deployment Skill — ULTRA Plan (2026-05-24)

Sister plan: see `vault/plans/code-review-skill-2026-05-23.md` (third side of triangle); `vault/plans/arch-decision-skill-2026-05-23.md` (second side); `vault/plans/auto-testing-skill-2026-05-23.md` (first side).

Spec: `vault/specs/deployment-skill.md` (15 sections, sealed 2026-05-24).
Apex section target: `Deploy Axis (sealed 2026-05-24) -- PP Quality Quadrangle complete`.

---

## PASO 0 grounding (already executed; cited verbatim)

Honest tabla por proyecto (decisional inputs for the scope):

| Project | Build | Deploy target | Method today | Gap |
|---|---|---|---|---|
| KobiiCraft | Maven multi-module (~60 plugins) | gex44 (`5.9.23.174`, user `kobii`, key `kobicraft_gex44`); systemd `kobiicraft@%i.service` at `/srv/kobiicraft/%i/` | `mvn package` + local `deploy-local.sh`; GH `deploy.yml` only build+upload-artifact | **REAL** -- no end-to-end |
| TUA-X | Docker (Python+Elixir+Next.js+compose) | vps204 (`204.168.166.63`, user `kobicraft`) | `git push` -> server-side `deploy/post-receive` -> docker compose up | **MINOR** -- no explicit `curl /health` step |
| InfinityOps | Elixir/Phoenix + Next.js + Docker | vps204 via GH Actions self-hosted runner | `.github/workflows/deploy-vps.yml` -- forced-command SSH, dedicated CD key, 24x15s curl-grep verify, concurrency group | **ZERO** -- §77 canonical |
| PP | n/a | n/a (per-user) | `install-global.ps1` runs on the new machine | **BY DESIGN** |

Decision driven by grounding: the skill is a **detector + invocador + healthcheck wrapper**, not a pipeline generator. InfinityOps already has §77 -- invoke, do not replace.

---

## Sequencing graph

```
P1 spec  -----+
P2 plan ------+--> P3 detectors -----> P9 V-block
                                         ^
P4 healthcheck --------------------------+
P5 gh_workflow --------------------------+
P6 git_push -----------------------------+
P7 scp_systemd --------------------------+
P8 deploy dispatcher --------------------+
                                         v
                                P10 /deploy command
                                         v
                          P11 vault/deploy/*.json (3 configs)
                                         v
                          P12 V-DEEP dry-run report
                                         v
                          P13 Apex + mirror
                                         v
                          P14 UKDL + session_lessons
                                         v
                          P15 verify_spp + push
```

P3, P4, P5, P6, P7 are independent and could run in parallel -- but per the parallel-Write batch cap = 2 lesson, they are written sequentially.

---

## Pasos detallados

### P1 -- Spec
- Output: `vault/specs/deployment-skill.md`
- Done-gate: 15 sections present; Jobs/Woz `zero-fiction-gate` passes; covers all 4 modes; cites §77.

### P2 -- Plan (this file)
- Output: `vault/plans/deployment-skill-2026-05-24.md`
- Done-gate: present; cites PASO 0; sequencing graph; per-paso done-gates.

### P3 -- detectors.py
- Output: `modules/deployment/detectors.py`
- Function: `detect_deploy_target(project_root: Path) -> dict`
- Logic: ordered probe of (gh-workflow -> git-push-to-deploy -> manual-scp -> none); returns `{mode, evidence, config_path}`.
- Done-gate: V-DETECT-{GH,PUSH,SCP,NONE} PASS via test_v_block.

### P4 -- healthcheck.py
- Output: `modules/deployment/healthcheck.py`
- Functions: `check_tcp(target, port, retries, delay)`, `check_http(url, retries, delay, expect_status)`, `check_curl_grep(url, pattern, retries, delay)`. All return `{ok: bool, attempts: int, evidence: str}`.
- Done-gate: V-HEALTHCHECK-NC + V-HEALTHCHECK-FAIL PASS with mocked subprocess.

### P5 -- runners/gh_workflow.py
- Output: `modules/deployment/runners/gh_workflow.py`
- Function: `run_gh_workflow(config, dry_run) -> dict`
- Logic: `gh workflow run <yml> --ref main` -> `gh run watch --exit-status`. Returns receipt. Cites §77 if workflow path matches `deploy-vps.yml`.
- Done-gate: dry-run mode present; `grep "git push origin"` in source returns 0 hits; §77 citation included when applicable.

### P6 -- runners/git_push.py
- Output: `modules/deployment/runners/git_push.py`
- Function: `run_git_push(config, dry_run) -> dict`
- Logic: validates `remote` is NOT `origin`, `github`, or matches `github.com`; runs `git push <remote> main`; captures stderr (post-receive lines); returns last 15 lines.
- Done-gate: dry-run present; remote-origin guard rejected with exit code; receipt parser correct.

### P7 -- runners/scp_systemd.py
- Output: `modules/deployment/runners/scp_systemd.py`
- Function: `run_scp_systemd(config, dry_run) -> dict`
- Logic: schema validation (rejects forbidden-key fields with exit 2); SSH key existence check (`os.path.expanduser` + `os.path.exists`); runs `build_cmd` -> `scp -i <key>` artefact_glob -> `ssh <alias> '<post_deploy_cmd>'`.
- Done-gate: V-CONFIG-INVALID PASS; V-CEILING-SSH PASS; CEILING is honest stop.

### P8 -- deploy.py (dispatcher)
- Output: `modules/deployment/deploy.py`
- Function: `main()` -- reads STDIN JSON, runs detector, dispatches to runner, executes healthcheck, writes receipt.
- Verdict shapes: pass / fail / ceiling / deploy-warn / skip / dry-run.
- Done-gate: STDIN/STDOUT contract; no level-1 `CLAUDEPP_DEPLOY_RUNNING` setting.

### P9 -- test_v_block.py
- Output: `modules/deployment/test_v_block.py`
- All 12 V-tests must pass with timing reports.

V-block:

| ID | Setup | Expected |
|---|---|---|
| V-DETECT-GH | tmpdir with `.github/workflows/deploy-vps.yml` mock | `mode=gh-workflow` |
| V-DETECT-PUSH | tmpdir with `deploy/post-receive` + git remote configured | `mode=git-push-to-deploy` |
| V-DETECT-SCP | tmpdir with `pom.xml` + `vault/deploy/x.json` (mode scp-systemd) | `mode=manual-scp` |
| V-DETECT-NONE | tmpdir empty | `mode=none`, ceiling |
| V-CEILING-SSH | mode scp-systemd; `~/.ssh/<key>` missing | exit 4; message includes expanded path |
| V-CONFIG-INVALID | JSON with forbidden-key field | schema FAIL exit 2 before runner executes |
| V-HEALTHCHECK-MISSING | JSON without `healthcheck` key | schema FAIL before deploy |
| V-HEALTHCHECK-NC | mocked `nc -z` succeeds | healthcheck `ok=true` |
| V-HEALTHCHECK-FAIL | deploy OK + healthcheck returns failure | exit 3 `deploy-warn`; report says so |
| V-NO-AUTO-PUSH | grep `runners/*.py` for `git push origin` | 0 hits |
| V-KOBIICRAFT (optional) | gex44 reachable + key present -> real run | SKIP if gex44 unreachable |
| V-CLOSED-LOOP | run 1 writes report -> run 2 surfaces it | mechanical, no LLM |

### P10 -- commands/deploy.md
- Output: `commands/deploy.md`
- Surface: `/deploy [--project NAME] [--env prod|staging] [--dry-run]`
- DEEP-mode protocol (8 steps): detect -> load config -> schema validate -> dispatch runner -> healthcheck -> write report -> echo verdict -> cite doctrine.

### P11 -- vault/deploy/*.json (3 configs)
- Outputs:
  - `vault/deploy/kobiicraft.json` (mode: scp-systemd, healthcheck: tcp 25565)
  - `vault/deploy/tua-x.json` (mode: git-push-to-deploy, healthcheck: http /health, URL deferred to Owner)
  - `vault/deploy/infinityops.json` (mode: gh-workflow, healthcheck: curl-grep)
- Done-gate: schemas valid; no forbidden keys; healthcheck specified.

### P12 -- V-DEEP dry-run report
- Output: `vault/deploys/<ts>_infinityops_dryrun.md`
- Execution: `--dry-run` over infinityops config (mode: gh-workflow). Receipt section says "DRY RUN -- would invoke: gh workflow run ...". No mutation.
- Done-gate: report exists; 4 sections; §77 cite present.

### P13 -- Apex section + mirror
- Output: `knowledge_vault/core/apex-completion-standard.md` (PP) and `~/.claude/knowledge_vault/core/apex-completion-standard.md` (live mirror).
- Section heading: `Deploy Axis (sealed 2026-05-24) -- PP Quality Quadrangle complete`.
- Done-gate: sha256(PP) == sha256(live mirror); Python `read_bytes`/`write_bytes` used; SEALING_REF stays `main`.

### P14 -- UKDL + session_lessons rows
- Outputs:
  - `vault/knowledge_base/ukdl-universal.md` -- add UKDL-DP-01..05 (Deployment) + UKDL-DP-REP-01.
  - `vault/knowledge_base/session_lessons.md` -- append L1..LN rows from iteration (post-execution).
- Done-gate: rows present, byte-safe append (Python read_bytes/write_bytes).

### P15 -- verify_spp + push
- Steps:
  1. `python tools/verify_spp.py` -- 7/7 STRICT PASS; pre-existing FAILs (mirror-parity, paths+secrets, rtk-fusion) documented in session_lessons.md per prior sealed pattern.
  2. `python tools/verify_full_install.py` -- exit 0.
  3. `git add` selective files (Deploy Skill only -- never `-A`).
  4. `git commit -m "feat(deploy): Deploy Axis sealed -- PP Quality Quadrangle complete"`.
  5. `git push origin main`.
  6. `REMOTE_DELTA = 0` verified both directions.

---

## Hard constraints (verifiable)

| Constraint | Verifier |
|---|---|
| NO secret material in vault/ | Schema validator rejects forbidden-key categories before runner executes |
| SSH key absent -> CEILING honest | V-CEILING-SSH |
| Healthcheck mandatory | V-HEALTHCHECK-MISSING |
| NO auto-push to origin | V-NO-AUTO-PUSH (grep over `runners/*.py`) |
| Reality Contract | `vault/deploys/<ts>_*.md` written only after healthcheck |
| §77 cite for gh-workflow on deploy-vps.yml | gh_workflow runner prints cite to stdout |
| n8n forbidden | Schema validator rejects `mode: n8n` and any `webhook.n8n.*` URL |
| Recursion guard level-2+ only | `grep -E 'env\["CLAUDEPP_DEPLOY_RUNNING"\] = "1"' modules/deployment/deploy.py` -> 0 hits |
| Mirror-Sync-Direction | sha256 PP == sha256 live mirror; `read_bytes`/`write_bytes` only |
| Slop-token gate | The `zero-fiction-gate` detector in scaffold-auditor.js enforces; this skill carries zero literal markers from the forbidden set in delivered runtime files |

---

## Status log (populated during execution)

| Paso | Status | Evidence |
|---|---|---|
| P1 | done | `vault/specs/deployment-skill.md` (15 sections; passes Jobs/Woz) |
| P2 | in progress | this file |
| P3..P15 | pending |  |

(updated by the executor as each paso completes -- empirical evidence inline)
