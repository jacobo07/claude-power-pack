# Ascension Autopilot: self-continuing S generations, two lanes -- PLAN (Owner choices 2026-11-11 ~16:44Z, pane d957c937)

Owner choices (AskUserQuestion, so NOT an authority receipt): budget 80M processed/day, 400M total; standing policy
"additive profiles allowed under the S26C conditions"; two parallel lanes (KSR, Tennis). verify_owner_turn refuses tool
results by design, so the mission `authority` calls need ONE typed Owner message (sentence at the end).

## Reality it rests on (16:45Z)
- Mission runtime already parks a finished wave as CHECKPOINT_COMPLETE with unblock "a new bounded plan inside the standing
  authority clears the checkpoint; only capital/intent/irreversible needs the Owner". Missing piece = judge + planner + armer.
- The one-shot watcher s26d_autoarm.sh proved the armer path (archive -> scaffold -> retarget -> authority -> clear) in dry runs
  and a live cron tick (16:40:01Z).
- Trusted dirs on GEX44 include gen3-pp (KSR lane) and tennis-all-match (t1 worktree, branch mission/tennis-all-match).
- S27 Tennis is running on gen3 (m-10566700b1fe); T2 typelift transfer to Tennis: dev 14 compile / 0 exact, held-out 8 / 0.
- GEX44: 20 cores, 49 GB available, claude 2.1.113 for headless judge/planner calls. No notification channel (Telegram unset).

## Design (EXECUTION mode; reuses the mission runtime, no second scheduler/ledger)
Home: GEX44 `~/agora/ascension-autopilot/` (outside the live PP clone, like the S26D watcher and the pgrep hook: no live deploy).
Driver: cron */5 + flock -> `autopilot.py tick`. One tick handles each lane at most once.
Lanes (`lanes.json`): KSR = cwd gen3-pp, product t1-campaign; TENNIS = cwd tennis-all-match (own GSD milestone, own branch).
On a lane whose mission holds CHECKPOINT_COMPLETE and whose generation is not yet processed:
1. JUDGE (independent `claude -p`, fresh context, tools limited to Read/Grep/Glob + running the checkpoint's own test commands):
   re-runs every gate named in the checkpoint + receipt shas; verdict AGREE / DISAGREE / INCONCLUSIVE as JSON with rc evidence.
   Not AGREE -> lane PARKED (never re-planned on an unverified result).
2. PLANNER (`claude -p`, read-only): inputs = checkpoint, portfolio, negative.jsonl rows, retired levers, the brief(s),
   policy; output = next PHASES packet + launch command (S28K, S29K... / S28T...). Must pre-register its decision rules.
3. POLICY (deterministic, autopilot.py, not a model): packet parses to 2-8 `Phase N:` lines; caps sum <= generation cap;
   NOT-authorised block present; forbidden acts absent (push, merge counters, revoke, R2, H2, canonical ctx/headers, certifier
   rule edits, paid); a new certification profile only if the packet names all S26C conditions (independent DOL-bytes target
   oracle, frozen pilot committed before draw, pre/post controls, A2 negatives, historical receipts byte-identical, separate
   counters). Fail -> lane PARKED + owner_queue.md entry.
4. ARM (same CLI path as the watcher): archive milestone, add packet, scaffold, retarget, authority = spend + gen cap
   (owner-turn = the typed Owner message), --extend-hours, checkpoint --clear; verify worker_acked on the next tick.
Budget ledger (`ledger.jsonl`, append-only): per generation the mission spend delta + judge/planner usage from `claude -p
--output-format json`. Caps: 80M per UTC day (a lane waits for the next day), 400M total, wall 2026-11-30T23:59Z,
<= 25M per generation. Fresh llm_fix tokens 0 unless a packet's pre-registered experiment names them (<= 1M/gen).
Stops (per lane): 3 consecutive generations with no new canonical certificate AND no newly validated capability (judge
field); judge not AGREE; policy fail; 2 failed arms. Global: kill switch file `OFF`, total/wall exhausted.
Owner-facing: `digest.md` (one block per generation: certs before/after per profile, spend, verdict, next), `owner_queue.md`.
S26D watcher stays as is (KSR lane's first step); the autopilot takes over each lane from its next checkpoint.
The Tennis lane starts at S27's checkpoint: its successor S28T is armed in tennis-all-match, KSR continues S26D on gen3.

## Tests before enabling (tools/test_autopilot.py, run on GEX44 against fake mission records + a scratch git repo)
policy rejects each forbidden act and a profile packet missing any one S26C condition; budget refuses the 81st M of a day and
the 401st M; 3 blank generations stop the lane; DISAGREE parks; kill switch stops a tick; the armer is dry-run on a fake
record end to end; a mutated check (e.g. policy disabled) must turn the suite red.

## Rollback
`touch ~/agora/ascension-autopilot/OFF` (next tick does nothing) or remove the cron line (backup kept). Every arm is a
normal mission act, reversible with `hold --stop`; all generations are micro-commits on their own branches; nothing canonical
is written by the autopilot itself.

## Cost to build
~4-6M processed tokens in this pane, 0 fresh, USD 0. Judge + planner per generation ~1-2M processed, counted in the ledger.

## Typed Owner authorization needed (one message)
"Apruebo autopilot: 400M total, 80M/día, hasta 2026-11-30, 25M máx por generación, perfiles aditivos con condiciones S26C, dos carriles KSR y Tennis"
