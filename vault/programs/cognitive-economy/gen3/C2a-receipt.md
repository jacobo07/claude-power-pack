# C2a receipt -- arm-A executor (build only, NO send)

Status: PARTIAL. Mission id: UNKNOWN to this session (no rehydration card was visible; goal cp50-c2).
Calls used: 8 of 9 (packet, dossier x2, arm_a.py, 1 Edit of arm_a.py, test_arm_a.py, run, receipt; commit is call 8+). No subagent, no search tool, nothing sent, no model call, G0_HOLDOUT.json never opened, wt_keosdtk_home untouched.

Files (wt_cp50_c2, branch cp50-c2; hashes: `git -C <tree> log -1 -- <path>`):
- tools/wros/binary/decomp/arm_a.py (prepare / records / executor_from_judged / load_judged)
- tools/wros/binary/decomp/gex44/capsule_build.py (`targets_for=None` keyword + resolve_targets_for; only edit to an existing .py)
- tools/wros/binary/decomp/test_arm_a.py

Drill (verbatim):
ARM_A_DRILL=7/8
PASS V-ARMA-COHORT, V-ARMA-UNITS, V-ARMA-NONL1, V-ARMA-RECORDS, V-ARMA-UNJUDGED, V-ARMA-NOZERO, V-ARMA-NOSEND
FAIL V-ARMA-CAPSULE-IDENTITY AssertionError: targets_for=[id] produced no new capsule: ['cap1-984a35109f79']
BENCH_DRILL=8/8

ARM_A_PREPARED: NOT RUN. The packet gates the real `prepare --first 1 --last 5` on both drills being all PASS; they were not. No capsule, units or job exist for the pilot; capsule id / manifest sha / job dir: none.

Reading of the failure (not fixed, per packet): with targets_for=[main:80426354] build() added no second capsule directory beside the baseline `cap1-984a35109f79`, so either the capsule id is derived from inputs that exclude `targets` and build returned the EXISTS path, or the manifest was not changed. The baseline-vs-None half of the gate passed (default unchanged, same dir and bytes). Not yet known: whether the existing dir's MANIFEST.json now holds the target. Next lease should read _stage_and_seal's id derivation and EXISTS check, make the id cover `targets`, then rerun the drill and `prepare`.
Functions with no unit: unknown (prepare not run; m2c venv refusal, if any, also unobserved).
Open points (decided, not asked): units are one per (function, m2c arm, oracle preset); candidate.UNIT_KEYS is read from candidate.py, not assumed; receipt host key is searched as host/hostname/host_name; arm-A cost tokens are 0 only because no model is called, every other unmeasured field is {"absent": reason}.

HANDOFF NOTE: C2a PARTIAL -- blocker: V-ARMA-CAPSULE-IDENTITY (targets_for does not yield a distinct capsule); prepare not run
