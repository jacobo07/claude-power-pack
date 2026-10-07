done_gate: the "Full suite command" in 01-VALIDATION.md, every command exit 0

# AO phase 1 close-out -- CR-01, WR-01, WR-02 + phase verification

Authority: Owner 'y' 2026-10-07 (laptop pane b9bd9469), a single exception to amendment A1 decision 4 (GEX44
optimization missions paused) for THIS unit only. Envelope: 4M processed tokens, at most 30 model calls; stop
before it. This packet is your whole task. Batch reads; never reread a file you have read. Never ask a question:
decide inside this scope; ending on a question is a failure. Do not run GSD commands. Do not start Phase 2.

Repo: this clone (/home/kobii/missions/autonomous-optimization), branch mission/autonomous-optimization. Python:
python3. Commit with `git commit -F <msgfile> -- <paths>` (pathspec only), one commit per step, prefix `ao-p1fix:`.
Do not push. Do not touch /home/kobii/.claude/skills/claude-power-pack, ~/.claude config, or any other mission dir.
Phase dir P = .planning/workstreams/autonomous-optimization/phases/01-usage-index-v5-substrate.
Read first, once: P/01-REVIEW.md (CR-01, WR-01, WR-02 -- each states file:line, failure and fix), P/01-VALIDATION.md.

## Steps
1. CR-01 (`tools/usage_index.py` main ~2112 and population ~1784): a bad or date-only `--until` must be REFUSED
   (population returns UNMEASURED with a reason; the CLI never turns it into "no bound"). Pass the raw value through;
   population rejects any `until` that is neither a valid ISO instant nor a number. Add V-gates to
   tools/test_usage_index_v5.py: `--until 2026-09-01` and `--until garbage` -> UNMEASURED, never MEASURED/EXACT;
   a valid instant still MEASURED (control). Show the new gate RED on the unfixed code first (record that output),
   then GREEN.
2. WR-01 (~1157-1162, ~1243-1245): a non-OSError exception while ingesting ONE file rolls that file back, records it
   via `_record_file_error`, and the refresh continues with the next file. Gate: a poison fixture file raising a
   non-OSError plus a good file -> refresh completes, the good file is indexed, the poison file carries files.error,
   population reports UNMEASURED for it. RED first, then GREEN.
3. WR-02 (~855-869 `_registry`, `_attribute`): launch cwd / home only from files with `v5_from = 0`; a legacy file
   that grew (`v5_from > 0`) never defines the launch root. Gate with a grown-legacy fixture whose new bytes carry a
   different cwd. RED first, then GREEN.
4. Run the quick command after each step and the full suite command at the end. Then write P/01-VERIFICATION.md:
   goal-backward against Phase 1's success criteria in ROADMAP.md, one row per criterion with the command that proves
   it and its output tail; CR-01/WR-01/WR-02 listed as FIXED with their gate names; the 5 info items listed as OPEN
   (not fixed here); every row labelled `plane: gex44`. Verdict PASS only if every criterion has evidence; otherwise
   GAPS with the list.

## Receipt
Write P/01-FIX-RECEIPT.md: commits, the RED-then-GREEN output for each gate, the full-suite output tail, files
touched, anything UNKNOWN. Commit it. Then stop.
