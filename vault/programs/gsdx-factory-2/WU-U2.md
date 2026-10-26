# WU-U2 -- factory-2 OPEX U2: CLASS_INTERRUPT COUNT_DIFFERS (GEX44 t1 campaign)

You are a fresh worker. Read no prior transcript. Everything you need is here, in
`vault/programs/gsdx-factory-2/WU-U1-receipt.md` and in `vault/plans/gsdx-factory-2-gen2-econ-plan-20261025.md`
sections 9 (row U2) and 12. U1 is closed. This unit is U2 only.

Mode EXECUTION. Budget: warn 5.5M, hard 6.0M processed (the pre-boundary guard enforces it). At 5.5M finish the
commit in hand and write the receipt. Search and certification are CPU on GEX44: never wait in a loop of tool calls.

## Where the work happens
- GEX44 clone `/home/kobii/missions/t1-campaign`, branch `t1/campaign` (HEAD 281b9881; repo-local identity is set).
  - Reach it by ssh only (python there is `python3`). For multi-line work, write the script locally with the Write tool
    (LF) in your scratchpad, `scp` it to `gex44:/tmp/u2_<n>.sh`, then run `bash /tmp/u2_<n>.sh </dev/null`.
  - Never pass a `python3 -c` with quotes, or a sed/regex, inline through PowerShell. U1 lost 3 calls that way.
  - Never pipe a here-string into ssh (BOM).
- **Receipt goes in the linked worktree, not the PP main checkout.** A background session cannot Write into the main
  checkout (U1 lost its receipt to that).
  - Path: `C:\Users\User\Apps\pp-gsdx-factory-2\vault\programs\gsdx-factory-2\WU-U2-receipt.md`. Create the directory if needed.
  - Commit only that file, pathspec-scoped, in that worktree:
    `& 'C:\Program Files\Git\cmd\git.exe' -C 'C:\Users\User\Apps\pp-gsdx-factory-2' commit -F <msgfile> -- vault/programs/gsdx-factory-2/WU-U2-receipt.md`
    after `git add` of the same path. Verify with `git log -1 --format=%s`.
  - The worktree has unrelated untracked files. Do not touch them.
- Forbidden:
  - pushing (laptop or GEX44), settings.json edits, capital requests;
  - arming or launching any mission or worker;
  - changes outside `~/missions/t1-campaign` on GEX44 (no Tennis/TB/ccr state);
  - editing this packet.

## Facts (read by the planner on GEX44)
- Input packet: `evidence/campaign/next/003-count_differs.json` (+ `.md`), committed in 281b9881.
  - Class CLASS_INTERRUPT, label COUNT_DIFFERS, band 95to100, cohort 45. The first entry is the lowest n_diff:
    medoid `fn_801BCA38`.
  - sha256 f8b47a855f42aa65dd31f3d7a1f78d68462fa429d9161ddf7792dd23963da62e.
  - Landed operators: arg-passthru@1, decl-swap@1, ptr-bytestride@1, stmt-swap@1, sum-reorder@1. None of them closes
    COUNT_DIFFERS (the instruction count differs from the target's).
- Operators live in `modules/recon_fabric/search_ops.py`. Precedents for landing one (read each `git show --stat` once):
  - 95939e7b `feat(recon_fabric): ptr-bytestride@1 operator (SL-v3) for MISSING_OPERATOR IMMEDIATE_ONLY`
  - 3d0b1300 `feat(recon_fabric): sum-reorder@1 operator (SL-v4) for MISSING_OPERATOR ARG_MIXED`
- Recorded-negative precedent, used when no source-level operator can close the class: adfa203b. It writes
  `evidence/campaign/interrupts/<label>-<medoid>.json` with outcome NO_SOURCE_OPERATOR. R3 of `next` then skips the label.
- Campaign tools: `python3 -m modules.recon_fabric.campaign next|pin|check|run`. `pin --from-next` takes only WIDEN
  packets. For a class operator, pin the medoid and its label with `pin --pin tam-ds-10 --expand COUNT_DIFFERS --max-depth 3`.
- Suites that must stay green: `tools/test_recon_fabric_next.py` (24), `tools/test_recon_fabric_cp1.py` (16),
  `tools/test_recon_fabric_fr1.py` (15), plus the operator suite the precedents touched.

## Do
1. **Diagnose the medoid.** Diff `fn_801BCA38`'s target asm against its current best candidate. Name the source-level
   shape that changes the instruction count (for example a redundant temp, a split or merged expression, a loop or
   unroll form, a cast).
   - No source-level shape explains the delta → write the recorded negative the adfa203b way, commit it, and go to step 5.
2. **Build the smallest operator** that produces that shape, versioned like the precedents (`<name>@1`, a new SL id).
   - Add a gate that drives its red branch: the operator applies to the shape, and is a no-op on a non-matching input.
   - Prove it on the medoid first: one search run must SOLVE `fn_801BCA38`. If it does not after two operator
     revisions, record the negative instead.
3. **Pin and run the class.** Pin `tam-ds-10` with the new operator set (label COUNT_DIFFERS, depth 3), run `check`,
   then start the run detached with nohup:
   `nohup python3 -m modules.recon_fabric.campaign run --pin tam-ds-10 > /tmp/u2_run.log 2>&1 < /dev/null & disown`.
   Then poll at most 6 times, each with
   `timeout 240 bash -c 'until [ -f .../verdict.json ]; do sleep 20; done'`, printing counts only.
4. **Certify the solved ones** the way 875c8c34 did (`certify run --solved .../solved.jsonl`).
   - Record certified before -> after from `evidence/frontier/counters.json`.
   - Commit code/test as `feat(recon_fabric): ...`.
   - Commit evidence as `evidence(campaign): U2 COUNT_DIFFERS -- tam-ds-10 certifies N by search (X/1797)`.
5. **Run `campaign next` once more** and commit its packet, recording the class, label and cohort (the U3 input).

## Receipt
Path: the worktree path above. First line `Status: DONE` (a recorded negative with its evidence is DONE too), or
`PARTIAL` with the exact next step. Include:
- GEX44 commits (hash and subject, unpushed);
- suite counts;
- the medoid diagnosis;
- run counts (subjects, solved, exhausted);
- certified before -> after;
- the follow-up `next` packet summary;
- UNKNOWNs.

Then stop. Do not start U3.
