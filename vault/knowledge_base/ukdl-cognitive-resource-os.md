# UKDL — Cognitive Resource OS (2026-09-27)

Mission-scoped entries. Kept out of `ukdl-universal.md` because that file's tail is
appended by an automated writer (CEPS capture); a hand edit there is a same-file
collision. Plan: `vault/plans/cognitive-resource-os-2026-09-27.md`.

### Hard Rules

**`HR-COST-OBSERVED-001`** -- A cost, budget, runway or savings figure is computed
from OBSERVED model usage (the transcript's `message.usage`) and names its source.
An estimate (chars/4, hook injection size) never feeds a budget or a savings claim.
Evidence: `tis.py` logged chars/4 of the JIT injection and `/cost-autopsy` reported
cache 0.00% from it, while transcripts show cache reads at ~98.5% of context;
`budget_monitor` priced hook bytes as input with output fixed at 0 (`ca69a04`).

### Process Rules

**`PR-PRICING-PROVENANCE-001`** -- Prices live in dated provenance files read from the
live pricing page, resolved through `tools/pricing_source.py`. Never hardcode a dated
filename; never write a price from memory. Evidence: `claude-opus-4-7` carried the
Opus 4/4.1 rate ($15/$75, 3x the real $5/$25) for four months because three tools
hardcoded `anthropic_2026-05.json` (`383cb37`).

**`PR-TRANSCRIPT-DEDUPE-001`** -- Transcript usage is repeated on every content-block
line of one message. Key calls by `(message.id, requestId)` before summing, exclude
`<synthetic>` entries, attribute `<session>/subagents/*.jsonl` to the session.
Evidence: 381 usage lines = 150 calls; 17,041 duplicates collapsed on one repo (`9fa1017`).

**`PR-SPLIT-BY-ENTRYPOINT-001`** -- Programmatic credit is measured on `sdk-cli`
sessions only; interactive `cli` sessions are subscription usage. Every transcript line
carries `entrypoint` (one value per file, 400/400 measured). (`ca69a04`)

### Traps

**`T-PROJECT-KEY-PARTIAL-SANITIZE-001`** -- Claude Code's transcript dir name replaces
EVERY non-alphanumeric character with `-`. Replacing only `:` and separators keeps the
`.` of `.claude` — and a directory with exactly that wrong name exists on this host,
empty, so the lookup exited 0 reporting 0 sessions. An empty scan is UNMEASURED, never
a quiet project (`48bbbb7`).

**`T-ONCE-PER-SESSION-PREFIX-001`** -- The startup prefix rides in every call's context.
Counting it once per session read 0.32% of all context; call-weighted it is ~50%.

**`T-ONE-CALL-1H-CACHE-WRITE-001`** -- Short programmatic sessions pay a 1-hour cache
write (2x input) for a prefix no later call reads. Measured over 7 days: 79.9% of
programmatic spend ($72.00 of $90.06) was 1h writes; median 1 call per session, 47 of
62 sessions made <= 2 calls; a session's first call found only 1.9% (sdk-cli) / 16.4%
(cli) of its prefix already cached by an earlier session. The prefix differs between
sessions near its front. HYPOTHESIS, not yet measured: the tool list varies with which
MCP servers connect. Tracked by `startup_shared_share_median` in `tis_observed.py`.

**`T-KNOWLEDGE-CORPUS-AUTOFEED-001`** -- `ukdl-universal.md` (949 KB) is appended by
CEPS auto-capture, one line per tool failure, duplicates included — including failures
of the session reading it. A corpus that grows with its reader's own errors is a log,
not doctrine; recorded, not yet fixed.

**`T-RULE-EXCLUSION-SCOPE-001`** -- On GEX44's claude 2.1.283 (Linux build, static reading of the installed
binary, no run), flag names mislead in both directions. `claudeMdExcludes` passed through `--settings` removes
only the named files from the user `~/.claude/rules` walk, despite its CLAUDE.md name. `--setting-sources`
without `user` also drops the user's CLAUDE.md, settings.json, and user-sourced skills/agents/commands, not
just rules. `CLAUDE_CODE_DISABLE_CLAUDE_MDS` empties the whole user rules directory (all ~22 files) plus
Managed/project CLAUDE.md, not just the three named files. `CLAUDE_CONFIG_DIR` moves `.credentials.json` along
with the whole config tree (an alternate HOME is graded the same way, by code structure, not byte-verified), and
`--bare` forces API-key auth. GEX44. Another claude version must re-run the pre-flight before relying on this.
Cites `.planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/EVIDENCE.md` sections 2b, 3 and 4,
commits `c632771` `d08644d`.
