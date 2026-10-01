# KSR Trait + Maturity Profile (raw harvest)

- repo: `C:\Users\User\Desktop\Cursor Projects\Wii Projects\KobiiSports Resort\CursorProjects`
- HEAD: `14f7840ce0b529b8c231121ddff80cbebd56348a` (2026-10-01, "backlog: Owner STOP 2026-10-01 - all 4 KSR missions halted, remaining work as KSR-B-060..072")
- date: 2026-10-01 | mode: read-only | KobiiCraft repos NOT read

## Taxonomy
Levels: L1 WORKS · L2 SURVIVES FAILURE · L3 OPERABLE · L4 EVOLVABLE · L5 PRODUCT · LG GOVERNED
Traits: T-LIVE-SERVICE, T-PERSISTENT-USER-STATE, T-CONCURRENT-USERS, T-REMOTE-DEPLOY, T-CONTENT-HEAVY, T-BUILD-ARTIFACT, T-LOCALIZED, T-AI-PIPELINE, T-ECONOMY, T-EXTERNAL-INTEGRATIONS, T-CONSTRAINED-TARGET, T-UI-SURFACE, T-MODDING-A-BINARY, T-PLAYABLE (+ added below if needed)
Status: LIVE (evidence it runs) / BUILT-UNPROVEN / DOC-ONLY

Observation (ARCHITECTURE.md:26-28, SDD-OS scaffold 2026-07-26): "Test directory: not found", "CI configuration: not found", 4000 source files, Make-driven.

