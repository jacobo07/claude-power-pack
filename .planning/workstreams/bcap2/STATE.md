# STATE: bcap2

status: ARMING 2026-11-19 on GEX44 (Owner "continua esa mision de absorcion hasta terminarlo todo"; vehicle BCAP-2 GEX44)
current_phase: 5 (phases 1-4 PARTIALLY_PROVEN)
authority: 120M processed tokens + 3 x 40M top-ups (only with commits outside .planning/ since the last grant)
base: laptop feature/knowledge-acquisition committed HEAD at arm (the commit that adds this file)

## Phase log
(empty — the worker appends one section per phase: gate, measured numbers, spend, 5-line meta-analysis)

### Phase 1 CPP-DBG-001: PARTIALLY_PROVEN
gate: `python3 tools/test_bcap2_dbg.py` exit 0, 37 PASS / 0 FAIL (20 adversarial fixtures + real bug 96b6f09a red->green). Liveness offenders 56->56.
spend: ~3.4M processed tokens (`mission_spend session-tree`, transcript ea6857df, incl. context re-reads); ceiling 14M.
meta-analysis:
1. The backlog assumed a CRAIF causal engine; the code says diagnosis is not CRAIF's role. Scanning first avoided building on a false premise.
2. Built a record verifier (extend CRAIF), not an engine; honest cost: nothing yet emits records live (R2).
3. Upstream skill was never fetched (R1); do it read-only before closing.
4. Hook-blocked `git stash drop` taught: use a WIP commit, not stash, for baselines in this shared repo.
5. Next: Phase 2 TDD shares fix.* fields with this verifier; wire done_gate there (R4).

### Phase 2 CPP-TDD-001: PARTIALLY_PROVEN
gate: `BCAP2_TDD_PYTHON=<venv py> python3 tools/test_bcap2_tdd.py` exit 0, 65 PASS / 0 FAIL (14 backlog fixtures + variants, real test_gaps mutation poles, routing, real slice 96b6f09a, CLI). Phase 1 gate 37/0. Liveness offenders 56->56.
spend: ~2.4M processed tokens this session (`mission_spend session-tree`, def2ee92, main only); ceiling 12M.
meta-analysis:
1. P07's file-presence check was the whole premise gap; keeping it as HEURISTIC_ONLY beside an evidence classifier avoided replacing a live registry entry.
2. No new verdict enum: stage facts map to strength_ladder keys, and the honest ceiling is ADVERSARIALLY-VERIFIED because TDD evidence supplies no production facts.
3. The mutator was reused unchanged; running it for real needed pytest+pytest-cov, absent on GEX44, so the gate fails loudly without BCAP2_TDD_PYTHON instead of skipping.
4. Nothing emits records live (R1) and done_gate/intent-verify do not consume them (R2): the card is a pointer; same weakness as Phase 1.
5. Next: Phase 3 AGSK (no dependency). Owed read-only upstream fetches (DBG R1, TDD R3) batch into one network step.

### Phase 3 CPP-AGSK-001: PARTIALLY_PROVEN
gate: `python3 tools/test_bcap2_agsk.py` exit 0, 55 PASS / 0 FAIL (ledger integrity, floor_guard both poles, routing recall/precision, liveness). Phase 1 gate 37/0. Liveness offenders 56->56.
pilot: AGSK-C constraint non-weakening absorbed as `modules/sqi/floor_guard.py` (diff-scoped; MIT NOTICE, pin 8c99fa36), latent card under domain "constraints" (not always-on).
residuals: 34 upstream rows in DISPOSITIONS.md are basis=HYPOTHESIS (only the pilot is READ); 7 rows UNVERIFIED (AGSK-B/D/E/F gaps unmeasured); nothing emits floor_guard live from done_gate (same weakness as Phases 1-2); closing needs those scans.
meta-analysis:
1. Scanning first showed 26 skills not 25; honest basis column stops a hypothesis reading as an absorption claim.
2. One pilot slice done fully beats 26 shallow ones; EXTEND landed beside the sqi census, no new router.
3. Routing negatives (typo, root cause, failing) pinned so the new card does not steal diagnose/tdd.
4. Weakening fixtures trip the auto-mode classifier on Write: edit via small Edits only.
5. Next: Phase 4 Anime.js (no dependency); batch owed upstream fetches (DBG R1, TDD R3) into one read-only network step.

