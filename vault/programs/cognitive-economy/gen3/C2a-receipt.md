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

## Variance (coordinator, 2026-10-10, answers the cost-breaker hold)

Metered from the worker transcript `58ac31ae-46c6-47a7-9c28-03546fd2584f.jsonl`, deduplicated by message.id (last
usage wins): 12 calls, claude-sonnet-5-5, input 24 + cache_write 171,670 + cache_read 1,894,944 + output 39,641 =
**2,106,279**, equal to the breaker's figure. The "Calls used: 8" line above counts tool calls up to the receipt; the
transcript has 11 tool calls plus a final text turn.

- The hold's 875,000 is not a forecast: it is `token_estimate` = route stop 1,750,000 / 2, so any run past the stop
  reads as ">2x". The real envelope was target 1.6M / stop 1.75M; the overrun against target is 1.32x.
- Calls 1-9 (the packet's 9-call plan, with a 3rd dossier page in place of the capsule_build Edit) = 1,502,116, under
  target. Calls 10-11 re-issued the commit after the `.ksr_vault` snapshot gate refused it (400,827); call 12 is the
  closing text (203,336). The whole overrun past target is those 3 unplanned calls.
- Per-call price was right: admission 1,467,018 / 9 = 163k; measured mean of calls 1-9 = 167k (+2%).
- Floor: call 1 already carried 107,338 before any work (system + rules + packet), paid 12 times = ~1.29M (61%).
  Context then grew 107k -> 203k (dossier 3 pages, arm_a.py 25k output kept in context). Output was 39,641 (1.9%).

Remaining work recomputed: in `vault/backlog/2026-10-10_cp50-c2-remaining.md` (row 6 and the C2a-fix lease).