## 1. What KSR is
- A **Wii homebrew mod of a retail game**: a Kamek C++ module (`Caddie_PAL.bin`) injected into the retail Wii Sports Resort PAL disc (RZTP01), adding ~14 new sports, a hub, coin economy, ranked ladder and a Mii renderer on top of the retail binary. (CLAUDE.md:3-8, 16-21; tools/caddie/src/main.cpp ~10,136 lines + tools/caddie/src/kobii/*)
- Shipped artifact is a patched disc image (WBFS) built by `inject_kamek_into_wbfs.py` / `inject_kamek_with_dol_swap.py`; golden DOL md5 pinned (BUILD_COMMANDS.md:21-29, ADR-010 in CLAUDE.md:8).
- Target is a bare 2006 console (PPC 750CL, 24 MB MEM1, 64 MB MEM2), no malloc per frame, static memory only (CLAUDE.md:6-7). The only "runtime" is Dolphin on a remote GEX44 host or the Owner's real Wii; no CI on the game (ARCHITECTURE.md:26-28: no test dir, no CI at repo root).
- Dominant activity in 2026-09 is **reverse engineering / reconstruction** (IOS address conflicts, Page-2 menu seam, KEOS decomp missions, source-linked DOL rebuild ADR-010), supported by an unusually heavy governance layer (UKDL HARD-RULES, 111 RULEs, ADR-001..010, 88 lessons).
- 2026-10-01: Owner STOP halted all 4 active missions (decomp, gex44match, srclink, p2w25) and turned remaining work into KSR-B-060..072 (.ksr_vault/frontier/BACKLOG_OWNER_STOP_20261001.md:1-32).

## 2. TRAITS (paths relative to repo root; `caddie` = tools/caddie)

Rule: a trait is PRESENT only if the PRODUCT (the Wii module/disc) or the repo's delivery chain really has it; dev-tooling-only occurrences are PARTIAL with the scope stated.

| trait | verdict | evidence |
|---|---|---|
| T-LIVE-SERVICE | **ABSENT** (for the product) | The game is an offline disc image. CLAUDE.md:90 says the Phoenix/OTP deploy standard applies to "web companion, leaderboard, telemetry sink, save-sync API" and "NOT to the Wii Homebrew Kamek hot-path" - i.e. such services are hypothetical. `vps_deploy/kobiisports/PIPELINE_STATE.md:3-4` is frozen at 2026-03-21 "INITIAL SETUP", cycle #0; Content pipeline "Videos processed: 0". KEOS gateway on VPS (KSR-B-041/042) is dev tooling, not a player-facing service. Only repo "service" in CI is a GitHub-pages docs site (`caddie/.github/workflows/website.yml:1-33`, upstream Kamek repo docs). |
| T-PERSISTENT-USER-STATE | **PRESENT** | `KobiiSaveData` NAND file `kobii.dat`, magic 0x4B4F4249, version 1..10 (`caddie/src/main.cpp:1118,1443-1445,1535-1536`); coin balance, tokens, ranked W/L, per-sport high scores (main.cpp:1100-1107); `WriteKobiiSave()` called at ~25 game-end sites (main.cpp:9368-9803); extra files `kobii_mii.dat`, `kobii_log.dat` (kobii_klog.cpp:132-135). No checksum/atomic-rename on the save (main.cpp:1555-1564 opens, seeks 0, overwrites in place). |
| T-CONCURRENT-USERS | **PARTIAL** | No server-side users. Local couch multiplayer only (Couch Ranked, main.cpp:1144-1151). LAN UDP transport written and "production-ready" per ADR-001 (`.ksr_vault/decisions/ADR-001-net-workstream-closure.md:30-45`) with `KobiiNetLiveTick` "code-complete" but never observed executing (same file:24-28). Net code in `caddie/src/kobii/kobii_net.cpp` is forensic/probe-gated (kobii_net.cpp:1895, 2028). |
| T-REMOTE-DEPLOY | **PARTIAL** | Delivery to *players* is a hand-carried WBFS (BUILD_COMMANDS.md:85-109), no remote prod. But there IS a remote build/test substrate: GEX44 Hetzner box (Dolphin headless) with md5-shielded deploy (`infra/gex44/ksr_deploy.sh:10-16,47-69`), queue-only access (RULE-090), dispatcher, slot ledger (`tools/kobishield/slot_ledger.py:1-24`), and a VPS for KEOS (KSR-B-035/042). HARD-RULES triggers 2 ("deploy/boot on real hardware") treat the Owner's physical Wii as the "prod". |
| T-CONTENT-HEAVY | **PRESENT** | Disc is 880,803,840 B WBFS (ADR-010 §3.3); 19-row sport registry (main.cpp:774-793); asset pipelines `asset-pipeline/`, `game-ready-assets/`, `tools/brres_autopsy.py`, N4/N8 build-time BRRES gate (CLAUDE.md:46-49); `governance/ASSET_LEDGER.md`; WSR corpus extraction (`tools/rvl_corpus`, `KSR_RVL_FST_CENSUS.md`). Content authoring is mostly reuse of retail WSR assets + model/texture injection, not a CMS. |
| T-BUILD-ARTIFACT | **PRESENT** | `python make.py --region PAL` -> `Caddie_PAL.bin`+`.map`; WBFS inject with `--verify`; golden DOL md5 `84d5ab24...` pinned (BUILD_COMMANDS.md:10-29,85-109); disc-identity gate (`tools/pack/verify_delivery_identity.py:1-50`). ADR-010 adds a byte-verified relink path (sha256 `855e4ffe...`). |
| T-LOCALIZED | **ABSENT** | No locale/language-select code in module: grep over caddie/src for localisation/language/i18n returned only incidental hits ("translation units", main.cpp:335,486,5513). HUD strings hard-coded English (`Sp2::PrintOutline("GET READY"...)`, main.cpp:6090). Retail-region PAL only (no other region build path in BUILD_COMMANDS.md). |
| T-AI-PIPELINE | **PARTIAL** (dev-side only) | Product contains no AI. Dev side: KEOS autopilot/agent harness (`tools/keos/*.py`, `.ksr_vault/frontier/KSR_BACKLOG.json` KSR-B-040..043), `tools/kobiiclaw/*` (self_healer, vision_oracle), `ai-pipeline/orchestrator.py` whose maintenance path literally says "For now, just report" (orchestrator.py:24-27) = stub. Real model credentials absent (KSR-B-041, status ABSENT). |
| T-ECONOMY | **PARTIAL** | In-game currency KobiiCoin: add/spend/saturation, refusal feedback, ranked payout (main.cpp:1139-1186,1205-1234), persisted via save v7+. Local single-player u32 only, no real money, no server authority, no anti-tamper; shop is "future UI" (main.cpp:1131-1133). |
| T-EXTERNAL-INTEGRATIONS | **PRESENT** | Dolphin (headless, GEX44), wit/Wiimms tools (BUILD_COMMANDS.md:115-120), devkitPPC/Kamek/mwcceppc (`caddie/tools/mwcceppc.exe`), Hetzner Robot API (RULE-102), jadx/DTK/GNU ld 2.45.1 (ADR-010 §2), RevoSDK/NAND/IOS on-console (kobii_net.cpp:30-76), Hermes/KEOS gateway. None is a customer-facing third-party API. |
| T-CONSTRAINED-TARGET | **PRESENT** (defining) | PPC 750CL, 24 MB MEM1/64 MB MEM2, 16.6 ms frame, no per-frame malloc, no double (CLAUDE.md:6-7); module size budget `.ksr_vault/binary_budget.csv`, `tools/governance/size_gate.py`; stack/GX FIFO rules (CLAUDE.md:10-14); HR-MMIO-01 watchdogs (UKDL/HARD-RULES.md:80-120). |
| T-UI-SURFACE | **PRESENT** | Hub + 2 sport pages, GX2D overlay, Sp2 text, NW4R layout, Page-2 native card seam (`caddie/src/kobii/kobii_page2_*.cpp`, ADR-007/008/009), TopBar/ranked badge (main.cpp:1243+). Rendered via retail engine; no web UI of its own. |
| T-MODDING-A-BINARY | **PRESENT** (defining) | Kamek module relocated into retail WSR `main.dol` (golden DOL, PAL.txt symbol table `caddie/externals/PAL.txt`), hook-by-address, DOL byte-verification doctrine (ADR-010), silicon provenance gate (`tools/pack/silicon_safety_check.py:1-28`), reconstruction/decomp programme (DTK/KEOS missions). |
| T-PLAYABLE | **PARTIAL** | 19 sports registered SPORT_READY (main.cpp:774-793) and AUTOTEST canary reaches init() for page-1 READY sports (`caddie/test/run_at_canary_ci.py:1-23`); but silicon boot of the hub is unproven: KSR-BUG-02 "`+` edge does not reach the hub" (`KSR_GAP_REGISTRY.md:12-17,40-45`), KSR-B-006 "unblocking event" NOT_STARTED, ADR-002: headless full-playthrough RED-NOT-VIABLE because `KobiiOnCalculate` never ticks headless (ADR-002:7-21). Registry has 222 audited systems, 192 not IMPLEMENTED (KSR_GAP_REGISTRY.md:47). |
| T-REVERSE-ENGINEERED-SUBJECT (new) | **PRESENT** | Definition: the project's correctness depends on facts about a binary it does not own that must be discovered and evidence-graded. Evidence: FIRST_PIXEL_FRONTIER (25 hypotheses), ADR-004/006/007, retractions of IOS_* addresses (kobii_net.cpp:26-29), HR-IOS-01/02, RULE-105, `tools/forensics/*`. |
| T-SCARCE-SHARED-HARDWARE (new) | **PRESENT** | Definition: a budgeted, shared physical resource gates verification. GEX44 boot quota 6/24h (RULE-097/slot_ledger.py:21-24), RULE-102/103/111 (scarce_resource_ledger), Owner's single physical Wii as silicon oracle (HR-MMIO-01 item 5-6). |

## 3. EXISTING CAPABILITIES (paths relative to repo root; `caddie` = tools/caddie)
Status key: LIVE = evidence it ran/runs; BUILT-UNPROVEN = code/config exists, no evidence of a successful run in its real context; DOC-ONLY = prose/spec/empty dir.

### KSR-01 Kamek module build
level: L1 | does: `python make.py --region PAL` produces `Caddie_PAL.bin` + `.map`, copies golden DOL verbatim | evidence: BUILD_COMMANDS.md:10-29; caddie/make.py | status: LIVE (local host only; no devkitPPC on GEX44/VPS, KSR-B-031)

### KSR-02 WBFS injection with verify
level: L1 | does: inject module (and optionally swapped DOL + matched map) into a base WBFS, `--verify` | evidence: BUILD_COMMANDS.md:85-113; tools/pack/inject_kamek_into_wbfs.py, inject_kamek_with_dol_swap.py | status: LIVE (wit not on PATH; scripts search WIT_CANDIDATES, BUILD_COMMANDS.md:115-120)

### KSR-03 Frame-deferred BootStageGate
level: L1 | does: one init operation per phase, frame 0 no IO, avoids boot-burst hang | evidence: UKDL/HARD-RULES.md:50-76 (KSR-WII-BOOT-001), main.cpp ~:1319 refs `KobiiBootStageGate` | status: LIVE on silicon (GREEN real Wii RZTP01 2026-06-18, evidence 20260618_182149.mp4, HARD-RULES.md:72-76)

### KSR-04 19-row sport registry and sport init chain
level: L1 | does: table of sports with Init fn, page, state READY/RESERVED, variants | evidence: caddie/src/main.cpp:720-793 | status: BUILT-UNPROVEN (reaches init under Dolphin AUTOTEST only; hub unreachable on silicon, KSR_GAP_REGISTRY.md:12-17; KSR-B-006 NOT_STARTED)

### KSR-05 Golden DOL pin + determinism verifier
level: L1 | does: md5 `84d5ab24...` shipped DOL pin; `dol_determinism_verify.py` classifies every diff as loader_body/hook/new, UNKNOWN fails | evidence: BUILD_COMMANDS.md:21-29,72-83; tools/forensics/dol_determinism_verify.py | status: LIVE

### KSR-06 Versioned, forward-compatible save schema
level: L2 | does: magic+version 1..10, zero-init struct then version-gated field reads (N11 Rule 3), old saves load | evidence: main.cpp:1414-1418,1443-1481,1535-1536; .ksr_vault/lessons/PILLAR_36_SCHEMA_MIGRATION.md | status: LIVE (code path run on real Wii per silicon boots; no CRC, in-place overwrite - see gaps)

### KSR-07 Save on every game end
level: L2 | does: `WriteKobiiSave()` at ~25 exit/settlement sites so crash between games loses nothing | evidence: main.cpp:3506,3739,9368-9803,10314; CLAUDE.md:20 | status: LIVE

### KSR-08 Deferred boot-time NAND write
level: L2 | does: Mii/stats write deferred off H&S->title boundary, flushed at first real save once NAND proven ready | evidence: main.cpp:1113-1117,1568-1569 (FEAT-RZTP01-BOOT-FIX 2026-06-12) | status: LIVE (silicon GREEN 2026-06-18)

### KSR-09 Preflight null-guard macros
level: L2 | does: KOBII_PTR_GUARD / _RV log `[N5] NULL tag @file:line` and return instead of faulting (RULE-084) | evidence: main.cpp:64-81; .ksr_vault/rules/RULE_084_NULL_GUARD.md | status: LIVE

### KSR-10 MD5-shielded remote deploy
level: L2 | does: pre-prune, free-space floor 2000 MB, scp, mandatory md5 handshake, delete corrupt remote file, GREEN/RED verdict | evidence: infra/gex44/ksr_deploy.sh:10-16,47-69 | status: LIVE (born of v20000.53 silent-truncation incident)

### KSR-11 Evidence durability gate (RULE-108)
level: L2 | does: grades each run report COMPLETE_PRIMARY..MISSING_PRIMARY, DECLARED_UNAVAILABLE as honest escape; `--strict`, `--selftest` | evidence: tools/governance/evidence_durability_gate.py:1-40; KSR-B-020 (7 MISSING_PRIMARY found by it) | status: LIVE (manual only, KSR-B-022 MANUAL)

### KSR-12 Mission HALT / STOP-file kill switches
level: L2 | does: CAS-transition mission to HALTED with no `budget:` so never renewed; `KEOS_AUTOPILOT.STOP` pauses autopilot; resume only by Owner | evidence: .ksr_vault/frontier/BACKLOG_OWNER_STOP_20261001.md:1-46 | status: LIVE (exercised 2026-10-01)

### KSR-13 Symbolised crash handler
level: L3 | does: on-console exception screen prints SRR0/LR/back chain with MapFile::QueryTextSymbol; host `kamek_addr2line.py` resolves | evidence: caddie/src/caddie/kernel/caddieException.cpp; BUILD_COMMANDS.md:111-113; ADR-004 verbatim dump with build banner | status: LIVE

### KSR-14 Init-transparency logging (N1) + FZDIAG breadcrumb ring
level: L3 | does: every early return logs reason; on-screen breadcrumb overlay (FZDIAG), OSReport tags | evidence: CLAUDE.md:44-45; main.cpp:6646 `KSR_FZDIAG`; RULE-106 | status: LIVE (note RULE-106: flag toggle changed the binary and masked a boot bug)

### KSR-15 KLOG session recorder + Tier-A flight recorder
level: L3 | does: bounded BSS ring, OVERFLOW accounting, CRC32, host parser `tools/kados/klog.py` is the authority (19/19 gate) | evidence: caddie/src/kobii/kobii_klog.cpp:1-64,82-135,327-331; kobii_kados_flight_recorder.cpp | status: BUILT-UNPROVEN (flag KSR_KADOS_KLOG; header says persistence leg deliberately absent at writing; image dies at power-off)

### KSR-16 GEX44 slot ledger + lease
level: L3 | does: derived balance = AUTHORIZED - CONSUMED, refuses stored totals, cross-pane lease TTL 180 min | evidence: tools/kobishield/slot_ledger.py:1-40; RULE-111; GEX44_SLOT_LEDGER.json seq 9,11 cited in KSR-B-030 | status: LIVE

### KSR-17 Dispatcher queue mandate + drift watch
level: L3 | does: all GEX44 work via queue (RULE-090), drift check (RULE-101), daemon-reload discipline (RULE-099), job types in `job_commands_kobii.py` | evidence: .ksr_vault/rules/RULE-090/099/101; tools/kobishield/job_commands_kobii.py + test_job_commands_kobii.py; KSR-B-030 resolved 2026-09-23 | status: LIVE (was INACTIVE Jul-Sep 2026)

### KSR-18 KobiiMii kill switch
level: L3 | does: RFL render override, OFF by default, activates only on stated conditions | evidence: caddie/src/kobii/kobiimii_killswitch.cpp:1,28,204-243 | status: BUILT-UNPROVEN

### KSR-19 Hardware failure triage + power-persistence runbooks
level: L3 | does: tiered T1-T3 escalation for GEX44 non-boot, ban on idle-poweroff timers | evidence: .ksr_vault/rules/RULE-102:28-33, RULE-103, RULE-104 | status: DOC-ONLY (runbook text; born of 2026-04-19/20 incidents)

### KSR-20 Forensic reflex arc tooling
level: L3 | does: crash addr -> addr2line/objdump/PAL.txt lookup, field_xref, bl_callers, vtable atlas, prolog audit | evidence: CLAUDE.md:65-81; tools/forensics/* (29 files); caddie/externals/PAL.txt | status: LIVE

### KSR-21 AT_CANARY menu CI
level: L4 | does: build AUTOTEST, md5-deploy, inject WBFS on GEX44, boot headless input-free, exit code = firmware's own `[AT_CANARY] VERDICT` | evidence: caddie/test/run_at_canary_ci.py:1-50; infra/gex44/at_canary_v69_capture.sh | status: LIVE (v20000.69) but only OnConfigure-level (ADR-002)

### KSR-22 Tool test suites + mutation ledger
level: L4 | does: 66 `test_*.py` under tools/ (governance=19, keos=15, ...), `gx_mutation_ledger.json` drives mutants against gx gates | evidence: tools/governance/gx_mutation_ledger.json:1-15; tools/governance/test_gx_*.py; tools/keos/test_*.py | status: LIVE for tooling; ZERO tests for the Kamek C++ itself except caddie/test pins (test_kobii_mii_stats.cpp, *_pin.py, *_gate.py)

### KSR-23 genomic_lint
level: L4 | does: mistake registry -> grep rules, post-compile pre-commit gate | evidence: tools/governance/genomic_lint.py:1-20; CLAUDE.md:72 | status: LIVE

### KSR-24 Binary size/budget gate
level: L4 | does: last retail-prod row of `binary_budget.csv` is the baseline; flags size drift (explicitly NOT layout-shift) | evidence: tools/governance/size_gate.py:1-25; .ksr_vault/binary_budget.csv | status: LIVE

### KSR-25 Compile-flag gating with zero bytes when off
level: L4 | does: probe/forensic code behind `KSR_*` flags; retail build byte-invariant | evidence: UKDL/HARD-RULES.md:99-103; kobii_klog.cpp:59-63; silicon_safety_check.py (bans flags for shipping) | status: LIVE

### KSR-26 Delivery identity gate
level: L4 | does: MATCH/MISMATCH/INCONCLUSIVE whether the disc carries the module the build just made | evidence: tools/pack/verify_delivery_identity.py:1-50 | status: BUILT-UNPROVEN (manual call; no evidence it is wired into the play/inject path)

### KSR-27 Byte-verified source-linked DOL (ADR-010)
level: L4 | does: R0 relink of 877 DTK objects reproduces retail sha256 `855e4ffe...` with positive+negative controls | evidence: .ksr_vault/decisions/ADR-010:22-30,39-53 | status: BUILT-UNPROVEN (R0 PASS reported; address-stability gate and WBFS sys/main.dol injector "do not exist yet", ADR-010 �4; srclink Phase 5 boot NOT_STARTED, KSR-B-066)

### KSR-28 Release / rollback / validation pipelines
level: L4 | does: nothing - `pipelines/release`, `pipelines/rollback`, `pipelines/validation` are empty; only `pipelines/prebuild/PREBUILD_VALIDATION_PIPELINE.md` | evidence: directory listing 2026-10-01 | status: DOC-ONLY

### KSR-29 pre-commit hooks (nested caddie repo)
level: L4 | does: trailing-whitespace, end-of-file, mixed-line-ending only | evidence: caddie/.pre-commit-config.yaml:1-7 | status: BUILT-UNPROVEN (installation not evidenced; no code checks)

### KSR-30 Coin economy, ranked ladder, skill-curve payout
level: L5 | does: KobiiCoinAdd/Spend with saturation + refusal sound, W/L tiers Bronze..Diamond, settle helper | evidence: main.cpp:1154-1234; .ksr_vault/lessons/PILLAR_29,_30 | status: BUILT-UNPROVEN (never observed on silicon hub; shop UI future, main.cpp:1131-1133)

### KSR-31 Sensory anchoring (N13)
level: L5 | does: `KobiiSoundPlaySafe` only, DRYA impact layers, palette lock, sound guard | evidence: CLAUDE.md:54; caddie/src/kobii/kobii_impact.cpp, kobii_sound.cpp | status: BUILT-UNPROVEN

### KSR-32 Build-time asset gates (N4/N8)
level: L5 | does: `brres_autopsy.py --check-dir` aborts build on bad BRRES | evidence: CLAUDE.md:46-49; tools/brres_autopsy.py | status: BUILT-UNPROVEN (script exists; wiring into make.py not verified by me)

### KSR-33 UI/UX consistency skills
level: L5 | does: wii-uiux skill, `uiux_wii_consistency/`, governance/WSR_FRAME_CODEX | evidence: .claude/skills/wii-uiux; governance/ | status: DOC-ONLY

### KSR-34 Riivolution distribution backend spec
level: L5 | does: spec for patch-based distribution | evidence: governance/SPEC_RIIVOLUTION_BACKEND.md; caddie/riivo/ (upstream) | status: DOC-ONLY

### KSR-35 UKDL hard rules with hardware confirmation
level: LG | does: HR-IOS-01, HR-IOS-02, KSR-WII-BOOT-001, HR-MMIO-01 with TRIGGER/ACCION/EXCEPCION(literal Owner phrase)/ORIGEN; KSR-WII-BOOT-001 marked CONFIRMED on real Wii | evidence: UKDL/HARD-RULES.md:1-120 | status: LIVE

### KSR-36 Silicon provenance gate (RULE-105)
level: LG | does: V-SILICON-PROVENANCE / REACHABLE / NANDWRITE fail-closed over PAL.txt and main.cpp | evidence: tools/pack/silicon_safety_check.py:1-28 | status: LIVE

### KSR-37 N-Laws N1-N22 + Forensic Reflex Arc
level: LG | does: 22 codified laws, 11 reflex triggers firing paired actions | evidence: CLAUDE.md:41-81; governance/N_LAWS_REFERENCE.md | status: LIVE (partially mechanised by genomic_lint; rest is behavioural)

### KSR-38 Owner STOP + backlog register with autonomy/gate fields
level: LG | does: items carry `gate` (ENGINEERING/ARCHAEOLOGY/VALIDATION/INFRA), `autonomy` (L1-AUTO/L2-BLOCKED/OWNER), `blocked_by`, acceptance | evidence: .ksr_vault/frontier/KSR_BACKLOG.json:17-60,495-723 | status: LIVE

### KSR-39 ADR log + public retractions
level: LG | does: ADR-001..010, in-file CORRECTION blocks, gap-registry amendments, KSR-B-023 mislabel row | evidence: .ksr_vault/decisions/; kobii_net.cpp:26-29; KSR_GAP_REGISTRY.md:12-45 | status: LIVE

### KSR-40 Handoffs / RESUMPTION / lessons vault
level: LG | does: 24 handoffs, 88 lessons, RESUMPTION_FILE per pane, CURRENT_STATE | evidence: .ksr_vault/handoffs, .ksr_vault/lessons, RESUMPTION_FILE.md:1-30 | status: LIVE (but CURRENT_STATE.md frozen 2026-04-15)

### KSR-41 Evidence-graded frontier (hypothesis table)
level: LG | does: FIRST_PIXEL_FRONTIER (25 hypotheses, UNMEASURED/WEAK/LIVE grades), EXPERIMENT_LEDGER, SCARCE_EVIDENCE_REGISTER, claim-separation lint | evidence: .ksr_vault/frontier/*; tools/governance/experiment_claim_separation.py, frontier_table_sync.py; KSR-B-010..014 | status: LIVE

## 4. GAPS FROM ITS OWN RECORD
Format: [level] what the record says (location) -> "Interpretation:" capability that would have prevented/shortened it. Items marked (OBS) are my own source observation, not in KSR's record.

G01 [L4] No reachable host can compile the module: "NO_DEVKITPRO on BOTH GEX44 and the VPS ... 16 of 27 rows blocked on a toolchain, not on knowledge" (KSR_BACKLOG.json KSR-B-031, line ~311). Interpretation: a reproducible build container/CI runner (infra/runpod/Dockerfile.ksr exists but nothing cites it as proven).
G02 [L4] No CI and no test dir at repo root (ARCHITECTURE.md:26-28); only whitespace pre-commit (caddie/.pre-commit-config.yaml:1-7); only CI workflow is an upstream docs-site deploy (website.yml). Interpretation: per-commit build + gate run (genomic_lint, size_gate, silicon_safety_check, pal_symbol_gate) as a hook/CI, which already exist as scripts but are caller-dependent.
G03 [L4] Automated playtesting dead end: "RED-NOT-VIABLE ... KobiiOnCalculate never ticks in a full GREEN pipeline - literal count 0" (ADR-002:7-21). AT_CANARY only reaches init in OnConfigure (run_at_canary_ci.py:12-17). Interpretation: a Dolphin input/savestate path that passes Health & Safety (DTM movie / savestate) was never built, so every behavioural claim past boot needs the Owner's hands.
G04 [L4] Test harness fidelity: "KobiiMiiRendererIsReady() returns false under any dev-capture flag ... No headless build has ever been able to render a KobiiMii" (RESUMPTION_FILE.md:56-63, REACH-5). Interpretation: a test-mode must not change the unit under test; a parity check between dev flags and prod paths.
G05 [L4/L2] Stale artifact on the execution target: staged disc dated 2026-09-03 while rebuilds continued; "Six weeks of rebuilds were invisible" (verify_delivery_identity.py:9-19). Interpretation: artifact-identity check inside the launcher/inject step, not a separate manual script (KSR-26 is BUILT-UNPROVEN).
G06 [L4] No release/rollback: `pipelines/release`, `pipelines/rollback`, `pipelines/validation` empty (listing); repo root holds ~7 loose `.wbfs` (4G.wbfs, KobiiSports_FLLE_*.wbfs, v15_canonical, KSR_P2FIX2_*, one `.VOID_DO_NOT_BOOT.txt`). Interpretation: a build manifest (hash -> commit -> flags -> verdict) and a "last known GREEN disc" pointer.
G07 [L4] Unversioned operational assets: /home/kobii/bin "~100 files with .bak, .new ... v2..v15" (KSR-B-034); skill only under ~/.claude (KSR-B-070); census script unversioned (KSR-B-071); `tools/caddie` is a nested git repo/gitlink (CL-05: "a gitlink with no checked-out directory always reports D tools/caddie"). Interpretation: infra-as-code with a drift check (RULE-091/101 exist; not covering bin/).
G08 [L3] Dispatcher dead while reporting healthy: "kobiiclaw.service INACTIVE; dispatcher reports RUNNING with no job since 2026-07-25; last real job 2026-04-22" (KSR-B-030). Interpretation: end-to-end synthetic job heartbeat (stub-smoke) on a schedule; resolved 2026-09-23 but monitoring still manual.
G09 [L3] Executor liveness lies: "capabilities.json said claude_cli usable: true" while codex out of quota and credential expired (KEOS_CLOSED_LOOP_BUG_LEDGER CL-02); wave identity read from printed output (CL-01); return path violated RULE-090 (CL-03). Interpretation: capability manifests need probed liveness, not declarations.
G10 [L3] Resource hygiene: GEX44 "138 run directories at 880 MB each ... 1.8T at 86 percent"; ksr_prune.sh "nothing schedules it" (KSR-B-032); billing counter 0.0 vs 71 days uptime (KSR-B-033); host RAM 1121 MB vs 2048 MB needed (KSR-B-060). Interpretation: scheduled retention + preflight resource check + cost telemetry.
G11 [L3] Mission supervision: srclink "epoch-2 worker became unreachable seconds after start"; p2w25 "worker idle for a day", worktree under %TEMP% "which the OS may reap" (BACKLOG_OWNER_STOP_20261001.md:13-14; KSR-B-068); 13 orphan ACTIVE goals, STATE.json missing (KSR-B-072). Interpretation: supervisor heartbeat + durable worktree location + goal-state reaper.
G12 [L3] False kill-switch: scaffold-auditor wrote BLOCKED_DELIVERY.md after 17 COMPILE-gate failures "that path is absent in the worktree, so the gate was blind, not the code broken" (KSR-B-067). Interpretation: gates must report INCONCLUSIVE when their subject is absent (same lesson as verify_delivery_identity's 3 verdicts).
G13 [L3] Observation perturbs the subject: FZDIAG OSReport breadcrumbs "had accidentally masked" the boot-burst hang (HARD-RULES.md:66-70); flag toggle changed -324 instructions (RULE-106). Interpretation: instrumentation-independence gate (size_gate.py partly; its own header says it does NOT cover layout shift).
G14 [L3/L1] Documented capability not executable / stale: CURRENT_STATE.md frozen 2026-04-15 ("VPS headless Dolphin BROKEN 2026-04-11"); vps_deploy/PIPELINE_STATE.md frozen 2026-03-21 "INITIAL SETUP"; ARCHITECTURE.md all "Open" sections; ai-pipeline/orchestrator.py "For now, just report" (orchestrator.py:24-27). Interpretation: status field per documented capability + executable doc-check.
G15 [L2] Evidence not durable: "7 evidence documents are MISSING_PRIMARY and 4 more came home renamed ... W16 never copied" (KSR-B-020/021); gate exists but MANUAL (KSR-B-022). Interpretation: repatriation as a harness step + scheduled gate.
G16 [L2] Fragile host services: KEOS gateway "Linger=no ... pm2 save and pm2 startup were deliberately NOT run" (KSR-B-042); SQLite 3.45.1 WAL-reset debt, journal_mode=DELETE (KSR-B-043). Interpretation: restart-survival test for every service on the box.
G17 [L2] (OBS) Player save integrity: save has magic+version but no checksum; write is NANDOpen -> NANDSeek(0) -> NANDWrite in place with no temp/rename or backup copy (main.cpp:1555-1564); load treats any failed validation as "memset to zero" (main.cpp:1498-1500), i.e. a torn write silently becomes a fresh profile with 0 coins. KSR's PILLAR_33/36 cover completeness and schema evolution, not corruption. Interpretation: CRC + two-slot write + load-time quarantine; KSR already wrote a CRC32 for KLOG (kobii_klog.cpp:327-331) that save does not use.
G18 [L2/LG] Provenance error shipped a dangerous call: "v102's NAND logger called IOS_Ioctl=0x8003bbc0 CREATEFILE on /dev/fs - an ADR-004 silicon-RED address mislabeled real-hw from GEX44/Dolphin runs" (HARD-RULES.md:25-27); first physical boot DSI at IOS_Open+0x54 (ADR-004:1-45); IOS_* "VERIFIED" names were actually EXI debugger routines, corrected 2026-09-28 (kobii_net.cpp:26-29). Interpretation: emulator-only evidence must never carry a hardware tag; RULE-105 gate was "slated to ship" and built only after the incident (silicon_safety_check.py:5-8).
G19 [L1] Product not reachable on silicon: "the KSR hub does not open" (KSR_GAP_REGISTRY.md:40-45, KSR-BUG-02); KSR-B-006 "unblocking event" priority 0 NOT_STARTED; 222 systems audited, 192 gaps (KSR_GAP_REGISTRY.md:47). Interpretation: a one-button end-to-end silicon smoke recipe with a bilateral evidence channel (HR-MMIO-01 item 5-6 already demands one for probes).
G20 [L1/L4] Regression found only by Owner on hardware: Wii Remote disconnect at wrist-strap screen = regression inside `7b1f402..f96801b` (KSR-BUG-14, KSR_GAP_REGISTRY.md:40-45); RZTP01 black-after-H&S diagnosed by "external analysis" (HARD-RULES.md:66-67). Interpretation: bisection harness over built discs plus a known-GREEN baseline corpus (RULE-106 is the manual protocol).
G21 [L3] First-pixel archaeology: "waves W5-W17 were all ARCHAEOLOGY on the Set-B first-pixel question, and that question is not on the mission's critical path" (KSR_BACKLOG.json header line 7). Interpretation: critical-path ranking before spending scarce slots (RULE-111 later added a ledger, not a prioritiser).
G22 [L3/L1] Slot economy: srclink Phase 5 "no confirmed GEX44 job type boots an arbitrary .wbfs; slot balance 0" (KSR-B-066); local Dolphin forbidden by Owner. Interpretation: a boot-any-WBFS job type, which is exactly what AT_CANARY half-has.
G23 [LG] Closure/halt cost: all 4 missions halted 2026-10-01; remaining work = 13 backlog rows all `autonomy: OWNER`, ~560 CRLF-only modified rows in wt_keosdtk_home, EOL rows in p2w25 (BACKLOG_OWNER_STOP.md:34-41). Interpretation: line-ending normalisation (.gitattributes) and a mission-exit clean-tree gate; resume needs a human by design.
G24 [L5] (OBS) No localization, onboarding, accessibility or marketing surface of its own: HUD strings hard-coded English (main.cpp:6090); the only web surface in CI is upstream Kamek docs (website.yml). Playable-state directive and Supremacy Gates are the nearest L5 standards (.ksr_vault/gates/*).

## 5. COUNTS AND WEAKEST AREAS

Counts (41 entries in section 3):
| level | LIVE | BUILT-UNPROVEN | DOC-ONLY | total |
|---|---|---|---|---|
| L1 WORKS | 4 | 1 | 0 | 5 |
| L2 SURVIVES FAILURE | 7 | 0 | 0 | 7 |
| L3 OPERABLE | 5 | 2 | 1 | 8 |
| L4 EVOLVABLE | 5 | 3 | 1 | 9 |
| L5 PRODUCT | 0 | 3 | 2 | 5 |
| LG GOVERNED | 7 | 0 | 0 | 7 |
| total | 28 | 9 | 4 | 41 |

Caveat on L2 "7 LIVE": these are mechanisms that exist and run; G17 shows the user-save leg has no corruption defence, and G15/G16 show the infra leg is half-manual. L2 is strong on *build/deploy integrity* and weak on *player-data integrity*.

Interpretation - 5 weakest areas (ranked):
1. L4 product-level CI / automated playtest: no CI (G02), headless playthrough RED-NOT-VIABLE (G03), test mode alters unit under test (G04); 66 tests cover tooling, near-zero cover the C++ module.
2. L1/L5 "a player can reach and enjoy it": hub unreachable on silicon, 192/222 systems not IMPLEMENTED, economy/ranked/sensory all BUILT-UNPROVEN, no localization/onboarding/a11y (G19, G24). L5 has zero LIVE entries.
3. L4 release and artifact lifecycle: empty release/rollback dirs, loose WBFS pile, stale-disc incident, unversioned scripts/skills (G05-G07).
4. L3 operability of the infra substrate: dispatcher INACTIVE-but-RUNNING, executor manifest lies, retention/billing/RAM unmanaged, supervisors lose workers, gates blind on absent subject (G08-G12).
5. L2 player-save integrity and L2 evidence durability: no CRC/atomic write/backup on kobii.dat (G17), evidence repatriation manual (G15).
Governance (LG) is the strongest and most over-built relative to the other levels: 111 rules, 10 ADRs, 88 lessons against 0 CI runs of the product; the record repeatedly shows rules being written AFTER an incident (G18, RULE-105) rather than a gate existing beforehand.

Method note: ~38 file reads; no builds, Dolphin, ssh or GEX44 access; KobiiCraft repos not touched; ignored dirs excluded. Unverified wiring is called out per entry (e.g. KSR-32). Not read: main.cpp beyond cited ranges, ADR-005..009 bodies, wiki/ and knowledge/ trees, .planning/ workstream STATE files.