### Phase 3 scan notes (historical)
Upstream pinned 8c99fa36 (MIT); scan notes and next steps in vault/programs/bcap-2/agsk/REUSE_LEDGER.md. No implementation yet. Spend this session before the wall: ~179k resident context (second session of epoch 2).

> Coordinator note 2026-11-19T16:5xZ (laptop pane 2cf9ec6d, Owner-approved): epochs 3 and 4 hung ~2 h on a host
> permission prompt for `Write tools/test_bcap2_agsk.py` (auto-mode classifier reads the seeded test-weakening
> fixtures as test tampering). The coordinator placed the worker's exact attempted content (11,350 chars) at that path.
> Do NOT re-create it with Write; change it with small Edit calls. Keep seeded-weakening fixtures in this file only.

### Phase 4 Anime.js into PP Design: PARTIALLY_PROVEN
gate: `python3 tools/test_bcap2_animejs.py` exit 0, 35 PASS / 0 FAIL (corpus, resolver poles, 5 seeded-red parser mutants, ledger, routing, no-dependency). Also green: test_cdio 8/8, test_motion_grammar 46/46, Phases 1-3 gates. Liveness offenders 56->56.
upstream: juliangarnier/anime @ 01b81be1 v4.5.0 MIT (NOTICE in vault/programs/bcap-2/animejs/). 21 capability rows each with one disposition; 3 new registered patterns VP-AJS-001..003 + selection/lifecycle doctrine `visual-patterns/motion-library-selection.md`; frontend routing now wakes on motion prompts without naming a library.
residuals: no real-browser verification (reduced-motion exercised, timeline cancel, unmount cleanup, bundle size) -> LAPTOP/browser plane; 26 upstream examples not individually read; Animatable, motion-path UNVERIFIED; baseline-ratchet promotion not evaluated; evidence_level stays `research`.
meta-analysis:
1. Upstream src has zero reduced-motion handling: the floor must stay a CPP property, now written into doctrine.
2. Most of the surface (scroll, draw, text, layout) was already owned by visual-patterns: 4 ALREADY OWNED rows, 3 new patterns only.
3. Regression caught by running the neighbouring gate: a new CDIO-13 file broke the pinned 13-dataset count; doctrine moved to visual-patterns, no dataset added.
4. Routing was blind to "animate this hero"; fixed with narrow strong phrases, negatives checked.
5. Next: Phase 5 Synsation (same owners, reuse the VP corpus mechanics).

### Phase 5 Synsation UX: PARTIALLY_PROVEN
gate: `python3 tools/test_bcap2_synsation.py` exit 0, 35 PASS / 0 FAIL (poles, 8 seeded-red source mutants, ledger UX-01..20, corpus, design_route wiring). Also green: test_cdio 8/8, test_motion_grammar 46/46, animejs 35/0, agsk 55/0, dbg 37/0, design_route 46/0. Liveness offenders 56->56.
built: `modules/cdio/ux_contracts.py` (waiting_pattern, check_disabled_control, check_hit_targets; wired via `design_route.ux_findings`), patterns VP-SYN-001/002 (hypothesis).
decisions: new patterns set min moderate/medium because restrained dashboard must keep resolving to VP-018 only (pinned by test_motion_grammar); no CDIO-13 file.
residuals: videos not on GEX44 (INFERRED claims) and browser-real checks -> LAPTOP_STEPS.md; UX-14..18 UNVERIFIED/HEURISTIC only; no UKDL/HR promotion.
pre-existing failures NOT caused by this work (verified identical at 5f60f05a): `test_cdio_componentry` V-CMP-WIRING (suite pins EXPECTED_DATASETS = 12; live-mirror) ; `test_bcap2_tdd` V-TDD-MUT-REAL (system python lacks pytest/coverage; set BCAP2_TDD_PYTHON).
owed: Phase 1/2 upstream-fetch residuals; backlog Status lines for Phases 3/4 (deferred-backlog rows for 3/4 not yet updated).

