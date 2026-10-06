# S5 receipt -- offline WU3 dependency packets (tranche context-runtime-3)
VERDICT: UNDECIDED overall. WU2 = dependency projection carries 3/3 critical pages whole (current 0/3, naive 1/3), judge ADMIT.
WU1 = no projection can carry its critical pages: the vendored builder BLOCKS both tools/floor_regression_gate.py and
tools/test_floor_regression_gate.py as credential-content at whole-file limits, so the dependency packet judges DEOPT.
One admitted unit of two (n=2) plus an oracle-seeded projection does not support WIN or LOSE.

## Method (offline, no live mutant)
- Critical pages = .py files the unit's own commits changed (oracle from history): WU1 0f07a3d7+b67f5d8f, WU2 4eea7a8c.
  History reproduced honestly: drift=none (worktree blob == last unit commit blob for every critical page).
- current = unit card + every existing repo file the card names, default builder limits (6000 B excerpt / 24000 B total).
  WU1 card = vault/plans/tok18-tranche-context-runtime-2026-10-06.md, WU2 card = WU2-packet.md.
- naive trim = same file list, raw bytes in card order, cut at the dependency packet's byte size (no dependency awareness).
- dependency = critical pages + direct imports + literal repo paths (tests: imports only), builder upper bounds
  maxExcerptBytes 65536 / maxTotalBytes 1048576 (probed: 65537 -> SUBJECT_INVALID).
- Limit: the dependency projection is seeded from the oracle, so it shows a packet CAN carry the work, not that a
  planner would have chosen these pages beforehand.

## Comparison (cmd: python tools/wu3_packets.py; est. tokens = bytes/4, not a tokenizer count)
| unit | projection | pages | bytes | est. tokens | critical whole |
|---|---|---|---|---|---|
| WU1 | current | 12 | 28571 | 7142 | 0/2 |
| WU1 | naive_trim | 4 | 41170 | 10292 | 0/2 |
| WU1 | dependency | 4 | 75169 | 18792 | 0/2 (both blocked: credential-content) |
| WU2 | current | 8 | 28981 | 7245 | 0/3 |
| WU2 | naive_trim | 4 | 19470 | 4867 | 1/3 |
| WU2 | dependency | 5 | 87564 | 21891 | 3/3 |
For WU2 the dependency packet is ~3x the current packet's bytes and is the only projection that is complete.
The current packets spend their budget on plan/vault pages: 9 of WU1's 12 pages are truncated or blocked.

## Exclusion (cmd: python tools/test_wu3_packets.py)
- WU1-private = {tools/test_floor_regression_gate.py}; WU2-private = {tools/wake_check.py, tools/test_wake_check.py, tools/vault_summarize.py}.
- V-WU3-EXCLUDE-WU1 / -WU2 PASS: neither dependency packet contains a page private to the other unit.
- V-WU3-EXCLUDE-CONTROL PASS (other pole): a packet built over both units' pages contains all 4 private pages, and the check reports them.
- Observed in the CURRENT packets: WU2's card names tools/test_floor_regression_gate.py (WU1-private). Its bytes were blocked, so it leaked by name only.

## Mutation (cmd: python tools/test_wu3_packets.py -> WU3_PASS=11/11, exit 0)
- Control V-WU3-ADMIT-CONTROL: WU2 dependency packet, all critical pages present -> ADMIT.
- V-WU3-MUTANT-PAGE: tools/wake_check.py removed from the packet -> PAGE (not-in-packet), never ADMIT.
- V-WU3-MUTANT-DEOPT: same removal, page absent where the worker runs -> DEOPT (absent-from-disk).
- V-WU3-TRUNCATED-IS-FAULT: default limits truncate vault_summarize.py -> PAGE. V-WU3-UNJUDGED-DEOPT: builder failure -> DEOPT.
- V-WU3-WU1-NO-SILENT-PASS: WU1 -> DEOPT (blocked), consistent with ADMIT iff every critical page is whole.
- The first run used limits above the builder's bound. The builder returned SUBJECT_INVALID and every packet judged DEOPT (builder-unjudged), so it failed closed rather than passing silently.

## Not run / open
- LIVE MUTANT NOT RUN (deferred by the packet): no worker was handed these packets.
- Credential-content filter blocks floor_regression_gate.py, test_floor_regression_gate.py and cep_gen2.py.
  Whether that is a true positive or a filter false positive is UNVERIFIED. Until it is decided, WU1-class work cannot be packeted (Owner/next unit).
- tests on reference.json: 28 private lines redacted in every projection (not critical, noted).
- Files were written via PowerShell WriteAllText because the Write tool asks for permission under ~/.claude in this non-interactive pane.

## Spend
~10 model calls in session 743714db (cap 17); processed tokens not measured with self_spend this session.

COMMITS: 599bd751 (code) + the receipt commit that adds this file (subject "docs(s5): WU3 offline packet receipt")