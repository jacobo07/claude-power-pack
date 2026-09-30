# UKDL — Cognitive Resource OS (2026-09-27)

Mission-scoped entries. Kept out of `ukdl-universal.md` because that file's tail is
appended by an automated writer (CEPS capture); a hand edit there is a same-file
collision. Plan: `vault/plans/cognitive-resource-os-2026-09-27.md`.

GEX44 run 2026-09-28 (branch `mission/cognitive-resource-os-gex44`): CRO-01 BLOCKED, CRO-02 MEASURED, CRO-03 PASS, CRO-04 UNJUDGED. Per-phase evidence paths and commits are in RESUMPTION section 2d; the entries below naming GEX44 come from that run and cite their phase EVIDENCE.

### Hard Rules

**`HR-COST-OBSERVED-001`** -- A cost, budget, runway or savings figure is computed
from OBSERVED model usage (the transcript's `message.usage`) and names its source.
An estimate (chars/4, hook injection size) never feeds a budget or a savings claim.
Evidence: `tis.py` logged chars/4 of the JIT injection and `/cost-autopsy` reported
cache 0.00% from it, while transcripts show cache reads at ~98.5% (laptop) of context;
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
Evidence: 381 usage lines (laptop) = 150 calls; 17,041 duplicates (laptop) collapsed on one repo (`9fa1017`).

**`PR-SPLIT-BY-ENTRYPOINT-001`** -- Programmatic credit is measured on `sdk-cli`
sessions only; interactive `cli` sessions are subscription usage. Every transcript line
carries `entrypoint` (one value per file, 400/400 (laptop) measured). (`ca69a04`)

**`PR-OWNER-GATE-BEFORE-RUN-001`** -- An unattended run that may not ask the Owner anything cannot contain a step
that only the Owner can approve. Settle every Owner-only approval (here, a package install) before launch, or
take the step out of the run. Evidence: GEX44 Phase 1 put the blocking package-legitimacy checkpoint (pinned
pytest/pluggy/iniconfig, job-scratch venv) inside the autonomous run; with no Owner reachable it was answered
rejected, so CRO-01 stayed BLOCKED while its four gates passed. GEX44.
Cites `.planning/workstreams/cognitive-resource-os/phases/01-gate-verdict-on-the-big-host/EVIDENCE.md` sections 2 and 4, commit `eab20dc`.

### Traps

**`T-PROJECT-KEY-PARTIAL-SANITIZE-001`** -- Claude Code's transcript dir name replaces
EVERY non-alphanumeric character with `-`. Replacing only `:` and separators keeps the
`.` of `.claude` — and a directory with exactly that wrong name exists on this host (laptop),
empty, so the lookup exited 0 reporting 0 sessions. An empty scan is UNMEASURED, never
a quiet project (`48bbbb7`).

**`T-ONCE-PER-SESSION-PREFIX-001`** -- The startup prefix rides in every call's context.
Counting it once per session read 0.32% (laptop) of all context; call-weighted it is ~50%.

**`T-ONE-CALL-1H-CACHE-WRITE-001`** -- Short programmatic sessions pay a 1-hour cache
write (2x input) for a prefix no later call reads. Measured over 7 days: 79.9% (laptop) of
programmatic spend ($72.00 (laptop) of $90.06) was 1h writes; median 1 call per session, 47 of
62 sessions made <= 2 calls; a session's first call found only 1.9% (sdk-cli) (laptop) / 16.4%
(cli) of its prefix (laptop) already cached by an earlier session. The prefix differs between
sessions near its front. HYPOTHESIS, not yet measured (as of 2026-09-27): the tool list varies with which
MCP servers connect. Tracked by `startup_shared_share_median` in `tis_observed.py`.
Tested once on GEX44 on 2026-09-28: UNJUDGED, see `T-BACK-TO-BACK-REUSE-001`.

**`T-KNOWLEDGE-CORPUS-AUTOFEED-001`** -- `ukdl-universal.md` (949 KB) (laptop) is appended by
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

**`T-BASELINE-WITHOUT-HOST-001`** -- The same observed metric differs by up to an order of magnitude between
hosts: first-call shared-prefix median sdk-cli 1.9% (laptop) vs 30.0% (GEX44), cli 16.4% (laptop) vs 46.6%
(GEX44). A figure without host, window, scope and entrypoint cannot be compared or reused. The instrument names
candidate factors (population, window, session shape) and cannot separate the cause. GEX44.
Cites `.planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/EVIDENCE.md` sections 2b and 3, commits `1766507` `cb6fc62`.

**`T-MEASURER-IN-CORPUS-001`** -- The run that measures a host's transcripts writes into them, and the corpus
moves while it is being read. On GEX44 this workstream's own sessions were 1 cli session and about $17.44 of the
trailing-7d cli spend. Two reads minutes apart gave a different call count. The Phase 4 A/B left 4 sdk-cli haiku
sessions under project keys `-tmp-claude-1000-cro-p04-ab-armA` and `-tmp-claude-1000-cro-p04-ab-armB`. Report the
measuring run's own dir as a separate scope and exclude experiment keys from the next baseline. GEX44.
Cites `.planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/EVIDENCE.md` and `.planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/EVIDENCE.md`, commits `1766507` `f32ea4b`.

**`T-BACK-TO-BACK-REUSE-001`** -- Two identical `claude -p` sessions launched seconds apart in one directory did
not miss each other's prefix. The second session's first call read 99.97% (default MCP) and 99.96% (MCP stripped)
of its context from cache (GEX44, claude 2.1.283, haiku, n=2 per arm). The default-MCP pair showed an identical
tool list and server statuses (vA NO), so MCP tool-list variance was never exercised: UNJUDGED, R8. The laptop's
1.9% sdk-cli first-call shared share (laptop) is therefore not reproduced by identical back-to-back sessions, and
its cause stays unmeasured. A rerun only counts if the MCP surface changes between run 1 and run 2. GEX44.
Cites `.planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/EVIDENCE.md` sections 1-4 (commits `740b41b` `f32ea4b`) and `.planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/EVIDENCE.md` section 3 (the laptop figure).

**`T-TRUTHY-PRESENCE-GUARD-001`** -- A guard meant to block on the PRESENCE of an environment variable, written
as a truthiness test (`environ.get(name)`), lets an empty-but-set variable through. In `ab_runner.py` an empty
`ANTHROPIC_API_KEY` or `CLAUDE_CONFIG_DIR` read as unset, and the empty `ANTHROPIC_API_KEY` would reach the child
claude. The recorded GEX44 run was not affected: no such name existed, and all four runs' init events record
apiKeySource none. Test membership (`name in environ`) and fix before any reuse of the runner. GEX44.
Cites `.planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/04-REVIEW.md` (CR-01 and the disposition) and `.planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/EVIDENCE.md` sections 0 and 2, commits `8c13d18` `cd93c98`.

**`T-POSIX-REWRITE-ON-POWERSHELL-001`** -- A command-rewriting PreToolUse hook that never reads `tool_name` rewrites
every shell the dispatcher routes to it. Both dispatchers send PowerShell through the chain that runs
`rtk-rewrite.js`; rtk turned a PowerShell `gh pr list` into `"...\rtk.exe" gh pr list`, a string followed by stray
tokens, and the call failed with ParserError. The failure reads as a PowerShell quirk, not as a hook, so nobody traced it.
Any hook that rewrites `tool_input.command` must scope itself to the tool whose grammar it emits; a missing
`tool_name` keeps the old behaviour so a rename degrades to "fires", never to "never fires". Laptop, 2026-09-30.
Cites `tools/test_rtk_rewrite_scope.py` (4/4, 2 red before), commit `f2a4788`.