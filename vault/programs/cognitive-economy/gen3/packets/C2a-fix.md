# C2a-fix -- capsule id must cover targets_for, then the drills, then ONE local `prepare` (build only, NO send)

Mission: the mission id on your rehydration card (write it in the receipt). Goal `cp50-c2`, bound to
C:\Users\User\Apps\recon_work\wt_cp50_c2 only. Authority: Owner "go ahead, y despues decide el presupuesto y rearma la
misión" 2026-10-10, after the C2a variance was explained (gen3/C2a-receipt.md § Variance). Supersedes C2a
m-e6ea9c26d377. NOTHING is sent to the VPS or GEX44 (no `stage.py send`, no ssh, no scp), no model or paid call is made
by your code, never read G0_HOLDOUT.json, never arm a mission, never push, never edit stage.py's RF_CURRENT_PHASE.
Envelope (route-C2a-fix.json): see the route; when the SESSION BUDGET warn advisory appears, go STRAIGHT to the receipt.
Hard limit 6 tool calls. 0 subagents. NO search tools (Glob/Grep). Read no file except the one in call 1.

## State you inherit (verified by the coordinator, do not re-verify)
- wt_cp50_c2, branch cp50-c2 at 3c86ae2. STAGED (not committed): `tools/wros/binary/decomp/arm_a.py` (A),
  `tools/wros/binary/decomp/test_arm_a.py` (A), `tools/wros/binary/decomp/gex44/capsule_build.py` (M, the `targets_for`
  keyword). Last run: ARM_A_DRILL=7/8 (FAIL V-ARMA-CAPSULE-IDENTITY: `targets_for=[id] produced no new capsule:
  ['cap1-984a35109f79']`), BENCH_DRILL=8/8.
- Root cause (read by the coordinator in capsule_build.py): `_stage_and_seal` derives the id at line 574,
  `cap_id = "cap1-" + custody.files_tree_hash(files)[:12]`, from `files = custody.scan_tree(tmp)` (line 573). `targets`
  reach only `meta["targets"]` (line 612), AFTER the id. When every target object is already in the tree (shared with a
  unit's object), the tree is unchanged, so the id is unchanged and the EXISTS branch (576-583) returns the old capsule.

## The fix (the ONLY code edit)
In `_stage_and_seal`, immediately BEFORE the line `    files = custody.scan_tree(tmp)`, insert:

```python
    if targets is not None:
        _write(os.path.join(tmp, "units", "TARGETS.jsonl"), b"".join(compact(t) for t in targets))
```

With `targets is None` nothing is written, so a build without the keyword stays byte-for-byte what it is today (the
None half of V-ARMA-CAPSULE-IDENTITY proves it). Edit nothing else: not arm_a.py, not test_arm_a.py, not bench.py.

## Call plan (6; there is no spare)
1. Read `C:\Users\User\Apps\recon_work\wt_cp50_c2\tools\wros\binary\decomp\gex44\capsule_build.py` offset 568 limit 10.
2. Edit: the insertion above (old_string = the `files = custody.scan_tree(tmp)` line plus the `cap_id = ...` line).
3. ONE PowerShell call, never Set-Location, `$env:PYTHONIOENCODING='utf-8'`, python =
   `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`, absolute script paths:
   a. `tools\wros\binary\decomp\test_arm_a.py` (must print ARM_A_DRILL=8/8), b. `tools\wros\binary\decomp\test_bench.py`
   (must stay BENCH_DRILL=8/8), c. ONLY if both are all PASS:
   `tools\wros\binary\decomp\arm_a.py prepare --draw C:\Users\User\Apps\recon_work\wt_keosdtk_home\.planning\workstreams\recon-factory\phases\07-g0-freeze\G0_FREEZE.json --first 1 --last 5 --out C:\Users\User\Apps\recon_work\recon_factory\cp50\c2a_prep_1_5`.
   Redirect all output to `$env:TEMP\c2afix_run.txt` and print only the lines matching
   `ARM_A_DRILL|BENCH_DRILL|^FAIL|ARM_A_PREPARED|CAPSULE=|REFUSED|Error`. A refusal of prepare (venv, capsule, stage.build)
   is a RESULT: record it verbatim, never work around it.
4. Write the receipt `C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cognitive-economy\gen3\C2a-fix-receipt.md`.
5. ONE PowerShell call (git = `C:\Program Files\Git\cmd\git.exe`, always `git -C <repo>`):
   a. `git -C <wt_cp50_c2> add -- tools/wros/binary/decomp/gex44/capsule_build.py`
   b. `git -C <wt_cp50_c2> diff --cached --binary --output=C:\Users\User\.claude\skills\claude-power-pack\vault\backlog\2026-10-10_cp50-c2a-fix.patch`
   c. commit in the PP repo by pathspec: the receipt + that patch, message from a temp file written with
      `[System.IO.File]::WriteAllText($p, $s, (New-Object System.Text.UTF8Encoding($false)))`;
      `git -C <PP> add -- <2 paths>; git -C <PP> commit -F <msgfile> -- <2 paths>`; print `git -C <PP> log -1 --format='%h %s'`.
   **Do NOT commit in wt_cp50_c2**: its `.ksr_vault` snapshot gate refuses every commit there (C1 and C2a both hit it;
   C2a burned 2 calls retrying). Never `--no-verify`. The staged index + the patch are the durable form.
6. Final message: the receipt's HANDOFF line only.

## Receipt (<= 15 lines)
Mission id, calls used, drill lines verbatim (ARM_A_DRILL, BENCH_DRILL), the ARM_A_PREPARED line (or the refusal
verbatim), capsule id + manifest sha256, units n, job dir, functions with no unit and why, the PP commit hash, open
points. Spend is metered by the control plane. Ending on a question counts as a failure. End with
`HANDOFF NOTE: C2a done -- C2b may send <job dir>` or `HANDOFF NOTE: C2a-fix PARTIAL -- <blocker>`.