### Phase 6 CDIO SaaS styles: SCAN ONLY (PARTIALLY_PROVEN, no new code)
Scan: vault/programs/bcap-2/saas-styles/REUSE_LEDGER.md. Style 1 open rules need real-browser measurement of third-party sites (laptop plane); style 2 blocked by 403 access; style 3 needs the Owner pick below.
OWNER DECISION NEEDED: style 3 "enterprise systematic": (a) new aesthetic family F11 (changes scorer KNOWN_FAMILIES + font sanction + f10 boundary test), or (b) a structural experience axis in the CDIO-09 style with no scorer change. Evidence (7-brand bench) favours (b): identity is structural, palette is near F1. My pick if forced: (b), reversible and internal. Not implemented.

### Phase 7 Brand Identity: PARTIALLY_PROVEN (BR-01..16 complete)
built (CCF owner extended, no new owner): modules/ccf/asset_validator.py, kit_readiness.py, PDF embeds the logo, unsafe concept ids rejected (BR-08 real path-traversal defect), release refuses missing/stale scan (BR-05 real defect), scanner signature recall (corpus 1.1).
gate: `python3 tools/test_bcap2_brand.py` exit 0, 71 PASS / 0 FAIL (BR-01..16, both poles; BR-11 determinism, BR-12 blob via CLI, BR-13 edit-after-generate, BR-14 licence poles, BR-15 partial provider failure, BR-16 frozen recall 8/8 + no false BLOCK + `--by llm` cannot override BLOCK). Also green: modules/ccf/test_ccf.py 16, test_asc_ccf. Liveness offenders 56->58->56 (asset_validator/kit_readiness declared LIBRARY in the registry, same multi-line-import precedent as the other ccf modules).
ledger: vault/programs/bcap-2/brand/REUSE_LEDGER.md (10 repos all HYPOTHESIS, none fetched; Marker-AI LICENSE_CONFLICT; LogoLoom unsafe behaviours pinned as negatives).
residuals: no real render/resvg, no mono-variant check, no font-file parse; scanner is first-pass only (3/5 clean descriptions WARN); BI-08..35 mostly not started; upstream unfetched.
meta-analysis: 1. Two real defects found by driving the CLI, not unit helpers (BR-05, BR-08). 2. Fixture words "ring"/"curve" trip scanner WARNs: fixtures avoid them. 3. Backlog files for Phases 3/4/6 have no Status line; deferred-backlog index rows now updated for 3, 4, 6, 7. 4. Next: Phase 8.
pre-existing failures unchanged: V-CMP-WIRING, V-TDD-MUT-REAL. Spend not re-measured this epoch (supervisor last: 26.2M of 120M).

### Phase 8 21 design resources: PARTIALLY_PROVEN (Workstream A slice only)
gate: `python3 tools/test_bcap2_d21.py` exit 0 (V-D21-01/02/03/04/05/06/07/09/10/24/25/31/36 + A06). Brand gate 71 PASS unchanged. Liveness offenders 56->56.
built: modules/cdicf/source_intake.py, vault/programs/bcap-2/design-resources/{SOURCES.json,REUSE_LEDGER.md}. Fail-closed rights gate; item-level evidence wins over source posture; denominator pinned in code.
residuals: no network (all 21 live_verified=false), capability denominators UNKNOWN, 23/36 scenarios undriven, Workstreams B-H not started.
decision: UNKNOWN-rights sources may admit an item that carries its own licence evidence (backlog: component-level licence is authoritative); REFERENCE_ONLY/RESTRICTED/UNKNOWN_ACCESS never admit code.
next: Phase 9 Ruflo (independent); one batched read-only upstream fetch step for owed Phase 1/2/7/8 residuals.

