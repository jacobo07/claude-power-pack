# C2b-fix -- types prelude on every arm-A unit + the cohort capsule becomes CURRENT, drills, ONE local re-prepare (NO send)

Mission: the mission id on your rehydration card (write it in the receipt). Goal `cp50-c2`, bound to
C:\Users\User\Apps\recon_work\wt_cp50_c2 only. Authority: Owner "y" 2026-10-11 to the coordinator's C2b-fix proposal,
after C2b came back PARTIAL (gen3/C2b-receipt.md). Supersedes m-b6b2ff893ae5. NOTHING is sent to the VPS or GEX44 (no
`stage.py send`, no ssh, no scp), never read G0_HOLDOUT.json, never arm a mission, never push, never touch stage.py
(its RF_CURRENT_PHASE = 7 edit is already in the tree and stays as is).
Envelope (route-C2b-fix.json): when the SESSION BUDGET warn advisory appears, go STRAIGHT to the receipt.
Hard limit 9 tool calls. 0 subagents. NO search tools (Glob/Grep). Read only the files named in the plan.

## State you inherit (verified by the coordinator, do not re-verify)
- Job ksrmb-20261010-203003 (Phase 7 job 1 of 4) returned custody-clean, but all 50 units COMPILE_FAILED, for two causes:
  1. **No base types.** `arm_a.compose` (arm_a.py:126) sends the plain arm as raw m2c text and the valid-syntax arm as
     `m2c_macros.h` + text. Neither carries s8..u64/f32/f64: mwcceppc stops at `typedef s32 M2C_UNK;` (macros line 13)
     and at line 1 of plain units (`s32 fn_8033A624(); /* extern */`), error 10140 `undefined identifier 's32'`.
  2. **No CURRENT_CAPSULE.json** at `C:\Users\User\Apps\recon_work\recon_factory\gex44`. `candidate.py judge` therefore
     marks every row STALE_INPUT "no CURRENT_CAPSULE to compare capsule cap1-ba8a3cfe2822 against". `_default_capsule`
     (arm_a.py:179-184) calls `capsule_build.build(...)` without `set_current=True`, and in capsule_build.py the EXISTS
     branch (578-585) returns before the `if set_current:` pointer write (631-637), so the cohort capsule, which already
     exists, can never become current even with the flag.
