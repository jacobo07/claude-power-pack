# PLAN-SKILL-RESIDENCY -- phase-4 audit (2026-10-03)

Auditor: oneshot-architect-auditor, read-only, 35 tool uses. Persisted by the parent session.
Verdict: **EXECUTE-WITH-FIXES**. C0-C3 run now (with G'6, G'8, G'9); C4/C5 frozen until G'1-G'5 and
G'7 are written into the plan.

| id | sev | gap | fix |
|---|---|---|---|
| G'1 | BLOCKER | Opportunity v1 is path-level (`rollover.session_writes`, rollover.py:175-186), so the motivating incident (own edit + peer hunk in the SAME file, R2 log 10:27) reads "no opportunity"; shell writes read as foreign | Line-level ownership: a staged +/- line is own only if it is in the session's Edit old/new_string, Write content or `toolUseResult.structuredPatch`; a shell write to the path -> `basis: unknown`. Fixture = the incident |
| G'2 | BLOCKER | `git diff --cached` at PreToolUse is not what the commit will contain: `-a`, `-- paths` / `--only`, `-i`, `add && commit` in one call, untracked files, `--pathspec-from-file`, `--amend`, `GIT_INDEX_FILE`, `-C dir`, `Set-Location`, `& $g`, aliases, scripted commits; TOCTOU with peers | Commit-plan parser with a fixture table, one row per form -> diff basis or `basis: unparsed` (= UNKNOWN, never "no opportunity"); aperture line in the card header |
| G'3 | MAJOR | A ledger-only card row cannot be "delivery": written at hook time, after the commit tool_use, and shows the model nothing (destructive_doctrine_card.js:84,131) | `delivered_by=card` only for `deny-card` before a LATER commit; ledger-only -> {skill, none}. Window for "Skill before": since the previous commit, else session start |
| G'4 | MAJOR | Python on the hook path: `python -c pass` 2-4 s vs card budget 5000 ms (hook-dispatcher.js:422,777); a node re-implementation of the CO-12 lock = second writer (co_12_telemetry.py:84-95, peer-edited, uncommitted) | Hook = pure node + one bounded `spawnSync(git, timeout 2500, --no-optional-locks)`; rows `{opportunity|unknown|timeout}` in the card's ledger; C5 = OFFLINE adapter ledger -> `record_signal` |
| G'5 | MAJOR | C4 never registers the card in the LIVE dispatcher (`~/.claude/hooks/hook-dispatcher.js`); a repo commit changes nothing | C4b: node --check, insert after live line 422 (HR-001, Owner-visible), sync mirror, G9 procedure (15/15 + --e2e), liveness = a ledger row with this pane's session_id |
| G'6 | MAJOR | Card + CO-12 rows from ~40 benchmark sessions mix with production (no env override for state_dir) | `CLAUDE_DOCTRINE_CARDS=off` + `DOCTRINE_CARDS_STATE_DIR` honoured by the card; runner child env sets both from C2; rows carry `source`/entrypoint; C4 frozen until C3 ends |
| G'7 | MAJOR | Nothing reads the new kind; dotted name breaks convention (co_12_telemetry.py:175,277-288); `foreign_custody` does the opposite of a foreign check (rollover.py:125-158) | kind `capability_opportunity`; consumer named in C8 with a positive control; reuse only `_git` + UNKNOWN idiom |
| G'8 | MINOR | C1: CMD regex requires message-before-name (name-first exists); built-ins counted; list-form content unhandled; isMeta expansions must stay 0; dedupe | order-agnostic regex, filter to installed set, list-form fixture or UNKNOWN, V-SKINV zero-count fixtures for `turnCompanion` and `sourceToolUseID` rows, dedupe by tool_use.id / uuid |
| G'9 | MINOR | Subagent sidechains (`<session>/subagents/agent-*.jsonl`); row `session_id` can differ from file `sessionId` | join on file sessionId + its subagents dir, never on a row field |
| G'10 | MINOR | Stale premises: HEAD; "142" vs Owner's 134 (`skill_overrides.final.json`); p3_delivery path unstated | corrected in the plan |
| G'11 | MINOR | Card spawn on every shell call in every pane (13 spawns already, :366-422) | early `continue:true` before any I/O unless the commit regex matches; measure non-commit median in the card test |

Clean: PreToolUse payload carries session_id and transcript_path; R2 G1-G12 preserved; `agent_telemetry.py`
absent (converge-later stands); heat-map advisor exists.
