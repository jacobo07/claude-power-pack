# PP Deferred Backlog — activation criteria

> Items that could NOT honestly close in the 2026-06-08 session-close
> sprint, each with an explicit activation criterion so a future session
> picks them up without re-discovery. Source audit:
> `vault/audits/session_close_2026-06-08.md`.

---

## D1 — apex-completion-standard.md bidirectional drift (verify_spp: `mirror-parity` + `drift-report`)

**State:** global `~/.claude/knowledge_vault/core/apex-completion-standard.md`
(174 350 B, LF-SHA `e553bcc`) ≠ repo copy (158 278 B, LF-SHA `03d9775`).
Both STRICT-FAIL rows share this single root cause.

**Why deferred (not a mechanical loose→PP sync):** the divergence is
**bidirectional and cross-project**, so a blind copy in either direction
destroys content (HR-006: "sync direction propagates corruption
byte-perfectly"):
- **global-only (+195 substantive lines):** *other projects'* axes —
  KobiiCraft "NL→DNA Axis" (Sesión 15), KobiMapEngine Sesiones 16-20,
  "Database Migration Doctrine". The global vault is a **shared
  multi-project accumulator**.
- **repo-only (+178 substantive lines):** PP-only clauses — C20
  MCP-Resilience, C21 Slash-Recovery, PP Dataset Baseline (v15),
  Security-First (v16), and now C26/C27 (this session).

**Activation criterion:** Owner decides the canonical model. Two options:
1. **Union-merge** — append the PP-only axes into global AND the
   cross-project axes into repo until LF-SHAs match. Tedious, must
   de-dup, must preserve both projects' content.
2. **De-scope the file from mirror-parity** — if the apex doc is
   *intentionally* a shared cross-project accumulator that cannot be
   kept in byte-parity, remove it from `verify_global_mirrors.py`'s
   PAIRS list and track PP clauses in a PP-exclusive ledger instead.

Recommended: option 2 (the file's content proves it serves multiple
projects; byte-parity is the wrong invariant for it). ~30-45 min once
the model is chosen.

---

## D2 — hooks-registration 6/7 (verify_spp: `hooks-registration`)

**State:** `verify_hooks_registration.py` reports `HOOKS_REG_PROBE=6/7`.
Sub-check `idempotency-mod` fails: 6 hook markers are built on disk but
absent from `~/.claude/settings.json`:
`restart_resume`, `output_contract_stop`, `budget_monitor`, `jit_warm`,
`cascade_check_bash`, `secret_firewall_gate`.

**Why deferred:** writing `~/.claude/settings.json` is **Owner-side** —
the classifier hard-denies agent edits to it (HR-001,
`feedback_automode_denies_self_modification`). The PP-internal half
(hook scripts) is shipped; only the registration step remains.

**Activation criterion (Owner runs):**
```
python tools/verify_hooks_registration.py        # re-run WITHOUT --dry-run to commit
```
The probe already prints "Re-run without --dry-run to commit." Once the
Owner applies it (or runs the documented `settings_merger.py register-*`
commands), the marker set reaches 11/11 and the row passes.

---

## D3 — paths+secrets residual: doc-class (35) + secret-class (9) (verify_spp: `paths+secrets`)

**State after this session's CODE-class fix:**
- `path-leak (code)`: **0** ✅ (3 benchmark JSONs allowlisted —
  machine-generated host-pinned records).
- `path-leak (doc)`: 35 in 26 files — narrative/command/setup docs that
  reference `C:\Users\User\...` (e.g. `commands/*.md`, `docs/HOOKS_SETUP.md`,
  `vault/knowledge_base/ukdl-universal.md`, dataset + audit `.md`).
- `secret hits`: 9 in 3 files — canonical **fake** AWS doc example
  access-key IDs in `tools/secret_rotation_advisor.py`, VPS-IP narrative
  in `vault/audits/manual_tools_audit_*.md`, ssh-alias narrative in
  `vault/knowledge_base/pp_dataset/pp_dataset_01_identity.md`.

`normalize_paths.py` exits 1 while `--check` sees any unallowed doc OR
secret hit, so the row stays RED until both classes reach 0.

**Why deferred:** all 35+9 are non-leaks (narrative / canonical fixtures),
but clearing them correctly means **surgical per-file allowlist entries**
(26 doc + 3 secret), not a broad glob — the allowlist is intentionally
file-specific so it never masks a *future* real leak. Doing 29 reviewed
entries exceeds the 30-min defer threshold. NOTE: the secret-class
allowlist edit also trips the HR-SECRET PreToolUse firewall when the
comment names the example-key literal — author comments without the
literal token.

**Activation criterion:** add 29 surgical allowlist entries to
`tools/normalize_paths.py::ALLOWLIST` ({"doc-path"} for the 26 narrative
docs, {"secret"} for the 3 fixture/narrative files), each with a one-line
justification matching the existing host-pinned/fixture precedent. Then
`python tools/normalize_paths.py --check` exits 0. ~30-45 min.

---

# Added 2026-09-30 (session 5fb53f17) — Owner: "leave everything remaining in the backlog"

## D4 — PP Self-Eval: observe the first night (acceptance §4.4)

**State:** scheduled task `PP-SelfEval` installed (daily 03:30), code at `e079c57`, gate
`tools/test_pp_eval.py` 38/38. No night has run yet.

**Why deferred:** it can only be observed after 03:30.

**Activation criterion:** after 2026-10-01 03:30, read `~/.claude/state/pp-eval/nights.jsonl`.
Pass = one row with a harvest block or a named skip reason (RAM < 6 GB, owner active). No row
at all = the task did not fire: check `schtasks /Query /TN PP-SelfEval /V` LastTaskResult.
Resumption: `vault/specs/pp-self-eval.RESUMPTION.md`.

**2026-10-01 — PASS on the criterion, and a defect it exposed, FIXED.** The task fired:
row `started 2026-10-01T01:30:01Z`, `SKIPPED: a session transcript changed in the last 15 min
(2639597a-....jsonl)`. That transcript is the worker of mission `m-20f1013db18c` (RUNNING), and
7 missions were RUNNING, so "owner active" would have skipped every night a mission was in
flight and D6 could never start. Fix in `nightly.owner_active`: a transcript whose session owns a
live mission (`gsd_mission.mission_for_session`) is not the Owner; an unavailable mission store
fails closed. Gates V-EVAL-MISSION-WORKER-NOT-OWNER, -ENDED-MISSION-IS-OWNER (control),
-MISSION-LOOKUP-FAILS-CLOSED; suite 41/41; isolated drill 2/2 KILLED, control 41/41. Note for
future drills: the harness must also copy `tools/gsd_mission.py` + `tools/gsd_long_run.py`, or
the control goes red. Next observable: tomorrow's row should not skip on a mission worker.

## D5 — PP Self-Eval: 5 mutation drills never ran

**State:** S1 4/4 and S2–S4 7/12 killed, 0 survived. Not run: quota mid-night stop, quota
ceiling, lock, owner-active skip, proposal gating (`drills_s2s4.json` entries 9–13; harness
`eval_drill.py` with a clean-copy control). Both lived in session scratchpad 5fb53f17; if it is
gone, rebuild from the drill list in commit `0ba8565`'s message and this entry.

**Why deferred:** Claude Code reaped the drill for host memory pressure (1.9 GB free of 31 GB)
and asked that it not be restarted unprompted.

**Activation criterion:** free RAM >= 6 GB. Run the 5 drills on isolated copies; each must
print KILLED and the live files must hash unchanged. ~20 min.

**2026-10-01 — 4 of 5 RUN on GEX44, all KILLED.** The handoff of 5fb53f17 listed 4 unrun
(`d5_b.json` + `d5_c.json`); `d5_a.json` (quota ceiling) is not re-verified here and its
earlier result is not on record in this entry. Method: `git archive` of HEAD `8a7cfaa`
(subject paths last changed `caeec1a`) for `modules/pp_eval`, `modules/owner_queue`,
`tools/test_pp_eval.py` and its fixture, copied to `kobii@gex44:~/drills/d5-<ts>/`; the
harness was `eval_drill.py` with its hardcoded `PP = ~/.claude/...` replaced by an argument,
because on GEX44 that path is the host's own live install, not the laptop's HEAD. Result:
CONTROL clean copy `PP_EVAL_PASS=38/38`; KILLED V-EVAL-QUOTA-STOPS-NIGHT,
V-EVAL-LOCK-REFUSES-SECOND, V-EVAL-OWNER-ACTIVE-SKIPS,
V-EVAL-PROPOSAL-QUEUED-ONLY-WHEN-ACTIONABLE; exported tree hash unchanged. Laptop files never
touched. Remaining: re-run V-EVAL-QUOTA-CEILING-SKIPS (`d5_a.json`) if its first result
cannot be found.

## D6 — PP Self-Eval: bank has 0 validated tasks (need >= 8)

**State:** first real harvest reaped after 2 legitimate rejections (an environment-dependent
mirror test; a 200-check suite red at its own fix). Nights harvest 5 per night on their own.

**Why deferred:** memory pressure; the nightly run will continue it without a session.

**Activation criterion:** `python tools/pp_eval.py status` shows `bank_tasks`. If still < 8 after
3 nights, PP's history is too environment-bound (many tests read the live install): add repos
whose tests read their own tree to `~/.claude/state/pp-eval/config.json` `"repos"`.

**2026-10-01:** `bank_tasks: 0, rejected: 2`. Night count toward the 3-night rule: 0 that ran
(the only night skipped on a mission worker, fixed in D4). Not harvested on GEX44 instead: the
bank validates tasks in the environment that ran them, and the nights run on Windows.

## D7 — Capability gaps 2–6 (audit `vault/audits/se-capability-gaps-2026-09-30.md`)

**State:** gap 1 (self-eval) built. Open, in the audit's order: (2) post-edit diagnostics —
`quality-gate.js` only reminds, nothing runs ruff/tsc on an edited file; (3) testing aimed at
user code — hypothesis and coverage installed, unused; mutation machinery points at PP only;
(4) SAST + dependency CVE scanning — semgrep, osv-scanner/pip-audit not installed; (5) symbol-
level code intelligence — no language server installed; (6) CI for PP's own 600+ gates.
Cheap alongside: wire `refcheck` and `done_gate` (built, no caller).

**Why deferred:** Owner chose gap 1 first; each is its own T2 spec.

**Activation criterion:** Owner picks the next gap. Gap 2 is the cheapest (ruff is installed).
Once D4–D6 give verdicts, re-rank using the self-eval's own data.

**2026-10-01: gap 2 DONE** — `hooks/post_edit_diagnostics.js`, spec
`vault/specs/post-edit-diagnostics.md` (LIVE rows + evidence), 88e8c91 / cfa3275, registered
and proven live. Open: gaps 3–6 (each its own T2 spec) and the cheap `refcheck` / `done_gate`
wiring; still waiting for the Owner to pick.

**2026-10-01: gap 3 v1 BUILT** (Owner: "3") — `tools/test_gaps.py` + `/test-gaps`, spec
`vault/specs/test-gaps.md`, dc7f781. Uncovered changed lines + surviving mutants on covered
changed lines, in an isolated copy; subprocess-driven tests measured. 14/14 gates; GEX44 drill
6/6 KILLED. Not in v1: hypothesis, fuzzing, flaky tests, non-Python. `/test-gaps` copied live
2026-10-01 (Owner "y"). Real project verified on GEX44 (75b0fd7).

**2026-10-01: gap 4 v1 BUILT** (Owner: "gap 4") — `tools/security_scan.py` + `/security-scan`
(live), spec `vault/specs/security-scan.md`. semgrep 1.178.0 (own venv `Apps\semgrep-venv`)
on changed lines + osv-scanner v2.6.0 (official release, SHA-256 verified, `Apps\osv-scanner`)
over lockfiles, `introduced` vs `existing`. UNCHECKED never reads as CLEAN. 12/12 gates (452 s,
needs network). Not in v1: done-gate wiring (blocking Stop hook + network scan = the starvation
shape), SBOM, licences. Open: gaps 5–6.

## D8 — Mission continuity: merge the UKDL candidates

**State:** `vault/knowledge_base/mission_continuity/UKDL_CANDIDATES_DURABLE_SUBSTRATE.md` not yet
merged into `ukdl-universal.md`. On 2026-09-30 another pane held 884 uncommitted lines there.

**Why deferred:** committing that file would sweep the other pane's hunks into this commit.

**Activation criterion:** `git status -- vault/knowledge_base/ukdl-universal.md` is clean. Then
merge by pathspec and check the hunk headers before committing.

**2026-10-01 check:** still blocked. `ukdl-universal.md` now carries 1248 uncommitted lines
(was 884) and was written 10:45, seven minutes before the check: a live writer.

## D9 — Delete the `gsd-long-smoke` worktree and branch `gsd-autonomous-run`

**State:** leftover from the M6 canary; obligation 3 of the 2026-09-30 rollover capsule.

**Why deferred:** destructive; needs an explicit Owner yes (a bare "y" to a two-option question
was not taken as one).

**Activation criterion:** Owner says delete. Then read both first (worktree status, unpushed
commits on the branch) and delete only if nothing unique would be lost.

**2026-10-01 — Owner said delete; NOT deleted, unique work found.** Repo
`Desktop\Cursor Projects\gsd-long-smoke` (no remote), worktree
`.claude\worktrees\gsd-autonomous-run`, branch head `806f202`. The branch carries **78 commits on
no other ref** (`rev-list --count master..gsd-autonomous-run`; a first query with `--exclude`
returned 0 and was wrong), and the worktree holds uncommitted work: 4 modified files (+76/-17)
and untracked `smoketext/reverse.py`, `tests/test_reverse.py`, phase `09-word-count`, last
written 2026-09-29. Needs a second answer: archive first (git bundle of the branch + a copy of
the dirty worktree under `~/.claude/backups/`) then delete, or keep.

**DONE 2026-10-01 16:2x** (Owner: "delete"). State re-verified first (head 806f202, 78 unique,
same diff, no write since 09-29, no process). Archived to
`~/.claude/backups/d9-gsd-long-smoke-20261001-162241/`: `gsd-autonomous-run.bundle` (verify OK,
head 806f202) + `worktree/` (190/190 files, uncommitted files hash-identical). Then
`git worktree remove --force` and `git update-ref -d refs/heads/gsd-autonomous-run 806f202`
(deletes only at the expected head). Restore drill: cloning the bundle gives head 806f202, 91
commits, 78 not on master. Restore with `git fetch <bundle> gsd-autonomous-run:gsd-autonomous-run`.

## D10 — `test_hook_mirror_identity` red 3/5 (other panes' files)

**State:** new live/repo drift in `hook-dispatcher.js`, `zero-issue-gate.js`; stale
KNOWN_DIVERGENCES entries `closer-guard.js`, `learning-sentinel.js`,
`windows-bash-bridge-guard.js`. `research-intent-detector.js` was reconciled in `55fe169`.

**Why deferred:** those files belong to live work in other panes.

**Activation criterion:** when those panes commit, decide per file which side wins (the gate's
own instruction), sync, and drop the stale entries so the ratchet turns.

**2026-10-01 — now 4/5.** Stale entries dropped (the three files are identical on both sides).
Decisions on the two drifts, neither applied:
- `zero-issue-gate.js`: **repo wins.** Committed (6f897bf 09-28, 745cc3b 09-27) and a behavioural
  superset of live (live is the 09-16 build; its 42 "unique" lines are the pre-refactor shapes,
  and MIX_ENV, jwExemptionGranted and the BLOCKED_DELIVERY notice all survive in repo; only the
  footer wording changed). Never deployed, so the "never starve the host" fix is not live.
  Deploy = back up `~/.claude/hooks/zero-issue-gate.js`, copy the repo file over it, `node
  --check`. Refused twice by the auto-mode classifier (self-modification). **DEPLOYED
  2026-10-01 15:33** after the Owner left auto mode ("try the hook thing again"): live == repo
  (SHA-256), `node --check` OK, old 09-16 build at `~/.claude/backups/hooks-20261001-153359/`.
  Mirror gate still 4/5, now only on `hook-dispatcher.js`.
- `hook-dispatcher.js`: **repo is ahead, not applied.** Its only difference is uncommitted work of
  another pane (names the abandoned scripts in `CHAIN-DEADLINE-ABANDONED before pool`; `node
  --check` OK, `restSteps` in scope). Idle since 09-30 20:27. Deploy after that pane commits it.

---

## D11 — Wii Sports Tennis reconstruction with Wii Motion OS integrated (Owner, 2026-10-08)

**Goal:** reconstruct the Tennis of Wii Sports from `E:\wbfs\Wii Sports + Wii Sports Resort [SP2P01]\SP2P01.wbfs`
(present, 1,549,795,328 bytes; the brackets in the folder name need `-LiteralPath` in PowerShell) into
`C:\Users\User\Desktop\Cursor Projects\Wii Projects\KobiiSports + KobiiSports Resort` (exists, EMPTY on 2026-10-08), so its
motion handling can be improved with Wii Motion OS integrated at source level.

**Known on 2026-10-08:**
- Wii Motion OS is a T3 spec plus 19 datasets (`KobiiSports Resort/_ksr_clean_repo/vault/specs/t3-wii-motion-os-compendium.md`,
  non-goal "implementation"), and `_ksr_clean_repo/tools/wmos_adapter` is at V0A. U1 (the injection substrate) is unresolved.
  With reconstructed source, motion code is changed in source, so the U1 study is not on this path.
- The recon factory is built for the Wii Sports Resort main.dol (34,159 functions). Wii Sports is a different executable,
  so it needs its own corpus, census, split and oracle-parity setup.
- Unknown and decisive: how Tennis's code is packaged (module vs main executable), its function count, and how many of
  its functions are shape-identical to already-solved Resort functions (shared engine and library families).

**Recommended scope:** a closure-scoped reconstruction, not a full matching rebuild. Reconstruct the motion closure
(Wiimote read, swing detection, racket and ball response), relink it with retail objects for everything else
(`relink.py` / `lcf2ld.py` exist in the decomp core), then integrate WMOS in that source. Validate in Dolphin on GEX44
(D7), then on hardware.

**Cost:** hypothesis until recon-factory CP50 measures the cost per function. See the Owner estimate of 2026-10-08 in
the gen3 session. Step 0 is zero-model: extract the disc, locate Tennis, count its functions, measure shape overlap
with the Resort census.

**Step 0 DONE 2026-10-08** (zero-model, `vault/plans/d11-tennis-step0.md`):
- Tennis is inside `files/EU/sys/sports/SportsPackEP.dol` (no RELs). DTK finds 14,885 functions.
- 63% of the DOL's functions have an exact shape match in the Resort factory split; only 23% of the Tennis candidate
  does (1,797 functions, an upper bound).
- The disc's Resort DOL is not the factory's binary.

**Step 1 DONE 2026-10-09** (zero-model, `vault/plans/d11-tennis-step1.md`):
- The novel closure inside the Tennis units is 1,323 functions, which agrees with step 0.
- Only 3 game functions call KPAD, and none of them is reachable from Tennis. Tennis gets motion through stored
  controller state (data), not through calls, so a call walk cannot size the motion closure.
- A DTK unit is not an SDK library: the 3,900-function SDK object made a first count meaningless. Libraries are now
  bounded by their version-string anchors.

**Step 2 DONE 2026-10-09** (zero-model probe, `vault/plans/d11-tennis-step2.md`):
- It corrected step 1: the 3 callers only call setters. KPADRead is inferred to be fn_800DB250.
- The read result lands in a per-channel controller object (~0xFB8 bytes), not in a global. The manager is published
  in SDA globals lbl_805133B8 and lbl_80513DF0.
- 51 Tennis functions (122 in the game) load the manager global directly, which is a floor. One-indirection field
  reads: Tennis 0. Inline reads through `this` are UNRESOLVED.

**Step 3 DONE 2026-10-09** (zero-model probe, `vault/plans/d11-tennis-step3.md`):
- Each controller is a 0xFC0-byte object at mgr+0x1C[ch]. The two getters are fn_800B7AD4 and fn_801DDEC8.
- Tennis has 50 getter callers. 20 of them read controller fields, mostly the raw buffer and low offsets. The derived
  state is read in 1. All of these are floors.
- Controls: positive met; negative 0/50.
Optional step 4: one level of argument propagation, then subtract the Resort-shape overlap.

**Activation criterion:** recon-factory CP50 has reported its cost per function and the learning-curve result (the
per-game cost model needs both). Step 0 may run earlier, because it is zero-model.

---

## D12 — cost-collapse / expected-completion admission: the rest of the mission (Owner, 2026-10-10)

**Goal:** finish the expected-completion admission program (`vault/specs/expected-completion-admission.md`, APPROVED)
and continue cost-collapse T2 reconciliation -> T3-T7 (`vault/specs/cost-collapse.md`). Work tree
`C:\Users\User\Apps\pp-cost-collapse`, branch cost-collapse/main (local, never pushed). Binding plan:
`vault/plans/cost-collapse-convergence-plan.md` there (Owner y 2026-10-08; E3C is split into E3C1/E3C2; D-C = stop for an
Owner cap decision after E4b).

**Done (all in that work tree):** T1 f3b503e6, T2 2b5b0ea5, E1, E2, E3-A 3f2ff5c4, E3R (D3 flip 14879ab0 + RECEIPT-E3
8350d524: 45 calls / 7.62M vs 34 / 6M), E3G 0ea29fc7 (call checkpoint + receipt survives the stop), E4a work-tree half
42ac887c (LAUNCHABLE_VERDICTS / KNOWN_VERDICTS / verdict_unknown, V-VERDICT 14/14).

**Stopped where:**
- E4a live half: PARTIAL on the laptop (session guard). On 2026-10-09 the laptop had 0.7 GB free; the Owner moved the
  chain to GEX44 ("Todo en GEX44"). Handoff 067af7c2. WU-E4a2, mission m-16bde3ea1101 on GEX44, ended
  **BLOCKED_PREMISE** (receipt 44a2a6f3, fetched as `gex44/cost-collapse` in the work tree): GEX44's live install
  (`~/.claude/skills/claude-power-pack` @1872e9a1) has **no route admission at all** (no route_admission.py, no `admit`).
  Nothing was applied and nothing was armed. Any mission armed on GEX44 would launch ungated.
- Not started: E3C1, E3C2, E4b/E4 landing, T2 reconciliation, T3a/T3b, T4-T7. gsdx-pcc m-53847a002b65 stays held until T7.

**Loose state to settle first:**
- **This live tree carries uncommitted E4a edits** to `tools/route_admission.py` and `tools/gsd_mission.py`, plus untracked
  `tools/test_verdict_contract.py` (rollback tag `cc-e4a-pre`). The live sweep serves that code. Snapshot:
  `vault/plans/expected-completion-E4a-live.patch` in the work tree (sha256 6DD6ABC9...5129C1). Live gates there were
  admission 43/43, envelope 55/55, owner_hold 32/32, test_gsd_mission 226/227 (V-MC-SUP-HOST-UNANSWERED-NOT-BLOCKED,
  unattributed vs cc-e4a-pre), test_verdict_contract RED (no live envelope_fixture.py). Land or revert; do not leave it.
- Work tree: the E4a worker's uncommitted test edit is snapshotted as `vault/plans/expected-completion-E4a-worktree-test.patch`.
- GEX44: clone `/home/kobii/missions/cost-collapse`, tag `cc-e4a2-pre` on its live tree, mission m-16bde3ea1101 BLOCKED.
  GEX44 has no session_budget_guard.
- Open points: E2's EAC reforecast is inert live (the only call site, gsd_mission.py:2778, passes no usage) -> E3C2.
  On GEX44 `admit` printed expected=None safety=None: verify the UNKNOWN fail-closed path before trusting a GEX44 verdict.

**Remaining units, in order:** E4a live (WATCHED contract on the plane whose sweep runs the chain) -> E3C1 (guard latency
offset/high-water, E3G drills d2-d5 + d4 diagnosis, 4 unrun suites, slim-t2 borrowed g/calls_err) -> E3C2 (EAC usage
wiring, recalibration with the E3 pair, promotion Cognitive CI check, route-E4) -> E4b/E4 (land T1, T2, E1-E3C here with
a rollback tag, KV/UKDL/CBR ratchet) -> **D-C Owner cap decision** -> T2 reconciliation -> T3a/T3b -> T4-T7.
Packets: `vault/specs/packets/` in the work tree (WU-E3C1 is still to be written from WU-E4a section 3).

**Activation criterion:** the Owner picks a plane:
(a) laptop, once free RAM >= 4 GB: resume E4a's live half here (`RESUMPTION_FILE.md` E4a block in the work tree);
(b) GEX44: first a scoped unit that ports the E1-E3 admission stack + E4a contract to GEX44 live; or
(c) GEX44 with the sweep for cost-collapse run from the clone's tools instead of live.
Budget: goal `cost-collapse` cap 69,774,423 declared 2026-10-08. What the E-units spent against it is not summed here; read
it from the goal ledger, do not estimate.

---

## D12 — EDD full-convergence mission: everything after P2-B-R (Owner, 2026-10-10)

**Owner:** "put the rest of the mission in the backlog of claude power pack". Parked, not cancelled.

**Where it runs:** GEX44, worktree `/home/kobii/missions/edd/.claude/worktrees/edd-run` (branch `mission/edd-run`),
workstream `.planning/workstreams/edd`. The resume prompt there is `RESUMPTION_FILE.md`, and the plan with decisions
D-01..D-05 is `ROADMAP.md`. The execution log of record is `vault/specs/edd-compiled-execution-canary.md`.

**Sealed as of 2026-10-10:**
- **Heads:** edd-run `594a36c1`, GEX44 live PP `30fdbf0f`, laptop `72f4dcdf`.
- **Phase 1:** done, except criterion 4.
- **Phase 2, P2-B v1:** FREEZE because the H01/H02 keys were incomplete.
- **Phase 2, P2-B-R (gold repair):**
  - Holdouts v2 sealed at `95a47e80`.
  - The independent re-audit found H01, H02 and H07 all correct, with 0 leaks.
  - The judge returned FREEZE on cost only: the re-auditor's tokens were 38.4 % under forecast (5 calls against 7 forecast); the author was −17.6 %.
- **Built and live:**
  - The breaker meter attributes per session on GEX44.
  - Contamination scan: `edd_p2b.py scan`.
  - Gold lineage/reseal: `edd_p2b.py reseal`.
  - The arming guard refuses learnings marked "not built" without a disposition, which is the UC-19 effect path.

**Remaining, in order:**
1. **Estimator residual for P2-B-R-AUDIT.** Find which two steps the 5-call audit skipped, then correct the audit cost
   model. The ±30 % rule requires this before the next unit is armed.
2. **Phase 1 criterion 4.** Write D-01..D-05 as DRK DecisionRecords (`modules/decision_review/decision_record.py`).
3. **P2-C, V-EDD-BENCH runner and BEFORE baseline:**
   - B0 is the deterministic pipeline (structural zero).
   - B1 is a model baseline, one isolated call per case.
   - Matches come from a blind scorer unit, and metrics are computed deterministically from them.
   - Packet, done-check and a frozen forecast are committed before arming. Arming goes only through `tools/edd_p2_chain.py`.
4. **Close Phase 2** (ceiling 16M), then re-forecast Phases 3–7 against what is left of the ~65M envelope (D-05).
5. **Phases 3–7 to Goal convergence.** Phase 3 includes the answer-leak transcript detector, which reuses `scan`. Close with the full handoff from the mission prompt.

**Open debt carried with it:**
- No push alert when the sweep is FAILING.
- UC-13: the generic `gsd_mission` arm is unbounded (PARTIAL, deferred to its owner).
- The iteration standard `Downloads\Promptsss\Prompts pa iterar\Universal\iteracion-avanzada-universal.txt` has not been read.
- Known reds stay explicit:
  - Laptop: V-MC-SUP-HOST-UNANSWERED-NOT-BLOCKED (`_auto_budget` refreshes `updated_at`).
  - GEX44: V-MC-PLAN-FACTS-REFUSES-OVERLAP (pre-existing).
- `m-e3ed7e14a5e2` stays untouched.

**Cost rule (D-05, binding):**
- Pane 24ca0218 coordinated 25.36M / 109 calls against a 2.0M forecast. Never coordinate from a long-context laptop pane.
- Use a fresh pane per phase. Measure its per-call cost (`mission_spend.session_tokens` on its own transcript) before
  budgeting, and hard-cap the coordinator per phase (1.0M for the rest of Phase 2).
- About 26M of the ~65M envelope is spent.

**Activation criterion:** the Owner says to resume EDD. Then, in a fresh pane, read the RESUMPTION_FILE on GEX44 and start at item 1. Never run `/gsd-autonomous --ws edd`.

---

## D13 — dgl durable goal / disposable lease: W3-W8 (Owner, 2026-10-10)

**Owner:** "put the rest of the mission in the backlog of claude power pack" (pane 42ce1ae6). Parked, not cancelled.
(The two D12 headings above were written by two panes on the same day; this entry takes D13 to avoid a third.)

**Where it lives:** worktree `C:\Users\User\Apps\pp-dgl`, branch `dgl/durable-goal-lease` (pushed to origin by the W1b
worker, unprompted). Plan: `vault/plans/durable-goal-lease-2026-10-09.md` (d0c2077b). Chain: `vault/programs/dgl/chain.json`
+ `CHAIN.md` (unit table, authoring rule). Goal `dgl`, cap 17.0M, chain envelope 16.0M.

**Sealed (head eaadf11f):**
- W1 PARTIAL (read-only, design recorded), W1b DONE: ledger lease epochs, programme, lease_open CAS + idempotent
  succession, lineage CLI; `tools/test_goal_lease.py` 10/10, 4 mutants killed.
- W2 DONE: `modules/provider_routing/workspace_registry.py` (generation CAS, fenced settle), registry-first binding
  precedence, cwd entry OBSERVE-only once the registry journal exists, closed-lease fence in the hooks;
  `tools/test_workspace_lease.py` 10/10, 4 mutants killed, regressions 0/0. Nothing installed live yet (that is W5).
- P3b-2 itself was run by main pane a5308810 (SRC PROVEN 294, P3B2_CHECK=PASS); see `vault/programs/dgl/D2-owner.md`.

**Stopped where:** the chain refused W3 on envelope (`used 11,154,078 + need 5,100,000 > 16,000,000`, tick log
`~/.claude/state/dgl-chain-tick.log`). Task `PP-DglChain-Tick` is **Disabled**. W3 packet + route are written and committed.

**Remaining, in order** (rows in CHAIN.md):
1. W3 — terminal reconciliation (TERMINAL_PROVEN vs UNKNOWN_RESERVED) + atomic succession `tools/goal_succession.py`.
2. W4 — predictive drain, SessionEnd wake, autopsy against binding records, crash matrix.
3. W5 — install to the live tree (DEPLOY class; never touch `tools/gsd_mission.py` / `tools/mission_steward.py` while
   ce-lifecycle-v3 has them dirty); re-point the tick to the live `tools/goal_chain.py`.
4. W6 — P3b self-host: lineage rf-p3b (L1, immutable) -> rf-p3b2 (L2); reconcile c2ae4b5c's hold by measured transcript.
5. W7 — VERIFY-ONLY of P3b-2 + lineage. 6. W8 — fresh-project canary, UKDL/CBR, retire the manual succession instructions.

**Gaps found live, owned by W3-W5:** a held/parked mission reads as "running" to the chain for ever; packet missions
without `done_check` stall on GSD NO_PHASES (bootstrap: `vault/programs/dgl/unit_done.py`, attached by the tick wrapper);
the tick borrows `gsdx_chain.py` from `Apps\pp-gsdx-factory-2`; W2 left no workspace-claim CLI (W6 needs one).

**Activation criterion:** the Owner raises the dgl budget. Units cost ~4-5M each (W1b 4.5M, W2 5.1M routes), so W3-W8 need
roughly 20-25M more against 4.85M left; a raise needs `--owner` on a TTY (`mission_spend.py`). Then `Enable-ScheduledTask
PP-DglChain-Tick`; the next tick arms W3. Read `vault/programs/dgl/RESUMPTION.md` in the worktree first.

---

## D14 — goal budget admission (A1 containment): the rest of the mission (Owner, 2026-10-10)

**Goal:** the pre-call goal reservation that A1 lacked (`vault/specs/goal-budget-admission.md`, status done).
Evidence and every number below: `vault/programs/cognitive-economy/gen2/evidence/goal-admission/CANARY.md`.

**Done (branch feature/knowledge-acquisition, local, not pushed):** closeout fix 19240f98, final-reply headroom a3aaa515,
output margin ac6af297, unwritten issuing request ffd8f9e9; Owner "done" on live canary #6 (2,912,243 of a 3M cap,
two panes + Agents, one reply each after the deny) 8259a97e. Capsule debt closed 2026-10-10: renewal churn b15a1792,
hookreg StopIteration 182fc46b. Gates at close: GOAL_PASS=58/58, HOOKREG_PASS=16/16 --live, ADMIT 12/12, ROUTE 33/33.

