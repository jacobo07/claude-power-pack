# RESUMPTION -- CP50 lease C2 (C2a arm-A executor, then C2b pilot on draw 1-5)

Identity. Recon C2 work tree C:\Users\User\Apps\recon_work\wt_cp50_c2 (branch cp50-c2, from keosdtk-home 3c86ae2).
PP repo C:\Users\User\.claude\skills\claude-power-pack (branch feature/knowledge-acquisition). Plan:
vault/plans/cp50-run-plan-2026-10-09.md C2 ("arm A on draw functions 1-5 in one cohort process; first measured cost per
function"). Authority: Owner "fund it" 2026-10-10.

State (2026-10-10 ~08:30):
- Goal cp50-c2 DECLARED: cap 4,000,000, root wt_cp50_c2 only, host DESKTOP-PMT5BS8, since 2026-10-10T08:15:28, used 0.
  Sizing: C2a ~2.4M ceiling (P3a 2.35M / P2a 2.40M class), C2b ~1.5M (P3b-2 1.49M class). wt_keosdtk_home stays
  bound to rf-p3b2, which is why C2 has its own tree.
- C2a: build_c2_dossier.py -> C2A-DOSSIER.md (99,322 chars, ~24.8k tokens, unknown=[]). Draw n=300 anchor 0f2ecb37
  MATCH; pilot = main:80426354, main:8044D4A8, main:804263A4, main:8044064C, main:8042A4D0. RF Phase 7 used 0 of 4.
  packets/C2a.md + route-C2a.json (target 1.6M | warn 1.7M | stop 1.75M, 9 worker calls; 12 calls was RECOMPILE
  need 1,793,022). Mission m-e6ea9c26d377 ARMED (PREPARED, no launch; the sweep launches it), max-cycles 2, max-hours 3,
  capsule-v2, envelope token_estimate 875k sonnet, ROUTE ADMISSIBLE need 1,467,018. It supersedes C1b
  m-4e2364edc538 (BLOCKED on its own commit; C1 work landed in recon 9929c29).
- Phase is read at SEND time (stage.py:1136 root_phase_cap), so C2a's local stage.build cannot spend a Phase 3 slot.
  Open point, not C2a's: stage.build cand_selection records "phase": CURRENT_PHASE (match_accel 4), metadata only.

PARKED 2026-10-10 (Owner "put the rest of the mission in the backlog"): C2a ran and ended PARTIAL (receipt PP
35165d69, ARM_A_DRILL 7/8, capsule id ignores targets_for, prepare not run, nothing sent). m-e6ea9c26d377 is under its
cost-breaker owner hold (processed 2,106,279 vs 875k estimate). Its code is STAGED, not committed, in wt_cp50_c2 (the
.ksr_vault snapshot gate refused). Copy in vault/backlog/2026-10-10_cp50-c2a-partial.patch. The remaining work is in
vault/backlog/2026-10-10_cp50-c2-remaining.md, which supersedes the actions below.

RE-ARMED 2026-10-10 (Owner "go ahead ... rearma la misión"): variance explained (C2a-receipt.md § Variance; 875k =
stop/2, the overrun = 2 commit retries + closing turn). Dead worker settled at measured 2,106,279: goal cp50-c2 used
2,106,279, open 0, remaining 1,893,721 (the "1.0M phantom" was real spend, not a phantom). C2a-fix mission
m-f5d386e909a5 PREPARED (supersedes m-e6ea9c26d377, HALTED), packet packets/C2a-fix.md, route-C2a-fix.json ADMISSIBLE
need 841,212 target 1.05M stop 1.2M. It makes no commit in wt_cp50_c2. C2b (~1.5M class) will NOT fit what is left
after C2a-fix: the Owner raises the cap with `goal-declare --owner` (TTY) sized from C2a-fix's measured spend.

Next 3 actions (historical):
1. When gen3/C2a-receipt.md lands: read it, meter the worker transcript (dedupe by message.id) against the 1.75M
   stop, re-run test_arm_a.py + test_bench.py from the coordinator with absolute paths (never Set-Location).
2. C2b (fresh pane or worker, goal cp50-c2): pre-checks (PINS, slot_ledger, GEX44 idle), set RF_CURRENT_PHASE = 7 in
   wt_cp50_c2 stage.py (commit), send the C2a job dir (job 1 of 4), wait, repatriate, `candidate.py judge`, then
   `arm_a.py records --first 1 --last 5`. Receipt = per-function cost table.
3. C3: CP50 cost = pilot per-function p50/p95 x 50 x arms + the GEX44 job budget; the Owner funds CP50 from that number.

Start: read this file, then C2a-receipt.md. Never Set-Location into a goal root.
