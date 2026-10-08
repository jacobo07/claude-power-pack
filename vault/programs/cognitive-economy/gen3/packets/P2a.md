# P2a -- recon-factory Phase 2 GEX44 leg, LOCAL half (A/A returned-object leg, AA capsule, second live root, build)

Mission: m-f501c31d6523 (write this id in the receipt, mandatory).
Authority: Owner "fund it" + "b" 2026-10-08 (STATE.md "DECIDED 2026-10-08"); route (a) split judge 2026-10-05; GAP-10
ratified 2026-10-03. Funds P2a ONLY: NO send, NO VPS or GEX44 contact of any kind, never write under
C:\Users\User\Apps\recon_work\match_accel_factory, never arm a mission, never push. P2b (send/wait/judge) is the main pane's.
Envelope (route-P2a.json): target 1.67M | warn 1.75M | stop 1.85M, then the session guard allows up to 4 closeout calls.
When the SESSION BUDGET warn advisory appears, go STRAIGHT to the receipt and the commit, whatever is unfinished, and
write the unfinished part as PARTIAL. Hard limit 11 tool calls. 0 subagents. NO search tools (Glob/Grep) at all.

## Corpus = ONE file
Read `C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cognitive-economy\gen3\recon-reforecast\P2A-DOSSIER.md`
once. It holds the Owner decisions, the measured facts, AA_GATE.md in full, P2a POLICY v1, the drill gates and the
verbatim source (AST-extracted, with line numbers) of every function you edit or call in stage.py, reproduce.py,
capsule_build.py, custody.py and oracle_parity.py. Read no other file; edit with Edit using the dossier's verbatim text as
old_string. Anything not in the dossier is UNKNOWN: write it down, never look it up. Implement policy v1; do not redesign it.

## Deliverables (recon work tree C:\Users\User\Apps\recon_work\wt_keosdtk_home, all under tools/wros/binary/decomp)
1. gex44/stage.py (policy 1), gex44/capsule_build.py (policy 2), gex44/reproduce.py (policy 3), oracle_parity.py (policy 4).
2. gex44/test_p2a.py with the 7 V-P2A-* gates of the dossier, final `P2A_DRILL=n/m`.
3. Run once (policy 5): build the AA capsule into C:\Users\User\Apps\recon_work\recon_factory\gex44, then
   `stage.py build --mode reproduce --capsule <id>` against that root. Print the CAPSULE= and BUILD= lines. NO send.
4. `.planning/workstreams/recon-factory/phases/02-oracle-parity-s1/02-03-SUMMARY.md` (<= 40 lines; carries the plan): drill
   lines verbatim, CAPSULE/BUILD lines, the exact P2b command sequence (pre-checks, send, wait, judge) for the main pane.

## Call plan (11)
1 Read dossier. 2-5 Edit (one consolidated Edit per file: stage.py, capsule_build.py, reproduce.py, oracle_parity.py).
6 Write test_p2a.py. 7 One PowerShell call (absolute python `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`,
cwd = the gex44 dir, PYTHONIOENCODING=utf-8): test_p2a.py, then, only if it printed P2A_DRILL=7/7, the capsule build and the
stage build. 8 Write SUMMARY. 9 Write receipt
`C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cognitive-economy\gen3\P2a-receipt.md`. 10 One PowerShell call:
commit the 5 code files + SUMMARY in the work tree, then the receipt in the PP repo, each by pathspec (`git add -- <paths>;
git commit -F <msgfile> -- <paths>`; git = `C:\Program Files\Git\cmd\git.exe`), then print both `git log -1 --format=%h %s`.
11 spare (one fix, only if call 7 failed; otherwise unused).

The recon work tree has ~568 dirty `.ksr_vault` paths owned by other sessions: never stage, restore or clean them.
Do not edit ROADMAP.md or STATE.md. Capsule and job directories are outside git; never commit them.

## Receipt (<= 20 lines)
Mission id, calls used, files + commit hashes, drill lines verbatim, CAPSULE= and BUILD= lines, open points. Spend is
metered by the control plane. Ending on a question counts as a failure. End with `HANDOFF NOTE: P2a done` or the blocker.
