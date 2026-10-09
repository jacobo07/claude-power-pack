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

Next zero-model probe (step 3): find the controller object's allocator (the loop at 800B7D88 in fn_800B7BFC), then
track `this` through argument registers into the Tennis units.

**Activation criterion:** recon-factory CP50 has reported its cost per function and the learning-curve result (the
per-game cost model needs both). Step 0 may run earlier, because it is zero-model.