**Remaining, in order:**
1. **GEX44 has no goal admission.** Per D12 (2026-10-09) GEX44's live install has no session_budget_guard; spend there is
   UNKNOWN and fails closed only for a goal that lists hosts. Not re-verified here. Owner of the port: A3 U4
   (`gen2/AMENDMENT-A3-2026-10-07.md`) / D12 option (b). Done = a GEX44 worker bound to a goal is admitted and settled in the
   laptop journal, and an unlisted host is refused.
2. **agent-solo-guard is machine-global.** `~/.claude/hooks/agent-solo-guard.js` keys its in-flight tracker on the host, so
   an Agent in one session blocks Agents in unrelated sessions for 30 s (canary #4: a worker blocked twice, ended its turn
   with a question, never reached the cap). Key it by session (or goal); it lives in `~/.claude` (HR-001: Owner step).
3. **V-SBG-LATENCY is load-sensitive.** `tools/test_session_budget_guard.py` asserts < 50 ms wall time; measured 13 ms to
   3,183 ms on identical code under host load. Make it judge CPU time or a median of N, so a red means the guard got slower.
4. **Residual reply margin (accepted).** A final reply can exceed its hold by a few hundred tokens (+187 in #6); the cap held
   only because leftover room absorbed it. Fix if a canary ever crosses: pad each final hold (~2%).
5. **The canary is not a recurring instrument.** `canary2.py` + `check3.py`/`check5.py` sit in the evidence folder. Promote to
   `tools/` (stagger, `final`-aware refusal detector) and decide a cadence. Each run costs ~3M processed: Owner decision.
6. **A1 itself is still ECONOMIC_CONTAINMENT** (A1 amendment: 42,307,381 / 20M, T3 + T7 frozen). A crossed cap is never
   raised: resuming means a new goal id the Owner declares. a1/u1 + a1/a1-2 are carried in `ce/a3*` and were never merged
   into `ce/gen2-completion`.
7. **AO phases 2-7 were paused "until pre-call budget admission exists"** (A1 amendment, AO exception). That condition is now
   met; they need a declared goal before they run.
8. **A1-6 (resume exam `next`).** Seen again 2026-10-10: `rollover.py certify` rejected an abbreviated first obligation and
   accepted only the capsule's verbatim text. Evidence for the A1-6 follow-up on next-action matching.

**Activation criterion:** item 1 when the Owner arms any unit on GEX44 (before arming, not after); item 2 when the Owner
approves a `~/.claude/hooks` diff; items 3-5 on any free PP slot (3 and 5 are zero-quota except 5's runs); items 6-7 when the
Owner declares the next goal for A1 or AO. Read CANARY.md's closing verdict first.

---

## D15 — GSD X Reconstruction Factory (gsdx-factory-2): the rest of the programme (Owner, 2026-10-10)

**Goal:** finish the Master Plan v1 (`vault/plans/gsdx-factory-master-plan.md` in the work tree, Owner "y" 2026-10-09:
Part A + recon-factory through Phase 9, Full WSR excluded, envelope 40M / hard 55M inside the 100M ledger cap). Work
tree `C:\Users\User\Apps\pp-gsdx-factory-2`, branch gsdx-factory/v2 (local, never pushed). Goal `gsdx-factory-2`.

**Done:** S1 economics (55ced1e8 ledger settle_stopped/correct, 006c8b7b steward, RECEIPT-S1 DONE); L1 obligations
595 rows disposed, unknown 0 (DONE_WITH_LIMITS); PLAN-1; DOCTRINE (41 rows enforced, 8626dadc); W3 PARTIAL, accepted
because dgl took over what it left (0b05acb7); PLAN-2; AG2R (Part A rows 11/11, 99446b7c); W4 live re-forecast tool
(610808c5, forecast.json 239120ec); PLAN-3 (6cf33a0a). Deterministic chain tick `tools/gsdx_chain.py`, CHAIN_PASS=13/13,
scheduled task PP-GsdxChain-Tick (every 15 min). Spent 8,817,916 measured, open 0 (goal-status 2026-10-10).

**Parked (unarmed, `chain.json` → `parked`):** AGMIN → AGCAN → AGECON → AGDONE → PLAN-4 (Part A G2..G5 + next planner).
Each also waits on `C:\Users\User\Apps\pp-dgl\vault\programs\dgl\W5-receipt.md` and ce-lifecycle-v3 WU-INST2.

**Not in the chain yet:** W5 GEX44 control-plane port (DEPLOY class: read the hard rules first; also resolves
cost-collapse E4a2 as option (a), see D12 cost-collapse); W6 rows not mapped to a phase; W8 closeout = promote KNOWLEDGE
K1-K7 (`vault/specs/gsdx-factory/KNOWLEDGE.md`) to UKDL/CBR; Part B; Production Reality. Recon-factory phases are
the Owner's CP50 track (C1 re-armed as m-4e2364edc538, goal cp50-c1b, in wt_cp50_c1); they are not gsdx units.

**Forecast (W4, forecast.json):** remaining 12.7M expected / 5.1M lower / 22.1M safety; total 21.4M expected, inside 40M.

**Open debt carried with it:**
- K7: live admission (ce-lifecycle-v3 L3) charges growth per tool call, so it over-prices ~2.8x. Routes are written
  in declared steps to fit; the fix belongs to ce-lifecycle-v3.
- K6: the supervisor still renews a worker whose receipt is not exactly DONE (91K and 98K wasted renewals). The chain
  side is fixed (5e835a8a); the packet template and supervisor side belong to ce-lifecycle-v3.
- Holds kept as UNKNOWN: old goal 530d9700 232,321; cp50-c1 150,000 (seq 6, old C1 session c021de1c).

**Activation criterion:** the Owner says to resume gsdx-factory. Then, in a fresh pane (never this long one), move the
`parked` units back into `units` in order, read RESUMPTION_FILE.md in the work tree, and let the chain tick arm them.
Before W5, run `hardrule_compile.py --class DEPLOY`.

