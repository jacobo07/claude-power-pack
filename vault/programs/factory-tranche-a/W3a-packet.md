# Unit W3a — live mission spend on the worker card

Repo: C:\Users\User\.claude\skills\claude-power-pack (a git worktree on its own branch; the path is rewritten below).
Use PowerShell; git is `& 'C:\Program Files\Git\cmd\git.exe'` (not on PATH). Python is
`C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`.

## Goal
A mission worker today cannot see how much of the Owner's authority it has already spent. `tools/gsd_mission.py`
already owns the measurement: `live_spend(rec, measure=None)` (around line 2509) returns
`{processed, measured_at, authority, room_after_reserve}` or `{processed: None, measured_at, error}`.
It is only called from the Owner status view (~line 6947). Wire it onto the worker card. Add no new owner and no new measurement.

## Change (in tools/gsd_mission.py only, plus one new test file)
1. In `render_card(rec, git_facts=None, gsd_facts="")` (around line 3584), add ONE block right after the
   `Dirty paths at hand-off:` line, before the work-tree and GSD lines, so the byte cap never cuts it:
   - when `rec.get("authority_tokens")` is set: `LIVE SPEND (measured <measured_at>): <processed:,> processed of
     authority <authority:,>; room after closeout reserve <room:,>. Stop and hand off before the room reaches 0.`
   - when `processed` is None: `LIVE SPEND: UNMEASURED (<error>) -- treat the room as unknown, never as available.`
   - when the mission has no `authority_tokens`: emit nothing (mission without an Owner ceiling).
   Let `render_card` take an optional `spend_fn=None` keyword. Pass it to `live_spend` as `measure`, so tests
   never read transcripts. Keep the existing signature compatible: every current caller passes positional or
   keyword `git_facts` / `gsd_facts` only.
2. A `live_spend` exception path already returns a dict. Do not wrap it again.

## Test (new file tools/test_w3_live_spend_card.py, V-* gate style like tools/test_wake_progress.py)
Print `W3A_PASS=n/n` and exit 0 only if all of these pass:
- V-W3A-LINE: a rec with authority_tokens=1_000_000 and a spend_fn returning 400_000 puts a `LIVE SPEND` line with
  `400,000` and `authority 1,000,000` on the card.
- V-W3A-UNMEASURED: a spend_fn that raises gives `LIVE SPEND: UNMEASURED`, never a 0.
- V-W3A-NO-AUTHORITY: no authority_tokens, so there is no `LIVE SPEND` line.
- V-W3A-ORDER: the LIVE SPEND line comes before `Predecessor's note`.
- V-W3A-MUTATION-RED: a mutated card that drops the line fails your line check. Prove the check can go red.
Build the minimal rec from fields render_card reads (mission_id, epoch, cwd, resume_command, ...). Read
render_card first. If `_autonomy_rubric`, `mb` or `mres` need state, monkeypatch them at the module boundary.

## Done
- `python tools/test_w3_live_spend_card.py` exit 0 and `python tools/test_gsd_mission.py` exit 0 (it was 233/233 at
  base, so keep it green).
- One commit on this branch, `git commit -m "<msg>" -- tools/gsd_mission.py tools/test_w3_live_spend_card.py`.
  Pathspec only, no `git add -A`.
- Receipt `vault/programs/factory-tranche-a/W3a-receipt.md`: what changed (file:line), test counts, and the line
  `COMMITS: <hash>`. Commit the receipt in a second commit or the same one, but the hash on the COMMITS line must
  be reachable from HEAD.
