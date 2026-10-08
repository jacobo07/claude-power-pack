# WU-TRIP -- spend without durable progress trips a checkpoint; a hold on a LIVE worker ends it (Amendment D L6)

Plan: ce-a3 Amendment D (pp-ce-a3 3aa002af, Owner "y") L6, ex a3b-r R4. Goal ce-lifecycle-v2. cwd = this worktree.
Precondition: WU-INST-receipt.md exists (DONE or WAITING_FOR_OWNER_ACTIVATION both allow this unit).

Measured: m-23568bbcd2f9 and m-906ce1fae68c burned 5-6M each while under holds; WU-1 spent 1.2M with one committed step.
Hold-on-DEAD settlement is already live (gsd_mission.py ~520-534); do not rebuild it.

Budget: 20 calls per epoch, max 2 epochs (0.7M). CHECKPOINT FIRST: commit a stub receipt. Logs under _logs/wutrip/.

Steps:
1. Progress signal = the existing progress fingerprint (commits + dirty diff hash). In supervise, for a RUNNING
   mission: if processed spend grew by >= max(25% of its token_estimate, 150,000) since the fingerprint last moved,
   trip once per epoch: ask for a checkpoint (the capsule-v2 handoff path), write the failure record (WU-1H's
   fault-capsule format, cause "spend_without_progress"), and reforecast (spend so far + calls left x measured
   per-call cost) into the mission record. Singleflight key (mission_id, epoch, "trip").
2. Hold on a LIVE worker: after the checkpoint lands or 2 sweep passes elapse, stop the worker process tree through
   the existing reaper used for orphans (never a bare Stop-Process on a pid you did not prove is the worker: match
   pid AND proc start time from the mission owner record). Settle its lease. The mission stays held.
3. Kill switch CPP_SWEEP_TRIPWIRE=off.
4. Tests (red first, hermetic): V-LIFE-TRIP-FLAT (spend grows, fingerprint flat -> one trip, record + reforecast),
   V-LIFE-TRIP-MOVING (fingerprint moves -> no trip; the control), V-LIFE-HOLD-LIVE-STOPS (fake live worker under hold
   -> stopped after checkpoint, lease settled), V-LIFE-HOLD-PID-REUSE (same pid, different start time -> not stopped).
   Mutants: drop the fingerprint check -> TRIP-MOVING red; drop the start-time match -> PID-REUSE red.
5. Run the four suites. Commit by pathspec, verify git log -1. Receipt WU-TRIP-receipt.md with hashes for the installer
   (L6 is in the approved install set; installing it is a re-run of WU-INST steps 2-6 for these files only).
6. Arm WU-FLOOR unless already held by a mission, if remaining - open >= 1,300,000 (atomic arm, lc-WU-FLOOR,
   --token-estimate 1000000). Never hand the arm to a pane.

Do not touch m-d84de9dd1edb or anything in ce-a3b-r (Owner action).

End your final message with: HANDOFF NOTE: WU-TRIP done
