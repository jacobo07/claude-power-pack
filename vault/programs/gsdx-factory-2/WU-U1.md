# WU-U1 -- factory-2 OPEX U1: WIDEN census of the 33-function cohort (GEX44 t1 campaign)

You are a fresh worker. Read no prior transcript. Everything you need is here, in
`vault/programs/gsdx-factory-2/WU-H3-receipt.md` and in `vault/plans/gsdx-factory-2-gen2-econ-plan-20261025.md`
sections 9 (row U1) and 12 (incl. the 2026-10-25 amendment: hard raised to 36M by the Owner).
H3 is landed: GEX44 `t1/campaign` 7f28f5b8 (`campaign next`) + b2648c34 (first packet). This unit is U1 only.

Mode EXECUTION. Budget: warn 2.2M, hard 2.4M processed (the pre-boundary guard enforces it). At 2.2M finish the
commit in hand and write the receipt. The census itself is CPU on GEX44: never wait for it in a loop of tool calls.

## Where the work happens
- GEX44 clone `/home/kobii/missions/t1-campaign`, branch `t1/campaign` (HEAD b2648c34; repo-local identity is set).
  Reach it by ssh only: `& "$env:SystemRoot\System32\OpenSSH\ssh.exe" -o BatchMode=yes gex44 "cd ~/missions/t1-campaign && <cmd> </dev/null"`
  (python there is `python3`). Multi-line remote work: write the script locally with the Write tool (LF) in your scratchpad,
  `scp` it to `gex44:/tmp/u1_<n>.sh`, run `bash /tmp/u1_<n>.sh </dev/null`. Never pipe a PowerShell here-string into ssh (BOM).
- Receipt: laptop PP repo `C:\Users\User\.claude\skills\claude-power-pack`, branch feature/knowledge-acquisition, shared:
  pathspec commits only (`git commit -F <msgfile> -- <paths>`), verify `git log -1 --format=%s`; git is
  `& 'C:\Program Files\Git\cmd\git.exe'`; Python `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`.
- Forbidden: pushing (laptop or GEX44), settings.json edits, capital requests, arming/launching any mission or worker,
  changes outside `~/missions/t1-campaign` on GEX44 (no Tennis/TB/ccr state), editing this packet.

## Facts (read by the planner on GEX44)
- Input: `evidence/campaign/next/001-census.json` (+ `.md`), class WIDEN, cohort 33 (fn + key), sha256
  fd213bc1e806d6f09a458e0806b4da00f866f5453fa1207daad629f08d4225e6, operators arg-passthru@1, decl-swap@1,
  ptr-bytestride@1, stmt-swap@1, sum-reorder@1, depth >= 3.
- `modules/recon_fabric/campaign.py`: `main(argv)` handles `next`, `pin [--pin ID] [--expand LABEL,...] [--max-evals N]
  [--min-pct P] [--max-n-diff N] [--max-depth D]`, `check`, `run`. `build_pin` selects by label medoids/members, not by an
  explicit function list. Last pin: `evidence/campaign/tam-ds-7.json` (budget batch 4, max_depth 3, max_evals 400, seed 7);
  its dir holds `results.jsonl`, `solved.jsonl` (the input of `certify run --solved`), `verdict.json`, `search/`.
- Evidence commit pattern: 875c8c34 `evidence(campaign): A7 ARG_MIXED widening -- tam-ds-7 certifies 3 more by search (519/1797)`.
  Read `git show --stat 875c8c34` once to see which frontier/counter files a certification touches.

## Do
1. Pin the census as `tam-ds-8` FROM the packet: if `pin` cannot take the cohort, add the smallest option
   (e.g. `--from-next evidence/campaign/next/001-census.json`) that pins exactly the packet's cohort and operator set, with a
   test in `tools/test_recon_fabric_next.py` or `tools/test_recon_fabric_fr1.py` (same cohort -> same pin bytes; a certified fn in
   the packet is refused). Both suites stay green. `campaign check --pin tam-ds-8` must pass.
2. Run it detached: `nohup python3 -m modules.recon_fabric.campaign run --pin tam-ds-8 > /tmp/u1_run.log 2>&1 & disown`.
   Then poll at most once per tool call with a bounded remote wait (`timeout 240 bash -c 'until [ -f .../verdict.json ]; do sleep 20; done'`),
   printing only counts (lines of results.jsonl, solved.jsonl). If it is not done after 6 polls, write the receipt PARTIAL with the
   exact resume command and stop.
3. Certify the solved ones the way 875c8c34 did (`certify run --solved evidence/campaign/tam-ds-8/solved.jsonl`; find the real
   module with `grep -rn "def main" modules/recon_fabric | grep -i certif`). Record certified before -> after (`counters.json`).
4. Commit on GEX44: code/test (if any) as `feat(recon_fabric): ...`, evidence as
   `evidence(campaign): U1 WIDEN census -- tam-ds-8 certifies N by search (X/1797)`. Zero solved is a valid result: commit the
   verdict anyway and say so.
5. Run `python3 -m modules.recon_fabric.campaign next` once more and record the new packet's class/label/cohort (expected:
   CLASS_INTERRUPT, the U2 input). Commit that packet too.

## Receipt
`vault/programs/gsdx-factory-2/WU-U1-receipt.md` (laptop), first line `Status: DONE` (or `PARTIAL` with the exact next step):
GEX44 commits (hash + subject, unpushed), suite counts, run counts (subjects, solved, exhausted), certified before -> after,
the follow-up `next` packet summary, UNKNOWNs. Commit it pathspec-scoped. Then stop; do not start U2.
