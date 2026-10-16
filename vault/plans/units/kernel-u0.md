# Work Unit kernel-u0 — recalibrate slim-t2 route pricing, then arm kernel-u1b

Goal `ccr`, lease L17. You have about 20 calls: no exploration. Every path you need is here.
Python `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe` (`$env:PYTHONIOENCODING='utf-8'`),
git `& 'C:\Program Files\Git\cmd\git.exe' -C <repo>`. PowerShell, not Bash. Never ask the Owner.
PP main = `C:\Users\User\.claude\skills\claude-power-pack`. Worktree = `...\.claude\worktrees\ccr-v5` (branch ccr/v5).

## Facts (measured 2026-10-15/16)
- `vault/config/route-floors.json` profile slim-t2 = floor 13507, growth 1725 (n=4), physical_ratio 2.4 (n=4).
  `tools/route_admission.py:144-151` prices calls_phys = ceil(calls x ratio); cost = calls_phys x (floor+packet) +
  growth x calls_phys x (calls_phys-1)/2. For 45 calls with packet 6500 it charged 12,127,806.
- Measured slim-t2 session a7e006a1-d5dc-4458-bdae-da5115e40f86 (mission m-589fabb143de): 18 turns, 306,884 processed
  (ledger cost_mark), result file `~/.claude/state/slim-jobs/m-589fabb143de/a7e006a1-*.out.json`. It was stopped by
  the session guard's call cap (route calls 20), not by tokens. That makes it CENSORED for physical_ratio.
- The transcript lives under `~/.claude/projects/C--Users-User--claude-skills-claude-power-pack--claude-worktrees-ccr-v5/a7e006a1*.jsonl`.

## Tasks
1. Measure a7e006a1's per-call context curve (first call, per-call mean increase) with a 20-line python script
   (dedupe assistant rows by message.id; ctx = input + cache_creation + cache_read).
2. Update slim-t2 in PP main `vault/config/route-floors.json`: growth = n-weighted mean of the old 1725 (n=4) and this
   sample's measured growth (n becomes 5). Leave physical_ratio unchanged (censored sample), and say so in a `"notes"`
   entry with the date and session id. Change nothing else.
3. Run `python tools/test_route_admission.py` (if it exists; otherwise
   `python tools/route_admission.py admit --route <worktree>\vault\plans\units\kernel-u1.route.json`) in PP main.
   It must pass. Commit ONLY that file, path-scoped:
   `git -C <PP main> commit -F <msg in $env:TEMP> -- vault/config/route-floors.json`. Check the file is not dirty
   from another writer first (`git status --short -- vault/config/route-floors.json` must be empty before your edit).
4. Write `vault/plans/units/kernel-u1b.route.json` in the worktree. Copy kernel-u1.route.json and pick the LARGEST
   `calls` that `route_admission admit` accepts with target 6,000,000 (stop 8,000,000), up to 70.
5. Arm the continuation:
   `python <PP main>\tools\gsd_mission.py arm-chain --cwd <worktree> --command "Execute tasks 1, 2, 3 and 7 of
   vault/plans/units/kernel-u1.md. Read vault/programs/ccr/evidence-kernel-u1.md FIRST: it already locates every
   function; do not re-explore." --wu-packet <worktree>\vault\plans\units\kernel-u1.md --token-estimate 6M
   --route <worktree>\vault\plans\units\kernel-u1b.route.json --max-cycles 1 --permission-mode auto --model sonnet`
6. Commit in the worktree (path-scoped): kernel-u1b.route.json and vault/programs/ccr/evidence-kernel-u1.md.
   Append to evidence-kernel-u1.md: the measured curve, the new growth, the admitted call count and the new mission id.
   Book yourself: `python <PP main>\tools\mission_spend.py goal-settle --goal ccr --session <your session id> --measured <processed>`.
If arm-chain refuses, record its exact output in the evidence file and stop. Do not retry the same shape.
