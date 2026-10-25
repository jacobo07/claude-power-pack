# WU-H3 -- factory-2 providerless continuation: `campaign next` (GEX44 t1 campaign)

You are a fresh worker. Read no prior transcript. Everything you need is here and in
`vault/plans/gsdx-factory-2-gen2-econ-plan-20261025.md` sections 1, 8 (row G3), 9, 10 (C-D) and 12.
Owner approval 2026-10-25: "y, y con solo bloques secretos" = plan approved, 26.5M hard under goal `gsdx-factory-2`.
H0/H1/H2 are landed (feature/knowledge-acquisition da357b8a, ea8e8d44). This unit is H3 only.

Mode EXECUTION. Budget: P50 2.0M, warn 2.75M, hard 2.9M processed (the pre-boundary guard enforces it).
At 2.75M finish the commit in hand and write the receipt. Keep tool output small: never cat a whole jsonl, print counts.

## Where the work happens
- Code and evidence: GEX44 clone `/home/kobii/missions/t1-campaign`, branch `t1/campaign` (HEAD 0c353ecb when this packet was written;
  repo-local git identity `kobii-gex44-mission` is set). You run on the laptop and reach it by ssh only:
  `& "$env:SystemRoot\System32\OpenSSH\ssh.exe" -o BatchMode=yes gex44 "cd ~/missions/t1-campaign && <cmd>"` (python there is `python3`).
  To write a file there: write it locally in your scratchpad with the Write tool (LF), then
  `& "$env:SystemRoot\System32\OpenSSH\scp.exe" <local> gex44:missions/t1-campaign/<path>`. Never pipe a PowerShell here-string into ssh (BOM).
  For a multi-line remote script, scp it and run `bash /path/x.sh </dev/null`.
- Receipt: laptop PP repo `C:\Users\User\.claude\skills\claude-power-pack`, branch feature/knowledge-acquisition, shared with other panes:
  pathspec commits only (`git commit -F <msgfile> -- <paths>`), verify `git log -1 --format=%s`, never `git add -A`, never rebase/reset.
  git: `& 'C:\Program Files\Git\cmd\git.exe'`. Python: `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`.
- Forbidden: pushing anything (laptop or GEX44), settings.json edits, capital requests, arming or launching any mission or worker,
  any change outside `~/missions/t1-campaign` on GEX44 (no live install, no other clone, no Tennis/TB/ccr state), editing this packet.

## Facts (verified by the planner on GEX44, read-only)
- Owner module: `modules/recon_fabric/campaign.py` (241 lines; `build_pin`, `check`, `run`, `cohort`, `members`, `verdict`, `main(argv)`).
  Its test: `tools/test_recon_fabric_fr1.py` (86 lines). Operators: `modules/recon_fabric/search_ops.py`.
- Views: `evidence/fingerprint/views.jsonl`, 557 rows `{"band","flags","fn","key","label","n_*","views":"fp-views1"}`.
  Bands: lt50 / 50to90 / 90to95 / 95to100. Labels (pre-A7): COUNT_DIFFERS 435, OPCODE_DIFFERS 68, REG_MAP_CONFLICT 31, REG_MAP_CONSISTENT 10,
  IMMEDIATE_ONLY 5, ARG_MIXED 5, ORDER_ONLY 2, RELOC_OR_BRANCH_ONLY 1.
- Certified: `evidence/frontier/frontier.jsonl` + `counters.json` (certified_by cert1 490, ledger 12, search 17 = 519/1797).
- Pins/runs: `evidence/campaign/tam-ds-{1..7}.json` + dirs (`results.jsonl`, `solved.jsonl`, `verdict.json`); tam-ds-4 left 12 REG_MAP_CONFLICT exhausted.
- Negatives: `evidence/campaign/interrupts/*.json` (one: RELOC_OR_BRANCH_ONLY fn_8025CDE8, no source operator).
- Landed operators (plan s9 U1): arg-passthru, ptr-bytestride@1, sum-reorder@1, decl/stmt-swap. Read the real ids from search_ops.py.

## Do
1. RED first: `tools/test_recon_fabric_next.py` (V-NEXT-*, prints `NEXT_PASS=n/m`), on small fixtures under `modules/recon_fabric/fixtures/`
   or a temp dir (never the real evidence tree as test input):
   - deterministic: same inputs -> byte-identical packet (and its sha256);
   - certified functions, recorded negatives and exhausted members never appear in a cohort; control: an uncertified, unexhausted one does;
   - while a landed operator has not yet been applied (no pin covering it at depth <= 3) to every uncertified searchable function, the next unit
     is the WIDEN census (plan U1); control: once a pin covers them, the next unit is a CLASS_INTERRUPT label class;
   - CLASS_INTERRUPT order: most functions in band 95to100 first, ties by label name; a label with a recorded negative is skipped;
   - nothing left -> an explicit `NO_WORK` packet, never an empty cohort.
2. Build `campaign next` in campaign.py (reuse `cohort`/`members`/`_jsonl`/`_sha`/`_write_atomic`; no new module unless it stays small):
   output `evidence/campaign/next/<seq>-<label|census>.json` = {class (WIDEN|CLASS_INTERRUPT|NO_WORK), label, band, cohort (fn, key),
   operator set, budget forecast (plan s12: WIDEN 1.5M hard, CLASS_INTERRUPT 6.0M hard), inputs with sha256 (views, frontier, pins, interrupts),
   rationale (one line per rule that fired)} and a short `.md` rendering a worker could be handed. No model, no network.
3. GREEN; the existing `tools/test_recon_fabric_fr1.py` still passes. One red drill: break the certified-exclusion rule, the suite must fail;
   restore it and show the restore (sha256 of campaign.py before/after equal).
4. Canary C-D: run `campaign next` on the REAL evidence tree once and record its packet (class, label, cohort size, sha). Expected first answer
   is the WIDEN census; if it is not, say which rule decided and why, do not force it.
5. Commit on GEX44 (`t1/campaign`), one or two commits, subject `feat(recon_fabric): campaign next ...` / `evidence(campaign): ...`.

## Receipt
`vault/programs/gsdx-factory-2/WU-H3-receipt.md` (laptop), first line `Status: DONE` (or `DONE_WITH_LIMITS` / `PARTIAL` with the exact next step):
GEX44 commits (hash + subject, unpushed), suite counts pasted, red-drill evidence, the C-D packet summary, UNKNOWNs.
Commit it pathspec-scoped. Then stop; do not start U1.
