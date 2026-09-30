# Cognitive Resource OS — RESUMPTION

Read this and continue with zero prior context. Update after every sealed unit.

## 1. Identity
Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`.
Plan of record: `vault/plans/cognitive-resource-os-2026-09-27.md` (Owner APPROVED 2026-09-27, incl. consent
to relocate `~/.claude/rules` content in P3 ONLY after an ablation shows non-inferior quality, one reversible
commit per move). Thesis: the gap is orphans + overlaps, not missing concepts — CONNECT/MERGE/EXTEND, 0 mega-systems.
Another writer is LIVE in this tree (touches gsd_mission.py, knowledge_acquisition). Commit by explicit pathspec only.

## 1a. GEX44 hand-back (2026-09-28)
- The GEX44 clone is `/home/kobii/missions/cognitive-resource-os` (Linux; the laptop reaches it as `ssh gex44`), with branch `mission/cognitive-resource-os` at `cd4e436`.
- This run worked in the worktree `.claude/worktrees/cro-gex44` on branch `mission/cognitive-resource-os-gex44`, branched from `cd4e436`. Every commit of phases 1-5 is on that branch. Nothing was pushed and nothing was merged.
- Hand-back, run by the Owner on GEX44 from the clone where `mission/cognitive-resource-os` is checked out: `git -C /home/kobii/missions/cognitive-resource-os merge --ff-only mission/cognitive-resource-os-gex44`. It is a fast-forward because `cd4e436` is an ancestor (this phase's EVIDENCE section 4 records the check). Or, from the laptop: `git fetch gex44:/home/kobii/missions/cognitive-resource-os mission/cognitive-resource-os-gex44`, then `git log --oneline cd4e436..FETCH_HEAD`.
- GEX44 host facts this run relied on: claude 2.1.283, no `~/.claude/rules`, no pytest, subscription auth only. `.planning/workstreams/cognitive-resource-os/phases/01-gate-verdict-on-the-big-host/EVIDENCE.md` section 0, `.planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/EVIDENCE.md` section 0a, `.planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/EVIDENCE.md` section 0. GEX44.

## 2. Sealed
- `9fa1017` tools/tis_observed.py — real usage from transcripts (dedupe by message.id+requestId; synthetic excluded;
  subagents attributed; MEASURED / MEASURED_ZERO / UNMEASURED). Baseline: 97 sessions (laptop), median startup context
  168,631 tok (laptop), 13,858 calls (laptop), startup prefix ≈ 50% (laptop) of all context (call-weighted ESTIMATE).
- `48bbbb7` /cost-autopsy → `tis_report.py --observed`; project key = non-alnum→'-'; empty dir = UNMEASURED exit 2.
- `383cb37` pricing: anthropic_2026-09.json (read live 2026-09-27); 2026-05 file priced opus-4-7 at Opus 4 rate (3x);
  tools/pricing_source.py resolves newest dated file for tis_report / budget_monitor / verify_full_install.
- `ca69a04` budget_monitor runway from OBSERVED sdk-cli spend (entrypoint split); estimate kept as source=estimate.
- `10299f8` (this commit) tis_observed: first_call_cache_read + startup_shared_share_median; UKDL
  `vault/knowledge_base/ukdl-cognitive-resource-os.md` (1 HR, 3 PR, 4 T).
MEASURED 2026-09-27 (7d, laptop): programmatic $90.06 (laptop) / 272 calls (laptop) / 62 sessions (laptop); 79.9% (laptop) = 1h cache writes; median 1 call
per session; first-call shared prefix 1.9% sdk-cli (laptop), 16.4% cli (laptop). Hypothesis (unmeasured): tool list varies with MCP. Tested once on GEX44: UNJUDGED (section 2d).
Coherence anchor: `python tools/test_tis_observed.py` 25/25 (laptop), `test_pricing_source.py` 5/5,
`test_budget_monitor_observed.py` 7/7. test_tco V-BASELINE-INTACT INCONCLUSIVE (full pytest >180s, host ~630 MB (laptop) free). GEX44 (Phase 1): same three gates plus test_prefix_inventory 9/9; full pytest BLOCKED (section 2d).

- `5496a60` /knowledge repointed (TUA-X renamed TUAX_UGC_SYSTEM -> CW_UGC_SYSTEM); stale session_delta
  PLANNED removed from the liveness registry (scanner: REACHABLE via hooks/session_delta_stop.js).
- `0d712dc` model-routing.json -> opus-5-5 / sonnet-5 / haiku-4-5; savings per component (cache reads 1x
  Opus->Sonnet); absent schema declared ABSENT; opus-4-7 fallbacks moved in 3 tools.
- `6aa3bb6` modules/token-optimizer/prefix_inventory.py: unconditional prefix ~102k tok (laptop) est. (rules 56.8k (laptop),
  CLAUDE.md 21.4k (laptop), agents 11.0k, skills 7.9k, MEMORY 4.0k); harness/tools/MCP/plugins declared NOT counted.
- P3 protocol predeclared: vault/plans/cognitive-resource-os-P3-ablation-protocol.md (pre-flight P0 = run an
  arm without rules and without touching global config/credentials; unresolved -> STOP, do not improvise).
- A peer session moved every rule's incident evidence to knowledge_vault/rules-evidence/ (rules ~267->216 KB (laptop)).
  Three+ transcript parsers now agree on dedupe (peer 8c39c27); consolidating them to one owner is open debt.

## 2a. Who owns what NOW (peer panes are executing parts of this plan — do not duplicate)
- Ralph H1 progress / no-progress halt / renewal-without-progress: CLOSED by peer `676370b` (measured: 18
  renewed missions made 0 commits (laptop)). Vestigial `last_progress_at` field remains. Ralph = peer-owned; leave it.
- gsd-x mission closure / evidence classes / gating facts (P2 territory): peer-owned, active (bc73a94, cf34451,
  302f58a, 99e96e1). Offer tis_observed/prefix_inventory as inputs; do not wire closure.py.
- Transcript parsers: token_ground_truth + token_corpus_audit aligned to tis_observed dedupe by peer `8c39c27`;
  tco_compact_gate reads transcripts itself (another peer). Consolidation to ONE owner = open, needs agreement.
- Rules evidence relocation (knowledge_vault/rules-evidence/): done by a peer 2026-09-28.
- THIS pane owns: observed usage + pricing + budget runway + prefix inventory + routing table + P3 protocol.

## 2b. Owner decisions pending
- hooks/kobiiclaw-autoresearch.js (Stop, registered at dispatcher:174) has been INERT since TUA-X renamed
  TUAX_UGC_SYSTEM -> CW_UGC_SYSTEM: its fallback path is dead, so every turn skips silently. Fixing the path
  REVIVES a per-turn `knowledge_engine.py inject <cwd>` that writes AKOS_KNOWLEDGE_BRIEF.md into every open
  repo (incl. trees other panes commit in) with a 5 s budget. Revive, retire, or move to SessionStart? Not
  changed. /knowledge (manual) was repointed; `domains` verified, `query` run, inject/brief not executed here.
- 01-02 Task 1 (package-legitimacy checkpoint: pytest 9.1.1 / pluggy 1.6.0 / iniconfig 2.3.0 into a job-scratch venv) needs the Owner's answer -- approved or rejected. `.planning/workstreams/cognitive-resource-os/phases/01-gate-verdict-on-the-big-host/EVIDENCE.md` section 2. GEX44.

**ANSWERED by the Owner 2026-09-28 (evening, laptop pane), superseding both items above:**
- kobiiclaw-autoresearch.js: RETIRE (remove from the dispatcher; manual /knowledge stays).
- 01-02 Task 1 pytest/pluggy/iniconfig into a job-scratch venv on GEX44: APPROVED.
- P3 ablation on the laptop: run NOW on subscription quota (Owner accepted the weekly-quota cost at ~50% used).
- GEX44 phases 2-5 merged into feature/knowledge-acquisition (this merge commit).
- GEX44 mission `m-3fa466eb6cc8` halted `no_progress` at 17:17Z, but its worker had committed phases 2-5 in the
  worktree `.claude/worktrees/cro-gex44`; the progress detector watched the mission cwd, not the worktree the
  worker ran in (ledger: `rehydration_mismatch` session cwd != mission cwd). The halt was right for the wrong
  reason (the run was really blocked on the Owner gate above). Ralph is peer-owned: reported, not fixed here.

## 2c. Sealed on GEX44 (branch mission/cognitive-resource-os-gex44)
- Phase 1: gate evidence (`55c6212` pre-checks + one gate, `a155e0d` remaining gates + verdict) and the BLOCKED suite record (`eab20dc` package-legitimacy checkpoint answered rejected). GEX44.
- Phase 2: evidence (`03fffab` tracer, `1766507` by_entrypoint.py reproducer, `cb6fc62` laptop comparison + verdict); `by_entrypoint.py` (the reproducer, under `.planning`, not `tools/`); its five review fixes (`ad22dcd` `add48ee` `71beaf0` `35479c8` `350fb84`) -- after them the selftest reads 11/11 (GEX44).
- Phase 3: the three evidence commits `6d2c6e1` `c632771` `d08644d`. GEX44.
- Phase 4: the tracer (`e3d9e1e`), the pre-registration commit (`740b41b`) and the runs (`f32ea4b`), plus the review `8c13d18` and disposition `cd93c98` commits. GEX44.
- Full list: `git log --oneline cd4e436..mission/cognitive-resource-os-gex44`. Phase 5's own seal commits sit on top of these.

## 2d. Verdicts of the GEX44 run (phases 1-4)
Each verdict is read from its phase EVIDENCE; figures are GEX44's, not the laptop's, unless a line says laptop.
- Phase 1 (CRO-01) -- BLOCKED: gates_verdict PASS (25/25, 5/5, 7/7, 9/9), suite_verdict BLOCKED (pytest absent; 01-02's install checkpoint answered rejected, no Owner reachable mid-run). `.planning/workstreams/cognitive-resource-os/phases/01-gate-verdict-on-the-big-host/EVIDENCE.md` sections 1-4. verification: gaps_found. GEX44. The laptop's V-BASELINE-INTACT stays INCONCLUSIVE (laptop). Commits `55c6212` `a155e0d` `eab20dc`.
- Phase 2 (CRO-02) -- MEASURED: per-entrypoint first-call shared share sdk-cli 30.0% (3 sessions) and cli 46.6% (13 sessions); sdk-cli trailing-7d $0.53, of which 98.6% was 1h cache writes; reconcile MATCH, no tool defect. `.planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/EVIDENCE.md` sections 1-5. verification: passed. GEX44. Differs from the laptop's 1.9% sdk-cli / 16.4% cli (laptop); the instrument cannot attribute the cause. Commits `03fffab` `1766507` `cb6fc62`.
- Phase 3 (CRO-03) -- PASS via claudeMdExcludes: the arm-B mechanism `--settings {"claudeMdExcludes":[...]}` naming
  the three R1 rule files (instrument-before-claim.md, destructive-state-authorization.md,
  real-context-reachability.md), zero model calls, version scope claude 2.1.283 (Linux build). Host applicability:
  GEX44 has no ~/.claude/rules, so the ablation runs on whichever host carries R1 (the laptop).
  `.planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/EVIDENCE.md` sections 3-4.
  verification: passed. GEX44. Commits `c632771` `d08644d`.
- Phase 4 (CRO-04) -- UNJUDGED (similar-reuse-variance-not-observed), rule_fired R8: four valid haiku runs on subscription quota; run-2 reuse 99.97% (default MCP) and 99.96% (MCP stripped); Arm A's MCP surface was identical across its two runs (vA NO); n=2 per arm. `.planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/EVIDENCE.md` sections 1-4. verification: passed. GEX44. Per the 04-REVIEW disposition, CR-01 had no effect on the recorded run, and the runner may not be reused before the fix. Commits `e3d9e1e` `740b41b` `f32ea4b`.

## 2e. Open follow-ups from the GEX44 run
- Instrument gaps (`.planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/EVIDENCE.md` section 4): no tool emits the per-entrypoint 7-day USD or the 1h-write share (`by_entrypoint.py` composes them); no tool attributes an entrypoint to a MEASURED_ZERO session; the laptop's L1 scope and L2 pricing file are not recorded in `10299f8`. GEX44.
- Corpus side effect (`.planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/EVIDENCE.md` section 4 `corpus_side_effect`): exclude project keys `-tmp-claude-1000-cro-p04-ab-armA` and `-tmp-claude-1000-cro-p04-ab-armB` from future GEX44 baselines.
- 04-REVIEW: CR-01, WR-01 and WR-02 are open and must be fixed under a new runner sha before any reuse of ab_runner.py. Open finding: CR-01 (`env_check()` truthy bypass). GEX44.
- `.planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/EVIDENCE.md`: the laptop's claude version is unrecorded, equivalence of the Windows build is assumed, and runtime confirmation of claudeMdExcludes was none by design (zero model calls). GEX44.

## 2f. P3 ablation DONE (laptop, 2026-09-29) -- supersedes section 4 items 1-2
- 32/32 runs valid first attempt (claude 2.1.284, opus-5-5). Positive control held: arm B first-call context
  29.0-29.5k lower in all 16 pairs. Both arms pass 8/8 tasks in 2/2 replicates -> decision row 1:
  R1 is a relocation candidate. CEILING caveat: no task came near failing in either arm, so the set has
  no measured power for small losses; B-prime (on-demand R1) not run. Arm B total context -20.7 %,
  wall time unchanged. `.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/REPORT.md`, commit `bec5fa0`.
- CRO-01 re-run on GEX44 PASS (section 5 of phase 01 EVIDENCE, commit 7a7b786).
- Next: Owner go per move; one R1 file per commit to on-demand loading, re-run its domain tasks, ideally
  after adding judgement tasks that have no pre-existing test.
- Judgement set DONE 2026-09-29 (ADDENDUM-J, REPORT.md section J): 6 hidden-grader tasks, 24/24 valid,
  both arms pass every check in 2/2 -> all three R1 files stay relocation candidates. Owner declined a
  neutral-repo replicate. Relocation is GLOBAL (~/.claude/rules): move one file per reversible step to
  on-demand (B-prime), then re-run `p3_runner.py run-j` for that file's tasks. Awaiting Owner go.
- MOVE 1 DONE 2026-09-29 (efdb5e0, Owner: "que sea una skill dentro de claude power pack"):
  instrument-before-claim is now PP skill `skills/instrument-before-claim/` + live copy; rules/ keeps a
  592 B pointer; backup ~/.claude/backups/rules-20260929-134341. B-prime 4/4 pass, first-call −11k,
  skill auto-activation 0/4 (REPORT.md "Move 1"). Revert = copy the backup over the pointer.
- MOVE 2 DONE 2026-09-29: real-context-reachability -> PP skill (same shape; backup
  ~/.claude/backups/rules-20260929-135725). B-prime 4/4 pass, first-call ~147.6k (−18k vs pre-move),
  auto-activation 0/4.
- MOVE 3 DONE 2026-09-29 (7f98579): destructive-state-authorization -> PP skill + deny-once card hook
  `hooks/destructive_doctrine_card.js` (PreToolUse-Bash-chain, both dispatchers; kill switch
  CLAUDE_DESTRUCTIVE_CARD=off; ledger ~/.claude/state/destructive-card/ledger.jsonl). E2E exposed and
  fixed a dispatcher deny-dominance defect (rtk-rewrite's allow overwrote gate denies). B-prime 4/4,
  first-call ~138.5k (≈−27k total), card fired live once and recovered. P3 relocation COMPLETE.
- MOVES 4-6 DONE 2026-09-30 (Owner go at 75 % weekly quota, pane bb280e67), OUTSIDE the ablation:
  guard-event-reachability `90c9e82`, monetary-quantity-integrity `46f5f99`, presence-is-not-residency
  `36091e1`. Same shape (byte-identical body, live==canonical, pointer, backups
  ~/.claude/backups/rules-20260930-0950xx). prefix_inventory: rules 91.9 KB / ~24.2k tok (was ~130 KB);
  net ≈ −10k tok per call. NO ablation and NO B-prime for these three -- quality without them in context
  is UNVERIFIED; revert = copy each backup over its pointer.
- MOVES 7-9 DONE 2026-09-30, same terms (no ablation): evaluation-corpus-governance `569bde0`,
  develop-here-prove-there `11df818`, recurring-work-cardinality `323b35a`; backups rules-20260930-0956xx.
  prefix_inventory: rules 69.1 KB / ~18.2k tok; skill_listing +0.5k. Moves 4-9 together ≈ −15k tok/call.
  Next by size: concurrent-writers-shared-tree, technical-failure-to-product-state, scoped-side-effect-authority.

## 3. Active decisions
- Estimates and observations never mix; every figure names its source.
- Pricing: never hardcode a dated filename; never invent a price (read the live page).
- Phase 4 (Ralph holes in tools/gsd_mission.py) goes LAST in P1-P4: the live writer edits that file.
- $ figures in this file are API-rate equivalents of usage, not charges, on either host.
Owner clarified 2026-09-28: ONLY the paid experiment is off; free work continues. Model-calling runs
(A/B, ablation) wait for subscription quota.

## 4. Next three actions
1. CRO-01. The Owner reviews the pinned pytest 9.1.1 / pluggy 1.6.0 / iniconfig 2.3.0 install (job-scratch venv only; digests in 01-02-PLAN.md's context) and answers the 01-02 Task 1 checkpoint. Then `/gsd-execute-phase 1 --ws cognitive-resource-os` re-runs 01-02 on GEX44. No model calls. Cites `.planning/workstreams/cognitive-resource-os/phases/01-gate-verdict-on-the-big-host/EVIDENCE.md` section 4 `next:`.
2. P3 on the laptop. Record the laptop's `claude --version`. Unless it is 2.1.283, re-run the Phase 3 pre-flight procedure (03-01-PLAN.md, zero model calls) against the laptop's own binary. On PASS, and only with the Owner's go on subscription quota, run P1 A/A of `vault/plans/cognitive-resource-os-P3-ablation-protocol.md` with arm B launched through `--settings {"claudeMdExcludes":[...]}` naming the laptop's own paths of the three R1 files. Cites `.planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/EVIDENCE.md` section 4 (`version_scope`, `host_applicability`).
3. Prefix-miss follow-up. The laptop's low first-call shared share (1.9% sdk-cli, laptop) is not reproduced by identical back-to-back sessions on GEX44 (Phase 4, ~99.96% reuse). Take the zero-call step first: from the laptop's own sdk-cli transcripts, through tis_observed, measure the time between consecutive sessions against the cache TTL. Any new A/B reuses ab_runner.py only after the open 04-REVIEW findings are fixed under a new runner sha, and it counts only if the MCP surface changes between run 1 and run 2. Cites `.planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/EVIDENCE.md` section 4 `next:` and `.planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/EVIDENCE.md` section 3a.
Still open, not touched by this run: section 2a (parser consolidation) and section 2b (kobiiclaw-autoresearch.js decision).

## 4a. Previous next actions (laptop, 2026-09-27/28)
1. DEFERRED by Owner 2026-09-27 ("why spend? better wait for the limit to come back"): run it on subscription
   quota after the usage limit resets, never as paid spend. Then: diagnose the cross-session prefix miss — two
   back-to-back `claude -p` runs in one dir, identical prompt, then two with `--strict-mcp-config` + empty MCP
   config; compare first-call cache_read. Worker argv is in tools/gsd_mission.py (LIVE writer there).
   $ figures in this file are API-rate EQUIVALENTS of usage, not charges.
2. Parser consolidation: propose (not impose) tis_observed as the single transcript-usage owner to the panes
   holding tco_compact_gate / token_ground_truth; migrate only with their agreement, one caller per commit.
3. Owner decision on hooks/kobiiclaw-autoresearch.js (section 2b), then P3 runs once quota returns.
Status 2026-09-28: item 1 ran on GEX44 as Phase 4 (section 2d); items 2 and 3 stay open (sections 2a, 2b).

## 4a. GEX44 mission (armed 2026-09-28, Owner: "carry on with cognitive resource OS on GEX44")
- Mission `m-3fa466eb6cc8`, worker 1 bg `a293bedf`, `/gsd-autonomous`, workstream `cognitive-resource-os`,
  max 12 cycles / 12 h, permission auto. Supervised by the generic `agora-mission-sweep.timer` (all missions
  under /home/kobii). Clone `~/missions/cognitive-resource-os`, branch `mission/cognitive-resource-os`
  (base 784e446; roadmap cd4e436). Root flat roadmap untouched (`workstream create --no-migrate`).
- Roadmap phases: 1 gates + full pytest with dirty-set bracket · 2 GEX44 observed baseline · 3 P3 pre-flight P0
  (no model calls) · 4 prefix cache-miss A/B (4 runs, subscription quota only: host is claudeAiOauth `max`,
  no API key) · 5 seal RESUMPTION/UKDL in the clone. Ablation run and rule relocation are OUT of scope.
- Hand-back is by FETCH, not push (ovo-push-gate refused a remote push; not routed around):
  `git fetch ssh://gex44/home/kobii/missions/cognitive-resource-os mission/cognitive-resource-os`.
- Status: `ssh gex44` then, with CPP_CLAUDE_EXE=/home/kobii/.local/bin/claude in env,
  `python3 ~/.claude/skills/claude-power-pack/tools/gsd_mission.py status` (without it: "host session list unavailable").
- Set up on GEX44: repo-local git identity in the clone (host has none globally); trust entry added to
  ~/.claude.json (backup `~/.claude.json.bak-cro-20260928`).

## 5. Start instruction
On the laptop: fetch the GEX44 branch (section 1a), then read sections 2c-2e before action 1.
Run the coherence anchor. `git log --oneline -8` and confirm the three commits. Then action 1.