### Phase 9 Ruflo CPP-RUFLO-001: PARTIALLY_PROVEN
gate: `python3 tools/test_bcap2_ruflo.py` exit 0 (attack/benign poles for 27 cases + permissive-mutant drill + real manifest + ledger binding). Liveness: ruflo_gate declared LIBRARY, no new orphans.
built: modules/ruflo_gate/gate.py (controls for 8 GHSA, #3294, #4750, #3157, plugin/MCP default-deny, lifecycle scan, install envelope, version coherence); vault/programs/bcap-2/ruflo/{HOLDS.json (19: 17 corrected, 2 residual), REUSE_LEDGER.md, install_sandbox.py}.
install: inert pinned v3.78.0 in /home/kobii/ruflo-sandbox-bcap2/run (--ignore-scripts, scrubbed env, nothing started, smoke `ruflo v3.78.0`). Real finding: @claude-flow/browser postinstall does `npm install -g`.
decision: law 6 uncorrectable holds (no provenance attestation, unverified maintainer fix claim) => no activation/trust, inert study copy only. Reversible (rm -rf the sandbox).
residuals: see ledger (runtime advisory verification, dist identity, netns blocked on host, npm audit unrecorded). Laptop step logged.
next: Phase 10 closeout.

### Phase 10 Closeout: DONE (the gate and the report; items stay PARTIALLY_PROVEN)
`python3 vault/programs/bcap-2/done_gate.py` exit 0 (8 item gates, liveness, ledgers). HANDOFF: vault/programs/bcap-2/HANDOFF.md. No item is ACTIVATED. Next work = fetch pass, Phase 8 B-H, Phase 7 BI-08..35, laptop steps, Owner style-3 decision.

### Epoch 10 reachability pass (Phase 8)
Status-only GET of all 21 sources: 30 URLs, 27x HTTP 200, 3x 403 (designmd.ai, vibeprompts.dev, uiverse.io site; its github galaxy repo is 200). Evidence: vault/programs/bcap-2/design-resources/LIVE_CHECK.json. Reachability only: no content read, `live_verified` left false, rights and capability denominators unchanged. D21-08 vibeprompts stays UNKNOWN_ACCESS.
Still owed: per-repo licence + pinned-commit fetch (Phases 1, 2, 3, 7, 8), Phase 8 B-H, Phase 7 BI-08..35, Owner style-3 decision. Spend not re-measured this epoch.

### Epoch 10 repo-metadata pass (Phase 8)
GitHub REST metadata for the 9 listed repos: vault/programs/bcap-2/design-resources/REPO_META.json. 8 with an SPDX licence (MIT x6, Apache-2.0 x1 design.md, uiverse galaxy MIT but last push 2024-09); ckissi/kinetics (D21-15) has NO detected licence -> must not admit code (fail-closed rights gate stands). Detector field only, LICENSE text not read, no commit pinned, `live_verified` unchanged; SOURCES.json untouched. Next: read LICENSE text at a pinned SHA per repo, then flip live_verified with the gate.

### Epoch 10 licence-pin pass (Phase 8)
vault/programs/bcap-2/design-resources/LICENSE_PINS.json: HEAD sha + sha256 of raw LICENSE bytes for the 9 repos. 7 LICENSE files read and head matches the detector (MIT x6, Apache-2.0 design.md). Two gaps: ibelick/motion-primitives (D21-14) detector says MIT but no LICENSE file under the 4 names tried -> treat as UNVERIFIED, not admitted; ckissi/kinetics (D21-15) no licence at all -> stays refused. Head text only, not legal analysis. `live_verified` and SOURCES.json still unchanged (page-level content and capability denominators not read).

### Epoch 10 upstream-pin pass (Phase 7 brand + Phases 1/2 mattpocock)
vault/programs/bcap-2/brand/UPSTREAM_PINS.json: all 10 brand backlog pins resolve via the GitHub API; LICENSE bytes hashed at each pinned SHA. Confirms ledger claims: Marker-AI LICENSE file is Apache-2.0 while detector says NOASSERTION (LICENSE_CONFLICT stands, README MIT claim not re-read); Forge-Space/branding-mcp archived. NEW: op7418/logo-generator-skill has NO licence -> reference only, never adapt. mattpocock/skills (Phase 1 diagnosing-bugs, Phase 2 tdd) LICENSE MIT at default HEAD; the per-skill subpath was not located/read, so DBG R1 and TDD R3 stay open (pin + licence of the repo known, skill content unread). Ledger rows still read HYPOTHESIS: not edited (gates pin them); evidence level unchanged.

### Epoch 10 Phase 3 + mattpocock locate pass
vault/programs/bcap-2/agsk/UPSTREAM_PINS.json: addyosmani/agent-skills @ 8c99fa36 re-resolved, MIT LICENSE sha256 recorded (agrees with the ledger; Phase 3 had no residual here). mattpocock/skills subpaths located at tree abeeaf95: skills/engineering/diagnosing-bugs/SKILL.md and skills/engineering/tdd/SKILL.md (MIT repo). Content NOT yet read: DBG R1 / TDD R3 now reduce to "read those two files at a pinned SHA and disposition them", no longer "find them". HEAD was unpinned at fetch time; the commit SHA still has to be recorded when they are read.

### Epoch 10 mattpocock read
Both skills read at pin abeeaf95; dispositions in vault/programs/bcap-2/dbg/MATTPOCOCK_READ.md. DBG R1 and TDD R3 reading closed; candidate gaps listed there are NOT yet checked against fixtures or implemented (next: verify each against test_bcap2_dbg 20 fixtures / test_bcap2_tdd, add missing ones with both poles).

### Epoch 11 mattpocock gaps
DBG +2 codes (NO-SEAM-UNRECORDED, MUTATION-NOT-LANDED), TDD tautology detector; poles in both gates; details in vault/programs/bcap-2/dbg/MATTPOCOCK_READ.md. Horizontal-slicing deferred. Spend not re-measured. Remaining: Phase 8 B-H + live_verified, Phase 7 BI-08..35, Owner style-3 pick (I chose (b)), laptop steps.

### Epoch 12 Phase 8 pin wiring
SOURCES.json now carries `license_pin` (pinned sha, licence sha256, spdx) for the 9 GitHub-backed sources, copied from LICENSE_PINS.json; gate +5 checks (V-D21-05, both poles incl. seeded mutant): the rights gate admits exactly the 7 licensed repos, refuses motion-primitives (no LICENSE file) and kinetics (none). `live_verified` stays false everywhere (page content unread). Gate 33 checks, exit 0; done_gate consistent. Spend not re-measured. Remaining unchanged: Phase 8 B-H, Phase 7 BI-08..35, laptop steps.

### Epoch 13 Phase 8 Workstreams B/C slice
built: modules/cdicf/reference_intel.py (rank with licence filter + diversity guard + ABSTAIN, design-decision brief validator, OBSERVED/INFERRED/UNKNOWN tokens, project-contract-wins merge, motion NONE abstain). gate: `python3 tools/test_bcap2_d21_bc.py` exit 0 (D21-B05/B06, V-D21-12/13/18, both poles + drill). Not yet in done_gate. Liveness offenders 56->56. Phase 8 stays PARTIALLY_PROVEN: B01-B04/B07 corpus, C01-C05/C07/C08, D-H not started; V-D21-11 drift reconciliation undone.
decision: ranking floor 0.34 and weights 0.5/0.3/0.2 are provisional (unmeasured vs keyword baseline; Gate B baseline comparison still owed). Spend not re-measured.

### Epoch 13b V-D21-11 drift reconciled
modules/design-md/README.md licence line now records DRIFT (old "Proprietary" kept visible, upstream repo LICENSE Apache-2.0 at pinned db977b3c); npm package licence field still UNVERIFIED (not read). test_bcap2_d21 +4 checks. Remaining Phase 8: B corpus, C, D-H; Phase 7 BI-08..35.

### Epoch 13c D21-C07
reference_intel.fidelity_claims: a 1:1/pixel-perfect claim needs observed text/states/responsive/fonts/a11y evidence; absent = unobserved. +6 checks in test_bcap2_d21_bc. Done gate PASS.

### Epoch 14: BI-09 territories
modules/ccf/territories.py (pure check_territories: >=3 distinct mechanism+brand_fact, recolour/missing not counted, reasoned narrow-brief exception is its own verdict). 7 checks in test_bcap2_brand, LIBRARY-declared, in done_gate NEW_MODULES; not yet wired into `cli generate` (stays PARTIALLY_PROVEN). Remaining: BI-08, BI-10..14, Phase 8 B01-B04/B07 + C rest, D-H. Spend not re-measured.

### Epoch 14: BI-14 critique
modules/ccf/critique.py (pure): evidence needs an instrument else demoted to judgment; unassessed criteria never pass; approve() only by human among >=2 qualifying directions. 7 checks, LIBRARY, in NEW_MODULES; not wired into `cli select` (PARTIALLY_PROVEN). Remaining: BI-08, BI-10..13, Phase 8 B01-B04/B07 + C rest, D-H. Spend not re-measured.

### Epoch 14: BI-08 brand truth
modules/ccf/brand_truth.py (pure intake): observed needs source+retrieved_at else rejected; empty/unknown-field/bad-origin rejected; missing fields listed unknown; clearance always NOT_ASSESSED. 5 checks, LIBRARY, in NEW_MODULES; not fed by `cli init --brief` or CrawlOS yet (PARTIALLY_PROVEN). Remaining: BI-10..13, Phase 8 B01-B04/B07 + C rest, D-H. Spend not re-measured.

### Epoch 14: BI-12 Visual DNA
modules/ccf/visual_dna.py (pure): versioned 1.0 contract, validate() lists problems never repairs, tokens_for() derives colour tokens and refuses to fork a project-pinned token (SSOT wins). 7 checks, LIBRARY, in NEW_MODULES; not yet compiled into DESIGN.md by the CLI (PARTIALLY_PROVEN). Remaining: BI-10, BI-11, BI-13, Phase 8 B01-B04/B07 + C rest, D-H. Spend not re-measured.

### Epoch 14: BI-13 provider policy
modules/ccf/provider_policy.py (pure, no provider call): route() = vector unless deterministic_possible is False AND a need is stated (unmeasured flagged, never buys an image call); plan_call() needs distinct fallback, tool bound 4, refuses parallel_orchestration/agent_memories/unverified_claims imports; cost/token/latency fields start None not 0. 7 checks, LIBRARY, in NEW_MODULES; not consulted by generate yet (PARTIALLY_PROVEN). Note: SDD-OS hook reported NOT_READY (front-matter missing) for the binding plan file; that file is the Owner-approved plan, left unedited. Remaining: BI-10, BI-11, Phase 8 B01-B04/B07 + C rest, D-H. Spend not re-measured.

### Epoch 14: BI-11 identity set
modules/ccf/identity_set.py (pure): 2-4 axes, rationale, category-default challenge, WCAG contrast computed (>=4.5), typography observation; KEEP preserves logo/font/palette, REFRESH preserves logo/font. 7 checks, LIBRARY, in NEW_MODULES; not called by CLI (PARTIALLY_PROVEN). Remaining: BI-10 (needs pinned fetch), Phase 8 B01-B04/B07 + C rest, D-H. Spend not re-measured.

### Epoch 15: BI-10 technique taxonomy
Pinned fetch of Marker-AI d14340c3 references/techniques.md (read-only): the 12 technique names are verified. modules/ccf/techniques.py (pure, method only, own wording because the licence conflict stands): check_hypothesis needs a registered technique, a >=4-word brand observation and a recipe whose steps each name a geometric operation; self_rating echoed UNVERIFIED, measured_originality always None. 6 checks in test_bcap2_brand, LIBRARY, in NEW_MODULES; not consulted by `cli generate` (PARTIALLY_PROVEN). Done gate PASS. Remaining: Phase 8 B01-B04/B07 + C rest, D-H; BI-08..14 CLI wiring; BI-15..35. Spend not re-measured.