- Plain-arm units that still fail after the prelude (m2c's unresolved `?` types such as `? var_r4;`) are a MEASURED
  RESULT of the plain arm, not a defect. Do not edit m2c text.

## The fix (three edits, nothing else)
A. arm_a.py: replace the whole `compose` function with:

```python
# Dolphin SDK base types (dolphin/types.h); m2c output and m2c_macros.h both use them and define none.
M2C_TYPES = ("typedef signed char s8;\ntypedef signed short s16;\ntypedef signed long s32;\ntypedef signed long long s64;\n"
             "typedef unsigned char u8;\ntypedef unsigned short u16;\ntypedef unsigned long u32;\n"
             "typedef unsigned long long u64;\ntypedef float f32;\ntypedef double f64;\n")


def compose(valid_syntax, text, header):
    return M2C_TYPES + ((header + "\n") if valid_syntax else "") + text
```

B. arm_a.py `_default_capsule`: add `set_current=True` to the `capsule_build.build(...)` call.
C. capsule_build.py EXISTS branch: before `log("CAPSULE=EXISTS %s" % cap_id)`, when `set_current` is true write the same
   pointer the BUILT path writes (`{"capsule_id", "manifest_sha256", "path": final, "created_at": existing["created_at"]}`,
   canonical_json, `.tmp` then os.replace, into `os.path.dirname(os.path.abspath(out_root))`), and put `"current": p` in
   the returned dict. Without `set_current` the branch must stay byte-for-byte what it is.
D. test_arm_a.py: add two gates in the file's existing style:
   `V-ARMA-TYPES-PRELUDE`: `compose(False, "s32 f(void);", "HDR")` and `compose(True, ...)` both start with
   `arm_a.M2C_TYPES`; only the True one contains "HDR", placed after the types.
   `V-ARMA-SETS-CURRENT`: with fake `capsule_build` / `stage` modules injected in sys.modules (build records its kwargs and
   returns {"capsule_id": "cap1-fake"}; resolve_capsule returns {"capsule_id": "cap1-fake", "manifest_sha256": "x"}),
   `_default_capsule(["a"])` passes `set_current=True`. Restore sys.modules afterwards.

## Call plan (9; no spare)
1. Read arm_a.py offset 124 limit 62. 2. Edit A. 3. Edit B.
4. Read capsule_build.py offset 576 limit 12. 5. Edit C.
6. Read test_arm_a.py, offset 1 limit 70, enough to see its gate() helper and main pattern. 7. Edit D (append the two
   gates where the existing gates are called).
8. ONE PowerShell call, never Set-Location, `$env:PYTHONIOENCODING='utf-8'`,
   `$env:MATCH_ACCEL_GEX44='C:\Users\User\Apps\recon_work\recon_factory\gex44'`, python
   `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`, absolute paths, all output to
   `$env:TEMP\c2bfix_run.txt`, print only lines matching
   `ARM_A_DRILL|BENCH_DRILL|CAPSULE|^FAIL|ARM_A_PREPARED|REFUSED|Refused|Error|CURRENT_OK|CURRENT_BAD|UNITS_TYPED`:
   a. `tools\wros\binary\decomp\test_arm_a.py` (must be all PASS, 10/10), b. `tools\wros\binary\decomp\test_bench.py`
   (8/8), c. `tools\wros\binary\decomp\gex44\test_capsule.py` (must stay all PASS), d. ONLY if a-c pass:
   `tools\wros\binary\decomp\arm_a.py prepare --draw C:\Users\User\Apps\recon_work\wt_keosdtk_home\.planning\workstreams\recon-factory\phases\07-g0-freeze\G0_FREEZE.json --first 1 --last 5 --out C:\Users\User\Apps\recon_work\recon_factory\cp50\c2bfix_prep_1_5`,
   e. a python -c check that prints `CURRENT_OK capsule=<id>` when
   `recon_factory\gex44\CURRENT_CAPSULE.json` names the prep's `capsule_id` with its `manifest_sha256` (else
   `CURRENT_BAD <why>`), and `UNITS_TYPED=<k>/<n>` = units in `c2bfix_prep_1_5\arm_a_units.jsonl` whose `source_text`
   starts with `typedef signed char s8;`. A refusal is a RESULT: record it verbatim, never work around it.
9. ONE PowerShell call: write the receipt
   `C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cognitive-economy\gen3\C2b-fix-receipt.md`
   (UTF-8 no BOM), then `git -C <wt_cp50_c2> add -- tools/wros/binary/decomp/arm_a.py tools/wros/binary/decomp/test_arm_a.py tools/wros/binary/decomp/gex44/capsule_build.py`,
   `git -C <wt_cp50_c2> diff --cached --binary --output=C:\Users\User\.claude\skills\claude-power-pack\vault\backlog\2026-10-11_cp50-c2b-fix.patch`,
   then commit in the PP repo by pathspec (receipt + patch only; message from a temp file written with
   `[System.IO.File]::WriteAllText($p,$s,(New-Object System.Text.UTF8Encoding($false)))`; `git -C <PP> add -- <2 paths>;
   git -C <PP> commit -F <msgfile> -- <2 paths>`; print `git -C <PP> log -1 --format='%h %s'`). git =
   `C:\Program Files\Git\cmd\git.exe`. **Do NOT commit in wt_cp50_c2** (its `.ksr_vault` gate refuses every commit);
   never `--no-verify`.
Then the final message: the receipt's HANDOFF line only.

## Receipt (<= 15 lines)
Mission id, calls used, drill lines verbatim, ARM_A_PREPARED line (or the refusal verbatim), capsule id + manifest
sha256, CURRENT_OK/CURRENT_BAD line, UNITS_TYPED line, job dir, functions with no unit, PP commit hash, open points.
Ending on a question counts as a failure. End with `HANDOFF NOTE: C2b-fix done -- C2b-retry may send <job dir>` or
`HANDOFF NOTE: C2b-fix PARTIAL -- <blocker>`.
