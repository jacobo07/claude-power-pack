# Unit W3c — MARGINAL_GAIN_LOW on top of NO_PROGRESS

Repo: C:\Users\User\.claude\skills\claude-power-pack (a git worktree on its own branch; the path is rewritten below).
Use PowerShell; git is `& 'C:\Program Files\Git\cmd\git.exe'` (not on PATH). Python is
`C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`.

## Goal
The supervisor in `tools/gsd_mission.py` halts a mission whose work tree did not move across
`NO_PROGRESS_EPOCHS` relays (around line 5578, using `next_progress` and `mission_fingerprint` near line 6190).
It misses the expensive case: the tree DOES move (notes, STATE.md rewrites), spend keeps rising, and nothing new
lands. KSEIP Tranche 1 burned 123.5M processed tokens like that. Add a MARGINAL_GAIN_LOW verdict that HOLDS the
relay, and add no new owner. The verdict is a pure function. Place the hold next to the existing NO_PROGRESS
branch and reuse the existing hold shape, `relay_held` ledger row + `row["held"]` + `continue`, as at ~5558-5562.

## Change (tools/gsd_mission.py only, plus one new test file)
1. Pure `judge_marginal_gain(samples: list[dict], window: int = 2) -> str`, where each sample is
   `{"head": str|None, "spent": int|None, "note_sha": str|None}`, oldest first, one per relay. It returns:
   - "UNKNOWN" if fewer than window+1 samples, or if any of the last window+1 has head or spent None.
     Unmeasured never holds.
   - "MARGINAL_GAIN_LOW" if, across the last window+1 samples, spent strictly rises each step AND head never
     changes (no new commit) AND note_sha is identical, meaning the same hypothesis was restated.
   - else "GAINING".
2. Keep a bounded sample list on the record. When the relay path computes `progress` (right after
   `next_progress(...)`), append `{"head", "spent", "note_sha"}` to `rec["gain_samples"]`, keeping the last 5.
   Persist it the same way the record's `progress` field is persisted on that path. Read how `progress` reaches
   the record before choosing. Take head from the work tree with the module's existing git helper (find the one
   render_card's caller uses for `git_facts`), spent from `mission_spend.processed_tokens(rec)`, catching an
   exception as None, and note_sha as the sha256 of `(rec.get("note") or "").strip()`.
3. Only when `act in ("relay", "replace")` and the verdict is MARGINAL_GAIN_LOW: write the ledger row
   `relay_held` with `reason="marginal_gain_low: spend rose over N relays with no new commit and the same note"`
   and the samples, set `row["held"]`, then `continue`. Hold, never halt: the Owner decides. A kill switch:
   env `GSD_MARGINAL_GAIN=off` disables the hold, so the verdict is still computed and recorded.
   It must not change what NO_PROGRESS does.

## Test (new file tools/test_w3_marginal_gain.py, V-* gate style like tools/test_wake_progress.py)
Print `W3C_PASS=n/n`, exit 0 only if all pass:
- V-W3C-LOW: 3 samples with the same head and the same note_sha, and spend 1M -> 2M -> 3M, give MARGINAL_GAIN_LOW.
- V-W3C-NEW-COMMIT: the same but the head changes in the last sample, which gives GAINING.
- V-W3C-NEW-NOTE: the same but note_sha changes, which gives GAINING.
- V-W3C-FLAT-SPEND: spend that does not rise gives GAINING. That case is NO_PROGRESS's territory, not this one.
- V-W3C-UNMEASURED: a None spent in the window gives UNKNOWN, and fewer than 3 samples gives UNKNOWN.
- V-W3C-MUTATION-RED: a mutant that ignores head (monkeypatched) makes V-W3C-NEW-COMMIT fail. Prove it can go red.
- If the supervisor wiring is testable with the seams tools/test_gsd_mission.py already uses for stalled missions
  (see its NO_PROGRESS_EPOCHS cases near line 883), add V-W3C-WIRED: a seeded mission with
  MARGINAL_GAIN_LOW samples is held (`relay_held`), not relayed, and is relayed with GSD_MARGINAL_GAIN=off. If
  those seams cannot reach it within your cap, say so in the receipt as an open item. Do not fake it.

## Done
- `python tools/test_w3_marginal_gain.py` exit 0, `python tools/test_gsd_mission.py` exit 0,
  `python tools/test_wake_progress.py` exit 0.
- Commit with a pathspec: `git commit -m "<msg>" -- tools/gsd_mission.py tools/test_w3_marginal_gain.py`.
- Receipt `vault/programs/factory-tranche-a/W3c-receipt.md`: what changed (file:line), the test counts, any open
  item, and the line `COMMITS: <hash>`, where the hash is reachable from HEAD.
