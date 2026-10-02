# PP Wiki — Index

Map of every page. Read this first on every query. Schema: [[CLAUDE]]. Timeline: [[log]].

- [[overview]] — evolving thesis on PP's strengths, weaknesses, direction

## Sources

- [[2026-09-30-karpathy-llm-wiki]] — Karpathy's gist defining the LLM Wiki pattern
- [[2026-09-30-yt-9uojngzcjo]] — video: 5 Claude Code concepts; "context is like milk", keep CLAUDE.md short
- [[2026-09-30-yt-91b_v-woaws]] — video: 500h of AI coding; specific prompts, don't-do section, verify the verifier
- [[2026-09-30-system-prompts-leaks]] — repo of reported system prompts incl. Claude Code (@ b632b67; not official)
- [[2026-10-01-sdd-external-research]] — how engineers and tools instruct AI agents; 33-item spec checklist with evidence tiers
- [[2026-10-01-sdd-internal-inventory]] — read-only audit of SDD-OS with file:line evidence
- [[2026-10-01-cbr-external-research]] — what makes a baseline ratchet work; 32-item checklist with evidence tiers
- [[2026-10-01-cbr-internal-inventory]] — read-only audit of the Constitutive Baseline Ratchet with file:line evidence
- [[2026-10-01-kobiicraft-capability-harvest]] — 50 KobiiCraft capabilities from source, by level × trait, with portable forms
- [[2026-10-01-ksr-maturity-profile]] — KobiiSports Resort traits, 41 capabilities, 24 self-recorded gaps; save-loss path verified
- [[2026-10-02-state-centric-reality-scan]] — state-centric mission: ownership sweep, goal spine connected, G-001 converged
- [[2026-10-02-token-economy-external-research]] — cache mechanics, masking vs summarising, fan-out cost; 30-item checklist with tiers
- [[2026-10-02-token-economy-internal-inventory]] — every PP token mechanism with status, measured numbers, owners, 15 contradictions
- [[2026-10-02-token-economy-external-research-2]] — Claude Code knobs (TTL, skillOverrides, autocompact, hook rewrites), coding-agent cost studies
- [[2026-09-30-yt-i10xtuixfey]] — app growth (off-topic for PP): creator equity partnerships, organic-format mining
- [[2026-09-30-yt-pffo4jysptw]] — app growth (off-topic for PP): paid UGC machine, views × conversion model, pay structure

## Components

- [[sdd-os]] — Spec-Driven Development OS: per-prompt tier + spec check; advisory; capability status
- [[constitutive-baseline-ratchet]] — CBR / Torre: per-family rule generations injected per prompt; gate and promotion unwired
- [[portfolio-learnings]] — `knowledge/PORTFOLIO_LEARNINGS.md`: rule-origin ledger, archive in practice (1 source + measurement)
- [[goal-spine]] — durable goal state + judge + scheduled sweep; LIVE since 2026-10-02 (1 source)

## Concepts

- [[llm-wiki-pattern]] — agent-maintained wiki: raw sources, wiki, schema; ingest/query/lint (1 source)
- [[compounding-vs-rederived-knowledge]] — written / read / kept-current test for any knowledge store (1 source)
- [[lean-always-loaded-context]] — keep the always-loaded layer to pointers; load depth on demand (1 source)
- [[maturity-transfer]] — capabilities (not lessons) from a mature repo, matched by trait × plane; proposals, not auto-apply (3 sources)
- [[verdict-pinned-to-what-runs]] — pin a green record to the discovered code closure, not to HEAD (1 source)

## Improvements

- [[measure-knowledge-store-consultation]] — DISCUSSING: which stores sessions actually read (measured)
- [[compact-instructions-section]] — IN-PROGRESS: section added to PP CLAUDE.md; verification pending (1 source)
- [[always-loaded-prefix-audit]] — IDEA, M: ~167 KB loaded every session; classify and trim (2 sources + measurement)
- [[spec-acceptance-as-goal-obligations]] — DISCUSSING, M: spec acceptance → goal obligations; done = judge PASS (3 sources)
- [[mutation-anchor-rot]] — IDEA, S: check drill anchors statically at record-gates / commit (1 source)
- [[tool-output-at-source]] — IDEA, M: tool results are 78 % of growth; shrink them before they land (2 sources)
- [[mid-session-prefix-rebuilds]] — IDEA, S: attributed — 73 % come back from idle > 1 h; see idle-return rollover (1 source)
- [[sdk-probe-floor]] — IDEA, S: 508 one-call `claude -p` runs pay a full floor; neutral cwd saves ~20k each (1 source)
- [[rtk-powershell-gap]] — IDEA, M: RTK compresses Bash only; PowerShell is 26 % of growth (1 source)
- [[cold-start-cache-sharing]] — IDEA, M: first calls write 85-91 % fresh; ≤ 12.4 % if starts read instead (1 source)
- [[hide-unused-skills]] — IDEA, S: 280 of 319 listed skills never invoked in 7 d; `skillOverrides: name-only` (1 source)
- [[hook-injection-diet]] — IDEA, S: hook additionalContext re-read ~$202 / 7 d; inject once per session (1 source)

## Syntheses

- [[goal-spine-connect-not-build]] — state-centric work became real by wiring, not building; G-001 converged unattended
- [[token-economy-levers]] — 7 d spend cut by category/thread/model; 10 levers ranked by bound × evidence × owner
- [[token-economy-brainstorm]] — wave 2: 10 new measurements, lateral pass, ~35 ideas by write/read, context, calls, output
- [[sdd-os-gap-analysis]] — SDD-OS vs an engineer-grade spec checklist: 0/33 met, 6 verified defects, 7 ranked fixes
- [[cbr-gap-analysis]] — CBR vs a 32-item ratchet checklist: 2/32 met, 10 verified defects, full-potential path, 8 ranked fixes
- [[maturity-transfer-pilot-kobiicraft-ksr]] — KobiiCraft → KSR: 6 ranked proposals, 4 product ideas, 16 non-transfers, reverse transfer
