# RESUMPTION_FILE: prr (Physical Runtime Working Set)

**Identity.** Claude Power Pack worktree `C:\Users\User\Apps\pp-prr`, branch `prr/main` (off 983cca18). Goal `prr`,
cap 38,000,000 (packet prr-l2-successor-20m-2026-10-12; lease L2 20M, expires 2026-10-14). Plan + Owner decision: `vault/plans/prr-physical-working-set-2026-10-12.md`. Coordinator pane ce64704d.
Sibling programme `ccr` is owned by pane c13cda65: read its files, never write them. GEX44 clone: `~/missions/prr`,
bench data `~/prr-bench/runs/`.

**Thesis (proven on GEX44, not yet on Windows).** claude 2.1.296 is Bun 1.4.3/JSC. A process keeps every history it
loaded: /compact and /clear cut tokens, not RAM (+12 MB/100 turns). Resume alone reloads all history. **Compaction
then process recycle (`--resume <sid>`) is bounded**: +0.27 MB/100 turns, epoch-start flat, resume 0.3 s, same sid;
resume RAM independent of a 10x larger pre-boundary history. Agents (+64 MB/100 turns, in-process) and images (peak
1.2 GB) follow the same rule. Evidence: `vault/programs/prr/evidence/{A1,B,C}-*.md`.

**State (coherence anchor: the commit that adds evidence C).** SEALED: A0 census (`modules/prr/census.py`), A1 matrix,
B/C benchmarks (`modules/prr/bench/`), O recycle policy (`modules/prr/recycle_policy.py`, observe default, act via
`CPP_PRR_RECYCLE=act` -> existing `~/.claude/scripts/restart-claude.ps1`). Canary-ring hook registration exists only
in this worktree: `.claude/settings.local.json` (untracked; SessionStart + Stop).
SEALED 2026-10-12 (fresh pane): D policy canary on GEX44: the real hook drives recycle after /compact and /clear, no
loop, same sid (`evidence/D-policy-canary-gex44.md`, `longrun.py --mode policy`; the hook ran in observe mode, so the
act path is not exercised). Receipt private_mb is null off Windows instead of vms (`mem_fields`, tested).
PENDING, all filed as backlog D28 (`vault/plans/deferred-backlog.md`): Windows act-path canary (3.33 GB free at
2026-10-12 evening), compact epoch-start drift (+4.5 MB/epoch in D, n=3), fleet observe ring, PGO, knowledge/UKDL/CBR.

**Active decisions.** Laptop = read-only until Available >= 4 GB (`python -m modules.prr.census`; 2,041 MB at 17:00).
Destructive actions only on panes this programme starts. Recycle only after a boundary crossed inside the process.

**Next 3 actions.**
1. Windows canary (needs >= 4 GB Available): open ONE kclaude pane in this worktree with `CPP_PRR_RECYCLE=act`; run
   ~10 tool turns, `/compact`; expect a receipt RECYCLE + acted, the pane relaunching `--resume` with the same sid, and
   the successor's private bytes near the fresh floor. Repeat with `/clear`. Measure private bytes before and after.
2. If green: observe ring (fleet, receipts only) through the PP dispatcher, then act ring by Owner word.
3. Knowledge: UKDL hard rule/trap candidates from A1/B/C (compact != RAM reclaim; recycle needs a boundary;
   memory note "V8" is wrong engine).

**Start.** `python tools/mission_spend.py goal-status --goal prr`, then `python -m modules.prr.census`, then action 1.
